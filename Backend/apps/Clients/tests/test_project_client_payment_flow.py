from rest_framework.test import APITestCase

from apps.Clients.models import Client, ClientProjectBalance, ProjectPayment
from apps.Projects.models.rent_projects_models import RentProjects
from apps.Safe.models import Safe


class ProjectClientPaymentFlowTest(APITestCase):
    def setUp(self):
        self.client_url = "/api/clients/clients/"
        self.supplier_url = "/api/suppliers/suppliers/"
        self.project_url = "/api/projects/"
        self.link_url = "/api/clients/projects/"
        self.payment_url = "/api/clients/projects/payments/"
        self.username = "test_user"

    def _create_client(self, name="Test Client", phone="01000000001"):
        response = self.client.post(
            self.client_url,
            {"name": name, "phone": phone, "username": self.username},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return Client.objects.latest("id")

    def _create_supplier(self, name="Test Supplier", phone="01000000002"):
        response = self.client.post(
            self.supplier_url,
            {"name": name, "phone": phone, "username": self.username},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        from apps.Suppliers.models import Supplier

        return Supplier.objects.latest("id")

    def _create_rent_project(self, supplier, cost=1000.0, name="Rent Project"):
        response = self.client.post(
            self.project_url,
            {
                "name": name,
                "project_type": "rent",
                "project_status": "active",
                "cost": cost,
                "supplier": supplier.id,
                "username": self.username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        return response.data["id"]

    def _link_project(self, client_id, project_id, project_type="rent"):
        response = self.client.post(
            self.link_url,
            {
                "project_type": project_type,
                "project_id": str(project_id),
                "client_id": str(client_id),
                "username": self.username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return response.data["data"]

    def test_rent_project_full_flow_cash_payment(self):
        client = self._create_client()
        supplier = self._create_supplier()
        project_id = self._create_rent_project(supplier, cost=1000.0)
        link_data = self._link_project(client.id, project_id)

        list_response = self.client.get(
            self.link_url, {"client_id": client.id}, format="json"
        )
        self.assertEqual(list_response.status_code, 200)
        results = list_response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["total"], 1000.0)
        self.assertEqual(results[0]["paid"], 0)
        self.assertEqual(results[0]["remining"], 1000.0)

        payment_response = self.client.post(
            self.payment_url,
            {
                "project_id": project_id,
                "project_type": "rent",
                "payment_amount": 500,
                "payment_type": "cash",
                "payment_date": "2026-06-07",
                "user_name": self.username,
            },
            format="json",
        )
        self.assertEqual(payment_response.status_code, 200)
        self.assertEqual(payment_response.data["status"], "sucess")

        cbp = ClientProjectBalance.objects.get(id=link_data["cbp_id"])
        self.assertEqual(cbp.paid, 500)
        self.assertEqual(cbp.remining, 500)

        client.refresh_from_db()
        self.assertEqual(client.total_balance_owed_to_us, 1000.0)
        self.assertEqual(client.total_remaining_balance_owed_to_us, 500.0)
        self.assertEqual(client.total_paid_amount, 500.0)

        safe = Safe.objects.get(id=1)
        self.assertEqual(safe.balance, 500.0)

    def test_payment_rejects_amount_over_remaining(self):
        client = self._create_client()
        supplier = self._create_supplier()
        project_id = self._create_rent_project(supplier, cost=1000.0)
        self._link_project(client.id, project_id)

        response = self.client.post(
            self.payment_url,
            {
                "project_id": project_id,
                "project_type": "rent",
                "payment_amount": 1500,
                "payment_type": "cash",
                "payment_date": "2026-06-07",
                "user_name": self.username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_check_payment_cleared_via_patch(self):
        client = self._create_client()
        supplier = self._create_supplier()
        project_id = self._create_rent_project(supplier, cost=1000.0)
        link_data = self._link_project(client.id, project_id)

        check_response = self.client.post(
            self.payment_url,
            {
                "project_id": project_id,
                "project_type": "rent",
                "payment_amount": 300,
                "payment_type": "check",
                "payment_date": "2026-06-07",
                "check_date": "2026-07-01",
                "user_name": self.username,
            },
            format="json",
        )
        self.assertEqual(check_response.status_code, 200)

        cbp = ClientProjectBalance.objects.get(id=link_data["cbp_id"])
        self.assertEqual(cbp.paid, 0)
        self.assertEqual(cbp.remining, 1000.0)

        payment = ProjectPayment.objects.latest("id")
        self.assertFalse(payment.is_cleared)

        clear_response = self.client.patch(
            self.payment_url,
            {"payment_id": payment.id, "user_name": self.username},
            format="json",
        )
        self.assertEqual(clear_response.status_code, 200)

        cbp.refresh_from_db()
        self.assertEqual(cbp.paid, 300)
        self.assertEqual(cbp.remining, 700)

        client.refresh_from_db()
        self.assertEqual(client.total_paid_amount, 300)

        safe = Safe.objects.get(id=1)
        self.assertEqual(safe.balance, 300.0)

    def test_link_rent_project_creates_rent_detail_row(self):
        client = self._create_client()
        supplier = self._create_supplier()
        project_id = self._create_rent_project(supplier, cost=800.0)
        link_data = self._link_project(client.id, project_id)

        rent_row = RentProjects.objects.get(CPB_fk_id=link_data["cbp_id"])
        self.assertEqual(rent_row.buying_price, 800.0)

    def test_payment_requires_user_name(self):
        client = self._create_client()
        supplier = self._create_supplier()
        project_id = self._create_rent_project(supplier)
        self._link_project(client.id, project_id)

        response = self.client.post(
            self.payment_url,
            {
                "project_id": project_id,
                "project_type": "rent",
                "payment_amount": 100,
                "payment_type": "cash",
                "payment_date": "2026-06-07",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
