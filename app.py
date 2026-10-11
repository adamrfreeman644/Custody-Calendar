from flask import Flask, jsonify, request, send_from_directory, Response
import os, sqlite3, csv, io
from datetime import datetime

APP_DIR=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.environ.get("DATA_DIR","/data")
DB_PATH=os.path.join(DATA_DIR,"custody.db")
os.makedirs(DATA_DIR, exist_ok=True)

app=Flask(__name__, static_folder="static")

VALID={"mum","mum-neg","dad-neg","dad"}

def db():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS overrides(
            date TEXT NOT NULL,
            period TEXT NOT NULL CHECK(period IN ('am','pm')),
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(date,period)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('dad_weekend_anchor','2026-09-12')")
        conn.commit()

init_db()

@app.get("/")
def index():
    return send_from_directory("static","index.html")

@app.get("/health")
def health():
    try:
        with db() as conn:
            conn.execute("SELECT 1").fetchone()
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),500

@app.get("/api/overrides")
def get_overrides():
    with db() as conn:
        rows=conn.execute("SELECT date,period,value FROM overrides ORDER BY date,period").fetchall()
    return jsonify([dict(r) for r in rows])

@app.put("/api/override")
def set_override():
    data=request.get_json(force=True)
    date=data.get("date","")
    period=data.get("period","")
    value=data.get("value","")
    try:
        datetime.strptime(date,"%Y-%m-%d")
    except ValueError:
        return jsonify({"error":"invalid date"}),400
    if period not in {"am","pm"} or value not in VALID:
        return jsonify({"error":"invalid period/value"}),400
    with db() as conn:
        conn.execute("""
          INSERT INTO overrides(date,period,value,updated_at)
          VALUES(?,?,?,CURRENT_TIMESTAMP)
          ON CONFLICT(date,period) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,(date,period,value))
        conn.commit()
    return jsonify({"ok":True})

@app.delete("/api/override")
def delete_override():
    data=request.get_json(force=True)
    with db() as conn:
        conn.execute("DELETE FROM overrides WHERE date=? AND period=?",(data.get("date"),data.get("period")))
        conn.commit()
    return jsonify({"ok":True})

@app.get("/api/export/<int:year>/<int:month>")
def export_month(year,month):
    if not 1 <= month <= 12:
        return jsonify({"error":"invalid month"}),400
    from calendar import monthrange
    rows=[["date","am","pm"]]
    with db() as conn:
        vals={(r["date"],r["period"]):r["value"] for r in conn.execute("SELECT date,period,value FROM overrides")}
    for d in range(1,monthrange(year,month)[1]+1):
        date=f"{year:04d}-{month:02d}-{d:02d}"
        rows.append([date,vals.get((date,"am"),""),vals.get((date,"pm"),"")])
    s=io.StringIO()
    w=csv.writer(s)
    w.writerows(rows)
    return Response(s.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f'attachment; filename="custody-schedule-{year:04d}-{month:02d}.csv"'})

@app.post("/api/import")
def import_csv():
    if "file" not in request.files:
        return jsonify({"error":"missing file"}),400
    text=request.files["file"].read().decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text))
    count=0
    with db() as conn:
        for row in reader:
            date=(row.get("date") or "").strip()
            for period in ("am","pm"):
                value=(row.get(period) or "").strip().lower()
                if value in VALID:
                    conn.execute("""
                      INSERT INTO overrides(date,period,value,updated_at)
                      VALUES(?,?,?,CURRENT_TIMESTAMP)
                      ON CONFLICT(date,period) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                    """,(date,period,value))
                    count+=1
        conn.commit()
    return jsonify({"ok":True,"imported":count})

@app.get("/api/backup")
def backup_db():
    return send_from_directory(DATA_DIR,"custody.db",as_attachment=True,download_name="custody.db")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)
