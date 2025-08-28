# bot.py
import re
import logging
from datetime import time

logging.basicConfig(
    filename='whatsapp_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# מילון מספרים בעברית -> מספרים
HEBREW_NUMBERS = {
    "אחת": 1,
    "אחד": 1,
    "שתיים": 2,
    "שניים": 2,
    "שתים": 2,
    "שלוש": 3,
    "ארבע": 4,
    "חמש": 5,
    "שש": 6,
    "שבע": 7,
    "שמונה": 8,
    "תשע": 9,
    "עשר": 10,
    "אחת עשרה": 11,
    "אחד עשרה": 11,
    "שתים עשרה": 12,
    "שניים עשר": 12,
}

def normalize_hebrew_time(text: str) -> str | None:
    """
    מקבל טקסט בעברית ומחזיר שעה בפורמט 24H (string).
    לדוגמה: 'שתיים' -> '14:00'
    """
    text = text.strip()

    # רבע ל-
    match = re.search(r"רבע ל(.*)", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            hour_24 = (hour - 1) if hour > 1 else 12
            return f"{hour_24}:45"

    # חצי
    match = re.search(r"(.*) וחצי", text)
    if match:
        word = match.group(1).strip()
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            return f"{hour}:30"

    # שעה עגולה
    for heb, num in HEBREW_NUMBERS.items():
        if heb in text:
            # נניח שמדובר בשעות בצהריים → נוסיף 12 אם < 12
            hour_24 = num if num >= 12 else num + 12
            return f"{hour_24}:00"

    return None

# --- פונקציה ראשית ---
def process_incoming_message(body: str, from_number: str) -> str:
    logging.info(f"Incoming message from {from_number}: {body}")

    normalized = normalize_hebrew_time(body)
    if normalized:
        return f"הבנתי שאתה מתכוון לשעה {normalized} ⏰"
    else:
        return f"היי! קיבלתי ממספר {from_number} את: “{body}” ✅"
