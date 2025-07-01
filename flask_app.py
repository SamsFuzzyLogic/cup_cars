from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from pytz import timezone, utc
import re
import sendgrid
from sendgrid.helpers.mail import Mail
from gspread_formatting import CellFormat, Color, TextFormat, format_cell_range

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def send_confirmation_email(to_email, name, q1, q2, q3, q4, lead_lap):
    sg = sendgrid.SendGridAPIClient(api_key="YOUR_SENDGRID_API_KEY")
    from_email = "your_verified_sender@example.com"
    subject = "✅ Cup Car Challenge – Confirmation Received"
    html_content = f"""
    <p>Hi {name},</p>
    <p>Thanks for participating in the Cup Car Challenge!</p>
    <ul>
        <li><strong>Chevrolet Driver:</strong> {q1}</li>
        <li><strong>Ford Driver:</strong> {q2}</li>
        <li><strong>Toyota Driver:</strong> {q3}</li>
        <li><strong>Manufacturer Winner:</strong> {q4}</li>
        <li><strong>Cars on Lead Lap:</strong> {lead_lap}</li>
    </ul>
    <p>🏁 Good luck and may the best team win!</p>
    """
    message = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=html_content)
    sg.send(message)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        entry_name = request.form.get("entry_name", "").strip()
        email = request.form.get("email", "").strip()
        q1 = request.form.get("q1")
        q2 = request.form.get("q2")
        q3 = request.form.get("q3")
        q4 = request.form.get("q4")
        lead_lap = request.form.get("lead_lap", "").strip()

        # Validation
        errors = []
        if not entry_name:
            errors.append("Entry Name is required.")
        if not email or not is_valid_email(email):
            errors.append("A valid Email Address is required.")
        if not lead_lap.isdigit() or not (1 <= int(lead_lap) <= 37):
            errors.append("Enter a number between 1 and 37 for cars finishing on the lead lap.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            # Timezone-aware timestamp
            eastern = timezone("US/Eastern")
            timestamp = datetime.now(utc).astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S")

            # Google Sheets setup
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
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

            # Save to sheet
            sheet.append_row([timestamp, email, entry_name, q1, q2, q3, q4, int(lead_lap)])

            # Send email
            send_confirmation_email(email, entry_name, q1, q2, q3, q4, int(lead_lap))

            flash("✅ Thank you! Your entry has been received and a confirmation email sent.", "success")
            return redirect(url_for("index"))

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)
