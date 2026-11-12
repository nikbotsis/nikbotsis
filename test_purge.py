import sqlite3
from contextlib import closing

import app as site

OLD = "Τεστ Παλιό"
NEW = "Τεστ Νέο"


def add(name, phone, days):
    with closing(sqlite3.connect(site.DB_PATH)) as conn, conn:
        conn.execute(
            "INSERT INTO customers (name, phone, service, message, created_at) "
            "VALUES (?, ?, 'leak', '', datetime('now', ?))",
            (name, phone, f"-{days} days"),
        )


def count(name):
    with closing(sqlite3.connect(site.DB_PATH)) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM customers WHERE name = ?", (name,)
        ).fetchone()[0]


def check(label, condition):
    print(("OK     " if condition else "ΛΑΘΟΣ  ") + "| " + label)


# Τεστ 1: άμεση διαγραφή
add(OLD, "6900000099", 400)
add(NEW, "6900000098", 2)
site.purge_old_requests()
check("Το παλιό αίτημα (400 ημερών) διαγράφηκε", count(OLD) == 0)
check("Το πρόσφατο αίτημα (2 ημερών) έμεινε", count(NEW) == 1)

# Τεστ 2: αυτόματη διαγραφή όταν έρθει επισκέπτης
add(OLD, "6900000099", 400)
site._last_purge = 0
site.app.test_client().get("/")
check("Αυτόματη διαγραφή με την άφιξη επισκέπτη", count(OLD) == 0)

# Τεστ 3: δεν ξανατρέχει πριν περάσει ένα 24ωρο
add(OLD, "6900000099", 400)
site.app.test_client().get("/")
check("Δεν ξανατρέχει αμέσως (μία φορά την ημέρα)", count(OLD) == 1)

with closing(sqlite3.connect(site.DB_PATH)) as conn, conn:
    conn.execute("DELETE FROM customers WHERE name IN (?, ?)", (OLD, NEW))
print("Καθαρισμός ολοκληρώθηκε")