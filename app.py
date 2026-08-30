# ================================================================
# MCTC SILANG-AMADEO, CAVITE
# COURT CASE INFORMATION SYSTEM
# ================================================================
#
# Put this file in the ROOT of your GitHub repository as:
#
#     app.py
#
# Put your logo here:
#
#     static/image0.png
#
# requirements.txt:
#
#     Flask==3.1.3
#     gunicorn==26.2.0
#
# Render:
#
# Build Command:
#     pip install -r requirements.txt
#
# Start Command:
#     gunicorn app:app
#
# IMPORTANT:
# This application is a starting/demo case-information system.
# Before using it for actual court records, have the court's
# authorized IT/security personnel review authentication,
# authorization, database security, backups, audit logging,
# document access, privacy, and deployment configuration.
#
# ================================================================

import os
import sqlite3
import secrets
import hashlib
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    send_from_directory,
    render_template_string,
    jsonify,
)


# ================================================================
# APPLICATION CONFIGURATION
# ================================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "court.db"

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = STATIC_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)


app = Flask(__name__)

# Do NOT use this development fallback for a real deployment.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-SECRET-KEY-IN-RENDER"
)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable this after HTTPS is configured on the production domain.
app.config["SESSION_COOKIE_SECURE"] = False


# ================================================================
# COURT INFORMATION
# ================================================================

COURT_NAME = "Municipal Circuit Trial Court of Silang-Amadeo, Cavite"

COURT_SHORT_NAME = "MCTC Silang-Amadeo"

COURT_ADDRESS_LINES = [
    "PNP Bldg, Plaza Libertad, Poblacion 2",
    "Silang, Cavite",
]

COURT_PHONE = "09284621305"

LOGO_FILENAME = "image0.png"


# ================================================================
# DATABASE HELPERS
# ================================================================

def get_db():
    """
    Open a SQLite database connection.

    SQLite is convenient for a small prototype.

    For an actual court production system, a managed database such
    as PostgreSQL should be considered together with proper backups,
    access controls, auditing, and disaster recovery.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    """
    Create all required database tables.
    """

    db = get_db()

    try:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS staff_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                created_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                case_number TEXT UNIQUE NOT NULL,

                case_title TEXT NOT NULL,

                case_type TEXT NOT NULL DEFAULT '',

                plaintiff TEXT NOT NULL DEFAULT '',

                defendant TEXT NOT NULL DEFAULT '',

                hearing_date TEXT NOT NULL DEFAULT '',

                hearing_time TEXT NOT NULL DEFAULT '',

                courtroom TEXT NOT NULL DEFAULT '',

                status TEXT NOT NULL DEFAULT 'Active',

                suspension_status TEXT NOT NULL DEFAULT 'No official suspension announced',

                suspension_details TEXT NOT NULL DEFAULT '',

                public_notes TEXT NOT NULL DEFAULT '',

                private_notes TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                case_id INTEGER NOT NULL,

                original_filename TEXT NOT NULL,

                stored_filename TEXT NOT NULL,

                is_public INTEGER NOT NULL DEFAULT 0,

                uploaded_at TEXT NOT NULL,

                FOREIGN KEY(case_id)
                    REFERENCES cases(id)
                    ON DELETE CASCADE
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                staff_username TEXT NOT NULL,

                action TEXT NOT NULL,

                case_number TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL
            )
            """
        )

        db.commit()

    finally:

        db.close()


# ================================================================
# PASSWORD FUNCTIONS
# ================================================================

def hash_password(password):
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    Passwords should never be stored as plain text.
    """

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )

    return (
        salt.hex()
        + "$"
        + password_hash.hex()
    )


def verify_password(password, stored_hash):
    """
    Verify a password against its stored PBKDF2 hash.
    """

    try:

        salt_hex, hash_hex = stored_hash.split("$", 1)

        salt = bytes.fromhex(salt_hex)

        expected = bytes.fromhex(hash_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000,
        )

        return secrets.compare_digest(
            actual,
            expected,
        )

    except Exception:

        return False


# ================================================================
# INITIAL STAFF ACCOUNT
# ================================================================

def create_initial_staff():
    """
    Create the first staff account from environment variables.

    Render environment variables:

        STAFF_USERNAME
        STAFF_PASSWORD

    Example:

        STAFF_USERNAME=courtstaff
        STAFF_PASSWORD=your-long-random-password

    Do not publish these values on GitHub.
    """

    username = os.environ.get(
        "STAFF_USERNAME",
        "courtstaff",
    )

    password = os.environ.get(
        "STAFF_PASSWORD",
    )

    if not password:

        return

    db = get_db()

    try:

        existing = db.execute(
            """
            SELECT id
            FROM staff_users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if existing:

            return

        db.execute(
            """
            INSERT INTO staff_users
            (
                username,
                password_hash,
                display_name,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                hash_password(password),
                "Court Staff",
                "staff",
                now_string(),
            ),
        )

        db.commit()

    finally:

        db.close()


# ================================================================
# GENERAL HELPERS
# ================================================================

def now_string():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def clean(value):
    """
    Safely normalize user input.
    """

    if value is None:
        return ""

    return str(value).strip()


def get_case(case_id):
    db = get_db()

    try:

        return db.execute(
            """
            SELECT *
            FROM cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

    finally:

        db.close()


def get_case_by_number(case_number):
    db = get_db()

    try:

        return db.execute(
            """
            SELECT *
            FROM cases
            WHERE case_number = ?
            """,
            (case_number,),
        ).fetchone()

    finally:

        db.close()


def log_action(action, case_number=""):
    """
    Store a simple staff audit record.
    """

    username = session.get(
        "staff_username",
        "unknown",
    )

    db = get_db()

    try:

        db.execute(
            """
            INSERT INTO audit_logs
            (
                staff_username,
                action,
                case_number,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                action,
                case_number,
                now_string(),
            ),
        )

        db.commit()

    finally:

        db.close()


# ================================================================
# AUTHENTICATION DECORATORS
# ================================================================

def staff_required(function):
    """
    Require a logged-in staff member.
    """

    @wraps(function)
    def wrapped(*args, **kwargs):

        if not session.get("staff_logged_in"):

            flash(
                "Please log in as court staff first.",
                "warning",
            )

            return redirect(
                url_for("staff_login")
            )

        return function(*args, **kwargs)

    return wrapped


# ================================================================
# TEMPLATE
# ================================================================

PAGE = r"""
<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
{{ title }} - MCTC Silang-Amadeo
</title>

<style>

:root {

    --purple-950: #24102f;
    --purple-900: #321342;
    --purple-800: #45175d;
    --purple-700: #5b1f76;
    --purple-600: #70278f;
    --purple-500: #8534a5;
    --purple-400: #9c55ba;
    --purple-300: #bd8bd0;
    --purple-200: #dcc3e5;
    --purple-100: #f0e7f4;

    --background: #f6f2f8;
    --surface: #ffffff;
    --surface-2: #faf7fc;

    --text: #241b29;
    --muted: #665c6c;

    --border: #ddd2e2;

    --success: #23733b;
    --warning: #9a6410;
    --danger: #a52b2b;

    --shadow:
        0 10px 30px rgba(45, 20, 55, .09);

    --radius: 16px;
}

html.dark {

    --background: #151019;
    --surface: #211926;
    --surface-2: #2a2030;

    --text: #f7eff9;
    --muted: #c8b8ce;

    --border: #493b4e;

    --purple-100: #382842;

    --shadow:
        0 10px 30px rgba(0, 0, 0, .30);
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

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: var(--background);

    color: var(--text);

    line-height: 1.6;
}

a {
    color: var(--purple-600);
    text-decoration: none;
}

html.dark a {
    color: var(--purple-300);
}

button,
input,
select,
textarea {

    font: inherit;
}

button {
    cursor: pointer;
}

.topbar {

    position: sticky;

    top: 0;

    z-index: 50;

    background:
        linear-gradient(
            135deg,
            var(--purple-950),
            var(--purple-700)
        );

    color: white;

    box-shadow:
        0 5px 20px rgba(0,0,0,.18);
}

.topbar-inner {

    width: min(1200px, calc(100% - 32px));

    margin: auto;

    min-height: 74px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 20px;
}

.brand {

    display: flex;

    align-items: center;

    gap: 13px;

    color: white;

    min-width: 0;
}

.brand-logo {

    width: 50px;

    height: 50px;

    object-fit: contain;

    display: block;

    flex: 0 0 auto;
}

.brand-title {

    font-weight: 800;

    line-height: 1.15;

    font-size: 15px;
}

.brand-subtitle {

    font-size: 12px;

    opacity: .82;

    margin-top: 3px;
}

.nav {

    display: flex;

    align-items: center;

    gap: 6px;

    flex-wrap: wrap;

    justify-content: flex-end;
}

.nav a,
.nav button {

    border: 0;

    background: transparent;

    color: white;

    padding: 9px 12px;

    border-radius: 10px;

    font-weight: 700;

    text-decoration: none;
}

.nav a:hover,
.nav button:hover {

    background: rgba(255,255,255,.13);
}

.container {

    width: min(1200px, calc(100% - 32px));

    margin: 0 auto;

    padding: 35px 0 60px;
}

.hero {

    background:
        linear-gradient(
            135deg,
            var(--purple-950),
            var(--purple-600)
        );

    color: white;

    border-radius: 24px;

    padding: 50px 35px;

    box-shadow: var(--shadow);

    margin-bottom: 28px;

    position: relative;

    overflow: hidden;
}

.hero::after {

    content: "";

    position: absolute;

    width: 260px;

    height: 260px;

    border-radius: 50%;

    right: -80px;

    top: -100px;

    background:
        rgba(255,255,255,.08);
}

.hero-content {

    position: relative;

    z-index: 2;

    max-width: 800px;
}

.hero h1 {

    margin: 0 0 12px;

    font-size:
        clamp(30px, 5vw, 52px);

    line-height: 1.08;
}

.hero p {

    margin: 8px 0;

    color: rgba(255,255,255,.90);

    font-size: 17px;
}

.grid {

    display: grid;

    grid-template-columns:
        repeat(12, 1fr);

    gap: 20px;
}

.col-12 {
    grid-column: span 12;
}

.col-8 {
    grid-column: span 8;
}

.col-6 {
    grid-column: span 6;
}

.col-4 {
    grid-column: span 4;
}

.card {

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: var(--radius);

    padding: 24px;

    box-shadow: var(--shadow);
}

.card h2,
.card h3 {

    margin-top: 0;

    line-height: 1.2;
}

.muted {
    color: var(--muted);
}

.small {
    font-size: 13px;
}

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 16px;
}

.form-full {
    grid-column: 1 / -1;
}

.field {

    display: flex;

    flex-direction: column;

    gap: 7px;
}

.field label {

    font-weight: 800;

    font-size: 14px;
}

input,
select,
textarea {

    width: 100%;

    border:
        1px solid var(--border);

    background: var(--surface-2);

    color: var(--text);

    border-radius: 10px;

    padding: 12px 13px;

    outline: none;
}

input:focus,
select:focus,
textarea:focus {

    border-color:
        var(--purple-500);

    box-shadow:
        0 0 0 3px
        rgba(112,39,143,.15);
}

textarea {

    min-height: 120px;

    resize: vertical;
}

.btn {

    display: inline-flex;

    align-items: center;

    justify-content: center;

    gap: 7px;

    border: 0;

    border-radius: 10px;

    padding: 11px 16px;

    font-weight: 800;

    text-decoration: none;

    transition:
        transform .15s ease,
        opacity .15s ease;
}

.btn:hover {
    transform: translateY(-1px);
}

.btn-primary {

    background: var(--purple-600);

    color: white;
}

.btn-secondary {

    background: var(--purple-100);

    color: var(--purple-800);
}

html.dark .btn-secondary {

    color: white;
}

.btn-danger {

    background: var(--danger);

    color: white;
}

.btn-success {

    background: var(--success);

    color: white;
}

.btn-light {

    background: white;

    color: var(--purple-800);
}

.actions {

    display: flex;

    flex-wrap: wrap;

    gap: 9px;

    margin-top: 18px;
}

.alert {

    border-radius: 12px;

    padding: 13px 15px;

    margin-bottom: 18px;

    border: 1px solid var(--border);

    background: var(--surface);

    font-weight: 650;
}

.alert.success {
    border-color: #8dc99e;
}

.alert.warning {
    border-color: #e4c27d;
}

.alert.danger {
    border-color: #df9999;
}

.alert.info {
    border-color: var(--purple-300);
}

.stat-grid {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 15px;
}

.stat {

    padding: 20px;

    border-radius: 15px;

    background:
        var(--purple-100);

    border:
        1px solid var(--border);
}

.stat-value {

    font-size: 30px;

    font-weight: 900;

    color:
        var(--purple-700);
}

html.dark .stat-value {
    color: var(--purple-300);
}

.stat-label {

    color: var(--muted);

    font-size: 13px;

    font-weight: 700;
}

.badge {

    display: inline-flex;

    align-items: center;

    padding: 5px 9px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: 800;

    background: var(--purple-100);

    color: var(--purple-800);
}

html.dark .badge {
    color: white;
}

.badge-success {

    background: #dff3e4;

    color: #1e6432;
}

.badge-warning {

    background: #fff0c9;

    color: #76500d;
}

.badge-danger {

    background: #f8dddd;

    color: #812525;
}

html.dark .badge-success,
html.dark .badge-warning,
html.dark .badge-danger {

    color: #241b29;
}

.case-result {

    border:
        1px solid var(--border);

    border-radius: 14px;

    padding: 18px;

    background: var(--surface-2);

    margin-top: 15px;
}

.case-result h3 {
    margin-bottom: 5px;
}

.case-meta {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 10px;

    margin-top: 15px;
}

.meta {

    padding: 11px;

    border-radius: 9px;

    background: var(--surface);

    border: 1px solid var(--border);
}

.meta strong {

    display: block;

    font-size: 12px;

    color: var(--muted);

    margin-bottom: 3px;
}

.table-wrap {

    overflow-x: auto;

    border-radius: 12px;

    border: 1px solid var(--border);
}

table {

    width: 100%;

    border-collapse: collapse;

    min-width: 850px;
}

th,
td {

    padding: 13px;

    text-align: left;

    border-bottom:
        1px solid var(--border);

    vertical-align: top;
}

th {

    background:
        var(--purple-100);

    color:
        var(--purple-900);

    font-size: 13px;
}

html.dark th {
    color: white;
}

tr:last-child td {
    border-bottom: 0;
}

.empty {

    text-align: center;

    padding: 35px;

    color: var(--muted);
}

.logo-large {

    width: 145px;

    height: 145px;

    object-fit: contain;

    display: block;

    margin: 0 auto 18px;
}

.footer {

    border-top:
        1px solid var(--border);

    padding: 25px 0 40px;

    color: var(--muted);

    font-size: 13px;

    text-align: center;
}

.login-box {

    width:
        min(460px, 100%);

    margin:
        40px auto;
}

.search-box {

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 20px;

    padding: 25px;

    box-shadow: var(--shadow);
}

.search-row {

    display: grid;

    grid-template-columns:
        1fr auto;

    gap: 10px;
}

.instructions {

    background:
        var(--purple-100);

    border:
        1px solid var(--border);

    border-radius: 14px;

    padding: 18px;

    margin-top: 18px;
}

.instructions ol {

    margin-bottom: 0;
}

.document {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 12px;

    border:
        1px solid var(--border);

    border-radius: 10px;

    padding: 12px 14px;

    margin-top: 9px;

    background: var(--surface-2);
}

hr {

    border: 0;

    border-top:
        1px solid var(--border);

    margin: 25px 0;
}

@media (max-width: 900px) {

    .col-8,
    .col-6,
    .col-4 {
        grid-column: span 12;
    }

    .stat-grid {
        grid-template-columns:
            repeat(2, 1fr);
    }

    .topbar-inner {
        align-items: flex-start;
        padding: 12px 0;
        flex-direction: column;
    }

    .nav {
        justify-content: flex-start;
    }
}

@media (max-width: 620px) {

    .container {
        width: min(
            100% - 20px,
            1200px
        );
        padding-top: 20px;
    }

    .hero {
        padding: 32px 22px;
    }

    .form-grid {
        grid-template-columns: 1fr;
    }

    .form-full {
        grid-column: auto;
    }

    .stat-grid {
        grid-template-columns: 1fr;
    }

    .case-meta {
        grid-template-columns: 1fr;
    }

    .search-row {
        grid-template-columns: 1fr;
    }
}

</style>

<script>

const translations = {

    en: {

        home: "Home",
        search: "Search Cases",
        staff: "Staff Login",
        dashboard: "Dashboard",
        logout: "Log Out",
        light: "Light",
        dark: "Dark",

        welcome:
            "Court Case Information System",

        search_title:
            "Search a Court Case",

        search_description:
            "Enter the case number and the name of a party exactly as registered by the court.",

        case_number:
            "Case Number",

        party_name:
            "Party Name",

        search_button:
            "Search Case",

        instructions:
            "How to search",

        instruction_1:
            "Enter the complete case number.",

        instruction_2:
            "Enter the name of a party to the case.",

        instruction_3:
            "Check the spelling before searching.",

        instruction_4:
            "Only information authorized for public viewing should appear here.",

        suspension:
            "Case Suspension Information",

        suspension_notice:
            "Case suspension should only be treated as official when announced or confirmed by the proper court or authorized government authority.",

        staff_dashboard:
            "Staff Dashboard",

        add_case:
            "Add Case",

        edit:
            "Edit",

        delete:
            "Delete",

        save:
            "Save Case",

        cancel:
            "Cancel",

        no_results:
            "No matching case was found.",

        hearing:
            "Hearing",

        status:
            "Status",

        case_information:
            "Case Information",

        public_notes:
            "Public Notes",

        private_notes:
            "Private Staff Notes",

        documents:
            "Documents",

        upload:
            "Upload",

        official:
            "Official Information",

        court_address:
            "Court Address",

        contact:
            "Contact",

        language:
            "Language",

        theme:
            "Theme"

    },

    fil: {

        home: "Home",

        search:
            "Maghanap ng Kaso",

        staff:
            "Login ng Staff",

        dashboard:
            "Dashboard",

        logout:
            "Mag-logout",

        light:
            "Maliwanag",

        dark:
            "Madilim",

        welcome:
            "Sistema ng Impormasyon sa mga Kaso ng Hukuman",

        search_title:
            "Maghanap ng Kaso",

        search_description:
            "Ilagay ang case number at pangalan ng partido ayon sa rekord ng hukuman.",

        case_number:
            "Case Number",

        party_name:
            "Pangalan ng Partido",

        search_button:
            "Maghanap",

        instructions:
            "Paraan ng paghahanap",

        instruction_1:
            "Ilagay ang buong case number.",

        instruction_2:
            "Ilagay ang pangalan ng isang partido sa kaso.",

        instruction_3:
            "Suriin ang spelling bago maghanap.",

        instruction_4:
            "Ang impormasyong maaaring makita ng publiko lamang ang dapat ipakita.",

        suspension:
            "Impormasyon tungkol sa Suspensyon ng Kaso",

        suspension_notice:
            "Ang suspensyon ng kaso ay dapat ituring na opisyal lamang kung ito ay inihayag o kinumpirma ng wastong hukuman o awtorisadong ahensiya ng pamahalaan.",

        staff_dashboard:
            "Dashboard ng Staff",

        add_case:
            "Magdagdag ng Kaso",

        edit:
            "I-edit",

        delete:
            "Burahin",

        save:
            "I-save ang Kaso",

        cancel:
            "Kanselahin",

        no_results:
            "Walang nakitang katugmang kaso.",

        hearing:
            "Pagdinig",

        status:
            "Status",

        case_information:
            "Impormasyon ng Kaso",

        public_notes:
            "Pampublikong Tala",

        private_notes:
            "Pribadong Tala ng Staff",

        documents:
            "Mga Dokumento",

        upload:
            "Mag-upload",

        official:
            "Opisyal na Impormasyon",

        court_address:
            "Address ng Hukuman",

        contact:
            "Contact",

        language:
            "Wika",

        theme:
            "Tema"

    }

};


function setLanguage(language) {

    localStorage.setItem(
        "court_language",
        language
    );

    document.documentElement
        .setAttribute(
            "lang",
            language
        );

    document
        .querySelectorAll(
            "[data-i18n]"
        )
        .forEach(function(element) {

            const key =
                element.getAttribute(
                    "data-i18n"
                );

            if (
                translations[language] &&
                translations[language][key]
            ) {

                element.textContent =
                    translations[language][key];

            }

        });

    document
        .querySelectorAll(
            "[data-i18n-placeholder]"
        )
        .forEach(function(element) {

            const key =
                element.getAttribute(
                    "data-i18n-placeholder"
                );

            if (
                translations[language] &&
                translations[language][key]
            ) {

                element.placeholder =
                    translations[language][key];

            }

        });

    document
        .querySelectorAll(
            "[data-i18n-value]"
        )
        .forEach(function(element) {

            const key =
                element.getAttribute(
                    "data-i18n-value"
                );

            if (
                translations[language] &&
                translations[language][key]
            ) {

                element.value =
                    translations[language][key];

            }

        });

    const selector =
        document.getElementById(
            "languageSelector"
        );

    if (selector) {
        selector.value = language;
    }
}


function setTheme(theme) {

    if (theme === "dark") {

        document.documentElement
            .classList
            .add("dark");

    } else {

        document.documentElement
            .classList
            .remove("dark");

    }

    localStorage.setItem(
        "court_theme",
        theme
    );
}


function initializePreferences() {

    const savedTheme =
        localStorage.getItem(
            "court_theme"
        ) || "light";

    const savedLanguage =
        localStorage.getItem(
            "court_language"
        ) || "en";

    setTheme(savedTheme);

    setLanguage(savedLanguage);
}


document.addEventListener(
    "DOMContentLoaded",
    initializePreferences
);

</script>

</head>

<body>

<header class="topbar">

<div class="topbar-inner">

<a
    href="{{ url_for('home') }}"
    class="brand"
>

<img
    src="{{ url_for('static', filename='image0.png') }}"
    class="brand-logo"
    alt="MCTC Silang-Amadeo Court Seal"
>

<div>

<div class="brand-title">
{{ court_short }}
</div>

<div class="brand-subtitle">
{{ court_name }}
</div>

</div>

</a>

<nav class="nav">

<a
    href="{{ url_for('home') }}"
    data-i18n="home"
>
Home
</a>

<a
    href="{{ url_for('public_search') }}"
    data-i18n="search"
>
Search Cases
</a>

{% if session.get("staff_logged_in") %}

<a
    href="{{ url_for('dashboard') }}"
    data-i18n="dashboard"
>
Dashboard
</a>

<form
    method="post"
    action="{{ url_for('logout') }}"
    style="display:inline"
>

<button
    type="submit"
    data-i18n="logout"
>
Log Out
</button>

</form>

{% else %}

<a
    href="{{ url_for('staff_login') }}"
    data-i18n="staff"
>
Staff Login
</a>

{% endif %}

<select
    id="languageSelector"
    onchange="setLanguage(this.value)"
    aria-label="Language"
    style="width:auto;padding:8px"
>

<option value="en">English</option>

<option value="fil">Filipino</option>

</select>

<button
    type="button"
    onclick="
        setTheme(
            document.documentElement.classList.contains('dark')
            ? 'light'
            : 'dark'
        )
    "
    aria-label="Toggle dark mode"
>
☾ / ☀
</button>

</nav>

</div>

</header>


<main class="container">

{% with messages = get_flashed_messages(with_categories=true) %}

{% if messages %}

{% for category, message in messages %}

<div class="alert {{ category }}">

{{ message }}

</div>

{% endfor %}

{% endif %}

{% endwith %}


{% block_content %}

{{ content|safe }}

{% endblock_content %}

</main>


<footer class="footer">

<strong>
{{ court_name }}
</strong>

<br>

{{ court_address[0] }}

<br>

{{ court_address[1] }}

<br>

{{ court_phone }}

<br><br>

<span>
Court Case Information System
</span>

</footer>

</body>

</html>
"""


# ================================================================
# RENDER HELPER
# ================================================================

def render_page(title, content):
    return render_template_string(
        PAGE,
        title=title,
        content=content,
        court_name=COURT_NAME,
        court_short=COURT_SHORT_NAME,
        court_address=COURT_ADDRESS_LINES,
        court_phone=COURT_PHONE,
    )


# ================================================================
# HOME PAGE
# ================================================================

@app.route("/")
def home():

    content = r"""
<section class="hero">

<div class="hero-content">

<h1 data-i18n="welcome">
Court Case Information System
</h1>

<p>
Municipal Circuit Trial Court of Silang-Amadeo, Cavite
</p>

<p>
Access public case information, hearing schedules,
and official court notices through this information system.
</p>

<div class="actions">

<a
    href="/cases"
    class="btn btn-light"
    data-i18n="search"
>
Search Cases
</a>

<a
    href="/staff/login"
    class="btn btn-secondary"
    data-i18n="staff"
>
Staff Login
</a>

</div>

</div>

</section>


<div class="grid">

<div class="col-8">

<div class="card">

<img
    src="/static/image0.png"
    class="logo-large"
    alt="Municipal Circuit Trial Court Seal"
>

<h2>
Municipal Circuit Trial Court of Silang-Amadeo, Cavite
</h2>

<p class="muted">
This website is intended to provide authorized public
case information and court announcements.
</p>

<h3 data-i18n="official">
Official Information
</h3>

<p>
<strong data-i18n="court_address">
Court Address
</strong>
</p>

<p>
PNP Bldg, Plaza Libertad, Poblacion 2<br>
Silang, Cavite
</p>

<p>
<strong data-i18n="contact">
Contact
</strong>
</p>

<p>
09284621305
</p>

</div>

</div>


<div class="col-4">

<div class="card">

<h2>
Search a Case
</h2>

<p class="muted">
Use the case number and party name to locate
publicly available case information.
</p>

<a
    href="/cases"
    class="btn btn-primary"
>
Open Case Search
</a>

</div>


<div class="card" style="margin-top:20px">

<h3 data-i18n="suspension">
Case Suspension Information
</h3>

<p
    class="small"
    data-i18n="suspension_notice"
>
Case suspension should only be treated as official
when announced or confirmed by the proper court
or authorized government authority.
</p>

</div>

</div>

</div>
"""

    return render_page(
        "Home",
        content,
    )


# ================================================================
# PUBLIC CASE SEARCH
# ================================================================

@app.route("/cases", methods=["GET", "POST"])
def public_search():

    result = None

    searched = False

    if request.method == "POST":

        case_number = clean(
            request.form.get(
                "case_number"
            )
        )

        party_name = clean(
            request.form.get(
                "party_name"
            )
        )

        searched = True

        if not case_number or not party_name:

            flash(
                "Please enter both the case number and party name.",
                "warning",
            )

        else:

            db = get_db()

            try:

                result = db.execute(
                    """
                    SELECT *
                    FROM cases
                    WHERE case_number = ?
                    AND (
                        lower(plaintiff)
                        LIKE lower(?)
                        OR
                        lower(defendant)
                        LIKE lower(?)
                    )
                    """,
                    (
                        case_number,
                        "%" + party_name + "%",
                        "%" + party_name + "%",
                    ),
                ).fetchone()

            finally:

                db.close()

    result_html = ""

    if searched:

        if result:

            result_html = f"""
<div class="case-result">

<h3>
{escape_html(result["case_title"])}
</h3>

<p>
<span class="badge">
{escape_html(result["case_number"])}
</span>
</p>

<div class="case-meta">

<div class="meta">

<strong>Case Type</strong>

{escape_html(result["case_type"]) or "—"}

</div>

<div class="meta">

<strong>Status</strong>

{escape_html(result["status"]) or "—"}

</div>

<div class="meta">

<strong>Hearing Date</strong>

{escape_html(result["hearing_date"]) or "—"}

</div>

<div class="meta">

<strong>Hearing Time</strong>

{escape_html(result["hearing_time"]) or "—"}

</div>

<div class="meta">

<strong>Party / Plaintiff</strong>

{escape_html(result["plaintiff"]) or "—"}

</div>

<div class="meta">

<strong>Party / Defendant</strong>

{escape_html(result["defendant"]) or "—"}

</div>

<div class="meta">

<strong>Courtroom</strong>

{escape_html(result["courtroom"]) or "—"}

</div>

<div class="meta">

<strong>Suspension Status</strong>

{escape_html(result["suspension_status"]) or "—"}

</div>

</div>

<hr>

<h3 data-i18n="public_notes">
Public Notes
</h3>

<p>
{escape_html(result["public_notes"]) or "No public note is currently available."}
</p>

<a
    class="btn btn-primary"
    href="/cases/view/{result["id"]}"
>
View Case
</a>

</div>
"""

        else:

            result_html = """
<div class="alert warning">

<strong data-i18n="no_results">
No matching case was found.
</strong>

<p>
Please check the case number and party name.
If you still cannot find the case, contact the court
using the official contact information.
</p>

</div>
"""

    content = f"""

<div class="search-box">

<h1 data-i18n="search_title">
Search a Court Case
</h1>

<p
    class="muted"
    data-i18n="search_description"
>
Enter the case number and the name of a party exactly
as registered by the court.
</p>

<form
    method="post"
    autocomplete="off"
>

<div class="form-grid">

<div class="field">

<label
    for="case_number"
    data-i18n="case_number"
>
Case Number
</label>

<input
    id="case_number"
    name="case_number"
    type="text"
    placeholder="Example: 12345"
    required
>

</div>

<div class="field">

<label
    for="party_name"
    data-i18n="party_name"
>
Party Name
</label>

<input
    id="party_name"
    name="party_name"
    type="text"
    placeholder="Enter party name"
    required
>

</div>

</div>

<div class="actions">

<button
    type="submit"
    class="btn btn-primary"
    data-i18n="search_button"
>
Search Case
</button>

<a
    href="/"
    class="btn btn-secondary"
    data-i18n="home"
>
Home
</a>

</div>

</form>

<div class="instructions">

<h3 data-i18n="instructions">
How to search
</h3>

<ol>

<li data-i18n="instruction_1">
Enter the complete case number.
</li>

<li data-i18n="instruction_2">
Enter the name of a party to the case.
</li>

<li data-i18n="instruction_3">
Check the spelling before searching.
</li>

<li data-i18n="instruction_4">
Only information authorized for public viewing should appear here.
</li>

</ol>

</div>

</div>

{result_html}

<div class="card" style="margin-top:20px">

<h3 data-i18n="suspension">
Case Suspension Information
</h3>

<p data-i18n="suspension_notice">
Case suspension should only be treated as official when
announced or confirmed by the proper court or authorized
government authority.
</p>

</div>

"""

    return render_page(
        "Search Cases",
        content,
    )


# ================================================================
# PUBLIC CASE VIEW
# ================================================================

@app.route("/cases/view/<int:case_id>")
def public_case_view(case_id):

    case = get_case(case_id)

    if not case:

        abort(404)

    documents = get_public_documents(case_id)

    document_html = ""

    if documents:

        for document in documents:

            document_html += f"""
<div class="document">

<span>
{escape_html(document["original_filename"])}
</span>

<a
    class="btn btn-secondary"
    href="/documents/public/{document["id"]}"
>
Open
</a>

</div>
"""

    else:

        document_html = """
<p class="muted">
No publicly available documents are currently attached
to this case.
</p>
"""

    content = f"""

<div class="card">

<p>

<a href="/cases">
← Back to Case Search
</a>

</p>

<h1>
{escape_html(case["case_title"])}
</h1>

<p>
<span class="badge">
{escape_html(case["case_number"])}
</span>
</p>

<div class="case-meta">

<div class="meta">

<strong>Case Type</strong>

{escape_html(case["case_type"]) or "—"}

</div>

<div class="meta">

<strong>Status</strong>

{escape_html(case["status"]) or "—"}

</div>

<div class="meta">

<strong>Hearing Date</strong>

{escape_html(case["hearing_date"]) or "—"}

</div>

<div class="meta">

<strong>Hearing Time</strong>

{escape_html(case["hearing_time"]) or "—"}

</div>

<div class="meta">

<strong>Plaintiff</strong>

{escape_html(case["plaintiff"]) or "—"}

</div>

<div class="meta">

<strong>Defendant</strong>

{escape_html(case["defendant"]) or "—"}

</div>

<div class="meta">

<strong>Courtroom</strong>

{escape_html(case["courtroom"]) or "—"}

</div>

<div class="meta">

<strong>Suspension Status</strong>

{escape_html(case["suspension_status"]) or "—"}

</div>

</div>

<hr>

<h2>
Public Case Information
</h2>

<p>
{escape_html(case["public_notes"]) or "No additional public information is currently available."}
</p>

<hr>

<h2 data-i18n="documents">
Documents
</h2>

<p class="muted">
Only documents specifically marked for public access
by authorized staff are displayed here.
</p>

{document_html}

<div class="alert warning" style="margin-top:20px">

<strong>
Important:
</strong>

Case information shown online may not constitute the
complete official court record. For official records,
please follow the court's authorized records-request
procedures.

</div>

</div>
"""

    return render_page(
        "Case Information",
        content,
    )


# ================================================================
# PUBLIC DOCUMENTS
# ================================================================

def get_public_documents(case_id):

    db = get_db()

    try:

        return db.execute(
            """
            SELECT *
            FROM documents
            WHERE case_id = ?
            AND is_public = 1
            ORDER BY uploaded_at DESC
            """,
            (case_id,),
        ).fetchall()

    finally:

        db.close()


@app.route("/documents/public/<int:document_id>")
def public_document(document_id):

    db = get_db()

    try:

        document = db.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            AND is_public = 1
            """,
            (document_id,),
        ).fetchone()

    finally:

        db.close()

    if not document:

        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        document["stored_filename"],
        as_attachment=False,
    )


# ================================================================
# STAFF LOGIN
# ================================================================

@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():

    if session.get("staff_logged_in"):

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = clean(
            request.form.get(
                "username"
            )
        )

        password = request.form.get(
            "password",
            "",
        )

        db = get_db()

        try:

            user = db.execute(
                """
                SELECT *
                FROM staff_users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        finally:

            db.close()

        if user and verify_password(
            password,
            user["password_hash"],
        ):

            session.clear()

            session["staff_logged_in"] = True

            session["staff_username"] = user["username"]

            session["staff_display_name"] = user["display_name"]

            session["staff_role"] = user["role"]

            log_action(
                "Staff login",
            )

            flash(
                "You are now logged in.",
                "success",
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger",
        )

    content = """

<div class="login-box">

<div class="card">

<img
    src="/static/image0.png"
    class="logo-large"
    alt="Court Seal"
>

<h1>
Staff Login
</h1>

<p class="muted">
Authorized court personnel only.
</p>

<form
    method="post"
    autocomplete="off"
>

<div class="field">

<label for="username">
Username
</label>

<input
    id="username"
    name="username"
    type="text"
    autocomplete="username"
    required
>

</div>

<br>

<div class="field">

<label for="password">
Password
</label>

<input
    id="password"
    name="password"
    type="password"
    autocomplete="current-password"
    required
>

</div>

<div class="actions">

<button
    type="submit"
    class="btn btn-primary"
>
Log In
</button>

<a
    href="/"
    class="btn btn-secondary"
>
Cancel
</a>

</div>

</form>

<div class="instructions">

<strong>
Security Notice
</strong>

<p class="small">
Never share your staff password. Do not save passwords
in public GitHub repositories.
</p>

</div>

</div>

</div>
"""

    return render_page(
        "Staff Login",
        content,
    )


# ================================================================
# LOGOUT
# ================================================================

@app.route("/staff/logout", methods=["POST"])
def logout():

    username = session.get(
        "staff_username",
        "",
    )

    if username:

        log_action(
            "Staff logout",
        )

    session.clear()

    flash(
        "You have been logged out.",
        "success",
    )

    return redirect(
        url_for("home")
    )


# ================================================================
# STAFF DASHBOARD
# ================================================================

@app.route("/staff")
@app.route("/staff/dashboard")
@staff_required
def dashboard():

    db = get_db()

    try:

        total_cases = db.execute(
            "SELECT COUNT(*) AS count FROM cases"
        ).fetchone()["count"]

        active_cases = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM cases
            WHERE lower(status) = 'active'
            """
        ).fetchone()["count"]

        suspended_cases = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM cases
            WHERE lower(suspension_status)
            LIKE '%suspend%'
            """
        ).fetchone()["count"]

        upcoming = db.execute(
            """
            SELECT *
            FROM cases
            WHERE hearing_date != ''
            ORDER BY hearing_date ASC
            LIMIT 10
            """
        ).fetchall()

    finally:

        db.close()

    rows = ""

    for case in upcoming:

        rows += f"""

<tr>

<td>
<strong>
{escape_html(case["case_number"])}
</strong>

<br>

<span class="small muted">
{escape_html(case["case_title"])}
</span>

</td>

<td>
{escape_html(case["hearing_date"]) or "—"}
</td>

<td>
{escape_html(case["hearing_time"]) or "—"}
</td>

<td>
{escape_html(case["status"]) or "—"}
</td>

<td>

<a
    href="/staff/case/{case["id"]}"
    class="btn btn-secondary"
>
View
</a>

</td>

</tr>

"""

    if not rows:

        rows = """
<tr>
<td colspan="5" class="empty">
No cases have been entered yet.
</td>
</tr>
"""

    content = f"""

<div class="hero">

<div class="hero-content">

<h1>
Staff Dashboard
</h1>

<p>
Welcome, {escape_html(session.get("staff_display_name", "Court Staff"))}.
</p>

<p>
Use this dashboard to manage authorized case information
and hearing schedules.
</p>

<div class="actions">

<a
    href="/staff/case/new"
    class="btn btn-light"
>
+ Add New Case
</a>

<a
    href="/cases"
    class="btn btn-secondary"
>
Public Case Search
</a>

</div>

</div>

</div>


<div class="stat-grid">

<div class="stat">

<div class="stat-value">
{total_cases}
</div>

<div class="stat-label">
Total Cases
</div>

</div>


<div class="stat">

<div class="stat-value">
{active_cases}
</div>

<div class="stat-label">
Active Cases
</div>

</div>


<div class="stat">

<div class="stat-value">
{suspended_cases}
</div>

<div class="stat-label">
Suspension Notices
</div>

</div>


<div class="stat">

<div class="stat-value">
10
</div>

<div class="stat-label">
Upcoming List Limit
</div>

</div>

</div>


<div class="card" style="margin-top:20px">

<h2>
Upcoming / Entered Hearings
</h2>

<div class="table-wrap">

<table>

<thead>

<tr>

<th>
Case
</th>

<th>
Hearing Date
</th>

<th>
Time
</th>

<th>
Status
</th>

<th>
Action
</th>

</tr>

</thead>

<tbody>

{rows}

</tbody>

</table>

</div>

</div>


<div class="card" style="margin-top:20px">

<h2>
Quick Actions
</h2>

<div class="actions">

<a
    href="/staff/case/new"
    class="btn btn-primary"
>
Add Case
</a>

<a
    href="/staff/cases"
    class="btn btn-secondary"
>
Manage All Cases
</a>

<a
    href="/staff/audit"
    class="btn btn-secondary"
>
Audit Log
</a>

</div>

</div>

"""

    return render_page(
        "Staff Dashboard",
        content,
    )


# ================================================================
# STAFF CASE LIST
# ================================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():

    query = clean(
        request.args.get(
            "q",
            "",
        )
    )

    db = get_db()

    try:

        if query:

            cases = db.execute(
                """
                SELECT *
                FROM cases
                WHERE case_number LIKE ?
                OR case_title LIKE ?
                OR plaintiff LIKE ?
                OR defendant LIKE ?
                ORDER BY updated_at DESC
                """,
                (
                    "%" + query + "%",
                    "%" + query + "%",
                    "%" + query + "%",
                    "%" + query + "%",
                ),
            ).fetchall()

        else:

            cases = db.execute(
                """
                SELECT *
                FROM cases
                ORDER BY updated_at DESC
                """
            ).fetchall()

    finally:

        db.close()

    rows = ""

    for case in cases:

        rows += f"""

<tr>

<td>
<strong>
{escape_html(case["case_number"])}
</strong>
</td>

<td>
{escape_html(case["case_title"])}
</td>

<td>
{escape_html(case["hearing_date"]) or "—"}
</td>

<td>
{escape_html(case["status"]) or "—"}
</td>

<td>

<a
    href="/staff/case/{case["id"]}"
    class="btn btn-secondary"
>
Edit
</a>

</td>

</tr>

"""

    if not rows:

        rows = """
<tr>
<td colspan="5" class="empty">
No cases found.
</td>
</tr>
"""

    content = f"""

<div class="card">

<h1>
Manage Cases
</h1>

<form
    method="get"
    style="margin-bottom:20px"
>

<div class="search-row">

<input
    type="search"
    name="q"
    value="{escape_html(query)}"
    placeholder="Search case number, title, plaintiff or defendant"
>

<button
    class="btn btn-primary"
    type="submit"
>
Search
</button>

</div>

</form>

<div class="actions">

<a
    href="/staff/case/new"
    class="btn btn-primary"
>
+ Add Case
</a>

<a
    href="/staff"
    class="btn btn-secondary"
>
Dashboard
</a>

</div>

<hr>

<div class="table-wrap">

<table>

<thead>

<tr>

<th>
Case Number
</th>

<th>
Case Title
</th>

<th>
Hearing
</th>

<th>
Status
</th>

<th>
Action
</th>

</tr>

</thead>

<tbody>

{rows}

</tbody>

</table>

</div>

</div>

"""

    return render_page(
        "Manage Cases",
        content,
    )


# ================================================================
# NEW CASE
# ================================================================

@app.route("/staff/case/new", methods=["GET", "POST"])
@staff_required
def new_case():

    if request.method == "POST":

        data = read_case_form()

        required = [
            data["case_number"],
            data["case_title"],
        ]

        if not all(required):

            flash(
                "Case number and case title are required.",
                "warning",
            )

        else:

            db = get_db()

            try:

                db.execute(
                    """
                    INSERT INTO cases
                    (
                        case_number,
                        case_title,
                        case_type,
                        plaintiff,
                        defendant,
                        hearing_date,
                        hearing_time,
                        courtroom,
                        status,
                        suspension_status,
                        suspension_details,
                        public_notes,
                        private_notes,
                        created_at,
                        updated_at
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["case_number"],
                        data["case_title"],
                        data["case_type"],
                        data["plaintiff"],
                        data["defendant"],
                        data["hearing_date"],
                        data["hearing_time"],
                        data["courtroom"],
                        data["status"],
                        data["suspension_status"],
                        data["suspension_details"],
                        data["public_notes"],
                        data["private_notes"],
                        now_string(),
                        now_string(),
                    ),
                )

                db.commit()

                log_action(
                    "Created case",
                    data["case_number"],
                )

                flash(
                    "Case successfully created.",
                    "success",
                )

                return redirect(
                    url_for(
                        "dashboard"
                    )
                )

            except sqlite3.IntegrityError:

                flash(
                    "That case number already exists.",
                    "danger",
                )

            finally:

                db.close()

    content = case_form_html(
        None,
        "Add New Case",
        "/staff/case/new",
    )

    return render_page(
        "Add Case",
        content,
    )


# ================================================================
# EDIT CASE
# ================================================================

@app.route(
    "/staff/case/<int:case_id>",
    methods=["GET", "POST"],
)
@staff_required
def edit_case(case_id):

    case = get_case(case_id)

    if not case:

        abort(404)

    if request.method == "POST":

        data = read_case_form()

        if not data["case_number"] or not data["case_title"]:

            flash(
                "Case number and case title are required.",
                "warning",
            )

        else:

            db = get_db()

            try:

                db.execute(
                    """
                    UPDATE cases
                    SET
                        case_number = ?,
                        case_title = ?,
                        case_type = ?,
                        plaintiff = ?,
                        defendant = ?,
                        hearing_date = ?,
                        hearing_time = ?,
                        courtroom = ?,
                        status = ?,
                        suspension_status = ?,
                        suspension_details = ?,
                        public_notes = ?,
                        private_notes = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        data["case_number"],
                        data["case_title"],
                        data["case_type"],
                        data["plaintiff"],
                        data["defendant"],
                        data["hearing_date"],
                        data["hearing_time"],
                        data["courtroom"],
                        data["status"],
                        data["suspension_status"],
                        data["suspension_details"],
                        data["public_notes"],
                        data["private_notes"],
                        now_string(),
                        case_id,
                    ),
                )

                db.commit()

                log_action(
                    "Updated case",
                    data["case_number"],
                )

                flash(
                    "Case updated successfully.",
                    "success",
                )

                return redirect(
                    url_for(
                        "edit_case",
                        case_id=case_id,
                    )
                )

            except sqlite3.IntegrityError:

                flash(
                    "Another case already uses that case number.",
                    "danger",
                )

            finally:

                db.close()

            case = get_case(case_id)

    documents = get_case_documents(
        case_id
    )

    content = case_form_html(
        case,
        "Edit Case",
        f"/staff/case/{case_id}",
        documents,
    )

    return render_page(
        "Edit Case",
        content,
    )


# ================================================================
# CASE FORM
# ================================================================

def read_case_form():

    return {

        "case_number":
            clean(
                request.form.get(
                    "case_number"
                )
            ),

        "case_title":
            clean(
                request.form.get(
                    "case_title"
                )
            ),

        "case_type":
            clean(
                request.form.get(
                    "case_type"
                )
            ),

        "plaintiff":
            clean(
                request.form.get(
                    "plaintiff"
                )
            ),

        "defendant":
            clean(
                request.form.get(
                    "defendant"
                )
            ),

        "hearing_date":
            clean(
                request.form.get(
                    "hearing_date"
                )
            ),

        "hearing_time":
            clean(
                request.form.get(
                    "hearing_time"
                )
            ),

        "courtroom":
            clean(
                request.form.get(
                    "courtroom"
                )
            ),

        "status":
            clean(
                request.form.get(
                    "status"
                )
            ) or "Active",

        "suspension_status":
            clean(
                request.form.get(
                    "suspension_status"
                )
            ) or "No official suspension announced",

        "suspension_details":
            clean(
                request.form.get(
                    "suspension_details"
                )
            ),

        "public_notes":
            clean(
                request.form.get(
                    "public_notes"
                )
            ),

        "private_notes":
            clean(
                request.form.get(
                    "private_notes"
                )
            ),

    }


def value_from_case(case, key):

    if not case:

        return ""

    return escape_html(
        case[key] or ""
    )


def case_form_html(
    case,
    heading,
    action,
    documents=None,
):

    if documents is None:

        documents = []

    documents_html = ""

    for document in documents:

        public_text = (
            "Public"
            if document["is_public"]
            else "Private"
        )

        documents_html += f"""

<div class="document">

<div>

<strong>
{escape_html(document["original_filename"])}
</strong>

<br>

<span class="small muted">
{public_text}
</span>

</div>

<div class="actions">

<a
    class="btn btn-secondary"
    href="/staff/documents/{document["id"]}"
>
Open
</a>

<form
    method="post"
    action="/staff/documents/{document["id"]}/delete"
    style="display:inline"
>

<button
    class="btn btn-danger"
    type="submit"
    onclick="return confirm('Delete this document?');"
>
Delete
</button>

</form>

</div>

</div>

"""

    if not documents_html:

        documents_html = """
<p class="muted">
No documents attached to this case.
</p>
"""

    if case:

        delete_section = f"""

<hr>

<h2>
Danger Zone
</h2>

<p class="muted">
Deleting a case permanently removes the case and its
associated document records from this application.
Use this only when authorized.
</p>

<form
    method="post"
    action="/staff/case/{case["id"]}/delete"
>

<button
    type="submit"
    class="btn btn-danger"
    onclick="
        return confirm(
            'Are you sure you want to permanently delete this case?'
        );
    "
>
Delete This Case
</button>

</form>

"""

    else:

        delete_section = ""

    return f"""

<div class="card">

<h1>
{escape_html(heading)}
</h1>

<p class="muted">
Enter only information that authorized court staff
are permitted to manage.
</p>

<form
    method="post"
    action="{action}"
>

<div class="form-grid">

<div class="field">

<label>
Case Number *
</label>

<input
    name="case_number"
    type="text"
    required
    value="{value_from_case(case, 'case_number')}"
>

</div>


<div class="field">

<label>
Case Title *
</label>

<input
    name="case_title"
    type="text"
    required
    value="{value_from_case(case, 'case_title')}"
>

</div>


<div class="field">

<label>
Case Type
</label>

<input
    name="case_type"
    type="text"
    placeholder="Example: Criminal / Civil"
    value="{value_from_case(case, 'case_type')}"
>

</div>


<div class="field">

<label>
Courtroom
</label>

<input
    name="courtroom"
    type="text"
    value="{value_from_case(case, 'courtroom')}"
>

</div>


<div class="field">

<label>
Plaintiff / Complainant
</label>

<input
    name="plaintiff"
    type="text"
    value="{value_from_case(case, 'plaintiff')}"
>

</div>


<div class="field">

<label>
Defendant / Respondent
</label>

<input
    name="defendant"
    type="text"
    value="{value_from_case(case, 'defendant')}"
>

</div>


<div class="field">

<label>
Hearing Date
</label>

<input
    name="hearing_date"
    type="date"
    value="{value_from_case(case, 'hearing_date')}"
>

</div>


<div class="field">

<label>
Hearing Time
</label>

<input
    name="hearing_time"
    type="time"
    value="{value_from_case(case, 'hearing_time')}"
>

</div>


<div class="field">

<label>
Status
</label>

<select name="status">

<option
    {"selected" if not case or case["status"] == "Active" else ""}
>
Active
</option>

<option
    {"selected" if case and case["status"] == "Pending" else ""}
>
Pending
</option>

<option
    {"selected" if case and case["status"] == "Resolved" else ""}
>
Resolved
</option>

<option
    {"selected" if case and case["status"] == "Closed" else ""}
>
Closed
</option>

<option
    {"selected" if case and case["status"] == "Archived" else ""}
>
Archived
</option>

</select>

</div>


<div class="field">

<label>
Suspension Status
</label>

<select name="suspension_status">

<option
    {"selected" if not case or case["suspension_status"] == "No official suspension announced" else ""}
>
No official suspension announced
</option>

<option
    {"selected" if case and case["suspension_status"] == "Official suspension announced" else ""}
>
Official suspension announced
</option>

<option
    {"selected" if case and case["suspension_status"] == "Hearing postponed" else ""}
>
Hearing postponed
</option>

<option
    {"selected" if case and case["suspension_status"] == "To be confirmed" else ""}
>
To be confirmed
</option>

</select>

</div>


<div class="field form-full">

<label>
Suspension Details
</label>

<textarea
    name="suspension_details"
>{value_from_case(case, 'suspension_details')}</textarea>

</div>


<div class="field form-full">

<label>
Public Notes
</label>

<textarea
    name="public_notes"
>{value_from_case(case, 'public_notes')}</textarea>

</div>


<div class="field form-full">

<label>
Private Staff Notes
</label>

<textarea
    name="private_notes"
>{value_from_case(case, 'private_notes')}</textarea>

</div>

</div>


<div class="actions">

<button
    type="submit"
    class="btn btn-primary"
>
Save Case
</button>

<a
    href="/staff"
    class="btn btn-secondary"
>
Cancel
</a>

</div>

</form>

{delete_section}

</div>


<div class="card" style="margin-top:20px">

<h2>
Documents
</h2>

{documents_html}

<form
    method="post"
    action="/staff/case/{case["id"] if case else 0}/upload"
    enctype="multipart/form-data"
    style="margin-top:20px"
>

<div class="field">

<label>
Upload Document
</label>

<input
    type="file"
    name="document"
    required
>

</div>

<div class="field" style="margin-top:15px">

<label>

<input
    type="checkbox"
    name="is_public"
    value="1"
    style="width:auto"
>

 Mark this document as publicly accessible

</label>

</div>

<div class="actions">

<button
    class="btn btn-secondary"
    type="submit"
    {"disabled" if not case else ""}
>
Upload Document
</button>

</div>

</form>

<p class="small muted">

Only mark a document public if authorized court personnel
have determined that it may be made available through the
public website.

</p>

</div>

"""


# ================================================================
# CASE DOCUMENTS
# ================================================================

def get_case_documents(case_id):

    db = get_db()

    try:

        return db.execute(
            """
            SELECT *
            FROM documents
            WHERE case_id = ?
            ORDER BY uploaded_at DESC
            """,
            (case_id,),
        ).fetchall()

    finally:

        db.close()


# ================================================================
# UPLOAD DOCUMENT
# ================================================================

@app.route(
    "/staff/case/<int:case_id>/upload",
    methods=["POST"],
)
@staff_required
def upload_document(case_id):

    case = get_case(case_id)

    if not case:

        abort(404)

    uploaded = request.files.get(
        "document"
    )

    if not uploaded or not uploaded.filename:

        flash(
            "Please select a document.",
            "warning",
        )

        return redirect(
            url_for(
                "edit_case",
                case_id=case_id,
            )
        )

    original_filename = uploaded.filename

    extension = Path(
        original_filename
    ).suffix.lower()

    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".doc",
        ".docx",
        ".txt",
    }

    if extension not in allowed_extensions:

        flash(
            "That file type is not allowed.",
            "danger",
        )

        return redirect(
            url_for(
                "edit_case",
                case_id=case_id,
            )
        )

    stored_filename = (
        secrets.token_hex(20)
        + extension
    )

    destination = (
        UPLOAD_DIR
        / stored_filename
    )

    uploaded.save(destination)

    is_public = (
        1
        if request.form.get(
            "is_public"
        )
        else 0
    )

    db = get_db()

    try:

        db.execute(
            """
            INSERT INTO documents
            (
                case_id,
                original_filename,
                stored_filename,
                is_public,
                uploaded_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                case_id,
                original_filename,
                stored_filename,
                is_public,
                now_string(),
            ),
        )

        db.commit()

    finally:

        db.close()

    log_action(
        "Uploaded document",
        case["case_number"],
    )

    flash(
        "Document uploaded successfully.",
        "success",
    )

    return redirect(
        url_for(
            "edit_case",
            case_id=case_id,
        )
    )


# ================================================================
# STAFF DOCUMENT VIEW
# ================================================================

@app.route(
    "/staff/documents/<int:document_id>"
)
@staff_required
def staff_document(document_id):

    db = get_db()

    try:

        document = db.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

    finally:

        db.close()

    if not document:

        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        document["stored_filename"],
        as_attachment=False,
    )


# ================================================================
# DELETE DOCUMENT
# ================================================================

@app.route(
    "/staff/documents/<int:document_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_document(document_id):

    db = get_db()

    try:

        document = db.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

        if not document:

            abort(404)

        case = db.execute(
            """
            SELECT *
            FROM cases
            WHERE id = ?
            """,
            (document["case_id"],),
        ).fetchone()

        db.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (document_id,),
        )

        db.commit()

    finally:

        db.close()

    filepath = (
        UPLOAD_DIR
        / document["stored_filename"]
    )

    try:

        if filepath.exists():

            filepath.unlink()

    except OSError:

        pass

    log_action(
        "Deleted document",
        case["case_number"]
        if case
        else "",
    )

    flash(
        "Document deleted.",
        "success",
    )

    return redirect(
        url_for(
            "edit_case",
            case_id=document["case_id"],
        )
    )


# ================================================================
# DELETE CASE
# ================================================================

@app.route(
    "/staff/case/<int:case_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_case(case_id):

    case = get_case(case_id)

    if not case:

        abort(404)

    documents = get_case_documents(
        case_id
    )

    db = get_db()

    try:

        db.execute(
            """
            DELETE FROM cases
            WHERE id = ?
            """,
            (case_id,),
        )

        db.commit()

    finally:

        db.close()

    for document in documents:

        filepath = (
            UPLOAD_DIR
            / document["stored_filename"]
        )

        try:

            if filepath.exists():

                filepath.unlink()

        except OSError:

            pass

    log_action(
        "Deleted case",
        case["case_number"],
    )

    flash(
        "The case has been deleted.",
        "success",
    )

    return redirect(
        url_for("dashboard")
    )


# ================================================================
# AUDIT LOG
# ================================================================

@app.route("/staff/audit")
@staff_required
def audit_log():

    db = get_db()

    try:

        logs = db.execute(
            """
            SELECT *
            FROM audit_logs
            ORDER BY id DESC
            LIMIT 250
            """
        ).fetchall()

    finally:

        db.close()

    rows = ""

    for item in logs:

        rows += f"""

<tr>

<td>
{escape_html(item["created_at"])}
</td>

<td>
{escape_html(item["staff_username"])}
</td>

<td>
{escape_html(item["action"])}
</td>

<td>
{escape_html(item["case_number"]) or "—"}
</td>

</tr>

"""

    if not rows:

        rows = """
<tr>
<td colspan="4" class="empty">
No audit entries yet.
</td>
</tr>
"""

    content = f"""

<div class="card">

<h1>
Staff Audit Log
</h1>

<p class="muted">
Recent system actions performed by logged-in staff.
</p>

<div class="table-wrap">

<table>

<thead>

<tr>

<th>
Date / Time
</th>

<th>
Staff
</th>

<th>
Action
</th>

<th>
Case Number
</th>

</tr>

</thead>

<tbody>

{rows}

</tbody>

</table>

</div>

<div class="actions">

<a
    href="/staff"
    class="btn btn-secondary"
>
Back to Dashboard
</a>

</div>

</div>

"""

    return render_page(
        "Audit Log",
        content,
    )


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route("/health")
def health():

    return jsonify(
        {
            "status": "ok",
            "service": "MCTC Silang-Amadeo Case Information System",
        }
    )


# ================================================================
# 404 PAGE
# ================================================================

@app.errorhandler(404)
def not_found(error):

    content = """

<div class="card">

<h1>
404 - Page Not Found
</h1>

<p class="muted">
The page you requested does not exist.
</p>

<div class="actions">

<a
    href="/"
    class="btn btn-primary"
>
Go Home
</a>

<a
    href="/cases"
    class="btn btn-secondary"
>
Search Cases
</a>

</div>

</div>

"""

    return render_page(
        "Not Found",
        content,
    ), 404


# ================================================================
# 413 FILE TOO LARGE
# ================================================================

@app.errorhandler(413)
def file_too_large(error):

    content = """

<div class="card">

<h1>
File Too Large
</h1>

<p class="muted">
The uploaded file is larger than the allowed limit.
The maximum upload size is 16 MB.
</p>

<a
    href="/staff"
    class="btn btn-primary"
>
Back to Dashboard
</a>

</div>

"""

    return render_page(
        "File Too Large",
        content,
    ), 413


# ================================================================
# HTML ESCAPING
# ================================================================

def escape_html(value):

    value = str(
        value if value is not None else ""
    )

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ================================================================
# SECURITY HEADERS
# ================================================================

@app.after_request
def security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    return response


# ================================================================
# APPLICATION STARTUP
# ================================================================

init_database()

create_initial_staff()


# ================================================================
# LOCAL DEVELOPMENT
# ================================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
