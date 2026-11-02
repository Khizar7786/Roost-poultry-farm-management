from rest_framework import status

from farms.models import Farm
from tests.helpers import FarmAPITestCase

from .models import Role, User


class AuthenticationTests(FarmAPITestCase):
    def login(self, username="owner", password=None):
        return self.client.post("/api/auth/login/", {
            "username": username, "password": self.password if password is None else password,
        }, format="json")

    def test_login_token_authenticates_profile_request(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        profile = self.client.get("/api/auth/me/")
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data["username"], self.owner.username)
        self.assertEqual(profile.data["role"], Role.OWNER)
        self.assertEqual(str(profile.data["farm"]), str(self.farm.pk))
        self.assertNotIn("password", profile.data)

    def test_wrong_password_is_rejected(self):
        self.assertEqual(self.login(password="incorrect").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_log_in(self):
        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        self.assertEqual(self.login().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_requests_cannot_read_private_endpoints(self):
        for path in ["/api/auth/me/", "/api/dashboard/", "/api/batches/", "/api/feed/stock/", "/api/sales/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_access_token_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-test-token")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_returns_a_working_access_token(self):
        login = self.login()
        response = self.client.post("/api/auth/login/refresh/", {
            "refresh": login.data["refresh"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_200_OK)

    def test_invalid_refresh_token_is_rejected(self):
        response = self.client.post("/api/auth/login/refresh/", {"refresh": "invalid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivation_blocks_login_and_an_existing_access_token(self):
        login = self.login(username=self.employee.username)
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        token = login.data["access"]
        self.client.force_authenticate(self.owner)
        response = self.client.post(f"/api/auth/employees/{self.employee.pk}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.login(username=self.employee.username).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)


class RegistrationTests(FarmAPITestCase):
    def payload(self):
        return {
            "full_name": "Test Farmer", "username": "new-owner", "email": "new@example.test",
            "password": self.password, "farm_name": "New farm", "farm_location": "Test",
        }

    def test_registration_creates_farm_and_owner_and_hashes_password(self):
        payload = self.payload()
        payload.update(role=Role.ADMIN, is_staff=True, is_superuser=True)
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-owner")
        self.assertEqual(user.role, Role.OWNER)
        self.assertEqual(user.farm.owner, user)
        self.assertEqual(user.farm.name, "New farm")
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn("password", response.data["user"])

    def test_duplicate_username_and_email_are_rejected_without_creating_a_farm(self):
        for field, value in [("username", "OWNER"), ("email", "OWNER@EXAMPLE.TEST")]:
            with self.subTest(field=field):
                payload = self.payload()
                payload[field] = value
                response = self.client.post("/api/auth/register/", payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
                self.assertEqual(Farm.objects.count(), 2)
                self.assertFalse(User.objects.filter(username="new-owner").exists())

    def test_weak_password_is_rejected(self):
        payload = self.payload()
        payload["password"] = "123"
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(Farm.objects.count(), 2)

    def test_owner_creates_employee_on_own_farm(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/auth/employees/register/", {
            "full_name": "Test Employee", "username": "new-employee", "email": "staff@example.test",
            "password": self.password, "role": Role.ADMIN, "farm": str(self.other_farm.pk),
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-employee")
        self.assertEqual(user.role, Role.EMPLOYEE)
        self.assertEqual(user.farm, self.farm)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(self.password))

    def test_duplicate_employee_username_is_a_validation_error(self):
        self.client.force_authenticate(self.owner)
        for username in ["employee", "EMPLOYEE"]:
            with self.subTest(username=username):
                response = self.client.post("/api/auth/employees/register/", {
                    "full_name": "Duplicate Employee", "username": username, "email": "duplicate@example.test",
                    "password": self.password,
                }, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("username", response.data)
                self.assertFalse(User.objects.filter(email="duplicate@example.test").exists())
