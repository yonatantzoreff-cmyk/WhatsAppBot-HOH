import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import json
import time
import logging
import re

# --- Logging בסיסי ---
logging.basicConfig(
    filename='whatsapp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Credentials ---
from credentials import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_NUMBER,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_SHEET_NAME,
    TWILIO_TEMPLATE_SID
)

# --- חיבור ל-Google Sheet ---
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open(GOOGLE_SHEET_NAME).sheet1
logging.info(f"Connected to Google Sheet '{GOOGLE_SHEET_NAME}' successfully!")

# --- חיבור ל-Twilio ---
client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- פונקציית ולידציה למספר ישראלי ---
def validate_israeli_number(number):
    number = re.sub(r"[ \-\(\)]", "", number)
    if number.startswith("0"):
        number = "+972" + number[1:]
    elif not number.startswith("+"):
        number = "+972" + number
    digits_only = re.sub(r"\D", "", number)
    if not (9 <= len(digits_only) <= 13):
        return None
    return f"whatsapp:{number}"

# --- קריאת כל השורות ---
rows = sheet.get_all_records()

for i, row in enumerate(rows, start=2):  # start=2 כי השורה הראשונה היא כותרת
    try:
        # בדיקה אם כבר נשלח
        status = sheet.cell(i, 6).value  # עמודה F היא העמודה השישית
        if status and status.lower() == "sent":
            logging.info(f"Skipping {row.get('name', 'UNKNOWN')} – already sent")
            continue

        name = row['name']
        event = row['event']
        date = row['date']
        time_val = row['time']
        raw_number = str(row['phone']).strip()

        whatsapp_number = validate_israeli_number(raw_number)
        if not whatsapp_number:
            raise ValueError(f"Invalid phone number: {raw_number}")

        # --- שליחת ההודעה עם JSON content_variables ---
        message = client_twilio.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=whatsapp_number,
            content_sid=TWILIO_TEMPLATE_SID,
            content_variables=json.dumps({
                "1": name,
                "2": event,
                "3": date,
                "4": time_val
            })
        )

        # עדכון סטטוס בשיטס
        sheet.update(range_name=f"F{i}", values=[[ "sent" ]])
        logging.info(f"Message sent to {name} ({whatsapp_number})")
        print(f"Message sent to {name} ({whatsapp_number})")

        time.sleep(1)  # מניעת Rate Limit

    except Exception as e:
        sheet.update(range_name=f"F{i}", values=[[f"failed: {str(e)}"]])
        logging.error(f"Failed to send to {row.get('name', 'UNKNOWN')} ({raw_number}): {str(e)}")
        print(f"Failed to send to {row.get('name', 'UNKNOWN')} ({raw_number}): {str(e)}")

# bot.py
def process_incoming_message(body: str, from_number: str) -> str:
    """
    כאן בעתיד נכניס לוגיקה: נרמול שעות בעברית, זיהוי תאריך, עדכון לשיטס וכו'.
    בינתיים, דמו פשוט שמחזיר טקסט תשובה.
    """
    return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
