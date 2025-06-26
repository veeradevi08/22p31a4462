from flask import Flask, jsonify, request, redirect, abort
from flask_cors import CORS
import datetime
import random
import string
import requests
import time

CLIENT_ID = "a4b2d021-de02-4c58-b2a7-29f203d307bc"
CLIENT_SECRET = "EkmKExUYkdTGchtY"

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJ2ZWxpc2V0dGl2ZWVyYWRldmlAZ21haWwuY29tIiwiZXhwIjoxNzUwOTIwNzU5LCJpYXQiOjE3NTA5MTk4NTksImlzcyI6IkFmZm9yZCBNZWRpY2FsIFRlY2hub2xvZ2llcyBQcml2YXRlIExpbWl0ZWQiLCJqdGkiOiI1MWM4ODRjNy1lMmQwLTQ0ZDYtYmVhYy1mMjMwZDRlZWM2MDAiLCJsb2NhbGUiOiJlbi1JTiIsIm5hbWUiOiJ2ZWVyYWRldmkgdmVsaXNldHRpIiwic3ViIjoiYTRiMmQwMjEtZGUwMi00YzU4LWIyYTctMjlmMjAzZDMwN2JjIn0sImVtYWlsIjoidmVsaXNldHRpdmVlcmFkZXZpQGdtYWlsLmNvbSIsIm5hbWUiOiJ2ZWVyYWRldmkgdmVsaXNldHRpIiwicm9sbE5vIjoiMjJwMzFhNDQ2MiIsImFjY2Vzc0NvZGUiOiJORndnUlQiLCJjbGllbnRJRCI6ImE0YjJkMDIxLWRlMDItNGM1OC1iMmE3LTI5ZjIwM2QzMDdiYyIsImNsaWVudFNlY3JldCI6IkVrbUtFeFVZa2RUR2NodFkifQ.ciDBq6OpPwmTklOvjXa9y1BssVi1mNmR3iokyvpcFlA"
TOKEN_EXPIRY = 1750920759

REGISTRATION_API_URL = "http://20.244.56.144/evaluation-service/register"
AUTH_API_URL = "http://20.244.56.144/evaluation-service/auth"
LOG_API_URL = "http://20.244.56.144/evaluation-service/logs"

def refresh_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRY
    auth_payload = {
        "email": "velisettiveeradevi@gmail.com",
        "name": "veeradevi velisetti",
        "rollNo": "22p31a4462",
        "mobileNo": "7989221534",
        "githubUsername": "veeradevi08",
        "accessCode": "NFwgRT",
        "clientID": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }
    try:
        response = requests.post(AUTH_API_URL, json=auth_payload)
        response.raise_for_status()
        data = response.json()
        ACCESS_TOKEN = data.get("access_token")
        TOKEN_EXPIRY = time.time() + data.get("expires_in", 3600)
        print("LOG [SYSTEM]: Successfully refreshed access token.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"LOG [SYSTEM_ERROR]: Failed to refresh access token: {e}")
        ACCESS_TOKEN = None
        TOKEN_EXPIRY = 0
        return False

def log_event(level, message, shortcode=None, original_url=None, additional_data=None):
    global ACCESS_TOKEN, TOKEN_EXPIRY

    if ACCESS_TOKEN is None or time.time() >= TOKEN_EXPIRY - 60:
        if not refresh_access_token():
            print(f"LOG [CRITICAL_ERROR]: Cannot send log, failed to obtain/refresh access token for level={level}, message={message}")
            return

    log_payload = {
        "stack": "backend",
        "level": level.lower(),
        "package": "handler",
        "message": message
    }

    if shortcode:
        log_payload["message"] += f" [Shortcode: {shortcode}]"
    if original_url:
        log_payload["message"] += f" [Original URL: {original_url}]"
    if additional_data:
        log_payload["message"] += f" [Data: {additional_data}]"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    try:
        response = requests.post(LOG_API_URL, json=log_payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"LOG [LOGGING_FAILED]: Failed to send log to external server: {e} | Payload: {log_payload}")

app = Flask(__name__)
CORS(app)

short_urls_db = {}

def generate_unique_shortcode(length=7):
    chars = string.ascii_letters + string.digits
    while True:
        shortcode = ''.join(random.choice(chars) for _ in range(length))
        if shortcode not in short_urls_db:
            return shortcode

def is_valid_url(url):
    return url.startswith('http://') or url.startswith('https://')

def get_iso8601_timestamp(dt_object):
    if dt_object.tzinfo is None:
        dt_object = dt_object.replace(tzinfo=datetime.timezone.utc)
    return dt_object.isoformat(timespec='seconds').replace('+00:00', 'Z')

@app.route('/shorturls', methods=['POST'])
def create_short_url():
    log_event("INFO", "Received request to create short URL.")
    data = request.get_json()

    if not data:
        log_event("WARNING", "Missing request body or invalid JSON.", additional_data={"raw_data": request.data.decode()})
        abort(400, description="Request body is missing or not valid JSON.")

    original_url = data.get('url')
    validity_minutes = data.get('validity', 30)
    custom_shortcode = data.get('shortcode')

    if not original_url or not isinstance(original_url, str) or not is_valid_url(original_url):
        log_event("WARNING", f"Invalid or missing URL: {original_url}")
        abort(400, description="Invalid or missing 'url' in request. Must be a valid HTTP/HTTPS URL string.")

    if not isinstance(validity_minutes, int) or validity_minutes <= 0:
        log_event("WARNING", f"Invalid validity period: {validity_minutes}", original_url=original_url)
        abort(400, description="Validity must be a positive integer in minutes.")

    shortcode_to_use = None
    if custom_shortcode:
        if not isinstance(custom_shortcode, str) or not custom_shortcode.isalnum() or not (4 <= len(custom_shortcode) <= 10):
            log_event("WARNING", f"Invalid custom shortcode format: {custom_shortcode}", original_url=original_url)
            abort(400, description="Custom shortcode must be an alphanumeric string between 4 and 10 characters.")

        if custom_shortcode in short_urls_db:
            log_event("WARNING", f"Custom shortcode already exists: {custom_shortcode}", original_url=original_url)
            abort(409, description=f"Custom shortcode '{custom_shortcode}' already in use. Please choose another.")
        shortcode_to_use = custom_shortcode
    else:
        shortcode_to_use = generate_unique_shortcode()

    creation_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = creation_time + datetime.timedelta(minutes=validity_minutes)

    short_urls_db[shortcode_to_use] = {
        "original_url": original_url,
        "creation_time": creation_time,
        "expiry_time": expiry_time,
        "total_clicks": 0,
        "click_data": []
    }
    log_event("INFO", f"Short URL created.", shortcode=shortcode_to_use, original_url=original_url)

    short_link = f"{request.url_root.rstrip('/')}/{shortcode_to_use}"
    response_data = {
        "shortLink": short_link,
        "expiry": get_iso8601_timestamp(expiry_time)
    }
    return jsonify(response_data), 201

@app.route('/<string:shortcode>', methods=['GET'])
def redirect_short_url(shortcode):
    log_event("INFO", f"Attempting to redirect shortcode.", shortcode=shortcode)
    short_url_info = short_urls_db.get(shortcode)

    if not short_url_info:
        log_event("WARNING", f"Shortcode not found for redirection.", shortcode=shortcode)
        abort(404, description="Short link not found.")

    if short_url_info["expiry_time"] < datetime.datetime.now(datetime.timezone.utc):
        log_event("WARNING", f"Expired shortcode accessed.", shortcode=shortcode, original_url=short_url_info['original_url'])
        abort(410, description="Short link has expired.")

    short_url_info["total_clicks"] += 1
    click_timestamp = datetime.datetime.now(datetime.timezone.utc)

    source = request.referrer if request.referrer else "direct_access"
    coarse_location = "Unknown/Local (Simulated)"

    short_url_info["click_data"].append({
        "timestamp": get_iso8601_timestamp(click_timestamp),
        "source": source,
        "location": coarse_location
    })
    log_event("INFO", f"Redirecting shortcode.", shortcode=shortcode, original_url=short_url_info['original_url'])

    return redirect(short_url_info["original_url"], code=302)

@app.route('/shorturls/<string:shortcode>', methods=['GET'])
def get_short_url_statistics(shortcode):
    log_event("INFO", f"Received request for statistics.", shortcode=shortcode)
    short_url_info = short_urls_db.get(shortcode)

    if not short_url_info:
        log_event("WARNING", f"Shortcode not found for statistics.", shortcode=shortcode)
        abort(404, description="Short link not found.")

    response_data = {
        "total_clicks": short_url_info["total_clicks"],
        "original_url": short_url_info["original_url"],
        "creation_date": get_iso8601_timestamp(short_url_info["creation_time"]),
        "expiry_date": get_iso8601_timestamp(short_url_info["expiry_time"]),
        "detailed_click_data": short_url_info["click_data"]
    }
    log_event("INFO", f"Providing statistics.", shortcode=shortcode)
    return jsonify(response_data)

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(409)
@app.errorhandler(410)
@app.errorhandler(500)
def handle_error(e):
    code = getattr(e, 'code', 500)
    description = getattr(e, 'description', "An unexpected error occurred.")
    log_event("ERROR", f"API Error {code}: {description}", additional_data={"error_details": str(e)})
    return jsonify({"message": description}), code

if __name__ == '__main__':
    print("LOG [SYSTEM]: Attempting to get initial access token on app startup...")
    if not refresh_access_token():
        print("LOG [CRITICAL_ERROR]: Failed to get initial access token. Logging to external server will not work.")
    else:
        print("LOG [SYSTEM]: Initial access token obtained successfully.")

    app.run(debug=True, port=5000)