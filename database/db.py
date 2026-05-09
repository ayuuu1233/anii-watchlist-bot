import sqlite3
from config import DB_PATH

# ─────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─────────────────────────────────────────────
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        first_name  TEXT,
        joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS watchlist (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        anime_id     INTEGER NOT NULL,           -- AniList ID
        title        TEXT    NOT NULL,
        title_romaji TEXT,
        cover_url    TEXT,
        total_eps    INTEGER DEFAULT 0,
        status       TEXT    DEFAULT 'plan',     -- watching/completed/on_hold/dropped/plan
        progress     INTEGER DEFAULT 0,          -- episodes watched
        score        REAL    DEFAULT 0,          -- user rating 1-10
        notes        TEXT    DEFAULT '',
        added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, anime_id)
    );

    CREATE TABLE IF NOT EXISTS reminders (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        anime_id   INTEGER NOT NULL,
        title      TEXT    NOT NULL,
        remind_at  TIMESTAMP NOT NULL,
        sent       INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS user_states (
        user_id  INTEGER PRIMARY KEY,
        state    TEXT,
        data     TEXT
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")

# ─────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────
def upsert_user(user_id, username, first_name):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?,?,?)",
        (user_id, username, first_name)
    )
    conn.commit(); conn.close()

# ─────────────────────────────────────────────
#  WATCHLIST CRUD
# ─────────────────────────────────────────────
def add_anime(user_id, anime_id, title, title_romaji, cover_url, total_eps, status="plan"):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO watchlist
              (user_id, anime_id, title, title_romaji, cover_url, total_eps, status)
            VALUES (?,?,?,?,?,?,?)
        """, (user_id, anime_id, title, title_romaji, cover_url, total_eps, status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False          # already in list
    finally:
        conn.close()

def remove_anime(user_id, anime_id):
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM watchlist WHERE user_id=? AND anime_id=?", (user_id, anime_id)
    )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0

def get_watchlist(user_id, status_filter=None):
    conn = get_conn()
    if status_filter:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id=? AND status=? ORDER BY updated_at DESC",
            (user_id, status_filter)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return rows

def get_anime_entry(user_id, anime_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM watchlist WHERE user_id=? AND anime_id=?", (user_id, anime_id)
    ).fetchone()
    conn.close()
    return row

def update_status(user_id, anime_id, status):
    conn = get_conn()
    conn.execute("""
        UPDATE watchlist SET status=?, updated_at=CURRENT_TIMESTAMP
        WHERE user_id=? AND anime_id=?
    """, (status, user_id, anime_id))
    conn.commit(); conn.close()

def update_progress(user_id, anime_id, progress, score=None):
    conn = get_conn()
    if score is not None:
        conn.execute("""
            UPDATE watchlist
            SET progress=?, score=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=? AND anime_id=?
        """, (progress, score, user_id, anime_id))
    else:
        conn.execute("""
            UPDATE watchlist
            SET progress=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=? AND anime_id=?
        """, (progress, user_id, anime_id))
    conn.commit(); conn.close()

def get_user_stats(user_id):
    conn = get_conn()
    stats = {}
    for status in ["watching","completed","on_hold","dropped","plan"]:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM watchlist WHERE user_id=? AND status=?",
            (user_id, status)
        ).fetchone()
        stats[status] = row["cnt"]
    ep_row = conn.execute(
        "SELECT SUM(progress) as total FROM watchlist WHERE user_id=?", (user_id,)
    ).fetchone()
    stats["total_episodes"] = ep_row["total"] or 0
    stats["total_anime"]    = sum(stats[s] for s in ["watching","completed","on_hold","dropped","plan"])
    conn.close()
    return stats

def get_top_rated(user_id, limit=10):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM watchlist WHERE user_id=? AND score > 0
        ORDER BY score DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return rows

# ─────────────────────────────────────────────
#  REMINDERS
# ─────────────────────────────────────────────
def add_reminder(user_id, anime_id, title, remind_at):
    conn = get_conn()
    conn.execute(
        "INSERT INTO reminders (user_id, anime_id, title, remind_at) VALUES (?,?,?,?)",
        (user_id, anime_id, title, remind_at)
    )
    conn.commit(); conn.close()

def get_due_reminders():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM reminders
        WHERE sent=0 AND remind_at <= CURRENT_TIMESTAMP
    """).fetchall()
    conn.close()
    return rows

def mark_reminder_sent(reminder_id):
    conn = get_conn()
    conn.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
    conn.commit(); conn.close()

def get_user_reminders(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM reminders WHERE user_id=? AND sent=0 ORDER BY remind_at
    """, (user_id,)).fetchall()
    conn.close()
    return rows

def delete_reminder(reminder_id, user_id):
    conn = get_conn()
    conn.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (reminder_id, user_id))
    conn.commit(); conn.close()

# ─────────────────────────────────────────────
#  USER STATE (for multi-step flows)
# ─────────────────────────────────────────────
def set_state(user_id, state, data=""):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_states (user_id, state, data) VALUES (?,?,?)",
        (user_id, state, data)
    )
    conn.commit(); conn.close()

def get_state(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT state, data FROM user_states WHERE user_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return row

def clear_state(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM user_states WHERE user_id=?", (user_id,))
    conn.commit(); conn.close()
