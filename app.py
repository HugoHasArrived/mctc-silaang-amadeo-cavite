import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    flash,
    render_template_string,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-IN-RENDER"
)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "court.db"
)

LOGO = "image0.jpeg"

COURT_NAME = (
    "Municipal Circuit Trial Court "
    "of Silang-Amadeo, Cavite"
)

COURT_ADDRESS = (
    "PNP Bldg, Plaza Libertad, Poblacion 2, "
    "Silang, Cavite"
)

COURT_PHONE = "09284621305"


# ============================================================
# TRANSLATIONS
# ============================================================

T = {

    "en": {

        "home": "Home",
        "search": "Search Cases",
        "hearings": "Hearings",
        "notices": "Court Notices",
        "about": "About",
        "staff": "Staff Login",
        "logout": "Log Out",
        "dashboard": "Dashboard",

        "court_portal":
            "COURT INFORMATION PORTAL",

        "welcome":
            "Welcome to the Municipal Circuit Trial Court of Silang-Amadeo, Cavite",

        "public_information":
            "Public Court Information",

        "search_case":
            "Search for a Case",

        "search_instruction":
            "Enter a case number or the name of a party to search approved public case information.",

        "case_number":
            "Case Number",

        "party_name":
            "Party Name",

        "search_button":
            "Search",

        "clear":
            "Clear",

        "how_search":
            "How to Search",

        "step1":
            "Enter the complete or partial case number.",

        "step2":
            "You may also enter the name of a party.",

        "step3":
            "You can use both fields to narrow your search.",

        "step4":
            "Press Search.",

        "step5":
            "Select View Case to see the approved public information.",

        "example":
            "Example: MCTC-2026-001",

        "results":
            "Search Results",

        "no_results":
            "No matching cases were found.",

        "try_again":
            "Please check the case number or party name and try again.",

        "view_case":
            "View Case",

        "case_information":
            "Case Information",

        "case_type":
            "Case Type",

        "parties":
            "Parties",

        "status":
            "Status",

        "summary":
            "Public Case Summary",

        "hearing_schedule":
            "Hearing Schedule",

        "hearing_date":
            "Hearing Date",

        "hearing_time":
            "Hearing Time",

        "courtroom":
            "Courtroom",

        "purpose":
            "Purpose",

        "no_hearings":
            "No published hearings are available.",

        "official_notices":
            "Official Court Notices",

        "suspension":
            "Suspension / Postponement Information",

        "no_notices":
            "No current notices are available.",

        "about_title":
            "About the Court",

        "contact":
            "Contact Information",

        "address":
            "Address",

        "telephone":
            "Telephone",

        "authorized":
            "Authorized Staff Only",

        "staff_login":
            "Staff Login",

        "username":
            "Username",

        "password":
            "Password",

        "sign_in":
            "Sign In",

        "login_help":
            "Sign in to manage authorized court information.",

        "login_error":
            "The username or password is incorrect.",

        "staff_dashboard":
            "Staff Dashboard",

        "welcome_staff":
            "Welcome, Court Staff",

        "staff_description":
            "Use this workspace to manage approved case information, hearings, and notices.",

        "add_case":
            "Add New Case",

        "manage_cases":
            "Manage Cases",

        "manage_hearings":
            "Manage Hearings",

        "manage_notices":
            "Manage Notices",

        "case_management":
            "Case Management",

        "new_case":
            "New Case",

        "edit":
            "Edit",

        "delete":
            "Delete",

        "save":
            "Save",

        "cancel":
            "Cancel",

        "delete_confirm":
            "Are you sure you want to delete this case?",

        "delete_warning":
            "Deleting a case also removes its hearings and documents.",

        "case_saved":
            "Case saved successfully.",

        "case_deleted":
            "Case deleted successfully.",

        "case_not_found":
            "Case not found.",

        "logout_success":
            "You have been logged out.",

        "privacy":
            "Privacy",

        "privacy_text":
            "Only information approved for public release should be placed in the public portal.",

        "language":
            "Language",

        "theme":
            "Theme",

        "light":
            "Light",

        "dark":
            "Dark",

        "public":
            "Public",

        "internal":
            "Internal",

        "documents":
            "Documents",

        "add_hearing":
            "Add Hearing",

        "add_notice":
            "Add Notice",

        "notice_title":
            "Notice Title",

        "notice_body":
            "Notice Information",

        "notice_type":
            "Notice Type",

        "publish":
            "Publish",

        "active":
            "Active",

        "inactive":
            "Inactive",

        "no_cases":
            "No cases have been added yet.",

        "profile":
            "Staff Profile",

        "credentials_hidden":
            "Your username and password are not displayed on this page.",

        "security":
            "Security Reminder",

        "security_text":
            "Never share staff credentials. Always log out when finished.",

    },

    "fil": {

        "home": "Home",

        "search": "Maghanap ng Kaso",

        "hearings": "Mga Pagdinig",

        "notices": "Mga Abiso",

        "about": "Tungkol sa Hukuman",

        "staff": "Login ng Kawani",

        "logout": "Mag-logout",

        "dashboard": "Dashboard",

        "court_portal":
            "PORTAL NG IMPORMASYON NG HUKUMAN",

        "welcome":
            "Maligayang pagdating sa Municipal Circuit Trial Court of Silang-Amadeo, Cavite",

        "public_information":
            "Pampublikong Impormasyon ng Hukuman",

        "search_case":
            "Maghanap ng Kaso",

        "search_instruction":
            "Ilagay ang numero ng kaso o pangalan ng partido upang maghanap ng aprubadong pampublikong impormasyon.",

        "case_number":
            "Numero ng Kaso",

        "party_name":
            "Pangalan ng Partido",

        "search_button":
            "Maghanap",

        "clear":
            "I-clear",

        "how_search":
            "Paano Maghanap",

        "step1":
            "Ilagay ang buo o bahagi ng numero ng kaso.",

        "step2":
            "Maaari ring ilagay ang pangalan ng isang partido.",

        "step3":
            "Maaaring gamitin ang parehong field upang paliitin ang resulta.",

        "step4":
            "Pindutin ang Maghanap.",

        "step5":
            "Piliin ang Tingnan ang Kaso upang makita ang aprubadong pampublikong impormasyon.",

        "example":
            "Halimbawa: MCTC-2026-001",

        "results":
            "Mga Resulta ng Paghahanap",

        "no_results":
            "Walang nahanap na tugmang kaso.",

        "try_again":
            "Suriin ang numero ng kaso o pangalan at subukang muli.",

        "view_case":
            "Tingnan ang Kaso",

        "case_information":
            "Impormasyon ng Kaso",

        "case_type":
            "Uri ng Kaso",

        "parties":
            "Mga Partido",

        "status":
            "Katayuan",

        "summary":
            "Pampublikong Buod ng Kaso",

        "hearing_schedule":
            "Iskedyul ng Pagdinig",

        "hearing_date":
            "Petsa ng Pagdinig",

        "hearing_time":
            "Oras ng Pagdinig",

        "courtroom":
            "Silid ng Hukuman",

        "purpose":
            "Layunin",

        "no_hearings":
            "Walang nailathalang pagdinig.",

        "official_notices":
            "Mga Opisyal na Abiso ng Hukuman",

        "suspension":
            "Impormasyon sa Suspensyon / Pagpapaliban",

        "no_notices":
            "Walang kasalukuyang abiso.",

        "about_title":
            "Tungkol sa Hukuman",

        "contact":
            "Impormasyon sa Pakikipag-ugnayan",

        "address":
            "Address",

        "telephone":
            "Telepono",

        "authorized":
            "Para Lamang sa Awtorisadong Kawani",

        "staff_login":
            "Login ng Kawani",

        "username":
            "Username",

        "password":
            "Password",

        "sign_in":
            "Mag-sign In",

        "login_help":
            "Mag-sign in upang pamahalaan ang awtorisadong impormasyon ng hukuman.",

        "login_error":
            "Mali ang username o password.",

        "staff_dashboard":
            "Dashboard ng Kawani",

        "welcome_staff":
            "Maligayang Pagdating, Kawani ng Hukuman",

        "staff_description":
            "Gamitin ang workspace na ito upang pamahalaan ang aprubadong impormasyon ng kaso, pagdinig, at mga abiso.",

        "add_case":
            "Magdagdag ng Bagong Kaso",

        "manage_cases":
            "Pamahalaan ang mga Kaso",

        "manage_hearings":
            "Pamahalaan ang mga Pagdinig",

        "manage_notices":
            "Pamahalaan ang mga Abiso",

        "case_management":
            "Pamamahala ng Kaso",

        "new_case":
            "Bagong Kaso",

        "edit":
            "I-edit",

        "delete":
            "Tanggalin",

        "save":
            "I-save",

        "cancel":
            "Kanselahin",

        "delete_confirm":
            "Sigurado ka bang gusto mong tanggalin ang kasong ito?",

        "delete_warning":
            "Ang pagtanggal ng kaso ay tatanggalin din ang mga pagdinig at dokumento nito.",

        "case_saved":
            "Matagumpay na na-save ang kaso.",

        "case_deleted":
            "Matagumpay na natanggal ang kaso.",

        "case_not_found":
            "Hindi nahanap ang kaso.",

        "logout_success":
            "Na-logout ka na.",

        "privacy":
            "Pribasiya",

        "privacy_text":
            "Ang impormasyong inaprubahan lamang para sa pampublikong paglalabas ang dapat ilagay sa pampublikong portal.",

        "language":
            "Wika",

        "theme":
            "Tema",

        "light":
            "Maliwanag",

        "dark":
            "Madilim",

        "public":
            "Pampubliko",

        "internal":
            "Panloob",

        "documents":
            "Mga Dokumento",

        "add_hearing":
            "Magdagdag ng Pagdinig",

        "add_notice":
            "Magdagdag ng Abiso",

        "notice_title":
            "Pamagat ng Abiso",

        "notice_body":
            "Impormasyon ng Abiso",

        "notice_type":
            "Uri ng Abiso",

        "publish":
            "I-publish",

        "active":
            "Aktibo",

        "inactive":
            "Hindi Aktibo",

        "no_cases":
            "Wala pang naidadagdag na kaso.",

        "profile":
            "Profile ng Kawani",

        "credentials_hidden":
            "Hindi ipinapakita sa pahinang ito ang iyong username at password.",

        "security":
            "Paalala sa Seguridad",

        "security_text":
            "Huwag kailanman ibahagi ang staff credentials. Palaging mag-logout kapag tapos na.",

    },

}


# ============================================================
# HELPERS
# ============================================================

def lang():
    value = session.get("language", "en")

    if value not in T:
        value = "en"

    return value


def tr(key):
    return T[lang()].get(
        key,
        T["en"].get(key, key)
    )


def theme():
    value = session.get(
        "theme",
        "light"
    )

    if value not in (
        "light",
        "dark"
    ):
        value = "light"

    return value


def now():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def get_db():
    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def staff_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("staff_id"):

            flash(
                "Please sign in first."
                if lang() == "en"
                else
                "Mag-sign in muna.",
                "warning"
            )

            return redirect(
                url_for(
                    "login"
                )
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# DATABASE
# ============================================================

def init_database():

    connection = get_db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'Staff',

            active INTEGER NOT NULL DEFAULT 1,

            created_at TEXT NOT NULL

        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_number TEXT UNIQUE NOT NULL,

            title TEXT NOT NULL,

            case_type TEXT,

            parties TEXT,

            status TEXT,

            public_summary TEXT,

            internal_notes TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS hearings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id INTEGER NOT NULL,

            hearing_date TEXT NOT NULL,

            hearing_time TEXT,

            courtroom TEXT,

            purpose TEXT,

            FOREIGN KEY(case_id)
            REFERENCES cases(id)
            ON DELETE CASCADE

        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title_en TEXT NOT NULL,

            title_fil TEXT NOT NULL,

            body_en TEXT NOT NULL,

            body_fil TEXT NOT NULL,

            notice_type TEXT NOT NULL,

            published INTEGER NOT NULL DEFAULT 1,

            created_at TEXT NOT NULL

        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            staff_id INTEGER,

            action TEXT,

            created_at TEXT NOT NULL

        )
        """
    )

    existing = connection.execute(
        "SELECT id FROM staff LIMIT 1"
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
                "admin",
                generate_password_hash(
                    "ChangeMe123!"
                ),
                "Administrator",
                1,
                now()
            )
        )

    connection.commit()

    connection.close()


def audit(action):

    staff_id = session.get(
        "staff_id"
    )

    connection = get_db()

    connection.execute(
        """
        INSERT INTO audit_logs
        (
            staff_id,
            action,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            staff_id,
            action,
            now()
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# CSS
# ============================================================

CSS = r"""

:root {

    --purple:
        #7c3aed;

    --purple-dark:
        #5b21b6;

    --purple-light:
        #ede9fe;

    --background:
        #f6f2fb;

    --surface:
        #ffffff;

    --surface-2:
        #faf7ff;

    --text:
        #21152e;

    --muted:
        #6b6174;

    --border:
        #ded4e8;

    --danger:
        #b91c1c;

    --success:
        #15803d;

    --warning:
        #a16207;

    --shadow:
        0 12px 35px
        rgba(67, 35, 92, .10);

}


body.dark {

    --background:
        #160d1d;

    --surface:
        #24152d;

    --surface-2:
        #2c1b36;

    --text:
        #f7efff;

    --muted:
        #c8b9d0;

    --border:
        #4b3755;

    --purple-light:
        #3b2250;

    --shadow:
        0 12px 35px
        rgba(0, 0, 0, .35);

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

    background:
        var(--background);

    color:
        var(--text);

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    line-height:
        1.6;

}


a {

    color:
        var(--purple);

    text-decoration:
        none;

}


a:hover {

    text-decoration:
        underline;

}


.container {

    width:
        min(1180px, 94%);

    margin:
        auto;

}


.navbar {

    position:
        sticky;

    top:
        0;

    z-index:
        1000;

    background:
        var(--surface);

    border-bottom:
        1px solid var(--border);

    box-shadow:
        0 4px 18px
        rgba(0,0,0,.06);

}


.nav-inner {

    min-height:
        76px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        20px;

}


.brand {

    display:
        flex;

    align-items:
        center;

    gap:
        12px;

    font-weight:
        800;

    color:
        var(--text);

}


.brand img {

    width:
        52px;

    height:
        52px;

    object-fit:
        contain;

}


.brand-text {

    line-height:
        1.2;

}


.brand-title {

    font-size:
        15px;

}


.brand-subtitle {

    color:
        var(--muted);

    font-size:
        12px;

}


.nav-links {

    display:
        flex;

    align-items:
        center;

    flex-wrap:
        wrap;

    gap:
        8px;

}


.nav-links a {

    padding:
        9px 11px;

    border-radius:
        9px;

    color:
        var(--text);

    font-size:
        14px;

}


.nav-links a:hover {

    background:
        var(--purple-light);

    text-decoration:
        none;

}


.controls {

    display:
        flex;

    gap:
        6px;

    align-items:
        center;

}


.control {

    border:
        1px solid var(--border);

    background:
        var(--surface);

    color:
        var(--text);

    border-radius:
        8px;

    padding:
        7px 9px;

    cursor:
        pointer;

    font-weight:
        700;

}


.control.active {

    background:
        var(--purple);

    color:
        white;

    border-color:
        var(--purple);

}


.hero {

    margin-top:
        30px;

    padding:
        55px;

    border-radius:
        24px;

    background:
        linear-gradient(
            135deg,
            var(--purple-dark),
            var(--purple)
        );

    color:
        white;

    display:
        grid;

    grid-template-columns:
        1fr 230px;

    gap:
        40px;

    align-items:
        center;

    box-shadow:
        var(--shadow);

}


.hero h1 {

    font-size:
        clamp(30px, 5vw, 56px);

    line-height:
        1.05;

    margin:
        12px 0;

}


.hero p {

    max-width:
        760px;

    font-size:
        18px;

}


.seal {

    display:
        flex;

    justify-content:
        center;

}


.seal img {

    width:
        190px;

    height:
        190px;

    object-fit:
        contain;

    background:
        rgba(255,255,255,.95);

    border-radius:
        50%;

    padding:
        12px;

}


.button {

    display:
        inline-flex;

    justify-content:
        center;

    align-items:
        center;

    gap:
        8px;

    border:
        0;

    border-radius:
        10px;

    padding:
        11px 17px;

    background:
        var(--purple);

    color:
        white;

    font-weight:
        800;

    cursor:
        pointer;

    font-size:
        14px;

}


.button:hover {

    background:
        var(--purple-dark);

    color:
        white;

    text-decoration:
        none;

}


.button.secondary {

    background:
        var(--surface);

    color:
        var(--purple);

    border:
        1px solid var(--border);

}


.button.danger {

    background:
        var(--danger);

}


.button.warning {

    background:
        var(--warning);

}


.hero .button {

    margin-top:
        12px;

}


main {

    padding:
        30px 0 70px;

}


.grid {

    display:
        grid;

    gap:
        20px;

}


.grid-2 {

    grid-template-columns:
        repeat(2, 1fr);

}


.grid-3 {

    grid-template-columns:
        repeat(3, 1fr);

}


.card {

    background:
        var(--surface);

    border:
        1px solid var(--border);

    border-radius:
        16px;

    padding:
        25px;

    margin-bottom:
        20px;

    box-shadow:
        var(--shadow);

}


.card h1,
.card h2,
.card h3 {

    margin-top:
        0;

}


.muted {

    color:
        var(--muted);

}


.notice {

    border-left:
        5px solid var(--purple);

    background:
        var(--surface-2);

    padding:
        17px;

    border-radius:
        10px;

    margin:
        12px 0;

}


.notice.warning {

    border-left-color:
        var(--warning);

}


.notice.danger {

    border-left-color:
        var(--danger);

}


.notice.success {

    border-left-color:
        var(--success);

}


.search-box {

    display:
        grid;

    grid-template-columns:
        1fr 1fr auto;

    gap:
        12px;

    align-items:
        end;

}


label {

    display:
        block;

    font-weight:
        700;

    margin-bottom:
        15px;

}


input,
textarea,
select {

    width:
        100%;

    margin-top:
        6px;

    padding:
        12px 13px;

    border:
        1px solid var(--border);

    border-radius:
        9px;

    background:
        var(--surface);

    color:
        var(--text);

    font: inherit;

}


textarea {

    min-height:
        130px;

    resize:
        vertical;

}


input:focus,
textarea:focus,
select:focus {

    outline:
        3px solid
        rgba(124,58,237,.20);

    border-color:
        var(--purple);

}


.result {

    display:
        grid;

    grid-template-columns:
        1.2fr 1fr .8fr auto;

    gap:
        15px;

    align-items:
        center;

    padding:
        17px 0;

    border-bottom:
        1px solid var(--border);

}


.result:last-child {

    border-bottom:
        0;

}


.status {

    display:
        inline-block;

    padding:
        5px 9px;

    border-radius:
        999px;

    background:
        var(--purple-light);

    color:
        var(--purple);

    font-weight:
        800;

    font-size:
        12px;

}


table {

    width:
        100%;

    border-collapse:
        collapse;

}


th,
td {

    text-align:
        left;

    padding:
        12px;

    border-bottom:
        1px solid var(--border);

    vertical-align:
        top;

}


th {

    color:
        var(--muted);

    font-size:
        13px;

}


.actions {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        8px;

}


.flash {

    padding:
        13px 16px;

    border-radius:
        10px;

    margin:
        15px 0;

    background:
        var(--purple-light);

    border:
        1px solid var(--border);

}


.flash.danger {

    background:
        #fee2e2;

    color:
        #7f1d1d;

}


.flash.success {

    background:
        #dcfce7;

    color:
        #14532d;

}


.flash.warning {

    background:
        #fef3c7;

    color:
        #78350f;

}


.empty {

    text-align:
        center;

    padding:
        45px 20px;

    color:
        var(--muted);

}


.steps {

    counter-reset:
        steps;

    list-style:
        none;

    padding:
        0;

}


.steps li {

    counter-increment:
        steps;

    padding:
        14px 14px 14px 55px;

    position:
        relative;

    border-bottom:
        1px solid var(--border);

}


.steps li::before {

    content:
        counter(steps);

    position:
        absolute;

    left:
        10px;

    top:
        10px;

    width:
        30px;

    height:
        30px;

    display:
        grid;

    place-items:
        center;

    background:
        var(--purple);

    color:
        white;

    border-radius:
        50%;

    font-weight:
        800;

}


footer {

    background:
        var(--purple-dark);

    color:
        white;

    padding:
        35px 0;

}


footer a {

    color:
        white;

}


.login {

    max-width:
        520px;

    margin:
        50px auto;

}


.center {

    text-align:
        center;

}


.admin-header {

    display:
        flex;

    justify-content:
        space-between;

    gap:
        20px;

    align-items:
        center;

    flex-wrap:
        wrap;

}


.kpi {

    font-size:
        34px;

    font-weight:
        900;

    color:
        var(--purple);

}


@media(max-width: 900px) {

    .nav-inner {

        flex-direction:
            column;

        padding:
            12px 0;

    }

    .hero {

        grid-template-columns:
            1fr;

        padding:
            30px;

    }

    .grid-2,
    .grid-3 {

        grid-template-columns:
            1fr;

    }

    .search-box {

        grid-template-columns:
            1fr;

    }

    .result {

        grid-template-columns:
            1fr;

    }

    table {

        display:
            block;

        overflow-x:
            auto;

    }

}


@media(max-width: 600px) {

    .container {

        width:
            92%;

    }

    .hero h1 {

        font-size:
            34px;

    }

    .brand-subtitle {

        display:
            none;

    }

}

"""


# ============================================================
# PAGE TEMPLATE
# ============================================================

PAGE = r"""
<!doctype html>

<html lang="{{ language }}">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>
    {{ title }} -
    {{ court_name }}
</title>

<style>
{{ css }}
</style>

</head>


<body class="{{ theme_name }}">


<header class="navbar">

<div class="container nav-inner">


<a
    class="brand"
    href="{{ url_for('home') }}"
>

<img
    src="{{ url_for('static', filename=logo) }}"
    alt="Official Court Seal"
>

<div class="brand-text">

<div class="brand-title">
{{ court_short }}
</div>

<div class="brand-subtitle">
{{ court_name }}
</div>

</div>

</a>


<nav class="nav-links">

<a href="{{ url_for('home') }}">
{{ tr("home") }}
</a>

<a href="{{ url_for('search') }}">
{{ tr("search") }}
</a>

<a href="{{ url_for('hearings') }}">
{{ tr("hearings") }}
</a>

<a href="{{ url_for('notices') }}">
{{ tr("notices") }}
</a>

<a href="{{ url_for('about') }}">
{{ tr("about") }}
</a>

{% if logged_in %}

<a href="{{ url_for('dashboard') }}">
{{ tr("dashboard") }}
</a>

<a href="{{ url_for('logout') }}">
{{ tr("logout") }}
</a>

{% else %}

<a href="{{ url_for('login') }}">
{{ tr("staff") }}
</a>

{% endif %}

</nav>


<div class="controls">

<a
    class="control {% if language == 'en' %}active{% endif %}"
    href="{{ url_for('set_language', value='en') }}"
>
EN
</a>

<a
    class="control {% if language == 'fil' %}active{% endif %}"
    href="{{ url_for('set_language', value='fil') }}"
>
FIL
</a>

<a
    class="control {% if theme_name == 'light' %}active{% endif %}"
    href="{{ url_for('set_theme', value='light') }}"
>
☀
</a>

<a
    class="control {% if theme_name == 'dark' %}active{% endif %}"
    href="{{ url_for('set_theme', value='dark') }}"
>
☾
</a>

</div>


</div>

</header>


<main>

<div class="container">


{% with messages = get_flashed_messages(
    with_categories=true
) %}

{% for category, message in messages %}

<div class="flash {{ category }}">

{{ message }}

</div>

{% endfor %}

{% endwith %}


{{ content | safe }}


</div>

</main>


<footer>

<div class="container">

<strong>
{{ court_name }}
</strong>

<br>

{{ court_address }}

<br>

{{ court_phone }}

<br><br>

{{ tr("privacy_text") }}

</div>

</footer>


</body>

</html>
"""


# ============================================================
# RENDER PAGE
# ============================================================

def page(title, content):

    return render_template_string(

        PAGE,

        title=title,

        content=content,

        css=CSS,

        logo=LOGO,

        court_name=COURT_NAME,

        court_short="MCTC Silang-Amadeo",

        court_address=COURT_ADDRESS,

        court_phone=COURT_PHONE,

        language=lang(),

        theme_name=theme(),

        logged_in=bool(
            session.get("staff_id")
        ),

        tr=tr,

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

    for item in notices:

        title = (
            item["title_fil"]
            if lang() == "fil"
            else item["title_en"]
        )

        body = (
            item["body_fil"]
            if lang() == "fil"
            else item["body_en"]
        )

        notice_html += f"""
        <div class="notice">

            <span class="status">
                {item["notice_type"]}
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
                {tr("court_portal")}
            </div>

            <h1>
                {COURT_NAME}
            </h1>

            <p>
                {tr("welcome")}
            </p>

            <p>
                {tr("search_instruction")}
            </p>

            <a
                class="button"
                href="{url_for('search')}"
            >
                🔎
                {tr("search_case")}
            </a>

        </div>


        <div class="seal">

            <img
                src="{url_for('static', filename=LOGO)}"
                alt="Official Court Seal"
            >

        </div>

    </section>


    <section class="grid grid-3">

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
                href="{url_for('search')}"
            >
                {tr("search_button")}
            </a>

        </div>


        <div class="card">

            <h2>
                📅
                {tr("hearing_schedule")}
            </h2>

            <p>
                {tr("hearings")}
            </p>

            <a
                class="button"
                href="{url_for('hearings')}"
            >
                {tr("hearings")}
            </a>

        </div>


        <div class="card">

            <h2>
                📢
                {tr("official_notices")}
            </h2>

            <p>
                {tr("suspension")}
            </p>

            <a
                class="button"
                href="{url_for('notices')}"
            >
                {tr("notices")}
            </a>

        </div>

    </section>


    <section class="card">

        <h2>
            {tr("how_search")}
        </h2>

        <ol class="steps">

            <li>
                {tr("step1")}
            </li>

            <li>
                {tr("step2")}
            </li>

            <li>
                {tr("step3")}
            </li>

            <li>
                {tr("step4")}
            </li>

            <li>
                {tr("step5")}
            </li>

        </ol>

        <div class="notice">

            <strong>
                {tr("example")}
            </strong>

        </div>

    </section>


    <section class="card">

        <h2>
            {tr("official_notices")}
        </h2>

        {
            notice_html
            or
            f"<div class='empty'>{tr('no_notices')}</div>"
        }

    </section>

    """

    return page(
        tr("home"),
        content
    )


# ============================================================
# LANGUAGE
# ============================================================

@app.route("/language/<value>")
def set_language(value):

    if value not in (
        "en",
        "fil"
    ):

        value = "en"

    session["language"] = value

    return redirect(
        request.referrer
        or url_for("home")
    )


@app.route("/set-language/<value>")
def set_language_alt(value):

    return set_language(value)


# ============================================================
# THEME
# ============================================================

@app.route("/theme/<value>")
def set_theme(value):

    if value not in (
        "light",
        "dark"
    ):

        value = "light"

    session["theme"] = value

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# PUBLIC SEARCH
# ============================================================

@app.route("/search")
def search():

    case_number = (
        request.args.get(
            "case_number",
            ""
        )
        .strip()
    )

    name = (
        request.args.get(
            "name",
            ""
        )
        .strip()
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
                    OR parties LIKE ?
                    OR title LIKE ?
                )
            ORDER BY case_number
            """,
            (
                case_number,
                "%" + case_number + "%",

                name,
                "%" + name + "%",
                "%" + name + "%",
            )
        ).fetchall()

        connection.close()

    rows = ""

    for item in results:

        rows += f"""

        <div class="result">

            <div>

                <strong>
                    {item["case_number"]}
                </strong>

                <br>

                {item["title"]}

            </div>


            <div>

                {item["parties"] or "-"}

            </div>


            <div>

                <span class="status">
                    {item["status"] or "-"}
                </span>

            </div>


            <div>

                <a
                    class="button secondary"
                    href="{url_for(
                        'case_view',
                        case_id=item['id']
                    )}"
                >
                    {tr("view_case")}
                </a>

            </div>

        </div>

        """

    if not rows:

        if case_number or name:

            rows = f"""

            <div class="empty">

                <h2>
                    {tr("no_results")}
                </h2>

                <p>
                    {tr("try_again")}
                </p>

            </div>

            """

        else:

            rows = f"""

            <div class="empty">

                <h2>
                    🔎
                </h2>

                <p>
                    {tr("search_instruction")}
                </p>

            </div>

            """

    content = f"""

    <div class="card">

        <h1>
            🔎
            {tr("search_case")}
        </h1>

        <p>
            {tr("search_instruction")}
        </p>

        <form method="get">

            <div class="search-box">

                <label>

                    {tr("case_number")}

                    <input
                        name="case_number"
                        value="{case_number}"
                        placeholder="MCTC-2026-001"
                    >

                </label>


                <label>

                    {tr("party_name")}

                    <input
                        name="name"
                        value="{name}"
                        placeholder="Juan Dela Cruz"
                    >

                </label>


                <button
                    class="button"
                    type="submit"
                >
                    🔎
                    {tr("search_button")}
                </button>

            </div>

        </form>

    </div>


    <div class="card">

        <h2>
            {tr("results")}
        </h2>

        {rows}

    </div>

    """

    return page(
        tr("search"),
        content
    )


# ============================================================
# PUBLIC CASE VIEW
# ============================================================

@app.route("/case/<int:case_id>")
def case_view(case_id):

    connection = get_db()

    case = connection.execute(
        """
        SELECT *
        FROM cases
        WHERE id = ?
        """,
        (case_id,)
    ).fetchone()

    hearings = connection.execute(
        """
        SELECT *
        FROM hearings
        WHERE case_id = ?
        ORDER BY hearing_date, hearing_time
        """,
        (case_id,)
    ).fetchall()

    connection.close()

    if case is None:

        return page(
            tr("case_not_found"),
            f"""
            <div class="card empty">

                <h1>
                    {tr("case_not_found")}
                </h1>

            </div>
            """
        ), 404

    hearing_rows = ""

    for hearing in hearings:

        hearing_rows += f"""

        <div class="notice">

            <h3>
                📅
                {hearing["hearing_date"]}
            </h3>

            <p>
                <strong>
                    {tr("hearing_time")}:
                </strong>

                {hearing["hearing_time"] or "-"}
            </p>

            <p>
                <strong>
                    {tr("courtroom")}:
                </strong>

                {hearing["courtroom"] or "-"}
            </p>

            <p>
                <strong>
                    {tr("purpose")}:
                </strong>

                {hearing["purpose"] or "-"}
            </p>

        </div>

        """

    content = f"""

    <div class="card">

        <span class="status">
            {case["status"] or "-"}
        </span>

        <h1>
            {case["case_number"]}
        </h1>

        <h2>
            {case["title"]}
        </h2>

        <p>
            <strong>
                {tr("case_type")}:
            </strong>

            {case["case_type"] or "-"}
        </p>

        <p>
            <strong>
                {tr("parties")}:
            </strong>

            {case["parties"] or "-"}
        </p>

    </div>


    <div class="card">

        <h2>
            {tr("summary")}
        </h2>

        <p>
            {case["public_summary"] or "-"}
        </p>

    </div>


    <div class="card">

        <h2>
            📅
            {tr("hearing_schedule")}
        </h2>

        {
            hearing_rows
            or
            f"<div class='empty'>{tr('no_hearings')}</div>"
        }

    </div>

    """

    return page(
        case["case_number"],
        content
    )


# ============================================================
# HEARINGS
# ============================================================

@app.route("/hearings")
def hearings():

    connection = get_db()

    rows = connection.execute(
        """
        SELECT
            hearings.*,
            cases.case_number,
            cases.title
        FROM hearings
        JOIN cases
        ON hearings.case_id = cases.id
        ORDER BY
            hearing_date,
            hearing_time
        """
    ).fetchall()

    connection.close()

    html = ""

    for item in rows:

        html += f"""

        <div class="notice">

            <h2>
                {item["case_number"]}
            </h2>

            <p>
                {item["title"]}
            </p>

            <p>
                <strong>
                    {tr("hearing_date")}:
                </strong>

                {item["hearing_date"]}
            </p>

            <p>
                <strong>
                    {tr("hearing_time")}:
                </strong>

                {item["hearing_time"] or "-"}
            </p>

            <p>
                <strong>
                    {tr("courtroom")}:
                </strong>

                {item["courtroom"] or "-"}
            </p>

            <p>
                <strong>
                    {tr("purpose")}:
                </strong>

                {item["purpose"] or "-"}
            </p>

        </div>

        """

    content = f"""

    <div class="card">

        <h1>
            📅
            {tr("hearing_schedule")}
        </h1>

        <p>
            {
                "Only published hearing information is shown here."
                if lang() == "en"
                else
                "Ang nailathalang impormasyon lamang tungkol sa pagdinig ang ipinapakita rito."
            }
        </p>

    </div>


    <div class="card">

        {
            html
            or
            f"<div class='empty'>{tr('no_hearings')}</div>"
        }

    </div>

    """

    return page(
        tr("hearings"),
        content
    )


# ============================================================
# NOTICES
# ============================================================

@app.route("/notices")
def notices():

    connection = get_db()

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

    for item in rows:

        title = (
            item["title_fil"]
            if lang() == "fil"
            else item["title_en"]
        )

        body = (
            item["body_fil"]
            if lang() == "fil"
            else item["body_en"]
        )

        html += f"""

        <div class="notice">

            <span class="status">
                {item["notice_type"]}
            </span>

            <h2>
                {title}
            </h2>

            <p>
                {body}
            </p>

        </div>

        """

    content = f"""

    <div class="card">

        <h1>
            📢
            {tr("official_notices")}
        </h1>

        <p>
            {tr("suspension")}
        </p>

    </div>


    <div class="card">

        {
            html
            or
            f"<div class='empty'>{tr('no_notices')}</div>"
        }

    </div>

    """

    return page(
        tr("notices"),
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
            ⚖️
            {tr("about_title")}
        </h1>

        <h2>
            {COURT_NAME}
        </h2>

        <p>
            {
                "This website is intended to provide approved public information concerning court cases, hearing schedules, and official notices."
                if lang() == "en"
                else
                "Ang website na ito ay nilalayon na magbigay ng aprubadong pampublikong impormasyon tungkol sa mga kaso, iskedyul ng pagdinig, at mga opisyal na abiso."
            }
        </p>

    </div>


    <div class="card">

        <h2>
            {tr("contact")}
        </h2>

        <p>
            <strong>
                {tr("address")}:
            </strong>
            <br>
            {COURT_ADDRESS}
        </p>

        <p>
            <strong>
                {tr("telephone")}:
            </strong>
            <br>
            {COURT_PHONE}
        </p>

    </div>


    <div class="card">

        <h2>
            {tr("privacy")}
        </h2>

        <p>
            {tr("privacy_text")}
        </p>

    </div>

    """

    return page(
        tr("about"),
        content
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if session.get("staff_id"):

        return redirect(
            url_for(
                "dashboard"
            )
        )

    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                ""
            )
            .strip()
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
            WHERE username = ?
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

            session["staff_id"] = staff["id"]

            session["role"] = staff["role"]

            session["language"] = "en"

            session["theme"] = "light"

            audit(
                "LOGIN"
            )

            return redirect(
                url_for(
                    "dashboard"
                )
            )

        flash(
            tr("login_error"),
            "danger"
        )

    content = f"""

    <div class="login">

        <div class="card">

            <div class="center">

                <img
                    src="{url_for(
                        'static',
                        filename=LOGO
                    )}"
                    alt="Court Seal"
                    style="
                        width:120px;
                        height:120px;
                        object-fit:contain;
                    "
                >

                <h1>
                    🔐
                    {tr("staff_login")}
                </h1>

                <p class="muted">
                    {tr("login_help")}
                </p>

            </div>


            <form
                method="post"
                autocomplete="off"
            >

                <label>

                    {tr("username")}

                    <input
                        type="text"
                        name="username"
                        autocomplete="username"
                        required
                    >

                </label>


                <label>

                    {tr("password")}

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
                    🔐
                    {tr("sign_in")}
                </button>

            </form>


            <div class="notice">

                <strong>
                    {tr("authorized")}
                </strong>

                <p>
                    {tr("credentials_hidden")}
                </p>

            </div>

        </div>

    </div>

    """

    return page(
        tr("staff_login"),
        content
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    session.modified = True

    flash(
        tr("logout_success"),
        "success"
    )

    response = redirect(
        url_for(
            "home"
        )
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-cache, no-store, "
        "must-revalidate"
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

@app.route("/staff")
@app.route("/dashboard")
@staff_required
def dashboard():

    connection = get_db()

    case_count = connection.execute(
        "SELECT COUNT(*) FROM cases"
    ).fetchone()[0]

    hearing_count = connection.execute(
        "SELECT COUNT(*) FROM hearings"
    ).fetchone()[0]

    notice_count = connection.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    recent = connection.execute(
        """
        SELECT *
        FROM cases
        ORDER BY updated_at DESC
        LIMIT 10
        """
    ).fetchall()

    connection.close()

    recent_html = ""

    for item in recent:

        recent_html += f"""

        <tr>

            <td>
                {item["case_number"]}
            </td>

            <td>
                {item["title"]}
            </td>

            <td>
                {item["status"] or "-"}
            </td>

            <td>

                <a
                    class="button secondary"
                    href="{url_for(
                        'edit_case',
                        case_id=item['id']
                    )}"
                >
                    {tr("edit")}
                </a>

            </td>

        </tr>

        """

    content = f"""

    <div class="admin-header">

        <div>

            <h1>
                {tr("staff_dashboard")}
            </h1>

            <p>
                {tr("welcome_staff")}
            </p>

        </div>

        <div>

            <a
                class="button"
                href="{url_for('new_case')}"
            >
                + {tr("add_case")}
            </a>

        </div>

    </div>


    <div class="grid grid-3">

        <div class="card">

            <div class="kpi">
                {case_count}
            </div>

            <strong>
                {tr("manage_cases")}
            </strong>

        </div>


        <div class="card">

            <div class="kpi">
                {hearing_count}
            </div>

            <strong>
                {tr("manage_hearings")}
            </strong>

        </div>


        <div class="card">

            <div class="kpi">
                {notice_count}
            </div>

            <strong>
                {tr("manage_notices")}
            </strong>

        </div>

    </div>


    <div class="card">

        <h2>
            {tr("recent_cases")}
        </h2>

        <div style="overflow-x:auto;">

            <table>

                <thead>

                    <tr>

                        <th>
                            {tr("case_number")}
                        </th>

                        <th>
                            {tr("case_information")}
                        </th>

                        <th>
                            {tr("status")}
                        </th>

                        <th>
                            {tr("edit")}
                        </th>

                    </tr>

                </thead>

                <tbody>

                    {
                        recent_html
                        or
                        f'''
                        <tr>
                            <td colspan="4">
                                {tr("no_cases")}
                            </td>
                        </tr>
                        '''
                    }

                </tbody>

            </table>

        </div>

    </div>


    <div class="card">

        <h2>
            🔐
            {tr("security")}
        </h2>

        <p>
            {tr("security_text")}
        </p>

        <p>
            {tr("credentials_hidden")}
        </p>

    </div>

    """

    return page(
        tr("dashboard"),
        content
    )


# ============================================================
# NEW CASE
# ============================================================

@app.route(
    "/staff/cases/new",
    methods=["GET", "POST"]
)
@staff_required
def new_case():

    if request.method == "POST":

        case_number = request.form.get(
            "case_number",
            ""
        ).strip()

        title = request.form.get(
            "title",
            ""
        ).strip()

        case_type = request.form.get(
            "case_type",
            ""
        ).strip()

        parties = request.form.get(
            "parties",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Pending"
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
                (
                    "Case number and title are required."
                    if lang() == "en"
                    else
                    "Kinakailangan ang numero at pamagat ng kaso."
                ),
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
                        case_type,
                        parties,
                        status,
                        public_summary,
                        internal_notes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_number,
                        title,
                        case_type,
                        parties,
                        status,
                        public_summary,
                        internal_notes,
                        now(),
                        now()
                    )
                )

                connection.commit()

                audit(
                    "CREATE CASE " + case_number
                )

                connection.close()

                flash(
                    tr("case_saved"),
                    "success"
                )

                return redirect(
                    url_for(
                        "dashboard"
                    )
                )

            except sqlite3.IntegrityError:

                connection.close()

                flash(
                    (
                        "That case number already exists."
                        if lang() == "en"
                        else
                        "Mayroon nang kasong gumagamit ng numerong iyon."
                    ),
                    "danger"
                )

    content = case_form(
        None
    )

    return page(
        tr("new_case"),
        content
    )


# ============================================================
# CASE FORM
# ============================================================

def case_form(case):

    if case:

        case_number = case["case_number"]

        title = case["title"]

        case_type = case["case_type"] or ""

        parties = case["parties"] or ""

        status = case["status"] or ""

        public_summary = (
            case["public_summary"]
            or ""
        )

        internal_notes = (
            case["internal_notes"]
            or ""
        )

        action = url_for(
            "edit_case",
            case_id=case["id"]
        )

        heading = tr("edit_case")

    else:

        case_number = ""

        title = ""

        case_type = ""

        parties = ""

        status = "Pending"

        public_summary = ""

        internal_notes = ""

        action = url_for(
            "new_case"
        )

        heading = tr("new_case")

    return f"""

    <div class="card">

        <h1>
            {heading}
        </h1>

        <form
            method="post"
            action="{action}"
        >

            <label>

                {tr("case_number")}

                <input
                    name="case_number"
                    value="{case_number}"
                    required
                    {"readonly" if case else ""}
                >

            </label>


            <label>

                Case Title

                <input
                    name="title"
                    value="{title}"
                    required
                >

            </label>


            <label>

                {tr("case_type")}

                <input
                    name="case_type"
                    value="{case_type}"
                >

            </label>


            <label>

                {tr("parties")}

                <textarea
                    name="parties"
                >{parties}</textarea>

            </label>


            <label>

                {tr("status")}

                <select name="status">

                    <option
                        {"selected" if status == "Pending" else ""}
                    >
                        Pending
                    </option>

                    <option
                        {"selected" if status == "Active" else ""}
                    >
                        Active
                    </option>

                    <option
                        {"selected" if status == "Resolved" else ""}
                    >
                        Resolved
                    </option>

                    <option
                        {"selected" if status == "Postponed" else ""}
                    >
                        Postponed
                    </option>

                    <option
                        {"selected" if status == "Suspended" else ""}
                    >
                        Suspended
                    </option>

                </select>

            </label>


            <label>

                {tr("summary")}

                <textarea
                    name="public_summary"
                >{public_summary}</textarea>

            </label>


            <label>

                Internal Notes

                <textarea
                    name="internal_notes"
                >{internal_notes}</textarea>

            </label>


            <div class="actions">

                <button
                    class="button"
                    type="submit"
                >
                    💾
                    {tr("save")}
                </button>

                <a
                    class="button secondary"
                    href="{url_for('dashboard')}"
                >
                    {tr("cancel")}
                </a>

            </div>

        </form>

    </div>

    """


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

        flash(
            tr("case_not_found"),
            "danger"
        )

        return redirect(
            url_for(
                "dashboard"
            )
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        case_type = request.form.get(
            "case_type",
            ""
        ).strip()

        parties = request.form.get(
            "parties",
            ""
        ).strip()

        status = request.form.get(
            "status",
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
                case_type = ?,
                parties = ?,
                status = ?,
                public_summary = ?,
                internal_notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                title,
                case_type,
                parties,
                status,
                public_summary,
                internal_notes,
                now(),
                case_id
            )
        )

        connection.commit()

        connection.close()

        audit(
            "UPDATE CASE "
            + case["case_number"]
        )

        flash(
            tr("case_saved"),
            "success"
        )

        return redirect(
            url_for(
                "dashboard"
            )
        )

    return page(
        tr("edit"),
        case_form(case)
    )


# ============================================================
# DELETE CASE
# ============================================================

@app.route(
    "/staff/cases/<int:case_id>/delete",
    methods=["POST"]
)
@staff_required
def delete_case(case_id):

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

        flash(
            tr("case_not_found"),
            "danger"
        )

        return redirect(
            url_for(
                "dashboard"
            )
        )

    connection.execute(
        """
        DELETE FROM hearings
        WHERE case_id = ?
        """,
        (case_id,)
    )

    connection.execute(
        """
        DELETE FROM cases
        WHERE id = ?
        """,
        (case_id,)
    )

    connection.commit()

    connection.close()

    audit(
        "DELETE CASE "
        + case["case_number"]
    )

    flash(
        tr("case_deleted"),
        "success"
    )

    return redirect(
        url_for(
            "dashboard"
        )
    )


# ============================================================
# STAFF CASE LIST
# ============================================================

@app.route("/staff/cases")
@staff_required
def staff_cases():

    query = request.args.get(
        "q",
        ""
    ).strip()

    connection = get_db()

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
                "%" + query + "%"
            )
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

        <tr>

            <td>
                {case["case_number"]}
            </td>

            <td>
                {case["title"]}
            </td>

            <td>
                {case["status"] or "-"}
            </td>

            <td>

                <div class="actions">

                    <a
                        class="button secondary"
                        href="{url_for(
                            'edit_case',
                            case_id=case['id']
                        )}"
                    >
                        ✏️
                        {tr("edit")}
                    </a>


                    <form
                        method="post"
                        action="{url_for(
                            'delete_case',
                            case_id=case['id']
                        )}"
                        onsubmit="return confirm(
                            '{{ tr("delete_confirm") }}'
                        );"
                    >

                        <button
                            class="button danger"
                            type="submit"
                        >
                            🗑
                            {tr("delete")}
                        </button>

                    </form>

                </div>

            </td>

        </tr>

        """

    content = f"""

    <div class="card">

        <div class="admin-header">

            <div>

                <h1>
                    {tr("case_management")}
                </h1>

                <p>
                    {tr("find_edit_delete")}
                </p>

            </div>

            <a
                class="button"
                href="{url_for('new_case')}"
            >
                +
                {tr("new_case")}
            </a>

        </div>


        <form method="get">

            <label>

                Search

                <input
                    name="q"
                    value="{query}"
                    placeholder="Case number or party name"
                >

            </label>

            <button
                class="button"
                type="submit"
            >
                🔎
                {tr("search_button")}
            </button>

        </form>

    </div>


    <div class="card">

        <div style="overflow-x:auto;">

            <table>

                <thead>

                    <tr>

                        <th>
                            {tr("case_number")}
                        </th>

                        <th>
                            {tr("case_information")}
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

                    {
                        rows
                        or
                        f'''
                        <tr>
                            <td colspan="4">
                                {tr("no_cases")}
                            </td>
                        </tr>
                        '''
                    }

                </tbody>

            </table>

        </div>

    </div>

    """

    return page(
        tr("manage_cases"),
        content
    )


# ============================================================
# STAFF HEARING CREATION
# ============================================================

@app.route(
    "/staff/hearings/new",
    methods=["GET", "POST"]
)
@staff_required
def new_hearing():

    connection = get_db()

    cases = connection.execute(
        """
        SELECT id, case_number, title
        FROM cases
        ORDER BY case_number
        """
    ).fetchall()

    connection.close()

    if request.method == "POST":

        case_id = request.form.get(
            "case_id"
        )

        hearing_date = request.form.get(
            "hearing_date"
        )

        hearing_time = request.form.get(
            "hearing_time"
        )

        courtroom = request.form.get(
            "courtroom"
        )

        purpose = request.form.get(
            "purpose"
        )

        connection = get_db()

        connection.execute(
            """
            INSERT INTO hearings
            (
                case_id,
                hearing_date,
                hearing_time,
                courtroom,
                purpose
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                case_id,
                hearing_date,
                hearing_time,
                courtroom,
                purpose
            )
        )

        connection.commit()

        connection.close()

        audit(
            "CREATE HEARING"
        )

        flash(
            (
                "Hearing added successfully."
                if lang() == "en"
                else
                "Matagumpay na naidagdag ang pagdinig."
            ),
            "success"
        )

        return redirect(
            url_for(
                "dashboard"
            )
        )

    options = ""

    for case in cases:

        options += f"""

        <option value="{case["id"]}">
            {case["case_number"]}
            -
            {case["title"]}
        </option>

        """

    content = f"""

    <div class="card">

        <h1>
            {tr("add_hearing")}
        </h1>

        <form method="post">

            <label>

                {tr("case_number")}

                <select
                    name="case_id"
                    required
                >

                    {options}

                </select>

            </label>


            <label>

                {tr("hearing_date")}

                <input
                    type="date"
                    name="hearing_date"
                    required
                >

            </label>


            <label>

                {tr("hearing_time")}

                <input
                    type="time"
                    name="hearing_time"
                >

            </label>


            <label>

                {tr("courtroom")}

                <input
                    name="courtroom"
                >

            </label>


            <label>

                {tr("purpose")}

                <textarea
                    name="purpose"
                ></textarea>

            </label>


            <button
                class="button"
                type="submit"
            >
                💾
                {tr("save")}
            </button>

        </form>

    </div>

    """

    return page(
        tr("add_hearing"),
        content
    )


# ============================================================
# STAFF NOTICE CREATION
# ============================================================

@app.route(
    "/staff/notices/new",
    methods=["GET", "POST"]
)
@staff_required
def new_notice():

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

        published = (
            1
            if request.form.get(
                "published"
            )
            else 0
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
                published,
                now()
            )
        )

        connection.commit()

        connection.close()

        audit(
            "CREATE NOTICE"
        )

        flash(
            (
                "Notice created successfully."
                if lang() == "en"
                else
                "Matagumpay na nagawa ang abiso."
            ),
            "success"
        )

        return redirect(
            url_for(
                "dashboard"
            )
        )

    content = f"""

    <div class="card">

        <h1>
            {tr("add_notice")}
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

                English Information

                <textarea
                    name="body_en"
                    required
                ></textarea>

            </label>


            <label>

                Filipino Information

                <textarea
                    name="body_fil"
                    required
                ></textarea>

            </label>


            <label>

                {tr("notice_type")}

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
                        Cancellation
                    </option>

                    <option>
                        Holiday
                    </option>

                </select>

            </label>


            <label>

                <input
                    type="checkbox"
                    name="published"
                    checked
                    style="width:auto;"
                >

                {tr("publish")}

            </label>


            <button
                class="button"
                type="submit"
            >
                💾
                {tr("save")}
            </button>

        </form>

    </div>

    """

    return page(
        tr("add_notice"),
        content
    )


# ============================================================
# STAFF PROFILE
# ============================================================

@app.route("/staff/profile")
@staff_required
def profile():

    connection = get_db()

    staff = connection.execute(
        """
        SELECT
            username,
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
        )
    ).fetchone()

    connection.close()

    content = f"""

    <div class="card">

        <h1>
            👤
            {tr("profile")}
        </h1>

        <p>
            <strong>
                {tr("role")}:
            </strong>

            {staff["role"]}
        </p>

        <p>
            <strong>
                {tr("active")}:
            </strong>

            {
                tr("active")
                if staff["active"]
                else tr("inactive")
            }
        </p>

        <p>
            <strong>
                Created:
            </strong>

            {staff["created_at"]}
        </p>

        <div class="notice">

            🔐

            {tr("credentials_hidden")}

        </div>

    </div>

    """

    return page(
        tr("profile"),
        content
    )


# ============================================================
# STARTUP
# ============================================================

init_database()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
