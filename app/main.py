import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import SecurityLog, IncidentUpdate, ResponseRequest
from .config import LOG_TOPIC
from .kafka_client import producer
from .db import init_db, list_alerts, list_incidents, update_incident, record_response
from .response_engine import execute_response

BASE_DIR=Path(__file__).resolve().parent.parent
STATIC_DIR=BASE_DIR/"static"
app=FastAPI(title="AI Integrated SOC Detection & Response Platform",version="1.0.0")
app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")
metrics={"logs_ingested":0,"alerts_created":0,"incidents_created":0,"responses_executed":0,"started_at":time.time()}

@app.on_event("startup")
def startup(): init_db()

@app.get("/",include_in_schema=False)
def dashboard(): return FileResponse(STATIC_DIR/"index.html")

@app.get("/health")
def health(): return {"status":"healthy","service":"soc-api"}

@app.get("/api/metrics")
def get_metrics():
    uptime=max(time.time()-metrics["started_at"],.001)
    return {**metrics,"ingest_rate_since_start":round(metrics["logs_ingested"]/uptime,2)}

@app.post("/api/logs",status_code=202)
def ingest_log(log:SecurityLog):
    p=producer();p.send(LOG_TOPIC,log.model_dump(mode="json"));p.flush();p.close()
    metrics["logs_ingested"]+=1
    return {"status":"accepted"}

@app.get("/api/alerts")
def alerts(limit:int=100): return list_alerts(min(limit,500))

@app.get("/api/incidents")
def incidents(limit:int=100): return list_incidents(min(limit,500))

@app.patch("/api/incidents/{incident_id}")
def change_incident(incident_id:int,update:IncidentUpdate):
    if update.status not in {"open","investigating","contained","resolved"}: raise HTTPException(400,"Invalid status")
    update_incident(incident_id,update.status);return {"incident_id":incident_id,"status":update.status}

@app.post("/api/incidents/{incident_id}/respond")
def respond(incident_id:int,request:ResponseRequest):
    item=next((x for x in list_incidents(500) if x["incident_id"]==incident_id),None)
    if not item: raise HTTPException(404,"Incident not found")
    result=execute_response(request.action,"source_ip_from_alert");record_response(incident_id,result)
    metrics["responses_executed"]+=1
    return {"incident_id":incident_id,"result":result}
