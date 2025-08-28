# bot.py
import re
import logging

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
    "ראשון": 6, "שני": 0, "שלישי": 1,
    "רביעי": 2, "חמישי": 3, "שישי": 4, "שבת": 5,
}


def extract_time(text: str) -> str | None:
    text = text.strip()

    # --- חצות ---
    if "חצות היום" in text:
        return "12:00"
    if "חצות" in text or "חצות הלילה" in text:
        return "00:00"

    # --- רבע ל- ---
    match = re.search(r"רבע ל(.*)", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            base_hour = (hour-1 if hour > 1 else 12)
            if "בבוקר" in text:
                return f"{base_hour:02d}:45"
            if "בערב" in text or "אחרי הצהריים" in text:
                return f"{(base_hour if base_hour >= 12 else base_hour+12):02d}:45"
            # ברירת מחדל = בוקר
            return f"{base_hour:02d}:45"

    # --- חצי ---
    match = re.search(r"(.*) וחצי", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            if "בבוקר" in text:
                return f"{hour:02d}:30"
            if "בערב" in text or "אחרי הצהריים" in text:
                return f"{(hour if hour >= 12 else hour+12):02d}:30"
            return f"{hour:02d}:30"

    # --- פורמט 24H ישיר ---
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # --- ספרות בלבד ---
    match = re.search(r"\b(\d{1,2})\b", text)
    if match:
        hour = int(match.group(1))

        # מקרים מיוחדים ל-12
        if hour == 12:
            if "בצהריים" in text:
                return "12:00"
            if "אחרי הצהריים" in text:
                return "12:00"  # 12:00 בצהריים
            if "בלילה" in text or "בערב" in text:
                return "00:00"

        # אחרי הצהריים
        if "אחרי הצהריים" in text and hour < 12:
            return f"{hour+12:02d}:00"

        if "בצהריים" in text and hour == 1:
            return "13:00"

        if "בבוקר" in text and hour <= 12:
            return f"{hour:02d}:00"
        if "בערב" in text and hour < 12:
            return f"{hour+12:02d}:00"
        if "בלילה" in text:
            return f"{hour:02d}:00"

        # ברירת מחדל: בוקר
        return f"{hour:02d}:00"

    # --- מילים בעברית ---
    for heb, num in HEBREW_NUMBERS.items():
        if heb in text:
            hour = num

            if hour == 12:
                if "בצהריים" in text:
                    return "12:00"
                if "אחרי הצהריים" in text:
                    return "12:00"
                if "בלילה" in text or "בערב" in text:
                    return "00:00"

            if "אחרי הצהריים" in text and hour < 12:
                return f"{hour+12:02d}:00"

            if "בצהריים" in text and hour == 1:
                return "13:00"

            if "בבוקר" in text and hour <= 12:
                return f"{hour:02d}:00"
            if "בערב" in text and hour < 12:
                return f"{hour+12:02d}:00"
            if "בלילה" in text:
                return f"{hour:02d}:00"

            # ברירת מחדל: בוקר
            return f"{hour:02d}:00"

    # --- ברירות מחדל ---
    if "בבוקר" in text:
        return "08:00"
    if "בערב" in text:
        return "20:00"
    if "אחרי הצהריים" in text:
        return "17:00"
    if "בצהריים" in text:
        return "12:00"

    return None


def normalize_hebrew_time(text: str) -> str | None:
    text = text.strip()

    # --- יום בשבוע ---
    for heb_day in WEEKDAYS.keys():
        if heb_day in text:
            time_part = extract_time(text)
            if not time_part and "בבוקר" in text:
                time_part = "08:00"
            if not time_part and ("בערב" in text or "בלילה" in text):
                time_part = "20:00"
            if not time_part and "בצהריים" in text:
                time_part = "12:00"
            if not time_part and "אחרי הצהריים" in text:
                time_part = "17:00"
            return f"יום {heb_day} {time_part or ''}".strip()

    # --- מחר ---
    if "מחר" in text:
        time_part = extract_time(text)
        if not time_part and "בבוקר" in text:
            time_part = "08:00"
        if not time_part and ("בערב" in text or "בלילה" in text):
            time_part = "20:00"
        if not time_part and "בצהריים" in text:
            time_part = "12:00"
        if not time_part and "אחרי הצהריים" in text:
            time_part = "17:00"
        return f"מחר {time_part or ''}".strip()

    # --- היום ---
    if "היום" in text:
        time_part = extract_time(text)
        if not time_part and "בבוקר" in text:
            time_part = "08:00"
        if not time_part and ("בערב" in text or "בלילה" in text):
            time_part = "20:00"
        if not time_part and "בצהריים" in text:
            time_part = "12:00"
        if not time_part and "אחרי הצהריים" in text:
            time_part = "17:00"
        return f"היום {time_part or ''}".strip()

    # --- ברירת מחדל: רק שעה ---
    hour_part = extract_time(text)
    if hour_part:
        return hour_part

    return None


def process_incoming_message(body: str, from_number: str) -> str:
    logging.info(f"Incoming message from {from_number}: {body}")
    normalized = normalize_hebrew_time(body)
    if normalized:
        return f"הבנתי שאתה מתכוון ל: {normalized} ⏰"
    else:
        return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
