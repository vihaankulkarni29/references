import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(email: str) -> str:
    if not email:
        return "N/A"
    email = email.strip()
    return email if EMAIL_RE.match(email) else "N/A"


def clean_text(text: str) -> str:
    if text is None:
        return "N/A"
    return " ".join(text.split())


def parse_date(date_str: str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            continue
    return None
