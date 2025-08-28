def extract_time(text: str) -> str | None:
    text = text.strip()

    # --- קייסים מיוחדים ---
    if "חצות היום" in text:
        return "12:00"
    if "חצות" in text or "חצות הלילה" in text:
        return "00:00"

    # --- רבע ל- (מלל), עם גבולות מילה ---
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

    # --- וחצי (מלל), עם גבולות מילה ---
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

    # --- 24H ישיר (21:15) ---
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"

    # --- "בשעה 8", "בשעה 9:30", "ב-09:30" ---
    match = re.search(r"\bבש(?:עה)?\s*(\d{1,2})(?::(\d{2}))?\b", text)
    if not match:
        match = re.search(r"\bב[-־]?\s*(\d{1,2})(?::(\d{2}))?\b", text)  # תופס גם "ב־10"
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0

        if h == 12:
            if "בצהריים" in text: return "12:00"
            if "אחרי הצהריים" in text: return "12:00"
            if "בערב" in text or "בלילה" in text: return "00:00"

        if "אחרי הצהריים" in text and h < 12:
            h += 12
        elif "בערב" in text and h < 12:
            h += 12
        elif "בבוקר" in text:
            h = h  # נשאר AM
        else:
            # ברירת מחדל: בוקר (AM)
            h = h

        return f"{h:02d}:{m:02d}"

    # --- ספרות בודדות (נזהר לא לאסוף מספרים לא רלוונטיים – נעדיף את הראשון) ---
    match = re.search(r"\b(\d{1,2})\b", text)
    if match:
        h = int(match.group(1))

        if h == 12:
            if "בצהריים" in text: return "12:00"
            if "אחרי הצהריים" in text: return "12:00"
            if "בערב" in text or "בלילה" in text: return "00:00"

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

    # --- מילים בעברית (שעה עגולה) ---
    match = re.search(rf"\b{HEB_WORDS_PATTERN}\b", text)
    if match:
        word = match.group(1)
        h = HEBREW_NUMBERS.get(word)
        if h:
            if h == 12:
                if "בצהריים" in text: return "12:00"
                if "אחרי הצהריים" in text: return "12:00"
                if "בערב" in text or "בלילה" in text: return "00:00"

            if "אחרי הצהריים" in text and h < 12: h += 12
            elif "בערב" in text and h < 12: h += 12
            elif "בבוקר" in text: h = h
            else: h = h  # ברירת מחדל: בוקר

            return f"{h:02d}:00"

    # --- מילות הקשר בלבד ---
    if "בבוקר" in text: return "08:00"
    if "בערב" in text or "בלילה" in text: return "20:00"
    if "בצהריים" in text: return "12:00"
    if "אחרי הצהריים" in text: return "17:00"

    return None
