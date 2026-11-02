from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from batches.models import ChickBatch
from farms.models import Farm, Shed


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FarmAPITestCase(APITestCase):
    """Two isolated farms and all three roles; fast hashing is test-only."""

    password = "TestOnly-SpruceBridge-83!"

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner", email="owner@example.test", password=cls.password, role=Role.OWNER,
        )
        cls.other_owner = User.objects.create_user(username="other-owner", role=Role.OWNER)
        cls.farm = Farm.objects.create(name="Own farm", location="Test", owner=cls.owner)
        cls.other_farm = Farm.objects.create(name="Other farm", location="Test", owner=cls.other_owner)
        for user, farm in [(cls.owner, cls.farm), (cls.other_owner, cls.other_farm)]:
            user.farm = farm
            user.save(update_fields=["farm"])
        cls.employee = User.objects.create_user(
            username="employee", email="employee@example.test", password=cls.password,
            role=Role.EMPLOYEE, farm=cls.farm,
        )
        cls.other_employee = User.objects.create_user(
            username="other-employee", role=Role.EMPLOYEE, farm=cls.other_farm,
        )
        cls.system_admin = User.objects.create_user(
            username="system-admin", password=cls.password, role=Role.ADMIN,
            is_staff=True, is_superuser=True,
        )
        cls.shed = Shed.objects.create(farm=cls.farm, name="Own shed", capacity=1000)
        cls.other_shed = Shed.objects.create(farm=cls.other_farm, name="Other shed", capacity=1000)
        cls.today = timezone.localdate()
        cls.batch = ChickBatch.objects.create(
            farm=cls.farm, shed=cls.shed, batch_number="OWN", arrival_date=cls.today,
            initial_count=100, current_count=90, created_by=cls.owner,
        )
        cls.other_batch = ChickBatch.objects.create(
            farm=cls.other_farm, shed=cls.other_shed, batch_number="OTHER", arrival_date=cls.today,
            initial_count=500, current_count=500, created_by=cls.other_owner,
        )

    def assert_list_ids(self, response, expected_ids):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertSetEqual({str(row["id"]) for row in records}, {str(pk) for pk in expected_ids})
