from datetime import date, timedelta
from rest_framework.exceptions import ValidationError


def get_month_start_end(month, year):
    """
    Returns the first and last date of the specified month and year.

    Args:
        month (int): Month number (1-12)
        year (int): Year (e.g., 2025)

    Returns:
        tuple: (first_date, last_date) as strings in format 'YYYY-M-D'

    Raises:
        ValueError: If month is not between 1-12
    """
    # Validate month input
    if not 1 <= month <= 12:
        raise ValidationError("الشهر يجب ان يكون بين 1 و 12")

    # Calculate first day of the month
    first_day = date(year, month, 1)

    # Calculate last day of the month
    if month == 12:
        last_day = date(year, month, 31)
    else:
        # First day of next month minus one day
        next_month = date(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)

    # Format dates as requested
    first_date_str = f"{first_day.year}-{first_day.month}-{first_day.day}"
    last_date_str = f"{last_day.year}-{last_day.month}-{last_day.day}"

    return first_date_str, last_date_str
