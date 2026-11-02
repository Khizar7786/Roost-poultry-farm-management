from unittest.mock import patch

from rest_framework import status

from feed.models import FeedStock
from tests.helpers import FarmAPITestCase


class RolePermissionTests(FarmAPITestCase):
    def test_owner_can_read_financial_and_staff_endpoints(self):
        self.client.force_authenticate(self.owner)
        for path in ["/api/sales/", "/api/auth/employees/", "/api/monitoring/price-predictions/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, status.HTTP_200_OK)

    def test_employee_and_admin_cannot_use_owner_only_endpoints(self):
        for user in [self.employee, self.system_admin]:
            self.client.force_authenticate(user)
            for path in ["/api/sales/", "/api/auth/employees/", "/api/monitoring/price-predictions/"]:
                with self.subTest(role=user.role, path=path):
                    self.assertEqual(self.client.get(path).status_code, status.HTTP_403_FORBIDDEN)
            for path in ["/api/sales/", "/api/auth/employees/register/", "/api/monitoring/price-predictions/trigger/"]:
                with self.subTest(role=user.role, path=path, method="POST"):
                    self.assertEqual(self.client.post(path, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_can_read_operational_endpoints(self):
        self.client.force_authenticate(self.employee)
        for path in ["/api/batches/", "/api/feed/stock/", "/api/health/vaccinations/", "/api/alerts/", "/api/dashboard/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, status.HTTP_200_OK)

    def test_employee_cannot_restock_feed(self):
        self.client.force_authenticate(self.employee)
        response = self.client.post("/api/feed/stock/", {
            "feed_type": "Starter", "quantity_kg": "100.00",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(FeedStock.objects.exists())

    def test_employee_cannot_change_or_delete_a_batch(self):
        self.client.force_authenticate(self.employee)
        path = f"/api/batches/{self.batch.pk}/"
        self.assertEqual(self.client.patch(path, {"status": "SOLD"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(path).status_code, status.HTTP_403_FORBIDDEN)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, "ACTIVE")

    def test_admin_can_use_django_administration(self):
        self.client.force_login(self.system_admin)
        self.assertEqual(self.client.get("/admin/").status_code, status.HTTP_200_OK)

    def test_ordinary_owner_cannot_use_django_administration(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get("/admin/").status_code, status.HTTP_302_FOUND)

    @patch("monitoring.views.predict_price")
    def test_denied_forecast_request_does_not_run_the_model(self, predict_price):
        self.client.force_authenticate(self.employee)
        response = self.client.post("/api/monitoring/price-predictions/trigger/", {"horizon_days": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        predict_price.assert_not_called()
