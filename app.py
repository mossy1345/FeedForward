import os
import sqlite3
import requests
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, get_flashed_messages, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from opencage.geocoder import OpenCageGeocode
import datetime
from functools import wraps

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#configure geocoder
key = 'c181a74ff5a34bf8ab449c4da95aec9c'
geocoder = OpenCageGeocode(key)

conn = sqlite3.connect('feedforward.db')
c = conn.cursor()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/donor", methods=["GET"], endpoint="donor_page")
def donor_page():
    return render_template('donor.html')

@app.route("/admin", methods=["GET"], endpoint="admin_page")
def admin():
    return render_template('admin.html')

#Routes for donations tracker
#------------------------------------------------------------------------------------------------------

#donor routes
@app.route("/donor_donations", methods=["GET"])
def donor_donations():
    user_id = session.get("user_id")  # Ensure the donor is logged in

    conn = sqlite3.connect('feedforward.db')
    cursor = conn.cursor()

    # Fetch current donations for donor (where status is pending)
    cursor.execute("""
        SELECT id, recipient_id, donor_name, eta, donation_description, donor_address, donation_type 
        FROM donations 
        WHERE recipient_id IN (SELECT user_id FROM users WHERE account_type = 'recipient') AND donation_status = 'pending' AND donor_name = (SELECT username FROM users WHERE user_id = ?)
    """, (user_id,))
    current_donations = cursor.fetchall()

    # Fetch past donations for donor (status cancelled)
    cursor.execute("""
        SELECT id, recipient_id, donor_name, eta, donation_description, donor_address, donation_type 
        FROM donations 
        WHERE recipient_id IN (SELECT user_id FROM users WHERE account_type = 'recipient') AND donation_status = 'cancelled' AND donor_name = (SELECT username FROM users WHERE user_id = ?)
    """, (user_id,))
    past_donations = cursor.fetchall()

    conn.close()

    return render_template("donor_donations.html", current_donations=current_donations, past_donations=past_donations)

#cancel donation (for donors)
@app.route("/cancel_donation/<int:donation_id>", methods=["POST"])
def cancel_donation(donation_id):
    conn = sqlite3.connect('feedforward.db')
    cursor = conn.cursor()

    # Update donation status to cancelled
    cursor.execute("""
        UPDATE donations
        SET donation_status = 'cancelled'
        WHERE id = ?
    """, (donation_id,))
    conn.commit()
    conn.close()

    return redirect("/donor_donations")

#recipeint routes
@app.route("/recipient_donations", methods=["GET"])
def recipient_donations():
    user_id = session.get("user_id")  # Ensure the recipient is logged in

    conn = sqlite3.connect('feedforward.db')
    cursor = conn.cursor()

    # Fetch current donations for recipient (status is pending)
    cursor.execute("""
        SELECT id, donor_name, eta, donation_description, donor_address, donation_type 
        FROM donations 
        WHERE recipient_id = ? AND donation_status = 'pending'
    """, (user_id,))
    current_donations = cursor.fetchall()

    # Fetch past donations for recipient (status completed)
    cursor.execute("""
        SELECT id, donor_name, eta, donation_description, donor_address, donation_type 
        FROM donations 
        WHERE recipient_id = ? AND donation_status = 'completed'
    """, (user_id,))
    past_donations = cursor.fetchall()

    conn.close()

    return render_template("recipient_donations.html", current_donations=current_donations, past_donations=past_donations)

#confirm delivery (for recipients)
@app.route("/confirm_delivery/<int:donation_id>", methods=["POST"])
def confirm_delivery(donation_id):
    conn = sqlite3.connect('feedforward.db')
    cursor = conn.cursor()

    # Update donation status to completed
    cursor.execute("""
        UPDATE donations
        SET donation_status = 'completed'
        WHERE id = ?
    """, (donation_id,))
    conn.commit()
    conn.close()

    return redirect("/recipient_donations")


#-------------------------------------------------------------------------------------------------------

def geocode_address(address):
    if not key:
        print("❌ Missing OpenCage API key.")
        return None, None

    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": address,
        "key": key,
        "limit": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            geometry = data["results"][0]["geometry"]
            return geometry["lat"], geometry["lng"]
        else:
            print("⚠️ No results found.")
            return None, None
    except Exception as e:
        print(f"❌ Geocoding failed: {e}")
        return None, None


@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    address = request.form.get("address")
    email = request.form.get("email")
    account_type = request.form.get("account_type")
    bio = request.form.get("bio")
    phone_number = request.form.get("phone_number")  # Optional field

    if not username or not password or not address or not email or not account_type:
        flash("All required fields must be filled.", "danger")
        return redirect("/signup")

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect("/signup")

    # Geocode the address
    latitude, longitude = geocode_address(address)
    if not latitude or not longitude:
        flash("Invalid address. Please enter a valid address.", "danger")
        return redirect("/signup")

    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect('feedforward.db')
        cur = conn.cursor()
        cur.execute("""
    INSERT INTO users (username, password, address, email, account_type, bio, latitude, longitude)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (username, hashed_password, address, email, account_type, bio, latitude, longitude))
        conn.commit()
        conn.close()
        flash("Account successfully created!", "success")
        return redirect("/login")
    except sqlite3.IntegrityError:
        flash("Username or email already exists.", "danger")
        return redirect("/signup")



@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template('login.html')

@app.route("/recipient", methods=["GET", "POST"])
def recipient():
    return render_template('foodbanks.html')

@app.route("/unauthorized")
def unauthorized():
    return render_template('unauthorized.html')

def get_markers():
    conn = sqlite3.connect("feedforward.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, latitude, longitude, address, bio 
        FROM users 
        WHERE account_type = 'recipient'
    """)
    markers = [
        {"user_id": row[0], "username": row[1], "lat": row[2], "lng": row[3], "address": row[4], "bio": row[5]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return markers

@app.route("/api/markers")
def markers():
    return jsonify(get_markers())


@app.route("/donate")
def donate():
    recipient_id = request.args.get("recipient_id")

    if not recipient_id or recipient_id == "undefined":  # Handle missing or undefined IDs
        return "Invalid recipient ID", 400  # Return an error response

    conn = sqlite3.connect("feedforward.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (recipient_id,))
    recipient = cursor.fetchone()
    conn.close()

    recipient_name = recipient[0] if recipient else "Unknown Recipient"

    return render_template("donorform.html", recipient_id=recipient_id, recipient_name=recipient_name)


@app.route("/submit_donation", methods=["POST"])
def submit_donation():
    recipient_id = request.form.get("recipient_id", "").strip()

    if not recipient_id.isdigit():  # Ensure recipient_id is a valid number
        return "Invalid recipient ID", 400  # Return an error response

    recipient_id = int(recipient_id)  # Now it's safe to convert

    donor_name = request.form["donor_name"]
    donor_address = request.form["donor_address"]
    donation_type = request.form["donation_type"]
    donation_description = request.form["donation_description"]
    eta = request.form["donation_datetime"]

    conn = sqlite3.connect("feedforward.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO donations 
        (recipient_id, donor_name, donor_address, donation_type, donation_description, eta) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (recipient_id, donor_name, donor_address, donation_type, donation_description, eta))
    conn.commit()
    conn.close()

    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)  # Ensures the app runs only when executed directly