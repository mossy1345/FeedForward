import csv
import datetime
import pytz
import requests
import urllib
import uuid

from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, get_flashed_messages
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return render_template("accessdenied.html"), 403
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or session.get("account_type") != role:
                return render_template("accessdenied.html"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator



