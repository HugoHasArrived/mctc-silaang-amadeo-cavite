import os
import sqlite3
import secrets
import html
from pathlib import Path
from datetime import datetime
from functools import wraps

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


# ============================================================
# APPLICATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "mctc_court.db"

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = STATIC_DIR / "uploads"

STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app = Flask(
    __name__,
    static_folder="static",
)


# ============================================================
# SESSION SECURITY
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["MAX_CONTENT_LENGTH"] = (
    20 * 1024 * 1024
)

if os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True


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

COURT_EMAIL = (
    "mctc2sad000@judiciary.gov.ph"
)

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/"
    "?api=1&query="
    "PNP+Bldg,+Plaza+Libertad,+"
    "Poblacion+2,+Silang,+Cavite"
)

LOGO_FILENAME = "image0.png"


# ============================================================
# UPLOAD SETTINGS
# ============================================================

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


# ============================================================
# TRANSLATIONS
# ============================================================

TEXT = {
    "en": {
        "home": "Home",
        "about": "About Us",
        "news": "News and Announcements",
        "contact": "Contact Us",
        "staff_login": "Staff Login",
        "search": "Search Cases",
        "calendar": "Tuesday Calendar",
        "laws": "Laws, Decisions and Rules",
        "requirements": "Requirements",
        "bonds": "Bond Requirements",
        "clearance": "Clearance Requirements",
        "dashboard": "Staff Dashboard",
        "logout": "Log Out",
        "cases": "Cases",
        "manage_cases": "Manage Cases",
        "add_case": "Add Case",
        "edit_case": "Edit Case",
        "delete_case": "Delete Case",
        "case_number": "Case Number",
        "last_name": "Last Name / Party",
        "parties": "Parties",
        "case_title": "Case Title",
        "case_type": "Case Type",
        "status": "Status",
        "nature": "Nature",
        "description": "Description",
        "hearing": "Hearing",
        "hearings": "Hearings",
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
        "notice": "Notice",
        "notices": "Notices",
        "upload": "Upload",
        "photo_document": "Photo / Document",
        "legal_resources": "Legal Resources",
        "requirements_management": (
            "Manage Requirements"
        ),
        "staff_accounts": "Staff Accounts",
        "add_staff": "Add Staff Account",
        "staff_email": "Staff Email",
        "staff_username": "Staff Username",
        "staff_password": "Temporary Password",
        "role": "Role",
        "administrator": "Administrator",
        "staff": "Staff",
        "active": "Active",
        "disabled": "Disabled",
        "enable": "Enable",
        "disable": "Disable",
        "search_case": "Search for a Case",
        "search_instruction": (
            "Enter BOTH the complete case number "
            "and the last name / party name."
        ),
        "search_step_1": (
            "Enter the complete case number."
        ),
        "search_step_2": (
            "Enter the last name of a party."
        ),
        "search_step_3": (
            "Both fields are required."
        ),
        "search_step_4": (
            "Click Search Case."
        ),
        "no_results": (
            "No matching public case was found."
        ),
        "login": "Log In",
        "username": "Username",
        "password": "Password",
        "invalid_login": (
            "Invalid username or password."
        ),
        "login_required": (
            "Please log in as authorized staff."
        ),
        "welcome": "Welcome, Court Staff",
        "quick_actions": "Quick Actions",
        "open_maps": "Open Google Maps",
        "phone": "Telephone",
        "email": "Email Address",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court "
            "of Silang-Amadeo, Cavite. All rights reserved."
        ),
        "not_uploaded": "Not yet uploaded",
        "suspension": "Suspension Information",
        "official_source": "Official Source",
    },
    "fil": {
        "home": "Home",
        "about": "Tungkol sa Amin",
        "news": "Balita at mga Anunsyo",
        "contact": "Makipag-ugnayan",
        "staff_login": "Staff Login",
        "search": "Maghanap ng Kaso",
        "calendar": "Kalendaryo ng Martes",
        "laws": "Mga Batas, Desisyon at Alituntunin",
        "requirements": "Mga Kinakailangan",
        "bonds": "Mga Kinakailangan para sa Bonds",
        "clearance": "Mga Kinakailangan para sa Clearance",
        "dashboard": "Dashboard ng Staff",
        "logout": "Mag-Logout",
        "cases": "Mga Kaso",
        "manage_cases": "Pamahalaan ang mga Kaso",
        "add_case": "Magdagdag ng Kaso",
        "edit_case": "I-edit ang Kaso",
        "delete_case": "Burahin ang Kaso",
        "case_number": "Numero ng Kaso",
        "last_name": "Apelyido / Partido",
        "parties": "Mga Partido",
        "case_title": "Pamagat ng Kaso",
        "case_type": "Uri ng Kaso",
        "status": "Katayuan",
        "nature": "Uri",
        "description": "Deskripsyon",
        "hearing": "Pagdinig",
        "hearings": "Mga Pagdinig",
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
        "notice": "Abiso",
        "notices": "Mga Abiso",
        "upload": "Mag-upload",
        "photo_document": "Larawan / Dokumento",
        "legal_resources": (
            "Mga Legal na Resources"
        ),
        "requirements_management": (
            "Pamahalaan ang mga Kinakailangan"
        ),
        "staff_accounts": "Mga Account ng Staff",
        "add_staff": "Magdagdag ng Staff Account",
        "staff_email": "Email ng Staff",
        "staff_username": "Username ng Staff",
        "staff_password": "Pansamantalang Password",
        "role": "Role",
        "administrator": "Administrator",
        "staff": "Staff",
        "active": "Aktibo",
        "disabled": "Hindi Aktibo",
        "enable": "I-enable",
        "disable": "I-disable",
        "search_case": "Maghanap ng Kaso",
        "search_instruction": (
            "Ilagay ang PAREHONG case number "
            "at apelyido / pangalan ng partido."
        ),
        "search_step_1": (
            "Ilagay ang buong case number."
        ),
        "search_step_2": (
            "Ilagay ang apelyido ng isang partido."
        ),
        "search_step_3": (
            "Kinakailangan ang parehong field."
        ),
        "search_step_4": (
            "I-click ang Maghanap."
        ),
        "no_results": (
            "Walang nakitang tumutugmang pampublikong kaso."
        ),
        "login": "Mag-Login",
        "username": "Username",
        "password": "Password",
        "invalid_login": (
            "Mali ang username o password."
        ),
        "login_required": (
            "Mag-login bilang awtorisadong staff."
        ),
        "welcome": (
            "Maligayang Pagdating, Kawani ng Hukuman"
        ),
        "quick_actions": "Mabilis na Aksyon",
        "open_maps": "Buksan ang Google Maps",
        "phone": "Telepono",
        "email": "Email Address",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court "
            "of Silang-Amadeo, Cavite. Lahat ng karapatan ay nakalaan."
        ),
        "not_uploaded": "Hindi pa naiu-upload",
        "suspension": (
            "Impormasyon sa Suspensyon"
        ),
        "official_source": "Opisyal na Source",
    },
}


def tr(key):
    language = session.get(
        "language",
        "en",
    )

    if language not in TEXT:
        language = "en"

    return TEXT[language].get(
        key,
        TEXT["en"].get(key, key),
    )


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


def now():
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

        CREATE TABLE IF NOT EXISTS resources (
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

    # --------------------------------------------------------
    # Default requirements
    # --------------------------------------------------------

    default_requirements = [
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

    for item in default_requirements:

        exists = connection.execute(
            """
            SELECT id
            FROM requirements
            WHERE category = ?
            """,
            (item[0],),
        ).fetchone()

        if exists is None:

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
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    now(),
                ),
            )

    # --------------------------------------------------------
    # Default administrator
    # --------------------------------------------------------
    #
    # Requested credentials:
    #
    # Username: admin
    # Password: admin123
    #
    # This is for the initial prototype.
    # Change it before real production use.
    #
    # --------------------------------------------------------

    admin = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE username = 'admin'
        """
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
                generate_password_hash(
                    "admin123"
                ),
                "admin",
                1,
                now(),
            ),
        )

    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# AUTHENTICATION
# ============================================================

def staff_required(function):

    @wraps(function)
    def wrapper(
        *args,
        **kwargs
    ):

        if not session.get(
            "staff_logged_in",
            False,
        ):

            flash(
                tr("login_required"),
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

        if not session.get(
            "staff_logged_in",
            False,
        ):

            return redirect(
                url_for(
                    "staff_login"
                )
            )

        if session.get(
            "staff_role"
        ) != "admin":

            abort(403)

        return function(
            *args,
            **kwargs
        )

    return wrapper


def audit(
    action,
    target="",
):

    username = session.get(
        "staff_username",
        "system",
    )

    connection = get_db()

    connection.execute(
        """
        INSERT INTO audit_logs
        (
            username,
            action,
            target,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            action,
            str(target),
            now(),
        ),
    )

    connection.commit()

    connection.close()


# ============================================================
# UPLOADS
# ============================================================

def save_upload(upload):

    if upload is None:
        return None, None

    if not upload.filename:
        return None, None

    original = upload.filename.strip()

    safe_name = (
        original
        .replace("/", "_")
        .replace("\\", "_")
    )

    extension = ""

    if "." in safe_name:

        extension = safe_name.rsplit(
            ".",
            1
        )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "That file type is not allowed."
        )

    unique_name = (
        secrets.token_hex(16)
        + "_"
        + safe_name
    )

    upload.save(
        UPLOAD_DIR / unique_name
    )

    return unique_name, safe_name


# ============================================================
# THEME / LANGUAGE
# ============================================================

@app.route(
    "/language/<language>"
)
def change_language(language):

    if language not in (
        "en",
        "fil",
    ):

        language = "en"

    session["language"] = language

    return redirect(
        request.referrer
        or url_for("home")
    )


@app.route(
    "/theme/<theme>"
)
def change_theme(theme):

    if theme not in (
        "light",
        "dark",
    ):

        theme = "light"

    session["theme"] = theme

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# HTML PAGE WRAPPER
# ============================================================

def render_page(
    title,
    body,
):

    theme = session.get(
        "theme",
        "light",
    )

    if session.get(
        "staff_logged_in",
        False,
    ):

        extra_staff_links = f"""

        <a
            href="{url_for('staff_dashboard')}"
        >
            {tr("dashboard")}
        </a>

        <a
            href="{url_for('staff_cases')}"
        >
            {tr("cases")}
        </a>

        <a
            href="{url_for('staff_calendar')}"
        >
            {tr("calendar")}
        </a>

        <a
            href="{url_for('staff_notices')}"
        >
            {tr("notices")}
        </a>

        <a
            href="{url_for('staff_laws')}"
        >
            {tr("laws")}
        </a>

        <a
            href="{url_for('staff_requirements')}"
        >
            {tr("requirements")}
        </a>

        """

        if session.get(
            "staff_role"
        ) == "admin":

            extra_staff_links += f"""

            <a
                href="{url_for('staff_accounts')}"
            >
                {tr("staff_accounts")}
            </a>

            """

        extra_staff_links += f"""

        <form
            method="post"
            action="{url_for('logout')}"
            style="display:inline"
        >

            <button
                type="submit"
                class="nav-button"
            >
                {tr("logout")}
            </button>

        </form>

        """

    else:

        extra_staff_links = f"""

        <a
            href="{url_for('staff_login')}"
        >
            {tr("staff_login")}
        </a>

        """

    other_language = (
        "fil"
        if session.get("language", "en") == "en"
        else "en"
    )

    language_label = (
        "FIL"
        if session.get("language", "en") == "en"
        else "EN"
    )

    other_theme = (
        "dark"
        if theme == "light"
        else "light"
    )

    theme_label = (
        "🌙"
        if theme == "light"
        else "☀️"
    )

    full = f"""
<!doctype html>

<html lang="{escape_html(
    session.get("language", "en")
)}">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="description"
    content="MCTC Silang-Amadeo Court Information Portal"
>

<title>
{escape_html(title)}
-
{escape_html(COURT_SHORT)}
</title>

<style>

{STYLE}

</style>

</head>


<body class="{escape_html(theme)}">


<header class="site-header">

    <div class="header-inner">


        <a
            href="{url_for('home')}"
            class="brand-link"
        >

            <img
                class="logo"
                src="{url_for(
                    'static',
                    filename=LOGO_FILENAME
                )}"
                alt="Official Court Logo"
            >

            <div class="brand">

                <strong>
                    {escape_html(COURT_NAME)}
                </strong>

                <small>
                    Court Information Portal
                </small>

            </div>

        </a>


        <nav class="nav">

            <a href="{url_for('home')}">
                {tr("home")}
            </a>

            <a href="{url_for('about')}">
                {tr("about")}
            </a>

            <a href="{url_for('news')}">
                {tr("news")}
            </a>

            <a href="{url_for('contact')}">
                {tr("contact")}
            </a>

            {extra_staff_links}

            <a
                href="{url_for(
                    'change_language',
                    language=other_language
                )}"
            >
                {language_label}
            </a>

            <a
                href="{url_for(
                    'change_theme',
                    theme=other_theme
                )}"
            >
                {theme_label}
            </a>

        </nav>

    </div>

</header>


<main class="container">

    {render_flash_messages()}

    {body}

</main>


<footer>

    <strong>
        {escape_html(COURT_NAME)}
    </strong>

    <p>
        {escape_html(COURT_ADDRESS)}
    </p>

    <p>
        <a
            href="tel:{escape_html(COURT_PHONE)}"
        >
            {escape_html(COURT_PHONE)}
        </a>

        <br>

        <a
            href="mailto:{escape_html(COURT_EMAIL)}"
        >
            {escape_html(COURT_EMAIL)}
        </a>

    </p>

    <p>

        <a
            href="{GOOGLE_MAPS_URL}"
            target="_blank"
            rel="noopener noreferrer"
        >
            🗺️
            {tr("open_maps")}
        </a>

    </p>

    <p>
        {tr("copyright")}
    </p>

</footer>


</body>

</html>
"""

    response = app.response_class(
        full,
        mimetype="text/html",
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


def render_flash_messages():

    from flask import get_flashed_messages

    output = ""

    for category, message in (
        get_flashed_messages(
            with_categories=True
        )
    ):

        output += f"""

        <div
            class="notice {escape_html(
                category
            )}"
        >
            {escape_html(message)}
        </div>

        """

    return output


# ============================================================
# STYLE
# ============================================================

STYLE = r"""

:root {

    --purple-dark: #3b0764;

    --purple: #6d28d9;

    --purple-light: #8b5cf6;

    --purple-soft: #f0e8fb;

    --background: #faf8fc;

    --surface: #ffffff;

    --surface-two: #f5eff9;

    --text: #211727;

    --muted: #65576d;

    --border: #ded3e5;

    --danger: #a51d3f;

    --success: #176b38;

    --warning: #8a5a00;

}

body.dark {

    --background: #130f17;

    --surface: #211a27;

    --surface-two: #2d2133;

    --text: #faf5ff;

    --muted: #d0c2d6;

    --border: #4e3c57;

    --purple-soft: #36253f;

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

    min-height:
        100vh;

    background:
        var(--background);

    color:
        var(--text);

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height:
        1.65;

}

a {

    color:
        var(--purple);

    text-decoration:
        none;

}

body.dark a {

    color:
        #c4a1ff;

}

a:hover {

    text-decoration:
        underline;

}

.site-header {

    position:
        sticky;

    top:
        0;

    z-index:
        1000;

    color:
        white;

    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );

    box-shadow:
        0 7px 25px
        rgba(
            41,
            7,
            57,
            .28
        );

}

.header-inner {

    width:
        min(
            1240px,
            94%
        );

    margin:
        auto;

    padding:
        11px 0;

    display:
        flex;

    align-items:
        center;

    gap:
        16px;

    flex-wrap:
        wrap;

}

.brand-link {

    display:
        flex;

    align-items:
        center;

    gap:
        12px;

    color:
        white;

    text-decoration:
        none;

    flex:
        1;

    min-width:
        260px;

}

.brand-link:hover {

    text-decoration:
        none;

}

.logo {

    width:
        60px;

    height:
        60px;

    object-fit:
        contain;

    object-position:
        center;

    background:
        white;

    padding:
        4px;

    border-radius:
        50%;

    display:
        block;

}

.brand strong {

    display:
        block;

    font-size:
        15px;

}

.brand small {

    display:
        block;

    opacity:
        .86;

}

.nav {

    display:
        flex;

    align-items:
        center;

    flex-wrap:
        wrap;

    gap:
        4px;

}

.nav a,
.nav-button {

    color:
        white;

    background:
        transparent;

    border:
        0;

    border-radius:
        9px;

    padding:
        8px 9px;

    font-size:
        12px;

    font-weight:
        800;

    cursor:
        pointer;

    text-decoration:
        none;

}

.nav a:hover,
.nav-button:hover {

    background:
        rgba(
            255,
            255,
            255,
            .14
        );

    text-decoration:
        none;

}

.container {

    width:
        min(
            1180px,
            94%
        );

    margin:
        auto;

    padding:
        30px 0 70px;

}

.hero {

    margin:
        20px 0 25px;

    padding:
        55px 25px;

    border-radius:
        25px;

    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple),
            var(--purple-light)
        );

    color:
        white;

    text-align:
        center;

}

.hero-logo {

    width:
        150px;

    height:
        150px;

    object-fit:
        contain;

    object-position:
        center;

    display:
        block;

    margin:
        0 auto 20px;

    background:
        white;

    border-radius:
        50%;

    padding:
        5px;

}

.hero h1 {

    max-width:
        930px;

    margin:
        12px auto;

    font-size:
        clamp(
            30px,
            5vw,
            56px
        );

    line-height:
        1.05;

}

.card {

    padding:
        23px;

    margin:
        18px 0;

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    background:
        var(--surface);

    box-shadow:
        0 10px 30px
        rgba(
            55,
            20,
            70,
            .07
        );

}

.grid {

    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                250px,
                1fr
            )
        );

    gap:
        18px;

}

.two {

    display:
        grid;

    grid-template-columns:
        1fr 1fr;

    gap:
        15px;

}

input,
textarea,
select {

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

}

textarea {

    min-height:
        120px;

    resize:
        vertical;

}

label {

    display:
        block;

    margin:
        12px 0 5px;

    font-weight:
        800;

}

button,
.button {

    display:
        inline-block;

    padding:
        11px 16px;

    border:
        0;

    border-radius:
        10px;

    background:
        var(--purple);

    color:
        white;

    font-weight:
        800;

    cursor:
        pointer;

    text-decoration:
        none;

}

button:hover,
.button:hover {

    background:
        var(--purple-dark);

    color:
        white;

    text-decoration:
        none;

}

.secondary {

    background:
        var(--surface-two);

    color:
        var(--text);

    border:
        1px solid
        var(--border);

}

.danger {

    background:
        var(--danger);

}

.actions {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        8px;

    margin:
        14px 0;

}

.notice {

    padding:
        14px 16px;

    border-left:
        5px solid
        var(--purple);

    border-radius:
        10px;

    background:
        var(--surface-two);

    margin:
        12px 0;

}

.notice.warning {

    border-left-color:
        #d97706;

}

.notice.danger {

    border-left-color:
        #b91c1c;

}

.notice.success {

    border-left-color:
        #15803d;

}

.status {

    display:
        inline-block;

    padding:
        4px 10px;

    border-radius:
        999px;

    background:
        var(--purple-soft);

    color:
        var(--purple-dark);

    font-size:
        12px;

    font-weight:
        900;

}

body.dark .status {

    color:
        #eadcff;

}

.table-wrap {

    overflow-x:
        auto;

}

table {

    width:
        100%;

    border-collapse:
        collapse;

}

th,
td {

    padding:
        11px;

    text-align:
        left;

    vertical-align:
        top;

    border-bottom:
        1px solid
        var(--border);

}

th {

    background:
        var(--surface-two);

}

.empty {

    padding:
        45px 10px;

    text-align:
        center;

    color:
        var(--muted);

}

.small {

    font-size:
        13px;

    color:
        var(--muted);

}

footer {

    padding:
        32px 15px;

    text-align:
        center;

    color:
        var(--muted);

    background:
        var(--surface);

    border-top:
        1px solid
        var(--border);

}

@media(max-width:900px) {

    .header-inner {

        align-items:
            flex-start;

        flex-direction:
            column;

    }

    .brand-link {

        width:
            100%;

    }

    .nav {

        width:
            100%;

    }

    .two {

        grid-template-columns:
            1fr;

    }

}

@media(max-width:520px) {

    .container {

        width:
            94%;

    }

    .hero {

        padding:
            35px 18px;

    }

    .hero h1 {

        font-size:
            34px;

    }

}
"""


# ============================================================
# PUBLIC HOME
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

        if current_language() == "fil":

            heading = notice["title_fil"]

            message = notice["body_fil"]

        else:

            heading = notice["title_en"]

            message = notice["body_en"]

        attachment = ""

        if notice["attachment"]:

            attachment = f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=notice['attachment']
                )}"
            >
                📎
                {tr("open")}
            </a>

            """

        notice_html += f"""

        <div class="notice">

            <h3>
                {escape_html(heading)}
            </h3>

            <p>
                {escape_html(message)}
            </p>

            {attachment}

        </div>

        """

    body = f"""

    <section class="hero">

        <img
            class="hero-logo"
            src="{url_for(
                'static',
                filename=LOGO_FILENAME
            )}"
            alt="Official court logo"
        >

        <h1>
            {escape_html(COURT_NAME)}
        </h1>

        <p>
            Court information, public case searching,
            notices and Tuesday calendar.
        </p>

        <div class="actions"
             style="justify-content:center;">

            <a
                class="button"
                href="{url_for(
                    'search_cases'
                )}"
            >
                🔎
                {tr("search")}
            </a>

            <a
                class="button secondary"
                href="{url_for(
                    'public_calendar'
                )}"
            >
                📅
                {tr("calendar")}
            </a>

        </div>

    </section>


    <div class="grid">

        <div class="card">

            <h2>
                🔎
                {tr("search_case")}
            </h2>

            <p>
                {tr("search_instruction")}
            </p>

            <a
                class="button"
                href="{url_for(
                    'search_cases'
                )}"
            >
                {tr("search_button")}
            </a>

        </div>


        <div class="card">

            <h2>
                📅
                {tr("calendar")}
            </h2>

            <p>
                View the public Tuesday court calendar.
            </p>

            <a
                class="button"
                href="{url_for(
                    'public_calendar'
                )}"
            >
                {tr("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                📢
                {tr("news")}
            </h2>

            <p>
                Read notices and announcements.
            </p>

            <a
                class="button"
                href="{url_for(
                    'news'
                )}"
            >
                {tr("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                ⚖️
                {tr("laws")}
            </h2>

            <p>
                View legal resources added by authorized
                staff.
            </p>

            <a
                class="button"
                href="{url_for(
                    'laws'
                )}"
            >
                {tr("view")}
            </a>

        </div>

    </div>


    <div class="card">

        <h2>
            ⚠️
            {tr("suspension")}
        </h2>

        <p>
            Do not assume that a hearing or case has been
            suspended, postponed or cancelled unless an
            official court notice confirms it.
        </p>

    </div>


    <div class="card">

        <h2>
            📢
            {tr("news")}
        </h2>

        {notice_html or
        '<p class="small">No notices have been published.</p>'}

    </div>

    """

    return render_page(
        tr("home"),
        body,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    body = f"""

    <div class="card">

        <h1>
            {tr("about")}
        </h1>

        <h2>
            {escape_html(COURT_NAME)}
        </h2>

        <p>
            This portal is designed to provide approved
            public court information and easier access
            to court announcements and schedules.
        </p>

        <div class="notice warning">

            <strong>
                Important:
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
        tr("about"),
        body,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact")
def contact():

    body = f"""

    <div class="card">

        <h1>
            {tr("contact")}
        </h1>

        <h2>
            {escape_html(COURT_NAME)}
        </h2>

        <p>

            <strong>
                {tr("address")}:
            </strong>

            <br>

            {escape_html(COURT_ADDRESS)}

        </p>


        <p>

            <strong>
                {tr("phone")}:
            </strong>

            <br>

            <a
                href="tel:{escape_html(
                    COURT_PHONE
                )}"
            >
                {escape_html(COURT_PHONE)}
            </a>

        </p>


        <p>

            <strong>
                {tr("email")}:
            </strong>

            <br>

            <a
                href="mailto:{escape_html(
                    COURT_EMAIL
                )}"
            >
                {escape_html(COURT_EMAIL)}
            </a>

        </p>


        <a
            class="button"
            href="{GOOGLE_MAPS_URL}"
            target="_blank"
            rel="noopener noreferrer"
        >
            🗺️
            {tr("open_maps")}
        </a>

    </div>

    """

    return render_page(
        tr("contact"),
        body,
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

    body = f"""

    <div class="card">

        <h1>
            📢
            {tr("news")}
        </h1>

    </div>

    """

    for notice in notices:

        title = (
            notice["title_fil"]
            if current_language() == "fil"
            else notice["title_en"]
        )

        message = (
            notice["body_fil"]
            if current_language() == "fil"
            else notice["body_en"]
        )

        body += f"""

        <div class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(message)}
            </p>

        """

        if notice["attachment"]:

            body += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=notice['attachment']
                )}"
            >
                📎
                {tr("open")}
            </a>

            """

        body += """

        </div>

        """

    if not notices:

        body += """

        <div class="card empty">

            No notices are currently published.

        </div>

        """

    return render_page(
        tr("news"),
        body,
    )


# ============================================================
# PUBLIC CASE SEARCH
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

    number = request.values.get(
        "case_number",
        "",
    ).strip()

    last_name = request.values.get(
        "last_name",
        "",
    ).strip()

    searched = (
        request.method == "POST"
        or bool(number)
        or bool(last_name)
    )

    if request.method == "POST":

        if not number or not last_name:

            flash(
                tr("both_required"),
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
                    number,
                    last_name,
                ),
            ).fetchone()

            db.close()

            if case is None:

                flash(
                    tr("no_results"),
                    "warning",
                )

    body = f"""

    <div class="card">

        <h1>
            🔎
            {tr("search_case")}
        </h1>

        <div class="instructions">

            <h3>
                {tr("how_search")}
            </h3>

            <ol>

                <li>
                    {tr("search_step_1")}
                </li>

                <li>
                    {tr("search_step_2")}
                </li>

                <li>
                    {tr("search_step_3")}
                </li>

                <li>
                    {tr("search_step_4")}
                </li>

            </ol>

        </div>


        <form method="post">

            <label>
                {tr("case_number")}
            </label>

            <input
                name="case_number"
                value="{escape_html(number)}"
                required
                autocomplete="off"
                placeholder="MCTC-2026-001"
            >


            <label>
                {tr("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(last_name)}"
                required
                autocomplete="off"
                placeholder="DELA CRUZ"
            >


            <button
                type="submit"
            >
                🔎
                {tr("search_button")}
            </button>

        </form>

    </div>

    """

    if case:

        body += f"""

        <div class="card">

            <span class="status">
                {escape_html(
                    case["status"]
                )}
            </span>

            <h2>
                {escape_html(
                    case["case_number"]
                )}
            </h2>

            <p>
                <strong>
                    {tr("parties")}:
                </strong>

                {escape_html(
                    case["parties"]
                )}
            </p>

            <p>
                <strong>
                    {tr("case_title")}:
                </strong>

                {escape_html(
                    case["case_title"]
                )}
            </p>

            <p>
                <strong>
                    {tr("nature")}:
                </strong>

                {escape_html(
                    case["case_type"]
                )}
            </p>

            <a
                class="button"
                href="{url_for(
                    'public_case',
                    case_id=case['id']
                )}"
            >
                {tr("view")}
            </a>

        </div>

        """

    return render_page(
        tr("search"),
        body,
    )


# ============================================================
# PUBLIC CASE DETAILS
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

    if not case:

        abort(404)

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""

        <div class="notice">

            <h3>
                {escape_html(
                    hearing["hearing_date"]
                )}
            </h3>

            <p>
                <strong>
                    {tr("hearing_time")}:
                </strong>

                {escape_html(
                    hearing["hearing_time"]
                )}
            </p>

            <p>
                <strong>
                    {tr("hearing_nature")}:
                </strong>

                {escape_html(
                    hearing["hearing_nature"]
                )}
            </p>

            <p>

                <strong>
                    {tr("hearing_status")}:
                </strong>

                <span class="status">
                    {escape_html(
                        hearing["hearing_status"]
                    )}
                </span>

            </p>

            <p>
                <strong>
                    {tr("courtroom")}:
                </strong>

                {escape_html(
                    hearing["courtroom"]
                )}
            </p>

        </div>

        """

    body = f"""

    <div class="card">

        <span class="status">
            {escape_html(
                case["status"]
            )}
        </span>

        <h1>
            {escape_html(
                case["case_number"]
            )}
        </h1>

        <h2>
            {escape_html(
                case["case_title"]
            )}
        </h2>

        <p>
            <strong>
                {tr("parties")}:
            </strong>

            {escape_html(
                case["parties"]
            )}
        </p>

        <p>
            <strong>
                {tr("nature")}:
            </strong>

            {escape_html(
                case["case_type"]
            )}
        </p>

        <p>
            {escape_html(
                case["public_description"]
            )}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {tr("hearings")}
        </h2>

        {hearing_html or '''
        <p class="small">
            No published hearing information.
        </p>
        '''}

    </div>

    """

    return render_page(
        tr("case"),
        body,
    )


# ============================================================
# PUBLIC TUESDAY CALENDAR
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
        ORDER BY
            calendar_date,
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
                    entry["hearing_status"]
                )}
            </td>

            <td>
                {escape_html(
                    entry["courtroom"]
                )}
            </td>

        </tr>

        """

    body = f"""

    <div class="card">

        <h1>
            📅
            {tr("calendar")}
        </h1>

        <p>
            Published Tuesday calendar.
        </p>

        <div class="notice warning">

            Hearing schedules may change.
            Confirm important details with
            the court.

        </div>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        {tr("hearing_date")}
                    </th>

                    <th>
                        {tr("hearing_time")}
                    </th>

                    <th>
                        {tr("case_number")}
                    </th>

                    <th>
                        {tr("parties")}
                    </th>

                    <th>
                        {tr("hearing_nature")}
                    </th>

                    <th>
                        {tr("hearing_status")}
                    </th>

                    <th>
                        {tr("courtroom")}
                    </th>

                </tr>

            </thead>

            <tbody>

                {rows or '''
                <tr>
                    <td colspan="7"
                        class="empty">
                        No Tuesday entries.
                    </td>
                </tr>
                '''}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        tr("calendar"),
        body,
    )


# ============================================================
# PUBLIC REQUIREMENTS
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

    body = f"""

    <div class="card">

        <h1>
            📄
            {tr("requirements")}
        </h1>

    </div>

    """

    for row in rows:

        if current_language() == "fil":

            title = row["title_fil"]

            description = (
                row["description_fil"]
                or tr("not_uploaded")
            )

        else:

            title = row["title_en"]

            description = (
                row["description_en"]
                or tr("not_uploaded")
            )

        file_link = ""

        if row["file_name"]:

            file_link = f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=row['file_name']
                )}"
            >
                {tr("open")}
            </a>

            """

        body += f"""

        <div class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(description)}
            </p>

            {file_link}

        </div>

        """

    return render_page(
        tr("requirements"),
        body,
    )


# ============================================================
# PUBLIC LEGAL RESOURCES
# ============================================================

@app.route(
    "/laws"
)
def laws():

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM resources
        ORDER BY category,
                 created_at DESC
        """
    ).fetchall()

    db.close()

    body = f"""

    <div class="card">

        <h1>
            ⚖️
            {tr("laws")}
        </h1>

        <p>
            This section is for approved references
            to Philippine laws, Supreme Court
            decisions, rules and other legal resources.
        </p>

        <div class="notice warning">

            Verify current legal authorities
            against an authoritative source.

        </div>

    </div>

    """

    for row in rows:

        body += f"""

        <div class="card">

            <span class="status">
                {escape_html(
                    row["category"]
                )}
            </span>

            <h2>
                {escape_html(
                    row["title"]
                )}
            </h2>

            <p>
                {escape_html(
                    row["description"]
                )}
            </p>

        """

        if row["source_url"]:

            body += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    row["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {tr("official_source")}
            </a>

            """

        if row["file_name"]:

            body += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=row['file_name']
                )}"
            >
                {tr("open")}
            </a>

            """

        body += """

        </div>

        """

    if not rows:

        body += """

        <div class="card empty">

            No legal resources have been published.

        </div>

        """

    return render_page(
        tr("laws"),
        body,
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

    if session.get(
        "staff_logged_in",
        False,
    ):

        return redirect(
            url_for(
                "staff_dashboard"
            )
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

            session["staff_username"] = (
                staff["username"]
            )

            session["staff_role"] = (
                staff["role"]
            )

            audit(
                "login",
                staff["username"],
            )

            return redirect(
                url_for(
                    "staff_dashboard"
                )
            )

        flash(
            tr("invalid_login"),
            "danger",
        )

    body = f"""

    <div class="login-box card">

        <img
            class="hero-logo"
            src="{url_for(
                'static',
                filename=LOGO_FILENAME
            )}"
            alt="Court logo"
        >

        <h1>
            🔐
            {tr("staff_login")}
        </h1>

        <p class="small">
            Authorized court staff only.
        </p>

        <form
            method="post"
            autocomplete="off"
        >

            <label>
                {tr("username")}
            </label>

            <input
                type="text"
                name="username"
                autocomplete="username"
                required
            >


            <label>
                {tr("password")}
            </label>

            <input
                type="password"
                name="password"
                autocomplete="current-password"
                required
            >


            <br>

            <button type="submit">

                {tr("login")}

            </button>

        </form>

    </div>

    """

    return render_page(
        tr("staff_login"),
        body,
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/staff/logout",
    methods=[
        "GET",
        "POST",
    ]
)
def logout():

    username = session.get(
        "staff_username",
        "unknown",
    )

    if session.get(
        "staff_logged_in"
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
        "no-store, "
        "no-cache, "
        "must-revalidate, "
        "max-age=0"
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

@app.route(
    "/staff"
)
@app.route(
    "/staff/dashboard"
)
@staff_required
def staff_dashboard():

    db = get_db()

    case_count = db.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    notice_count = db.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    calendar_count = db.execute(
        "SELECT COUNT(*) FROM tuesday_calendar"
    ).fetchone()[0]

    law_count = db.execute(
        "SELECT COUNT(*) FROM resources"
    ).fetchone()[0]

    db.close()

    body = f"""

    <section class="hero">

        <h1>
            {tr("welcome")}
        </h1>

        <p>
            Use the tools below to manage approved
            public court information.
        </p>

    </section>


    <section class="grid">

        <div class="stat">

            <span class="stat-number">
                {case_count}
            </span>

            <strong>
                {tr("cases")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {notice_count}
            </span>

            <strong>
                {tr("notices")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {calendar_count}
            </span>

            <strong>
                {tr("calendar")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {law_count}
            </span>

            <strong>
                {tr("laws")}
            </strong>

        </div>

    </section>


    <section class="card">

        <h2>
            ⚡
            {tr("quick_actions")}
        </h2>

        <div class="grid">

            <a
                class="card"
                href="{url_for(
                    'staff_cases'
                )}"
            >
                📋
                <h3>
                    {tr("manage_cases")}
                </h3>

                <p class="small">
                    Add, edit, delete cases and
                    change hearing information.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_calendar'
                )}"
            >
                📅
                <h3>
                    {tr("manage_calendar")}
                </h3>

                <p class="small">
                    Manage the Tuesday calendar.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_notices'
                )}"
            >
                📢
                <h3>
                    {tr("manage_notices")}
                </h3>

                <p class="small">
                    Upload photos and documents.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_laws'
                )}"
            >
                ⚖️
                <h3>
                    {tr("manage_laws")}
                </h3>

                <p class="small">
                    Add laws, decisions and rules.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_requirements'
                )}"
            >
                📄
                <h3>
                    {tr("requirements_management")}
                </h3>

                <p class="small">
                    Manage bond and clearance
                    information.
                </p>

            </a>

        </div>

    </section>

    """

    if session.get(
        "staff_role"
    ) == "admin":

        body += f"""

        <section class="card">

            <h2>
                👥
                {tr("staff_accounts")}
            </h2>

            <p>
                Only administrators can add or manage
                other staff accounts.
            </p>

            <a
                class="button"
                href="{url_for(
                    'staff_accounts'
                )}"
            >
                {tr("staff_accounts")}
            </a>

        </section>

        """

    return render_page(
        tr("dashboard"),
        body,
    )


# ============================================================
# STAFF CASES
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

                <strong>
                    {escape_html(
                        case["case_number"]
                    )}
                </strong>

                <br>

                {escape_html(
                    case["case_title"]
                )}

            </td>


            <td>
                {escape_html(
                    case["parties"]
                )}
            </td>


            <td>
                {escape_html(
                    case["case_type"]
                )}
            </td>


            <td>
                <span class="status">
                    {escape_html(
                        case["status"]
                    )}
                </span>
            </td>


            <td>

                <div class="actions">

                    <a
                        class="button secondary"
                        href="{url_for(
                            'staff_edit_case',
                            case_id=case['id']
                        )}"
                    >
                        {tr("edit")}
                    </a>


                    <a
                        class="button secondary"
                        href="{url_for(
                            'staff_hearing',
                            case_id=case['id']
                        )}"
                    >
                        {tr("hearing")}
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
                            type="submit"
                            class="danger"
                        >
                            {tr("delete")}
                        </button>

                    </form>

                </div>

            </td>

        </tr>

        """

    body = f"""

    <div class="flex">

        <h1>
            {tr("manage_cases")}
        </h1>

        <a
            class="button"
            href="{url_for(
                'staff_add_case'
            )}"
        >
            ➕
            {tr("add_case")}
        </a>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        {tr("case_number")}
                    </th>

                    <th>
                        {tr("parties")}
                    </th>

                    <th>
                        {tr("case_type")}
                    </th>

                    <th>
                        {tr("status")}
                    </th>

                    <th>
                        Actions
                    </th>

                </tr>

            </thead>

            <tbody>

                {rows or '''
                <tr>
                    <td
                        colspan="5"
                        class="empty"
                    >
                        No cases.
                    </td>
                </tr>
                '''}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        tr("cases"),
        body,
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

        case_number = request.form.get(
            "case_number",
            "",
        ).strip()

        last_name = request.form.get(
            "last_name",
            "",
        ).strip()

        parties = request.form.get(
            "parties",
            "",
        ).strip()

        case_title = request.form.get(
            "case_title",
            "",
        ).strip()

        case_type = request.form.get(
            "case_type",
            "",
        ).strip()

        status = request.form.get(
            "status",
            "Pending",
        ).strip()

        public_description = request.form.get(
            "public_description",
            "",
        ).strip()

        internal_notes = request.form.get(
            "internal_notes",
            "",
        ).strip()

        if (
            not case_number
            or not last_name
            or not parties
            or not case_title
        ):

            flash(
                "Please complete all required fields.",
                "danger",
            )

            return redirect(
                url_for(
                    "staff_add_case"
                )
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
                    now(),
                    now(),
                ),
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

        audit(
            "case_created",
            case_number,
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

    body = f"""

    <div class="card">

        <h1>
            ➕
            {tr("add_case")}
        </h1>

        <form method="post">

            <label>
                {tr("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {tr("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {tr("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                {tr("case_title")}
            </label>

            <input
                name="case_title"
                required
            >


            <label>
                {tr("case_type")}
            </label>

            <input
                name="case_type"
            >


            <label>
                {tr("status")}
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
                {tr("description")}
            </label>

            <textarea
                name="public_description"
            ></textarea>


            <label>
                Private Staff Notes
            </label>

            <textarea
                name="internal_notes"
            ></textarea>


            <div class="actions">

                <button type="submit">
                    {tr("save")}
                </button>

                <a
                    class="button secondary"
                    href="{url_for(
                        'staff_cases'
                    )}"
                >
                    {tr("cancel")}
                </a>

            </div>

        </form>

    </div>

    """

    return render_page(
        tr("add_case"),
        body,
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

    if not case:

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

                now(),

                case_id,
            ),
        )

        db.commit()

        db.close()

        audit(
            "case_updated",
            case["case_number"],
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

    status_options = ""

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
            if value == case["status"]
            else ""
        )

        status_options += f"""
        <option {selected}>
            {escape_html(value)}
        </option>
        """

    body = f"""

    <div class="card">

        <h1>
            ✏️
            {tr("edit_case")}
        </h1>

        <form method="post">

            <label>
                {tr("case_number")}
            </label>

            <input
                value="{escape_html(
                    case["case_number"]
                )}"
                disabled
            >


            <label>
                {tr("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(
                    case["last_name"]
                )}"
                required
            >


            <label>
                {tr("parties")}
            </label>

            <input
                name="parties"
                value="{escape_html(
                    case["parties"]
                )}"
                required
            >


            <label>
                {tr("case_title")}
            </label>

            <input
                name="case_title"
                value="{escape_html(
                    case["case_title"]
                )}"
                required
            >


            <label>
                {tr("case_type")}
            </label>

            <input
                name="case_type"
                value="{escape_html(
                    case["case_type"]
                )}"
            >


            <label>
                {tr("status")}
            </label>

            <select name="status">

                {status_options}

            </select>


            <label>
                {tr("description")}
            </label>

            <textarea
                name="public_description"
            >{escape_html(
                case["public_description"]
            )}</textarea>


            <label>
                Private Staff Notes
            </label>

            <textarea
                name="internal_notes"
            >{escape_html(
                case["internal_notes"]
            )}</textarea>


            <div class="actions">

                <button type="submit">
                    {tr("save")}
                </button>

                <a
                    class="button secondary"
                    href="{url_for(
                        'staff_cases'
                    )}"
                >
                    {tr("cancel")}
                </a>

            </div>

        </form>

    </div>

    """

    return render_page(
        tr("edit_case"),
        body,
    )


# ============================================================
# DELETE CASE
# ============================================================

@app.post(
    "/staff/cases/<int:case_id>/delete"
)
@staff_required
def staff_delete_case(case_id):

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

    db.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    db.commit()

    db.close()

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
# HEARING EDITOR
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

        hearing_date = request.form.get(
            "hearing_date",
            "",
        ).strip()

        hearing_time = request.form.get(
            "hearing_time",
            "",
        ).strip()

        hearing_nature = request.form.get(
            "hearing_nature",
            "",
        ).strip()

        hearing_status = request.form.get(
            "hearing_status",
            "Scheduled",
        ).strip()

        courtroom = request.form.get(
            "courtroom",
            "",
        ).strip()

        remarks = request.form.get(
            "remarks",
            "",
        ).strip()

        if hearing:

            db.execute(
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
                (
                    hearing_date,
                    hearing_time,
                    hearing_nature,
                    hearing_status,
                    courtroom,
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
                    hearing_nature,
                    hearing_status,
                    courtroom,
                    remarks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    hearing_date,
                    hearing_time,
                    hearing_nature,
                    hearing_status,
                    courtroom,
                    remarks,
                ),
            )

        db.commit()

        db.close()

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

    db.close()

    current_date = (
        hearing["hearing_date"]
        if hearing
        else ""
    )

    current_time = (
        hearing["hearing_time"]
        if hearing
        else ""
    )

    current_nature = (
        hearing["hearing_nature"]
        if hearing
        else "Initial Hearing"
    )

    current_status = (
        hearing["hearing_status"]
        if hearing
        else "Scheduled"
    )

    current_room = (
        hearing["courtroom"]
        if hearing
        else ""
    )

    current_remarks = (
        hearing["remarks"]
        if hearing
        else ""
    )

    hearing_natures = [
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

    for value in hearing_natures:

        selected = (
            "selected"
            if value == current_nature
            else ""
        )

        nature_options += f"""
        <option {selected}>
            {escape_html(value)}
        </option>
        """

    status_options = ""

    for value in hearing_statuses:

        selected = (
            "selected"
            if value == current_status
            else ""
        )

        status_options += f"""
        <option {selected}>
            {escape_html(value)}
        </option>
        """

    body = f"""

    <div class="card">

        <h1>
            📅
            {tr("hearing")}
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
                {tr("hearing_date")}
            </label>

            <input
                type="date"
                name="hearing_date"
                value="{escape_html(
                    current_date
                )}"
                required
            >


            <label>
                {tr("hearing_time")}
            </label>

            <input
                type="time"
                name="hearing_time"
                value="{escape_html(
                    current_time
                )}"
            >


            <label>
                {tr("hearing_nature")}
            </label>

            <select
                name="hearing_nature"
            >

                {nature_options}

            </select>


            <label>
                {tr("hearing_status")}
            </label>

            <select
                name="hearing_status"
            >

                {status_options}

            </select>


            <label>
                {tr("courtroom")}
            </label>

            <input
                name="courtroom"
                value="{escape_html(
                    current_room
                )}"
            >


            <label>
                {tr("remarks")}
            </label>

            <textarea
                name="remarks"
            >{escape_html(
                current_remarks
            )}</textarea>


            <button type="submit">
                {tr("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        tr("hearing"),
        body,
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
        ORDER BY
            calendar_date,
            calendar_time,
            id
        """
    ).fetchall()

    db.close()

    entries_html = ""

    for entry in entries:

        status_options = ""

        for value in [
            "Scheduled",
            "Ongoing",
            "Completed",
            "Reset",
            "Postponed",
            "Cancelled",
        ]:

            selected = (
                "selected"
                if value
                == entry["hearing_status"]
                else ""
            )

            status_options += f"""
            <option {selected}>
                {value}
            </option>
            """

        entries_html += f"""

        <div class="card">

            <form
                method="post"
                action="{url_for(
                    'edit_calendar',
                    entry_id=entry['id']
                )}"
            >

                <div class="two">

                    <div>

                        <label>
                            Date
                        </label>

                        <input
                            type="date"
                            name="calendar_date"
                            value="{escape_html(
                                entry["calendar_date"]
                            )}"
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
                            value="{escape_html(
                                entry["calendar_time"]
                            )}"
                            required
                        >

                    </div>

                </div>


                <label>
                    {tr("case_number")}
                </label>

                <input
                    name="case_number"
                    value="{escape_html(
                        entry["case_number"]
                    )}"
                    required
                >


                <label>
                    {tr("last_name")}
                </label>

                <input
                    name="last_name"
                    value="{escape_html(
                        entry["last_name"]
                    )}"
                    required
                >


                <label>
                    {tr("parties")}
                </label>

                <input
                    name="parties"
                    value="{escape_html(
                        entry["parties"]
                    )}"
                    required
                >


                <label>
                    {tr("hearing_nature")}
                </label>

                <input
                    name="hearing_nature"
                    value="{escape_html(
                        entry["hearing_nature"]
                    )}"
                    required
                >


                <label>
                    {tr("hearing_status")}
                </label>

                <select name="hearing_status">

                    {status_options}

                </select>


                <label>
                    {tr("courtroom")}
                </label>

                <input
                    name="courtroom"
                    value="{escape_html(
                        entry["courtroom"]
                    )}"
                >


                <label>
                    {tr("remarks")}
                </label>

                <textarea
                    name="remarks"
                >{escape_html(
                    entry["remarks"]
                )}</textarea>


                <label>

                    <input
                        type="checkbox"
                        name="public_visible"
                        style="width:auto"
                        {
                            "checked"
                            if entry["public_visible"]
                            else ""
                        }
                    >

                    Publish to civilians

                </label>


                <div class="actions">

                    <button type="submit">

                        {tr("save")}

                    </button>

                    <a
                        class="button danger"
                        href="{url_for(
                            'delete_calendar',
                            entry_id=entry['id']
                        )}"
                        onclick="
                            return confirm(
                                'Delete this entry?'
                            );
                        "
                    >
                        {tr("delete")}
                    </a>

                </div>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            📅
            {tr("manage_calendar")}
        </h1>

        <p>
            Staff can edit the Tuesday calendar.
            Civilians can see entries that are
            published.
        </p>

    </div>


    <div class="card">

        <h2>
            {tr("add")}
        </h2>

        <form
            method="post"
            action="{url_for(
                'add_calendar'
            )}"
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
                {tr("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {tr("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {tr("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                {tr("hearing_nature")}
            </label>

            <input
                name="hearing_nature"
                required
            >


            <label>
                {tr("hearing_status")}
            </label>

            <select
                name="hearing_status"
            >

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
                {tr("courtroom")}
            </label>

            <input
                name="courtroom"
            >


            <label>
                {tr("remarks")}
            </label>

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
                {tr("add")}
            </button>

        </form>

    </div>


    <div>

        {entries_html or
        '<div class="card empty">No calendar entries.</div>'}

    </div>

    """

    return render_page(
        tr("calendar"),
        body,
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
            hearing_status,
            courtroom,
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
                "hearing_status",
                "Scheduled",
            ).strip(),

            request.form.get(
                "courtroom",
                "",
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

            now(),

            now(),
        )
    )

    db.commit()

    db.close()

    audit(
        "calendar_created",
        request.form.get(
            "case_number",
            "",
        ),
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
def edit_calendar(entry_id):

    db = get_db()

    db.execute(
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
                "hearing_status",
                "Scheduled",
            ).strip(),

            request.form.get(
                "courtroom",
                "",
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

            now(),

            entry_id,
        )
    )

    db.commit()

    db.close()

    audit(
        "calendar_updated",
        entry_id,
    )

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

    audit(
        "calendar_deleted",
        entry_id,
    )

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
            if current_language() == "fil"
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

            """

        if notice["attachment"]:

            rows += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=notice['attachment']
                )}"
            >
                📎
                {tr("open")}
            </a>

            """

        rows += f"""

            <br><br>

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
                    {tr("delete")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            📢
            {tr("manage_notices")}
        </h1>

        <p>
            Staff can publish notices with photos
            or documents.
        </p>


        <form
            method="post"
            action="{url_for(
                'add_notice'
            )}"
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
                {tr("photo_document")}
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


            <button type="submit">
                {tr("upload")}
            </button>

        </form>

    </div>


    <div class="card">

        {rows or
        '<p class="empty">No notices yet.</p>'}

    </div>

    """

    return render_page(
        tr("notices"),
        body,
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

    if not (
        title_en
        and title_fil
        and body_en
        and body_fil
    ):

        flash(
            "Complete all notice fields.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_notices"
            )
        )

    uploaded = request.files.get(
        "attachment"
    )

    try:

        filename, original = save_upload(
            uploaded
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
            now(),
            now(),
        )
    )

    db.commit()

    db.close()

    audit(
        "notice_created",
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

    audit(
        "notice_deleted",
        notice_id,
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
        FROM resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    resources_html = ""

    for row in rows:

        resources_html += f"""

        <div class="notice">

            <span class="status">
                {escape_html(
                    row["category"]
                )}
            </span>

            <h3>
                {escape_html(
                    row["title"]
                )}
            </h3>

            <p>
                {escape_html(
                    row["description"]
                )}
            </p>

            """

        if row["source_url"]:

            resources_html += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    row["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {tr("official_source")}
            </a>

            """

        if row["file_name"]:

            resources_html += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=row['file_name']
                )}"
            >
                {tr("open")}
            </a>

            """

        resources_html += f"""

            <form
                method="post"
                action="{url_for(
                    'delete_law',
                    law_id=row['id']
                )}"
                style="display:inline"
                onsubmit="
                    return confirm(
                        'Delete this resource?'
                    );
                "
            >

                <button
                    type="submit"
                    class="danger"
                >
                    {tr("delete")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            ⚖️
            {tr("manage_laws")}
        </h1>

        <p>
            Add references to Philippine laws,
            decisions, rules and other official
            legal resources.
        </p>


        <form
            method="post"
            action="{url_for(
                'add_law'
            )}"
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


            <button type="submit">
                {tr("add")}
            </button>

        </form>

    </div>


    <div class="card">

        {resources_html or
        '<p class="empty">No legal resources yet.</p>'}

    </div>

    """

    return render_page(
        tr("laws"),
        body,
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

    try:

        filename, original = save_upload(
            request.files.get("file")
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

    db = get_db()

    db.execute(
        """
        INSERT INTO resources
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
            now(),
            now(),
        )
    )

    db.commit()

    db.close()

    audit(
        "resource_created",
        title,
    )

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
def delete_law(law_id):

    db = get_db()

    row = db.execute(
        """
        SELECT *
        FROM resources
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
        DELETE FROM resources
        WHERE id = ?
        """,
        (law_id,),
    )

    db.commit()

    db.close()

    audit(
        "resource_deleted",
        law_id,
    )

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

        if current_language() == "fil":

            title = row["title_fil"]

            description = row[
                "description_fil"
            ]

        else:

            title = row["title_en"]

            description = row[
                "description_en"
            ]

        sections += f"""

        <div class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p class="small">
                Current:
                {escape_html(
                    description
                    or tr("not_uploaded")
                )}
            </p>

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
                    Upload official document
                </label>

                <input
                    type="file"
                    name="document"
                >


                <button type="submit">
                    {tr("save")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            📄
            {tr("requirements_management")}
        </h1>

        <p>
            Bond and clearance requirements begin
            as "Not yet uploaded".
        </p>

    </div>

    {sections}

    """

    return render_page(
        tr("requirements"),
        body,
    )


@app.post(
    "/staff/requirements/<category>/update"
)
@staff_required
def update_requirement(category):

    if category not in (
        "bond",
        "clearance",
    ):

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
                now(),
                category,
            ),
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
                now(),
                category,
            ),
        )

    db.commit()

    db.close()

    audit(
        "requirement_updated",
        category,
    )

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
#
# ADMIN ONLY
#
# Initial account:
#
# Username: admin
# Password: admin123
#
# Admin can add other staff accounts with:
# - email
# - username
# - password
# - role
#
# Passwords are stored as hashes.
# ============================================================

@app.route(
    "/staff/accounts"
)
@admin_required
def staff_accounts():

    db = get_db()

    accounts = db.execute(
        """
        SELECT
            id,
            username,
            email,
            role,
            active,
            created_at
        FROM staff
        ORDER BY username
        """
    ).fetchall()

    db.close()

    rows = ""

    for account in accounts:

        state = (
            tr("active")
            if account["active"]
            else tr("disabled")
        )

        action_text = (
            tr("disable")
            if account["active"]
            else tr("enable")
        )

        rows += f"""

        <tr>

            <td>
                {escape_html(
                    account["username"]
                )}
            </td>

            <td>
                {escape_html(
                    account["email"]
                )}
            </td>

            <td>
                {escape_html(
                    account["role"]
                )}
            </td>

            <td>
                <span class="status">
                    {escape_html(state)}
                </span>
            </td>

            <td>

                <form
                    method="post"
                    action="{url_for(
                        'toggle_staff_account',
                        staff_id=account['id']
                    )}"
                    style="display:inline"
                >

                    <button
                        type="submit"
                        class="secondary"
                    >
                        {action_text}
                    </button>

                </form>

                """

        if account["username"] != "admin":

            rows += f"""

                <form
                    method="post"
                    action="{url_for(
                        'delete_staff_account',
                        staff_id=account['id']
                    )}"
                    style="display:inline"
                    onsubmit="
                        return confirm(
                            'Delete this staff account?'
                        );
                    "
                >

                    <button
                        type="submit"
                        class="danger"
                    >
                        {tr("delete")}
                    </button>

                </form>

            """

        rows += """

            </td>

        </tr>

        """

    body = f"""

    <div class="card">

        <h1>
            👥
            {tr("staff_accounts")}
        </h1>

        <p>
            You are signed in as an administrator.
            You can add additional staff accounts below.
        </p>

    </div>


    <div class="card">

        <h2>
            ➕
            {tr("add_staff")}
        </h2>

        <form
            method="post"
            action="{url_for(
                'add_staff_account'
            )}"
        >

            <label>
                {tr("staff_email")}
            </label>

            <input
                type="email"
                name="email"
                required
            >


            <label>
                {tr("staff_username")}
            </label>

            <input
                name="username"
                required
                autocomplete="off"
            >


            <label>
                {tr("staff_password")}
            </label>

            <input
                type="password"
                name="password"
                required
                autocomplete="new-password"
            >


            <label>
                {tr("role")}
            </label>

            <select name="role">

                <option value="staff">
                    {tr("staff")}
                </option>

                <option value="admin">
                    {tr("administrator")}
                </option>

            </select>


            <button type="submit">
                {tr("add_staff")}
            </button>

        </form>

    </div>


    <div class="card table-wrap">

        <h2>
            Existing Staff Accounts
        </h2>

        <table>

            <thead>

                <tr>

                    <th>
                        {tr("username")}
                    </th>

                    <th>
                        {tr("staff_email")}
                    </th>

                    <th>
                        {tr("role")}
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

                {rows}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        tr("staff_accounts"),
        body,
    )


@app.post(
    "/staff/accounts/add"
)
@admin_required
def add_staff_account():

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

    if role not in (
        "staff",
        "admin",
    ):

        role = "staff"

    if not username or not email or not password:

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
            "Staff passwords must be at least 8 characters.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    db = get_db()

    try:

        db.execute(
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

        db.commit()

    except sqlite3.IntegrityError:

        db.close()

        flash(
            "That username or email already exists.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    db.close()

    audit(
        "staff_created",
        username,
    )

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
def toggle_staff_account(staff_id):

    db = get_db()

    account = db.execute(
        """
        SELECT *
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if not account:

        db.close()

        abort(404)

    if account["username"] == "admin":

        db.close()

        flash(
            "The primary admin account cannot be disabled.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    new_state = (
        0
        if account["active"]
        else 1
    )

    db.execute(
        """
        UPDATE staff
        SET active = ?
        WHERE id = ?
        """,
        (
            new_state,
            staff_id,
        ),
    )

    db.commit()

    db.close()

    audit(
        "staff_toggled",
        account["username"],
    )

    return redirect(
        url_for(
            "staff_accounts"
        )
    )


@app.post(
    "/staff/accounts/<int:staff_id>/delete"
)
@admin_required
def delete_staff_account(staff_id):

    db = get_db()

    account = db.execute(
        """
        SELECT *
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if not account:

        db.close()

        abort(404)

    if account["username"] == "admin":

        db.close()

        flash(
            "The primary admin account cannot be deleted.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    db.execute(
        """
        DELETE FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    )

    db.commit()

    db.close()

    audit(
        "staff_deleted",
        account["username"],
    )

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
# FILES
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    return {
        "status": "ok",
        "service": "MCTC Silang-Amadeo",
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(403)
def forbidden(error):

    body = """

    <div class="card empty">

        <h1>
            403
        </h1>

        <h2>
            Access Denied
        </h2>

        <p>
            You do not have permission to access this page.
        </p>

        <a
            class="button"
            href="/"
        >
            Home
        </a>

    </div>

    """

    return render_page(
        "403",
        body,
    ), 403


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

        <p>
            The requested page could not be found.
        </p>

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


@app.errorhandler(413)
def too_large(error):

    body = """

    <div class="card empty">

        <h1>
            413
        </h1>

        <h2>
            File Too Large
        </h2>

        <p>
            The maximum upload size is 20 MB.
        </p>

        <a
            class="button"
            href="/"
        >
            Home
        </a>

    </div>

    """

    return render_page(
        "413",
        body,
    ), 413


# ============================================================
# SECURITY HEADERS
# ============================================================

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
