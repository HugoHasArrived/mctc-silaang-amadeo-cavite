import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    abort,
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# MCTC SILANG-AMADEO, CAVITE
# COURT INFORMATION WEBSITE
# ============================================================
#
# This application provides:
#
#   Public:
#       - Case searching
#       - Tuesday calendar
#       - Public notices
#       - Public documents
#       - Bond requirements
#       - Clearance requirements
#       - Legal resources
#       - Court information
#       - English / Filipino
#       - Light / dark mode
#
#   Staff:
#       - Login
#       - Case management
#       - Calendar management
#       - Notice management
#       - Document management
#       - Legal resource management
#       - Uploads
#       - Delete cases
#       - Logout
#
# ============================================================


# ------------------------------------------------------------
# APPLICATION
# ------------------------------------------------------------

app = Flask(__name__)

# IMPORTANT:
# On Render, create an environment variable called SECRET_KEY.
#
# For local development the fallback below is acceptable.
# For production, always use a Render environment variable.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32),
)


# ------------------------------------------------------------
# COURT INFORMATION
# ------------------------------------------------------------

COURT_NAME = "Municipal Circuit Trial Court of Silang-Amadeo, Cavite"

COURT_ADDRESS_1 = "PNP Bldg, Plaza Libertad, Poblacion 2"
COURT_ADDRESS_2 = "Silang, Cavite"

COURT_PHONE = "09284621305"

LOGO_FILENAME = "image0.png"


# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "mctc.db",
)


# ------------------------------------------------------------
# UPLOAD CONFIGURATION
# ------------------------------------------------------------

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads",
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True,
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "doc",
    "docx",
}


# ------------------------------------------------------------
# DATABASE CONNECTION
# ------------------------------------------------------------

def get_db():
    """
    Open a SQLite connection.
    """

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ------------------------------------------------------------
# DATABASE INITIALIZATION
# ------------------------------------------------------------

def init_db():
    """
    Create all tables required by the application.
    """

    db = get_db()

    # --------------------------------------------------------
    # STAFF
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # CASES
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            party_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            case_title TEXT,
            case_type TEXT,
            case_status TEXT,
            hearing_date TEXT,
            hearing_time TEXT,
            judge TEXT,
            description TEXT,
            public_information TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # CASE DOCUMENTS
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS case_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            is_public INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(case_id) REFERENCES cases(id)
        )
        """
    )

    # --------------------------------------------------------
    # NOTICES
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            filename TEXT,
            published INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # TUESDAY CALENDAR
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendar_date TEXT NOT NULL,
            calendar_time TEXT NOT NULL,
            case_number TEXT,
            party_name TEXT,
            proceeding TEXT,
            room TEXT,
            status TEXT,
            public_notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # LEGAL RESOURCES
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS legal_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            source_url TEXT,
            publication_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # REQUIREMENTS
    # --------------------------------------------------------

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_type TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            filename TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # CREATE DEFAULT REQUIREMENTS
    # --------------------------------------------------------

    for requirement_type, title in [
        (
            "bond",
            "Requirements for Bonds",
        ),
        (
            "clearance",
            "Requirements for Clearance",
        ),
    ]:

        existing = db.execute(
            """
            SELECT id
            FROM requirements
            WHERE requirement_type = ?
            """,
            (requirement_type,),
        ).fetchone()

        if existing is None:

            db.execute(
                """
                INSERT INTO requirements
                (
                    requirement_type,
                    title,
                    body,
                    filename,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    requirement_type,
                    title,
                    "Not yet uploaded.",
                    None,
                    now(),
                ),
            )

    # --------------------------------------------------------
    # DEFAULT STAFF ACCOUNT
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Do not put a real court password here.
    #
    # Set these Render environment variables:
    #
    # STAFF_USERNAME
    # STAFF_PASSWORD
    #
    # The account is created automatically the first time
    # the application starts.
    #
    # --------------------------------------------------------

    username = os.environ.get(
        "STAFF_USERNAME"
    )

    password = os.environ.get(
        "STAFF_PASSWORD"
    )

    if username and password:

        existing = db.execute(
            """
            SELECT id
            FROM staff
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if existing is None:

            db.execute(
                """
                INSERT INTO staff
                (
                    username,
                    password_hash,
                    display_name,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    generate_password_hash(password),
                    "Court Staff",
                    now(),
                ),
            )

    db.commit()

    db.close()


# ------------------------------------------------------------
# TIME
# ------------------------------------------------------------

def now():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ------------------------------------------------------------
# FILE VALIDATION
# ------------------------------------------------------------

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ------------------------------------------------------------
# STAFF AUTHENTICATION
# ------------------------------------------------------------

def staff_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        if not session.get("staff_id"):

            flash(
                "Please log in as court staff first.",
                "warning",
            )

            return redirect(
                url_for("staff_login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated


# ------------------------------------------------------------
# LANGUAGE
# ------------------------------------------------------------

@app.context_processor
def inject_global_data():

    language = session.get(
        "language",
        "en",
    )

    theme = session.get(
        "theme",
        "light",
    )

    return {
        "language": language,
        "theme": theme,
        "court_name": COURT_NAME,
        "court_address_1": COURT_ADDRESS_1,
        "court_address_2": COURT_ADDRESS_2,
        "court_phone": COURT_PHONE,
        "logo_filename": LOGO_FILENAME,
        "staff_logged_in": bool(
            session.get("staff_id")
        ),
    }


# ------------------------------------------------------------
# LANGUAGE ROUTE
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# THEME ROUTE
# ------------------------------------------------------------

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
# PUBLIC PAGES
# ============================================================


# ------------------------------------------------------------
# HOME
# ------------------------------------------------------------

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

    return render_template(
        "index.html",
        notices=notices,
    )


# ------------------------------------------------------------
# SEARCH PAGE
# ------------------------------------------------------------

@app.route(
    "/search",
    methods=[
        "GET",
        "POST",
    ],
)
def search_cases():

    case = None

    searched = False

    if request.method == "POST":

        searched = True

        case_number = (
            request.form.get(
                "case_number",
                "",
            )
            .strip()
        )

        last_name = (
            request.form.get(
                "last_name",
                "",
            )
            .strip()
        )

        # BOTH fields are mandatory.
        if not case_number or not last_name:

            flash(
                "Both the case number and last name / party name are required.",
                "danger",
            )

            return render_template(
                "search.html",
                case=None,
                searched=searched,
            )

        db = get_db()

        case = db.execute(
            """
            SELECT *
            FROM cases
            WHERE LOWER(case_number) = LOWER(?)
            AND LOWER(last_name) = LOWER(?)
            """,
            (
                case_number,
                last_name,
            ),
        ).fetchone()

        db.close()

        if case is None:

            flash(
                "No public case record matched both pieces of information.",
                "warning",
            )

    return render_template(
        "search.html",
        case=case,
        searched=searched,
    )


# ------------------------------------------------------------
# CASE DETAILS
# ------------------------------------------------------------

@app.route(
    "/case/<int:case_id>"
)
def case_details(case_id):

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

    documents = db.execute(
        """
        SELECT *
        FROM case_documents
        WHERE case_id = ?
        AND is_public = 1
        ORDER BY uploaded_at DESC
        """,
        (case_id,),
    ).fetchall()

    db.close()

    return render_template(
        "case.html",
        case=case,
        documents=documents,
    )


# ------------------------------------------------------------
# TUESDAY CALENDAR
# ------------------------------------------------------------

@app.route(
    "/calendar"
)
def public_calendar():

    db = get_db()

    entries = db.execute(
        """
        SELECT *
        FROM calendar_entries
        ORDER BY calendar_date ASC,
                 calendar_time ASC
        """
    ).fetchall()

    db.close()

    return render_template(
        "calendar.html",
        entries=entries,
    )


# ------------------------------------------------------------
# PUBLIC NOTICES
# ------------------------------------------------------------

@app.route(
    "/notices"
)
def public_notices():

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

    return render_template(
        "notices.html",
        notices=notices,
    )


# ------------------------------------------------------------
# BOND REQUIREMENTS
# ------------------------------------------------------------

@app.route(
    "/bonds"
)
def bonds():

    db = get_db()

    requirement = db.execute(
        """
        SELECT *
        FROM requirements
        WHERE requirement_type = 'bond'
        """
    ).fetchone()

    db.close()

    return render_template(
        "bonds.html",
        requirement=requirement,
    )


# ------------------------------------------------------------
# CLEARANCE REQUIREMENTS
# ------------------------------------------------------------

@app.route(
    "/clearance"
)
def clearance():

    db = get_db()

    requirement = db.execute(
        """
        SELECT *
        FROM requirements
        WHERE requirement_type = 'clearance'
        """
    ).fetchone()

    db.close()

    return render_template(
        "clearance.html",
        requirement=requirement,
    )


# ------------------------------------------------------------
# LEGAL RESOURCES
# ------------------------------------------------------------

@app.route(
    "/laws"
)
def laws():

    db = get_db()

    resources = db.execute(
        """
        SELECT *
        FROM legal_resources
        ORDER BY category ASC,
                 publication_date DESC
        """
    ).fetchall()

    db.close()

    return render_template(
        "laws.html",
        resources=resources,
    )


# ------------------------------------------------------------
# COURT INFORMATION
# ------------------------------------------------------------

@app.route(
    "/contact"
)
def contact():

    return render_template(
        "contact.html"
    )


# ============================================================
# STAFF LOGIN / LOGOUT
# ============================================================


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.route(
    "/staff/login",
    methods=[
        "GET",
        "POST",
    ],
)
def staff_login():

    # If already logged in, go directly to dashboard.
    if session.get("staff_id"):

        return redirect(
            url_for("staff_dashboard")
        )

    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                "",
            )
            .strip()
        )

        password = request.form.get(
            "password",
            "",
        )

        if not username or not password:

            flash(
                "Please enter your staff login information.",
                "danger",
            )

            return render_template(
                "login.html"
            )

        db = get_db()

        staff = db.execute(
            """
            SELECT *
            FROM staff
            WHERE username = ?
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

            # Clear any previous session.
            session.clear()

            # Start a fresh authenticated session.
            session["staff_id"] = staff["id"]

            session["staff_name"] = (
                staff["display_name"]
            )

            session["language"] = "en"
            session["theme"] = "light"

            flash(
                "Welcome to the staff portal.",
                "success",
            )

            return redirect(
                url_for("staff_dashboard")
            )

        flash(
            "Invalid staff login.",
            "danger",
        )

    return render_template(
        "login.html"
    )


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------

@app.route(
    "/staff/logout",
    methods=[
        "GET",
        "POST",
    ],
)
def staff_logout():

    # Completely remove authentication session.
    session.clear()

    flash(
        "You have been logged out.",
        "success",
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route(
    "/staff"
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
        FROM calendar_entries
        """
    ).fetchone()[0]

    document_count = db.execute(
        """
        SELECT COUNT(*)
        FROM case_documents
        """
    ).fetchone()[0]

    db.close()

    return render_template(
        "staff.html",
        case_count=case_count,
        notice_count=notice_count,
        calendar_count=calendar_count,
        document_count=document_count,
    )


# ============================================================
# STAFF CASE MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# CASE LIST
# ------------------------------------------------------------

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

    return render_template(
        "staff_cases.html",
        cases=cases,
    )


# ------------------------------------------------------------
# ADD CASE
# ------------------------------------------------------------

@app.route(
    "/staff/cases/new",
    methods=[
        "GET",
        "POST",
    ],
)
@staff_required
def staff_new_case():

    if request.method == "POST":

        case_number = (
            request.form.get(
                "case_number",
                "",
            )
            .strip()
        )

        party_name = (
            request.form.get(
                "party_name",
                "",
            )
            .strip()
        )

        last_name = (
            request.form.get(
                "last_name",
                "",
            )
            .strip()
        )

        case_title = (
            request.form.get(
                "case_title",
                "",
            )
            .strip()
        )

        case_type = (
            request.form.get(
                "case_type",
                "",
            )
            .strip()
        )

        case_status = (
            request.form.get(
                "case_status",
                "",
            )
            .strip()
        )

        hearing_date = (
            request.form.get(
                "hearing_date",
                "",
            )
            .strip()
        )

        hearing_time = (
            request.form.get(
                "hearing_time",
                "",
            )
            .strip()
        )

        judge = (
            request.form.get(
                "judge",
                "",
            )
            .strip()
        )

        description = (
            request.form.get(
                "description",
                "",
            )
            .strip()
        )

        public_information = (
            request.form.get(
                "public_information",
                "",
            )
            .strip()
        )

        if not case_number:

            flash(
                "Case number is required.",
                "danger",
            )

            return render_template(
                "staff_cases.html",
                cases=[],
            )

        if not party_name:

            flash(
                "Party name is required.",
                "danger",
            )

            return render_template(
                "staff_cases.html",
                cases=[],
            )

        if not last_name:

            flash(
                "Last name is required.",
                "danger",
            )

            return render_template(
                "staff_cases.html",
                cases=[],
            )

        db = get_db()

        try:

            db.execute(
                """
                INSERT INTO cases
                (
                    case_number,
                    party_name,
                    last_name,
                    case_title,
                    case_type,
                    case_status,
                    hearing_date,
                    hearing_time,
                    judge,
                    description,
                    public_information,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_number,
                    party_name,
                    last_name,
                    case_title,
                    case_type,
                    case_status,
                    hearing_date,
                    hearing_time,
                    judge,
                    description,
                    public_information,
                    now(),
                    now(),
                ),
            )

            db.commit()

            flash(
                "Case added successfully.",
                "success",
            )

        except sqlite3.IntegrityError:

            flash(
                "A case with that case number already exists.",
                "danger",
            )

        finally:

            db.close()

        return redirect(
            url_for("staff_cases")
        )

    return render_template(
        "staff_cases.html",
        cases=[],
        show_new_form=True,
    )


# ------------------------------------------------------------
# EDIT CASE
# ------------------------------------------------------------

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

        case_number = (
            request.form.get(
                "case_number",
                "",
            )
            .strip()
        )

        party_name = (
            request.form.get(
                "party_name",
                "",
            )
            .strip()
        )

        last_name = (
            request.form.get(
                "last_name",
                "",
            )
            .strip()
        )

        case_title = (
            request.form.get(
                "case_title",
                "",
            )
            .strip()
        )

        case_type = (
            request.form.get(
                "case_type",
                "",
            )
            .strip()
        )

        case_status = (
            request.form.get(
                "case_status",
                "",
            )
            .strip()
        )

        hearing_date = (
            request.form.get(
                "hearing_date",
                "",
            )
            .strip()
        )

        hearing_time = (
            request.form.get(
                "hearing_time",
                "",
            )
            .strip()
        )

        judge = (
            request.form.get(
                "judge",
                "",
            )
            .strip()
        )

        description = (
            request.form.get(
                "description",
                "",
            )
            .strip()
        )

        public_information = (
            request.form.get(
                "public_information",
                "",
            )
            .strip()
        )

        db = get_db()

        try:

            db.execute(
                """
                UPDATE cases
                SET
                    case_number = ?,
                    party_name = ?,
                    last_name = ?,
                    case_title = ?,
                    case_type = ?,
                    case_status = ?,
                    hearing_date = ?,
                    hearing_time = ?,
                    judge = ?,
                    description = ?,
                    public_information = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    case_number,
                    party_name,
                    last_name,
                    case_title,
                    case_type,
                    case_status,
                    hearing_date,
                    hearing_time,
                    judge,
                    description,
                    public_information,
                    now(),
                    case_id,
                ),
            )

            db.commit()

            flash(
                "Case updated successfully.",
                "success",
            )

        except sqlite3.IntegrityError:

            flash(
                "That case number is already being used.",
                "danger",
            )

        finally:

            db.close()

        return redirect(
            url_for("staff_cases")
        )

    return render_template(
        "staff_cases.html",
        cases=[],
        edit_case=case,
    )


# ------------------------------------------------------------
# DELETE CASE
# ------------------------------------------------------------

@app.route(
    "/staff/cases/<int:case_id>/delete",
    methods=[
        "POST",
    ],
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

        flash(
            "Case could not be found.",
            "danger",
        )

        return redirect(
            url_for("staff_cases")
        )

    # Delete related documents first.
    db.execute(
        """
        DELETE FROM case_documents
        WHERE case_id = ?
        """,
        (case_id,),
    )

    db.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (case_id,),
    )

    db.commit()

    db.close()

    flash(
        "Case deleted successfully.",
        "success",
    )

    return redirect(
        url_for("staff_cases")
    )


# ============================================================
# STAFF DOCUMENT MANAGEMENT
# ============================================================


@app.route(
    "/staff/documents"
)
@staff_required
def staff_documents():

    db = get_db()

    documents = db.execute(
        """
        SELECT
            case_documents.*,
            cases.case_number,
            cases.party_name
        FROM case_documents
        JOIN cases
        ON cases.id = case_documents.case_id
        ORDER BY case_documents.uploaded_at DESC
        """
    ).fetchall()

    cases = db.execute(
        """
        SELECT id, case_number, party_name
        FROM cases
        ORDER BY case_number ASC
        """
    ).fetchall()

    db.close()

    return render_template(
        "staff_documents.html",
        documents=documents,
        cases=cases,
    )


# ------------------------------------------------------------
# UPLOAD CASE DOCUMENT
# ------------------------------------------------------------

@app.route(
    "/staff/documents/upload",
    methods=[
        "POST",
    ],
)
@staff_required
def upload_case_document():

    case_id = request.form.get(
        "case_id"
    )

    title = (
        request.form.get(
            "title",
            "",
        )
        .strip()
    )

    public = (
        request.form.get(
            "is_public"
        )
        == "on"
    )

    uploaded_file = request.files.get(
        "document"
    )

    if not case_id:

        flash(
            "Please select a case.",
            "danger",
        )

        return redirect(
            url_for("staff_documents")
        )

    if not title:

        flash(
            "Please enter a document title.",
            "danger",
        )

        return redirect(
            url_for("staff_documents")
        )

    if (
        not uploaded_file
        or not uploaded_file.filename
    ):

        flash(
            "Please select a document.",
            "danger",
        )

        return redirect(
            url_for("staff_documents")
        )

    if not allowed_file(
        uploaded_file.filename
    ):

        flash(
            "That file type is not allowed.",
            "danger",
        )

        return redirect(
            url_for("staff_documents")
        )

    original_filename = secure_filename(
        uploaded_file.filename
    )

    unique_filename = (
        secrets.token_hex(12)
        + "_"
        + original_filename
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename,
    )

    uploaded_file.save(
        filepath
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO case_documents
        (
            case_id,
            title,
            filename,
            is_public,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            case_id,
            title,
            unique_filename,
            int(public),
            now(),
        ),
    )

    db.commit()

    db.close()

    flash(
        "Document uploaded successfully.",
        "success",
    )

    return redirect(
        url_for("staff_documents")
    )


# ------------------------------------------------------------
# DELETE DOCUMENT
# ------------------------------------------------------------

@app.route(
    "/staff/documents/<int:document_id>/delete",
    methods=[
        "POST",
    ],
)
@staff_required
def delete_document(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM case_documents
        WHERE id = ?
        """,
        (document_id,),
    ).fetchone()

    if document:

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            document["filename"],
        )

        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except OSError:
                pass

        db.execute(
            """
            DELETE FROM case_documents
            WHERE id = ?
            """,
            (document_id,),
        )

        db.commit()

    db.close()

    flash(
        "Document deleted.",
        "success",
    )

    return redirect(
        url_for("staff_documents")
    )


# ============================================================
# FILE ACCESS
# ============================================================


@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):

    # Public access is intentionally restricted.
    #
    # A document must be marked public before civilians
    # can access it.
    #
    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM case_documents
        WHERE filename = ?
        AND is_public = 1
        """,
        (filename,),
    ).fetchone()

    db.close()

    if document is None:

        if not session.get("staff_id"):

            abort(404)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
    )


# ============================================================
# STAFF CALENDAR
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
        FROM calendar_entries
        ORDER BY calendar_date ASC,
                 calendar_time ASC
        """
    ).fetchall()

    db.close()

    return render_template(
        "staff_calendar.html",
        entries=entries,
    )


# ------------------------------------------------------------
# ADD CALENDAR ENTRY
# ------------------------------------------------------------

@app.route(
    "/staff/calendar/add",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_calendar_add():

    calendar_date = (
        request.form.get(
            "calendar_date",
            "",
        )
        .strip()
    )

    calendar_time = (
        request.form.get(
            "calendar_time",
            "",
        )
        .strip()
    )

    case_number = (
        request.form.get(
            "case_number",
            "",
        )
        .strip()
    )

    party_name = (
        request.form.get(
            "party_name",
            "",
        )
        .strip()
    )

    proceeding = (
        request.form.get(
            "proceeding",
            "",
        )
        .strip()
    )

    room = (
        request.form.get(
            "room",
            "",
        )
        .strip()
    )

    status = (
        request.form.get(
            "status",
            "",
        )
        .strip()
    )

    public_notes = (
        request.form.get(
            "public_notes",
            "",
        )
        .strip()
    )

    if not calendar_date:

        flash(
            "Calendar date is required.",
            "danger",
        )

        return redirect(
            url_for("staff_calendar")
        )

    if not calendar_time:

        flash(
            "Calendar time is required.",
            "danger",
        )

        return redirect(
            url_for("staff_calendar")
        )

    db = get_db()

    db.execute(
        """
        INSERT INTO calendar_entries
        (
            calendar_date,
            calendar_time,
            case_number,
            party_name,
            proceeding,
            room,
            status,
            public_notes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            calendar_date,
            calendar_time,
            case_number,
            party_name,
            proceeding,
            room,
            status,
            public_notes,
            now(),
            now(),
        ),
    )

    db.commit()

    db.close()

    flash(
        "Tuesday calendar entry added.",
        "success",
    )

    return redirect(
        url_for("staff_calendar")
    )


# ------------------------------------------------------------
# DELETE CALENDAR ENTRY
# ------------------------------------------------------------

@app.route(
    "/staff/calendar/<int:entry_id>/delete",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_calendar_delete(entry_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM calendar_entries
        WHERE id = ?
        """,
        (entry_id,),
    )

    db.commit()

    db.close()

    flash(
        "Calendar entry deleted.",
        "success",
    )

    return redirect(
        url_for("staff_calendar")
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

    return render_template(
        "staff_notices.html",
        notices=notices,
    )


# ------------------------------------------------------------
# ADD NOTICE
# ------------------------------------------------------------

@app.route(
    "/staff/notices/add",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_notice_add():

    title = (
        request.form.get(
            "title",
            "",
        )
        .strip()
    )

    body = (
        request.form.get(
            "body",
            "",
        )
        .strip()
    )

    published = (
        request.form.get(
            "published"
        )
        == "on"
    )

    uploaded_file = request.files.get(
        "attachment"
    )

    filename = None

    if uploaded_file and uploaded_file.filename:

        if not allowed_file(
            uploaded_file.filename
        ):

            flash(
                "The notice attachment type is not allowed.",
                "danger",
            )

            return redirect(
                url_for("staff_notices")
            )

        safe_name = secure_filename(
            uploaded_file.filename
        )

        filename = (
            secrets.token_hex(12)
            + "_"
            + safe_name
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename,
        )

        uploaded_file.save(
            filepath
        )

    if not title or not body:

        flash(
            "Notice title and content are required.",
            "danger",
        )

        return redirect(
            url_for("staff_notices")
        )

    db = get_db()

    db.execute(
        """
        INSERT INTO notices
        (
            title,
            body,
            filename,
            published,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            title,
            body,
            filename,
            int(published),
            now(),
        ),
    )

    db.commit()

    db.close()

    flash(
        "Notice published.",
        "success",
    )

    return redirect(
        url_for("staff_notices")
    )


# ------------------------------------------------------------
# DELETE NOTICE
# ------------------------------------------------------------

@app.route(
    "/staff/notices/<int:notice_id>/delete",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_notice_delete(notice_id):

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

        if notice["filename"]:

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                notice["filename"],
            )

            if os.path.exists(filepath):

                try:
                    os.remove(filepath)
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
        ORDER BY category ASC,
                 publication_date DESC
        """
    ).fetchall()

    db.close()

    return render_template(
        "staff_laws.html",
        resources=resources,
    )


# ------------------------------------------------------------
# ADD LEGAL RESOURCE
# ------------------------------------------------------------

@app.route(
    "/staff/laws/add",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_law_add():

    category = (
        request.form.get(
            "category",
            "",
        )
        .strip()
    )

    title = (
        request.form.get(
            "title",
            "",
        )
        .strip()
    )

    description = (
        request.form.get(
            "description",
            "",
        )
        .strip()
    )

    source_url = (
        request.form.get(
            "source_url",
            "",
        )
        .strip()
    )

    publication_date = (
        request.form.get(
            "publication_date",
            "",
        )
        .strip()
    )

    if not category or not title:

        flash(
            "Category and title are required.",
            "danger",
        )

        return redirect(
            url_for("staff_laws")
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
            publication_date,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            category,
            title,
            description,
            source_url,
            publication_date,
            now(),
        ),
    )

    db.commit()

    db.close()

    flash(
        "Legal resource added.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


# ------------------------------------------------------------
# DELETE LEGAL RESOURCE
# ------------------------------------------------------------

@app.route(
    "/staff/laws/<int:resource_id>/delete",
    methods=[
        "POST",
    ],
)
@staff_required
def staff_law_delete(resource_id):

    db = get_db()

    db.execute(
        """
        DELETE FROM legal_resources
        WHERE id = ?
        """,
        (resource_id,),
    )

    db.commit()

    db.close()

    flash(
        "Legal resource deleted.",
        "success",
    )

    return redirect(
        url_for("staff_laws")
    )


# ============================================================
# REQUIREMENTS MANAGEMENT
# ============================================================


@app.route(
    "/staff/requirements",
)
@staff_required
def staff_requirements():

    db = get_db()

    requirements = db.execute(
        """
        SELECT *
        FROM requirements
        ORDER BY requirement_type
        """
    ).fetchall()

    db.close()

    return render_template(
        "staff_requirements.html",
        requirements=requirements,
    )


# ------------------------------------------------------------
# UPDATE REQUIREMENT
# ------------------------------------------------------------

@app.route(
    "/staff/requirements/<requirement_type>/update",
    methods=[
        "POST",
    ],
)
@staff_required
def update_requirement(
    requirement_type
):

    if requirement_type not in {
        "bond",
        "clearance",
    }:

        abort(404)

    title = (
        request.form.get(
            "title",
            "",
        )
        .strip()
    )

    body = (
        request.form.get(
            "body",
            "",
        )
        .strip()
    )

    uploaded_file = request.files.get(
        "document"
    )

    filename = None

    if uploaded_file and uploaded_file.filename:

        if not allowed_file(
            uploaded_file.filename
        ):

            flash(
                "That document type is not allowed.",
                "danger",
            )

            return redirect(
                url_for("staff_requirements")
            )

        safe_name = secure_filename(
            uploaded_file.filename
        )

        filename = (
            secrets.token_hex(12)
            + "_"
            + safe_name
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename,
        )

        uploaded_file.save(
            filepath
        )

    db = get_db()

    if filename:

        db.execute(
            """
            UPDATE requirements
            SET
                title = ?,
                body = ?,
                filename = ?,
                updated_at = ?
            WHERE requirement_type = ?
            """,
            (
                title,
                body,
                filename,
                now(),
                requirement_type,
            ),
        )

    else:

        db.execute(
            """
            UPDATE requirements
            SET
                title = ?,
                body = ?,
                updated_at = ?
            WHERE requirement_type = ?
            """,
            (
                title,
                body,
                now(),
                requirement_type,
            ),
        )

    db.commit()

    db.close()

    flash(
        "Requirement information updated.",
        "success",
    )

    return redirect(
        url_for("staff_requirements")
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
        "service": "MCTC Silang-Amadeo Court Information System",
    }


# ============================================================
# ERROR HANDLERS
# ============================================================


@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_error(error):

    return render_template(
        "500.html"
    ), 500


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


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
