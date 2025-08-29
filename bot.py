# bot.py
import re
import logging

logging.basicConfig(
    filename='whatsapp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# מספרים במילים -> מספרים
HEBREW_NUMBERS = {
    "אחת": 1, "אחד": 1,
    "שתיים": 2, "שניים": 2, "שתים": 2,
    "שלוש": 3, "ארבע": 4, "חמש": 5,
    "שש": 6, "שבע": 7, "שמונה": 8,
    "תשע": 9, "עשר": 10,
    "אחת עשרה": 11, "אחד עשרה": 11,
    "שתים עשרה": 12, "שניים עשר": 12,
}

# ימים (לתצוגה בלבד – לא מחשבים תאריכים בפועל)
WEEKDAYS = {
    "ראשון": 6, "שני": 0, "שלישי": 1,
    "רביעי": 2, "חמישי": 3, "שישי": 4, "שבת": 5,
}

# תבנית מילים של שעות עם גבולות מילה (למשפטים חופשיים)
HEB_WORDS_PATTERN = r"(אחת עשרה|אחד עשרה|שתים עשרה|שניים עשר|אחת|אחד|שתיים|שניים|שתים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)"


def extract_time(text: str) -> str | None:
    """
    מחלץ שעה מתוך טקסט חופשי בעברית ומחזיר בפורמט 24H (כמו '09:30').
    ברירת מחדל: בוקר (AM) אם לא צוין אחרת.
    """
    text = text.strip()

    # --- קייסים מיוחדים ---
    if "חצות היום" in text:
        return "12:00"
    if "חצות" in text or "חצות הלילה" in text:
        return "00:00"

    # --- רבע ל... (מילים) ---
    match = re.search(rf"\bרבע ל\s*{HEB_WORDS_PATTERN}\b", text)
    if match:
        word = match.group(1)
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            base = (hour - 1) if hour > 1 else 12
            if "בבוקר" in text:
                return f"{base:02d}:45"
            if "בערב" in text or "אחרי הצהריים" in text:
                return f"{(base if base >= 12 else base+12):02d}:45"
            # ברירת מחדל: בוקר
            return f"{base:02d}:45"

    # --- ... וחצי (מילים) ---
    match = re.search(rf"\b{HEB_WORDS_PATTERN}\s+וחצי\b", text)
    if match:
        word = match.group(1)
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            if "בבוקר" in text:
                return f"{hour:02d}:30"
            if "בערב" in text or "אחרי הצהריים" in text:
                return f"{(hour if hour >= 12 else hour+12):02d}:30"
            # ברירת מחדל: בוקר
            return f"{hour:02d}:30"

    # --- פורמט 24H ישיר (21:15) ---
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"

    # --- "בשעה 8" / "ב־21:00" / "ב-9:30" ---
    match = re.search(r"\bבש(?:עה)?\s*(\d{1,2})(?::(\d{2}))?\b", text)
    if not match:
        match = re.search(r"\bב[-־]?\s*(\d{1,2})(?::(\d{2}))?\b", text)  # תופס "ב־10" / "ב-10"
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0

        # טיפול ב-12
        if h == 12:
            if "בצהריים" in text or "אחרי הצהריים" in text:
                return "12:00"
            if "בערב" in text or "בלילה" in text:
                return "00:00"

        if "אחרי הצהריים" in text and h < 12:
            h += 12
        elif "בערב" in text and h < 12:
            h += 12
        elif "בבוקר" in text:
            h = h  # AM
        else:
            # ברירת מחדל: בוקר
            h = h

        return f"{h:02d}:{m:02d}"

    # --- ספרות בודדות ("8") ---
    match = re.search(r"\b(\d{1,2})\b", text)
    if match:
        h = int(match.group(1))

        if h == 12:
            if "בצהריים" in text or "אחרי הצהריים" in text:
                return "12:00"
            if "בערב" in text or "בלילה" in text:
                return "00:00"

        if "אחרי הצהריים" in text and h < 12:
            h += 12
        elif "בערב" in text and h < 12:
            h += 12
        elif "בבוקר" in text:
            h = h
        else:
            # ברירת מחדל: בוקר
            h = h

        return f"{h:02d}:00"

    # --- מילים בודדות ("שש", "אחת") ---
    match = re.search(rf"\b{HEB_WORDS_PATTERN}\b", text)
    if match:
        word = match.group(1)
        h = HEBREW_NUMBERS.get(word)
        if h:
            if h == 12:
                if "בצהריים" in text or "אחרי הצהריים" in text:
                    return "12:00"
                if "בערב" in text or "בלילה" in text:
                    return "00:00"

            if "אחרי הצהריים" in text and h < 12:
                h += 12
            elif "בערב" in text and h < 12:
                h += 12
            elif "בבוקר" in text:
                h = h
            else:
                # ברירת מחדל: בוקר
                h = h

            return f"{h:02d}:00"

    # --- רק מילות הקשר ---
    if "בבוקר" in text:
        return "08:00"
    if "בערב" in text or "בלילה" in text:
        return "20:00"
    if "בצהריים" in text:
        return "12:00"
    if "אחרי הצהריים" in text:
        return "17:00"

    return None


def normalize_hebrew_time(text: str) -> str | None:
    """
    מנרמל ביטויים שלמים (כולל 'היום', 'מחר', 'יום שלישי' וכו').
    מחזיר מחרוזת קריאה כמו: 'מחר 09:00', 'יום חמישי 20:00', או רק שעה '09:30'.
    """
    text = text.strip()

    # יום בשבוע (מציגים "יום X <שעה>")
    for heb_day in WEEKDAYS.keys():
        if heb_day in text:
            t = extract_time(text)
            if not t and "בבוקר" in text:
                t = "08:00"
            if not t and ("בערב" in text or "בלילה" in text):
                t = "20:00"
            if not t and "בצהריים" in text:
                t = "12:00"
            if not t and "אחרי הצהריים" in text:
                t = "17:00"
            return f"יום {heb_day} {t or ''}".strip()

    # מחר
    if "מחר" in text:
        t = extract_time(text)
        if not t and "בבוקר" in text:
            t = "08:00"
        if not t and ("בערב" in text or "בלילה" in text):
            t = "20:00"
        if not t and "בצהריים" in text:
            t = "12:00"
        if not t and "אחרי הצהריים" in text:
            t = "17:00"
        return f"מחר {t or ''}".strip()

    # היום
    if "היום" in text:
        t = extract_time(text)
        if not t and "בבוקר" in text:
            t = "08:00"
        if not t and ("בערב" in text or "בלילה" in text):
            t = "20:00"
        if not t and "בצהריים" in text:
            t = "12:00"
        if not t and "אחרי הצהריים" in text:
            t = "17:00"
        return f"היום {t or ''}".strip()

    # ברירת מחדל – רק שעה
    t = extract_time(text)
    if t:
        return t

    return None


def process_incoming_message(body: str, from_number: str) -> str:
    """
    נקודת הכניסה של הווב-הוק: מקבל טקסט חופשי ומחזיר תשובת בוט.
    """
    logging.info(f"Incoming message from {from_number}: {body}")
    normalized = normalize_hebrew_time(body)
    if normalized:
        return f"הבנתי שאתה מתכוון ל: {normalized} ⏰"
    else:
        return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
