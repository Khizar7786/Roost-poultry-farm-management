from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from farms.models import Farm, Shed

from .models import ChickBatch


class BatchShedOwnershipTests(APITestCase):
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
        cls.shed = Shed.objects.create(farm=cls.farm, name="Own shed", capacity=500)
        cls.other_shed = Shed.objects.create(farm=other_farm, name="Other shed", capacity=500)
        cls.batch = ChickBatch.objects.create(
            farm=cls.farm, shed=cls.shed, batch_number="EXISTING",
            arrival_date="2026-11-01", initial_count=100, current_count=100,
        )

    def setUp(self):
        self.client.force_authenticate(self.owner)

    def create_batch(self, shed):
        return self.client.post("/api/batches/", {
            "batch_number": "NEW", "shed": str(shed.pk) if shed else None,
            "arrival_date": "2026-11-01", "initial_count": 50,
        }, format="json")

    def test_owner_can_create_batch_in_own_shed(self):
        response = self.create_batch(self.shed)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        batch = ChickBatch.objects.get(batch_number="NEW")
        self.assertEqual(batch.farm, self.farm)
        self.assertEqual(batch.shed, self.shed)
        self.assertEqual(batch.current_count, 50)

    def test_batch_can_have_no_shed(self):
        response = self.create_batch(None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(ChickBatch.objects.get(batch_number="NEW").shed)

    def test_other_farms_shed_is_rejected_on_create(self):
        response = self.create_batch(self.other_shed)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shed", response.data)
        self.assertFalse(ChickBatch.objects.filter(batch_number="NEW").exists())

    def test_other_farms_shed_is_rejected_on_update(self):
        response = self.client.patch(f"/api/batches/{self.batch.pk}/", {
            "shed": str(self.other_shed.pk),
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shed", response.data)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.shed, self.shed)

    def test_employee_cannot_create_batches(self):
        self.client.force_authenticate(self.employee)
        self.assertEqual(self.create_batch(self.shed).status_code, status.HTTP_403_FORBIDDEN)
