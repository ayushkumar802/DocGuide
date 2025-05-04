import requests
import pandas as pd
import re
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import random
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from email.utils import formataddr
import pickle
import nltk
from nltk.data import find

def download_nltk_data():
    try:
        find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    try:
        find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')

download_nltk_data()


def send_email(receiver_email, name):
    otp = random.randint(1000, 9999)
    sender_email = "docguidebussiness@gmail.com"
    sender_password = "naqe dxqo efef xvrm"

    subject = "Email Verification"

    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, sans-serif; color: #000000; padding: 20px;">
      <p>Hi <strong>{name}</strong>,</p>
      <p>Your One-Time Password (OTP) for accessing the <strong>DocGuide App</strong> is:</p>
      <p style="font-size: 20px; font-weight: bold; color: #28a745;">{otp}</p>
      <p>This OTP is valid for the next <strong>24 hours</strong>.</p>
      <p>If you did not request this, please disregard this email.</p>
      <br>
      <p>Thank you,<br>
      <strong>The DocGuide Team</strong></p>
    </body>
    </html>
    """

    # Create the email
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("DocGuide", sender_email))
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        failed = server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        if failed:
            notice = f"Failed to send email to: {', '.join(failed.keys())}"
            return None, notice
        else:
            notice = f"Mail sent successfully to {receiver_email}"
            return otp, notice

    except smtplib.SMTPRecipientsRefused:
        notice = "Invalid email address. Please check the recipient email."
    except smtplib.SMTPAuthenticationError:
        notice = "Authentication failed. Check sender email and app password."
    except Exception as e:
        notice = f"Failed to send email. Error: {e}"

    return None, notice




def receive_email(name, user_email, user_message):
    sender_email = "docguidebussiness@gmail.com"
    sender_password = "naqe dxqo efef xvrm"
    receiver_email = "ayushkumarrio22@gmail.com"

    subject = "User Request"
    html_body = f"""
    You received a request from <b>{name.capitalize()}</b><br>
    <b>Email:</b> {user_email}<br><br>
    <b>Request Message:</b><br>{user_message}
    """

    # Create the email message object
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("DocGuide requests", sender_email))
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        failed = server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        if failed:
            notice = f"Failed to send email to: {', '.join(failed.keys())}"
        else:
            notice = "Email sent successfully"

    except smtplib.SMTPRecipientsRefused:
        notice = "Recipient email address was refused. Please check the email."
    except smtplib.SMTPAuthenticationError:
        notice = "Authentication failed. Check your email and app password."
    except Exception as e:
        notice = f"Failed to send email. Error: {e}"

    return notice



# # Text cleaning function
def preprocess_text(text):
    text = text.lower()
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = re.sub(f"[{string.punctuation}]", " ", text)
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return " ".join(words)


def predict(symptom_text,doctor_df,vectorizer,model,definition_):
    processed_text = preprocess_text(symptom_text)
    input_vec = vectorizer.transform([processed_text])
    specialization = model.predict(input_vec)[0]
    # Filter doctor directory
    doctors = doctor_df[doctor_df['Specialization'] == specialization]
    definition_series = definition_[definition_['Specialization'] == specialization]['Definition']
    definition = definition_series.iloc[0] if not definition_series.empty else "No definition available."

    if not doctors.empty:
        list_=[]
        for _, row in doctors.head(6).iterrows():
            list_.append([row['Doctor Name'],row['Phone Number'],row['City']])
        return specialization,definition,list_
    else:
        return specialization,definition,"No doctors found for this specialization in the directory."
