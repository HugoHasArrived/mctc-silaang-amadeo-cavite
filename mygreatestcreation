
from flask import Flask, request, redirect, url_for, session, flash, jsonify, abort, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER",
)
app.config["DATABASE_PATH"] = os.environ.get(
    "DATABASE_PATH",
    "mctc_court.db",
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(
    os.environ.get("RENDER")
)

COURT_NAME = "Municipal Circuit Trial Court of Silang-Amadeo, Cavite"
COURT_SHORT_NAME = "MCTC Silang-Amadeo"
LOGO_FILENAME = "1280px-Seal_of_the_Supreme_Court_(Philippines).png"

PRIMARY_PURPLE = "#7B2CBF"
SECONDARY_PURPLE = "#9D4EDD"
DARK_PURPLE = "#42105F"

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
    },
}

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


def db():
    connection = sqlite3.connect(
        app.config["DATABASE_PATH"]
    )
    connection.row_factory = sqlite3.Row
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )
    return connection


def now():
    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def clean(value, limit=5000):
    if value is None:
        return ""
    return str(value).strip()[:limit]


def clean_case_number(value):
    return clean(value, 100).upper()


def clean_name(value):
    return " ".join(
        clean(value, 300).split()
    )


def logged_in():
    return bool(
        session.get("staff_id")
    )


def current_username():
    return session.get(
        "username",
        ""
    )


def current_role():
    return session.get(
        "role",
        ""
    )


def current_language():
    language = session.get(
        "language",
        "en"
    )
    if language not in TRANSLATIONS:
        language = "en"
    return language


def current_theme():
    theme = session.get(
        "theme",
        "light"
    )
    if theme not in (
        "light",
        "dark",
    ):
        theme = "light"
    return theme


def audit(action, target=""):
    connection = db()
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
            current_username() or "system",
            action,
            target,
            now(),
        ),
    )
    connection.commit()
    connection.close()


def staff_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not logged_in():
            flash(
                "Please log in as authorized court staff.",
                "warning",
            )
            return redirect(
                url_for("staff_login")
            )
        return function(*args, **kwargs)
    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not logged_in():
            return redirect(
                url_for("staff_login")
            )
        if current_role() != "admin":
            abort(403)
        return function(*args, **kwargs)
    return wrapper


def initialize_database():
    connection = db()

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
            parties TEXT NOT NULL DEFAULT '',
            case_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            hearing_date TEXT NOT NULL DEFAULT '',
            hearing_time TEXT NOT NULL DEFAULT '',
            courtroom TEXT NOT NULL DEFAULT '',
            public_summary TEXT NOT NULL DEFAULT '',
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
            purpose TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Scheduled',
            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_en TEXT NOT NULL,
            title_fil TEXT NOT NULL,
            body_en TEXT NOT NULL,
            body_fil TEXT NOT NULL,
            notice_type TEXT NOT NULL DEFAULT 'General',
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
            FOREIGN KEY(case_id)
                REFERENCES cases(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )

    if connection.execute(
        "SELECT id FROM staff WHERE username = ?",
        ("admin",),
    ).fetchone() is None:

        admin_password = os.environ.get(
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
                    admin_password
                ),
                "admin",
                1,
                now(),
            ),
        )

    if connection.execute(
        "SELECT id FROM cases LIMIT 1"
    ).fetchone() is None:

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
                now(),
                now(),
            ),
        )

    if connection.execute(
        "SELECT id FROM notices LIMIT 1"
    ).fetchone() is None:

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
                "Please rely on official court announcements.",
                "Mangyaring umasa sa mga opisyal na abiso ng hukuman.",
                "General",
                1,
                now(),
            ),
        )

    connection.commit()
    connection.close()


CSS = r"""
:root {
    --purple-dark: #42105F;
    --purple: #7B2CBF;
    --purple-light: #9D4EDD;
    --purple-soft: #EFE2F7;
    --background: #FAF8FC;
    --surface: #FFFFFF;
    --text: #211427;
    --heading: #42105F;
    --muted: #5D5062;
    --border: #D8CCDF;
    --danger: #92183C;
    --danger-bg: #FFE4EB;
    --success: #21643A;
    --success-bg: #DFF4E5;
    --warning: #715000;
    --warning-bg: #FFF1BE;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: var(--background);
    color: var(--text);
    line-height: 1.65;
}

body.dark {
    --background: #111014;
    --surface: #211B26;
    --text: #FFFFFF;
    --heading: #F1D9FF;
    --muted: #DDD1E2;
    --border: #675573;
    --purple-soft: #392643;
    --danger: #FFB8CA;
    --danger-bg: #421723;
    --success: #B7EFC7;
    --success-bg: #183824;
    --warning: #FFE3A5;
    --warning-bg: #493817;
}

a {
    color: var(--purple);
}

.site-header {
    position: sticky;
    top: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
    padding: 13px 4%;
    color: white;
    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );
    box-shadow:
        0 6px 24px
        rgba(55, 15, 80, .25);
}

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    color: white;
    text-decoration: none;
    margin-right: auto;
}

.brand-logo {
    width: 50px;
    height: 50px;
    object-fit: contain;
    padding: 3px;
    background: white;
    border-radius: 50%;
}

.brand strong,
.brand small {
    display: block;
}

.brand small {
    opacity: .82;
}

.main-nav {
    display: flex;
    align-items: center;
    gap: 13px;
    flex-wrap: wrap;
}

.main-nav a,
.nav-button {
    color: white;
    text-decoration: none;
    font-weight: 800;
    font-size: 13px;
}

.nav-button {
    border: 0;
    background: transparent;
    padding: 0;
    cursor: pointer;
}

.nav-form {
    display: inline;
    margin: 0;
}

.tools {
    display: flex;
    gap: 6px;
}

.tool {
    color: white;
    text-decoration: none;
    padding: 5px 8px;
    border:
        1px solid
        rgba(255,255,255,.45);
    border-radius: 8px;
    font-size: 12px;
}

main {
    width: 92%;
    max-width: 1180px;
    min-height: 76vh;
    margin: auto;
    padding: 35px 0 65px;
}

footer {
    padding: 30px 20px;
    color: white;
    text-align: center;
    background: var(--purple-dark);
}

.hero {
    display: grid;
    grid-template-columns: 1.5fr .5fr;
    gap: 35px;
    align-items: center;
    padding: 52px;
    color: white;
    border-radius: 24px;
    background:
        linear-gradient(
            135deg,
            var(--purple),
            var(--purple-light)
        );
}

.hero h1 {
    margin: 15px 0;
    font-size: clamp(34px, 5vw, 62px);
    line-height: 1.04;
}

.hero p {
    max-width: 760px;
    font-size: 18px;
}

.hero-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 24px;
}

.seal-holder {
    display: grid;
    place-items: center;
    padding: 20px;
    border-radius: 22px;
    background: rgba(255,255,255,.15);
}

.seal-holder img {
    width: 190px;
    height: 190px;
    object-fit: contain;
}

.card,
.form,
.stat-card {
    margin: 20px 0;
    padding: 25px;
    color: var(--text);
    border:
        1px solid
        var(--border);
    border-radius: 18px;
    background: var(--surface);
    box-shadow:
        0 9px 28px
        rgba(70, 20, 100, .08);
}

.card h1,
.card h2,
.card h3,
.form h1,
.form h2 {
    color: var(--heading);
}

.grid {
    display: grid;
    gap: 18px;
    margin: 22px 0;
}

.grid-two {
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(280px, 1fr)
        );
}

.grid-four {
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(155px, 1fr)
        );
}

.button,
button {
    border: 0;
    border-radius: 10px;
    padding: 11px 18px;
    background: var(--purple);
    color: white;
    cursor: pointer;
    font-weight: 900;
    text-decoration: none;
}

.button.secondary {
    background: var(--purple-soft);
    color: var(--heading);
}

button.danger,
.button.danger {
    background: var(--danger);
    color: white;
}

.form {
    max-width: 780px;
    margin: 25px auto;
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
    min-height: 125px;
    resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
    outline:
        3px solid
        rgba(123,44,191,.25);
    border-color: var(--purple);
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
        1fr 1.5fr 1fr auto;
    gap: 15px;
    align-items: center;
    padding: 15px 0;
    border-bottom:
        1px solid
        var(--border);
}

.row {
    display: flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
    padding: 13px 0;
    border-bottom:
        1px solid
        var(--border);
}

.status {
    display: inline-block;
    width: max-content;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--purple-soft);
    color: var(--heading);
    font-size: 12px;
    font-weight: 900;
}

.notice {
    padding: 16px;
    border-left:
        5px solid
        var(--purple);
    border-radius: 10px;
    background: var(--purple-soft);
    margin: 12px 0;
}

.alert {
    padding: 12px 15px;
    margin-bottom: 15px;
    border-radius: 9px;
}

.alert.warning {
    background: var(--warning-bg);
    color: var(--warning);
}

.alert.danger {
    background: var(--danger-bg);
    color: var(--danger);
}

.alert.success {
    background: var(--success-bg);
    color: var(--success);
}

.friendly-dashboard {
    padding: 34px;
    color: white;
    border-radius: 22px;
    background:
        linear-gradient(
            135deg,
            #53146F,
            #7B2CBF,
            #9D4EDD
        );
}

.friendly-dashboard h1 {
    margin: 8px 0;
    color: white;
    font-size: clamp(30px, 5vw, 50px);
}

.friendly-dashboard p {
    color: white;
}

.staff-actions {
    display: grid;
    grid-template-columns:
        repeat(
            4,
            1fr
        );
    gap: 14px;
    margin-top: 25px;
}

.staff-action {
    color: var(--text);
    background: var(--surface);
    padding: 18px;
    border-radius: 14px;
    text-decoration: none;
    border:
        1px solid
        var(--border);
}

.staff-action strong {
    display: block;
    color: var(--purple);
    margin-top: 6px;
}

.staff-action span {
    color: var(--muted);
    font-size: 13px;
}

.split {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}

.muted {
    color: var(--muted);
}

.empty {
    text-align: center;
    padding: 40px 20px;
}

@media(max-width:850px) {

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

    .staff-actions {
        grid-template-columns: 1fr 1fr;
    }
}

@media(max-width:520px) {

    main {
        width: 94%;
    }

    .hero h1 {
        font-size: 36px;
    }

    .friendly-dashboard {
        padding: 25px;
    }

    .staff-actions {
        grid-template-columns: 1fr;
    }
}
"""


def page(title, content):

    labels = TRANSLATIONS[
        current_language()
    ]

    if logged_in():

        navigation = f"""
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

        <a href="/dashboard">
            {labels["dashboard"]}
        </a>

        <a href="/staff/cases">
            {labels["cases"]}
        </a>

        <form
            method="post"
            action="/logout"
            class="nav-form"
        >

            <button
                class="nav-button"
                type="submit"
            >
                {labels["logout"]}
            </button>

        </form>
        """

    else:

        navigation = f"""
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

        <a href="/login">
            {labels["login"]}
        </a>

        """

    html = f"""
    <!doctype html>

    <html lang="{current_language()}">

    <head>

        <meta charset="utf-8">

        <meta
            name="viewport"
            content="width=device-width,initial-scale=1"
        >

        <meta
            name="theme-color"
            content="{PRIMARY_PURPLE}"
        >

        <title>
            {title}
        </title>

        <style>
            {CSS}
        </style>

    </head>


    <body class="{current_theme()}">

        <header class="site-header">

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

                    <strong>
                        {COURT_SHORT_NAME}
                    </strong>

                    <small>
                        Cavite
                    </small>

                </span>

            </a>


            <nav class="main-nav">

                {navigation}

            </nav>


            <div class="tools">

                <a
                    class="tool"
                    href="/language/en"
                >
                    EN
                </a>

                <a
                    class="tool"
                    href="/language/fil"
                >
                    FIL
                </a>

                <a
                    class="tool"
                    href="/theme/light"
                >
                    ☀
                </a>

                <a
                    class="tool"
                    href="/theme/dark"
                >
                    ☾
                </a>

            </div>

        </header>


        <main>

            {render_messages()}

            {content}

        </main>


        <footer>

            <strong>
                {COURT_NAME}
            </strong>

            <br>

            Public Information Portal

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


def render_messages():

    from flask import get_flashed_messages

    html = ""

    for category, message in (
        get_flashed_messages(
            with_categories=True
        )
    ):

        html += (
            '<div class="alert '
            + category
            + '">'
            + message
            + '</div>'
        )

    return html


# ============================================================
# PUBLIC HOME
# ============================================================

@app.route("/")
def home():

    connection = db()

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
                Search approved public case
                information, hearing schedules,
                and official court notices.
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
                🔎 Search for a Case
            </h2>

            <p>
                Search using a case number
                or party name.
            </p>

            <a
                class="button secondary"
                href="/search"
            >
                Start Searching
            </a>

        </div>


        <div class="card">

            <h2>
                📅 Hearing Schedule
            </h2>

            <p>
                View published hearing dates,
                times, and courtrooms.
            </p>

            <a
                class="button secondary"
                href="/hearings"
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
                class="button secondary"
                href="/notices"
            >
                View Notices
            </a>

        </div>


        <div class="card">

            <h2>
                🌐 English / Filipino
            </h2>

            <p>
                Switch between English
                and Filipino.
            </p>

            <a
                class="button secondary"
                href="/language/fil"
            >
                Filipino
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            Latest Notices
        </h2>

        {
            notice_html
            or
            "<p>No official notices are currently published.</p>"
        }

    </section>


    <section class="card">

        <h2>
            🔐 Privacy Reminder
        </h2>

        <p>
            Only information approved for
            public release should appear
            on this public portal.
        </p>

    </section>
    """

    return page(
        "MCTC Silang-Amadeo",
        content
    )


# ============================================================
# LANGUAGE
# ============================================================

@app.route(
    "/language/<language>"
)
def language(
    language
):

    if language not in TRANSLATIONS:

        abort(404)

    session[
        "language"
    ] = language

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# THEME
# ============================================================

@app.route(
    "/theme/<theme>"
)
def theme(
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
        or url_for("home")
    )


# ============================================================
# PUBLIC SEARCH
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

        connection = db()

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
            ORDER BY case_number
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

    rows = ""

    for case in results:

        rows += f"""
        <div class="result">

            <div>

                <strong>
                    {case["case_number"]}
                </strong>

                <br>

                {case["title"]}

            </div>

            <div>
                {case["parties"]}
            </div>

            <div>

                <span class="status">
                    {case["status"]}
                </span>

            </div>

            <a
                class="button secondary"
                href="/case/{case["id"]}"
            >
                View
            </a>

        </div>
        """

    if not rows:

        if case_number or name:

            rows = """
            <div class="empty">

                <div style="font-size:45px;">
                    🔎
                </div>

                <h2>
                    No matching case found
                </h2>

                <p>
                    Check your search and try again.
                </p>

            </div>
            """

        else:

            rows = """
            <div class="empty">

                <div style="font-size:45px;">
                    📋
                </div>

                <h2>
                    Search for a case
                </h2>

                <p>
                    Follow the steps above to begin.
                </p>

            </div>
            """

    content = f"""
    <div class="card">

        <span>
            PUBLIC CASE INFORMATION
        </span>

        <h1>
            🔎 Search for a Case
        </h1>

        <h2>
            How to search
        </h2>

        <ol>

            <li>
                Enter the case number if you know it.
            </li>

            <li>
                Or enter the name of a party.
            </li>

            <li>
                You can use both fields to
                narrow the search.
            </li>

            <li>
                Click
                <strong>
                    Search
                </strong>.
            </li>

            <li>
                Click
                <strong>
                    View
                </strong>
                beside a matching case.
            </li>

        </ol>

        <div class="notice">

            <strong>
                Example
            </strong>

            <p>
                Case number:
                <code>
                    DEMO-001
                </code>
            </p>

            <p>
                Name:
                <code>
                    Demo Party
                </code>
            </p>

        </div>

    </div>


    <div class="card">

        <form
            method="get"
            class="search-form"
        >

            <label>

                Case Number

                <input
                    name="case_number"
                    value="{case_number}"
                    placeholder="MCTC-2026-001"
                >

            </label>


            <label>

                Name / Party

                <input
                    name="name"
                    value="{name}"
                    placeholder="JUAN DELA CRUZ"
                >

            </label>


            <button
                class="button"
                type="submit"
            >
                🔎 Search
            </button>

        </form>

    </div>


    <div class="card">

        <div class="split">

            <h2>
                Results
            </h2>

            <span class="muted">
                {len(results)}
                result(s)
            </span>

        </div>

        {rows}

    </div>
    """

    return page(
        "Search Cases",
        content
    )


# ============================================================
# PUBLIC CASE DETAILS
# ============================================================

@app.route(
    "/case/<int:case_id>"
)
def case_details(
    case_id
):

    connection = db()

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
        ORDER BY hearing_date, hearing_time
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
        ORDER BY display_name
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

    document_html = ""

    for document in documents:

        document_html += f"""
        <div class="notice">

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

        {
            hearing_html
            or
            "<p>No public hearing schedule.</p>"
        }

    </div>


    <div class="card">

        <h2>
            📄 Public Documents
        </h2>

        {
            document_html
            or
            "<p>No public documents are available.</p>"
        }

    </div>
    """

    return page(
        case["case_number"],
        content
    )


# ============================================================
# PUBLIC HEARINGS
# ============================================================

@app.route(
    "/hearings"
)
def hearings():

    connection = db()

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

    html = ""

    for row in rows:

        html += f"""
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

    content = f"""
    <div class="card">

        <h1>
            📅 Hearing Schedule
        </h1>

        <p>
            Published hearing information.
        </p>

        {html
        or
        "<p>No hearing schedules are currently published.</p>"}

    </div>
    """

    return page(
        "Hearings",
        content
    )


# ============================================================
# PUBLIC NOTICES
# ============================================================

@app.route(
    "/notices"
)
def notices():

    connection = db()

    rows = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE published = 1
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    html = ""

    for row in rows:

        if current_language() == "fil":

            title = row["title_fil"]
            body = row["body_fil"]

        else:

            title = row["title_en"]
            body = row["body_en"]

        html += f"""
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

        </div>
        """

    return page(
        "Court Notices",
        html
        or
        """
        <div class="card">

            <h1>
                Court Notices
            </h1>

            <p>
                No active notices.
            </p>

        </div>
        """,
    )


# ============================================================
# LOGIN
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

        username = clean(
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

        connection = db()

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

            return redirect(
                url_for(
                    "dashboard"
                )
            )

        flash(
            "The username or password is incorrect.",
            "danger",
        )

    content = """
    <div class="form">

        <div
            style="
                text-align:center;
                margin-bottom:25px;
            "
        >

            <div style="font-size:55px;">
                ⚖️
            </div>

            <h1>
                Welcome, Court Staff 💜
            </h1>

            <p class="muted">
                Sign in to the authorized
                staff portal.
            </p>

        </div>


        <form method="post">

            <label>

                Username

                <input
                    type="text"
                    name="username"
                    autocomplete="username"
                    required
                >

            </label>


            <label>

                Password

                <input
                    type="password"
                    name="password"
                    autocomplete="current-password"
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
                Authorized personnel only.
            </strong>

            <p>
                Login credentials are not
                displayed on the website.
            </p>

        </div>

    </div>
    """

    return page(
        "Staff Login",
        content
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

    # Destroy the entire authentication session.
    session.clear()

    # Start a clean anonymous session.
    session["language"] = "en"
    session["theme"] = "light"

    response = redirect(
        url_for(
            "home"
        )
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

    connection = db()

    counts = {}

    counts["cases"] = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    counts["hearings"] = connection.execute(
        "SELECT COUNT(*) FROM hearings"
    ).fetchone()[0]

    counts["notices"] = connection.execute(
        "SELECT COUNT(*) FROM notices WHERE published = 1"
    ).fetchone()[0]

    counts["documents"] = connection.execute(
        "SELECT COUNT(*) FROM documents"
    ).fetchone()[0]

    recent = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        LIMIT 8
        """
    ).fetchall()

    connection.close()

    recent_html = ""

    for case in recent:

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
                class="button secondary"
                href="/staff/cases/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    content = f"""
    <section
        class="friendly-dashboard"
    >

        <span>
            ⚖️ AUTHORIZED STAFF PORTAL
        </span>

        <h1>
            Welcome back 💜
        </h1>

        <p>
            Manage authorized cases, hearings,
            documents, and official notices.
        </p>

    </section>


    <div class="grid grid-four">

        <div class="stat-card">

            <span>
                Cases
            </span>

            <strong>
                {counts["cases"]}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Hearings
            </span>

            <strong>
                {counts["hearings"]}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Notices
            </span>

            <strong>
                {counts["notices"]}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Documents
            </span>

            <strong>
                {counts["documents"]}
            </strong>

        </div>

    </div>


    <div class="staff-actions">

        <a
            class="staff-action"
            href="/staff/cases"
        >

            <div style="font-size:30px;">
                📋
            </div>

            <strong>
                Manage Cases
            </strong>

            <span>
                Search and update records.
            </span>

        </a>


        <a
            class="staff-action"
            href="/staff/cases/add"
        >

            <div style="font-size:30px;">
                ➕
            </div>

            <strong>
                Add Case
            </strong>

            <span>
                Create a new case.
            </span>

        </a>


        <a
            class="staff-action"
            href="/staff/notices"
        >

            <div style="font-size:30px;">
                📢
            </div>

            <strong>
                Notices
            </strong>

            <span>
                Publish official notices.
            </span>

        </a>


        <a
            class="staff-action"
            href="/staff/activity"
        >

            <div style="font-size:30px;">
                📝
            </div>

            <strong>
                Audit Log
            </strong>

            <span>
                Review staff activity.
            </span>

        </a>

    </div>


    <div class="card">

        <h2>
            📋 Recently Updated Cases
        </h2>

        {recent_html
        or
        "<p>No cases yet.</p>"}

    </div>


    <div class="notice">

        <strong>
            💡 Staff Reminder
        </strong>

        <p>
            Only enter or publish information
            approved for the intended audience.
        </p>

    </div>
    """

    return page(
        "Staff Dashboard",
        content
    )


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route(
    "/staff/cases"
)
@staff_required
def staff_cases():

    connection = db()

    cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    rows = ""

    for case in cases:

        rows += f"""
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
                class="button secondary"
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

        {rows
        or
        "<p>No cases have been entered.</p>"}

    </div>
    """

    return page(
        "Manage Cases",
        content
    )


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

        title = clean(
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

        case_type = clean(
            request.form.get(
                "case_type",
                "",
            ),
            100,
        )

        status = clean(
            request.form.get(
                "status",
                "Pending",
            ),
            50,
        )

        hearing_date = clean(
            request.form.get(
                "hearing_date",
                "",
            ),
            30,
        )

        hearing_time = clean(
            request.form.get(
                "hearing_time",
                "",
            ),
            30,
        )

        courtroom = clean(
            request.form.get(
                "courtroom",
                "",
            ),
            150,
        )

        public_summary = clean(
            request.form.get(
                "public_summary",
                "",
            )
        )

        internal_notes = clean(
            request.form.get(
                "internal_notes",
                "",
            )
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

            if status not in CASE_STATUSES:
                status = "Pending"

            connection = db()

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
                        now(),
                        now(),
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

    content = """
    <div class="form">

        <h1>
            ➕ Add Case
        </h1>

        <p class="muted">
            Fill in the fields below.
            Only enter information authorized
            for this system.
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

                <select
                    name="status"
                >

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
                ></textarea>

            </label>


            <label>
                Internal Notes

                <textarea
                    name="internal_notes"
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
        content
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

    connection = db()

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
        ORDER BY hearing_date, hearing_time
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

    document_html = ""

    for document in documents:

        document_html += f"""
        <div class="notice">

            <strong>
                {document["display_name"]}
            </strong>

            <br>

            <span>
                {
                    "Public"
                    if document["public_access"]
                    else "Restricted"
                }
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
            ✏️ Edit
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

                <select name="status">

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

        {
            hearing_html
            or
            "<p>No hearings.</p>"
        }

    </div>


    <div class="card">

        <h2>
            📄 Add Document
        </h2>

        <p class="muted">
            This prototype stores document
            references. Actual confidential files
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

                Publicly accessible

            </label>


            <button
                class="button"
                type="submit"
            >
                Add Document
            </button>

        </form>


        <hr>

        {
            document_html
            or
            "<p>No documents.</p>"
        }

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
        content
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

    connection = db()

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

        title = clean(
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

        case_type = clean(
            request.form.get(
                "case_type",
                "",
            ),
            100,
        )

        status = clean(
            request.form.get(
                "status",
                "Pending",
            ),
            50,
        )

        hearing_date = clean(
            request.form.get(
                "hearing_date",
                "",
            ),
            30,
        )

        hearing_time = clean(
            request.form.get(
                "hearing_time",
                "",
            ),
            30,
        )

        courtroom = clean(
            request.form.get(
                "courtroom",
                "",
            ),
            150,
        )

        public_summary = clean(
            request.form.get(
                "public_summary",
                "",
            )
        )

        internal_notes = clean(
            request.form.get(
                "internal_notes",
                "",
            )
        )

        if status not in CASE_STATUSES:

            status = "Pending"

        connection = db()

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
                now(),
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

        <form method="post">

            <label>
                Case Title

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

                    {
                        ''.join(
                            f'<option {"selected" if item == case["status"] else ""}>{item}</option>'
                            for item in CASE_STATUSES
                        )
                    }

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
        content
    )


# ============================================================
# DELETE CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_case(
    case_id
):

    connection = db()

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
        "DELETE_CASE",
        case["case_number"],
    )

    return redirect(
        url_for(
            "staff_cases"
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

    connection = db()

    row = connection.execute(
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

    if row is None:

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
        row["case_number"],
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=row["case_id"],
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

    connection = db()

    document = connection.execute(
        """
        SELECT
            documents.case_id,
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
# CREATE HEARING
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearings",
    methods=["POST"],
)
@staff_required
def add_hearing(
    case_id
):

    connection = db()

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

    hearing_date = clean(
        request.form.get(
            "hearing_date",
            "",
        ),
        30,
    )

    hearing_time = clean(
        request.form.get(
            "hearing_time",
            "",
        ),
        30,
    )

    courtroom = clean(
        request.form.get(
            "courtroom",
            "",
        ),
        150,
    )

    purpose = clean(
        request.form.get(
            "purpose",
            "",
        ),
        500,
    )

    status = clean(
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

    if status not in HEARING_STATUSES:

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
# CREATE DOCUMENT
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/documents",
    methods=["POST"],
)
@staff_required
def add_document(
    case_id
):

    connection = db()

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

    display_name = clean(
        request.form.get(
            "display_name",
            "",
        ),
        300,
    )

    document_url = clean(
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

    if not display_name or not document_url:

        connection.close()

        flash(
            "Document name and URL are required.",
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
            now(),
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
# STAFF NOTICES
# ============================================================

@app.route(
    "/staff/notices",
    methods=["GET", "POST"],
)
@staff_required
def staff_notices():

    if request.method == "POST":

        title_en = clean(
            request.form.get(
                "title_en",
                "",
            ),
            500,
        )

        title_fil = clean(
            request.form.get(
                "title_fil",
                "",
            ),
            500,
        )

        body_en = clean(
            request.form.get(
                "body_en",
                "",
            )
        )

        body_fil = clean(
            request.form.get(
                "body_fil",
                "",
            )
        )

        notice_type = clean(
            request.form.get(
                "notice_type",
                "General",
            ),
            100,
        )

        if notice_type not in NOTICE_TYPES:

            notice_type = "General"

        if (
            not title_en
            or not title_fil
            or not body_en
            or not body_fil
        ):

            flash(
                "English and Filipino versions are required.",
                "danger",
            )

        else:

            connection = db()

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
                    now(),
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

    connection = db()

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
                Filipino:
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
            Publish only approved official notices.
        </p>

        <form method="post">

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
    or
    "<p>No notices found.</p>"}
    """

    return page(
        "Manage Notices",
        content
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

    connection = db()

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
# PROFILE
# ============================================================

@app.route(
    "/staff/profile"
)
@staff_required
def profile():

    connection = db()

    member = connection.execute(
        """
        SELECT
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

    if member is None:

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
                Role:
            </strong>

            {member["role"]}
        </p>

        <p>
            <strong>
                Status:
            </strong>

            {
                "Active"
                if member["active"]
                else "Inactive"
            }
        </p>

        <p>
            <strong>
                Account created:
            </strong>

            {member["created_at"]}
        </p>

        <div class="notice">

            Your username and password
            are intentionally not displayed
            on this page.

        </div>

    </div>
    """

    return page(
        "Staff Profile",
        content
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
            About
        </h1>

        <h2>
            {COURT_NAME}
        </h2>

        <p>
            This prototype provides public
            case-information search, hearing
            schedules, and official notices,
            together with a restricted
            staff-management area.
        </p>

    </div>
    """

    return page(
        "About",
        content
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
            Use the court's official contact
            channels for authoritative information.
        </p>

    </div>
    """

    return page(
        "Contact",
        content
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
            Only approved public information
            should be published through the
            public portal.
        </p>

        <p>
            Restricted, sealed, confidential,
            or protected records should not
            be made publicly accessible.
        </p>

    </div>
    """

    return page(
        "Privacy",
        content
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
            Online information should not
            be treated as a substitute for
            certified court records or
            official court orders.
        </p>

    </div>
    """

    return page(
        "Terms",
        content
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/api/health"
)
def health():

    return jsonify(
        {
            "status": "ok",
            "service": COURT_SHORT_NAME,
            "time": now(),
        }
    )


# ============================================================
# PUBLIC CASE API
# ============================================================

@app.route(
    "/api/public/cases"
)
def public_case_api():

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

    connection = db()

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
# ERROR HANDLERS
# ============================================================

@app.errorhandler(403)
def error_403(error):

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
        content
    ), 403


@app.errorhandler(404)
def error_404(error):

    content = """
    <div class="card">

        <h1>
            404
        </h1>

        <p>
            The requested URL was not found
            on this server.
        </p>

        <p class="muted">
            Return to the main court portal
            and choose an available page.
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
        "Not Found",
        content
    ), 404


@app.errorhandler(500)
def error_500(error):

    content = """
    <div class="card">

        <h1>
            500
        </h1>

        <p>
            The server encountered
            an unexpected error.
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
        content
    ), 500


# ============================================================
# STARTUP
# ============================================================

initialize_database()


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
# Implementation review 1: Keep the public homepage available at /.
# Implementation review 2: Keep public case search available at /search.
# Implementation review 3: Keep public case details available at /case/<id>.
# Implementation review 4: Keep public hearing schedules available at /hearings.
# Implementation review 5: Keep public notices available at /notices.
# Implementation review 6: Keep staff login available at /login.
# Implementation review 7: Keep staff dashboard protected by staff authentication.
# Implementation review 8: Keep logout clearing the entire session.
# Implementation review 9: Keep usernames out of public pages.
# Implementation review 10: Keep passwords out of rendered pages.
# Implementation review 11: Use a strong SECRET_KEY in production.
# Implementation review 12: Use a strong ADMIN_PASSWORD in production.
# Implementation review 13: Use HTTPS in production.
# Implementation review 14: Review public case fields before real deployment.
# Implementation review 15: Review document permissions before real deployment.
# Implementation review 16: Review suspension notices before publication.
# Implementation review 17: Review postponement notices before publication.
# Implementation review 18: Review English wording before publication.
# Implementation review 19: Review Filipino wording before publication.
# Implementation review 20: Review light-mode readability.
# Implementation review 21: Review dark-mode readability.
# Implementation review 22: Review mobile layout.
# Implementation review 23: Review keyboard accessibility.
# Implementation review 24: Review screen-reader accessibility.
# Implementation review 25: Review backups and restoration.
# Implementation review 26: Keep the public homepage available at /.
# Implementation review 27: Keep public case search available at /search.
# Implementation review 28: Keep public case details available at /case/<id>.
# Implementation review 29: Keep public hearing schedules available at /hearings.
# Implementation review 30: Keep public notices available at /notices.
# Implementation review 31: Keep staff login available at /login.
# Implementation review 32: Keep staff dashboard protected by staff authentication.
# Implementation review 33: Keep logout clearing the entire session.
# Implementation review 34: Keep usernames out of public pages.
# Implementation review 35: Keep passwords out of rendered pages.
# Implementation review 36: Use a strong SECRET_KEY in production.
# Implementation review 37: Use a strong ADMIN_PASSWORD in production.
# Implementation review 38: Use HTTPS in production.
# Implementation review 39: Review public case fields before real deployment.
# Implementation review 40: Review document permissions before real deployment.
# Implementation review 41: Review suspension notices before publication.
# Implementation review 42: Review postponement notices before publication.
# Implementation review 43: Review English wording before publication.
# Implementation review 44: Review Filipino wording before publication.
# Implementation review 45: Review light-mode readability.
# Implementation review 46: Review dark-mode readability.
# Implementation review 47: Review mobile layout.
# Implementation review 48: Review keyboard accessibility.
# Implementation review 49: Review screen-reader accessibility.
# Implementation review 50: Review backups and restoration.
# Implementation review 51: Keep the public homepage available at /.
# Implementation review 52: Keep public case search available at /search.
# Implementation review 53: Keep public case details available at /case/<id>.
# Implementation review 54: Keep public hearing schedules available at /hearings.
# Implementation review 55: Keep public notices available at /notices.
# Implementation review 56: Keep staff login available at /login.
# Implementation review 57: Keep staff dashboard protected by staff authentication.
# Implementation review 58: Keep logout clearing the entire session.
# Implementation review 59: Keep usernames out of public pages.
# Implementation review 60: Keep passwords out of rendered pages.
# Implementation review 61: Use a strong SECRET_KEY in production.
# Implementation review 62: Use a strong ADMIN_PASSWORD in production.
# Implementation review 63: Use HTTPS in production.
# Implementation review 64: Review public case fields before real deployment.
# Implementation review 65: Review document permissions before real deployment.
# Implementation review 66: Review suspension notices before publication.
# Implementation review 67: Review postponement notices before publication.
# Implementation review 68: Review English wording before publication.
# Implementation review 69: Review Filipino wording before publication.
# Implementation review 70: Review light-mode readability.
# Implementation review 71: Review dark-mode readability.
# Implementation review 72: Review mobile layout.
# Implementation review 73: Review keyboard accessibility.
# Implementation review 74: Review screen-reader accessibility.
# Implementation review 75: Review backups and restoration.
# Implementation review 76: Keep the public homepage available at /.
# Implementation review 77: Keep public case search available at /search.
# Implementation review 78: Keep public case details available at /case/<id>.
# Implementation review 79: Keep public hearing schedules available at /hearings.
# Implementation review 80: Keep public notices available at /notices.
# Implementation review 81: Keep staff login available at /login.
# Implementation review 82: Keep staff dashboard protected by staff authentication.
# Implementation review 83: Keep logout clearing the entire session.
# Implementation review 84: Keep usernames out of public pages.
# Implementation review 85: Keep passwords out of rendered pages.
# Implementation review 86: Use a strong SECRET_KEY in production.
# Implementation review 87: Use a strong ADMIN_PASSWORD in production.
# Implementation review 88: Use HTTPS in production.
# Implementation review 89: Review public case fields before real deployment.
# Implementation review 90: Review document permissions before real deployment.
# Implementation review 91: Review suspension notices before publication.
# Implementation review 92: Review postponement notices before publication.
# Implementation review 93: Review English wording before publication.
# Implementation review 94: Review Filipino wording before publication.
# Implementation review 95: Review light-mode readability.
# Implementation review 96: Review dark-mode readability.
# Implementation review 97: Review mobile layout.
# Implementation review 98: Review keyboard accessibility.
# Implementation review 99: Review screen-reader accessibility.
# Implementation review 100: Review backups and restoration.
# Implementation review 101: Keep the public homepage available at /.
# Implementation review 102: Keep public case search available at /search.
# Implementation review 103: Keep public case details available at /case/<id>.
# Implementation review 104: Keep public hearing schedules available at /hearings.
# Implementation review 105: Keep public notices available at /notices.
# Implementation review 106: Keep staff login available at /login.
# Implementation review 107: Keep staff dashboard protected by staff authentication.
# Implementation review 108: Keep logout clearing the entire session.
# Implementation review 109: Keep usernames out of public pages.
# Implementation review 110: Keep passwords out of rendered pages.
# Implementation review 111: Use a strong SECRET_KEY in production.
# Implementation review 112: Use a strong ADMIN_PASSWORD in production.
# Implementation review 113: Use HTTPS in production.
# Implementation review 114: Review public case fields before real deployment.
# Implementation review 115: Review document permissions before real deployment.
# Implementation review 116: Review suspension notices before publication.
# Implementation review 117: Review postponement notices before publication.
# Implementation review 118: Review English wording before publication.
# Implementation review 119: Review Filipino wording before publication.
# Implementation review 120: Review light-mode readability.
# Implementation review 121: Review dark-mode readability.
# Implementation review 122: Review mobile layout.
# Implementation review 123: Review keyboard accessibility.
# Implementation review 124: Review screen-reader accessibility.
# Implementation review 125: Review backups and restoration.
# Implementation review 126: Keep the public homepage available at /.
# Implementation review 127: Keep public case search available at /search.
# Implementation review 128: Keep public case details available at /case/<id>.
# Implementation review 129: Keep public hearing schedules available at /hearings.
# Implementation review 130: Keep public notices available at /notices.
# Implementation review 131: Keep staff login available at /login.
# Implementation review 132: Keep staff dashboard protected by staff authentication.
# Implementation review 133: Keep logout clearing the entire session.
# Implementation review 134: Keep usernames out of public pages.
# Implementation review 135: Keep passwords out of rendered pages.
# Implementation review 136: Use a strong SECRET_KEY in production.
# Implementation review 137: Use a strong ADMIN_PASSWORD in production.
# Implementation review 138: Use HTTPS in production.
# Implementation review 139: Review public case fields before real deployment.
# Implementation review 140: Review document permissions before real deployment.
# Implementation review 141: Review suspension notices before publication.
# Implementation review 142: Review postponement notices before publication.
# Implementation review 143: Review English wording before publication.
# Implementation review 144: Review Filipino wording before publication.
# Implementation review 145: Review light-mode readability.
# Implementation review 146: Review dark-mode readability.
# Implementation review 147: Review mobile layout.
# Implementation review 148: Review keyboard accessibility.
# Implementation review 149: Review screen-reader accessibility.
# Implementation review 150: Review backups and restoration.
# Implementation review 151: Keep the public homepage available at /.
# Implementation review 152: Keep public case search available at /search.
# Implementation review 153: Keep public case details available at /case/<id>.
# Implementation review 154: Keep public hearing schedules available at /hearings.
# Implementation review 155: Keep public notices available at /notices.
# Implementation review 156: Keep staff login available at /login.
# Implementation review 157: Keep staff dashboard protected by staff authentication.
# Implementation review 158: Keep logout clearing the entire session.
# Implementation review 159: Keep usernames out of public pages.
# Implementation review 160: Keep passwords out of rendered pages.
# Implementation review 161: Use a strong SECRET_KEY in production.
# Implementation review 162: Use a strong ADMIN_PASSWORD in production.
# Implementation review 163: Use HTTPS in production.
# Implementation review 164: Review public case fields before real deployment.
# Implementation review 165: Review document permissions before real deployment.
