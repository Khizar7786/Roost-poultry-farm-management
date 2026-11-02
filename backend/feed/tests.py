from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import Role, User
from batches.models import ChickBatch
from farms.models import Farm

from .models import FeedConsumptionLog, FeedStock
from .serializers import FeedConsumptionLogSerializer
from .views import FeedConsumptionLogListCreateView


class FeedValidationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", role=Role.OWNER)
        other_owner = User.objects.create_user(username="other", role=Role.OWNER)
        cls.farm = Farm.objects.create(name="Own farm", location="Test", owner=cls.owner)
        other_farm = Farm.objects.create(name="Other farm", location="Test", owner=other_owner)
        cls.owner.farm = cls.farm
        cls.owner.save(update_fields=["farm"])
        cls.employee = User.objects.create_user(
            username="employee", role=Role.EMPLOYEE, farm=cls.farm,
        )
        cls.batch = ChickBatch.objects.create(
            farm=cls.farm, batch_number="OWN", arrival_date="2026-11-01",
            initial_count=100, current_count=100,
        )
        cls.other_batch = ChickBatch.objects.create(
            farm=other_farm, batch_number="OTHER", arrival_date="2026-11-01",
            initial_count=100, current_count=100,
        )
        cls.stock = FeedStock.objects.create(farm=cls.farm, feed_type="Starter", quantity_kg=100)
        cls.other_stock = FeedStock.objects.create(
            farm=other_farm, feed_type="Starter", quantity_kg=100,
        )

    def setUp(self):
        self.client.force_authenticate(self.owner)

    def log_payload(self, quantity="25.00"):
        return {
            "batch": str(self.batch.pk), "feed_stock": str(self.stock.pk),
            "quantity_kg": quantity, "log_date": "2026-11-02",
        }

    def test_negative_and_zero_consumption_are_rejected(self):
        for quantity in ["-5.00", "0.00"]:
            with self.subTest(quantity=quantity):
                response = self.client.post("/api/feed/logs/", self.log_payload(quantity), format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("quantity_kg", response.data)
                self.stock.refresh_from_db()
                self.assertEqual(self.stock.quantity_kg, Decimal("100.00"))
                self.assertFalse(FeedConsumptionLog.objects.exists())

    def test_employee_can_log_positive_consumption(self):
        self.client.force_authenticate(self.employee)
        response = self.client.post("/api/feed/logs/", self.log_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("75.00"))
        self.assertEqual(FeedConsumptionLog.objects.get().logged_by, self.employee)

    def test_consuming_exact_remaining_stock_is_allowed(self):
        response = self.client.post("/api/feed/logs/", self.log_payload("100.00"), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("0.00"))

    def test_consumption_above_remaining_stock_is_rejected(self):
        response = self.client.post("/api/feed/logs/", self.log_payload("101.00"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("100.00"))
        self.assertFalse(FeedConsumptionLog.objects.exists())

    def test_fractional_consumption_can_use_the_exact_remaining_stock(self):
        FeedStock.objects.filter(pk=self.stock.pk).update(quantity_kg=Decimal("0.30"))
        for quantity in ["0.10", "0.20"]:
            response = self.client.post("/api/feed/logs/", self.log_payload(quantity), format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("0.00"))

    def test_other_farms_stock_and_batch_are_rejected(self):
        for field, value in [("feed_stock", self.other_stock.pk), ("batch", self.other_batch.pk)]:
            with self.subTest(field=field):
                payload = self.log_payload()
                payload[field] = str(value)
                response = self.client.post("/api/feed/logs/", payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertFalse(FeedConsumptionLog.objects.exists())
        self.stock.refresh_from_db()
        self.other_stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("100.00"))
        self.assertEqual(self.other_stock.quantity_kg, Decimal("100.00"))

    def test_negative_stock_and_reorder_threshold_are_rejected(self):
        for field in ["quantity_kg", "reorder_threshold_kg"]:
            with self.subTest(field=field):
                feed_type = f"Grower {field}"
                payload = {"feed_type": feed_type, "quantity_kg": "50.00", "reorder_threshold_kg": "10.00"}
                payload[field] = "-1.00"
                response = self.client.post("/api/feed/stock/", payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
                self.assertFalse(FeedStock.objects.filter(feed_type=feed_type).exists())

    def test_zero_stock_and_reorder_threshold_are_allowed(self):
        response = self.client.post("/api/feed/stock/", {
            "feed_type": "Grower", "quantity_kg": "0.00", "reorder_threshold_kg": "0.00",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_stock_is_rechecked_after_request_validation(self):
        request = SimpleNamespace(user=self.owner)
        serializer = FeedConsumptionLogSerializer(
            data=self.log_payload("80.00"), context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Another request consumes stock between validation and saving this one.
        FeedStock.objects.filter(pk=self.stock.pk).update(quantity_kg=Decimal("30.00"))
        view = FeedConsumptionLogListCreateView()
        view.request = request
        with self.assertRaises(ValidationError):
            view.perform_create(serializer)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("30.00"))
        self.assertFalse(FeedConsumptionLog.objects.exists())

    def test_failed_log_creation_rolls_back_stock_deduction(self):
        request = SimpleNamespace(user=self.owner)
        serializer = FeedConsumptionLogSerializer(
            data=self.log_payload(), context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        view = FeedConsumptionLogListCreateView()
        view.request = request
        with patch.object(serializer, "save", side_effect=RuntimeError("Test save failure")):
            with self.assertRaises(RuntimeError):
                view.perform_create(serializer)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity_kg, Decimal("100.00"))
        self.assertFalse(FeedConsumptionLog.objects.exists())
