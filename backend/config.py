import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "shop")

CASSANDRA_HOSTS = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "shop_sessions")

COOKIE_NAME = "sid"
SESSION_TTL = int(os.getenv("SESSION_TTL", "1800"))       # 30 min, sliding
GUEST_CART_TTL = int(os.getenv("GUEST_CART_TTL", str(7 * 24 * 3600)))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"    # set to 1 behind HTTPS
