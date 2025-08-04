import os
import requests
import psycopg2
from datetime import datetime

# === Load Secrets from Environment Variables ===
supabase_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

manager_id = os.getenv("FPL_MANAGER_ID")
if not manager_id:
    raise ValueError("❌ Missing FPL_MANAGER_ID environment variable.")

# === Fetch Rank History from FPL API ===
url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/"
response = requests.get(url)

if response.status_code != 200:
    raise Exception(f"❌ Failed to fetch data from FPL API: HTTP {response.status_code}")

data = response.json()
current = data.get("current", [])

# === Handle pre-season (no gameweeks played yet) ===
if not current:
    print("🕒 No gameweeks played yet. Tracker waiting for GW1.")
    exit(0)

latest = current[-1]
rank_data = {
    "gw": latest["event"],
    "overall_rank": latest["overall_rank"],
    "points": latest["points"],
    "total_points": latest["total_points"],
    "timestamp": datetime.utcnow()
}

# === Insert into Supabase Database ===
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
    print(f"✅ GW{rank_data['gw']} rank data inserted successfully.")
finally:
    cur.close()
    conn.close()
