import sqlite3
from config import DB_FILE

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()


def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        telegram_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        link TEXT UNIQUE,
        type TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
