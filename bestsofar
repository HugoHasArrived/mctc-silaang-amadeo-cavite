from flask import Flask, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import os
import secrets

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER"
)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "mctc_court.db"
)

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

LOGO_FILENAME = (
    "1280px-Seal_of_the_Supreme_Court_(Philippines).png"
)

PRIMARY_PURPLE = "#7B2CBF"

SECONDARY_PURPLE = "#9D4EDD"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )
    return connection


def current_time():
    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def initialize_database():
    connection = get_db()

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
            published INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            url TEXT NOT NULL,
            public_access INTEGER DEFAULT 0,
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
        ("admin",)
    ).fetchone()

    if existing_staff is None:
        admin_password = os.environ.get(
            "ADMIN_PASSWORD",
            "admin123"
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
                current_time()
            )
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
                    "Please check official court announcements "
                    "for suspension, postponement, or cancellation "
                    "of hearings."
                ),
                (
                    "Mangyaring tingnan ang mga opisyal na abiso "
                    "ng hukuman para sa suspensyon, pagpapaliban, "
                    "o pagkansela ng mga pagdinig."
                ),
                "Important",
                1,
                current_time()
            )
        )

    connection.commit()
    connection.close()


# ============================================================
# AUTHENTICATION
# ============================================================

def is_logged_in():
    return bool(
        session.get("staff_id")
    )


def staff_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash(
                "Authorized staff login required.",
                "warning"
            )
            return redirect(
                url_for("staff_login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


def is_admin():
    return (
        session.get("role")
        == "admin"
    )


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(
                url_for("staff_login")
            )

        if not is_admin():
            abort(403)

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# AUDIT LOG
# ============================================================

def write_audit(
    action,
    target=""
):
    connection = get_db()

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
            session.get(
                "username",
                "system"
            ),
            action,
            target,
            current_time()
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {
    "en": {
        "home": "Home",
        "search": "Search Cases",
        "hearings": "Hearings",
        "notices": "Notices",
        "login": "Staff Login",
        "dashboard": "Dashboard",
        "logout": "Logout",
        "case_number": "Case Number",
        "name": "Name / Party",
        "status": "Status",
        "search_button": "Search",
        "public_information": "Public Information",
        "official_notice": "Official Court Notice",
        "suspension": (
            "Suspension / Postponement Notices"
        )
    },
    "fil": {
        "home": "Tahanan",
        "search": "Maghanap ng Kaso",
        "hearings": "Mga Pagdinig",
        "notices": "Mga Abiso",
        "login": "Pag-login ng Kawani",
        "dashboard": "Dashboard",
        "logout": "Mag-logout",
        "case_number": "Numero ng Kaso",
        "name": "Pangalan / Partido",
        "status": "Katayuan",
        "search_button": "Maghanap",
        "public_information": (
            "Pampublikong Impormasyon"
        ),
        "official_notice": (
            "Opisyal na Abiso ng Hukuman"
        ),
        "suspension": (
            "Mga Abiso sa Suspensyon / Pagpapaliban"
        )
    }
}


@app.context_processor
def inject_globals():
    language = session.get(
        "language",
        "en"
    )

    if language not in TRANSLATIONS:
        language = "en"

    return {
        "court_name": COURT_NAME,
        "logo_filename": LOGO_FILENAME,
        "language": language,
        "labels": TRANSLATIONS[language],
        "theme": session.get(
            "theme",
            "light"
        ),
        "logged_in": is_logged_in(),
        "username": session.get(
            "username"
        )
    }


# ============================================================
# PAGE BUILDER
# ============================================================

def render_page(
    title,
    content
):
    theme = session.get(
        "theme",
        "light"
    )

    logo_url = (
        "/static/"
        + LOGO_FILENAME
    )

    navigation = ""

    navigation += (
        '<a href="/">Home</a>'
    )

    navigation += (
        '<a href="/search">'
        'Search Cases'
        '</a>'
    )

    navigation += (
        '<a href="/hearings">'
        'Hearings'
        '</a>'
    )

    navigation += (
        '<a href="/notices">'
        'Notices'
        '</a>'
    )

    if is_logged_in():
        navigation += (
            '<a href="/dashboard">'
            'Dashboard'
            '</a>'
        )
        navigation += (
            '<a href="/logout">'
            'Logout'
            '</a>'
        )
    else:
        navigation += (
            '<a href="/login">'
            'Staff Login'
            '</a>'
        )

    css = """
    :root {
        --purple-dark: #4a126b;
        --purple: #7b2cbf;
        --purple-light: #9d4edd;
        --purple-pale: #f1e5fa;
        --background: #faf7fd;
        --surface: #ffffff;
        --text: #26132f;
        --muted: #705e77;
        --border: #e5d8eb;
        --danger: #b4234d;
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
        color: var(--text);
        line-height: 1.6;
    }

    body.dark {
        --background: #17111c;
        --surface: #241b2b;
        --text: #f5edf8;
        --muted: #bea9c7;
        --border: #4b3955;
        --purple-pale: #33213e;
    }

    header {
        position: sticky;
        top: 0;
        z-index: 100;
        background:
            linear-gradient(
                135deg,
                var(--purple-dark),
                var(--purple),
                var(--purple-light)
            );
        color: white;
        padding: 14px 5%;
        display: flex;
        gap: 20px;
        align-items: center;
        flex-wrap: wrap;
        box-shadow:
            0 5px 22px
            rgba(60, 15, 80, 0.25);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        color: white;
        margin-right: auto;
    }

    .brand img {
        width: 52px;
        height: 52px;
        object-fit: contain;
        background: white;
        border-radius: 50%;
        padding: 4px;
    }

    .brand strong {
        display: block;
    }

    .brand small {
        display: block;
        opacity: 0.85;
    }

    nav {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }

    nav a {
        color: white;
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
    }

    .tools {
        display: flex;
        gap: 7px;
    }

    .tools a {
        color: white;
        border:
            1px solid
            rgba(255,255,255,.4);
        border-radius: 8px;
        padding: 6px 9px;
        text-decoration: none;
    }

    main {
        width:
            min(1150px, 92%);
        margin: auto;
        min-height: 76vh;
        padding: 38px 0 70px;
    }

    footer {
        background:
            var(--purple-dark);
        color: white;
        text-align: center;
        padding: 32px 20px;
    }

    .hero {
        background:
            linear-gradient(
                135deg,
                var(--purple),
                var(--purple-light)
            );
        color: white;
        border-radius: 24px;
        padding: 55px;
        display: grid;
        grid-template-columns: 1.4fr .6fr;
        gap: 35px;
        align-items: center;
    }

    .hero h1 {
        font-size:
            clamp(34px, 5vw, 65px);
        line-height: 1.02;
        margin: 15px 0;
    }

    .seal {
        display: grid;
        place-items: center;
        padding: 20px;
        background: rgba(255,255,255,.15);
        border-radius: 22px;
    }

    .seal img {
        width: 190px;
        height: 190px;
        object-fit: contain;
    }

    .grid {
        display: grid;
        gap: 20px;
        margin: 25px 0;
    }

    .two {
        grid-template-columns:
            repeat(
                auto-fit,
                minmax(280px, 1fr)
            );
    }

    .four {
        grid-template-columns:
            repeat(
                auto-fit,
                minmax(160px, 1fr)
            );
    }

    .card,
    .form-card,
    .stat {
        background: var(--surface);
        border:
            1px solid
            var(--border);
        border-radius: 18px;
        padding: 25px;
        box-shadow:
            0 8px 28px
            rgba(75, 20, 111, .08);
        margin: 20px 0;
    }

    .button {
        display: inline-block;
        background: var(--purple);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 19px;
        text-decoration: none;
        font-weight: 800;
        cursor: pointer;
    }

    button {
        background: var(--purple);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 11px 18px;
        cursor: pointer;
        font-weight: 800;
    }

    .secondary {
        background: var(--purple-pale);
        color: var(--purple-dark);
    }

    form {
        display: grid;
        gap: 15px;
    }

    label {
        display: grid;
        gap: 6px;
        font-weight: 800;
    }

    input,
    textarea,
    select {
        width: 100%;
        border:
            1px solid
            var(--border);
        border-radius: 9px;
        padding: 12px;
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
            1.3fr
            1fr
            .6fr
            auto;
        gap: 12px;
        align-items: center;
        border-bottom:
            1px solid
            var(--border);
        padding: 14px 0;
    }

    .status {
        display: inline-block;
        width: max-content;
        background: var(--purple-pale);
        color: var(--purple-dark);
        border-radius: 99px;
        padding: 4px 9px;
        font-size: 12px;
        font-weight: 900;
    }

    .row {
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
        padding: 13px 0;
        border-bottom:
            1px solid
            var(--border);
    }

    .split {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        align-items: center;
    }

    .stat span {
        color: var(--muted);
    }

    .stat strong {
        display: block;
        font-size: 35px;
        color: var(--purple);
    }

    .alert {
        padding: 12px 15px;
        border-radius: 9px;
        margin-bottom: 15px;
    }

    .alert.warning {
        background: #fff0bf;
        color: #6d4d00;
    }

    .alert.danger {
        background: #ffe0e7;
        color: #861d3c;
    }

    .alert.success {
        background: #def5e4;
        color: #245b37;
    }

    .notice {
        border-left:
            5px solid
            var(--purple);
        padding: 15px;
        margin: 12px 0;
    }

    .muted {
        color: var(--muted);
    }

    .document {
        padding: 13px;
        background: var(--purple-pale);
        border-radius: 10px;
        margin: 8px 0;
    }

    @media(max-width:800px) {
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

        .split {
            align-items: flex-start;
            flex-direction: column;
        }

        header {
            align-items: flex-start;
        }

        .brand {
            width: 100%;
        }
    }
    """

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta
            name="viewport"
            content="width=device-width,
                     initial-scale=1"
        >
        <title>{title}</title>
        <style>{css}</style>
    </head>
    <body class="{theme}">
        <header>
            <a class="brand" href="/">
                <img
                    src="{logo_url}"
                    alt="Court seal"
                    onerror="
                        this.style.display='none';
                    "
                >
                <span>
                    <strong>
                        MCTC Silang-Amadeo
                    </strong>
                    <small>
                        Cavite
                    </small>
                </span>
            </a>

            <nav>
                {navigation}
            </nav>

            <div class="tools">
                <a href="/language/en">EN</a>
                <a href="/language/fil">FIL</a>
                <a href="/theme/light">☀</a>
                <a href="/theme/dark">☾</a>
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
            Public information portal prototype
        </footer>
    </body>
    </html>
    """

    return html


# ============================================================
# PUBLIC HOME
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

    notice_html = ""

    for notice in notices:
        title = notice["title_en"]

        body = notice["body_en"]

        notice_html += (
            '<div class="notice">'
            f'<span class="status">'
            f'{notice["notice_type"]}'
            f'</span>'
            f'<h3>{title}</h3>'
            f'<p>{body}</p>'
            '</div>'
        )

    if not notice_html:
        notice_html = (
            "<p>No notices have been published.</p>"
        )

    content = f"""
    <section class="hero">
        <div>
            <div>
                ⚖️ MCTC SILANG–AMADEO
            </div>

            <h1>
                {COURT_NAME}
            </h1>

            <p>
                Public case information,
                hearing schedules,
                and official court notices.
            </p>

            <a
                class="button"
                href="/search"
            >
                🔎 Search a Case
            </a>
        </div>

        <div class="seal">
            <img
                src="/static/{LOGO_FILENAME}"
                alt="Court seal"
            >
        </div>
    </section>

    <section class="grid two">

        <div class="card">
            <h2>
                🔎 Case Search
            </h2>

            <p>
                Search permitted public case
                information by case number
                or party name.
            </p>

            <a
                class="button secondary"
                href="/search"
            >
                Open Search
            </a>
        </div>

        <div class="card">
            <h2>
                📅 Hearing Schedule
            </h2>

            <p>
                View published hearing
                dates and times.
            </p>

            <a
                class="button secondary"
                href="/hearings"
            >
                View Hearings
            </a>
        </div>

        <div class="card">
            <h2>
                📢 Court Notices
            </h2>

            <p>
                Read official suspension,
                postponement, and
                court-operation notices.
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
                🌐 Language
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
            Official Notices
        </h2>

        {notice_html}
    </section>

    <section class="card">
        <h2>
            🔐 Privacy
        </h2>

        <p>
            Only information approved for
            public release should be displayed
            on the public portal. Restricted,
            sealed, or confidential records
            should not be published here.
        </p>
    </section>
    """

    return render_page(
        "MCTC Silang-Amadeo",
        content
    )


# ============================================================
# LANGUAGE
# ============================================================

@app.route("/language/<language>")
def set_language(language):

    if language not in TRANSLATIONS:
        abort(404)

    session["language"] = language

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# THEME
# ============================================================

@app.route("/theme/<theme>")
def set_theme(theme):

    if theme not in (
        "light",
        "dark"
    ):
        abort(404)

    session["theme"] = theme

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# PUBLIC CASE SEARCH
# ============================================================

@app.route("/search")
def search_cases():

    case_number = request.args.get(
        "case_number",
        ""
    ).strip()

    name = request.args.get(
        "name",
        ""
    ).strip()

    results = []

    if case_number or name:

        connection = get_db()

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
                hearing_date,
                hearing_time,
                case_number
            """,
            (
                case_number,
                "%" + case_number + "%",
                name,
                "%" + name + "%",
                "%" + name + "%"
            )
        ).fetchall()

        connection.close()

    results_html = ""

    for case in results:

        results_html += f"""
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
                href="/case/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    if not results_html:

        if case_number or name:
            results_html = (
                "<p>"
                "No matching public case "
                "information was found."
                "</p>"
            )
        else:
            results_html = (
                "<p>"
                "Enter a case number or party name."
                "</p>"
            )

    content = f"""
    <div class="card">

        <h1>
            🔎 Case Search
        </h1>

        <p>
            Search information approved
            for public access.
        </p>

        <form
            class="search-form"
            method="get"
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

            <button>
                Search
            </button>

        </form>

    </div>

    <div class="card">

        <h2>
            Results
        </h2>

        {results_html}

    </div>
    """

    return render_page(
        "Case Search",
        content
    )


# ============================================================
# PUBLIC CASE DETAILS
# ============================================================

@app.route("/case/<int:case_id>")
def case_details(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
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
        (case_id,)
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
        (case_id,)
    ).fetchall()

    connection.close()

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""
        <div class="row">

            <strong>
                {hearing["hearing_date"]}
                {hearing["hearing_time"]}
            </strong>

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
        hearing_html = (
            "<p>"
            "No hearing schedule has been published."
            "</p>"
        )

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
        document_html = (
            "<p>"
            "No public documents have been published."
            "</p>"
        )

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

        <div class="grid two">

            <div>
                <strong>
                    Hearing Date
                </strong>

                <br>

                {case["hearing_date"]
                or "Not published"}
            </div>

            <div>
                <strong>
                    Hearing Time
                </strong>

                <br>

                {case["hearing_time"]
                or "Not published"}
            </div>

            <div>
                <strong>
                    Courtroom
                </strong>

                <br>

                {case["courtroom"]
                or "Not published"}
            </div>

            <div>
                <strong>
                    Case Type
                </strong>

                <br>

                {case["case_type"]
                or "Not published"}
            </div>

        </div>

    </div>

    <div class="card">

        <h2>
            📅 Hearings
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

    return render_page(
        case["case_number"],
        content
    )


# ============================================================
# PUBLIC HEARINGS
# ============================================================

@app.route("/hearings")
def public_hearings():

    connection = get_db()

    hearings = connection.execute(
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

    if not hearing_html:
        hearing_html = (
            "<p>"
            "No hearing schedules are currently published."
            "</p>"
        )

    content = f"""
    <div class="card">

        <h1>
            📅 Public Hearing Schedule
        </h1>

        <p>
            Published hearing information.
        </p>

        {hearing_html}

    </div>

    <div class="card">

        <h3>
            Important
        </h3>

        <p>
            Hearing information may change.
            Please verify important information
            through the court's authorized channels.
        </p>

    </div>
    """

    return render_page(
        "Hearings",
        content
    )


# ============================================================
# PUBLIC NOTICES
# ============================================================

@app.route("/notices")
def public_notices():

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

    language = session.get(
        "language",
        "en"
    )

    notice_html = ""

    for notice in notices:

        if language == "fil":
            title = notice["title_fil"]
            body = notice["body_fil"]
        else:
            title = notice["title_en"]
            body = notice["body_en"]

        notice_html += f"""
        <div class="card">

            <span class="status">
                {notice["notice_type"]}
            </span>

            <h2>
                {title}
            </h2>

            <p>
                {body}
            </p>

            <small>
                {notice["created_at"]}
            </small>

        </div>
        """

    if not notice_html:
        notice_html = (
            "<div class='card'>"
            "<p>No active court notices.</p>"
            "</div>"
        )

    return render_page(
        "Court Notices",
        notice_html
    )


# ============================================================
# STAFF LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def staff_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = get_db()

        staff = connection.execute(
            """
            SELECT *
            FROM staff
            WHERE
                username = ?
                AND active = 1
            """,
            (username,)
        ).fetchone()

        connection.close()

        if (
            staff
            and check_password_hash(
                staff["password_hash"],
                password
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

            audit(
                "LOGIN",
                username
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    messages = get_flash_messages()

    message_html = ""

    for category, message in messages:

        message_html += (
            f'<div class="alert {category}">'
            f'{message}'
            f'</div>'
        )

    content = f"""
    <div class="form-card">

        <h1>
            🔐 Authorized Staff Login
        </h1>

        <p>
            This area is for authorized
            court personnel only.
        </p>

        {message_html}

        <form method="post">

            <label>
                Username

                <input
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

            <button>
                Sign In
            </button>

        </form>

        <p class="muted">
            Development account:
            admin / admin123
        </p>

    </div>
    """

    return render_page(
        "Staff Login",
        content
    )


def get_flash_messages():

    from flask import get_flashed_messages

    return get_flashed_messages(
        with_categories=True
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    if session.get("staff_id"):
        audit(
            "LOGOUT",
            session.get(
                "username",
                ""
            )
        )

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/dashboard")
@staff_required
def dashboard():

    connection = get_db()

    cases_count = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    hearings_count = connection.execute(
        "SELECT COUNT(*) FROM hearings"
    ).fetchone()[0]

    notices_count = connection.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    documents_count = connection.execute(
        "SELECT COUNT(*) FROM documents"
    ).fetchone()[0]

    connection.close()

    content = f"""
    <h1>
        Staff Dashboard
    </h1>

    <p>
        Welcome,
        <strong>
            {session.get("username")}
        </strong>
    </p>

    <div class="grid four">

        <div class="stat">
            <span>Cases</span>
            <strong>
                {cases_count}
            </strong>
        </div>

        <div class="stat">
            <span>Hearings</span>
            <strong>
                {hearings_count}
            </strong>
        </div>

        <div class="stat">
            <span>Notices</span>
            <strong>
                {notices_count}
            </strong>
        </div>

        <div class="stat">
            <span>Documents</span>
            <strong>
                {documents_count}
            </strong>
        </div>

    </div>

    <div class="grid two">

        <a
            class="card"
            href="/staff/cases"
        >
            <h2>
                📋 Manage Cases
            </h2>

            <p>
                Create, review, and update
                case records.
            </p>
        </a>

        <a
            class="card"
            href="/staff/notices"
        >
            <h2>
                📢 Manage Notices
            </h2>

            <p>
                Publish official court notices.
            </p>
        </a>

        <a
            class="card"
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
    """

    return render_page(
        "Dashboard",
        content
    )


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():

    connection = get_db()

    cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY
            updated_at DESC
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
            Manage Cases
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

    return render_page(
        "Manage Cases",
        content
    )


# ============================================================
# ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=["GET", "POST"]
)
@staff_required
def add_case():

    if request.method == "POST":

        case_number = request.form.get(
            "case_number",
            ""
        ).strip()

        title = request.form.get(
            "title",
            ""
        ).strip()

        parties = request.form.get(
            "parties",
            ""
        ).strip()

        case_type = request.form.get(
            "case_type",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Pending"
        ).strip()

        hearing_date = request.form.get(
            "hearing_date",
            ""
        ).strip()

        hearing_time = request.form.get(
            "hearing_time",
            ""
        ).strip()

        courtroom = request.form.get(
            "courtroom",
            ""
        ).strip()

        public_summary = request.form.get(
            "public_summary",
            ""
        ).strip()

        internal_notes = request.form.get(
            "internal_notes",
            ""
        ).strip()

        if not case_number or not title:

            flash(
                "Case number and title are required.",
                "danger"
            )

        else:

            connection = get_db()

            try:

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
                        current_time(),
                        current_time()
                    )
                )

                connection.commit()

                write_audit(
                    "CREATE_CASE",
                    case_number
                )

                connection.close()

                return redirect(
                    url_for("staff_cases")
                )

            except sqlite3.IntegrityError:

                connection.rollback()
                connection.close()

                flash(
                    "That case number already exists.",
                    "danger"
                )

    content = """
    <div class="form-card">

        <h1>
            Add Case
        </h1>

        <form method="post">

            <label>
                Case Number

                <input
                    name="case_number"
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

            <button>
                Save Case
            </button>

        </form>

    </div>
    """

    return render_page(
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
def staff_case(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
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
        (case_id,)
    ).fetchall()

    documents = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE case_id = ?
        ORDER BY
            created_at DESC
        """,
        (case_id,)
    ).fetchall()

    connection.close()

    hearings_html = ""

    for hearing in hearings:

        hearings_html += f"""
        <div class="row">

            <span>
                {hearing["hearing_date"]}
            </span>

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

                <button>
                    Delete
                </button>

            </form>

        </div>
        """

    documents_html = ""

    for document in documents:

        visibility = (
            "Public"
            if document["public_access"]
            else "Restricted"
        )

        documents_html += f"""
        <div class="document">

            <strong>
                {document["display_name"]}
            </strong>

            <br>

            <span>
                {visibility}
            </span>

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
            Edit Case
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
                Internal Notes:
            </strong>

            {case["internal_notes"]}
        </p>

        <p>
            <strong>
                Public Summary:
            </strong>

            {case["public_summary"]}
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
                Date
                <input
                    type="date"
                    name="hearing_date"
                    required
                >
            </label>

            <label>
                Time
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
                <input
                    name="status"
                    value="Scheduled"
                >
            </label>

            <button>
                Add Hearing
            </button>

        </form>

    </div>

    <div class="card">

        <h2>
            Existing Hearings
        </h2>

        {hearings_html
        or "<p>No hearings.</p>"}

    </div>

    <div class="card">

        <h2>
            📄 Add Document
        </h2>

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
                URL
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

            <button>
                Add Document
            </button>

        </form>

        {documents_html
        or "<p>No documents.</p>"}

    </div>
    """

    return render_page(
        "Staff Case",
        content
    )


# ============================================================
# EDIT CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=["GET", "POST"]
)
@staff_required
def edit_case(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
    ).fetchone()

    connection.close()

    if case is None:
        abort(404)

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        parties = request.form.get(
            "parties",
            ""
        ).strip()

        case_type = request.form.get(
            "case_type",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Pending"
        ).strip()

        hearing_date = request.form.get(
            "hearing_date",
            ""
        ).strip()

        hearing_time = request.form.get(
            "hearing_time",
            ""
        ).strip()

        courtroom = request.form.get(
            "courtroom",
            ""
        ).strip()

        public_summary = request.form.get(
            "public_summary",
            ""
        ).strip()

        internal_notes = request.form.get(
            "internal_notes",
            ""
        ).strip()

        connection = get_db()

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
                current_time(),
                case_id
            )
        )

        connection.commit()
        connection.close()

        write_audit(
            "UPDATE_CASE",
            case["case_number"]
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id
            )
        )

    content = f"""
    <div class="form-card">

        <h1>
            Edit {case["case_number"]}
        </h1>

        <form method="post">

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

                <input
                    name="status"
                    value="{case["status"]}"
                >
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

            <button>
                Update Case
            </button>

        </form>

    </div>
    """

    return render_page(
        "Edit Case",
        content
    )


# ============================================================
# ADD HEARING
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearings",
    methods=["POST"]
)
@staff_required
def create_hearing(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
    ).fetchone()

    if case is None:
        connection.close()
        abort(404)

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
            request.form.get(
                "hearing_date",
                ""
            ).strip(),
            request.form.get(
                "hearing_time",
                ""
            ).strip(),
            request.form.get(
                "courtroom",
                ""
            ).strip(),
            request.form.get(
                "purpose",
                ""
            ).strip(),
            request.form.get(
                "status",
                "Scheduled"
            ).strip()
        )
    )

    connection.commit()
    connection.close()

    write_audit(
        "CREATE_HEARING",
        case["case_number"]
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=case_id
        )
    )


# ============================================================
# DELETE HEARING
# ============================================================

@app.route(
    "/staff/hearings/<int:hearing_id>/delete",
    methods=["POST"]
)
@staff_required
def remove_hearing(hearing_id):

    connection = get_db()

    hearing = connection.execute(
        """
        SELECT
            hearings.id,
            cases.case_number
        FROM hearings
        JOIN cases
            ON cases.id = hearings.case_id
        WHERE hearings.id = ?
        """,
        (hearing_id,)
    ).fetchone()

    if hearing is None:
        connection.close()
        abort(404)

    connection.execute(
        """
        DELETE FROM hearings
        WHERE id = ?
        """,
        (hearing_id,)
    )

    connection.commit()
    connection.close()

    write_audit(
        "DELETE_HEARING",
        hearing["case_number"]
    )

    return redirect(
        request.referrer
        or url_for("dashboard")
    )


# ============================================================
# ADD DOCUMENT
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/documents",
    methods=["POST"]
)
@staff_required
def create_document(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
    ).fetchone()

    if case is None:
        connection.close()
        abort(404)

    display_name = request.form.get(
        "display_name",
        ""
    ).strip()

    url = request.form.get(
        "url",
        ""
    ).strip()

    public_access = (
        1
        if request.form.get(
            "public_access"
        )
        else 0
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
            url,
            public_access,
            current_time()
        )
    )

    connection.commit()
    connection.close()

    write_audit(
        "CREATE_DOCUMENT",
        case["case_number"]
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=case_id
        )
    )


# ============================================================
# MANAGE NOTICES
# ============================================================

@app.route(
    "/staff/notices",
    methods=["GET", "POST"]
)
@staff_required
def manage_notices():

    if request.method == "POST":

        title_en = request.form.get(
            "title_en",
            ""
        ).strip()

        title_fil = request.form.get(
            "title_fil",
            ""
        ).strip()

        body_en = request.form.get(
            "body_en",
            ""
        ).strip()

        body_fil = request.form.get(
            "body_fil",
            ""
        ).strip()

        notice_type = request.form.get(
            "notice_type",
            "General"
        ).strip()

        connection = get_db()

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
                current_time()
            )
        )

        connection.commit()
        connection.close()

        write_audit(
            "CREATE_NOTICE",
            title_en
        )

        return redirect(
            url_for("manage_notices")
        )

    connection = get_db()

    notices = connection.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    notice_html = ""

    for notice in notices:

        notice_html += f"""
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

            <form
                method="post"
                action="/staff/notices/{notice["id"]}/delete"
            >
                <button>
                    Delete
                </button>
            </form>

        </div>
        """

    content = f"""
    <div class="form-card">

        <h1>
            Create Official Notice
        </h1>

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

                <select name="notice_type">

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

            <button>
                Publish Notice
            </button>

        </form>

    </div>

    {notice_html}

    """

    return render_page(
        "Manage Notices",
        content
    )


# ============================================================
# DELETE NOTICE
# ============================================================

@app.route(
    "/staff/notices/<int:notice_id>/delete",
    methods=["POST"]
)
@staff_required
def remove_notice(notice_id):

    connection = get_db()

    notice = connection.execute(
        """
        SELECT title_en
        FROM notices
        WHERE id = ?
        """,
        (notice_id,)
    ).fetchone()

    if notice is None:
        connection.close()
        abort(404)

    connection.execute(
        """
        DELETE FROM notices
        WHERE id = ?
        """,
        (notice_id,)
    )

    connection.commit()
    connection.close()

    write_audit(
        "DELETE_NOTICE",
        notice["title_en"]
    )

    return redirect(
        url_for(
            "manage_notices"
        )
    )


# ============================================================
# AUDIT LOG
# ============================================================

@app.route("/staff/activity")
@staff_required
def activity():

    connection = get_db()

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
            📝 Audit Log
        </h1>

        {rows
        or "<p>No activity recorded.</p>"}

    </div>
    """

    return render_page(
        "Audit Log",
        content
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
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
            This website is a prototype
            public information portal.
        </p>

        <p>
            It is designed to provide
            approved public case information,
            hearing schedules, and official
            notices.
        </p>

    </div>
    """

    return render_page(
        "About",
        content
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact")
def contact():

    content = """
    <div class="card">

        <h1>
            Contact & Verification
        </h1>

        <p>
            For authoritative information,
            use the court's officially
            published contact channels.
        </p>

        <p>
            Information shown on this portal
            may change and should be verified
            when necessary.
        </p>

    </div>
    """

    return render_page(
        "Contact",
        content
    )


# ============================================================
# PRIVACY
# ============================================================

@app.route("/privacy")
def privacy():

    content = """
    <div class="card">

        <h1>
            Privacy
        </h1>

        <p>
            Only court-approved public
            information should be published
            through the public portion
            of this system.
        </p>

        <p>
            Restricted, sealed, confidential,
            or otherwise protected documents
            should not be exposed through
            public case search.
        </p>

    </div>
    """

    return render_page(
        "Privacy",
        content
    )


# ============================================================
# TERMS
# ============================================================

@app.route("/terms")
def terms():

    content = """
    <div class="card">

        <h1>
            Terms of Use
        </h1>

        <p>
            Public information shown here
            should not be treated as a
            substitute for certified court
            records or official court orders.
        </p>

        <p>
            The court should determine what
            information may be published.
        </p>

    </div>
    """

    return render_page(
        "Terms",
        content
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    return jsonify(
        {
            "status": "ok",
            "service": COURT_NAME
        }
    )


# ============================================================
# PUBLIC API
# ============================================================

@app.route(
    "/api/public/cases"
)
def public_cases_api():

    number = request.args.get(
        "case_number",
        ""
    ).strip()

    name = request.args.get(
        "name",
        ""
    ).strip()

    connection = get_db()

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
            "%" + name + "%"
        )
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(row)
            for row in rows
        ]
    )


# ============================================================
# ERROR PAGES
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

    return render_page(
        "Forbidden",
        content
    ), 403


@app.errorhandler(404)
def not_found(error):

    content = """
    <div class="card">

        <h1>
            404
        </h1>

        <p>
            The requested page was not found.
        </p>

        <a
            class="button"
            href="/"
        >
            Return Home
        </a>

    </div>
    """

    return render_page(
        "Not Found",
        content
    ), 404


@app.errorhandler(500)
def server_error(error):

    content = """
    <div class="card">

        <h1>
            500
        </h1>

        <p>
            The server encountered an error.
        </p>

        <a
            class="button"
            href="/"
        >
            Return Home
        </a>

    </div>
    """

    return render_page(
        "Server Error",
        content
    ), 500


# ============================================================
# VALIDATION HELPERS
# ============================================================

CASE_STATUSES = [
    "Pending",
    "Scheduled",
    "For Hearing",
    "Submitted",
    "Resolved",
    "Archived"
]


HEARING_STATUSES = [
    "Scheduled",
    "Completed",
    "Postponed",
    "Cancelled"
]


NOTICE_TYPES = [
    "General",
    "Suspension",
    "Postponement",
    "Holiday",
    "Court Operations"
]


def clean_text(
    value,
    maximum=5000
):

    if value is None:
        return ""

    value = str(value)

    value = value.strip()

    return value[:maximum]


def valid_case_status(
    value
):

    return value in CASE_STATUSES


def valid_hearing_status(
    value
):

    return value in HEARING_STATUSES


def valid_notice_type(
    value
):

    return value in NOTICE_TYPES


def normalize_case_number(
    value
):

    value = clean_text(
        value,
        100
    )

    return value.upper()


def normalize_name(
    value
):

    value = clean_text(
        value,
        300
    )

    return " ".join(
        value.split()
    )


def has_public_summary(
    case
):

    return bool(
        case["public_summary"]
    )


def case_is_public(
    case
):

    return (
        case is not None
        and has_public_summary(case)
    )


def document_is_public(
    document
):

    return bool(
        document
        and document["public_access"]
    )


def staff_role():
    return session.get(
        "role",
        "staff"
    )


def staff_username():
    return session.get(
        "username",
        ""
    )


def current_theme():
    return session.get(
        "theme",
        "light"
    )


def current_language_name():
    language = session.get(
        "language",
        "en"
    )

    return (
        "Filipino"
        if language == "fil"
        else "English"
    )


def application_name():
    return COURT_NAME


def logo_path():
    return (
        "/static/"
        + LOGO_FILENAME
    )


def public_route_name():
    return "Public Case Portal"


def staff_route_name():
    return "Staff Case Portal"


def database_name():
    return DATABASE


def primary_color():
    return PRIMARY_PURPLE


def secondary_color():
    return SECONDARY_PURPLE


def supported_languages():
    return list(
        TRANSLATIONS.keys()
    )


def supported_case_statuses():
    return list(
        CASE_STATUSES
    )


def supported_hearing_statuses():
    return list(
        HEARING_STATUSES
    )


def supported_notice_types():
    return list(
        NOTICE_TYPES
    )


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APPLICATION_METADATA = {
    "name": COURT_NAME,
    "short_name": "MCTC Silang-Amadeo",
    "primary_color": PRIMARY_PURPLE,
    "secondary_color": SECONDARY_PURPLE,
    "logo": LOGO_FILENAME,
    "languages": supported_languages(),
    "case_statuses": supported_case_statuses(),
    "hearing_statuses": supported_hearing_statuses(),
    "notice_types": supported_notice_types()
}


def application_metadata():
    return dict(
        APPLICATION_METADATA
    )


# ============================================================
# PRODUCTION REVIEW CHECKLIST
# ============================================================

PRODUCTION_REVIEW = {}

PRODUCTION_TOPICS = [
    "review password policy",
    "review session security",
    "review HTTPS configuration",
    "review database backups",
    "review audit logging",
    "review staff authorization",
    "review public-information approval",
    "review document permissions",
    "review privacy controls",
    "review records retention",
    "review case-number validation",
    "review hearing-date validation",
    "review notice approval",
    "review suspension notice approval",
    "review English translation",
    "review Filipino translation",
    "review accessibility",
    "review mobile layout",
    "review error handling",
    "review production secrets",
    "review dependency updates",
    "review incident response",
    "review disaster recovery",
    "review account deactivation",
    "review backup restoration"
]


for checklist_number in range(
    1,
    1701
):

    topic = PRODUCTION_TOPICS[
        (
            checklist_number - 1
        )
        % len(PRODUCTION_TOPICS)
    ]

    PRODUCTION_REVIEW[
        checklist_number
    ] = (
        "Production review "
        f"item {checklist_number}: "
        f"{topic}."
    )


def production_review():
    return dict(
        PRODUCTION_REVIEW
    )


def production_review_count():
    return len(
        PRODUCTION_REVIEW
    )


# ============================================================
# SAFE STARTUP
# ============================================================

initialize_database()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )


# End of MCTC Silang-Amadeo application.
