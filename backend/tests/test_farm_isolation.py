from decimal import Decimal

from rest_framework import status

from alerts.models import Alert, AlertType
from feed.models import FeedConsumptionLog, FeedStock
from health.models import VaccinationRecord, VaccinationStatus
from monitoring.models import MortalityEvent, MortalitySource, PricePrediction
from sales.models import SaleRecord
from tests.helpers import FarmAPITestCase


class FarmIsolationTests(FarmAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.rows = {}
        for label, farm, owner, batch in [
            ("own", cls.farm, cls.owner, cls.batch),
            ("other", cls.other_farm, cls.other_owner, cls.other_batch),
        ]:
            stock = FeedStock.objects.create(farm=farm, feed_type="Starter", quantity_kg=10)
            log = FeedConsumptionLog.objects.create(
                batch=batch, feed_stock=stock, quantity_kg=1, log_date=cls.today, logged_by=owner,
            )
            vaccine = VaccinationRecord.objects.create(
                batch=batch, vaccine_name="Test vaccine", scheduled_date=cls.today, scheduled_by=owner,
            )
            mortality = MortalityEvent.objects.create(
                batch=batch, source=MortalitySource.MANUAL, detected_count=1, confirmed=True, logged_by=owner,
            )
            alert = Alert.objects.create(farm=farm, batch=batch, alert_type=AlertType.SYSTEM, message=label)
            sale = SaleRecord.objects.create(
                farm=farm, batch=batch, buyer_name=label, quantity=10,
                price_per_unit=Decimal("350.00"), sale_date=cls.today, recorded_by=owner,
            )
            forecast = PricePrediction.objects.create(
                farm=farm, requested_by=owner, horizon_days=1,
                forecast=[{"price_pkr": 350 if label == "own" else 999}],
            )
            cls.rows[label] = {
                "/api/batches/": batch, "/api/feed/stock/": stock,
                "/api/feed/logs/": log, "/api/health/vaccinations/": vaccine,
                "/api/monitoring/mortality-events/": mortality, "/api/alerts/": alert,
                "/api/sales/": sale, "/api/monitoring/price-predictions/": forecast,
            }

    def setUp(self):
        self.client.force_authenticate(self.owner)

    def test_owner_lists_only_own_farm_records(self):
        for path, record in self.rows["own"].items():
            with self.subTest(path=path):
                self.assert_list_ids(self.client.get(path), [record.pk])

    def test_employee_lists_only_own_farm_operational_records(self):
        self.client.force_authenticate(self.employee)
        for path, record in self.rows["own"].items():
            if path in ["/api/sales/", "/api/monitoring/price-predictions/"]:
                continue
            with self.subTest(path=path):
                self.assert_list_ids(self.client.get(path), [record.pk])

    def test_staff_roster_does_not_expose_other_farms_employees(self):
        self.assert_list_ids(self.client.get("/api/auth/employees/"), [self.employee.pk])

    def test_owner_cannot_deactivate_another_farms_employee(self):
        response = self.client.post(f"/api/auth/employees/{self.other_employee.pk}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_employee.refresh_from_db()
        self.assertTrue(self.other_employee.is_active)

    def test_foreign_batch_cannot_be_read_updated_or_deleted(self):
        path = f"/api/batches/{self.other_batch.pk}/"
        self.assertEqual(self.client.get(path).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(path, {"batch_number": "CHANGED"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(path).status_code, status.HTTP_404_NOT_FOUND)
        self.other_batch.refresh_from_db()
        self.assertEqual(self.other_batch.batch_number, "OTHER")

    def test_foreign_sale_cannot_be_read_updated_or_deleted(self):
        sale = self.rows["other"]["/api/sales/"]
        path = f"/api/sales/{sale.pk}/"
        self.assertEqual(self.client.get(path).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(path, {"buyer_name": "CHANGED"}, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(path).status_code, status.HTTP_404_NOT_FOUND)
        sale.refresh_from_db()
        self.assertEqual(sale.buyer_name, "other")

    def test_sale_cannot_reference_another_farms_batch(self):
        response = self.client.post("/api/sales/", {
            "batch": str(self.other_batch.pk), "buyer_name": "Test", "quantity": 1,
            "price_per_unit": "350.00", "sale_date": str(self.today),
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SaleRecord.objects.count(), 2)

    def test_foreign_alert_cannot_be_acknowledged(self):
        alert = self.rows["other"]["/api/alerts/"]
        response = self.client.post(f"/api/alerts/{alert.pk}/acknowledge/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        alert.refresh_from_db()
        self.assertFalse(alert.acknowledged)

    def test_foreign_vaccination_cannot_be_marked_administered(self):
        record = self.rows["other"]["/api/health/vaccinations/"]
        response = self.client.post(f"/api/health/vaccinations/{record.pk}/administer/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        record.refresh_from_db()
        self.assertEqual(record.status, VaccinationStatus.SCHEDULED)

    def test_dashboard_uses_only_own_farm_totals_and_forecast(self):
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["farm_name"], self.farm.name)
        self.assertEqual(response.data["flock_overview"]["active_batch_count"], 1)
        self.assertEqual(response.data["flock_overview"]["total_birds"], 90)
        self.assertEqual(response.data["market_price_forecast"]["forecast"], [{"price_pkr": 350}])

    def test_employee_dashboard_omits_owner_forecast(self):
        self.client.force_authenticate(self.employee)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("market_price_forecast", response.data)

    def test_farm_profile_and_sheds_belong_to_logged_in_user(self):
        response = self.client.get("/api/farms/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.farm.pk))
        self.assert_list_ids(self.client.get("/api/farms/sheds/"), [self.shed.pk])
