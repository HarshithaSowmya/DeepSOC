import asyncio
import os
import secrets
import time
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from kafka.errors import KafkaError
from .models import SecurityLog, IncidentUpdate, ResponseRequest
from .config import LOG_TOPIC, SOC_MODE
from .kafka_client import producer, kafka_reachable
from .db import init_db, list_alerts, list_incidents, update_incident, record_response, get_alert, get_incident, dashboard_metrics
from .response_engine import execute_response
from .ml_detector import AnomalyDetector
from .detection import process_event
from . import simulator

STATIC_DIR=Path(__file__).resolve().parent.parent/'static'
ASSET_HASHES={name:hashlib.sha256((STATIC_DIR/name).read_bytes()).hexdigest()[:16]
              for name in ('styles.css','app.js')}
state={'mode':'unknown','detector':None,'producer':None,'sim_task':None,'sim_stop':None}

@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    if SOC_MODE not in {'auto','demo','kafka'}:raise RuntimeError('SOC_MODE must be auto, demo or kafka')
    state['mode']=('kafka' if kafka_reachable() else 'demo') if SOC_MODE=='auto' else SOC_MODE
    state['sim_task']=None
    if state['mode']=='demo':
        state['detector']=await asyncio.to_thread(AnomalyDetector)
        state['sim_stop']=asyncio.Event()
        state['sim_task']=asyncio.create_task(simulator.run(state['detector'],state['sim_stop']))
    else:
        state['producer']=await asyncio.to_thread(producer)
    try:yield
    finally:
        if state['sim_task']:
            state['sim_stop'].set()
            await state['sim_task']
        if state['producer']:
            state['producer'].close(timeout=10)
            state['producer']=None

app=FastAPI(title='DeepSOC · AI Integrated SOC Detection & Response',version='2.0.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(STATIC_DIR)),name='static')

@app.middleware('http')
async def access_control(request:Request,call_next):
    key=os.getenv('API_KEY','')
    if key and request.url.path.startswith('/api/') and not secrets.compare_digest(request.headers.get('X-API-Key',''),key):
        return JSONResponse({'detail':'API key required'},status_code=401)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['X-Frame-Options']='DENY'
    if request.url.path=='/' or request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    return response

@app.get('/',include_in_schema=False)
def dashboard():
    html=(STATIC_DIR/'index.html').read_text(encoding='utf-8-sig')
    for name,version in ASSET_HASHES.items():
        html=html.replace(f'/static/{name}',f'/assets/{version}/{name}')
    return HTMLResponse(html)

@app.get('/assets/{version}/{filename}',include_in_schema=False)
def versioned_asset(version:str,filename:str):
    if ASSET_HASHES.get(filename)!=version:
        raise HTTPException(404,'Asset version not found')
    return FileResponse(STATIC_DIR/filename,headers={
        'Cache-Control':'public, max-age=31536000, immutable'})

@app.get('/health')
def health():
    if state['sim_task'] and state['sim_task'].done():raise HTTPException(503,'Detection simulator stopped')
    if state['mode']=='kafka' and not kafka_reachable():raise HTTPException(503,'Kafka unavailable')
    return {'status':'healthy','service':'soc-api','mode':state['mode']}

@app.get('/api/metrics')
def get_metrics():return {**dashboard_metrics(),'mode':state['mode']}

@app.post('/api/logs',status_code=202)
def ingest_log(log:SecurityLog):
    event=log.model_dump(mode='json')
    if state['mode']=='kafka':
        try:state['producer'].send(LOG_TOPIC,event).get(timeout=10)
        except KafkaError as exc:raise HTTPException(503,'Kafka ingestion unavailable') from exc
    else:process_event(state['detector'],event)
    return {'status':'accepted','mode':state['mode']}

@app.get('/api/alerts')
def alerts(limit:int=Query(100,ge=1,le=500)):return list_alerts(limit)

@app.get('/api/incidents')
def incidents(limit:int=Query(100,ge=1,le=500)):return list_incidents(limit)

@app.patch('/api/incidents/{incident_id}')
def change_incident(incident_id:int,update:IncidentUpdate):
    if not update_incident(incident_id,update.status):raise HTTPException(404,'Incident not found')
    return {'incident_id':incident_id,'status':update.status}

@app.post('/api/incidents/{incident_id}/respond')
def respond(incident_id:int,request:ResponseRequest):
    incident=get_incident(incident_id)
    if not incident:raise HTTPException(404,'Incident not found')
    if incident['status'] in {'resolved','contained'}:raise HTTPException(409,'Incident already contained or resolved')
    alert=get_alert(incident['alert_id'])
    result=execute_response(request.action,alert['source_ip'] if alert else 'unknown')
    record_response(incident_id,result)
    return {'incident_id':incident_id,'result':result,'simulated':True}
