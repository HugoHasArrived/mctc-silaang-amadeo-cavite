"""
============================================================
MCTC SILANG-AMADEO COURT INFORMATION PORTAL
============================================================

Flask application for:

    Municipal Circuit Trial Court of Silang-Amadeo, Cavite

Address:
    PNP Bldg, Plaza Libertad, Poblacion 2
    Silang, Cavite

Phone:
    09284621305

------------------------------------------------------------
FEATURES
------------------------------------------------------------

PUBLIC
    - Home page
    - Public case search
    - Case number search
    - Party/name search
    - Public case details
    - Public hearing schedule
    - Public court notices
    - Suspension/postponement information
    - English / Filipino
    - Light / Dark mode
    - Court logo

STAFF
    - Staff login
    - Dashboard
    - Add cases
    - Edit cases
    - Delete cases
    - Add hearings
    - Delete hearings
    - Add document references
    - Remove document references
    - Publish notices
    - Delete notices
    - Audit log
    - Logout

IMPORTANT
    This application should be treated as a prototype until
    proper security, privacy, records-management, database,
    hosting, backup, and authorization requirements are
    completed.

------------------------------------------------------------
FILES
------------------------------------------------------------

Recommended repository:

    app.py
    requirements.txt
    render.yaml

    static/
        image0.png

No templates folder is required by this version because the
HTML is generated directly by this Python application.

------------------------------------------------------------
RENDER
------------------------------------------------------------

Build Command:

    pip install -r requirements.txt

Start Command:

    gunicorn app:app

------------------------------------------------------------
ENVIRONMENT VARIABLES
------------------------------------------------------------

SECRET_KEY
ADMIN_USERNAME
ADMIN_PASSWORD
DATABASE_PATH

Example:

    SECRET_KEY = a-long-random-secret
    ADMIN_USERNAME = your-staff-username
    ADMIN_PASSWORD = your-strong-password

Never put a real password directly into source code.

============================================================
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
import html
import secrets


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_RENDER"
)

app.config["DATABASE_PATH"] = os.environ.get(
    "DATABASE_PATH",
    "mctc_court.db"
)

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
    "Municipal Circuit Trial Court of "
    "Silang-Amadeo, Cavite"
)

COURT_SHORT_NAME = "MCTC Silang-Amadeo"

COURT_ADDRESS = (
    "PNP Bldg, Plaza Libertad, Poblacion 2, "
    "Silang, Cavite"
)

COURT_PHONE = "09284621305"

LOGO_FILENAME = "image0.png"


# ============================================================
# COLORS
# ============================================================

PRIMARY_PURPLE = "#7B2CBF"
SECONDARY_PURPLE = "#9D4EDD"
DARK_PURPLE = "#42105F"
LIGHT_PURPLE = "#EFE2F7"


# ============================================================
# LANGUAGES
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
        "language": "Language",
        "light": "Light",
        "dark": "Dark",
        "search_case": "Search for a Case",
        "case_number": "Case Number",
        "name": "Name / Party",
        "search_button": "Search",
        "view": "View",
        "results": "Results",
        "status": "Status",
        "hearing": "Hearing",
        "hearing_date": "Hearing Date",
        "hearing_time": "Hearing Time",
        "courtroom": "Courtroom",
        "official_notice": "Official Court Notice",
        "suspension": "Suspension / Postponement",
        "public_information": "Public Information",
        "staff_area": "Staff Area",
        "welcome": "Welcome",
        "manage_cases": "Manage Cases",
        "add_case": "Add Case",
        "edit_case": "Edit Case",
        "delete_case": "Delete Case",
        "save": "Save",
        "cancel": "Cancel",
        "parties": "Parties",
        "case_type": "Case Type",
        "title": "Case Title",
        "public_summary": "Public Summary",
        "internal_notes": "Internal Notes",
        "add_hearing": "Add Hearing",
        "purpose": "Purpose",
        "add_document": "Add Document",
        "display_name": "Display Name",
        "approved_url": "Approved URL",
        "public_access": "Publicly Accessible",
        "remove": "Remove",
        "danger_zone": "Danger Zone",
        "publish_notice": "Publish Court Notice",
        "notice_type": "Notice Type",
        "notice_title_en": "English Title",
        "notice_title_fil": "Filipino Title",
        "notice_body_en": "English Notice",
        "notice_body_fil": "Filipino Notice",
        "publish": "Publish",
        "no_results": "No matching cases were found.",
        "search_instruction_title": "How to search",
        "search_instruction_1": (
            "Enter the case number if you know it."
        ),
        "search_instruction_2": (
            "Or enter the name of a party."
        ),
        "search_instruction_3": (
            "You may use both fields together."
        ),
        "search_instruction_4": (
            "Click Search."
        ),
        "search_instruction_5": (
            "Open View beside the matching case."
        ),
        "privacy": "Privacy Reminder",
        "privacy_text": (
            "Only information approved for public release "
            "should appear on this public portal."
        ),
        "public_documents": "Public Documents",
        "no_public_documents": (
            "No public documents are currently available."
        ),
        "no_hearings": (
            "No hearing information is currently published."
        ),
        "court_notices": "Court Notices",
        "no_notices": (
            "No official notices are currently published."
        ),
        "suspension_information": (
            "Suspension and postponement information"
        ),
        "suspension_text": (
            "A hearing should not be assumed to be suspended "
            "or postponed unless an official court notice says so."
        ),
        "staff_login_title": "Authorized Staff Login",
        "username": "Username",
        "password": "Password",
        "login_button": "Log In",
        "staff_only": (
            "This area is for authorized court staff only."
        ),
        "logout_confirm": (
            "Are you sure you want to log out?"
        ),
        "dashboard_intro": (
            "Use the shortcuts below to manage court "
            "information."
        ),
        "total_cases": "Total Cases",
        "total_hearings": "Total Hearings",
        "total_notices": "Total Notices",
        "quick_actions": "Quick Actions",
        "recent_cases": "Recent Cases",
        "recent_notices": "Recent Notices",
        "no_cases": "No cases have been entered yet.",
        "create_case": "Create a new case",
        "manage_case_info": (
            "Search, edit, or remove case records."
        ),
        "manage_hearing_info": (
            "Review upcoming hearing information."
        ),
        "manage_notice_info": (
            "Publish official court announcements."
        ),
        "invalid_login": (
            "The username or password is incorrect."
        ),
        "logged_out": "You have been logged out.",
        "login_required": (
            "Please log in as authorized court staff."
        ),
        "case_created": "Case created successfully.",
        "case_updated": "Case updated successfully.",
        "case_deleted": "Case deleted successfully.",
        "hearing_added": "Hearing added successfully.",
        "hearing_deleted": "Hearing deleted successfully.",
        "document_added": "Document reference added.",
        "document_removed": "Document reference removed.",
        "notice_created": "Notice published successfully.",
        "notice_deleted": "Notice deleted successfully.",
        "not_found": "The requested information was not found.",
        "error": "Something went wrong.",
        "about_title": "About the Portal",
        "contact_title": "Contact the Court",
        "prototype_notice": (
            "Prototype portal. Verify important information "
            "with the court before relying on it."
        ),
    },

    "fil": {
        "home": "Home",
        "search": "Maghanap ng Kaso",
        "hearings": "Mga Pagdinig",
        "notices": "Mga Abiso",
        "login": "Pag-login ng Kawani",
        "dashboard": "Dashboard",
        "cases": "Mga Kaso",
        "logout": "Mag-logout",
        "about": "Tungkol",
        "contact": "Makipag-ugnayan",
        "language": "Wika",
        "light": "Maliwanag",
        "dark": "Madilim",
        "search_case": "Maghanap ng Kaso",
        "case_number": "Numero ng Kaso",
        "name": "Pangalan / Partido",
        "search_button": "Maghanap",
        "view": "Tingnan",
        "results": "Mga Resulta",
        "status": "Katayuan",
        "hearing": "Pagdinig",
        "hearing_date": "Petsa ng Pagdinig",
        "hearing_time": "Oras ng Pagdinig",
        "courtroom": "Silid ng Hukuman",
        "official_notice": "Opisyal na Abiso ng Hukuman",
        "suspension": "Suspensyon / Pagpapaliban",
        "public_information": "Pampublikong Impormasyon",
        "staff_area": "Lugar ng mga Kawani",
        "welcome": "Maligayang Pagdating",
        "manage_cases": "Pamahalaan ang mga Kaso",
        "add_case": "Magdagdag ng Kaso",
        "edit_case": "I-edit ang Kaso",
        "delete_case": "Burahin ang Kaso",
        "save": "I-save",
        "cancel": "Kanselahin",
        "parties": "Mga Partido",
        "case_type": "Uri ng Kaso",
        "title": "Pamagat ng Kaso",
        "public_summary": "Pampublikong Buod",
        "internal_notes": "Panloob na Tala",
        "add_hearing": "Magdagdag ng Pagdinig",
        "purpose": "Layunin",
        "add_document": "Magdagdag ng Dokumento",
        "display_name": "Pangalan ng Dokumento",
        "approved_url": "Aprubadong URL",
        "public_access": "Maaaring Tingnan ng Publiko",
        "remove": "Alisin",
        "danger_zone": "Lugar ng Panganib",
        "publish_notice": "Maglathala ng Abiso ng Hukuman",
        "notice_type": "Uri ng Abiso",
        "notice_title_en": "Pamagat sa Ingles",
        "notice_title_fil": "Pamagat sa Filipino",
        "notice_body_en": "Abiso sa Ingles",
        "notice_body_fil": "Abiso sa Filipino",
        "publish": "I-publish",
        "no_results": "Walang nakitang tumutugmang kaso.",
        "search_instruction_title": "Paano maghanap",
        "search_instruction_1": (
            "Ilagay ang numero ng kaso kung alam mo ito."
        ),
        "search_instruction_2": (
            "O ilagay ang pangalan ng isang partido."
        ),
        "search_instruction_3": (
            "Maaaring gamitin ang parehong field."
        ),
        "search_instruction_4": (
            "I-click ang Maghanap."
        ),
        "search_instruction_5": (
            "I-click ang Tingnan sa tabi ng kaso."
        ),
        "privacy": "Paalala sa Pribasiya",
        "privacy_text": (
            "Ang impormasyong aprubado lamang para sa "
            "publikong paglalabas ang dapat makita rito."
        ),
        "public_documents": "Mga Pampublikong Dokumento",
        "no_public_documents": (
            "Walang pampublikong dokumento na kasalukuyang "
            "magagamit."
        ),
        "no_hearings": (
            "Walang kasalukuyang inilalathalang impormasyon "
            "tungkol sa pagdinig."
        ),
        "court_notices": "Mga Abiso ng Hukuman",
        "no_notices": (
            "Walang kasalukuyang opisyal na abiso."
        ),
        "suspension_information": (
            "Impormasyon tungkol sa suspensyon at pagpapaliban"
        ),
        "suspension_text": (
            "Huwag ipagpalagay na suspendido o ipinagpaliban "
            "ang pagdinig maliban kung may opisyal na abiso "
            "mula sa hukuman."
        ),
        "staff_login_title": (
            "Pag-login ng Awtorisadong Kawani"
        ),
        "username": "Username",
        "password": "Password",
        "login_button": "Mag-login",
        "staff_only": (
            "Para lamang ito sa mga awtorisadong kawani "
            "ng hukuman."
        ),
        "logout_confirm": (
            "Sigurado ka bang gusto mong mag-logout?"
        ),
        "dashboard_intro": (
            "Gamitin ang mga shortcut sa ibaba upang "
            "pamahalaan ang impormasyon ng hukuman."
        ),
        "total_cases": "Kabuuang Kaso",
        "total_hearings": "Kabuuang Pagdinig",
        "total_notices": "Kabuuang Abiso",
        "quick_actions": "Mabilis na Aksyon",
        "recent_cases": "Mga Kamakailang Kaso",
        "recent_notices": "Mga Kamakailang Abiso",
        "no_cases": (
            "Wala pang nailagay na mga kaso."
        ),
        "create_case": "Gumawa ng bagong kaso",
        "manage_case_info": (
            "Maghanap, mag-edit, o mag-alis ng mga tala ng kaso."
        ),
        "manage_hearing_info": (
            "Tingnan ang impormasyon tungkol sa mga pagdinig."
        ),
        "manage_notice_info": (
            "Maglathala ng mga opisyal na anunsyo ng hukuman."
        ),
        "invalid_login": (
            "Mali ang username o password."
        ),
        "logged_out": "Ikaw ay naka-logout na.",
        "login_required": (
            "Mag-login bilang awtorisadong kawani."
        ),
        "case_created": "Matagumpay na nagawa ang kaso.",
        "case_updated": "Matagumpay na na-update ang kaso.",
        "case_deleted": "Matagumpay na nabura ang kaso.",
        "hearing_added": (
            "Matagumpay na naidagdag ang pagdinig."
        ),
        "hearing_deleted": (
            "Matagumpay na nabura ang pagdinig."
        ),
        "document_added": (
            "Naidagdag ang reference ng dokumento."
        ),
        "document_removed": (
            "Naalis ang reference ng dokumento."
        ),
        "notice_created": (
            "Matagumpay na nailathala ang abiso."
        ),
        "notice_deleted": (
            "Matagumpay na nabura ang abiso."
        ),
        "not_found": (
            "Hindi nahanap ang hinihinging impormasyon."
        ),
        "error": "May nangyaring problema.",
        "about_title": "Tungkol sa Portal",
        "contact_title": "Makipag-ugnayan sa Hukuman",
        "prototype_notice": (
            "Prototype portal. Suriin muna ang mahahalagang "
            "impormasyon sa hukuman bago ito gamitin bilang "
            "batayan."
        ),
    },
}


# ============================================================
# CHOICES
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
# CLEANING / ESCAPING
# ============================================================

def clean(value, limit=5000):
    if value is None:
        return ""

    return str(value).strip()[:limit]


def clean_case_number(value):
    return clean(
        value,
        100,
    ).upper()


def clean_name(value):
    return " ".join(
        clean(
            value,
            300,
        ).split()
    )


def safe(value):
    return html.escape(
        str(value or ""),
        quote=True,
    )


# ============================================================
# SESSION HELPERS
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


def labels():
    return TRANSLATIONS[
        current_language()
    ]


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
            current_username() or "system",
            clean(action, 200),
            clean(target, 500),
            now(),
        ),
    )

    connection.commit()
    connection.close()


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
                labels()["login_required"],
                "warning",
            )

            return redirect(
                url_for("staff_login")
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
                url_for("staff_login")
            )

        if current_role() != "admin":
            abort(403)

        return function(
            *args,
            **kwargs,
        )

    return wrapper


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
    # STAFF ACCOUNT
    # --------------------------------------------------------

    admin_username = os.environ.get(
        "ADMIN_USERNAME",
        "admin",
    )

    admin_password = os.environ.get(
        "ADMIN_PASSWORD",
        "admin123",
    )

    existing = connection.execute(
        """
        SELECT id
        FROM staff
        WHERE username = ?
        """,
        (
            admin_username,
        ),
    ).fetchone()

    if existing is None:
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
                admin_username,
                generate_password_hash(
                    admin_password
                ),
                "admin",
                1,
                now(),
            ),
        )

    # --------------------------------------------------------
    # DEMO RECORD
    # --------------------------------------------------------

    case_count = connection.execute(
        """
        SELECT COUNT(*)
        AS total
        FROM cases
        """
    ).fetchone()["total"]

    if case_count == 0:
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

        demo_id = connection.execute(
            """
            SELECT id
            FROM cases
            WHERE case_number = ?
            """,
            (
                "DEMO-001",
            ),
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
                demo_id,
                "2099-01-01",
                "09:00",
                "Demo Courtroom",
                "Demonstration only",
                "Scheduled",
            ),
        )

    # --------------------------------------------------------
    # DEMO NOTICE
    # --------------------------------------------------------

    notice_count = connection.execute(
        """
        SELECT COUNT(*)
        AS total
        FROM notices
        """
    ).fetchone()["total"]

    if notice_count == 0:
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
                    "announcements for changes to court "
                    "operations, hearing schedules, "
                    "suspensions, or postponements."
                ),
                (
                    "Mangyaring umasa sa mga opisyal na "
                    "abiso ng hukuman para sa mga pagbabago "
                    "sa operasyon, iskedyul ng pagdinig, "
                    "suspensyon, o pagpapaliban."
                ),
                "General",
                1,
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
    --surface-2: #F5F0F8;

    --text: #211427;
    --heading: #42105F;
    --muted: #5D5062;
    --border: #D8CCDF;

    --danger: #A51D45;
    --danger-bg: #FFE4EB;

    --success: #21643A;
    --success-bg: #DFF4E5;

    --warning: #715000;
    --warning-bg: #FFF1BE;

    --shadow: rgba(70, 20, 100, .10);
}

body.dark {
    --background: #111014;
    --surface: #211B26;
    --surface-2: #2A2230;

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

    --shadow: rgba(0, 0, 0, .30);
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
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    background: var(--background);
    color: var(--text);

    line-height: 1.65;

    transition:
        background .2s ease,
        color .2s ease;
}

a {
    color: var(--purple);
    font-weight: 700;
}

button,
input,
select,
textarea {
    font: inherit;
}

button {
    cursor: pointer;
}

.site-header {
    position: sticky;
    top: 0;

    z-index: 1000;

    display: flex;
    align-items: center;

    gap: 18px;

    flex-wrap: wrap;

    padding:
        12px
        4%;

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

    gap: 12px;

    color: white;

    text-decoration: none;

    margin-right: auto;

    min-width: 230px;
}

.brand-logo {
    width: 58px;
    height: 58px;

    object-fit: contain;

    display: block;

    background: white;

    border-radius: 50%;

    padding: 4px;

    box-shadow:
        0 3px 12px
        rgba(0, 0, 0, .20);
}

.brand strong,
.brand small {
    display: block;
}

.brand strong {
    font-size: 15px;
}

.brand small {
    opacity: .85;
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
}

.nav-form {
    display: inline;

    margin: 0;
}

.tools {
    display: flex;

    gap: 6px;

    align-items: center;
}

.tool {
    color: white;

    text-decoration: none;

    padding:
        6px
        9px;

    border:
        1px solid
        rgba(255,255,255,.45);

    border-radius: 8px;

    font-size: 12px;

    font-weight: 800;
}

main {
    width: 92%;

    max-width: 1180px;

    min-height: 76vh;

    margin: auto;

    padding:
        35px
        0
        70px;
}

footer {
    padding: 32px 20px;

    color: white;

    text-align: center;

    background:
        var(--purple-dark);
}

.hero {
    display: grid;

    grid-template-columns:
        minmax(0, 1.6fr)
        minmax(220px, .4fr);

    gap: 35px;

    align-items: center;

    padding: 50px;

    color: white;

    border-radius: 26px;

    background:
        linear-gradient(
            135deg,
            var(--purple),
            var(--purple-light)
        );

    box-shadow:
        0 15px 35px
        rgba(90, 30, 120, .20);
}

.hero h1 {
    margin:
        15px
        0;

    font-size:
        clamp(
            32px,
            5vw,
            60px
        );

    line-height: 1.05;
}

.hero p {
    max-width: 760px;

    font-size: 18px;
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

    min-height: 230px;

    padding: 20px;

    border-radius: 22px;

    background:
        rgba(255,255,255,.15);
}

.seal-holder img {
    width: 205px;
    height: 205px;

    object-fit: contain;

    display: block;
}

.card,
.form,
.stat-card {
    margin:
        20px
        0;

    padding:
        25px;

    color: var(--text);

    border:
        1px solid
        var(--border);

    border-radius: 18px;

    background:
        var(--surface);

    box-shadow:
        0 9px 28px
        var(--shadow);
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

    margin:
        22px
        0;
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

.grid-three {
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                220px,
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
    border: 0;

    border-radius: 10px;

    padding:
        11px
        18px;

    background:
        var(--purple);

    color: white;

    cursor: pointer;

    font-weight: 900;

    text-decoration: none;

    display: inline-block;
}

.button:hover,
button:hover {
    filter: brightness(1.08);
}

.button.secondary {
    background:
        var(--purple-soft);

    color:
        var(--heading);
}

.button.danger,
button.danger {
    background:
        var(--danger);

    color: white;
}

.form {
    max-width: 800px;

    margin:
        25px
        auto;
}

.form form {
    display: grid;

    gap: 15px;
}

.form label,
.field {
    display: grid;

    gap: 7px;

    font-weight: 800;
}

input,
select,
textarea {
    width: 100%;

    padding:
        12px;

    border:
        1px solid
        var(--border);

    border-radius: 9px;

    background:
        var(--surface);

    color:
        var(--text);

    outline: none;
}

textarea {
    min-height: 130px;

    resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
    outline:
        3px solid
        rgba(123,44,191,.25);

    border-color:
        var(--purple);
}

.search-form {
    display: grid;

    grid-template-columns:
        1fr
        1fr
        auto;

    gap: 12px;

    align-items: end;
}

.result {
    display: grid;

    grid-template-columns:
        1.1fr
        1.5fr
        .8fr
        auto;

    gap: 15px;

    align-items: center;

    padding:
        17px
        0;

    border-bottom:
        1px solid
        var(--border);
}

.row {
    display: flex;

    align-items: center;

    gap: 15px;

    flex-wrap: wrap;

    padding:
        14px
        0;

    border-bottom:
        1px solid
        var(--border);
}

.status {
    display: inline-block;

    width: max-content;

    padding:
        4px
        10px;

    border-radius: 999px;

    background:
        var(--purple-soft);

    color:
        var(--heading);

    font-size: 12px;

    font-weight: 900;
}

.notice {
    padding: 17px;

    border-left:
        5px solid
        var(--purple);

    border-radius: 10px;

    background:
        var(--purple-soft);

    margin:
        12px
        0;
}

.alert {
    padding:
        13px
        16px;

    margin-bottom:
        15px;

    border-radius: 9px;

    font-weight: 700;
}

.alert.warning {
    background:
        var(--warning-bg);

    color:
        var(--warning);
}

.alert.danger {
    background:
        var(--danger-bg);

    color:
        var(--danger);
}

.alert.success {
    background:
        var(--success-bg);

    color:
        var(--success);
}

.alert.info {
    background:
        var(--purple-soft);

    color:
        var(--heading);
}

.friendly-dashboard {
    padding:
        35px;

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

.friendly-dashboard h1,
.friendly-dashboard h2,
.friendly-dashboard p {
    color: white;
}

.friendly-dashboard h1 {
    margin:
        8px
        0;

    font-size:
        clamp(
            30px,
            5vw,
            50px
        );
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
    color:
        var(--text);

    background:
        var(--surface);

    padding:
        19px;

    border-radius: 14px;

    text-decoration: none;

    border:
        1px solid
        var(--border);
}

.staff-action strong {
    display: block;

    color:
        var(--purple);

    margin-top:
        7px;
}

.staff-action span {
    color:
        var(--muted);

    font-size:
        13px;
}

.stat-card {
    text-align: center;
}

.stat-number {
    display: block;

    font-size:
        36px;

    font-weight:
        950;

    color:
        var(--purple);
}

.split {
    display: flex;

    justify-content:
        space-between;

    align-items:
        center;

    gap:
        20px;

    flex-wrap:
        wrap;
}

.muted {
    color:
        var(--muted);
}

.empty {
    text-align:
        center;

    padding:
        45px
        20px;
}

.steps {
    display: grid;

    gap:
        10px;

    padding-left:
        25px;
}

.step-box {
    padding:
        14px
        16px;

    border-radius:
        12px;

    background:
        var(--surface-2);

    border:
        1px solid
        var(--border);
}

.login-box {
    max-width:
        520px;

    margin:
        40px
        auto;
}

.logo-large {
    width:
        150px;

    height:
        150px;

    display:
        block;

    object-fit:
        contain;

    margin:
        0
        auto
        20px;

    border-radius:
        50%;

    background:
        white;

    padding:
        6px;
}

hr {
    border:
        0;

    border-top:
        1px solid
        var(--border);

    margin:
        25px
        0;
}

.small {
    font-size:
        13px;
}

code {
    padding:
        3px
        7px;

    border-radius:
        6px;

    background:
        var(--surface-2);

    color:
        var(--heading);
}

@media(max-width: 900px) {

    .hero {
        grid-template-columns:
            1fr;

        padding:
            32px;
    }

    .seal-holder {
        min-height:
            200px;
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

        margin-right:
            0;
    }

    .main-nav {
        width:
            100%;
    }

    .staff-actions {
        grid-template-columns:
            1fr
            1fr;
    }
}

@media(max-width: 520px) {

    main {
        width:
            94%;

        padding-top:
            22px;
    }

    .hero {
        padding:
            25px;
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

    .site-header {
        padding:
            10px
            3%;
    }

    .tools {
        width:
            100%;
    }
}
"""


# ============================================================
# HTML HELPERS
# ============================================================

def render_messages():
    output = ""

    for category, message in get_flashed_messages(
        with_categories=True
    ):
        output += (
            '<div class="alert '
            + safe(category)
            + '">'
            + safe(message)
            + "</div>"
        )

    return output


def page(
    title,
    content,
):
    t = labels()

    if logged_in():

        navigation = f"""
        <a href="{url_for("home")}">
            {safe(t["home"])}
        </a>

        <a href="{url_for("search")}">
            {safe(t["search"])}
        </a>

        <a href="{url_for("hearings")}">
            {safe(t["hearings"])}
        </a>

        <a href="{url_for("notices")}">
            {safe(t["notices"])}
        </a>

        <a href="{url_for("dashboard")}">
            {safe(t["dashboard"])}
        </a>

        <a href="{url_for("staff_cases")}">
            {safe(t["cases"])}
        </a>

        <form
            method="post"
            action="{url_for("logout")}"
            class="nav-form"
        >
            <button
                class="nav-button"
                type="submit"
                onclick="return confirm('{safe(t["logout_confirm"])}')"
            >
                {safe(t["logout"])}
            </button>
        </form>
        """

    else:

        navigation = f"""
        <a href="{url_for("home")}">
            {safe(t["home"])}
        </a>

        <a href="{url_for("search")}">
            {safe(t["search"])}
        </a>

        <a href="{url_for("hearings")}">
            {safe(t["hearings"])}
        </a>

        <a href="{url_for("notices")}">
            {safe(t["notices"])}
        </a>

        <a href="{url_for("staff_login")}">
            {safe(t["login"])}
        </a>
        """

    html_page = f"""
<!doctype html>

<html lang="{safe(current_language())}">

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

    <meta
        name="description"
        content="MCTC Silang-Amadeo Court Information Portal"
    >

    <title>
        {safe(title)}
        -
        {safe(COURT_SHORT_NAME)}
    </title>

    <style>
        {CSS}
    </style>

</head>

<body class="{safe(current_theme())}">

<header class="site-header">

    <a
        class="brand"
        href="{url_for("home")}"
    >

        <img
            class="brand-logo"
            src="{url_for("static", filename=LOGO_FILENAME)}"
            alt="MCTC Silang-Amadeo Court Seal"
        >

        <span>

            <strong>
                {safe(COURT_SHORT_NAME)}
            </strong>

            <small>
                Silang-Amadeo, Cavite
            </small>

        </span>

    </a>

    <nav class="main-nav">

        {navigation}

    </nav>

    <div class="tools">

        <a
            class="tool"
            href="{url_for("language", language="en")}"
        >
            EN
        </a>

        <a
            class="tool"
            href="{url_for("language", language="fil")}"
        >
            FIL
        </a>

        <a
            class="tool"
            href="{url_for("theme", theme="light")}"
        >
            ☀
        </a>

        <a
            class="tool"
            href="{url_for("theme", theme="dark")}"
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
        {safe(COURT_NAME)}
    </strong>

    <br>

    <span>
        {safe(COURT_ADDRESS)}
    </span>

    <br>

    <span>
        Tel: {safe(COURT_PHONE)}
    </span>

    <br><br>

    <small>
        {safe(t["prototype_notice"])}
    </small>

</footer>

</body>

</html>
"""

    response = make_response(
        html_page
    )

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "max-age=0, private"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    t = labels()

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

        if current_language() == "fil":

            notice_title = notice["title_fil"]

            notice_body = notice["body_fil"]

        else:

            notice_title = notice["title_en"]

            notice_body = notice["body_en"]

        notice_html += f"""
        <div class="notice">

            <span class="status">
                {safe(notice["notice_type"])}
            </span>

            <h3>
                {safe(notice_title)}
            </h3>

            <p>
                {safe(notice_body)}
            </p>

        </div>
        """

    if not notice_html:
        notice_html = f"""
        <p class="muted">
            {safe(t["no_notices"])}
        </p>
        """

    content = f"""
    <section class="hero">

        <div>

            <div>
                ⚖️
                {safe(t["public_information"])}
            </div>

            <h1>
                {safe(COURT_NAME)}
            </h1>

            <p>
                Search approved public case information,
                hearing schedules, and official court notices.
            </p>

            <div class="hero-buttons">

                <a
                    class="button"
                    href="{url_for("search")}"
                >
                    🔎
                    {safe(t["search_case"])}
                </a>

                <a
                    class="button secondary"
                    href="{url_for("hearings")}"
                >
                    📅
                    {safe(t["hearings"])}
                </a>

            </div>

        </div>

        <div class="seal-holder">

            <img
                src="{url_for("static", filename=LOGO_FILENAME)}"
                alt="Official court seal"
            >

        </div>

    </section>


    <section class="grid grid-two">

        <div class="card">

            <h2>
                🔎
                {safe(t["search_case"])}
            </h2>

            <p>
                Search using a case number,
                a party name, or both.
            </p>

            <a
                class="button secondary"
                href="{url_for("search")}"
            >
                {safe(t["search_button"])}
            </a>

        </div>


        <div class="card">

            <h2>
                📅
                {safe(t["hearings"])}
            </h2>

            <p>
                View published hearing dates,
                times, and courtrooms.
            </p>

            <a
                class="button secondary"
                href="{url_for("hearings")}"
            >
                {safe(t["hearings"])}
            </a>

        </div>


        <div class="card">

            <h2>
                📢
                {safe(t["court_notices"])}
            </h2>

            <p>
                Check official announcements,
                suspension notices, postponements,
                holidays, and court operations.
            </p>

            <a
                class="button secondary"
                href="{url_for("notices")}"
            >
                {safe(t["notices"])}
            </a>

        </div>


        <div class="card">

            <h2>
                🌐
                {safe(t["language"])}
            </h2>

            <p>
                English / Filipino
            </p>

            <a
                class="button secondary"
                href="{url_for("language", language="fil")}"
            >
                FIL
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            📢
            {safe(t["court_notices"])}
        </h2>

        {notice_html}

    </section>


    <section class="card">

        <h2>
            ⚠️
            {safe(t["suspension_information"])}
        </h2>

        <p>
            {safe(t["suspension_text"])}
        </p>

        <a
            class="button secondary"
            href="{url_for("notices")}"
        >
            {safe(t["notices"])}
        </a>

    </section>


    <section class="card">

        <h2>
            🔐
            {safe(t["privacy"])}
        </h2>

        <p>
            {safe(t["privacy_text"])}
        </p>

    </section>
    """

    return page(
        COURT_SHORT_NAME,
        content,
    )


# ============================================================
# LANGUAGE
# ============================================================

@app.route("/language/<language>")
def language(language):

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
def theme(theme):

    if theme not in (
        "light",
        "dark",
    ):
        abort(404)

    session["theme"] = theme

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# PUBLIC SEARCH
# ============================================================

@app.route("/search")
def search():

    t = labels()

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

        if case_number and name:

            results = connection.execute(
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
                    "%" + case_number + "%",
                    "%" + name + "%",
                    "%" + name + "%",
                ),
            ).fetchall()

        elif case_number:

            results = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE case_number LIKE ?
                ORDER BY case_number
                """,
                (
                    "%" + case_number + "%",
                ),
            ).fetchall()

        else:

            results = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE
                    title LIKE ?
                    OR parties LIKE ?
                ORDER BY case_number
                """,
                (
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
                    {safe(case["case_number"])}
                </strong>

                <br>

                {safe(case["title"])}

            </div>

            <div>

                {safe(case["parties"])}

            </div>

            <div>

                <span class="status">
                    {safe(case["status"])}
                </span>

            </div>

            <div>

                <a
                    class="button secondary"
                    href="{url_for("case_details", case_id=case["id"])}"
                >
                    {safe(t["view"])}
                </a>

            </div>

        </div>
        """

    if not rows:

        if case_number or name:

            rows = f"""
            <div class="empty">

                <div style="font-size:45px;">
                    🔎
                </div>

                <h2>
                    {safe(t["no_results"])}
                </h2>

                <p>
                    Check the case number or party name
                    and try again.
                </p>

            </div>
            """

        else:

            rows = f"""
            <div class="empty">

                <div style="font-size:45px;">
                    📋
                </div>

                <h2>
                    {safe(t["search_case"])}
                </h2>

                <p>
                    Enter a case number or name above.
                </p>

            </div>
            """

    content = f"""

    <div class="card">

        <h1>
            🔎
            {safe(t["search_case"])}
        </h1>

        <h2>
            {safe(t["search_instruction_title"])}
        </h2>

        <div class="steps">

            <div class="step-box">
                <strong>1.</strong>
                {safe(t["search_instruction_1"])}
            </div>

            <div class="step-box">
                <strong>2.</strong>
                {safe(t["search_instruction_2"])}
            </div>

            <div class="step-box">
                <strong>3.</strong>
                {safe(t["search_instruction_3"])}
            </div>

            <div class="step-box">
                <strong>4.</strong>
                {safe(t["search_instruction_4"])}
            </div>

            <div class="step-box">
                <strong>5.</strong>
                {safe(t["search_instruction_5"])}
            </div>

        </div>

    </div>


    <div class="card">

        <form
            method="get"
            class="search-form"
        >

            <label>

                {safe(t["case_number"])}

                <input
                    name="case_number"
                    value="{safe(case_number)}"
                    placeholder="MCTC-2026-001"
                    autocomplete="off"
                >

            </label>


            <label>

                {safe(t["name"])}

                <input
                    name="name"
                    value="{safe(name)}"
                    placeholder="JUAN DELA CRUZ"
                    autocomplete="off"
                >

            </label>


            <button
                type="submit"
            >
                🔎
                {safe(t["search_button"])}
            </button>

        </form>

    </div>


    <div class="card">

        <div class="split">

            <h2>
                {safe(t["results"])}
            </h2>

            <span class="muted">
                {len(results)}
            </span>

        </div>

        {rows}

    </div>
    """

    return page(
        t["search_case"],
        content,
    )


# ============================================================
# PUBLIC CASE DETAILS
# ============================================================

@app.route("/case/<int:case_id>")
def case_details(case_id):

    t = labels()

    connection = db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
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
        (
            case_id,
        ),
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
        (
            case_id,
        ),
    ).fetchall()

    connection.close()

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""
        <div class="row">

            <strong>
                {safe(hearing["hearing_date"])}
            </strong>

            <span>
                {safe(hearing["hearing_time"])}
            </span>

            <span>
                {safe(hearing["courtroom"])}
            </span>

            <span>
                {safe(hearing["purpose"])}
            </span>

            <span class="status">
                {safe(hearing["status"])}
            </span>

        </div>
        """

    if not hearing_html:

        hearing_html = f"""
        <p class="muted">
            {safe(t["no_hearings"])}
        </p>
        """

    document_html = ""

    for document in documents:

        document_html += f"""
        <div class="notice">

            📄

            <a
                href="{safe(document["url"])}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {safe(document["display_name"])}
            </a>

        </div>
        """

    if not document_html:

        document_html = f"""
        <p class="muted">
            {safe(t["no_public_documents"])}
        </p>
        """

    content = f"""

    <div class="card">

        <span class="status">
            {safe(case["status"])}
        </span>

        <h1>
            {safe(case["case_number"])}
        </h1>

        <h2>
            {safe(case["title"])}
        </h2>

        <p>
            <strong>
                {safe(t["parties"])}:
            </strong>

            {safe(case["parties"])}
        </p>

        <p>
            <strong>
                {safe(t["case_type"])}:
            </strong>

            {safe(case["case_type"])}
        </p>

        <p>
            {safe(case["public_summary"])}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {safe(t["hearings"])}
        </h2>

        {hearing_html}

    </div>


    <div class="card">

        <h2>
            📄
            {safe(t["public_documents"])}
        </h2>

        {document_html}

    </div>


    <div class="card">

        <h2>
            ⚠️
            {safe(t["suspension_information"])}
        </h2>

        <p>
            {safe(t["suspension_text"])}
        </p>

    </div>
    """

    return page(
        case["case_number"],
        content,
    )


# ============================================================
# PUBLIC HEARINGS
# ============================================================

@app.route("/hearings")
def hearings():

    t = labels()

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

    html_rows = ""

    for row in rows:

        html_rows += f"""
        <div class="row">

            <strong>
                {safe(row["hearing_date"])}
            </strong>

            <span>
                {safe(row["hearing_time"])}
            </span>

            <span>
                {safe(row["case_number"])}
            </span>

            <span>
                {safe(row["courtroom"])}
            </span>

            <span class="status">
                {safe(row["status"])}
            </span>

        </div>
        """

    if not html_rows:

        html_rows = f"""
        <p class="muted">
            {safe(t["no_hearings"])}
        </p>
        """

    content = f"""

    <div class="card">

        <h1>
            📅
            {safe(t["hearings"])}
        </h1>

        <p>
            Published hearing information.
        </p>

        {html_rows}

    </div>


    <div class="card">

        <h2>
            ⚠️
            {safe(t["suspension_information"])}
        </h2>

        <p>
            {safe(t["suspension_text"])}
        </p>

        <a
            class="button secondary"
            href="{url_for("notices")}"
        >
            {safe(t["notices"])}
        </a>

    </div>
    """

    return page(
        t["hearings"],
        content,
    )


# ============================================================
# PUBLIC NOTICES
# ============================================================

@app.route("/notices")
def notices():

    t = labels()

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

    html_rows = ""

    for row in rows:

        if current_language() == "fil":

            title = row["title_fil"]

            body = row["body_fil"]

        else:

            title = row["title_en"]

            body = row["body_en"]

        html_rows += f"""
        <div class="notice">

            <span class="status">
                {safe(row["notice_type"])}
            </span>

            <h2>
                {safe(title)}
            </h2>

            <p>
                {safe(body)}
            </p>

        </div>
        """

    if not html_rows:

        html_rows = f"""
        <div class="empty">

            <div style="font-size:45px;">
                📢
            </div>

            <p>
                {safe(t["no_notices"])}
            </p>

        </div>
        """

    content = f"""

    <div class="card">

        <h1>
            📢
            {safe(t["court_notices"])}
        </h1>

        {html_rows}

    </div>


    <div class="card">

        <h2>
            ⚠️
            {safe(t["suspension_information"])}
        </h2>

        <p>
            {safe(t["suspension_text"])}
        </p>

    </div>
    """

    return page(
        t["notices"],
        content,
    )


# ============================================================
# STAFF LOGIN
# ============================================================

@app.route(
    "/login",
    methods=[
        "GET",
        "POST",
    ],
)
def staff_login():

    t = labels()

    if logged_in():

        return redirect(
            url_for("dashboard")
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
            (
                username,
            ),
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

            session["staff_id"] = staff["id"]

            session["username"] = staff["username"]

            session["role"] = staff["role"]

            session.setdefault(
                "language",
                "en",
            )

            session.setdefault(
                "theme",
                "light",
            )

            audit(
                "Staff login",
                staff["username"],
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            t["invalid_login"],
            "danger",
        )

    content = f"""

    <div class="login-box card">

        <img
            class="logo-large"
            src="{url_for("static", filename=LOGO_FILENAME)}"
            alt="Court seal"
        >

        <h1>
            🔐
            {safe(t["staff_login_title"])}
        </h1>

        <p class="muted">
            {safe(t["staff_only"])}
        </p>

        <form
            method="post"
        >

            <label class="field">

                {safe(t["username"])}

                <input
                    type="text"
                    name="username"
                    required
                    autocomplete="username"
                >

            </label>


            <label class="field">

                {safe(t["password"])}

                <input
                    type="password"
                    name="password"
                    required
                    autocomplete="current-password"
                >

            </label>


            <button
                type="submit"
            >
                🔐
                {safe(t["login_button"])}
            </button>

        </form>

    </div>
    """

    return page(
        t["login"],
        content,
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=["POST"],
)
def logout():

    username = current_username()

    if username:
        audit(
            "Staff logout",
            username,
        )

    session.clear()

    response = redirect(
        url_for("home")
    )

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "max-age=0, private"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/dashboard")
@staff_required
def dashboard():

    t = labels()

    connection = db()

    total_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM cases
        """
    ).fetchone()["total"]

    total_hearings = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM hearings
        """
    ).fetchone()["total"]

    total_notices = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM notices
        """
    ).fetchone()["total"]

    recent_cases = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).fetchall()

    recent_notices = connection.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).fetchall()

    connection.close()

    recent_case_html = ""

    for case in recent_cases:

        recent_case_html += f"""
        <div class="row">

            <strong>
                {safe(case["case_number"])}
            </strong>

            <span>
                {safe(case["title"])}
            </span>

            <span class="status">
                {safe(case["status"])}
            </span>

            <a
                class="button secondary"
                href="{url_for("staff_case", case_id=case["id"])}"
            >
                {safe(t["view"])}
            </a>

        </div>
        """

    if not recent_case_html:

        recent_case_html = f"""
        <p class="muted">
            {safe(t["no_cases"])}
        </p>
        """

    recent_notice_html = ""

    for notice in recent_notices:

        if current_language() == "fil":
            notice_title = notice["title_fil"]
        else:
            notice_title = notice["title_en"]

        recent_notice_html += f"""
        <div class="row">

            <strong>
                {safe(notice_title)}
            </strong>

            <span class="status">
                {safe(notice["notice_type"])}
            </span>

        </div>
        """

    if not recent_notice_html:

        recent_notice_html = f"""
        <p class="muted">
            {safe(t["no_notices"])}
        </p>
        """

    content = f"""

    <section class="friendly-dashboard">

        <div>
            <span>
                👋
                {safe(t["welcome"])}
            </span>

            <h1>
                Staff Dashboard
            </h1>

            <p>
                {safe(t["dashboard_intro"])}
            </p>
        </div>

    </section>


    <section class="grid grid-three">

        <div class="stat-card">

            <span class="stat-number">
                {total_cases}
            </span>

            <strong>
                {safe(t["total_cases"])}
            </strong>

        </div>


        <div class="stat-card">

            <span class="stat-number">
                {total_hearings}
            </span>

            <strong>
                {safe(t["total_hearings"])}
            </strong>

        </div>


        <div class="stat-card">

            <span class="stat-number">
                {total_notices}
            </span>

            <strong>
                {safe(t["total_notices"])}
            </strong>

        </div>

    </section>


    <section class="card">

        <h2>
            ⚡
            {safe(t["quick_actions"])}
        </h2>

        <div class="staff-actions">

            <a
                class="staff-action"
                href="{url_for("add_case")}"
            >
                ➕
                <strong>
                    {safe(t["add_case"])}
                </strong>
                <span>
                    {safe(t["create_case"])}
                </span>
            </a>


            <a
                class="staff-action"
                href="{url_for("staff_cases")}"
            >
                📋
                <strong>
                    {safe(t["manage_cases"])}
                </strong>
                <span>
                    {safe(t["manage_case_info"])}
                </span>
            </a>


            <a
                class="staff-action"
                href="{url_for("hearings")}"
            >
                📅
                <strong>
                    {safe(t["hearings"])}
                </strong>
                <span>
                    {safe(t["manage_hearing_info"])}
                </span>
            </a>


            <a
                class="staff-action"
                href="{url_for("staff_new_notice")}"
            >
                📢
                <strong>
                    {safe(t["notices"])}
                </strong>
                <span>
                    {safe(t["manage_notice_info"])}
                </span>
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            📋
            {safe(t["recent_cases"])}
        </h2>

        {recent_case_html}

    </section>


    <section class="card">

        <h2>
            📢
            {safe(t["recent_notices"])}
        </h2>

        {recent_notice_html}

    </section>
    """

    return page(
        t["dashboard"],
        content,
    )


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():

    t = labels()

    query = clean(
        request.args.get(
            "q",
            "",
        ),
        300,
    )

    connection = db()

    if query:

        cases = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE
                case_number LIKE ?
                OR title LIKE ?
                OR parties LIKE ?
            ORDER BY case_number
            """,
            (
                "%" + query + "%",
                "%" + query + "%",
                "%" + query + "%",
            ),
        ).fetchall()

    else:

        cases = connection.execute(
            """
            SELECT *
            FROM cases
            ORDER BY case_number
            """
        ).fetchall()

    connection.close()

    rows = ""

    for case in cases:

        rows += f"""
        <div class="result">

            <div>

                <strong>
                    {safe(case["case_number"])}
                </strong>

                <br>

                {safe(case["title"])}

            </div>

            <div>
                {safe(case["parties"])}
            </div>

            <div>

                <span class="status">
                    {safe(case["status"])}
                </span>

            </div>

            <div>

                <a
                    class="button secondary"
                    href="{url_for("staff_case", case_id=case["id"])}"
                >
                    {safe(t["view"])}
                </a>

            </div>

        </div>
        """

    if not rows:

        rows = f"""
        <div class="empty">

            <div style="font-size:45px;">
                📋
            </div>

            <h2>
                {safe(t["no_cases"])}
            </h2>

        </div>
        """

    content = f"""

    <div class="split">

        <h1>
            📋
            {safe(t["manage_cases"])}
        </h1>

        <a
            class="button"
            href="{url_for("add_case")}"
        >
            ➕
            {safe(t["add_case"])}
        </a>

    </div>


    <div class="card">

        <form
            method="get"
            class="search-form"
        >

            <label>

                Search

                <input
                    name="q"
                    value="{safe(query)}"
                    placeholder="Case number or party name"
                >

            </label>

            <div></div>

            <button
                type="submit"
            >
                🔎
                {safe(t["search_button"])}
            </button>

        </form>

    </div>


    <div class="card">

        {rows}

    </div>
    """

    return page(
        t["manage_cases"],
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
    ],
)
@staff_required
def add_case():

    t = labels()

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
            200,
        )

        public_summary = clean(
            request.form.get(
                "public_summary",
                "",
            ),
            5000,
        )

        internal_notes = clean(
            request.form.get(
                "internal_notes",
                "",
            ),
            10000,
        )

        if not case_number or not title:

            flash(
                "Case number and title are required.",
                "warning",
            )

        else:

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

                case_id = cursor.lastrowid

                if hearing_date:

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
                            "Initial hearing",
                            "Scheduled",
                        ),
                    )

                connection.commit()

                connection.close()

                audit(
                    "Case created",
                    case_number,
                )

                flash(
                    t["case_created"],
                    "success",
                )

                return redirect(
                    url_for(
                        "staff_case",
                        case_id=case_id,
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
            ➕
            {safe(t["add_case"])}
        </h1>

        <p class="muted">
            Enter only information that is appropriate
            for the court's authorized system.
        </p>

        <form
            method="post"
        >

            <label>

                {safe(t["case_number"])}

                <input
                    name="case_number"
                    required
                    placeholder="MCTC-2026-001"
                >

            </label>


            <label>

                {safe(t["title"])}

                <input
                    name="title"
                    required
                >

            </label>


            <label>

                {safe(t["parties"])}

                <input
                    name="parties"
                >

            </label>


            <label>

                {safe(t["case_type"])}

                <input
                    name="case_type"
                >

            </label>


            <label>

                {safe(t["status"])}

                <select name="status">

                    {"".join(
                        f'<option value="{safe(status)}">{safe(status)}</option>'
                        for status in CASE_STATUSES
                    )}

                </select>

            </label>


            <label>

                {safe(t["hearing_date"])}

                <input
                    type="date"
                    name="hearing_date"
                >

            </label>


            <label>

                {safe(t["hearing_time"])}

                <input
                    type="time"
                    name="hearing_time"
                >

            </label>


            <label>

                {safe(t["courtroom"])}

                <input
                    name="courtroom"
                >

            </label>


            <label>

                {safe(t["public_summary"])}

                <textarea
                    name="public_summary"
                ></textarea>

            </label>


            <label>

                {safe(t["internal_notes"])}

                <textarea
                    name="internal_notes"
                ></textarea>

            </label>


            <button
                type="submit"
            >
                💾
                {safe(t["save"])}
            </button>

        </form>

    </div>
    """

    return page(
        t["add_case"],
        content,
    )


# ============================================================
# STAFF CASE DETAILS
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>"
)
@staff_required
def staff_case(case_id):

    t = labels()

    connection = db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
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
        (
            case_id,
        ),
    ).fetchall()

    documents = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE case_id = ?
        ORDER BY created_at DESC
        """,
        (
            case_id,
        ),
    ).fetchall()

    connection.close()

    hearing_html = ""

    for hearing in hearings:

        hearing_html += f"""
        <div class="row">

            <strong>
                {safe(hearing["hearing_date"])}
            </strong>

            <span>
                {safe(hearing["hearing_time"])}
            </span>

            <span>
                {safe(hearing["courtroom"])}
            </span>

            <span>
                {safe(hearing["purpose"])}
            </span>

            <span class="status">
                {safe(hearing["status"])}
            </span>

            <form
                method="post"
                action="{url_for("delete_hearing", hearing_id=hearing["id"])}"
            >

                <button
                    class="danger"
                    type="submit"
                    onclick="return confirm('Delete this hearing?')"
                >
                    Delete
                </button>

            </form>

        </div>
        """

    if not hearing_html:

        hearing_html = f"""
        <p class="muted">
            {safe(t["no_hearings"])}
        </p>
        """

    document_html = ""

    for document in documents:

        access = (
            "Public"
            if document["public_access"]
            else "Restricted"
        )

        document_html += f"""
        <div class="notice">

            <strong>
                {safe(document["display_name"])}
            </strong>

            <br>

            <span class="muted">
                {safe(access)}
            </span>

            <br>

            <small>
                {safe(document["url"])}
            </small>

            <br><br>

            <form
                method="post"
                action="{url_for("delete_document", document_id=document["id"])}"
            >

                <button
                    class="danger"
                    type="submit"
                    onclick="return confirm('Remove this document reference?')"
                >
                    {safe(t["remove"])}
                </button>

            </form>

        </div>
        """

    if not document_html:

        document_html = f"""
        <p class="muted">
            {safe(t["no_public_documents"])}
        </p>
        """

    content = f"""

    <div class="split">

        <h1>
            {safe(case["case_number"])}
        </h1>

        <a
            class="button"
            href="{url_for("edit_case", case_id=case_id)}"
        >
            ✏️
            {safe(t["edit_case"])}
        </a>

    </div>


    <div class="card">

        <span class="status">
            {safe(case["status"])}
        </span>

        <h2>
            {safe(case["title"])}
        </h2>

        <p>
            <strong>
                {safe(t["parties"])}:
            </strong>

            {safe(case["parties"])}
        </p>

        <p>
            <strong>
                {safe(t["case_type"])}:
            </strong>

            {safe(case["case_type"])}
        </p>

        <p>
            <strong>
                {safe(t["public_summary"])}:
            </strong>
        </p>

        <p>
            {safe(case["public_summary"])}
        </p>

        <hr>

        <p>
            <strong>
                Internal Notes:
            </strong>
        </p>

        <p>
            {safe(case["internal_notes"])}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {safe(t["add_hearing"])}
        </h2>

        <form
            method="post"
            action="{url_for("add_hearing", case_id=case_id)}"
        >

            <label class="field">

                {safe(t["hearing_date"])}

                <input
                    type="date"
                    name="hearing_date"
                    required
                >

            </label>


            <label class="field">

                {safe(t["hearing_time"])}

                <input
                    type="time"
                    name="hearing_time"
                >

            </label>


            <label class="field">

                {safe(t["courtroom"])}

                <input
                    name="courtroom"
                >

            </label>


            <label class="field">

                {safe(t["purpose"])}

                <input
                    name="purpose"
                >

            </label>


            <label class="field">

                {safe(t["status"])}

                <select name="status">

                    {"".join(
                        f'<option value="{safe(status)}">{safe(status)}</option>'
                        for status in HEARING_STATUSES
                    )}

                </select>

            </label>


            <button
                type="submit"
            >
                ➕
                {safe(t["add_hearing"])}
            </button>

        </form>

    </div>


    <div class="card">

        <h2>
            📅
            Existing Hearings
        </h2>

        {hearing_html}

    </div>


    <div class="card">

        <h2>
            📄
            {safe(t["add_document"])}
        </h2>

        <p class="muted">

            This version stores document references.
            Use approved secure storage for actual
            court documents.

        </p>

        <form
            method="post"
            action="{url_for("add_document", case_id=case_id)}"
        >

            <label class="field">

                {safe(t["display_name"])}

                <input
                    name="display_name"
                    required
                >

            </label>


            <label class="field">

                {safe(t["approved_url"])}

                <input
                    name="url"
                    required
                >

            </label>


            <label class="field">

                <span>

                    <input
                        type="checkbox"
                        name="public_access"
                    >

                    {safe(t["public_access"])}

                </span>

            </label>


            <button
                type="submit"
            >
                ➕
                {safe(t["add_document"])}
            </button>

        </form>

        <hr>

        {document_html}

    </div>


    <div class="card">

        <h2>
            ⚠️
            {safe(t["danger_zone"])}
        </h2>

        <p class="muted">
            Deleting a case also deletes its hearings
            and document references.
        </p>

        <form
            method="post"
            action="{url_for("delete_case", case_id=case_id)}"
        >

            <button
                class="danger"
                type="submit"
                onclick="return confirm('DELETE THIS CASE? This cannot be undone.')"
            >
                🗑️
                {safe(t["delete_case"])}
            </button>

        </form>

    </div>
    """

    return page(
        case["case_number"],
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
    ],
)
@staff_required
def edit_case(case_id):

    t = labels()

    connection = db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
    ).fetchone()

    connection.close()

    if case is None:
        abort(404)

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
            200,
        )

        public_summary = clean(
            request.form.get(
                "public_summary",
                "",
            ),
            5000,
        )

        internal_notes = clean(
            request.form.get(
                "internal_notes",
                "",
            ),
            10000,
        )

        if not case_number or not title:

            flash(
                "Case number and title are required.",
                "warning",
            )

        else:

            connection = db()

            try:

                connection.execute(
                    """
                    UPDATE cases
                    SET
                        case_number = ?,
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
                        case_id,
                    ),
                )

                connection.commit()

                connection.close()

                audit(
                    "Case updated",
                    case_number,
                )

                flash(
                    t["case_updated"],
                    "success",
                )

                return redirect(
                    url_for(
                        "staff_case",
                        case_id=case_id,
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
            ✏️
            {safe(t["edit_case"])}
        </h1>

        <form
            method="post"
        >

            <label>

                {safe(t["case_number"])}

                <input
                    name="case_number"
                    value="{safe(case["case_number"])}"
                    required
                >

            </label>


            <label>

                {safe(t["title"])}

                <input
                    name="title"
                    value="{safe(case["title"])}"
                    required
                >

            </label>


            <label>

                {safe(t["parties"])}

                <input
                    name="parties"
                    value="{safe(case["parties"])}"
                >

            </label>


            <label>

                {safe(t["case_type"])}

                <input
                    name="case_type"
                    value="{safe(case["case_type"])}"
                >

            </label>


            <label>

                {safe(t["status"])}

                <select name="status">

                    {"".join(
                        f'<option value="{safe(status)}"'
                        + (
                            " selected"
                            if status == case["status"]
                            else ""
                        )
                        + f'>{safe(status)}</option>'
                        for status in CASE_STATUSES
                    )}

                </select>

            </label>


            <label>

                {safe(t["hearing_date"])}

                <input
                    type="date"
                    name="hearing_date"
                    value="{safe(case["hearing_date"])}"
                >

            </label>


            <label>

                {safe(t["hearing_time"])}

                <input
                    type="time"
                    name="hearing_time"
                    value="{safe(case["hearing_time"])}"
                >

            </label>


            <label>

                {safe(t["courtroom"])}

                <input
                    name="courtroom"
                    value="{safe(case["courtroom"])}"
                >

            </label>


            <label>

                {safe(t["public_summary"])}

                <textarea
                    name="public_summary"
                >{safe(case["public_summary"])}</textarea>

            </label>


            <label>

                {safe(t["internal_notes"])}

                <textarea
                    name="internal_notes"
                >{safe(case["internal_notes"])}</textarea>

            </label>


            <button
                type="submit"
            >
                💾
                {safe(t["save"])}
            </button>

        </form>

    </div>
    """

    return page(
        t["edit_case"],
        content,
    )


# ============================================================
# DELETE CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_case(case_id):

    connection = db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
    ).fetchone()

    if case is None:

        connection.close()

        abort(404)

    case_number = case["case_number"]

    connection.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "Case deleted",
        case_number,
    )

    flash(
        labels()["case_deleted"],
        "success",
    )

    return redirect(
        url_for("staff_cases")
    )


# ============================================================
# ADD HEARING
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearings",
    methods=["POST"],
)
@staff_required
def add_hearing(case_id):

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
        200,
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

        flash(
            "Hearing date is required.",
            "warning",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    connection = db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
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
        "Hearing added",
        case["case_number"],
    )

    flash(
        labels()["hearing_added"],
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
def delete_hearing(hearing_id):

    connection = db()

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
        (
            hearing_id,
        ),
    ).fetchone()

    if hearing is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM hearings
        WHERE id = ?
        """,
        (
            hearing_id,
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "Hearing deleted",
        hearing["case_number"],
    )

    flash(
        labels()["hearing_deleted"],
        "success",
    )

    return redirect(
        request.referrer
        or url_for("staff_cases")
    )


# ============================================================
# ADD DOCUMENT REFERENCE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/documents",
    methods=["POST"],
)
@staff_required
def add_document(case_id):

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

        flash(
            "Document name and URL are required.",
            "warning",
        )

        return redirect(
            url_for(
                "staff_case",
                case_id=case_id,
            )
        )

    connection = db()

    case = connection.execute(
        """
        SELECT case_number
        FROM cases
        WHERE id = ?
        """,
        (
            case_id,
        ),
    ).fetchone()

    if case is None:

        connection.close()

        abort(404)

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
        "Document reference added",
        case["case_number"],
    )

    flash(
        labels()["document_added"],
        "success",
    )

    return redirect(
        url_for(
            "staff_case",
            case_id=case_id,
        )
    )


# ============================================================
# DELETE DOCUMENT REFERENCE
# ============================================================

@app.route(
    "/staff/documents/<int:document_id>/delete",
    methods=["POST"],
)
@staff_required
def delete_document(document_id):

    connection = db()

    document = connection.execute(
        """
        SELECT
            documents.id,
            cases.case_number
        FROM documents
        JOIN cases
            ON cases.id = documents.case_id
        WHERE documents.id = ?
        """,
        (
            document_id,
        ),
    ).fetchone()

    if document is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (
            document_id,
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "Document reference removed",
        document["case_number"],
    )

    flash(
        labels()["document_removed"],
        "success",
    )

    return redirect(
        request.referrer
        or url_for("staff_cases")
    )


# ============================================================
# STAFF NEW NOTICE
# ============================================================

@app.route(
    "/staff/notices/new",
    methods=[
        "GET",
        "POST",
    ],
)
@staff_required
def staff_new_notice():

    t = labels()

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
            ),
            10000,
        )

        body_fil = clean(
            request.form.get(
                "body_fil",
                "",
            ),
            10000,
        )

        notice_type = clean(
            request.form.get(
                "notice_type",
                "General",
            ),
            100,
        )

        if (
            not title_en
            or not title_fil
            or not body_en
            or not body_fil
        ):

            flash(
                "Please complete all notice fields.",
                "warning",
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
                "Notice published",
                title_en,
            )

            flash(
                t["notice_created"],
                "success",
            )

            return redirect(
                url_for("notices")
            )

    content = f"""

    <div class="form">

        <h1>
            📢
            {safe(t["publish_notice"])}
        </h1>

        <form
            method="post"
        >

            <label>

                {safe(t["notice_type"])}

                <select name="notice_type">

                    {"".join(
                        f'<option value="{safe(kind)}">'
                        f'{safe(kind)}'
                        f'</option>'
                        for kind in NOTICE_TYPES
                    )}

                </select>

            </label>


            <label>

                {safe(t["notice_title_en"])}

                <input
                    name="title_en"
                    required
                >

            </label>


            <label>

                {safe(t["notice_title_fil"])}

                <input
                    name="title_fil"
                    required
                >

            </label>


            <label>

                {safe(t["notice_body_en"])}

                <textarea
                    name="body_en"
                    required
                ></textarea>

            </label>


            <label>

                {safe(t["notice_body_fil"])}

                <textarea
                    name="body_fil"
                    required
                ></textarea>

            </label>


            <button
                type="submit"
            >
                📢
                {safe(t["publish"])}
            </button>

        </form>

    </div>
    """

    return page(
        t["publish_notice"],
        content,
    )


# ============================================================
# STAFF NOTICE MANAGEMENT
# ============================================================

@app.route("/staff/notices")
@staff_required
def staff_notices():

    t = labels()

    connection = db()

    notices_rows = connection.execute(
        """
        SELECT *
        FROM notices
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    rows = ""

    for notice in notices_rows:

        if current_language() == "fil":

            title = notice["title_fil"]

        else:

            title = notice["title_en"]

        rows += f"""
        <div class="row">

            <div>

                <strong>
                    {safe(title)}
                </strong>

                <br>

                <span class="status">
                    {safe(notice["notice_type"])}
                </span>

            </div>

            <form
                method="post"
                action="{url_for("delete_notice", notice_id=notice["id"])}"
            >

                <button
                    class="danger"
                    type="submit"
                    onclick="return confirm('Delete this notice?')"
                >
                    {safe(t["delete_case"])}
                </button>

            </form>

        </div>
        """

    content = f"""

    <div class="split">

        <h1>
            📢
            {safe(t["notices"])}
        </h1>

        <a
            class="button"
            href="{url_for("staff_new_notice")}"
        >
            ➕
            {safe(t["publish_notice"])}
        </a>

    </div>


    <div class="card">

        {rows or safe(t["no_notices"])}

    </div>
    """

    return page(
        t["notices"],
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
def delete_notice(notice_id):

    connection = db()

    notice = connection.execute(
        """
        SELECT *
        FROM notices
        WHERE id = ?
        """,
        (
            notice_id,
        ),
    ).fetchone()

    if notice is None:

        connection.close()

        abort(404)

    connection.execute(
        """
        DELETE FROM notices
        WHERE id = ?
        """,
        (
            notice_id,
        ),
    )

    connection.commit()

    connection.close()

    audit(
        "Notice deleted",
        notice["title_en"],
    )

    flash(
        labels()["notice_deleted"],
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


# ============================================================
# AUDIT LOG
# ============================================================

@app.route("/staff/audit")
@admin_required
def audit_log():

    connection = db()

    logs = connection.execute(
        """
        SELECT *
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT 250
        """
    ).fetchall()

    connection.close()

    rows = ""

    for log in logs:

        rows += f"""
        <div class="row">

            <strong>
                {safe(log["created_at"])}
            </strong>

            <span>
                {safe(log["username"])}
            </span>

            <span>
                {safe(log["action"])}
            </span>

            <span>
                {safe(log["target"])}
            </span>

        </div>
        """

    content = f"""

    <div class="card">

        <h1>
            🧾 Audit Log
        </h1>

        <p class="muted">
            Recent staff actions.
        </p>

        {rows or '<p>No audit records.</p>'}

    </div>
    """

    return page(
        "Audit Log",
        content,
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    t = labels()

    content = f"""

    <div class="card">

        <h1>
            ⚖️
            {safe(t["about_title"])}
        </h1>

        <p>
            <strong>
                {safe(COURT_NAME)}
            </strong>
        </p>

        <p>
            {safe(COURT_ADDRESS)}
        </p>

        <p>
            {safe(COURT_PHONE)}
        </p>

        <p>
            {safe(t["prototype_notice"])}
        </p>

    </div>
    """

    return page(
        t["about"],
        content,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact")
def contact():

    t = labels()

    content = f"""

    <div class="card">

        <h1>
            📞
            {safe(t["contact_title"])}
        </h1>

        <h2>
            {safe(COURT_NAME)}
        </h2>

        <p>
            📍
            {safe(COURT_ADDRESS)}
        </p>

        <p>
            ☎️
            {safe(COURT_PHONE)}
        </p>

        <p class="muted">
            Please verify important information
            directly with the court.
        </p>

    </div>
    """

    return page(
        t["contact"],
        content,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify(
        {
            "status": "ok",
            "service": "MCTC Silang-Amadeo",
            "timestamp": now(),
        }
    )


# ============================================================
# API - PUBLIC CASE SEARCH
# ============================================================

@app.route("/api/cases")
def api_cases():

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

    if case_number and name:

        rows = connection.execute(
            """
            SELECT
                id,
                case_number,
                title,
                parties,
                case_type,
                status,
                hearing_date,
                hearing_time,
                courtroom,
                public_summary
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
                "%" + case_number + "%",
                "%" + name + "%",
                "%" + name + "%",
            ),
        ).fetchall()

    elif case_number:

        rows = connection.execute(
            """
            SELECT
                id,
                case_number,
                title,
                parties,
                case_type,
                status,
                hearing_date,
                hearing_time,
                courtroom,
                public_summary
            FROM cases
            WHERE case_number LIKE ?
            ORDER BY case_number
            """,
            (
                "%" + case_number + "%",
            ),
        ).fetchall()

    elif name:

        rows = connection.execute(
            """
            SELECT
                id,
                case_number,
                title,
                parties,
                case_type,
                status,
                hearing_date,
                hearing_time,
                courtroom,
                public_summary
            FROM cases
            WHERE
                title LIKE ?
                OR parties LIKE ?
            ORDER BY case_number
            """,
            (
                "%" + name + "%",
                "%" + name + "%",
            ),
        ).fetchall()

    else:

        rows = []

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

@app.errorhandler(404)
def not_found(error):

    t = labels()

    content = f"""

    <div class="card empty">

        <div style="font-size:65px;">
            🔎
        </div>

        <h1>
            404
        </h1>

        <h2>
            {safe(t["not_found"])}
        </h2>

        <a
            class="button"
            href="{url_for("home")}"
        >
            {safe(t["home"])}
        </a>

    </div>
    """

    return page(
        "404",
        content,
    ), 404


@app.errorhandler(403)
def forbidden(error):

    content = """

    <div class="card empty">

        <div style="font-size:65px;">
            🔐
        </div>

        <h1>
            403
        </h1>

        <h2>
            Access denied
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

    return page(
        "403",
        content,
    ), 403


@app.errorhandler(500)
def server_error(error):

    content = """

    <div class="card empty">

        <div style="font-size:65px;">
            ⚠️
        </div>

        <h1>
            500
        </h1>

        <h2>
            Server error
        </h2>

        <p>
            Something went wrong while processing
            the request.
        </p>

        <a
            class="button"
            href="/"
        >
            Home
        </a>

    </div>
    """

    return page(
        "500",
        content,
    ), 500


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def security_headers(response):

    response.headers["X-Content-Type-Options"] = (
        "nosniff"
    )

    response.headers["X-Frame-Options"] = (
        "SAMEORIGIN"
    )

    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )

    return response


# ============================================================
# INITIALIZE
# ============================================================

initialize_database()


# ============================================================
# LOCAL DEVELOPMENT
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
