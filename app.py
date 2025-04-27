from flask import Flask, render_template, request, redirect, url_for, flash, session
import numpy as np
import pandas as pd
import functions as f
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)


# Set your database URL here
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://chalaksetu_user:zVzQNRcri49z4aqBvRzAvDtgZhRZncAf@dpg-d06cfmruibrs73eeoibg-a.ohio-postgres.render.com/chalaksetu'

# Optional but recommended:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

# Create tables (only ONCE)
with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])  # allow GET and POST both
def index():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Search user from database
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            flash("Login successful!", "success")
            return redirect(url_for('welcome'))  # Redirect to welcome page
        else:
            flash("Invalid username or password.", "error")
            return render_template('index.html')  # Stay on login page and show error

    return render_template('index.html')



app.secret_key = "your_secret_key"  # needed for flashing messages and session


# Assuming f.send_email(email) returns (otp, notice)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('signup'))

        otp, notice = f.send_email(email)  # Sending email OTP

        # Save everything in session
        session['generated_otp'] = str(otp)  # important: save OTP as str
        session['username'] = username
        session['email'] = email
        session['password'] = password

        flash(notice, "error")  # Flash the "OTP sent" notice
        return redirect(url_for('verify_otp'))

    return render_template('signup.html')


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form.get("otp")
        actual_otp = session.get('generated_otp')

        print(f"User OTP entered: {user_otp}")
        print(f"Actual OTP: {actual_otp}")

        if user_otp is None or actual_otp is None:
            flash("Session expired or invalid request. Please sign up again.", "error")
            return redirect(url_for('signup'))

        if user_otp.strip() == actual_otp.strip():
            flash("OTP Verified Successfully!", "success")

            username = session.get('username')
            email = session.get('email')
            password = session.get('password')

            try:
                new_user = User(username=username, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                print(f"User {username} inserted successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error inserting user: {e}")
                flash("An error occurred while creating your account.", "error")
                return redirect(url_for('signup'))

            return redirect(url_for('index'))
        else:
            flash("Invalid OTP, please try again.", "error")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')



@app.route("/welcome")
def welcome():
    df = pd.read_csv("datasets/indian_cities_coordinates.csv")
    city_ = list(df['City Name'])
    city_.insert(0, "My Current Location")

    return render_template('welcome.html', city=city_, mechanics_list=[])



@app.route("/start", methods=["POST"])
def start():
    df = pd.read_csv("datasets/indian_cities_coordinates.csv")
    selected_city = request.form.get("selected_city")
    print(f"Selected city: {selected_city}")

    city_ = list(df['City Name'])
    city_.insert(0, "My Current Location")

    mechanics_list = []  # default empty
    if selected_city:
        flash(f"You selected: {selected_city}", "success")
        mechanics_list = f.near_mechnics(selected_city, df)
    else:
        flash("No city selected!", "error")

    return render_template('welcome.html', city=city_, mechanics_list=mechanics_list)


if __name__ == '__main__':
    app.run(debug=True)

