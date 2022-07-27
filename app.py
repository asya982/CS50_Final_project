from flask import Flask, render_template, redirect

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def registration():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/messages')
def messages():
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5001)