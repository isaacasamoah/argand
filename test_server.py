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

def test_failure_mock_cites_immutable_evidence(client):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','action':'failure_fixture'}).json()
 assert a['tutor_source']=='deliberate failure fixture'
 r=client.post('/api/attempts/'+a['id']+'/investigate').json()
 assert r['classification']=='supported_failure' and r['source'].startswith('Mock')
 assert all(c['quote']==a['evidence'][c['id']] for c in r['citations'])

def test_mock_does_not_invent_unknown_diagnosis(client):
 a=client.post('/api/attempts',json={'problem_id':'roots-8','text':'99'}).json()
 r=client.post('/api/attempts/'+a['id']+'/investigate').json()
 assert r['classification']=='insufficient_evidence'

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
