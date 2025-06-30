import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import re
from gspread_formatting import (
    CellFormat, Color, TextFormat, format_cell_range
)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

st.set_page_config(page_title="Chicago Road Race", layout="centered")

# Centered logo image using HTML
st.markdown(
    '''
    <div style="text-align: center;">
        <img src="cupcar.png" width="150">
    </div>
    ''',
    unsafe_allow_html=True
)

st.title("NASCAR Chicago Survey")

# Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gsecrets = st.secrets["gspread"]
creds_dict = {
    "type": gsecrets["type"],
    "project_id": gsecrets["project_id"],
    "private_key_id": gsecrets["private_key_id"],
    "private_key": gsecrets["private_key"].replace("\\n", "\n"),
    "client_email": gsecrets["client_email"],
    "client_id": gsecrets["client_id"],
    "auth_uri": gsecrets["auth_uri"],
    "token_uri": gsecrets["token_uri"],
    "auth_provider_x509_cert_url": gsecrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": gsecrets["client_x509_cert_url"],
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Cup Survey")

# Access or create worksheet
target_title = "Chicago 2025"
worksheet_list = spreadsheet.worksheets()
sheet = next((ws for ws in worksheet_list if ws.title.strip().lower() == target_title.lower()), None)

if not sheet:
    sheet = spreadsheet.add_worksheet(title=target_title, rows="100", cols="10")

# Headers setup
headers = ["Timestamp", "Entry Name", "Email", "Chevrolet Driver", "Ford Driver", "Toyota Driver", "Manufacturer", "Lead Lap Count"]
values = sheet.get_all_values()
if not values or values[0] != headers:
    sheet.update("A1:H1", [headers])
    header_format = CellFormat(
        backgroundColor=Color(0.27, 0.27, 0.27),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(sheet, "A1:H1", header_format)

# Form fields
st.header("Entry Name")
entry_name = st.text_input("Please enter your name:")

st.header("Email Address")
email = st.text_input("Enter your email address:")

st.header("1. Best Chevrolet Driver")
q1 = st.radio("Pick a Chevrolet Driver", [
    "Ross Chastain", "Austin Dillon", "Kyle Larson", "Justin Haley", "Kyle Busch",
    "Chase Elliott", "Ty Dillon", "A.J. Allmendinger", "William Byron",
    "Ricky Stenhouse", "Alex Bowman", "Michael McDowell", "Carson Hocevar", "Shane Van Gisbergen"
])
st.markdown("<br>", unsafe_allow_html=True)

st.header("2. Best Ford Driver")
q2 = st.radio("Pick a Ford Driver", [
    "Austin Cindric", "Noah Gragson", "Brad Keselowski", "Ryan Blaney",
    "Chris Buescher", "Josh Berry", "Joey Logano", "Todd Gilliland",
    "Zane Smith", "Cole Custer", "Ryan Preece"
])
st.markdown("<br>", unsafe_allow_html=True)

st.header("3. Best Toyota Driver")
q3 = st.radio("Pick a Toyota Driver", [
    "Denny Hamlin", "Chase Briscoe", "Christopher Bell", "Bubba Wallace",
    "Riley Herbst", "John Hunter Nemechek", "Erik Jones", "Tyler Reddick", "Ty Gibbs"
])
st.markdown("<br>", unsafe_allow_html=True)

st.header("4. Which Manufacturer Wins the Race")
q4 = st.radio("Which Manufacturer Wins:", ["Chevrolet", "Ford", "Toyota"])
st.markdown("<br>", unsafe_allow_html=True)

st.header("5. Number of Cars Finishing on Lead Lap (required)")
lead_lap = st.number_input("How Many Cars Finish on the Lead Lap?", min_value=1, max_value=37, placeholder="Out of 37")

# Submission logic
if st.button("Submit"):
    errors = []
    if not entry_name.strip():
        errors.append("🚫 Entry Name is required.")
    if not email.strip() or not is_valid_email(email):
        errors.append("🚫 A valid Email Address is required.")
    if not lead_lap:
        errors.append("🚫 You must enter how many cars finish on the lead lap.")

    if errors:
        for err in errors:
            st.warning(err)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, entry_name, email, q1, q2, q3, q4, int(lead_lap)])
        st.success("✅ Godspeed!")
