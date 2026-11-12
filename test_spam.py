import os
import sqlite3
import time
from contextlib import closing

from itsdangerous import URLSafeTimedSerializer

os.environ.pop("NTFY_TOPIC", None)  # να μη σταλούν πραγματικές ειδοποιήσεις

import app as site

TEST_NAME = "Τεστ Spam"


def count():
    with closing(sqlite3.connect(site.DB_PATH)) as conn:
        return conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]


def token(age_seconds):
    serializer = URLSafeTimedSerializer(site.app.secret_key, salt="contact-form")
    return serializer.dumps(time.time() - age_seconds)


def send(label, expect_saved, **overrides):
    data = {
        "name": TEST_NAME,
        "phone": "6900000001",
        "service": "leak",
        "message": "",
        "form_token": token(10),
    }
    data.update(overrides)
    before = count()
    site.app.test_client().post("/", data=data)
    saved = count() > before
    verdict = "OK   " if saved == expect_saved else "ΛΑΘΟΣ"
    print(f"{verdict} | {label} | αποθηκεύτηκε: {saved}")


send("Σωστό αίτημα", True)
send("Κρυφό πεδίο συμπληρωμένο (bot)", False, extra_field_2="http://spam.example")
send("Χωρίς token", False, form_token="")
send("Πειραγμένο token", False, form_token="abc.def.ghi")
send("Πολύ γρήγορη αποστολή (0 δευτ.)", False, form_token=token(0))
send("Σύνδεσμος στο μήνυμα", False, message="δείτε www.spam.gr", phone="6900000002")
send("Μη έγκυρο τηλέφωνο", False, phone="123")
send("Πολύ μεγάλο κείμενο", False, message="α" * 2000, phone="6900000003")
send("Ίδιο τηλέφωνο, 2η φορά", True)
send("Ίδιο τηλέφωνο, 3η φορά", True)
send("Ίδιο τηλέφωνο, 4η φορά (πάνω από το όριο)", False)

with closing(sqlite3.connect(site.DB_PATH)) as conn, conn:
    removed = conn.execute("DELETE FROM customers WHERE name = ?", (TEST_NAME,)).rowcount
print(f"Καθαρισμός: διαγράφηκαν {removed} δοκιμαστικά αιτήματα")