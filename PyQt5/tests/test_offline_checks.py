"""Offline checks for the PyQt5 desktop app (no UI interaction required)."""

from __future__ import annotations

import compileall
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Headless Qt before any PyQt5 widget imports
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PYQT_ROOT = Path(__file__).resolve().parents[1]
if str(PYQT_ROOT) not in sys.path:
    sys.path.insert(0, str(PYQT_ROOT))

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from components.utils import api_errors
from components.utils.auth_context import enrich_payload_with_user, get_logged_in_username
from components.projects.ui_projects import ProjectApiWorker


class CompileAllTest(unittest.TestCase):
    def test_all_pyqt5_modules_compile(self):
        ok = compileall.compile_dir(str(PYQT_ROOT), quiet=1)
        self.assertTrue(ok, "One or more PyQt5 modules failed to compile")


class AuthContextTest(unittest.TestCase):
    def setUp(self):
        QSettings("FactorySystem").clear()

    def tearDown(self):
        QSettings("FactorySystem").clear()

    def test_fallback_when_settings_empty(self):
        self.assertEqual(get_logged_in_username(), "system")

    def test_prefers_user_name_then_email(self):
        settings = QSettings("FactorySystem")
        settings.setValue("email", "user@example.com")
        settings.setValue("user_name", "  Ahmed  ")
        self.assertEqual(get_logged_in_username(), "Ahmed")

    def test_enrich_payload_adds_user_name(self):
        payload = enrich_payload_with_user({"CBP_id": "1"})
        self.assertEqual(payload["CBP_id"], "1")
        self.assertEqual(payload["user_name"], "system")

    def test_enrich_payload_keeps_existing_user_name(self):
        payload = enrich_payload_with_user({"user_name": "custom"})
        self.assertEqual(payload["user_name"], "custom")

    def test_enrich_payload_can_add_username(self):
        payload = enrich_payload_with_user({}, include_username=True)
        self.assertEqual(payload["username"], "system")


class ApiErrorsTest(unittest.TestCase):
    def test_user_name_required_arabic(self):
        msg = api_errors.parse_api_error_payload(
            {"status": "failed", "errors": {"user_name": ["This field is required."]}}
        )
        self.assertIn("اسم المستخدم", msg)
        self.assertIn("هذا الحقل مطلوب", msg)

    def test_parse_success_response(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {"status": "success", "data": {"id": 1}}
        ok, data = api_errors.parse_api_response(response)
        self.assertTrue(ok)
        self.assertEqual(data["data"]["id"], 1)

    def test_parse_empty_success_body(self):
        response = MagicMock(status_code=200)
        response.json.side_effect = ValueError("empty")
        ok, data = api_errors.parse_api_response(response)
        self.assertTrue(ok)
        self.assertEqual(data, {})

    def test_parse_400_user_name_error(self):
        response = MagicMock(status_code=400)
        response.json.return_value = {
            "status": "failed",
            "errors": {"user_name": ["This field is required."]},
        }
        ok, msg = api_errors.parse_api_response(response)
        self.assertFalse(ok)
        self.assertIn("اسم المستخدم", msg)


class ProjectApiWorkerTest(unittest.TestCase):
    def test_patch_json_success(self):
        worker = ProjectApiWorker(
            "PATCH",
            "http://example.test/projects/rent/info/",
            enrich_payload_with_user({"CBP_id": "1", "selling_price": "1000"}),
        )
        results = {"error": None, "success": None}

        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"status": "success"}

        with patch("components.projects.ui_projects.request", return_value=mock_response) as req:
            worker.run()
            req.assert_called_once()
            call_kwargs = req.call_args.kwargs
            self.assertIn("json", call_kwargs)
            self.assertEqual(call_kwargs["json"]["user_name"], "system")
            self.assertEqual(call_kwargs["json"]["CBP_id"], "1")

    def test_emits_error_on_failed_response(self):
        worker = ProjectApiWorker("GET", "http://example.test/projects/")
        errors = []

        worker.error.connect(errors.append)
        mock_response = MagicMock(status_code=400)
        mock_response.json.return_value = {
            "status": "failed",
            "errors": {"user_name": ["This field is required."]},
        }

        with patch("components.projects.ui_projects.request", return_value=mock_response):
            worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("اسم المستخدم", errors[0])


class ImportSmokeTest(unittest.TestCase):
    def test_critical_modules_import(self):
        modules = [
            "components.projects.rent.update_rent_project_dialog",
            "components.projects.rent.ui_rent_project",
            "components.projects.sell_ind.sell_ind_update_project_dialog",
            "components.projects.sell_ind.ui_sell_ind_project",
            "components.clients.payment_dialog",
            "components.clients.invoice_payment_details_dialog",
            "components.projects.ui_projects",
        ]
        for name in modules:
            with self.subTest(module=name):
                __import__(name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
