import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import pytz
from gspread_formatting import (
    CellFormat, Color, TextFormat, format_cell_range
)
import sendgrid
from sendgrid.helpers.mail import Mail

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def send_confirmation_email(to_email, name, q1, q2, q3, q4, lead_lap):
    sg = sendgrid.SendGridAPIClient(api_key=st.secrets["sendgrid"]["api_key"])
    from_email = st.secrets["sendgrid"]["sender_email"]
    subject = "✅ NASCAR Cup Car Challenge – Confirmation Received"
    html_content = f"""
    <p>Hi {name},</p>
    <p>Thanks for participating in the NASCAR Cup Car Challenge!</p>

    <p><strong>Your picks:</strong></p>
    <ul>
        <li><strong>Chevrolet Driver:</strong> {q1}</li>
        <li><strong>Ford Driver:</strong> {q2}</li>
        <li><strong>Toyota Driver:</strong> {q3}</li>
        <li><strong>Manufacturer Winner:</strong> {q4}</li>
        <li><strong>Cars on Lead Lap:</strong> {lead_lap}</li>
    </ul>

    <p>🏁 Good luck!</p>
    """
    message = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=html_content)
    sg.send(message)

st.set_page_config(page_title="Chicago Road Race", layout="centered")

st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image("images/cupcar_logo.png", width=150)
st.markdown("</div>", unsafe_allow_html=True)

st.title("NASCAR Chicago Survey")
st.markdown("###")
st.markdown("---")

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

target_title = "Chicago 2025"
worksheet_list = spreadsheet.worksheets()
sheet = next((ws for ws in worksheet_list if ws.title.strip().lower() == target_title.lower()), None)
if not sheet:
    sheet = spreadsheet.add_worksheet(title=target_title, rows="100", cols="10")

headers = ["Timestamp", "Email", "Entry Name", "Chevrolet Driver", "Ford Driver", "Toyota Driver", "Manufacturer", "Lead Lap"]
values = sheet.get_all_values()
if not values or values[0] != headers:
    sheet.update("A1:H1", [headers])
    header_format = CellFormat(
        backgroundColor=Color(0.27, 0.27, 0.27),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1))
    )
    format_cell_range(sheet, "A1:H1", header_format)

if not st.session_state.get("submitted", False):
    with st.form("cupcar_survey_form"):
        col1, col2 = st.columns(2)
        with col1:
            entry_name = st.text_input("Entry Name")
        with col2:
            email = st.text_input("Email Address")

        st.markdown("---")

        q1 = st.radio("1. Best Chevrolet Driver", [
            "Ross Chastain", "Austin Dillon", "Kyle Larson", "Justin Haley", "Kyle Busch",
            "Chase Elliott", "Ty Dillon", "A.J. Allmendinger", "William Byron",
            "Ricky Stenhouse", "Alex Bowman", "Michael McDowell", "Carson Hocevar", "Shane Van Gisbergen"
        ])
        st.markdown("###")

        q2 = st.radio("2. Best Ford Driver", [
            "Austin Cindric", "Noah Gragson", "Brad Keselowski", "Ryan Blaney",
            "Chris Buescher", "Josh Berry", "Joey Logano", "Todd Gilliland",
            "Zane Smith", "Cole Custer", "Ryan Preece"
        ])
        st.markdown("###")

        q3 = st.radio("3. Best Toyota Driver", [
            "Denny Hamlin", "Chase Briscoe", "Christopher Bell", "Bubba Wallace",
            "Riley Herbst", "John Hunter Nemechek", "Erik Jones", "Tyler Reddick", "Ty Gibbs"
        ])
        st.markdown("###")

        q4 = st.radio("4. Which Manufacturer Wins:", ["Chevrolet", "Ford", "Toyota"])
        st.markdown("###")

        lead_lap = st.number_input("5. Number of Cars Finishing on Lead Lap", value=0, placeholder="Out of 37")

        submitted = st.form_submit_button("Submit")

    if submitted:
        errors = []
        if not entry_name.strip():
            errors.append("🚫 Entry Name is required.")
        if not email.strip() or not is_valid_email(email):
            errors.append("🚫 A valid Email Address is required.")
        if lead_lap <= 0 or lead_lap > 37:
            errors.append("🚫 Enter a number between 1 and 37 for cars finishing on the lead lap.")

        if errors:
            for err in errors:
                st.warning(err)
        else:
            eastern = pytz.timezone("US/Eastern")
            timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
            sheet.append_row([timestamp, email, entry_name, q1, q2, q3, q4, int(lead_lap)])
            send_confirmation_email(email, entry_name, q1, q2, q3, q4, int(lead_lap))
            st.session_state["submitted"] = True
            st.success("✅ Thank you! Your entry has been submitted and a confirmation email has been sent.")
else:
    st.success("✅ Your entry has already been submitted. Thank you for participating!")
