import pytest
from fastapi.testclient import TestClient
import server
@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'DB',tmp_path/'test.sqlite3');monkeypatch.delenv('TYPESAFE_API_KEY',raising=False)
 return TestClient(server.app)
@pytest.mark.parametrize('text,status',[('2','incomplete'),('2, 2, 2','incomplete'),('2, -1+i*sqrt(3), -1-i*sqrt(3)','complete'),('2, -1+sqrt(3)*i, -1-sqrt(3)*i','complete'),('8','incorrect'),('__import__("os").system("id")','not_checked'),('2**999999','not_checked'),('1/0','not_checked'),('2.0','not_checked'),('I think the answer is two','not_checked')])
def test_exact_root_checker(text,status):assert server.check(server.PROBLEMS[0],text)['status']==status

def test_transfer_and_unity():
 assert server.check(server.PROBLEMS[1],'-2,1+i*sqrt(3),1-i*sqrt(3)')['status']=='complete'
 assert server.check(server.PROBLEMS[2],'1,-1,i,-i')['status']=='complete'

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
