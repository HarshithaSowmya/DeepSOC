import importlib
from html.parser import HTMLParser
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path,monkeypatch):
    import app.db as db
    import app.main as main
    monkeypatch.setattr(db,'DB_PATH',str(tmp_path/'test.db'))
    monkeypatch.setattr(main,'SOC_MODE','demo')
    monkeypatch.delenv('API_KEY',raising=False)
    with TestClient(main.app) as c:yield c

def threat(client):
    r=client.post('/api/logs',json={'source_ip':'192.0.2.42','destination_port':22,'failed_attempts':25,'bytes_sent':4500000,'duration_ms':20000})
    assert r.status_code==202
    a=next(a for a in client.get('/api/alerts').json() if a['source_ip']=='192.0.2.42')
    i=next(i for i in client.get('/api/incidents').json() if i['alert_id']==a['alert_id'])
    return a,i

def test_detection_response_lifecycle(client):
    a,i=threat(client)
    assert a['severity']=='critical'
    path=f"/api/incidents/{i['incident_id']}"
    assert client.patch(path,json={'status':'investigating'}).status_code==200
    r=client.post(path+'/respond',json={'action':'block_ip'})
    assert r.status_code==200 and r.json()['simulated'] is True
    assert client.post(path+'/respond',json={'action':'block_ip'}).status_code==409
    assert next(x for x in client.get('/api/alerts').json() if x['alert_id']==a['alert_id'])['status']=='contained'
    assert client.patch(path,json={'status':'resolved'}).status_code==200
    m=client.get('/api/metrics').json()
    assert m['logs_ingested']>=1 and m['responses_executed']==1
    assert len(m['activity'])==30 and sum(x['events'] for x in m['activity'])>=1

def test_validation_and_missing_incidents(client):
    for payload in [{'source_ip':'bad'},{'source_ip':'10.0.0.1','failed_attempts':-1},{'source_ip':'10.0.0.1','destination_port':70000}]:
        assert client.post('/api/logs',json=payload).status_code==422
    assert client.get('/api/alerts?limit=-1').status_code==422
    assert client.patch('/api/incidents/99999',json={'status':'resolved'}).status_code==404
    assert client.patch('/api/incidents/1',json={'status':'invalid'}).status_code==422
    assert client.post('/api/incidents/1/respond',json={'action':'arbitrary'}).status_code==422

def test_api_key(client,monkeypatch):
    monkeypatch.setenv('API_KEY','test-secret')
    assert client.get('/api/metrics').status_code==401
    assert client.get('/api/metrics',headers={'X-API-Key':'wrong'}).status_code==401
    assert client.get('/api/metrics',headers={'X-API-Key':'test-secret'}).status_code==200
    assert client.get('/health').status_code==200
    assert client.get('/').status_code==200

def test_persistence(client):
    import app.db as db
    threat(client)
    before=db.dashboard_metrics()
    db.init_db()
    after=db.dashboard_metrics()
    assert before['logs_ingested']<=after['logs_ingested']
    assert after['alerts_created']>=before['alerts_created']

def test_dashboard_has_unique_ids(client):
    class IDs(HTMLParser):
        def __init__(self):super().__init__();self.ids=[]
        def handle_starttag(self,tag,attrs):self.ids.extend(v for k,v in attrs if k=='id')
    p=IDs();p.feed(client.get('/').text)
    assert len(p.ids)==len(set(p.ids))
    assert client.get('/static/app.js').status_code==200
