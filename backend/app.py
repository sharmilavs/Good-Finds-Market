from datetime import datetime, timezone

from bson import ObjectId
from flask import Flask, g, jsonify, request
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

import config
import sessions
from db import init_mongo, mongo

app = Flask(__name__)
init_mongo()


def now():
    return datetime.now(timezone.utc)


def error(message, status=400):
    return jsonify({"error": message}), status


# --------------------------------------------------------------------------
# Session handling: every request gets a session (guest until they log in).
# --------------------------------------------------------------------------
@app.before_request
def load_session():
    g.session = sessions.get(request.cookies.get(config.COOKIE_NAME)) or sessions.create()


@app.after_request
def set_session_cookie(resp):
    sess = getattr(g, "session", None)
    if sess:
        resp.set_cookie(
            config.COOKIE_NAME,
            str(sess["id"]),
            max_age=config.SESSION_TTL,
            httponly=True,
            samesite="Lax",
            secure=config.COOKIE_SECURE,
        )
    return resp


def cart_key(sess=None):
    sess = sess or g.session
    return f"user:{sess['user_id']}" if sess["user_id"] else f"guest:{sess['id']}"


# --------------------------------------------------------------------------
# Cart helpers (MongoDB). The cart stores only product_id + qty; names and
# prices are always read from the products collection so clients can't tamper.
# --------------------------------------------------------------------------
def add_to_cart(key, product_id, qty):
    updated = mongo.carts.update_one(
        {"_id": key, "items.product_id": product_id},
        {"$inc": {"items.$.qty": qty}, "$set": {"updated_at": now()}},
    )
    if updated.matched_count == 0:
        mongo.carts.update_one(
            {"_id": key},
            {
                "$push": {"items": {"product_id": product_id, "qty": qty}},
                "$set": {"updated_at": now()},
            },
            upsert=True,
        )


def hydrate_cart(key):
    cart = mongo.carts.find_one({"_id": key}) or {"items": []}
    ids = [i["product_id"] for i in cart["items"]]
    products = {p["_id"]: p for p in mongo.products.find({"_id": {"$in": ids}})}
    items, total = [], 0
    for i in cart["items"]:
        p = products.get(i["product_id"])
        if not p:
            continue
        line_total = p["price_cents"] * i["qty"]
        total += line_total
        items.append(
            {
                "product_id": p["_id"],
                "name": p["name"],
                "price_cents": p["price_cents"],
                "qty": i["qty"],
                "line_total_cents": line_total,
                "tone": p.get("tone"),
            "category": p.get("category", "Accessories"),
            }
        )
    return {"items": items, "total_cents": total}


def parse_qty(value, minimum=1):
    try:
        qty = int(value)
    except (TypeError, ValueError):
        return None
    return qty if minimum <= qty <= 99 else None


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
def start_user_session(user_id):
    """Rotate the session id on login (prevents fixation) and merge the guest cart."""
    old = g.session
    old_key = cart_key(old)
    sessions.destroy(old)
    g.session = sessions.create(user_id=user_id)

    guest = mongo.carts.find_one_and_delete({"_id": old_key})
    for item in (guest or {}).get("items", []):
        add_to_cart(cart_key(), item["product_id"], item["qty"])


def credentials():
    body = request.get_json(silent=True) or {}
    return (body.get("email") or "").strip().lower(), body.get("password") or ""


@app.post("/api/register")
def register():
    email, password = credentials()
    if "@" not in email or len(password) < 8:
        return error("Enter a valid email and a password of at least 8 characters.")
    try:
        result = mongo.users.insert_one(
            {
                "email": email,
                "password_hash": generate_password_hash(password),
                "created_at": now(),
            }
        )
    except DuplicateKeyError:
        return error("An account with this email already exists.", 409)
    start_user_session(str(result.inserted_id))
    return jsonify({"user": {"email": email}}), 201


@app.post("/api/login")
def login():
    email, password = credentials()
    user = mongo.users.find_one({"email": email})
    if not user or not check_password_hash(user["password_hash"], password):
        return error("Email or password is incorrect.", 401)
    start_user_session(str(user["_id"]))
    return jsonify({"user": {"email": email}})


@app.post("/api/logout")
def logout():
    sessions.destroy(g.session)
    g.session = sessions.create()  # fresh guest session
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    uid = g.session["user_id"]
    user = mongo.users.find_one({"_id": ObjectId(uid)}) if uid else None
    return jsonify({"user": {"email": user["email"]} if user else None})


# --------------------------------------------------------------------------
# Catalog + cart
# --------------------------------------------------------------------------
@app.get("/api/products")
def list_products():
    products = [
        {
            "id": p["_id"],
            "name": p["name"],
            "description": p.get("description", ""),
            "price_cents": p["price_cents"],
            "stock": p["stock"],
            "tone": p.get("tone"),
            "category": p.get("category", "Accessories"),
        }
        for p in mongo.products.find().sort("name", 1)
    ]
    return jsonify({"products": products})


@app.get("/api/cart")
def get_cart():
    return jsonify(hydrate_cart(cart_key()))


@app.post("/api/cart/items")
def add_item():
    body = request.get_json(silent=True) or {}
    product_id, qty = body.get("product_id"), parse_qty(body.get("qty", 1))
    if qty is None:
        return error("Quantity must be between 1 and 99.")
    if not mongo.products.find_one({"_id": product_id}, {"_id": 1}):
        return error("Product not found.", 404)
    add_to_cart(cart_key(), product_id, qty)
    return jsonify(hydrate_cart(cart_key()))


@app.patch("/api/cart/items/<product_id>")
def update_item(product_id):
    body = request.get_json(silent=True) or {}
    qty = parse_qty(body.get("qty"), minimum=0)
    if qty is None:
        return error("Quantity must be between 0 and 99.")
    if qty == 0:
        return remove_item(product_id)
    mongo.carts.update_one(
        {"_id": cart_key(), "items.product_id": product_id},
        {"$set": {"items.$.qty": qty, "updated_at": now()}},
    )
    return jsonify(hydrate_cart(cart_key()))


@app.delete("/api/cart/items/<product_id>")
def remove_item(product_id):
    mongo.carts.update_one(
        {"_id": cart_key()},
        {"$pull": {"items": {"product_id": product_id}}, "$set": {"updated_at": now()}},
    )
    return jsonify(hydrate_cart(cart_key()))


# --------------------------------------------------------------------------
# Checkout: reserve stock atomically per product, roll back if any line fails.
# --------------------------------------------------------------------------
@app.post("/api/checkout")
def checkout():
    if not g.session["user_id"]:
        return error("Log in to check out.", 401)

    # Validate the delivery address BEFORE reserving stock. This prevents
    # inventory from being changed when the address form is incomplete.
    body = request.get_json(silent=True) or {}
    address = body.get("delivery_address") or {}
    required = ("full_name", "phone", "address_line", "city", "state", "postal_code")
    cleaned_address = {field: str(address.get(field, "")).strip() for field in required}
    if any(not cleaned_address[field] for field in required):
        return error("Please complete all delivery address fields before placing your order.")
    if not cleaned_address["phone"].isdigit() or len(cleaned_address["phone"]) != 10:
        return error("Enter a valid 10-digit phone number.")
    if not cleaned_address["postal_code"].isdigit() or len(cleaned_address["postal_code"]) != 6:
        return error("Enter a valid 6-digit PIN code.")

    key = cart_key()
    cart = mongo.carts.find_one({"_id": key})
    if not cart or not cart.get("items"):
        return error("Your cart is empty.")

    reserved, lines, total = [], [], 0
    for item in cart["items"]:
        product = mongo.products.find_one_and_update(
            {"_id": item["product_id"], "stock": {"$gte": item["qty"]}},
            {"$inc": {"stock": -item["qty"]}},
            return_document=ReturnDocument.BEFORE,
        )
        if product is None:
            for pid, qty in reserved:
                mongo.products.update_one({"_id": pid}, {"$inc": {"stock": qty}})
            return error("An item in your cart is out of stock. Your cart has not been cleared.", 409)
        reserved.append((item["product_id"], item["qty"]))
        line_total = product["price_cents"] * item["qty"]
        total += line_total
        lines.append({
            "product_id": product["_id"],
            "name": product["name"],
            "price_cents": product["price_cents"],
            "qty": item["qty"],
            "line_total_cents": line_total,
        })

    order = {
        "user_id": g.session["user_id"],
        "items": lines,
        "total_cents": total,
        "delivery_address": cleaned_address,
        "created_at": now(),
    }
    try:
        result = mongo.orders.insert_one(order)
    except Exception:
        # Restore reserved stock if saving the order fails.
        for pid, qty in reserved:
            mongo.products.update_one({"_id": pid}, {"$inc": {"stock": qty}})
        raise

    mongo.carts.delete_one({"_id": key})
    return jsonify({"order_id": str(result.inserted_id), "total_cents": total, "delivery_address": cleaned_address}), 201


@app.get("/api/orders")
def list_orders():
    uid = g.session["user_id"]
    if not uid:
        return jsonify({"orders": []})
    orders = [
        {
            "id": str(o["_id"]),
            "items": o["items"],
            "total_cents": o["total_cents"],
            "created_at": o["created_at"].isoformat(),
            "delivery_address": o.get("delivery_address", {}),
        }
        for o in mongo.orders.find({"user_id": uid}).sort("created_at", -1).limit(20)
    ]
    return jsonify({"orders": orders})


@app.post("/api/logout-everywhere")
def logout_everywhere():
    if g.session["user_id"]:
        sessions.destroy_all_for_user(g.session["user_id"])
    g.session = sessions.create()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=5000, debug=True, use_reloader=False)
