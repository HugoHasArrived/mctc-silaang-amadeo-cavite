# ============================================================
# IMPORTANT FIXES FOR YOUR APP
# ============================================================
#
# 1. The website ALWAYS starts in public mode.
# 2. Opening the website never logs a visitor into staff mode.
# 3. Staff login is only created after successful authentication.
# 4. Logging out completely clears the session.
# 5. Username/password are NEVER displayed on the website.
# 6. Dark mode uses high-contrast text and surfaces.
# 7. Light mode uses high-contrast text and surfaces.
# 8. The public search page explains exactly how to search.
# 9. The staff dashboard explains what each action does.
#
# Replace the matching parts of your app.py with these sections.
# ============================================================


# ============================================================
# SESSION CONFIGURATION
# ============================================================

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("RENDER") is not None
)


# ============================================================
# PUBLIC DEFAULT SESSION
# ============================================================

@app.before_request
def configure_public_session():

    # DO NOT create a staff session automatically.
    #
    # A visitor arriving at "/" remains a visitor.
    #
    # The only way "staff_id" should exist is after a
    # successful staff login.

    if "language" not in session:
        session["language"] = "en"

    if "theme" not in session:
        session["theme"] = "light"


# ============================================================
# LOGIN CHECK
# ============================================================

def is_logged_in():

    return (
        session.get("staff_id")
        is not None
    )


# ============================================================
# LOGGED-IN USER HELPER
# ============================================================

def logged_in_username():

    if not is_logged_in():
        return None

    return session.get(
        "username"
    )


# ============================================================
# LOGGED-IN ROLE HELPER
# ============================================================

def logged_in_role():

    if not is_logged_in():
        return None

    return session.get(
        "role"
    )


# ============================================================
# COMPLETE LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=["GET", "POST"]
)
def logout():

    username = session.get(
        "username"
    )

    # Record logout before destroying the session.
    if username:

        try:

            write_audit(
                "LOGOUT",
                username
            )

        except Exception:

            pass

    # Completely destroy the authentication session.
    session.clear()

    # Create a fresh public session.
    session["language"] = "en"
    session["theme"] = "light"

    response = redirect(
        url_for("home")
    )

    # Prevent the browser from showing a cached
    # staff dashboard after logout.
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
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def staff_login():

    # A logged-in staff member should not see
    # the login page again.
    if is_logged_in():

        return redirect(
            url_for(
                "dashboard"
            )
        )

    if request.method == "POST":

        username = clean_text(
            request.form.get(
                "username",
                ""
            ),
            100
        )

        password = request.form.get(
            "password",
            ""
        )

        connection = get_database()

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

            # Remove EVERYTHING from a previous
            # anonymous or expired session.
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

            # Set normal public preferences.
            session["language"] = "en"
            session["theme"] = "light"

            write_audit(
                "LOGIN",
                username
            )

            response = redirect(
                url_for(
                    "dashboard"
                )
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

        flash(
            "The username or password is incorrect.",
            "danger"
        )

    # ========================================================
    # DO NOT SHOW USERNAME OR PASSWORD HERE
    # ========================================================

    content = """
    <div class="form">

        <div
            class="login-header"
        >

            <div
                class="login-icon"
            >
                ⚖️
            </div>

            <span
                class="eyebrow"
            >
                AUTHORIZED ACCESS
            </span>

            <h1>
                Staff Login
            </h1>

            <p
                class="muted"
            >
                Sign in to access the
                court staff portal.
            </p>

        </div>


        <form
            method="post"
            autocomplete="off"
        >

            <label>

                Username

                <input
                    type="text"
                    name="username"
                    autocomplete="username"
                    placeholder="Enter your username"
                    required
                >

            </label>


            <label>

                Password

                <input
                    type="password"
                    name="password"
                    autocomplete="current-password"
                    placeholder="Enter your password"
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


        <div
            class="login-security-note"
        >

            🔒 Authorized court personnel only.

            <br><br>

            Your login credentials are
            not displayed on this website.

        </div>

    </div>
    """

    return page(
        "Staff Login",
        content
    )


# ============================================================
# PUBLIC SEARCH PAGE
# ============================================================

@app.route(
    "/search"
)
def search():

    case_number = clean_case_number(
        request.args.get(
            "case_number",
            ""
        )
    )

    name = clean_name(
        request.args.get(
            "name",
            ""
        )
    )

    results = []

    if case_number or name:

        connection = get_database()

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


    # ========================================================
    # SEARCH RESULT HTML
    # ========================================================

    results_html = ""

    for case in results:

        results_html += f"""
        <div
            class="search-result"
        >

            <div
                class="result-main"
            >

                <strong
                    class="result-case-number"
                >
                    {case["case_number"]}
                </strong>

                <h3>
                    {case["title"]}
                </h3>

                <p>
                    {case["parties"]}
                </p>

            </div>


            <div>

                <span
                    class="status"
                >
                    {case["status"]}
                </span>

            </div>


            <div>

                <a
                    class="button secondary"
                    href="/case/{case["id"]}"
                >
                    View Case
                </a>

            </div>

        </div>
        """

    if not results_html:

        if case_number or name:

            results_html = """
            <div
                class="empty-state"
            >

                <div
                    class="empty-icon"
                >
                    🔎
                </div>

                <h2>
                    No matching case found
                </h2>

                <p>
                    Check the case number
                    or name and try again.
                </p>

            </div>
            """

        else:

            results_html = """
            <div
                class="empty-state"
            >

                <div
                    class="empty-icon"
                >
                    📋
                </div>

                <h2>
                    Search for a case
                </h2>

                <p>
                    Enter a case number,
                    a party name, or both.
                </p>

            </div>
            """

    # ========================================================
    # SPECIFIC SEARCH INSTRUCTIONS
    # ========================================================

    content = f"""
    <div
        class="page-heading"
    >

        <span
            class="eyebrow"
        >
            PUBLIC CASE INFORMATION
        </span>

        <h1>
            🔎 Search for a Case
        </h1>

        <p
            class="lead"
        >
            Find case information that
            has been approved for public
            viewing.
        </p>

    </div>


    <div
        class="card search-instructions"
    >

        <h2>
            How to search
        </h2>


        <div
            class="instruction-step"
        >

            <span>
                1
            </span>

            <div>

                <strong>
                    Search by Case Number
                </strong>

                <p>
                    Enter the case number
                    exactly as it appears
                    on the court record.
                </p>

                <code>
                    Example:
                    MCTC-2026-001
                </code>

            </div>

        </div>


        <div
            class="instruction-step"
        >

            <span>
                2
            </span>

            <div>

                <strong>
                    Search by Name
                </strong>

                <p>
                    Enter the party or
                    case name.
                </p>

                <code>
                    Example:
                    JUAN DELA CRUZ
                </code>

            </div>

        </div>


        <div
            class="instruction-step"
        >

            <span>
                3
            </span>

            <div>

                <strong>
                    Use Both Fields
                </strong>

                <p>
                    You can enter both
                    the case number and
                    name to narrow the
                    results.
                </p>

            </div>

        </div>


        <div
            class="instruction-warning"
        >

            ⚠️

            <div>

                <strong>
                    Privacy reminder
                </strong>

                <p>
                    Only information approved
                    for public access is shown.
                    Do not attempt to obtain
                    restricted or confidential
                    information through this
                    search.

                </p>

            </div>

        </div>

    </div>


    <div
        class="card"
    >

        <h2>
            Search
        </h2>

        <form
            method="get"
            class="search-form"
        >

            <label>

                Case Number

                <input
                    type="text"
                    name="case_number"
                    value="{case_number}"
                    placeholder="MCTC-2026-001"
                >

            </label>


            <label>

                Name / Party

                <input
                    type="text"
                    name="name"
                    value="{name}"
                    placeholder="JUAN DELA CRUZ"
                >

            </label>


            <button
                class="button"
                type="submit"
            >
                🔎 Search Cases
            </button>

        </form>

    </div>


    <div
        class="card"
    >

        <div
            class="results-heading"
        >

            <h2>
                Results
            </h2>

            <span>
                {len(results)}
                result(s)
            </span>

        </div>

        {results_html}

    </div>
    """

    return page(
        "Search Cases",
        content
    )


# ============================================================
# FRIENDLIER STAFF DASHBOARD
# ============================================================

@app.route(
    "/dashboard"
)
@staff_required
def dashboard():

    connection = get_database()

    total_cases = connection.execute(
        """
        SELECT COUNT(*)
        FROM cases
        """
    ).fetchone()[0]

    total_hearings = connection.execute(
        """
        SELECT COUNT(*)
        FROM hearings
        """
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
        LIMIT 6
        """
    ).fetchall()

    connection.close()

    recent_html = ""

    for case in recent_cases:

        recent_html += f"""
        <div
            class="friendly-case"
        >

            <div>

                <strong>
                    {case["case_number"]}
                </strong>

                <p>
                    {case["title"]}
                </p>

            </div>

            <span
                class="status"
            >
                {case["status"]}
            </span>

            <a
                class="button secondary"
                href="/staff/cases/{case["id"]}"
            >
                Open
            </a>

        </div>
        """

    content = f"""
    <section
        class="friendly-dashboard"
    >

        <span>
            ⚖️ AUTHORIZED STAFF PORTAL
        </span>

        <h1>
            Welcome to the Court Workspace 💜
        </h1>

        <p>
            Use the tools below to manage
            authorized case information,
            hearing schedules, and
            official notices.
        </p>

        <div
            class="staff-actions"
        >

            <a
                href="/staff/cases"
                class="staff-action"
            >

                <div>
                    📋
                </div>

                <strong>
                    Manage Cases
                </strong>

                <span>
                    Search and update
                    case records.
                </span>

            </a>


            <a
                href="/staff/cases/add"
                class="staff-action"
            >

                <div>
                    ➕
                </div>

                <strong>
                    Add Case
                </strong>

                <span>
                    Create a new
                    authorized case record.
                </span>

            </a>


            <a
                href="/staff/notices"
                class="staff-action"
            >

                <div>
                    📢
                </div>

                <strong>
                    Court Notices
                </strong>

                <span>
                    Publish official
                    announcements.
                </span>

            </a>


            <a
                href="/staff/activity"
                class="staff-action"
            >

                <div>
                    📝
                </div>

                <strong>
                    Activity Log
                </strong>

                <span>
                    Review staff activity.
                </span>

            </a>

        </div>

    </section>


    <div
        class="grid grid-four"
    >

        <div class="card stat-card">

            <span>
                Total Cases
            </span>

            <strong>
                {total_cases}
            </strong>

        </div>


        <div class="card stat-card">

            <span>
                Hearings
            </span>

            <strong>
                {total_hearings}
            </strong>

        </div>


        <div class="card stat-card">

            <span>
                Published Notices
            </span>

            <strong>
                {total_notices}
            </strong>

        </div>


        <div class="card stat-card">

            <span>
                Documents
            </span>

            <strong>
                {total_documents}
            </strong>

        </div>

    </div>


    <div class="card">

        <div
            class="results-heading"
        >

            <h2>
                📋 Recently Updated Cases
            </h2>

            <a
                href="/staff/cases"
            >
                View All
            </a>

        </div>


        {recent_html
        or
        "<p>No cases have been entered yet.</p>"}

    </div>


    <div
        class="staff-help"
    >

        <strong>
            💡 Need help?
        </strong>

        <p>
            Start with
            <b>Manage Cases</b>
            to search existing records,
            or choose
            <b>Add Case</b>
            to enter a new authorized
            record.
        </p>

        <p>
            Use
            <b>Court Notices</b>
            only for official notices
            that have been approved
            for publication.
        </p>

    </div>
    """

    response = page(
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

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


# ============================================================
# REPLACE YOUR CSS WITH THESE DARK/LIGHT RULES
# ============================================================

SITE_CSS += """

/* ============================================================
   ACCESSIBLE THEME VARIABLES
   ============================================================ */

:root {

    --purple-dark:
        #42105F;

    --purple:
        #7B2CBF;

    --purple-light:
        #9D4EDD;

    --purple-soft:
        #EFE2F7;

    --background:
        #FAF8FC;

    --surface:
        #FFFFFF;

    --surface-alt:
        #F4EDF8;

    --text:
        #211427;

    --heading:
        #42105F;

    --muted:
        #5E5063;

    --border:
        #D7C9DF;

    --danger:
        #94183D;

    --danger-bg:
        #FFE4EC;

    --success:
        #21613A;

    --success-bg:
        #E0F4E6;

}


/* ============================================================
   DARK MODE
   ============================================================ */

body.dark {

    --background:
        #111014;

    --surface:
        #1F1B24;

    --surface-alt:
        #2A2330;

    --text:
        #FFFFFF;

    --heading:
        #F5DFFF;

    --muted:
        #E0D5E5;

    --border:
        #675675;

    --purple-soft:
        #392645;

    --danger:
        #FFB4C7;

    --danger-bg:
        #451927;

    --success:
        #B8F1C8;

    --success-bg:
        #163523;

}


/* ============================================================
   READABILITY
   ============================================================ */

body {

    background:
        var(--background);

    color:
        var(--text);

}


h1,
h2,
h3,
h4,
h5,
h6 {

    color:
        var(--heading);

}


p,
li,
label,
span {

    color:
        inherit;

}


.muted {

    color:
        var(--muted);

}


.card,
.form,
.stat-card {

    background:
        var(--surface);

    color:
        var(--text);

    border:
        1px solid
        var(--border);

}


input,
textarea,
select {

    background:
        var(--surface);

    color:
        var(--text);

    border:
        1px solid
        var(--border);

}


input::placeholder,
textarea::placeholder {

    color:
        var(--muted);

    opacity:
        .9;

}


code {

    display:
        inline-block;

    background:
        var(--purple-soft);

    color:
        var(--heading);

    padding:
        5px 8px;

    border-radius:
        7px;

}


/* ============================================================
   LOGIN
   ============================================================ */

.login-header {

    text-align:
        center;

    margin-bottom:
        25px;

}


.login-icon {

    font-size:
        55px;

    margin-bottom:
        10px;

}


.login-security-note {

    margin-top:
        20px;

    padding:
        15px;

    border-radius:
        10px;

    background:
        var(--purple-soft);

    color:
        var(--text);

    font-size:
        13px;

}


/* ============================================================
   SEARCH INSTRUCTIONS
   ============================================================ */

.search-instructions {

    border-left:
        5px solid
        var(--purple);

}


.instruction-step {

    display:
        flex;

    gap:
        15px;

    margin:
        20px 0;

}


.instruction-step > span {

    min-width:
        34px;

    height:
        34px;

    border-radius:
        50%;

    display:
        grid;

    place-items:
        center;

    background:
        var(--purple);

    color:
        white;

    font-weight:
        900;

}


.instruction-step strong {

    color:
        var(--heading);

}


.instruction-warning {

    display:
        flex;

    gap:
        12px;

    margin-top:
        20px;

    padding:
        16px;

    border-radius:
        12px;

    background:
        var(--purple-soft);

}


/* ============================================================
   SEARCH RESULTS
   ============================================================ */

.search-result {

    display:
        grid;

    grid-template-columns:
        1fr
        auto
        auto;

    gap:
        20px;

    align-items:
        center;

    padding:
        20px 0;

    border-bottom:
        1px solid
        var(--border);

}


.result-case-number {

    color:
        var(--purple);

}


.result-main h3 {

    margin:
        4px 0;

    color:
        var(--heading);

}


.results-heading {

    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;

    gap:
        15px;

}


.empty-state {

    text-align:
        center;

    padding:
        40px 20px;

}


.empty-icon {

    font-size:
        45px;

}


/* ============================================================
   FRIENDLY DASHBOARD
   ============================================================ */

.friendly-dashboard {

    background:
        linear-gradient(
            135deg,
            #51146F,
            #7B2CBF,
            #9D4EDD
        );

    color:
        white;

    padding:
        35px;

    border-radius:
        22px;

    margin-bottom:
        25px;

}


.friendly-dashboard * {

    color:
        white;

}


.friendly-dashboard h1 {

    color:
        white;

    margin:
        8px 0;

    font-size:
        clamp(
            30px,
            5vw,
            50px
        );

}


.staff-actions {

    display:
        grid;

    grid-template-columns:
        repeat(
            4,
            1fr
        );

    gap:
        14px;

    margin-top:
        25px;

}


.staff-action {

    display:
        block;

    color:
        var(--text);

    background:
        var(--surface);

    padding:
        18px;

    border-radius:
        14px;

    text-decoration:
        none;

}


.staff-action > div {

    font-size:
        30px;

}


.staff-action strong {

    display:
        block;

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


.staff-help {

    background:
        var(--purple-soft);

    color:
        var(--text);

    border-radius:
        15px;

    padding:
        20px;

    margin-top:
        20px;

}


.staff-help strong {

    color:
        var(--heading);

}


@media(
    max-width: 850px
) {

    .staff-actions {

        grid-template-columns:
            1fr 1fr;

    }

}


@media(
    max-width: 600px
) {

    .staff-actions {

        grid-template-columns:
            1fr;

    }

    .search-result {

        grid-template-columns:
            1fr;

    }

    .results-heading {

        align-items:
            flex-start;

        flex-direction:
            column;

    }

}


/* ============================================================
   VERY DARK BACKGROUND PROTECTION
   ============================================================ */

body.dark input:focus,
body.dark textarea:focus,
body.dark select:focus {

    outline:
        3px solid
        rgba(
            210,
            150,
            255,
            .35
        );

}


body.dark .button.secondary {

    background:
        #453052;

    color:
        #FFFFFF;

}


body.dark .status {

    background:
        #453052;

    color:
        #FFFFFF;

}


body.dark .notice {

    background:
        #2A2032;

    color:
        #FFFFFF;

}


/* ============================================================
   PRINT
   ============================================================ */

@media print {

    .site-header,
    .tools,
    footer,
    .button {

        display:
            none !important;

    }

    body {

        background:
            white;

        color:
            black;

    }

    .card {

        box-shadow:
            none;

        border:
            1px solid
            #999;

    }

}
"""


# ============================================================
# IMPORTANT:
# DO NOT PUT LOGIN CREDENTIALS IN THE DASHBOARD
# ============================================================

# DELETE any old code resembling:
#
#   Username: admin
#   Password: admin123
#
# DELETE any:
#
#   demo-login
#   development account
#   admin / admin123
#
# from your HTML.
#
# The login page should contain only the login fields.


# ============================================================
# OPTIONAL: FRIENDLY STAFF LOGOUT BUTTON
# ============================================================

STAFF_LOGOUT_HTML = """
<form
    method="post"
    action="/logout"
    class="nav-form"
>

    <button
        type="submit"
        class="nav-button"
        title="Log out of the staff portal"
    >
        🚪 Log Out
    </button>

</form>
"""


# ============================================================
# IMPORTANT DATABASE STARTUP
# ============================================================

initialize_database()


# ============================================================
# RENDER START
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
