import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, get_flashed_messages
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/donor", methods=["GET"])
def donor():
    return render_template('donor.html')

@app.route("/test")
def test():
    return render_template('donor.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template('login.html')