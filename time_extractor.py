# time_extractor.py
import re
from typing import List, Dict, Optional, Tuple
from dateparser.search import search_dates

# מילים->ספרות (עם וריאנטים)
HEBREW_NUMBERS = {
    "אחת": 1, "אחד": 1,
    "שתיים": 2, "שניים": 2, "שתים": 2,
    "שלוש": 3, "ארבע": 4, "חמש": 5,
    "שש": 6, "שבע": 7, "שמונה": 8,
    "תשע": 9, "עשר": 10,
    "אחת עשרה": 11, "אחד עשר": 11, "אחד עשרה": 11,
    "שתים עשרה": 12, "שתיים עשרה": 12, "שניים עשר": 12,
}

# תבנית מילים לשעות
HEB_WORDS_PATTERN = (
    r"(אחת עשרה|אחד עשר|אחד עשרה|שתיים עשרה|שתים עשרה|שניים עשר|"
    r"אחת|אחד|שתיים|שניים|שתים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)"
)

def _format_hm(h: int, m: int = 0) -> str:
    return f"{h:02d}:{m:02d}"

def _context_period(text: str) -> str:
    """הקשר כללי למשפט כולו (fallback)."""
    if any(w in text for w in ["בבוקר", "בוקר"]): return "morning"
    if any(w in text for w in ["אחרי הצהריים", "אחה\"צ"]): return "afternoon"
    if any(w in text for w in ["בצהריים", "צהריים"]): return "noon"
    if any(w in text for w in ["בערב", "בלילה", "לילה"]): return "evening"
    return "default"

def _local_period(text: str, span: Optional[tuple[int,int]], fallback: str) -> str:
    """
    קובע בוקר/צהריים/אחה״צ/ערב/לילה לפי מילת הקשר סמוכה מאוד.
    אם אין התאמה קרובה – חוזר ל'default' (ברירת מחדל בוקר), ולא להקשר הגלובלי.
    """
    if not span:
        return "default"
    start, end = span
    after = text[end:end+15]   # מיד אחרי ההתאמה
    before = text[max(0, start-15):start]  # מיד לפני

    # בדיקה אחרי ההתאמה (מיידית)
    if re.match(r"\s*(בבוקר|בוקר)", after):
        return "morning"
    if re.match(r"\s*(אחרי הצהריים|אחה\"צ)", after):
        return "afternoon"
    if re.match(r"\s*(בצהריים|צהריים)", after):
        return "noon"
    if re.match(r"\s*(בערב|בלילה|לילה)", after):
        return "evening"

    # בדיקה לפני (כמו "בערב בשבע")
    if re.search(r"(בבוקר|בוקר)\s*$", before):
        return "morning"
    if re.search(r"(אחרי הצהריים|אחה\"צ)\s*$", before):
        return "afternoon"
    if re.search(r"(בצהריים|צהריים)\s*$", before):
        return "noon"
    if re.search(r"(בערב|בלילה|לילה)\s*$", before):
        return "evening"

    return "default"
def _rule_based_candidates(text: str) -> List[Dict]:
    """איסוף מועמדים לפי חוקים דטרמיניסטיים (regex)."""
    t = text.strip()
    global_period = _context_period(t)
    cands: List[Dict] = []

    def add(val, m_span=None):
        cands.append({"span": m_span, "value": val, "source": "rule"})

    # --- חצות ---
    if "חצות היום" in t:
        add("12:00")
    if "חצות" in t or "חצות הלילה" in t:
        add("00:00")

    # --- "רבע ל..." (תומך גם ב"ברבע ל־") + סימני פיסוק
    m = re.search(rf"(?<!\S)ב?רבע\s+ל[־-]?\s*{HEB_WORDS_PATTERN}(?=[\s,.!?״”)]|$)", t)
    if m:
        loc_period = _local_period(t, m.span(), "default")
        word = m.group(1)
        hour = HEBREW_NUMBERS.get(word)
        if hour:
            base = (hour - 1) if hour > 1 else 12
            if loc_period in ("evening", "afternoon"):
                hh = base if base >= 12 else base + 12
            else:
                hh = base
            add(_format_hm(hh, 45), m.span())

    # --- "... וחצי" (עם/בלי "בשעה"/"ב") + סימני פיסוק
    m = re.search(rf"(?<!\S)(?:ב(?:שעה)?\s*)?{HEB_WORDS_PATTERN}\s+וחצי(?=[\s,.!?״”)]|$)", t)
    if m:
        loc_period = _local_period(t, m.span(), "default")
        word = m.group(1)
        hour = HEBREW_NUMBERS.get(word)
        if hour is not None:
            hh = hour
            if loc_period in ("evening", "afternoon"):
                hh = hh if hh >= 12 else hh + 12
            add(_format_hm(hh, 30), m.span())

    # --- 24H ישיר (21:15)
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m:
        h, mm = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mm <= 59:
            add(_format_hm(h, mm), m.span())

    # --- "בשעה 8" / "ב־21:00" / "ב-9:30" (ספרות, עם קונטקסט מקומי)
    m = re.search(r"\bבש(?:עה)?\s*(\d{1,2})(?::(\d{2}))?\b", t)
    if not m:
        m = re.search(r"\bב[־-]?\s*(\d{1,2})(?::(\d{2}))?\b", t)
    if m:
        loc_period = _local_period(t, m.span(), "default")
        h = int(m.group(1)); mm = int(m.group(2) or 0)

        # כלל מפורש ל"בלילה" במספרים
        if "בלילה" in t:
            if h == 12:
                add("00:00", m.span())  # 12 בלילה -> 00:00
            elif 1 <= h <= 4:
                add(_format_hm(h, mm), m.span())  # 1..4 בלילה -> 01..04
            # 5..11 בלילה לא כופים — נמשיך לכלל רגיל

        if h == 12:
            if loc_period == "noon":
                val = "12:00"
            elif loc_period in ("evening", "afternoon"):
                val = "00:00"
            else:
                val = "12:00"
        else:
            hh = h
            if loc_period in ("evening", "afternoon") and hh < 12:
                hh += 12
            val = _format_hm(hh, mm)
        add(val, m.span())

    # --- "אחת בצהריים" / "בשעה אחת בצהריים" (מילים + בצהריים)
    m = re.search(rf"(?<!\S)(?:ב(?:שעה)?\s*)?{HEB_WORDS_PATTERN}\s+בצהריים(?=[\s,.!?״”)]|$)", t)
    if m:
        word = m.group(1)
        n = HEBREW_NUMBERS.get(word)
        if n == 1:
            add("13:00", m.span())
        elif n == 12:
            add("12:00", m.span())
        elif 2 <= n <= 11:
            add(_format_hm(n + 12, 0), m.span())

    # --- "מילה + בלילה" (אחת/שתיים... בלילה)
    m = re.search(rf"(?<!\S)(?:ב(?:שעה)?\s*)?{HEB_WORDS_PATTERN}\s+בלילה(?=[\s,.!?״”)]|$)", t)
    if m:
        word = m.group(1)
        n = HEBREW_NUMBERS.get(word)
        if n == 12:
            add("00:00", m.span())
        elif n == 1:
            add("01:00", m.span())
        elif 2 <= n <= 4:
            add(_format_hm(n, 0), m.span())
        else:
            # 5..11 בלילה – אמביוולנטי; נשאיר לכללים אחרים
            pass

    # --- מילים בודדות (עם/בלי "ב"/"בשעה")
    m = re.search(
    rf"(?<!\S)(?:ב(?:שעה)?\s*)?{HEB_WORDS_PATTERN}(?!\s+וחצי)(?=[\s,.!?״”)]|$)",
    t)
    if m:
        loc_period = _local_period(t, m.span(), "default")
        word = m.group(1)
        n = HEBREW_NUMBERS.get(word)
        if n is not None:
            if n == 12:
                if loc_period == "noon":
                    add("12:00", m.span())
                elif loc_period in ("evening", "afternoon"):
                    add("00:00", m.span())
                else:
                    add("12:00", m.span())
            else:
                hh = n
                if "בלילה" in t and 1 <= hh <= 4:
                    pass  # כבר טופל לעיל
                elif loc_period in ("evening", "afternoon") and hh < 12:
                    hh += 12
                add(_format_hm(hh, 0), m.span())

    # --- "סביב/סביבות/בערך <שעה>" (ספרות או מילים)
    m = re.search(
        rf"(?<!\S)(סביב|סביבות|בערך)\s+(?:ב(?:שעה)?\s*)?(?:{HEB_WORDS_PATTERN}|(\d{{1,2}}))(?=[\s,.!?״”)]|$)",
        t
    )
    if m:
        # group(2)=מילה, group(3)=ספרה (לפי הסוגריים בדפוס)
        word_match = m.group(2)
        digit_match = m.group(3)
        if digit_match:
            h = int(digit_match)
        else:
            h = HEBREW_NUMBERS.get(word_match or "", None)
        if h is not None:
            loc_period = _local_period(t, m.span(), "default")
            if "בלילה" in t and 1 <= h <= 4:
                pass
            elif loc_period in ("evening","afternoon") and h < 12:
                h += 12
            add(_format_hm(h, 0), m.span())

    # --- ספרה בודדת (fallback זהיר)
    m = re.search(r"\b(\d{1,2})\b", t)
    if m:
        loc_period = _local_period(t, m.span(), "default")
        h = int(m.group(1))
        if 0 <= h <= 23:
            if h == 12:
                if loc_period == "noon":
                    val = "12:00"
                elif loc_period in ("evening","afternoon"):
                    val = "00:00"
                else:
                    val = "12:00"
            else:
                hh = h
                if "בלילה" in t and 1 <= hh <= 4:
                    pass
                elif loc_period in ("evening","afternoon") and hh < 12:
                    hh += 12
                val = _format_hm(hh, 0)
            add(val, m.span())

    # --- מילות הקשר בלבד (fallback כללי)
    if global_period == "morning":   add("08:00")
    if global_period == "evening":   add("20:00")
    if global_period == "noon":      add("12:00")
    if global_period == "afternoon": add("17:00")

    return cands

def _dateparser_candidates(text: str) -> List[Dict]:
    """מועמדים מ-dateparser לכל טקסט חופשי (גיבוי)."""
    cands: List[Dict] = []
    try:
        found = search_dates(
            text, languages=["he"],
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": None}
        )
        if found:
            for frag, dt in found:
                cands.append({
                    "span": None,
                    "value": _format_hm(dt.hour, dt.minute),
                    "source": "dateparser",
                    "frag": frag
                })
    except Exception:
        pass
    return cands

def extract_times_all(text: str) -> List[Dict]:
    """מאחד מועמדים מחוקים ו-dateparser, מונע כפילויות."""
    c = _rule_based_candidates(text)
    dp = _dateparser_candidates(text)
    seen = set(x["value"] for x in c)
    for d in dp:
        if d["value"] not in seen:
            c.append(d)
            seen.add(d["value"])
    return c

def extract_best_time(text: str) -> Optional[str]:
    """מחזיר את השעה הטובה ביותר בטקסט: קודם כלל עם span מוקדם, אחרת כלל, אחרת dateparser."""
    cands = extract_times_all(text)
    if not cands:
        return None
    rule_spans = [c for c in cands if c["source"] == "rule" and c["span"]]
    if rule_spans:
        rule_spans.sort(key=lambda c: c["span"][0])  # ההתאמה המוקדמת במשפט
        return rule_spans[0]["value"]
    rule_any = [c for c in cands if c["source"] == "rule"]
    if rule_any:
        return rule_any[0]["value"]
    return cands[0]["value"]
