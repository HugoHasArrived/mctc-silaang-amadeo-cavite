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
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "mctc_court.db"

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = STATIC_DIR / "uploads"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER"
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    app.config["SESSION_COOKIE_SECURE"] = False


# ============================================================
# COURT INFORMATION
# ============================================================

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

COURT_SHORT = "MCTC Silang-Amadeo"

COURT_ADDRESS = (
    "PNP Bldg, Plaza Libertad, Poblacion 2, "
    "Silang, Cavite"
)

COURT_PHONE = "09284621305"

COURT_EMAIL = "mctc2sad000@judiciary.gov.ph"

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/"
    "?api=1&query="
    "PNP+Bldg+Plaza+Libertad+Poblacion+2+Silang+Cavite"
)

LOGO_FILENAME = "image0.png"


# ============================================================
# ALLOWED UPLOADS
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
# LANGUAGE
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
        "requirements": "Requirements",
        "bonds": "Bond Requirements",
        "clearance": "Clearance Requirements",
        "dashboard": "Staff Dashboard",
        "logout": "Log Out",
        "login": "Log In",
        "case": "Case",
        "cases": "Cases",
        "hearing": "Hearing",
        "hearings": "Hearings",
        "notices": "Notices",
        "save": "Save",
        "edit": "Edit",
        "delete": "Delete",
        "add": "Add",
        "view": "View",
        "cancel": "Cancel",
        "username": "Username",
        "password": "Password",
        "case_number": "Case Number",
        "last_name": "Last Name / Party",
        "parties": "Parties",
        "nature": "Nature",
        "status": "Status",
        "title": "Title",
        "description": "Description",
        "hearing_date": "Hearing Date",
        "hearing_time": "Hearing Time",
        "hearing_nature": "Nature of Hearing",
        "hearing_status": "Hearing Status",
        "courtroom": "Courtroom",
        "remarks": "Remarks",
        "search_case": "Search for a Case",
        "search_button": "Search Case",
        "how_search": "How to Search",
        "step_one": "Enter the complete case number.",
        "step_two": "Enter the last name of a party.",
        "step_three": "Both fields are required.",
        "step_four": "Click Search Case.",
        "no_results": (
            "No matching public case was found."
        ),
        "both_required": (
            "Please enter BOTH the case number and "
            "last name / party name."
        ),
        "welcome": "Welcome, Court Staff",
        "quick_actions": "Quick Actions",
        "manage_cases": "Manage Cases",
        "manage_calendar": "Manage Tuesday Calendar",
        "manage_notices": "Manage Notices",
        "manage_laws": "Manage Legal Resources",
        "manage_requirements": "Manage Requirements",
        "attachment": "Photo / Document",
        "open": "Open",
        "official_source": "Official Source",
        "google_maps": "Open Google Maps",
        "phone": "Telephone",
        "email": "Email Address",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. All rights reserved."
        ),
        "not_uploaded": "Not yet uploaded",
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
        "requirements": "Mga Kinakailangan",
        "bonds": "Mga Kinakailangan para sa Bonds",
        "clearance": "Mga Kinakailangan para sa Clearance",
        "dashboard": "Dashboard ng Staff",
        "logout": "Mag-Logout",
        "login": "Mag-Login",
        "case": "Kaso",
        "cases": "Mga Kaso",
        "hearing": "Pagdinig",
        "hearings": "Mga Pagdinig",
        "notices": "Mga Abiso",
        "save": "I-save",
        "edit": "I-edit",
        "delete": "Burahin",
        "add": "Magdagdag",
        "view": "Tingnan",
        "cancel": "Kanselahin",
        "username": "Username",
        "password": "Password",
        "case_number": "Numero ng Kaso",
        "last_name": "Apelyido / Partido",
        "parties": "Mga Partido",
        "nature": "Uri",
        "status": "Katayuan",
        "title": "Pamagat",
        "description": "Deskripsyon",
        "hearing_date": "Petsa ng Pagdinig",
        "hearing_time": "Oras ng Pagdinig",
        "hearing_nature": "Uri ng Pagdinig",
        "hearing_status": "Katayuan ng Pagdinig",
        "courtroom": "Silid ng Hukuman",
        "remarks": "Mga Tala",
        "search_case": "Maghanap ng Kaso",
        "search_button": "Maghanap",
        "how_search": "Paano Maghanap",
        "step_one": "Ilagay ang buong case number.",
        "step_two": "Ilagay ang apelyido ng isang partido.",
        "step_three": "Kinakailangan ang parehong field.",
        "step_four": "I-click ang Maghanap.",
        "no_results": (
            "Walang nakitang pampublikong kaso."
        ),
        "both_required": (
            "Ilagay ang PAREHONG case number at "
            "apelyido / pangalan ng partido."
        ),
        "welcome": (
            "Maligayang Pagdating, Kawani ng Hukuman"
        ),
        "quick_actions": "Mabilis na Aksyon",
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
        "attachment": "Larawan / Dokumento",
        "open": "Buksan",
        "official_source": "Opisyal na Source",
        "google_maps": "Buksan ang Google Maps",
        "phone": "Telepono",
        "email": "Email Address",
        "address": "Address",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. Lahat ng karapatan ay nakalaan."
        ),
        "not_uploaded": "Hindi pa naiu-upload",
    },
}


# ============================================================
# BASIC HELPERS
# ============================================================

def now():
    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def escape_html(value):
    return html.escape(
        str(value or ""),
        quote=True,
    )


def current_language():
    language = session.get(
        "language",
        "en",
    )

    if language not in TRANSLATIONS:
        language = "en"

    return language


def T(key):
    language = current_language()

    return TRANSLATIONS[language].get(
        key,
        TRANSLATIONS["en"].get(
            key,
            key,
        ),
    )


# ============================================================
# DATABASE HELPER
# ============================================================

def get_db():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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

    # --------------------------------------------------------
    # Requirement defaults
    # --------------------------------------------------------

    defaults = [
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

    for item in defaults:

        exists = db.execute(
            """
            SELECT id
            FROM requirements
            WHERE category = ?
            """,
            (item[0],),
        ).fetchone()

        if exists is None:

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
                    now(),
                ),
            )

    # --------------------------------------------------------
    # Create staff account from Render environment variables.
    # --------------------------------------------------------

    username = os.environ.get(
        "STAFF_USERNAME"
    )

    password = os.environ.get(
        "STAFF_PASSWORD"
    )

    if username and password:

        staff_exists = db.execute(
            """
            SELECT id
            FROM staff
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if staff_exists is None:

            db.execute(
                """
                INSERT INTO staff
                (
                    username,
                    password_hash,
                    display_name,
                    role,
                    active,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    generate_password_hash(
                        password
                    ),
                    "Court Staff",
                    "staff",
                    1,
                    now(),
                ),
            )

    db.commit()

    db.close()


# ============================================================
# DO THIS BEFORE ROUTES
# ============================================================

init_database()


# ============================================================
# STAFF AUTHENTICATION DECORATOR
# ============================================================
#
# This is defined BEFORE any route uses:
#
#     @staff_required
#
# This fixes your NameError.
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
                T("login_required"),
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


# ============================================================
# AUDIT LOG
# ============================================================

def audit(
    action,
    target="",
):

    username = session.get(
        "staff_username",
        "system",
    )

    db = get_db()

    db.execute(
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

    db.commit()

    db.close()


# ============================================================
# FILE UPLOAD
# ============================================================

def save_upload(upload):

    if not upload:

        return None

    if not upload.filename:

        return None

    safe_name = secure_filename(
        upload.filename
    )

    if not safe_name:

        return None

    extension = Path(
        safe_name
    ).suffix.lower().replace(
        ".",
        "",
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "That file type is not allowed."
        )

    generated = (
        secrets.token_hex(12)
        + "_"
        + safe_name
    )

    destination = (
        UPLOAD_DIR
        / generated
    )

    upload.save(
        destination
    )

    return generated


# ============================================================
# PAGE STYLES
# ============================================================

STYLE = r"""
:root {

    --purple-950: #28063b;
    --purple-900: #3b0764;
    --purple-800: #4c1d95;
    --purple-700: #6d28d9;
    --purple-600: #7c3aed;
    --purple-500: #8b5cf6;
    --purple-300: #c4b5fd;
    --purple-100: #ede9fe;

    --background: #f8f6fb;
    --surface: #ffffff;
    --surface-2: #f3eef8;

    --text: #211426;
    --muted: #65566e;
    --border: #ded2e6;

    --danger: #a61b3c;
    --success: #176b37;
    --warning: #8b5800;

    --shadow:
        0 10px 30px
        rgba(53, 18, 73, .08);
}

body.dark {

    --background: #130e18;
    --surface: #211826;
    --surface-2: #2c2033;

    --text: #fbf6ff;
    --muted: #d3c5da;
    --border: #4c3a55;

    --purple-100: #362541;

    --danger: #ffb4c7;
    --success: #aee8bb;
    --warning: #ffdb9a;

    --shadow:
        0 12px 35px
        rgba(0,0,0,.32);
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

    background:
        var(--background);

    color:
        var(--text);

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height: 1.65;
}

a {

    color:
        var(--purple-700);

    text-decoration:
        none;
}

body.dark a {
    color:
        var(--purple-300);
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

    background:
        linear-gradient(
            135deg,
            var(--purple-950),
            var(--purple-800),
            var(--purple-600)
        );

    color:
        white;

    box-shadow:
        0 7px 25px
        rgba(37, 7, 53, .25);
}

.header-inner {

    width:
        min(
            1200px,
            94%
        );

    min-height:
        78px;

    margin:
        auto;

    padding:
        12px 0;

    display:
        flex;

    align-items:
        center;

    gap:
        16px;

    flex-wrap:
        wrap;
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

    flex-shrink:
        0;
}

.brand {

    flex:
        1;

    min-width:
        230px;

    color:
        white;
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

    gap:
        5px;

    flex-wrap:
        wrap;
}

.nav a,
.nav button {

    color:
        white;

    border:
        0;

    background:
        transparent;

    padding:
        8px 10px;

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
}

.nav a:hover,
.nav button:hover {

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
        60px 25px;

    text-align:
        center;

    color:
        white;

    border-radius:
        25px;

    background:
        linear-gradient(
            135deg,
            var(--purple-950),
            var(--purple-700),
            var(--purple-500)
        );

    box-shadow:
        0 15px 35px
        rgba(62, 19, 84, .20);
}

.hero h1 {

    max-width:
        950px;

    margin:
        15px auto;

    font-size:
        clamp(
            30px,
            5vw,
            57px
        );

    line-height:
        1.05;
}

.hero p {

    max-width:
        760px;

    margin:
        15px auto;

    color:
        rgba(
            255,
            255,
            255,
            .91
        );
}

.hero-logo {

    width:
        155px;

    height:
        155px;

    display:
        block;

    object-fit:
        contain;

    margin:
        0 auto 20px;
}

.card {

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        18px;

    box-shadow:
        var(--shadow);

    padding:
        23px;

    margin:
        18px 0;
}

.grid {

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
}

.two {

    display:
        grid;

    grid-template-columns:
        1fr 1fr;

    gap:
        15px;
}

label {

    display:
        block;

    font-weight:
        800;

    margin:
        12px 0 5px;
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
        125px;

    resize:
        vertical;
}

input:focus,
textarea:focus,
select:focus {

    outline:
        3px solid
        rgba(
            124,
            58,
            237,
            .20
        );

    border-color:
        var(--purple-600);
}

.button,
button {

    display:
        inline-block;

    border:
        0;

    border-radius:
        10px;

    background:
        var(--purple-700);

    color:
        white;

    padding:
        11px 16px;

    font-weight:
        800;

    cursor:
        pointer;

    text-decoration:
        none;
}

.button:hover,
button:hover {

    background:
        var(--purple-800);

    color:
        white;

    text-decoration:
        none;
}

.secondary {

    background:
        var(--surface-2);

    color:
        var(--text);
}

.danger {

    background:
        var(--danger);

    color:
        white;
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

.status {

    display:
        inline-block;

    padding:
        4px 10px;

    border-radius:
        999px;

    background:
        var(--purple-100);

    color:
        var(--purple-800);

    font-size:
        12px;

    font-weight:
        900;
}

body.dark .status {

    color:
        #eadbff;
}

.notice {

    background:
        var(--surface-2);

    border:
        1px solid
        var(--border);

    border-left:
        5px solid
        var(--purple-600);

    border-radius:
        11px;

    padding:
        15px;

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

    border-bottom:
        1px solid
        var(--border);

    vertical-align:
        top;
}

th {

    background:
        var(--surface-2);
}

.empty {

    text-align:
        center;

    padding:
        45px 10px;

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
        32px 15px;
}

.login-box {

    max-width:
        510px;

    margin:
        45px auto;
}

.instructions {

    background:
        var(--purple-100);

    color:
        var(--purple-900);

    border:
        1px solid
        var(--border);

    padding:
        18px;

    border-radius:
        13px;

    margin:
        15px 0;
}

body.dark .instructions {

    color:
        #efe2ff;
}

.stat {

    text-align:
        center;

    padding:
        25px;

    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        17px;

    box-shadow:
        var(--shadow);
}

.stat-number {

    display:
        block;

    font-size:
        38px;

    font-weight:
        950;

    color:
        var(--purple-600);
}

.flex {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        15px;

    flex-wrap:
        wrap;
}

@media(max-width:850px) {

    .header-inner {

        align-items:
            flex-start;

        flex-direction:
            column;
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
            36px;
    }
}
"""


# ============================================================
# PAGE RENDERER
# ============================================================

def render_page(
    title,
    body,
):

    language = current_language()

    theme = session.get(
        "theme",
        "light",
    )

    logged_in = bool(
        session.get(
            "staff_logged_in",
            False,
        )
    )

    if logged_in:

        staff_navigation = f"""

        <a
            href="{url_for('staff_dashboard')}"
        >
            {T("dashboard")}
        </a>

        <a
            href="{url_for('staff_cases')}"
        >
            {T("cases")}
        </a>

        <a
            href="{url_for('staff_calendar')}"
        >
            {T("calendar")}
        </a>

        <a
            href="{url_for('staff_notices')}"
        >
            {T("notices")}
        </a>

        <a
            href="{url_for('staff_laws')}"
        >
            {T("laws")}
        </a>

        <a
            href="{url_for('staff_requirements')}"
        >
            {T("requirements")}
        </a>

        <form
            method="post"
            action="{url_for('logout')}"
            style="display:inline"
        >

            <button
                type="submit"
                class="nav-button"
                onclick="
                    return confirm(
                        'Log out now?'
                    );
                "
            >
                {T("logout")}
            </button>

        </form>

        """

    else:

        staff_navigation = f"""

        <a
            href="{url_for('staff_login')}"
        >
            {T("staff")}
        </a>

        """

    language_link = (
        "fil"
        if language == "en"
        else "en"
    )

    language_name = (
        "Filipino"
        if language == "en"
        else "English"
    )

    next_theme = (
        "dark"
        if theme == "light"
        else "light"
    )

    theme_name = (
        "Dark Mode"
        if theme == "light"
        else "Light Mode"
    )

    full_html = f"""
<!DOCTYPE html>

<html
    lang="{escape_html(language)}"
>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="description"
    content="Court Information Portal"
/>

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
    style="color:white;text-decoration:none"
>

<img
    class="logo"
    src="{url_for(
        'static',
        filename=LOGO_FILENAME
    )}"
    alt="Official court logo"
>

</a>

<div class="brand">

<strong>
{escape_html(COURT_NAME)}
</strong>

<small>
Official Court Information Portal
</small>

</div>

<nav class="nav">

<a
    href="{url_for('home')}"
>
{T("home")}
</a>

<a
    href="{url_for('about')}"
>
{T("about")}
</a>

<a
    href="{url_for('news')}"
>
{T("news")}
</a>

<a
    href="{url_for('contact')}"
>
{T("contact")}
</a>

{staff_navigation}

<a
    href="{url_for(
        'change_language',
        language=language_link
    )}"
>
{language_name}
</a>

<a
    href="{url_for(
        'change_theme',
        theme=next_theme
    )}"
>
{theme_name}
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
{escape_html(COURT_PHONE)}
<br>
{escape_html(COURT_EMAIL)}
</p>

<p>

<a
    href="{GOOGLE_MAPS_URL}"
    target="_blank"
    rel="noopener noreferrer"
>
{T("google_maps")}
</a>

</p>

<p>
{T("copyright")}
</p>

</footer>

</body>

</html>
"""

    return full_html


def render_flash_messages():

    messages = ""

    for category, message in flash_messages():

        messages += f"""

        <div
            class="notice {escape_html(category)}"
        >
            {escape_html(message)}
        </div>

        """

    return messages


def flash_messages():

    from flask import get_flashed_messages

    return get_flashed_messages(
        with_categories=True
    )


# ============================================================
# LANGUAGE ROUTES
# ============================================================

@app.route(
    "/language/<language>"
)
def change_language(language):

    if language not in {
        "en",
        "fil",
    }:

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

    if theme not in {
        "light",
        "dark",
    }:

        theme = "light"

    session["theme"] = theme

    return redirect(
        request.referrer
        or url_for("home")
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

    notices_html = ""

    for notice in notices:

        if current_language() == "fil":

            title = notice["title_fil"]

            body = notice["body_fil"]

        else:

            title = notice["title_en"]

            body = notice["body_en"]

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
                {T("open")}
            </a>

            """

        notices_html += f"""

        <div class="notice">

            <h3>
                {escape_html(title)}
            </h3>

            <p>
                {escape_html(body)}
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
            alt="Court logo"
        >

        <h1>
            {escape_html(COURT_NAME)}
        </h1>

        <p>
            Search approved public case information,
            view the Tuesday calendar, and read official
            court announcements.
        </p>

        <div class="actions"
             style="justify-content:center;">

            <a
                class="button"
                href="{url_for('search_cases')}"
            >
                🔎
                {T("search")}
            </a>

            <a
                class="button secondary"
                href="{url_for('public_calendar')}"
            >
                📅
                {T("calendar")}
            </a>

        </div>

    </section>


    <section class="grid">

        <div class="card">

            <h2>
                🔎
                {T("search_case")}
            </h2>

            <p>
                {T("both_required")}
            </p>

            <a
                class="button"
                href="{url_for('search_cases')}"
            >
                {T("search_button")}
            </a>

        </div>


        <div class="card">

            <h2>
                📅
                {T("calendar")}
            </h2>

            <p>
                View the published Tuesday court calendar.
            </p>

            <a
                class="button"
                href="{url_for('public_calendar')}"
            >
                {T("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                📢
                {T("news")}
            </h2>

            <p>
                View official announcements and
                approved attachments.
            </p>

            <a
                class="button"
                href="{url_for('news')}"
            >
                {T("view")}
            </a>

        </div>


        <div class="card">

            <h2>
                ⚖️
                {T("laws")}
            </h2>

            <p>
                View legal-resource links and
                approved reference documents.
            </p>

            <a
                class="button"
                href="{url_for('laws')}"
            >
                {T("view")}
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            📢
            {T("news")}
        </h2>

        {notices_html or '<p class="small">No announcements yet.</p>'}

    </section>


    <section class="card">

        <h2>
            ⚠️
            {T("suspension")}
        </h2>

        <p>
            A hearing should not be assumed to be
            suspended, cancelled, or postponed unless
            an official court notice or authorized
            announcement confirms it.
        </p>

        <a
            class="button secondary"
            href="{url_for('news')}"
        >
            {T("news")}
        </a>

    </section>

    """

    return render_page(
        T("home"),
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
            {T("about")}
        </h1>

        <h2>
            {escape_html(COURT_NAME)}
        </h2>

        <p>
            This portal provides approved public
            information about the court, case
            information, public announcements,
            and the Tuesday calendar.
        </p>

        <div class="notice warning">

            <strong>
                Important
            </strong>

            <p>
                Information shown online does not replace
                official court records, orders, notices,
                or certified documents.
            </p>

        </div>

    </div>

    """

    return render_page(
        T("about"),
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
            {T("contact")}
        </h1>

        <h2>
            {escape_html(COURT_NAME)}
        </h2>

        <p>
            <strong>
                {T("address")}:
            </strong>
            <br>
            {escape_html(COURT_ADDRESS)}
        </p>

        <p>
            <strong>
                {T("phone")}:
            </strong>
            <br>
            <a
                href="tel:{COURT_PHONE}"
            >
                {escape_html(COURT_PHONE)}
            </a>
        </p>

        <p>
            <strong>
                {T("email")}:
            </strong>
            <br>
            <a
                href="mailto:{COURT_EMAIL}"
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
            {T("google_maps")}
        </a>

    </div>

    """

    return render_page(
        T("contact"),
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
            {T("news")}
        </h1>

        <p>
            Official information published by
            authorized staff.
        </p>

    </div>

    """

    for notice in notices:

        if current_language() == "fil":

            title = notice["title_fil"]

            message = notice["body_fil"]

        else:

            title = notice["title_en"]

            message = notice["body_en"]

        attachment_html = ""

        if notice["attachment"]:

            attachment_html = f"""

            <p>

                <a
                    class="button secondary"
                    href="{url_for(
                        'uploaded_file',
                        filename=notice['attachment']
                    )}"
                >
                    📎
                    {T("open")}
                </a>

            </p>

            """

        body += f"""

        <article class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(message)}
            </p>

            {attachment_html}

            <p class="small">
                {escape_html(
                    notice["created_at"]
                )}
            </p>

        </article>

        """

    if not notices:

        body += """

        <div class="card empty">

            No official announcements
            have been published yet.

        </div>

        """

    return render_page(
        T("news"),
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

    number = request.values.get(
        "case_number",
        "",
    ).strip()

    last_name = request.values.get(
        "last_name",
        "",
    ).strip()

    result = None

    attempted = (
        request.method == "POST"
        or bool(number)
        or bool(last_name)
    )

    if request.method == "POST":

        # BOTH fields required.
        if not number or not last_name:

            flash(
                T("both_required"),
                "danger",
            )

        else:

            db = get_db()

            result = db.execute(
                """
                SELECT *
                FROM cases
                WHERE
                    lower(case_number)
                    = lower(?)
                AND
                    lower(last_name)
                    = lower(?)
                LIMIT 1
                """,
                (
                    number,
                    last_name,
                ),
            ).fetchone()

            db.close()

            if result is None:

                flash(
                    T("no_results"),
                    "warning",
                )

    body = f"""

    <div class="card">

        <h1>
            🔎
            {T("search_case")}
        </h1>


        <div class="instructions">

            <h3>
                {T("how_search")}
            </h3>

            <ol>

                <li>
                    {T("step_one")}
                </li>

                <li>
                    {T("step_two")}
                </li>

                <li>
                    {T("step_three")}
                </li>

                <li>
                    {T("step_four")}
                </li>

            </ol>

        </div>


        <form method="post">

            <label>
                {T("case_number")}
            </label>

            <input
                name="case_number"
                value="{escape_html(number)}"
                placeholder="Example: MCTC-2026-001"
                required
                autocomplete="off"
            >


            <label>
                {T("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(last_name)}"
                placeholder="Example: DELA CRUZ"
                required
                autocomplete="off"
            >


            <div class="actions">

                <button
                    type="submit"
                >
                    🔎
                    {T("search_button")}
                </button>

            </div>

        </form>

    </div>

    """

    if result:

        body += f"""

        <div class="card">

            <span class="status">
                {escape_html(
                    result["status"]
                )}
            </span>

            <h2>
                {escape_html(
                    result["case_number"]
                )}
            </h2>

            <p>

                <strong>
                    {T("parties")}:
                </strong>

                {escape_html(
                    result["parties"]
                )}

            </p>

            <p>

                <strong>
                    {T("nature")}:
                </strong>

                {escape_html(
                    result["case_type"]
                )}

            </p>

            <p>
                {escape_html(
                    result["public_description"]
                )}
            </p>

            <a
                class="button"
                href="{url_for(
                    'public_case',
                    case_id=result['id']
                )}"
            >
                {T("view")}
            </a>

        </div>

        """

    return render_page(
        T("search"),
        body,
    )


# ============================================================
# PUBLIC CASE VIEW
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
                    {T("hearing_time")}:
                </strong>

                {escape_html(
                    hearing["hearing_time"]
                )}
            </p>

            <p>
                <strong>
                    {T("hearing_nature")}:
                </strong>

                {escape_html(
                    hearing["hearing_nature"]
                )}
            </p>

            <p>
                <strong>
                    {T("hearing_status")}:
                </strong>

                <span class="status">
                    {escape_html(
                        hearing["hearing_status"]
                    )}
                </span>

            </p>

            <p>
                <strong>
                    {T("courtroom")}:
                </strong>

                {escape_html(
                    hearing["courtroom"]
                )}

            </p>

        </div>

        """

    if not hearing_html:

        hearing_html = """

        <p class="small">
            No published hearing information.
        </p>

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
                {T("parties")}:
            </strong>

            {escape_html(
                case["parties"]
            )}
        </p>

        <p>
            <strong>
                {T("nature")}:
            </strong>

            {escape_html(
                case["case_type"]
            )}
        </p>

        <hr>

        <p>
            {escape_html(
                case["public_description"]
            )}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {T("hearings")}
        </h2>

        {hearing_html}

    </div>

    """

    return render_page(
        T("case"),
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

    body = f"""

    <div class="card">

        <h1>
            📅
            {T("calendar")}
        </h1>

        <p>
            This is the publicly published
            Tuesday court calendar.
        </p>

        <div class="notice warning">

            Hearing information may change.
            Please verify important information
            with the court.

        </div>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        {T("hearing_date")}
                    </th>

                    <th>
                        {T("hearing_time")}
                    </th>

                    <th>
                        {T("case_number")}
                    </th>

                    <th>
                        {T("parties")}
                    </th>

                    <th>
                        {T("hearing_nature")}
                    </th>

                    <th>
                        {T("hearing_status")}
                    </th>

                    <th>
                        {T("courtroom")}
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
        T("calendar"),
        body,
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

    body = f"""

    <div class="card">

        <h1>
            📄
            {T("requirements")}
        </h1>

        <p>
            Requirements shown here are published
            by authorized staff.
        </p>

    </div>

    """

    for row in rows:

        if current_language() == "fil":

            heading = row["title_fil"]

            description = (
                row["description_fil"]
                or T("not_uploaded")
            )

        else:

            heading = row["title_en"]

            description = (
                row["description_en"]
                or T("not_uploaded")
            )

        file_html = ""

        if row["file_name"]:

            file_html = f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=row['file_name']
                )}"
            >
                {T("open")}
            </a>

            """

        body += f"""

        <div class="card">

            <h2>
                {escape_html(
                    heading
                )}
            </h2>

            <p>
                {escape_html(
                    description
                )}
            </p>

            {file_html}

        </div>

        """

    return render_page(
        T("requirements"),
        body,
    )


# ============================================================
# LAWS / DECISIONS / RULES
# ============================================================

@app.route(
    "/laws"
)
def laws():

    db = get_db()

    resources = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY
            category,
            created_at DESC
        """
    ).fetchall()

    db.close()

    body = f"""

    <div class="card">

        <h1>
            ⚖️
            {T("laws")}
        </h1>

        <p>
            This section can contain references to
            Philippine laws, Supreme Court decisions,
            rules, issuances, and other official legal
            resources added by authorized staff.
        </p>

        <div class="notice warning">

            Always verify the current official text
            or status of a legal authority before
            relying on it.

        </div>

    </div>

    """

    for row in resources:

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
                {T("official_source")}
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
                {T("open")}
            </a>

            """

        body += """

        </div>

        """

    if not resources:

        body += """

        <div class="card empty">

            No legal resources have been published yet.

        </div>

        """

    return render_page(
        T("laws"),
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

        username = (
            request.form
            .get(
                "username",
                "",
            )
            .strip()
        )

        password = request.form.get(
            "password",
            "",
        )

        # Render environment-variable account
        configured_username = os.environ.get(
            "STAFF_USERNAME"
        )

        configured_password = os.environ.get(
            "STAFF_PASSWORD"
        )

        if (
            configured_username
            and configured_password
            and secrets.compare_digest(
                username,
                configured_username,
            )
            and secrets.compare_digest(
                password,
                configured_password,
            )
        ):

            session.clear()

            session["staff_logged_in"] = True

            session["staff_username"] = username

            session["staff_role"] = "staff"

            return redirect(
                url_for(
                    "staff_dashboard"
                )
            )

        # Database account fallback
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

            session["staff_username"] = (
                staff["username"]
            )

            session["staff_role"] = (
                staff["role"]
            )

            return redirect(
                url_for(
                    "staff_dashboard"
                )
            )

        flash(
            T("invalid_login"),
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
            {T("staff")}
        </h1>

        <p class="small">
            Authorized court personnel only.
        </p>

        <form
            method="post"
            autocomplete="off"
        >

            <label>
                {T("username")}
            </label>

            <input
                type="text"
                name="username"
                autocomplete="username"
                required
            >


            <label>
                {T("password")}
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
                {T("login")}
            </button>

        </form>

        <div class="notice">

            Your staff credentials are not displayed
            on public pages.

        </div>

    </div>

    """

    return render_page(
        T("staff"),
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
#
# Notice:
# Hearings are deliberately NOT a separate dashboard item.
# The Tuesday calendar is the main schedule-management area.
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
        """
        SELECT COUNT(*)
        FROM cases
        """
    ).fetchone()[0]

    notice_count = db.execute(
        """
        SELECT COUNT(*)
        FROM notices
        """
    ).fetchone()[0]

    calendar_count = db.execute(
        """
        SELECT COUNT(*)
        FROM tuesday_calendar
        """
    ).fetchone()[0]

    law_count = db.execute(
        """
        SELECT COUNT(*)
        FROM legal_resources
        """
    ).fetchone()[0]

    db.close()

    body = f"""

    <section class="hero">

        <h1>
            {T("welcome")}
        </h1>

        <p>
            Manage court information from one place.
        </p>

    </section>


    <section class="grid">

        <div class="stat">

            <span class="stat-number">
                {case_count}
            </span>

            <strong>
                {T("cases")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {notice_count}
            </span>

            <strong>
                {T("notices")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {calendar_count}
            </span>

            <strong>
                {T("calendar")}
            </strong>

        </div>


        <div class="stat">

            <span class="stat-number">
                {law_count}
            </span>

            <strong>
                {T("laws")}
            </strong>

        </div>

    </section>


    <section class="card">

        <h2>
            ⚡
            {T("quick_actions")}
        </h2>

        <div class="grid">

            <a
                class="card"
                href="{url_for(
                    'staff_cases'
                )}"
            >

                <h3>
                    📋
                    {T("manage_cases")}
                </h3>

                <p class="small">
                    Add, edit or delete case records.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_calendar'
                )}"
            >

                <h3>
                    📅
                    {T("manage_calendar")}
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

                <h3>
                    📢
                    {T("manage_notices")}
                </h3>

                <p class="small">
                    Upload notices with photos
                    or documents.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_laws'
                )}"
            >

                <h3>
                    ⚖️
                    {T("manage_laws")}
                </h3>

                <p class="small">
                    Manage laws, decisions
                    and rules.
                </p>

            </a>


            <a
                class="card"
                href="{url_for(
                    'staff_requirements'
                )}"
            >

                <h3>
                    📄
                    {T("manage_requirements")}
                </h3>

                <p class="small">
                    Manage bond and clearance
                    requirements.
                </p>

            </a>

        </div>

    </section>

    """

    return render_page(
        T("dashboard"),
        body,
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
        ORDER BY
            updated_at DESC
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
                <span class="small">
                    {escape_html(
                        case["case_title"]
                    )}
                </span>
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
                        {T("edit")}
                    </a>

                    <a
                        class="button secondary"
                        href="{url_for(
                            'staff_hearing',
                            case_id=case['id']
                        )}"
                    >
                        {T("hearing")}
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
                            {T("delete")}
                        </button>

                    </form>

                </div>

            </td>

        </tr>

        """

    if not rows:

        rows = """

        <tr>

            <td
                colspan="5"
                class="empty"
            >
                No cases found.
            </td>

        </tr>

        """

    body = f"""

    <div class="flex">

        <h1>
            {T("manage_cases")}
        </h1>

        <a
            class="button"
            href="{url_for(
                'staff_add_case'
            )}"
        >
            ➕
            {T("add_case")}
        </a>

    </div>


    <div class="card">

        <div class="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>
                            {T("case_number")}
                        </th>

                        <th>
                            {T("parties")}
                        </th>

                        <th>
                            Type
                        </th>

                        <th>
                            {T("status")}
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

    </div>

    """

    return render_page(
        T("cases"),
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
                (
                    "Case number, last name, "
                    "parties, and case title "
                    "are required."
                ),
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
            {T("add_case")}
        </h1>

        <form method="post">

            <label>
                {T("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {T("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {T("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                Case Title
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
                {T("status")}
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
                {T("public_information")}
            </label>

            <textarea
                name="public_description"
            ></textarea>


            <label>
                {T("private_notes")}
            </label>

            <textarea
                name="internal_notes"
            ></textarea>


            <div class="actions">

                <button
                    type="submit"
                >
                    {T("save")}
                </button>

                <a
                    class="button secondary"
                    href="{url_for(
                        'staff_cases'
                    )}"
                >
                    {T("cancel")}
                </a>

            </div>

        </form>

    </div>

    """

    return render_page(
        T("add_case"),
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

    body = f"""

    <div class="card">

        <h1>
            ✏️
            {T("edit")}
            {T("case")}
        </h1>

        <form method="post">

            <label>
                {T("case_number")}
            </label>

            <input
                value="{escape_html(
                    case["case_number"]
                )}"
                disabled
            >


            <label>
                {T("last_name")}
            </label>

            <input
                name="last_name"
                value="{escape_html(
                    case["last_name"]
                )}"
                required
            >


            <label>
                {T("parties")}
            </label>

            <input
                name="parties"
                value="{escape_html(
                    case["parties"]
                )}"
                required
            >


            <label>
                Case Title
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
                {T("status")}
            </label>

            <select name="status">

                {

                    "".join(
                        (
                            f'<option '
                            f'{"selected" if value == case["status"] else ""}'
                            f'>{value}</option>'
                        )
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
                Public Information
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

                <button
                    type="submit"
                >
                    {T("save")}
                </button>

                <a
                    class="button secondary"
                    href="{url_for(
                        'staff_cases'
                    )}"
                >
                    {T("cancel")}
                </a>

            </div>

        </form>

    </div>

    """

    return render_page(
        T("edit"),
        body,
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

        date_value = request.form.get(
            "hearing_date",
            "",
        ).strip()

        time_value = request.form.get(
            "hearing_time",
            "",
        ).strip()

        nature_value = request.form.get(
            "hearing_nature",
            "",
        ).strip()

        status_value = request.form.get(
            "hearing_status",
            "Scheduled",
        ).strip()

        room_value = request.form.get(
            "courtroom",
            "",
        ).strip()

        remarks_value = request.form.get(
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
                    date_value,
                    time_value,
                    nature_value,
                    status_value,
                    room_value,
                    remarks_value,
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
                    date_value,
                    time_value,
                    nature_value,
                    status_value,
                    room_value,
                    remarks_value,
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

    current_time_value = (
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

        <option
            {selected}
        >
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

        <option
            {selected}
        >
            {escape_html(value)}
        </option>

        """

    body = f"""

    <div class="card">

        <h1>
            📅
            {T("hearing")}
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
                {T("hearing_date")}
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
                {T("hearing_time")}
            </label>

            <input
                type="time"
                name="hearing_time"
                value="{escape_html(
                    current_time_value
                )}"
            >


            <label>
                {T("hearing_nature")}
            </label>

            <select
                name="hearing_nature"
            >

                {nature_options}

            </select>


            <label>
                {T("hearing_status")}
            </label>

            <select
                name="hearing_status"
            >

                {status_options}

            </select>


            <label>
                {T("courtroom")}
            </label>

            <input
                name="courtroom"
                value="{escape_html(
                    current_room
                )}"
            >


            <label>
                {T("remarks")}
            </label>

            <textarea
                name="remarks"
            >{escape_html(
                current_remarks
            )}</textarea>


            <button
                type="submit"
            >
                {T("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        T("hearing"),
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

    rows = ""

    for entry in entries:

        edit_form = f"""

        <form
            method="post"
            action="{url_for(
                'edit_calendar',
                entry_id=entry['id']
            )}"
        >

            <input
                type="date"
                name="calendar_date"
                value="{escape_html(
                    entry["calendar_date"]
                )}"
                required
            >

            <input
                type="time"
                name="calendar_time"
                value="{escape_html(
                    entry["calendar_time"]
                )}"
                required
            >

            <input
                name="case_number"
                value="{escape_html(
                    entry["case_number"]
                )}"
                required
            >

            <input
                name="last_name"
                value="{escape_html(
                    entry["last_name"]
                )}"
                required
            >

            <input
                name="parties"
                value="{escape_html(
                    entry["parties"]
                )}"
                required
            >

            <input
                name="hearing_nature"
                value="{escape_html(
                    entry["hearing_nature"]
                )}"
                required
            >

            <select
                name="hearing_status"
            >

                {
                    "".join(
                        (
                            f'<option '
                            f'{"selected" if value == entry["hearing_status"] else ""}'
                            f'>{value}</option>'
                        )
                        for value
                        in [
                            "Scheduled",
                            "Ongoing",
                            "Completed",
                            "Reset",
                            "Postponed",
                            "Cancelled",
                        ]
                    )
                }

            </select>


            <input
                name="courtroom"
                value="{escape_html(
                    entry["courtroom"]
                )}"
                placeholder="Courtroom"
            >


            <input
                name="remarks"
                value="{escape_html(
                    entry["remarks"]
                )}"
                placeholder="Remarks"
            >

            <label>

                <input
                    type="checkbox"
                    name="public_visible"
                    style="width:auto"
                    {"checked" if entry["public_visible"] else ""}
                >

                Publish

            </label>

            <button
                type="submit"
            >
                {T("save")}
            </button>

        </form>

        <form
            method="post"
            action="{url_for(
                'delete_calendar',
                entry_id=entry['id']
            )}"
            onsubmit="
                return confirm(
                    'Delete this Tuesday calendar entry?'
                );
            "
        >

            <button
                type="submit"
                class="danger"
            >
                {T("delete")}
            </button>

        </form>

        """

        rows += f"""

        <tr>

            <td colspan="8">

                {edit_form}

            </td>

        </tr>

        """

    body = f"""

    <div class="card">

        <h1>
            📅
            {T("manage_calendar")}
        </h1>

        <p>
            Add and edit the Tuesday court calendar.
            Civilian users see only entries marked
            for public publication.
        </p>

    </div>


    <div class="card">

        <h2>
            Add Tuesday Entry
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
                {T("case_number")}
            </label>

            <input
                name="case_number"
                required
            >


            <label>
                {T("last_name")}
            </label>

            <input
                name="last_name"
                required
            >


            <label>
                {T("parties")}
            </label>

            <input
                name="parties"
                required
            >


            <label>
                {T("hearing_nature")}
            </label>

            <input
                name="hearing_nature"
                placeholder="
                Initial Hearing /
                Arraignment /
                Pre-Trial /
                Trial /
                Other
                "
                required
            >


            <label>
                {T("hearing_status")}
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
                {T("courtroom")}
            </label>

            <input
                name="courtroom"
            >


            <label>
                {T("remarks")}
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


            <button
                type="submit"
            >
                {T("add")}
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            Existing Tuesday Entries
        </h2>

        <div class="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>
                            Entry
                        </th>

                    </tr>

                </thead>

                <tbody>

                    {rows or '''
                    <tr>
                        <td class="empty">
                            No Tuesday entries yet.
                        </td>
                    </tr>
                    '''}

                </tbody>

            </table>

        </div>

    </div>

    """

    return render_page(
        T("calendar"),
        body,
    )


@app.post(
    "/staff/calendar/add"
)
@staff_required
def add_calendar():

    calendar_date = request.form.get(
        "calendar_date",
        "",
    ).strip()

    calendar_time = request.form.get(
        "calendar_time",
        "",
    ).strip()

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

    public_visible = int(
        bool(
            request.form.get(
                "public_visible"
            )
        )
    )

    if not all(
        [
            calendar_date,
            calendar_time,
            case_number,
            last_name,
            parties,
            hearing_nature,
        ]
    ):

        flash(
            "Please complete all required calendar fields.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_calendar"
            )
        )

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
            now(),
            now(),
        ),
    )

    db.commit()

    db.close()

    audit(
        "calendar_created",
        case_number,
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
        str(entry_id),
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

    audit(
        "calendar_deleted",
        str(entry_id),
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

    items = ""

    for notice in notices:

        title = (
            notice["title_fil"]
            if current_language() == "fil"
            else notice["title_en"]
        )

        items += f"""

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

            items += f"""

            <p>

                <a
                    class="button secondary"
                    href="{url_for(
                        'uploaded_file',
                        filename=notice['attachment']
                    )}"
                >
                    📎
                    {T("open")}
                </a>

            </p>

            """

        items += f"""

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

                <button
                    type="submit"
                    class="danger"
                >
                    {T("delete")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            📢
            {T("manage_notices")}
        </h1>

        <form
            method="post"
            action="{url_for(
                'add_notice'
            )}"
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
                {T("attachment")}
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
                {T("upload")}
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            {T("notices")}
        </h2>

        {items or '<p class="empty">No notices yet.</p>'}

    </div>

    """

    return render_page(
        T("notices"),
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

    if (
        not title_en
        or not title_fil
        or not body_en
        or not body_fil
    ):

        flash(
            "All notice fields are required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_notices"
            )
        )

    try:

        filename = save_upload(
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

    original = None

    uploaded = request.files.get(
        "attachment"
    )

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
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
        ),
    )

    db.commit()

    db.close()

    audit(
        "notice_created",
        title_en,
    )

    flash(
        "Notice published successfully.",
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
        str(notice_id),
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

    resources = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    items = ""

    for item in resources:

        items += f"""

        <div class="notice">

            <span class="status">
                {escape_html(
                    item["category"]
                )}
            </span>

            <h3>
                {escape_html(
                    item["title"]
                )}
            </h3>

            <p>
                {escape_html(
                    item["description"]
                )}
            </p>

        """

        if item["source_url"]:

            items += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    item["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {T("official_source")}
            </a>

            """

        if item["file_name"]:

            items += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=item['file_name']
                )}"
            >
                {T("open")}
            </a>

            """

        items += f"""

            <form
                method="post"
                action="{url_for(
                    'delete_law',
                    law_id=item['id']
                )}"
                style="display:inline"
                onsubmit="
                    return confirm(
                        'Delete this legal resource?'
                    );
                "
            >

                <button
                    type="submit"
                    class="danger"
                >
                    {T("delete")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            ⚖️
            {T("manage_laws")}
        </h1>

        <p>
            Add official references to Philippine
            laws, Supreme Court decisions, rules,
            issuances, and other legal resources.
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


            <button
                type="submit"
            >
                {T("add")}
            </button>

        </form>

    </div>


    <div class="card">

        {items or '<p class="empty">No legal resources yet.</p>'}

    </div>

    """

    return render_page(
        T("laws"),
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

    if not category or not title:

        flash(
            "Category and title are required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_laws"
            )
        )

    try:

        filename = save_upload(
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

    original = None

    uploaded = request.files.get(
        "file"
    )

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
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
            now(),
            now(),
        ),
    )

    db.commit()

    db.close()

    audit(
        "law_added",
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

        title = (
            row["title_fil"]
            if current_language() == "fil"
            else row["title_en"]
        )

        description = (
            row["description_fil"]
            if current_language() == "fil"
            else row["description_en"]
        )

        sections += f"""

        <div class="card">

            <h2>
                {escape_html(
                    title
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
                    Replace / Upload Document
                </label>

                <input
                    type="file"
                    name="document"
                >


                <button
                    type="submit"
                >
                    {T("save")}
                </button>

            </form>

        </div>

        """

    body = f"""

    <div class="card">

        <h1>
            📄
            {T("manage_requirements")}
        </h1>

        <p>
            Bond and clearance requirements begin
            as "Not yet uploaded".
        </p>

    </div>

    {sections}

    """

    return render_page(
        T("requirements"),
        body,
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

    try:

        filename = save_upload(
            uploaded
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

    original = None

    if uploaded and uploaded.filename:

        original = secure_filename(
            uploaded.filename
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
# PUBLIC UPLOADED FILE
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
# 404
# ============================================================

@app.errorhandler(404)
def error_404(error):

    body = """

    <div class="card empty">

        <h1>
            404
        </h1>

        <h2>
            Page Not Found
        </h2>

        <p>
            The page you requested does not exist.
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


# ============================================================
# 403
# ============================================================

@app.errorhandler(403)
def error_403(error):

    body = """

    <div class="card empty">

        <h1>
            403
        </h1>

        <h2>
            Access Denied
        </h2>

        <p>
            You do not have permission to access
            this page.
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


# ============================================================
# 413
# ============================================================

@app.errorhandler(413)
def error_413(error):

    body = """

    <div class="card empty">

        <h1>
            413
        </h1>

        <h2>
            File Too Large
        </h2>

        <p>
            The uploaded file exceeds the 20 MB limit.
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
        "File Too Large",
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
# RUN
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
