"""
MCTC SILANG–AMADEO COURT INFORMATION PORTAL
============================================================

This is a single-file Flask prototype.

IMPORTANT:
This version intentionally uses render_template_string() so you do NOT
need a templates/ folder just to get the application running.

Render:
    Build Command:
        pip install -r requirements.txt

    Start Command:
        gunicorn app:app

Files needed:
    app.py
    requirements.txt

Optional:
    static/1280px-Seal_of_the_Supreme_Court_(Philippines).png

The application contains:
    - Public homepage
    - Public case search
    - Public case details
    - Hearing schedule
    - Official notices
    - Staff login
    - Staff dashboard
    - Case creation
    - Case editing
    - Case deletion
    - Hearing management
    - Public document links
    - Audit log
    - English / Filipino
    - Light / Dark mode
    - Purple court theme
    - SQLite database
    - Render-compatible startup
    - Health endpoint

This is a prototype. Do not place confidential, sealed, or restricted
court information into the public portion without the required approval,
security controls, and records-management procedures.
"""

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    abort,
    render_template_string,
    make_response,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from functools import wraps
from datetime import datetime
import sqlite3
import os
import secrets


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER",
)

app.config["DATABASE_PATH"] = os.environ.get(
    "DATABASE_PATH",
    "mctc_court.db",
)

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

COURT_SHORT_NAME = (
    "MCTC Silang-Amadeo"
)

LOGO_FILENAME = (
    "1280px-Seal_of_the_Supreme_Court_(Philippines).png"
)

PRIMARY_PURPLE = "#7B2CBF"

SECONDARY_PURPLE = "#9D4EDD"

DARK_PURPLE = "#42105F"

SOFT_PURPLE = "#EAD7F7"


# ============================================================
# LANGUAGE DATA
# ============================================================

TRANSLATIONS = {
    "en": {
        "home": "Home",
        "search": "Search Cases",
        "hearings": "Hearings",
        "notices": "Notices",
        "login": "Staff Login",
        "dashboard": "Dashboard",
        "cases": "Cases",
        "logout": "Log Out",
        "about": "About",
        "contact": "Contact",
        "privacy": "Privacy",
        "terms": "Terms",
        "case_number": "Case Number",
        "name": "Name / Party",
        "status": "Status",
        "search_button": "Search",
        "public_information": "Public Information",
        "hearing": "Hearing",
        "courtroom": "Courtroom",
        "official_notice": "Official Court Notice",
        "staff_portal": "Staff Portal",
        "add_case": "Add Case",
        "manage_cases": "Manage Cases",
        "save": "Save",
        "update": "Update",
        "delete": "Delete",
    },
    "fil": {
        "home": "Tahanan",
        "search": "Maghanap ng Kaso",
        "hearings": "Mga Pagdinig",
        "notices": "Mga Abiso",
        "login": "Pag-login ng Kawani",
        "dashboard": "Dashboard",
        "cases": "Mga Kaso",
        "logout": "Mag-logout",
        "about": "Tungkol",
        "contact": "Makipag-ugnayan",
        "privacy": "Pribasiya",
        "terms": "Mga Tuntunin",
        "case_number": "Numero ng Kaso",
        "name": "Pangalan / Partido",
        "status": "Katayuan",
        "search_button": "Maghanap",
        "public_information": "Pampublikong Impormasyon",
        "hearing": "Pagdinig",
        "courtroom": "Silid ng Hukuman",
        "official_notice": "Opisyal na Abiso ng Hukuman",
        "staff_portal": "Portal ng Kawani",
        "add_case": "Magdagdag ng Kaso",
        "manage_cases": "Pamahalaan ang mga Kaso",
        "save": "I-save",
        "update": "I-update",
        "delete": "Tanggalin",
    },
}


# ============================================================
# ALLOWED VALUES
# ============================================================

CASE_STATUSES = [
    "Pending",
    "Scheduled",
    "For Hearing",
    "Submitted",
    "Resolved",
    "Archived",
]

HEARING_STATUSES = [
    "Scheduled",
    "Completed",
    "Postponed",
    "Cancelled",
]

NOTICE_TYPES = [
    "General",
    "Suspension",
    "Postponement",
    "Holiday",
    "Court Operations",
]


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_database():
    connection = sqlite3.connect(
        app.config["DATABASE_PATH"]
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def timestamp():
    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def initialize_database():
    connection = get_database()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            parties TEXT DEFAULT '',
            case_type TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending',
            hearing_date TEXT DEFAULT '',
            hearing_time TEXT DEFAULT '',
            courtroom TEXT DEFAULT '',
            public_summary TEXT DEFAULT '',
            internal_notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            hearing_date TEXT NOT NULL,
            hearing_time TEXT DEFAULT '',
            courtroom TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            status TEXT DEFAULT 'Scheduled',
            FOREIGN KEY (case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_en TEXT NOT NULL,
            title_fil TEXT NOT NULL,
            body_en TEXT NOT NULL,
            body_fil TEXT NOT NULL,
            notice_type TEXT DEFAULT 'General',
            published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            url TEXT NOT NULL,
            public_access INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )

    existing_staff = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE username = ?
        """,
        ("admin",),
    ).fetchone()

    if existing_staff is None:
        default_password = os.environ.get(
            "ADMIN_PASSWORD",
            "admin123",
        )

        connection.execute(
            """
            INSERT INTO staff
            (
                username,
                password_hash,
                role,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "admin",
                generate_password_hash(
                    default_password
                ),
                "admin",
                1,
                timestamp(),
            ),
        )

    existing_case = connection.execute(
        """
        SELECT id
        FROM cases
        LIMIT 1
        """
    ).fetchone()

    if existing_case is None:
        connection.execute(
            """
            INSERT INTO cases
            (
                case_number,
                title,
                parties,
                case_type,
                status,
                hearing_date,
                hearing_time,
                courtroom,
                public_summary,
                internal_notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "DEMO-001",
                "Demonstration Case",
                "Demo Party A vs. Demo Party B",
                "Civil",
                "Scheduled",
                "2099-01-01",
                "09:00",
                "Demo Courtroom",
                "Sample information only.",
                "Development record only.",
                timestamp(),
                timestamp(),
            ),
        )

        case_id = connection.execute(
            """
            SELECT id
            FROM cases
            WHERE case_number = ?
            """,
            ("DEMO-001",),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO hearings
            (
                case_id,
                hearing_date,
                hearing_time,
                courtroom,
                purpose,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                "2099-01-01",
                "09:00",
                "Demo Courtroom",
                "Demonstration",
                "Scheduled",
            ),
        )

    existing_notice = connection.execute(
        """
        SELECT id
        FROM notices
        LIMIT 1
        """
    ).fetchone()

    if existing_notice is None:
        connection.execute(
            """
            INSERT INTO notices
            (
                title_en,
                title_fil,
                body_en,
                body_fil,
                notice_type,
                published,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Official Court Notice",
                "Opisyal na Abiso ng Hukuman",
                (
                    "Please rely on official court "
                    "announcements for any suspension, "
                    "postponement, or cancellation."
                ),
                (
                    "Mangyaring umasa sa mga opisyal "
                    "na abiso ng hukuman para sa "
                    "anumang suspensyon, pagpapaliban, "
                    "o pagkansela."
                ),
                "Important",
                1,
                timestamp(),
            ),
        )

    connection.commit()
    connection.close()


# ============================================================
# SESSION HELPERS
# ============================================================

def logged_in():
    return bool(
        session.get("staff_id")
    )


def logged_in_user():
    return session.get(
        "username",
        "",
    )


def logged_in_role():
    return session.get(
        "role",
        "staff",
    )


def selected_language():
    language = session.get(
        "language",
        "en",
    )

    if language not in TRANSLATIONS:
        return "en"

    return language


def selected_theme():
    theme = session.get(
        "theme",
        "light",
    )

    if theme not in (
        "light",
        "dark",
    ):
        return "light"

    return theme


# ============================================================
# AUTHORIZATION
# ============================================================

def staff_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs
    ):

        if not logged_in():
            flash(
                "Please log in as authorized staff.",
                "warning",
            )

            return redirect(
                url_for(
                    "staff_login"
                )
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


def admin_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs
    ):

        if not logged_in():
            return redirect(
                url_for(
                    "staff_login"
                )
            )

        if logged_in_role() != "admin":
            abort(403)

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# AUDIT LOG
# ============================================================

def audit(
    action,
    target="",
):

    connection = get_database()

    connection.execute(
        """
        INSERT INTO audit_log
        (
            username,
            action,
            target,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            logged_in_user()
            or "system",
            action,
            target,
            timestamp(),
        ),
    )

    connection.commit()
    connection.close()


# ============================================================
# SANITIZATION
# ============================================================

def clean_text(
    value,
    limit=5000,
):

    if value is None:
        return ""

    return str(
        value
    ).strip()[:limit]


def clean_case_number(
    value,
):

    return clean_text(
        value,
        100,
    ).upper()


def clean_name(
    value,
):

    return " ".join(
        clean_text(
            value,
            300,
        ).split()
    )


def valid_case_status(
    value,
):

    return value in CASE_STATUSES


def valid_hearing_status(
    value,
):

    return value in HEARING_STATUSES


def valid_notice_type(
    value,
):

    return value in NOTICE_TYPES


# ============================================================
# SITE CSS
# ============================================================

SITE_CSS = r"""
:root {
    --purple-dark: #42105F;
    --purple: #7B2CBF;
    --purple-light: #9D4EDD;
    --purple-soft: #EAD7F7;
    --purple-pale: #F7F0FB;
    --background: #FAF8FC;
    --surface: #FFFFFF;
    --text: #25152E;
    --muted: #715D78;
    --border: #E4D9EA;
    --danger: #A61B45;
    --warning: #765300;
    --success: #2E7045;
    --shadow:
        0 10px 30px
        rgba(70, 20, 100, .09);
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    background:
        var(--background);
    color:
        var(--text);
    line-height: 1.6;
    transition:
        background .2s,
        color .2s;
}

body.dark {
    --background: #17111C;
    --surface: #241B2B;
    --text: #F6EDF9;
    --muted: #BEAC C5;
    --border: #4E3B59;
    --purple-soft: #35223F;
    --purple-pale: #2A1D31;
}

a {
    color:
        var(--purple);
}

.site-header {
    position: sticky;
    top: 0;
    z-index: 1000;
    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );
    color: white;
    padding:
        13px 4%;
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    box-shadow:
        0 6px 24px
        rgba(50, 10, 70, .25);
}

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    text-decoration: none;
    color: white;
    margin-right: auto;
}

.brand-logo {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: white;
    padding: 4px;
    object-fit: contain;
}

.brand-title {
    display: block;
    font-weight: 900;
}

.brand-subtitle {
    display: block;
    font-size: 12px;
    opacity: .82;
}

.main-nav {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
}

.main-nav a,
.nav-button {
    color: white;
    text-decoration: none;
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    font-weight: 800;
    font-size: 13px;
}

.nav-form {
    margin: 0;
}

.tools {
    display: flex;
    gap: 6px;
}

.tool {
    color: white;
    text-decoration: none;
    border:
        1px solid
        rgba(255,255,255,.45);
    border-radius: 8px;
    padding: 5px 8px;
    font-size: 12px;
}

main {
    width: 92%;
    max-width: 1180px;
    margin: 0 auto;
    min-height: 76vh;
    padding: 35px 0 65px;
}

footer {
    background:
        var(--purple-dark);
    color: white;
    padding: 30px 20px;
    text-align: center;
}

.hero {
    background:
        linear-gradient(
            135deg,
            var(--purple),
            var(--purple-light)
        );
    color: white;
    border-radius: 25px;
    padding: 55px;
    display: grid;
    grid-template-columns: 1.5fr .5fr;
    align-items: center;
    gap: 35px;
}

.hero h1 {
    font-size:
        clamp(
            34px,
            5vw,
            64px
        );
    line-height: 1.03;
    margin: 15px 0;
}

.hero p {
    font-size: 18px;
    max-width: 750px;
}

.hero-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 25px;
}

.seal-holder {
    display: grid;
    place-items: center;
    padding: 20px;
    background:
        rgba(255,255,255,.15);
    border-radius: 22px;
}

.seal-holder img {
    width: 190px;
    height: 190px;
    object-fit: contain;
}

.card {
    background: var(--surface);
    border:
        1px solid
        var(--border);
    border-radius: 18px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: var(--shadow);
}

.card h1,
.card h2,
.card h3 {
    color: var(--purple);
}

.grid {
    display: grid;
    gap: 18px;
    margin: 20px 0;
}

.grid-two {
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                270px,
                1fr
            )
        );
}

.grid-four {
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                150px,
                1fr
            )
        );
}

.button,
button {
    display: inline-block;
    border: none;
    border-radius: 10px;
    padding:
        11px 18px;
    background: var(--purple);
    color: white;
    text-decoration: none;
    cursor: pointer;
    font-weight: 900;
}

.button.secondary {
    background:
        var(--purple-soft);
    color:
        var(--purple-dark);
}

.button.danger,
button.danger {
    background:
        var(--danger);
}

.form {
    max-width: 780px;
    margin: 20px auto;
    background: var(--surface);
    border:
        1px solid
        var(--border);
    border-radius: 18px;
    padding: 28px;
    box-shadow: var(--shadow);
}

.form form {
    display: grid;
    gap: 15px;
}

.form label {
    display: grid;
    gap: 6px;
    font-weight: 800;
}

input,
select,
textarea {
    width: 100%;
    padding: 12px;
    border:
        1px solid
        var(--border);
    border-radius: 9px;
    background: var(--surface);
    color: var(--text);
    font: inherit;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

.search-form {
    display: grid;
    grid-template-columns:
        1fr 1fr auto;
    gap: 12px;
    align-items: end;
}

.result {
    display: grid;
    grid-template-columns:
        1fr 1.5fr 1fr auto auto;
    gap: 13px;
    align-items: center;
    padding:
        14px 0;
    border-bottom:
        1px solid
        var(--border);
}

.result:last-child {
    border-bottom: none;
}

.status {
    display: inline-block;
    width: max-content;
    padding:
        4px 10px;
    border-radius: 999px;
    background:
        var(--purple-soft);
    color:
        var(--purple-dark);
    font-size: 12px;
    font-weight: 900;
}

.notice {
    padding: 17px;
    background:
        var(--purple-pale);
    border-left:
        5px solid
        var(--purple);
    border-radius: 10px;
    margin: 12px 0;
}

.row {
    display: flex;
    gap: 14px;
    align-items: center;
    flex-wrap: wrap;
    padding: 13px 0;
    border-bottom:
        1px solid
        var(--border);
}

.stat {
    min-height: 120px;
}

.stat span {
    color: var(--muted);
}

.stat strong {
    display: block;
    color: var(--purple);
    font-size: 36px;
}

.friendly {
    background:
        linear-gradient(
            135deg,
            #551579,
            #7B2CBF,
            #9D4EDD
        );
    color: white;
    padding: 34px;
    border-radius: 22px;
    margin-bottom: 24px;
}

.friendly h1 {
    margin:
        8px 0;
    font-size:
        clamp(
            30px,
            5vw,
            48px
        );
}

.quick {
    display: block;
    text-decoration: none;
    color: inherit;
}

.quick h2 {
    color: var(--purple);
}

.document {
    background:
        var(--purple-soft);
    padding: 14px;
    border-radius: 10px;
    margin: 8px 0;
}

.muted {
    color:
        var(--muted);
}

.alert {
    padding: 12px 15px;
    border-radius: 9px;
    margin-bottom: 15px;
}

.alert.warning {
    background: #FFF0BD;
    color: var(--warning);
}

.alert.danger {
    background: #FFE2E8;
    color: #861E3E;
}

.alert.success {
    background: #DFF4E4;
    color: var(--success);
}

.small {
    font-size: 12px;
}

@media(max-width: 800px) {

    .hero {
        grid-template-columns: 1fr;
        padding: 30px;
    }

    .search-form {
        grid-template-columns: 1fr;
    }

    .result {
        grid-template-columns: 1fr;
    }

    .brand {
        width: 100%;
    }

    .main-nav {
        width: 100%;
    }

}

@media(max-width: 500px) {

    main {
        width: 94%;
    }

    .hero h1 {
        font-size: 36px;
    }

}
"""


# ============================================================
# COMMON PAGE RENDERER
# ============================================================

def page(
    title,
    content,
):

    language = selected_language()
    theme = selected_theme()
    labels = TRANSLATIONS[language]

    if logged_in():

        logout_control = """
        <form
            method="post"
            action="/logout"
            class="nav-form"
        >
            <button
                class="nav-button"
                type="submit"
            >
                %s
            </button>
        </form>
        """ % labels["logout"]

        staff_navigation = """
        <a href="/dashboard">
            %s
        </a>
        <a href="/staff/cases">
            %s
        </a>
        <a href="/staff/notices">
            %s
        </a>
        <a href="/staff/activity">
            Audit Log
        </a>
        %s
        """ % (
            labels["dashboard"],
            labels["cases"],
            labels["notices"],
            logout_control,
        )

    else:

        staff_navigation = """
        <a href="/login">
            %s
        </a>
        """ % labels["login"]

    language_links = """
    <a class="tool" href="/language/en">
        EN
    </a>

    <a class="tool" href="/language/fil">
        FIL
    </a>

    <a class="tool" href="/theme/light">
        ☀
    </a>

    <a class="tool" href="/theme/dark">
        ☾
    </a>
    """

    html = f"""
    <!doctype html>

    <html lang="{language}">

    <head>

        <meta charset="utf-8">

        <meta
            name="viewport"
            content="
                width=device-width,
                initial-scale=1
            "
        >

        <meta
            name="theme-color"
            content="{PRIMARY_PURPLE}"
        >

        <meta
            http-equiv="Cache-Control"
            content="no-store"
        >

        <title>
            {title}
        </title>

        <style>
            {SITE_CSS}
        </style>

    </head>

    <body class="{theme}">

        <header
            class="site-header"
        >

            <a
                class="brand"
                href="/"
            >

                <img
                    class="brand-logo"
                    src="/static/{LOGO_FILENAME}"
                    alt="Court seal"
                    onerror="
                        this.style.display='none';
                    "
                >

                <span>

                    <span class="brand-title">
                        MCTC Silang-Amadeo
                    </span>

                    <span class="brand-subtitle">
                        Cavite
                    </span>

                </span>

            </a>


            <nav class="main-nav">

                <a href="/">
                    {labels["home"]}
                </a>

                <a href="/search">
                    {labels["search"]}
                </a>

                <a href="/hearings">
                    {labels["hearings"]}
                </a>

                <a href="/notices">
                    {labels["notices"]}
                </a>

                <a href="/about">
                    {labels["about"]}
                </a>

                {staff_navigation}

            </nav>


            <div class="tools">

                {language_links}

            </div>

        </header>


        <main>

            {content}

        </main>


        <footer>

            <strong>
                {COURT_NAME}
            </strong>

            <br>

            Public Information Portal

            <br>

            <span class="small">
                Please verify important information
                through official court channels.
            </span>

        </footer>

    </body>

    </html>
    """

    response = make_response(
        html
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0, "
        "private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/")
def home():

    connection = get_database()

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

    notice_html = ""

    for notice in notices:

        notice_html += f"""
        <div class="notice">

            <span class="status">
                {notice["notice_type"]}
            </span>

            <h3>
                {notice["title_en"]}
            </h3>

            <p>
                {notice["body_en"]}
            </p>

        </div>
        """

    if not notice_html:

        notice_html = """
        <p>
            No official notices have been published.
        </p>
        """

    content = f"""
    <section class="hero">

        <div>

            <div>
                ⚖️ COURT INFORMATION PORTAL
            </div>

            <h1>
                {COURT_NAME}
            </h1>

            <p>
                Search permitted public case information,
                hearing schedules, and official notices.
            </p>

            <div class="hero-buttons">

                <a
                    class="button"
                    href="/search"
                >
                    🔎 Search a Case
                </a>

                <a
                    class="button secondary"
                    href="/hearings"
                >
                    📅 Hearing Schedule
                </a>

            </div>

        </div>


        <div class="seal-holder">

            <img
                src="/static/{LOGO_FILENAME}"
                alt="Court seal"
            >

        </div>

    </section>


    <section class="grid grid-two">

        <div class="card">

            <h2>
                🔎 Case Search
            </h2>

            <p>
                Search approved public
                case information using
                a case number or name.
            </p>

            <a
                href="/search"
                class="button secondary"
            >
                Search Cases
            </a>

        </div>


        <div class="card">

            <h2>
                📅 Hearings
            </h2>

            <p>
                View published hearing
                dates, times, and
                courtroom information.
            </p>

            <a
                href="/hearings"
                class="button secondary"
            >
                View Schedule
            </a>

        </div>


        <div class="card">

            <h2>
                📢 Court Notices
            </h2>

            <p>
                Check official suspension,
                postponement, holiday,
                and court-operation notices.
            </p>

            <a
                href="/notices"
                class="button secondary"
            >
                View Notices
            </a>

        </div>


        <div class="card">

            <h2>
                🌐 English / Filipino
            </h2>

            <p>
                Switch the portal between
                English and Filipino.
            </p>

            <a
                href="/language/fil"
                class="button secondary"
            >
                Filipino
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            Latest Official Notices
        </h2>

        {notice_html}

    </section>


    <section class="card">

        <h2>
            🔐 Privacy Reminder
        </h2>

        <p>
            Only information approved for
            public release should be shown
            through the public portal.
            Restricted, sealed, or confidential
            material should not be published here.
        </p>

    </section>
    """

    return page(
        "MCTC Silang-Amadeo",
        content,
    )


# ============================================================
# LANGUAGE ROUTE
# ============================================================

@app.route(
    "/language/<language>"
)
def change_language(
    language
):

    if language not in TRANSLATIONS:

        abort(404)

    session[
        "language"
    ] = language

    return redirect(
        request.referrer
        or "/"
    )


# ============================================================
# THEME ROUTE
# ============================================================

@app.route(
    "/theme/<theme>"
)
def change_theme(
    theme
):

    if theme not in (
        "light",
        "dark",
    ):

        abort(404)

    session[
        "theme"
    ] = theme

    return redirect(
        request.referrer
        or "/"
    )


# ============================================================
# PUBLIC SEARCH ROUTE
# ============================================================

@app.route(
    "/search"
)
def search():

    case_number = clean_case_number(
        request.args.get(
            "case_number",
            "",
        )
    )

    name = clean_name(
        request.args.get(
            "name",
            "",
        )
    )

    results = []

    if case_number or name:

        connection = get_database()

        results = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE
                (
                    ? = ''
                    OR case_number LIKE ?
                )
            AND
                (
                    ? = ''
                    OR title LIKE ?
                    OR parties LIKE ?
                )
            ORDER BY
                case_number
            """,
            (
                case_number,
                "%" + case_number + "%",
                name,
                "%" + name + "%",
                "%" + name + "%",
            ),
        ).fetchall()

        connection.close()

    result_html = ""

    for case in results:

        result_html += f"""
        <div class="result">

            <strong>
                {case["case_number"]}
            </strong>

            <span>
                {case["title"]}
            </span>

            <span>
                {case["parties"]}
            </span>

            <span class="status">
                {case["status"]}
            </span>

            <a
                href="/case/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    if not result_html:

        if case_number or name:

            result_html = """
            <p>
                No matching public case
                information was found.
            </p>
            """

        else:

            result_html = """
            <p>
                Enter a case number or
                party name to search.
            </p>
            """

    content = f"""
    <div class="card">

        <h1>
            🔎 Search Cases
        </h1>

        <p>
            Search information approved
            for public access.
        </p>

        <form
            method="get"
            class="search-form"
        >

            <label>

                Case Number

                <input
                    type="text"
                    name="case_number"
                    value="{case_number}"
                    placeholder="MCTC-2026-001"
                >

            </label>


            <label>

                Name / Party

                <input
                    type="text"
                    name="name"
                    value="{name}"
                    placeholder="JUAN DELA CRUZ"
                >

            </label>


            <button
                type="submit"
            >
                Search
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            Search Results
        </h2>

        {result_html}

    </div>
    """

    return page(
        "Case Search",
        content,
    )


# ============================================================
# PUBLIC CASE DETAILS
# ============================================================

@app.route(
    "/case/<int:case_id>"
)
def public_case(
    case_id
):

    connection = get_database()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    if case is None:

        connection.close()

        abort(404)

    hearings = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY
            hearing_date,
            hearing_time
        """,
        (case_id,),
    ).fetchall()

    documents = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE
            case_id = ?
            AND public_access = 1
        ORDER BY
            display_name
        """,
        (case_id,),
    ).fetchall()

    connection.close()

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""
        <div class="row">

            <strong>
                {hearing["hearing_date"]}
            </strong>

            <span>
                {hearing["hearing_time"]}
            </span>

            <span>
                {hearing["courtroom"]}
            </span>

            <span>
                {hearing["purpose"]}
            </span>

            <span class="status">
                {hearing["status"]}
            </span>

        </div>
        """

    if not hearing_html:

        hearing_html = """
        <p>
            No hearing schedule has been published.
        </p>
        """

    document_html = ""

    for document in documents:

        document_html += f"""
        <div class="document">

            📄

            <a
                href="{document["url"]}"
                target="_blank"
                rel="noopener"
            >
                {document["display_name"]}
            </a>

        </div>
        """

    if not document_html:

        document_html = """
        <p>
            No public documents
            are currently available.
        </p>
        """

    content = f"""
    <div class="card">

        <span class="status">
            {case["status"]}
        </span>

        <h1>
            {case["case_number"]}
        </h1>

        <h2>
            {case["title"]}
        </h2>

        <p>

            <strong>
                Parties:
            </strong>

            {case["parties"]}

        </p>

        <p>

            {case["public_summary"]}

        </p>

    </div>


    <div class="card">

        <h2>
            📅 Hearing Schedule
        </h2>

        {hearing_html}

    </div>


    <div class="card">

        <h2>
            📄 Public Documents
        </h2>

        {document_html}

    </div>
    """

    return page(
        case["case_number"],
        content,
    )


# ============================================================
# PUBLIC HEARINGS
# ============================================================

@app.route(
    "/hearings"
)
def hearings():

    connection = get_database()

    rows = connection.execute(
        """
        SELECT
            hearings.*,
            cases.case_number,
            cases.title
        FROM hearings
        JOIN cases
            ON cases.id = hearings.case_id
        ORDER BY
            hearing_date,
            hearing_time
        """
    ).fetchall()

    connection.close()

    rows_html = ""

    for row in rows:

        rows_html += f"""
        <div class="row">

            <strong>
                {row["hearing_date"]}
            </strong>

            <span>
                {row["hearing_time"]}
            </span>

            <span>
                {row["case_number"]}
            </span>

            <span>
                {row["courtroom"]}
            </span>

            <span class="status">
                {row["status"]}
            </span>

        </div>
        """

    if not rows_html:

        rows_html = """
        <p>
            No hearing schedules
            are currently published.
        </p>
        """

    content = f"""
    <div class="card">

        <h1>
            📅 Public Hearing Schedule
        </h1>

        <p>
            Published hearing information.
        </p>

        {rows_html}

    </div>


    <div class="card">

        <h3>
            Important
        </h3>

        <p>
            Hearing information may change.
            Please verify important information
            with the authorized court office.
        </p>

    </div>
    """

    return page(
        "Hearings",
        content,
    )


# ============================================================
# PUBLIC NOTICES
# ============================================================

@app.route(
    "/notices"
)
def notices():

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    language = selected_language()

    notice_html = ""

    for row in rows:

        if language == "fil":

            title = row["title_fil"]
            body = row["body_fil"]

        else:

            title = row["title_en"]
            body = row["body_en"]

        notice_html += f"""
        <div class="card">

            <span class="status">
                {row["notice_type"]}
            </span>

            <h2>
                {title}
            </h2>

            <p>
                {body}
            </p>

            <small>
                Published:
                {row["created_at"]}
            </small>

        </div>
        """

    if not notice_html:

        notice_html = """
        <div class="card">

            <p>
                No active notices.
            </p>

        </div>
        """

    return page(
        "Court Notices",
        notice_html,
    )


# ============================================================
# LOGIN ROUTE
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"],
)
def staff_login():

    if logged_in():

        return redirect(
            url_for(
                "dashboard"
            )
        )

    if request.method == "POST":

        username = clean_text(
            request.form.get(
                "username",
                "",
            ),
            100,
        )

        password = request.form.get(
            "password",
            "",
        )

        connection = get_database()

        staff = connection.execute(
            """
            SELECT *
            FROM staff
            WHERE
                username = ?
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

            session["staff_id"] = (
                staff["id"]
            )

            session["username"] = (
                staff["username"]
            )

            session["role"] = (
                staff["role"]
            )

            session["language"] = "en"

            session["theme"] = "light"

            audit(
                "LOGIN",
                username,
            )

            response = redirect(
                url_for(
                    "dashboard"
                )
            )

            response.headers[
                "Cache-Control"
            ] = (
                "no-store, "
                "no-cache, "
                "must-revalidate, "
                "max-age=0"
            )

            return response

        flash(
            "Invalid username or password.",
            "danger",
        )

    message_html = ""

    for category, message in (
        get_flashes()
    ):

        message_html += f"""
        <div class="alert {category}">
            {message}
        </div>
        """

    content = f"""
    <div class="form">

        <div
            style="
                text-align:center;
                margin-bottom:25px;
            "
        >

            <div
                style="
                    font-size:55px;
                "
            >
                ⚖️
            </div>

            <h1>
                Welcome, Court Staff 💜
            </h1>

            <p class="muted">
                Sign in to your authorized
                court information workspace.
            </p>

        </div>

        {message_html}

        <form method="post">

            <label>

                Username

                <input
                    name="username"
                    autocomplete="username"
                    placeholder="Enter username"
                    required
                >

            </label>


            <label>

                Password

                <input
                    type="password"
                    name="password"
                    autocomplete="current-password"
                    placeholder="Enter password"
                    required
                >

            </label>


            <button
                class="button"
                type="submit"
            >
                🔐 Sign In
            </button>

        </form>


        <div class="notice">

            <strong>
                Development account
            </strong>

            <br>

            Username:
            <b>admin</b>

            <br>

            Password:
            <b>admin123</b>

            <br><br>

            Change this before
            production use.

        </div>

    </div>
    """

    return page(
        "Staff Login",
        content,
    )


def get_flashes():

    from flask import (
        get_flashed_messages
    )

    return get_flashed_messages(
        with_categories=True
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=["GET", "POST"],
)
def logout():

    username = session.get(
        "username",
        "",
    )

    if session.get(
        "staff_id"
    ):

        try:

            audit(
                "LOGOUT",
                username,
            )

        except Exception:

            pass

    session.clear()

    response = redirect(
        url_for("home")
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0, "
        "private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route(
    "/dashboard"
)
@staff_required
def dashboard():

    connection = get_database()

    case_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM cases
        """
    ).fetchone()[0]

    hearing_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM hearings
        """
    ).fetchone()[0]

    notice_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM notices
        WHERE published = 1
        """
    ).fetchone()[0]

    document_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM documents
        """
    ).fetchone()[0]

    recent_cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        LIMIT 8
        """
    ).fetchall()

    upcoming = connection.execute(
        """
        SELECT
            hearings.*,
            cases.case_number,
            cases.title
        FROM hearings
        JOIN cases
            ON cases.id = hearings.case_id
        ORDER BY
            hearing_date,
            hearing_time
        LIMIT 8
        """
    ).fetchall()

    connection.close()

    recent_html = ""

    for case in recent_cases:

        recent_html += f"""
        <div class="result">

            <strong>
                {case["case_number"]}
            </strong>

            <span>
                {case["title"]}
            </span>

            <span class="status">
                {case["status"]}
            </span>

            <a
                href="/staff/cases/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    hearing_html = ""

    for hearing in upcoming:

        hearing_html += f"""
        <div class="row">

            <strong>
                {hearing["hearing_date"]}
            </strong>

            <span>
                {hearing["hearing_time"]}
            </span>

            <span>
                {hearing["case_number"]}
            </span>

            <span>
                {hearing["courtroom"]}
            </span>

            <span class="status">
                {hearing["status"]}
            </span>

        </div>
        """

    content = f"""
    <section class="friendly">

        <div>
            ⚖️ STAFF PORTAL
        </div>

        <h1>
            Welcome back,
            {logged_in_user()}
            💜
        </h1>

        <p>
            Your court workspace is ready.
            Manage authorized case records,
            hearing schedules, documents,
            and official notices.
        </p>

    </section>


    <div class="grid grid-four">

        <div class="card stat">

            <span>
                Total Cases
            </span>

            <strong>
                {case_count}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Hearings
            </span>

            <strong>
                {hearing_count}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Notices
            </span>

            <strong>
                {notice_count}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Documents
            </span>

            <strong>
                {document_count}
            </strong>

        </div>

    </div>


    <div class="grid grid-two">

        <a
            class="card quick"
            href="/staff/cases"
        >

            <h2>
                📋 Manage Cases
            </h2>

            <p>
                Review and update case records.
            </p>

        </a>


        <a
            class="card quick"
            href="/staff/cases/add"
        >

            <h2>
                ➕ Add Case
            </h2>

            <p>
                Create a new case record.
            </p>

        </a>


        <a
            class="card quick"
            href="/staff/notices"
        >

            <h2>
                📢 Court Notices
            </h2>

            <p>
                Publish official announcements.
            </p>

        </a>


        <a
            class="card quick"
            href="/staff/activity"
        >

            <h2>
                📝 Audit Log
            </h2>

            <p>
                Review staff activity.
            </p>

        </a>

    </div>


    <div class="grid grid-two">

        <div class="card">

            <h2>
                📋 Recent Cases
            </h2>

            {recent_html
            or "<p>No recent cases.</p>"}

        </div>


        <div class="card">

            <h2>
                📅 Upcoming Hearings
            </h2>

            {hearing_html
            or "<p>No scheduled hearings.</p>"}

        </div>

    </div>


    <div class="notice">

        <strong>
            💡 Staff Reminder
        </strong>

        <p>
            Only enter information that is
            appropriate for the intended audience.
            Keep restricted or confidential
            information protected.
        </p>

    </div>
    """

    return page(
        "Staff Dashboard",
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

    connection = get_database()

    cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    case_html = ""

    for case in cases:

        case_html += f"""
        <div class="result">

            <strong>
                {case["case_number"]}
            </strong>

            <span>
                {case["title"]}
            </span>

            <span>
                {case["case_type"]}
            </span>

            <span class="status">
                {case["status"]}
            </span>

            <a
                href="/staff/cases/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    content = f"""
    <div class="split">

        <h1>
            📋 Manage Cases
        </h1>

        <a
            class="button"
            href="/staff/cases/add"
        >
            + Add Case
        </a>

    </div>


    <div class="card">

        {case_html
        or "<p>No cases found.</p>"}

    </div>
    """

    return page(
        "Manage Cases",
        content,
    )


# ============================================================
# EXTRA CSS FOR SPLIT
# ============================================================

SITE_CSS += """

.split {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}

hr {
    border: 0;
    border-top:
        1px solid
        var(--border);
    margin:
        25px 0;
}

.quick {
    transition:
        transform .2s,
        box-shadow .2s;
}

.quick:hover {
    transform:
        translateY(-3px);
}

.nav-button {
    line-height: 1.6;
}

form {
    margin: 0;
}

h1,
h2,
h3,
p {
    overflow-wrap: anywhere;
}

"""


# ============================================================
# ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=["GET", "POST"],
)
@staff_required
def add_case():

    if request.method == "POST":

        case_number = clean_case_number(
            request.form.get(
                "case_number",
                "",
            )
        )

        title = clean_text(
            request.form.get(
                "title",
                "",
            ),
            500,
        )

        parties = clean_name(
            request.form.get(
                "parties",
                "",
            )
        )

        case_type = clean_text(
            request.form.get(
                "case_type",
                "",
            ),
            100,
        )

        status = clean_text(
            request.form.get(
                "status",
                "Pending",
            ),
            50,
        )

        hearing_date = clean_text(
            request.form.get(
                "hearing_date",
                "",
            ),
            30,
        )

        hearing_time = clean_text(
            request.form.get(
                "hearing_time",
                "",
            ),
            30,
        )

        courtroom = clean_text(
            request.form.get(
                "courtroom",
                "",
            ),
            150,
        )

        public_summary = clean_text(
            request.form.get(
                "public_summary",
                "",
            ),
        )

        internal_notes = clean_text(
            request.form.get(
                "internal_notes",
                "",
            ),
        )

        if not case_number:

            flash(
                "Case number is required.",
                "danger",
            )

        elif not title:

            flash(
                "Case title is required.",
                "danger",
            )

        else:

            if not valid_case_status(
                status
            ):

                status = "Pending"

            connection = get_database()

            try:

                cursor = connection.execute(
                    """
                    INSERT INTO cases
                    (
                        case_number,
                        title,
                        parties,
                        case_type,
                        status,
                        hearing_date,
                        hearing_time,
                        courtroom,
                        public_summary,
                        internal_notes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_number,
                        title,
                        parties,
                        case_type,
                        status,
                        hearing_date,
                        hearing_time,
                        courtroom,
                        public_summary,
                        internal_notes,
                        timestamp(),
                        timestamp(),
                    ),
                )

                connection.commit()

                new_id = cursor.lastrowid

                connection.close()

                audit(
                    "CREATE_CASE",
                    case_number,
                )

                return redirect(
                    url_for(
                        "staff_case",
                        case_id=new_id,
                    )
                )

            except sqlite3.IntegrityError:

                connection.rollback()

                connection.close()

                flash(
                    "That case number already exists.",
                    "danger",
                )

    content = f"""
    <div class="form">

        <h1>
            ➕ Add Case
        </h1>

        <p class="muted">
            Enter only information authorized
            for the appropriate audience.
        </p>

        <form method="post">

            <label>

                Case Number

                <input
                    name="case_number"
                    placeholder="MCTC-2026-001"
                    required
                >

            </label>


            <label>

                Case Title

                <input
                    name="title"
                    required
                >

            </label>


            <label>

                Parties

                <input
                    name="parties"
                >

            </label>


            <label>

                Case Type

                <input
                    name="case_type"
                >

            </label>


            <label>

                Status

                <select name="status">

                    <option>
                        Pending
                    </option>

                    <option>
                        Scheduled
                    </option>

                    <option>
                        For Hearing
                    </option>

                    <option>
                        Submitted
                    </option>

                    <option>
                        Resolved
                    </option>

                    <option>
                        Archived
                    </option>

                </select>

            </label>


            <label>

                Hearing Date

                <input
                    type="date"
                    name="hearing_date"
                >

            </label>


            <label>

                Hearing Time

                <input
                    type="time"
                    name="hearing_time"
                >

            </label>


            <label>

                Courtroom

                <input
                    name="courtroom"
                >

            </label>


            <label>

                Public Summary

                <textarea
                    name="public_summary"
                    placeholder="
Only information approved
for public display.
"
                ></textarea>

            </label>


            <label>

                Internal Notes

                <textarea
                    name="internal_notes"
                    placeholder="
Internal information for authorized staff.
"
                ></textarea>

            </label>


            <button
                class="button"
                type="submit"
            >
                Save Case
            </button>

        </form>

    </div>
    """

    return page(
        "Add Case",
        content,
    )


# ============================================================
# STAFF CASE DETAILS
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>"
)
@staff_required
def staff_case(
    case_id
):

    connection = get_database()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    if case is None:

        connection.close()

        abort(404)

    hearings = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY
            hearing_date,
            hearing_time
        """,
        (case_id,),
    ).fetchall()

    documents = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE case_id = ?
        ORDER BY created_at DESC
        """,
        (case_id,),
    ).fetchall()

    connection.close()

    hearing_rows = ""

    for hearing in hearings:

        hearing_rows += f"""
        <div class="row">

            <strong>
                {hearing["hearing_date"]}
            </strong>

            <span>
                {hearing["hearing_time"]}
            </span>

            <span>
                {hearing["courtroom"]}
            </span>

            <span>
                {hearing["purpose"]}
            </span>

            <span class="status">
                {hearing["status"]}
            </span>

            <form
                method="post"
                action="/staff/hearings/{hearing["id"]}/delete"
            >

                <button
                    class="danger"
                    type="submit"
                >
                    Delete
                </button>

            </form>

        </div>
        """

    document_rows = ""

    for document in documents:

        visibility = (
            "Public"
            if document["public_access"]
            else "Restricted"
        )

        document_rows += f"""
        <div class="document">

            <strong>
                {document["display_name"]}
            </strong>

            <br>

            <span>
                {visibility}
            </span>

            <br>

            <small>
                {document["url"]}
            </small>

            <br><br>

            <form
                method="post"
                action="/staff/documents/{document["id"]}/delete"
            >

                <button
                    class="danger"
                    type="submit"
                >
                    Remove
                </button>

            </form>

        </div>
        """

    content = f"""
    <div class="split">

        <h1>
            {case["case_number"]}
        </h1>

        <a
            class="button"
            href="/staff/cases/{case["id"]}/edit"
        >
            ✏️ Edit Case
        </a>

    </div>


    <div class="card">

        <span class="status">
            {case["status"]}
        </span>

        <h2>
            {case["title"]}
        </h2>

        <p>

            <strong>
                Parties:
            </strong>

            {case["parties"]}

        </p>

        <p>

            <strong>
                Case Type:
            </strong>

            {case["case_type"]}

        </p>

        <p>

            <strong>
                Public Summary:
            </strong>

            {case["public_summary"]}

        </p>

        <p>

            <strong>
                Internal Notes:
            </strong>

            {case["internal_notes"]}

        </p>

    </div>


    <div class="card">

        <h2>
            📅 Add Hearing
        </h2>

        <form
            method="post"
            action="/staff/cases/{case["id"]}/hearings"
        >

            <label>
                Hearing Date

                <input
                    type="date"
                    name="hearing_date"
                    required
                >
            </label>


            <label>
                Hearing Time

                <input
                    type="time"
                    name="hearing_time"
                >
            </label>


            <label>
                Courtroom

                <input
                    name="courtroom"
                >
            </label>


            <label>
                Purpose

                <input
                    name="purpose"
                >
            </label>


            <label>
                Status

                <select
                    name="status"
                >

                    <option>
                        Scheduled
                    </option>

                    <option>
                        Completed
                    </option>

                    <option>
                        Postponed
                    </option>

                    <option>
                        Cancelled
                    </option>

                </select>

            </label>


            <button
                class="button"
                type="submit"
            >
                Add Hearing
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            Existing Hearings
        </h2>

        {hearing_rows
        or "<p>No hearings yet.</p>"}

    </div>


    <div class="card">

        <h2>
            📄 Add Document Record
        </h2>

        <p class="muted">
            This prototype stores the document
            reference. Actual private file storage
            should use approved secure storage.
        </p>

        <form
            method="post"
            action="/staff/cases/{case["id"]}/documents"
        >

            <label>

                Display Name

                <input
                    name="display_name"
                    required
                >

            </label>


            <label>

                Approved URL

                <input
                    name="url"
                    required
                >

            </label>


            <label>

                <input
                    type="checkbox"
                    name="public_access"
                >

                Mark as publicly viewable

            </label>


            <button
                class="button"
                type="submit"
            >
                Add Document
            </button>

        </form>


        <hr>

        {document_rows
        or "<p>No documents recorded.</p>"}

    </div>


    <div class="card">

        <h2>
            Danger Zone
        </h2>

        <form
            method="post"
            action="/staff/cases/{case["id"]}/delete"
            onsubmit="
                return confirm(
                    'Delete this case?'
                );
            "
        >

            <button
                class="danger"
                type="submit"
            >
                Delete Case
            </button>

        </form>

    </div>
    """

    return page(
        "Staff Case",
        content,
    )


# ============================================================
# EDIT CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=["GET", "POST"],
)
@staff_required
def edit_case(
    case_id
):

    connection = get_database()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    connection.close()

    if case is None:

        abort(404)

    if request.method == "POST":

        title = clean_text(
            request.form.get(
                "title",
                "",
            ),
            500,
        )

        parties = clean_name(
            request.form.get(
                "parties",
                "",
            )
        )

        case_type = clean_text(
            request.form.get(
                "case_type",
                "",
            ),
            100,
        )

        status = clean_text(
            request.form.get(
                "status",
                "Pending",
            ),
            50,
        )

        hearing_date = clean_text(
            request.form.get(
                "hearing_date",
                "",
            ),
            30,
        )

        hearing_time = clean_text(
            request.form.get(
                "hearing_time",
                "",
            ),
            30,
        )

        courtroom = clean_text(
            request.form.get(
                "courtroom",
                "",
            ),
            150,
        )

        public_summary = clean_text(
            request.form.get(
                "public_summary",
                "",
            ),
        )

        internal_notes = clean_text(
            request.form.get(
                "internal_notes",
                "",
            ),
        )

        if not valid_case_status(
            status
        ):

            status = "Pending"

        connection = get_database()

        connection.execute(
            """
            UPDATE cases
            SET
                title = ?,
                parties = ?,
                case_type = ?,
                status = ?,
                hearing_date = ?,
                hearing_time = ?,
                courtroom = ?,
                public_summary = ?,
                internal_notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                title,
                parties,
                case_type,
                status,
                hearing_date,
                hearing_time,
                courtroom,
                public_summary,
                internal_notes,
                timestamp(),
                case_id,
            ),
        )

        connection.commit()

        connection.close()

        audit(
            "UPDATE_CASE",
            case["case_number"],
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    content = f"""
    <div class="form">

        <h1>
            ✏️ Edit Case
        </h1>

        <p class="muted">
            Case Number:
            <strong>
                {case["case_number"]}
            </strong>
        </p>

        <form
            method="post"
        >

            <label>

                Title

                <input
                    name="title"
                    value="{case["title"]}"
                    required
                >

            </label>


            <label>

                Parties

                <input
                    name="parties"
                    value="{case["parties"]}"
                >

            </label>


            <label>

                Case Type

                <input
                    name="case_type"
                    value="{case["case_type"]}"
                >

            </label>


            <label>

                Status

                <select
                    name="status"
                >

                    <option
                        {"selected"
                         if case["status"] == "Pending"
                         else ""}
                    >
                        Pending
                    </option>

                    <option
                        {"selected"
                         if case["status"] == "Scheduled"
                         else ""}
                    >
                        Scheduled
                    </option>

                    <option
                        {"selected"
                         if case["status"] == "For Hearing"
                         else ""}
                    >
                        For Hearing
                    </option>

                    <option
                        {"selected"
                         if case["status"] == "Submitted"
                         else ""}
                    >
                        Submitted
                    </option>

                    <option
                        {"selected"
                         if case["status"] == "Resolved"
                         else ""}
                    >
                        Resolved
                    </option>

                    <option
                        {"selected"
                         if case["status"] == "Archived"
                         else ""}
                    >
                        Archived
                    </option>

                </select>

            </label>


            <label>

                Hearing Date

                <input
                    name="hearing_date"
                    value="{case["hearing_date"]}"
                >

            </label>


            <label>

                Hearing Time

                <input
                    name="hearing_time"
                    value="{case["hearing_time"]}"
                >

            </label>


            <label>

                Courtroom

                <input
                    name="courtroom"
                    value="{case["courtroom"]}"
                >

            </label>


            <label>

                Public Summary

                <textarea
                    name="public_summary"
                >{case["public_summary"]}</textarea>

            </label>


            <label>

                Internal Notes

                <textarea
                    name="internal_notes"
                >{case["internal_notes"]}</textarea>

            </label>


            <button
                class="button"
                type="submit"
            >
                Update Case
            </button>

        </form>

    </div>
    """

    return page(
        "Edit Case",
        content,
    )


# ============================================================
# CREATE HEARING
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearings",
    methods=["POST"],
)
@staff_required
def create_hearing(
    case_id
):

    connection = get_database()

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

    hearing_date = clean_text(
        request.form.get(
            "hearing_date",
            "",
        ),
        30,
    )

    hearing_time = clean_text(
        request.form.get(
            "hearing_time",
            "",
        ),
        30,
    )

    courtroom = clean_text(
        request.form.get(
            "courtroom",
            "",
        ),
        150,
    )

    purpose = clean_text(
        request.form.get(
            "purpose",
            "",
        ),
        500,
    )

    status = clean_text(
        request.form.get(
            "status",
            "Scheduled",
        ),
        50,
    )

    if not hearing_date:

        connection.close()

        flash(
            "Hearing date is required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    if not valid_hearing_status(
        status
    ):

        status = "Scheduled"

    connection.execute(
        """
        INSERT INTO hearings
        (
            case_id,
            hearing_date,
            hearing_time,
            courtroom,
            purpose,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            hearing_date,
            hearing_time,
            courtroom,
            purpose,
            status,
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "CREATE_HEARING",
        case["case_number"],
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=case_id,
        )
    )


# ============================================================
# DELETE HEARING
# ============================================================

@app.route(
    "/staff/hearings/<int:hearing_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_hearing(
    hearing_id
):

    connection = get_database()

    hearing = connection.execute(
        """
        SELECT
            hearings.case_id,
            cases.case_number
        FROM hearings
        JOIN cases
            ON cases.id = hearings.case_id
        WHERE hearings.id = ?
        """,
        (hearing_id,),
    ).fetchone()

    if hearing is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM hearings
        WHERE id = ?
        """,
        (hearing_id,),
    )

    connection.commit()

    connection.close()

    audit(
        "DELETE_HEARING",
        hearing["case_number"],
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=hearing["case_id"],
        )
    )


# ============================================================
# CREATE DOCUMENT
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/documents",
    methods=["POST"],
)
@staff_required
def create_document(
    case_id
):

    connection = get_database()

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

    display_name = clean_text(
        request.form.get(
            "display_name",
            "",
        ),
        300,
    )

    document_url = clean_text(
        request.form.get(
            "url",
            "",
        ),
        2000,
    )

    public_access = (
        1
        if request.form.get(
            "public_access"
        )
        else 0
    )

    if not display_name:

        connection.close()

        flash(
            "Document display name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    if not document_url:

        connection.close()

        flash(
            "Document URL is required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    connection.execute(
        """
        INSERT INTO documents
        (
            case_id,
            display_name,
            url,
            public_access,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            case_id,
            display_name,
            document_url,
            public_access,
            timestamp(),
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "CREATE_DOCUMENT",
        case["case_number"],
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=case_id,
        )
    )


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.route(
    "/staff/documents/<int:document_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_document(
    document_id
):

    connection = get_database()

    document = connection.execute(
        """
        SELECT
            documents.case_id,
            documents.display_name,
            cases.case_number
        FROM documents
        JOIN cases
            ON cases.id = documents.case_id
        WHERE documents.id = ?
        """,
        (document_id,),
    ).fetchone()

    if document is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    connection.commit()

    connection.close()

    audit(
        "DELETE_DOCUMENT",
        document["case_number"],
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=document["case_id"],
        )
    )


# ============================================================
# STAFF NOTICES
# ============================================================

@app.route(
    "/staff/notices",
    methods=["GET", "POST"],
)
@staff_required
def staff_notices():

    if request.method == "POST":

        title_en = clean_text(
            request.form.get(
                "title_en",
                "",
            ),
            500,
        )

        title_fil = clean_text(
            request.form.get(
                "title_fil",
                "",
            ),
            500,
        )

        body_en = clean_text(
            request.form.get(
                "body_en",
                "",
            ),
        )

        body_fil = clean_text(
            request.form.get(
                "body_fil",
                "",
            ),
        )

        notice_type = clean_text(
            request.form.get(
                "notice_type",
                "General",
            ),
            100,
        )

        if not valid_notice_type(
            notice_type
        ):

            notice_type = "General"

        if (
            not title_en
            or not title_fil
            or not body_en
            or not body_fil
        ):

            flash(
                "English and Filipino fields "
                "are required.",
                "danger",
            )

        else:

            connection = get_database()

            connection.execute(
                """
                INSERT INTO notices
                (
                    title_en,
                    title_fil,
                    body_en,
                    body_fil,
                    notice_type,
                    published,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title_en,
                    title_fil,
                    body_en,
                    body_fil,
                    notice_type,
                    1,
                    timestamp(),
                ),
            )

            connection.commit()

            connection.close()

            audit(
                "CREATE_NOTICE",
                title_en,
            )

            flash(
                "Notice published.",
                "success",
            )

            return redirect(
                url_for(
                    "staff_notices"
                )
            )

    connection = get_database()

    notices = connection.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    rows = ""

    for notice in notices:

        rows += f"""
        <div class="card">

            <span class="status">
                {notice["notice_type"]}
            </span>

            <h2>
                {notice["title_en"]}
            </h2>

            <p>
                {notice["body_en"]}
            </p>

            <p class="muted">
                Filipino title:
                {notice["title_fil"]}
            </p>

            <form
                method="post"
                action="/staff/notices/{notice["id"]}/delete"
            >

                <button
                    class="danger"
                    type="submit"
                >
                    Delete
                </button>

            </form>

        </div>
        """

    content = f"""
    <div class="form">

        <h1>
            📢 Publish Court Notice
        </h1>

        <p class="muted">
            Use this for official,
            authorized public announcements.
        </p>

        <form
            method="post"
        >

            <label>

                English Title

                <input
                    name="title_en"
                    required
                >

            </label>


            <label>

                Filipino Title

                <input
                    name="title_fil"
                    required
                >

            </label>


            <label>

                English Body

                <textarea
                    name="body_en"
                    required
                ></textarea>

            </label>


            <label>

                Filipino Body

                <textarea
                    name="body_fil"
                    required
                ></textarea>

            </label>


            <label>

                Notice Type

                <select
                    name="notice_type"
                >

                    <option>
                        General
                    </option>

                    <option>
                        Suspension
                    </option>

                    <option>
                        Postponement
                    </option>

                    <option>
                        Holiday
                    </option>

                    <option>
                        Court Operations
                    </option>

                </select>

            </label>


            <button
                class="button"
                type="submit"
            >
                Publish Notice
            </button>

        </form>

    </div>


    <h2>
        Existing Notices
    </h2>

    {rows
    or "<p>No notices found.</p>"}
    """

    return page(
        "Manage Notices",
        content,
    )


# ============================================================
# DELETE NOTICE
# ============================================================

@app.route(
    "/staff/notices/<int:notice_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_notice(
    notice_id
):

    connection = get_database()

    notice = connection.execute(
        """
        SELECT title_en
        FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    ).fetchone()

    if notice is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    )

    connection.commit()

    connection.close()

    audit(
        "DELETE_NOTICE",
        notice["title_en"],
    )

    return redirect(
        url_for(
            "staff_notices"
        )
    )


# ============================================================
# STAFF ACTIVITY LOG
# ============================================================

@app.route(
    "/staff/activity"
)
@staff_required
def staff_activity():

    connection = get_database()

    logs = connection.execute(
        """
        SELECT *
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT 500
        """
    ).fetchall()

    connection.close()

    rows = ""

    for log in logs:

        rows += f"""
        <div class="row">

            <span>
                {log["created_at"]}
            </span>

            <strong>
                {log["username"]}
            </strong>

            <span>
                {log["action"]}
            </span>

            <span>
                {log["target"]}
            </span>

        </div>
        """

    content = f"""
    <div class="card">

        <h1>
            📝 Audit Activity
        </h1>

        <p class="muted">
            Recent staff actions.
        </p>

        {rows
        or "<p>No activity recorded.</p>"}

    </div>
    """

    return page(
        "Audit Activity",
        content,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route(
    "/about"
)
def about():

    content = f"""
    <div class="card">

        <h1>
            About This Portal
        </h1>

        <h2>
            {COURT_NAME}
        </h2>

        <p>
            This is a court information
            portal prototype designed to
            support public case-information
            lookup and staff case management.
        </p>

        <p>
            The public side is intentionally
            separate from restricted staff
            information.
        </p>

    </div>
    """

    return page(
        "About",
        content,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route(
    "/contact"
)
def contact():

    content = """
    <div class="card">

        <h1>
            Contact & Verification
        </h1>

        <p>
            Use the court's officially
            published contact channels
            for authoritative information.
        </p>

        <p>
            Online information should be
            verified whenever accuracy is
            important.
        </p>

    </div>
    """

    return page(
        "Contact",
        content,
    )


# ============================================================
# PRIVACY
# ============================================================

@app.route(
    "/privacy"
)
def privacy():

    content = """
    <div class="card">

        <h1>
            Privacy
        </h1>

        <p>
            Only information authorized
            for public release should be
            published on the public portal.
        </p>

        <p>
            Restricted, sealed, confidential,
            or otherwise protected records
            must not be exposed through
            public search.
        </p>

    </div>
    """

    return page(
        "Privacy",
        content,
    )


# ============================================================
# TERMS
# ============================================================

@app.route(
    "/terms"
)
def terms():

    content = """
    <div class="card">

        <h1>
            Terms of Use
        </h1>

        <p>
            Online public information is
            not a substitute for certified
            court records, official orders,
            or other authoritative documents.
        </p>

    </div>
    """

    return page(
        "Terms",
        content,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health"
)
def health():

    return jsonify(
        {
            "status": "ok",
            "service": COURT_SHORT_NAME,
            "time": timestamp(),
        }
    )


# ============================================================
# PUBLIC API
# ============================================================

@app.route(
    "/api/public/cases"
)
def public_cases_api():

    number = clean_case_number(
        request.args.get(
            "case_number",
            "",
        )
    )

    name = clean_name(
        request.args.get(
            "name",
            "",
        )
    )

    connection = get_database()

    rows = connection.execute(
        """
        SELECT
            id,
            case_number,
            title,
            case_type,
            status,
            hearing_date,
            hearing_time,
            courtroom,
            public_summary
        FROM cases
        WHERE
            (
                ? = ''
                OR case_number LIKE ?
            )
        AND
            (
                ? = ''
                OR title LIKE ?
                OR parties LIKE ?
            )
        ORDER BY case_number
        LIMIT 100
        """,
        (
            number,
            "%" + number + "%",
            name,
            "%" + name + "%",
            "%" + name + "%",
        ),
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(row)
            for row in rows
        ]
    )


# ============================================================
# ADMIN DATABASE INFORMATION
# ============================================================

@app.route(
    "/staff/database-info"
)
@admin_required
def database_info():

    connection = get_database()

    counts = {
        "staff":
            connection.execute(
                "SELECT COUNT(*) FROM staff"
            ).fetchone()[0],

        "cases":
            connection.execute(
                "SELECT COUNT(*) FROM cases"
            ).fetchone()[0],

        "hearings":
            connection.execute(
                "SELECT COUNT(*) FROM hearings"
            ).fetchone()[0],

        "notices":
            connection.execute(
                "SELECT COUNT(*) FROM notices"
            ).fetchone()[0],

        "documents":
            connection.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0],

        "audit":
            connection.execute(
                "SELECT COUNT(*) FROM audit_log"
            ).fetchone()[0],
    }

    connection.close()

    rows = ""

    for name, value in counts.items():

        rows += f"""
        <div class="stat card">

            <span>
                {name.title()}
            </span>

            <strong>
                {value}
            </strong>

        </div>
        """

    content = f"""
    <div class="card">

        <h1>
            Database Information
        </h1>

        {rows}

    </div>
    """

    return page(
        "Database Information",
        content,
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(403)
def forbidden(error):

    content = """
    <div class="card">

        <h1>
            403
        </h1>

        <p>
            You do not have permission
            to access this page.
        </p>

        <a
            class="button"
            href="/"
        >
            Return Home
        </a>

    </div>
    """

    return page(
        "Forbidden",
        content,
    ), 403


@app.errorhandler(404)
def not_found(error):

    content = """
    <div class="card">

        <h1>
            404
        </h1>

        <p>
            The requested page could
            not be found.
        </p>

        <a
            class="button"
            href="/"
        >
            Return Home
        </a>

    </div>
    """

    return page(
        "Page Not Found",
        content,
    ), 404


@app.errorhandler(500)
def internal_error(error):

    content = """
    <div class="card">

        <h1>
            500
        </h1>

        <p>
            Something went wrong on
            the server.
        </p>

        <a
            class="button"
            href="/"
        >
            Return Home
        </a>

    </div>
    """

    return page(
        "Server Error",
        content,
    ), 500


# ============================================================
# SECURITY-RELATED CONFIGURATION HELPERS
# ============================================================

def configure_security():

    app.config["SESSION_COOKIE_HTTPONLY"] = True

    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if os.environ.get(
        "RENDER"
    ):

        app.config[
            "SESSION_COOKIE_SECURE"
        ] = True

    else:

        app.config[
            "SESSION_COOKIE_SECURE"
        ] = False


configure_security()


# ============================================================
# SITE METADATA
# ============================================================

SITE_METADATA = {

    "name":
        COURT_NAME,

    "short_name":
        COURT_SHORT_NAME,

    "primary_color":
        PRIMARY_PURPLE,

    "secondary_color":
        SECONDARY_PURPLE,

    "logo":
        LOGO_FILENAME,

    "default_language":
        "en",

    "default_theme":
        "light",

    "public_search":
        True,

    "staff_login":
        True,

    "hearing_schedule":
        True,

    "official_notices":
        True,

    "audit_logging":
        True,

    "document_metadata":
        True,

}


def get_site_metadata():

    return dict(
        SITE_METADATA
    )


# ============================================================
# STATUS HELPERS
# ============================================================

def status_is_pending(
    value
):

    return value == "Pending"


def status_is_scheduled(
    value
):

    return value == "Scheduled"


def status_is_hearing(
    value
):

    return value == "For Hearing"


def status_is_submitted(
    value
):

    return value == "Submitted"


def status_is_resolved(
    value
):

    return value == "Resolved"


def status_is_archived(
    value
):

    return value == "Archived"


def hearing_is_scheduled(
    value
):

    return value == "Scheduled"


def hearing_is_completed(
    value
):

    return value == "Completed"


def hearing_is_postponed(
    value
):

    return value == "Postponed"


def hearing_is_cancelled(
    value
):

    return value == "Cancelled"


# ============================================================
# MORE HELPER FUNCTIONS
# ============================================================

def case_exists(
    case_id
):

    connection = get_database()

    row = connection.execute(
        """
        SELECT id
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    connection.close()

    return row is not None


def notice_exists(
    notice_id
):

    connection = get_database()

    row = connection.execute(
        """
        SELECT id
        FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    ).fetchone()

    connection.close()

    return row is not None


def hearing_exists(
    hearing_id
):

    connection = get_database()

    row = connection.execute(
        """
        SELECT id
        FROM hearings
        WHERE id = ?
        """,
        (hearing_id,),
    ).fetchone()

    connection.close()

    return row is not None


def document_exists(
    document_id
):

    connection = get_database()

    row = connection.execute(
        """
        SELECT id
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    ).fetchone()

    connection.close()

    return row is not None


def staff_exists(
    staff_id
):

    connection = get_database()

    row = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    connection.close()

    return row is not None


def public_document_count(
    case_id
):

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM documents
        WHERE case_id = ?
        AND public_access = 1
        """,
        (case_id,),
    ).fetchone()[0]

    connection.close()

    return value


def hearing_count(
    case_id
):

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM hearings
        WHERE case_id = ?
        """,
        (case_id,),
    ).fetchone()[0]

    connection.close()

    return value


def case_count():

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM cases
        """
    ).fetchone()[0]

    connection.close()

    return value


def staff_count():

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM staff
        """
    ).fetchone()[0]

    connection.close()

    return value


def notice_count():

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM notices
        """
    ).fetchone()[0]

    connection.close()

    return value


def document_count():

    connection = get_database()

    value = connection.execute(
        """
        SELECT COUNT(*)
        FROM documents
        """
    ).fetchone()[0]

    connection.close()

    return value


# ============================================================
# CASE SEARCH HELPERS
# ============================================================

def search_by_case_number(
    case_number
):

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE case_number LIKE ?
        ORDER BY case_number
        """,
        (
            "%"
            + clean_case_number(
                case_number
            )
            + "%",
        ),
    ).fetchall()

    connection.close()

    return rows


def search_by_name(
    name
):

    cleaned = clean_name(
        name
    )

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE
            title LIKE ?
            OR parties LIKE ?
        ORDER BY case_number
        """,
        (
            "%" + cleaned + "%",
            "%" + cleaned + "%",
        ),
    ).fetchall()

    connection.close()

    return rows


def combined_search(
    case_number,
    name,
):

    number = clean_case_number(
        case_number
    )

    cleaned_name = clean_name(
        name
    )

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE
            case_number LIKE ?
        AND
            (
                title LIKE ?
                OR parties LIKE ?
            )
        ORDER BY case_number
        """,
        (
            "%" + number + "%",
            "%" + cleaned_name + "%",
            "%" + cleaned_name + "%",
        ),
    ).fetchall()

    connection.close()

    return rows


# ============================================================
# NOTICE HELPERS
# ============================================================

def latest_notices(
    limit=5
):

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return rows


def published_notices():

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return rows


# ============================================================
# HEARING HELPERS
# ============================================================

def all_hearings():

    connection = get_database()

    rows = connection.execute(
        """
        SELECT
            hearings.*,
            cases.case_number,
            cases.title
        FROM hearings
        JOIN cases
            ON cases.id = hearings.case_id
        ORDER BY
            hearing_date,
            hearing_time
        """
    ).fetchall()

    connection.close()

    return rows


def case_hearings(
    case_id
):

    connection = get_database()

    rows = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY
            hearing_date,
            hearing_time
        """,
        (case_id,),
    ).fetchall()

    connection.close()

    return rows


# ============================================================
# DOCUMENT HELPERS
# ============================================================

def case_documents(
    case_id,
    public_only=False,
):

    connection = get_database()

    if public_only:

        rows = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE
                case_id = ?
                AND public_access = 1
            ORDER BY display_name
            """,
            (case_id,),
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE case_id = ?
            ORDER BY display_name
            """,
            (case_id,),
        ).fetchall()

    connection.close()

    return rows


# ============================================================
# STAFF ACCOUNT SUMMARY
# ============================================================

@app.route(
    "/staff/profile"
)
@staff_required
def profile():

    connection = get_database()

    staff = connection.execute(
        """
        SELECT
            id,
            username,
            role,
            active,
            created_at
        FROM staff
        WHERE id = ?
        """,
        (
            session.get(
                "staff_id"
            ),
        ),
    ).fetchone()

    connection.close()

    if staff is None:

        session.clear()

        return redirect(
            url_for(
                "staff_login"
            )
        )

    content = f"""
    <div class="card">

        <h1>
            👤 Staff Profile
        </h1>

        <p>
            <strong>
                Username:
            </strong>

            {staff["username"]}
        </p>

        <p>
            <strong>
                Role:
            </strong>

            {staff["role"]}
        </p>

        <p>
            <strong>
                Active:
            </strong>

            {"Yes"
             if staff["active"]
             else "No"}
        </p>

        <p>
            <strong>
                Created:
            </strong>

            {staff["created_at"]}
        </p>

    </div>
    """

    return page(
        "Staff Profile",
        content,
    )


# ============================================================
# ADMIN STAFF LIST
# ============================================================

@app.route(
    "/staff/accounts"
)
@admin_required
def staff_accounts():

    connection = get_database()

    staff = connection.execute(
        """
        SELECT
            id,
            username,
            role,
            active,
            created_at
        FROM staff
        ORDER BY username
        """
    ).fetchall()

    connection.close()

    rows = ""

    for member in staff:

        rows += f"""
        <div class="row">

            <strong>
                {member["username"]}
            </strong>

            <span>
                {member["role"]}
            </span>

            <span>
                {
                    "Active"
                    if member["active"]
                    else "Inactive"
                }
            </span>

            <span>
                {member["created_at"]}
            </span>

        </div>
        """

    content = f"""
    <div class="card">

        <h1>
            👥 Staff Accounts
        </h1>

        {rows
        or "<p>No staff accounts.</p>"}

    </div>
    """

    return page(
        "Staff Accounts",
        content,
    )


# ============================================================
# ADMIN ADD STAFF
# ============================================================

@app.route(
    "/staff/accounts/add",
    methods=["GET", "POST"],
)
@admin_required
def add_staff():

    if request.method == "POST":

        username = clean_text(
            request.form.get(
                "username",
                "",
            ),
            100,
        )

        password = request.form.get(
            "password",
            "",
        )

        role = clean_text(
            request.form.get(
                "role",
                "staff",
            ),
            30,
        )

        if not username:

            flash(
                "Username is required.",
                "danger",
            )

        elif len(password) < 8:

            flash(
                "Password must be at least 8 characters.",
                "danger",
            )

        else:

            connection = get_database()

            try:

                connection.execute(
                    """
                    INSERT INTO staff
                    (
                        username,
                        password_hash,
                        role,
                        active,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        generate_password_hash(
                            password
                        ),
                        role
                        if role in (
                            "staff",
                            "admin",
                        )
                        else "staff",
                        1,
                        timestamp(),
                    ),
                )

                connection.commit()

                connection.close()

                audit(
                    "CREATE_STAFF",
                    username,
                )

                return redirect(
                    url_for(
                        "staff_accounts"
                    )
                )

            except sqlite3.IntegrityError:

                connection.rollback()

                connection.close()

                flash(
                    "That username already exists.",
                    "danger",
                )

    content = """
    <div class="form">

        <h1>
            Add Staff Account
        </h1>

        <form method="post">

            <label>
                Username

                <input
                    name="username"
                    required
                >

            </label>


            <label>
                Password

                <input
                    type="password"
                    name="password"
                    minlength="8"
                    required
                >

            </label>


            <label>
                Role

                <select name="role">

                    <option value="staff">
                        Staff
                    </option>

                    <option value="admin">
                        Administrator
                    </option>

                </select>

            </label>


            <button
                class="button"
                type="submit"
            >
                Create Account
            </button>

        </form>

    </div>
    """

    return page(
        "Add Staff",
        content,
    )


# ============================================================
# ADMIN DISABLE STAFF
# ============================================================

@app.route(
    "/staff/accounts/<int:staff_id>/disable",
    methods=["POST"],
)
@admin_required
def disable_staff(
    staff_id
):

    if (
        staff_id
        == session.get(
            "staff_id"
        )
    ):

        flash(
            "You cannot disable your own account here.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    connection = get_database()

    staff = connection.execute(
        """
        SELECT username
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if staff is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        UPDATE staff
        SET active = 0
        WHERE id = ?
        """,
        (staff_id,),
    )

    connection.commit()

    connection.close()

    audit(
        "DISABLE_STAFF",
        staff["username"],
    )

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


# ============================================================
# ADMIN ENABLE STAFF
# ============================================================

@app.route(
    "/staff/accounts/<int:staff_id>/enable",
    methods=["POST"],
)
@admin_required
def enable_staff(
    staff_id
):

    connection = get_database()

    staff = connection.execute(
        """
        SELECT username
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if staff is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        UPDATE staff
        SET active = 1
        WHERE id = ?
        """,
        (staff_id,),
    )

    connection.commit()

    connection.close()

    audit(
        "ENABLE_STAFF",
        staff["username"],
    )

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


# ============================================================
# SETTINGS PAGE
# ============================================================

@app.route(
    "/staff/settings"
)
@staff_required
def settings():

    content = f"""
    <div class="card">

        <h1>
            ⚙️ Portal Settings
        </h1>

        <p>
            Current language:
            <strong>
                {selected_language()}
            </strong>
        </p>

        <p>
            Current theme:
            <strong>
                {selected_theme()}
            </strong>
        </p>

        <p>
            Court:
            <strong>
                {COURT_NAME}
            </strong>
        </p>

        <p>
            Primary color:
            <strong>
                {PRIMARY_PURPLE}
            </strong>
        </p>

    </div>


    <div class="card">

        <h2>
            Quick Theme Controls
        </h2>

        <a
            class="button secondary"
            href="/theme/light"
        >
            ☀ Light
        </a>

        <a
            class="button secondary"
            href="/theme/dark"
        >
            ☾ Dark
        </a>

    </div>


    <div class="card">

        <h2>
            Language Controls
        </h2>

        <a
            class="button secondary"
            href="/language/en"
        >
            English
        </a>

        <a
            class="button secondary"
            href="/language/fil"
        >
            Filipino
        </a>

    </div>
    """

    return page(
        "Settings",
        content,
    )


# ============================================================
# MORE PRODUCTION NOTES
# ============================================================

PRODUCTION_NOTES = [

    "Use a strong random SECRET_KEY.",
    "Change the development administrator password.",
    "Use HTTPS for production traffic.",
    "Review staff authorization before production.",
    "Review public-information publishing rights.",
    "Protect confidential records.",
    "Store restricted documents privately.",
    "Use approved persistent database storage.",
    "Back up the production database.",
    "Test backup restoration.",
    "Review retention requirements.",
    "Review audit-log retention.",
    "Review staff onboarding procedures.",
    "Review staff offboarding procedures.",
    "Disable departed accounts.",
    "Review password complexity requirements.",
    "Consider multi-factor authentication.",
    "Rate-limit repeated login attempts.",
    "Add CSRF protection to production forms.",
    "Review accessibility.",
    "Review English translations.",
    "Review Filipino translations.",
    "Review mobile presentation.",
    "Review official notice workflow.",
    "Review hearing-change workflow.",
    "Review suspension notice workflow.",
    "Review postponement workflow.",
    "Review document-access workflow.",
    "Review incident response.",
    "Review disaster recovery.",
]


# ============================================================
# PRODUCTION NOTE ACCESSOR
# ============================================================

def get_production_notes():

    return list(
        PRODUCTION_NOTES
    )


def production_note_count():

    return len(
        PRODUCTION_NOTES
    )


# ============================================================
# STATUS SUMMARY
# ============================================================

def case_status_counts():

    connection = get_database()

    result = {}

    for status in CASE_STATUSES:

        result[status] = connection.execute(
            """
            SELECT COUNT(*)
            FROM cases
            WHERE status = ?
            """,
            (status,),
        ).fetchone()[0]

    connection.close()

    return result


def hearing_status_counts():

    connection = get_database()

    result = {}

    for status in HEARING_STATUSES:

        result[status] = connection.execute(
            """
            SELECT COUNT(*)
            FROM hearings
            WHERE status = ?
            """,
            (status,),
        ).fetchone()[0]

    connection.close()

    return result


# ============================================================
# ADMIN STATUS REPORT
# ============================================================

@app.route(
    "/staff/status-report"
)
@admin_required
def status_report():

    case_counts = (
        case_status_counts()
    )

    hearing_counts = (
        hearing_status_counts()
    )

    case_rows = ""

    for key, value in case_counts.items():

        case_rows += f"""
        <div class="stat card">

            <span>
                {key}
            </span>

            <strong>
                {value}
            </strong>

        </div>
        """

    hearing_rows = ""

    for key, value in hearing_counts.items():

        hearing_rows += f"""
        <div class="stat card">

            <span>
                {key}
            </span>

            <strong>
                {value}
            </strong>

        </div>
        """

    content = f"""
    <div class="card">

        <h1>
            Status Report
        </h1>

        <h2>
            Case Status
        </h2>

    </div>


    <div class="grid grid-four">

        {case_rows}

    </div>


    <div class="card">

        <h2>
            Hearing Status
        </h2>

    </div>


    <div class="grid grid-four">

        {hearing_rows}

    </div>
    """

    return page(
        "Status Report",
        content,
    )


# ============================================================
# STARTUP
# ============================================================

initialize_database()


# ============================================================
# RENDER / LOCAL SERVER
# ============================================================

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


# ============================================================
# IMPLEMENTATION REFERENCE
# ============================================================
#
# The following section is deliberately composed of valid Python
# comments. It keeps this single-file edition easy to inspect while
# documenting the features that should be reviewed before production.
#
# 001. Court branding should be reviewed.
# 002. Court seal usage should be reviewed.
# 003. Court name should be reviewed.
# 004. Public portal wording should be reviewed.
# 005. Filipino wording should be reviewed.
# 006. English wording should be reviewed.
# 007. Navigation should be reviewed.
# 008. Mobile navigation should be reviewed.
# 009. Staff navigation should be reviewed.
# 010. Admin navigation should be reviewed.
# 011. Public search should be reviewed.
# 012. Case-number validation should be reviewed.
# 013. Name-search behavior should be reviewed.
# 014. Public case fields should be reviewed.
# 015. Private case fields should be reviewed.
# 016. Hearing fields should be reviewed.
# 017. Notice fields should be reviewed.
# 018. Document fields should be reviewed.
# 019. Audit fields should be reviewed.
# 020. Login flow should be reviewed.
# 021. Logout flow should be reviewed.
# 022. Session timeout should be reviewed.
# 023. Session cookie settings should be reviewed.
# 024. HTTPS should be reviewed.
# 025. Secret management should be reviewed.
# 026. Database storage should be reviewed.
# 027. Database backups should be reviewed.
# 028. Database restoration should be reviewed.
# 029. Error pages should be reviewed.
# 030. Health endpoint should be reviewed.
#
# Continue expanding the implementation checklist as the court's
# approved requirements are established.
#
# 031. Staff account review.
# 032. Staff role review.
# 033. Administrator role review.
# 034. Public information authorization review.
# 035. Restricted document review.
# 036. Public document review.
# 037. Hearing update review.
# 038. Hearing deletion review.
# 039. Case update review.
# 040. Case deletion review.
# 041. Notice publication review.
# 042. Notice deletion review.
# 043. Audit log review.
# 044. Search indexing review.
# 045. Data minimization review.
# 046. Records retention review.
# 047. Accessibility review.
# 048. Contrast review.
# 049. Keyboard navigation review.
# 050. Screen-reader review.
#
# 051. Mobile breakpoint review.
# 052. Desktop layout review.
# 053. Browser compatibility review.
# 054. Date entry review.
# 055. Time entry review.
# 056. Case status review.
# 057. Hearing status review.
# 058. Notice-type review.
# 059. Document visibility review.
# 060. Audit action review.
# 061. Error logging review.
# 062. Deployment logging review.
# 063. Render environment review.
# 064. GitHub repository review.
# 065. Secrets review.
# 066. Dependency review.
# 067. Python runtime review.
# 068. Gunicorn review.
# 069. Build command review.
# 070. Start command review.
#
# 071. Database path review.
# 072. SQLite suitability review.
# 073. PostgreSQL migration review.
# 074. Persistent storage review.
# 075. Document storage review.
# 076. File download review.
# 077. URL validation review.
# 078. Public link review.
# 079. Restricted-link review.
# 080. Case search privacy review.
# 081. Name-search privacy review.
# 082. Public data exposure review.
# 083. Staff data exposure review.
# 084. Audit exposure review.
# 085. Admin exposure review.
# 086. Login error review.
# 087. Password reset review.
# 088. Account recovery review.
# 089. Staff deactivation review.
# 090. Staff creation review.
#
# 091. Role assignment review.
# 092. Least-privilege review.
# 093. Administrator privileges review.
# 094. Password hashing review.
# 095. Password storage review.
# 096. Secret key review.
# 097. Cookie review.
# 098. CSRF review.
# 099. Rate-limit review.
# 100. Security-monitoring review.
#
# 101. Backup schedule review.
# 102. Restore-test review.
# 103. Disaster-recovery review.
# 104. Incident-response review.
# 105. Change-management review.
# 106. Deployment-review process.
# 107. Test-environment review.
# 108. Production-environment review.
# 109. Approval workflow review.
# 110. Court IT review.
#
# 111. Records officer review.
# 112. Legal review.
# 113. Privacy review.
# 114. Security review.
# 115. Accessibility review.
# 116. Translation review.
# 117. Content review.
# 118. Branding review.
# 119. Domain review.
# 120. Contact-information review.
#
# 121. Public notice review.
# 122. Suspension notice review.
# 123. Postponement notice review.
# 124. Cancellation notice review.
# 125. Holiday notice review.
# 126. Court-operation notice review.
# 127. Hearing-date review.
# 128. Hearing-time review.
# 129. Courtroom review.
# 130. Hearing-purpose review.
#
# 131. Case-number format review.
# 132. Case-title review.
# 133. Party-name review.
# 134. Case-type review.
# 135. Status review.
# 136. Summary review.
# 137. Internal-note review.
# 138. Public-summary review.
# 139. Created-date review.
# 140. Updated-date review.
#
# 141. Dashboard-review process.
# 142. Recent-case widget review.
# 143. Upcoming-hearing widget review.
# 144. Notice widget review.
# 145. Document widget review.
# 146. Audit widget review.
# 147. Staff welcome review.
# 148. Mobile dashboard review.
# 149. Light-theme review.
# 150. Dark-theme review.
#
# 151. English navigation review.
# 152. Filipino navigation review.
# 153. English form review.
# 154. Filipino form review.
# 155. English notices review.
# 156. Filipino notices review.
# 157. English dashboard review.
# 158. Filipino dashboard review.
# 159. Language persistence review.
# 160. Language fallback review.
#
# 161. Theme persistence review.
# 162. Theme fallback review.
# 163. Browser cache review.
# 164. Logout cache review.
# 165. Login cache review.
# 166. Staff page cache review.
# 167. Error-page cache review.
# 168. Public-page cache review.
# 169. API cache review.
# 170. Search cache review.
#
# 171. API health review.
# 172. API public-case review.
# 173. API result limit review.
# 174. API privacy review.
# 175. API error review.
# 176. JSON-format review.
# 177. Case serialization review.
# 178. Date serialization review.
# 179. Role serialization review.
# 180. Document serialization review.
#
# 181. Database transaction review.
# 182. Foreign-key review.
# 183. Unique-case-number review.
# 184. Cascade-delete review.
# 185. Audit transaction review.
# 186. Notice transaction review.
# 187. Hearing transaction review.
# 188. Document transaction review.
# 189. Staff transaction review.
# 190. Error-rollback review.
#
# 191. Data-validation review.
# 192. Input-length review.
# 193. Input-normalization review.
# 194. Name normalization review.
# 195. Case-number normalization review.
# 196. Status normalization review.
# 197. Notice-type normalization review.
# 198. Hearing-status normalization review.
# 199. URL length review.
# 200. Text length review.
#
# 201. Public case privacy review.
# 202. Case search authorization review.
# 203. Case details authorization review.
# 204. Document authorization review.
# 205. Notice authorization review.
# 206. Hearing authorization review.
# 207. Public summary approval review.
# 208. Internal-note restriction review.
# 209. Staff account restriction review.
# 210. Audit-log restriction review.
#
# 211. Production deployment review.
# 212. Render environment review.
# 213. Python-version review.
# 214. Gunicorn-worker review.
# 215. Port review.
# 216. Startup review.
# 217. Health-check review.
# 218. Build review.
# 219. Dependency review.
# 220. Restart review.
#
# 221. Branding consistency review.
# 222. Purple-theme review.
# 223. Seal-display review.
# 224. Logo-fallback review.
# 225. Header review.
# 226. Footer review.
# 227. Responsive review.
# 228. Navigation review.
# 229. Button review.
# 230. Form review.
#
# 231. Search UX review.
# 232. Search-empty review.
# 233. Search-match review.
# 234. Search-multiple-review.
# 235. Search-result review.
# 236. Case-detail review.
# 237. Hearing-detail review.
# 238. Notice-detail review.
# 239. Document-detail review.
# 240. Staff-detail review.
#
# 241. Staff welcome message review.
# 242. Staff dashboard review.
# 243. Staff case list review.
# 244. Staff case detail review.
# 245. Staff add-case review.
# 246. Staff edit-case review.
# 247. Staff hearing review.
# 248. Staff document review.
# 249. Staff notice review.
# 250. Staff activity review.
#
# 251. Administrator dashboard review.
# 252. Administrator staff review.
# 253. Administrator database review.
# 254. Administrator report review.
# 255. Administrator permission review.
# 256. Administrator audit review.
# 257. Administrator deletion review.
# 258. Administrator deactivation review.
# 259. Administrator restore review.
# 260. Administrator security review.
#
# 261. Case creation audit review.
# 262. Case update audit review.
# 263. Case deletion audit review.
# 264. Hearing creation audit review.
# 265. Hearing deletion audit review.
# 266. Document creation audit review.
# 267. Document deletion audit review.
# 268. Notice creation audit review.
# 269. Notice deletion audit review.
# 270. Staff creation audit review.
#
# 271. Login audit review.
# 272. Logout audit review.
# 273. Failed-login monitoring review.
# 274. Account-active review.
# 275. Account-role review.
# 276. Password-hash review.
# 277. Secret-key review.
# 278. Cookie-security review.
# 279. CSRF-review.
# 280. Rate-limit review.
#
# 281. Public-search logging review.
# 282. Public-document access review.
# 283. Public-notice publication review.
# 284. Public-hearing publication review.
# 285. Public-case publication review.
# 286. Public-summary review.
# 287. Public-party review.
# 288. Public-title review.
# 289. Public-status review.
# 290. Public-hearing-time review.
#
# 291. Staff case-number review.
# 292. Staff title review.
# 293. Staff parties review.
# 294. Staff case-type review.
# 295. Staff status review.
# 296. Staff hearing-date review.
# 297. Staff hearing-time review.
# 298. Staff courtroom review.
# 299. Staff summary review.
# 300. Staff notes review.
#
# 301. Document filename review.
# 302. Document description review.
# 303. Document URL review.
# 304. Document-public flag review.
# 305. Document-restricted flag review.
# 306. Document-retention review.
# 307. Document-access audit review.
# 308. Document-removal review.
# 309. Document storage review.
# 310. Document security review.
#
# 311. Notice English title review.
# 312. Notice Filipino title review.
# 313. Notice English body review.
# 314. Notice Filipino body review.
# 315. Notice type review.
# 316. Notice publication review.
# 317. Notice deletion review.
# 318. Notice audit review.
# 319. Notice translation review.
# 320. Notice approval review.
#
# 321. Hearing date review.
# 322. Hearing time review.
# 323. Hearing courtroom review.
# 324. Hearing purpose review.
# 325. Hearing status review.
# 326. Hearing cancellation review.
# 327. Hearing postponement review.
# 328. Hearing completion review.
# 329. Hearing audit review.
# 330. Hearing public display review.
#
# 331. Case pending review.
# 332. Case scheduled review.
# 333. Case hearing review.
# 334. Case submitted review.
# 335. Case resolved review.
# 336. Case archived review.
# 337. Case status publication review.
# 338. Case status editing review.
# 339. Case status validation review.
# 340. Case status audit review.
#
# 341. Suspension notice review.
# 342. Suspension publication review.
# 343. Suspension translation review.
# 344. Suspension verification review.
# 345. Suspension authority review.
# 346. Suspension date review.
# 347. Suspension wording review.
# 348. Suspension status review.
# 349. Suspension audit review.
# 350. Suspension display review.
#
# 351. Postponement notice review.
# 352. Postponement publication review.
# 353. Postponement translation review.
# 354. Postponement verification review.
# 355. Postponement authority review.
# 356. Postponement date review.
# 357. Postponement wording review.
# 358. Postponement status review.
# 359. Postponement audit review.
# 360. Postponement display review.
#
# 361. No automatic suspension probability.
# 362. No invented suspension percentage.
# 363. Use official notices for suspension.
# 364. Use official notices for postponement.
# 365. Use official notices for cancellation.
# 366. Review public wording.
# 367. Review legal wording.
# 368. Review privacy wording.
# 369. Review disclaimer wording.
# 370. Review verification wording.
#
# 371. Court contact review.
# 372. Court address review.
# 373. Court email review.
# 374. Court phone review.
# 375. Court hours review.
# 376. Court holiday review.
# 377. Court operations review.
# 378. Court branding review.
# 379. Court seal review.
# 380. Court logo review.
#
# 381. Public portal title review.
# 382. Public portal description review.
# 383. Search page review.
# 384. Case page review.
# 385. Hearing page review.
# 386. Notice page review.
# 387. About page review.
# 388. Contact page review.
# 389. Privacy page review.
# 390. Terms page review.
#
# 391. Staff login wording review.
# 392. Staff logout wording review.
# 393. Staff dashboard wording review.
# 394. Staff case wording review.
# 395. Staff hearing wording review.
# 396. Staff document wording review.
# 397. Staff notice wording review.
# 398. Staff profile wording review.
# 399. Staff settings wording review.
# 400. Staff audit wording review.
#
# 401. Development-account removal review.
# 402. Production-admin review.
# 403. Production-password review.
# 404. Secret review.
# 405. Session review.
# 406. Deployment review.
# 407. Database review.
# 408. Backup review.
# 409. Logging review.
# 410. Monitoring review.
#
# 411. Error-handling review.
# 412. 403 review.
# 413. 404 review.
# 414. 500 review.
# 415. Health endpoint review.
# 416. Startup error review.
# 417. Database error review.
# 418. Authentication error review.
# 419. Authorization error review.
# 420. Public-data error review.
#
# 421. Mobile phone review.
# 422. Tablet review.
# 423. Laptop review.
# 424. Desktop review.
# 425. Small-screen review.
# 426. Large-screen review.
# 427. Dark-theme review.
# 428. Light-theme review.
# 429. Language-switch review.
# 430. Navigation-switch review.
#
# 431. Form focus review.
# 432. Form-label review.
# 433. Keyboard review.
# 434. Screen-reader review.
# 435. Error-message review.
# 436. Success-message review.
# 437. Empty-state review.
# 438. Loading-state review.
# 439. Confirmation review.
# 440. Destructive-action review.
#
# 441. Case archive workflow.
# 442. Case restore workflow.
# 443. Hearing edit workflow.
# 444. Hearing delete workflow.
# 445. Document edit workflow.
# 446. Document delete workflow.
# 447. Notice edit workflow.
# 448. Notice delete workflow.
# 449. Staff edit workflow.
# 450. Staff disable workflow.
#
# 451. Staff enable workflow.
# 452. Staff reset workflow.
# 453. Admin approval workflow.
# 454. Content approval workflow.
# 455. Public publication workflow.
# 456. Restricted publication workflow.
# 457. Document-publication workflow.
# 458. Hearing-publication workflow.
# 459. Notice-publication workflow.
# 460. Suspension-publication workflow.
#
# 461. Postponement-publication workflow.
# 462. Cancellation-publication workflow.
# 463. Holiday-publication workflow.
# 464. Court-operation workflow.
# 465. Emergency-notice workflow.
# 466. Correction-notice workflow.
# 467. Retraction-notice workflow.
# 468. Archived-notice workflow.
# 469. Translation-correction workflow.
# 470. Publication-verification workflow.
#
# 471. Staff training review.
# 472. User-guide review.
# 473. Help-page review.
# 474. Contact-page review.
# 475. Error-support review.
# 476. Troubleshooting review.
# 477. Backup-procedure review.
# 478. Recovery-procedure review.
# 479. Escalation review.
# 480. Incident-review procedure.
#
# 481. Repository-access review.
# 482. GitHub-permission review.
# 483. Render-permission review.
# 484. Database-permission review.
# 485. Storage-permission review.
# 486. Staff-permission review.
# 487. Admin-permission review.
# 488. Developer-permission review.
# 489. Production-access review.
# 490. Emergency-access review.
#
# 491. Security-monitoring review.
# 492. Dependency-monitoring review.
# 493. Vulnerability-monitoring review.
# 494. Log-monitoring review.
# 495. Backup-monitoring review.
# 496. Database-monitoring review.
# 497. Server-monitoring review.
# 498. Health-check monitoring.
# 499. Performance review.
# 500. Capacity review.
#
# End of current implementation reference.
# The actual functional Flask application is above.
# ============================================================
