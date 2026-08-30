from flask import Flask, request, redirect, url_for, session, flash, jsonify, render_template_string, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import os
import secrets

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER"
)

app.config["DATABASE"] = os.environ.get(
    "DATABASE_PATH",
    "court_portal.db"
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
        "cases": "Cases",
        "logout": "Log Out",
        "case_number": "Case Number",
        "name": "Name / Party",
        "search_button": "Search",
        "status": "Status",
        "public_information": "Public Information",
        "official_notice": "Official Court Notice",
        "suspension": "Suspension / Postponement Notices",
        "staff_area": "Staff Area",
        "about": "About",
        "privacy": "Privacy",
        "terms": "Terms",
        "contact": "Contact",
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
        "case_number": "Numero ng Kaso",
        "name": "Pangalan / Partido",
        "search_button": "Maghanap",
        "status": "Katayuan",
        "public_information": "Pampublikong Impormasyon",
        "official_notice": "Opisyal na Abiso ng Hukuman",
        "suspension": "Mga Abiso ng Suspensyon / Pagpapaliban",
        "staff_area": "Lugar ng mga Kawani",
        "about": "Tungkol",
        "privacy": "Pribasiya",
        "terms": "Mga Tuntunin",
        "contact": "Makipag-ugnayan",
    },
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    connection = sqlite3.connect(
        app.config["DATABASE"]
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


# ============================================================
# PASSWORD HELPERS
# ============================================================

def create_password_hash(
    password
):

    return generate_password_hash(
        password
    )


def verify_password(
    stored_hash,
    password
):

    return check_password_hash(
        stored_hash,
        password
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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
            FOREIGN KEY(case_id)
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
                create_password_hash(
                    admin_password
                ),
                "admin",
                1,
                current_time()
            )
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
                "Sample public information only.",
                "Sample internal note only.",
                current_time(),
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
                    "Please check official court "
                    "announcements for suspension, "
                    "postponement, or cancellation "
                    "of hearings."
                ),
                (
                    "Mangyaring tingnan ang mga "
                    "opisyal na abiso ng hukuman "
                    "para sa suspensyon, pagpapaliban, "
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
# SESSION HELPERS
# ============================================================

def is_logged_in():

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
        "staff"
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
        "dark"
    ):
        theme = "light"

    return theme


# ============================================================
# AUTHORIZATION DECORATORS
# ============================================================

def staff_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs
    ):

        if not is_logged_in():

            flash(
                "Please sign in as authorized court staff.",
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


def admin_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs
    ):

        if not is_logged_in():

            return redirect(
                url_for("staff_login")
            )

        if current_role() != "admin":

            abort(403)

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# AUDIT LOGGING
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
            current_username()
            or "system",
            action,
            target,
            current_time()
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# COMMON CSS
# ============================================================

SITE_CSS = """

:root {

    --purple-dark:
        #42105F;

    --purple:
        #7B2CBF;

    --purple-light:
        #9D4EDD;

    --purple-soft:
        #EAD7F7;

    --background:
        #FAF7FD;

    --surface:
        #FFFFFF;

    --text:
        #24152E;

    --muted:
        #6E5C75;

    --border:
        #E4D9EA;

    --danger:
        #A61B45;

    --success:
        #2E7045;

    --warning:
        #765600;
}


* {

    box-sizing:
        border-box;

}


html {

    scroll-behavior:
        smooth;

}


body {

    margin:
        0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        var(--background);

    color:
        var(--text);

    line-height:
        1.6;

}


body.dark {

    --background:
        #17111C;

    --surface:
        #241B2B;

    --text:
        #F7EFFA;

    --muted:
        #BFAFC7;

    --border:
        #4D3C58;

    --purple-soft:
        #34213F;

}


a {

    color:
        var(--purple);

}


button {

    font:
        inherit;

}


.site-header {

    position:
        sticky;

    top:
        0;

    z-index:
        1000;

    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );

    color:
        #FFFFFF;

    padding:
        13px 4%;

    display:
        flex;

    align-items:
        center;

    gap:
        18px;

    flex-wrap:
        wrap;

    box-shadow:
        0 6px 25px
        rgba(
            55,
            15,
            80,
            .22
        );

}


.brand {

    color:
        white;

    text-decoration:
        none;

    display:
        flex;

    align-items:
        center;

    gap:
        11px;

    margin-right:
        auto;

}


.brand img {

    width:
        50px;

    height:
        50px;

    background:
        white;

    border-radius:
        50%;

    padding:
        3px;

    object-fit:
        contain;

}


.brand strong {

    display:
        block;

}


.brand small {

    display:
        block;

    opacity:
        .8;

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
.main-nav button {

    color:
        white;

    text-decoration:
        none;

    border:
        none;

    background:
        none;

    padding:
        0;

    cursor:
        pointer;

    font-weight:
        700;

    font-size:
        14px;

}


.language-tools {

    display:
        flex;

    gap:
        6px;

}


.language-tools a {

    color:
        white;

    text-decoration:
        none;

    padding:
        5px 8px;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .4
        );

    border-radius:
        8px;

    font-size:
        12px;

}


main {

    width:
        92%;

    max-width:
        1150px;

    margin:
        auto;

    min-height:
        76vh;

    padding:
        35px 0 70px;

}


footer {

    background:
        var(--purple-dark);

    color:
        white;

    text-align:
        center;

    padding:
        32px 20px;

}


.hero {

    background:
        linear-gradient(
            135deg,
            var(--purple),
            var(--purple-light)
        );

    color:
        white;

    border-radius:
        24px;

    padding:
        50px;

    display:
        grid;

    grid-template-columns:
        1.5fr .5fr;

    gap:
        30px;

    align-items:
        center;

}


.hero h1 {

    font-size:
        clamp(
            34px,
            5vw,
            64px
        );

    line-height:
        1.03;

    margin:
        15px 0;

}


.hero p {

    font-size:
        18px;

    max-width:
        760px;

}


.seal-box {

    background:
        rgba(
            255,
            255,
            255,
            .15
        );

    border-radius:
        20px;

    padding:
        20px;

    text-align:
        center;

}


.seal-box img {

    width:
        185px;

    height:
        185px;

    object-fit:
        contain;

}


.card {

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    padding:
        25px;

    margin:
        20px 0;

    box-shadow:
        0 8px 28px
        rgba(
            70,
            20,
            100,
            .08
        );

}


.card h1,
.card h2 {

    color:
        var(--purple);

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
                160px,
                1fr
            )
        );

}


.button {

    display:
        inline-block;

    background:
        var(--purple);

    color:
        white;

    text-decoration:
        none;

    border:
        none;

    border-radius:
        10px;

    padding:
        11px 18px;

    font-weight:
        800;

    cursor:
        pointer;

}


.button.secondary {

    background:
        var(--purple-soft);

    color:
        var(--purple-dark);

}


.form {

    max-width:
        760px;

    margin:
        20px auto;

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    padding:
        28px;

    box-shadow:
        0 8px 28px
        rgba(
            70,
            20,
            100,
            .08
        );

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

    background:
        var(--surface);

    color:
        var(--text);

    font:
        inherit;

}


textarea {

    min-height:
        120px;

    resize:
        vertical;

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
        1fr 1.6fr auto auto;

    gap:
        14px;

    align-items:
        center;

    padding:
        14px 0;

    border-bottom:
        1px solid
        var(--border);

}


.status {

    display:
        inline-block;

    width:
        max-content;

    background:
        var(--purple-soft);

    color:
        var(--purple-dark);

    border-radius:
        99px;

    padding:
        4px 10px;

    font-size:
        12px;

    font-weight:
        900;

}


.notice {

    background:
        var(--purple-soft);

    border-left:
        5px solid
        var(--purple);

    border-radius:
        10px;

    padding:
        15px;

    margin:
        12px 0;

}


.row {

    display:
        flex;

    gap:
        14px;

    align-items:
        center;

    flex-wrap:
        wrap;

    padding:
        13px 0;

    border-bottom:
        1px solid
        var(--border);

}


.stat strong {

    display:
        block;

    font-size:
        35px;

    color:
        var(--purple);

}


.muted {

    color:
        var(--muted);

}


.friendly {

    background:
        linear-gradient(
            135deg,
            #57127A,
            #7B2CBF,
            #9D4EDD
        );

    color:
        white;

    border-radius:
        21px;

    padding:
        32px;

    margin-bottom:
        24px;

}


.friendly h1 {

    font-size:
        clamp(
            30px,
            5vw,
            48px
        );

    margin:
        8px 0;

}


.quick {

    text-decoration:
        none;

    color:
        var(--text);

}


.danger {

    background:
        var(--danger);

}


@media (
    max-width: 780px
) {

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

}


@media (
    max-width: 500px
) {

    main {

        width:
            94%;

    }


    .hero h1 {

        font-size:
            36px;

    }

}
"""


# ============================================================
# PAGE RENDERING
# ============================================================

def render_page(
    title,
    content
):

    language = current_language()

    theme = current_theme()

    labels = TRANSLATIONS[
        language
    ]

    if is_logged_in():

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

        <form
            method="post"
            action="/logout"
            style="
                display:inline;
                margin:0;
            "
        >
            <button
                type="submit"
                class="navbutton"
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

    navigation += f"""
    <a href="/about">
        {labels["about"]}
    </a>

    <a href="/contact">
        {labels["contact"]}
    </a>
    """

    html = f"""
    <!doctype html>

    <html lang="{language}">

    <head>

        <meta charset="utf-8">

        <meta
            name="viewport"
            content="width=device-width,
                     initial-scale=1"
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

        <header class="site-header">

            <a
                href="/"
                class="brand"
            >

                <img
                    src="/static/{LOGO_FILENAME}"
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


            <nav class="main-nav">

                {navigation}

            </nav>


            <div class="language-tools">

                <a href="/language/en">
                    EN
                </a>

                <a href="/language/fil">
                    FIL
                </a>

                <a href="/theme/light">
                    ☀
                </a>

                <a href="/theme/dark">
                    ☾
                </a>

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
# HOME
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

        notices_html += f"""
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

    if not notices_html:

        notices_html = (
            "<p>"
            "No official notices have been published."
            "</p>"
        )

    content = f"""
    <section class="hero">

        <div>

            <span>
                ⚖️ MCTC SILANG–AMADEO
            </span>

            <h1>
                {COURT_NAME}
            </h1>

            <p>
                Public case information,
                hearing schedules,
                and official court notices.
            </p>

            <p>

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

            </p>

        </div>


        <div class="seal-box">

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
                Search case information
                approved for public release.
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
                schedules.
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
                operations notices.
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
            Latest Official Notices
        </h2>

        {notices_html}

    </section>


    <section class="card">

        <h2>
            🔐 Privacy Reminder
        </h2>

        <p>
            Only information that the court
            has authorized for public release
            should be published through the
            public portal.
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
        or url_for("home")
    )


# ============================================================
# THEME
# ============================================================

@app.route(
    "/theme/<theme>"
)
def change_theme(
    theme
):

    if theme not in (
        "light",
        "dark"
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
    "/search",
    methods=["GET"]
)
def search():

    case_number = (
        request.args.get(
            "case_number",
            ""
        ).strip()
    )

    name = (
        request.args.get(
            "name",
            ""
        ).strip()
    )

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

            result_html = (
                "<p>"
                "No matching public case "
                "information was found."
                "</p>"
            )

        else:

            result_html = (
                "<p>"
                "Enter a case number "
                "or party name."
                "</p>"
            )

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
            Search Results
        </h2>

        {result_html}

    </div>
    """

    return render_page(
        "Case Search",
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
        ORDER BY
            display_name
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

        hearing_html = (
            "<p>"
            "No hearing schedule "
            "has been published."
            "</p>"
        )

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

    if not document_html:

        document_html = (
            "<p>"
            "No public documents "
            "have been published."
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

        <div class="grid grid-two">

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
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def staff_login():

    if is_logged_in():

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                ""
            ).strip()
        )

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
            and verify_password(
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

            session["language"] = "en"

            session["theme"] = "light"

            write_audit(
                "LOGIN",
                username
            )

            response = redirect(
                url_for("dashboard")
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
            "danger"
        )

    content = """
    <div class="form">

        <div style="
            text-align:center;
        ">

            <div style="
                font-size:52px;
            ">
                ⚖️
            </div>

            <h1>
                Welcome, Court Staff 💜
            </h1>

            <p class="muted">
                Sign in to manage authorized
                court information.
            </p>

        </div>


        <form
            method="post"
        >

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


            <button
                class="button"
                type="submit"
            >
                🔐 Sign In
            </button>

        </form>


        <div class="notice">

            <strong>
                Development login
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

    return render_page(
        "Staff Login",
        content
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=["GET", "POST"]
)
def logout():

    username = (
        session.get(
            "username",
            ""
        )
    )

    if session.get("staff_id"):

        try:

            write_audit(
                "LOGOUT",
                username
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

    connection = get_db()

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

    upcoming_html = ""

    for hearing in upcoming:

        upcoming_html += f"""
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
    <div class="friendly">

        <span>
            ⚖️ STAFF PORTAL
        </span>

        <h1>
            Welcome back,
            {current_username()}
            💜
        </h1>

        <p>
            Your court information workspace
            is ready. Use the tools below
            to manage authorized information.
        </p>

    </div>


    <div class="grid grid-four">

        <div class="card stat">

            <span>
                Cases
            </span>

            <strong>
                {total_cases}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Hearings
            </span>

            <strong>
                {total_hearings}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Published Notices
            </span>

            <strong>
                {total_notices}
            </strong>

        </div>


        <div class="card stat">

            <span>
                Documents
            </span>

            <strong>
                {total_documents}
            </strong>

        </div>

    </div>


    <div class="grid grid-two">

        <a
            href="/staff/cases"
            class="card quick"
        >

            <h2>
                📋 Manage Cases
            </h2>

            <p>
                Review and update
                case records.
            </p>

        </a>


        <a
            href="/staff/cases/add"
            class="card quick"
        >

            <h2>
                ➕ Add Case
            </h2>

            <p>
                Create a new case record.
            </p>

        </a>


        <a
            href="/staff/notices"
            class="card quick"
        >

            <h2>
                📢 Court Notices
            </h2>

            <p>
                Publish official
                announcements.
            </p>

        </a>


        <a
            href="/staff/activity"
            class="card quick"
        >

            <h2>
                📝 Audit Activity
            </h2>

            <p>
                Review staff activity.
            </p>

        </a>

    </div>


    <div class="grid grid-two">

        <div class="card">

            <h2>
                📋 Recently Updated Cases
            </h2>

            {recent_html
            or "<p>No cases yet.</p>"}

        </div>


        <div class="card">

            <h2>
                📅 Upcoming Hearings
            </h2>

            {upcoming_html
            or "<p>No hearings scheduled.</p>"}

        </div>

    </div>


    <div class="notice">

        <strong>
            💡 Staff Reminder
        </strong>

        <p>
            Only enter and publish information
            that has been authorized for the
            intended audience. Restricted or
            confidential information should
            remain protected.
        </p>

    </div>
    """

    response = render_page(
        "Staff Dashboard",
        content
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

    return response


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route(
    "/staff/cases"
)
@staff_required
def staff_cases():

    connection = get_db()

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
            href="/staff/cases/add"
            class="button"
        >
            + Add Case
        </a>

    </div>


    <div class="card">

        {rows
        or "<p>No cases found.</p>"}

    </div>
    """

    return render_page(
        "Manage Cases",
        content
    )


# ============================================================
# SPLIT HELPER
# ============================================================

def split_helper():
    return None


# ============================================================
# ADD CASE FORM
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=["GET", "POST"]
)
@staff_required
def create_case():

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

        if (
            not case_number
            or not title
        ):

            flash(
                "Case number and title are required.",
                "danger"
            )

            return render_case_form(
                "Add Case"
            )

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
                url_for(
                    "staff_cases"
                )
            )

        except sqlite3.IntegrityError:

            connection.rollback()

            connection.close()

            flash(
                "That case number already exists.",
                "danger"
            )

    return render_case_form(
        "Add Case"
    )


def render_case_form(
    title
):

    content = f"""
    <div class="form">

        <h1>
            {title}
        </h1>

        <p class="muted">
            Enter only information
            that is appropriate for
            the selected audience.
        </p>

        <form method="post">

            <label>

                Case Number

                <input
                    name="case_number"
                    required
                    placeholder="MCTC-2026-001"
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

               
