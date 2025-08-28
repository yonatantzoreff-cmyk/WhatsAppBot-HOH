# bot.py
import re
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    filename='whatsapp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEBREW_NUMBERS = {
    "אחת": 1, "אחד": 1,
    "שתיים": 2, "שניים": 2, "שתים": 2,
    "שלוש": 3, "ארבע": 4, "חמש": 5,
    "שש": 6, "שבע": 7, "שמונה": 8,
    "תשע": 9, "עשר": 10,
    "אחת עשרה": 11, "אחד עשרה": 11,
    "שתים עשרה": 12, "שניים עשר": 12,
}

WEEKDAYS = {
    "ראשון": 6,  # Python: Monday=0, Sunday=6
    "שני": 0,
    "שלישי": 1,
    "רביעי": 2,
    "חמישי": 3,
    "שישי": 4,
    "שבת": 5,
}

def normalize_hebrew_time(text: str) -> str | None:
    """
    מזהה שעות/ימים בביטויים בעברית ומחזיר מחרוזת סטנדרטית.
    לדוגמה:
    - 'מחר בשעה 9 בבוקר' -> 'מחר 09:00'
    - 'יום חמישי ב-20:00' -> 'יום חמישי 20:00'
    """
    text = text.strip()

    # --- יום בשבוע ---
    for heb_day, weekday_idx in WEEKDAYS.items():
        if heb_day in text:
            return f"יום {heb_day} {extract_time(text) or ''}".strip()

    # --- מחר ---
    if "מחר" in text:
        return f"מחר {extract_time(text) or ''}".strip()

    # --- היום ---
    if "היום" in text:
        return f"היום {extract_time(text) or ''}".strip()

    # ברירת מחדל: רק שעה
    hour_part = extract_time(text)
    if hour_part:
        return hour_part

    return None

def extract_time(text: str) -> str | None:
    """מחלץ שעה (כולל ספרות + בוקר/ערב)"""
    # פורמט 24H ישיר (21:15)
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return f"{hour:02d}:{minute:02d}"

    # ספרות בלבד
    match = re.search(r"\b(\d{1,2})\b", text)
    if match:
        hour = int(match.group(1))
        # בדיקת "בבוקר" או "בערב"
        if "בבוקר" in text and hour <= 12:
            return f"{hour:02d}:00"
        if "בערב" in text and hour <= 12:
            return f"{hour+12:02d}:00"
        # ברירת מחדל: נניח שעות אחר הצהריים
        return f"{(hour if hour >= 12 else hour+12):02d}:00"

    # מילים בעברית
    for heb, num in HEBREW_NUMBERS.items():
        if heb in text:
            hour = num
            if "בבוקר" in text and hour <= 12:
                return f"{hour:02d}:00"
            if "בערב" in text and hour <= 12:
                return f"{hour+12:02d}:00"
            return f"{(hour if hour >= 12 else hour+12):02d}:00"

    # רבע ל-
    match = re.search(r"רבע ל(.*)", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            return f"{(hour-1 if hour>1 else 12):02d}:45"

    # חצי
    match = re.search(r"(.*) וחצי", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            return f"{(hour if hour>=12 else hour+12):02d}:30"

    return None

# --- פונקציה ראשית ---
def process_incoming_message(body: str, from_number: str) -> str:
    logging.info(f"Incoming message from {from_number}: {body}")

    normalized = normalize_hebrew_time(body)
    if normalized:
        return f"הבנתי שאתה מתכוון ל: {normalized} ⏰"
    else:
        return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
