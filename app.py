"""
MCTC SILANG-AMADEO, CAVITE
PUBLIC CASE INFORMATION PORTAL + STAFF MANAGEMENT

Render Build Command:
    pip install -r requirements.txt

Render Start Command:
    gunicorn app:app

Repository structure:

    app.py
    requirements.txt
    static/
        1280px-Seal_of_the_Supreme_Court_(Philippines).png

This version:
- Opens in public/logged-out mode.
- Has working / homepage.
- Has public case search.
- Has public case details.
- Has hearing schedules.
- Has official notices.
- Has English and Filipino.
- Has light and dark mode.
- Has purple styling.
- Has staff login.
- Has friendly staff dashboard.
- Does NOT display the username/password anywhere after login.
- Has working logout.
- Has working case deletion.
- Has hearing deletion.
- Has document deletion.
- Uses SQLite.
- Uses hashed passwords.
- Does not require a templates/ folder.
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
    make_response,
    get_flashed_messages,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from functools import wraps
from datetime import datetime
import sqlite3
import os


# ============================================================
# APPLICATION
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

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(
    os.environ.get("RENDER")
)


# ============================================================
# COURT INFORMATION
# ============================================================

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

COURT_SHORT_NAME = "MCTC Silang-Amadeo"

LOGO_FILENAME = (
    "1280px-Seal_of_the_Supreme_Court_(Philippines).png"
)

PRIMARY_PURPLE = "#7B2CBF"

SECONDARY_PURPLE = "#9D4EDD"

DARK_PURPLE = "#42105F"


# ============================================================
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {

    "en": {

        "home":
            "Home",

        "search":
            "Search Cases",

        "hearings":
            "Hearings",

        "notices":
            "Notices",

        "login":
            "Staff Login",

        "dashboard":
            "Dashboard",

        "cases":
            "Cases",

        "logout":
            "Log Out",

        "about":
            "About",

        "contact":
            "Contact",

        "privacy":
            "Privacy",

        "terms":
            "Terms",

    },

    "fil": {

        "home":
            "Tahanan",

        "search":
            "Maghanap ng Kaso",

        "hearings":
            "Mga Pagdinig",

        "notices":
            "Mga Abiso",

        "login":
            "Pag-login ng Kawani",

        "dashboard":
            "Dashboard",

        "cases":
            "Mga Kaso",

        "logout":
            "Mag-logout",

        "about":
            "Tungkol",

        "contact":
            "Makipag-ugnayan",

        "privacy":
            "Pribasiya",

        "terms":
            "Mga Tuntunin",

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
# DATABASE
# ============================================================

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


# ============================================================
# CLEAN INPUT
# ============================================================

def clean(
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

    return clean(
        value,
        100,
    ).upper()


def clean_name(
    value,
):

    return " ".join(
        clean(
            value,
            300,
        ).split()
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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

    # --------------------------------------------------------
    # Default staff account
    # --------------------------------------------------------

    staff = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE username = ?
        """,
        ("admin",),
    ).fetchone()

    if staff is None:

        password = os.environ.get(
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
                    password
                ),
                "admin",
                1,
                now(),
            ),
        )

    # --------------------------------------------------------
    # Demo case
    # --------------------------------------------------------

    demo_case = connection.execute(
        """
        SELECT id
        FROM cases
        LIMIT 1
        """
    ).fetchone()

    if demo_case is None:

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
                "DEMO-001",
                "Demonstration Case",
                "Demo Party A vs. Demo Party B",
                "Civil",
                "Scheduled",
                "2099-01-01",
                "09:00",
                "Demo Courtroom",
                "Sample public information.",
                "Sample development record.",
                now(),
                now(),
            ),
        )

        demo_id = cursor.lastrowid

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
                demo_id,
                "2099-01-01",
                "09:00",
                "Demo Courtroom",
                "Demonstration",
                "Scheduled",
            ),
        )

    # --------------------------------------------------------
    # Default notice
    # --------------------------------------------------------

    notice = connection.execute(
        """
        SELECT id
        FROM notices
        LIMIT 1
        """
    ).fetchone()

    if notice is None:

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
                "General",
                1,
                now(),
            ),
        )

    connection.commit()

    connection.close()


# ============================================================
# SESSION
# ============================================================

def logged_in():

    return bool(
        session.get("staff_id")
    )


def current_username():

    return session.get(
        "username",
        "",
    )


def current_role():

    return session.get(
        "role",
        "",
    )


def current_language():

    language = session.get(
        "language",
        "en",
    )

    if language not in TRANSLATIONS:
        language = "en"

    return language


def current_theme():

    theme = session.get(
        "theme",
        "light",
    )

    if theme not in (
        "light",
        "dark",
    ):

        theme = "light"

    return theme


# ============================================================
# AUTHORIZATION
# ============================================================

def staff_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs,
    ):

        if not logged_in():

            flash(
                "Please sign in as authorized court staff.",
                "warning",
            )

            return redirect(
                url_for(
                    "staff_login"
                )
            )

        return function(
            *args,
            **kwargs,
        )

    return wrapper


def admin_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs,
    ):

        if not logged_in():

            return redirect(
                url_for(
                    "staff_login"
                )
            )

        if current_role() != "admin":

            abort(403)

        return function(
            *args,
            **kwargs,
        )

    return wrapper


# ============================================================
# AUDIT
# ============================================================

def audit(
    action,
    target="",
):

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
            current_username()
            or "system",
            action,
            target,
            now(),
        ),
    )

    connection.commit()

    connection.close()


# ============================================================
# CSS
# ============================================================

CSS = r"""
:root {

    --purple-dark: #42105F;
    --purple: #7B2CBF;
    --purple-light: #9D4EDD;
    --purple-soft: #EFE2F7;

    --background: #FAF8FC;
    --surface: #FFFFFF;
    --surface-alt: #F4EEF8;

    --text: #211427;
    --heading: #42105F;
    --muted: #5C5062;

    --border: #D8CBDD;

    --danger: #971A43;
    --danger-bg: #FFE4EB;

    --success: #24623B;
    --success-bg: #DFF4E5;

    --warning: #735000;
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

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height: 1.65;

    color:
        var(--text);

    background:
        var(--background);
}

body.dark {

    --background:
        #111014;

    --surface:
        #211B26;

    --surface-alt:
        #2A2330;

    --text:
        #FFFFFF;

    --heading:
        #F1D9FF;

    --muted:
        #DED1E5;

    --border:
        #665472;

    --purple-soft:
        #392643;

    --danger:
        #FFB7CA;

    --danger-bg:
        #451A28;

    --success:
        #B7F0C8;

    --success-bg:
        #183824;

    --warning:
        #FFE3A5;

    --warning-bg:
        #493817;
}

a {
    color:
        var(--purple);
}

.site-header {

    position:
        sticky;

    top:
        0;

    z-index:
        1000;

    display:
        flex;

    align-items:
        center;

    gap:
        18px;

    flex-wrap:
        wrap;

    padding:
        13px 4%;

    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );

    color:
        white;

    box-shadow:
        0 6px 25px
        rgba(
            60,
            15,
            80,
            .25
        );
}

.brand {

    display:
        flex;

    align-items:
        center;

    gap:
        11px;

    color:
        white;

    text-decoration:
        none;

    margin-right:
        auto;
}

.brand-logo {

    width:
        50px;

    height:
        50px;

    object-fit:
        contain;

    background:
        white;

    border-radius:
        50%;

    padding:
        3px;
}

.brand strong,
.brand small {

    display:
        block;
}

.brand small {

    opacity:
        .82;
}

.main-nav {

    display:
        flex;

    align-items:
        center;

    gap:
        14px;

    flex-wrap:
        wrap;
}

.main-nav a,
.nav-button {

    color:
        white;

    font-weight:
        800;

    font-size:
        13px;

    text-decoration:
        none;
}

.nav-button {

    padding:
        0;

    border:
        0;

    background:
        transparent;

    cursor:
        pointer;
}

.nav-form {

    display:
        inline;

    margin:
        0;
}

.tools {

    display:
        flex;

    gap:
        6px;
}

.tool {

    color:
        white;

    text-decoration:
        none;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .45
        );

    border-radius:
        8px;

    padding:
        5px 8px;

    font-size:
        12px;
}

main {

    width:
        92%;

    max-width:
        1180px;

    min-height:
        77vh;

    margin:
        auto;

    padding:
        35px 0 70px;
}

footer {

    padding:
        30px 20px;

    color:
        white;

    background:
        var(--purple-dark);

    text-align:
        center;
}

.hero {

    display:
        grid;

    grid-template-columns:
        1.45fr
        .55fr;

    gap:
        35px;

    align-items:
        center;

    padding:
        52px;

    color:
        white;

    border-radius:
        25px;

    background:
        linear-gradient(
            135deg,
            var(--purple),
            var(--purple-light)
        );
}

.hero h1 {

    margin:
        14px 0;

    font-size:
        clamp(
            34px,
            5vw,
            62px
        );

    line-height:
        1.04;
}

.hero p {

    max-width:
        760px;

    font-size:
        18px;
}

.hero-buttons {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        10px;

    margin-top:
        24px;
}

.seal-holder {

    display:
        grid;

    place-items:
        center;

    padding:
        20px;

    border-radius:
        22px;

    background:
        rgba(
            255,
            255,
            255,
            .15
        );
}

.seal-holder img {

    width:
        190px;

    height:
        190px;

    object-fit:
        contain;
}

.card,
.form,
.stat-card {

    margin:
        20px 0;

    padding:
        25px;

    color:
        var(--text);

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    background:
        var(--surface);

    box-shadow:
        0 9px 28px
        rgba(
            70,
            20,
            100,
            .08
        );
}

.card h1,
.card h2,
.card h3,
.form h1,
.form h2 {

    color:
        var(--heading);
}

.grid {

    display:
        grid;

    gap:
        18px;

    margin:
        22px 0;
}

.grid-two {

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                280px,
                1fr
            )
        );
}

.grid-four {

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                155px,
                1fr
            )
        );
}

.button,
button {

    border:
        0;

    border-radius:
        10px;

    padding:
        11px 18px;

    color:
        white;

    background:
        var(--purple);

    font-weight:
        900;

    text-decoration:
        none;

    cursor:
        pointer;
}

.button.secondary {

    color:
        var(--heading);

    background:
        var(--purple-soft);
}

button.danger,
.button.danger {

    color:
        white;

    background:
        var(--danger);
}

.form {

    max-width:
        780px;

    margin:
        25px auto;
}

.form form {

    display:
        grid;

    gap:
        15px;
}

.form label {

    display:
        grid;

    gap:
        6px;

    font-weight:
        800;
}

input,
select,
textarea {

    width:
        100%;

    padding:
        12px;

    border:
        1px solid
        var(--border);

    border-radius:
        9px;

    color:
        var(--text);

    background:
        var(--surface);

    font:
        inherit;
}

textarea {

    min-height:
        125px;

    resize:
        vertical;
}

input:focus,
select:focus,
textarea:focus {

    outline:
        3px solid
        rgba(
            123,
            44,
            191,
            .25
        );

    border-color:
        var(--purple);
}

.search-form {

    display:
        grid;

    grid-template-columns:
        1fr 1fr auto;

    gap:
        12px;

    align-items:
        end;
}

.result {

    display:
        grid;

    grid-template-columns:
        1fr 1.4fr 1fr auto;

    gap:
        15px;

    align-items:
        center;

    padding:
        15px 0;

    border-bottom:
        1px solid
        var(--border);
}

.row {

    display:
        flex;

    align-items:
        center;

    gap:
        15px;

    flex-wrap:
        wrap;

    padding:
        13px 0;

    border-bottom:
        1px solid
        var(--border);
}

.status {

    display:
        inline-block;

    width:
        max-content;

    padding:
        4px 10px;

    border-radius:
        999px;

    color:
        var(--heading);

    background:
        var(--purple-soft);

    font-size:
        12px;

    font-weight:
        900;
}

.notice {

    padding:
        16px;

    margin:
        12px 0;

    border-left:
        5px solid
        var(--purple);

    border-radius:
        10px;

    color:
        var(--text);

    background:
        var(--purple-soft);
}

.alert {

    padding:
        12px 15px;

    margin-bottom:
        15px;

    border-radius:
        9px;
}

.alert.warning {

    color:
        var(--warning);

    background:
        var(--warning-bg);
}

.alert.danger {

    color:
        var(--danger);

    background:
        var(--danger-bg);
}

.alert.success {

    color:
        var(--success);

    background:
        var(--success-bg);
}

.friendly-dashboard {

    padding:
        35px;

    margin-bottom:
        25px;

    border-radius:
        22px;

    color:
        white;

    background:
        linear-gradient(
            135deg,
            #511470,
            #7B2CBF,
            #9D4EDD
        );
}

.friendly-dashboard h1 {

    color:
        white;

    margin:
        8px 0;

    font-size:
        clamp(
            30px,
            5vw,
            50px
        );
}

.friendly-dashboard p,
.friendly-dashboard span {

    color:
        white;
}

.staff-actions {

    display:
        grid;

    grid-template-columns:
        repeat(
            4,
            1fr
        );

    gap:
        14px;

    margin:
        25px 0;
}

.staff-action {

    display:
        block;

    padding:
        20px;

    color:
        var(--text);

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        14px;

    text-decoration:
        none;
}

.staff-action strong {

    display:
        block;

    margin-top:
        7px;

    color:
        var(--purple);
}

.staff-action span {

    color:
        var(--muted);

    font-size:
        13px;
}

.empty {

    text-align:
        center;

    padding:
        40px 20px;
}

.split {

    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;

    gap:
        20px;

    flex-wrap:
        wrap;
}

@media(max-width:850px) {

    .hero {

        grid-template-columns:
            1fr;

        padding:
            30px;
    }

    .search-form {

        grid-template-columns:
            1fr;
    }

    .result {

        grid-template-columns:
            1fr;
    }

    .brand {

        width:
            100%;
    }

    .main-nav {

        width:
            100%;
    }

    .staff-actions {

        grid-template-columns:
            1fr 1fr;
    }
}

@media(max-width:520px) {

    main {

        width:
            94%;
    }

    .hero h1 {

        font-size:
            36px;
    }

    .friendly-dashboard {

        padding:
            25px;
    }

    .staff-actions {

        grid-template-columns:
            1fr;
    }
}
"""


# ============================================================
# PAGE GENERATOR
# ============================================================

def render_page(
    title,
    content,
):

    language = current_language()

    theme = current_theme()

    labels = TRANSLATIONS[
        language
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

        <a href="/staff/profile">
            Profile
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

        <a href="/about">
            {labels["about"]}
        </a>

        <a href="/login">
            {labels["login"]}
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

        <title>
            {title}
        </title>

        <style>
            {CSS}
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


# ============================================================
# FLASH MESSAGES
# ============================================================

def render_messages():

    output = ""

    for category, message in (
        get_flashed_messages(
            with_categories=True
        )
    ):

        output += f"""
        <div class="alert {category}">
            {message}
        </div>
        """

    return output


# ============================================================
# HOME
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

    notices_html = ""

    for notice in notices:

        title = (
            notice["title_fil"]
            if current_language() == "fil"
            else notice["title_en"]
        )

        body = (
            notice["body_fil"]
            if current_language() == "fil"
            else notice["body_en"]
        )

        notices_html += f"""
        <div class="notice">

            <span class="status">
                {notice["notice_type"]}
            </span>

            <h3>
                {title}
            </h3>

            <p>
                {body}
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
                Search approved public case information,
                view hearing schedules, and check official
                court notices.
            </p>

            <div class="hero-buttons">

                <a
                    href="/search"
                    class="button"
                >
                    🔎 Search a Case
                </a>

                <a
                    href="/hearings"
                    class="button secondary"
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
                Use the case number or the name
                of a party to find approved
                public information.
            </p>

            <a
                href="/search"
                class="button secondary"
            >
                Start Searching
            </a>

        </div>


        <div class="card">

            <h2>
                📅 Hearing Schedule
            </h2>

            <p>
                Review published hearing dates,
                times, courtrooms, and status.
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
                📢 Official Notices
            </h2>

            <p>
                Check official suspension,
                postponement, cancellation,
                holiday, and court-operation notices.
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
                🌐 Language & Theme
            </h2>

            <p>
                Use the EN/FIL buttons and
                light/dark buttons in the header.
            </p>

        </div>

    </section>


    <section class="card">

        <h2>
            Latest Notices
        </h2>

        {
            notices_html
            or
            "<p>No current notices.</p>"
        }

    </section>


    <section class="card">

        <h2>
            🔐 Privacy Reminder
        </h2>

        <p>
            Only information authorized for
            public release should be displayed
            here. Restricted, sealed, confidential,
            or protected information should not
            be published through the public portal.
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

@app.route(
    "/language/<language>"
)
def set_language(language):

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
def set_theme(theme):

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

    result_html = ""

    for case in results:

        result_html += f"""
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

    if not result_html:

        if case_number or name:

            result_html = """
            <div class="empty">

                <div style="font-size:45px;">
                    🔎
                </div>

                <h2>
                    No matching case found
                </h2>

                <p>
                    Check the case number or name
                    and try again.
                </p>

            </div>
            """

        else:

            result_html = """
            <div class="empty">

                <div style="font-size:45px;">
                    📋
                </div>

                <h2>
                    Ready to search
                </h2>

                <p>
                    Enter a case number or party name.
                </p>

            </div>
            """

    content = f"""
    <div class="card">

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
                You may fill in both fields to
                narrow the results.
            </li>

            <li>
                Click
                <strong>
                    Search
                </strong>.
            </li>

            <li>
                Choose
                <strong>
                    View
                </strong>
                beside the case you need.
            </li>

        </ol>


        <div class="notice">

            <strong>
                Example
            </strong>

            <p>
                Case Number:
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

        {result_html}

    </div>
    """

    return render_page(
        "Search Cases",
        content
    )


# ============================================================
# PUBLIC CASE
# ============================================================

@app.route(
    "/case/<int:case_id>"
)
def public_case(
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
            "<p>No public hearing information.</p>"
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

    return render_page(
        case["case_number"],
        content
    )


# ============================================================
# PUBLIC HEARINGS
# ============================================================

@app.route(
    "/hearings"
)
def hearing_schedule():

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

        {
            html
            or
            "<p>No hearings are currently published.</p>"
        }

    </div>
    """

    return render_page(
        "Hearing Schedule",
        content
    )


# ============================================================
# PUBLIC NOTICES
# ============================================================

@app.route(
    "/notices"
)
def public_notices():

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

    return render_page(
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
# STAFF LOGIN
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
            WHERE username = ?
            AND active = 1
            """,
            (username,),
        ).fetchone()

        connection.close()

        if (
            staff is not None
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
                Sign in to the authorized
                staff information portal.
            </p>

        </div>


        <form
            method="post"
            autocomplete="off"
        >

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
                Your login credentials are not
                displayed on the website.
            </p>

        </div>

    </div>
    """

    return render_page(
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

    if session.get("staff_id"):

        try:

            audit(
                "LOGOUT",
                username,
            )

        except Exception:

            pass

    session.clear()

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
# DASHBOARD
# ============================================================

@app.route(
    "/dashboard"
)
@staff_required
def dashboard():

    connection = db()

    total_cases = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    total_hearings = connection.execute(
        "SELECT COUNT(*) FROM hearings"
    ).fetchone()[0]

    total_notices = connection.execute(
        """
        SELECT COUNT(*)
        FROM notices
        WHERE published = 1
        """
    ).fetchone()[0]

    total_documents = connection.execute(
        "SELECT COUNT(*) FROM documents"
    ).fetchone()[0]

    recent_cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        LIMIT 6
        """
    ).fetchall()

    connection.close()

    recent_html = ""

    for case in recent_cases:

        recent_html += f"""
        <div class="result">

            <div>

                <strong>
                    {case["case_number"]}
                </strong>

                <br>

                {case["title"]}

            </div>

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
            Your court workspace is ready.
            Choose an action below to begin.
        </p>

    </section>


    <div class="grid grid-four">

        <div class="stat-card">

            <span>
                Cases
            </span>

            <strong>
                {total_cases}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Hearings
            </span>

            <strong>
                {total_hearings}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Notices
            </span>

            <strong>
                {total_notices}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Documents
            </span>

            <strong>
                {total_documents}
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
                Find, edit, or delete cases.
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
                Create a new case record.
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
                Court Notices
            </strong>

            <span>
                Publish approved notices.
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
                Audit Activity
            </strong>

            <span>
                Review recent staff actions.
            </span>

        </a>

    </div>


    <div class="card">

        <h2>
            📋 Recently Updated Cases
        </h2>

        {
            recent_html
            or
            "<p>No cases yet.</p>"
        }

    </div>


    <div class="notice">

        <strong>
            💡 Staff Reminder
        </strong>

        <p>
            Only enter information authorized
            for the intended audience.
        </p>

    </div>
    """

    return render_page(
        "Staff Dashboard",
        content
    )


# ============================================================
# STAFF CASES
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

            <div>

                <strong>
                    {case["case_number"]}
                </strong>

                <br>

                {case["title"]}

            </div>


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

        <p class="muted">
            Choose a case to view or edit it.
        </p>

        {
            rows
            or
            "<p>No cases have been entered yet.</p>"
        }

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

                flash(
                    "Case created successfully.",
                    "success",
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
            Enter information carefully and
            publish only approved information.
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
                onsubmit="
                    return confirm(
                        'Delete this hearing?'
                    );
                "
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
                onsubmit="
                    return confirm(
                        'Remove this document record?'
                    );
                "
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

        {
            hearing_html
            or
            "<p>No hearings yet.</p>"
        }

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
            "<p>No document records.</p>"
        }

    </div>


    <div class="card">

        <h2>
            ⚠️ Case Actions
        </h2>

        <p class="muted">
            Deleting a case permanently removes
            its case record, hearings, and document
            records from this database.
        </p>

        <form
            method="post"
            action="/staff/cases/{case["id"]}/delete"
            onsubmit="
                return confirm(
                    'Are you sure you want to permanently delete case '
                    + '{case["case_number"]}'
                    + '? This cannot be undone.'
                );
            "
        >

            <button
                class="danger"
                type="submit"
            >
                🗑️ Delete Case
            </button>

        </form>

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

        flash(
            "Case updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    status_options = ""

    for item in CASE_STATUSES:

        selected = (
            "selected"
            if item == case["status"]
            else ""
        )

        status_options += (
            f'<option {selected}>{item}</option>'
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

                    {status_options}

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

    return render_page(
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
        SELECT
            id,
            case_number,
            title
        FROM cases
        WHERE id = ?
        """,
        (case_id,),
    ).fetchone()

    if case is None:

        connection.close()

        flash(
            "The case could not be found.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_cases"
            )
        )

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

    flash(
        "Case "
        + case["case_number"]
        + " was deleted successfully.",
        "success",
    )

    return redirect(
        url_for(
            "staff_cases"
        )
    )


# ============================================================
# ADD HEARING
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

    if status not in HEARING_STATUSES:

        status = "Scheduled"

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

    flash(
        "Hearing added successfully.",
        "success",
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

    flash(
        "Hearing deleted.",
        "success",
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=row["case_id"],
        )
    )


# ============================================================
# ADD DOCUMENT
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

    flash(
        "Document added.",
        "success",
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

    connection = db()

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

    flash(
        "Document removed.",
        "success",
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

            <form
                method="post"
                action="/staff/notices/{notice["id"]}/delete"
                onsubmit="
                    return confirm(
                        'Delete this notice?'
                    );
                "
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

    {
        rows
        or
        "<p>No notices found.</p>"
    }
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
# STAFF PROFILE
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
                Created:
            </strong>

            {member["created_at"]}
        </p>

        <div class="notice">

            Your username and password
            are not displayed here.

        </div>

    </div>
    """

    return render_page(
        "Staff Profile",
        content
    )


# ============================================================
# STAFF ACTIVITY
# ============================================================

@app.route(
    "/staff/activity"
)
@staff_required
def activity():

    connection = db()

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

            <strong>
                {log["created_at"]}
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

        {rows
        or
        "<p>No activity has been recorded.</p>"}

    </div>
    """

    return render_page(
        "Audit Activity",
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
            This portal is a prototype for
            public case information, hearing
            schedules, and official notices.
        </p>

        <p>
            Public information and restricted
            staff information are intentionally
            separated.
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
            Use the court's officially published
            contact channels for authoritative
            information.
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
            Only information approved for
            public release should appear in
            the public portal.
        </p>

        <p>
            Restricted, sealed, confidential,
            or protected records should not
            be exposed through public search.
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
            Online information is not a
            substitute for certified court
            records, official orders, or
            other authoritative documents.
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
# PUBLIC API
# ============================================================

@app.route(
    "/api/public/cases"
)
def public_cases_api():

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

    connection = db()

    cases = connection.execute(
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
            case_number,
            "%" + case_number + "%",
            name,
            "%" + name + "%",
            "%" + name + "%",
        ),
    ).fetchall()

    connection.close()

    return jsonify(
        [
            dict(case)
            for case in cases
        ]
    )


# ============================================================
# ERROR: FORBIDDEN
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


# ============================================================
# ERROR: NOT FOUND
# ============================================================

@app.errorhandler(404)
def not_found(error):

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
            Start from the main court portal
            and select an available page.
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


# ============================================================
# ERROR: SERVER ERROR
# ============================================================

@app.errorhandler(500)
def server_error(error):

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

    return render_page(
        "Server Error",
        content
    ), 500


# ============================================================
# DATABASE STARTUP
# ============================================================

initialize_database()


# ============================================================
# LOCAL / RENDER ENTRY POINT
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
