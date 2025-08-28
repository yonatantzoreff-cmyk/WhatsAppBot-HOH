# bot.py
import os
import re
import json
import logging

# --- Logging בסיסי ---
logging.basicConfig(
    filename='whatsapp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- פונקציית ולידציה למספר ישראלי ---
def validate_israeli_number(number: str) -> str | None:
    number = re.sub(r"[ \-\(\)]", "", number)
    if number.startswith("0"):
        number = "+972" + number[1:]
    elif not number.startswith("+"):
        number = "+972" + number
    digits_only = re.sub(r"\D", "", number)
    if not (9 <= len(digits_only) <= 13):
        return None
    return f"whatsapp:{number}"

# --- פונקציה מרכזית לטיפול בהודעות נכנסות ---
def process_incoming_message(body: str, from_number: str) -> str:
    """
    כרגע: מחזירים תשובה דמו. 
    בהמשך נוסיף:
    - נרמול שעות בעברית ("נכנס בשתיים" -> 14:00)
    - עדכון Google Sheets (עם ENV vars)
    - שליחת הודעה חכמה דרך Twilio
    """
    logging.info(f"Incoming message from {from_number}: {body}")
    return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
