import base64
import os
import sqlite3
from contextlib import closing

os.environ["ADMIN_PASSWORD"] = "test-pass-123"
os.environ.pop("NTFY_TOPIC", None)

import app as site

NAME = "Τεστ Admin"
PASSWORD = "test-pass-123"


def auth(password):
    token = base64.b64encode(f"admin:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def check(label, condition):
    print(("OK     " if condition else "ΛΑΘΟΣ  ") + "| " + label)


def add_row():
    with closing(sqlite3.connect(site.DB_PATH)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, service, message, created_at) "
            "VALUES (?, '6900000097', 'leak', '', CURRENT_TIMESTAMP)",
            (NAME,),
        )
        return cursor.lastrowid


def status_of(row_id):
    with closing(sqlite3.connect(site.DB_PATH)) as conn:
        row = conn.execute(
            "SELECT status FROM customers WHERE id = ?", (row_id,)
        ).fetchone()
    return row[0] if row else None


client = site.app.test_client()
row = add_row()

check("Χωρίς κωδικό: 401", client.get("/admin").status_code == 401)
check("Λάθος κωδικός: 401", client.get("/admin", headers=auth("wrong")).status_code == 401)

page = client.get("/admin", headers=auth(PASSWORD))
check("Σωστός κωδικός: 200", page.status_code == 200)
check("Η σελίδα περιέχει csrf token", 'name="csrf"' in page.get_data(as_text=True))
check("Η σελίδα δεν αποθηκεύεται στην cache", page.headers.get("Cache-Control") == "no-store")

url = f"/admin/status/{row}"
r = client.post(url, data={"status": "done"}, headers=auth(PASSWORD))
check("Αλλαγή κατάστασης χωρίς csrf: 400", r.status_code == 400)
check("... και η κατάσταση δεν άλλαξε", status_of(row) != "done")
client.post(
    url, data={"status": "done", "csrf": site.make_csrf_token()}, headers=auth(PASSWORD)
)
check("Αλλαγή κατάστασης με csrf: αποθηκεύτηκε", status_of(row) == "done")

url = f"/admin/delete/{row}"
r = client.post(url, headers=auth(PASSWORD))
check(
    "Διαγραφή χωρίς csrf: 400 και το αίτημα μένει",
    r.status_code == 400 and status_of(row) is not None,
)
client.post(url, data={"csrf": site.make_csrf_token()}, headers=auth(PASSWORD))
check("Διαγραφή με csrf: το αίτημα διαγράφηκε", status_of(row) is None)

site._login_fails.clear()
for _ in range(site.LOGIN_MAX_FAILS):
    client.get("/admin", headers=auth("wrong"))
r = client.get("/admin", headers=auth(PASSWORD))
check(f"Μετά από {site.LOGIN_MAX_FAILS} λάθη: μπλοκάρει (429)", r.status_code == 429)
site._login_fails.clear()
check(
    "Μετά την άρση του μπλοκ δουλεύει ξανά",
    client.get("/admin", headers=auth(PASSWORD)).status_code == 200,
)

with closing(sqlite3.connect(site.DB_PATH)) as conn, conn:
    conn.execute("DELETE FROM customers WHERE name = ?", (NAME,))
print("Καθαρισμός ολοκληρώθηκε")