from flask import Flask, render_template, request, redirect, url_for, flash, session
import numpy as np
import pandas as pd
import functions
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


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


from flask import session, redirect, url_for

@app.route('/', methods=['GET', 'POST'])
def home():
    logged_in = session.get('logged_in', False)
    if request.method == 'POST':
        if not logged_in:
            flash("Please log in to use this feature.", "error")
            return redirect(url_for('home'))  # redirect so flash can show
        if request.form['prompt-input'] == "":
            flash("Enter your prompt", "error")
            return redirect(url_for('home'))
        else:
            symptom_text = request.form['prompt-input']

            # Load model and vectorizer
            with open("models/model.pkl", "rb") as f1:
                model = pickle.load(f1)

            with open("models/vectorizer.pkl", "rb") as f2:
                vectorizer = pickle.load(f2)

            doctor_df = pd.read_csv('datasets/doctors_dataset_1000_v2.csv')


            # Make prediction
            specialization, definition, list_ = functions.predict(symptom_text, doctor_df, vectorizer, model, definition_)

            # Store in session temporarily
            session['specialization'] = specialization
            session['definition'] = definition
            session['list_'] = list_

            # Redirect to prevent resubmission
            return redirect(url_for('home'))

    # GET request: extract from session once and clear it
    specialization = session.pop('specialization', "")
    definition = session.pop('definition', "")
    list_ = session.pop('list_', [])

    return render_template('home.html',
                           specialization=specialization,
                           definition=definition,
                           list_=list_,
                           logged_in=session.get('logged_in', False))


@app.route('/terms')
def terms():
    logged_in = session.get('logged_in', False)
    return render_template('terms.html', logged_in=logged_in)


@app.route("/signin", methods=["GET", "POST"])  # allow GET and POST both
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Search user from database
        user = User.query.filter_by(username=username).first()

        # if user and user.password == password:
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for('home'))

        else:
            flash("Wrong user or password!", "error")
            return render_template('signin.html')  # Stay on login page and show error

    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Unregistered Email","error")
            return redirect(url_for("forget"))
        otp, notice = functions.send_email(email, user.username)  # Sending email OTP

        session['generated_otp'] = str(otp)
        session['username'] = user.username
        session['email'] = email
        # session['password'] = password
        session['password'] = generate_password_hash(password)  # hash before saving
        flash(notice, "success")
        return redirect(url_for("verify_otp"))

    return render_template('forget.html')


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        exist_user=User.query.filter(User.email == email).first()
        if exist_user:
            flash("This email is already registered", "error")
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('signup'))

        otp, notice = functions.send_email(email,username)  # Sending email OTP
        print(otp)
        # Save everything in session
        session['generated_otp'] = str(otp)  # important: save OTP as str
        session['username'] = username
        session['email'] = email
        # session['password'] = password
        session['password'] = generate_password_hash(password)  # hash before saving

        flash(notice, "success")  # Flash the "OTP sent" notice
        return redirect(url_for('verify_otp'))

    return render_template('signup.html')


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form.get("otp")
        actual_otp = session.get('generated_otp')


        if user_otp is None or actual_otp is None:
            flash("Session expired or invalid request. Please sign up again.", "error")
            return redirect(url_for('signup'))

        if user_otp.strip() == actual_otp.strip():
            flash("OTP Verified Successfully!", "success")

            username = session.get('username')
            email = session.get('email')
            password = session.get('password')

            try:
                existing_user = User.query.filter(User.email == email).first()
                if existing_user:
                    db.session.delete(existing_user)
                    db.session.commit()

                new_user = User(username=username, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                print(f"User {username} inserted successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error inserting user: {e}")
                flash("An error occurred while creating your account.", "error")
                return redirect(url_for('signup'))

            return redirect(url_for('signin'))
        else:
            flash("Invalid OTP, please try again.", "error")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    logged_in = session.get('logged_in', False)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # For now, you can just flash it or print it to console
        notice = functions.receive_email(name,email,message)
        flash(notice, 'success')
        return redirect('/contact')

    return render_template('contact.html', logged_in=logged_in)

@app.route('/about')
def about():
    logged_in = session.get('logged_in', False)
    return render_template('about.html', logged_in=logged_in)


if __name__ == '__main__':
    app.run(debug=True)

