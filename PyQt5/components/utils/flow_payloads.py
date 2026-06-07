"""Pure payload builders for client/project/payment API flows."""

from __future__ import annotations

from typing import Optional


def build_create_project_payload(
    name: str,
    project_type: str,
    cost: float,
    *,
    supplier_id: Optional[int] = None,
    project_status: str = "active",
) -> dict:
    """Build POST /api/projects/ payload (mirrors ProjectsUI.handle_add_project)."""
    payload = {
        "name": name,
        "project_type": project_type,
        "project_status": project_status,
        "cost": cost,
    }
    if project_type in ("rent", "selling") and supplier_id is not None:
        payload["supplier"] = str(supplier_id)
    return payload


def project_type_from_ui_label(pt_text: str) -> str:
    """Map Arabic project type label to API project_type."""
    if pt_text == "تأجير":
        return "rent"
    if pt_text == "بيع":
        return "selling"
    return "industrial"


def build_link_project_payload(
    project_type: str,
    project_id,
    client_id,
    username: str,
) -> dict:
    """Build POST /api/clients/projects/ payload (mirrors ProjectSelectionDialog.handle_next)."""
    p_type = project_type or ""
    if p_type != "campaine" and p_type not in ("rent", "industrial", "selling"):
        p_type = "project"
    return {
        "project_type": p_type,
        "project_id": str(project_id),
        "client_id": str(client_id) if client_id else "",
        "username": username,
    }


def build_payment_payload(
    project_id,
    project_type: str,
    payment_amount: str,
    payment_type: str,
    *,
    payment_date: str,
    check_cleared_date: str,
    notes: str = "",
    portal_invoice_number: str = "",
    check_date: Optional[str] = None,
) -> dict:
    """Build POST /api/clients/projects/payments/ payload (mirrors PaymentDialog.handle_save)."""
    form_data = {
        "project_id": str(project_id),
        "project_type": str(project_type),
        "payment_amount": payment_amount,
        "payment_date": payment_date,
        "payment_type": payment_type,
        "check_cleared_date": check_cleared_date,
        "notes": notes,
        "portal_invoice_number": portal_invoice_number,
    }
    if payment_type == "check" and check_date:
        form_data["check_date"] = check_date
    return form_data
