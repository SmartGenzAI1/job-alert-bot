from datetime import datetime
from .db import cur, conn


# ---------- USERS ----------

def add_user(uid, name):
    cur.execute(
        "INSERT OR IGNORE INTO users VALUES(?,?,?,?)",
        (uid, name, "jobs", datetime.utcnow())
    )
    conn.commit()


def set_category(uid, cat):
    cur.execute("UPDATE users SET category=? WHERE telegram_id=?", (cat, uid))
    conn.commit()


def get_users():
    return cur.execute("SELECT telegram_id, category FROM users").fetchall()


# ---------- JOBS ----------

def add_job(title, company, link, typ):
    try:
        cur.execute(
            "INSERT INTO jobs(title,company,link,type,created_at) VALUES(?,?,?,?,?)",
            (title, company, link, typ, datetime.utcnow())
        )
        conn.commit()
        return True
    except:
        return False


def get_latest_jobs(typ, limit=10):
    return cur.execute(
        "SELECT title,company,link FROM jobs WHERE type=? ORDER BY id DESC LIMIT ?",
        (typ, limit)
    ).fetchall()
