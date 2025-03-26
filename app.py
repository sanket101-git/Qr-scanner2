import os
import pickle
import pandas as pd
from flask import Flask, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)

# Set a secret key for the session
app.secret_key = os.urandom(24)

# Path to the credentials file you downloaded from Google Cloud Console
CLIENT_SECRET_FILE = 'https://github.com/sanket101-git/Qr-scanner2/blob/7d8357d27f44b94c3ee12ef1f4627bfed4ee2195/client_secret_1068304963084-vdm3qlbm4b76k4skdop44gfvan7rghf3.apps.googleusercontent.com.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

# The ID of your Google Sheets document
SPREADSHEET_ID = '1GTXyh9LW-DTVDkcFhumMwWDn9I8jZWTV1fLDqncoGl4'

# Function to authenticate and get credentials
def get_credentials():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    if not credentials or credentials.expired and credentials.refresh_token:
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        flow.redirect_uri = url_for('oauth2callback', _external=True)  # Callback URL for Render
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        session['state'] = state
        return redirect(authorization_url)
    
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    return credentials

# Route to handle OAuth callback
@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)  # Callback URL for Render
    credentials = flow.fetch_token(authorization_response=request.url)
    
    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)
    
    return redirect(url_for('index'))

# Function to append data to Google Sheets
def append_data_to_sheet(data):
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    
    # Prepare the data to append
    values = [[data]]
    body = {'values': values}
    
    # Append the data to the specified Google Sheet
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:A",  # Append to the first column in Sheet1
        valueInputOption="RAW",
        body=body
    ).execute()

    return result

@app.route("/")
def index():
    return "QR Scanner is live. Ready to scan QR codes!"

@app.route("/save_qr_data", methods=["POST"])
def save_qr_data():
    data = request.get_json()
    qr_data = data.get("qr_data")
    
    if qr_data:
        append_data_to_sheet(qr_data)  # Save QR data to Google Sheets
        return jsonify({"message": f"QR Code data '{qr_data}' has been saved successfully!"}), 200
    
    return jsonify({"message": "No QR data received."}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
