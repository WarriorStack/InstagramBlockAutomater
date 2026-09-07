import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "instagram.db"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        con.commit()

def add_users(usernames):
    now = datetime.now().isoformat(timespec="seconds")
    added = 0
    with connect() as con:
        for username in usernames:
            u = username.strip().lstrip("@").strip().lower()
            if not u:
                continue
            try:
                con.execute(
                    "INSERT INTO users(username,status,created_at,updated_at) VALUES(?,?,?,?)",
                    (u, "Pending", now, now)
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
        con.commit()
    return added

def get_users(search=""):
    with connect() as con:
        if search:
            return con.execute(
                "SELECT * FROM users WHERE username LIKE ? ORDER BY username",
                (f"%{search.lower()}%",)
            ).fetchall()
        return con.execute("SELECT * FROM users ORDER BY username").fetchall()

def set_status(user_id, status):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        con.execute(
            "UPDATE users SET status=?, updated_at=? WHERE id=?",
            (status, now, user_id)
        )
        con.commit()

def stats():
    with connect() as con:
        rows = con.execute(
            "SELECT status, COUNT(*) AS n FROM users GROUP BY status"
        ).fetchall()
    d = {"Pending":0, "Blocked":0, "Skipped":0}
    for r in rows:
        d[r["status"]] = r["n"]
    d["Total"] = sum(d.values())
    return d
