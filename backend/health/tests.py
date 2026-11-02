from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from batches.models import ChickBatch
from farms.models import Farm

from .models import VaccinationRecord


class VaccinationOwnershipTests(APITestCase):
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

    def setUp(self):
        self.client.force_authenticate(self.owner)

    def schedule(self, batch):
        return self.client.post("/api/health/vaccinations/", {
            "batch": str(batch.pk), "vaccine_name": "Test vaccine",
            "scheduled_date": "2026-11-03",
        }, format="json")

    def test_owner_can_schedule_for_own_batch(self):
        response = self.schedule(self.batch)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = VaccinationRecord.objects.get()
        self.assertEqual(record.batch, self.batch)
        self.assertEqual(record.scheduled_by, self.owner)

    def test_other_farms_batch_is_rejected(self):
        response = self.schedule(self.other_batch)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("batch", response.data)
        self.assertFalse(VaccinationRecord.objects.exists())

    def test_employee_cannot_schedule_vaccinations(self):
        self.client.force_authenticate(self.employee)
        self.assertEqual(self.schedule(self.batch).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(VaccinationRecord.objects.exists())
