import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///movie4night.db")


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":  # if method post do one thing if not another
        if not request.form.get("username"):
            return render_template("fail.html")
        elif not request.form.get("password"):
            return render_template("fail.html")
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("fail.html")
        elif not re.search(r"[\d]", request.form.get("password")):
            return render_template("fail.html")
        elif len(db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))) != 0:
            return render_template("fail.html")

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password")))

        flash("Registered!")
        return render_template("login.html")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("fail.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("fail.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("fail.html")
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Logged in!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route('/generate', methods=['POST'])
def generate():
    film = db.execute("SELECT * FROM movies WHERE id = 1")
    return render_template('generated.html', film=film)

@app.route('/messages')
def messages():
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5001) 