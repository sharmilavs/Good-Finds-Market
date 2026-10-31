# Good Finds Market: Online Shopping Cart + Session Management

React (Vite) + Flask + MongoDB + Cassandra

| Concern | Store | Why |
|---|---|---|
| Users, products, carts, orders | MongoDB | Flexible documents, atomic `$inc`/`$push`/`$pull`, TTL index cleans abandoned carts |
| Login sessions | Cassandra | Fast primary-key lookups, native `USING TTL` gives sliding expiry |

## Run it

```bash
# 1. databases (Cassandra needs ~30-60 s to be ready)
docker compose up -d

# 2. backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py          # loads sample products
python app.py           # http://localhost:5000

# 3. frontend (new terminal)
cd frontend
npm install
npm run dev             # http://localhost:5173
```

## How sessions work

1. Every request without a valid `sid` cookie gets a **guest session** stored in Cassandra (`sessions` table, 30 min TTL).
2. Each request rewrites the row with a fresh TTL, so the session expires only after 30 min of inactivity.
3. The guest cart lives in Mongo under `guest:<session_id>`.
4. On login/register the session id is **rotated** (prevents session fixation), `user_id` is attached, and the guest cart is **merged** into `user:<user_id>`.
5. Logout deletes the Cassandra row and issues a new guest session.
6. `sessions_by_user` lets you revoke every session for a user (`/api/logout-everywhere`).

## API

| Method | Path | Purpose |
|---|---|---|
| GET | /api/products | List catalog |
| POST | /api/register, /api/login, /api/logout | Auth |
| GET | /api/me | Current user (or null) |
| GET | /api/cart | Cart with server-side prices |
| POST | /api/cart/items | `{product_id, qty}` add |
| PATCH / DELETE | /api/cart/items/<id> | Change qty (0 removes) / remove |
| POST | /api/checkout | Reserve stock, create order, clear cart (login required) |
| GET | /api/orders | Order history |

## Before production
- Serve over HTTPS and set `COOKIE_SECURE=1`.
- Add CSRF protection (the cookie is `SameSite=Lax`, but add tokens for state-changing routes).
- Use `NetworkTopologyStrategy` and replication factor 3 in Cassandra.
- Rate-limit `/api/login`.
- Use a Mongo replica set and multi-document transactions for checkout instead of manual stock rollback.
