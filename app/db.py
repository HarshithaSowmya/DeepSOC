import json
import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    con = connect()
    con.execute('''CREATE TABLE IF NOT EXISTS alerts (
        alert_id TEXT PRIMARY KEY, timestamp TEXT, source_ip TEXT,
        anomaly_score REAL, severity TEXT, reason TEXT,
        event_json TEXT, status TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS incidents (
        incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT, created_at TEXT, status TEXT, response_action TEXT)''')
    con.commit()
    con.close()

def save_alert(a):
    con = connect()
    con.execute("INSERT OR REPLACE INTO alerts VALUES (?,?,?,?,?,?,?,?)",
        (a["alert_id"], a["timestamp"], a["source_ip"], a["anomaly_score"],
         a["severity"], a["reason"], json.dumps(a["event"]), a["status"]))
    con.commit(); con.close()

def list_alerts(limit=100):
    con = connect()
    rows = con.execute(
        "SELECT alert_id,timestamp,source_ip,anomaly_score,severity,reason,event_json,status "
        "FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    keys = ["alert_id","timestamp","source_ip","anomaly_score","severity","reason","event","status"]
    return [dict(zip(keys, [*r[:6], json.loads(r[6]), r[7]])) for r in rows]

def create_incident(alert_id):
    con = connect()
    cur = con.execute(
        "INSERT INTO incidents(alert_id,created_at,status) VALUES(?,?,?)",
        (alert_id, datetime.now(timezone.utc).isoformat(), "open"))
    con.commit(); value = cur.lastrowid; con.close(); return value

def list_incidents(limit=100):
    con = connect()
    rows = con.execute(
        "SELECT incident_id,alert_id,created_at,status,response_action "
        "FROM incidents ORDER BY incident_id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    keys = ["incident_id","alert_id","created_at","status","response_action"]
    return [dict(zip(keys, r)) for r in rows]

def update_incident(incident_id, status):
    con = connect()
    con.execute("UPDATE incidents SET status=? WHERE incident_id=?", (status, incident_id))
    con.commit(); con.close()

def record_response(incident_id, action):
    con = connect()
    con.execute("UPDATE incidents SET response_action=?,status=? WHERE incident_id=?",
                (action, "contained", incident_id))
    con.commit(); con.close()
