import json
import os
import re
import secrets
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENTS_DIR = os.path.join(BASE_DIR, "clients")
TEMPLATE = "demo"
SAMPLE_KEYS = ["gallery", "reviews", "reviews_sample", "google_reviews_url"]
GREEK_MONTHS = [
    "Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
    "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος",
]


def ask(question, default=None, validator=None, error="Μη έγκυρη τιμή, δοκιμάστε ξανά."):
    while True:
        suffix = f" [{default}]" if default is not None else ""
        answer = input(f"{question}{suffix}: ").strip()
        if not answer and default is not None:
            answer = str(default)
        if answer and (validator is None or validator(answer)):
            return answer
        print("  ->", error)


def valid_slug(value):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", value):
        return False
    folder_taken = os.path.exists(os.path.join(CLIENTS_DIR, value))
    bat_taken = os.path.exists(os.path.join(BASE_DIR, f"start_{value}.bat"))
    return not (folder_taken or bat_taken)


def normalize_phone(raw):
    digits = re.sub(r"[\s\-\.\(\)]", "", raw)
    if digits.startswith("+30"):
        digits = digits[3:]
    elif digits.startswith("0030"):
        digits = digits[4:]
    if re.fullmatch(r"(69[0-9]{8}|2[0-9]{9})", digits):
        return digits
    return None


def format_phone(digits):
    return f"+30 {digits[:3]} {digits[3:6]} {digits[6:]}"


def next_port():
    ports = [5000, 5001]
    for filename in os.listdir(BASE_DIR):
        lower = filename.lower()
        if lower.startswith("start") and lower.endswith(".bat"):
            path = os.path.join(BASE_DIR, filename)
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for match in re.finditer(
                r"^\s*set\s+PORT=(\d+)", text, re.IGNORECASE | re.MULTILINE
            ):
                ports.append(int(match.group(1)))
    return max(ports) + 1


def choose_services(services):
    print("\nΥπηρεσίες του προτύπου:")
    for number, service in enumerate(services, start=1):
        print(f"  {number}. {service['short']}  ({service['title']})")
    answer = input(
        "Ποιες κάνει ο υδραυλικός; Γράψτε αριθμούς με κόμμα (π.χ. 1,2,4) "
        "ή Enter για όλες: "
    ).strip()
    if not answer:
        return services
    try:
        picked = sorted({int(x) for x in answer.replace(" ", "").split(",") if x})
        chosen = [services[i - 1] for i in picked if 1 <= i <= len(services)]
    except ValueError:
        chosen = []
    if not chosen:
        print("  -> Δεν κατάλαβα την επιλογή, κρατάω όλες τις υπηρεσίες.")
        return services
    if len(chosen) not in (3, 6):
        print("  -> Σημείωση: με 3 ή 6 υπηρεσίες το πλέγμα φαίνεται πιο ισορροπημένο.")
    return chosen


def main():
    template_path = os.path.join(CLIENTS_DIR, TEMPLATE, "config.json")
    with open(template_path, encoding="utf-8") as f:
        config = json.load(f)

    print("=== Δημιουργία νέου πελάτη ===")
    print("Πατήστε Enter για να δεχτείτε την τιμή που φαίνεται σε [αγκύλες].\n")

    slug = ask(
        "Όνομα φακέλου (λατινικά πεζά, με παύλες, π.χ. nikos-ydravlikos)",
        validator=valid_slug,
        error="Μόνο λατινικά πεζά, αριθμοί και παύλες, και να μην υπάρχει ήδη.",
    )
    business_name = ask("Όνομα επιχείρησης όπως θα φαίνεται στο site (π.χ. Υδραυλικά Νίκου)")
    city = ask("Πόλη (μπαίνει στον τίτλο της σελίδας)")
    areas = [
        a.strip()
        for a in ask("Περιοχές που εξυπηρετεί, χωρισμένες με κόμμα").split(",")
        if a.strip()
    ]
    phone_digits = normalize_phone(
        ask(
            "Τηλέφωνο επικοινωνίας της επιχείρησης (κινητό ή σταθερό)",
            validator=lambda v: normalize_phone(v) is not None,
            error="Γράψτε έγκυρο ελληνικό αριθμό, 10 ψηφία (π.χ. 6912345678).",
        )
    )
    default_whatsapp = "ναι" if phone_digits.startswith("69") else "όχι"
    whatsapp = ask(
        "Έχει WhatsApp σε αυτόν τον αριθμό; (ναι/όχι)",
        default=default_whatsapp,
        validator=lambda v: v.lower() in ("ναι", "όχι", "nai", "oxi", "yes", "no"),
        error="Γράψτε ναι ή όχι.",
    ).lower() in ("ναι", "nai", "yes")
    legal_name = ask("Επωνυμία για την πολιτική απορρήτου (π.χ. Νίκος Παπαδόπουλος)")
    address = ask("Διεύθυνση της επιχείρησης")
    email = ask(
        "Email επικοινωνίας",
        validator=lambda v: re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v) is not None,
        error="Γράψτε ένα έγκυρο email.",
    )
    retention = int(
        ask(
            "Για πόσους μήνες διατηρούνται τα αιτήματα πριν διαγραφούν",
            default=12,
            validator=lambda v: v.isdigit() and 1 <= int(v) <= 60,
            error="Γράψτε αριθμό από 1 έως 60.",
        )
    )
    services = choose_services(config.get("services", []))
    port = ask(
        "Πόρτα για τοπική δοκιμή",
        default=next_port(),
        validator=lambda v: v.isdigit() and 1024 <= int(v) <= 65535,
        error="Γράψτε αριθμό από 1024 έως 65535.",
    )

    words = business_name.split()
    if len(words) >= 2:
        logo_main, logo_accent = words[0] + " ", " ".join(words[1:])
    else:
        logo_main, logo_accent = business_name, ""
    now = datetime.now()

    config.update(
        {
            "business_name": business_name,
            "logo_main": logo_main,
            "logo_accent": logo_accent,
            "city": city,
            "phone": format_phone(phone_digits),
            "whatsapp": whatsapp,
            "areas": areas,
            "services": services,
            "legal_name": legal_name,
            "address": address,
            "contact_email": email,
            "data_retention_months": retention,
            "privacy_updated": f"{GREEK_MONTHS[now.month - 1]} {now.year}",
            "privacy_draft": True,
        }
    )
    for key in SAMPLE_KEYS:
        config.pop(key, None)

    client_dir = os.path.join(CLIENTS_DIR, slug)
    os.makedirs(os.path.join(client_dir, "images"))
    with open(os.path.join(client_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    secret_key = secrets.token_hex(32)
    admin_password = secrets.token_urlsafe(14)
    ntfy_topic = f"{slug}-{secrets.token_urlsafe(16)}"
    bat = (
        "@echo off\n"
        'cd /d "%~dp0"\n'
        "call .venv\\Scripts\\activate\n"
        f"set CLIENT={slug}\n"
        f"set PORT={port}\n"
        f"set NTFY_TOPIC={ntfy_topic}\n"
        f"set SECRET_KEY={secret_key}\n"
        f"set ADMIN_PASSWORD={admin_password}\n"
        "set FLASK_DEBUG=1\n"
        "python app.py\n"
        "pause\n"
    )
    with open(os.path.join(BASE_DIR, f"start_{slug}.bat"), "w", encoding="utf-8") as f:
        f.write(bat)

    print("\n" + "=" * 62)
    print(f"ΕΤΟΙΜΟΣ ο πελάτης: {business_name}")
    print("=" * 62)
    print(f"Φάκελος            : clients\\{slug}")
    print(f"Αρχείο εκκίνησης   : start_{slug}.bat")
    print(f"Site (τοπικά)      : http://127.0.0.1:{port}")
    print(f"Πίνακας διαχείρισης: http://127.0.0.1:{port}/admin")
    print("   χρήστης         : admin")
    print(f"   κωδικός         : {admin_password}")
    print(f"Κανάλι ntfy (για το κινητό του υδραυλικού): {ntfy_topic}")
    print()
    print("Τα μυστικά αυτά υπάρχουν και μέσα στο start_" + slug + ".bat.")
    print("Μην το στείλεις σε κανέναν και μην το ανεβάσεις πουθενά.")
    print()
    print("Επόμενα βήματα:")
    print(f"  1. Διπλό κλικ στο start_{slug}.bat και άνοιγμα του site.")
    print("  2. Φωτογραφίες και κριτικές μπαίνουν ΜΟΝΟ όταν υπάρχουν πραγματικές.")
    print("  3. Η πολιτική απορρήτου είναι προσχέδιο: πρέπει να τη δει νομικός.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nΑκυρώθηκε. Δεν δημιουργήθηκε τίποτα.")