import pytest
from fastapi.testclient import TestClient
import server
@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'DB',tmp_path/'test.sqlite3');monkeypatch.delenv('TYPESAFE_API_KEY',raising=False);monkeypatch.delenv('OPENAI_API_KEY',raising=False)
 return TestClient(server.app)
@pytest.mark.parametrize('text,status',[('2','incomplete'),('2, 2, 2','incomplete'),('2, -1+i*sqrt(3), -1-i*sqrt(3)','complete'),('2, -1+sqrt(3)*i, -1-sqrt(3)*i','complete'),('8','incorrect'),('__import__("os").system("id")','not_checked'),('2**999999','not_checked'),('1/0','not_checked'),('2.0','not_checked'),('I think the answer is two','not_checked')])
def test_exact_root_checker(text,status):assert server.check(server.PROBLEMS[0],text)['status']==status

def test_single_practice(client):
 assert [p['id'] for p in client.get('/api/config').json()['problems']]==['roots-8']
 assert client.post('/api/attempts',json={'problem_id':'roots-minus8','text':'-2'}).status_code==400

def test_no_false_jev_pass(client):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'}).json()
 assert a['checker']['status']=='incomplete'
 r=client.post('/api/attempts/'+a['id']+'/evaluate');assert r.status_code==503

def test_chat_and_voice_without_key(client,monkeypatch):
 monkeypatch.delenv('OPENAI_API_KEY',raising=False)
 assert client.post('/api/attempts',json={'problem_id':'roots-8','action':'chat','text':'Why?'}).status_code==503
 assert client.post('/api/voice/session',headers={'Origin':'http://127.0.0.1:18770'},json={'sdp':'offer','problem_id':'roots-8'}).status_code==503
 assert client.post('/api/voice/session',headers={'Origin':'https://example.com'},json={'sdp':'offer','problem_id':'roots-8'}).status_code==403

def test_voice_server_owns_models_and_context(client,monkeypatch):
 monkeypatch.setenv('OPENAI_API_KEY','dummy-test-key')
 captured={}
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):
   captured.update(kwargs['json'])
   return server.httpx.Response(200,json={'session':{'id':'live_test'},'transport':{'sdp':'answer'}},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'}).json()
 r=client.post('/api/voice/session',headers={'Origin':'http://127.0.0.1:18770'},json={'sdp':'offer','problem_id':'roots-8','parent_id':a['id']})
 assert r.status_code==200
 assert captured['session']['model']=='gpt-live-1'
 assert captured['session']['delegation']['responses']['model']=='gpt-6.1-sol'
 assert captured['session']['audio']['output']['voice']=='willow'
 assert captured['session']['delegation']['responses']['reasoning']['effort']=='medium'
 assert 'incomplete' in captured['session']['input'][0]['content'][0]['text']
 assert 'dummy-test-key' not in r.text
 assert client.post('/api/voice/session',headers={'Origin':'http://127.0.0.1:18770'},json={'sdp':'offer','problem_id':'roots-unity','parent_id':a['id']}).status_code==400

def test_chat_preserves_checker_history(client,monkeypatch):
 monkeypatch.setenv('OPENAI_API_KEY','dummy-test-key')
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):
   assert 'incomplete' in kwargs['json']['input']
   assert kwargs['json']['store'] is False
   return server.httpx.Response(200,json={'output':[{'type':'message','content':[{'type':'output_text','text':'What other angles could work?'}]}]},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'}).json()
 r=client.post('/api/attempts',json={'problem_id':'roots-8','action':'chat','text':'What next?','parent_id':a['id']})
 assert r.status_code==200 and r.json()['checker']['status']=='not_checked'
 assert r.json()['history'][0]['checker']['status']=='incomplete'

def test_voice_checker_lesson_and_practice(client):
 r=client.post('/api/voice/check',json={'example':'lesson','roots':'1+i,-1-i'}).json()
 assert r['checker']['status']=='complete'
 assert client.post('/api/voice/check',json={'example':'lesson','roots':'1-i'}).json()['checker']['status']=='incorrect'
 assert client.post('/api/voice/check',json={'example':'practice','roots':'2'}).json()['checker']['status']=='incomplete'
 assert client.post('/api/voice/check',json={'example':'lesson','roots':'__import__("os")'}).json()['checker']['status']=='not_checked'
 assert client.post('/api/voice/check',json={'example':'other','roots':'2'}).status_code==400

@pytest.mark.parametrize('radius,angle,matches',[(2,0,True),(2,120,True),(2,240,True),(2,360,True),(1.9,120,False),(2,115,False),(0,0,False),(3,45,False)])
def test_visual_candidate_checked_exactly(client,radius,angle,matches):
 result=client.post('/api/practice/cube',json={'modulus':radius,'angle':angle}).json()
 assert result['matches'] is matches
 if matches:
  assert server.check(server.PROBLEMS[0],result['exact'])['status']=='incomplete'
  assert result['cubed']==[8,0]
 else:assert result['exact'] is None

def test_visual_candidate_bounds_and_duplicates(client):
 for radius,angle in [(3.1,0),(2,361),(2,121),(1.99,120)]:
  assert client.post('/api/practice/cube',json={'modulus':radius,'angle':angle}).status_code>=400
 a=client.post('/api/practice/cube',json={'modulus':2,'angle':0}).json()
 b=client.post('/api/practice/cube',json={'modulus':2,'angle':360}).json()
 assert a['exact']==b['exact']

@pytest.mark.parametrize('text,status',[('2','incomplete'),('2,8','incorrect'),('2,-1+i*sqrt(3),-1-i*sqrt(3)','complete'),('hello','not_checked')])
def test_model_feedback_receives_exact_checker(client,monkeypatch,text,status):
 monkeypatch.setenv('OPENAI_API_KEY','dummy-test-key')
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):
   state=server.json.loads(kwargs['json']['input'])
   assert kwargs['json']['model']=='gpt-6.1-sol' and kwargs['json']['reasoning']['effort']=='low'
   assert state['checker']['status']==status and state['question']==text
   assert 'do not name missing roots' in kwargs['json']['instructions']
   return server.httpx.Response(200,json={'output':[{'type':'message','content':[{'type':'output_text','text':'Feedback grounded in the supplied result.'}]}]},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 response=client.post('/api/attempts',json={'problem_id':'roots-8','text':text})
 assert response.status_code==200
 row=response.json();assert row['checker']['status']==status
 assert row['tutor_source'].startswith('OpenAI tutor')
 assert row['evidence']['T1']==row['tutor']
 assert server.json.loads(row['evidence']['C1'])==row['checker']

def test_model_feedback_failure_preserves_checked_attempt(client,monkeypatch):
 monkeypatch.setenv('OPENAI_API_KEY','dummy-test-key')
 class BrokenClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,*args,**kwargs):raise server.httpx.ConnectError('offline')
 monkeypatch.setattr(server.httpx,'AsyncClient',BrokenClient)
 response=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'})
 assert response.status_code==200
 row=response.json();assert row['checker']['status']=='incomplete'
 assert row['tutor_source']=='SymPy result · model feedback unavailable'
 assert server.get_attempt(row['id'])['checker']==row['checker']


def test_single_roots_accumulate_without_losing_verified_work(client):
 parent=None
 for text,expected,status in [('2',1,'incomplete'),('2',1,'incomplete'),('8',1,'incorrect'),('hello',1,'not_checked'),('-1+sqrt(3)i',2,'incomplete'),('-1-i*sqrt(3)',3,'complete')]:
  response=client.post('/api/attempts',json={'problem_id':'roots-8','action':'collect','text':text,'parent_id':parent})
  assert response.status_code==200
  row=response.json();assert len(row['collected_roots'])==expected;assert len(row['collection_points'])==expected;assert row['checker']['status']==status
  parent=row['id']
 hint=client.post('/api/attempts',json={'problem_id':'roots-8','action':'hint','parent_id':parent}).json()
 assert hint['collected_roots']==row['collected_roots']
 assert client.post('/api/attempts',json={'problem_id':'roots-8','action':'collect','text':'2,8','parent_id':parent}).status_code==400
 assert client.post('/api/attempts',json={'problem_id':'roots-8','action':'collect','text':'2'}).json()['collected_roots']==['2']

@pytest.mark.parametrize('value',['(1)/(2)','i^2','i(1+1)','sqrt(3)i','(1+i)(1-i)'])
def test_math_editor_notation_is_supported(value):
 assert server.check(server.PROBLEMS[0],value)['status']!='not_checked'

def test_live_assertions_use_probability_and_actual_response(client,monkeypatch):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','action':'failure_fixture'}).json()
 monkeypatch.setenv('TYPESAFE_API_KEY','dummy');monkeypatch.setenv('OPENAI_API_KEY','dummy')
 calls=[]
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):
   body=kwargs['json'];calls.append(body)
   if 'typesafe' in url:
    assert body['state']['tutor']==a['tutor']
    assert all(q['type']=='noul' for q in body['questions'].values())
    data={'answers':{i:{'type':'noul','noul':.05 if i=='A01' else .99} for i in body['questions']}}
   else:
    assert body['model']=='gpt-6.1-sol'
    data={'output':[{'content':[{'type':'output_text','text':server.json.dumps({'classification':'supported_failure','statement':'The reply calls an incomplete set complete.','citations':[{'id':'T1','quote':a['tutor']},{'id':'C1','quote':a['evidence']['C1']}]})}]}]}
   return server.httpx.Response(200,json=data,request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 r=client.post('/api/attempts/'+a['id']+'/evaluate');assert r.status_code==200
 rows={x['id']:x for x in r.json()['rows']}
 assert rows['A01']['state']=='fail' and rows['A01']['probability']==.05
 assert rows['A01']['annotation']['classification']=='supported_failure'
 assert rows['A07']['state']=='not_applicable' and len(calls)==2

def test_voice_evidence_scopes_mode_and_recomputes_tool_checks(client):
 events=[{'who':'You','text':'Check 2','context':{'mode':'practice','latestAttempt':None}}, {'who':'Tool','args':{'example':'practice','roots':'2'},'result':{'checker':{'status':'complete'}}}, {'who':'Tutor','text':'It works, but there are more roots.','context':{'mode':'practice','latestAttempt':None}}, {'who':'You','text':'Explain the lesson','context':{'mode':'lesson'}}, {'who':'Tutor','text':'The real axis is horizontal.','context':{'mode':'lesson'}}]
 r=client.post('/api/voice/evidence',json={'session_id':'test','events':events});assert r.status_code==200
 first,last=r.json();assert first['checker']['status']=='incomplete' and last['checker']['status']=='not_checked'
 assert first['mode']=='practice' and last['mode']=='lesson'
 assert 'Explain the lesson' not in first['evidence']['V1']
 assert client.post('/api/voice/evidence',json={'session_id':'test','events':events}).json()[0]['id']==first['id']

@pytest.mark.parametrize('bad',[1.2,True,'0.8'])
def test_invalid_jev_probability_never_passes(client,monkeypatch,bad):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'}).json();monkeypatch.setenv('TYPESAFE_API_KEY','dummy')
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):return server.httpx.Response(200,json={'answers':{i:{'noul':bad} for i in kwargs['json']['questions']}},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 assert client.post('/api/attempts/'+a['id']+'/evaluate').status_code==502

def test_investigator_rejects_invented_quotes(client,monkeypatch):
 import asyncio
 a=client.post('/api/attempts',json={'problem_id':'roots-8','action':'failure_fixture'}).json()
 monkeypatch.setenv('OPENAI_API_KEY','dummy')
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):return server.httpx.Response(200,json={'output':[{'content':[{'type':'output_text','text':server.json.dumps({'classification':'supported_failure','statement':'Invented claim','citations':[{'id':'T1','quote':'This was never said.'}]})}]}]},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 result=asyncio.run(server.explain_failure(a,{'id':'A01'}));assert 'error' in result and 'statement' not in result

@pytest.mark.parametrize('probability,expected',[(.34,'fail'),(.35,'uncertain'),(.5,'uncertain'),(.65,'uncertain'),(.66,'pass')])
def test_probability_boundaries(client,monkeypatch,probability,expected):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'2'}).json();monkeypatch.setenv('TYPESAFE_API_KEY','dummy')
 class FakeClient:
  def __init__(self,**kwargs):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*args):pass
  async def post(self,url,**kwargs):return server.httpx.Response(200,json={'answers':{i:{'noul':probability} for i in kwargs['json']['questions']}},request=server.httpx.Request('POST',url))
 monkeypatch.setattr(server.httpx,'AsyncClient',FakeClient)
 r=client.post('/api/attempts/'+a['id']+'/evaluate').json()
 row=next(x for x in r['rows'] if x['id']=='A01');assert row['state']==expected
 assert ('annotation' in row)==(expected!='pass')

def test_voice_snapshot_versions_preserve_previous_evidence(client):
 events=[{'who':'Tutor','text':'The horizontal axis','context':{'mode':'lesson'}}]
 first=client.post('/api/voice/evidence',json={'session_id':'snapshots','events':events}).json()[0]
 events.append({'who':'Tutor','text':' is the real part.','context':{'mode':'lesson'}})
 second=client.post('/api/voice/evidence',json={'session_id':'snapshots','events':events}).json()[0]
 assert first['record_key']==second['record_key'] and first['id']!=second['id']
 assert server.get_attempt(first['id'])['tutor']=='The horizontal axis'
 assert server.get_attempt(second['id'])['tutor']=='The horizontal axis is the real part.'
