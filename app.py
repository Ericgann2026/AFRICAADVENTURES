from flask import Flask, abort, render_template, request, redirect, session, send_from_directory, url_for
import sqlite3
import os
import base64
import requests
from decimal import Decimal

app = Flask(__name__)
USER_MEDIA_DIRECTORY = os.environ.get(
    "USER_MEDIA_DIRECTORY", os.path.join(app.root_path, "static", "media")
)
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(app.root_path, "bookings.db")
)
USER_MEDIA_FILES = {
    "impala-family.jpeg": "WhatsApp Image 2026-08-24 at 2.28.20 PM.jpeg",
    "giraffe.jpeg": "WhatsApp Image 2026-08-24 at 2.36.52 PM.jpeg",
    "deer-path.jpeg": "WhatsApp Image 2026-08-24 at 2.36.53 PM (1).jpeg",
    "langurs.jpeg": "WhatsApp Image 2026-08-24 at 2.36.53 PM (2).jpeg",
    "elk.jpeg": "WhatsApp Image 2026-08-24 at 2.36.53 PM.jpeg",
    "capybara.jpeg": "WhatsApp Image 2026-08-24 at 2.36.54 PM (1).jpeg",
    "impala-grove.jpeg": "WhatsApp Image 2026-08-24 at 2.36.54 PM.jpeg",
    "blackbuck.jpeg": "WhatsApp Image 2026-08-24 at 2.36.55 PM.jpeg",
    "wildebeest.jpeg": "WhatsApp Image 2026-08-24 at 2.36.56 PM.jpeg",
    "ostriches.jpeg": "WhatsApp Image 2026-08-24 at 2.36.58 PM.jpeg",
    "prairie-dogs.jpeg": "WhatsApp Image 2026-08-24 at 2.37.01 PM.jpeg",
    "raccoon.jpeg": "WhatsApp Image 2026-08-24 at 2.37.02 PM.jpeg",
    "wildlife-moment-1.mp4": "WhatsApp Video 2026-08-24 at 2.36.52 PM.mp4",
    "wildlife-moment-2.mp4": "WhatsApp Video 2026-08-24 at 2.37.02 PM.mp4",
}
# ============================================================
# PAYPAL LIVE
# ============================================================

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")

PAYPAL_BASE_URL = "https://api-m.paypal.com"

# Prices are in USD per traveler. Keep this list on the server so a visitor
# cannot alter the amount submitted to PayPal from their browser.
DESTINATION_PRICES = {
    # Kenya tourist sites — $100 USD per traveler.
    "Bamburi Beach": Decimal("100.00"),
    "Fort Jesus": Decimal("100.00"),
    "Nyali Beach": Decimal("100.00"),
    "Diani Beach": Decimal("100.00"),
    "Mt Kenya": Decimal("100.00"),
    "Lake Nakuru": Decimal("100.00"),
    "Tsavo East National Park": Decimal("100.00"),
    "Hells Gate National Park": Decimal("100.00"),
    "Amboseli National Park": Decimal("100.00"),
    "Nairobi National Park": Decimal("100.00"),
    "Maasai Mara National Reserve": Decimal("100.00"),
    "Serengeti": Decimal("500.00"),
    "Serengeti Safari": Decimal("500.00"),
    "Serengeti National Park": Decimal("150.00"),
    "Ngorongoro Conservation Reserve": Decimal("150.00"),
    "Mount Kilimanjaro": Decimal("150.00"),
    "Tarangire National Park": Decimal("150.00"),
    "Ngorongoro Crater": Decimal("400.00"),
    "Zanzibar": Decimal("350.00"),
    "Zanzibar Escape": Decimal("350.00"),
    "Kruger National Park": Decimal("200.00"),
    "Kruger Safari": Decimal("250.00"),
    "Cape Town": Decimal("200.00"),
    "Addo Elephant National Park": Decimal("200.00"),
    "Cape of Good Hope": Decimal("200.00"),
    "Cango Caves": Decimal("200.00"),
    "Cape Point Nature Reserve": Decimal("200.00"),
    "Cape Town Adventure": Decimal("220.00"),
    "Garden Route": Decimal("200.00"),
    "South Africa": Decimal("250.00"),
}

KENYA_PACKAGES = {
    "bamburi-beach": {"name": "Bamburi Beach", "description": "A palm-lined Indian Ocean beach near Mombasa, ideal for a relaxed coastal escape.", "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=85"},
    "fort-jesus": {"name": "Fort Jesus", "description": "Explore Mombasa's historic UNESCO-listed Portuguese fort overlooking the old harbour.", "image": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1600&q=85"},
    "nyali-beach": {"name": "Nyali Beach", "description": "Enjoy soft sands, warm water and an easygoing beach atmosphere on Mombasa's north coast.", "image": "https://images.unsplash.com/photo-1473116763249-2faaef81ccda?auto=format&fit=crop&w=1600&q=85"},
    "diani-beach": {"name": "Diani Beach", "description": "Unwind on brilliant white sand beside the turquoise waters of Kenya's southern coast.", "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=85"},
    "mt-kenya": {"name": "Mt Kenya", "description": "Discover alpine landscapes, forest trails and the dramatic peaks of Kenya's highest mountain.", "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1600&q=85"},
    "lake-nakuru": {"name": "Lake Nakuru", "description": "Spot flamingos, rhinos and other wildlife around this beautiful Rift Valley lake.", "image": "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1600&q=85"},
    "tsavo-east-national-park": {"name": "Tsavo East National Park", "description": "Experience vast savannah, red-dust elephants and classic big-sky safari country.", "image": "/media/wildebeest.jpeg"},
    "hells-gate-national-park": {"name": "Hells Gate National Park", "description": "Walk or cycle among dramatic cliffs, gorges and geothermal scenery.", "image": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=85"},
    "amboseli-national-park": {"name": "Amboseli National Park", "description": "See iconic elephant herds beneath the unforgettable backdrop of Mount Kilimanjaro.", "image": "https://images.unsplash.com/photo-1535338454770-8be927b5a00b?auto=format&fit=crop&w=1600&q=85"},
    "nairobi-national-park": {"name": "Nairobi National Park", "description": "Enjoy a remarkable wildlife experience right beside Kenya's vibrant capital.", "image": "https://images.unsplash.com/photo-1547970810-dc1eac37d174?auto=format&fit=crop&w=1600&q=85"},
    "maasai-mara-national-reserve": {"name": "Maasai Mara National Reserve", "description": "Witness extraordinary wildlife and the great sweep of the Mara savannah, where elephant herds move across the golden plains.", "image": "https://images.unsplash.com/photo-1554490752-3c5a21bf379a?auto=format&fit=crop&w=1600&q=90"},
}

TANZANIA_PACKAGES = {
    "serengeti-national-park": {"name": "Serengeti National Park", "description": "Explore legendary grasslands and remarkable wildlife in one of Africa's greatest safari landscapes.", "image": "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?auto=format&fit=crop&w=1600&q=85"},
    "ngorongoro-conservation-reserve": {"name": "Ngorongoro Conservation Reserve", "description": "Descend into the spectacular crater and encounter an extraordinary concentration of wildlife.", "image": "/media/impala-grove.jpeg"},
    "mount-kilimanjaro": {"name": "Mount Kilimanjaro", "description": "Take in the beauty of Africa's highest mountain and its unforgettable surrounding landscapes.", "image": "https://images.unsplash.com/photo-1650609344968-b9b52a653ed4?auto=format&fit=crop&w=1600&q=85"},
    "tarangire-national-park": {"name": "Tarangire National Park", "description": "Discover ancient baobabs, vast elephant herds and peaceful river valleys on safari.", "image": "/media/ostriches.jpeg"},
}

SOUTH_AFRICA_PACKAGES = {
    "kruger-national-park": {"name": "Kruger National Park", "description": "Search for the Big Five across one of Africa's most celebrated wildlife reserves.", "image": "/media/impala-family.jpeg"},
    "addo-elephant-national-park": {"name": "Addo Elephant National Park", "description": "See magnificent elephant herds in the diverse landscapes of South Africa's Eastern Cape.", "image": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=1600&q=85"},
    "cape-of-good-hope": {"name": "Cape of Good Hope", "description": "Experience dramatic ocean views where rugged cliffs meet the wild Atlantic coastline.", "image": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=1600&q=85"},
    "cango-caves": {"name": "Cango Caves", "description": "Explore extraordinary underground chambers and ancient limestone formations.", "image": "https://images.unsplash.com/photo-1524721696987-b9527df9e512?auto=format&fit=crop&w=1600&q=85"},
    "cape-town": {"name": "Cape Town", "description": "Discover Table Mountain, beautiful beaches and South Africa's vibrant coastal city.", "image": "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1600&q=85"},
    "cape-point-nature-reserve": {"name": "Cape Point Nature Reserve", "description": "Take in sweeping sea views, coastal trails and remarkable wildlife at the peninsula's edge.", "image": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=85"},
}


def get_booking_total(destination, people):
    """Return the USD total for a selected destination and group size."""
    price_per_traveler = DESTINATION_PRICES.get(destination)

    if price_per_traveler is None:
        return None

    try:
        traveler_count = int(people)
    except (TypeError, ValueError):
        return None

    if traveler_count < 1:
        return None

    return (price_per_traveler * traveler_count).quantize(Decimal("0.01"))


def get_paypal_access_token():

    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise Exception("PayPal Live credentials are missing.")

    credentials = f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}"

    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",

        headers={
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },

        data={
            "grant_type": "client_credentials"
        },

        timeout=30
    )

    response.raise_for_status()

    return response.json()["access_token"]


# ============================================================
# CREATE PAYPAL ORDER
# ============================================================

@app.route("/paypal/create-order", methods=["POST"])
def paypal_create_order():

    try:

        data = request.get_json() or {}

        booking_id = data.get("booking_id")

        if not booking_id:
            return {
                "error": "Booking ID is required."
            }, 400

        connection = sqlite3.connect(DATABASE_PATH)

        booking = connection.execute("""
            SELECT id, destination, people
            FROM bookings
            WHERE id = ?
        """, (
            booking_id,
        )).fetchone()

        connection.close()

        if not booking:
            return {
                "error": "Booking not found."
            }, 404

        total = get_booking_total(booking[1], booking[2])

        if total is None:
            return {
                "error": "This booking does not have a valid destination price."
            }, 400

        amount = format(total, ".2f")

        connection = sqlite3.connect(DATABASE_PATH)
        connection.execute("""
            UPDATE bookings
            SET payment_amount = ?, payment_currency = 'USD'
            WHERE id = ?
        """, (amount, booking_id))
        connection.commit()
        connection.close()

        access_token = get_paypal_access_token()

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(booking_id),
                    "description": "Africa Adventures Booking",
                    "amount": {
                        "currency_code": "USD",
                        "value": amount
                    }
                }
            ]
        }

        response = requests.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order_data,
            timeout=30
        )

        if not response.ok:

            print(
                "PayPal CREATE ERROR:",
                response.text
            )

            return {
                "error": "PayPal could not create the order.",
                "details": response.text
            }, response.status_code

        result = response.json()

        connection = sqlite3.connect(DATABASE_PATH)
        connection.execute("""
            UPDATE bookings
            SET paypal_order_id = ?
            WHERE id = ?
        """, (result["id"], booking_id))
        connection.commit()
        connection.close()

        print(
            "PAYPAL ORDER CREATED:",
            result
        )

        return result

    except Exception as error:

        print(
            "PayPal create order error:",
            error
        )

        return {
            "error": "Unable to create PayPal order."
        }, 500


# ============================================================
# CAPTURE PAYPAL ORDER
# ============================================================

@app.route("/paypal/capture-order", methods=["POST"])
def paypal_capture_order():

    try:

        data = request.get_json() or {}

        order_id = data.get("orderID")
        booking_id = data.get("booking_id")

        if not order_id:
            return {
                "success": False,
                "error": "PayPal order ID is required."
            }, 400

        if not booking_id:
            return {
                "success": False,
                "error": "Booking ID is required."
            }, 400

        # Get PayPal access token
        access_token = get_paypal_access_token()

        # Capture the PayPal payment
        response = requests.post(

            f"{PAYPAL_BASE_URL}/v2/checkout/orders/"
            f"{order_id}/capture",

            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },

            json={},

            timeout=30
        )

        if not response.ok:

            print(
                "PayPal CAPTURE ERROR:",
                response.text
            )

            return {
                "success": False,
                "error": "PayPal could not capture the payment.",
                "details": response.text
            }, response.status_code

        result = response.json()

        print(
            "PAYPAL PAYMENT RESULT:",
            result
        )

        # Check whether PayPal completed the payment and that the captured
        # order matches the saved booking, currency and exact total.
        if result.get("status") != "COMPLETED":

            return {
                "success": False,
                "error": "Payment was not completed."
            }, 400

        connection = sqlite3.connect(DATABASE_PATH)

        connection.row_factory = sqlite3.Row
        booking = connection.execute("""
            SELECT destination, people, paypal_order_id
            FROM bookings
            WHERE id = ?
        """, (booking_id,)).fetchone()

        expected_total = get_booking_total(
            booking["destination"] if booking else None,
            booking["people"] if booking else None
        )
        captured_unit = (result.get("purchase_units") or [{}])[0]
        captured_amount = ((captured_unit.get("payments") or {}).get("captures") or [{}])[0].get("amount", {})

        if (
            not booking
            or expected_total is None
            or booking["paypal_order_id"] != order_id
            or captured_unit.get("reference_id") != str(booking_id)
            or captured_amount.get("currency_code") != "USD"
            or captured_amount.get("value") != format(expected_total, ".2f")
        ):
            connection.close()
            return {"success": False, "error": "Payment details could not be verified."}, 400

        # Mark booking as paid only after the exact server-side amount is verified.

        connection.execute("""
            UPDATE bookings
            SET payment_status = 'Paid',
                payment_method = 'PayPal'
            WHERE id = ?
        """, (
            booking_id,
        ))

        connection.commit()
        connection.close()

        return {
            "success": True,
            "booking_id": booking_id,
            "order_id": order_id
        }

    except Exception as error:

        print(
            "PayPal capture error:",
            error
        )

        return {
            "success": False,
            "error": "Unable to capture PayPal payment."
        }, 500
# =========================================================
# FLASK SECRET KEY
# =========================================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32))


# =========================================================
# DATABASE
# =========================================================

def create_database():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            destination TEXT NOT NULL,
            people INTEGER NOT NULL,
            travel_date TEXT NOT NULL,
            message TEXT,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'Pending'
        )
    """)

    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(bookings)")
    }

    for column, definition in {
        "payment_amount": "TEXT",
        "payment_currency": "TEXT",
        "paypal_order_id": "TEXT",
    }.items():
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE bookings ADD COLUMN {column} {definition}")

    connection.commit()
    connection.close()


create_database()


# =========================================================
# HOME
# =========================================================

@app.route("/media/<filename>")
def user_media(filename):
    """Serve only the wildlife media explicitly selected for the site."""
    source_name = USER_MEDIA_FILES.get(filename)
    if not source_name:
        abort(404)
    return send_from_directory(USER_MEDIA_DIRECTORY, source_name)


@app.route("/")
def home():
    return render_template(
        "index.html",
        kenya_packages=KENYA_PACKAGES,
        tanzania_packages=TANZANIA_PACKAGES,
        south_africa_packages=SOUTH_AFRICA_PACKAGES,
    )


# =========================================================
# COUNTRIES
# =========================================================

@app.route("/kenya")
def kenya():
    return render_template("kenya.html", packages=KENYA_PACKAGES)


@app.route("/kenya/<package_slug>")
def kenya_package(package_slug):
    package = KENYA_PACKAGES.get(package_slug)
    if package is None:
        abort(404)
    return render_template("kenya_package.html", package=package)


@app.route("/tanzania")
def tanzania():
    return render_template("tanzania.html")


@app.route("/south-africa")
def south_africa():
    return render_template("south-africa.html")


# =========================================================
# OTHER PAGES
# =========================================================

@app.route("/adventures")
def adventures():
    return render_template("adventures.html", kenya_packages=KENYA_PACKAGES)


@app.route("/wildlife")
def wildlife():
    return render_template("wildlife.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/success")
def success():
    # Keep the legacy URL working while using the current confirmation page.
    return redirect(url_for("payment_success", **request.args))


# =========================================================
# BOOKING
# =========================================================

@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":

        name = request.form.get("name", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        destination = request.form.get("destination", "")
        people = request.form.get("people", "1")
        travel_date = request.form.get("travel_date", "")
        message = request.form.get("message", "")

        if get_booking_total(destination, people) is None:
            return "Please select a valid adventure and number of travelers.", 400

        connection = sqlite3.connect(DATABASE_PATH)

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO bookings
            (
                name,
                email,
                phone,
                destination,
                people,
                date,
                message,
                payment_method,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            destination,
            people,
            travel_date,
            message,
            "",
            "Pending"
        ))

        booking_id = cursor.lastrowid

        connection.commit()
        connection.close()

        # Send customer to payment page
        return redirect(
            f"/payment?booking_id={booking_id}"
        )

    destination = request.args.get(
        "destination",
        ""
    )
    kenya_package_names = {package["name"] for package in KENYA_PACKAGES.values()}

    return render_template(
        "booking.html",
        destination=destination,
        destinations={
            name: price for name, price in DESTINATION_PRICES.items()
            if name not in kenya_package_names
        },
        is_kenya_package=destination in kenya_package_names,
    )


# =========================================================
# PAYMENT
# =========================================================

@app.route("/payment", methods=["GET", "POST"])
def payment():

    if request.method == "POST":

        booking_id = request.form.get("booking_id")
        payment_method = request.form.get("payment_method")

        if not booking_id:
            return "Booking ID is missing", 400

        if not payment_method:
            return "Please select a payment method", 400

        connection = sqlite3.connect(DATABASE_PATH)

        connection.execute("""
            UPDATE bookings
            SET payment_method = ?
            WHERE id = ?
        """, (
            payment_method,
            booking_id
        ))

        connection.commit()
        connection.close()

        return redirect(
            f"/payment?booking_id={booking_id}"
        )

    booking_id = request.args.get("booking_id")

    if not booking_id:
        return "Booking ID is missing", 400

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    booking = connection.execute("""
        SELECT *
        FROM bookings
        WHERE id = ?
    """, (
        booking_id,
    )).fetchone()

    connection.close()

    if not booking:
        return "Booking not found", 404

    payment_total = get_booking_total(booking["destination"], booking["people"])

    if payment_total is None:
        return "This booking does not have a valid destination price.", 400

    return render_template(
        "payment.html",
        booking=booking,
        booking_id=booking_id,
        paypal_client_id=PAYPAL_CLIENT_ID,
        payment_total=payment_total,
    )
    # CUSTOMER OPENS PAYMENT PAGE
    booking_id = request.args.get("booking_id")

    if not booking_id:
        return "Booking ID is missing", 400

    return render_template(
        "payment.html",
        booking_id=booking_id
    )

    # -----------------------------------------------------
    # SHOW PAYMENT PAGE
    # -----------------------------------------------------

    booking_id = request.args.get(
        "booking_id"
    )

    if not booking_id:
        return "No booking was provided."

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    booking_data = connection.execute("""
        SELECT *
        FROM bookings
        WHERE id = ?
    """, (
        booking_id,
    )).fetchone()

    connection.close()

    if not booking_data:
        return "Booking not found."

    return render_template(
        "payment.html",
        booking=booking_data,
        destination=booking_data["destination"],
        people=booking_data["people"],
        booking_id=booking_data["id"]
    )


# =========================================================
# CONFIRMATION
# =========================================================
# STEP 2
# =========================================================

@app.route("/confirmation/<int:booking_id>")
def confirmation(booking_id):

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    booking = connection.execute("""
        SELECT *
        FROM bookings
        WHERE id = ?
    """, (
        booking_id,
    )).fetchone()

    connection.close()

    if not booking:
        return "Booking not found."

    return render_template(
        "confirmation.html",
        booking=booking
    )


# =========================================================
# PAYMENT SUCCESS
# =========================================================

@app.route("/payment-success")
def payment_success():

    booking_id = request.args.get(
        "booking_id"
    )

    if not booking_id:
        return "Booking ID is missing."

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        UPDATE bookings
        SET payment_status = 'Paid'
        WHERE id = ?
    """, (
        booking_id,
    ))

    connection.commit()
    connection.close()

    return render_template(
    "payment_success.html",
    booking_id=booking_id
)


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        if username == "admin" and password == "Africa123":

            session["admin_logged_in"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Incorrect username or password."
        )

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):

        return redirect("/admin/login")

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    bookings = connection.execute("""
        SELECT *
        FROM bookings
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        bookings=bookings
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        "/admin/login"
    )


# =========================================================
# DELETE BOOKING
# =========================================================

@app.route(
    "/admin/delete/<int:booking_id>",
    methods=["POST"]
)
def delete_booking(booking_id):

    if not session.get("admin_logged_in"):

        return redirect(
            "/admin/login"
        )

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (
        booking_id,
    ))

    connection.commit()
    connection.close()

    return redirect(
        "/admin"
    )


# =========================================================
# START WEBSITE
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
