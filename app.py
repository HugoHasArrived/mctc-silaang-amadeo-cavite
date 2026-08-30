from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

# ============================================================
# DEMO STAFF ACCOUNT
# ============================================================
# Username: admin
# Password: admin123
#
# IMPORTANT:
# This is only for the prototype.
# Use a real database and secure account management in production.
# ============================================================

STAFF = {
    "admin": generate_password_hash("admin123")
}


# ============================================================
# DEMO CASE DATA
# ============================================================

CASES = [
    {
        "case_number": "MCTC-2026-001",
        "name": "JUAN DELA CRUZ",
        "type": "Civil",
        "hearing": "September 15, 2026 — 9:00 AM",
        "status": "Scheduled",
        "public_info": (
            "Sample public case information. "
            "Do not enter real confidential information into this demo."
        )
    },
    {
        "case_number": "MCTC-2026-002",
        "name": "MARIA SANTOS",
        "type": "Criminal",
        "hearing": "October 2, 2026 — 1:30 PM",
        "status": "Scheduled",
        "public_info": "Sample public case information."
    }
]


# ============================================================
# COURT NOTICES
# ============================================================

NOTICES = [
    {
        "title_en": "Court Suspension Notices",
        "title_fil": "Mga Abiso sa Pagsuspinde ng Hukuman",

        "text_en": (
            "Check official court announcements for any suspension, "
            "postponement, or cancellation of hearings. This website "
            "does not predict the chance of suspension."
        ),

        "text_fil": (
            "Tingnan ang mga opisyal na abiso ng hukuman para sa anumang "
            "suspensyon, pagpapaliban, o pagkansela ng pagdinig. "
            "Ang website na ito ay hindi humuhula ng posibilidad ng suspensyon."
        )
    }
]


# ============================================================
# PUBLIC HOMEPAGE
# ============================================================

@app.route("/")
def home():
    return render_template(
        "index.html",
        notices=NOTICES
    )


# ============================================================
# PUBLIC CASE SEARCH
# ============================================================

@app.route("/search")
def search():

    case_number = request.args.get(
        "case_number",
        ""
    ).strip().lower()

    name = request.args.get(
        "name",
        ""
    ).strip().lower()

    results = []

    if case_number or name:

        for case in CASES:

            number_match = (
                not case_number
                or case_number in case["case_number"].lower()
            )

            name_match = (
                not name
                or name in case["name"].lower()
            )

            if number_match and name_match:
                results.append(case)

    return render_template(
        "search.html",
        results=results,
        searched=bool(case_number or name)
    )


# ============================================================
# STAFF LOGIN
# ============================================================

@app.route(
    "/staff/login",
    methods=["GET", "POST"]
)
def staff_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username in STAFF
            and check_password_hash(
                STAFF[username],
                password
            )
        ):

            session["staff"] = username

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid staff login.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# STAFF LOGOUT
# ============================================================

@app.route("/staff/logout")
def staff_logout():

    session.pop(
        "staff",
        None
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/staff/dashboard")
def dashboard():

    if "staff" not in session:
        return redirect(
            url_for("staff_login")
        )

    return render_template(
        "dashboard.html",
        cases=CASES,
        notices=NOTICES
    )


# ============================================================
# ADD CASE
# ============================================================

@app.route(
    "/staff/cases/add",
    methods=["POST"]
)
def add_case():

    if "staff" not in session:
        return redirect(
            url_for("staff_login")
        )

    case = {

        "case_number":
            request.form.get(
                "case_number",
                ""
            ).strip(),

        "name":
            request.form.get(
                "name",
                ""
            ).strip(),

        "type":
            request.form.get(
                "type",
                "Civil"
            ).strip(),

        "hearing":
            request.form.get(
                "hearing",
                ""
            ).strip(),

        "status":
            request.form.get(
                "status",
                "Scheduled"
            ).strip(),

        "public_info":
            request.form.get(
                "public_info",
                ""
            ).strip()
    }

    if (
        case["case_number"]
        and case["name"]
    ):

        CASES.append(case)

        flash(
            "Demo case added successfully.",
            "success"
        )

    else:

        flash(
            "Case number and name are required.",
            "error"
        )

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
