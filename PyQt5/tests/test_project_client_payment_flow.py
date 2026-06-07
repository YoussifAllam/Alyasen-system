"""Mocked API flow tests for create → link → pay sequence (no live backend)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PYQT_ROOT = Path(__file__).resolve().parents[1]
if str(PYQT_ROOT) not in sys.path:
    sys.path.insert(0, str(PYQT_ROOT))

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from components.Main_Ui_Components.constant import BACKEND_BASE_URL
from components.clients.payment_dialog import ApiWorker as PaymentApiWorker
from components.clients.select_project_dialog import ApiWorker as LinkApiWorker
from components.projects.ui_projects import ProjectApiWorker
from components.utils.auth_context import enrich_payload_with_user, get_logged_in_username
from components.utils.flow_payloads import (
    build_create_project_payload,
    build_link_project_payload,
    build_payment_payload,
)


class MockRequestRouter:
    """Return canned JSON per URL and record call order."""

    def __init__(self):
        self.calls: list[dict] = []
        self._project_id = 10
        self._cbp_id = 5

    def __call__(self, method, url, **kwargs):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "json": kwargs.get("json"),
                "data": kwargs.get("data"),
                "files": kwargs.get("files"),
            }
        )
        response = MagicMock()
        response.status_code = 200

        if url.endswith("/projects/") and method == "POST":
            response.json.return_value = {"status": "success", "id": self._project_id}
        elif url.endswith("/clients/projects/") and method == "POST":
            response.json.return_value = {
                "status": "success",
                "data": {"cbp_id": self._cbp_id, "project_type": "rent"},
            }
        elif url.endswith("/clients/projects/payments/") and method == "POST":
            response.json.return_value = {"status": "sucess"}
        else:
            response.json.return_value = {"status": "success"}

        return response


class ProjectClientPaymentFlowTest(unittest.TestCase):
    def setUp(self):
        QSettings("FactorySystem").clear()

    def tearDown(self):
        QSettings("FactorySystem").clear()

    def _run_worker(self, worker):
        results = {"success": None, "error": None}
        worker.success.connect(lambda data: results.update({"success": data}))
        worker.error.connect(lambda msg: results.update({"error": msg}))
        worker.run()
        self.assertIsNone(results["error"], results["error"])
        return results["success"]

    def test_full_flow_call_sequence_and_payloads(self):
        router = MockRequestRouter()
        username = get_logged_in_username()

        create_payload = enrich_payload_with_user(
            build_create_project_payload(
                "Rent Flow Project",
                "rent",
                1000.0,
                supplier_id=3,
            ),
            include_username=True,
        )
        link_payload = build_link_project_payload("rent", 10, 1, username)
        payment_payload = enrich_payload_with_user(
            build_payment_payload(
                project_id=10,
                project_type="rent",
                payment_amount="500",
                payment_type="cash",
                payment_date="2026-06-07",
                check_cleared_date="2026-06-07",
            )
        )

        with patch("components.projects.ui_projects.request", side_effect=router):
            self._run_worker(
                ProjectApiWorker(
                    "POST",
                    f"{BACKEND_BASE_URL}/projects/",
                    create_payload,
                )
            )

        with patch("components.clients.select_project_dialog.request", side_effect=router):
            self._run_worker(
                LinkApiWorker(
                    "POST",
                    f"{BACKEND_BASE_URL}/clients/projects/",
                    data=link_payload,
                )
            )

        with patch("components.clients.payment_dialog.request", side_effect=router):
            self._run_worker(
                PaymentApiWorker(
                    "POST",
                    f"{BACKEND_BASE_URL}/clients/projects/payments/",
                    data=payment_payload,
                )
            )

        self.assertEqual(len(router.calls), 3)
        self.assertEqual(router.calls[0]["method"], "POST")
        self.assertTrue(router.calls[0]["url"].endswith("/projects/"))
        self.assertEqual(router.calls[1]["url"], f"{BACKEND_BASE_URL}/clients/projects/")
        self.assertEqual(
            router.calls[2]["url"],
            f"{BACKEND_BASE_URL}/clients/projects/payments/",
        )

        create_json = router.calls[0]["json"]
        self.assertEqual(create_json["name"], "Rent Flow Project")
        self.assertEqual(create_json["project_type"], "rent")
        self.assertEqual(create_json["cost"], 1000.0)
        self.assertEqual(create_json["supplier"], "3")
        self.assertEqual(create_json["username"], username)

        link_data = router.calls[1]["data"]
        self.assertEqual(link_data["project_type"], "rent")
        self.assertEqual(link_data["project_id"], "10")
        self.assertEqual(link_data["client_id"], "1")
        self.assertEqual(link_data["username"], username)

        payment_data = router.calls[2]["data"]
        self.assertEqual(payment_data["project_id"], "10")
        self.assertEqual(payment_data["project_type"], "rent")
        self.assertEqual(payment_data["payment_amount"], "500")
        self.assertEqual(payment_data["payment_type"], "cash")
        self.assertEqual(payment_data["user_name"], username)

    def test_payment_payload_uses_base_project_id_not_cbp_id(self):
        """Payment lookup on backend uses BaseProject id, not CBP id."""
        base_project_id = 10
        cbp_id = 5

        payload = enrich_payload_with_user(
            build_payment_payload(
                project_id=base_project_id,
                project_type="rent",
                payment_amount="100",
                payment_type="cash",
                payment_date="2026-06-07",
                check_cleared_date="2026-06-07",
            )
        )

        self.assertEqual(payload["project_id"], str(base_project_id))
        self.assertNotEqual(payload["project_id"], str(cbp_id))

    def test_link_payload_normalizes_unknown_type_to_project(self):
        payload = build_link_project_payload("legacy", 7, 2, "system")
        self.assertEqual(payload["project_type"], "project")
        self.assertEqual(payload["project_id"], "7")


if __name__ == "__main__":
    unittest.main(verbosity=2)
