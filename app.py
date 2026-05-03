import os
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash, g
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# ─────────────────────────────────────────────
# App & Config
# ─────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gp-dev-secret-2025-xK9#mP2$")

DATABASE = os.path.join(os.path.dirname(__file__), "girma_prime.db")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the admin dashboard."
login_manager.login_message_category = "warning"

# ─────────────────────────────────────────────
# Hardcoded Admin Credentials (MVP)
# ─────────────────────────────────────────────

ADMIN_USERNAME = "girma_admin"
ADMIN_PASSWORD_HASH = generate_password_hash("GirmaPrime2025!")


# ─────────────────────────────────────────────
# Flask-Login User Model
# ─────────────────────────────────────────────

class AdminUser(UserMixin):
    def __init__(self):
        self.id = "admin"
        self.username = ADMIN_USERNAME


@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser()
    return None


# ─────────────────────────────────────────────
# Database Utilities
# ─────────────────────────────────────────────

def get_db():
    """Opens a new DB connection if one doesn't exist for the current context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Creates tables and seeds sample data on first run."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT    NOT NULL,
            use         TEXT    NOT NULL,
            price       REAL    NOT NULL,
            category    TEXT    NOT NULL CHECK(category IN ('Flowers','Pots','Accessories')),
            image_url   TEXT    NOT NULL
        )
    """)

    # Orders table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name    TEXT    NOT NULL,
            whatsapp_number  TEXT    NOT NULL,
            delivery_address TEXT    NOT NULL,
            delivery_date    TEXT    NOT NULL,
            cart_items       TEXT    NOT NULL,   -- JSON blob
            total            REAL    NOT NULL,
            status           TEXT    NOT NULL DEFAULT 'Pending',
            created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Seed only if products table is empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        seed_products = [
            # ── Pots ──────────────────────────────────────────────────────────
            (
                "The 'Karfi' Stand",
                "30cm × 30cm lightweight concrete fibre decorative pot stand, "
                "hand-finished with a matte stone texture. Built to bear weight "
                "while staying effortlessly elegant in any space.",
                "Elevating your decorative pots",
                50000.0,
                "Pots",
                "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=600&q=80"
            ),
            (
                "The 'Zuwa' Terracotta Vessel",
                "Handcrafted 20cm terracotta pot with a raw, earthy glaze finish. "
                "Breathable walls promote healthy root systems. Drainage hole included.",
                "Indoor statement planting — succulents, herbs, and trailing vines",
                28000.0,
                "Pots",
                "https://images.unsplash.com/photo-1604762524889-3e2fcc145683?w=600&q=80"
            ),
            (
                "The 'Raha' Glazed Cylinder",
                "Swahili for 'peace'. A 25cm tall glazed ceramic cylinder in "
                "muted sage — wheel-thrown, kiln-fired, and signed by the artisan.",
                "A calm centrepiece for living rooms and entryways",
                42000.0,
                "Pots",
                "https://images.unsplash.com/photo-1612015498838-b5e2b0f12dc9?w=600&q=80"
            ),

            # ── Flowers ───────────────────────────────────────────────────────
            (
                "Preserved Ivory Rose Bouquet",
                "Twelve long-stemmed ivory roses, ethically preserved via the "
                "glycerine method. Maintains softness and colour for 1–3 years "
                "with zero maintenance.",
                "Permanent table arrangements, gifts, and memorials",
                75000.0,
                "Flowers",
                "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=600&q=80"
            ),
            (
                "Dried Pampas Grass Bundle",
                "Sustainably harvested pampas grass, bleached to a warm cream. "
                "Sold in bundles of five 80cm stems, ready for vase styling.",
                "Boho and minimalist interior styling",
                22000.0,
                "Flowers",
                "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=600&q=80"
            ),
            (
                "Tropical Bird of Paradise",
                "Strelitzia reginae — a live, nursery-grown Bird of Paradise plant "
                "in a 30cm grow pot. Ships with care card and first-feed fertiliser.",
                "Dramatic indoor statement and bright outdoor patios",
                65000.0,
                "Flowers",
                "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80"
            ),

            # ── Accessories ───────────────────────────────────────────────────
            (
                "Premium Organic Potting Mix (5L)",
                "A blend of coco coir, perlite, and slow-release nutrients. "
                "pH balanced for tropical and subtropical houseplants. No synthetic "
                "fertilisers. Compostable bag.",
                "Repotting, propagation, and new plantings",
                8500.0,
                "Accessories",
                "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80"
            ),
            (
                "Brass Watering Can — 1.5L",
                "Hand-hammered solid brass with a long-spout precision nozzle. "
                "Develops a natural patina over time. Holds 1.5 litres.",
                "Precision watering of indoor plants and seedlings",
                38000.0,
                "Accessories",
                "https://images.unsplash.com/photo-1585320806297-9794b3e4aaae?w=600&q=80"
            ),
            (
                "Misting Bottle — Amber Glass",
                "200ml amber borosilicate glass misting bottle with a fine-mist "
                "brass pump head. Protects water from UV degradation. Dishwasher safe.",
                "Humidity-loving plants: ferns, calathea, orchids",
                12500.0,
                "Accessories",
                "https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=600&q=80"
            ),
        ]

        cur.executemany(
            "INSERT INTO products (name, description, use, price, category, image_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            seed_products
        )

    db.commit()
    db.close()


# ─────────────────────────────────────────────
# Helper: Format currency
# ─────────────────────────────────────────────

def fmt_naira(amount: float) -> str:
    return f"₦{amount:,.0f}"


# ─────────────────────────────────────────────
# Public Routes — Storefront
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/products")
def api_products():
    """Returns all products as JSON. Optionally filter by ?category=Pots"""
    db = get_db()
    category = request.args.get("category", "").strip()

    if category and category != "All":
        rows = db.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY id",
            (category,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()

    products = [dict(row) for row in rows]
    return jsonify(products)


@app.route("/api/order", methods=["POST"])
def api_place_order():
    """Accepts checkout form data and writes an order to the DB."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

    required = ["customer_name", "whatsapp_number", "delivery_address",
                "delivery_date", "cart_items", "total"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Missing fields: {', '.join(missing)}"}), 422

    # Validate cart is a non-empty list
    cart = data["cart_items"]
    if not isinstance(cart, list) or len(cart) == 0:
        return jsonify({"success": False, "error": "Cart is empty"}), 422

    # Validate and sanitise total
    try:
        total = float(data["total"])
        if total <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid total amount"}), 422

    # Sanitise WhatsApp number: strip non-digits, ensure it starts with country code
    raw_wa = str(data["whatsapp_number"]).strip()
    wa_digits = "".join(c for c in raw_wa if c.isdigit())
    if len(wa_digits) < 10:
        return jsonify({"success": False, "error": "Invalid WhatsApp number"}), 422
    # If Nigerian local format (starts with 0), convert to international
    if wa_digits.startswith("0"):
        wa_digits = "234" + wa_digits[1:]

    db = get_db()
    cur = db.execute(
        """INSERT INTO orders
           (customer_name, whatsapp_number, delivery_address, delivery_date,
            cart_items, total, status)
           VALUES (?, ?, ?, ?, ?, ?, 'Pending')""",
        (
            str(data["customer_name"]).strip(),
            wa_digits,
            str(data["delivery_address"]).strip(),
            str(data["delivery_date"]).strip(),
            json.dumps(cart),
            total,
        )
    )
    db.commit()
    order_id = cur.lastrowid

    return jsonify({
        "success": True,
        "order_id": order_id,
        "message": (
            f"Thank you, {data['customer_name'].split()[0]}! "
            f"Your order #{order_id} has been received. "
            f"We'll confirm via WhatsApp shortly."
        )
    }), 201


# ─────────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if (username == ADMIN_USERNAME and
                check_password_hash(ADMIN_PASSWORD_HASH, password)):
            user = AdminUser()
            login_user(user, remember=False)
            next_page = request.args.get("next") or url_for("admin")
            return redirect(next_page)
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────

@app.route("/admin")
@login_required
def admin():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC"
    ).fetchall()

    orders = []
    for row in rows:
        o = dict(row)
        # Parse cart JSON back to Python list for template access
        try:
            o["cart_items_parsed"] = json.loads(o["cart_items"])
        except (json.JSONDecodeError, TypeError):
            o["cart_items_parsed"] = []

        # Build WhatsApp deep-link with pre-filled message
        # Format delivery date for the message (keep as-is from DB)
        wa_message = (
            f"Hi {o['customer_name'].split()[0]}, thanks for your order of "
            f"{fmt_naira(o['total'])} from Girma Prime! "
            f"We are preparing your delivery for {o['delivery_date']}."
        )
        import urllib.parse
        o["wa_link"] = (
            f"https://wa.me/{o['whatsapp_number']}"
            f"?text={urllib.parse.quote(wa_message)}"
        )

        o["total_display"] = fmt_naira(o["total"])
        orders.append(o)

    # Summary stats
    total_orders = len(orders)
    total_revenue = sum(o["total"] for o in orders)
    pending_orders = sum(1 for o in orders if o["status"] == "Pending")

    return render_template(
        "admin.html",
        orders=orders,
        total_orders=total_orders,
        total_revenue=fmt_naira(total_revenue),
        pending_orders=pending_orders,
    )


@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    """AJAX endpoint to update an order's status."""
    data = request.get_json(silent=True)
    new_status = data.get("status") if data else None

    allowed_statuses = ["Pending", "Confirmed", "Out for Delivery", "Delivered", "Cancelled"]
    if new_status not in allowed_statuses:
        return jsonify({"success": False, "error": "Invalid status"}), 422

    db = get_db()
    db.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (new_status, order_id)
    )
    db.commit()
    return jsonify({"success": True, "status": new_status})


@app.route("/admin/order/<int:order_id>/delete", methods=["POST"])
@login_required
def delete_order(order_id):
    """Permanently removes an order record."""
    db = get_db()
    db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# Template filter: Naira formatting for Jinja
# ─────────────────────────────────────────────

@app.template_filter("naira")
def naira_filter(value):
    try:
        return fmt_naira(float(value))
    except (ValueError, TypeError):
        return value


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)