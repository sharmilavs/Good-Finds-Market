"""Session store on Cassandra. Rows expire automatically via TTL (sliding window)."""
import uuid
from datetime import datetime, timezone

import config
from db import cassandra

_insert = cassandra.prepare(
    "INSERT INTO sessions (session_id, user_id, created_at, last_seen) "
    "VALUES (?, ?, ?, ?) USING TTL ?"
)
_insert_by_user = cassandra.prepare(
    "INSERT INTO sessions_by_user (user_id, session_id) VALUES (?, ?) USING TTL ?"
)
_select = cassandra.prepare(
    "SELECT user_id, created_at FROM sessions WHERE session_id = ?"
)
_delete = cassandra.prepare("DELETE FROM sessions WHERE session_id = ?")
_delete_by_user = cassandra.prepare(
    "DELETE FROM sessions_by_user WHERE user_id = ? AND session_id = ?"
)
_list_by_user = cassandra.prepare(
    "SELECT session_id FROM sessions_by_user WHERE user_id = ?"
)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _write(sess):
    """Write the session row with a fresh TTL (this is what slides the expiry)."""
    cassandra.execute(
        _insert,
        [sess["id"], sess["user_id"] or "", sess["created_at"], _now(), config.SESSION_TTL],
    )
    if sess["user_id"]:
        cassandra.execute(
            _insert_by_user, [sess["user_id"], sess["id"], config.SESSION_TTL]
        )


def create(user_id=None):
    sess = {"id": uuid.uuid4(), "user_id": user_id, "created_at": _now()}
    _write(sess)
    return sess


def get(raw_id):
    try:
        sid = uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        return None
    row = cassandra.execute(_select, [sid]).one()
    if row is None:
        return None
    sess = {"id": sid, "user_id": row.user_id or None, "created_at": row.created_at}
    _write(sess)  # sliding expiry
    return sess


def destroy(sess):
    cassandra.execute(_delete, [sess["id"]])
    if sess["user_id"]:
        cassandra.execute(_delete_by_user, [sess["user_id"], sess["id"]])


def destroy_all_for_user(user_id):
    for row in cassandra.execute(_list_by_user, [user_id]):
        cassandra.execute(_delete, [row.session_id])
        cassandra.execute(_delete_by_user, [user_id, row.session_id])
