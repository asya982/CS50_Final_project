import re

from random import randrange, choice
import site
#from tkinter.tix import Select
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import apology, login_required

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
    print(generate_password_hash("123"))
    genres = db.execute("SELECT DISTINCT genre FROM movie")
    return render_template('index.html', genres = genres)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":  # if method post do one thing if not another
        if not request.form.get("username"):
            flash("Must provide username!")
            return redirect('/register')
        elif not request.form.get("password"):
            flash("Must provide password!")
            return redirect('/register')
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords are not the same!")
            return redirect('/register')
        elif not re.search(r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[A-Za-z0-9]{8,}', request.form.get("password")):
            flash("Password does not meet the requirements!")
            return redirect('/register')
        elif len(db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))) != 0:
            flash("Username is already taken!")
            return redirect('/register')

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
            flash("Must provide username!")
            return render_template('login.html')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password!")
            return render_template('login.html')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Wrong password or username!")
            return render_template('login.html')
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
    added = str()
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
            return render_template('congrats.html')
        film = db.execute("SELECT * FROM movie WHERE id = ?", movie_id)
        site_rating = db.execute("SELECT AVG(rating), COUNT(rating) FROM user_rating WHERE film_id = ?", movie_id)
        try:
            added = db.execute("SELECT status FROM  users_history WHERE movie_id=?  AND user_id=?",movie_id,session['user_id'])[0]['status']
        except:
            added = None
            print("хуйня")
        db.execute("UPDATE movie SET site_rating = ? WHERE id = ?", site_rating[0]["AVG(rating)"], movie_id)
        return render_template('generated.html', film=film, site_rating=site_rating,added=added)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changePass():
    if request.method == 'POST':
        if not request.form.get("oldpassword"):
            flash ("Must provide password!")
            return redirect('/changepass')
        elif not check_password_hash(db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]['hash'], request.form.get("oldpassword")):
            flash("Invalid password!")
            return redirect('/changepass')
        elif not request.form.get("password"):
            flash("Invalid password!")
            return redirect('/changepass')
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords do not match!")
            return redirect('/changepass')
        elif not re.search(r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[A-Za-z0-9]{8,}", request.form.get("password")):
            flash("Password does not meet the requirements")
            return redirect('/changepass')
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("password")), session["user_id"])
        flash("Your password has changed!")
        return redirect("/")
    else:
        return render_template('changepass.html')


@app.route('/add_to_watched',methods = ['POST'])
@login_required
def add_to_watched():
    id = db.execute("SELECT COUNT(id) FROM users_history")[0]['COUNT(id)'] + 1
    rate=float(request.form.get('rate'))

    if db.execute("SELECT * FROM users_history WHERE user_id = ? AND movie_id = ? AND status = 'watch later'", session["user_id"], request.form.get('watched')):
        db.execute("UPDATE users_history SET status = 'wathced' WHERE user_id = ? AND movie_id = ?", session["user_id"], request.form.get('watched'))

    db.execute("INSERT INTO users_history(id,user_id,movie_id,status) VALUES(?,?,?,'watched')", id ,session['user_id'], request.form.get('watched'))
    db.execute("INSERT INTO user_rating(user_id,film_id,rating) VALUES(?,?,?)", session['user_id'], request.form.get('watched'),rate)

    site_rating = db.execute("SELECT AVG(rating), COUNT(rating) FROM user_rating WHERE film_id = ?", request.form.get('watched'))
    db.execute("UPDATE movie SET site_rating = ? WHERE id = ?", site_rating[0]["AVG(rating)"], request.form.get('watched'))


    print("totochno to sho trebo" ,request.form.get('watched'))
    flash("Added to watched")
    return redirect("/")


@app.route('/add_to_later',methods = ['POST'])
@login_required
def add_to_laters():
    id = db.execute("SELECT COUNT(id) FROM users_history")[0]['COUNT(id)'] + 1
    db.execute("INSERT INTO users_history(id,user_id,movie_id,status) VALUES(?,?,?,'watch later')", id ,session['user_id'], request.form.get('later'))
    flash("Added to Watch later")
    return redirect("/")


@app.route('/add',methods=["GET", "POST"])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get("title")
        rating = request.form.get("rating")
        genre = request.form.get("genre")
        image = request.form.get("image")


        db.execute("INSERT INTO movie(title,rating,genre,image,site_rating) VALUES(?,?,?,?,?)", title, rating, genre, image, 5.0)

        db.execute("INSERT INTO user_rating (film_id, rating, user_id) VALUES (?, ?, ?)", db.execute("SELECT id FROM movie WHERE title = ?", title)[0]['id'], 5.0, 0)


        return redirect("/add")
    else: 
        genres = db.execute("SELECT DISTINCT genre FROM movie")
        return render_template('add.html', genres = genres)

@app.route("/watched", methods=["GET", "POST"])
@login_required
def table():
    laters=db.execute("SELECT * FROM movie WHERE id IN (SELECT movie_id FROM users_history WHERE status='watch later' AND user_id=?)", session["user_id"])
    watched = db.execute("SELECT * FROM movie WHERE id IN (SELECT movie_id FROM users_history WHERE status='watched' AND user_id=?) ORDER BY title", session["user_id"])
    return render_template('main.html',watched=watched, laters=laters)



@app.route('/chat', methods=["GET", "POST"])
@login_required
def message():
    if request.method == "POST":
        if not request.form.get("message"):
            return redirect("/chat")
        if len(request.form.get("message")) > 255:
            return redirect("/chat")  

        if db.execute("SELECT COUNT(id) FROM chat")[0]["COUNT(id)"] > 75:
            db.execute("DELETE FROM chat WHERE id IN (SELECT id FROM chat LIMIT 10);")

        now = datetime.now().strftime("%H:%M")
        message = request.form.get('message')
        user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]['username']
        db.execute("INSERT INTO chat (sendername, message, time) VALUES (?, ?, ?)", user, message, now)
        return redirect("/chat")
    else:
        name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        messages = db.execute("SELECT * FROM chat")
        return render_template('chat.html', name=name, messages=messages)

if __name__ == '__main__':
    app.run(app) 

