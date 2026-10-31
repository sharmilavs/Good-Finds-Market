"""Database connections.

MongoDB   -> users, products, carts, orders   (flexible documents, atomic $inc/$push)
Cassandra -> login sessions                   (fast key lookups, built-in TTL expiry)
"""
import time

from cassandra.cluster import Cluster
from pymongo import ASCENDING, DESCENDING, MongoClient

import config

mongo = MongoClient(config.MONGO_URI)[config.MONGO_DB]


def init_mongo():
    mongo.users.create_index([("email", ASCENDING)], unique=True)
    mongo.orders.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    # Abandoned carts clean themselves up.
    mongo.carts.create_index("updated_at", expireAfterSeconds=config.GUEST_CART_TTL)


def connect_cassandra(retries=30, delay=4):
    """Cassandra takes a while to boot in Docker, so retry."""
    last_error = None
    for _ in range(retries):
        try:
            cluster = Cluster(config.CASSANDRA_HOSTS, port=config.CASSANDRA_PORT)
            conn = cluster.connect()
            conn.execute(
                f"CREATE KEYSPACE IF NOT EXISTS {config.CASSANDRA_KEYSPACE} "
                "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}"
            )
            conn.set_keyspace(config.CASSANDRA_KEYSPACE)
            # Lookup by session id (every request).
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                       session_id uuid PRIMARY KEY,
                       user_id    text,
                       created_at timestamp,
                       last_seen  timestamp)"""
            )
            # Lookup by user (e.g. "log out everywhere").
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions_by_user (
                       user_id    text,
                       session_id uuid,
                       PRIMARY KEY ((user_id), session_id))"""
            )
            return conn
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(delay)
    raise RuntimeError("Could not connect to Cassandra") from last_error


cassandra = connect_cassandra()
