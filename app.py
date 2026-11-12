import json
import hmac
import os
import re
import sqlite3
import threading
import time
from contextlib import closing
from functools import wraps

import requests
from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.getenv("CLIENT", "demo")
CLIENT_DIR = os.path.join(BASE_DIR, "clients", CLIENT)
DB_PATH = os.path.join(CLIENT_DIR, "customers.db")


def load_site_config():
    config_path = os.path.join(CLIENT_DIR, "config.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


SITE = load_site_config()
print(f"[CLIENT] {CLIENT} | PORT: {os.getenv('PORT', '5000')} | DB: {DB_PATH}")


@app.context_processor
def inject_site():
    return {"site": SITE}                                                                                   

SERVICE_LABELS = {s["key"]: s["title"] for s in SITE["services"]}
SERVICE_LABELS["other"] = "Άλλο"

STATUS_LABELS = {
    "new": "Νέο",
    "called": "Καλέστηκε",
    "done": "Ολοκληρώθηκε",
}

def check_admin(username, password):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        return False
    return hmac.compare_digest(
        username.encode(), b"admin"
    ) and hmac.compare_digest(password.encode(), admin_password.encode())


LOGIN_MAX_FAILS = 8
LOGIN_WINDOW = 10 * 60
_login_fails = {}


def login_blocked(ip):
    now = time.time()
    recent = [t for t in _login_fails.get(ip, []) if now - t < LOGIN_WINDOW]
    if recent:
        _login_fails[ip] = recent
    else:
        _login_fails.pop(ip, None)
    return len(recent) >= LOGIN_MAX_FAILS


def register_login_fail(ip):
    _login_fails.setdefault(ip, []).append(time.time())


def challenge():
    return Response(
        "Απαιτείται σύνδεση.",
        401,
        {"WWW-Authenticate": 'Basic realm="Admin"'},
    )


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        if login_blocked(ip):
            return Response(
                "Πολλές αποτυχημένες προσπάθειες. Δοκιμάστε ξανά σε λίγα λεπτά.",
                429,
                {"Retry-After": str(LOGIN_WINDOW)},
            )
        auth = request.authorization
        if not auth:
            return challenge()
        if not check_admin(auth.username or "", auth.password or ""):
            register_login_fail(ip)
            print("[ΑΣΦΑΛΕΙΑ] Αποτυχημένη προσπάθεια σύνδεσης στο admin")
            return challenge()
        _login_fails.pop(ip, None)
        return view(*args, **kwargs)

    return wrapped


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(customers)")]
        if "created_at" not in columns:
            conn.execute("ALTER TABLE customers ADD COLUMN created_at TEXT")
        if "status" not in columns:
            conn.execute("ALTER TABLE customers ADD COLUMN status TEXT DEFAULT 'new'")
        if "urgent" not in columns:
            conn.execute("ALTER TABLE customers ADD COLUMN urgent INTEGER DEFAULT 0")
FORM_MIN_SECONDS = 3
FORM_MAX_AGE = 6 * 60 * 60
MAX_PER_PHONE_PER_HOUR = 3
MAX_PER_HOUR = 40
LINK_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024

if app.secret_key == "change-me":
    print("[ΠΡΟΣΟΧΗ] Δεν έχει οριστεί SECRET_KEY. Βάλε μια τυχαία τιμή στο .bat")


def make_form_token():
    serializer = URLSafeTimedSerializer(app.secret_key, salt="contact-form")
    return serializer.dumps(time.time())


def read_form_token(token):
    serializer = URLSafeTimedSerializer(app.secret_key, salt="contact-form")
    try:
        return serializer.loads(token, max_age=FORM_MAX_AGE)
    except BadSignature:
        return None


def count_recent(conn, phone=None):
    if phone:
        return conn.execute(
            "SELECT COUNT(*) FROM customers "
            "WHERE phone = ? AND created_at >= datetime('now', '-1 hour')",
            (phone,),
        ).fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM customers "
        "WHERE created_at >= datetime('now', '-1 hour')"
    ).fetchone()[0]


def normalize_greek_mobile(raw):
    digits = re.sub(r"[\s\-\.\(\)]", "", raw)
    if digits.startswith("+30"):
        digits = digits[3:]
    elif digits.startswith("0030"):
        digits = digits[4:]
    if re.fullmatch(r"69[0-9]{8}", digits):
        return digits
    return None


def send_notification(name, phone, service, urgent):
    topic = os.getenv("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC is not set.")
        return
    service_label = SERVICE_LABELS.get(service, service)
    payload = {
        "topic": topic,
                "title": (
            f"ΕΠΕΙΓΟΝ αίτημα - {SITE['business_name']}"
            if urgent
            else f"Νέο αίτημα - {SITE['business_name']}"
        ),
        "message": f"Όνομα: {name}\nΤηλέφωνο: {phone}\nΥπηρεσία: {service_label}",
    }
    if urgent:
        payload["priority"] = 5
        payload["tags"] = ["rotating_light"]
    try:
        r = requests.post("https://ntfy.sh", json=payload, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print("Notification failed:", e)


PURGE_INTERVAL = 24 * 60 * 60
_last_purge = 0.0


def retention_months():
    try:
        return max(1, int(SITE.get("data_retention_months", 12)))
    except (TypeError, ValueError):
        return 12


def purge_old_requests():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        cursor = conn.execute(
            "DELETE FROM customers WHERE created_at IS NOT NULL "
            "AND created_at < datetime('now', ?)",
            (f"-{retention_months()} months",),
        )
        return cursor.rowcount


@app.before_request
def purge_if_due():
    global _last_purge
    if time.time() - _last_purge >= PURGE_INTERVAL:
        _last_purge = time.time()
        deleted = purge_old_requests()
        if deleted:
            print(f"[ΚΑΘΑΡΙΣΜΟΣ] Διαγράφηκαν {deleted} παλιά αιτήματα")


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        back = redirect(url_for("home", _anchor="contact"))

        # Στρώμα 1: κρυφό πεδίο-παγίδα (το συμπληρώνουν μόνο τα bots)
        if request.form.get("extra_field_2"):
            print("[SPAM] παγίδα")
            flash("Το αίτημά σας καταχωρήθηκε επιτυχώς!")
            return back

        # Στρώμα 2: υπογεγραμμένο token και χρόνος συμπλήρωσης
        issued = read_form_token(request.form.get("form_token", ""))
        if issued is None:
            print("[SPAM] άκυρο ή ληγμένο token")
            flash("Η σελίδα έληξε. Παρακαλούμε δοκιμάστε ξανά.")
            return back
        if time.time() - issued < FORM_MIN_SECONDS:
            print("[SPAM] πολύ γρήγορη αποστολή")
            flash("Παρακαλούμε δοκιμάστε ξανά.")
            return back

        name = (request.form.get("name") or "").strip()
        phone_raw = (request.form.get("phone") or "").strip()
        service = (request.form.get("service") or "").strip()
        message = (request.form.get("message") or "").strip()
        urgent = 1 if request.form.get("urgent") else 0

        if not (name and service in SERVICE_LABELS):
            flash("Συμπληρώστε όνομα και υπηρεσία.")
            return back

        # Στρώμα 3: μέγεθος και σύνδεσμοι
        if len(name) > 80 or len(message) > 1000:
            flash("Το κείμενο είναι πολύ μεγάλο. Παρακαλούμε συντομεύστε το.")
            return back
        if LINK_PATTERN.search(name) or LINK_PATTERN.search(message):
            print("[SPAM] σύνδεσμος στο κείμενο")
            flash("Παρακαλούμε μην συμπεριλαμβάνετε συνδέσμους στο αίτημά σας.")
            return back

        phone = normalize_greek_mobile(phone_raw)
        if not phone:
            flash("Γράψτε ένα έγκυρο ελληνικό κινητό τηλέφωνο, π.χ. 6912345678.")
            return back

        # Στρώμα 4: όρια στη βάση
        with closing(sqlite3.connect(DB_PATH)) as conn:
            too_many = (
                count_recent(conn, phone) >= MAX_PER_PHONE_PER_HOUR
                or count_recent(conn) >= MAX_PER_HOUR
            )
        if too_many:
            print("[SPAM] όριο αιτημάτων")
            flash(f"Έχουμε λάβει πολλά αιτήματα. Καλέστε μας στο {SITE.get('phone', '')}.")
            return back

        with closing(sqlite3.connect(DB_PATH)) as conn, conn:
            conn.execute(
                "INSERT INTO customers (name, phone, service, message, urgent, created_at) "
                "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (name, phone, service, message, urgent),
            )

        threading.Thread(
            target=send_notification, args=(name, phone, service, urgent), daemon=True
        ).start()

        flash("Το αίτημά σας καταχωρήθηκε επιτυχώς!")
        return back

    return render_template("index.html", form_token=make_form_token())


@app.route("/client-images/<filename>")
def client_image(filename):
    return send_from_directory(os.path.join(CLIENT_DIR, "images"), filename)


CSRF_MAX_AGE = 4 * 60 * 60


def make_csrf_token():
    return URLSafeTimedSerializer(app.secret_key, salt="admin-csrf").dumps("admin")


def csrf_ok(token):
    try:
        URLSafeTimedSerializer(app.secret_key, salt="admin-csrf").loads(
            token, max_age=CSRF_MAX_AGE
        )
        return True
    except BadSignature:
        return False


def csrf_error():
    return Response(
        "Η σελίδα έληξε ή το αίτημα δεν είναι έγκυρο. "
        "Ανανεώστε το /admin και δοκιμάστε ξανά.",
        400,
    )


@app.after_request
def protect_admin_pages(response):
    if request.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.route("/admin")
@require_admin
def admin():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, phone, service, message, status, urgent, "
            "datetime(created_at, 'localtime') AS created_at "
            "FROM customers ORDER BY id DESC"
        ).fetchall()
    return render_template(
        "admin.html",
        customers=rows,
        service_labels=SERVICE_LABELS,
        status_labels=STATUS_LABELS,
        csrf_token=make_csrf_token(),
    )


@app.route("/admin/status/<int:customer_id>", methods=["POST"])
@require_admin
def update_status(customer_id):
    if not csrf_ok(request.form.get("csrf", "")):
        return csrf_error()
    status = request.form.get("status", "")
    if status in STATUS_LABELS:
        with closing(sqlite3.connect(DB_PATH)) as conn, conn:
            conn.execute(
                "UPDATE customers SET status = ? WHERE id = ?",
                (status, customer_id),
            )
    return redirect(url_for("admin", _anchor=f"request-{customer_id}"))


@app.route("/admin/delete/<int:customer_id>", methods=["POST"])
@require_admin
def delete_request(customer_id):
    if not csrf_ok(request.form.get("csrf", "")):
        return csrf_error()
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    print(f"[ADMIN] Διαγράφηκε το αίτημα #{customer_id}")
    return redirect(url_for("admin"))

init_db()

if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG") == "1",
        port=int(os.getenv("PORT", "5000")),
    )