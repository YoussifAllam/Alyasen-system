"""Parse backend API error payloads into a single user-facing Arabic message."""

from __future__ import annotations

from typing import Any

from requests import exceptions as requests_exceptions

_FIELD_LABELS = {
    "client_id": "كود العميل",
    "payment_amount": "المبلغ المدفوع",
    "username": "اسم المستخدم",
    "notes": "ملاحظات",
    "invoice_number": "رقم الفاتورة",
    "batch_id": "رقم طبقة السعر",
    "material_id": "المنتج",
    "name": "اسم الصنف",
    "material_name": "اسم الصنف",
    "product_name": "اسم الصنف",
    "category_name": "النوع",
    "unit_name": "الوحدة",
    "quantity_in_unit": "الكمية",
    "buy_price_per_unit": "سعر الشراء",
    "sell_price_per_unit": "سعر البيع",
    "serial_code": "سيريال كود",
    "non_field_errors": "",
}


def _format_error_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [_format_error_value(item) for item in value]
        return " — ".join(part for part in parts if part)
    if isinstance(value, dict):
        return parse_api_error_payload(value)
    return str(value).strip()


def parse_api_error_payload(data: Any) -> str:
    """Turn a JSON error body (dict/str/list) into one readable message."""
    if data is None:
        return "حدث خطأ غير معروف."

    if isinstance(data, str):
        text = data.strip()
        return text or "حدث خطأ غير معروف."

    if isinstance(data, list):
        parts = [_format_error_value(item) for item in data]
        joined = " — ".join(part for part in parts if part)
        return joined or "حدث خطأ غير معروف."

    if not isinstance(data, dict):
        return str(data).strip() or "حدث خطأ غير معروف."

    status = str(data.get("status", "")).lower()
    if status in ("faild", "failed", "error"):
        for key in ("error", "errors", "message", "detail"):
            if key in data and data[key] not in (None, "", {}):
                msg = _format_error_value(data[key])
                if msg:
                    return msg

    for key in ("الخطأ", "الخطاء", "حطأ", "خطأ", "خطا"):
        if key in data and data[key] not in (None, "", {}):
            msg = _format_error_value(data[key])
            if msg:
                return msg

    for key in ("detail", "message", "error"):
        if key in data and data[key] not in (None, "", {}):
            msg = _format_error_value(data[key])
            if msg:
                return msg

    if "non_field_errors" in data:
        msg = _format_error_value(data["non_field_errors"])
        if msg:
            return msg

    if "errors" in data:
        if isinstance(data["errors"], dict):
            msg = _format_field_errors(data["errors"])
            if msg:
                return msg
        else:
            msg = _format_error_value(data["errors"])
            if msg:
                return msg

    field_like = all(
        isinstance(v, (str, list, dict, int, float, bool, type(None)))
        for v in data.values()
    )
    if field_like and data:
        msg = _format_field_errors(data)
        if msg:
            return msg

    return "حدث خطأ غير متوقع من الخادم."


def _format_field_errors(errors: dict) -> str:
    parts = []
    for field, messages in errors.items():
        label = _FIELD_LABELS.get(field, field)
        text = _format_error_value(messages)
        if not text:
            continue
        if label:
            parts.append(f"{label}: {text}")
        else:
            parts.append(text)
    return " — ".join(parts)


def parse_api_error_response(response) -> str:
    """Parse an HTTP error response (non-2xx) into a user-facing message."""
    status_code = getattr(response, "status_code", None)
    try:
        data = response.json()
        msg = parse_api_error_payload(data)
        if msg:
            return msg
    except (ValueError, TypeError, requests_exceptions.JSONDecodeError):
        pass

    text = (getattr(response, "text", None) or "").strip()
    if text and len(text) < 800 and not text.startswith("<"):
        return text

    if status_code and status_code >= 500:
        return "حدث خطأ داخلي في الخادم. حاول مرة أخرى أو راجع مسؤول النظام."
    if status_code:
        return f"خطأ من الخادم (رمز {status_code})"
    return "حدث خطأ غير معروف من الخادم."


def is_api_failure_payload(data: Any) -> bool:
    """True when a 2xx JSON body still reports failure."""
    if not isinstance(data, dict):
        return False
    status = str(data.get("status", "")).lower()
    return status in ("faild", "failed", "error")


def is_http_success(status_code: int) -> bool:
    return 200 <= status_code < 300


def parse_api_response(response) -> tuple[bool, Any]:
    """Return (True, payload) on success or (False, user_message) on failure."""
    status_code = getattr(response, "status_code", 0)
    if not is_http_success(status_code):
        return False, parse_api_error_response(response)

    if status_code == 204:
        return True, {"status": "success"}

    try:
        data = response.json()
    except (ValueError, TypeError):
        return True, {}

    if is_api_failure_payload(data):
        return False, parse_api_error_payload(data)

    return True, data


def format_request_exception(exc: Exception) -> str:
    if isinstance(exc, requests_exceptions.ConnectionError):
        return (
            "تعذر الاتصال بالخادم.\n"
            "تأكد من تشغيل الخادم وصحة عنوان الاتصال في الإعدادات."
        )
    if isinstance(exc, requests_exceptions.Timeout):
        return "انتهت مهلة الاتصال بالخادم. حاول مرة أخرى بعد قليل."
    if isinstance(exc, requests_exceptions.JSONDecodeError):
        return (
            "استجابة غير صالحة من الخادم (ليست بيانات JSON).\n"
            "قد يكون الخادم متوقفاً أو يعيد صفحة خطأ بدلاً من البيانات المتوقعة."
        )
    msg = str(exc).strip()
    if msg:
        return f"فشل الاتصال بالخادم: {msg}"
    return "فشل الاتصال بالخادم."
