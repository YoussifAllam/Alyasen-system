"""
Centralized Input Validation Utilities for the PyQt5 ERP System.

Provides reusable validation functions and a visual feedback mechanism
that highlights invalid fields with a red border and shows inline error messages.
"""

import re
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QComboBox, QMessageBox


# --- Style Constants ---
ERROR_STYLE = "border: 2px solid #ef4444;"
NORMAL_STYLE = ""  # Reset to default (handled by global stylesheet)


def _set_error(widget, has_error):
    """Applies or removes the error border style on a widget."""
    if has_error:
        widget.setStyleSheet(ERROR_STYLE)
    else:
        widget.setStyleSheet(NORMAL_STYLE)


def _clear_errors(fields):
    """Resets the error style on a list of widgets."""
    for field in fields:
        _set_error(field, False)


# --- Individual Validators ---

def validate_not_empty(widget, field_name):
    """
    Checks that a QLineEdit or QTextEdit is not empty.
    Returns (is_valid, error_message).
    """
    if isinstance(widget, QLineEdit):
        value = widget.text().strip()
    elif isinstance(widget, QTextEdit):
        value = widget.toPlainText().strip()
    else:
        return True, ""

    if not value:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" مطلوب."
    _set_error(widget, False)
    return True, ""


def validate_positive_number(widget, field_name):
    """
    Checks that a QLineEdit contains a valid positive number (> 0).
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" مطلوب."
    try:
        num = float(value)
        if num <= 0:
            _set_error(widget, True)
            return False, f"حقل \"{field_name}\" يجب أن يكون رقمًا موجبًا أكبر من صفر."
        _set_error(widget, False)
        return True, ""
    except ValueError:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على رقم صحيح."


def validate_non_negative_number(widget, field_name):
    """
    Checks that a QLineEdit contains a valid non-negative number (>= 0).
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" مطلوب."
    try:
        num = float(value)
        if num < 0:
            _set_error(widget, True)
            return False, f"حقل \"{field_name}\" يجب أن يكون رقمًا لا يقل عن صفر."
        _set_error(widget, False)
        return True, ""
    except ValueError:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على رقم صحيح."


def validate_optional_number(widget, field_name):
    """
    If the field is not empty, checks that it contains a valid number.
    An empty field is considered valid (optional).
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, False)
        return True, ""
    try:
        float(value)
        _set_error(widget, False)
        return True, ""
    except ValueError:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على رقم صحيح."


def validate_phone(widget, field_name="رقم الهاتف"):
    """
    Checks that a QLineEdit contains a plausible phone number.
    Allows digits, +, -, spaces. Must have at least 7 digits.
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" مطلوب."

    # Remove allowed non-digit characters for digit count check
    digits_only = re.sub(r"[^\d]", "", value)
    # Check for invalid characters
    if not re.match(r"^[\d\s\+\-\(\)]+$", value):
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يحتوي على أحرف غير صالحة. يُسمح فقط بالأرقام و + - ()."
    if len(digits_only) < 7:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على 7 أرقام على الأقل."
    _set_error(widget, False)
    return True, ""


def validate_email(widget, field_name="البريد الإلكتروني"):
    """
    Checks that a QLineEdit contains a valid email format.
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" مطلوب."

    email_pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على بريد إلكتروني صالح (مثل: user@example.com)."
    _set_error(widget, False)
    return True, ""


def validate_optional_email(widget, field_name="البريد الإلكتروني"):
    """
    If the field is not empty, checks for valid email format.
    An empty field is considered valid (optional).
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if not value:
        _set_error(widget, False)
        return True, ""
    return validate_email(widget, field_name)


def validate_combo_selected(widget, field_name):
    """
    Checks that a QComboBox has a valid selection (not the placeholder with None/empty data).
    Returns (is_valid, error_message).
    """
    current_data = widget.currentData()
    if current_data is None or current_data == "":
        _set_error(widget, True)
        return False, f"الرجاء اختيار \"{field_name}\"."
    _set_error(widget, False)
    return True, ""


def validate_password_match(password_widget, confirm_widget, field_name="كلمة المرور"):
    """
    Checks that two password fields match.
    Returns (is_valid, error_message).
    """
    p1 = password_widget.text().strip()
    p2 = confirm_widget.text().strip()
    if p1 != p2:
        _set_error(confirm_widget, True)
        return False, "كلمة المرور وتأكيد كلمة المرور غير متطابقتين."
    _set_error(confirm_widget, False)
    return True, ""


def validate_min_length(widget, field_name, min_len):
    """
    Checks that a QLineEdit value has at least `min_len` characters.
    Returns (is_valid, error_message).
    """
    value = widget.text().strip()
    if len(value) < min_len:
        _set_error(widget, True)
        return False, f"حقل \"{field_name}\" يجب أن يحتوي على {min_len} أحرف على الأقل."
    _set_error(widget, False)
    return True, ""


# --- Batch Validation Runner ---

def run_validations(parent_widget, validations):
    """
    Runs a list of validation tuples and shows a combined error message if any fail.

    Args:
        parent_widget: The parent widget for the QMessageBox.
        validations: A list of (is_valid, error_message) tuples,
                     typically from calling individual validators.

    Returns:
        True if ALL validations passed, False otherwise.
    """
    errors = []
    for is_valid, error_msg in validations:
        if not is_valid:
            errors.append(f"• {error_msg}")

    if errors:
        full_message = "\n".join(errors)
        QMessageBox.warning(parent_widget, "خطأ في البيانات", full_message)
        return False
    return True
