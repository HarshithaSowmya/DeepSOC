"""SQLite persistence shared by the API and Kafka worker."""
from contextlib import contextmanager
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone
from .config import DB_PATH

ALERT_KEYS=['alert_id','timestamp','source_ip','anomaly_score','severity','reason','event','status']
INCIDENT_KEYS=['incident_id','alert_id','created_at','status','response_action']

@contextmanager
def connect():
    con=sqlite3.connect(DB_PATH,timeout=30)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA busy_timeout=30000')
    try:
        with con:
            yield con
    finally:
        con.close()

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True,exist_ok=True)
    with connect() as con:
        con.execute('PRAGMA journal_mode=WAL')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS alerts(alert_id TEXT PRIMARY KEY,timestamp TEXT,source_ip TEXT,anomaly_score REAL,severity TEXT,reason TEXT,event_json TEXT,status TEXT);
        CREATE TABLE IF NOT EXISTS incidents(incident_id INTEGER PRIMARY KEY AUTOINCREMENT,alert_id TEXT,created_at TEXT,status TEXT,response_action TEXT);
        CREATE TABLE IF NOT EXISTS traffic(minute INTEGER PRIMARY KEY,events INTEGER DEFAULT 0,alerts INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS counters(name TEXT PRIMARY KEY,value INTEGER DEFAULT 0);
        CREATE INDEX IF NOT EXISTS alert_time ON alerts(timestamp DESC);
        CREATE INDEX IF NOT EXISTS incident_alert ON incidents(alert_id);
        ''')

def alert_dict(row):
    if row is None:return None
    a=dict(zip(ALERT_KEYS,list(row)))
    a['event']=json.loads(a['event'])
    return a

def save_alert(a):
    with connect() as con:
        con.execute('INSERT INTO alerts VALUES(?,?,?,?,?,?,?,?)',(a['alert_id'],a['timestamp'],a['source_ip'],a['anomaly_score'],a['severity'],a['reason'],json.dumps(a['event']),a['status']))

def persist_detection(alert=None):
    """Persist one processed event and its optional incident atomically."""
    minute=int(time.time()//60)*60
    with connect() as con:
        con.execute('INSERT INTO counters VALUES(?,1) ON CONFLICT(name) DO UPDATE SET value=value+1',('processed',))
        con.execute('INSERT INTO traffic VALUES(?,1,?) ON CONFLICT(minute) DO UPDATE SET events=events+1,alerts=alerts+excluded.alerts',(minute,int(alert is not None)))
        con.execute('DELETE FROM traffic WHERE minute<?',(minute-86400,))
        if alert:
            a=alert
            con.execute('INSERT INTO alerts VALUES(?,?,?,?,?,?,?,?)',(a['alert_id'],a['timestamp'],a['source_ip'],a['anomaly_score'],a['severity'],a['reason'],json.dumps(a['event']),a['status']))
            con.execute('INSERT INTO incidents(alert_id,created_at,status) VALUES(?,?,?)',(a['alert_id'],datetime.now(timezone.utc).isoformat(),'open'))

def list_alerts(limit=100):
    with connect() as con:return [alert_dict(r) for r in con.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?',(limit,))]

def get_alert(alert_id):
    with connect() as con:return alert_dict(con.execute('SELECT * FROM alerts WHERE alert_id=?',(alert_id,)).fetchone())

def get_incident(incident_id):
    with connect() as con:
        row=con.execute('SELECT * FROM incidents WHERE incident_id=?',(incident_id,)).fetchone()
        return dict(row) if row else None

def create_incident(alert_id):
    with connect() as con:return con.execute('INSERT INTO incidents(alert_id,created_at,status) VALUES(?,?,?)',(alert_id,datetime.now(timezone.utc).isoformat(),'open')).lastrowid

def list_incidents(limit=100):
    with connect() as con:return [dict(r) for r in con.execute('SELECT * FROM incidents ORDER BY incident_id DESC LIMIT ?',(limit,))]

def update_incident(incident_id,status):
    with connect() as con:
        cur=con.execute('UPDATE incidents SET status=? WHERE incident_id=?',(status,incident_id))
        con.execute('UPDATE alerts SET status=? WHERE alert_id=(SELECT alert_id FROM incidents WHERE incident_id=?)',(status,incident_id))
        return cur.rowcount>0

def record_response(incident_id,action):
    with connect() as con:
        con.execute("UPDATE incidents SET response_action=?,status='contained' WHERE incident_id=?",(action,incident_id))
        con.execute("UPDATE alerts SET status='contained' WHERE alert_id=(SELECT alert_id FROM incidents WHERE incident_id=?)",(incident_id,))
        con.execute("INSERT INTO counters VALUES('responses',1) ON CONFLICT(name) DO UPDATE SET value=value+1")

def dashboard_metrics():
    now=int(time.time()//60)*60
    with connect() as con:
        counters={r['name']:r['value'] for r in con.execute('SELECT * FROM counters')}
        severities={r[0]:r[1] for r in con.execute('SELECT severity,COUNT(*) FROM alerts GROUP BY severity')}
        counts=con.execute("SELECT COUNT(*),SUM(status IN ('open','investigating')),SUM(severity='critical' AND status IN ('open','investigating')) FROM alerts").fetchone()
        opened=con.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('open','investigating')").fetchone()[0]
        buckets={r['minute']:dict(r) for r in con.execute('SELECT * FROM traffic WHERE minute>=?',(now-29*60,))}
        activity=[buckets.get(t,{'minute':t,'events':0,'alerts':0}) for t in range(now-29*60,now+1,60)]
        # Counts for the current minute bucket, with the completed bucket included proportionally.
        fraction=(time.time()-now)/60
        rate=activity[-1]['events']+activity[-2]['events']*(1-fraction)
        return dict(logs_ingested=counters.get('processed',0),alerts_created=counts[0],incidents_created=con.execute('SELECT COUNT(*) FROM incidents').fetchone()[0],active_alerts=counts[1] or 0,critical_alerts=counts[2] or 0,open_incidents=opened,responses_executed=counters.get('responses',0),severity_counts=severities,activity=activity,events_last_minute=round(rate))
