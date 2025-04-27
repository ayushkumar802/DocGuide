import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import requests

def send_email(receiver_email):
    otp = random.randint(1000,9999)
    sender_email = "chalaksetu@gmail.com"
    sender_password = "cdxa ztyl jjig zkev"

    subject = "Email Verification"
    body = f"""Hi there!!\nThis is your otp: {otp} for ChalakSetu App. This OTP will be valid for next 24 hours."""

    # Create the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        notice = f"Email sent successfully to {receiver_email}"
    except Exception as e:
        notice = f"Failed to send email. Error: {e}"

    return otp, notice


def get_my_location():
    response = requests.get("https://ipinfo.io")
    data = response.json()

    loc = data.get("loc")  # format: "lat,lng"
    if loc:
        lat, lng = map(float, loc.split(","))
        return lat, lng
    else:
        return None


def get_osm_mechanics(lat, lon, radius=10000):
    overpass_url = "http://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      node["shop"="car_repair"](around:{radius},{lat},{lon});
      way["shop"="car_repair"](around:{radius},{lat},{lon});
      relation["shop"="car_repair"](around:{radius},{lat},{lon});
    );
    out center;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        print("Request failed:", response.status_code)
        return []

    data = response.json()
    elements = data.get('elements', [])

    if not elements:
        print("No mechanics found in this area.")
        return []

    mechanics = []
    for element in elements:
        name = element.get('tags', {}).get('name', 'Unnamed Mechanic')
        lat = element.get('lat') or element.get('center', {}).get('lat')
        lon = element.get('lon') or element.get('center', {}).get('lon')
        mechanics.append({
            'name': name,
            'latitude': lat,
            'longitude': lon
        })

    return mechanics[:4]

def near_mechnics(city,df):
    if city == "My Current Location":
        lat, lon = get_my_location()
    else:
        lat = list(df[df['City Name']==city]['Latitude'])[0]
        lon = list(df[df['City Name']==city]['Longitude'])[0]
    mechanics = get_osm_mechanics(lat, lon)
    list_ = []
    if mechanics:
        for i, m in enumerate(mechanics, 1):
            list_.append(f"{i}. {m['name']} at ({m['latitude']}, {m['longitude']})")
    else:
        list_.append("No mechanic shops found nearby.")
    return list_