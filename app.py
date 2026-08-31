import os
import html
import sqlite3
import secrets

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
# Features:
#
# - Public home page
# - About Us
# - News and Announcements
# - Contact Us
# - Google Maps
# - Public case search
# - Case number + last name BOTH required
# - Public case information
# - Tuesday Calendar
# - Staff login
# - Admin login
# - Staff account management
# - Add / edit / delete cases
# - Edit hearing nature
# - Edit hearing status
# - Add / edit / delete Tuesday calendar entries
# - Upload notice photos/documents
# - Bond requirements
# - Clearance requirements
# - Legal resources
# - Laws / decisions / rules links
# - English / Filipino
# - Light / Dark mode
# - Automatic logout
# - Security headers
#
# IMPORTANT:
# This is a prototype court-information application.
# Before using real confidential judicial records, the system
# must undergo the appropriate security, privacy, authentication,
# database, document-storage, backup, and deployment review.
#
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


DATABASE = (
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
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "PLEASE-CHANGE-THIS-SECRET-KEY",
)


# ============================================================
# SESSION SETTINGS
# ============================================================

app.config[
    "SESSION_COOKIE_HTTPONLY"
] = True


app.config[
    "SESSION_COOKIE_SAMESITE"
] = "Lax"


app.config[
    "MAX_CONTENT_LENGTH"
] = (
    20 * 1024 * 1024
)


if os.environ.get(
    "RENDER"
):

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


COURT_SHORT_NAME = (
    "MCTC Silang-Amadeo"
)


COURT_ADDRESS = (
    "PNP Bldg, Plaza Libertad, "
    "Poblacion 2, Silang, Cavite"
)


COURT_PHONE = (
    "09284621305"
)


COURT_EMAIL = (
    "mctc2sad000@judiciary.gov.ph"
)


# Google Maps search link based on the supplied address.
GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/"
    "?api=1"
    "&query="
    "Municipal+Circuit+Trial+Court+"
    "Silang+Amadeo+Cavite"
)


LOGO_FILENAME = (
    "image0.png"
)


# ============================================================
# FILE TYPES
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

        "login": "Log In",

        "cases": "Cases",

        "case": "Case",

        "hearing": "Hearing",

        "hearings": "Hearings",

        "notices": "Notices",

        "staff_accounts": "Staff Accounts",

        "manage_cases": "Manage Cases",

        "manage_calendar": (
            "Manage Tuesday Calendar"
        ),

        "manage_notices": (
            "Manage Notices"
        ),

        "manage_laws": (
            "Manage Legal Resources"
        ),

        "manage_requirements": (
            "Manage Requirements"
        ),

        "add_case": "Add Case",

        "edit_case": "Edit Case",

        "delete_case": "Delete Case",

        "add_staff": "Add Staff Account",

        "username": "Username",

        "password": "Password",

        "email": "Email Address",

        "role": "Role",

        "case_number": "Case Number",

        "last_name": (
            "Last Name / Party Name"
        ),

        "parties": "Parties",

        "case_title": "Case Title",

        "case_type": "Case Type",

        "status": "Status",

        "nature": "Nature",

        "description": "Description",

        "hearing_date": "Hearing Date",

        "hearing_time": "Hearing Time",

        "hearing_nature": (
            "Nature of Hearing"
        ),

        "hearing_status": (
            "Hearing Status"
        ),

        "courtroom": "Courtroom",

        "remarks": "Remarks",

        "search_case": (
            "Search for a Case"
        ),

        "search_instruction": (
            "You must enter BOTH the complete "
            "case number and the last name "
            "or party name."
        ),

        "how_search": "How to Search",

        "step_one": (
            "Enter the complete case number."
        ),

        "step_two": (
            "Enter the last name of a party."
        ),

        "step_three": (
            "Both fields are required."
        ),

        "step_four": (
            "Click Search Case."
        ),

        "both_required": (
            "Both the case number and last "
            "name / party name are required."
        ),

        "no_results": (
            "No matching public case was found."
        ),

        "invalid_login": (
            "Invalid username or password."
        ),

        "login_required": (
            "Please log in as authorized staff."
        ),

        "welcome": "Welcome, Court Staff",

        "quick_actions": "Quick Actions",

        "save": "Save",

        "add": "Add",

        "edit": "Edit",

        "delete": "Delete",

        "cancel": "Cancel",

        "view": "View",

        "open": "Open",

        "upload": "Upload",

        "attachment": (
            "Photo / Document"
        ),

        "phone": "Telephone",

        "address": "Address",

        "official_source": (
            "Official Source"
        ),

        "open_maps": "Open Google Maps",

        "copyright": (
            "© 2026 Municipal Circuit Trial "
            "Court of Silang-Amadeo, Cavite. "
            "All rights reserved."
        ),

        "not_uploaded": (
            "Not yet uploaded"
        ),

    },

    "fil": {

        "home": "Home",

        "about": "Tungkol sa Amin",

        "news": (
            "Balita at mga Anunsyo"
        ),

        "contact": (
            "Makipag-ugnayan"
        ),

        "staff_login": (
            "Staff Login"
        ),

        "search": (
            "Maghanap ng Kaso"
        ),

        "calendar": (
            "Kalendaryo ng Martes"
        ),

        "laws": (
            "Mga Batas, Desisyon at Alituntunin"
        ),

        "requirements": (
            "Mga Kinakailangan"
        ),

        "bonds": (
            "Mga Kinakailangan para sa Bonds"
        ),

        "clearance": (
            "Mga Kinakailangan para sa Clearance"
        ),

        "dashboard": (
            "Dashboard ng Staff"
        ),

        "logout": (
            "Mag-Logout"
        ),

        "login": (
            "Mag-Login"
        ),

        "cases": (
            "Mga Kaso"
        ),

        "case": "Kaso",

        "hearing": "Pagdinig",

        "hearings": "Mga Pagdinig",

        "notices": "Mga Abiso",

        "staff_accounts": (
            "Mga Account ng Staff"
        ),

        "manage_cases": (
            "Pamahalaan ang mga Kaso"
        ),

        "manage_calendar": (
            "Pamahalaan ang Kalendaryo ng Martes"
        ),

        "manage_notices": (
            "Pamahalaan ang mga Abiso"
        ),

        "manage_laws": (
            "Pamahalaan ang Legal Resources"
        ),

        "manage_requirements": (
            "Pamahalaan ang mga Kinakailangan"
        ),

        "add_case": (
            "Magdagdag ng Kaso"
        ),

        "edit_case": (
            "I-edit ang Kaso"
        ),

        "delete_case": (
            "Burahin ang Kaso"
        ),

        "add_staff": (
            "Magdagdag ng Staff Account"
        ),

        "username": "Username",

        "password": "Password",

        "email": "Email Address",

        "role": "Role",

        "case_number": (
            "Numero ng Kaso"
        ),

        "last_name": (
            "Apelyido / Pangalan ng Partido"
        ),

        "parties": "Mga Partido",

        "case_title": (
            "Pamagat ng Kaso"
        ),

        "case_type": (
            "Uri ng Kaso"
        ),

        "status": "Katayuan",

        "nature": "Uri",

        "description": (
            "Deskripsyon"
        ),

        "hearing_date": (
            "Petsa ng Pagdinig"
        ),

        "hearing_time": (
            "Oras ng Pagdinig"
        ),

        "hearing_nature": (
            "Uri ng Pagdinig"
        ),

        "hearing_status": (
            "Katayuan ng Pagdinig"
        ),

        "courtroom": (
            "Silid ng Hukuman"
        ),

        "remarks": "Mga Tala",

        "search_case": (
            "Maghanap ng Kaso"
        ),

        "search_instruction": (
            "Kinakailangang ilagay ang PAREHONG "
            "case number at apelyido o pangalan "
            "ng partido."
        ),

        "how_search": (
            "Paano Maghanap"
        ),

        "step_one": (
            "Ilagay ang buong case number."
        ),

        "step_two": (
            "Ilagay ang apelyido ng isang partido."
        ),

        "step_three": (
            "Kinakailangan ang parehong field."
        ),

        "step_four": (
            "I-click ang Maghanap."
        ),

        "both_required": (
            "Kinakailangan ang parehong case number "
            "at apelyido / pangalan ng partido."
        ),

        "no_results": (
            "Walang nakitang pampublikong kaso."
        ),

        "invalid_login": (
            "Mali ang username o password."
        ),

        "login_required": (
            "Mag-login bilang awtorisadong staff."
        ),

        "welcome": (
            "Maligayang Pagdating, Kawani ng Hukuman"
        ),

        "quick_actions": (
            "Mabilis na Aksyon"
        ),

        "save": "I-save",

        "add": "Magdagdag",

        "edit": "I-edit",

        "delete": "Burahin",

        "cancel": "Kanselahin",

        "view": "Tingnan",

        "open": "Buksan",

        "upload": "Mag-upload",

        "attachment": (
            "Larawan / Dokumento"
        ),

        "phone": "Telepono",

        "address": "Address",

        "official_source": (
            "Opisyal na Source"
        ),

        "open_maps": (
            "Buksan ang Google Maps"
        ),

        "copyright": (
            "© 2026 Municipal Circuit Trial "
            "Court of Silang-Amadeo, Cavite. "
            "Lahat ng karapatan ay nakalaan."
        ),

        "not_uploaded": (
            "Hindi pa naiu-upload"
        ),

    },

}


def tr(key):

    language = session.get(
        "language",
        "en",
    )

    if language not in TRANSLATIONS:

        language = "en"

    return TRANSLATIONS[
        language
    ].get(
        key,
        TRANSLATIONS["en"].get(
            key,
            key,
        ),
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

    # --------------------------------------------------------
    # REQUIREMENT PLACEHOLDERS
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

        found = connection.execute(
            """
            SELECT id
            FROM requirements
            WHERE category = ?
            """,
            (item[0],),
        ).fetchone()

        if found is None:

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
                    current_time(),
                ),
            )

    # --------------------------------------------------------
    # INITIAL ADMIN
    # --------------------------------------------------------
    #
    # Requested login:
    #
    # Username: admin
    # Password: admin123
    #
    # For real production use, change this password.
    #
    # --------------------------------------------------------

    administrator = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE username = ?
        """,
        ("admin",),
    ).fetchone()

    if administrator is None:

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
                current_time(),
            ),
        )

    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# AUTHORIZATION
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


# ============================================================
# AUDIT
# ============================================================

def write_audit(
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
            current_time(),
        ),
    )

    connection.commit()

    connection.close()


# ============================================================
# FILE HELPERS
# ============================================================

def save_upload(upload):

    if upload is None:
        return None, None

    if not upload.filename:
        return None, None

    original = secure_filename(
        upload.filename
    )

    if not original:
        return None, None

    extension = Path(
        original
    ).suffix.lower().lstrip(".")

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "That file type is not allowed."
        )

    generated = (
        secrets.token_hex(12)
        + "_"
        + original
    )

    destination = (
        UPLOAD_DIR
        / generated
    )

    upload.save(
        destination
    )

    return generated, original


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

    notice_cards = ""

    for notice in notices:

        if current_language() == "fil":

            title = notice[
                "title_fil"
            ]

            message = notice[
                "body_fil"
            ]

        else:

            title = notice[
                "title_en"
            ]

            message = notice[
                "body_en"
            ]

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

        notice_cards += f"""

        <article class="notice">

            <h3>
                {escape_html(title)}
            </h3>

            <p>
                {escape_html(message)}
            </p>

            {attachment}

        </article>

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
            Court information,
            public case searching,
            announcements and the
            Tuesday calendar.
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


    <section class="grid">

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
                View the publicly published
                Tuesday court calendar.
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
                Read court announcements
                and notices.
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
                Browse legal resources
                published by authorized staff.
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

    </section>


    <section class="card">

        <h2>
            ⚠️
            {tr("suspension")}
        </h2>

        <p>
            A hearing should not be assumed
            to be suspended, postponed or
            cancelled unless an official
            court notice confirms the change.
        </p>

    </section>


    <section class="card">

        <h2>
            📢
            {tr("news")}
        </h2>

        {
            notice_cards
            or
            '<p class="small">No announcements yet.</p>'
        }

    </section>

    """

    return render_page(
        tr("home"),
        body,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route(
    "/about"
)
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
            This portal provides approved
            public court information,
            announcements, schedules and
            legal-resource links.
        </p>

        <div class="notice warning">

            <strong>
                Important
            </strong>

            <p>
                Online information does not
                replace official court records,
                orders, notices or certified
                documents.
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

@app.route(
    "/contact"
)
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

            {escape_html(
                COURT_ADDRESS
            )}

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
                {escape_html(
                    COURT_PHONE
                )}
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
                {escape_html(
                    COURT_EMAIL
                )}
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

@app.route(
    "/news"
)
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

        if current_language() == "fil":

            title = notice[
                "title_fil"
            ]

            message = notice[
                "body_fil"
            ]

        else:

            title = notice[
                "title_en"
            ]

            message = notice[
                "body_en"
            ]

        body += f"""

        <article class="card">

            <h2>
                {escape_html(title)}
            </h2>

            <p>
                {escape_html(message)}
            </p>

        """

        if notice["attachment"]:

            body += f"""

            <p>

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

            </p>

            """

        body += """

        </article>

        """

    if not notices:

        body += """

        <div class="card empty">

            No notices have been published.

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

    number = request.values.get(
        "case_number",
        "",
    ).strip()

    last_name = request.values.get(
        "last_name",
        "",
    ).strip()

    case = None

    attempted = (
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
                LIMIT 1
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
                    {tr("step_one")}
                </li>

                <li>
                    {tr("step_two")}
                </li>

                <li>
                    {tr("step_three")}
                </li>

                <li>
                    {tr("step_four")}
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


            <button type="submit">

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
        ORDER BY
            hearing_date,
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
                {tr("parties")}:
            </strong>

            {escape_html(
                case["parties"]
            )}

        </p>

        <p>

            <strong>
                {tr("case_type")}:
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

        {hearing_html}

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
            View the Tuesday court calendar
            published by authorized staff.
        </p>

        <div class="notice warning">

            Hearing schedules may change.
            Please confirm important details
            with the court.

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
                    <td
                        colspan="7"
                        class="empty"
                    >
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
# REQUIREMENTS PUBLIC PAGE
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

            title = row[
                "title_fil"
            ]

            description = (
                row[
                    "description_fil"
                ]
                or tr("not_uploaded")
            )

        else:

            title = row[
                "title_en"
            ]

            description = (
                row[
                    "description_en"
                ]
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
# PUBLIC LAWS PAGE
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
            {tr("laws")}
        </h1>

        <p>
            References may include Philippine laws,
            Supreme Court decisions, rules,
            issuances and other official legal
            resources added by authorized staff.
        </p>

        <div class="notice warning">

            Verify legal authorities against an
            authoritative current source.

        </div>

    </div>

    """

    for resource in resources:

        body += f"""

        <div class="card">

            <span class="status">
                {escape_html(
                    resource["category"]
                )}
            </span>

            <h2>
                {escape_html(
                    resource["title"]
                )}
            </h2>

            <p>
                {escape_html(
                    resource["description"]
                )}
            </p>

        """

        if resource[
            "source_url"
        ]:

            body += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    resource["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {tr("official_source")}
            </a>

            """

        if resource[
            "file_name"
        ]:

            body += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=resource['file_name']
                )}"
            >
                {tr("open")}
            </a>

            """

        body += """

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
    ],
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
            staff is not None
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

            write_audit(
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


            <button
                type="submit"
            >
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
    ],
)
def logout():

    username = session.get(
        "staff_username",
        "unknown",
    )

    if session.get(
        "staff_logged_in",
        False,
    ):

        write_audit(
            "logout",
            username,
        )

    session.clear()

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

    resource_count = db.execute(
        "SELECT COUNT(*) FROM legal_resources"
    ).fetchone()[0]

    db.close()

    body = f"""

    <section class="hero">

        <h1>
            {tr("welcome")}
        </h1>

        <p>
            Manage the court information
            portal from one place.
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
                {resource_count}
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

                <h3>
                    📋
                    {tr("manage_cases")}
                </h3>

                <p class="small">
                    Add, edit and delete cases.
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

                <h3>
                    📢
                    {tr("manage_notices")}
                </h3>

                <p class="small">
                    Upload photos or documents.
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

                <h3>
                    📄
                    {tr("manage_requirements")}
                </h3>

                <p class="small">
                    Manage bond and clearance
                    requirements.
                </p>

            </a>


    """

    if session.get(
        "staff_role"
    ) == "admin":

        body += f"""

            <a
                class="card"
                href="{url_for(
                    'staff_accounts'
                )}"
            >

                <h3>
                    👥
                    {tr("staff_accounts")}
                </h3>

                <p class="small">
                    Add and manage staff accounts.
                </p>

            </a>

        """

    body += """

        </div>

    </section>

    """

    return render_page(
        tr("dashboard"),
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
                            class="danger"
                            type="submit"
                        >
                            {tr("delete")}
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
                No cases have been added.
            </td>

        </tr>

        """

    body = f"""

    <div class="flex">

        <h1>
            📋
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

                {rows}

            </tbody>

        </table>

    </div>

    """

    return render_page(
        tr("cases"),
        body,
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

        if not (
            case_number
            and last_name
            and parties
            and case_title
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

        write_audit(
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

        write_audit(
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

    options = ""

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

        options += f"""

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

                {options}

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


            <button
                type="submit"
            >
                {tr("save")}
            </button>

        </form>

    </div>

    """

    return render_page(
        tr("edit_case"),
        body,
    )


# ============================================================
# STAFF DELETE CASE
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

    if case is None:

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

    write_audit(
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
    ],
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

    if case is None:

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

        write_audit(
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

    hearing_nature = (
        hearing["hearing_nature"]
        if hearing
        else "Initial Hearing"
    )

    hearing_status = (
        hearing["hearing_status"]
        if hearing
        else "Scheduled"
    )

    courtroom = (
        hearing["courtroom"]
        if hearing
        else ""
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

        "Hearing",

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

    nature_options = ""

    for value in natures:

        selected = (
            "selected"
            if value == hearing_nature
            else ""
        )

        nature_options += f"""

        <option {selected}>
            {escape_html(value)}
        </option>

        """

    status_options = ""

    for value in statuses:

        selected = (
            "selected"
            if value == hearing_status
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


        <div class="notice">

            Staff can change the
            <strong>nature of hearing</strong>
            and the
            <strong>hearing status</strong>
            here.

        </div>


        <form method="post">

            <label>
                {tr("hearing_date")}
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
                {tr("hearing_time")}
            </label>

            <input
                type="time"
                name="hearing_time"
                value="{escape_html(
                    hearing_time
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
                    courtroom
                )}"
            >


            <label>
                {tr("remarks")}
            </label>

            <textarea
                name="remarks"
            >{escape_html(
                remarks
            )}</textarea>


            <button
                type="submit"
            >
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

    cards = ""

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
                {escape_html(value)}
            </option>

            """

        cards += f"""

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

                    <button
                        type="submit"
                    >
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
            Add and edit Tuesday calendar entries.
            Civilian users only see entries marked
            for publication.
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


    {cards or
    '<div class="card empty">No Tuesday entries.</div>'}

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

            current_time(),

            current_time(),
        ),
    )

    db.commit()

    db.close()

    write_audit(
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

            current_time(),

            entry_id,
        ),
    )

    db.commit()

    db.close()

    write_audit(
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

    write_audit(
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

    cards = ""

    for notice in notices:

        title = (
            notice["title_fil"]
            if current_language() == "fil"
            else notice["title_en"]
        )

        cards += f"""

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

            cards += f"""

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

        cards += f"""

            <br>
            <br>

            <form
                method="post"
                action="{url_for(
                    'delete_notice',
                    notice_id=notice['id']
                )}"
            >

                <button
                    type="submit"
                    class="danger"
                    onclick="
                        return confirm(
                            'Delete this notice?'
                        );
                    "
                >
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
            Staff can upload a photo or document
            together with a public notice.
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
                {tr("attachment")}
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

        {cards or
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
            current_time(),
            current_time(),
        ),
    )

    db.commit()

    db.close()

    write_audit(
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

    if notice:

        if notice["attachment"]:

            path = (
                UPLOAD_DIR
                / notice["attachment"]
            )

            if path.exists():

                try:

                    path.unlink()

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

    write_audit(
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

    resources = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    cards = ""

    for resource in resources:

        cards += f"""

        <div class="notice">

            <span class="status">
                {escape_html(
                    resource["category"]
                )}
            </span>

            <h3>
                {escape_html(
                    resource["title"]
                )}
            </h3>

            <p>
                {escape_html(
                    resource["description"]
                )}
            </p>

        """

        if resource[
            "source_url"
        ]:

            cards += f"""

            <a
                class="button secondary"
                href="{escape_html(
                    resource["source_url"]
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {tr("official_source")}
            </a>

            """

        if resource[
            "file_name"
        ]:

            cards += f"""

            <a
                class="button secondary"
                href="{url_for(
                    'uploaded_file',
                    filename=resource['file_name']
                )}"
            >
                {tr("open")}
            </a>

            """

        cards += f"""

            <form
                method="post"
                action="{url_for(
                    'delete_law',
                    law_id=resource['id']
                )}"
                style="display:inline"
            >

                <button
                    type="submit"
                    class="danger"
                    onclick="
                        return confirm(
                            'Delete this resource?'
                        );
                    "
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

        {cards or
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
        ),
    )

    db.commit()

    db.close()

    write_audit(
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

    if row and row[
        "file_name"
    ]:

        path = (
            UPLOAD_DIR
            / row["file_name"]
        )

        if path.exists():

            try:

                path.unlink()

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

    write_audit(
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

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY category
        """
    ).fetchall()

    db.close()

    cards = ""

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

        cards += f"""

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
                    Official Document
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
            {tr("manage_requirements")}
        </h1>

        <p>
            Requirements for bonds and clearance
            start as "Not yet uploaded".
        </p>

    </div>


    {cards}

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
                current_time(),
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
                current_time(),
                category,
            ),
        )

    db.commit()

    db.close()

    write_audit(
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

        status_text = (
            "Active"
            if account["active"]
            else "Disabled"
        )

        toggle_text = (
            "Disable"
            if account["active"]
            else "Enable"
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
                    {status_text}
                </span>
            </td>

            <td>

                <form
                    method="post"
                    action="{url_for(
                        'toggle_staff',
                        staff_id=account['id']
                    )}"
                    style="display:inline"
                >

                    <button
                        type="submit"
                    >
                        {toggle_text}
                    </button>

                </form>

        """

        if account["username"] != "admin":

            rows += f"""

                <form
                    method="post"
                    action="{url_for(
                        'delete_staff',
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
            Administrator access is required.
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
                'add_staff'
            )}"
        >

            <label>
                {tr("email")}
            </label>

            <input
                type="email"
                name="email"
                required
            >


            <label>
                {tr("username")}
            </label>

            <input
                name="username"
                required
                autocomplete="off"
            >


            <label>
                {tr("password")}
            </label>

            <input
                type="password"
                name="password"
                minlength="8"
                required
                autocomplete="new-password"
            >


            <label>
                {tr("role")}
            </label>

            <select name="role">

                <option value="staff">
                    Staff
                </option>

                <option value="admin">
                    Administrator
                </option>

            </select>


            <button
                type="submit"
            >
                {tr("add_staff")}
            </button>

        </form>

    </div>


    <div class="card table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        Username
                    </th>

                    <th>
                        Email
                    </th>

                    <th>
                        Role
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
    ).strip()

    if role not in (
        "staff",
        "admin",
    ):

        role = "staff"

    if not (
        username
        and email
        and password
    ):

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
            "Password must contain at least 8 characters.",
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
                current_time(),
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

    write_audit(
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
def toggle_staff(staff_id):

    db = get_db()

    account = db.execute(
        """
        SELECT *
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if account is None:

        db.close()

        abort(404)

    if account["username"] == "admin":

        db.close()

        flash(
            "The primary admin cannot be disabled.",
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

    write_audit(
        "staff_status_changed",
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
def delete_staff(staff_id):

    db = get_db()

    account = db.execute(
        """
        SELECT *
        FROM staff
        WHERE id = ?
        """,
        (staff_id,),
    ).fetchone()

    if account is None:

        db.close()

        abort(404)

    if account["username"] == "admin":

        db.close()

        flash(
            "The primary admin cannot be deleted.",
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

    write_audit(
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
# PUBLIC UPLOADED FILES
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
        "service": COURT_SHORT_NAME,
    }


# ============================================================
# ERROR HANDLERS
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
            You do not have permission
            to access this page.
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
def add_security_headers(response):

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
# PAGE RENDERING
# ============================================================

def render_flash_messages():

    from flask import (
        get_flashed_messages
    )

    output = ""

    messages = get_flashed_messages(
        with_categories=True
    )

    for category, message in messages:

        output += f"""

        <div
            class="notice
            {escape_html(category)}"
        >

            {escape_html(message)}

        </div>

        """

    return output


def render_page(
    title,
    body,
):

    theme = session.get(
        "theme",
        "light",
    )

    language = session.get(
        "language",
        "en",
    )

    if language not in (
        "en",
        "fil",
    ):

        language = "en"

    language_switch = (
        "fil"
        if language == "en"
        else "en"
    )

    language_label = (
        "FIL"
        if language == "en"
        else "EN"
    )

    next_theme = (
        "dark"
        if theme == "light"
        else "light"
    )

    theme_label = (
        "🌙"
        if theme == "light"
        else "☀️"
    )

    staff_area = ""

    if session.get(
        "staff_logged_in",
        False,
    ):

        staff_area = f"""

        <a
            href="{url_for(
                'staff_dashboard'
            )}"
        >
            {tr("dashboard")}
        </a>

        <a
            href="{url_for(
                'staff_cases'
            )}"
        >
            {tr("cases")}
        </a>

        <a
            href="{url_for(
                'staff_calendar'
            )}"
        >
            {tr("calendar")}
        </a>

        <a
            href="{url_for(
                'staff_notices'
            )}"
        >
            {tr("notices")}
        </a>

        <a
            href="{url_for(
                'staff_laws'
            )}"
        >
            {tr("laws")}
        </a>

        <a
            href="{url_for(
                'staff_requirements'
            )}"
        >
            {tr("requirements")}
        </a>

        """

        if session.get(
            "staff_role"
        ) == "admin":

            staff_area += f"""

            <a
                href="{url_for(
                    'staff_accounts'
                )}"
            >
                {tr("staff_accounts")}
            </a>

            """

        staff_area += f"""

        <form
            method="post"
            action="{url_for(
                'logout'
            )}"
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

        staff_area = f"""

        <a
            href="{url_for(
                'staff_login'
            )}"
        >
            {tr("staff_login")}
        </a>

        """

    return f"""
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

<title>
{escape_html(title)}
-
{escape_html(COURT_SHORT_NAME)}
</title>


<style>

{STYLE}

</style>

</head>


<body
    class="{escape_html(theme)}"
>


<header
    class="site-header"
>

    <div
        class="header-inner"
    >

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
                alt="Court logo"
            >

            <div class="brand">

                <strong>
                    {escape_html(
                        COURT_NAME
                    )}
                </strong>

                <small>
                    Official Court
                    Information Portal
                </small>

            </div>

        </a>


        <nav class="nav">

            <a
                href="{url_for('home')}"
            >
                {tr("home")}
            </a>

            <a
                href="{url_for('about')}"
            >
                {tr("about")}
            </a>

            <a
                href="{url_for('news')}"
            >
                {tr("news")}
            </a>

            <a
                href="{url_for('contact')}"
            >
                {tr("contact")}
            </a>

            {staff_area}

            <a
                href="{url_for(
                    'change_language',
                    language=language_switch
                )}"
            >
                {language_label}
            </a>

            <a
                href="{url_for(
                    'change_theme',
                    theme=next_theme
                )}"
            >
                {theme_label}
            </a>

        </nav>

    </div>

</header>


<main
    class="container"
>

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
            href="tel:{escape_html(
                COURT_PHONE
            )}"
        >
            {escape_html(
                COURT_PHONE
            )}
        </a>

        <br>

        <a
            href="mailto:{escape_html(
                COURT_EMAIL
            )}"
        >
            {escape_html(
                COURT_EMAIL
            )}
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


# ============================================================
# STARTUP
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
