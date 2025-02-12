import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, get_flashed_messages
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import datetime
from functools import wraps

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

@app.route("/recipient", methods=["GET"], endpoint="recipient_page")
def recipient():
    return render_template('recipient.html')

@app.route("/foodbanks", methods=["GET"], endpoint="foodbanks_page")
def foodbanks():
    return render_template('foodbanks.html')

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
    
    if not username or not password or not address or not email or not account_type:
        flash("All fields are required.", "danger")
        return redirect("/signup")
    
    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect("/signup")
    
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect('feedforward.db')
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, address, email, account_type)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, address, email, account_type))
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

@app.route("/unauthorized")
def unauthorized():
    return render_template('unauthorized.html')

if __name__ == "__main__":
    app.run(debug=True)  # Ensures the app runs only when executed directly