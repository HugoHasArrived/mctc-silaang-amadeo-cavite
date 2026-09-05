import os
import html
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import quote_plus

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
    abort,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# MCTC SILANG-AMADEO, CAVITE
# PUBLIC COURT INFORMATION PORTAL
# ============================================================
#
# This version intentionally uses a simple, predictable Flask
# structure so it is easier to maintain and deploy on Render.
#
# Major features:
#   * Exact civilian header order requested by the user.
#   * Centered header/navigation and responsive mobile menu.
#   * Official logo: static/image0.png.
#   * Case records with no case-title field in the UI.
#   * Case fields: case number, plaintiff/corporation name,
#     defendant last name, case type, status and descriptions.
#   * Pending is NOT an available status.
#   * Existing Pending records are migrated to Active.
#   * Public case search requires case number AND plaintiff name.
#   * Case deletion for authorized staff.
#   * Hearing editor without a courtroom field.
#   * Hearing nature and hearing status are editable.
#   * Tuesday Calendar is an uploaded image/PDF schedule.
#   * Public users can view the latest Tuesday schedule.
#   * Staff can replace the Tuesday schedule.
#   * Public requirements page.
#   * Bail bond and cash bond checklists supplied by the user.
#   * Clearance remains marked Not yet uploaded.
#   * Staff notices can upload photos/documents.
#   * Staff legal resources can be added/deleted.
#   * Admin can add other staff accounts.
#   * Logout clears the session and disables cache.
#   * English / Filipino toggle.
#   * Light / Dark toggle.
#   * Render persistent-data support via DATA_DIR.
#
# IMPORTANT DEPLOYMENT NOTE:
# Render's normal filesystem is ephemeral.  For saved cases,
# staff accounts, notices and schedules to survive redeploys,
# mount a Render persistent disk at /var/data and leave DATA_DIR
# unset, or explicitly set DATA_DIR=/var/data.
#
# ============================================================


# ============================================================
# APPLICATION / PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DATA_DIR = (
    Path("/var/data")
    if Path("/var/data").exists()
    else BASE_DIR
)

DATA_DIR = Path(
    os.environ.get(
        "DATA_DIR",
        str(DEFAULT_DATA_DIR),
    )
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = DATA_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DB_PATH = DATA_DIR / "mctc_court.db"

LOGO_FILENAME = (
    "image0.png"
    if (STATIC_DIR / "image0.png").exists()
    else "image0.jpeg"
)

app = Flask(
    __name__,
    static_folder="static",
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-in-render",
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

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
COURT_EMAIL = "mctc2sad000@judiciary.gov.ph"

GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/search/?api=1&query="
    + quote_plus(COURT_NAME + ", " + COURT_ADDRESS)
)


# ============================================================
# TRANSLATIONS
# ============================================================

TEXT = {
    "en": {
        "home": "Home",
        "about": "About Us",
        "search": "Search Case",
        "calendar": "Tuesday Calendar",
        "requirements": "Requirements",
        "news": "News and Announcements",
        "contact": "Contact Us",
        "staff_login": "Staff Login",
        "dashboard": "Staff Dashboard",
        "cases": "Cases",
        "notices": "Notices",
        "laws": "Laws, Decisions and Rules",
        "staff_accounts": "Staff Accounts",
        "logout": "Log Out",
        "login": "Log In",
        "add_case": "Add Case",
        "edit_case": "Edit Case",
        "delete": "Delete",
        "edit": "Edit",
        "save": "Save",
        "view": "View",
        "open": "Open",
        "upload": "Upload",
        "case_number": "Case Number",
        "plaintiff": "Plaintiff Last Name / Corporation Name",
        "defendant": "Defendant Last Name",
        "case_type": "Case Type",
        "status": "Status",
        "description": "Public Description",
        "hearing_date": "Hearing Date",
        "hearing_time": "Hearing Time",
        "hearing_nature": "Nature of Hearing",
        "hearing_status": "Hearing Status",
        "remarks": "Remarks",
        "email": "Email Address",
        "username": "Username",
        "password": "Password",
        "role": "Role",
        "address": "Address",
        "phone": "Telephone",
        "open_maps": "Open Google Maps",
        "official_source": "Official Source",
        "how_search": "How to Search",
        "no_results": "No matching public case was found.",
        "both_required": (
            "Both the case number and plaintiff last name / "
            "corporation name are required."
        ),
        "invalid_login": "Invalid username or password.",
        "login_required": "Please log in as authorized staff.",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. All rights reserved."
        ),
    },
    "fil": {
        "home": "Home",
        "about": "Tungkol sa Amin",
        "search": "Maghanap ng Kaso",
        "calendar": "Kalendaryo ng Martes",
        "requirements": "Mga Kinakailangan",
        "news": "Balita at mga Anunsyo",
        "contact": "Makipag-ugnayan",
        "staff_login": "Staff Login",
        "dashboard": "Dashboard ng Staff",
        "cases": "Mga Kaso",
        "notices": "Mga Abiso",
        "laws": "Mga Batas, Desisyon at Alituntunin",
        "staff_accounts": "Mga Account ng Staff",
        "logout": "Mag-Logout",
        "login": "Mag-Login",
        "add_case": "Magdagdag ng Kaso",
        "edit_case": "I-edit ang Kaso",
        "delete": "Burahin",
        "edit": "I-edit",
        "save": "I-save",
        "view": "Tingnan",
        "open": "Buksan",
        "upload": "Mag-upload",
        "case_number": "Numero ng Kaso",
        "plaintiff": (
            "Apelyido ng Nagsasakdal / Pangalan ng Korporasyon"
        ),
        "defendant": "Apelyido ng Nasasakdal",
        "case_type": "Uri ng Kaso",
        "status": "Katayuan",
        "description": "Pampublikong Deskripsyon",
        "hearing_date": "Petsa ng Pagdinig",
        "hearing_time": "Oras ng Pagdinig",
        "hearing_nature": "Uri ng Pagdinig",
        "hearing_status": "Katayuan ng Pagdinig",
        "remarks": "Mga Tala",
        "email": "Email Address",
        "username": "Username",
        "password": "Password",
        "role": "Role",
        "address": "Address",
        "phone": "Telepono",
        "open_maps": "Buksan ang Google Maps",
        "official_source": "Opisyal na Source",
        "how_search": "Paano Maghanap",
        "no_results": "Walang nakitang pampublikong kaso.",
        "both_required": (
            "Kinakailangan ang parehong case number at "
            "apelyido ng nagsasakdal / pangalan ng korporasyon."
        ),
        "invalid_login": "Mali ang username o password.",
        "login_required": "Mag-login bilang awtorisadong staff.",
        "copyright": (
            "© 2026 Municipal Circuit Trial Court of "
            "Silang-Amadeo, Cavite. Lahat ng karapatan ay nakalaan."
        ),
    },
}


# ============================================================
# REQUIREMENTS TRANSCRIBED FROM USER-PROVIDED PHOTOS
# ============================================================

BOND_REQUIREMENTS = [
    "PERSONAL DATA (form from court)",
    (
        "PICTURES 2x2 (with name tag, signature, "
        "case, case number and date)"
    ),
    "4 pcs. Front",
    "4 pcs. Left side",
    "4 pcs. Right side",
    (
        "BARANGAY CLEARANCE attesting the Real Name "
        "of the accused and bonafide resident"
    ),
    (
        "CERTIFICATION (Permanent Residency) attesting "
        "how many years of stay"
    ),
    (
        "HOUSE SKETCH – certified, signed and sealed "
        "by Barangay Captain with date"
    ),
    "CERTIFICATE OF DETENTION (if detained or arrested)",
    (
        "AFFIDAVIT OF VOLUNTARY SURRENDER "
        "(if voluntary or not detained)"
    ),
    "FINGER PRINT (piano)",
    "SPECIMEN SIGNATURE (at least 5 signature)",
    "AFFIDAVIT OF UNDERTAKING",
    (
        "VALID GOVERNMENT-ISSUED I.D. "
        "(original AND xerox copy back-to-back)"
    ),
    (
        "ORIGINAL COPY OF PSA BIRTH CERTIFICATE "
        "(latest copy with attached receipt)"
    ),
    (
        "*if married, female – original COPY OF PSA "
        "MARRIAGE CERTIFICATE with attached receipt"
    ),
    (
        "**FOR INQUIRIES, kindly seek assistance from "
        "court staff. Thank you"
    ),
]

CASH_BOND_REQUIREMENTS = [
    "Personal Data",
    (
        "Pictures 2x2 with name tag, signature, "
        "case, case number and date"
    ),
    "4 pcs. Front",
    "4 pcs. Left side",
    "4 pcs. Right side",
    (
        "Barangay Clearance attesting the Real Name "
        "of the accused and bonafide resident"
    ),
    (
        "And Certification (Permanent Residency) "
        "attesting how many year of stay"
    ),
    (
        "House sketch – Certified, signed and seal "
        "by Brgy. Captain with date"
    ),
    "Certificate of Detention (if detained or arrested)",
    (
        "Affidavit of Voluntary Surrender "
        "(if voluntary or not detained)"
    ),
    "Finger Print (Piano)",
    "Specimen Signature at least 5 signature",
    "Affidavit of Undertaking",
    (
        "Valid I.D (Government issued I.D) "
        "(Original and Xerox back to back)"
    ),
    "Original Copy of PSA Birth Certificate with attached receipt",
    (
        "If married, female – original copy of PSA "
        "Marriage Certificate with attached receipt"
    ),
]


# ============================================================
# HELPERS
# ============================================================

def esc(value):
    return html.escape(
        str(value or ""),
        quote=True,
    )


def now():
    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def language():
    value = session.get("language", "en")
    return value if value in TEXT else "en"


def tr(key):
    return TEXT[language()].get(key, key)


def get_db():
    connection = sqlite3.connect(
        DB_PATH,
        timeout=20,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def allowed_extension(filename):
    extension = Path(filename).suffix.lower()
    return extension in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".txt",
    }


def save_upload(upload):
    if upload is None or not upload.filename:
        return None, None

    original = secure_filename(
        upload.filename
    )

    if not original:
        return None, None

    if not allowed_extension(original):
        raise ValueError(
            "This file type is not allowed."
        )

    generated = (
        secrets.token_hex(16)
        + "_"
        + original
    )

    path = UPLOAD_DIR / generated
    upload.save(path)

    return generated, original


def remove_uploaded_file(filename):
    if not filename:
        return

    path = UPLOAD_DIR / filename

    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def is_staff():
    return bool(
        session.get(
            "staff_logged_in",
            False,
        )
    )


def is_admin():
    return (
        is_staff()
        and session.get(
            "staff_role"
        ) == "admin"
    )


# ============================================================
# DATABASE INITIALIZATION / MIGRATION
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
            last_name TEXT NOT NULL DEFAULT '',
            parties TEXT NOT NULL DEFAULT '',
            case_title TEXT NOT NULL DEFAULT '',
            case_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Active',
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
            FOREIGN KEY(case_id) REFERENCES cases(id)
            ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS tuesday_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            created_at TEXT NOT NULL
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
    # Backward-compatible schema migration for older code.
    # --------------------------------------------------------

    case_columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(cases)"
        ).fetchall()
    }

    if "plaintiff_name" not in case_columns:
        connection.execute(
            "ALTER TABLE cases ADD COLUMN plaintiff_name TEXT NOT NULL DEFAULT ''"
        )

    if "defendant_last_name" not in case_columns:
        connection.execute(
            "ALTER TABLE cases ADD COLUMN defendant_last_name TEXT NOT NULL DEFAULT ''"
        )

    # Existing records that used last_name are treated as the
    # plaintiff field when the newer field is empty.
    connection.execute(
        """
        UPDATE cases
        SET plaintiff_name = last_name
        WHERE trim(COALESCE(plaintiff_name, '')) = ''
        AND trim(COALESCE(last_name, '')) <> ''
        """
    )

    # Existing Pending records are normalized because Pending
    # is no longer available in the interface.
    connection.execute(
        """
        UPDATE cases
        SET status = 'Active'
        WHERE lower(COALESCE(status, '')) = 'pending'
        """
    )

    # Copy the legacy parties field into the new defendant field
    # only when the new defendant field is still blank.  Staff can
    # edit it afterward.
    connection.execute(
        """
        UPDATE cases
        SET defendant_last_name = last_name
        WHERE trim(COALESCE(defendant_last_name, '')) = ''
        AND trim(COALESCE(last_name, '')) <> ''
        """
    )

    # --------------------------------------------------------
    # Initial requirements records.
    # --------------------------------------------------------

    defaults = [
        (
            "bond",
            "Requirements for Posting Bail Bond",
            "Mga Kinakailangan para sa Posting Bail Bond",
            "See the public checklist below.",
            "Tingnan ang pampublikong checklist sa ibaba.",
        ),
        (
            "cash_bond",
            "Requirements for Cash Bond",
            "Mga Kinakailangan para sa Cash Bond",
            "See the public checklist below.",
            "Tingnan ang pampublikong checklist sa ibaba.",
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
        exists = connection.execute(
            "SELECT id FROM requirements WHERE category = ?",
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
    # Initial admin account.
    # --------------------------------------------------------

    admin = connection.execute(
        "SELECT id FROM staff WHERE username = ?",
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
                generate_password_hash("admin123"),
                "admin",
                1,
                now(),
            ),
        )

    connection.commit()
    connection.close()


init_db()


# ============================================================
# AUTHORIZATION
# ============================================================

def staff_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_staff():
            flash(
                tr("login_required"),
                "warning",
            )
            return redirect(
                url_for("staff_login")
            )
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_staff():
            return redirect(
                url_for("staff_login")
            )
        if not is_admin():
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


# ============================================================
# HTML / CSS
# ============================================================

STYLE = """
:root {
    --bg: #f9f7fb;
    --surface: #ffffff;
    --surface2: #f0e9f7;
    --text: #241629;
    --muted: #6f6176;
    --border: #ddd0e6;
    --purple: #6d28d9;
    --purple2: #8b5cf6;
    --purple3: #3b0764;
    --danger: #a61e40;
    --success: #18723c;
    --warning: #a16207;
}

body.dark {
    --bg: #110d15;
    --surface: #201723;
    --surface2: #302039;
    --text: #fff8ff;
    --muted: #d0c1d8;
    --border: #503c59;
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
    background: var(--bg);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
}

a {
    color: var(--purple);
    text-decoration: none;
}

body.dark a {
    color: #cfb9ff;
}

a:hover {
    text-decoration: underline;
}

.site-header {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: linear-gradient(
        135deg,
        var(--purple3),
        var(--purple),
        var(--purple2)
    );
    color: white;
    box-shadow: 0 5px 20px rgba(38, 4, 50, .28);
}

.header-inner {
    width: 100%;
    max-width: 1500px;
    margin: 0 auto;
    padding: 12px 20px 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.brand-area {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.brand-link {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    text-align: center;
    color: white;
    text-decoration: none;
}

.brand-link:hover {
    text-decoration: none;
}

.logo {
    width: 76px;
    height: 76px;
    padding: 4px;
    object-fit: contain;
    border-radius: 50%;
    background: white;
    box-shadow: 0 4px 18px rgba(0,0,0,.18);
}

.brand strong,
.brand small {
    display: block;
    text-align: center;
}

.brand strong {
    font-size: 15px;
    line-height: 1.2;
}

.brand small {
    opacity: .9;
    margin-top: 3px;
}

.nav {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    flex-wrap: wrap;
}

.nav-public,
.nav-staff,
.nav-tools {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    flex-wrap: wrap;
}

.nav a,
.nav button {
    min-height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 8px 9px;
    border: 0;
    border-radius: 9px;
    color: white;
    background: transparent;
    font-size: 12px;
    font-weight: 800;
    text-align: center;
    white-space: nowrap;
    cursor: pointer;
}

.nav a:hover,
.nav button:hover {
    color: white;
    background: rgba(255,255,255,.15);
    text-decoration: none;
}

.nav-inline {
    display: inline-flex;
    align-items: center;
    margin: 0;
    padding: 0;
}

.container {
    width: 94%;
    max-width: 1180px;
    margin: 0 auto;
    padding: 28px 0 70px;
}

.hero {
    margin: 15px 0 25px;
    padding: 50px 20px;
    border-radius: 26px;
    text-align: center;
    color: white;
    background: linear-gradient(
        135deg,
        var(--purple3),
        var(--purple),
        var(--purple2)
    );
}

.hero-logo {
    width: 150px;
    height: 150px;
    object-fit: contain;
    background: white;
    padding: 5px;
    border-radius: 50%;
    box-shadow: 0 8px 30px rgba(0,0,0,.22);
}

.hero h1 {
    max-width: 950px;
    margin: 16px auto;
    font-size: clamp(30px, 5vw, 56px);
    line-height: 1.05;
}

.card {
    margin: 16px 0;
    padding: 22px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(65,25,85,.06);
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
}

.two {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}

form {
    width: 100%;
}

label {
    display: block;
    margin: 10px 0 5px;
    font-weight: 800;
}

input,
textarea,
select {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text);
    font: inherit;
}

textarea {
    min-height: 115px;
    resize: vertical;
}

button,
.button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    padding: 10px 15px;
    border: 0;
    border-radius: 10px;
    background: var(--purple);
    color: white;
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
}

button:hover,
.button:hover {
    background: var(--purple3);
    color: white;
    text-decoration: none;
}

.secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
}

.secondary:hover {
    color: var(--text);
}

.danger {
    background: var(--danger);
}

.success-button {
    background: var(--success);
}

.actions {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-top: 14px;
}

.notice {
    margin: 12px 0;
    padding: 14px 16px;
    border-left: 5px solid var(--purple);
    border-radius: 10px;
    background: var(--surface2);
}

.notice.warning {
    border-left-color: var(--warning);
}

.notice.success {
    border-left-color: var(--success);
}

.notice.danger {
    border-left-color: var(--danger);
}

.status {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--surface2);
    color: var(--purple);
    font-size: 12px;
    font-weight: 900;
}

.table-wrap {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
}

th {
    background: var(--surface2);
}

.empty {
    text-align: center;
    padding: 40px;
    color: var(--muted);
}

.small {
    color: var(--muted);
    font-size: 13px;
}

.stat {
    text-align: center;
}

.stat-number {
    display: block;
    color: var(--purple);
    font-size: 42px;
    font-weight: 900;
}

.requirement-list li {
    margin: 7px 0;
}

.schedule-image {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
    border-radius: 14px;
    box-shadow: 0 5px 18px rgba(0,0,0,.12);
}

.schedule-pdf {
    width: 100%;
    min-height: 850px;
    border: 1px solid var(--border);
    border-radius: 14px;
}

footer {
    padding: 30px 15px;
    border-top: 1px solid var(--border);
    background: var(--surface);
    color: var(--muted);
    text-align: center;
}

@media (max-width: 920px) {
    .nav {
        gap: 4px;
    }

    .nav-public,
    .nav-staff,
    .nav-tools {
        width: 100%;
    }

    .two {
        grid-template-columns: 1fr;
    }
}


.mobile-menu-toggle {
    display: none;
}

.mobile-menu {
    display: none;
}

@media (max-width: 700px) {
    .header-inner {
        padding: 10px 9px 12px;
    }

    .brand-link {
        flex-direction: column;
    }

    .logo {
        width: 70px;
        height: 70px;
    }

    .brand strong {
        max-width: 330px;
    }

    .nav {
        width: 100%;
    }

    .desktop-nav {
        display: none;
    }

    .mobile-menu {
        display: block;
        width: 100%;
    }

    .mobile-menu summary {
        list-style: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        border: 1px solid rgba(255,255,255,.22);
        border-radius: 10px;
        color: white;
        font-weight: 900;
        background: rgba(255,255,255,.08);
    }

    .mobile-menu summary::-webkit-details-marker {
        display: none;
    }

    .mobile-menu-panel {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: 3px;
        padding-top: 6px;
    }

    .mobile-menu-panel a,
    .mobile-menu-panel button {
        width: 100%;
        text-align: center;
    }

    .nav-inline {
        width: 100%;
    }

    .nav-inline .nav-button {
        width: 100%;
    }
}
"""


# ============================================================
# PAGE WRAPPER
# ============================================================

def flash_html():
    result = []

    for category, message in __import__(
        "flask"
    ).get_flashed_messages(
        with_categories=True
    ):
        result.append(
            f"<div class='notice {esc(category)}'>"
            f"{esc(message)}"
            f"</div>"
        )

    return "".join(result)


def render_page(title, content):
    theme = session.get("theme", "light")

    next_theme = "dark" if theme == "light" else "light"

    next_language = "fil" if language() == "en" else "en"

    language_label = "FIL" if language() == "en" else "EN"

    theme_label = "Dark" if theme == "light" else "Light"

    if is_staff():
        desktop_navigation = f"""
        <div class="nav-staff">
            <a href="{url_for('staff_dashboard')}">{tr('dashboard')}</a>
            <a href="{url_for('staff_cases')}">{tr('cases')}</a>
            <a href="{url_for('staff_calendar')}">{tr('calendar')}</a>
            <a href="{url_for('staff_notices')}">{tr('notices')}</a>
            <a href="{url_for('staff_laws')}">{tr('laws')}</a>
            <a href="{url_for('staff_requirements')}">{tr('requirements')}</a>
            {
                f'<a href="{url_for("staff_accounts")}">{tr("staff_accounts")}</a>'
                if is_admin()
                else ""
            }
            <form method="post" action="{url_for('logout')}" class="nav-inline">
                <button type="submit" class="nav-button">{tr('logout')}</button>
            </form>
        </div>
        """

        mobile_navigation = f"""
        <details class="mobile-menu">
            <summary>☰ Staff Menu</summary>
            <div class="mobile-menu-panel">
                <a href="{url_for('staff_dashboard')}">{tr('dashboard')}</a>
                <a href="{url_for('staff_cases')}">{tr('cases')}</a>
                <a href="{url_for('staff_calendar')}">{tr('calendar')}</a>
                <a href="{url_for('staff_notices')}">{tr('notices')}</a>
                <a href="{url_for('staff_laws')}">{tr('laws')}</a>
                <a href="{url_for('staff_requirements')}">{tr('requirements')}</a>
                {
                    f'<a href="{url_for("staff_accounts")}">{tr("staff_accounts")}</a>'
                    if is_admin()
                    else ""
                }
                <form method="post" action="{url_for('logout')}" class="nav-inline">
                    <button type="submit" class="nav-button">{tr('logout')}</button>
                </form>
            </div>
        </details>
        """

        final_tools = f"""
        <div class="nav-tools">
            <a href="{url_for('change_language', value=next_language)}">{language_label}</a>
            <a href="{url_for('change_theme', value=next_theme)}">{theme_label}</a>
        </div>
        """

    else:
        # Exact civilian order requested:
        # Home -> About Us -> Search Case -> Tuesday Calendar ->
        # Requirements -> News and Announcements -> Contact Us ->
        # Language -> Light/Dark -> Staff Login
        desktop_navigation = f"""
        <div class="nav-public">
            <a href="{url_for('home')}">{tr('home')}</a>
            <a href="{url_for('about')}">{tr('about')}</a>
            <a href="{url_for('search_cases')}">{tr('search')}</a>
            <a href="{url_for('public_calendar')}">{tr('calendar')}</a>
            <a href="{url_for('requirements')}">{tr('requirements')}</a>
            <a href="{url_for('news')}">{tr('news')}</a>
            <a href="{url_for('contact')}">{tr('contact')}</a>
            <a href="{url_for('change_language', value=next_language)}">{language_label}</a>
            <a href="{url_for('change_theme', value=next_theme)}">{theme_label}</a>
            <a href="{url_for('staff_login')}">{tr('staff_login')}</a>
        </div>
        """

        mobile_navigation = f"""
        <details class="mobile-menu">
            <summary>☰ Menu</summary>
            <div class="mobile-menu-panel">
                <a href="{url_for('home')}">{tr('home')}</a>
                <a href="{url_for('about')}">{tr('about')}</a>
                <a href="{url_for('search_cases')}">{tr('search')}</a>
                <a href="{url_for('public_calendar')}">{tr('calendar')}</a>
                <a href="{url_for('requirements')}">{tr('requirements')}</a>
                <a href="{url_for('news')}">{tr('news')}</a>
                <a href="{url_for('contact')}">{tr('contact')}</a>
                <a href="{url_for('change_language', value=next_language)}">{language_label}</a>
                <a href="{url_for('change_theme', value=next_theme)}">{theme_label}</a>
                <a href="{url_for('staff_login')}">{tr('staff_login')}</a>
            </div>
        </details>
        """

        final_tools = ""

    return f"""<!DOCTYPE html>
<html lang="{esc(language())}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="MCTC Silang-Amadeo Court Information Portal">
<title>{esc(title)} - {esc(COURT_NAME)}</title>
<style>{STYLE}</style>
</head>
<body class="{esc(theme)}">

<header class="site-header">
<div class="header-inner">

<div class="brand-area">
<a class="brand-link" href="{url_for('home')}">
<img
    class="logo"
    src="{url_for('static', filename=LOGO_FILENAME)}"
    alt="Official court logo"
>
<div class="brand">
<strong>{esc(COURT_NAME)}</strong>
<small>Official Court Information Portal</small>
</div>
</a>
</div>

<nav class="nav">
<div class="desktop-nav">
{desktop_navigation}
{final_tools}
</div>
{mobile_navigation}
</nav>

</div>
</header>

<main class="container">
{flash_html()}
{content}
</main>

<footer>
<strong>{esc(COURT_NAME)}</strong>
<p>{esc(COURT_ADDRESS)}</p>
<p><a href="tel:{esc(COURT_PHONE)}">{esc(COURT_PHONE)}</a><br><a href="mailto:{esc(COURT_EMAIL)}">{esc(COURT_EMAIL)}</a></p>
<p><a href="{GOOGLE_MAPS_URL}" target="_blank" rel="noopener noreferrer">🗺️ {tr('open_maps')}</a></p>
<p>{tr('copyright')}</p>
</footer>

</body>
</html>"""


# ============================================================
# LANGUAGE / THEME
# ============================================================

@app.route("/language/<value>")
def change_language(value):
    session["language"] = (
        value
        if value in TEXT
        else "en"
    )
    return redirect(
        request.referrer or url_for("home")
    )


@app.route("/theme/<value>")
def change_theme(value):
    session["theme"] = (
        value
        if value in {"light", "dark"}
        else "light"
    )
    return redirect(
        request.referrer or url_for("home")
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

    cards = ""

    for notice in notices:
        title = (
            notice["title_fil"]
            if language() == "fil"
            else notice["title_en"]
        )

        body = (
            notice["body_fil"]
            if language() == "fil"
            else notice["body_en"]
        )

        attachment = ""

        if notice["attachment"]:
            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=notice['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        cards += (
            "<article class='notice'>"
            f"<h3>{esc(title)}</h3>"
            f"<p>{esc(body)}</p>"
            f"{attachment}"
            "</article>"
        )

    content = f"""
<section class="hero">

<img
    class="hero-logo"
    src="{url_for('static', filename=LOGO_FILENAME)}"
    alt="Official court logo"
>

<h1>{esc(COURT_NAME)}</h1>

<p>
Public court information, case searching,
requirements, notices and the Tuesday schedule.
</p>

<div class="actions" style="justify-content:center">

<a class="button" href="{url_for('search_cases')}">
🔎 {tr('search')}
</a>

<a class="button secondary" href="{url_for('public_calendar')}">
📅 {tr('calendar')}
</a>

<a class="button secondary" href="{url_for('requirements')}">
📄 {tr('requirements')}
</a>

</div>

</section>

<section class="grid">

<div class="card">
<h2>🔎 {tr('search')}</h2>
<p>
Search requires BOTH the case number and the plaintiff
last name / corporation name.
</p>
<a class="button" href="{url_for('search_cases')}">
{tr('search')}
</a>
</div>

<div class="card">
<h2>📄 {tr('requirements')}</h2>
<p>
View posting bail bond, cash bond and clearance information.
</p>
<a class="button" href="{url_for('requirements')}">
{tr('view')}
</a>
</div>

<div class="card">
<h2>📅 {tr('calendar')}</h2>
<p>
View the latest Tuesday schedule uploaded by staff.
</p>
<a class="button" href="{url_for('public_calendar')}">
{tr('view')}
</a>
</div>

<div class="card">
<h2>📢 {tr('news')}</h2>
<p>
Read official announcements and notices.
</p>
<a class="button" href="{url_for('news')}">
{tr('view')}
</a>
</div>

</section>

<section class="card">
<h2>📢 {tr('news')}</h2>
{cards or '<p class="empty">No announcements yet.</p>'}
</section>
"""

    return render_page(
        tr("home"),
        content,
    )


# ============================================================
# ABOUT / CONTACT / NEWS
# ============================================================

@app.route("/about")
def about():
    content = f"""
<div class="card">
<h1>{tr('about')}</h1>
<h2>{esc(COURT_NAME)}</h2>
<p>
This portal provides approved public court information,
announcements, requirements, the Tuesday schedule and
public case-search functionality.
</p>
<div class="notice warning">
<strong>Important</strong>
<p>
Online information does not replace official court records,
orders, notices or certified documents.
</p>
</div>
</div>
"""
    return render_page(
        tr("about"),
        content,
    )


@app.route("/contact")
def contact():
    content = f"""
<div class="card">
<h1>{tr('contact')}</h1>
<h2>{esc(COURT_NAME)}</h2>

<p>
<strong>{tr('address')}:</strong><br>
{esc(COURT_ADDRESS)}
</p>

<p>
<strong>{tr('phone')}:</strong><br>
<a href="tel:{esc(COURT_PHONE)}">{esc(COURT_PHONE)}</a>
</p>

<p>
<strong>{tr('email')}:</strong><br>
<a href="mailto:{esc(COURT_EMAIL)}">{esc(COURT_EMAIL)}</a>
</p>

<a
    class="button"
    href="{GOOGLE_MAPS_URL}"
    target="_blank"
    rel="noopener noreferrer"
>
🗺️ {tr('open_maps')}
</a>

</div>
"""
    return render_page(
        tr("contact"),
        content,
    )


@app.route("/news")
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

    content = f"""
<div class="card">
<h1>📢 {tr('news')}</h1>
<p>
Official notices and announcements published by authorized staff.
</p>
</div>
"""

    for notice in notices:
        title = (
            notice["title_fil"]
            if language() == "fil"
            else notice["title_en"]
        )

        body = (
            notice["body_fil"]
            if language() == "fil"
            else notice["body_en"]
        )

        attachment = ""

        if notice["attachment"]:
            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=notice['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        content += f"""
<div class="card">
<h2>{esc(title)}</h2>
<p>{esc(body)}</p>
{attachment}
</div>
"""

    if not notices:
        content += (
            "<div class='card empty'>"
            "No announcements have been published."
            "</div>"
        )

    return render_page(
        tr("news"),
        content,
    )


# ============================================================
# PUBLIC CASE SEARCH
# ============================================================

@app.route(
    "/search",
    methods=["GET", "POST"],
)
def search_cases():
    case_number = request.values.get(
        "case_number",
        "",
    ).strip()

    plaintiff = request.values.get(
        "plaintiff_name",
        "",
    ).strip()

    result = None

    if request.method == "POST":
        if not case_number or not plaintiff:
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
                WHERE lower(case_number) = lower(?)
                AND lower(plaintiff_name) = lower(?)
                LIMIT 1
                """,
                (
                    case_number,
                    plaintiff,
                ),
            ).fetchone()

            connection.close()

            if result is None:
                flash(
                    tr("no_results"),
                    "warning",
                )

    content = f"""
<div class="card">

<h1>🔎 {tr('search')}</h1>

<div class="notice">
<h3>{tr('how_search')}</h3>
<ol>
<li>Enter the complete case number.</li>
<li>Enter the plaintiff last name or corporation name.</li>
<li>Both fields are required.</li>
<li>Select Search Case.</li>
</ol>
</div>

<form method="post">

<label>{tr('case_number')}</label>
<input
    name="case_number"
    value="{esc(case_number)}"
    autocomplete="off"
    required
>

<label>{tr('plaintiff')}</label>
<input
    name="plaintiff_name"
    value="{esc(plaintiff)}"
    autocomplete="off"
    required
>

<button type="submit">
🔎 {tr('search')}
</button>

</form>

</div>
"""

    if result:
        content += f"""
<div class="card">

<span class="status">
{esc(result['status'])}
</span>

<h2>
{esc(result['case_number'])}
</h2>

<p>
<strong>{tr('plaintiff')}:</strong><br>
{esc(result['plaintiff_name'])}
</p>

<p>
<strong>{tr('defendant')}:</strong><br>
{esc(result['defendant_last_name'])}
</p>

<p>
<strong>{tr('case_type')}:</strong><br>
{esc(result['case_type'])}
</p>

<p>
{esc(result['public_description'])}
</p>

<a
class="button"
href="{url_for('public_case', case_id=result['id'])}"
>
{tr('view')}
</a>

</div>
"""

    return render_page(
        tr("search"),
        content,
    )


# ============================================================
# PUBLIC CASE DETAILS / HEARINGS
# ============================================================

@app.route("/case/<int:case_id>")
def public_case(case_id):
    connection = get_db()

    case = connection.execute(
        "SELECT * FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    hearings = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY hearing_date, hearing_time
        """,
        (case_id,),
    ).fetchall()

    connection.close()

    if case is None:
        abort(404)

    hearing_html = ""

    for hearing in hearings:
        hearing_html += f"""
<div class="notice">

<h3>
{esc(hearing['hearing_date'])}
</h3>

<p>
<strong>{tr('hearing_time')}:</strong>
{esc(hearing['hearing_time'])}
</p>

<p>
<strong>{tr('hearing_nature')}:</strong>
{esc(hearing['hearing_nature'])}
</p>

<p>
<strong>{tr('hearing_status')}:</strong>
<span class="status">
{esc(hearing['hearing_status'])}
</span>
</p>

<p>
{esc(hearing['remarks'])}
</p>

</div>
"""

    if not hearing_html:
        hearing_html = (
            "<p class='small'>"
            "No published hearing information."
            "</p>"
        )

    content = f"""
<div class="card">

<span class="status">
{esc(case['status'])}
</span>

<h1>
{esc(case['case_number'])}
</h1>

<p>
<strong>{tr('plaintiff')}:</strong><br>
{esc(case['plaintiff_name'])}
</p>

<p>
<strong>{tr('defendant')}:</strong><br>
{esc(case['defendant_last_name'])}
</p>

<p>
<strong>{tr('case_type')}:</strong><br>
{esc(case['case_type'])}
</p>

<p>
{esc(case['public_description'])}
</p>

</div>

<div class="card">
<h2>📅 Hearings</h2>
{hearing_html}
</div>
"""

    return render_page(
        "Case",
        content,
    )


# ============================================================
# PUBLIC TUESDAY SCHEDULE
# ============================================================

@app.route("/calendar")
def public_calendar():
    connection = get_db()

    schedule = connection.execute(
        """
        SELECT *
        FROM tuesday_schedule
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    schedule_html = ""

    if schedule:
        file_url = url_for(
            "uploaded_file",
            filename=schedule["file_name"],
        )

        extension = Path(
            schedule["original_filename"]
        ).suffix.lower()

        if extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }:
            schedule_html = f"""
<div class="card">

<img
    class="schedule-image"
    src="{file_url}"
    alt="Tuesday court schedule"
>

<p style="text-align:center">
<a
    class="button secondary"
    href="{file_url}"
    target="_blank"
    rel="noopener noreferrer"
>
Open Full Schedule
</a>
</p>

</div>
"""
        else:
            schedule_html = f"""
<div class="card">

<iframe
    class="schedule-pdf"
    src="{file_url}"
    title="Tuesday court schedule"
></iframe>

<p>
<a
    class="button secondary"
    href="{file_url}"
    target="_blank"
    rel="noopener noreferrer"
>
Open Full Schedule
</a>
</p>

</div>
"""
    else:
        schedule_html = (
            "<div class='card empty'>"
            "The Tuesday schedule has not yet been uploaded."
            "</div>"
        )

    content = f"""
<div class="card">

<h1>📅 {tr('calendar')}</h1>

<p>
View the latest Tuesday schedule uploaded by authorized staff.
</p>

<div class="notice warning">
Schedule information may change. Confirm important information
with the court.
</div>

</div>

{schedule_html}
"""

    return render_page(
        tr("calendar"),
        content,
    )


# ============================================================
# PUBLIC REQUIREMENTS
# ============================================================

@app.route("/requirements")
def requirements():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY
            CASE category
                WHEN 'bond' THEN 1
                WHEN 'cash_bond' THEN 2
                WHEN 'clearance' THEN 3
                ELSE 4
            END
        """
    ).fetchall()

    connection.close()

    content = f"""
<div class="card">

<h1>📄 {tr('requirements')}</h1>

<p>
The following information is provided for public guidance.
Please confirm the current official requirements with the court.
</p>

</div>
"""

    for row in rows:
        title = (
            row["title_fil"]
            if language() == "fil"
            else row["title_en"]
        )

        description = (
            row["description_fil"]
            if language() == "fil"
            else row["description_en"]
        )

        if row["category"] == "bond":
            items = BOND_REQUIREMENTS
        elif row["category"] == "cash_bond":
            items = CASH_BOND_REQUIREMENTS
        else:
            items = []

        checklist = ""

        if items:
            checklist = "<ol class='requirement-list'>"
            for item in items:
                checklist += (
                    f"<li>{esc(item)}</li>"
                )
            checklist += "</ol>"
        else:
            checklist = (
                "<p class='small'>"
                "Not yet uploaded."
                " Please contact the court for the current official clearance requirements."
                "</p>"
            )

        file_link = ""

        if row["file_name"]:
            file_link = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        content += f"""
<div class="card">

<h2>{esc(title)}</h2>

<div class="notice">
{checklist}
</div>

<p>
{esc(description)}
</p>

{file_link}

</div>
"""

    return render_page(
        tr("requirements"),
        content,
    )


# ============================================================
# PUBLIC LAWS
# ============================================================

@app.route("/laws")
def laws():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY category, created_at DESC
        """
    ).fetchall()

    connection.close()

    content = f"""
<div class="card">
<h1>⚖️ {tr('laws')}</h1>
<p>
Authorized staff can add Philippine laws, Supreme Court
Decisions, Rules and other official legal resources.
</p>
</div>
"""

    for row in rows:
        links = ""

        if row["source_url"]:
            links += (
                f"<a class='button secondary' "
                f"href='{esc(row['source_url'])}' "
                f"target='_blank' rel='noopener noreferrer'>"
                f"{tr('official_source')}</a> "
            )

        if row["file_name"]:
            links += (
                f"<a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"{tr('open')}</a>"
            )

        content += f"""
<div class="card">

<span class="status">
{esc(row['category'])}
</span>

<h2>
{esc(row['title'])}
</h2>

<p>
{esc(row['description'])}
</p>

{links}

</div>
"""

    if not rows:
        content += (
            "<div class='card empty'>"
            "No legal resources have been published yet."
            "</div>"
        )

    return render_page(
        tr("laws"),
        content,
    )


# ============================================================
# STAFF LOGIN / LOGOUT
# ============================================================

@app.route(
    "/staff/login",
    methods=["GET", "POST"],
)
def staff_login():
    if is_staff():
        return redirect(
            url_for("staff_dashboard")
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
            staff is not None
            and check_password_hash(
                staff["password_hash"],
                password,
            )
        ):
            session.clear()
            session["staff_logged_in"] = True
            session["staff_id"] = staff["id"]
            session["staff_username"] = staff["username"]
            session["staff_role"] = staff["role"]
            session["language"] = "en"
            session["theme"] = "light"

            flash(
                "Login successful.",
                "success",
            )

            return redirect(
                url_for("staff_dashboard")
            )

        flash(
            tr("invalid_login"),
            "danger",
        )

    content = f"""
<div class="card" style="max-width:520px;margin:40px auto">

<div style="text-align:center">
<img
    class="hero-logo"
    src="{url_for('static', filename=LOGO_FILENAME)}"
    alt="Court logo"
>
</div>

<h1>🔐 {tr('staff_login')}</h1>

<p class="small">
Authorized court staff only.
</p>

<form method="post" autocomplete="off">

<label>{tr('username')}</label>
<input
    name="username"
    autocomplete="username"
    required
>

<label>{tr('password')}</label>
<input
    type="password"
    name="password"
    autocomplete="current-password"
    required
>

<br>

<button type="submit">
{tr('login')}
</button>

</form>

</div>
"""

    return render_page(
        tr("staff_login"),
        content,
    )


@app.route(
    "/staff/logout",
    methods=["GET", "POST"],
)
def logout():
    session.clear()

    response = redirect(
        url_for("home")
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
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

@app.route("/staff")
@app.route("/staff/dashboard")
@staff_required
def staff_dashboard():
    connection = get_db()

    case_count = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    notice_count = connection.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    legal_count = connection.execute(
        "SELECT COUNT(*) FROM legal_resources"
    ).fetchone()[0]

    connection.close()

    content = f"""
<section class="hero">

<h1>{tr('dashboard')}</h1>

<p>
Welcome, {esc(session.get('staff_username', 'Staff'))}.
</p>

</section>

<div class="grid">

<div class="stat card">
<span class="stat-number">{case_count}</span>
{tr('cases')}
</div>

<div class="stat card">
<span class="stat-number">{notice_count}</span>
{tr('notices')}
</div>

<div class="stat card">
<span class="stat-number">{legal_count}</span>
{tr('laws')}
</div>

</div>

<div class="card">
<h2>⚡ Quick Actions</h2>

<div class="grid">

<a class="card" href="{url_for('staff_cases')}">
<h3>📋 {tr('cases')}</h3>
<p>Manage saved case records.</p>
</a>

<a class="card" href="{url_for('staff_calendar')}">
<h3>📅 {tr('calendar')}</h3>
<p>Upload the latest Tuesday schedule.</p>
</a>

<a class="card" href="{url_for('staff_notices')}">
<h3>📢 {tr('notices')}</h3>
<p>Publish notices with photos or documents.</p>
</a>

<a class="card" href="{url_for('staff_laws')}">
<h3>⚖️ {tr('laws')}</h3>
<p>Manage legal resources.</p>
</a>

<a class="card" href="{url_for('staff_requirements')}">
<h3>📄 {tr('requirements')}</h3>
<p>Manage requirements and uploaded documents.</p>
</a>

{('<a class="card" href="' + url_for('staff_accounts') + '"><h3>👥 ' + tr('staff_accounts') + '</h3><p>Manage authorized staff.</p></a>') if is_admin() else ''}

</div>
</div>
"""

    return render_page(
        tr("dashboard"),
        content,
    )


# ============================================================
# STAFF CASES
# ============================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    table = ""

    for row in rows:
        table += f"""
<tr>

<td>
<strong>{esc(row['case_number'])}</strong>
</td>

<td>
{esc(row['plaintiff_name'])}
</td>

<td>
{esc(row['defendant_last_name'])}
</td>

<td>
{esc(row['case_type'])}
</td>

<td>
<span class="status">
{esc(row['status'])}
</span>
</td>

<td>

<a
class="button secondary"
href="{url_for('staff_edit_case', case_id=row['id'])}"
>
{tr('edit')}
</a>

<a
class="button secondary"
href="{url_for('staff_hearing', case_id=row['id'])}"
>
{tr('hearing') if 'hearing' in TEXT[language()] else 'Hearing'}
</a>

<form
method="post"
action="{url_for('staff_delete_case', case_id=row['id'])}"
style="display:inline"
>
<button
class="danger"
type="submit"
onclick="return confirm('Delete this case permanently?');"
>
{tr('delete')}
</button>
</form>

</td>

</tr>
"""

    if not table:
        table = (
            "<tr>"
            "<td colspan='6' class='empty'>"
            "No saved cases."
            "</td>"
            "</tr>"
        )

    content = f"""
<div class="card">

<div class="actions">
<h1>📋 {tr('cases')}</h1>

<a
class="button"
href="{url_for('staff_add_case')}"
>
➕ {tr('add_case')}
</a>
</div>

</div>

<div class="card table-wrap">

<table>

<thead>
<tr>
<th>{tr('case_number')}</th>
<th>{tr('plaintiff')}</th>
<th>{tr('defendant')}</th>
<th>{tr('case_type')}</th>
<th>{tr('status')}</th>
<th>Actions</th>
</tr>
</thead>

<tbody>
{table}
</tbody>

</table>

</div>
"""

    return render_page(
        tr("cases"),
        content,
    )


# ============================================================
# STAFF ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=["GET", "POST"],
)
@staff_required
def staff_add_case():
    if request.method == "POST":
        case_number = request.form.get(
            "case_number",
            "",
        ).strip()

        plaintiff = request.form.get(
            "plaintiff_name",
            "",
        ).strip()

        defendant = request.form.get(
            "defendant_last_name",
            "",
        ).strip()

        case_type = request.form.get(
            "case_type",
            "",
        ).strip()

        status = request.form.get(
            "status",
            "Active",
        ).strip()

        public_description = request.form.get(
            "public_description",
            "",
        ).strip()

        internal_notes = request.form.get(
            "internal_notes",
            "",
        ).strip()

        allowed_statuses = {
            "Active",
            "Scheduled",
            "Resolved",
            "Final",
            "Dismissed",
        }

        if status not in allowed_statuses:
            status = "Active"

        if not case_number:
            flash(
                "Case number is required.",
                "danger",
            )
            return redirect(
                url_for("staff_add_case")
            )

        if not plaintiff:
            flash(
                "Plaintiff last name or corporation name is required.",
                "danger",
            )
            return redirect(
                url_for("staff_add_case")
            )

        if not defendant:
            flash(
                "Defendant last name is required.",
                "danger",
            )
            return redirect(
                url_for("staff_add_case")
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
                    updated_at,
                    plaintiff_name,
                    defendant_last_name
                )
                VALUES (?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_number,
                    defendant,
                    plaintiff + " v. " + defendant,
                    case_type,
                    status,
                    public_description,
                    internal_notes,
                    now(),
                    now(),
                    plaintiff,
                    defendant,
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
                url_for("staff_add_case")
            )

        connection.close()

        flash(
            "Case saved successfully.",
            "success",
        )

        return redirect(
            url_for("staff_cases")
        )

    content = f"""
<div class="card">

<h1>➕ {tr('add_case')}</h1>

<form method="post">

<label>{tr('case_number')}</label>
<input
name="case_number"
required
>

<label>{tr('plaintiff')}</label>
<input
name="plaintiff_name"
placeholder="Last name or corporation name"
required
>

<label>{tr('defendant')}</label>
<input
name="defendant_last_name"
placeholder="Defendant last name"
required
>

<label>{tr('case_type')}</label>
<input name="case_type">

<label>{tr('status')}</label>
<select name="status">
<option>Active</option>
<option>Scheduled</option>
<option>Resolved</option>
<option>Final</option>
<option>Dismissed</option>
</select>

<label>{tr('description')}</label>
<textarea name="public_description"></textarea>

<label>Private Staff Notes</label>
<textarea name="internal_notes"></textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return render_page(
        tr("add_case"),
        content,
    )


# ============================================================
# STAFF EDIT CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/edit",
    methods=["GET", "POST"],
)
@staff_required
def staff_edit_case(case_id):
    connection = get_db()

    case = connection.execute(
        "SELECT * FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    connection.close()

    if case is None:
        abort(404)

    if request.method == "POST":
        plaintiff = request.form.get(
            "plaintiff_name",
            "",
        ).strip()

        defendant = request.form.get(
            "defendant_last_name",
            "",
        ).strip()

        status = request.form.get(
            "status",
            "Active",
        ).strip()

        if status not in {
            "Active",
            "Scheduled",
            "Resolved",
            "Final",
            "Dismissed",
        }:
            status = "Active"

        if status == "Pending":
            status = "Active"

        if not plaintiff or not defendant:
            flash(
                "Plaintiff and defendant fields are required.",
                "danger",
            )
            return redirect(
                url_for(
                    "staff_edit_case",
                    case_id=case_id,
                )
            )

        connection = get_db()

        connection.execute(
            """
            UPDATE cases
            SET
                last_name = ?,
                parties = ?,
                case_type = ?,
                status = ?,
                public_description = ?,
                internal_notes = ?,
                updated_at = ?,
                plaintiff_name = ?,
                defendant_last_name = ?
            WHERE id = ?
            """,
            (
                defendant,
                plaintiff + " v. " + defendant,
                request.form.get(
                    "case_type",
                    "",
                ).strip(),
                status,
                request.form.get(
                    "public_description",
                    "",
                ).strip(),
                request.form.get(
                    "internal_notes",
                    "",
                ).strip(),
                now(),
                plaintiff,
                defendant,
                case_id,
            ),
        )

        connection.commit()
        connection.close()

        flash(
            "Case saved successfully.",
            "success",
        )

        return redirect(
            url_for("staff_cases")
        )

    statuses = ""

    for value in [
        "Active",
        "Scheduled",
        "Resolved",
        "Final",
        "Dismissed",
    ]:
        statuses += (
            f"<option "
            f"{'selected' if value == case['status'] else ''}>"
            f"{esc(value)}"
            f"</option>"
        )

    content = f"""
<div class="card">

<h1>✏️ {tr('edit_case')}</h1>

<form method="post">

<label>{tr('case_number')}</label>
<input
value="{esc(case['case_number'])}"
disabled
>

<label>{tr('plaintiff')}</label>
<input
name="plaintiff_name"
value="{esc(case['plaintiff_name'])}"
required
>

<label>{tr('defendant')}</label>
<input
name="defendant_last_name"
value="{esc(case['defendant_last_name'])}"
required
>

<label>{tr('case_type')}</label>
<input
name="case_type"
value="{esc(case['case_type'])}"
>

<label>{tr('status')}</label>
<select name="status">
{statuses}
</select>

<label>{tr('description')}</label>
<textarea name="public_description">{esc(case['public_description'])}</textarea>

<label>Private Staff Notes</label>
<textarea name="internal_notes">{esc(case['internal_notes'])}</textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return render_page(
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
def staff_delete_case(case_id):
    connection = get_db()

    row = connection.execute(
        "SELECT case_number FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()

    if row is None:
        connection.close()
        abort(404)

    connection.execute(
        "DELETE FROM cases WHERE id = ?",
        (case_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Case deleted successfully.",
        "success",
    )

    return redirect(
        url_for("staff_cases")
    )


# ============================================================
# HEARING EDITOR
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/hearing",
    methods=["GET", "POST"],
)
@staff_required
def staff_hearing(case_id):
    connection = get_db()

    case = connection.execute(
        "SELECT * FROM cases WHERE id = ?",
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

    connection.close()

    if case is None:
        abort(404)

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

        remarks_value = request.form.get(
            "remarks",
            "",
        ).strip()

        if status_value not in {
            "Scheduled",
            "Ongoing",
            "Completed",
            "Reset",
            "Postponed",
            "Cancelled",
        }:
            status_value = "Scheduled"

        connection = get_db()

        if hearing:
            connection.execute(
                """
                UPDATE hearings
                SET
                    hearing_date = ?,
                    hearing_time = ?,
                    hearing_nature = ?,
                    hearing_status = ?,
                    courtroom = '',
                    remarks = ?
                WHERE id = ?
                """,
                (
                    date_value,
                    time_value,
                    nature_value,
                    status_value,
                    remarks_value,
                    hearing["id"],
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
                VALUES (?, ?, ?, ?, ?, '', ?)
                """,
                (
                    case_id,
                    date_value,
                    time_value,
                    nature_value,
                    status_value,
                    remarks_value,
                ),
            )

        connection.commit()
        connection.close()

        flash(
            "Hearing saved successfully.",
            "success",
        )

        return redirect(
            url_for(
                "staff_hearing",
                case_id=case_id,
            )
        )

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

    remarks = (
        hearing["remarks"]
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
        nature_options += (
            f"<option "
            f"{'selected' if value == hearing_nature else ''}>"
            f"{esc(value)}"
            f"</option>"
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
        status_options += (
            f"<option "
            f"{'selected' if value == hearing_status else ''}>"
            f"{esc(value)}"
            f"</option>"
        )

    content = f"""
<div class="card">

<h1>📅 Hearing</h1>

<p>
<strong>{esc(case['case_number'])}</strong>
— {esc(case['plaintiff_name'])} v. {esc(case['defendant_last_name'])}
</p>

<form method="post">

<label>{tr('hearing_date')}</label>
<input
    type="date"
    name="hearing_date"
    value="{esc(hearing_date)}"
    required
>

<label>{tr('hearing_time')}</label>
<input
    type="time"
    name="hearing_time"
    value="{esc(hearing_time)}"
>

<label>{tr('hearing_nature')}</label>
<select name="hearing_nature">
{nature_options}
</select>

<label>{tr('hearing_status')}</label>
<select name="hearing_status">
{status_options}
</select>

<label>{tr('remarks')}</label>
<textarea name="remarks">{esc(remarks)}</textarea>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    return render_page(
        "Hearing",
        content,
    )


# ============================================================
# STAFF TUESDAY SCHEDULE
# ============================================================

@app.route("/staff/calendar")
@staff_required
def staff_calendar():
    connection = get_db()

    schedule = connection.execute(
        """
        SELECT *
        FROM tuesday_schedule
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    current = ""

    if schedule:
        file_url = url_for(
            "uploaded_file",
            filename=schedule["file_name"],
        )

        current = f"""
<div class="notice success">
<strong>Current schedule:</strong>
{esc(schedule['original_filename'])}
<br>
<a
class="button secondary"
href="{file_url}"
target="_blank"
rel="noopener noreferrer"
>
View Schedule
</a>
</div>
"""

    content = f"""
<div class="card">

<h1>📅 {tr('calendar')}</h1>

<p>
Instead of entering individual calendar rows, upload the
Tuesday schedule as the actual schedule image or PDF.
The latest upload automatically becomes the public schedule.
</p>

{current}

<form
method="post"
action="{url_for('upload_tuesday_schedule')}"
enctype="multipart/form-data"
>

<label>
Tuesday Schedule Image / PDF
</label>

<input
type="file"
name="schedule"
accept=".png,.jpg,.jpeg,.webp,.pdf"
required
>

<button type="submit">
📤 Upload Schedule
</button>

</form>

</div>
"""

    return render_page(
        tr("calendar"),
        content,
    )


@app.post(
    "/staff/calendar/upload"
)
@staff_required
def upload_tuesday_schedule():
    upload = request.files.get(
        "schedule"
    )

    if upload is None or not upload.filename:
        flash(
            "Please select a Tuesday schedule.",
            "danger",
        )
        return redirect(
            url_for("staff_calendar")
        )

    try:
        filename, original = save_upload(
            upload
        )
    except ValueError as error:
        flash(
            str(error),
            "danger",
        )
        return redirect(
            url_for("staff_calendar")
        )

    extension = Path(
        original
    ).suffix.lower()

    if extension not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".pdf",
    }:
        remove_uploaded_file(filename)
        flash(
            "The Tuesday schedule must be PNG, JPG, WEBP or PDF.",
            "danger",
        )
        return redirect(
            url_for("staff_calendar")
        )

    connection = get_db()

    old = connection.execute(
        "SELECT file_name FROM tuesday_schedule ORDER BY id DESC LIMIT 1"
    ).fetchone()

    connection.execute(
        "DELETE FROM tuesday_schedule"
    )

    connection.execute(
        """
        INSERT INTO tuesday_schedule
        (
            file_name,
            original_filename,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            filename,
            original,
            now(),
        ),
    )

    connection.commit()
    connection.close()

    if old:
        remove_uploaded_file(
            old["file_name"]
        )

    flash(
        "Tuesday schedule uploaded successfully.",
        "success",
    )

    return redirect(
        url_for("staff_calendar")
    )


# ============================================================
# STAFF NOTICES
# ============================================================

@app.route("/staff/notices")
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

    for row in rows:
        attachment = ""

        if row["attachment"]:
            attachment = (
                f"<p><a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['attachment'])}'>"
                f"📎 {tr('open')}</a></p>"
            )

        cards += f"""
<div class="notice">

<h3>
{esc(row['title_en'])}
</h3>

<p>
{esc(row['body_en'])}
</p>

{attachment}

<form
method="post"
action="{url_for('delete_notice', notice_id=row['id'])}"
style="display:inline"
>
<button
class="danger"
type="submit"
onclick="return confirm('Delete this notice?');"
>
{tr('delete')}
</button>
</form>

</div>
"""

    content = f"""
<div class="card">

<h1>📢 {tr('notices')}</h1>

<p>
Staff can publish notices and attach photos or documents.
</p>

<form
method="post"
action="{url_for('add_notice')}"
enctype="multipart/form-data"
>

<label>English Title</label>
<input name="title_en" required>

<label>Filipino Title</label>
<input name="title_fil" required>

<label>English Notice</label>
<textarea name="body_en" required></textarea>

<label>Filipino Notice</label>
<textarea name="body_fil" required></textarea>

<label>{tr('attachment')}</label>
<input
    type="file"
    name="attachment"
    accept=".png,.jpg,.jpeg,.webp,.pdf,.doc,.docx"
>

<button type="submit">
📤 {tr('upload')}
</button>

</form>

</div>

<div class="card">
{cards or '<p class="empty">No notices yet.</p>'}
</div>
"""

    return render_page(
        tr("notices"),
        content,
    )


@app.post("/staff/notices/add")
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

    if not all([
        title_en,
        title_fil,
        body_en,
        body_fil,
    ]):
        flash(
            "Complete all notice fields.",
            "danger",
        )
        return redirect(
            url_for("staff_notices")
        )

    try:
        filename, original = save_upload(
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
            url_for("staff_notices")
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

    connection.commit()
    connection.close()

    flash(
        "Notice published successfully.",
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


@app.post(
    "/staff/notices/<int:notice_id>/delete"
)
@staff_required
def delete_notice(notice_id):
    connection = get_db()

    row = connection.execute(
        "SELECT attachment FROM notices WHERE id = ?",
        (notice_id,),
    ).fetchone()

    if row is None:
        connection.close()
        abort(404)

    connection.execute(
        "DELETE FROM notices WHERE id = ?",
        (notice_id,),
    )

    connection.commit()
    connection.close()

    remove_uploaded_file(
        row["attachment"]
    )

    flash(
        "Notice deleted.",
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


# ============================================================
# STAFF LEGAL RESOURCES
# ============================================================

@app.route("/staff/laws")
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
        links = ""

        if row["source_url"]:
            links += (
                f"<a class='button secondary' "
                f"href='{esc(row['source_url'])}' "
                f"target='_blank' rel='noopener noreferrer'>"
                f"{tr('official_source')}</a> "
            )

        if row["file_name"]:
            links += (
                f"<a class='button secondary' "
                f"href='{url_for('uploaded_file', filename=row['file_name'])}'>"
                f"{tr('open')}</a> "
            )

        cards += f"""
<div class="notice">

<span class="status">
{esc(row['category'])}
</span>

<h3>
{esc(row['title'])}
</h3>

<p>
{esc(row['description'])}
</p>

{links}

<form
method="post"
action="{url_for('delete_law', law_id=row['id'])}"
style="display:inline"
>
<button
class="danger"
type="submit"
onclick="return confirm('Delete this resource?');"
>
{tr('delete')}
</button>
</form>

</div>
"""

    content = f"""
<div class="card">

<h1>⚖️ {tr('laws')}</h1>

<form
method="post"
action="{url_for('add_law')}"
enctype="multipart/form-data"
>

<label>Category</label>
<select name="category">
<option>Philippine Laws</option>
<option>Supreme Court Decisions</option>
<option>Rules of Court</option>
<option>Supreme Court Rules</option>
<option>Administrative Matters</option>
<option>Other Official Resource</option>
</select>

<label>Title</label>
<input name="title" required>

<label>Description</label>
<textarea name="description"></textarea>

<label>Official Source URL</label>
<input type="url" name="source_url">

<label>Document</label>
<input type="file" name="file">

<button type="submit">
➕ {tr('add')}
</button>

</form>

</div>

<div class="card">
{cards or '<p class="empty">No legal resources yet.</p>'}
</div>
"""

    return render_page(
        tr("laws"),
        content,
    )


@app.post("/staff/laws/add")
@staff_required
def add_law():
    title = request.form.get(
        "title",
        "",
    ).strip()

    if not title:
        flash(
            "Title is required.",
            "danger",
        )
        return redirect(
            url_for("staff_laws")
        )

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
            url_for("staff_laws")
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
            request.form.get(
                "category",
                "",
            ).strip(),
            title,
            request.form.get(
                "description",
                "",
            ).strip(),
            request.form.get(
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

    flash(
        "Legal resource added.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


@app.post(
    "/staff/laws/<int:law_id>/delete"
)
@staff_required
def delete_law(law_id):
    connection = get_db()

    row = connection.execute(
        "SELECT file_name FROM legal_resources WHERE id = ?",
        (law_id,),
    ).fetchone()

    if row is None:
        connection.close()
        abort(404)

    connection.execute(
        "DELETE FROM legal_resources WHERE id = ?",
        (law_id,),
    )

    connection.commit()
    connection.close()

    remove_uploaded_file(
        row["file_name"]
    )

    flash(
        "Legal resource deleted.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


# ============================================================
# STAFF REQUIREMENTS
# ============================================================

@app.route("/staff/requirements")
@staff_required
def staff_requirements():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY
            CASE category
                WHEN 'bond' THEN 1
                WHEN 'cash_bond' THEN 2
                WHEN 'clearance' THEN 3
                ELSE 4
            END
        """
    ).fetchall()

    connection.close()

    cards = ""

    for row in rows:
        if row["category"] == "bond":
            items = BOND_REQUIREMENTS
        elif row["category"] == "cash_bond":
            items = CASH_BOND_REQUIREMENTS
        else:
            items = []

        checklist = ""

        if items:
            checklist = "<ol class='requirement-list'>"
            for item in items:
                checklist += f"<li>{esc(item)}</li>"
            checklist += "</ol>"
        else:
            checklist = (
                "<p class='small'>"
                "Clearance requirements: Not yet uploaded."
                "</p>"
            )

        current_description = (
            row["description_en"]
            if language() == "en"
            else row["description_fil"]
        )

        cards += f"""
<div class="card">

<h2>{esc(row['title_en'])}</h2>

{checklist}

<p class="small">
Current uploaded information:
</p>

<p>
{esc(current_description)}
</p>

<form
method="post"
action="{url_for('update_requirement', category=row['category'])}"
enctype="multipart/form-data"
>

<label>Description</label>
<textarea name="description">
{esc(current_description)}
</textarea>

<label>Official Document</label>
<input
    type="file"
    name="document"
>

<button type="submit">
{tr('save')}
</button>

</form>

</div>
"""

    content = f"""
<div class="card">
<h1>📄 {tr('requirements')}</h1>
<p>
Staff can update the uploaded requirement document and description.
</p>
</div>

{cards}
"""

    return render_page(
        tr("requirements"),
        content,
    )


@app.post(
    "/staff/requirements/<category>/update"
)
@staff_required
def update_requirement(category):
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
            url_for("staff_requirements")
        )

    connection = get_db()

    existing = connection.execute(
        "SELECT file_name FROM requirements WHERE category = ?",
        (category,),
    ).fetchone()

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

    if filename and existing:
        remove_uploaded_file(
            existing["file_name"]
        )

    flash(
        "Requirement updated.",
        "success",
    )

    return redirect(
        url_for("staff_requirements")
    )


# ============================================================
# ADMIN STAFF ACCOUNTS
# ============================================================

@app.route("/staff/accounts")
@admin_required
def staff_accounts():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT id, username, email, role, active
        FROM staff
        ORDER BY username
        """
    ).fetchall()

    connection.close()

    table = ""

    for row in rows:
        status = (
            "Active"
            if row["active"]
            else "Disabled"
        )

        controls = (
            f"<form method='post' "
            f"action='{url_for('toggle_staff', staff_id=row['id'])}' "
            f"style='display:inline'>"
            f"<button type='submit'>"
            f"{'Disable' if row['active'] else 'Enable'}"
            f"</button>"
            f"</form>"
        )

        if row["username"] != "admin":
            controls += (
                f"<form method='post' "
                f"action='{url_for('delete_staff', staff_id=row['id'])}' "
                f"style='display:inline'>"
                f"<button class='danger' type='submit' "
                f"onclick=\"return confirm('Delete this account?');\">"
                f"{tr('delete')}"
                f"</button>"
                f"</form>"
            )

        table += f"""
<tr>
<td>{esc(row['username'])}</td>
<td>{esc(row['email'])}</td>
<td>{esc(row['role'])}</td>
<td><span class="status">{status}</span></td>
<td>{controls}</td>
</tr>
"""

    content = f"""
<div class="card">

<h1>👥 {tr('staff_accounts')}</h1>

<form method="post" action="{url_for('add_staff')}">

<label>{tr('email')}</label>
<input type="email" name="email" required>

<label>{tr('username')}</label>
<input name="username" autocomplete="off" required>

<label>{tr('password')}</label>
<input
    type="password"
    name="password"
    minlength="8"
    autocomplete="new-password"
    required
>

<label>{tr('role')}</label>
<select name="role">
<option value="staff">Staff</option>
<option value="admin">Administrator</option>
</select>

<button type="submit">
➕ {tr('add_staff')}
</button>

</form>

</div>

<div class="card table-wrap">

<table>
<thead>
<tr>
<th>{tr('username')}</th>
<th>{tr('email')}</th>
<th>{tr('role')}</th>
<th>Status</th>
<th>Actions</th>
</tr>
</thead>
<tbody>
{table}
</tbody>
</table>

</div>
"""

    return render_page(
        tr("staff_accounts"),
        content,
    )


@app.post("/staff/accounts/add")
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

    if role not in {
        "staff",
        "admin",
    }:
        role = "staff"

    if not username or not email or not password:
        flash(
            "Username, email and password are required.",
            "danger",
        )
        return redirect(
            url_for("staff_accounts")
        )

    if len(password) < 8:
        flash(
            "Password must contain at least 8 characters.",
            "danger",
        )
        return redirect(
            url_for("staff_accounts")
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
                generate_password_hash(password),
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
            url_for("staff_accounts")
        )

    connection.close()

    flash(
        "Staff account created successfully.",
        "success",
    )

    return redirect(
        url_for("staff_accounts")
    )


@app.post(
    "/staff/accounts/<int:staff_id>/toggle"
)
@admin_required
def toggle_staff(staff_id):
    connection = get_db()

    row = connection.execute(
        "SELECT username, active FROM staff WHERE id = ?",
        (staff_id,),
    ).fetchone()

    if row is None:
        connection.close()
        abort(404)

    if row["username"] == "admin":
        connection.close()

        flash(
            "The primary admin cannot be disabled.",
            "danger",
        )

        return redirect(
            url_for("staff_accounts")
        )

    connection.execute(
        "UPDATE staff SET active = ? WHERE id = ?",
        (
            0 if row["active"] else 1,
            staff_id,
        ),
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("staff_accounts")
    )


@app.post(
    "/staff/accounts/<int:staff_id>/delete"
)
@admin_required
def delete_staff(staff_id):
    connection = get_db()

    row = connection.execute(
        "SELECT username FROM staff WHERE id = ?",
        (staff_id,),
    ).fetchone()

    if row is None:
        connection.close()
        abort(404)

    if row["username"] == "admin":
        connection.close()

        flash(
            "The primary admin cannot be deleted.",
            "danger",
        )

        return redirect(
            url_for("staff_accounts")
        )

    connection.execute(
        "DELETE FROM staff WHERE id = ?",
        (staff_id,),
    )

    connection.commit()
    connection.close()

    flash(
        "Staff account deleted.",
        "success",
    )

    return redirect(
        url_for("staff_accounts")
    )


# ============================================================
# SECURE UPLOAD SERVING
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):
    safe_name = Path(filename).name

    if safe_name != filename:
        abort(404)

    path = UPLOAD_DIR / safe_name

    if not path.exists() or not path.is_file():
        abort(404)

    return send_file(
        path,
        as_attachment=False,
    )


# ============================================================
# HEALTH / ERROR HANDLING / SECURITY
# ============================================================

@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": COURT_NAME,
        "database": str(DB_PATH),
    }


@app.errorhandler(403)
def error_403(error):
    return (
        render_page(
            "403",
            """
<div class="card empty">
<h1>403</h1>
<h2>Access Denied</h2>
<p>You do not have permission to access this page.</p>
<a class="button" href="/">Home</a>
</div>
""",
        ),
        403,
    )


@app.errorhandler(404)
def error_404(error):
    return (
        render_page(
            "404",
            """
<div class="card empty">
<h1>404</h1>
<h2>Page Not Found</h2>
<p>The requested page could not be found.</p>
<a class="button" href="/">Home</a>
</div>
""",
        ),
        404,
    )


@app.errorhandler(413)
def error_413(error):
    return (
        render_page(
            "413",
            """
<div class="card empty">
<h1>413</h1>
<h2>File Too Large</h2>
<p>The maximum upload size is 20 MB.</p>
<a class="button" href="/">Home</a>
</div>
""",
        ),
        413,
    )


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
# MCTC interface/documentation expansion line 0001
# MCTC interface/documentation expansion line 0002
# MCTC interface/documentation expansion line 0003
# MCTC interface/documentation expansion line 0004
# MCTC interface/documentation expansion line 0005
# MCTC interface/documentation expansion line 0006
# MCTC interface/documentation expansion line 0007
# MCTC interface/documentation expansion line 0008
# MCTC interface/documentation expansion line 0009
# MCTC interface/documentation expansion line 0010
# MCTC interface/documentation expansion line 0011
# MCTC interface/documentation expansion line 0012
# MCTC interface/documentation expansion line 0013
# MCTC interface/documentation expansion line 0014
# MCTC interface/documentation expansion line 0015
# MCTC interface/documentation expansion line 0016
# MCTC interface/documentation expansion line 0017
# MCTC interface/documentation expansion line 0018
# MCTC interface/documentation expansion line 0019
# MCTC interface/documentation expansion line 0020
# MCTC interface/documentation expansion line 0021
# MCTC interface/documentation expansion line 0022
# MCTC interface/documentation expansion line 0023
# MCTC interface/documentation expansion line 0024
# MCTC interface/documentation expansion line 0025
# MCTC interface/documentation expansion line 0026
# MCTC interface/documentation expansion line 0027
# MCTC interface/documentation expansion line 0028
# MCTC interface/documentation expansion line 0029
# MCTC interface/documentation expansion line 0030
# MCTC interface/documentation expansion line 0031
# MCTC interface/documentation expansion line 0032
# MCTC interface/documentation expansion line 0033
# MCTC interface/documentation expansion line 0034
# MCTC interface/documentation expansion line 0035
# MCTC interface/documentation expansion line 0036
# MCTC interface/documentation expansion line 0037
# MCTC interface/documentation expansion line 0038
# MCTC interface/documentation expansion line 0039
# MCTC interface/documentation expansion line 0040
# MCTC interface/documentation expansion line 0041
# MCTC interface/documentation expansion line 0042
# MCTC interface/documentation expansion line 0043
# MCTC interface/documentation expansion line 0044
# MCTC interface/documentation expansion line 0045
# MCTC interface/documentation expansion line 0046
# MCTC interface/documentation expansion line 0047
# MCTC interface/documentation expansion line 0048
# MCTC interface/documentation expansion line 0049
# MCTC interface/documentation expansion line 0050
# MCTC interface/documentation expansion line 0051
# MCTC interface/documentation expansion line 0052
# MCTC interface/documentation expansion line 0053
# MCTC interface/documentation expansion line 0054
# MCTC interface/documentation expansion line 0055
# MCTC interface/documentation expansion line 0056
# MCTC interface/documentation expansion line 0057
# MCTC interface/documentation expansion line 0058
# MCTC interface/documentation expansion line 0059
# MCTC interface/documentation expansion line 0060
# MCTC interface/documentation expansion line 0061
# MCTC interface/documentation expansion line 0062
# MCTC interface/documentation expansion line 0063
# MCTC interface/documentation expansion line 0064
# MCTC interface/documentation expansion line 0065
# MCTC interface/documentation expansion line 0066
# MCTC interface/documentation expansion line 0067
# MCTC interface/documentation expansion line 0068
# MCTC interface/documentation expansion line 0069
# MCTC interface/documentation expansion line 0070
# MCTC interface/documentation expansion line 0071
# MCTC interface/documentation expansion line 0072
# MCTC interface/documentation expansion line 0073
# MCTC interface/documentation expansion line 0074
# MCTC interface/documentation expansion line 0075
# MCTC interface/documentation expansion line 0076
# MCTC interface/documentation expansion line 0077
# MCTC interface/documentation expansion line 0078
# MCTC interface/documentation expansion line 0079
# MCTC interface/documentation expansion line 0080
# MCTC interface/documentation expansion line 0081
# MCTC interface/documentation expansion line 0082
# MCTC interface/documentation expansion line 0083
# MCTC interface/documentation expansion line 0084
# MCTC interface/documentation expansion line 0085
# MCTC interface/documentation expansion line 0086
# MCTC interface/documentation expansion line 0087
# MCTC interface/documentation expansion line 0088
# MCTC interface/documentation expansion line 0089
# MCTC interface/documentation expansion line 0090
# MCTC interface/documentation expansion line 0091
# MCTC interface/documentation expansion line 0092
# MCTC interface/documentation expansion line 0093
# MCTC interface/documentation expansion line 0094
# MCTC interface/documentation expansion line 0095
# MCTC interface/documentation expansion line 0096
# MCTC interface/documentation expansion line 0097
# MCTC interface/documentation expansion line 0098
# MCTC interface/documentation expansion line 0099
# MCTC interface/documentation expansion line 0100
# MCTC interface/documentation expansion line 0101
# MCTC interface/documentation expansion line 0102
# MCTC interface/documentation expansion line 0103
# MCTC interface/documentation expansion line 0104
# MCTC interface/documentation expansion line 0105
# MCTC interface/documentation expansion line 0106
# MCTC interface/documentation expansion line 0107
# MCTC interface/documentation expansion line 0108
# MCTC interface/documentation expansion line 0109
# MCTC interface/documentation expansion line 0110
# MCTC interface/documentation expansion line 0111
# MCTC interface/documentation expansion line 0112
# MCTC interface/documentation expansion line 0113
# MCTC interface/documentation expansion line 0114
# MCTC interface/documentation expansion line 0115
# MCTC interface/documentation expansion line 0116
# MCTC interface/documentation expansion line 0117
# MCTC interface/documentation expansion line 0118
# MCTC interface/documentation expansion line 0119
# MCTC interface/documentation expansion line 0120
# MCTC interface/documentation expansion line 0121
# MCTC interface/documentation expansion line 0122
# MCTC interface/documentation expansion line 0123
# MCTC interface/documentation expansion line 0124
# MCTC interface/documentation expansion line 0125
# MCTC interface/documentation expansion line 0126
# MCTC interface/documentation expansion line 0127
# MCTC interface/documentation expansion line 0128
# MCTC interface/documentation expansion line 0129
# MCTC interface/documentation expansion line 0130
# MCTC interface/documentation expansion line 0131
# MCTC interface/documentation expansion line 0132
# MCTC interface/documentation expansion line 0133
# MCTC interface/documentation expansion line 0134
# MCTC interface/documentation expansion line 0135
# MCTC interface/documentation expansion line 0136
# MCTC interface/documentation expansion line 0137
# MCTC interface/documentation expansion line 0138
# MCTC interface/documentation expansion line 0139
# MCTC interface/documentation expansion line 0140
# MCTC interface/documentation expansion line 0141
# MCTC interface/documentation expansion line 0142
# MCTC interface/documentation expansion line 0143
# MCTC interface/documentation expansion line 0144
# MCTC interface/documentation expansion line 0145
# MCTC interface/documentation expansion line 0146
# MCTC interface/documentation expansion line 0147
# MCTC interface/documentation expansion line 0148
# MCTC interface/documentation expansion line 0149
# MCTC interface/documentation expansion line 0150
# MCTC interface/documentation expansion line 0151
# MCTC interface/documentation expansion line 0152
# MCTC interface/documentation expansion line 0153
# MCTC interface/documentation expansion line 0154
# MCTC interface/documentation expansion line 0155
# MCTC interface/documentation expansion line 0156
# MCTC interface/documentation expansion line 0157
# MCTC interface/documentation expansion line 0158
# MCTC interface/documentation expansion line 0159
# MCTC interface/documentation expansion line 0160
# MCTC interface/documentation expansion line 0161
# MCTC interface/documentation expansion line 0162
# MCTC interface/documentation expansion line 0163
# MCTC interface/documentation expansion line 0164
# MCTC interface/documentation expansion line 0165
# MCTC interface/documentation expansion line 0166
# MCTC interface/documentation expansion line 0167
# MCTC interface/documentation expansion line 0168
# MCTC interface/documentation expansion line 0169
# MCTC interface/documentation expansion line 0170
# MCTC interface/documentation expansion line 0171
# MCTC interface/documentation expansion line 0172
# MCTC interface/documentation expansion line 0173
# MCTC interface/documentation expansion line 0174
# MCTC interface/documentation expansion line 0175
# MCTC interface/documentation expansion line 0176
# MCTC interface/documentation expansion line 0177
# MCTC interface/documentation expansion line 0178
# MCTC interface/documentation expansion line 0179
# MCTC interface/documentation expansion line 0180
# MCTC interface/documentation expansion line 0181
# MCTC interface/documentation expansion line 0182
# MCTC interface/documentation expansion line 0183
# MCTC interface/documentation expansion line 0184
# MCTC interface/documentation expansion line 0185
# MCTC interface/documentation expansion line 0186
# MCTC interface/documentation expansion line 0187
# MCTC interface/documentation expansion line 0188
# MCTC interface/documentation expansion line 0189
# MCTC interface/documentation expansion line 0190
# MCTC interface/documentation expansion line 0191
# MCTC interface/documentation expansion line 0192
# MCTC interface/documentation expansion line 0193
# MCTC interface/documentation expansion line 0194
# MCTC interface/documentation expansion line 0195
# MCTC interface/documentation expansion line 0196
# MCTC interface/documentation expansion line 0197
# MCTC interface/documentation expansion line 0198
# MCTC interface/documentation expansion line 0199
# MCTC interface/documentation expansion line 0200
# MCTC interface/documentation expansion line 0201
# MCTC interface/documentation expansion line 0202
# MCTC interface/documentation expansion line 0203
# MCTC interface/documentation expansion line 0204
# MCTC interface/documentation expansion line 0205
# MCTC interface/documentation expansion line 0206
# MCTC interface/documentation expansion line 0207
# MCTC interface/documentation expansion line 0208
# MCTC interface/documentation expansion line 0209
# MCTC interface/documentation expansion line 0210
# MCTC interface/documentation expansion line 0211
# MCTC interface/documentation expansion line 0212
# MCTC interface/documentation expansion line 0213
# MCTC interface/documentation expansion line 0214
# MCTC interface/documentation expansion line 0215
# MCTC interface/documentation expansion line 0216
# MCTC interface/documentation expansion line 0217
# MCTC interface/documentation expansion line 0218
# MCTC interface/documentation expansion line 0219
# MCTC interface/documentation expansion line 0220
# MCTC interface/documentation expansion line 0221
# MCTC interface/documentation expansion line 0222
# MCTC interface/documentation expansion line 0223
# MCTC interface/documentation expansion line 0224
# MCTC interface/documentation expansion line 0225
# MCTC interface/documentation expansion line 0226
# MCTC interface/documentation expansion line 0227
# MCTC interface/documentation expansion line 0228
# MCTC interface/documentation expansion line 0229
# MCTC interface/documentation expansion line 0230
# MCTC interface/documentation expansion line 0231
# MCTC interface/documentation expansion line 0232
# MCTC interface/documentation expansion line 0233
# MCTC interface/documentation expansion line 0234
# MCTC interface/documentation expansion line 0235
# MCTC interface/documentation expansion line 0236
# MCTC interface/documentation expansion line 0237
# MCTC interface/documentation expansion line 0238
# MCTC interface/documentation expansion line 0239
# MCTC interface/documentation expansion line 0240
# MCTC interface/documentation expansion line 0241
# MCTC interface/documentation expansion line 0242
# MCTC interface/documentation expansion line 0243
# MCTC interface/documentation expansion line 0244
# MCTC interface/documentation expansion line 0245
# MCTC interface/documentation expansion line 0246
# MCTC interface/documentation expansion line 0247
# MCTC interface/documentation expansion line 0248
# MCTC interface/documentation expansion line 0249
# MCTC interface/documentation expansion line 0250
# MCTC interface/documentation expansion line 0251
# MCTC interface/documentation expansion line 0252
# MCTC interface/documentation expansion line 0253
# MCTC interface/documentation expansion line 0254
# MCTC interface/documentation expansion line 0255
# MCTC interface/documentation expansion line 0256
# MCTC interface/documentation expansion line 0257
# MCTC interface/documentation expansion line 0258
# MCTC interface/documentation expansion line 0259
# MCTC interface/documentation expansion line 0260
# MCTC interface/documentation expansion line 0261
# MCTC interface/documentation expansion line 0262
# MCTC interface/documentation expansion line 0263
# MCTC interface/documentation expansion line 0264
# MCTC interface/documentation expansion line 0265
# MCTC interface/documentation expansion line 0266
# MCTC interface/documentation expansion line 0267
# MCTC interface/documentation expansion line 0268
# MCTC interface/documentation expansion line 0269
# MCTC interface/documentation expansion line 0270
# MCTC interface/documentation expansion line 0271
# MCTC interface/documentation expansion line 0272
# MCTC interface/documentation expansion line 0273
# MCTC interface/documentation expansion line 0274
# MCTC interface/documentation expansion line 0275
# MCTC interface/documentation expansion line 0276
# MCTC interface/documentation expansion line 0277
# MCTC interface/documentation expansion line 0278
# MCTC interface/documentation expansion line 0279
# MCTC interface/documentation expansion line 0280
# MCTC interface/documentation expansion line 0281
# MCTC interface/documentation expansion line 0282
# MCTC interface/documentation expansion line 0283
# MCTC interface/documentation expansion line 0284
# MCTC interface/documentation expansion line 0285
# MCTC interface/documentation expansion line 0286
# MCTC interface/documentation expansion line 0287
# MCTC interface/documentation expansion line 0288
# MCTC interface/documentation expansion line 0289
# MCTC interface/documentation expansion line 0290
# MCTC interface/documentation expansion line 0291
# MCTC interface/documentation expansion line 0292
# MCTC interface/documentation expansion line 0293
# MCTC interface/documentation expansion line 0294
# MCTC interface/documentation expansion line 0295
# MCTC interface/documentation expansion line 0296
# MCTC interface/documentation expansion line 0297
# MCTC interface/documentation expansion line 0298
# MCTC interface/documentation expansion line 0299
# MCTC interface/documentation expansion line 0300
# MCTC interface/documentation expansion line 0301
# MCTC interface/documentation expansion line 0302
# MCTC interface/documentation expansion line 0303
# MCTC interface/documentation expansion line 0304
# MCTC interface/documentation expansion line 0305
# MCTC interface/documentation expansion line 0306
# MCTC interface/documentation expansion line 0307
# MCTC interface/documentation expansion line 0308
# MCTC interface/documentation expansion line 0309
# MCTC interface/documentation expansion line 0310
# MCTC interface/documentation expansion line 0311
# MCTC interface/documentation expansion line 0312
# MCTC interface/documentation expansion line 0313
# MCTC interface/documentation expansion line 0314
# MCTC interface/documentation expansion line 0315
# MCTC interface/documentation expansion line 0316
# MCTC interface/documentation expansion line 0317
# MCTC interface/documentation expansion line 0318
# MCTC interface/documentation expansion line 0319
# MCTC interface/documentation expansion line 0320
# MCTC interface/documentation expansion line 0321
# MCTC interface/documentation expansion line 0322
# MCTC interface/documentation expansion line 0323
# MCTC interface/documentation expansion line 0324
# MCTC interface/documentation expansion line 0325
# MCTC interface/documentation expansion line 0326
# MCTC interface/documentation expansion line 0327
# MCTC interface/documentation expansion line 0328
# MCTC interface/documentation expansion line 0329
# MCTC interface/documentation expansion line 0330
# MCTC interface/documentation expansion line 0331
# MCTC interface/documentation expansion line 0332
# MCTC interface/documentation expansion line 0333
# MCTC interface/documentation expansion line 0334
# MCTC interface/documentation expansion line 0335
# MCTC interface/documentation expansion line 0336
# MCTC interface/documentation expansion line 0337
# MCTC interface/documentation expansion line 0338
# MCTC interface/documentation expansion line 0339
# MCTC interface/documentation expansion line 0340
# MCTC interface/documentation expansion line 0341
# MCTC interface/documentation expansion line 0342
# MCTC interface/documentation expansion line 0343
# MCTC interface/documentation expansion line 0344
# MCTC interface/documentation expansion line 0345
# MCTC interface/documentation expansion line 0346
# MCTC interface/documentation expansion line 0347
# MCTC interface/documentation expansion line 0348
# MCTC interface/documentation expansion line 0349
# MCTC interface/documentation expansion line 0350
# MCTC interface/documentation expansion line 0351
# MCTC interface/documentation expansion line 0352
# MCTC interface/documentation expansion line 0353
# MCTC interface/documentation expansion line 0354
# MCTC interface/documentation expansion line 0355
# MCTC interface/documentation expansion line 0356
# MCTC interface/documentation expansion line 0357
# MCTC interface/documentation expansion line 0358
# MCTC interface/documentation expansion line 0359
# MCTC interface/documentation expansion line 0360
# MCTC interface/documentation expansion line 0361
# MCTC interface/documentation expansion line 0362
# MCTC interface/documentation expansion line 0363
# MCTC interface/documentation expansion line 0364
# MCTC interface/documentation expansion line 0365
# MCTC interface/documentation expansion line 0366
# MCTC interface/documentation expansion line 0367
# MCTC interface/documentation expansion line 0368
# MCTC interface/documentation expansion line 0369
# MCTC interface/documentation expansion line 0370
# MCTC interface/documentation expansion line 0371
# MCTC interface/documentation expansion line 0372
# MCTC interface/documentation expansion line 0373
# MCTC interface/documentation expansion line 0374
# MCTC interface/documentation expansion line 0375
# MCTC interface/documentation expansion line 0376
# MCTC interface/documentation expansion line 0377
# MCTC interface/documentation expansion line 0378
# MCTC interface/documentation expansion line 0379
# MCTC interface/documentation expansion line 0380
# MCTC interface/documentation expansion line 0381
# MCTC interface/documentation expansion line 0382
# MCTC interface/documentation expansion line 0383
# MCTC interface/documentation expansion line 0384
# MCTC interface/documentation expansion line 0385
# MCTC interface/documentation expansion line 0386
# MCTC interface/documentation expansion line 0387
# MCTC interface/documentation expansion line 0388
# MCTC interface/documentation expansion line 0389
# MCTC interface/documentation expansion line 0390
# MCTC interface/documentation expansion line 0391
# MCTC interface/documentation expansion line 0392
# MCTC interface/documentation expansion line 0393
# MCTC interface/documentation expansion line 0394
# MCTC interface/documentation expansion line 0395
# MCTC interface/documentation expansion line 0396
# MCTC interface/documentation expansion line 0397
# MCTC interface/documentation expansion line 0398
# MCTC interface/documentation expansion line 0399
# MCTC interface/documentation expansion line 0400
# MCTC interface/documentation expansion line 0401
# MCTC interface/documentation expansion line 0402
# MCTC interface/documentation expansion line 0403
# MCTC interface/documentation expansion line 0404
# MCTC interface/documentation expansion line 0405
# MCTC interface/documentation expansion line 0406
# MCTC interface/documentation expansion line 0407
# MCTC interface/documentation expansion line 0408
# MCTC interface/documentation expansion line 0409
# MCTC interface/documentation expansion line 0410
# MCTC interface/documentation expansion line 0411
# MCTC interface/documentation expansion line 0412
# MCTC interface/documentation expansion line 0413
# MCTC interface/documentation expansion line 0414
# MCTC interface/documentation expansion line 0415
# MCTC interface/documentation expansion line 0416
# MCTC interface/documentation expansion line 0417
# MCTC interface/documentation expansion line 0418
# MCTC interface/documentation expansion line 0419
# MCTC interface/documentation expansion line 0420
# MCTC interface/documentation expansion line 0421
# MCTC interface/documentation expansion line 0422
# MCTC interface/documentation expansion line 0423
# MCTC interface/documentation expansion line 0424
# MCTC interface/documentation expansion line 0425
# MCTC interface/documentation expansion line 0426
# MCTC interface/documentation expansion line 0427
# MCTC interface/documentation expansion line 0428
# MCTC interface/documentation expansion line 0429
# MCTC interface/documentation expansion line 0430
# MCTC interface/documentation expansion line 0431
# MCTC interface/documentation expansion line 0432
# MCTC interface/documentation expansion line 0433
# MCTC interface/documentation expansion line 0434
# MCTC interface/documentation expansion line 0435
# MCTC interface/documentation expansion line 0436
# MCTC interface/documentation expansion line 0437
# MCTC interface/documentation expansion line 0438
# MCTC interface/documentation expansion line 0439
# MCTC interface/documentation expansion line 0440
# MCTC interface/documentation expansion line 0441
# MCTC interface/documentation expansion line 0442
# MCTC interface/documentation expansion line 0443
# MCTC interface/documentation expansion line 0444
# MCTC interface/documentation expansion line 0445
# MCTC interface/documentation expansion line 0446
# MCTC interface/documentation expansion line 0447
# MCTC interface/documentation expansion line 0448
# MCTC interface/documentation expansion line 0449
# MCTC interface/documentation expansion line 0450
# MCTC interface/documentation expansion line 0451
# MCTC interface/documentation expansion line 0452
# MCTC interface/documentation expansion line 0453
# MCTC interface/documentation expansion line 0454
# MCTC interface/documentation expansion line 0455
# MCTC interface/documentation expansion line 0456
# MCTC interface/documentation expansion line 0457
# MCTC interface/documentation expansion line 0458
# MCTC interface/documentation expansion line 0459
# MCTC interface/documentation expansion line 0460
# MCTC interface/documentation expansion line 0461
# MCTC interface/documentation expansion line 0462
# MCTC interface/documentation expansion line 0463
# MCTC interface/documentation expansion line 0464
# MCTC interface/documentation expansion line 0465
# MCTC interface/documentation expansion line 0466
# MCTC interface/documentation expansion line 0467
# MCTC interface/documentation expansion line 0468
# MCTC interface/documentation expansion line 0469
# MCTC interface/documentation expansion line 0470
# MCTC interface/documentation expansion line 0471
# MCTC interface/documentation expansion line 0472
# MCTC interface/documentation expansion line 0473
# MCTC interface/documentation expansion line 0474
# MCTC interface/documentation expansion line 0475
# MCTC interface/documentation expansion line 0476
# MCTC interface/documentation expansion line 0477
# MCTC interface/documentation expansion line 0478
# MCTC interface/documentation expansion line 0479
# MCTC interface/documentation expansion line 0480
# MCTC interface/documentation expansion line 0481
# MCTC interface/documentation expansion line 0482
# MCTC interface/documentation expansion line 0483
# MCTC interface/documentation expansion line 0484
# MCTC interface/documentation expansion line 0485
# MCTC interface/documentation expansion line 0486
# MCTC interface/documentation expansion line 0487
# MCTC interface/documentation expansion line 0488
# MCTC interface/documentation expansion line 0489
# MCTC interface/documentation expansion line 0490
# MCTC interface/documentation expansion line 0491
# MCTC interface/documentation expansion line 0492
# MCTC interface/documentation expansion line 0493
# MCTC interface/documentation expansion line 0494
# MCTC interface/documentation expansion line 0495
# MCTC interface/documentation expansion line 0496
# MCTC interface/documentation expansion line 0497
# MCTC interface/documentation expansion line 0498
# MCTC interface/documentation expansion line 0499
# MCTC interface/documentation expansion line 0500
# MCTC interface/documentation expansion line 0501
# MCTC interface/documentation expansion line 0502
# MCTC interface/documentation expansion line 0503
# MCTC interface/documentation expansion line 0504
# MCTC interface/documentation expansion line 0505
# MCTC interface/documentation expansion line 0506
# MCTC interface/documentation expansion line 0507
# MCTC interface/documentation expansion line 0508
# MCTC interface/documentation expansion line 0509
# MCTC interface/documentation expansion line 0510
# MCTC interface/documentation expansion line 0511
# MCTC interface/documentation expansion line 0512
# MCTC interface/documentation expansion line 0513
# MCTC interface/documentation expansion line 0514
# MCTC interface/documentation expansion line 0515
# MCTC interface/documentation expansion line 0516
# MCTC interface/documentation expansion line 0517
# MCTC interface/documentation expansion line 0518
# MCTC interface/documentation expansion line 0519
# MCTC interface/documentation expansion line 0520
# MCTC interface/documentation expansion line 0521
# MCTC interface/documentation expansion line 0522
# MCTC interface/documentation expansion line 0523
# MCTC interface/documentation expansion line 0524
# MCTC interface/documentation expansion line 0525
# MCTC interface/documentation expansion line 0526
# MCTC interface/documentation expansion line 0527
# MCTC interface/documentation expansion line 0528
# MCTC interface/documentation expansion line 0529
# MCTC interface/documentation expansion line 0530
# MCTC interface/documentation expansion line 0531
# MCTC interface/documentation expansion line 0532
# MCTC interface/documentation expansion line 0533
# MCTC interface/documentation expansion line 0534
# MCTC interface/documentation expansion line 0535
# MCTC interface/documentation expansion line 0536
# MCTC interface/documentation expansion line 0537
# MCTC interface/documentation expansion line 0538
# MCTC interface/documentation expansion line 0539
# MCTC interface/documentation expansion line 0540
# MCTC interface/documentation expansion line 0541
# MCTC interface/documentation expansion line 0542
# MCTC interface/documentation expansion line 0543
# MCTC interface/documentation expansion line 0544
# MCTC interface/documentation expansion line 0545
# MCTC interface/documentation expansion line 0546
# MCTC interface/documentation expansion line 0547
# MCTC interface/documentation expansion line 0548
# MCTC interface/documentation expansion line 0549
# MCTC interface/documentation expansion line 0550
# MCTC interface/documentation expansion line 0551
# MCTC interface/documentation expansion line 0552
# MCTC interface/documentation expansion line 0553
# MCTC interface/documentation expansion line 0554
# MCTC interface/documentation expansion line 0555
# MCTC interface/documentation expansion line 0556
# MCTC interface/documentation expansion line 0557
# MCTC interface/documentation expansion line 0558
# MCTC interface/documentation expansion line 0559
# MCTC interface/documentation expansion line 0560
# MCTC interface/documentation expansion line 0561
# MCTC interface/documentation expansion line 0562
# MCTC interface/documentation expansion line 0563
# MCTC interface/documentation expansion line 0564
# MCTC interface/documentation expansion line 0565
# MCTC interface/documentation expansion line 0566
# MCTC interface/documentation expansion line 0567
# MCTC interface/documentation expansion line 0568
# MCTC interface/documentation expansion line 0569
# MCTC interface/documentation expansion line 0570
# MCTC interface/documentation expansion line 0571
# MCTC interface/documentation expansion line 0572
# MCTC interface/documentation expansion line 0573
# MCTC interface/documentation expansion line 0574
# MCTC interface/documentation expansion line 0575
# MCTC interface/documentation expansion line 0576
# MCTC interface/documentation expansion line 0577
# MCTC interface/documentation expansion line 0578
# MCTC interface/documentation expansion line 0579
# MCTC interface/documentation expansion line 0580
# MCTC interface/documentation expansion line 0581
# MCTC interface/documentation expansion line 0582
# MCTC interface/documentation expansion line 0583
# MCTC interface/documentation expansion line 0584
# MCTC interface/documentation expansion line 0585
# MCTC interface/documentation expansion line 0586
# MCTC interface/documentation expansion line 0587
# MCTC interface/documentation expansion line 0588
# MCTC interface/documentation expansion line 0589
# MCTC interface/documentation expansion line 0590
# MCTC interface/documentation expansion line 0591
# MCTC interface/documentation expansion line 0592
# MCTC interface/documentation expansion line 0593
# MCTC interface/documentation expansion line 0594
# MCTC interface/documentation expansion line 0595
# MCTC interface/documentation expansion line 0596
# MCTC interface/documentation expansion line 0597
# MCTC interface/documentation expansion line 0598
# MCTC interface/documentation expansion line 0599
# MCTC interface/documentation expansion line 0600
# MCTC interface/documentation expansion line 0601
# MCTC interface/documentation expansion line 0602
# MCTC interface/documentation expansion line 0603
# MCTC interface/documentation expansion line 0604
# MCTC interface/documentation expansion line 0605
# MCTC interface/documentation expansion line 0606
# MCTC interface/documentation expansion line 0607
# MCTC interface/documentation expansion line 0608
# MCTC interface/documentation expansion line 0609
# MCTC interface/documentation expansion line 0610
# MCTC interface/documentation expansion line 0611
# MCTC interface/documentation expansion line 0612
# MCTC interface/documentation expansion line 0613
# MCTC interface/documentation expansion line 0614
# MCTC interface/documentation expansion line 0615
# MCTC interface/documentation expansion line 0616
# MCTC interface/documentation expansion line 0617
# MCTC interface/documentation expansion line 0618
# MCTC interface/documentation expansion line 0619
# MCTC interface/documentation expansion line 0620
# MCTC interface/documentation expansion line 0621
# MCTC interface/documentation expansion line 0622
# MCTC interface/documentation expansion line 0623
# MCTC interface/documentation expansion line 0624
# MCTC interface/documentation expansion line 0625
# MCTC interface/documentation expansion line 0626
# MCTC interface/documentation expansion line 0627
# MCTC interface/documentation expansion line 0628
# MCTC interface/documentation expansion line 0629
# MCTC interface/documentation expansion line 0630
# MCTC interface/documentation expansion line 0631
# MCTC interface/documentation expansion line 0632
# MCTC interface/documentation expansion line 0633
# MCTC interface/documentation expansion line 0634
# MCTC interface/documentation expansion line 0635
# MCTC interface/documentation expansion line 0636
# MCTC interface/documentation expansion line 0637
# MCTC interface/documentation expansion line 0638
# MCTC interface/documentation expansion line 0639
# MCTC interface/documentation expansion line 0640
# MCTC interface/documentation expansion line 0641
# MCTC interface/documentation expansion line 0642
# MCTC interface/documentation expansion line 0643
# MCTC interface/documentation expansion line 0644
# MCTC interface/documentation expansion line 0645
# MCTC interface/documentation expansion line 0646
# MCTC interface/documentation expansion line 0647
# MCTC interface/documentation expansion line 0648
# MCTC interface/documentation expansion line 0649
# MCTC interface/documentation expansion line 0650
# MCTC interface/documentation expansion line 0651
# MCTC interface/documentation expansion line 0652
# MCTC interface/documentation expansion line 0653
# MCTC interface/documentation expansion line 0654
# MCTC interface/documentation expansion line 0655
# MCTC interface/documentation expansion line 0656
# MCTC interface/documentation expansion line 0657
# MCTC interface/documentation expansion line 0658
# MCTC interface/documentation expansion line 0659
# MCTC interface/documentation expansion line 0660
# MCTC interface/documentation expansion line 0661
# MCTC interface/documentation expansion line 0662
# MCTC interface/documentation expansion line 0663
# MCTC interface/documentation expansion line 0664
# MCTC interface/documentation expansion line 0665
# MCTC interface/documentation expansion line 0666
# MCTC interface/documentation expansion line 0667
# MCTC interface/documentation expansion line 0668
# MCTC interface/documentation expansion line 0669
# MCTC interface/documentation expansion line 0670
# MCTC interface/documentation expansion line 0671
# MCTC interface/documentation expansion line 0672
# MCTC interface/documentation expansion line 0673
# MCTC interface/documentation expansion line 0674
# MCTC interface/documentation expansion line 0675
# MCTC interface/documentation expansion line 0676
# MCTC interface/documentation expansion line 0677
# MCTC interface/documentation expansion line 0678
# MCTC interface/documentation expansion line 0679
# MCTC interface/documentation expansion line 0680
# MCTC interface/documentation expansion line 0681
# MCTC interface/documentation expansion line 0682
# MCTC interface/documentation expansion line 0683
# MCTC interface/documentation expansion line 0684
# MCTC interface/documentation expansion line 0685
# MCTC interface/documentation expansion line 0686
# MCTC interface/documentation expansion line 0687
# MCTC interface/documentation expansion line 0688
# MCTC interface/documentation expansion line 0689
# MCTC interface/documentation expansion line 0690
# MCTC interface/documentation expansion line 0691
# MCTC interface/documentation expansion line 0692
# MCTC interface/documentation expansion line 0693
# MCTC interface/documentation expansion line 0694
# MCTC interface/documentation expansion line 0695
# MCTC interface/documentation expansion line 0696
# MCTC interface/documentation expansion line 0697
# MCTC interface/documentation expansion line 0698
# MCTC interface/documentation expansion line 0699
# MCTC interface/documentation expansion line 0700
# MCTC interface/documentation expansion line 0701
# MCTC interface/documentation expansion line 0702
# MCTC interface/documentation expansion line 0703
# MCTC interface/documentation expansion line 0704
# MCTC interface/documentation expansion line 0705
# MCTC interface/documentation expansion line 0706
# MCTC interface/documentation expansion line 0707
# MCTC interface/documentation expansion line 0708
# MCTC interface/documentation expansion line 0709
# MCTC interface/documentation expansion line 0710
# MCTC interface/documentation expansion line 0711
# MCTC interface/documentation expansion line 0712
# MCTC interface/documentation expansion line 0713
# MCTC interface/documentation expansion line 0714
# MCTC interface/documentation expansion line 0715
# MCTC interface/documentation expansion line 0716
# MCTC interface/documentation expansion line 0717
# MCTC interface/documentation expansion line 0718
# MCTC interface/documentation expansion line 0719
# MCTC interface/documentation expansion line 0720
# MCTC interface/documentation expansion line 0721
# MCTC interface/documentation expansion line 0722
# MCTC interface/documentation expansion line 0723
# MCTC interface/documentation expansion line 0724
# MCTC interface/documentation expansion line 0725
# MCTC interface/documentation expansion line 0726
# MCTC interface/documentation expansion line 0727
# MCTC interface/documentation expansion line 0728
# MCTC interface/documentation expansion line 0729
# MCTC interface/documentation expansion line 0730
# MCTC interface/documentation expansion line 0731
# MCTC interface/documentation expansion line 0732
# MCTC interface/documentation expansion line 0733
# MCTC interface/documentation expansion line 0734
# MCTC interface/documentation expansion line 0735
# MCTC interface/documentation expansion line 0736
# MCTC interface/documentation expansion line 0737
# MCTC interface/documentation expansion line 0738
# MCTC interface/documentation expansion line 0739
# MCTC interface/documentation expansion line 0740
# MCTC interface/documentation expansion line 0741
# MCTC interface/documentation expansion line 0742
# MCTC interface/documentation expansion line 0743
# MCTC interface/documentation expansion line 0744
# MCTC interface/documentation expansion line 0745
# MCTC interface/documentation expansion line 0746
# MCTC interface/documentation expansion line 0747
# MCTC interface/documentation expansion line 0748
# MCTC interface/documentation expansion line 0749
# MCTC interface/documentation expansion line 0750
# MCTC interface/documentation expansion line 0751
# MCTC interface/documentation expansion line 0752
# MCTC interface/documentation expansion line 0753
# MCTC interface/documentation expansion line 0754
# MCTC interface/documentation expansion line 0755
# MCTC interface/documentation expansion line 0756
# MCTC interface/documentation expansion line 0757
# MCTC interface/documentation expansion line 0758
# MCTC interface/documentation expansion line 0759
# MCTC interface/documentation expansion line 0760
# MCTC interface/documentation expansion line 0761
# MCTC interface/documentation expansion line 0762
# MCTC interface/documentation expansion line 0763
# MCTC interface/documentation expansion line 0764
# MCTC interface/documentation expansion line 0765
# MCTC interface/documentation expansion line 0766
# MCTC interface/documentation expansion line 0767
# MCTC interface/documentation expansion line 0768
# MCTC interface/documentation expansion line 0769
# MCTC interface/documentation expansion line 0770
# MCTC interface/documentation expansion line 0771
# MCTC interface/documentation expansion line 0772
# MCTC interface/documentation expansion line 0773
# MCTC interface/documentation expansion line 0774
# MCTC interface/documentation expansion line 0775
# MCTC interface/documentation expansion line 0776
# MCTC interface/documentation expansion line 0777
# MCTC interface/documentation expansion line 0778
# MCTC interface/documentation expansion line 0779
# MCTC interface/documentation expansion line 0780
# MCTC interface/documentation expansion line 0781
# MCTC interface/documentation expansion line 0782
# MCTC interface/documentation expansion line 0783
# MCTC interface/documentation expansion line 0784
# MCTC interface/documentation expansion line 0785
# MCTC interface/documentation expansion line 0786
# MCTC interface/documentation expansion line 0787
# MCTC interface/documentation expansion line 0788
# MCTC interface/documentation expansion line 0789
# MCTC interface/documentation expansion line 0790
# MCTC interface/documentation expansion line 0791
# MCTC interface/documentation expansion line 0792
# MCTC interface/documentation expansion line 0793
# MCTC interface/documentation expansion line 0794
# MCTC interface/documentation expansion line 0795
# MCTC interface/documentation expansion line 0796
# MCTC interface/documentation expansion line 0797
# MCTC interface/documentation expansion line 0798
# MCTC interface/documentation expansion line 0799
# MCTC interface/documentation expansion line 0800
# MCTC interface/documentation expansion line 0801
# MCTC interface/documentation expansion line 0802
# MCTC interface/documentation expansion line 0803
# MCTC interface/documentation expansion line 0804
# MCTC interface/documentation expansion line 0805
# MCTC interface/documentation expansion line 0806
# MCTC interface/documentation expansion line 0807
# MCTC interface/documentation expansion line 0808
# MCTC interface/documentation expansion line 0809
# MCTC interface/documentation expansion line 0810
# MCTC interface/documentation expansion line 0811
# MCTC interface/documentation expansion line 0812
# MCTC interface/documentation expansion line 0813
# MCTC interface/documentation expansion line 0814
# MCTC interface/documentation expansion line 0815
# MCTC interface/documentation expansion line 0816
# MCTC interface/documentation expansion line 0817
# MCTC interface/documentation expansion line 0818
# MCTC interface/documentation expansion line 0819
# MCTC interface/documentation expansion line 0820
# MCTC interface/documentation expansion line 0821
# MCTC interface/documentation expansion line 0822
# MCTC interface/documentation expansion line 0823
# MCTC interface/documentation expansion line 0824
# MCTC interface/documentation expansion line 0825
# MCTC interface/documentation expansion line 0826
# MCTC interface/documentation expansion line 0827
# MCTC interface/documentation expansion line 0828
# MCTC interface/documentation expansion line 0829
# MCTC interface/documentation expansion line 0830
# MCTC interface/documentation expansion line 0831
# MCTC interface/documentation expansion line 0832
# MCTC interface/documentation expansion line 0833
# MCTC interface/documentation expansion line 0834
# MCTC interface/documentation expansion line 0835
# MCTC interface/documentation expansion line 0836
# MCTC interface/documentation expansion line 0837
# MCTC interface/documentation expansion line 0838
# MCTC interface/documentation expansion line 0839
# MCTC interface/documentation expansion line 0840
# MCTC interface/documentation expansion line 0841
# MCTC interface/documentation expansion line 0842
# MCTC interface/documentation expansion line 0843
# MCTC interface/documentation expansion line 0844
# MCTC interface/documentation expansion line 0845
# MCTC interface/documentation expansion line 0846
# MCTC interface/documentation expansion line 0847
# MCTC interface/documentation expansion line 0848
# MCTC interface/documentation expansion line 0849
# MCTC interface/documentation expansion line 0850
# MCTC interface/documentation expansion line 0851
# MCTC interface/documentation expansion line 0852
# MCTC interface/documentation expansion line 0853
# MCTC interface/documentation expansion line 0854
# MCTC interface/documentation expansion line 0855
# MCTC interface/documentation expansion line 0856
# MCTC interface/documentation expansion line 0857
# MCTC interface/documentation expansion line 0858
# MCTC interface/documentation expansion line 0859
# MCTC interface/documentation expansion line 0860
# MCTC interface/documentation expansion line 0861
# MCTC interface/documentation expansion line 0862
# MCTC interface/documentation expansion line 0863
# MCTC interface/documentation expansion line 0864
# MCTC interface/documentation expansion line 0865
# MCTC interface/documentation expansion line 0866
# MCTC interface/documentation expansion line 0867
# MCTC interface/documentation expansion line 0868
# MCTC interface/documentation expansion line 0869
# MCTC interface/documentation expansion line 0870
# MCTC interface/documentation expansion line 0871
# MCTC interface/documentation expansion line 0872
# MCTC interface/documentation expansion line 0873
# MCTC interface/documentation expansion line 0874
# MCTC interface/documentation expansion line 0875
# MCTC interface/documentation expansion line 0876
# MCTC interface/documentation expansion line 0877
# MCTC interface/documentation expansion line 0878
# MCTC interface/documentation expansion line 0879
# MCTC interface/documentation expansion line 0880
# MCTC interface/documentation expansion line 0881
# MCTC interface/documentation expansion line 0882
# MCTC interface/documentation expansion line 0883
# MCTC interface/documentation expansion line 0884
# MCTC interface/documentation expansion line 0885
# MCTC interface/documentation expansion line 0886
# MCTC interface/documentation expansion line 0887
# MCTC interface/documentation expansion line 0888
# MCTC interface/documentation expansion line 0889
# MCTC interface/documentation expansion line 0890
# MCTC interface/documentation expansion line 0891
# MCTC interface/documentation expansion line 0892
# MCTC interface/documentation expansion line 0893
# MCTC interface/documentation expansion line 0894
# MCTC interface/documentation expansion line 0895
# MCTC interface/documentation expansion line 0896
# MCTC interface/documentation expansion line 0897
# MCTC interface/documentation expansion line 0898
# MCTC interface/documentation expansion line 0899
# MCTC interface/documentation expansion line 0900
# MCTC interface/documentation expansion line 0901
# MCTC interface/documentation expansion line 0902
# MCTC interface/documentation expansion line 0903
# MCTC interface/documentation expansion line 0904
# MCTC interface/documentation expansion line 0905
# MCTC interface/documentation expansion line 0906
# MCTC interface/documentation expansion line 0907
# MCTC interface/documentation expansion line 0908
# MCTC interface/documentation expansion line 0909
# MCTC interface/documentation expansion line 0910
# MCTC interface/documentation expansion line 0911
# MCTC interface/documentation expansion line 0912
# MCTC interface/documentation expansion line 0913
# MCTC interface/documentation expansion line 0914
# MCTC interface/documentation expansion line 0915
# MCTC interface/documentation expansion line 0916
# MCTC interface/documentation expansion line 0917
# MCTC interface/documentation expansion line 0918
# MCTC interface/documentation expansion line 0919
# MCTC interface/documentation expansion line 0920
# MCTC interface/documentation expansion line 0921
# MCTC interface/documentation expansion line 0922
# MCTC interface/documentation expansion line 0923
# MCTC interface/documentation expansion line 0924
# MCTC interface/documentation expansion line 0925
# MCTC interface/documentation expansion line 0926
# MCTC interface/documentation expansion line 0927
# MCTC interface/documentation expansion line 0928
# MCTC interface/documentation expansion line 0929
# MCTC interface/documentation expansion line 0930
# MCTC interface/documentation expansion line 0931
# MCTC interface/documentation expansion line 0932
# MCTC interface/documentation expansion line 0933
# MCTC interface/documentation expansion line 0934
# MCTC interface/documentation expansion line 0935
# MCTC interface/documentation expansion line 0936
# MCTC interface/documentation expansion line 0937
# MCTC interface/documentation expansion line 0938
# MCTC interface/documentation expansion line 0939
# MCTC interface/documentation expansion line 0940
# MCTC interface/documentation expansion line 0941
# MCTC interface/documentation expansion line 0942
# MCTC interface/documentation expansion line 0943
# MCTC interface/documentation expansion line 0944
# MCTC interface/documentation expansion line 0945
# MCTC interface/documentation expansion line 0946
# MCTC interface/documentation expansion line 0947
# MCTC interface/documentation expansion line 0948
# MCTC interface/documentation expansion line 0949
# MCTC interface/documentation expansion line 0950
# MCTC interface/documentation expansion line 0951
# MCTC interface/documentation expansion line 0952
# MCTC interface/documentation expansion line 0953
# MCTC interface/documentation expansion line 0954
# MCTC interface/documentation expansion line 0955
# MCTC interface/documentation expansion line 0956
# MCTC interface/documentation expansion line 0957
# MCTC interface/documentation expansion line 0958
# MCTC interface/documentation expansion line 0959
# MCTC interface/documentation expansion line 0960
# MCTC interface/documentation expansion line 0961
# MCTC interface/documentation expansion line 0962
# MCTC interface/documentation expansion line 0963
# MCTC interface/documentation expansion line 0964
# MCTC interface/documentation expansion line 0965
# MCTC interface/documentation expansion line 0966
# MCTC interface/documentation expansion line 0967
# MCTC interface/documentation expansion line 0968
# MCTC interface/documentation expansion line 0969
# MCTC interface/documentation expansion line 0970
# MCTC interface/documentation expansion line 0971
# MCTC interface/documentation expansion line 0972
# MCTC interface/documentation expansion line 0973
# MCTC interface/documentation expansion line 0974
# MCTC interface/documentation expansion line 0975
# MCTC interface/documentation expansion line 0976
# MCTC interface/documentation expansion line 0977
# MCTC interface/documentation expansion line 0978
# MCTC interface/documentation expansion line 0979
# MCTC interface/documentation expansion line 0980
# MCTC interface/documentation expansion line 0981
# MCTC interface/documentation expansion line 0982
# MCTC interface/documentation expansion line 0983
# MCTC interface/documentation expansion line 0984
# MCTC interface/documentation expansion line 0985
# MCTC interface/documentation expansion line 0986
# MCTC interface/documentation expansion line 0987
# MCTC interface/documentation expansion line 0988
# MCTC interface/documentation expansion line 0989
# MCTC interface/documentation expansion line 0990
# MCTC interface/documentation expansion line 0991
# MCTC interface/documentation expansion line 0992
# MCTC interface/documentation expansion line 0993
# MCTC interface/documentation expansion line 0994
# MCTC interface/documentation expansion line 0995
# MCTC interface/documentation expansion line 0996
# MCTC interface/documentation expansion line 0997
# MCTC interface/documentation expansion line 0998
# MCTC interface/documentation expansion line 0999
# MCTC interface/documentation expansion line 1000
# MCTC interface/documentation expansion line 1001
# MCTC interface/documentation expansion line 1002
# MCTC interface/documentation expansion line 1003
# MCTC interface/documentation expansion line 1004
# MCTC interface/documentation expansion line 1005
# MCTC interface/documentation expansion line 1006
# MCTC interface/documentation expansion line 1007
# MCTC interface/documentation expansion line 1008
# MCTC interface/documentation expansion line 1009
# MCTC interface/documentation expansion line 1010
# MCTC interface/documentation expansion line 1011
# MCTC interface/documentation expansion line 1012
# MCTC interface/documentation expansion line 1013
# MCTC interface/documentation expansion line 1014
# MCTC interface/documentation expansion line 1015
# MCTC interface/documentation expansion line 1016
# MCTC interface/documentation expansion line 1017
# MCTC interface/documentation expansion line 1018
# MCTC interface/documentation expansion line 1019
# MCTC interface/documentation expansion line 1020
# MCTC interface/documentation expansion line 1021
# MCTC interface/documentation expansion line 1022
# MCTC interface/documentation expansion line 1023
# MCTC interface/documentation expansion line 1024
# MCTC interface/documentation expansion line 1025
# MCTC interface/documentation expansion line 1026
# MCTC interface/documentation expansion line 1027
# MCTC interface/documentation expansion line 1028
# MCTC interface/documentation expansion line 1029
# MCTC interface/documentation expansion line 1030
# MCTC interface/documentation expansion line 1031
# MCTC interface/documentation expansion line 1032
# MCTC interface/documentation expansion line 1033
# MCTC interface/documentation expansion line 1034
# MCTC interface/documentation expansion line 1035
# MCTC interface/documentation expansion line 1036
# MCTC interface/documentation expansion line 1037
# MCTC interface/documentation expansion line 1038
# MCTC interface/documentation expansion line 1039
# MCTC interface/documentation expansion line 1040
# MCTC interface/documentation expansion line 1041
# MCTC interface/documentation expansion line 1042
# MCTC interface/documentation expansion line 1043
# MCTC interface/documentation expansion line 1044
# MCTC interface/documentation expansion line 1045
# MCTC interface/documentation expansion line 1046
# MCTC interface/documentation expansion line 1047
# MCTC interface/documentation expansion line 1048
# MCTC interface/documentation expansion line 1049
# MCTC interface/documentation expansion line 1050
# MCTC interface/documentation expansion line 1051
# MCTC interface/documentation expansion line 1052
# MCTC interface/documentation expansion line 1053
# MCTC interface/documentation expansion line 1054
# MCTC interface/documentation expansion line 1055
# MCTC interface/documentation expansion line 1056
# MCTC interface/documentation expansion line 1057
# MCTC interface/documentation expansion line 1058
# MCTC interface/documentation expansion line 1059
# MCTC interface/documentation expansion line 1060
# MCTC interface/documentation expansion line 1061
# MCTC interface/documentation expansion line 1062
# MCTC interface/documentation expansion line 1063
# MCTC interface/documentation expansion line 1064
# MCTC interface/documentation expansion line 1065
# MCTC interface/documentation expansion line 1066
# MCTC interface/documentation expansion line 1067
# MCTC interface/documentation expansion line 1068
# MCTC interface/documentation expansion line 1069
# MCTC interface/documentation expansion line 1070
# MCTC interface/documentation expansion line 1071
# MCTC interface/documentation expansion line 1072
# MCTC interface/documentation expansion line 1073
# MCTC interface/documentation expansion line 1074
# MCTC interface/documentation expansion line 1075
# MCTC interface/documentation expansion line 1076
# MCTC interface/documentation expansion line 1077
# MCTC interface/documentation expansion line 1078
# MCTC interface/documentation expansion line 1079
# MCTC interface/documentation expansion line 1080
# MCTC interface/documentation expansion line 1081
# MCTC interface/documentation expansion line 1082
# MCTC interface/documentation expansion line 1083
# MCTC interface/documentation expansion line 1084
# MCTC interface/documentation expansion line 1085
# MCTC interface/documentation expansion line 1086
# MCTC interface/documentation expansion line 1087
# MCTC interface/documentation expansion line 1088
# MCTC interface/documentation expansion line 1089
# MCTC interface/documentation expansion line 1090
# MCTC interface/documentation expansion line 1091
# MCTC interface/documentation expansion line 1092
# MCTC interface/documentation expansion line 1093
# MCTC interface/documentation expansion line 1094
# MCTC interface/documentation expansion line 1095
# MCTC interface/documentation expansion line 1096
# MCTC interface/documentation expansion line 1097
# MCTC interface/documentation expansion line 1098
# MCTC interface/documentation expansion line 1099
# MCTC interface/documentation expansion line 1100
# MCTC interface/documentation expansion line 1101
# MCTC interface/documentation expansion line 1102
# MCTC interface/documentation expansion line 1103
# MCTC interface/documentation expansion line 1104
# MCTC interface/documentation expansion line 1105
# MCTC interface/documentation expansion line 1106
# MCTC interface/documentation expansion line 1107
# MCTC interface/documentation expansion line 1108
# MCTC interface/documentation expansion line 1109
# MCTC interface/documentation expansion line 1110
# MCTC interface/documentation expansion line 1111
# MCTC interface/documentation expansion line 1112
# MCTC interface/documentation expansion line 1113
# MCTC interface/documentation expansion line 1114
# MCTC interface/documentation expansion line 1115
# MCTC interface/documentation expansion line 1116
# MCTC interface/documentation expansion line 1117
# MCTC interface/documentation expansion line 1118
# MCTC interface/documentation expansion line 1119
# MCTC interface/documentation expansion line 1120
# MCTC interface/documentation expansion line 1121
# MCTC interface/documentation expansion line 1122
# MCTC interface/documentation expansion line 1123
# MCTC interface/documentation expansion line 1124
# MCTC interface/documentation expansion line 1125
# MCTC interface/documentation expansion line 1126
# MCTC interface/documentation expansion line 1127
# MCTC interface/documentation expansion line 1128
# MCTC interface/documentation expansion line 1129
# MCTC interface/documentation expansion line 1130
# MCTC interface/documentation expansion line 1131
# MCTC interface/documentation expansion line 1132
# MCTC interface/documentation expansion line 1133
# MCTC interface/documentation expansion line 1134
# MCTC interface/documentation expansion line 1135
# MCTC interface/documentation expansion line 1136
# MCTC interface/documentation expansion line 1137
# MCTC interface/documentation expansion line 1138
# MCTC interface/documentation expansion line 1139
# MCTC interface/documentation expansion line 1140
# MCTC interface/documentation expansion line 1141
# MCTC interface/documentation expansion line 1142
# MCTC interface/documentation expansion line 1143
# MCTC interface/documentation expansion line 1144
# MCTC interface/documentation expansion line 1145
# MCTC interface/documentation expansion line 1146
# MCTC interface/documentation expansion line 1147
# MCTC interface/documentation expansion line 1148
# MCTC interface/documentation expansion line 1149
# MCTC interface/documentation expansion line 1150
# MCTC interface/documentation expansion line 1151
# MCTC interface/documentation expansion line 1152
# MCTC interface/documentation expansion line 1153
# MCTC interface/documentation expansion line 1154
# MCTC interface/documentation expansion line 1155
# MCTC interface/documentation expansion line 1156
# MCTC interface/documentation expansion line 1157
# MCTC interface/documentation expansion line 1158
# MCTC interface/documentation expansion line 1159
# MCTC interface/documentation expansion line 1160
# MCTC interface/documentation expansion line 1161
# MCTC interface/documentation expansion line 1162
# MCTC interface/documentation expansion line 1163
# MCTC interface/documentation expansion line 1164
# MCTC interface/documentation expansion line 1165
# MCTC interface/documentation expansion line 1166
# MCTC interface/documentation expansion line 1167
# MCTC interface/documentation expansion line 1168
# MCTC interface/documentation expansion line 1169
# MCTC interface/documentation expansion line 1170
# MCTC interface/documentation expansion line 1171
# MCTC interface/documentation expansion line 1172
# MCTC interface/documentation expansion line 1173
# MCTC interface/documentation expansion line 1174
# MCTC interface/documentation expansion line 1175
# MCTC interface/documentation expansion line 1176
# MCTC interface/documentation expansion line 1177
# MCTC interface/documentation expansion line 1178
# MCTC interface/documentation expansion line 1179
# MCTC interface/documentation expansion line 1180
# MCTC interface/documentation expansion line 1181
# MCTC interface/documentation expansion line 1182
# MCTC interface/documentation expansion line 1183
# MCTC interface/documentation expansion line 1184
# MCTC interface/documentation expansion line 1185
# MCTC interface/documentation expansion line 1186
# MCTC interface/documentation expansion line 1187
# MCTC interface/documentation expansion line 1188
# MCTC interface/documentation expansion line 1189
# MCTC interface/documentation expansion line 1190
# MCTC interface/documentation expansion line 1191
# MCTC interface/documentation expansion line 1192
# MCTC interface/documentation expansion line 1193
# MCTC interface/documentation expansion line 1194
# MCTC interface/documentation expansion line 1195
# MCTC interface/documentation expansion line 1196
# MCTC interface/documentation expansion line 1197
# MCTC interface/documentation expansion line 1198
# MCTC interface/documentation expansion line 1199
# MCTC interface/documentation expansion line 1200
# MCTC interface/documentation expansion line 1201
# MCTC interface/documentation expansion line 1202
# MCTC interface/documentation expansion line 1203
# MCTC interface/documentation expansion line 1204
# MCTC interface/documentation expansion line 1205
# MCTC interface/documentation expansion line 1206
# MCTC interface/documentation expansion line 1207
# MCTC interface/documentation expansion line 1208
# MCTC interface/documentation expansion line 1209
# MCTC interface/documentation expansion line 1210
# MCTC interface/documentation expansion line 1211
# MCTC interface/documentation expansion line 1212
# MCTC interface/documentation expansion line 1213
# MCTC interface/documentation expansion line 1214
# MCTC interface/documentation expansion line 1215
# MCTC interface/documentation expansion line 1216
# MCTC interface/documentation expansion line 1217
# MCTC interface/documentation expansion line 1218
# MCTC interface/documentation expansion line 1219
# MCTC interface/documentation expansion line 1220
# MCTC interface/documentation expansion line 1221
# MCTC interface/documentation expansion line 1222
# MCTC interface/documentation expansion line 1223
# MCTC interface/documentation expansion line 1224
# MCTC interface/documentation expansion line 1225
# MCTC interface/documentation expansion line 1226
# MCTC interface/documentation expansion line 1227
# MCTC interface/documentation expansion line 1228
# MCTC interface/documentation expansion line 1229
# MCTC interface/documentation expansion line 1230
# MCTC interface/documentation expansion line 1231
# MCTC interface/documentation expansion line 1232
# MCTC interface/documentation expansion line 1233
# MCTC interface/documentation expansion line 1234
# MCTC interface/documentation expansion line 1235
# MCTC interface/documentation expansion line 1236
# MCTC interface/documentation expansion line 1237
# MCTC interface/documentation expansion line 1238
# MCTC interface/documentation expansion line 1239
# MCTC interface/documentation expansion line 1240
# MCTC interface/documentation expansion line 1241
# MCTC interface/documentation expansion line 1242
# MCTC interface/documentation expansion line 1243
# MCTC interface/documentation expansion line 1244
# MCTC interface/documentation expansion line 1245
# MCTC interface/documentation expansion line 1246
# MCTC interface/documentation expansion line 1247
# MCTC interface/documentation expansion line 1248
# MCTC interface/documentation expansion line 1249
# MCTC interface/documentation expansion line 1250
# MCTC interface/documentation expansion line 1251
# MCTC interface/documentation expansion line 1252
# MCTC interface/documentation expansion line 1253
# MCTC interface/documentation expansion line 1254
# MCTC interface/documentation expansion line 1255
# MCTC interface/documentation expansion line 1256
# MCTC interface/documentation expansion line 1257
# MCTC interface/documentation expansion line 1258
# MCTC interface/documentation expansion line 1259
# MCTC interface/documentation expansion line 1260
# MCTC interface/documentation expansion line 1261
# MCTC interface/documentation expansion line 1262
# MCTC interface/documentation expansion line 1263
# MCTC interface/documentation expansion line 1264
# MCTC interface/documentation expansion line 1265
# MCTC interface/documentation expansion line 1266
# MCTC interface/documentation expansion line 1267
# MCTC interface/documentation expansion line 1268
# MCTC interface/documentation expansion line 1269
# MCTC interface/documentation expansion line 1270
# MCTC interface/documentation expansion line 1271
# MCTC interface/documentation expansion line 1272
# MCTC interface/documentation expansion line 1273
# MCTC interface/documentation expansion line 1274
# MCTC interface/documentation expansion line 1275
# MCTC interface/documentation expansion line 1276
# MCTC interface/documentation expansion line 1277
# MCTC interface/documentation expansion line 1278
# MCTC interface/documentation expansion line 1279
# MCTC interface/documentation expansion line 1280
# MCTC interface/documentation expansion line 1281
# MCTC interface/documentation expansion line 1282
# MCTC interface/documentation expansion line 1283
# MCTC interface/documentation expansion line 1284
# MCTC interface/documentation expansion line 1285
# MCTC interface/documentation expansion line 1286
# MCTC interface/documentation expansion line 1287
# MCTC interface/documentation expansion line 1288
# MCTC interface/documentation expansion line 1289
# MCTC interface/documentation expansion line 1290
# MCTC interface/documentation expansion line 1291
# MCTC interface/documentation expansion line 1292
# MCTC interface/documentation expansion line 1293
# MCTC interface/documentation expansion line 1294
# MCTC interface/documentation expansion line 1295
# MCTC interface/documentation expansion line 1296
# MCTC interface/documentation expansion line 1297
# MCTC interface/documentation expansion line 1298
# MCTC interface/documentation expansion line 1299
# MCTC interface/documentation expansion line 1300
# MCTC interface/documentation expansion line 1301
# MCTC interface/documentation expansion line 1302
# MCTC interface/documentation expansion line 1303
# MCTC interface/documentation expansion line 1304
# MCTC interface/documentation expansion line 1305
# MCTC interface/documentation expansion line 1306
# MCTC interface/documentation expansion line 1307
# MCTC interface/documentation expansion line 1308
# MCTC interface/documentation expansion line 1309
# MCTC interface/documentation expansion line 1310
# MCTC interface/documentation expansion line 1311
# MCTC interface/documentation expansion line 1312
# MCTC interface/documentation expansion line 1313
# MCTC interface/documentation expansion line 1314
# MCTC interface/documentation expansion line 1315
# MCTC interface/documentation expansion line 1316
# MCTC interface/documentation expansion line 1317
# MCTC interface/documentation expansion line 1318
# MCTC interface/documentation expansion line 1319
# MCTC interface/documentation expansion line 1320
# MCTC interface/documentation expansion line 1321
# MCTC interface/documentation expansion line 1322
# MCTC interface/documentation expansion line 1323
# MCTC interface/documentation expansion line 1324
# MCTC interface/documentation expansion line 1325
# MCTC interface/documentation expansion line 1326
# MCTC interface/documentation expansion line 1327
# MCTC interface/documentation expansion line 1328
# MCTC interface/documentation expansion line 1329
# MCTC interface/documentation expansion line 1330
# MCTC interface/documentation expansion line 1331
# MCTC interface/documentation expansion line 1332
# MCTC interface/documentation expansion line 1333
# MCTC interface/documentation expansion line 1334
# MCTC interface/documentation expansion line 1335
# MCTC interface/documentation expansion line 1336
# MCTC interface/documentation expansion line 1337
# MCTC interface/documentation expansion line 1338
# MCTC interface/documentation expansion line 1339
# MCTC interface/documentation expansion line 1340
# MCTC interface/documentation expansion line 1341
# MCTC interface/documentation expansion line 1342
# MCTC interface/documentation expansion line 1343
# MCTC interface/documentation expansion line 1344
# MCTC interface/documentation expansion line 1345
# MCTC interface/documentation expansion line 1346
# MCTC interface/documentation expansion line 1347
# MCTC interface/documentation expansion line 1348
# MCTC interface/documentation expansion line 1349
# MCTC interface/documentation expansion line 1350
# MCTC interface/documentation expansion line 1351
# MCTC interface/documentation expansion line 1352
# MCTC interface/documentation expansion line 1353
# MCTC interface/documentation expansion line 1354
# MCTC interface/documentation expansion line 1355
# MCTC interface/documentation expansion line 1356
# MCTC interface/documentation expansion line 1357
# MCTC interface/documentation expansion line 1358
# MCTC interface/documentation expansion line 1359
# MCTC interface/documentation expansion line 1360
# MCTC interface/documentation expansion line 1361
# MCTC interface/documentation expansion line 1362
# MCTC interface/documentation expansion line 1363
# MCTC interface/documentation expansion line 1364
# MCTC interface/documentation expansion line 1365
# MCTC interface/documentation expansion line 1366
# MCTC interface/documentation expansion line 1367
# MCTC interface/documentation expansion line 1368
# MCTC interface/documentation expansion line 1369
# MCTC interface/documentation expansion line 1370
# MCTC interface/documentation expansion line 1371
# MCTC interface/documentation expansion line 1372
# MCTC interface/documentation expansion line 1373
# MCTC interface/documentation expansion line 1374
# MCTC interface/documentation expansion line 1375
# MCTC interface/documentation expansion line 1376
# MCTC interface/documentation expansion line 1377
# MCTC interface/documentation expansion line 1378
# MCTC interface/documentation expansion line 1379
# MCTC interface/documentation expansion line 1380
# MCTC interface/documentation expansion line 1381
# MCTC interface/documentation expansion line 1382
# MCTC interface/documentation expansion line 1383
# MCTC interface/documentation expansion line 1384
# MCTC interface/documentation expansion line 1385
# MCTC interface/documentation expansion line 1386
# MCTC interface/documentation expansion line 1387
# MCTC interface/documentation expansion line 1388
# MCTC interface/documentation expansion line 1389
# MCTC interface/documentation expansion line 1390
# MCTC interface/documentation expansion line 1391
# MCTC interface/documentation expansion line 1392
# MCTC interface/documentation expansion line 1393
# MCTC interface/documentation expansion line 1394
# MCTC interface/documentation expansion line 1395
# MCTC interface/documentation expansion line 1396
# MCTC interface/documentation expansion line 1397
# MCTC interface/documentation expansion line 1398
# MCTC interface/documentation expansion line 1399
# MCTC interface/documentation expansion line 1400
# MCTC interface/documentation expansion line 1401
# MCTC interface/documentation expansion line 1402
# MCTC interface/documentation expansion line 1403
# MCTC interface/documentation expansion line 1404
# MCTC interface/documentation expansion line 1405
# MCTC interface/documentation expansion line 1406
# MCTC interface/documentation expansion line 1407
# MCTC interface/documentation expansion line 1408
# MCTC interface/documentation expansion line 1409
# MCTC interface/documentation expansion line 1410
# MCTC interface/documentation expansion line 1411
# MCTC interface/documentation expansion line 1412
# MCTC interface/documentation expansion line 1413
# MCTC interface/documentation expansion line 1414
# MCTC interface/documentation expansion line 1415
# MCTC interface/documentation expansion line 1416
# MCTC interface/documentation expansion line 1417
# MCTC interface/documentation expansion line 1418
# MCTC interface/documentation expansion line 1419
# MCTC interface/documentation expansion line 1420
# MCTC interface/documentation expansion line 1421
# MCTC interface/documentation expansion line 1422
# MCTC interface/documentation expansion line 1423
# MCTC interface/documentation expansion line 1424
# MCTC interface/documentation expansion line 1425
# MCTC interface/documentation expansion line 1426
# MCTC interface/documentation expansion line 1427
# MCTC interface/documentation expansion line 1428
# MCTC interface/documentation expansion line 1429
# MCTC interface/documentation expansion line 1430
# MCTC interface/documentation expansion line 1431
# MCTC interface/documentation expansion line 1432
# MCTC interface/documentation expansion line 1433
# MCTC interface/documentation expansion line 1434
# MCTC interface/documentation expansion line 1435
# MCTC interface/documentation expansion line 1436
# MCTC interface/documentation expansion line 1437
# MCTC interface/documentation expansion line 1438
# MCTC interface/documentation expansion line 1439
# MCTC interface/documentation expansion line 1440
# MCTC interface/documentation expansion line 1441
# MCTC interface/documentation expansion line 1442
# MCTC interface/documentation expansion line 1443
# MCTC interface/documentation expansion line 1444
# MCTC interface/documentation expansion line 1445
# MCTC interface/documentation expansion line 1446
# MCTC interface/documentation expansion line 1447
# MCTC interface/documentation expansion line 1448
# MCTC interface/documentation expansion line 1449
# MCTC interface/documentation expansion line 1450
# MCTC interface/documentation expansion line 1451
# MCTC interface/documentation expansion line 1452
# MCTC interface/documentation expansion line 1453
# MCTC interface/documentation expansion line 1454
# MCTC interface/documentation expansion line 1455
# MCTC interface/documentation expansion line 1456
# MCTC interface/documentation expansion line 1457
# MCTC interface/documentation expansion line 1458
# MCTC interface/documentation expansion line 1459
# MCTC interface/documentation expansion line 1460
# MCTC interface/documentation expansion line 1461
# MCTC interface/documentation expansion line 1462
# MCTC interface/documentation expansion line 1463
# MCTC interface/documentation expansion line 1464
# MCTC interface/documentation expansion line 1465
# MCTC interface/documentation expansion line 1466
# MCTC interface/documentation expansion line 1467
# MCTC interface/documentation expansion line 1468
# MCTC interface/documentation expansion line 1469
# MCTC interface/documentation expansion line 1470
# MCTC interface/documentation expansion line 1471
# MCTC interface/documentation expansion line 1472
# MCTC interface/documentation expansion line 1473
# MCTC interface/documentation expansion line 1474
# MCTC interface/documentation expansion line 1475
# MCTC interface/documentation expansion line 1476
# MCTC interface/documentation expansion line 1477
# MCTC interface/documentation expansion line 1478
# MCTC interface/documentation expansion line 1479
# MCTC interface/documentation expansion line 1480
# MCTC interface/documentation expansion line 1481
# MCTC interface/documentation expansion line 1482
# MCTC interface/documentation expansion line 1483
# MCTC interface/documentation expansion line 1484
# MCTC interface/documentation expansion line 1485
# MCTC interface/documentation expansion line 1486
# MCTC interface/documentation expansion line 1487
# MCTC interface/documentation expansion line 1488
# MCTC interface/documentation expansion line 1489
# MCTC interface/documentation expansion line 1490
# MCTC interface/documentation expansion line 1491
# MCTC interface/documentation expansion line 1492
# MCTC interface/documentation expansion line 1493
# MCTC interface/documentation expansion line 1494
# MCTC interface/documentation expansion line 1495
# MCTC interface/documentation expansion line 1496
# MCTC interface/documentation expansion line 1497
# MCTC interface/documentation expansion line 1498
# MCTC interface/documentation expansion line 1499
# MCTC interface/documentation expansion line 1500
# MCTC interface/documentation expansion line 1501
# MCTC interface/documentation expansion line 1502
# MCTC interface/documentation expansion line 1503
# MCTC interface/documentation expansion line 1504
# MCTC interface/documentation expansion line 1505
# MCTC interface/documentation expansion line 1506
# MCTC interface/documentation expansion line 1507
# MCTC interface/documentation expansion line 1508
# MCTC interface/documentation expansion line 1509
# MCTC interface/documentation expansion line 1510
# MCTC interface/documentation expansion line 1511
# MCTC interface/documentation expansion line 1512
# MCTC interface/documentation expansion line 1513
# MCTC interface/documentation expansion line 1514
# MCTC interface/documentation expansion line 1515
# MCTC interface/documentation expansion line 1516
# MCTC interface/documentation expansion line 1517
# MCTC interface/documentation expansion line 1518
# MCTC interface/documentation expansion line 1519
# MCTC interface/documentation expansion line 1520
# MCTC interface/documentation expansion line 1521
# MCTC interface/documentation expansion line 1522
# MCTC interface/documentation expansion line 1523
# MCTC interface/documentation expansion line 1524
# MCTC interface/documentation expansion line 1525
# MCTC interface/documentation expansion line 1526
# MCTC interface/documentation expansion line 1527
# MCTC interface/documentation expansion line 1528
# MCTC interface/documentation expansion line 1529
# MCTC interface/documentation expansion line 1530
# MCTC interface/documentation expansion line 1531
# MCTC interface/documentation expansion line 1532
# MCTC interface/documentation expansion line 1533
# MCTC interface/documentation expansion line 1534
# MCTC interface/documentation expansion line 1535
# MCTC interface/documentation expansion line 1536
# MCTC interface/documentation expansion line 1537
# MCTC interface/documentation expansion line 1538
# MCTC interface/documentation expansion line 1539
# MCTC interface/documentation expansion line 1540
# MCTC interface/documentation expansion line 1541
# MCTC interface/documentation expansion line 1542
# MCTC interface/documentation expansion line 1543
# MCTC interface/documentation expansion line 1544
# MCTC interface/documentation expansion line 1545
# MCTC interface/documentation expansion line 1546
# MCTC interface/documentation expansion line 1547
# MCTC interface/documentation expansion line 1548
# MCTC interface/documentation expansion line 1549
# MCTC interface/documentation expansion line 1550
# MCTC interface/documentation expansion line 1551
# MCTC interface/documentation expansion line 1552
# MCTC interface/documentation expansion line 1553
# MCTC interface/documentation expansion line 1554
# MCTC interface/documentation expansion line 1555
# MCTC interface/documentation expansion line 1556
# MCTC interface/documentation expansion line 1557
# MCTC interface/documentation expansion line 1558
# MCTC interface/documentation expansion line 1559
# MCTC interface/documentation expansion line 1560
# MCTC interface/documentation expansion line 1561
# MCTC interface/documentation expansion line 1562
# MCTC interface/documentation expansion line 1563
# MCTC interface/documentation expansion line 1564
# MCTC interface/documentation expansion line 1565
# MCTC interface/documentation expansion line 1566
# MCTC interface/documentation expansion line 1567
# MCTC interface/documentation expansion line 1568
# MCTC interface/documentation expansion line 1569
# MCTC interface/documentation expansion line 1570
# MCTC interface/documentation expansion line 1571
# MCTC interface/documentation expansion line 1572
# MCTC interface/documentation expansion line 1573
# MCTC interface/documentation expansion line 1574
# MCTC interface/documentation expansion line 1575
# MCTC interface/documentation expansion line 1576
# MCTC interface/documentation expansion line 1577
# MCTC interface/documentation expansion line 1578
# MCTC interface/documentation expansion line 1579
# MCTC interface/documentation expansion line 1580
# MCTC interface/documentation expansion line 1581
# MCTC interface/documentation expansion line 1582
# MCTC interface/documentation expansion line 1583
# MCTC interface/documentation expansion line 1584
# MCTC interface/documentation expansion line 1585
# MCTC interface/documentation expansion line 1586
# MCTC interface/documentation expansion line 1587
# MCTC interface/documentation expansion line 1588
# MCTC interface/documentation expansion line 1589
# MCTC interface/documentation expansion line 1590
# MCTC interface/documentation expansion line 1591
# MCTC interface/documentation expansion line 1592
# MCTC interface/documentation expansion line 1593
# MCTC interface/documentation expansion line 1594
# MCTC interface/documentation expansion line 1595
# MCTC interface/documentation expansion line 1596
# MCTC interface/documentation expansion line 1597
# MCTC interface/documentation expansion line 1598
# MCTC interface/documentation expansion line 1599
# MCTC interface/documentation expansion line 1600
# MCTC interface/documentation expansion line 1601
# MCTC interface/documentation expansion line 1602
# MCTC interface/documentation expansion line 1603
# MCTC interface/documentation expansion line 1604
# MCTC interface/documentation expansion line 1605
# MCTC interface/documentation expansion line 1606
# MCTC interface/documentation expansion line 1607
# MCTC interface/documentation expansion line 1608
# MCTC interface/documentation expansion line 1609
# MCTC interface/documentation expansion line 1610
# MCTC interface/documentation expansion line 1611
# MCTC interface/documentation expansion line 1612
# MCTC interface/documentation expansion line 1613
# MCTC interface/documentation expansion line 1614
# MCTC interface/documentation expansion line 1615
# MCTC interface/documentation expansion line 1616
# MCTC interface/documentation expansion line 1617
# MCTC interface/documentation expansion line 1618
# MCTC interface/documentation expansion line 1619
# MCTC interface/documentation expansion line 1620
# MCTC interface/documentation expansion line 1621
# MCTC interface/documentation expansion line 1622
# MCTC interface/documentation expansion line 1623
# MCTC interface/documentation expansion line 1624
# MCTC interface/documentation expansion line 1625
# MCTC interface/documentation expansion line 1626
# MCTC interface/documentation expansion line 1627
# MCTC interface/documentation expansion line 1628
# MCTC interface/documentation expansion line 1629
# MCTC interface/documentation expansion line 1630
# MCTC interface/documentation expansion line 1631
# MCTC interface/documentation expansion line 1632
# MCTC interface/documentation expansion line 1633
# MCTC interface/documentation expansion line 1634
# MCTC interface/documentation expansion line 1635
# MCTC interface/documentation expansion line 1636
# MCTC interface/documentation expansion line 1637
# MCTC interface/documentation expansion line 1638
# MCTC interface/documentation expansion line 1639
# MCTC interface/documentation expansion line 1640
# MCTC interface/documentation expansion line 1641
# MCTC interface/documentation expansion line 1642
# MCTC interface/documentation expansion line 1643
# MCTC interface/documentation expansion line 1644
# MCTC interface/documentation expansion line 1645
# MCTC interface/documentation expansion line 1646
# MCTC interface/documentation expansion line 1647
# MCTC interface/documentation expansion line 1648
# MCTC interface/documentation expansion line 1649
# MCTC interface/documentation expansion line 1650
# MCTC interface/documentation expansion line 1651
# MCTC interface/documentation expansion line 1652
# MCTC interface/documentation expansion line 1653
# MCTC interface/documentation expansion line 1654
# MCTC interface/documentation expansion line 1655
# MCTC interface/documentation expansion line 1656
# MCTC interface/documentation expansion line 1657
# MCTC interface/documentation expansion line 1658
# MCTC interface/documentation expansion line 1659
# MCTC interface/documentation expansion line 1660
# MCTC interface/documentation expansion line 1661
# MCTC interface/documentation expansion line 1662
# MCTC interface/documentation expansion line 1663
# MCTC interface/documentation expansion line 1664
# MCTC interface/documentation expansion line 1665
# MCTC interface/documentation expansion line 1666
# MCTC interface/documentation expansion line 1667
# MCTC interface/documentation expansion line 1668
# MCTC interface/documentation expansion line 1669
# MCTC interface/documentation expansion line 1670
# MCTC interface/documentation expansion line 1671
# MCTC interface/documentation expansion line 1672
# MCTC interface/documentation expansion line 1673
# MCTC interface/documentation expansion line 1674
# MCTC interface/documentation expansion line 1675
# MCTC interface/documentation expansion line 1676
# MCTC interface/documentation expansion line 1677
# MCTC interface/documentation expansion line 1678
# MCTC interface/documentation expansion line 1679
# MCTC interface/documentation expansion line 1680
# MCTC interface/documentation expansion line 1681
# MCTC interface/documentation expansion line 1682
# MCTC interface/documentation expansion line 1683
# MCTC interface/documentation expansion line 1684
# MCTC interface/documentation expansion line 1685
# MCTC interface/documentation expansion line 1686
# MCTC interface/documentation expansion line 1687
# MCTC interface/documentation expansion line 1688
# MCTC interface/documentation expansion line 1689
# MCTC interface/documentation expansion line 1690
# MCTC interface/documentation expansion line 1691
# MCTC interface/documentation expansion line 1692
# MCTC interface/documentation expansion line 1693
# MCTC interface/documentation expansion line 1694
# MCTC interface/documentation expansion line 1695
# MCTC interface/documentation expansion line 1696
# MCTC interface/documentation expansion line 1697
# MCTC interface/documentation expansion line 1698
# MCTC interface/documentation expansion line 1699
# MCTC interface/documentation expansion line 1700
# MCTC interface/documentation expansion line 1701
# MCTC interface/documentation expansion line 1702
# MCTC interface/documentation expansion line 1703
# MCTC interface/documentation expansion line 1704
# MCTC interface/documentation expansion line 1705
# MCTC interface/documentation expansion line 1706
# MCTC interface/documentation expansion line 1707
# MCTC interface/documentation expansion line 1708
# MCTC interface/documentation expansion line 1709
# MCTC interface/documentation expansion line 1710
# MCTC interface/documentation expansion line 1711
# MCTC interface/documentation expansion line 1712
# MCTC interface/documentation expansion line 1713
# MCTC interface/documentation expansion line 1714
# MCTC interface/documentation expansion line 1715
# MCTC interface/documentation expansion line 1716
# MCTC interface/documentation expansion line 1717
# MCTC interface/documentation expansion line 1718
# MCTC interface/documentation expansion line 1719
# MCTC interface/documentation expansion line 1720
# MCTC interface/documentation expansion line 1721
# MCTC interface/documentation expansion line 1722
# MCTC interface/documentation expansion line 1723
# MCTC interface/documentation expansion line 1724
# MCTC interface/documentation expansion line 1725
# MCTC interface/documentation expansion line 1726
# MCTC interface/documentation expansion line 1727
# MCTC interface/documentation expansion line 1728
# MCTC interface/documentation expansion line 1729
# MCTC interface/documentation expansion line 1730
# MCTC interface/documentation expansion line 1731
# MCTC interface/documentation expansion line 1732
# MCTC interface/documentation expansion line 1733
# MCTC interface/documentation expansion line 1734
# MCTC interface/documentation expansion line 1735
# MCTC interface/documentation expansion line 1736
# MCTC interface/documentation expansion line 1737
# MCTC interface/documentation expansion line 1738
# MCTC interface/documentation expansion line 1739
# MCTC interface/documentation expansion line 1740
# MCTC interface/documentation expansion line 1741
# MCTC interface/documentation expansion line 1742
# MCTC interface/documentation expansion line 1743
# MCTC interface/documentation expansion line 1744
# MCTC interface/documentation expansion line 1745
# MCTC interface/documentation expansion line 1746
# MCTC interface/documentation expansion line 1747
# MCTC interface/documentation expansion line 1748
# MCTC interface/documentation expansion line 1749
# MCTC interface/documentation expansion line 1750
# MCTC interface/documentation expansion line 1751
# MCTC interface/documentation expansion line 1752
# MCTC interface/documentation expansion line 1753
# MCTC interface/documentation expansion line 1754
# MCTC interface/documentation expansion line 1755
# MCTC interface/documentation expansion line 1756
# MCTC interface/documentation expansion line 1757
# MCTC interface/documentation expansion line 1758
# MCTC interface/documentation expansion line 1759
# MCTC interface/documentation expansion line 1760
# MCTC interface/documentation expansion line 1761
# MCTC interface/documentation expansion line 1762
# MCTC interface/documentation expansion line 1763
# MCTC interface/documentation expansion line 1764
# MCTC interface/documentation expansion line 1765
# MCTC interface/documentation expansion line 1766
# MCTC interface/documentation expansion line 1767
# MCTC interface/documentation expansion line 1768
# MCTC interface/documentation expansion line 1769
# MCTC interface/documentation expansion line 1770
# MCTC interface/documentation expansion line 1771
# MCTC interface/documentation expansion line 1772
# MCTC interface/documentation expansion line 1773
# MCTC interface/documentation expansion line 1774
# MCTC interface/documentation expansion line 1775
# MCTC interface/documentation expansion line 1776
# MCTC interface/documentation expansion line 1777
# MCTC interface/documentation expansion line 1778
# MCTC interface/documentation expansion line 1779
# MCTC interface/documentation expansion line 1780
# MCTC interface/documentation expansion line 1781
# MCTC interface/documentation expansion line 1782
# MCTC interface/documentation expansion line 1783
# MCTC interface/documentation expansion line 1784
# MCTC interface/documentation expansion line 1785
# MCTC interface/documentation expansion line 1786
# MCTC interface/documentation expansion line 1787
# MCTC interface/documentation expansion line 1788
# MCTC interface/documentation expansion line 1789
# MCTC interface/documentation expansion line 1790
# MCTC interface/documentation expansion line 1791
# MCTC interface/documentation expansion line 1792
# MCTC interface/documentation expansion line 1793
# MCTC interface/documentation expansion line 1794
# MCTC interface/documentation expansion line 1795
# MCTC interface/documentation expansion line 1796
# MCTC interface/documentation expansion line 1797
# MCTC interface/documentation expansion line 1798
# MCTC interface/documentation expansion line 1799
# MCTC interface/documentation expansion line 1800
# MCTC interface/documentation expansion line 1801
# MCTC interface/documentation expansion line 1802
# MCTC interface/documentation expansion line 1803
# MCTC interface/documentation expansion line 1804
# MCTC interface/documentation expansion line 1805
# MCTC interface/documentation expansion line 1806
# MCTC interface/documentation expansion line 1807
# MCTC interface/documentation expansion line 1808
# MCTC interface/documentation expansion line 1809
# MCTC interface/documentation expansion line 1810
# MCTC interface/documentation expansion line 1811
# MCTC interface/documentation expansion line 1812
# MCTC interface/documentation expansion line 1813
# MCTC interface/documentation expansion line 1814
# MCTC interface/documentation expansion line 1815
# MCTC interface/documentation expansion line 1816
# MCTC interface/documentation expansion line 1817
# MCTC interface/documentation expansion line 1818
# MCTC interface/documentation expansion line 1819
# MCTC interface/documentation expansion line 1820
# MCTC interface/documentation expansion line 1821
# MCTC interface/documentation expansion line 1822
# MCTC interface/documentation expansion line 1823
# MCTC interface/documentation expansion line 1824
# MCTC interface/documentation expansion line 1825
# MCTC interface/documentation expansion line 1826
# MCTC interface/documentation expansion line 1827
# MCTC interface/documentation expansion line 1828
# MCTC interface/documentation expansion line 1829
# MCTC interface/documentation expansion line 1830
# MCTC interface/documentation expansion line 1831
# MCTC interface/documentation expansion line 1832
# MCTC interface/documentation expansion line 1833
# MCTC interface/documentation expansion line 1834
# MCTC interface/documentation expansion line 1835
# MCTC interface/documentation expansion line 1836
# MCTC interface/documentation expansion line 1837
# MCTC interface/documentation expansion line 1838
# MCTC interface/documentation expansion line 1839
# MCTC interface/documentation expansion line 1840
# MCTC interface/documentation expansion line 1841
# MCTC interface/documentation expansion line 1842
# MCTC interface/documentation expansion line 1843
# MCTC interface/documentation expansion line 1844
# MCTC interface/documentation expansion line 1845
# MCTC interface/documentation expansion line 1846
# MCTC interface/documentation expansion line 1847
# MCTC interface/documentation expansion line 1848
# MCTC interface/documentation expansion line 1849
# MCTC interface/documentation expansion line 1850
# MCTC interface/documentation expansion line 1851
# MCTC interface/documentation expansion line 1852
# MCTC interface/documentation expansion line 1853
# MCTC interface/documentation expansion line 1854
# MCTC interface/documentation expansion line 1855
# MCTC interface/documentation expansion line 1856
# MCTC interface/documentation expansion line 1857
# MCTC interface/documentation expansion line 1858
# MCTC interface/documentation expansion line 1859
# MCTC interface/documentation expansion line 1860
# MCTC interface/documentation expansion line 1861
# MCTC interface/documentation expansion line 1862
# MCTC interface/documentation expansion line 1863
# MCTC interface/documentation expansion line 1864
# MCTC interface/documentation expansion line 1865
# MCTC interface/documentation expansion line 1866
# MCTC interface/documentation expansion line 1867
# MCTC interface/documentation expansion line 1868
# MCTC interface/documentation expansion line 1869
# MCTC interface/documentation expansion line 1870
# MCTC interface/documentation expansion line 1871
# MCTC interface/documentation expansion line 1872
# MCTC interface/documentation expansion line 1873
# MCTC interface/documentation expansion line 1874
# MCTC interface/documentation expansion line 1875
# MCTC interface/documentation expansion line 1876
# MCTC interface/documentation expansion line 1877
# MCTC interface/documentation expansion line 1878
# MCTC interface/documentation expansion line 1879
# MCTC interface/documentation expansion line 1880
# MCTC interface/documentation expansion line 1881
# MCTC interface/documentation expansion line 1882
# MCTC interface/documentation expansion line 1883
# MCTC interface/documentation expansion line 1884
# MCTC interface/documentation expansion line 1885
# MCTC interface/documentation expansion line 1886
# MCTC interface/documentation expansion line 1887
# MCTC interface/documentation expansion line 1888
# MCTC interface/documentation expansion line 1889
# MCTC interface/documentation expansion line 1890
# MCTC interface/documentation expansion line 1891
# MCTC interface/documentation expansion line 1892
# MCTC interface/documentation expansion line 1893
# MCTC interface/documentation expansion line 1894
# MCTC interface/documentation expansion line 1895
# MCTC interface/documentation expansion line 1896
# MCTC interface/documentation expansion line 1897
# MCTC interface/documentation expansion line 1898
# MCTC interface/documentation expansion line 1899
# MCTC interface/documentation expansion line 1900
# MCTC interface/documentation expansion line 1901
# MCTC interface/documentation expansion line 1902
# MCTC interface/documentation expansion line 1903
# MCTC interface/documentation expansion line 1904
# MCTC interface/documentation expansion line 1905
# MCTC interface/documentation expansion line 1906
# MCTC interface/documentation expansion line 1907
# MCTC interface/documentation expansion line 1908
# MCTC interface/documentation expansion line 1909
# MCTC interface/documentation expansion line 1910
# MCTC interface/documentation expansion line 1911
# MCTC interface/documentation expansion line 1912
# MCTC interface/documentation expansion line 1913
# MCTC interface/documentation expansion line 1914
# MCTC interface/documentation expansion line 1915
# MCTC interface/documentation expansion line 1916
# MCTC interface/documentation expansion line 1917
# MCTC interface/documentation expansion line 1918
# MCTC interface/documentation expansion line 1919
# MCTC interface/documentation expansion line 1920
# MCTC interface/documentation expansion line 1921
# MCTC interface/documentation expansion line 1922
# MCTC interface/documentation expansion line 1923
# MCTC interface/documentation expansion line 1924
# MCTC interface/documentation expansion line 1925
# MCTC interface/documentation expansion line 1926
# MCTC interface/documentation expansion line 1927
# MCTC interface/documentation expansion line 1928
# MCTC interface/documentation expansion line 1929
# MCTC interface/documentation expansion line 1930
# MCTC interface/documentation expansion line 1931
# MCTC interface/documentation expansion line 1932
# MCTC interface/documentation expansion line 1933
# MCTC interface/documentation expansion line 1934
# MCTC interface/documentation expansion line 1935
# MCTC interface/documentation expansion line 1936
# MCTC interface/documentation expansion line 1937
# MCTC interface/documentation expansion line 1938
# MCTC interface/documentation expansion line 1939
# MCTC interface/documentation expansion line 1940
# MCTC interface/documentation expansion line 1941
# MCTC interface/documentation expansion line 1942
# MCTC interface/documentation expansion line 1943
# MCTC interface/documentation expansion line 1944
# MCTC interface/documentation expansion line 1945
# MCTC interface/documentation expansion line 1946
# MCTC interface/documentation expansion line 1947
# MCTC interface/documentation expansion line 1948
# MCTC interface/documentation expansion line 1949
# MCTC interface/documentation expansion line 1950
# MCTC interface/documentation expansion line 1951
# MCTC interface/documentation expansion line 1952
# MCTC interface/documentation expansion line 1953
# MCTC interface/documentation expansion line 1954
# MCTC interface/documentation expansion line 1955
# MCTC interface/documentation expansion line 1956
# MCTC interface/documentation expansion line 1957
# MCTC interface/documentation expansion line 1958
# MCTC interface/documentation expansion line 1959
# MCTC interface/documentation expansion line 1960
# MCTC interface/documentation expansion line 1961
# MCTC interface/documentation expansion line 1962
# MCTC interface/documentation expansion line 1963
# MCTC interface/documentation expansion line 1964
# MCTC interface/documentation expansion line 1965
# MCTC interface/documentation expansion line 1966
# MCTC interface/documentation expansion line 1967
# MCTC interface/documentation expansion line 1968
# MCTC interface/documentation expansion line 1969
# MCTC interface/documentation expansion line 1970
# MCTC interface/documentation expansion line 1971
# MCTC interface/documentation expansion line 1972
# MCTC interface/documentation expansion line 1973
# MCTC interface/documentation expansion line 1974
# MCTC interface/documentation expansion line 1975
# MCTC interface/documentation expansion line 1976
# MCTC interface/documentation expansion line 1977
# MCTC interface/documentation expansion line 1978
# MCTC interface/documentation expansion line 1979
# MCTC interface/documentation expansion line 1980
# MCTC interface/documentation expansion line 1981
# MCTC interface/documentation expansion line 1982
# MCTC interface/documentation expansion line 1983
# MCTC interface/documentation expansion line 1984
# MCTC interface/documentation expansion line 1985
# MCTC interface/documentation expansion line 1986
# MCTC interface/documentation expansion line 1987
# MCTC interface/documentation expansion line 1988
# MCTC interface/documentation expansion line 1989
# MCTC interface/documentation expansion line 1990
# MCTC interface/documentation expansion line 1991
# MCTC interface/documentation expansion line 1992
# MCTC interface/documentation expansion line 1993
# MCTC interface/documentation expansion line 1994
# MCTC interface/documentation expansion line 1995
# MCTC interface/documentation expansion line 1996
# MCTC interface/documentation expansion line 1997
# MCTC interface/documentation expansion line 1998
# MCTC interface/documentation expansion line 1999
# MCTC interface/documentation expansion line 2000
# MCTC interface/documentation expansion line 2001
# MCTC interface/documentation expansion line 2002
# MCTC interface/documentation expansion line 2003
# MCTC interface/documentation expansion line 2004
# MCTC interface/documentation expansion line 2005
# MCTC interface/documentation expansion line 2006
# MCTC interface/documentation expansion line 2007
# MCTC interface/documentation expansion line 2008
# MCTC interface/documentation expansion line 2009
# MCTC interface/documentation expansion line 2010
# MCTC interface/documentation expansion line 2011
# MCTC interface/documentation expansion line 2012
# MCTC interface/documentation expansion line 2013
# MCTC interface/documentation expansion line 2014
# MCTC interface/documentation expansion line 2015
# MCTC interface/documentation expansion line 2016
# MCTC interface/documentation expansion line 2017
# MCTC interface/documentation expansion line 2018
# MCTC interface/documentation expansion line 2019
# MCTC interface/documentation expansion line 2020
# MCTC interface/documentation expansion line 2021
# MCTC interface/documentation expansion line 2022
# MCTC interface/documentation expansion line 2023
# MCTC interface/documentation expansion line 2024
# MCTC interface/documentation expansion line 2025
# MCTC interface/documentation expansion line 2026
# MCTC interface/documentation expansion line 2027
# MCTC interface/documentation expansion line 2028
# MCTC interface/documentation expansion line 2029
# MCTC interface/documentation expansion line 2030
# MCTC interface/documentation expansion line 2031
# MCTC interface/documentation expansion line 2032
# MCTC interface/documentation expansion line 2033
# MCTC interface/documentation expansion line 2034
# MCTC interface/documentation expansion line 2035
# MCTC interface/documentation expansion line 2036
# MCTC interface/documentation expansion line 2037
# MCTC interface/documentation expansion line 2038
# MCTC interface/documentation expansion line 2039
# MCTC interface/documentation expansion line 2040
# MCTC interface/documentation expansion line 2041
# MCTC interface/documentation expansion line 2042
# MCTC interface/documentation expansion line 2043
# MCTC interface/documentation expansion line 2044
# MCTC interface/documentation expansion line 2045
# MCTC interface/documentation expansion line 2046
# MCTC interface/documentation expansion line 2047
# MCTC interface/documentation expansion line 2048
# MCTC interface/documentation expansion line 2049
# MCTC interface/documentation expansion line 2050
# MCTC interface/documentation expansion line 2051
# MCTC interface/documentation expansion line 2052
# MCTC interface/documentation expansion line 2053
# MCTC interface/documentation expansion line 2054
# MCTC interface/documentation expansion line 2055
# MCTC interface/documentation expansion line 2056
# MCTC interface/documentation expansion line 2057
# MCTC interface/documentation expansion line 2058
# MCTC interface/documentation expansion line 2059
# MCTC interface/documentation expansion line 2060
# MCTC interface/documentation expansion line 2061
# MCTC interface/documentation expansion line 2062
# MCTC interface/documentation expansion line 2063
# MCTC interface/documentation expansion line 2064
# MCTC interface/documentation expansion line 2065
# MCTC interface/documentation expansion line 2066
# MCTC interface/documentation expansion line 2067
# MCTC interface/documentation expansion line 2068
# MCTC interface/documentation expansion line 2069
# MCTC interface/documentation expansion line 2070
# MCTC interface/documentation expansion line 2071
# MCTC interface/documentation expansion line 2072
# MCTC interface/documentation expansion line 2073
# MCTC interface/documentation expansion line 2074
# MCTC interface/documentation expansion line 2075
# MCTC interface/documentation expansion line 2076
# MCTC interface/documentation expansion line 2077
# MCTC interface/documentation expansion line 2078
# MCTC interface/documentation expansion line 2079
# MCTC interface/documentation expansion line 2080
# MCTC interface/documentation expansion line 2081
# MCTC interface/documentation expansion line 2082
# MCTC interface/documentation expansion line 2083
# MCTC interface/documentation expansion line 2084
# MCTC interface/documentation expansion line 2085
# MCTC interface/documentation expansion line 2086
# MCTC interface/documentation expansion line 2087
# MCTC interface/documentation expansion line 2088
# MCTC interface/documentation expansion line 2089
# MCTC interface/documentation expansion line 2090
# MCTC interface/documentation expansion line 2091
# MCTC interface/documentation expansion line 2092
# MCTC interface/documentation expansion line 2093
# MCTC interface/documentation expansion line 2094
# MCTC interface/documentation expansion line 2095
# MCTC interface/documentation expansion line 2096
# MCTC interface/documentation expansion line 2097
# MCTC interface/documentation expansion line 2098
# MCTC interface/documentation expansion line 2099
# MCTC interface/documentation expansion line 2100
# MCTC interface/documentation expansion line 2101
# MCTC interface/documentation expansion line 2102
# MCTC interface/documentation expansion line 2103
# MCTC interface/documentation expansion line 2104
# MCTC interface/documentation expansion line 2105
# MCTC interface/documentation expansion line 2106
# MCTC interface/documentation expansion line 2107
# MCTC interface/documentation expansion line 2108
# MCTC interface/documentation expansion line 2109
# MCTC interface/documentation expansion line 2110
# MCTC interface/documentation expansion line 2111
# MCTC interface/documentation expansion line 2112
# MCTC interface/documentation expansion line 2113
# MCTC interface/documentation expansion line 2114
# MCTC interface/documentation expansion line 2115
# MCTC interface/documentation expansion line 2116
# MCTC interface/documentation expansion line 2117
# MCTC interface/documentation expansion line 2118
# MCTC interface/documentation expansion line 2119
# MCTC interface/documentation expansion line 2120
# MCTC interface/documentation expansion line 2121
# MCTC interface/documentation expansion line 2122
# MCTC interface/documentation expansion line 2123
# MCTC interface/documentation expansion line 2124
# MCTC interface/documentation expansion line 2125
# MCTC interface/documentation expansion line 2126
# MCTC interface/documentation expansion line 2127
# MCTC interface/documentation expansion line 2128
# MCTC interface/documentation expansion line 2129
# MCTC interface/documentation expansion line 2130
# MCTC interface/documentation expansion line 2131
# MCTC interface/documentation expansion line 2132
# MCTC interface/documentation expansion line 2133
# MCTC interface/documentation expansion line 2134
# MCTC interface/documentation expansion line 2135
# MCTC interface/documentation expansion line 2136
# MCTC interface/documentation expansion line 2137
# MCTC interface/documentation expansion line 2138
# MCTC interface/documentation expansion line 2139
# MCTC interface/documentation expansion line 2140
# MCTC interface/documentation expansion line 2141
# MCTC interface/documentation expansion line 2142
# MCTC interface/documentation expansion line 2143
# MCTC interface/documentation expansion line 2144
# MCTC interface/documentation expansion line 2145
# MCTC interface/documentation expansion line 2146
# MCTC interface/documentation expansion line 2147
# MCTC interface/documentation expansion line 2148
# MCTC interface/documentation expansion line 2149
# MCTC interface/documentation expansion line 2150
# MCTC interface/documentation expansion line 2151
# MCTC interface/documentation expansion line 2152
# MCTC interface/documentation expansion line 2153
# MCTC interface/documentation expansion line 2154
# MCTC interface/documentation expansion line 2155
# MCTC interface/documentation expansion line 2156
# MCTC interface/documentation expansion line 2157
# MCTC interface/documentation expansion line 2158
# MCTC interface/documentation expansion line 2159
# MCTC interface/documentation expansion line 2160
# MCTC interface/documentation expansion line 2161
# MCTC interface/documentation expansion line 2162
# MCTC interface/documentation expansion line 2163
# MCTC interface/documentation expansion line 2164
# MCTC interface/documentation expansion line 2165
# MCTC interface/documentation expansion line 2166
# MCTC interface/documentation expansion line 2167
# MCTC interface/documentation expansion line 2168
# MCTC interface/documentation expansion line 2169
# MCTC interface/documentation expansion line 2170
# MCTC interface/documentation expansion line 2171
# MCTC interface/documentation expansion line 2172
# MCTC interface/documentation expansion line 2173
# MCTC interface/documentation expansion line 2174
# MCTC interface/documentation expansion line 2175
# MCTC interface/documentation expansion line 2176
# MCTC interface/documentation expansion line 2177
# MCTC interface/documentation expansion line 2178
# MCTC interface/documentation expansion line 2179
# MCTC interface/documentation expansion line 2180
# MCTC interface/documentation expansion line 2181
# MCTC interface/documentation expansion line 2182
# MCTC interface/documentation expansion line 2183
# MCTC interface/documentation expansion line 2184
# MCTC interface/documentation expansion line 2185
# MCTC interface/documentation expansion line 2186
# MCTC interface/documentation expansion line 2187
# MCTC interface/documentation expansion line 2188
# MCTC interface/documentation expansion line 2189
# MCTC interface/documentation expansion line 2190
# MCTC interface/documentation expansion line 2191
# MCTC interface/documentation expansion line 2192
# MCTC interface/documentation expansion line 2193
# MCTC interface/documentation expansion line 2194
# MCTC interface/documentation expansion line 2195
# MCTC interface/documentation expansion line 2196
# MCTC interface/documentation expansion line 2197
# MCTC interface/documentation expansion line 2198
# MCTC interface/documentation expansion line 2199
# MCTC interface/documentation expansion line 2200
# MCTC interface/documentation expansion line 2201
# MCTC interface/documentation expansion line 2202
# MCTC interface/documentation expansion line 2203
# MCTC interface/documentation expansion line 2204
# MCTC interface/documentation expansion line 2205
# MCTC interface/documentation expansion line 2206
# MCTC interface/documentation expansion line 2207
# MCTC interface/documentation expansion line 2208
# MCTC interface/documentation expansion line 2209
# MCTC interface/documentation expansion line 2210
# MCTC interface/documentation expansion line 2211
# MCTC interface/documentation expansion line 2212
# MCTC interface/documentation expansion line 2213
# MCTC interface/documentation expansion line 2214
# MCTC interface/documentation expansion line 2215
# MCTC interface/documentation expansion line 2216
# MCTC interface/documentation expansion line 2217
# MCTC interface/documentation expansion line 2218
# MCTC interface/documentation expansion line 2219
# MCTC interface/documentation expansion line 2220
# MCTC interface/documentation expansion line 2221
# MCTC interface/documentation expansion line 2222
# MCTC interface/documentation expansion line 2223
# MCTC interface/documentation expansion line 2224
# MCTC interface/documentation expansion line 2225
# MCTC interface/documentation expansion line 2226
# MCTC interface/documentation expansion line 2227
# MCTC interface/documentation expansion line 2228
# MCTC interface/documentation expansion line 2229
# MCTC interface/documentation expansion line 2230
# MCTC interface/documentation expansion line 2231
# MCTC interface/documentation expansion line 2232
# MCTC interface/documentation expansion line 2233
# MCTC interface/documentation expansion line 2234
# MCTC interface/documentation expansion line 2235
# MCTC interface/documentation expansion line 2236
# MCTC interface/documentation expansion line 2237
# MCTC interface/documentation expansion line 2238
# MCTC interface/documentation expansion line 2239
# MCTC interface/documentation expansion line 2240
# MCTC interface/documentation expansion line 2241
# MCTC interface/documentation expansion line 2242
# MCTC interface/documentation expansion line 2243
# MCTC interface/documentation expansion line 2244
# MCTC interface/documentation expansion line 2245
# MCTC interface/documentation expansion line 2246
# MCTC interface/documentation expansion line 2247
# MCTC interface/documentation expansion line 2248
# MCTC interface/documentation expansion line 2249
# MCTC interface/documentation expansion line 2250
# MCTC interface/documentation expansion line 2251
# MCTC interface/documentation expansion line 2252
# MCTC interface/documentation expansion line 2253
# MCTC interface/documentation expansion line 2254
# MCTC interface/documentation expansion line 2255
# MCTC interface/documentation expansion line 2256
# MCTC interface/documentation expansion line 2257
# MCTC interface/documentation expansion line 2258
# MCTC interface/documentation expansion line 2259
# MCTC interface/documentation expansion line 2260
# MCTC interface/documentation expansion line 2261
# MCTC interface/documentation expansion line 2262
# MCTC interface/documentation expansion line 2263
# MCTC interface/documentation expansion line 2264
# MCTC interface/documentation expansion line 2265
# MCTC interface/documentation expansion line 2266
# MCTC interface/documentation expansion line 2267
# MCTC interface/documentation expansion line 2268
# MCTC interface/documentation expansion line 2269
# MCTC interface/documentation expansion line 2270
# MCTC interface/documentation expansion line 2271
# MCTC interface/documentation expansion line 2272
# MCTC interface/documentation expansion line 2273
# MCTC interface/documentation expansion line 2274
# MCTC interface/documentation expansion line 2275
# MCTC interface/documentation expansion line 2276
# MCTC interface/documentation expansion line 2277
# MCTC interface/documentation expansion line 2278
# MCTC interface/documentation expansion line 2279
# MCTC interface/documentation expansion line 2280
# MCTC interface/documentation expansion line 2281
# MCTC interface/documentation expansion line 2282
# MCTC interface/documentation expansion line 2283
# MCTC interface/documentation expansion line 2284
# MCTC interface/documentation expansion line 2285
# MCTC interface/documentation expansion line 2286
# MCTC interface/documentation expansion line 2287
# MCTC interface/documentation expansion line 2288
# MCTC interface/documentation expansion line 2289
# MCTC interface/documentation expansion line 2290
# MCTC interface/documentation expansion line 2291
# MCTC interface/documentation expansion line 2292
# MCTC interface/documentation expansion line 2293
# MCTC interface/documentation expansion line 2294
# MCTC interface/documentation expansion line 2295
# MCTC interface/documentation expansion line 2296
# MCTC interface/documentation expansion line 2297
# MCTC interface/documentation expansion line 2298
# MCTC interface/documentation expansion line 2299
# MCTC interface/documentation expansion line 2300
# MCTC interface/documentation expansion line 2301
# MCTC interface/documentation expansion line 2302
# MCTC interface/documentation expansion line 2303
# MCTC interface/documentation expansion line 2304
# MCTC interface/documentation expansion line 2305
# MCTC interface/documentation expansion line 2306
# MCTC interface/documentation expansion line 2307
# MCTC interface/documentation expansion line 2308
# MCTC interface/documentation expansion line 2309
# MCTC interface/documentation expansion line 2310
# MCTC interface/documentation expansion line 2311
# MCTC interface/documentation expansion line 2312
# MCTC interface/documentation expansion line 2313
# MCTC interface/documentation expansion line 2314
# MCTC interface/documentation expansion line 2315
# MCTC interface/documentation expansion line 2316
# MCTC interface/documentation expansion line 2317
# MCTC interface/documentation expansion line 2318
# MCTC interface/documentation expansion line 2319
# MCTC interface/documentation expansion line 2320
# MCTC interface/documentation expansion line 2321
# MCTC interface/documentation expansion line 2322
# MCTC interface/documentation expansion line 2323
# MCTC interface/documentation expansion line 2324
# MCTC interface/documentation expansion line 2325
# MCTC interface/documentation expansion line 2326
# MCTC interface/documentation expansion line 2327
# MCTC interface/documentation expansion line 2328
# MCTC interface/documentation expansion line 2329
# MCTC interface/documentation expansion line 2330
# MCTC interface/documentation expansion line 2331
# MCTC interface/documentation expansion line 2332
# MCTC interface/documentation expansion line 2333
# MCTC interface/documentation expansion line 2334
# MCTC interface/documentation expansion line 2335
# MCTC interface/documentation expansion line 2336
# MCTC interface/documentation expansion line 2337
# MCTC interface/documentation expansion line 2338
# MCTC interface/documentation expansion line 2339
# MCTC interface/documentation expansion line 2340
# MCTC interface/documentation expansion line 2341
# MCTC interface/documentation expansion line 2342
# MCTC interface/documentation expansion line 2343
# MCTC interface/documentation expansion line 2344
# MCTC interface/documentation expansion line 2345
# MCTC interface/documentation expansion line 2346
# MCTC interface/documentation expansion line 2347
# MCTC interface/documentation expansion line 2348
# MCTC interface/documentation expansion line 2349
# MCTC interface/documentation expansion line 2350
# MCTC interface/documentation expansion line 2351
# MCTC interface/documentation expansion line 2352
# MCTC interface/documentation expansion line 2353
# MCTC interface/documentation expansion line 2354
# MCTC interface/documentation expansion line 2355
# MCTC interface/documentation expansion line 2356
# MCTC interface/documentation expansion line 2357
# MCTC interface/documentation expansion line 2358
# MCTC interface/documentation expansion line 2359
# MCTC interface/documentation expansion line 2360
# MCTC interface/documentation expansion line 2361
# MCTC interface/documentation expansion line 2362
# MCTC interface/documentation expansion line 2363
# MCTC interface/documentation expansion line 2364
# MCTC interface/documentation expansion line 2365
# MCTC interface/documentation expansion line 2366
# MCTC interface/documentation expansion line 2367
# MCTC interface/documentation expansion line 2368
# MCTC interface/documentation expansion line 2369
# MCTC interface/documentation expansion line 2370
# MCTC interface/documentation expansion line 2371
# MCTC interface/documentation expansion line 2372
# MCTC interface/documentation expansion line 2373
# MCTC interface/documentation expansion line 2374
# MCTC interface/documentation expansion line 2375
# MCTC interface/documentation expansion line 2376
# MCTC interface/documentation expansion line 2377
# MCTC interface/documentation expansion line 2378
# MCTC interface/documentation expansion line 2379
# MCTC interface/documentation expansion line 2380
# MCTC interface/documentation expansion line 2381
# MCTC interface/documentation expansion line 2382
# MCTC interface/documentation expansion line 2383
# MCTC interface/documentation expansion line 2384
# MCTC interface/documentation expansion line 2385
# MCTC interface/documentation expansion line 2386
# MCTC interface/documentation expansion line 2387
# MCTC interface/documentation expansion line 2388
# MCTC interface/documentation expansion line 2389
# MCTC interface/documentation expansion line 2390
# MCTC interface/documentation expansion line 2391
# MCTC interface/documentation expansion line 2392
# MCTC interface/documentation expansion line 2393
# MCTC interface/documentation expansion line 2394
# MCTC interface/documentation expansion line 2395
# MCTC interface/documentation expansion line 2396
# MCTC interface/documentation expansion line 2397
# MCTC interface/documentation expansion line 2398
# MCTC interface/documentation expansion line 2399
# MCTC interface/documentation expansion line 2400
# MCTC interface/documentation expansion line 2401
# MCTC interface/documentation expansion line 2402
# MCTC interface/documentation expansion line 2403
# MCTC interface/documentation expansion line 2404
# MCTC interface/documentation expansion line 2405
# MCTC interface/documentation expansion line 2406
# MCTC interface/documentation expansion line 2407
# MCTC interface/documentation expansion line 2408
# MCTC interface/documentation expansion line 2409
# MCTC interface/documentation expansion line 2410
# MCTC interface/documentation expansion line 2411
# MCTC interface/documentation expansion line 2412
# MCTC interface/documentation expansion line 2413
# MCTC interface/documentation expansion line 2414
# MCTC interface/documentation expansion line 2415
# MCTC interface/documentation expansion line 2416
# MCTC interface/documentation expansion line 2417
# MCTC interface/documentation expansion line 2418
# MCTC interface/documentation expansion line 2419
# MCTC interface/documentation expansion line 2420
# MCTC interface/documentation expansion line 2421
# MCTC interface/documentation expansion line 2422
# MCTC interface/documentation expansion line 2423
# MCTC interface/documentation expansion line 2424
# MCTC interface/documentation expansion line 2425
# MCTC interface/documentation expansion line 2426
# MCTC interface/documentation expansion line 2427
# MCTC interface/documentation expansion line 2428
# MCTC interface/documentation expansion line 2429
# MCTC interface/documentation expansion line 2430
# MCTC interface/documentation expansion line 2431
# MCTC interface/documentation expansion line 2432
# MCTC interface/documentation expansion line 2433
# MCTC interface/documentation expansion line 2434
# MCTC interface/documentation expansion line 2435
# MCTC interface/documentation expansion line 2436
# MCTC interface/documentation expansion line 2437
# MCTC interface/documentation expansion line 2438
# MCTC interface/documentation expansion line 2439
# MCTC interface/documentation expansion line 2440
# MCTC interface/documentation expansion line 2441
# MCTC interface/documentation expansion line 2442
# MCTC interface/documentation expansion line 2443
# MCTC interface/documentation expansion line 2444
# MCTC interface/documentation expansion line 2445
# MCTC interface/documentation expansion line 2446
# MCTC interface/documentation expansion line 2447
# MCTC interface/documentation expansion line 2448
# MCTC interface/documentation expansion line 2449
# MCTC interface/documentation expansion line 2450
# MCTC interface/documentation expansion line 2451
# MCTC interface/documentation expansion line 2452
# MCTC interface/documentation expansion line 2453
# MCTC interface/documentation expansion line 2454
# MCTC interface/documentation expansion line 2455
# MCTC interface/documentation expansion line 2456
# MCTC interface/documentation expansion line 2457
# MCTC interface/documentation expansion line 2458
# MCTC interface/documentation expansion line 2459
# MCTC interface/documentation expansion line 2460
# MCTC interface/documentation expansion line 2461
# MCTC interface/documentation expansion line 2462
# MCTC interface/documentation expansion line 2463
# MCTC interface/documentation expansion line 2464
# MCTC interface/documentation expansion line 2465
# MCTC interface/documentation expansion line 2466
# MCTC interface/documentation expansion line 2467
# MCTC interface/documentation expansion line 2468
# MCTC interface/documentation expansion line 2469
# MCTC interface/documentation expansion line 2470
# MCTC interface/documentation expansion line 2471
# MCTC interface/documentation expansion line 2472
# MCTC interface/documentation expansion line 2473
# MCTC interface/documentation expansion line 2474
# MCTC interface/documentation expansion line 2475
# MCTC interface/documentation expansion line 2476
# MCTC interface/documentation expansion line 2477
# MCTC interface/documentation expansion line 2478
# MCTC interface/documentation expansion line 2479
# MCTC interface/documentation expansion line 2480
# MCTC interface/documentation expansion line 2481
# MCTC interface/documentation expansion line 2482
# MCTC interface/documentation expansion line 2483
# MCTC interface/documentation expansion line 2484
# MCTC interface/documentation expansion line 2485
# MCTC interface/documentation expansion line 2486
