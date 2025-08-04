import requests
import psycopg2
from datetime import datetime

# === CONFIG ===
manager_id = "506374"  # Replace with your real FPL manager ID
supabase_config = psycopg2.connect(
    host="db.fjlznnsnizpydvasxmen.supabase.co",
    database="postgres",
    user="postgres",
    password="Sallins21*",
    port=5432
)
# === FETCH RANK HISTORY FROM FPL ===
url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/"
r = requests.get(url)

if r.status_code != 200:
    raise Exception(f"Failed to fetch FPL data: HTTP {r.status_code}")

data = r.json()
current = data.get("current", [])

if not current:
    print("🕒 No gameweeks have been played yet. Waiting for GW1.")
    exit(0)

latest = current[-1]

rank_data = {
    "gw": latest["event"],
    "overall_rank": latest["overall_rank"],
    "points": latest["points"],
    "total_points": latest["total_points"],
    "timestamp": datetime.utcnow()
}
# === INSERT INTO SUPABASE ===
try:
    conn = psycopg2.connect(**supabase_config)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO rank_tracker (gw, overall_rank, points, total_points, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (gw) DO UPDATE
        SET overall_rank = EXCLUDED.overall_rank,
            points = EXCLUDED.points,
            total_points = EXCLUDED.total_points,
            timestamp = EXCLUDED.timestamp
    """, (
        rank_data["gw"],
        rank_data["overall_rank"],
        rank_data["points"],
        rank_data["total_points"],
        rank_data["timestamp"]
    ))

    conn.commit()
    print(f"✅ Inserted GW{rank_data['gw']} data: {rank_data}")
finally:
    cur.close()
    conn.close()