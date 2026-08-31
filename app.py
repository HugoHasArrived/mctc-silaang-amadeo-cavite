import os
import html
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    abort,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mctc_court.db"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True


COURT_NAME = "Municipal Circuit Trial Court of Silang-Amadeo, Cavite"
COURT_ADDRESS = "PNP Bldg, Plaza Libertad, Poblacion 2, Silang, Cavite"
COURT_PHONE = "09284621305"
COURT_EMAIL = "mctc2sad000@judiciary.gov.ph"
LOGO_FILENAME = "image0.png"

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/?api=1&query="
    + quote_plus(COURT_NAME + ", " + COURT_ADDRESS)
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "txt",
}


TEXT = {
    "en": {
        "home": "Home",
        "about": "About Us",
        "news": "News and Announcements",
        "contact": "Contact Us",
        "staff_login": "Staff Login",
        "search": "Search Cases",
        "calendar": "Tuesday Calendar",
        "requirements": "Requirements",
        "laws": "Laws, Decisions and Rules",
        "dashboard": "Staff Dashboard",
        "logout": "Log Out",
        "login": "Log In",
        "cases": "Cases",
        "manage_cases": "Manage Cases",
        "manage_calendar": "Manage Tuesday Calendar",
        "manage_notices": "Manage Notices",
        "manage_laws": "Manage Legal Resources",
        "manage_requirements": "Manage Requirements",
        "staff_accounts": "Staff Accounts",
        "add_case": "Add Case",
        "edit_case": "Edit Case",
        "delete_case": "Delete Case",
        "add_staff": "Add Staff Account",
        "username": "Username",
        "password": "Password",
        "email": "Email Address",
        "role": "Role",
        "case_number": "Case Number",
        "last_name": "Last Name / Party Name",
        "parties": "Parties",
        "case_title": "Case Title",
        "case_type": "Case Type",
        "status": "Status",
        "description": "Description",
        "hearing_date": "Hearing Date",
        "hearing_time": "Hearing Time",
        "hearing_nature": "Nature of Hearing",
        "hearing_status": "Hearing Status",
        "courtroom": "Courtroom",
        "remarks": "Remarks",
        "save": "Save",
        "add": "Add",
        "edit": "Edit",
        "delete": "Delete",
        "cancel": "Cancel",
        "view": "View",
        "open": "Open",
        "upload": "Upload",
        "attachment": "Photo / Document",
        "phone": "Telephone",
        "address": "Address",
        "official_source": "Official Source",
        "open_maps": "Open Google Maps",
        "both_required": "Both the case number and last name / party name are required.",
        "no_results": "No matching public case was found.",
        "invalid_login": "Invalid username or password.",
        "login_required": "Please log in as authorized staff.",
        "welcome": "Welcome, Court Staff",
        "quick_actions": "Quick Actions",
        "how_search": "How to Search",
        "step_one": "Enter the complete case number.",
        "step_two": "Enter the last name of a party.",
        "step_three": "Both fields are required.",
        "step_four": "Click Search Case.",
        "not_uploaded": "Not yet uploaded",
        "copyright": "© 2026 Municipal Circuit Trial Court of Silang-Amadeo, Cavite. All rights reserved.",
    },
    "fil": {
        "home": "Home",
        "about": "Tungkol sa Amin",
        "news": "Balita at mga Anunsyo",
        "contact": "Makipag-ugnayan",
        "staff_login": "Staff Login",
        "search": "Maghanap ng Kaso",
        "calendar": "Kalendaryo ng Martes",
        "requirements": "Mga Kinakailangan",
        "laws": "Mga Batas, Desisyon at Alituntunin",
        "dashboard": "Dashboard ng Staff",
        "logout": "Mag-Logout",
        "login": "Mag-Login",
        "cases": "Mga Kaso",
        "manage_cases": "Pamahalaan ang mga Kaso",
        "manage_calendar": "Pamahalaan ang Kalendaryo ng Martes",
        "manage_notices": "Pamahalaan ang mga Abiso",
        "manage_laws": "Pamahalaan ang Legal Resources",
        "manage_requirements": "Pamahalaan ang mga Kinakailangan",
        "staff_accounts": "Mga Account ng Staff",
        "add_case": "Magdagdag ng Kaso",
        "edit_case": "I-edit ang Kaso",
        "delete_case": "Burahin ang Kaso",
        "add_staff": "Magdagdag ng Staff Account",
        "username": "Username",
        "password": "Password",
        "email": "Email Address",
        "role": "Role",
        "case_number": "Numero ng Kaso",
        "last_name": "Apelyido / Pangalan ng Partido",
        "parties": "Mga Partido",
        "case_title": "Pamagat ng Kaso",
        "case_type": "Uri ng Kaso",
        "status": "Katayuan",
        "description": "Deskripsyon",
        "hearing_date": "Petsa ng Pagdinig",
        "hearing_time": "Oras ng Pagdinig",
        "hearing_nature": "Uri ng Pagdinig",
        "hearing_status": "Katayuan ng Pagdinig",
        "courtroom": "Silid ng Hukuman",
        "remarks": "Mga Tala",
        "save": "I-save",
        "add": "Magdagdag",
        "edit": "I-edit",
        "delete": "Burahin",
        "cancel": "Kanselahin",
        "view": "Tingnan",
        "open": "Buksan",
        "upload": "Mag-upload",
        "attachment": "Larawan / Dokumento",
        "phone": "Telepono",
        "address": "Address",
        "official_source": "Opisyal na Source",
        "open_maps": "Buksan ang Google Maps",
        "both_required": "Kinakailangan ang parehong case number at apelyido / pangalan ng partido.",
        "no_results": "Walang nakitang pampublikong kaso.",
        "invalid_login": "Mali ang username o password.",
        "login_required": "Mag-login bilang awtorisadong staff.",
        "welcome": "Maligayang Pagdating, Kawani ng Hukuman",
        "quick_actions": "Mabilis na Aksyon",
        "how_search": "Paano Maghanap",
        "step_one": "Ilagay ang buong case number.",
        "step_two": "Ilagay ang apelyido ng isang partido.",
        "step_three": "Kinakailangan ang parehong field.",
        "step_four": "I-click ang Maghanap.",
        "not_uploaded": "Hindi pa naiu-upload",
        "copyright": "© 2026 Municipal Circuit Trial Court of Silang-Amadeo, Cavite. Lahat ng karapatan ay nakalaan.",
    },
}


REQUIREMENT_DETAILS = {
    "bond": [
        "PERSONAL DATA (form from court)",
        "PICTURES 2x2 with name tag, signature, case, case number and date",
        "4 pcs. Front",
        "4 pcs. Left side",
        "4 pcs. Right side",
        "BARANGAY CLEARANCE attesting the Real Name of the accused and bonafide resident",
        "CERTIFICATION (Permanent Residency) attesting how many years of stay",
        "HOUSE SKETCH - certified, signed and sealed by Barangay Captain with date",
        "CERTIFICATE OF DETENTION (if detained or arrested)",
        "AFFIDAVIT OF VOLUNTARY SURRENDER (if voluntary or not detained)",
        "FINGER PRINT (piano)",
        "SPECIMEN SIGNATURE (at least 5 signature)",
        "AFFIDAVIT OF UNDERTAKING",
        "VALID GOVERNMENT-ISSUED I.D. (original AND xerox copy back-to-back)",
        "ORIGINAL COPY OF PSA BIRTH CERTIFICATE (latest copy with attached receipt)",
        "If married, female - original copy of PSA MARRIAGE CERTIFICATE with attached receipt",
        "FOR INQUIRIES, kindly seek assistance from court staff.",
    ],
    "cash_bond": [
        "PERSONAL DATA",
        "PICTURES 2x2 with name tag, signature, case, case number and date",
        "4 pcs. Front",
        "4 pcs. Left side",
        "4 pcs. Right side",
        "BARANGAY CLEARANCE attesting the Real Name of the accused and bonafide resident",
        "CERTIFICATION (Permanent Residency) attesting how many year of stay",
        "HOUSE SKETCH - Certified, signed and seal by Brgy. Captain with date",
        "CERTIFICATE OF DETENTION (if detained or arrested)",
        "AFFIDAVIT OF VOLUNTARY SURRENDER (if voluntary or not detained)",
        "Finger Print (Piano)",
        "Specimen Signature at least 5 signature",
        "Affidavit of Undertaking",
        "Valid I.D (Government issued I.D) (Original and Xerox back to back)",
        "Original Copy of PSA Birth Certificate with attached receipt",
        "If married, female - original copy of PSA Marriage Certificate with attached receipt",
    ],
    "clearance": [],
}


def esc(value):
    return html.escape(str(value or ""), quote=True)


def lang():
    value = session.get("language", "en")
    return value if value in TEXT else "en"


def tr(key):
    return TEXT[lang()].get(key, key)


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def audit(action, target=""):
    try:
        connection = get_db()
        connection.execute(
            """
            INSERT INTO audit_logs
            (username, action, target, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session.get("staff_username", "system"),
                action,
                str(target),
                now(),
            ),
        )
        connection.commit()
        connection.close()
    except sqlite3.Error:
        pass


def save_upload(file):
    if file is None or not file.filename:
        return None, None

    original = secure_filename(file.filename)
    if not original:
        return None, None

    extension = Path(original).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("That file type is not allowed.")

    filename = secrets.token_hex(12) + "_" + original
    file.save(UPLOAD_DIR / filename)
    return filename, original


def staff_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("staff_logged_in", False):
            flash(tr("login_required"), "warning")
            return redirect(url_for("staff_login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("staff_logged_in", False):
            return redirect(url_for("staff_login"))
        if session.get("staff_role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def requirement_list(category):
    items = REQUIREMENT_DETAILS.get(category, [])
    if not items:
        return (
            "<p class='small'>"
            "The current checklist has not been uploaded. "
            "Please contact the court for the current official requirement."
            "</p>"
        )

    output = "<ol class='requirement-list'>"
    for item in items:
        output += f"<li>{esc(item)}</li>"
    output += "</ol>"
    return output


def init_db():
    connection = get_db()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            last_name TEXT NOT NULL,
            parties TEXT NOT NULL,
            case_title TEXT NOT NULL,
            case_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            public_description TEXT NOT NULL DEFAULT '',
            internal_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            hearing_date TEXT NOT NULL,
            hearing_time TEXT NOT NULL DEFAULT '',
            hearing_nature TEXT NOT NULL DEFAULT '',
            hearing_status TEXT NOT NULL DEFAULT 'Scheduled',
            courtroom TEXT NOT NULL DEFAULT '',
            remarks TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tuesday_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendar_date TEXT NOT NULL,
            calendar_time TEXT NOT NULL,
            case_number TEXT NOT NULL,
            last_name TEXT NOT NULL,
            parties TEXT NOT NULL,
            hearing_nature TEXT NOT NULL,
            hearing_status TEXT NOT NULL DEFAULT 'Scheduled',
            courtroom TEXT NOT NULL DEFAULT '',
            remarks TEXT NOT NULL DEFAULT '',
            public_visible INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_en TEXT NOT NULL,
            title_fil TEXT NOT NULL,
            body_en TEXT NOT NULL,
            body_fil TEXT NOT NULL,
            attachment TEXT,
            original_filename TEXT,
            published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS legal_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            file_name TEXT,
            original_filename TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            title_en TEXT NOT NULL,
            title_fil TEXT NOT NULL,
            description_en TEXT NOT NULL DEFAULT '',
            description_fil TEXT NOT NULL DEFAULT '',
            file_name TEXT,
            original_filename TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )

    defaults = [
        (
            "bond",
            "Requirements for Posting Bail Bond",
            "Mga Kinakailangan para sa Posting Bail Bond",
        ),
        (
            "cash_bond",
            "Requirements for Cash Bond",
            "Mga Kinakailangan para sa Cash Bond",
        ),
        (
            "clearance",
            "Requirements for Clearance",
            "Mga Kinakailangan para sa Clearance",
        ),
    ]

    for category, title_en, title_fil in defaults:
        row = connection.execute(
            "SELECT id FROM requirements WHERE category = ?",
            (category,),
        ).fetchone()

        if row is None:
            connection.execute(
                """
                INSERT INTO requirements
                (
                    category,
                    title_en,
                    title_fil,
                    description_en,
                    description_fil,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    category,
                    title_en,
                    title_fil,
                    "Not yet uploaded",
                    "Hindi pa naiu-upload",
                    now(),
                ),
            )

    admin = connection.execute(
        "SELECT id FROM staff WHERE username = 'admin'"
    ).fetchone()

    if admin is None:
        connection.execute(
            """
            INSERT INTO staff
            (
                username,
                email,
                password_hash,
                role,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "admin",
                COURT_EMAIL,
                generate_password_hash("admin123"),
                "admin",
                1,
                now(),
            ),
        )

    connection.commit()
    connection.close()


init_db()


STYLE = """
:root {
    --bg: #faf8fc;
    --surface: #ffffff;
    --surface2: #f1e9f7;
    --text: #24152c;
    --muted: #6f6077;
    --border: #ddd0e5;
    --purple: #6d28d9;
    --purple2: #8b5cf6;
    --deep: #3b0764;
    --danger: #a61e40;
}

body.dark {
    --bg: #120e16;
    --surface: #211824;
    --surface2: #302139;
    --text: #fff8ff;
    --muted: #d0bfd9;
    --border: #513e5a;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
}

a {
    color: var(--purple);
    text-decoration: none;
}

body.dark a {
    color: #ccb3ff;
}

a:hover {
    text-decoration: underline;
}

.site-header {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: linear-gradient(
        135deg,
        var(--deep),
        var(--purple),
        var(--purple2)
    );
    color: white;
    box-shadow: 0 5px 20px rgba(40, 5, 55, .3);
}

.header-inner {
    width: 94%;
    max-width: 1280px;
    margin: auto;
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 10px 0;
}

.brand-link {
    display: flex;
    align-items: center;
    gap: 12px;
    color: white;
    flex: 1;
    min-width: 270px;
    text-decoration: none;
}

.brand-link:hover {
    text-decoration: none;
}

.logo {
    width: 60px;
    height: 60px;
    padding: 4px;
    object-fit: contain;
    background: white;
    border-radius: 50%;
    flex-shrink: 0;
}

.brand strong {
    display: block;
    font-size: 14px;
}

.brand small {
    opacity: .88;
}

.nav {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
    flex: 1;
}

.nav a,
.nav button {
    color: white;
    background: transparent;
    border: 0;
    padding: 8px 9px;
    border-radius: 9px;
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
}

.nav a:hover,
.nav button:hover {
    background: rgba(255,255,255,.14);
    text-decoration: none;
}

.nav-spacer {
    flex: 1 1 auto;
    min-width: 18px;
}

.container {
    width: 94%;
    max-width: 1180px;
    margin: auto;
    padding: 28px 0 70px;
}

.hero {
    padding: 52px 22px;
    margin: 15px 0 24px;
    border-radius: 25px;
    color: white;
    text-align: center;
    background: linear-gradient(
        135deg,
        var(--deep),
        var(--purple),
        var(--purple2)
    );
}

.hero-logo {
    width: 145px;
    height: 145px;
    object-fit: contain;
    background: white;
    padding: 5px;
    border-radius: 50%;
}

.hero h1 {
    max-width: 950px;
    margin: 15px auto;
    font-size: clamp(31px, 5vw, 56px);
    line-height: 1.05;
}

.grid {
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(250px, 1fr)
    );
    gap: 16px;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 22px;
    margin: 16px 0;
    box-shadow: 0 9px 25px rgba(60,20,80,.07);
}

.two {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}

label {
    display: block;
    font-weight: 800;
    margin: 10px 0 5px;
}

input,
textarea,
select {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text);
    font: inherit;
}

textarea {
    min-height: 110px;
    resize: vertical;
}

button,
.button {
    display: inline-block;
    padding: 10px 15px;
    border: 0;
    border-radius: 10px;
    background: var(--purple);
    color: white;
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
}

button:hover,
.button:hover {
    background: var(--deep);
    color: white;
    text-decoration: none;
}

.secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
}

.danger {
    background: var(--danger);
}

.actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
}

.notice {
    padding: 14px 16px;
    border-left: 5px solid var(--purple);
    border-radius: 10px;
    background: var(--surface2);
    margin: 12px 0;
}

.notice.warning {
    border-left-color: #d97706;
}

.notice.success {
    border-left-color: #15803d;
}

.notice.danger {
    border-left-color: #b91c1c;
}

.status {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--surface2);
    color: var(--purple);
    font-size: 12px;
    font-weight: 900;
}

.table-wrap {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 10px;
    text-align: left;
    vertical-align: top;
    border-bottom: 1px solid var(--border);
}

th {
    background: var(--surface2);
}

.empty {
    text-align: center;
    padding: 40px;
    color: var(--muted);
}

.small {
    font-size: 13px;
    color: var(--muted);
}

.stat {
    text-align: center;
}

.stat-number {
    display: block;
    font-size: 40px;
    color: var(--purple);
    font-weight: 900;
}

.requirement-list li {
    margin: 7px 0;
}

footer {
    border-top: 1px solid var(--border);
    background: var(--surface);
    color: var(--muted);
    text-align: center;
    padding: 30px 15px;
}

@media (max-width: 920px) {
    .header-inner {
        flex-direction: column;
        align-items: stretch;
    }

    .brand-link {
        width: 100%;
    }

    .nav {
        width: 100%;
    }

    .nav-spacer {
        display: none;
    }
}

@media (max-width: 700px) {
    .two {
        grid-template-columns: 1fr;
    }
}
"""


def render_flash():
    messages = []
    for category, message in __import__("flask").get_flashed_messages(with_categories=True):
        messages.append(
            "<div class='notice %s'>%s</div>"
            % (esc(category), esc(message))
        )
    return "".join(messages)


def page(title, content):
    theme = session.get("theme", "light")
    next_theme = "dark" if theme == "light" else "light"
    theme_icon = "🌙" if theme == "light" else "☀️"

    next_lang = "fil" if lang() == "en" else "en"
    lang_label = "FIL" if lang() == "en" else "EN"

    nav = ""

    nav += f"<a href='{url_for('home')}'>{tr('home')}</a>"
    nav += f"<a href='{url_for('search_cases')}'>{tr('search')}</a>"
    nav += f"<a href='{url_for('public_calendar')}'>{tr('calendar')}</a>"
    nav += f"<a href='{url_for('requirements')}'>{tr('requirements')}</a>"

    nav += "<span class='nav-spacer'></span>"

    nav += f"<a href='{url_for('about')}'>{tr('about')}</a>"
    nav += f"<a href='{url_for('news')}'>{tr('news')}</a>"
    nav += f"<a href='{url_for('contact')}'>{tr('contact')}</a>"

    if session.get("staff_logged_in", False):

        nav += (
            f"<a href='{url_for('staff_dashboard')}'>"
            f"{tr('dashboard')}</a>"
        )

        nav += (
            f"<a href='{url_for('staff_cases')}'>"
            f"{tr('cases')}</a>"
        )

        nav += (
            f"<a href='{url_for('staff_notices')}'>"
            f"{tr('news')}</a>"
        )

        if session.get("staff_role") == "admin":
            nav += (
                f"<a href='{url_for('staff_accounts')}'>"
                f"{tr('staff_accounts')}</a>"
            )

        nav += (
            f"<form method='post' action='{url_for('logout')}' "
            f"style='display:inline'>"
            f"<button class='nav-button' type='submit'>"
            f"{tr('logout')}"
            f"</button>"
            f"</form>"
        )

    else:
        nav += (
            f"<a href='{url_for('staff_login')}'>"
            f"{tr('staff_login')}</a>"
        )

    nav += (
        f"<a href='{url_for('change_language', language=next_lang)}'>"
        f"{lang_label}</a>"
    )

    nav += (
        f"<a href='{url_for('change_theme', theme=next_theme)}'>"
        f"{theme_icon}</a>"
    )

    logo_url = url_for(
        "static",
        filename=LOGO_FILENAME,
    )

    return f"""<!DOCTYPE html>
<html lang="{esc(lang())}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="MCTC Silang-Amadeo Court Information Portal">
<title>{esc(title)} - {esc(COURT_NAME)}</title>
<style>{STYLE}</style>
</head>
<body class="{esc(theme)}">

<header class="site-header">
<div class="header-inner">

<a class="brand-link" href="{url_for('home')}">
<img class="logo" src="{logo_url}" alt="Official court logo">
<div class="brand">
<strong>{esc(COURT_NAME)}</strong>
<small>Official Court Information Portal</small>
</div>
</a>

<nav class="nav">
{nav}
</nav>

</div>
</header>

<main class="container">
{render_flash()}
{content}
</main>

<footer>

<strong>{esc(COURT_NAME)}</strong>

<p>{esc(COURT_ADDRESS)}</p>

<p>
<a href="tel:{esc(COURT_PHONE)}">
{esc(COURT_PHONE)}
</a>
<br>
<a href="mailto:{esc(COURT_EMAIL)}">
{esc(COURT_EMAIL)}
</a>
</p>

<p>
<a href="{GOOGLE_MAPS_URL}"
target="_blank"
rel="noopener noreferrer">
🗺️ {tr('open_maps')}
</a>
</p>

<p>{tr('copyright')}</p>

</footer>

</body>
</html>"""


# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.route("/")
def home():
    connection = get_db()
    notices = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).fetchall()
    connection.close()

    notices_html = ""

    for notice in notices:
        if lang() == "fil":
            title = notice["title_fil"]
            text = notice["body_fil"]
        else:
            title = notice["title_en"]
            text = notice["body_en"]

        attachment = ""

        if notice["attachment"]:
            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=notice['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        notices_html += (
            f"<article class='notice'>"
            f"<h3>{esc(title)}</h3>"
            f"<p>{esc(text)}</p>"
            f"{attachment}"
            f"</article>"
        )

    content = f"""
<section class="hero">

<img
    class="hero-logo"
    src="{url_for('static', filename=LOGO_FILENAME)}"
    alt="Court logo"
>

<h1>{esc(COURT_NAME)}</h1>

<p>
Search approved public case information,
view the Tuesday calendar, and read
court announcements.
</p>

<div class="actions" style="justify-content:center">

<a class="button"
href="{url_for('search_cases')}">
🔎 {tr('search')}
</a>

<a class="button secondary"
href="{url_for('public_calendar')}">
📅 {tr('calendar')}
</a>

<a class="button secondary"
href="{url_for('requirements')}">
📄 {tr('requirements')}
</a>

</div>

</section>


<section class="grid">

<div class="card">
<h2>🔎 {tr('search_cases')}</h2>
<p>
{tr('both_required')}
</p>
<a class="button"
href="{url_for('search_cases')}">
{tr('search')}
</a>
</div>

<div class="card">
<h2>📅 {tr('calendar')}</h2>
<p>
View the Tuesday court calendar
published by authorized staff.
</p>
<a class="button"
href="{url_for('public_calendar')}">
{tr('view')}
</a>
</div>

<div class="card">
<h2>📄 {tr('requirements')}</h2>
<p>
View posting bail bond,
cash bond and clearance information.
</p>
<a class="button"
href="{url_for('requirements')}">
{tr('view')}
</a>
</div>

<div class="card">
<h2>⚖️ {tr('laws')}</h2>
<p>
View published legal resources.
</p>
<a class="button"
href="{url_for('laws')}">
{tr('view')}
</a>
</div>

</section>


<section class="card">

<h2>📢 {tr('news')}</h2>

{notices_html or
"<p class='small'>No announcements yet.</p>"}

</section>
"""

    return page(
        tr("home"),
        content,
    )


@app.route("/about")
def about():
    content = f"""
<div class="card">

<h1>{tr('about')}</h1>

<h2>{esc(COURT_NAME)}</h2>

<p>
This portal provides approved public court
information, announcements, schedules,
requirements and legal-resource links.
</p>

<div class="notice warning">
<strong>Important</strong>
<p>
Online information does not replace official
court records, orders, notices or certified
documents.
</p>
</div>

</div>
"""
    return page(
        tr("about"),
        content,
    )


@app.route("/contact")
def contact():
    content = f"""
<div class="card">

<h1>{tr('contact')}</h1>

<h2>{esc(COURT_NAME)}</h2>

<p>
<strong>{tr('address')}:</strong><br>
{esc(COURT_ADDRESS)}
</p>

<p>
<strong>{tr('phone')}:</strong><br>
<a href="tel:{esc(COURT_PHONE)}">
{esc(COURT_PHONE)}
</a>
</p>

<p>
<strong>{tr('email')}:</strong><br>
<a href="mailto:{esc(COURT_EMAIL)}">
{esc(COURT_EMAIL)}
</a>
</p>

<a class="button"
href="{GOOGLE_MAPS_URL}"
target="_blank"
rel="noopener noreferrer">
🗺️ {tr('open_maps')}
</a>

</div>
"""
    return page(
        tr("contact"),
        content,
    )


@app.route("/news")
def news():
    connection = get_db()
    notices = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        """
    ).fetchall()
    connection.close()

    content = f"""
<div class="card">
<h1>📢 {tr('news')}</h1>
</div>
"""

    for notice in notices:
        if lang() == "fil":
            title = notice["title_fil"]
            text = notice["body_fil"]
        else:
            title = notice["title_en"]
            text = notice["body_en"]

        attachment = ""

        if notice["attachment"]:
            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=notice['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        content += (
            f"<div class='card'>"
            f"<h2>{esc(title)}</h2>"
            f"<p>{esc(text)}</p>"
            f"{attachment}"
            f"</div>"
        )

    if not notices:
        content += (
            "<div class='card empty'>"
            "No announcements have been published."
            "</div>"
        )

    return page(
        tr("news"),
        content,
    )


@app.route("/search", methods=["GET", "POST"])
def search_cases():
    case_number = request.values.get(
        "case_number",
        "",
    ).strip()

    last_name = request.values.get(
        "last_name",
        "",
    ).strip()

    result = None

    if request.method == "POST":
        if not case_number or not last_name:
            flash(
                tr("both_required"),
                "danger",
            )
        else:
            connection = get_db()
            result = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE lower(case_number) = lower(?)
                AND lower(last_name) = lower(?)
                LIMIT 1
                """,
                (
                    case_number,
                    last_name,
                ),
            ).fetchone()
            connection.close()

            if result is None:
                flash(
                    tr("no_results"),
                    "warning",
                )

    content = f"""
<div class="card">

<h1>🔎 {tr('search_cases')}</h1>

<div class="notice">

<h3>{tr('how_search')}</h3>

<ol>
<li>{tr('step_one')}</li>
<li>{tr('step_two')}</li>
<li>{tr('step_three')}</li>
<li>{tr('step_four')}</li>
</ol>

</div>

<form method="post">

<label>{tr('case_number')}</label>

<input
name="case_number"
value="{esc(case_number)}"
required
autocomplete="off"
>

<label>{tr('last_name')}</label>

<input
name="last_name"
value="{esc(last_name)}"
required
autocomplete="off"
>

<button type="submit">
🔎 {tr('search')}
</button>

</form>

</div>
"""

    if result:
        content += f"""
<div class="card">

<span class="status">
{esc(result['status'])}
</span>

<h2>
{esc(result['case_number'])}
</h2>

<p>
<strong>{tr('parties')}:</strong>
{esc(result['parties'])}
</p>

<p>
<strong>{tr('case_title')}:</strong>
{esc(result['case_title'])}
</p>

<p>
<strong>{tr('case_type')}:</strong>
{esc(result['case_type'])}
</p>

<a
class="button"
href="{url_for('public_case', case_id=result['id'])}">
{tr('view')}
</a>

</div>
"""

    return page(
        tr("search"),
        content,
    )


@app.route("/case/<int:case_id>")
def public_case(case_id):
    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    hearings = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY hearing_date, hearing_time
        """,
        (case_id,),
    ).fetchall()

    connection.close()

    if case is None:
        abort(404)

    hearings_html = ""

    for hearing in hearings:
        hearings_html += f"""
<div class="notice">

<h3>
{esc(hearing['hearing_date'])}
</h3>

<p>
<strong>{tr('hearing_time')}:</strong>
{esc(hearing['hearing_time'])}
</p>

<p>
<strong>{tr('hearing_nature')}:</strong>
{esc(hearing['hearing_nature'])}
</p>

<p>
<strong>{tr('hearing_status')}:</strong>
<span class="status">
{esc(hearing['hearing_status'])}
</span>
</p>

<p>
<strong>{tr('courtroom')}:</strong>
{esc(hearing['courtroom'])}
</p>

</div>
"""

    if not hearings_html:
        hearings_html = (
            "<p class='small'>"
            "No published hearing information."
            "</p>"
        )

    content = f"""
<div class="card">

<span class="status">
{esc(case['status'])}
</span>

<h1>
{esc(case['case_number'])}
</h1>

<h2>
{esc(case['case_title'])}
</h2>

<p>
<strong>{tr('parties')}:</strong>
{esc(case['parties'])}
</p>

<p>
<strong>{tr('case_type')}:</strong>
{esc(case['case_type'])}
</p>

<p>
{esc(case['public_description'])}
</p>

</div>


<div class="card">

<h2>📅 {tr('hearings')}</h2>

{hearings_html}

</div>
"""

    return page(
        tr("case"),
        content,
    )


@app.route("/calendar")
def public_calendar():
    connection = get_db()

    entries = connection.execute(
        """
        SELECT *
        FROM tuesday_calendar
        WHERE public_visible = 1
        ORDER BY calendar_date, calendar_time, id
        """
    ).fetchall()

    connection.close()

    rows = ""

    for entry in entries:
        rows += f"""
<tr>

<td>
{esc(entry['calendar_date'])}
</td>

<td>
{esc(entry['calendar_time'])}
</td>

<td>
{esc(entry['case_number'])}
</td>

<td>
{esc(entry['parties'])}
</td>

<td>
{esc(entry['hearing_nature'])}
</td>

<td>
{esc(entry['hearing_status'])}
</td>

<td>
{esc(entry['courtroom'])}
</td>

</tr>
"""

    if not rows:
        rows = """
<tr>
<td colspan="7" class="empty">
No Tuesday entries.
</td>
</tr>
"""

    content = f"""
<div class="card">

<h1>📅 {tr('calendar')}</h1>

<p>
Public Tuesday calendar published by authorized staff.
</p>

<div class="notice warning">
Schedules may change. Confirm important information
with the court.
</div>

</div>


<div class="card table-wrap">

<table>

<thead>

<tr>
<th>{tr('hearing_date')}</th>
<th>{tr('hearing_time')}</th>
<th>{tr('case_number')}</th>
<th>{tr('parties')}</th>
<th>{tr('hearing_nature')}</th>
<th>{tr('hearing_status')}</th>
<th>{tr('courtroom')}</th>
</tr>

</thead>

<tbody>
{rows}
</tbody>

</table>

</div>
"""

    return page(
        tr("calendar"),
        content,
    )


@app.route("/requirements")
def requirements():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY
            CASE category
                WHEN 'bond' THEN 1
                WHEN 'cash_bond' THEN 2
                WHEN 'clearance' THEN 3
                ELSE 4
            END
        """
    ).fetchall()

    connection.close()

    content = f"""
<div class="card">

<h1>📄 {tr('requirements')}</h1>

<p>
These requirements are provided for public information.
For the current official requirement, please contact
the court.
</p>

</div>
"""

    for row in rows:

        title = (
            row["title_fil"]
            if lang() == "fil"
            else row["title_en"]
        )

        description = (
            row["description_fil"]
            if lang() == "fil"
            else row["description_en"]
        )

        file_link = ""

        if row["file_name"]:
            file_link = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        content += f"""
<div class="card">

<h2>
{esc(title)}
</h2>

<div class="notice">
{requirement_list(row['category'])}
</div>

<p>
<strong>Current information:</strong><br>
{esc(description or tr('not_uploaded'))}
</p>

{file_link}

</div>
"""

    return page(
        tr("requirements"),
        content,
    )


@app.route("/laws")
def laws():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY category, created_at DESC
        """
    ).fetchall()

    connection.close()

    content = f"""
<div class="card">

<h1>⚖️ {tr('laws')}</h1>

<p>
Authorized staff may add Philippine laws,
Supreme Court decisions, rules and other
official legal resources.
</p>

</div>
"""

    for row in rows:

        links = ""

        if row["source_url"]:
            links += (
                f"<a class='button secondary' "
                f"href='{esc(row['source_url'])}' "
                f"target='_blank' rel='noopener noreferrer'>"
                f"{tr('official_source')}</a> "
            )

        if row["file_name"]:
            links += (
                f"<a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"{tr('open')}</a>"
            )

        content += (
            f"<div class='card'>"
            f"<span class='status'>{esc(row['category'])}</span>"
            f"<h2>{esc(row['title'])}</h2>"
            f"<p>{esc(row['description'])}</p>"
            f"{links}"
            f"</div>"
        )

    if not rows:
        content += (
            "<div class='card empty'>"
            "No legal resources have been published."
            "</div>"
        )

    return page(
        tr("laws"),
        content,
    )


# ============================================================
# STAFF AUTHENTICATION
# ============================================================

@app.route(
    "/staff/login",
    methods=["GET", "POST"],
)
def staff_login():

    if session.get(
        "staff_logged_in", False,
    ):

        return redirect(
            url_for("staff_dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        connection = get_db()

        staff = connection.execute(
            """
            SELECT *
            FROM staff
            WHERE username = ?
            AND active = 1
            """,
            (username,),
        ).fetchone()

        connection.close()

        if (
            staff
            and check_password_hash(
                staff["password_hash"],
                password,
            )
        ):

            session.clear()

            session["staff_logged_in"] = True
            session["staff_id"] = staff["id"]
            session["staff_username"] = staff["username"]
            session["staff_role"] = staff["role"]
            session["language"] = "en"
            session["theme"] = "light"

            audit(
                "login",
                username,
            )

            return redirect(
                url_for("staff_dashboard")
            )

        flash(
            tr("invalid_login"),
            "danger",
        )

    content = f"""
<div
class="card"
style="max-width:520px;margin:45px auto"
>

<img
class="hero-logo"
src="{url_for('static', filename=LOGO_FILENAME)}"
alt="Court logo"
>

<h1>🔐 {tr('staff_login')}</h1>

<p class="small">
Authorized court staff only.
</p>

<form
method="post"
autocomplete="off"
>

<label>
{tr('username')}
</label>

<input
name="username"
autocomplete="username"
required
>

<label>
{tr('password')}
</label>

<input
type="password"
name="password"
autocomplete="current-password"
required
>

<br>

<button type="submit">
{tr('login')}
</button>

</form>

</div>
"""

    return page(
        tr("staff_login"),
        content,
    )


@app.route(
    "/staff/logout",
    methods=["GET", "POST"],
)
def logout():

    username = session.get(
        "staff_username",
        "unknown",
    )

    if session.get(
        "staff_logged_in",
        False,
    ):
        audit(
            "logout",
            username,
        )

    session.clear()

    response = redirect(
        url_for("home")
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    flash(
        "You have been logged out.",
        "success",
    )

    return response


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/staff")
@app.route("/staff/dashboard")
@staff_required
def staff_dashboard():

    connection = get_db()

    cases = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    notices = connection.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    calendar = connection.execute(
        "SELECT COUNT(*) FROM tuesday_calendar"
    ).fetchone()[0]

    laws_count = connection.execute(
        "SELECT COUNT(*) FROM legal_resources"
    ).fetchone()[0]

    connection.close()

    cards = f"""
<div class="grid">

<div class="stat card">
<span class="stat-number">{cases}</span>
{tr('cases')}
</div>

<div class="stat card">
<span class="stat-number">{notices}</span>
{tr('notices')}
</div>

<div class="stat card">
<span class="stat-number">{calendar}</span>
{tr('calendar')}
</div>

<div class="stat card">
<span class="stat-number">{laws_count}</span>
{tr('laws')}
</div>

</div>
"""

    links = f"""
<div class="grid">

<a class="card" href="{url_for('staff_cases')}">
<h3>📋 {tr('manage_cases')}</h3>
<p>Add, edit and delete cases.</p>
</a>

<a class="card" href="{url_for('staff_calendar')}">
<h3>📅 {tr('manage_calendar')}</h3>
<p>Edit the Tuesday calendar.</p>
</a>

<a class="card" href="{url_for('staff_notices')}">
<h3>📢 {tr('manage_notices')}</h3>
<p>Upload photos or documents with notices.</p>
</a>

<a class="card" href="{url_for('staff_laws')}">
<h3>⚖️ {tr('manage_laws')}</h3>
<p>Add legal resources.</p>
</a>

<a class="card" href="{url_for('staff_requirements')}">
<h3>📄 {tr('manage_requirements')}</h3>
<p>Manage bond, cash bond and clearance requirements.</p>
</a>
"""

    if session.get("staff_role") == "admin":
        links += f"""
<a class="card" href="{url_for('staff_accounts')}">
<h3>👥 {tr('staff_accounts')}</h3>
<p>Add and manage staff accounts.</p>
</a>
"""

    links += "</div>"

    content = f"""
<section class="hero">

<h1>
{tr('welcome')}
</h1>

<p>
Manage approved public court information.
</p>

</section>

{cards}

<div class="card">

<h2>
⚡ {tr('quick_actions')}
</h2>

{links}

</div>
"""

    return page(
        tr("dashboard"),
        content,
    )


# ============================================================
# STAFF CASES
# ============================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    table = ""

    for row in rows:
        table += f"""
<tr>

<td>
<strong>{esc(row['case_number'])}</strong>
<br>
{esc(row['case_title'])}
</td>

<td>
{esc(row['parties'])}
</td>

<td>
{esc(row['case_type'])}
</td>

<td>
<span class="status">
{esc(row['status'])}
</span>
</td>

<td>

<a
class="button secondary"
href="{url_for('staff_edit_case', case_id=row['id'])}">
{tr('edit')}
</a>

<a
class="button secondary"
href="{url_for('staff_hearing', case_id=row['id'])}">
{tr('hearing')}
</a>

<form
method="post"
action="{url_for('staff_delete_case', case_id=row['id'])}"
style="display:inline"
>

<button
class="danger"
onclick="
return confirm(
'Delete this case permanently?'
);
"
>
{tr('delete')}
</button>

</form>

</td>

</tr>
"""

    if not table:
        table = """
<tr>
<td colspan="5" class="empty">
No cases.
</td>
</tr>
"""

    content = f"""
<div class="card">

<div class="actions">

<h1>
📋 {tr('manage_cases')}
</h1>

<a
class="button"
href="{url_for('staff_add_case')}">
➕ {tr('add_case')}
</a>

</div>

</div>


<div class="card table-wrap">

<table>

<thead>

<tr>
<th>{tr('case_number')}</th>
<th>{tr('parties')}</th>
<th>{tr('case_type')}</th>
<th>{tr('status')}</th>
<th>Actions</th>
</tr>

</thead>

<tbody>
{table}
</tbody>

</table>

</div>
"""

    return page(
        tr("cases"),
        content,
    )


@app.route(
    "/staff/cases/add",
    methods=["GET", "POST"],
)
@staff_required
def staff_add_case():

    if request.method == "POST":

        form = request.form

        values = (
            form.get(
                "case_number",
                "",
            ).strip(),

            form.get(
                "last_name",
                "",
            ).strip(),

            form.get(
                "parties",
                "",
            ).strip(),

            form.get(
                "case_title",
                "",
            ).strip(),

            form.get(
                "case_type",
                "",
            ).strip(),

            form.get(
                "status",
                "Pending",
            ).strip(),

            form.get(
                "public_description",
                "",
            ).strip(),

            form.get(
                "internal_notes",
                "",
            ).strip(),
        )

        if not all(
            values[:4]
        ):

            flash(
                "Complete all required case fields.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_add_case"
                )
            )

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO cases
                (
                    case_number,
                    last_name,
                    parties,
                    case_title,
                    case_type,
                    status,
                    public_description,
                    internal_notes,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values
                + (
                    now(),
                    now(),
                ),
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            flash(
                "That case number already exists.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_add_case"
                )
            )

        connection.close()

        audit(
            "case_created",
            values[0],
        )

        flash(
            "Case created successfully.",
            "success",
        )

        return redirect(
            url_for(
                "staff_cases"
            )
        )

    content = f"""
<div class="card">

<h1>
➕ {tr('add_case')}
</h1>

<form method="post">

<label>{tr('case_number')}</label>
<input name="case_number" required>

<label>{tr('last_name')}</label>
<input name="last_name" required>

<label>{tr('parties')}</label>
<input name="parties" required>

<label>{tr('case_title')}</label>
<input name="case_title" required>

<label>{tr('case_type')}</label>
<input name="case_type">

<label>{tr('status')}</label>
<select name="status">
<option>Pending</option>
<option>Active</option>
<option>Scheduled</option>
<option>Resolved</option>
<option>Final</option>
<option>Dismissed</option>
</select>

<label>{tr('description')}</label>
<textarea name="public_description"></textarea>

<label>
Private Staff Notes
</label>
<textarea name="internal_notes"></textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return page(
        tr("add_case"),
        content,
    )


@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=["GET", "POST"],
)
@staff_required
def staff_edit_case(
    case_id
):

    connection = get_db()

    case = connection.execute(
        "SELECT * FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    connection.close()

    if case is None:
        abort(404)

    if request.method == "POST":

        form = request.form

        connection = get_db()

        connection.execute(
            """
            UPDATE cases
            SET
                last_name = ?,
                parties = ?,
                case_title = ?,
                case_type = ?,
                status = ?,
                public_description = ?,
                internal_notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                form.get(
                    "last_name",
                    "",
                ).strip(),

                form.get(
                    "parties",
                    "",
                ).strip(),

                form.get(
                    "case_title",
                    "",
                ).strip(),

                form.get(
                    "case_type",
                    "",
                ).strip(),

                form.get(
                    "status",
                    "Pending",
                ).strip(),

                form.get(
                    "public_description",
                    "",
                ).strip(),

                form.get(
                    "internal_notes",
                    "",
                ).strip(),

                now(),

                case_id,
            ),
        )

        connection.commit()
        connection.close()

        audit(
            "case_updated",
            case[
                "case_number"
            ],
        )

        flash(
            "Case updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "staff_cases"
            )
        )

    statuses = ""

    for value in [
        "Pending",
        "Active",
        "Scheduled",
        "Resolved",
        "Final",
        "Dismissed",
    ]:

        selected = (
            "selected"
            if value
            == case["status"]
            else ""
        )

        statuses += (
            "<option %s>%s</option>"
            % (
                selected,
                value,
            )
        )

    content = f"""
<div class="card">

<h1>
✏️ {tr('edit_case')}
</h1>

<form method="post">

<label>{tr('case_number')}</label>
<input
value="{esc(case['case_number'])}"
disabled
>

<label>{tr('last_name')}</label>
<input
name="last_name"
value="{esc(case['last_name'])}"
required
>

<label>{tr('parties')}</label>
<input
name="parties"
value="{esc(case['parties'])}"
required
>

<label>{tr('case_title')}</label>
<input
name="case_title"
value="{esc(case['case_title'])}"
required
>

<label>{tr('case_type')}</label>
<input
name="case_type"
value="{esc(case['case_type'])}"
>

<label>{tr('status')}</label>
<select name="status">
{statuses}
</select>

<label>{tr('description')}</label>
<textarea
name="public_description"
>{esc(case['public_description'])}</textarea>

<label>
Private Staff Notes
</label>
<textarea
name="internal_notes"
>{esc(case['internal_notes'])}</textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return page(
        tr("edit_case"),
        content,
    )


@app.post(
    "/staff/cases/<int:case_id>/delete"
)
@staff_required
def staff_delete_case(
    case_id
):

    connection = get_db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    if case is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    connection.commit()
    connection.close()

    audit(
        "case_deleted",
        case["case_number"],
    )

    flash(
        "Case deleted successfully.",
        "success",
    )

    return redirect(
        url_for(
            "staff_cases"
        )
    )


# ============================================================
# STAFF HEARING EDITOR
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearing",
    methods=["GET", "POST"],
)
@staff_required
def staff_hearing(
    case_id
):

    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    hearing = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (case_id,),
    ).fetchone()

    connection.close()

    if case is None:
        abort(404)

    if request.method == "POST":

        form = request.form

        values = (
            form.get(
                "hearing_date",
                "",
            ).strip(),

            form.get(
                "hearing_time",
                "",
            ).strip(),

            form.get(
                "hearing_nature",
                "",
            ).strip(),

            form.get(
                "hearing_status",
                "Scheduled",
            ).strip(),

            form.get(
                "courtroom",
                "",
            ).strip(),

            form.get(
                "remarks",
                "",
            ).strip(),
        )

        connection = get_db()

        if hearing:

            connection.execute(
                """
                UPDATE hearings
                SET
                    hearing_date = ?,
                    hearing_time = ?,
                    hearing_nature = ?,
                    hearing_status = ?,
                    courtroom = ?,
                    remarks = ?
                WHERE id = ?
                """,
                values
                + (
                    hearing["id"],
                ),
            )

        else:

            connection.execute(
                """
                INSERT INTO hearings
                (
                    case_id,
                    hearing_date,
                    hearing_time,
                    hearing_nature,
                    hearing_status,
                    courtroom,
                    remarks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                )
                + values,
            )

        connection.commit()
        connection.close()

        audit(
            "hearing_updated",
            case["case_number"],
        )

        flash(
            "Hearing updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "staff_hearing",
                case_id=case_id,
            )
        )

    date_value = (
        hearing["hearing_date"]
        if hearing
        else ""
    )

    time_value = (
        hearing["hearing_time"]
        if hearing
        else ""
    )

    nature_value = (
        hearing["hearing_nature"]
        if hearing
        else "Initial Hearing"
    )

    status_value = (
        hearing["hearing_status"]
        if hearing
        else "Scheduled"
    )

    courtroom_value = (
        hearing["courtroom"]
        if hearing
        else ""
    )

    remarks_value = (
        hearing["remarks"]
        if hearing
        else ""
    )

    natures = [
        "Initial Hearing",
        "Arraignment",
        "Pre-Trial",
        "Trial",
        "Motion",
        "Compliance",
        "Judgment",
        "Promulgation",
        "Hearing",
        "Other",
    ]

    hearing_statuses = [
        "Scheduled",
        "Ongoing",
        "Completed",
        "Reset",
        "Postponed",
        "Cancelled",
    ]

    nature_options = ""

    for value in natures:

        nature_options += (
            f"<option "
            f"{'selected' if value == nature_value else ''}>"
            f"{esc(value)}"
            f"</option>"
        )

    status_options = ""

    for value in hearing_statuses:

        status_options += (
            f"<option "
            f"{'selected' if value == status_value else ''}>"
            f"{esc(value)}"
            f"</option>"
        )

    content = f"""
<div class="card">

<h1>
📅 {tr('hearing')}
</h1>

<p>
<strong>
{esc(case['case_number'])}
</strong>
-
{esc(case['parties'])}
</p>

<div class="notice">
Staff can change the hearing date,
nature, status, courtroom and remarks.
</div>

<form method="post">

<label>{tr('hearing_date')}</label>

<input
type="date"
name="hearing_date"
value="{esc(date_value)}"
required
>

<label>{tr('hearing_time')}</label>

<input
type="time"
name="hearing_time"
value="{esc(time_value)}"
>

<label>{tr('hearing_nature')}</label>

<select name="hearing_nature">
{nature_options}
</select>

<label>{tr('hearing_status')}</label>

<select name="hearing_status">
{status_options}
</select>

<label>{tr('courtroom')}</label>

<input
name="courtroom"
value="{esc(courtroom_value)}"
>

<label>{tr('remarks')}</label>

<textarea
name="remarks"
>{esc(remarks_value)}</textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return page(
        tr("hearing"),
        content,
    )


# ============================================================
# STAFF TUESDAY CALENDAR
# ============================================================

@app.route("/staff/calendar")
@staff_required
def staff_calendar():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM tuesday_calendar
        ORDER BY calendar_date, calendar_time, id
        """
    ).fetchall()

    connection.close()

    cards = ""

    for row in rows:

        statuses = ""

        for value in [
            "Scheduled",
            "Ongoing",
            "Completed",
            "Reset",
            "Postponed",
            "Cancelled",
        ]:

            statuses += (
                f"<option "
                f"{'selected' if value == row['hearing_status'] else ''}>"
                f"{esc(value)}"
                f"</option>"
            )

        checked = (
            "checked"
            if row["public_visible"]
            else ""
        )

        cards += f"""
<div class="card">

<form
method="post"
action="{url_for('edit_calendar', entry_id=row['id'])}"
>

<div class="two">

<div>

<label>Date</label>

<input
type="date"
name="calendar_date"
value="{esc(row['calendar_date'])}"
required
>

</div>

<div>

<label>Time</label>

<input
type="time"
name="calendar_time"
value="{esc(row['calendar_time'])}"
required
>

</div>

</div>


<label>{tr('case_number')}</label>

<input
name="case_number"
value="{esc(row['case_number'])}"
required
>


<label>{tr('last_name')}</label>

<input
name="last_name"
value="{esc(row['last_name'])}"
required
>


<label>{tr('parties')}</label>

<input
name="parties"
value="{esc(row['parties'])}"
required
>


<label>{tr('hearing_nature')}</label>

<input
name="hearing_nature"
value="{esc(row['hearing_nature'])}"
required
>


<label>{tr('hearing_status')}</label>

<select name="hearing_status">
{statuses}
</select>


<label>{tr('courtroom')}</label>

<input
name="courtroom"
value="{esc(row['courtroom'])}"
>


<label>{tr('remarks')}</label>

<textarea name="remarks">{esc(row['remarks'])}</textarea>


<label>

<input
type="checkbox"
name="public_visible"
{checked}
style="width:auto"
>

Publish to civilians

</label>


<button type="submit">
{tr('save')}
</button>

</form>


<br>

<a
class="button danger"
href="{url_for('delete_calendar', entry_id=row['id'])}"
onclick="
return confirm(
'Delete this calendar entry?'
);
"
>
{tr('delete')}
</a>

</div>
"""

    content = f"""
<div class="card">

<h1>
📅 {tr('manage_calendar')}
</h1>

<p>
Staff can add and edit the Tuesday calendar.
Civilians see only entries marked for publication.
</p>

</div>


<div class="card">

<h2>
Add Tuesday Entry
</h2>

<form
method="post"
action="{url_for('add_calendar')}"
>

<div class="two">

<div>

<label>Date</label>

<input
type="date"
name="calendar_date"
required
>

</div>

<div>

<label>Time</label>

<input
type="time"
name="calendar_time"
required
>

</div>

</div>


<label>{tr('case_number')}</label>

<input
name="case_number"
required
>


<label>{tr('last_name')}</label>

<input
name="last_name"
required
>


<label>{tr('parties')}</label>

<input
name="parties"
required
>


<label>{tr('hearing_nature')}</label>

<input
name="hearing_nature"
required
>


<label>{tr('hearing_status')}</label>

<select
name="hearing_status"
>

<option>Scheduled</option>
<option>Ongoing</option>
<option>Completed</option>
<option>Reset</option>
<option>Postponed</option>
<option>Cancelled</option>

</select>


<label>{tr('courtroom')}</label>

<input
name="courtroom"
>


<label>{tr('remarks')}</label>

<textarea
name="remarks"
></textarea>


<label>

<input
type="checkbox"
name="public_visible"
checked
style="width:auto"
>

Publish to civilians

</label>


<button type="submit">
{tr('add')}
</button>

</form>

</div>


{cards or
"<div class='card empty'>No Tuesday entries.</div>"
}
"""

    return page(
        tr("calendar"),
        content,
    )


@app.post("/staff/calendar/add")
@staff_required
def add_calendar():

    form = request.form

    values = (
        form.get(
            "calendar_date",
            "",
        ).strip(),

        form.get(
            "calendar_time",
            "",
        ).strip(),

        form.get(
            "case_number",
            "",
        ).strip(),

        form.get(
            "last_name",
            "",
        ).strip(),

        form.get(
            "parties",
            "",
        ).strip(),

        form.get(
            "hearing_nature",
            "",
        ).strip(),

        form.get(
            "hearing_status",
            "Scheduled",
        ).strip(),

        form.get(
            "courtroom",
            "",
        ).strip(),

        form.get(
            "remarks",
            "",
        ).strip(),

        int(
            bool(
                form.get(
                    "public_visible"
                )
            )
        ),

        now(),
        now(),
    )

    if not all(values[:6]):

        flash(
            "Complete all required calendar fields.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_calendar"
            )
        )

    connection = get_db()

    connection.execute(
        """
        INSERT INTO tuesday_calendar
        (
            calendar_date,
            calendar_time,
            case_number,
            last_name,
            parties,
            hearing_nature,
            hearing_status,
            courtroom,
            remarks,
            public_visible,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )

    connection.commit()
    connection.close()

    audit(
        "calendar_created",
        values[2],
    )

    flash(
        "Tuesday calendar entry added.",
        "success",
    )

    return redirect(
        url_for(
            "staff_calendar"
        )
    )


@app.post(
    "/staff/calendar/<int:entry_id>/edit"
)
@staff_required
def edit_calendar(
    entry_id
):

    form = request.form

    connection = get_db()

    connection.execute(
        """
        UPDATE tuesday_calendar
        SET
            calendar_date = ?,
            calendar_time = ?,
            case_number = ?,
            last_name = ?,
            parties = ?,
            hearing_nature = ?,
            hearing_status = ?,
            courtroom = ?,
            remarks = ?,
            public_visible = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            form.get(
                "calendar_date",
                "",
            ).strip(),

            form.get(
                "calendar_time",
                "",
            ).strip(),

            form.get(
                "case_number",
                "",
            ).strip(),

            form.get(
                "last_name",
                "",
            ).strip(),

            form.get(
                "parties",
                "",
            ).strip(),

            form.get(
                "hearing_nature",
                "",
            ).strip(),

            form.get(
                "hearing_status",
                "Scheduled",
            ).strip(),

            form.get(
                "courtroom",
                "",
            ).strip(),

            form.get(
                "remarks",
                "",
            ).strip(),

            int(
                bool(
                    form.get(
                        "public_visible"
                    )
                )
            ),

            now(),

            entry_id,
        ),
    )

    connection.commit()
    connection.close()

    flash(
        "Tuesday calendar entry updated.",
        "success",
    )

    return redirect(
        url_for(
            "staff_calendar"
        )
    )


@app.route(
    "/staff/calendar/<int:entry_id>/delete"
)
@staff_required
def delete_calendar(
    entry_id
):

    connection = get_db()

    connection.execute(
        """
        DELETE FROM tuesday_calendar
        WHERE id = ?
        """,
        (entry_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Tuesday calendar entry deleted.",
        "success",
    )

    return redirect(
        url_for(
            "staff_calendar"
        )
    )


# ============================================================
# STAFF NOTICES
# ============================================================

@app.route("/staff/notices")
@staff_required
def staff_notices():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    cards = ""

    for notice in rows:

        attachment = ""

        if notice[
            "attachment"
        ]:

            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=notice['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        cards += f"""
<div class="notice">

<h3>
{esc(notice['title_en'])}
</h3>

<p>
{esc(notice['body_en'])}
</p>

{attachment}

<form
method="post"
action="{url_for('delete_notice', notice_id=notice['id'])}"
style="display:inline"
>

<button
class="danger"
type="submit"
onclick="
return confirm(
'Delete this notice?'
);
"
>
{tr('delete')}
</button>

</form>

</div>
"""

    content = f"""
<div class="card">

<h1>
📢 {tr('manage_notices')}
</h1>

<form
method="post"
action="{url_for('add_notice')}"
enctype="multipart/form-data"
>

<label>
English Title
</label>

<input
name="title_en"
required
>


<label>
Filipino Title
</label>

<input
name="title_fil"
required
>


<label>
English Notice
</label>

<textarea
name="body_en"
required
></textarea>


<label>
Filipino Notice
</label>

<textarea
name="body_fil"
required
></textarea>


<label>
{tr('attachment')}
</label>

<input
type="file"
name="attachment"
accept=".pdf,.png,.jpg,.jpeg,.webp,.doc,.docx"
>


<button type="submit">
{tr('upload')}
</button>

</form>

</div>


<div class="card">

{cards or
"<p class='empty'>No notices yet.</p>"
}

</div>
"""

    return page(
        tr("notices"),
        content,
    )


@app.post("/staff/notices/add")
@staff_required
def add_notice():

    form = request.form

    title_en = form.get(
        "title_en",
        "",
    ).strip()

    title_fil = form.get(
        "title_fil",
        "",
    ).strip()

    body_en = form.get(
        "body_en",
        "",
    ).strip()

    body_fil = form.get(
        "body_fil",
        "",
    ).strip()

    if not all([
        title_en,
        title_fil,
        body_en,
        body_fil,
    ]):

        flash(
            "Complete all notice fields.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_notices"
            )
        )

    try:

        filename, original = save_upload(
            request.files.get(
                "attachment"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "danger",
        )

        return redirect(
            url_for(
                "staff_notices"
            )
        )

    connection = get_db()

    connection.execute(
        """
        INSERT INTO notices
        (
            title_en,
            title_fil,
            body_en,
            body_fil,
            attachment,
            original_filename,
            published,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title_en,
            title_fil,
            body_en,
            body_fil,
            filename,
            original,
            1,
            now(),
            now(),
        ),
    )

    connection.commit()
    connection.close()

    flash(
        "Notice published.",
        "success",
    )

    return redirect(
        url_for(
            "staff_notices"
        )
    )


@app.post(
    "/staff/notices/<int:notice_id>/delete"
)
@staff_required
def delete_notice(
    notice_id
):

    connection = get_db()

    row = connection.execute(
        """
        SELECT attachment
        FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    ).fetchone()

    if row and row["attachment"]:

        path = (
            UPLOAD_DIR
            / row["attachment"]
        )

        if path.exists():

            try:
                path.unlink()
            except OSError:
                pass

    connection.execute(
        """
        DELETE FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Notice deleted.",
        "success",
    )

    return redirect(
        url_for(
            "staff_notices"
        )
    )


# ============================================================
# STAFF LEGAL RESOURCES
# ============================================================

@app.route("/staff/laws")
@staff_required
def staff_laws():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    cards = ""

    for row in rows:

        links = ""

        if row["source_url"]:
            links += (
                f"<a class='button secondary' "
                f"href='{esc(row['source_url'])}' "
                f"target='_blank' "
                f"rel='noopener noreferrer'>"
                f"{tr('official_source')}"
                f"</a> "
            )

        if row["file_name"]:
            links += (
                f"<a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"{tr('open')}"
                f"</a> "
            )

        cards += f"""
<div class="notice">

<span class="status">
{esc(row['category'])}
</span>

<h3>
{esc(row['title'])}
</h3>

<p>
{esc(row['description'])}
</p>

{links}

<form
method="post"
action="{url_for('delete_law', law_id=row['id'])}"
style="display:inline"
>

<button
class="danger"
type="submit"
onclick="
return confirm(
'Delete this legal resource?'
);
"
>
{tr('delete')}
</button>

</form>

</div>
"""

    content = f"""
<div class="card">

<h1>
⚖️ {tr('manage_laws')}
</h1>

<form
method="post"
action="{url_for('add_law')}"
enctype="multipart/form-data"
>

<label>
Category
</label>

<select name="category">

<option>Philippine Laws</option>
<option>Supreme Court Decisions</option>
<option>Rules of Court</option>
<option>Supreme Court Rules</option>
<option>Administrative Matters</option>
<option>Other Official Resource</option>

</select>


<label>
Title
</label>

<input
name="title"
required
>


<label>
Description
</label>

<textarea
name="description"
></textarea>


<label>
Official Source URL
</label>

<input
type="url"
name="source_url"
>


<label>
Document
</label>

<input
type="file"
name="file"
>


<button type="submit">
{tr('add')}
</button>

</form>

</div>


<div class="card">

{cards or
"<p class='empty'>No legal resources yet.</p>"
}

</div>
"""

    return page(
        tr("laws"),
        content,
    )


@app.post(
    "/staff/laws/add"
)
@staff_required
def add_law():

    title = request.form.get(
        "title",
        "",
    ).strip()

    if not title:

        flash(
            "Title is required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_laws"
            )
        )

    try:

        filename, original = save_upload(
            request.files.get(
                "file"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "danger",
        )

        return redirect(
            url_for(
                "staff_laws"
            )
        )

    connection = get_db()

    connection.execute(
        """
        INSERT INTO legal_resources
        (
            category,
            title,
            description,
            source_url,
            file_name,
            original_filename,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.form.get(
                "category",
                "",
            ).strip(),

            title,

            request.form.get(
                "description",
                "",
            ).strip(),

            request.form.get(
                "source_url",
                "",
            ).strip(),

            filename,

            original,

            now(),

            now(),
        ),
    )

    connection.commit()
    connection.close()

    flash(
        "Legal resource added.",
        "success",
    )

    return redirect(
        url_for(
            "staff_laws"
        )
    )


@app.post(
    "/staff/laws/<int:law_id>/delete"
)
@staff_required
def delete_law(
    law_id
):

    connection = get_db()

    row = connection.execute(
        """
        SELECT file_name
        FROM legal_resources
        WHERE id = ?
        """,
        (law_id,),
    ).fetchone()

    if row and row["file_name"]:

        path = (
            UPLOAD_DIR
            / row["file_name"]
        )

        if path.exists():

            try:
                path.unlink()
            except OSError:
                pass

    connection.execute(
        """
        DELETE FROM legal_resources
        WHERE id = ?
        """,
        (law_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Legal resource deleted.",
        "success",
    )

    return redirect(
        url_for(
            "staff_laws"
        )
    )


# ============================================================
# STAFF REQUIREMENTS
# ============================================================

@app.route(
    "/staff/requirements"
)
@staff_required
def staff_requirements():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY
            CASE category
                WHEN 'bond' THEN 1
                WHEN 'cash_bond' THEN 2
                WHEN 'clearance' THEN 3
                ELSE 4
            END
        """
    ).fetchall()

    connection.close()

    cards = ""

    for row in rows:

        title = (
            row["title_fil"]
            if lang() == "fil"
            else row["title_en"]
        )

        description = (
            row["description_fil"]
            if lang() == "fil"
            else row["description_en"]
        )

        cards += f"""
<div class="card">

<h2>
{esc(title)}
</h2>

{requirement_list(row['category'])}

<p class="small">
Current uploaded information:
</p>

<p>
{esc(description or tr('not_uploaded'))}
</p>

<form
method="post"
action="{url_for('update_requirement', category=row['category'])}"
enctype="multipart/form-data"
>

<label>
Description
</label>

<textarea
name="description"
>{esc(description)}</textarea>

<label>
Official Document
</label>

<input
type="file"
name="document"
>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    content = f"""
<div class="card">

<h1>
📄 {tr('manage_requirements')}
</h1>

<p>
Bond, cash bond and clearance requirements
can be updated by authorized staff.
</p>

</div>

{cards}
"""

    return page(
        tr("requirements"),
        content,
    )


@app.post(
    "/staff/requirements/<category>/update"
)
@staff_required
def update_requirement(
    category
):

    if category not in {
        "bond",
        "cash_bond",
        "clearance",
    }:

        abort(404)

    description = request.form.get(
        "description",
        "",
    ).strip()

    try:

        filename, original = save_upload(
            request.files.get(
                "document"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "danger",
        )

        return redirect(
            url_for(
                "staff_requirements"
            )
        )

    connection = get_db()

    if filename:

        connection.execute(
            """
            UPDATE requirements
            SET
                description_en = ?,
                description_fil = ?,
                file_name = ?,
                original_filename = ?,
                updated_at = ?
            WHERE category = ?
            """,
            (
                description,
                description,
                filename,
                original,
                now(),
                category,
            ),
        )

    else:

        connection.execute(
            """
            UPDATE requirements
            SET
                description_en = ?,
                description_fil = ?,
                updated_at = ?
            WHERE category = ?
            """,
            (
                description,
                description,
                now(),
                category,
            ),
        )

    connection.commit()
    connection.close()

    flash(
        "Requirement updated.",
        "success",
    )

    return redirect(
        url_for(
            "staff_requirements"
        )
    )


# ============================================================
# STAFF ACCOUNT MANAGEMENT
# ============================================================

@app.route(
    "/staff/accounts"
)
@admin_required
def staff_accounts():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT
            id,
            username,
            email,
            role,
            active
        FROM staff
        ORDER BY username
        """
    ).fetchall()

    connection.close()

    table = ""

    for row in rows:

        controls = (
            f"<form method='post' "
            f"action='{url_for('toggle_staff', staff_id=row['id'])}' "
            f"style='display:inline'>"
            f"<button type='submit'>"
            f"{'Disable' if row['active'] else 'Enable'}"
            f"</button>"
            f"</form>"
        )

        if row["username"] != "admin":

            controls += (
                f"<form method='post' "
                f"action='{url_for('delete_staff', staff_id=row['id'])}' "
                f"style='display:inline'>"
                f"<button "
                f"class='danger' "
                f"type='submit' "
                f"onclick=\"return confirm('Delete this staff account?');\">"
                f"{tr('delete')}"
                f"</button>"
                f"</form>"
            )

        table += f"""
<tr>

<td>
{esc(row['username'])}
</td>

<td>
{esc(row['email'])}
</td>

<td>
{esc(row['role'])}
</td>

<td>
<span class="status">
{'Active' if row['active'] else 'Disabled'}
</span>
</td>

<td>
{controls}
</td>

</tr>
"""

    content = f"""
<div class="card">

<h1>
👥 {tr('staff_accounts')}
</h1>

<p>
Only administrators can add or manage
staff accounts.
</p>

</div>


<div class="card">

<h2>
➕ {tr('add_staff')}
</h2>

<form
method="post"
action="{url_for('add_staff')}"
>

<label>{tr('email')}</label>

<input
type="email"
name="email"
required
>


<label>{tr('username')}</label>

<input
name="username"
required
autocomplete="off"
>


<label>{tr('password')}</label>

<input
type="password"
name="password"
minlength="8"
required
autocomplete="new-password"
>


<label>{tr('role')}</label>

<select name="role">

<option value="staff">
Staff
</option>

<option value="admin">
Administrator
</option>

</select>


<button type="submit">
{tr('add_staff')}
</button>

</form>

</div>


<div class="card table-wrap">

<table>

<thead>

<tr>

<th>
Username
</th>

<th>
Email
</th>

<th>
Role
</th>

<th>
Status
</th>

<th>
Actions
</th>

</tr>

</thead>

<tbody>

{table}

</tbody>

</table>

</div>
"""

    return page(
        tr("staff_accounts"),
        content,
    )


@app.post(
    "/staff/accounts/add"
)
@admin_required
def add_staff():

    username = request.form.get(
        "username",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    password = request.form.get(
        "password",
        "",
    )

    role = request.form.get(
        "role",
        "staff",
    ).strip()

    if role not in {
        "staff",
        "admin",
    }:

        role = "staff"

    if not (
        username
        and email
        and password
    ):

        flash(
            "Username, email and password are required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    if len(password) < 8:

        flash(
            "Password must contain at least 8 characters.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO staff
            (
                username,
                email,
                password_hash,
                role,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                email,
                generate_password_hash(
                    password
                ),
                role,
                1,
                now(),
            ),
        )

        connection.commit()

    except sqlite3.IntegrityError:

        connection.close()

        flash(
            "That username or email already exists.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    connection.close()

    flash(
        "Staff account created successfully.",
        "success",
    )

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


@app.post(
    "/staff/accounts/<int:staff_id>/toggle"
)
@admin_required
def toggle_staff(
    staff_id
):

    connection = get_db()

    row = connection.execute(
        """
        SELECT username, active
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if row is None:

        connection.close()

        abort(404)

    if row["username"] == "admin":

        connection.close()

        flash(
            "The primary admin cannot be disabled.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    connection.execute(
        """
        UPDATE staff
        SET active = ?
        WHERE id = ?
        """,
        (
            0 if row["active"] else 1,
            staff_id,
        ),
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


@app.post(
    "/staff/accounts/<int:staff_id>/delete"
)
@admin_required
def delete_staff(
    staff_id
):

    connection = get_db()

    row = connection.execute(
        """
        SELECT username
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if row is None:

        connection.close()

        abort(404)

    if row["username"] == "admin":

        connection.close()

        flash(
            "The primary admin cannot be deleted.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    connection.execute(
        """
        DELETE FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Staff account deleted.",
        "success",
    )

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


# ============================================================
# UPLOADED FILES
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(
    filename
):

    return send_from_directory(
        UPLOAD_DIR,
        filename,
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return {
        "status": "ok",
        "service": COURT_NAME,
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(403)
def forbidden(error):

    content = """
<div class="card empty">
<h1>403</h1>
<h2>Access Denied</h2>
<p>
You do not have permission to access this page.
</p>
<a class="button" href="/">
Home
</a>
</div>
"""

    return page(
        "403",
        content,
    ), 403


@app.errorhandler(404)
def not_found(error):

    content = """
<div class="card empty">
<h1>404</h1>
<h2>Page Not Found</h2>
<p>
The requested page could not be found.
</p>
<a class="button" href="/">
Home
</a>
</div>
"""

    return page(
        "404",
        content,
    ), 404


@app.errorhandler(413)
def too_large(error):

    content = """
<div class="card empty">
<h1>413</h1>
<h2>File Too Large</h2>
<p>
Maximum upload size is 20 MB.
</p>
<a class="button" href="/">
Home
</a>
</div>
"""

    return page(
        "413",
        content,
    ), 413


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def add_security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    return response


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "5000",
            )
        ),
        debug=False,
    )
