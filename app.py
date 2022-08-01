import re

from random import randrange, choice
from tkinter.tix import Select
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_socketio import SocketIO, send

from helpers import apology, login_required

app = Flask(__name__)

app.config['SECRET'] = 'secret2228'
socketio = SocketIO(app, cors_allowed_origins='*')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///movie4night.db")


@app.route('/')
def index():
    genres = db.execute("SELECT DISTINCT genre FROM movie")
    return render_template('index.html', genres = genres)

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
    genre = request.form.get("genres")
    movies = list()
    try:
        user_id = session['user_id']
    except:
        if str(genre) != "all":
            for movie in db.execute("SELECT id FROM movie WHERE genre = ?",genre):
                movies.append(movie['id'])
        else:
            for movie in db.execute("SELECT id FROM movie"):
                movies.append(movie['id'])
    else:
        if str(genre) != "all":
            for movie in db.execute("SELECT id FROM movie WHERE genre = ? AND id NOT IN (SELECT movie_id FROM users_history WHERE user_id = ? AND status ='watched')",genre,user_id):
                movies.append(movie['id'])
        else:
            for movie in db.execute("SELECT id FROM movie WHERE id NOT IN (SELECT movie_id FROM users_history WHERE user_id = ? AND status ='watched')",user_id):
                movies.append(movie['id'])
    finally:
        try:
            movie_id = choice(movies)
        except:
            return render_template('fail.html')
        film = db.execute("SELECT * FROM movie WHERE id = ?", movie_id)
        return render_template('generated.html', film=film)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changePass():
    if request.method == 'POST':
        if not request.form.get("oldpassword"):
            return render_template("fail.html")
        elif not check_password_hash(db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]['hash'], request.form.get("oldpassword")):
            return render_template("fail.html")
        elif not request.form.get("password"):
            return render_template("fail.html")
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("fail.html")
        elif not re.search(r"[\d]", request.form.get("password")):
            return render_template("fail.html")
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(
            request.form.get("password")), session["user_id"])
        flash("Your password has changed!")
        return redirect("/")
    else:
        return render_template('changepass.html')

@app.route('/add_to_watched',methods = ['POST'])
@login_required
def add_to_watched():
    id = db.execute("SELECT COUNT(id) FROM users_history")[0]['COUNT(id)'] + 1
    db.execute("INSERT INTO users_history(id,user_id,movie_id,status) VALUES(?,?,?,'watched')", id ,session['user_id'], request.form.get('watched'))
    flash("Added to watched")
    return redirect("/")

@app.route('/add',methods=["GET", "POST"])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get("title")
        rating = request.form.get("rating")
        site_rating = request.form.get("site_rating")
        genre = request.form.get("genre")
        image = request.form.get("image")

        db.execute("INSERT INTO movie(title,rating,site_rating,genre,image) VALUES(?,?,?,?,?)", title, rating, site_rating, genre, image)
        return redirect("/add")
    else: 
        genres = db.execute("SELECT DISTINCT genre FROM movie")
        return render_template('add.html', genres = genres)

@app.route("/watched", methods=["GET", "POST"])
@login_required
def table():
        watched = db.execute("SELECT * FROM movie WHERE id IN (SELECT movie_id FROM users_history WHERE status='watched')")
        return render_template('main.html',watched=watched)


@socketio.on('message')
def handle_message(message):
    print("Recieved message: " + message)
    if message != "User connected!":
        send(message, broadcast=True)

@app.route('/chat')
@login_required
def message():
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    return render_template('chat.html', name=name)

if __name__ == '__main__':
    socketio.run(app, port="5001") 

