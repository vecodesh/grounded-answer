import re
import datetime
from typing import Optional, List, Dict

AMENDMENT_EFFECTIVE_DATE = datetime.date(2026, 3, 1)

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def parse_date(date_input: Optional[str]) -> Optional[datetime.date]:
    """Parse standard date strings like YYYY-MM-DD or Month YYYY."""
    if not date_input:
        return None

    date_str = date_input.strip().lower()

    # Try ISO YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", date_str)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        try:
            return datetime.date(year, month, day)
        except ValueError:
            pass

    # Try Month Day, Year or Day Month Year
    d_m_y = re.match(r"^(\d{1,2})\s+([a-z]+)\s+(\d{4})$", date_str)
    if d_m_y:
        day = int(d_m_y.group(1))
        month_name = d_m_y.group(2)
        year = int(d_m_y.group(3))
        if month_name in MONTH_MAP:
            try:
                return datetime.date(year, MONTH_MAP[month_name], day)
            except ValueError:
                pass

    # Try Month Year
    m_y = re.match(r"^([a-z]+)\s+(\d{4})$", date_str)
    if m_y:
        month_name = m_y.group(1)
        year = int(m_y.group(2))
        if month_name in MONTH_MAP:
            return datetime.date(year, MONTH_MAP[month_name], 15)

    return None


def extract_date_from_query(query: str) -> Optional[datetime.date]:
    """
    Extract date mentions from natural language query.
    Examples:
        - "in February 2026" -> 2026-02-15
        - "for a claim in April 2026" -> 2026-04-15
        - "occurring on 15 March 2026" -> 2026-03-15
        - "before March 2026" -> 2026-02-15
        - "after March 2026" -> 2026-04-15
    """
    q = query.lower()

    # Match explicit day month year: "1 march 2026", "15 february 2026"
    match_dmy = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)\s+(\d{4})\b", q)
    if match_dmy:
        day = int(match_dmy.group(1))
        month_str = match_dmy.group(2)
        year = int(match_dmy.group(3))
        if month_str in MONTH_MAP:
            try:
                return datetime.date(year, MONTH_MAP[month_str], day)
            except ValueError:
                pass

    # Match month day year: "march 1, 2026", "february 15 2026"
    match_mdy = re.search(r"\b([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", q)
    if match_mdy:
        month_str = match_mdy.group(1)
        day = int(match_mdy.group(2))
        year = int(match_mdy.group(3))
        if month_str in MONTH_MAP:
            try:
                return datetime.date(year, MONTH_MAP[month_str], day)
            except ValueError:
                pass

    # Match month year: "february 2026", "april 2026", "jan 2026"
    match_my = re.search(r"\b([a-z]+)\s+(\d{4})\b", q)
    if match_my:
        month_str = match_my.group(1)
        year = int(match_my.group(2))
        if month_str in MONTH_MAP:
            # Default to mid-month for month-level queries
            return datetime.date(year, MONTH_MAP[month_str], 15)

    # Match relative expressions
    if "before 1 march 2026" in q or "before march 2026" in q or "prior to march 2026" in q:
        return datetime.date(2026, 2, 15)
    if "on or after 1 march 2026" in q or "after march 2026" in q or "from march 2026" in q:
        return datetime.date(2026, 3, 15)

    # Match ISO format in query
    match_iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", q)
    if match_iso:
        y, m, d = map(int, match_iso.groups())
        try:
            return datetime.date(y, m, d)
        except ValueError:
            pass

    return None


def is_post_amendment(target_date: Optional[datetime.date]) -> bool:
    """Return True if target_date falls on or after 1 March 2026."""
    if target_date is None:
        # If unspecified, default to base manual era unless query specifically asks about amendments
        return False
    return target_date >= AMENDMENT_EFFECTIVE_DATE


def adjust_temporal_scores(results: List[Dict], target_date: Optional[datetime.date]) -> List[Dict]:
    """
    Adjust relevance scores based on temporal validity for the target claim/determination date.
    """
    if target_date is None:
        return results

    post_amendment = is_post_amendment(target_date)

    adjusted = []
    for r in results:
        item = dict(r)
        clause_id = item.get("clause_id", "")
        source = item.get("source", "manual")
        eff_end = item.get("effective_end")
        eff_start = item.get("effective_start")

        if post_amendment:
            # On/after March 1, 2026: Boost amendment clauses and penalize outdated base versions
            if "Amdt 2026-01" in clause_id or source == "amendment-2026-01":
                item["score"] = item["score"] + 0.35
                item["final_score"] = item["score"]
            elif eff_end == "2026-02-28":
                # Outdated base version
                item["score"] = item["score"] - 0.25
                item["final_score"] = item["score"]
        else:
            # Before March 1, 2026: Penalize amendment clauses
            if "Amdt 2026-01" in clause_id or source == "amendment-2026-01":
                item["score"] = item["score"] - 0.50
                item["final_score"] = item["score"]

        adjusted.append(item)

    adjusted.sort(key=lambda x: x.get("final_score", x.get("score", 0)), reverse=True)
    return adjusted
