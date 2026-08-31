import os
import sqlite3
import secrets
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
    render_template_string,
    abort,
    send_from_directory,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# MCTC SILANG-AMADEO, CAVITE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "mctc.db"

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = STATIC_DIR / "uploads"

STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


# ============================================================
# COURT INFORMATION
# ============================================================

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

COURT_ADDRESS = (
    "PNP Bldg, Plaza Libertad, Poblacion 2, "
    "Silang, Cavite"
)

COURT_PHONE = "09284621305"

COURT_EMAIL = "mctc2sad000@judiciary.gov.ph"

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/"
    "?api=1&query=PNP+Bldg+Plaza+Libertad+"
    "Poblacion+2+Silang+Cavite"
)

LOGO = "image0.png"


# ============================================================
# FILE TYPES
# ============================================================

ALLOWED_FILES = {
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


# ============================================================
# DATABASE
# ============================================================

def get_db():
    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def current_time():
    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def init_database():

    db = get_db()

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
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
            courtroom TEXT NOT NULL DEFAULT '',
            hearing_nature TEXT NOT NULL DEFAULT '',
            hearing_status TEXT NOT NULL DEFAULT 'Scheduled',
            remarks TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tuesday_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendar_date TEXT NOT NULL,
            calendar_time TEXT NOT NULL,
            case_number TEXT NOT NULL,
            last_name TEXT NOT NULL,
            parties TEXT NOT NULL,
            hearing_nature TEXT NOT NULL,
            courtroom TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Scheduled',
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
            staff_username TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )

    # --------------------------------------------------------
    # REQUIREMENTS PLACEHOLDERS
    # --------------------------------------------------------

    requirement_defaults = [
        (
            "bond",
            "Requirements for Bonds",
            "Mga Kinakailangan para sa Bonds",
            "Not yet uploaded",
            "Hindi pa naiu-upload",
        ),
        (
            "clearance",
            "Requirements for Clearance",
            "Mga Kinakailangan para sa Clearance",
            "Not yet uploaded",
            "Hindi pa naiu-upload",
        ),
    ]

    for item in requirement_defaults:

        existing = db.execute(
            """
            SELECT id
            FROM requirements
            WHERE category = ?
            """,
            (item[0],)
        ).fetchone()

        if existing is None:

            db.execute(
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
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    current_time(),
                )
            )

    db.commit()

    db.close()


init_database()


# ============================================================
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {
    "en": {
        "home": "Home",
        "about": "About Us",
        "news": "News and Announcements",
        "contact": "Contact Us",
        "staff": "Staff Login",
        "search": "Search Cases",
        "calendar": "Tuesday Calendar",
        "laws": "Laws, Decisions and Rules",
        "bonds": "Bond Requirements",
        "clearance": "Clearance Requirements",
        "login": "Login",
        "logout": "Logout",
        "dashboard": "Staff Dashboard",
        "case": "Case",
        "cases": "Cases",
        "save": "Save",
        "delete": "Delete",
        "edit": "Edit",
        "cancel": "Cancel",
        "add": "Add",
        "view": "View",
        "search_case": "Search for a Case",
        "case_number": "Case Number",
        "last_name": "Last Name / Party",
        "search_button": "Search Case",
        "both_required": (
            "Both the case number and last name / party "
            "are required."
        ),
        "how_search": "How to Search",
        "step1": (
            "Enter the complete case number."
        ),
        "step2": (
            "Enter the last name of a party."
        ),
        "step3": (
            "Both fields are required."
        ),
        "step4": (
            "Click Search Case."
        ),
        "no_results": "No matching public case was found.",
        "hearing": "Hearing",
        "hearings": "Hearings",
        "hearing_date": "Hearing Date",
        "hearing_time": "Hearing Time",
        "hearing_nature": "Nature of Hearing",
        "hearing_status": "Hearing Status",
        "courtroom": "Courtroom",
        "remarks": "Remarks",
        "notice": "Notice",
        "notices": "Notices",
        "upload": "Upload",
        "attachment": "Photo / Document",
        "suspension": "Suspension Information",
        "nature": "Nature",
        "status": "Status",
        "parties": "Parties",
        "title": "Title",
        "description": "Description",
        "public_information": "Public Information",
        "private_notes": "Private Staff Notes",
        "login_required": (
            "Please log in as authorized court staff."
        ),
        "invalid_login": (
            "Invalid staff username or password."
        ),
        "welcome_staff": "Welcome, Court Staff",
        "quick_actions": "Quick Actions",
        "add_case": "Add New Case",
        "manage_cases": "Manage Cases",
        "manage_calendar": "Manage Tuesday Calendar",
        "manage_notices": "Manage Notices",
        "manage_laws": "Manage Legal Resources",
        "manage_requirements": "Manage Requirements",
        "password": "Password",
        "username": "Username",
        "security": "Security",
        "credentials_hidden": (
            "Your username and password are not displayed "
            "on public pages."
        ),
        "google_maps": "Open Google Maps",
        "phone": "Telephone",
        "email": "Email",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. All rights reserved."
        ),
        "not_yet_uploaded": "Not yet uploaded",
    },

    "fil": {
        "home": "Home",
        "about": "Tungkol sa Amin",
        "news": "Balita at mga Anunsyo",
        "contact": "Makipag-ugnayan",
        "staff": "Staff Login",
        "search": "Maghanap ng Kaso",
        "calendar": "Kalendaryo ng Martes",
        "laws": "Mga Batas, Desisyon at Alituntunin",
        "bonds": "Mga Kinakailangan para sa Bonds",
        "clearance": "Mga Kinakailangan para sa Clearance",
        "login": "Login",
        "logout": "Mag-Logout",
        "dashboard": "Dashboard ng Staff",
        "case": "Kaso",
        "cases": "Mga Kaso",
        "save": "I-save",
        "delete": "Burahin",
        "edit": "I-edit",
        "cancel": "Kanselahin",
        "add": "Magdagdag",
        "view": "Tingnan",
        "search_case": "Maghanap ng Kaso",
        "case_number": "Numero ng Kaso",
        "last_name": "Apelyido / Partido",
        "search_button": "Maghanap",
        "both_required": (
            "Kinakailangan ang parehong case number "
            "at apelyido / pangalan ng partido."
        ),
        "how_search": "Paano Maghanap",
        "step1": "Ilagay ang buong case number.",
        "step2": "Ilagay ang apelyido ng isang partido.",
        "step3": "Kinakailangan ang parehong field.",
        "step4": "I-click ang Maghanap.",
        "no_results": (
            "Walang nakitang pampublikong kaso."
        ),
        "hearing": "Pagdinig",
        "hearings": "Mga Pagdinig",
        "hearing_date": "Petsa ng Pagdinig",
        "hearing_time": "Oras ng Pagdinig",
        "hearing_nature": "Uri ng Pagdinig",
        "hearing_status": "Katayuan ng Pagdinig",
        "courtroom": "Silid ng Hukuman",
        "remarks": "Mga Tala",
        "notice": "Abiso",
        "notices": "Mga Abiso",
        "upload": "Mag-upload",
        "attachment": "Larawan / Dokumento",
        "suspension": "Impormasyon sa Suspensyon",
        "nature": "Uri",
        "status": "Katayuan",
        "parties": "Mga Partido",
        "title": "Pamagat",
        "description": "Deskripsyon",
        "public_information": "Pampublikong Impormasyon",
        "private_notes": "Pribadong Tala ng Staff",
        "login_required": (
            "Mag-login bilang awtorisadong staff ng hukuman."
        ),
        "invalid_login": (
            "Mali ang username o password ng staff."
        ),
        "welcome_staff": (
            "Maligayang Pagdating, Kawani ng Hukuman"
        ),
        "quick_actions": "Mabilis na Aksyon",
        "add_case": "Magdagdag ng Bagong Kaso",
        "manage_cases": "Pamahalaan ang mga Kaso",
        "manage_calendar": (
            "Pamahalaan ang Kalendaryo ng Martes"
        ),
        "manage_notices": "Pamahalaan ang mga Abiso",
        "manage_laws": (
            "Pamahalaan ang Legal Resources"
        ),
        "manage_requirements": (
            "Pamahalaan ang mga Kinakailangan"
        ),
        "password": "Password",
        "username": "Username",
        "security": "Seguridad",
        "credentials_hidden": (
            "Hindi ipinapakita ang username at password "
            "sa mga pampublikong pahina."
        ),
        "google_maps": "Buksan ang Google Maps",
        "phone": "Telepono",
        "email": "Email",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. Lahat ng karapatan ay nakalaan."
        ),
        "not_yet_uploaded": "Hindi pa naiu-upload",
    },
}


def t(key):
    language = session.get(
        "language",
        "en",
    )

    if language not in TRANSLATIONS:
        language = "en"

    return TRANSLATIONS[language].get(
        key,
        TRANSLATIONS["en"].get(key, key),
    )


# ============================================================
# PAGE RENDERER
# ============================================================

def render_page(
    title,
    body,
):
    language = session.get(
        "language",
        "en",
    )

    theme = session.get(
        "theme",
        "light",
    )

    logged = bool(
        session.get(
            "staff_id"
        )
    )

    logout_area = ""

    if logged:

        logout_area = f"""
        <form
            method="post"
            action="{url_for('logout')}"
            style="display:inline"
        >
            <button
                class="nav-button"
                type="submit"
                onclick="
                    return confirm(
                        '{t("logout")}?'
                    );
                "
            >
                {t("logout")}
            </button>
        </form>
        """

    html = f"""
<!DOCTYPE html>

<html lang="{language}">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="description"
    content="MCTC Silang-Amadeo Court Information Portal"
>

<title>
{title} -
{COURT_NAME}
</title>

<style>

:root {{

    --purple-900: #3b0764;
    --purple-800: #4c1d95;
    --purple-700: #6d28d9;
    --purple-600: #7c3aed;
    --purple-500: #8b5cf6;

    --background: #f8f5fb;
    --surface: #ffffff;
    --surface-two: #f2ebf7;

    --text: #24162d;
    --muted: #66586f;

    --border: #ddd2e4;

    --success: #166534;
    --warning: #92400e;
    --danger: #991b1b;
}}

body.dark {{

    --background: #130d17;
    --surface: #221729;
    --surface-two: #2d1d38;

    --text: #f9f3fc;
    --muted: #d0bfd6;

    --border: #503d59;

    --success: #a7edbb;
    --warning: #ffd38a;
    --danger: #ffb7c1;
}}

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{

    margin: 0;

    background:
        var(--background);

    color:
        var(--text);

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height: 1.65;
}}

a {{
    color: var(--purple-600);
    text-decoration: none;
}}

body.dark a {{
    color: #c4a1ff;
}}

a:hover {{
    text-decoration: underline;
}}

.site-header {{

    background:
        linear-gradient(
            135deg,
            var(--purple-900),
            var(--purple-700),
            var(--purple-500)
        );

    color: white;

    position: sticky;

    top: 0;

    z-index: 1000;

    box-shadow:
        0 8px 25px
        rgba(44, 10, 68, .25);
}}

.header-inner {{

    width:
        min(
            1220px,
            94%
        );

    min-height:
        78px;

    margin:
        auto;

    display:
        flex;

    align-items:
        center;

    gap:
        18px;

    flex-wrap:
        wrap;

    padding:
        12px
        0;
}}

.logo {{

    width:
        60px;

    height:
        60px;

    object-fit:
        contain;

    object-position:
        center;

    border-radius:
        50%;

    background:
        #ffffff;

    padding:
        4px;

    flex-shrink:
        0;
}}

.brand {{
    color: white;
    min-width: 220px;
    flex: 1;
}}

.brand strong {{
    display: block;
    font-size: 15px;
}}

.brand small {{
    display: block;
    opacity: .88;
}}

.nav {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
}}

.nav a,
.nav-button {{

    color: white;

    padding:
        8px
        10px;

    border:
        0;

    background:
        transparent;

    border-radius:
        9px;

    font-size:
        13px;

    font-weight:
        800;

    cursor:
        pointer;

    text-decoration:
        none;
}}

.nav a:hover,
.nav-button:hover {{
    background:
        rgba(
            255,
            255,
            255,
            .13
        );

    text-decoration:
        none;
}}

.container {{

    width:
        min(
            1180px,
            94%
        );

    margin:
        auto;

    padding:
        32px
        0
        70px;
}}

.card {{

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    padding:
        24px;

    margin:
        18px 0;

    box-shadow:
        0 10px 28px
        rgba(
            40,
            15,
            55,
            .07
        );
}}

.hero {{

    padding:
        55px 25px;

    text-align:
        center;

    border-radius:
        24px;

    background:
        linear-gradient(
            135deg,
            var(--purple-900),
            var(--purple-700)
        );

    color:
        white;

    margin:
        20px 0 25px;
}}

.hero h1 {{
    font-size:
        clamp(
            32px,
            5vw,
            57px
        );

    line-height:
        1.05;

    margin:
        10px auto;

    max-width:
        900px;
}}

.hero-logo {{

    width:
        155px;

    height:
        155px;

    object-fit:
        contain;

    margin:
        0 auto 20px;

    display:
        block;
}}

.grid {{

    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                255px,
                1fr
            )
        );

    gap:
        18px;
}}

button,
.button {{

    display:
        inline-block;

    border:
        0;

    border-radius:
        10px;

    padding:
        11px
        16px;

    background:
        var(--purple-700);

    color:
        white;

    font-weight:
        800;

    cursor:
        pointer;

    text-decoration:
        none;
}}

button:hover,
.button:hover {{
    background:
        var(--purple-800);

    color:
        white;

    text-decoration:
        none;
}}

.button.secondary {{
    background:
        var(--surface-two);

    color:
        var(--text);

    border:
        1px solid
        var(--border);
}}

.button.danger,
button.danger {{
    background:
        var(--danger);

    color:
        white;
}}

.actions {{

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        9px;

    margin:
        15px 0;
}}

label {{

    display:
        block;

    font-weight:
        800;

    margin:
        12px 0 5px;
}}

input,
textarea,
select {{

    width:
        100%;

    padding:
        12px;

    border:
        1px solid
        var(--border);

    border-radius:
        10px;

    background:
        var(--surface);

    color:
        var(--text);

    font:
        inherit;
}}

textarea {{
    min-height:
        120px;

    resize:
        vertical;
}}

input:focus,
textarea:focus,
select:focus {{

    outline:
        3px solid
        rgba(
            124,
            58,
            237,
            .2
        );

    border-color:
        var(--purple-600);
}}

.two {{
    display:
        grid;

    grid-template-columns:
        1fr 1fr;

    gap:
        14px;
}}

.notice {{

    padding:
        15px;

    border-left:
        5px solid
        var(--purple-600);

    border-radius:
        10px;

    background:
        var(--surface-two);

    margin:
        12px 0;
}}

.warning {{
    border-left-color:
        #d97706;
}}

.error {{
    border-left-color:
        #b91c1c;
}}

.status {{

    display:
        inline-block;

    background:
        var(--surface-two);

    color:
        var(--purple-800);

    border-radius:
        999px;

    padding:
        4px
        10px;

    font-size:
        12px;

    font-weight:
        900;
}}

body.dark .status {{
    color:
        #e3c7ff;
}}

.table-wrap {{
    overflow-x:
        auto;
}}

table {{
    width:
        100%;

    border-collapse:
        collapse;
}}

th,
td {{
    text-align:
        left;

    padding:
        11px;

    border-bottom:
        1px solid
        var(--border);

    vertical-align:
        top;
}}

th {{
    background:
        var(--surface-two);
}}

.empty {{
    text-align:
        center;

    padding:
        45px
        10px;

    color:
        var(--muted);
}}

.login-box {{
    max-width:
        500px;

    margin:
        50px auto;
}}

footer {{

    border-top:
        1px solid
        var(--border);

    background:
        var(--surface);

    color:
        var(--muted);

    text-align:
        center;

    padding:
        30px
        15px;
}}

@media(max-width:800px) {{

    .header-inner {{
        align-items:
            flex-start;

        flex-direction:
            column;
    }}

    .nav {{
        width:
            100%;
    }}

    .two {{
        grid-template-columns:
            1fr;
    }}

}}

</style>

</head>

<body class="{theme}">

<header class="site-header">

<div class="header-inner">

<img
    class="logo"
    src="{url_for('static', filename=LOGO)}"
    alt="Court logo"
>

<div class="brand">

<strong>
{COURT_NAME}
</strong>

<small>
Official Court Information Portal
</small>

</div>

<nav class="nav">

<a href="{url_for('home')}">
{t("home")}
</a>

<a href="{url_for('about')}">
{t("about")}
</a>

<a href="{url_for('news')}">
{t("news")}
</a>

<a href="{url_for('contact')}">
{t("contact")}
</a>

<a href="{url_for('search_cases')}">
{t("search")}
</a>

<a href="{url_for('public_calendar')}">
{t("calendar")}
</a>

<a href="{url_for('laws')}">
{t("laws")}
</a>

<a href="{url_for('requirements')}">
{t("bonds")}
</a>

<a href="{url_for('staff_login')}">
{t("staff")}
</a>

{logout_area}

</nav>

</div>

</header>


<main class="container">

{render_messages()}

{body}

</main>


<footer>

<strong>
{COURT_NAME}
</strong>

<p>
{COURT_ADDRESS}
</p>

<p>
{COURT_PHONE}
<br>
{COURT_EMAIL}
</p>

<p>
<a
    href="{GOOGLE_MAPS_URL}"
    target="_blank"
    rel="noopener noreferrer"
>
{t("google_maps")}
</a>
</p>

<p>
{t("copyright")}
</p>

</footer>

</body>

</html>
"""

    return html


def render_messages():

    messages = ""

    for category, message in flash_messages():

        messages += f"""
        <div class="notice {category}">
            {escape_html(message)}
        </div>
        """

    return messages


def flash_messages():

    from flask import get_flashed_messages

    return get_flashed_messages(
        with_categories=True
    )


def escape_html(value):

    import html

    return html.escape(
        str(value or ""),
        quote=True,
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    db = get_db()

    notices = db.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).fetchall()

    db.close()

    notice_html = ""

    for notice in notices:

        title = (
            notice["title_fil"]
            if session.get("language") == "fil"
            else notice["title_en"]
        )

        body = (
            notice["body_fil"]
            if session.get("language") == "fil"
            else notice["body_en"]
        )

        notice_html += f"""
        <div class="notice">

            <h3>
                {escape_html(title)}
            </h3>

            <p>
                {escape_html(body)}
            </p>

        </div>
        """

    content = f"""

    <section class="hero">

        <img
            class="hero-logo"
            src="{url_for('static', filename=LOGO)}"
            alt="Official court logo"
        >

        <h1>
            {COURT_NAME}
        </h1>

        <p>
            Search approved public case information,
            view the Tuesday calendar, and read
            official court announcements.
        </p>

        <div class="actions"
             style="justify-content:center;">

            <a
                class="button"
                href="{url_for('search_cases')}"
            >
                🔎
                {t("search_case")}
            </a>

            <a
                class="button secondary"
                href="{url_for('public_calendar')}"
            >
                📅
                {t("calendar")}
            </a>

        </div>

    </section>


    <section class="grid">

        <div class="card">

            <h2>
                🔎
                {t("search_case")}
            </h2>

            <p>
                {t("both_required")}
            </p>

            <a
                class="button"
                href="{url_for('search_cases')}"
            >
                {t("search")}
            </a>

        </div>


        <div class="card">

            <h2>
                📅
                {t("calendar")}
            </h2>

            <p>
                View the Tuesday court calendar
                published by authorized staff.
            </p>

            <a
                class="button"
                href="{url_for('public_calendar')}"
            >
                {t("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                📢
                {t("news")}
            </h2>

            <p>
                Read published court notices,
                announcements and attachments.
            </p>

            <a
                class="button"
                href="{url_for('news')}"
            >
                {t("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                ⚖️
                {t("laws")}
            </h2>

            <p>
                View official legal resources,
                decisions and rules added by staff.
            </p>

            <a
                class="button"
                href="{url_for('laws')}"
            >
                {t("view")}
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            ⚠️
            {t("suspension")}
        </h2>

        <p>
            A case or hearing should not be assumed to
            be suspended, cancelled, or postponed unless
            an official court announcement or authorized
            government notice confirms it.
        </p>

        <a
            class="button secondary"
            href="{url_for('news')}"
        >
            {t("news")}
        </a>

    </section>


    <section class="card">

        <h2>
            📢
            {t("news")}
        </h2>

        {notice_html or '<p class="muted">No notices published yet.</p>'}

    </section>

    """

    return render_page(
        t("home"),
        content,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    content = f"""

    <div class="card">

        <h1>
            {t("about")}
        </h1>

        <h2>
            {COURT_NAME}
        </h2>

        <p>
            This portal is intended to provide approved
            public information concerning cases, court
            announcements, legal resources and the
            Tuesday calendar.
        </p>

        <div class="notice warning">

            <strong>
                Important
            </strong>

            <p>
                Online information does not replace
                official court records, orders,
                notices or certified documents.
            </p>

        </div>

    </div>

    """

    return render_page(
        t("about"),
        content,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact")
def contact():

    content = f"""

    <div class="card">

        <h1>
            {t("contact")}
        </h1>

        <h2>
            {COURT_NAME}
        </h2>

        <p>
            <strong>
                {t("address")}:
            </strong>

            <br>

            {COURT_ADDRESS}

        </p>

        <p>
            <strong>
                {t("phone")}:
            </strong>

            <br>

            <a
                href="tel:{COURT_PHONE}"
            >
                {COURT_PHONE}
            </a>

        </p>

        <p>

            <strong>
                {t("email")}:
            </strong>

            <br>

            <a
                href="mailto:{COURT_EMAIL}"
            >
                {COURT_EMAIL}
            </a>

        </p>

        <a
            class="button"
            href="{GOOGLE_MAPS_URL}"
            target="_blank"
            rel="noopener noreferrer"
        >
            🗺️
            {t("google_maps")}
        </a>

    </div>

    """

    return render_page(
        t("contact"),
        content,
    )


# ============================================================
# NEWS
# ============================================================

@app.route("/news")
def news():

    db = get_db()

    notices = db.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    content = f"""

    <div class="card">

        <h1>
            📢
            {t("news")}
        </h1>

        <p>
            Official notices published by authorized staff.
        </p>

    </div>

    """

    for notice in notices:

        if session.get("language") == "fil":

            title = notice["title_fil"]

            body = notice["body_fil"]

        else:

            title = notice["title_en"]

            body = notice["body_en"]

        attachment_html = ""

        if notice["attachment"]:

            attachment_html = f"""

            <p>

                <a
                    class="button secondary"
                    href="{url_for(
                        'public_upload',
                        filename=notice['attachment']
                    )}"
                >
                    📎
                    Open Attachment
                </a>

            </p>

            """

        content += f"""

        <article class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(body)}
            </p>

            {attachment_html}

        </article>

        """

    if not notices:

        content += """

        <div class="card empty">

            No notices are currently published.

        </div>

        """

    return render_page(
        t("news"),
        content,
    )


# ============================================================
# PUBLIC SEARCH
# ============================================================

@app.route(
    "/search",
    methods=[
        "GET",
        "POST",
    ],
)
def search_cases():

    case = None

    searched = False

    case_number = request.values.get(
        "case_number",
        ""
    ).strip()

    last_name = request.values.get(
        "last_name",
        ""
    ).strip()

    if request.method == "POST":

        searched = True

        # BOTH REQUIRED
        if not case_number or not last_name:

            flash(
                t("both_required"),
                "danger",
            )

        else:

            db = get_db()

            case = db.execute(
                """
                SELECT *
                FROM cases
                WHERE
                    lower(case_number)
                    = lower(?)
                AND
                    lower(last_name)
                    = lower(?)
                """,
                (
                    case_number,
                    last_name,
                ),
            ).fetchone()

            db.close()

            if case is None:

                flash(
                    t("no_results"),
                    "warning",
                )

    content = f"""

    <div class="card">

        <h1>
            🔎
            {t("search_case")}
        </h1>

        <div class="notice">

            <h3>
                {t("how_search")}
            </h3>

            <ol>

                <li>
                    {t("step1")}
                </li>

                <li>
                    {t("step2")}
                </li>

                <li>
                    {t("step3")}
                </li>

                <li>
                    {t("step4")}
                </li>

            </ol>

        </div>


        <form method="post">

            <label>
                {t("case_number")}
            </label>

            <input
                name="case_number"
                value="{escape_html(case_number)}"
                required
                autocomplete="off"
                placeholder="MCTC-2026-001"
            >


            <label>
                {t("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(last_name)}"
                required
                autocomplete="off"
                placeholder="Dela Cruz"
            >


            <button
                type="submit"
            >
                🔎
                {t("search_button")}
            </button>

        </form>

    </div>

    """

    if searched and case:

        content += f"""

        <div class="card">

            <span class="status">
                {escape_html(case["status"])}
            </span>

            <h2>
                {escape_html(case["case_number"])}
            </h2>

            <p>
                <strong>
                    {t("parties")}:
                </strong>

                {escape_html(case["parties"])}
            </p>

            <p>
                <strong>
                    {t("nature")}:
                </strong>

                {escape_html(case["nature"])}
            </p>

            <p>
                {escape_html(case["public_description"])}
            </p>

            <a
                class="button"
                href="{url_for(
                    'public_case',
                    case_id=case['id']
                )}"
            >
                {t("view")}
            </a>

        </div>

        """

    return render_page(
        t("search"),
        content,
    )


# ============================================================
# PUBLIC CASE
# ============================================================

@app.route(
    "/case/<int:case_id>"
)
def public_case(case_id):

    db = get_db()

    case = db.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    hearings = db.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY hearing_date,
                 hearing_time
        """,
        (case_id,),
    ).fetchall()

    db.close()

    if case is None:
        abort(404)

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""

        <div class="notice">

            <h3>
                📅
                {escape_html(
                    hearing["hearing_date"]
                )}
            </h3>

            <p>
                <strong>
                    {t("hearing_time")}:
                </strong>

                {escape_html(
                    hearing["hearing_time"]
                )}
            </p>

            <p>
                <strong>
                    {t("hearing_nature")}:
                </strong>

                {escape_html(
                    hearing["hearing_nature"]
                )}
            </p>

            <p>
                <strong>
                    {t("hearing_status")}:
                </strong>

                {escape_html(
                    hearing["hearing_status"]
                )}
            </p>

            <p>
                <strong>
                    {t("courtroom")}:
                </strong>

                {escape_html(
                    hearing["courtroom"]
                )}
            </p>

        </div>

        """

    if not hearing_html:

        hearing_html = f"""

        <p class="muted">
            No published hearing information.
        </p>

        """

    content = f"""

    <div class="card">

        <h1>
            {escape_html(case["case_number"])}
        </h1>

        <h2>
            {escape_html(case["case_title"])}
        </h2>

        <p>

            <strong>
                {t("parties")}:
            </strong>

            {escape_html(case["parties"])}

        </p>

        <p>

            <strong>
                {t("nature")}:
            </strong>

            {escape_html(case["nature"])}

        </p>

        <p>

            <strong>
                {t("status")}:
            </strong>

            <span class="status">
                {escape_html(case["status"])}
            </span>

        </p>

        <hr>

        <p>
            {escape_html(case["public_description"])}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {t("hearings")}
        </h2>

        {hearing_html}

    </div>

    """

    return render_page(
        t("case"),
        content,
    )


# ============================================================
# TUESDAY CALENDAR
# ============================================================

@app.route(
    "/calendar"
)
def public_calendar():

    db = get_db()

    entries = db.execute(
        """
        SELECT *
        FROM tuesday_calendar
        WHERE public_visible = 1
        ORDER BY calendar_date,
                 calendar_time,
                 id
        """
    ).fetchall()

    db.close()

    rows = ""

    for entry in entries:

        rows += f"""

        <tr>

            <td>
                {escape_html(
                    entry["calendar_date"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["calendar_time"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["case_number"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["parties"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["hearing_nature"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["courtroom"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["status"]
                )}
            </td>

        </tr>

        """

    if not rows:

        rows = """

        <tr>

            <td
                colspan="7"
                class="empty"
            >
                No Tuesday calendar entries
                have been published.
            </td>

        </tr>

        """

    content = f"""

    <div class="card">

        <h1>
            📅
            {t("calendar")}
        </h1>

        <p>
            The calendar below contains entries
            published by authorized court staff.
        </p>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        {t("hearing_date")}
                    </th>

                    <th>
                        {t("hearing_time")}
                    </th>

                    <th>
                        {t("case_number")}
                    </th>

                    <th>
                        {t("parties")}
                    </th>

                    <th>
                        {t("hearing_nature")}
                    </th>

                    <th>
                        {t("courtroom")}
                    </th>

                    <th>
                        {t("status")}
                    </th>

                </tr>

            </thead>

            <tbody>

                {rows}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        t("calendar"),
        content,
    )


# ============================================================
# REQUIREMENTS
# ============================================================

@app.route(
    "/requirements"
)
def requirements():

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY category
        """
    ).fetchall()

    db.close()

    content = """

    <div class="card">

        <h1>
            Requirements
        </h1>

        <p>
            Requirements shown here are only published
            after being entered by authorized staff.
        </p>

    </div>

    """

    for row in rows:

        if session.get("language") == "fil":

            title = row["title_fil"]

            description = (
                row["description_fil"]
                or t("not_yet_uploaded")
            )

        else:

            title = row["title_en"]

            description = (
                row["description_en"]
                or t("not_yet_uploaded")
            )

        attachment = ""

        if row["file_name"]:

            attachment = f"""

            <a
                class="button secondary"
                href="{url_for(
                    'public_upload',
                    filename=row['file_name']
                )}"
            >
                Open Document
            </a>

            """

        content += f"""

        <div class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(description)}
            </p>

            {attachment}

        </div>

        """

    return render_page(
        t("requirements"),
        content,
    )


# ============================================================
# LAWS
# ============================================================

@app.route(
    "/laws"
)
def laws():

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY category,
                 created_at DESC
        """
    ).fetchall()

    db.close()

    content = f"""

    <div class="card">

        <h1>
            ⚖️
            {t("laws")}
        </h1>

        <p>
            This section is designed for staff to add
            links and approved reference documents for
            Philippine laws, Supreme Court decisions,
            rules, and other legal resources.
        </p>

        <div class="notice warning">

            <strong>
                Important:
            </strong>

            <p>
                Legal resources should be verified against
                authoritative sources before being relied upon.
            </p>

        </div>

    </div>

    """

    for row in rows:

        content += f"""

        <div class="card">

            <span class="status">
                {escape_html(row["category"])}
            </span>

            <h2>
                {escape_html(row["title"])}
            </h2>

            <p>
                {escape_html(row["description"])}
            </p>

            """

        if row["source_url"]:

            content += f"""

            <a
                class="button secondary"
                href="{escape_html(row["source_url"])}"
                target="_blank"
                rel="noopener noreferrer"
            >
                Official Source
            </a>

            """

        if row["file_name"]:

            content += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'public_upload',
                    filename=row['file_name']
                )}"
            >
                Open File
            </a>

            """

        content += """

        </div>

        """

    return render_page(
        t("laws"),
        content,
    )


# ============================================================
# STAFF LOGIN
# ============================================================

@app.route(
    "/staff/login",
    methods=[
        "GET",
        "POST",
    ]
)
def staff_login():

    if session.get("staff_id"):

        return redirect(
            url_for("staff_dashboard")
        )

    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        password = request.form.get(
            "password",
            "",
        )

        configured_user = os.environ.get(
            "STAFF_USERNAME"
        )

        configured_password = os.environ.get(
            "STAFF_PASSWORD"
        )

        if configured_user and configured_password:

            if (
                secrets.compare_digest(
                    username,
                    configured_user,
                )
                and secrets.compare_digest(
                    password,
                    configured_password,
                )
            ):

                session.clear()

                session["staff_id"] = "environment"

                session["staff_username"] = username

                session["staff_role"] = "staff"

                return redirect(
                    url_for(
                        "staff_dashboard"
                    )
                )

        db = get_db()

        staff = db.execute(
            """
            SELECT *
            FROM staff
            WHERE username = ?
            AND active = 1
            """,
            (username,),
        ).fetchone()

        db.close()

        if staff and check_password_hash(
            staff["password_hash"],
            password,
        ):

            session.clear()

            session["staff_id"] = staff["id"]

            session["staff_username"] = staff["username"]

            session["staff_role"] = staff["role"]

            return redirect(
                url_for(
                    "staff_dashboard"
                )
            )

        flash(
            t("invalid_login"),
            "danger",
        )

    content = f"""

    <div class="login-box card">

        <img
            src="{url_for(
                'static',
                filename=LOGO
            )}"
            class="hero-logo"
            alt="Court logo"
        >

        <h1>
            🔐
            {t("login")}
        </h1>

        <p class="muted">
            Authorized staff only.
        </p>

        <form
            method="post"
            autocomplete="off"
        >

            <label>
                {t("username")}
            </label>

            <input
                type="text"
                name="username"
                autocomplete="username"
                required
            >

            <label>
                {t("password")}
            </label>

            <input
                type="password"
                name="password"
                autocomplete="current-password"
                required
            >

            <br>

            <button
                type="submit"
            >
                {t("login")}
            </button>

        </form>

        <div class="notice">

            {t("credentials_hidden")}

        </div>

    </div>

    """

    return render_page(
        t("login"),
        content,
    )


# ============================================================
# STAFF LOGOUT
# ============================================================

@app.route(
    "/staff/logout",
    methods=[
        "GET",
        "POST",
    ]
)
def logout():

    session.clear()

    response = redirect(
        url_for("home")
    )

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    flash(
        "You have been logged out.",
        "success",
    )

    return response


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route(
    "/staff"
)
@app.route(
    "/staff/dashboard"
)
@staff_required
def staff_dashboard():

    db = get_db()

    total_cases = db.execute(
        "SELECT COUNT(*) AS n FROM cases"
    ).fetchone()["n"]

    total_notices = db.execute(
        "SELECT COUNT(*) AS n FROM notices"
    ).fetchone()["n"]

    total_calendar = db.execute(
        "SELECT COUNT(*) AS n FROM tuesday_calendar"
    ).fetchone()["n"]

    total_laws = db.execute(
        "SELECT COUNT(*) AS n FROM legal_resources"
    ).fetchone()["n"]

    db.close()

    content = f"""

    <section class="hero">

        <h1>
            {t("welcome_staff")}
        </h1>

        <p>
            Manage approved public information
            from one place.
        </p>

    </section>


    <section class="grid">

        <div class="card">

            <h2>
                📋
                {t("cases")}
            </h2>

            <h1>
                {total_cases}
            </h1>

        </div>


        <div class="card">

            <h2>
                📢
                {t("notices")}
            </h2>

            <h1>
                {total_notices}
            </h1>

        </div>


        <div class="card">

            <h2>
                📅
                {t("calendar")}
            </h2>

            <h1>
                {total_calendar}
            </h1>

        </div>


        <div class="card">

            <h2>
                ⚖️
                {t("laws")}
            </h2>

            <h1>
                {total_laws}
            </h1>

        </div>

    </section>


    <section class="card">

        <h2>
            ⚡
            {t("quick_actions")}
        </h2>

        <div class="grid">

            <a
                class="card"
                href="{url_for('staff_cases')}"
            >
                📋
                <h3>
                    {t("manage_cases")}
                </h3>
                <p>
                    Search, edit and delete case records.
                </p>
            </a>


            <a
                class="card"
                href="{url_for('staff_calendar')}"
            >
                📅
                <h3>
                    {t("manage_calendar")}
                </h3>
                <p>
                    Manage the Tuesday calendar.
                </p>
            </a>


            <a
                class="card"
                href="{url_for('staff_notices')}"
            >
                📢
                <h3>
                    {t("manage_notices")}
                </h3>
                <p>
                    Upload photos and documents with notices.
                </p>
            </a>


            <a
                class="card"
                href="{url_for('staff_laws')}"
            >
                ⚖️
                <h3>
                    {t("manage_laws")}
                </h3>
                <p>
                    Add laws, decisions and rules.
                </p>
            </a>


            <a
                class="card"
                href="{url_for('staff_requirements')}"
            >
                📄
                <h3>
                    {t("manage_requirements")}
                </h3>
                <p>
                    Manage bond and clearance requirements.
                </p>
            </a>

        </div>

    </section>

    """

    return render_page(
        t("dashboard"),
        content,
    )


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route(
    "/staff/cases"
)
@staff_required
def staff_cases():

    db = get_db()

    cases = db.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        """
    ).fetchall()

    db.close()

    rows = ""

    for case in cases:

        rows += f"""

        <tr>

            <td>
                {escape_html(case["case_number"])}
            </td>

            <td>
                {escape_html(case["parties"])}
            </td>

            <td>
                {escape_html(case["case_title"])}
            </td>

            <td>
                {escape_html(case["status"])}
            </td>

            <td>

                <a
                    class="button secondary"
                    href="{url_for(
                        'staff_edit_case',
                        case_id=case['id']
                    )}"
                >
                    {t("edit")}
                </a>

                <form
                    method="post"
                    action="{url_for(
                        'staff_delete_case',
                        case_id=case['id']
                    )}"
                    style="display:inline"
                    onsubmit="
                        return confirm(
                            'Delete this case permanently?'
                        );
                    "
                >

                    <button
                        class="danger"
                        type="submit"
                    >
                        {t("delete")}
                    </button>

                </form>

            </td>

        </tr>

        """

    content = f"""

    <div class="split">

        <h1>
            {t("manage_cases")}
        </h1>

    </div>


    <div class="card">

        <a
            class="button"
            href="{url_for('staff_add_case')}"
        >
            ➕
            {t("add_case")}
        </a>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        {t("case_number")}
                    </th>

                    <th>
                        {t("parties")}
                    </th>

                    <th>
                        {t("title")}
                    </th>

                    <th>
                        {t("status")}
                    </th>

                    <th>
                        Actions
                    </th>

                </tr>

            </thead>

            <tbody>

                {rows or '''
                <tr>
                    <td colspan="5" class="empty">
                        No cases have been added.
                    </td>
                </tr>
                '''}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        t("manage_cases"),
        content,
    )


# ============================================================
# ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=[
        "GET",
        "POST",
    ]
)
@staff_required
def staff_add_case():

    if request.method == "POST":

        case_number = (
            request.form
            .get(
                "case_number",
                "",
            )
            .strip()
        )

        last_name = (
            request.form
            .get(
                "last_name",
                "",
            )
            .strip()
        )

        parties = (
            request.form
            .get(
                "parties",
                "",
            )
            .strip()
        )

        case_title = (
            request.form
            .get(
                "case_title",
                "",
            )
            .strip()
        )

        case_type = (
            request.form
            .get(
                "case_type",
                "",
            )
            .strip()
        )

        status = (
            request.form
            .get(
                "status",
                "Pending",
            )
            .strip()
        )

        public_description = (
            request.form
            .get(
                "public_description",
                "",
            )
            .strip()
        )

        internal_notes = (
            request.form
            .get(
                "internal_notes",
                "",
            )
            .strip()
        )

        if not case_number:

            flash(
                "Case number is required.",
                "danger",
            )

            return redirect(
                url_for("staff_add_case")
            )

        if not last_name:

            flash(
                "Last name is required.",
                "danger",
            )

            return redirect(
                url_for("staff_add_case")
            )

        if not parties:

            flash(
                "Party information is required.",
                "danger",
            )

            return redirect(
                url_for("staff_add_case")
            )

        if not case_title:

            flash(
                "Case title is required.",
                "danger",
            )

            return redirect(
                url_for("staff_add_case")
            )

        db = get_db()

        try:

            db.execute(
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
                (
                    case_number,
                    last_name,
                    parties,
                    case_title,
                    case_type,
                    status,
                    public_description,
                    internal_notes,
                    current_time(),
                    current_time(),
                )
            )

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            flash(
                "That case number already exists.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_add_case"
                )
            )

        db.close()

        flash(
            "Case created successfully.",
            "success",
        )

        return redirect(
            url_for("staff_cases")
        )

    content = f"""

    <div class="form card">

        <h1>
            {t("add_case")}
        </h1>

        <form method="post">

            <label>
                {t("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {t("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {t("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                {t("title")}
            </label>

            <input
                name="case_title"
                required
            >


            <label>
                Case Type
            </label>

            <input
                name="case_type"
            >


            <label>
                {t("status")}
            </label>

            <select name="status">

                <option>
                    Pending
                </option>

                <option>
                    Active
                </option>

                <option>
                    Scheduled
                </option>

                <option>
                    Resolved
                </option>

                <option>
                    Final
                </option>

                <option>
                    Dismissed
                </option>

            </select>


            <label>
                {t("public_information")}
            </label>

            <textarea
                name="public_description"
            ></textarea>


            <label>
                {t("private_notes")}
            </label>

            <textarea
                name="internal_notes"
            ></textarea>


            <button
                type="submit"
            >
                {t("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        t("add_case"),
        content,
    )


# ============================================================
# EDIT CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=[
        "GET",
        "POST",
    ]
)
@staff_required
def staff_edit_case(case_id):

    db = get_db()

    case = db.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    db.close()

    if case is None:
        abort(404)

    if request.method == "POST":

        db = get_db()

        db.execute(
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
                request.form.get(
                    "last_name",
                    "",
                ).strip(),

                request.form.get(
                    "parties",
                    "",
                ).strip(),

                request.form.get(
                    "case_title",
                    "",
                ).strip(),

                request.form.get(
                    "case_type",
                    "",
                ).strip(),

                request.form.get(
                    "status",
                    "Pending",
                ).strip(),

                request.form.get(
                    "public_description",
                    "",
                ).strip(),

                request.form.get(
                    "internal_notes",
                    "",
                ).strip(),

                current_time(),

                case_id,
            ),
        )

        db.commit()
        db.close()

        flash(
            "Case updated successfully.",
            "success",
        )

        return redirect(
            url_for("staff_cases")
        )

    content = f"""

    <div class="card">

        <h1>
            {t("edit_case")}
        </h1>

        <form method="post">

            <label>
                {t("case_number")}
            </label>

            <input
                value="{escape_html(
                    case["case_number"]
                )}"
                disabled
            >


            <label>
                {t("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(
                    case["last_name"]
                )}"
                required
            >


            <label>
                {t("parties")}
            </label>

            <input
                name="parties"
                value="{escape_html(
                    case["parties"]
                )}"
                required
            >


            <label>
                {t("title")}
            </label>

            <input
                name="case_title"
                value="{escape_html(
                    case["case_title"]
                )}"
                required
            >


            <label>
                Case Type
            </label>

            <input
                name="case_type"
                value="{escape_html(
                    case["case_type"]
                )}"
            >


            <label>
                {t("status")}
            </label>

            <select name="status">

                {

                    "".join(
                        f'''
                        <option
                            {
                                "selected"
                                if value == case["status"]
                                else ""
                            }
                        >
                            {value}
                        </option>
                        '''
                        for value
                        in [
                            "Pending",
                            "Active",
                            "Scheduled",
                            "Resolved",
                            "Final",
                            "Dismissed",
                        ]
                    )

                }

            </select>


            <label>
                {t("public_information")}
            </label>

            <textarea
                name="public_description"
            >{escape_html(
                case["public_description"]
            )}</textarea>


            <label>
                {t("private_notes")}
            </label>

            <textarea
                name="internal_notes"
            >{escape_html(
                case["internal_notes"]
            )}</textarea>


            <button
                type="submit"
            >
                {t("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        t("edit_case"),
        content,
    )


# ============================================================
# DELETE CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/delete",
    methods=[
        "POST",
    ]
)
@staff_required
def staff_delete_case(case_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    db.commit()
    db.close()

    flash(
        "Case deleted successfully.",
        "success",
    )

    return redirect(
        url_for("staff_cases")
    )


# ============================================================
# STAFF HEARINGS / HEARING NATURE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearing",
    methods=[
        "GET",
        "POST",
    ]
)
@staff_required
def staff_hearing(case_id):

    db = get_db()

    case = db.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    if not case:

        db.close()

        abort(404)

    hearing = db.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (case_id,),
    ).fetchone()

    if request.method == "POST":

        hearing_date = (
            request.form.get(
                "hearing_date",
                "",
            )
            .strip()
        )

        hearing_time = (
            request.form.get(
                "hearing_time",
                "",
            )
            .strip()
        )

        courtroom = (
            request.form.get(
                "courtroom",
                "",
            )
            .strip()
        )

        hearing_nature = (
            request.form.get(
                "hearing_nature",
                "",
            )
            .strip()
        )

        hearing_status = (
            request.form.get(
                "hearing_status",
                "Scheduled",
            )
            .strip()
        )

        remarks = (
            request.form.get(
                "remarks",
                "",
            )
            .strip()
        )

        if hearing:

            db.execute(
                """
                UPDATE hearings
                SET
                    hearing_date = ?,
                    hearing_time = ?,
                    courtroom = ?,
                    hearing_nature = ?,
                    hearing_status = ?,
                    remarks = ?
                WHERE id = ?
                """,
                (
                    hearing_date,
                    hearing_time,
                    courtroom,
                    hearing_nature,
                    hearing_status,
                    remarks,
                    hearing["id"],
                ),
            )

        else:

            db.execute(
                """
                INSERT INTO hearings
                (
                    case_id,
                    hearing_date,
                    hearing_time,
                    courtroom,
                    hearing_nature,
                    hearing_status,
                    remarks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    hearing_date,
                    hearing_time,
                    courtroom,
                    hearing_nature,
                    hearing_status,
                    remarks,
                ),
            )

        db.commit()

        db.close()

        flash(
            "Hearing information updated.",
            "success",
        )

        return redirect(
            url_for(
                "staff_hearing",
                case_id=case_id,
            )
        )

    db.close()

    hearing_date = (
        hearing["hearing_date"]
        if hearing
        else ""
    )

    hearing_time = (
        hearing["hearing_time"]
        if hearing
        else ""
    )

    courtroom = (
        hearing["courtroom"]
        if hearing
        else ""
    )

    hearing_nature = (
        hearing["hearing_nature"]
        if hearing
        else ""
    )

    hearing_status = (
        hearing["hearing_status"]
        if hearing
        else "Scheduled"
    )

    remarks = (
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
        "Other",
    ]

    statuses = [
        "Scheduled",
        "Ongoing",
        "Completed",
        "Reset",
        "Postponed",
        "Cancelled",
    ]

    content = f"""

    <div class="card">

        <h1>
            {t("hearing")}
        </h1>

        <p>

            <strong>
                {escape_html(
                    case["case_number"]
                )}
            </strong>

            -
            {escape_html(
                case["parties"]
            )}

        </p>


        <form method="post">

            <label>
                {t("hearing_date")}
            </label>

            <input
                type="date"
                name="hearing_date"
                value="{escape_html(
                    hearing_date
                )}"
                required
            >


            <label>
                {t("hearing_time")}
            </label>

            <input
                type="time"
                name="hearing_time"
                value="{escape_html(
                    hearing_time
                )}"
            >


            <label>
                {t("hearing_nature")}
            </label>

            <select name="hearing_nature">

                {
                    "".join(
                        f"""
                        <option
                            {"selected"
                             if nature == hearing_nature
                             else ""}
                        >
                            {nature}
                        </option>
                        """
                        for nature in natures
                    )
                }

            </select>


            <label>
                {t("hearing_status")}
            </label>

            <select name="hearing_status">

                {
                    "".join(
                        f"""
                        <option
                            {"selected"
                             if status == hearing_status
                             else ""}
                        >
                            {status}
                        </option>
                        """
                        for status in statuses
                    )
                }

            </select>


            <label>
                {t("courtroom")}
            </label>

            <input
                name="courtroom"
                value="{escape_html(
                    courtroom
                )}"
            >


            <label>
                {t("remarks")}
            </label>

            <textarea
                name="remarks"
            >{escape_html(
                remarks
            )}</textarea>


            <button
                type="submit"
            >
                {t("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        t("hearing"),
        content,
    )


# ============================================================
# STAFF TUESDAY CALENDAR
# ============================================================

@app.route(
    "/staff/calendar"
)
@staff_required
def staff_calendar():

    db = get_db()

    entries = db.execute(
        """
        SELECT *
        FROM tuesday_calendar
        ORDER BY calendar_date,
                 calendar_time
        """
    ).fetchall()

    db.close()

    rows = ""

    for item in entries:

        rows += f"""

        <tr>

            <td>
                {escape_html(
                    item["calendar_date"]
                )}
            </td>

            <td>
                {escape_html(
                    item["calendar_time"]
                )}
            </td>

            <td>
                {escape_html(
                    item["case_number"]
                )}
            </td>

            <td>
                {escape_html(
                    item["parties"]
                )}
            </td>

            <td>
                {escape_html(
                    item["hearing_nature"]
                )}
            </td>

            <td>
                {escape_html(
                    item["status"]
                )}
            </td>

            <td>

                <form
                    method="post"
                    action="{url_for(
                        'delete_calendar',
                        entry_id=item['id']
                    )}"
                    onsubmit="
                        return confirm(
                            'Delete this Tuesday entry?'
                        );
                    "
                >

                    <button class="danger">
                        {t("delete")}
                    </button>

                </form>

            </td>

        </tr>

        """

    content = f"""

    <div class="card">

        <h1>
            📅
            {t("manage_calendar")}
        </h1>

        <form
            method="post"
            action="{url_for('add_calendar')}"
        >

            <div class="two">

                <div>

                    <label>
                        Date
                    </label>

                    <input
                        type="date"
                        name="calendar_date"
                        required
                    >

                </div>

                <div>

                    <label>
                        Time
                    </label>

                    <input
                        type="time"
                        name="calendar_time"
                        required
                    >

                </div>

            </div>


            <label>
                {t("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {t("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {t("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                {t("hearing_nature")}
            </label>

            <input
                name="hearing_nature"
                required
                placeholder="
                Initial Hearing / Arraignment /
                Pre-Trial / Trial / Other
                "
            >


            <label>
                {t("courtroom")}
            </label>

            <input
                name="courtroom"
            >


            <label>
                {t("status")}
            </label>

            <select name="status">

                <option>
                    Scheduled
                </option>

                <option>
                    Ongoing
                </option>

                <option>
                    Completed
                </option>

                <option>
                    Reset
                </option>

                <option>
                    Postponed
                </option>

                <option>
                    Cancelled
                </option>

            </select>


            <label>
                {t("remarks")}
            </label>

            <textarea
                name="remarks"
            ></textarea>


            <label>

                <input
                    type="checkbox"
                    name="public_visible"
                    checked
                    style="
                        width:auto;
                    "
                >

                Publish for civilians

            </label>


            <button
                type="submit"
            >
                {t("add")}
            </button>

        </form>

    </div>


    <div class="card table-wrap">

        <h2>
            Tuesday Calendar Entries
        </h2>

        <table>

            <thead>

                <tr>

                    <th>
                        Date
                    </th>

                    <th>
                        Time
                    </th>

                    <th>
                        Case
                    </th>

                    <th>
                        Parties
                    </th>

                    <th>
                        Nature
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

                {rows or '''
                <tr>
                    <td
                        colspan="7"
                        class="empty"
                    >
                        No calendar entries.
                    </td>
                </tr>
                '''}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        t("calendar"),
        content,
    )


@app.post(
    "/staff/calendar/add"
)
@staff_required
def add_calendar():

    db = get_db()

    db.execute(
        """
        INSERT INTO tuesday_calendar
        (
            calendar_date,
            calendar_time,
            case_number,
            last_name,
            parties,
            hearing_nature,
            courtroom,
            status,
            remarks,
            public_visible,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.form.get(
                "calendar_date",
                "",
            ).strip(),

            request.form.get(
                "calendar_time",
                "",
            ).strip(),

            request.form.get(
                "case_number",
                "",
            ).strip(),

            request.form.get(
                "last_name",
                "",
            ).strip(),

            request.form.get(
                "parties",
                "",
            ).strip(),

            request.form.get(
                "hearing_nature",
                "",
            ).strip(),

            request.form.get(
                "courtroom",
                "",
            ).strip(),

            request.form.get(
                "status",
                "Scheduled",
            ).strip(),

            request.form.get(
                "remarks",
                "",
            ).strip(),

            int(
                bool(
                    request.form.get(
                        "public_visible"
                    )
                )
            ),

            current_time(),

            current_time(),
        )
    )

    db.commit()

    db.close()

    flash(
        "Tuesday calendar entry added.",
        "success",
    )

    return redirect(
        url_for("staff_calendar")
    )


@app.post(
    "/staff/calendar/<int:entry_id>/delete"
)
@staff_required
def delete_calendar(entry_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM tuesday_calendar
        WHERE id = ?
        """,
        (entry_id,),
    )

    db.commit()

    db.close()

    flash(
        "Tuesday calendar entry deleted.",
        "success",
    )

    return redirect(
        url_for("staff_calendar")
    )


# ============================================================
# STAFF NOTICES
# ============================================================

@app.route(
    "/staff/notices"
)
@staff_required
def staff_notices():

    db = get_db()

    notices = db.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    rows = ""

    for notice in notices:

        title = (
            notice["title_fil"]
            if session.get("language") == "fil"
            else notice["title_en"]
        )

        rows += f"""

        <div class="notice">

            <h3>
                {escape_html(title)}
            </h3>

            <p>
                {escape_html(
                    notice["body_en"]
                )}
            </p>

            <form
                method="post"
                action="{url_for(
                    'delete_notice',
                    notice_id=notice['id']
                )}"
                onsubmit="
                    return confirm(
                        'Delete this notice?'
                    );
                "
            >

                <button class="danger">
                    {t("delete")}
                </button>

            </form>

        </div>

        """

    content = f"""

    <div class="card">

        <h1>
            📢
            {t("manage_notices")}
        </h1>

        <form
            method="post"
            action="{url_for('add_notice')}"
            enctype="multipart/form-data"
        >

            <div class="two">

                <div>

                    <label>
                        English Title
                    </label>

                    <input
                        name="title_en"
                        required
                    >

                </div>

                <div>

                    <label>
                        Filipino Title
                    </label>

                    <input
                        name="title_fil"
                        required
                    >

                </div>

            </div>


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
                {t("attachment")}
            </label>

            <input
                type="file"
                name="attachment"
                accept="
                .pdf,
                .png,
                .jpg,
                .jpeg,
                .webp,
                .doc,
                .docx
                "
            >


            <button
                type="submit"
            >
                {t("upload")}
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            Published Notices
        </h2>

        {rows or '<p>No notices yet.</p>'}

    </div>

    """

    return render_page(
        t("notices"),
        content,
    )


@app.post(
    "/staff/notices/add"
)
@staff_required
def add_notice():

    title_en = request.form.get(
        "title_en",
        "",
    ).strip()

    title_fil = request.form.get(
        "title_fil",
        "",
    ).strip()

    body_en = request.form.get(
        "body_en",
        "",
    ).strip()

    body_fil = request.form.get(
        "body_fil",
        "",
    ).strip()

    uploaded = request.files.get(
        "attachment"
    )

    filename = None

    original = None

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
        )

        extension = Path(
            original
        ).suffix.lower().replace(
            ".",
            "",
        )

        if extension not in ALLOWED_FILES:

            flash(
                "That attachment type is not allowed.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_notices"
                )
            )

        filename = (
            secrets.token_hex(12)
            + "_"
            + original
        )

        uploaded.save(
            UPLOAD_DIR / filename
        )

    db = get_db()

    db.execute(
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
            current_time(),
            current_time(),
        ),
    )

    db.commit()

    db.close()

    flash(
        "Notice published.",
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


@app.post(
    "/staff/notices/<int:notice_id>/delete"
)
@staff_required
def delete_notice(notice_id):

    db = get_db()

    notice = db.execute(
        """
        SELECT *
        FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    ).fetchone()

    if notice and notice["attachment"]:

        file_path = (
            UPLOAD_DIR
            / notice["attachment"]
        )

        if file_path.exists():

            try:

                file_path.unlink()

            except OSError:

                pass

    db.execute(
        """
        DELETE FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    )

    db.commit()

    db.close()

    flash(
        "Notice deleted.",
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


# ============================================================
# STAFF REQUIREMENTS
# ============================================================

@app.route(
    "/staff/requirements"
)
@staff_required
def staff_requirements():

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY category
        """
    ).fetchall()

    db.close()

    sections = ""

    for row in rows:

        description = (
            row["description_fil"]
            if session.get("language") == "fil"
            else row["description_en"]
        )

        sections += f"""

        <div class="card">

            <h2>
                {escape_html(
                    row["title_fil"]
                    if session.get("language") == "fil"
                    else row["title_en"]
                )}
            </h2>

            <form
                method="post"
                action="{url_for(
                    'update_requirement',
                    category=row['category']
                )}"
                enctype="multipart/form-data"
            >

                <label>
                    Description
                </label>

                <textarea
                    name="description"
                >{escape_html(
                    description
                )}</textarea>


                <label>
                    Upload Document
                </label>

                <input
                    type="file"
                    name="document"
                >


                <button
                    type="submit"
                >
                    {t("save")}
                </button>

            </form>

        </div>

        """

    content = f"""

    <h1>
        {t("manage_requirements")}
    </h1>

    <div class="notice">

        Bond requirements and clearance requirements
        start as "Not yet uploaded" until authorized
        staff add the official information.

    </div>

    {sections}

    """

    return render_page(
        t("requirements"),
        content,
    )


@app.post(
    "/staff/requirements/<category>/update"
)
@staff_required
def update_requirement(category):

    if category not in {
        "bond",
        "clearance",
    }:

        abort(404)

    description = request.form.get(
        "description",
        "",
    ).strip()

    uploaded = request.files.get(
        "document"
    )

    filename = None

    original = None

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
        )

        extension = Path(
            original
        ).suffix.lower().replace(
            ".",
            "",
        )

        if extension not in ALLOWED_FILES:

            flash(
                "That file type is not allowed.",
                "danger",
            )

            return redirect(
                url_for("staff_requirements")
            )

        filename = (
            secrets.token_hex(12)
            + "_"
            + original
        )

        uploaded.save(
            UPLOAD_DIR / filename
        )

    db = get_db()

    if filename:

        db.execute(
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
                current_time(),
                category,
            )
        )

    else:

        db.execute(
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
                current_time(),
                category,
            )
        )

    db.commit()

    db.close()

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
# STAFF LEGAL RESOURCES
# ============================================================

@app.route(
    "/staff/laws"
)
@staff_required
def staff_laws():

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    items = ""

    for row in rows:

        items += f"""

        <div class="notice">

            <strong>
                {escape_html(
                    row["title"]
                )}
            </strong>

            <br>

            {escape_html(
                row["category"]
            )}

            <p>
                {escape_html(
                    row["description"]
                )}
            </p>

            """

        if row["source_url"]:

            items += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    row["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                Open Official Source
            </a>

            """

        items += f"""

            <form
                method="post"
                action="{url_for(
                    'delete_law',
                    law_id=row['id']
                )}"
                style="display:inline"
                onsubmit="
                    return confirm(
                        'Delete this legal resource?'
                    );
                "
            >

                <button class="danger">
                    {t("delete")}
                </button>

            </form>

        </div>

        """

    content = f"""

    <div class="card">

        <h1>
            ⚖️
            {t("manage_laws")}
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

                <option>
                    Philippine Laws
                </option>

                <option>
                    Supreme Court Decisions
                </option>

                <option>
                    Rules of Court
                </option>

                <option>
                    Supreme Court Rules
                </option>

                <option>
                    Administrative Matters
                </option>

                <option>
                    Other Official Resource
                </option>

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


            <button
                type="submit"
            >
                {t("add")}
            </button>

        </form>

    </div>


    <div class="card">

        {items or '<p>No legal resources added yet.</p>'}

    </div>

    """

    return render_page(
        t("laws"),
        content,
    )


@app.post(
    "/staff/laws/add"
)
@staff_required
def add_law():

    category = request.form.get(
        "category",
        "",
    ).strip()

    title = request.form.get(
        "title",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    source_url = request.form.get(
        "source_url",
        "",
    ).strip()

    uploaded = request.files.get(
        "file"
    )

    filename = None

    original = None

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
        )

        extension = Path(
            original
        ).suffix.lower().replace(
            ".",
            "",
        )

        if extension not in ALLOWED_FILES:

            flash(
                "That file type is not allowed.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_laws"
                )
            )

        filename = (
            secrets.token_hex(12)
            + "_"
            + original
        )

        uploaded.save(
            UPLOAD_DIR / filename
        )

    db = get_db()

    db.execute(
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
            category,
            title,
            description,
            source_url,
            filename,
            original,
            current_time(),
            current_time(),
        )
    )

    db.commit()

    db.close()

    flash(
        "Legal resource added.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


@app.post(
    "/staff/laws/<int:law_id>/delete"
)
@staff_required
def delete_law(law_id):

    db = get_db()

    row = db.execute(
        """
        SELECT *
        FROM legal_resources
        WHERE id = ?
        """,
        (law_id,),
    ).fetchone()

    if row and row["file_name"]:

        file_path = (
            UPLOAD_DIR
            / row["file_name"]
        )

        if file_path.exists():

            try:

                file_path.unlink()

            except OSError:

                pass

    db.execute(
        """
        DELETE FROM legal_resources
        WHERE id = ?
        """,
        (law_id,),
    )

    db.commit()

    db.close()

    flash(
        "Legal resource deleted.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


# ============================================================
# STAFF DOCUMENT ACCESS
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def public_upload(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename,
    )


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    body = """

    <div class="card empty">

        <h1>
            404
        </h1>

        <h2>
            Page Not Found
        </h2>

        <a
            class="button"
            href="/"
        >
            Home
        </a>

    </div>

    """

    return render_page(
        "404",
        body,
    ), 404


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return {
        "status": "ok",
        "service": "MCTC Silang-Amadeo"
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000,
            )
        ),
        debug=False,
    )
