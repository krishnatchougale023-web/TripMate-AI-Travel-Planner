from flask import Flask, render_template, request, Response, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from openai import OpenAI
import re
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# =======================================
# MYSQL CONNECTION
# =======================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="tripmate"
)

cursor = db.cursor()

# =======================================
# AI CONNECTION
# =======================================

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


# =======================================
# HOME
# =======================================

@app.route("/")
def home():
    return render_template("trip.html")


# =======================================
# LOGIN
# =======================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return render_template(
                "login.html",
                error="Account does not exist. Please sign up first."
            )

        if not check_password_hash(user["password"], password):
            return render_template(
                "login.html",
                error="Incorrect password."
            )

        session["user_email"] = user["email"]
        session["user_name"] = user["name"]

        return redirect(url_for("plan_trip"))

    return render_template("login.html")


@app.route("/profile")
def profile():

    user_email = session.get("user_email")

    if not user_email:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT name, email, phone, gender, city
        FROM users
        WHERE email = %s
        """,
        (user_email,)
    )

    user = cursor.fetchone()
    cursor.close()

    return render_template("profile.html", user=user)


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    session.pop("user_name", None)

    return redirect(url_for("home"))


# =======================================
# SIGNUP
# =======================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "")
        city = request.form.get("city", "").strip()
        travel_preference = request.form.get("travel_preference", "")
        travel_type = request.form.get("travel_type", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Phone number validation
        if not re.fullmatch(r"[0-9]{10}", phone):
            return render_template(
                "signup.html",
                phone_error="Invalid phone number. Enter exactly 10 digits."
            )

        # Password validation
        if len(password) > 14 or not re.search(r"[^A-Za-z0-9]", password):
            return render_template(
                "signup.html",
                password_error="Wrong password."
            )

        # Confirm password validation
        if password != confirm_password:
            return render_template(
                "signup.html",
                confirm_error="Passwords do not match. Please enter the same password."
            )

        # Check email in MySQL
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return render_template(
                "signup.html",
                error="Email already registered."
            )

        # Hash password
        hashed_password = generate_password_hash(password)

        # Save user in MySQL
        cursor.execute(
            """
            INSERT INTO users
            (name, email, phone, gender, city, travel_preference, travel_type, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                name,
                email,
                phone,
                gender,
                city,
                travel_preference,
                travel_type,
                hashed_password
            )
        )

        db.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


# =======================================
# TRAVEL GUIDES
# =======================================

@app.route("/travel-guides")
def travel_guides():
    return render_template("travelGuides.html")


# =======================================
# PLAN TRIP
# =======================================

@app.route("/plan-trip")
def plan_trip():

    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("planTrip.html")

# =======================================
# MY TRIPS
# =======================================

@app.route("/my-trips")
def my_trips():

    user_email = session.get("user_email")

    if not user_email:
        return redirect(url_for("login"))

    trip_cursor = db.cursor()

    trip_cursor.execute(
        """
        SELECT trips.id,
               trips.start_point,
               trips.destination,
               trips.days,
               trips.budget,
               trips.people,
               trips.trip_plan,
               trips.created_at
        FROM trips
        JOIN users ON trips.user_id = users.id
        WHERE users.email = %s
        ORDER BY trips.created_at DESC
        """,
        (user_email,)
    )

    trips = trip_cursor.fetchall()

    trip_cursor.close()

    return render_template(
        "myTrips.html",
        trips=trips
    )

    # =======================================
# VIEW SINGLE TRIP
# =======================================

@app.route("/view-trip/<int:trip_id>")
def view_trip(trip_id):

    user_email = session.get("user_email")

    if not user_email:
        return redirect(url_for("login"))

    trip_cursor = db.cursor()

    trip_cursor.execute(
        """
        SELECT trips.id,
               trips.start_point,
               trips.destination,
               trips.days,
               trips.budget,
               trips.people,
               trips.trip_plan,
               trips.created_at
        FROM trips
        JOIN users ON trips.user_id = users.id
        WHERE trips.id = %s
        AND users.email = %s
        """,
        (trip_id, user_email)
    )

    trip = trip_cursor.fetchone()

    trip_cursor.close()

    if not trip:
        return redirect(url_for("my_trips"))

    return render_template(
        "viewTrip.html",
        trip=trip
    )


# =======================================
# CONTACT
# =======================================

@app.route("/contact")
def contact():
    return render_template("contact.html")


# =======================================
# GENERATE TRIP
# =======================================

@app.route("/generate-trip", methods=["POST"])
def generate_trip():

    start_point = request.form["start_point"]
    place = request.form["place"]
    days = request.form["days"]
    budget = request.form["budget"]
    people = request.form["people"]

    prompt = f"""
Create a simple, attractive and practical travel itinerary.

Starting Point: {start_point}
Destination: {place}
Duration: {days} Days
Number of Travelers: {people}
Total Budget: ₹{budget}

First estimate the approximate road travel distance and travel time
from {start_point} to {place}.

Then create the complete trip plan according to the given number
of days, travelers and total budget.

The entire trip MUST stay within the total budget of ₹{budget}.

Calculate an approximate budget for:
Travel / Transportation
Hotel / Stay
Food
Local Transportation
Activities / Entry Fees
Other Expenses
Total Estimated Cost
Remaining Budget

The estimated total cost must NOT exceed ₹{budget}.

If the budget is low, suggest affordable options.
If the budget is higher, suggest better accommodation and activities
while still staying within the given budget.

IMPORTANT:
Starting Point: {start_point} is ONLY for calculating the approximate
distance and travel time.

Do NOT include any tourist places, attractions or sightseeing
locations from the Starting Point in the day-wise itinerary.

All day-wise places MUST be tourist places or sightseeing locations
in the Destination: {place} or its nearby tourist area.

Use exactly this structure:

Trip to {place} ({days} Days)

Starting Point: {start_point}
Destination: {place}
Approximate Distance: Give the approximate distance from {start_point} to {place}.
Approximate Travel Time: Give the approximate travel time from {start_point} to {place}.

Day 1
- Destination place
- Destination place
- Destination place

Day 2
- Destination place
- Destination place
- Destination place

Continue until Day {days}.

Top Attractions
- Important tourist places from {place}.
- Important tourist places from {place}.

Best Food to Try
- Popular local food.
- Popular local food.

Estimated Budget
Travel / Transportation:
₹...

Hotel / Stay:
₹...

Food:
₹...

Local Transportation:
₹...

Activities / Entry Fees:
₹...

Other Expenses:
₹...

Total Estimated Cost:
₹...

Remaining Budget:
₹...

Destination History
Write a short history of {place}.

Rules:
- Do NOT use tables.
- Do NOT use markdown symbols such as #, **, | or ---.
- Do NOT include timings in the day-wise itinerary.
- Use simple English.
- Keep each point short.
- Match the itinerary with {days} days.
- Keep the complete trip within ₹{budget}.
- Distance and travel time must be approximate.
- Do not invent an exact route or exact fare.
- Do not include Starting Point tourist places in any day.
- Day-wise locations must belong to the Destination or nearby Destination area.

Finish with:

Have a Safe and Happy Journey!
"""

    # =======================================
    # AI GENERATES THE TRIP
    # =======================================

    response = client.chat.completions.create(
        model="openrouter/free",
        extra_body={
            "provider": {
                "sort": "latency"
            }
        },
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    trip = response.choices[0].message.content
    print("LOGGED USER:", session.get("user_email"))
    # Save original trip plan for download
    session["trip_plan"] = trip

    print(trip)

    # =======================================
    # SAVE GENERATED TRIP IN MYSQL
    # =======================================

    user_email = session.get("user_email")

    if user_email:

        trip_cursor = db.cursor()

        trip_cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (user_email,)
        )

        user = trip_cursor.fetchone()

        if user:

            user_id = user[0]

            trip_cursor.execute(
                """
                INSERT INTO trips
                (user_id, start_point, destination, days, budget, people, trip_plan)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    start_point,
                    place,
                    days,
                    budget,
                    people,
                    trip
                )
            )

            db.commit()

        trip_cursor.close()

    # =======================================
    # CONVERT HEADINGS INTO HTML
    # =======================================

    trip = re.sub(
        r"^Starting Point:?$",
        "<h2>Starting Point</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Destination:?$",
        "<h2>Destination</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Approximate Distance:?$",
        "<h2>Approximate Distance</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Approximate Travel Time:?$",
        "<h2>Approximate Travel Time</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Day\s+(\d+):?$",
        r"<h2>Day \1</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Top Attractions:?$",
        "<h2>Top Attractions</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Best Food to Try:?$",
        "<h2>Best Food to Try</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Estimated Budget:?$",
        "<h2>Estimated Budget</h2>",
        trip,
        flags=re.MULTILINE
    )

    trip = re.sub(
        r"^Destination History:?$",
        "<h2>Destination History</h2>",
        trip,
        flags=re.MULTILINE
    )

    lines = trip.split("\n")
    formatted = ""

    headings = {
        "Starting Point",
        "Destination",
        "Approximate Distance",
        "Approximate Travel Time",
        "Top Attractions",
        "Best Food to Try",
        "Estimated Budget",
        "Destination History",
        "Travel Tips"
    }

    budget_labels = {
        "Travel / Transportation",
        "Hotel / Stay",
        "Food",
        "Local Transportation",
        "Activities / Entry Fees",
        "Other Expenses",
        "Total Estimated Cost",
        "Remaining Budget"
    }

    pending_bullets = []

    def add_bullets():
        nonlocal pending_bullets, formatted

        if not pending_bullets:
            return

        if len(pending_bullets) == 1:
            formatted += f"<p>{pending_bullets[0]}</p>"
        else:
            formatted += "<ul>"

            for item in pending_bullets:
                formatted += f"<li>{item}</li>"

            formatted += "</ul>"

        pending_bullets = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line:
            add_bullets()
            i += 1
            continue

        # Main title
        if line.startswith("Trip to"):
            add_bullets()
            formatted += f"<h2 class='trip-title'>{line}</h2>"
            i += 1
            continue

        # Section headings
        clean_heading = line.rstrip(":")

        if clean_heading in headings:
            add_bullets()
            formatted += f"<h2>{clean_heading}</h2>"
            i += 1
            continue

        # Budget label + amount
        if clean_heading in budget_labels:

            add_bullets()

            amount = ""

            if i + 1 < len(lines):

                next_line = lines[i + 1].strip()

                if next_line.startswith("₹"):
                    amount = next_line
                    i += 1

            if amount:

                formatted += (
                    f"<p class='budget-line'>"
                    f"<span>{clean_heading}:</span> {amount}"
                    f"</p>"
                )

            else:

                formatted += (
                    f"<p class='budget-line'>"
                    f"<span>{clean_heading}:</span>"
                    f"</p>"
                )

            i += 1
            continue

        # Day headings
        day_match = re.match(
            r"^Day\s+(\d+):?$",
            line,
            re.IGNORECASE
        )

        if day_match:

            add_bullets()

            formatted += f"<h2>Day {day_match.group(1)}</h2>"

            i += 1
            continue

        # Safe Journey message
        if line.startswith("-"):

            clean_line = line[1:].strip()

            if clean_line == "Have a Safe and Happy Journey!":

                add_bullets()

                formatted += (
                    '<p class="journey-message">'
                    'Have a Safe and Happy Journey!'
                    '</p>'
                )

                i += 1
                continue

            pending_bullets.append(clean_line)

            i += 1
            continue

        if line == "Have a Safe and Happy Journey!":

            add_bullets()

            formatted += (
                '<p class="journey-message">'
                'Have a Safe and Happy Journey!'
                '</p>'
            )

            i += 1
            continue

        # Normal paragraph
        add_bullets()

        formatted += f"<p>{line}</p>"

        i += 1

    add_bullets()

    trip = formatted

    return render_template(
        "TripResult.html",
        trip=trip
    )


# =======================================
# SUBMIT FEEDBACK
# =======================================




@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():

    name = request.form.get("name", "").strip()
    rating = request.form.get("rating", "")
    message = request.form.get("message", "").strip()

    user_email = session.get("user_email")

    user_id = None
    email = None

    if user_email:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, email FROM users WHERE email = %s",
            (user_email,)
        )

        user = cursor.fetchone()
        cursor.close()

        if user:
            user_id = user["id"]
            email = user["email"]

    # Feedback database मध्ये save करा
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO feedback
        (user_id, name, email, rating, message)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            user_id,
            name,
            email,
            rating,
            message
        )
    )

    db.commit()
    cursor.close()

    print("New Feedback:")
    print("Name:", name)
    print("Rating:", rating)
    print("Message:", message)

    return "", 204


# =======================================
# DOWNLOAD TRIP PLAN
# =======================================

@app.route("/download-trip")
def download_trip():

    trip = session.get("trip_plan")

    if not trip:
        return "No trip plan available."

    return Response(
        trip,
        mimetype="text/plain",
        headers={
            "Content-Disposition":
            "attachment; filename=TripMate_Trip_Plan.txt"
        }
    )


# =======================================
# RUN APP
# =======================================

if __name__ == "__main__":
    app.run(debug=True)