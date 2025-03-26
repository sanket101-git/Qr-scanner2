import os
import pickle
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__, template_folder="templates")  # Ensure the templates folder is recognized

# Set a secret key for session handling
app.secret_key = os.urandom(24)

# Google API Credentials & Sheets Configuration
CLIENT_SECRET_FILE = '/etc/secrets/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SPREADSHEET_ID = '1GTXyh9LW-DTVDkcFhumMwWDn9I8jZWTV1fLDqncoGl4'  # Replace with your actual Google Sheets ID

# Function to get Google API credentials
def get_credentials():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or credentials.expired and credentials.refresh_token:
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        flow.redirect_uri = url_for('oauth2callback', _external=True)
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        session['state'] = state
        return redirect(authorization_url)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return credentials

# OAuth2 callback route
@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    credentials = flow.fetch_token(authorization_response=request.url)

    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)

    return redirect(url_for('index'))

# Function to append scanned QR data to Google Sheets
def append_data_to_sheet(data):
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    values = [[data]]
    body = {'values': values}

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:A",  # Append to the first column in Sheet1
        valueInputOption="RAW",
        body=body
    ).execute()

    return result

# ✅ Serve the HTML page
@app.route("/")
def index():
    return render_template("index.html")  # This will load the frontend

# ✅ Route to save QR data to Google Sheets
@app.route("/save_qr_data", methods=["POST"])
def save_qr_data():
    data = request.get_json()
    qr_data = data.get("qr_data")

    if qr_data:
        append_data_to_sheet(qr_data)  # Save to Google Sheets
        return jsonify({"message": f"QR Code data '{qr_data}' has been saved successfully!"}), 200

    return jsonify({"message": "No QR data received."}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
