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

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from werkzeug.utils import secure_filename


# ============================================================
# MCTC SILANG-AMADEO, CAVITE
# COURT INFORMATION PORTAL
# ============================================================
#
# Main features:
#
# - Purple court portal design
# - English / Filipino
# - Light / Dark mode
# - Official court logo: static/image0.png
# - Public case search
# - Case number + last name BOTH required
# - Case details
# - Hearing information
# - Staff login
# - Administrator login
# - Staff account management
# - Add / edit / delete cases
# - Change hearing nature
# - Change hearing status
# - Tuesday calendar
# - Staff-editable Tuesday calendar
# - Public Tuesday calendar
# - Notice publishing
# - Photo/document uploads for notices
# - Bond requirements
# - Cash bond requirements
# - Clearance requirements
# - Laws / decisions / rules resource section
# - Google Maps
# - Court address / phone / email
# - Logout
# - Security headers
# - Health check
#
# Initial administrator:
#
# Username: admin
# Password: admin123
#
# IMPORTANT:
# This is a prototype/public-information portal.
# Do not place confidential judicial documents into a
# publicly accessible folder without implementing the
# appropriate authentication, authorization, privacy,
# storage, logging, backup and security controls.
#
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

DB_PATH = (
    BASE_DIR
    / "mctc_court.db"
)

STATIC_DIR = (
    BASE_DIR
    / "static"
)

UPLOAD_DIR = (
    STATIC_DIR
    / "uploads"
)

STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
)


# ============================================================
# SESSION
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32),
)

app.config[
    "MAX_CONTENT_LENGTH"
] = (
    20 * 1024 * 1024
)

app.config[
    "SESSION_COOKIE_HTTPONLY"
] = True

app.config[
    "SESSION_COOKIE_SAMESITE"
] = "Lax"

if os.environ.get("RENDER"):

    app.config[
        "SESSION_COOKIE_SECURE"
    ] = True


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

COURT_PHONE = (
    "09284621305"
)

COURT_EMAIL = (
    "mctc2sad000@judiciary.gov.ph"
)


# Google Maps query generated from the address supplied.
MAP_QUERY = quote_plus(
    COURT_NAME
    + ", "
    + COURT_ADDRESS
)

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/"
    "?api=1&query="
    + MAP_QUERY
)


LOGO_FILENAME = (
    "image0.png"
)


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
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {

    "en": {

        "home":
            "Home",

        "about":
            "About Us",

        "news":
            "News and Announcements",

        "contact":
            "Contact Us",

        "staff_login":
            "Staff Login",

        "search":
            "Search Cases",

        "calendar":
            "Tuesday Calendar",

        "laws":
            "Laws, Decisions and Rules",

        "requirements":
            "Requirements",

        "dashboard":
            "Staff Dashboard",

        "logout":
            "Log Out",

        "login":
            "Log In",

        "cases":
            "Cases",

        "case":
            "Case",

        "hearing":
            "Hearing",

        "hearings":
            "Hearings",

        "notices":
            "Notices",

        "staff_accounts":
            "Staff Accounts",

        "manage_cases":
            "Manage Cases",

        "manage_calendar":
            "Manage Tuesday Calendar",

        "manage_notices":
            "Manage Notices",

        "manage_laws":
            "Manage Legal Resources",

        "manage_requirements":
            "Manage Requirements",

        "add_case":
            "Add Case",

        "edit_case":
            "Edit Case",

        "delete_case":
            "Delete Case",

        "add_staff":
            "Add Staff Account",

        "username":
            "Username",

        "password":
            "Password",

        "email":
            "Email Address",

        "role":
            "Role",

        "case_number":
            "Case Number",

        "last_name":
            "Last Name / Party Name",

        "parties":
            "Parties",

        "case_title":
            "Case Title",

        "case_type":
            "Case Type",

        "status":
            "Status",

        "description":
            "Description",

        "hearing_date":
            "Hearing Date",

        "hearing_time":
            "Hearing Time",

        "hearing_nature":
            "Nature of Hearing",

        "hearing_status":
            "Hearing Status",

        "courtroom":
            "Courtroom",

        "remarks":
            "Remarks",

        "search_case":
            "Search for a Case",

        "how_search":
            "How to Search",

        "step_one":
            "Enter the complete case number.",

        "step_two":
            "Enter the last name of a party.",

        "step_three":
            "Both fields are required.",

        "step_four":
            "Click Search Case.",

        "both_required":
            "Both the case number and last name / "
            "party name are required.",

        "no_results":
            "No matching public case was found.",

        "invalid_login":
            "Invalid username or password.",

        "login_required":
            "Please log in as authorized staff.",

        "welcome":
            "Welcome, Court Staff",

        "quick_actions":
            "Quick Actions",

        "save":
            "Save",

        "add":
            "Add",

        "edit":
            "Edit",

        "delete":
            "Delete",

        "cancel":
            "Cancel",

        "view":
            "View",

        "open":
            "Open",

        "upload":
            "Upload",

        "attachment":
            "Photo / Document",

        "phone":
            "Telephone",

        "address":
            "Address",

        "official_source":
            "Official Source",

        "open_maps":
            "Open Google Maps",

        "suspension":
            "Suspension Information",

        "not_uploaded":
            "Not yet uploaded",

        "copyright":
            "© 2026 Municipal Circuit Trial Court "
            "of Silang-Amadeo, Cavite. "
            "All rights reserved.",

    },

    "fil": {

        "home":
            "Home",

        "about":
            "Tungkol sa Amin",

        "news":
            "Balita at mga Anunsyo",

        "contact":
            "Makipag-ugnayan",

        "staff_login":
            "Staff Login",

        "search":
            "Maghanap ng Kaso",

        "calendar":
            "Kalendaryo ng Martes",

        "laws":
            "Mga Batas, Desisyon at Alituntunin",

        "requirements":
            "Mga Kinakailangan",

        "dashboard":
            "Dashboard ng Staff",

        "logout":
            "Mag-Logout",

        "login":
            "Mag-Login",

        "cases":
            "Mga Kaso",

        "case":
            "Kaso",

        "hearing":
            "Pagdinig",

        "hearings":
            "Mga Pagdinig",

        "notices":
            "Mga Abiso",

        "staff_accounts":
            "Mga Account ng Staff",

        "manage_cases":
            "Pamahalaan ang mga Kaso",

        "manage_calendar":
            "Pamahalaan ang Kalendaryo ng Martes",

        "manage_notices":
            "Pamahalaan ang mga Abiso",

        "manage_laws":
            "Pamahalaan ang Legal Resources",

        "manage_requirements":
            "Pamahalaan ang mga Kinakailangan",

        "add_case":
            "Magdagdag ng Kaso",

        "edit_case":
            "I-edit ang Kaso",

        "delete_case":
            "Burahin ang Kaso",

        "add_staff":
            "Magdagdag ng Staff Account",

        "username":
            "Username",

        "password":
            "Password",

        "email":
            "Email Address",

        "role":
            "Role",

        "case_number":
            "Numero ng Kaso",

        "last_name":
            "Apelyido / Pangalan ng Partido",

        "parties":
            "Mga Partido",

        "case_title":
            "Pamagat ng Kaso",

        "case_type":
            "Uri ng Kaso",

        "status":
            "Katayuan",

        "description":
            "Deskripsyon",

        "hearing_date":
            "Petsa ng Pagdinig",

        "hearing_time":
            "Oras ng Pagdinig",

        "hearing_nature":
            "Uri ng Pagdinig",

        "hearing_status":
            "Katayuan ng Pagdinig",

        "courtroom":
            "Silid ng Hukuman",

        "remarks":
            "Mga Tala",

        "search_case":
            "Maghanap ng Kaso",

        "how_search":
            "Paano Maghanap",

        "step_one":
            "Ilagay ang buong case number.",

        "step_two":
            "Ilagay ang apelyido ng isang partido.",

        "step_three":
            "Kinakailangan ang parehong field.",

        "step_four":
            "I-click ang Maghanap.",

        "both_required":
            "Kinakailangan ang parehong case number "
            "at apelyido / pangalan ng partido.",

        "no_results":
            "Walang nakitang pampublikong kaso.",

        "invalid_login":
            "Mali ang username o password.",

        "login_required":
            "Mag-login bilang awtorisadong staff.",

        "welcome":
            "Maligayang Pagdating, Kawani ng Hukuman",

        "quick_actions":
            "Mabilis na Aksyon",

        "save":
            "I-save",

        "add":
            "Magdagdag",

        "edit":
            "I-edit",

        "delete":
            "Burahin",

        "cancel":
            "Kanselahin",

        "view":
            "Tingnan",

        "open":
            "Buksan",

        "upload":
            "Mag-upload",

        "attachment":
            "Larawan / Dokumento",

        "phone":
            "Telepono",

        "address":
            "Address",

        "official_source":
            "Opisyal na Source",

        "open_maps":
            "Buksan ang Google Maps",

        "suspension":
            "Impormasyon sa Suspensyon",

        "not_uploaded":
            "Hindi pa naiu-upload",

        "copyright":
            "© 2026 Municipal Circuit Trial Court "
            "of Silang-Amadeo, Cavite. "
            "Lahat ng karapatan ay nakalaan.",

    },

}


# ============================================================
# REQUIREMENT CHECKLISTS
# ============================================================
#
# These items were transcribed from the two images supplied
# in this conversation.
#
# ============================================================

REQUIREMENT_DETAILS = {

    "bond": [

        "Personal Data (form from court)",

        (
            "Pictures 2x2 with name tag, signature, "
            "case, case number and date"
        ),

        "4 pcs. Front",

        "4 pcs. Left side",

        "4 pcs. Right side",

        (
            "Barangay Clearance attesting the real name "
            "of the accused and bona fide resident"
        ),

        (
            "Certification (Permanent Residency) "
            "attesting how many years of stay"
        ),

        (
            "House Sketch — certified, signed and sealed "
            "by Barangay Captain with date"
        ),

        (
            "Certificate of Detention "
            "(if detained or arrested)"
        ),

        (
            "Affidavit of Voluntary Surrender "
            "(if voluntary or not detained)"
        ),

        "Finger Print (piano)",

        "Specimen Signature (at least 5 signatures)",

        "Affidavit of Undertaking",

        (
            "Valid Government-Issued I.D. "
            "(original AND xerox copy back-to-back)"
        ),

        (
            "Original copy of PSA Birth Certificate "
            "(latest copy with attached receipt)"
        ),

        (
            "If married, female — original copy of "
            "PSA Marriage Certificate with attached receipt"
        ),

        (
            "For inquiries, seek assistance from "
            "court staff."
        ),

    ],

    "cash_bond": [

        "Personal Data",

        (
            "Pictures 2x2 with name tag, signature, "
            "case, case number and date"
        ),

        "4 pcs. Front",

        "4 pcs. Left side",

        "4 pcs. Right side",

        (
            "Barangay Clearance attesting the real name "
            "of the accused and bona fide resident"
        ),

        (
            "Certification (Permanent Residency) "
            "attesting how many years of stay"
        ),

        (
            "House Sketch — certified, signed and sealed "
            "by Brgy. Captain with date"
        ),

        (
            "Certificate of Detention "
            "(if detained or arrested)"
        ),

        (
            "Affidavit of Voluntary Surrender "
            "(if voluntary or not detained)"
        ),

        "Finger Print (Piano)",

        (
            "Specimen Signature "
            "(at least 5 signatures)"
        ),

        "Affidavit of Undertaking",

        (
            "Valid I.D. (Government-issued I.D.) "
            "— original and xerox back-to-back"
        ),

        (
            "Original copy of PSA Birth Certificate "
            "with attached receipt"
        ),

        (
            "If married, female — original copy of "
            "PSA Marriage Certificate with attached receipt"
        ),

    ],

    "clearance": [],

}


def requirement_details(category):

    items = REQUIREMENT_DETAILS.get(
        category,
        [],
    )

    if not items:

        return (
            "<p class='small'>"
            "Not yet uploaded. "
            "Please contact the court for the "
            "current official clearance requirements."
            "</p>"
        )

    result = (
        "<ol class='requirement-list'>"
    )

    for item in items:

        result += (
            "<li>%s</li>"
            % esc(item)
        )

    result += "</ol>"

    return result


# ============================================================
# GENERAL HELPERS
# ============================================================

def lang():

    value = session.get(
        "language",
        "en",
    )

    if value not in TRANSLATIONS:

        return "en"

    return value


def tr(key):

    return TRANSLATIONS[
        lang()
    ].get(
        key,
        key,
    )


def esc(value):

    return html.escape(
        str(value or ""),
        quote=True,
    )


def now():

    return datetime.utcnow().isoformat(
        timespec="seconds"
    )


def get_db():

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# AUDIT
# ============================================================

def audit(
    action,
    target="",
):

    try:

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
                session.get(
                    "staff_username",
                    "system",
                ),
                action,
                str(target),
                now(),
            ),
        )

        connection.commit()

        connection.close()

    except sqlite3.Error:

        pass


# ============================================================
# AUTHORIZATION
# ============================================================

def staff_required(fn):

    @wraps(fn)
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

        return fn(
            *args,
            **kwargs
        )

    return wrapper


def admin_required(fn):

    @wraps(fn)
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

        return fn(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# FILE UPLOAD
# ============================================================

def save_upload(file):

    if file is None:

        return None, None

    if not file.filename:

        return None, None

    original = secure_filename(
        file.filename
    )

    if not original:

        return None, None

    extension = (
        Path(original)
        .suffix
        .lower()
        .lstrip(".")
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "That file type is not allowed."
        )

    generated = (
        secrets.token_hex(12)
        + "_"
        + original
    )

    file.save(
        UPLOAD_DIR / generated
    )

    return (
        generated,
        original,
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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

    for (
        category,
        title_en,
        title_fil,
    ) in defaults:

        existing = connection.execute(
            """
            SELECT id
            FROM requirements
            WHERE category = ?
            """,
            (category,),
        ).fetchone()

        if existing is None:

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
        """
        SELECT id
        FROM staff
        WHERE username = ?
        """,
        ("admin",),
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


init_db()


# ============================================================
# CSS
# ============================================================

STYLE = """
:root{
    --bg:#faf8fc;
    --surface:#ffffff;
    --surface2:#f2eafa;
    --text:#25162d;
    --muted:#6d5d75;
    --border:#ded1e6;
    --purple:#6d28d9;
    --purple2:#8b5cf6;
    --deep:#3b0764;
    --danger:#a61e40;
    --ok:#18703b;
}

body.dark{
    --bg:#130f18;
    --surface:#211927;
    --surface2:#30213a;
    --text:#fff8ff;
    --muted:#d1c0d9;
    --border:#503e5b;
}

*{
    box-sizing:border-box;
}

body{
    margin:0;
    min-height:100vh;
    background:var(--bg);
    color:var(--text);
    font-family:Arial,Helvetica,sans-serif;
    line-height:1.6;
}

a{
    color:var(--purple);
    text-decoration:none;
}

body.dark a{
    color:#ccb1ff;
}

a:hover{
    text-decoration:underline;
}

.site-header{
    position:sticky;
    top:0;
    z-index:1000;
    background:
        linear-gradient(
            135deg,
            var(--deep),
            var(--purple),
            var(--purple2)
        );
    color:white;
    box-shadow:
        0 7px 24px
        rgba(35,4,49,.3);
}

.header-inner{
    width:94%;
    max-width:1280px;
    margin:auto;
    display:flex;
    align-items:center;
    gap:15px;
    padding:10px 0;
    flex-wrap:wrap;
}

.brand-link{
    color:#fff;
    display:flex;
    align-items:center;
    gap:12px;
    flex:1;
    min-width:260px;
    text-decoration:none;
}

.brand-link:hover{
    text-decoration:none;
}

.logo{
    width:58px;
    height:58px;
    object-fit:contain;
    background:#fff;
    border-radius:50%;
    padding:4px;
}

.brand strong{
    display:block;
    font-size:14px;
}

.brand small{
    display:block;
    opacity:.88;
}

.nav{
    display:flex;
    align-items:center;
    flex-wrap:wrap;
    gap:4px;
}

.nav a,
.nav button{
    border:0;
    background:transparent;
    color:#fff;
    padding:8px 9px;
    border-radius:9px;
    font-weight:800;
    font-size:12px;
    cursor:pointer;
}

.nav a:hover,
.nav button:hover{
    background:rgba(255,255,255,.15);
    text-decoration:none;
}

.container{
    width:94%;
    max-width:1180px;
    margin:auto;
    padding:28px 0 70px;
}

.hero{
    padding:55px 22px;
    border-radius:25px;
    margin:15px 0 24px;
    text-align:center;
    color:#fff;
    background:
        linear-gradient(
            135deg,
            var(--deep),
            var(--purple),
            var(--purple2)
        );
}

.hero-logo{
    width:145px;
    height:145px;
    object-fit:contain;
    background:#fff;
    border-radius:50%;
    padding:5px;
}

.hero h1{
    max-width:950px;
    margin:15px auto;
    font-size:clamp(31px,5vw,56px);
    line-height:1.05;
}

.grid{
    display:grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(250px,1fr)
        );
    gap:16px;
}

.card{
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:18px;
    padding:22px;
    margin:16px 0;
    box-shadow:
        0 9px 25px
        rgba(60,20,80,.07);
}

.two{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:14px;
}

label{
    display:block;
    font-weight:800;
    margin:10px 0 5px;
}

input,
textarea,
select{
    width:100%;
    padding:12px;
    border:
        1px solid
        var(--border);
    border-radius:10px;
    background:var(--surface);
    color:var(--text);
    font:inherit;
}

textarea{
    min-height:115px;
    resize:vertical;
}

button,
.button{
    display:inline-block;
    padding:10px 15px;
    border:0;
    border-radius:10px;
    background:var(--purple);
    color:#fff;
    font-weight:800;
    cursor:pointer;
    text-decoration:none;
}

button:hover,
.button:hover{
    background:var(--deep);
    color:#fff;
    text-decoration:none;
}

.secondary{
    background:var(--surface2);
    color:var(--text);
    border:1px solid var(--border);
}

.danger{
    background:var(--danger);
}

.actions{
    display:flex;
    align-items:center;
    gap:8px;
    flex-wrap:wrap;
    margin-top:14px;
}

.notice{
    padding:14px 16px;
    border-left:5px solid var(--purple);
    background:var(--surface2);
    border-radius:10px;
    margin:12px 0;
}

.notice.warning{
    border-left-color:#d97706;
}

.notice.success{
    border-left-color:var(--ok);
}

.notice.danger{
    border-left-color:#b91c1c;
}

.status{
    display:inline-block;
    padding:4px 10px;
    border-radius:999px;
    background:var(--surface2);
    color:var(--purple);
    font-weight:900;
    font-size:12px;
}

.table-wrap{
    overflow:auto;
}

table{
    width:100%;
    border-collapse:collapse;
}

th,
td{
    padding:10px;
    text-align:left;
    border-bottom:
        1px solid
        var(--border);
    vertical-align:top;
}

th{
    background:var(--surface2);
}

.empty{
    text-align:center;
    padding:40px;
    color:var(--muted);
}

.small{
    font-size:13px;
    color:var(--muted);
}

.stat{
    text-align:center;
}

.stat-number{
    display:block;
    font-size:40px;
    font-weight:900;
    color:var(--purple);
}

.requirement-list li{
    margin:8px 0;
}

footer{
    border-top:
        1px solid
        var(--border);
    background:var(--surface);
    color:var(--muted);
    text-align:center;
    padding:30px 15px;
}

@media(max-width:850px){

    .header-inner{
        align-items:flex-start;
        flex-direction:column;
    }

    .nav{
        width:100%;
    }

    .two{
        grid-template-columns:1fr;
    }
}

@media(max-width:520px){

    .hero{
        padding:35px 18px;
    }

    .hero h1{
        font-size:34px;
    }
}
"""


# ============================================================
# PAGE TEMPLATE
# ============================================================

PAGE = """<!doctype html>
<html lang="%s">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<meta
    name="description"
    content="MCTC Silang-Amadeo Court Information Portal"
>

<title>
%s
-
%s
</title>

<style>
%s
</style>

</head>


<body class="%s">


<header class="site-header">

<div class="header-inner">


<a
    class="brand-link"
    href="%s"
>

<img
    class="logo"
    src="%s"
    alt="Official court logo"
>

<div class="brand">

<strong>
%s
</strong>

<small>
Official Court Information Portal
</small>

</div>

</a>


<nav class="nav">

%s

</nav>


</div>

</header>


<main class="container">

%s

</main>


<footer>

<strong>
%s
</strong>

<p>
%s
</p>

<p>

<a
    href="tel:%s"
>
%s
</a>

<br>

<a
    href="mailto:%s"
>
%s
</a>

</p>

<p>

<a
    href="%s"
    target="_blank"
    rel="noopener noreferrer"
>
🗺️
%s
</a>

</p>

<p>
%s
</p>

</footer>


</body>

</html>
"""


# ============================================================
# PAGE RENDERING
# ============================================================

def page(
    title,
    content,
):

    theme = session.get(
        "theme",
        "light",
    )

    other_theme = (
        "dark"
        if theme == "light"
        else "light"
    )

    other_language = (
        "fil"
        if lang() == "en"
        else "en"
    )

    language_label = (
        "FIL"
        if lang() == "en"
        else "EN"
    )

    theme_label = (
        "🌙"
        if theme == "light"
        else "☀️"
    )

    nav = ""

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("home"),
            tr("home"),
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("about"),
            tr("about"),
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("news"),
            tr("news"),
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("contact"),
            tr("contact"),
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("search_cases"),
            tr("search"),
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for("public_calendar"),
            tr("calendar"),
        )
    )

    if session.get(
        "staff_logged_in"
    ):

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_dashboard"
                ),
                tr("dashboard"),
            )
        )

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_cases"
                ),
                tr("cases"),
            )
        )

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_calendar"
                ),
                tr("calendar"),
            )
        )

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_notices"
                ),
                tr("notices"),
            )
        )

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_laws"
                ),
                tr("laws"),
            )
        )

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_requirements"
                ),
                tr("requirements"),
            )
        )

        if session.get(
            "staff_role"
        ) == "admin":

            nav += (
                "<a href='%s'>%s</a>"
                % (
                    url_for(
                        "staff_accounts"
                    ),
                    tr(
                        "staff_accounts"
                    ),
                )
            )

        nav += (
            "<form "
            "method='post' "
            "action='%s' "
            "style='display:inline'>"
            "<button "
            "type='submit' "
            "class='nav-button'>"
            "%s"
            "</button>"
            "</form>"
            % (
                url_for("logout"),
                tr("logout"),
            )
        )

    else:

        nav += (
            "<a href='%s'>%s</a>"
            % (
                url_for(
                    "staff_login"
                ),
                tr("staff_login"),
            )
        )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for(
                "change_language",
                language=other_language,
            ),
            language_label,
        )
    )

    nav += (
        "<a href='%s'>%s</a>"
        % (
            url_for(
                "change_theme",
                theme=other_theme,
            ),
            theme_label,
        )
    )

    flashes = ""

    for (
        category,
        message,
    ) in __import__(
        "flask"
    ).get_flashed_messages(
        with_categories=True
    ):

        flashes += (
            "<div class='notice %s'>%s</div>"
            % (
                esc(category),
                esc(message),
            )
        )

    return PAGE % (
        esc(lang()),
        esc(title),
        esc(COURT_NAME),
        STYLE,
        esc(theme),
        url_for("home"),
        url_for(
            "static",
            filename=LOGO_FILENAME,
        ),
        esc(COURT_NAME),
        nav,
        flashes + content,
        esc(COURT_NAME),
        esc(COURT_ADDRESS),
        esc(COURT_PHONE),
        esc(COURT_PHONE),
        esc(COURT_EMAIL),
        esc(COURT_EMAIL),
        GOOGLE_MAPS_URL,
        tr("open_maps"),
        tr("copyright"),
    )


# ============================================================
# LANGUAGE / THEME
# ============================================================

@app.route(
    "/language/<language>"
)
def change_language(
    language
):

    if language not in TRANSLATIONS:

        language = "en"

    session[
        "language"
    ] = language

    return redirect(
        request.referrer
        or url_for("home")
    )


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

        theme = "light"

    session[
        "theme"
    ] = theme

    return redirect(
        request.referrer
        or url_for("home")
    )


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

    notice_html = ""

    for notice in notices:

        if lang() == "fil":

            title = notice[
                "title_fil"
            ]

            text = notice[
                "body_fil"
            ]

        else:

            title = notice[
                "title_en"
            ]

            text = notice[
                "body_en"
            ]

        attachment = ""

        if notice[
            "attachment"
        ]:

            attachment = (
                "<a class='button secondary' "
                "href='%s'>📎 %s</a>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=notice[
                            "attachment"
                        ],
                    ),
                    tr("open"),
                )
            )

        notice_html += (
            "<div class='notice'>"
            "<h3>%s</h3>"
            "<p>%s</p>"
            "%s"
            "</div>"
            % (
                esc(title),
                esc(text),
                attachment,
            )
        )

    content = (
        "<section class='hero'>"
        "<img class='hero-logo' "
        "src='%s' "
        "alt='Court logo'>"
        "<h1>%s</h1>"
        "<p>"
        "Search approved public case information, "
        "view the Tuesday calendar, and read "
        "official court announcements."
        "</p>"
        "<div class='actions' "
        "style='justify-content:center'>"
        "<a class='button' href='%s'>"
        "🔎 %s"
        "</a>"
        "<a class='button secondary' href='%s'>"
        "📅 %s"
        "</a>"
        "</div>"
        "</section>"
        % (
            url_for(
                "static",
                filename=LOGO_FILENAME,
            ),
            esc(COURT_NAME),
            url_for(
                "search_cases"
            ),
            tr("search"),
            url_for(
                "public_calendar"
            ),
            tr("calendar"),
        )
    )

    content += (
        "<section class='grid'>"

        "<div class='card'>"
        "<h2>🔎 %s</h2>"
        "<p>%s</p>"
        "<a class='button' href='%s'>"
        "%s"
        "</a>"
        "</div>"

        "<div class='card'>"
        "<h2>📅 %s</h2>"
        "<p>"
        "View the public Tuesday calendar."
        "</p>"
        "<a class='button' href='%s'>"
        "%s"
        "</a>"
        "</div>"

        "<div class='card'>"
        "<h2>📢 %s</h2>"
        "<p>"
        "Read announcements and notices."
        "</p>"
        "<a class='button' href='%s'>"
        "%s"
        "</a>"
        "</div>"

        "<div class='card'>"
        "<h2>⚖️ %s</h2>"
        "<p>"
        "View approved legal resources."
        "</p>"
        "<a class='button' href='%s'>"
        "%s"
        "</a>"
        "</div>"

        "</section>"
        % (
            tr("search_case"),
            tr("both_required"),
            url_for(
                "search_cases"
            ),
            tr("search"),

            tr("calendar"),
            url_for(
                "public_calendar"
            ),
            tr("view"),

            tr("news"),
            url_for("news"),
            tr("view"),

            tr("laws"),
            url_for("laws"),
            tr("view"),
        )
    )

    content += (
        "<section class='card'>"
        "<h2>⚠️ %s</h2>"
        "<p>"
        "A hearing should not be assumed "
        "suspended, postponed, or cancelled "
        "unless an official court notice "
        "confirms the change."
        "</p>"
        "</section>"
        % tr("suspension")
    )

    content += (
        "<section class='card'>"
        "<h2>📢 %s</h2>"
        "%s"
        "</section>"
        % (
            tr("news"),
            notice_html
            or (
                "<p class='small'>"
                "No announcements yet."
                "</p>"
            ),
        )
    )

    return page(
        tr("home"),
        content,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route(
    "/about"
)
def about():

    content = (
        "<div class='card'>"
        "<h1>%s</h1>"
        "<h2>%s</h2>"
        "<p>"
        "This portal provides approved public "
        "court information, announcements, "
        "schedules and legal-resource links."
        "</p>"
        "<div class='notice warning'>"
        "<strong>Important</strong>"
        "<p>"
        "Online information does not replace "
        "official court records, orders, "
        "notices or certified documents."
        "</p>"
        "</div>"
        "</div>"
        % (
            tr("about"),
            esc(COURT_NAME),
        )
    )

    return page(
        tr("about"),
        content,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route(
    "/contact"
)
def contact():

    content = (
        "<div class='card'>"

        "<h1>%s</h1>"

        "<h2>%s</h2>"

        "<p>"
        "<strong>%s:</strong>"
        "<br>%s"
        "</p>"

        "<p>"
        "<strong>%s:</strong>"
        "<br>"
        "<a href='tel:%s'>%s</a>"
        "</p>"

        "<p>"
        "<strong>%s:</strong>"
        "<br>"
        "<a href='mailto:%s'>%s</a>"
        "</p>"

        "<a class='button' "
        "href='%s' "
        "target='_blank' "
        "rel='noopener'>"
        "🗺️ %s"
        "</a>"

        "</div>"
        % (
            tr("contact"),
            esc(COURT_NAME),
            tr("address"),
            esc(COURT_ADDRESS),
            tr("phone"),
            esc(COURT_PHONE),
            esc(COURT_PHONE),
            tr("email"),
            esc(COURT_EMAIL),
            esc(COURT_EMAIL),
            GOOGLE_MAPS_URL,
            tr("open_maps"),
        )
    )

    return page(
        tr("contact"),
        content,
    )


# ============================================================
# NEWS
# ============================================================

@app.route(
    "/news"
)
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

    content = (
        "<div class='card'>"
        "<h1>📢 %s</h1>"
        "</div>"
        % tr("news")
    )

    for notice in notices:

        if lang() == "fil":

            title = notice[
                "title_fil"
            ]

            text = notice[
                "body_fil"
            ]

        else:

            title = notice[
                "title_en"
            ]

            text = notice[
                "body_en"
            ]

        attachment = ""

        if notice[
            "attachment"
        ]:

            attachment = (
                "<p>"
                "<a class='button secondary' "
                "href='%s'>"
                "📎 %s"
                "</a>"
                "</p>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=notice[
                            "attachment"
                        ],
                    ),
                    tr("open"),
                )
            )

        content += (
            "<article class='card'>"
            "<h2>%s</h2>"
            "<p>%s</p>"
            "%s"
            "</article>"
            % (
                esc(title),
                esc(text),
                attachment,
            )
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

        if (
            not case_number
            or not last_name
        ):

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
                WHERE
                    lower(case_number)
                    = lower(?)
                AND
                    lower(last_name)
                    = lower(?)
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

    content = (
        "<div class='card'>"

        "<h1>🔎 %s</h1>"

        "<div class='notice'>"

        "<h3>%s</h3>"

        "<ol>"

        "<li>%s</li>"
        "<li>%s</li>"
        "<li>%s</li>"
        "<li>%s</li>"

        "</ol>"

        "</div>"

        "<form method='post'>"

        "<label>%s</label>"

        "<input "
        "name='case_number' "
        "value='%s' "
        "required "
        "autocomplete='off'>"

        "<label>%s</label>"

        "<input "
        "name='last_name' "
        "value='%s' "
        "required "
        "autocomplete='off'>"

        "<button type='submit'>"
        "🔎 %s"
        "</button>"

        "</form>"

        "</div>"
        % (
            tr("search_case"),
            tr("how_search"),
            tr("step_one"),
            tr("step_two"),
            tr("step_three"),
            tr("step_four"),
            tr("case_number"),
            esc(case_number),
            tr("last_name"),
            esc(last_name),
            tr("search"),
        )
    )

    if result:

        content += (
            "<div class='card'>"

            "<span class='status'>%s</span>"

            "<h2>%s</h2>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "<a class='button' "
            "href='%s'>"
            "%s"
            "</a>"

            "</div>"
            % (
                esc(
                    result["status"]
                ),
                esc(
                    result["case_number"]
                ),
                tr("parties"),
                esc(
                    result["parties"]
                ),
                tr("case_title"),
                esc(
                    result["case_title"]
                ),
                tr("case_type"),
                esc(
                    result["case_type"]
                ),
                url_for(
                    "public_case",
                    case_id=result["id"],
                ),
                tr("view"),
            )
        )

    return page(
        tr("search"),
        content,
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
        (case_id,),
    ).fetchone()

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

    connection.close()

    if case is None:

        abort(404)

    hearings_html = ""

    for hearing in hearings:

        hearings_html += (
            "<div class='notice'>"

            "<h3>%s</h3>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "<p>"
            "<strong>%s:</strong> "
            "<span class='status'>%s</span>"
            "</p>"

            "<p>"
            "<strong>%s:</strong> %s"
            "</p>"

            "</div>"
            % (
                esc(
                    hearing[
                        "hearing_date"
                    ]
                ),
                tr("hearing_time"),
                esc(
                    hearing[
                        "hearing_time"
                    ]
                ),
                tr("hearing_nature"),
                esc(
                    hearing[
                        "hearing_nature"
                    ]
                ),
                tr("hearing_status"),
                esc(
                    hearing[
                        "hearing_status"
                    ]
                ),
                tr("courtroom"),
                esc(
                    hearing[
                        "courtroom"
                    ]
                ),
            )
        )

    if not hearings_html:

        hearings_html = (
            "<p class='small'>"
            "No published hearing information."
            "</p>"
        )

    content = (
        "<div class='card'>"

        "<span class='status'>%s</span>"

        "<h1>%s</h1>"

        "<h2>%s</h2>"

        "<p>"
        "<strong>%s:</strong> %s"
        "</p>"

        "<p>"
        "<strong>%s:</strong> %s"
        "</p>"

        "<p>%s</p>"

        "</div>"

        "<div class='card'>"

        "<h2>📅 %s</h2>"

        "%s"

        "</div>"
        % (
            esc(
                case["status"]
            ),
            esc(
                case[
                    "case_number"
                ]
            ),
            esc(
                case["case_title"]
            ),
            tr("parties"),
            esc(
                case["parties"]
            ),
            tr("case_type"),
            esc(
                case["case_type"]
            ),
            esc(
                case[
                    "public_description"
                ]
            ),
            tr("hearings"),
            hearings_html,
        )
    )

    return page(
        tr("case"),
        content,
    )


# ============================================================
# PUBLIC TUESDAY CALENDAR
# ============================================================

@app.route(
    "/calendar"
)
def public_calendar():

    connection = get_db()

    entries = connection.execute(
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

    connection.close()

    table = ""

    for entry in entries:

        table += (
            "<tr>"

            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"

            "</tr>"
            % (
                esc(
                    entry[
                        "calendar_date"
                    ]
                ),
                esc(
                    entry[
                        "calendar_time"
                    ]
                ),
                esc(
                    entry[
                        "case_number"
                    ]
                ),
                esc(
                    entry[
                        "parties"
                    ]
                ),
                esc(
                    entry[
                        "hearing_nature"
                    ]
                ),
                esc(
                    entry[
                        "hearing_status"
                    ]
                ),
                esc(
                    entry[
                        "courtroom"
                    ]
                ),
            )
        )

    if not table:

        table = (
            "<tr>"
            "<td "
            "colspan='7' "
            "class='empty'>"
            "No Tuesday entries."
            "</td>"
            "</tr>"
        )

    content = (
        "<div class='card'>"

        "<h1>📅 %s</h1>"

        "<p>"
        "Public Tuesday calendar published "
        "by authorized staff."
        "</p>"

        "<div class='notice warning'>"
        "Schedules may change. "
        "Confirm important information "
        "with the court."
        "</div>"

        "</div>"

        "<div class='card table-wrap'>"

        "<table>"

        "<thead>"
        "<tr>"

        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"

        "</tr>"
        "</thead>"

        "<tbody>%s</tbody>"

        "</table>"

        "</div>"
        % (
            tr("calendar"),
            tr("hearing_date"),
            tr("hearing_time"),
            tr("case_number"),
            tr("parties"),
            tr("hearing_nature"),
            tr("hearing_status"),
            tr("courtroom"),
            table,
        )
    )

    return page(
        tr("calendar"),
        content,
    )


# ============================================================
# PUBLIC REQUIREMENTS
# ============================================================

@app.route(
    "/requirements"
)
def requirements():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY category
        """
    ).fetchall()

    connection.close()

    content = (
        "<div class='card'>"
        "<h1>📄 %s</h1>"
        "</div>"
        % tr("requirements")
    )

    for row in rows:

        if lang() == "fil":

            title = row[
                "title_fil"
            ]

            description = row[
                "description_fil"
            ]

        else:

            title = row[
                "title_en"
            ]

            description = row[
                "description_en"
            ]

        file_link = ""

        if row[
            "file_name"
        ]:

            file_link = (
                "<a class='button secondary' "
                "href='%s'>"
                "%s"
                "</a>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=row[
                            "file_name"
                        ],
                    ),
                    tr("open"),
                )
            )

        content += (
            "<div class='card'>"

            "<h2>%s</h2>"

            "<p>%s</p>"

            "%s"

            "%s"

            "</div>"
            % (
                esc(title),
                esc(
                    description
                    or tr(
                        "not_uploaded"
                    )
                ),
                requirement_details(
                    row["category"]
                ),
                file_link,
            )
        )

    return page(
        tr("requirements"),
        content,
    )


# ============================================================
# PUBLIC LEGAL RESOURCES
# ============================================================

@app.route(
    "/laws"
)
def laws():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY
            category,
            created_at DESC
        """
    ).fetchall()

    connection.close()

    content = (
        "<div class='card'>"

        "<h1>⚖️ %s</h1>"

        "<p>"
        "Approved references to Philippine laws, "
        "Supreme Court decisions, rules and "
        "other legal resources."
        "</p>"

        "<div class='notice warning'>"
        "Verify legal authorities against an "
        "authoritative current source."
        "</div>"

        "</div>"
        % tr("laws")
    )

    for row in rows:

        links = ""

        if row[
            "source_url"
        ]:

            links += (
                "<a class='button secondary' "
                "href='%s' "
                "target='_blank' "
                "rel='noopener'>"
                "%s"
                "</a> "
                % (
                    esc(
                        row[
                            "source_url"
                        ]
                    ),
                    tr(
                        "official_source"
                    ),
                )
            )

        if row[
            "file_name"
        ]:

            links += (
                "<a class='button secondary' "
                "href='%s'>"
                "%s"
                "</a>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=row[
                            "file_name"
                        ],
                    ),
                    tr("open"),
                )
            )

        content += (
            "<div class='card'>"

            "<span class='status'>%s</span>"

            "<h2>%s</h2>"

            "<p>%s</p>"

            "%s"

            "</div>"
            % (
                esc(
                    row["category"]
                ),
                esc(
                    row["title"]
                ),
                esc(
                    row["description"]
                ),
                links,
            )
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
# STAFF LOGIN
# ============================================================

@app.route(
    "/staff/login",
    methods=[
        "GET",
        "POST",
    ],
)
def staff_login():

    if session.get(
        "staff_logged_in"
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
                staff[
                    "password_hash"
                ],
                password,
            )
        ):

            session.clear()

            session[
                "staff_logged_in"
            ] = True

            session[
                "staff_id"
            ] = staff["id"]

            session[
                "staff_username"
            ] = staff["username"]

            session[
                "staff_role"
            ] = staff["role"]

            session[
                "language"
            ] = "en"

            session[
                "theme"
            ] = "light"

            audit(
                "login",
                username,
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

    content = (
        "<div class='card' "
        "style='max-width:520px;"
        "margin:40px auto'>"

        "<img "
        "class='hero-logo' "
        "src='%s' "
        "alt='Court logo'>"

        "<h1>🔐 %s</h1>"

        "<p class='small'>"
        "Authorized court staff only."
        "</p>"

        "<form "
        "method='post' "
        "autocomplete='off'>"

        "<label>%s</label>"

        "<input "
        "name='username' "
        "required "
        "autocomplete='username'>"

        "<label>%s</label>"

        "<input "
        "type='password' "
        "name='password' "
        "required "
        "autocomplete='current-password'>"

        "<br>"

        "<button "
        "type='submit'>"
        "%s"
        "</button>"

        "</form>"

        "</div>"
        % (
            url_for(
                "static",
                filename=LOGO_FILENAME,
            ),
            tr("staff_login"),
            tr("username"),
            tr("password"),
            tr("login"),
        )
    )

    return page(
        tr("staff_login"),
        content,
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/staff/logout",
    methods=[
        "GET",
        "POST",
    ],
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

    flash(
        "You have been logged out.",
        "success",
    )

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

    connection = get_db()

    cases_count = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    notices_count = connection.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    calendar_count = connection.execute(
        "SELECT COUNT(*) FROM tuesday_calendar"
    ).fetchone()[0]

    legal_count = connection.execute(
        "SELECT COUNT(*) FROM legal_resources"
    ).fetchone()[0]

    connection.close()

    content = (
        "<section class='hero'>"

        "<h1>%s</h1>"

        "<p>"
        "Manage approved public court information."
        "</p>"

        "</section>"

        "<section class='grid'>"

        "<div class='stat card'>"
        "<span class='stat-number'>%s</span>"
        "%s"
        "</div>"

        "<div class='stat card'>"
        "<span class='stat-number'>%s</span>"
        "%s"
        "</div>"

        "<div class='stat card'>"
        "<span class='stat-number'>%s</span>"
        "%s"
        "</div>"

        "<div class='stat card'>"
        "<span class='stat-number'>%s</span>"
        "%s"
        "</div>"

        "</section>"

        "<section class='card'>"

        "<h2>⚡ %s</h2>"

        "<div class='grid'>"

        "<a class='card' href='%s'>"
        "<h3>📋 %s</h3>"
        "<p>"
        "Add, edit and delete cases."
        "</p>"
        "</a>"

        "<a class='card' href='%s'>"
        "<h3>📅 %s</h3>"
        "<p>"
        "Edit the Tuesday calendar."
        "</p>"
        "</a>"

        "<a class='card' href='%s'>"
        "<h3>📢 %s</h3>"
        "<p>"
        "Upload photos or documents."
        "</p>"
        "</a>"

        "<a class='card' href='%s'>"
        "<h3>⚖️ %s</h3>"
        "<p>"
        "Manage legal resources."
        "</p>"
        "</a>"

        "<a class='card' href='%s'>"
        "<h3>📄 %s</h3>"
        "<p>"
        "Manage bond, cash bond and clearance."
        "</p>"
        "</a>"
        % (
            tr("welcome"),
            cases_count,
            tr("cases"),
            notices_count,
            tr("notices"),
            calendar_count,
            tr("calendar"),
            legal_count,
            tr("laws"),
            tr("quick_actions"),
            url_for("staff_cases"),
            tr("manage_cases"),
            url_for("staff_calendar"),
            tr("manage_calendar"),
            url_for("staff_notices"),
            tr("manage_notices"),
            url_for("staff_laws"),
            tr("manage_laws"),
            url_for("staff_requirements"),
            tr("manage_requirements"),
        )
    )

    if session.get(
        "staff_role"
    ) == "admin":

        content += (
            "<a class='card' href='%s'>"
            "<h3>👥 %s</h3>"
            "<p>"
            "Add and manage staff accounts."
            "</p>"
            "</a>"
            % (
                url_for(
                    "staff_accounts"
                ),
                tr("staff_accounts"),
            )
        )

    content += (
        "</div>"
        "</section>"
    )

    return page(
        tr("dashboard"),
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

        rows += (
            "<tr>"

            "<td>"
            "<strong>%s</strong>"
            "<br>%s"
            "</td>"

            "<td>%s</td>"

            "<td>%s</td>"

            "<td>"
            "<span class='status'>%s</span>"
            "</td>"

            "<td>"

            "<a class='button secondary' "
            "href='%s'>"
            "%s"
            "</a> "

            "<a class='button secondary' "
            "href='%s'>"
            "%s"
            "</a> "

            "<form "
            "method='post' "
            "action='%s' "
            "style='display:inline'>"

            "<button "
            "class='danger' "
            "onclick=\""
            "return confirm("
            "'Delete this case permanently?');"
            "\">"

            "%s"

            "</button>"

            "</form>"

            "</td>"

            "</tr>"
            % (
                esc(
                    case[
                        "case_number"
                    ]
                ),
                esc(
                    case[
                        "case_title"
                    ]
                ),
                esc(
                    case["parties"]
                ),
                esc(
                    case["case_type"]
                ),
                esc(
                    case["status"]
                ),
                url_for(
                    "staff_edit_case",
                    case_id=case[
                        "id"
                    ],
                ),
                tr("edit"),
                url_for(
                    "staff_hearing",
                    case_id=case[
                        "id"
                    ],
                ),
                tr("hearing"),
                url_for(
                    "staff_delete_case",
                    case_id=case[
                        "id"
                    ],
                ),
                tr("delete"),
            )
        )

    if not rows:

        rows = (
            "<tr>"
            "<td "
            "colspan='5' "
            "class='empty'>"
            "No cases."
            "</td>"
            "</tr>"
        )

    content = (
        "<div class='card'>"

        "<div class='actions'>"

        "<h1>📋 %s</h1>"

        "<a class='button' "
        "href='%s'>"
        "➕ %s"
        "</a>"

        "</div>"

        "</div>"

        "<div class='card table-wrap'>"

        "<table>"

        "<thead>"

        "<tr>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>Actions</th>"
        "</tr>"

        "</thead>"

        "<tbody>%s</tbody>"

        "</table>"

        "</div>"
        % (
            tr("manage_cases"),
            url_for(
                "staff_add_case"
            ),
            tr("add_case"),
            tr("case_number"),
            tr("parties"),
            tr("case_type"),
            tr("status"),
            rows,
        )
    )

    return page(
        tr("cases"),
        content,
    )


# ============================================================
# STAFF ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=[
        "GET",
        "POST",
    ],
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

    content = (
        "<div class='card'>"

        "<h1>➕ %s</h1>"

        "<form method='post'>"

        "<label>%s</label>"
        "<input name='case_number' required>"

        "<label>%s</label>"
        "<input name='last_name' required>"

        "<label>%s</label>"
        "<input name='parties' required>"

        "<label>%s</label>"
        "<input name='case_title' required>"

        "<label>%s</label>"
        "<input name='case_type'>"

        "<label>%s</label>"

        "<select name='status'>"
        "<option>Pending</option>"
        "<option>Active</option>"
        "<option>Scheduled</option>"
        "<option>Resolved</option>"
        "<option>Final</option>"
        "<option>Dismissed</option>"
        "</select>"

        "<label>%s</label>"
        "<textarea "
        "name='public_description'>"
        "</textarea>"

        "<label>"
        "Private Staff Notes"
        "</label>"

        "<textarea "
        "name='internal_notes'>"
        "</textarea>"

        "<button>%s</button>"

        "</form>"

        "</div>"
        % (
            tr("add_case"),
            tr("case_number"),
            tr("last_name"),
            tr("parties"),
            tr("case_title"),
            tr("case_type"),
            tr("status"),
            tr("description"),
            tr("save"),
        )
    )

    return page(
        tr("add_case"),
        content,
    )


# ============================================================
# STAFF EDIT CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@staff_required
def staff_edit_case(
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

    content = (
        "<div class='card'>"

        "<h1>✏️ %s</h1>"

        "<form method='post'>"

        "<label>%s</label>"
        "<input "
        "value='%s' "
        "disabled>"

        "<label>%s</label>"
        "<input "
        "name='last_name' "
        "value='%s' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='parties' "
        "value='%s' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='case_title' "
        "value='%s' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='case_type' "
        "value='%s'>"

        "<label>%s</label>"
        "<select name='status'>"
        "%s"
        "</select>"

        "<label>%s</label>"
        "<textarea "
        "name='public_description'>"
        "%s"
        "</textarea>"

        "<label>"
        "Private Staff Notes"
        "</label>"

        "<textarea "
        "name='internal_notes'>"
        "%s"
        "</textarea>"

        "<button>%s</button>"

        "</form>"

        "</div>"
        % (
            tr("edit_case"),
            tr("case_number"),
            esc(
                case["case_number"]
            ),
            tr("last_name"),
            esc(
                case["last_name"]
            ),
            tr("parties"),
            esc(
                case["parties"]
            ),
            tr("case_title"),
            esc(
                case["case_title"]
            ),
            tr("case_type"),
            esc(
                case["case_type"]
            ),
            tr("status"),
            statuses,
            tr("description"),
            esc(
                case[
                    "public_description"
                ]
            ),
            esc(
                case[
                    "internal_notes"
                ]
            ),
            tr("save"),
        )
    )

    return page(
        tr("edit_case"),
        content,
    )


# ============================================================
# DELETE CASE
# ============================================================

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
        case[
            "case_number"
        ],
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
    ],
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

    if case is None:

        connection.close()

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
                    hearing[
                        "id"
                    ],
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
            case[
                "case_number"
            ],
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

    connection.close()

    date_value = (
        hearing[
            "hearing_date"
        ]
        if hearing
        else ""
    )

    time_value = (
        hearing[
            "hearing_time"
        ]
        if hearing
        else ""
    )

    nature_value = (
        hearing[
            "hearing_nature"
        ]
        if hearing
        else "Initial Hearing"
    )

    status_value = (
        hearing[
            "hearing_status"
        ]
        if hearing
        else "Scheduled"
    )

    room_value = (
        hearing[
            "courtroom"
        ]
        if hearing
        else ""
    )

    remarks_value = (
        hearing[
            "remarks"
        ]
        if hearing
        else ""
    )

    nature_options = ""

    for value in [

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

    ]:

        selected = (
            "selected"
            if value
            == nature_value
            else ""
        )

        nature_options += (
            "<option %s>%s</option>"
            % (
                selected,
                value,
            )
        )

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
            == status_value
            else ""
        )

        status_options += (
            "<option %s>%s</option>"
            % (
                selected,
                value,
            )
        )

    content = (
        "<div class='card'>"

        "<h1>📅 %s</h1>"

        "<p>"
        "<strong>%s</strong>"
        " - %s"
        "</p>"

        "<div class='notice'>"
        "Staff can change the hearing "
        "date, nature, status, courtroom "
        "and remarks here."
        "</div>"

        "<form method='post'>"

        "<label>%s</label>"
        "<input "
        "type='date' "
        "name='hearing_date' "
        "value='%s' "
        "required>"

        "<label>%s</label>"
        "<input "
        "type='time' "
        "name='hearing_time' "
        "value='%s'>"

        "<label>%s</label>"
        "<select "
        "name='hearing_nature'>"
        "%s"
        "</select>"

        "<label>%s</label>"
        "<select "
        "name='hearing_status'>"
        "%s"
        "</select>"

        "<label>%s</label>"
        "<input "
        "name='courtroom' "
        "value='%s'>"

        "<label>%s</label>"
        "<textarea "
        "name='remarks'>"
        "%s"
        "</textarea>"

        "<button>%s</button>"

        "</form>"

        "</div>"
        % (
            tr("hearing"),
            esc(
                case[
                    "case_number"
                ]
            ),
            esc(
                case[
                    "parties"
                ]
            ),
            tr("hearing_date"),
            esc(date_value),
            tr("hearing_time"),
            esc(time_value),
            tr("hearing_nature"),
            nature_options,
            tr("hearing_status"),
            status_options,
            tr("courtroom"),
            esc(room_value),
            tr("remarks"),
            esc(remarks_value),
            tr("save"),
        )
    )

    return page(
        tr("hearing"),
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

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM tuesday_calendar
        ORDER BY
            calendar_date,
            calendar_time,
            id
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

            selected = (
                "selected"
                if value
                == row[
                    "hearing_status"
                ]
                else ""
            )

            statuses += (
                "<option %s>%s</option>"
                % (
                    selected,
                    value,
                )
            )

        checked = (
            "checked"
            if row[
                "public_visible"
            ]
            else ""
        )

        cards += (
            "<div class='card'>"

            "<form "
            "method='post' "
            "action='%s'>"

            "<div class='two'>"

            "<div>"

            "<label>Date</label>"

            "<input "
            "type='date' "
            "name='calendar_date' "
            "value='%s' "
            "required>"

            "</div>"

            "<div>"

            "<label>Time</label>"

            "<input "
            "type='time' "
            "name='calendar_time' "
            "value='%s' "
            "required>"

            "</div>"

            "</div>"

            "<label>%s</label>"

            "<input "
            "name='case_number' "
            "value='%s' "
            "required>"

            "<label>%s</label>"

            "<input "
            "name='last_name' "
            "value='%s' "
            "required>"

            "<label>%s</label>"

            "<input "
            "name='parties' "
            "value='%s' "
            "required>"

            "<label>%s</label>"

            "<input "
            "name='hearing_nature' "
            "value='%s' "
            "required>"

            "<label>%s</label>"

            "<select "
            "name='hearing_status'>"
            "%s"
            "</select>"

            "<label>%s</label>"

            "<input "
            "name='courtroom' "
            "value='%s'>"

            "<label>%s</label>"

            "<textarea "
            "name='remarks'>"
            "%s"
            "</textarea>"

            "<label>"

            "<input "
            "type='checkbox' "
            "name='public_visible' "
            "%s "
            "style='width:auto'>"

            " Publish to civilians"

            "</label>"

            "<button>%s</button>"

            "</form>"

            "<br>"

            "<a class='button danger' "
            "href='%s' "
            "onclick=\""
            "return confirm("
            "'Delete this entry?');"
            "\">"
            "%s"
            "</a>"

            "</div>"
            % (
                url_for(
                    "edit_calendar",
                    entry_id=row[
                        "id"
                    ],
                ),
                esc(
                    row[
                        "calendar_date"
                    ]
                ),
                esc(
                    row[
                        "calendar_time"
                    ]
                ),
                tr("case_number"),
                esc(
                    row[
                        "case_number"
                    ]
                ),
                tr("last_name"),
                esc(
                    row[
                        "last_name"
                    ]
                ),
                tr("parties"),
                esc(
                    row[
                        "parties"
                    ]
                ),
                tr("hearing_nature"),
                esc(
                    row[
                        "hearing_nature"
                    ]
                ),
                tr("hearing_status"),
                statuses,
                tr("courtroom"),
                esc(
                    row[
                        "courtroom"
                    ]
                ),
                tr("remarks"),
                esc(
                    row[
                        "remarks"
                    ]
                ),
                checked,
                tr("save"),
                url_for(
                    "delete_calendar",
                    entry_id=row[
                        "id"
                    ],
                ),
                tr("delete"),
            )
        )

    add_form = (
        "<div class='card'>"

        "<h2>Add Tuesday Entry</h2>"

        "<form "
        "method='post' "
        "action='%s'>"

        "<div class='two'>"

        "<div>"

        "<label>Date</label>"

        "<input "
        "type='date' "
        "name='calendar_date' "
        "required>"

        "</div>"

        "<div>"

        "<label>Time</label>"

        "<input "
        "type='time' "
        "name='calendar_time' "
        "required>"

        "</div>"

        "</div>"

        "<label>%s</label>"
        "<input "
        "name='case_number' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='last_name' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='parties' "
        "required>"

        "<label>%s</label>"
        "<input "
        "name='hearing_nature' "
        "required>"

        "<label>%s</label>"

        "<select "
        "name='hearing_status'>"

        "<option>Scheduled</option>"
        "<option>Ongoing</option>"
        "<option>Completed</option>"
        "<option>Reset</option>"
        "<option>Postponed</option>"
        "<option>Cancelled</option>"

        "</select>"

        "<label>%s</label>"
        "<input "
        "name='courtroom'>"

        "<label>%s</label>"
        "<textarea "
        "name='remarks'>"
        "</textarea>"

        "<label>"

        "<input "
        "type='checkbox' "
        "name='public_visible' "
        "checked "
        "style='width:auto'>"

        " Publish to civilians"

        "</label>"

        "<button>%s</button>"

        "</form>"

        "</div>"
        % (
            url_for(
                "add_calendar"
            ),
            tr("case_number"),
            tr("last_name"),
            tr("parties"),
            tr("hearing_nature"),
            tr("hearing_status"),
            tr("courtroom"),
            tr("remarks"),
            tr("add"),
        )
    )

    content = (
        "<div class='card'>"

        "<h1>📅 %s</h1>"

        "<p>"
        "Staff can add and edit the Tuesday "
        "calendar. Civilians see entries "
        "marked for publication."
        "</p>"

        "</div>"

        "%s"

        "%s"
        % (
            tr(
                "manage_calendar"
            ),
            add_form,
            cards
            or (
                "<div class='card empty'>"
                "No Tuesday entries."
                "</div>"
            ),
        )
    )

    return page(
        tr("calendar"),
        content,
    )


@app.post(
    "/staff/calendar/add"
)
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

    if not all(
        values[:6]
    ):

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
                "<a class='button secondary' "
                "href='%s'>"
                "📎 %s"
                "</a>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=notice[
                            "attachment"
                        ],
                    ),
                    tr("open"),
                )
            )

        cards += (
            "<div class='notice'>"

            "<h3>%s</h3>"

            "<p>%s</p>"

            "%s"

            "<br><br>"

            "<form "
            "method='post' "
            "action='%s' "
            "style='display:inline'>"

            "<button "
            "class='danger' "
            "onclick=\""
            "return confirm("
            "'Delete this notice?');"
            "\">"

            "%s"

            "</button>"

            "</form>"

            "</div>"
            % (
                esc(
                    notice[
                        "title_en"
                    ]
                ),
                esc(
                    notice[
                        "body_en"
                    ]
                ),
                attachment,
                url_for(
                    "delete_notice",
                    notice_id=notice[
                        "id"
                    ],
                ),
                tr("delete"),
            )
        )

    content = (
        "<div class='card'>"

        "<h1>📢 %s</h1>"

        "<p>"
        "Staff can upload photos or documents "
        "with public announcements."
        "</p>"

        "<form "
        "method='post' "
        "action='%s' "
        "enctype='multipart/form-data'>"

        "<label>"
        "English Title"
        "</label>"

        "<input "
        "name='title_en' "
        "required>"

        "<label>"
        "Filipino Title"
        "</label>"

        "<input "
        "name='title_fil' "
        "required>"

        "<label>"
        "English Notice"
        "</label>"

        "<textarea "
        "name='body_en' "
        "required>"
        "</textarea>"

        "<label>"
        "Filipino Notice"
        "</label>"

        "<textarea "
        "name='body_fil' "
        "required>"
        "</textarea>"

        "<label>%s</label>"

        "<input "
        "type='file' "
        "name='attachment'>"

        "<button>%s</button>"

        "</form>"

        "</div>"

        "<div class='card'>"

        "%s"

        "</div>"
        % (
            tr("manage_notices"),
            url_for(
                "add_notice"
            ),
            tr("attachment"),
            tr("upload"),
            cards
            or (
                "<p class='empty'>"
                "No notices yet."
                "</p>"
            ),
        )
    )

    return page(
        tr("notices"),
        content,
    )


@app.post(
    "/staff/notices/add"
)
@staff_required
def add_notice():

    form = request.form

    if not all(
        form.get(
            key,
            "",
        ).strip()
        for key in [
            "title_en",
            "title_fil",
            "body_en",
            "body_fil",
        ]
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

    try:

        filename, original = (
            save_upload(
                request.files.get(
                    "attachment"
                )
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
            form[
                "title_en"
            ].strip(),

            form[
                "title_fil"
            ].strip(),

            form[
                "body_en"
            ].strip(),

            form[
                "body_fil"
            ].strip(),

            filename,

            original,

            1,

            now(),

            now(),
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "notice_created",
        form[
            "title_en"
        ],
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
def delete_notice(
    notice_id
):

    connection = get_db()

    notice = connection.execute(
        """
        SELECT attachment
        FROM notices
        WHERE id = ?
        """,
        (notice_id,),
    ).fetchone()

    if (
        notice
        and notice[
            "attachment"
        ]
    ):

        file_path = (
            UPLOAD_DIR
            / notice[
                "attachment"
            ]
        )

        if file_path.exists():

            try:

                file_path.unlink()

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

        source = ""

        if row[
            "source_url"
        ]:

            source = (
                "<a class='button secondary' "
                "href='%s' "
                "target='_blank' "
                "rel='noopener'>"
                "%s"
                "</a> "
                % (
                    esc(
                        row[
                            "source_url"
                        ]
                    ),
                    tr(
                        "official_source"
                    ),
                )
            )

        file_link = ""

        if row[
            "file_name"
        ]:

            file_link = (
                "<a class='button secondary' "
                "href='%s'>"
                "%s"
                "</a>"
                % (
                    url_for(
                        "uploaded_file",
                        filename=row[
                            "file_name"
                        ],
                    ),
                    tr("open"),
                )
            )

        cards += (
            "<div class='notice'>"

            "<span class='status'>%s</span>"

            "<h3>%s</h3>"

            "<p>%s</p>"

            "%s%s"

            "<form "
            "method='post' "
            "action='%s' "
            "style='display:inline'>"

            "<button "
            "class='danger'>"
            "%s"
            "</button>"

            "</form>"

            "</div>"
            % (
                esc(
                    row[
                        "category"
                    ]
                ),
                esc(
                    row[
                        "title"
                    ]
                ),
                esc(
                    row[
                        "description"
                    ]
                ),
                source,
                file_link,
                url_for(
                    "delete_law",
                    law_id=row[
                        "id"
                    ],
                ),
                tr("delete"),
            )
        )

    content = (
        "<div class='card'>"

        "<h1>⚖️ %s</h1>"

        "<p>"
        "Add Philippine laws, Supreme Court "
        "decisions, rules and other official "
        "legal resources."
        "</p>"

        "<form "
        "method='post' "
        "action='%s' "
        "enctype='multipart/form-data'>"

        "<label>Category</label>"

        "<select name='category'>"

        "<option>"
        "Philippine Laws"
        "</option>"

        "<option>"
        "Supreme Court Decisions"
        "</option>"

        "<option>"
        "Rules of Court"
        "</option>"

        "<option>"
        "Supreme Court Rules"
        "</option>"

        "<option>"
        "Administrative Matters"
        "</option>"

        "<option>"
        "Other Official Resource"
        "</option>"

        "</select>"

        "<label>Title</label>"

        "<input "
        "name='title' "
        "required>"

        "<label>Description</label>"

        "<textarea "
        "name='description'>"
        "</textarea>"

        "<label>"
        "Official Source URL"
        "</label>"

        "<input "
        "type='url' "
        "name='source_url'>"

        "<label>Document</label>"

        "<input "
        "type='file' "
        "name='file'>"

        "<button>%s</button>"

        "</form>"

        "</div>"

        "<div class='card'>"

        "%s"

        "</div>"
        % (
            tr(
                "manage_laws"
            ),
            url_for(
                "add_law"
            ),
            tr("add"),
            cards
            or (
                "<p class='empty'>"
                "No legal resources yet."
                "</p>"
            ),
        )
    )

    return page(
        tr("laws"),
        content,
    )


@app.post(
    "/staff/laws/add"
)
@staff_required
def add_law():

    form = request.form

    title = form.get(
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

        filename, original = (
            save_upload(
                request.files.get(
                    "file"
                )
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
            form.get(
                "category",
                "",
            ).strip(),

            title,

            form.get(
                "description",
                "",
            ).strip(),

            form.get(
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

    audit(
        "legal_resource_created",
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
def delete_law(
    law_id
):

    connection = get_db()

    resource = connection.execute(
        """
        SELECT file_name
        FROM legal_resources
        WHERE id = ?
        """,
        (law_id,),
    ).fetchone()

    if (
        resource
        and resource[
            "file_name"
        ]
    ):

        path = (
            UPLOAD_DIR
            / resource[
                "file_name"
            ]
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

    audit(
        "legal_resource_deleted",
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

    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY category
        """
    ).fetchall()

    connection.close()

    cards = ""

    for row in rows:

        title = (
            row[
                "title_fil"
            ]
            if lang() == "fil"
            else row[
                "title_en"
            ]
        )

        description = (
            row[
                "description_fil"
            ]
            if lang() == "fil"
            else row[
                "description_en"
            ]
        )

        cards += (
            "<div class='card'>"

            "<h2>%s</h2>"

            "<div class='notice'>"

            "<strong>"
            "Checklist from the supplied "
            "court requirement notice:"
            "</strong>"

            "%s"

            "</div>"

            "<p>"
            "<strong>"
            "Current uploaded description:"
            "</strong>"
            "<br>"
            "%s"
            "</p>"

            "<form "
            "method='post' "
            "action='%s' "
            "enctype='multipart/form-data'>"

            "<label>"
            "Description"
            "</label>"

            "<textarea "
            "name='description'>"
            "%s"
            "</textarea>"

            "<label>"
            "Official Document"
            "</label>"

            "<input "
            "type='file' "
            "name='document'>"

            "<button>%s</button>"

            "</form>"

            "</div>"
            % (
                esc(title),
                requirement_details(
                    row[
                        "category"
                    ]
                ),
                esc(
                    description
                    or tr(
                        "not_uploaded"
                    )
                ),
                url_for(
                    "update_requirement",
                    category=row[
                        "category"
                    ],
                ),
                esc(
                    description
                ),
                tr("save"),
            )
        )

    content = (
        "<div class='card'>"

        "<h1>📄 %s</h1>"

        "<p>"
        "Manage posting bail bond, cash bond "
        "and clearance requirements."
        "</p>"

        "</div>"

        "%s"
        % (
            tr(
                "manage_requirements"
            ),
            cards,
        )
    )

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

        filename, original = (
            save_upload(
                request.files.get(
                    "document"
                )
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

    for staff in rows:

        controls = (
            "<form "
            "method='post' "
            "action='%s' "
            "style='display:inline'>"

            "<button>%s</button>"

            "</form>"
            % (
                url_for(
                    "toggle_staff",
                    staff_id=staff[
                        "id"
                    ],
                ),
                (
                    "Disable"
                    if staff[
                        "active"
                    ]
                    else "Enable"
                ),
            )
        )

        if staff[
            "username"
        ] != "admin":

            controls += (
                "<form "
                "method='post' "
                "action='%s' "
                "style='display:inline'>"

                "<button "
                "class='danger' "
                "onclick=\""
                "return confirm("
                "'Delete this staff account?');"
                "\">"

                "%s"

                "</button>"

                "</form>"
                % (
                    url_for(
                        "delete_staff",
                        staff_id=staff[
                            "id"
                        ],
                    ),
                    tr("delete"),
                )
            )

        table += (
            "<tr>"

            "<td>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"

            "<td>"
            "<span class='status'>%s</span>"
            "</td>"

            "<td>%s</td>"

            "</tr>"
            % (
                esc(
                    staff[
                        "username"
                    ]
                ),
                esc(
                    staff[
                        "email"
                    ]
                ),
                esc(
                    staff[
                        "role"
                    ]
                ),
                (
                    "Active"
                    if staff[
                        "active"
                    ]
                    else "Disabled"
                ),
                controls,
            )
        )

    content = (
        "<div class='card'>"

        "<h1>👥 %s</h1>"

        "<p>"
        "Only administrators can add "
        "or manage staff accounts."
        "</p>"

        "</div>"

        "<div class='card'>"

        "<h2>➕ %s</h2>"

        "<form "
        "method='post' "
        "action='%s'>"

        "<label>%s</label>"

        "<input "
        "type='email' "
        "name='email' "
        "required>"

        "<label>%s</label>"

        "<input "
        "name='username' "
        "required "
        "autocomplete='off'>"

        "<label>%s</label>"

        "<input "
        "type='password' "
        "name='password' "
        "minlength='8' "
        "required "
        "autocomplete='new-password'>"

        "<label>%s</label>"

        "<select name='role'>"

        "<option "
        "value='staff'>"
        "Staff"
        "</option>"

        "<option "
        "value='admin'>"
        "Administrator"
        "</option>"

        "</select>"

        "<button>%s</button>"

        "</form>"

        "</div>"

        "<div class='card table-wrap'>"

        "<table>"

        "<thead>"

        "<tr>"

        "<th>Username</th>"
        "<th>Email</th>"
        "<th>Role</th>"
        "<th>Status</th>"
        "<th>Actions</th>"

        "</tr>"

        "</thead>"

        "<tbody>%s</tbody>"

        "</table>"

        "</div>"
        % (
            tr(
                "staff_accounts"
            ),
            tr("add_staff"),
            url_for(
                "add_staff"
            ),
            tr("email"),
            tr("username"),
            tr("password"),
            tr("role"),
            tr("add_staff"),
            table,
        )
    )

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
    )

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
            "Username, email and password "
            "are required.",
            "danger",
        )

        return redirect(
            url_for(
                "staff_accounts"
            )
        )

    if len(password) < 8:

        flash(
            "Password must contain at least "
            "8 characters.",
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
def toggle_staff(
    staff_id
):

    connection = get_db()

    staff = connection.execute(
        """
        SELECT
            username,
            active
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if staff is None:

        connection.close()

        abort(404)

    if staff[
        "username"
    ] == "admin":

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
            0
            if staff[
                "active"
            ]
            else 1,
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

    if staff[
        "username"
    ] == "admin":

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
# HEALTH CHECK
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
def error_403(
    error
):

    content = (
        "<div class='card empty'>"
        "<h1>403</h1>"
        "<h2>Access Denied</h2>"
        "<p>"
        "You do not have permission "
        "to access this page."
        "</p>"
        "<a class='button' href='%s'>"
        "Home"
        "</a>"
        "</div>"
        % url_for(
            "home"
        )
    )

    return (
        page(
            "403",
            content,
        ),
        403,
    )


@app.errorhandler(404)
def error_404(
    error
):

    content = (
        "<div class='card empty'>"
        "<h1>404</h1>"
        "<h2>Page Not Found</h2>"
        "<p>"
        "The requested page could not "
        "be found."
        "</p>"
        "<a class='button' href='%s'>"
        "Home"
        "</a>"
        "</div>"
        % url_for(
            "home"
        )
    )

    return (
        page(
            "404",
            content,
        ),
        404,
    )


@app.errorhandler(413)
def error_413(
    error
):

    content = (
        "<div class='card empty'>"
        "<h1>413</h1>"
        "<h2>File Too Large</h2>"
        "<p>"
        "Maximum upload size is 20 MB."
        "</p>"
        "<a class='button' href='%s'>"
        "Home"
        "</a>"
        "</div>"
        % url_for(
            "home"
        )
    )

    return (
        page(
            "413",
            content,
        ),
        413,
    )


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def security_headers(
    response
):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = (
        "strict-origin-when-cross-origin"
    )

    return response


# ============================================================
# APPLICATION START
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
