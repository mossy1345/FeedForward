import csv
import datetime
import pytz
import requests
import urllib
import uuid

from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, get_flashed_messages
from functools import wraps

def login_required(allowed_roles=None):
    def decorator(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            if "user_id" not in session:
                flash("You must be logged in to access this page.", "danger")
                return redirect("/login")

            # Check if the user's role matches allowed roles
            user_role = session.get("user_role")
            if allowed_roles and user_role not in allowed_roles:
                flash("You do not have permission to view this page.", "danger")
                return redirect("/unauthorized")

            return f(*args, **kwargs)
        return wrapped_function
    return decorator



