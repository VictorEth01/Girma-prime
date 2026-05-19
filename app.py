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
                "Elevating your decorative posts",
                50000.0,
                "Pots",
                "/static/images/karfi stand.jpg"
            ),
            (
                "The \"Wadata\" Stand- Hausa word for Affluence",
                "24cm cylindrical Raffia basket on 40cm 1/2 metal pipe stand with a natural jute finish. The woven basket conceals plastic nursery planters, while the sturdy stand adds a touch of industrial chic.",
                "Conceals plastic planters, adds natural earthy ambience to your space",
                16000.0,
                "Pots",
                "/static/images/watada stand.jpg"
            ),
            (
                "The 'Lightweight'concrete Fibre pot",
                "Large, minimalist cylindrical planter featuring a smooth matte finish. Designed with clean, seamless vertical lines to anchor modern contemporary interiors.",
                "Perfect for large indoor botanicals and statement corners",
                20000.0,
                "Pots",
                "/static/images/light weight concrete Fibre pot.jpg"
            ),

            # ── Flowers ───────────────────────────────────────────────────────
           (
            "Aglaonema (Chinese Evergreen)",
            "Striking variegated leaves with a lush, bushy growth habit. Incredibly resilient and perfect for beginners.",
            "Low-light indoor spaces",
            14000.0,
            "Flowers",
            "/static/images/Aglaonema plant.jpg"
        ),
        (
            "Alocasia Amazonica",
            "Dramatic, dark green leaves with striking white veins and scalloped edges. A true tropical statement piece.",
            "High-humidity statement decor",
            18000.0,
            "Flowers",
            "/static/images/Alocasia Amazonica.jpg"
        ),
        (
            "Sweet Basil",
            "Highly aromatic, vibrant green leaves. Essential for culinary gardens and providing a fresh, herbal home scent.",
            "Culinary herb & natural fragrance",
            5000.0,
            "Flowers",
            "/static/images/Basil.jpg"
        ),
        (
            "Classic Jade Plant",
            "A beautiful succulent with thick, woody stems and glossy green, fleshy leaves. Symbolizes growth and renewal.",
            "Drought-tolerant desk decor",
            25000.0,
            "Flowers",
            "/static/images/Big jade plant .jpg"
        ),
        (
            "Potted Celery Plant",
            "Lush, bright green foliage with a crisp, earthy fragrance. A beautiful and functional addition to a kitchen garden.",
            "Edible foliage & kitchen decor",
            5000.0,
            "Flowers",
            "/static/images/Celery plant.jpg"
        ),
        (
            "Red Cordyline (Ti Plant)",
            "Stunning architectural plant featuring sword-like leaves with vibrant streaks of pink, burgundy, and deep red.",
            "Adding a pop of color to neutral spaces",
            16000.0,
            "Flowers",
            "/static/images/Cordyline.jpg"
        ),
        (
            "Dwarf Dieffenbachia",
            "Compact, broad-leafed beauty displaying spectacular contrasting patterns of cream, yellow, and deep green.",
            "Brightening shaded corners",
            15000.0,
            "Flowers",
            "/static/images/Dwarf Dieffenbachia.jpg"
        ),
        (
            "Dwarf Sansevieria",
            "A compact, bird's-nest variety of the classic Snake Plant. Virtually indestructible and an excellent air purifier.",
            "Bedside tables and low-light areas",
            10000.0,
            "Flowers",
            "/static/images/Dwarf sansevieria plant.jpg"
        ),
        (
            "Echeveria Rosette",
            "A mathematically perfect rosette of pastel-green, fleshy succulent leaves. Thrives on neglect and bright sun.",
            "Windowsills and dry terrariums",
            10000.0,
            "Flowers",
            "/static/images/Echeveria plant.jpg"
        ),
        (
            "Fiddle Leaf Fig",
            "The ultimate interior design staple. Features massive, violin-shaped leaves with heavy veining and an upright habit.",
            "Living room statement piece",
            30000.0,
            "Flowers",
            "/static/images/Fiddle leaf Fig.jpg"
        ),
        (
            "Fittonia (Nerve Plant)",
            "Intricate, web-like venation across small, vibrant green leaves. Creates a beautiful, dense mat of foliage.",
            "Terrariums and humid environments",
            14000.0,
            "Flowers",
            "/static/images/Fittonia.jpg"
        ),
        (
            "Foxtail Fern",
            "Plumes of soft, needle-like leaves that resemble a fox's tail. Adds incredible texture and a vibrant, bright green hue.",
            "Textural contrast in mixed displays",
            35000.0,
            "Flowers",
            "/static/images/Foxtail fern.jpg"
        ),
        (
            "Hoya (Wax Plant)",
            "Thick, waxy trailing leaves that can produce stunning, star-shaped porcelain flowers under the right conditions.",
            "Hanging baskets and high shelves",
            14000.0,
            "Flowers",
            "/static/images/Hoya plant.jpg"
        ),
        (
            "Fresh Mint",
            "Vigorous, sprawling herb with deeply veined leaves and an unmistakable, refreshing aroma.",
            "Culinary use and patio decor",
            5000.0,
            "Flowers",
            "/static/images/Mint.jpg"
        ),
        (
            "Mondo Grass",
            "Sleek, dark green, grass-like foliage that grows in tight, neat clumps. Perfect for a minimalist, modern aesthetic.",
            "Border planting and modern pots",
            40000.0,
            "Flowers",
            "/static/images/Mondo grass.jpg"
        ),
        (
            "Pachira (Money Tree)",
            "Features a signature braided trunk topped with palmate, bright green leaves. Said to bring positive energy and fortune.",
            "Home offices and entryways",
            20000.0,
            "Flowers",
            "/static/images/Money tree.jpg"
        ),
        (
            "Monstera Siltepecana",
            "A rare, beautiful trailing aroid featuring silvery-green lance-shaped leaves with deep green veining.",
            "Trailing off shelves or climbing moss poles",
            14000.0,
            "Flowers",
            "/static/images/monstera siltepecana.jpg"
        ),
        (
            "Cuban Oregano",
            "Thick, fuzzy, succulent-like leaves with a potent, savory herbal scent. Extremely easy to care for.",
            "Aromatic kitchen decor",
            5000.0,
            "Flowers",
            "/static/images/oregano.jpg"
        ),
        (
            "Parlor Palm",
            "Elegant, arching fronds that bring a soft, tropical feel to any room. Highly adaptable to typical indoor conditions.",
            "Softening harsh architectural lines",
            40000.0,
            "Flowers",
            "/static/images/parlor palm.jpg"
        ),
        (
            "Peace Lily",
            "Deep green, glossy foliage producing elegant white spathe flowers. Renowned for its superior air-purifying qualities.",
            "Low-light spaces and bedrooms",
            15000.0,
            "Flowers",
            "/static/images/Peace Lily.jpg"
        ),
        (
            "Philodendron Erubescens",
            "A robust climbing plant with large, arrow-shaped green leaves and striking red stems.",
            "Vertical height in corners",
            14000.0,
            "Flowers",
            "/static/images/Philodendron Erubescens.jpg"
        ),
       
        (
            "Purple Anthurium",
            "A rare variant of the classic flamingo flower, featuring a stunning, deep violet-purple spathe.",
            "Premium exotic gift or centerpiece",
            28000.0,
            "Flowers",
            "/static/images/purple anthurium.jpg"
        ),
        (
            "Red Anthurium",
            "Features glossy, heart-shaped green leaves and brilliant, waxy red blooms that last for months.",
            "High-contrast tropical decor",
            35000.0,
            "Flowers",
            "/static/images/Red Anthurium.jpg"
        ),
        (
            "Potted Rosemary",
            "Woody, evergreen herb with needle-like leaves and a powerful, piney fragrance. Needs bright, direct sunlight.",
            "Sunny windowsills and culinary use",
            5000.0,
            "Flowers",
            "/static/images/Rosemary.jpg"
        ),
        (
            "Rubber Plant (Ficus Elastica)",
            "Thick, glossy, oversized dark green leaves with striking red central veins. A bold architectural houseplant.",
            "Modern minimalist interiors",
            25000.0,
            "Flowers",
            "/static/images/Rubber plant(Green).jpg"
        ),
        (
            "Sansevieria Cylindrica",
            "Striking, smooth, tubular spikes that grow vertically. The ultimate modern, structural, low-maintenance plant.",
            "Contemporary styling and tight spaces",
            18000.0,
            "Flowers",
            "/static/images/Sanseveria cylindrica.jpg"
        ),
        (
            "Silver Peperomia",
            "Deeply corrugated, heart-shaped leaves with a stunning metallic silver sheen and dark green veins.",
            "Desks and coffee table displays",
            15000.0,
            "Flowers",
            "/static/images/Silver pepperonia.jpg"
        ),
        (
            "Variegated Spider Plant",
            "Classic, resilient houseplant with arching green and white striped leaves. Excellent for beginners.",
            "Hanging baskets and air purification",
            13000.0,
            "Flowers",
            "/static/images/Spider plant.jpg"
        ),
        (
            "Fresh Thyme",
            "Tiny, aromatic leaves on delicate woody stems. A beautiful, creeping herb perfect for sunny spots.",
            "Culinary gardens and sunny patios",
            5000.0,
            "Flowers",
            "/static/images/Thyme.jpg"
        ),
        (
            "Zebra Calathea",
            "Incredible, velvety light green leaves with dark green stripes resembling a zebra. Leaves fold up at night.",
            "High-humidity indirect light spaces",
            16000.0,
            "Flowers",
            "/static/images/zebra calethea.jpg"
        ),
        (
            "Small ZZ Plant",
            "Graceful, wand-like stems with fleshy, oval-shaped glossy leaves. Tolerates extreme neglect and low light.",
            "Windowless offices and dark corners",
            15000.0,
            "Flowers",
            "/static/images/ZZ plant.jpg"
        ),
    
        




            # ── Accessories ──────────────────────────────────────────────────
            (
            "The 'Tsayi' Cross-Base Stand",
            "A sleek, mid-century modern black metal stand featuring a minimalist X-frame design. Built to elevate your favorite indoor planters. (Note: Stand only, pot and plant not included).",
            "Elevating medium to large floor planters",
            15000.0,
            "Accessories",
            "/static/images/Tall cross stand.jpg"
        
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