from PyQt5.QtCore import QDate, QDateTime, Qt
from PyQt5.QtWidgets import QDateEdit

from .constant import DATE_DISPLAY_FORMAT

TIME_DISPLAY_FORMAT = "hh:mm"


def configure_date_edit(
    date_edit: QDateEdit, *, calendar_popup: bool = True
) -> QDateEdit:
    """Apply app-wide display format and optional calendar popup to a QDateEdit."""
    date_edit.setDisplayFormat(DATE_DISPLAY_FORMAT)
    if calendar_popup:
        date_edit.setCalendarPopup(True)
    return date_edit


def format_date(qdate: QDate) -> str:
    """Format a QDate for API payloads using the app standard."""
    return qdate.toString(DATE_DISPLAY_FORMAT)


def format_api_date(date_string: str) -> str:
    """Parse a date/datetime string from the API and return the date in the app display format.

    Handles both ISO datetime (e.g. '2026-05-31T09:49:19+03:00') and
    plain date strings (e.g. '2026-05-31').
    Returns the original string unchanged if parsing fails.
    """
    if not date_string:
        return date_string

    # Try parsing as full ISO datetime first
    parsed_dt = QDateTime.fromString(date_string, Qt.ISODate)
    if parsed_dt.isValid():
        return parsed_dt.date().toString(DATE_DISPLAY_FORMAT)

    # Fallback: try as plain date string
    parsed_date = QDate.fromString(date_string, "yyyy-MM-dd")
    if parsed_date.isValid():
        return parsed_date.toString(DATE_DISPLAY_FORMAT)

    return date_string


def format_api_time(date_string: str) -> str:
    """Extract the time portion (hh:mm) from an ISO datetime string.

    Returns an empty string if the input has no time component or parsing fails.
    """
    if not date_string:
        return ""

    parsed_dt = QDateTime.fromString(date_string, Qt.ISODate)
    if parsed_dt.isValid():
        return parsed_dt.time().toString(TIME_DISPLAY_FORMAT)

    return ""
