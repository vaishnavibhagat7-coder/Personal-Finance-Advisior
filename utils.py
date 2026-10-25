import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def to_decimal(value, default="0.00"):
    """Safely convert a numeric or string value to Decimal with 2 decimal places."""
    if value is None:
        return Decimal(default)
    try:
        dec = Decimal(str(value))
        return dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal(default)


def format_indian_number(number):
    """
    Format a number using the Indian numbering system.
    Examples:
      1000 -> 1,000.00
      25000 -> 25,000.00
      150000 -> 1,50,000.00
      10000000 -> 1,00,00,000.00
    """
    if number is None:
        return "0.00"
    try:
        dec = to_decimal(number)
        is_negative = dec < 0
        dec = abs(dec)
        
        # Split integer and decimal parts
        parts = f"{dec:.2f}".split(".")
        integer_part = parts[0]
        decimal_part = parts[1]

        if len(integer_part) <= 3:
            formatted_int = integer_part
        else:
            # Last 3 digits
            last_three = integer_part[-3:]
            remainder = integer_part[:-3]
            # Group remainder in pairs of 2 digits from right to left
            groups = []
            while len(remainder) > 2:
                groups.insert(0, remainder[-2:])
                remainder = remainder[:-2]
            if remainder:
                groups.insert(0, remainder)
            formatted_int = ",".join(groups) + "," + last_three

        formatted = f"{formatted_int}.{decimal_part}"
        return f"-{formatted}" if is_negative else formatted
    except Exception:
        return str(number)


def format_currency(amount, symbol="₹"):
    """Format an amount as currency using the Indian numbering format."""
    formatted_num = format_indian_number(amount)
    if formatted_num.startswith("-"):
        return f"-{symbol}{formatted_num[1:]}"
    return f"{symbol}{formatted_num}"


def format_percentage(val):
    """Format a value as a percentage with one decimal place."""
    if val is None:
        return "0.0%"
    try:
        dec = to_decimal(val)
        return f"{dec:.1f}%"
    except Exception:
        return "0.0%"


def get_month_bounds(year: int, month: int):
    """Return the start date and end date for a given year and month."""
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    return start_date, end_date


def get_month_name(month: int):
    """Return the full name of a month given its number (1-12)."""
    return calendar.month_name[month]


def shift_months(dt: date, months: int) -> date:
    """Safely add or subtract months to/from a date object using pure Python standard library."""
    total_months = dt.year * 12 + (dt.month - 1) + months
    year = total_months // 12
    month = (total_months % 12) + 1
    max_days = calendar.monthrange(year, month)[1]
    day = min(dt.day, max_days)
    return date(year, month, day)


DEFAULT_CATEGORIES = [
    {"name": "Food", "icon": "bi-cup-hot", "color": "#f59e0b"},
    {"name": "Food & Dining", "icon": "bi-cup-hot", "color": "#f59e0b"},
    {"name": "Rent and Housing", "icon": "bi-house-door", "color": "#3b82f6"},
    {"name": "Transportation", "icon": "bi-car-front", "color": "#6366f1"},
    {"name": "Education", "icon": "bi-mortarboard", "color": "#8b5cf6"},
    {"name": "Healthcare", "icon": "bi-heart-pulse", "color": "#ec4899"},
    {"name": "Shopping", "icon": "bi-bag", "color": "#f43f5e"},
    {"name": "Entertainment", "icon": "bi-film", "color": "#a855f7"},
    {"name": "Utilities", "icon": "bi-lightning-charge", "color": "#eab308"},
    {"name": "Groceries", "icon": "bi-cart3", "color": "#10b981"},
    {"name": "Travel", "icon": "bi-airplane", "color": "#06b6d4"},
    {"name": "Subscriptions", "icon": "bi-arrow-repeat", "color": "#14b8a6"},
    {"name": "Personal Care", "icon": "bi-person", "color": "#f97316"},
    {"name": "Other", "icon": "bi-three-dots", "color": "#64748b"}
]


def seed_default_categories(db_session, category_model):
    """Ensure default expense categories are populated in the database."""
    count = db_session.query(category_model).filter_by(is_default=True).count()
    if count == 0:
        for cat_data in DEFAULT_CATEGORIES:
            cat = category_model(
                name=cat_data["name"],
                icon=cat_data["icon"],
                color=cat_data["color"],
                is_default=True,
                user_id=None
            )
            db_session.add(cat)
        db_session.commit()
