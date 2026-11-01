import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL, document TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL, plan_id TEXT NOT NULL,
                document TEXT NOT NULL, UNIQUE(session_id, plan_id)
            );
            CREATE TABLE IF NOT EXISTS requests (
                session_id TEXT NOT NULL, kind TEXT NOT NULL, created REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS request_window ON requests(kind, created);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def session(self, cookie, days):
        timestamp = time.time()
        if cookie and len(cookie) <= 100:
            session_id = hashlib.sha256(cookie.encode()).hexdigest()
            with self.connection() as db:
                row = db.execute("SELECT * FROM sessions WHERE id=? AND expires>?", (session_id, timestamp)).fetchone()
            if row:
                return dict(row), None
        token = secrets.token_urlsafe(32)
        session_id = hashlib.sha256(token.encode()).hexdigest()
        record = {"id": session_id, "csrf": secrets.token_urlsafe(32), "expires": timestamp + days * 86400}
        with self.connection() as db:
            db.execute("INSERT INTO sessions VALUES(?,?,?)", (record["id"], record["csrf"], record["expires"]))
            # Bounded privacy retention: remove expired browser-session data.
            expired = [row[0] for row in db.execute("SELECT id FROM sessions WHERE expires<=?", (timestamp,))]
            for expired_id in expired:
                for table in ("plans", "orders", "requests"):
                    db.execute("DELETE FROM " + table + " WHERE session_id=?", (expired_id,))
            db.execute("DELETE FROM sessions WHERE expires<=?", (timestamp,))
        return record, token

    def limit(self, session_id, kind, per_session, global_limit):
        timestamp = time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM requests WHERE created<?", (timestamp - 3600,))
            count = db.execute("SELECT COUNT(*) FROM requests WHERE kind=?", (kind,)).fetchone()[0]
            own = db.execute("SELECT COUNT(*) FROM requests WHERE kind=? AND session_id=?", (kind, session_id)).fetchone()[0]
            if count >= global_limit or own >= per_session:
                return False
            db.execute("INSERT INTO requests VALUES(?,?,?)", (session_id, kind, timestamp))
            return True

    def put_plan(self, session_id, plan):
        with self.connection() as db:
            db.execute("INSERT INTO plans VALUES(?,?,?)", (plan["id"], session_id, json.dumps(plan)))

    def get_plan(self, session_id, plan_id):
        with self.connection() as db:
            row = db.execute("SELECT document FROM plans WHERE session_id=? AND id=?", (session_id, plan_id)).fetchone()
            return json.loads(row[0]) if row else None

    def get_order(self, session_id, order_id):
        with self.connection() as db:
            row = db.execute("SELECT document FROM orders WHERE session_id=? AND id=?", (session_id, order_id)).fetchone()
            return json.loads(row[0]) if row else None

    def reserve_order(self, session_id, order):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT document FROM orders WHERE session_id=? AND plan_id=?", (session_id, order["plan_id"])).fetchone()
            if row:
                return json.loads(row[0])
            db.execute("INSERT INTO orders VALUES(?,?,?,?)", (order["id"], session_id, order["plan_id"], json.dumps(order)))
            return order

    def update_order(self, session_id, order, allow_restart=False):
        """Persist transitions atomically without a stale request undoing payment."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT document FROM orders WHERE session_id=? AND id=?", (session_id, order["id"])).fetchone()
            if not row:
                return None
            current = json.loads(row[0])
            before, after = current["status"], order["status"]
            if before in {"COMPLETED", "SIMULATED"}:
                return current
            if before == "PENDING" and after != "COMPLETED":
                return current
            if before == "CAPTURING" and after in {"CREATING", "CREATED", "APPROVED", "CANCELLED"}:
                return current
            if before == "CANCELLED" and after in {"CREATING", "CREATED", "APPROVED"} and not allow_restart:
                # A cancelled checkout can still finish its in-flight create call.
                # Retain the provider reference for reconciliation, not its stale status.
                order = dict(order, status="CANCELLED")
            db.execute("UPDATE orders SET document=? WHERE session_id=? AND id=?", (json.dumps(order), session_id, order["id"]))
            return order

    def orders(self, session_id):
        with self.connection() as db:
            rows = db.execute("SELECT document FROM orders WHERE session_id=? ORDER BY rowid DESC LIMIT 100", (session_id,)).fetchall()
            return [json.loads(row[0]) for row in rows]
