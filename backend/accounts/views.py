from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.permissions import IsFarmOwner

from .models import User
from .serializers import (
    RegisterEmployeeSerializer,
    RegisterFarmSerializer,
    UserSerializer,
)


class RegisterFarmView(generics.CreateAPIView):
    """UC-05 Register Farm/Account. Open to anyone (no auth required)."""

    serializer_class = RegisterFarmSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Farm and owner account created. You can now log in.",
                "user": UserSerializer(user).data,
                "farm_id": str(user.farm_id),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """UC-04 User Login. POST {username, password} -> {access, refresh}.

    (djangorestframework-simplejwt's default serializer already implements
    the "validate credentials against the database" / "invalid credentials
    -> error message" flow from the use case's main and alternative flows.)
    """


class RegisterEmployeeView(generics.CreateAPIView):
    """Owner creates a Farm Employee account under their farm."""

    serializer_class = RegisterEmployeeSerializer
    permission_classes = [IsFarmOwner]

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class EmployeeListView(generics.ListAPIView):
    """Owner's roster of employees, for the "manage staff" screen."""

    serializer_class = UserSerializer
    permission_classes = [IsFarmOwner]

    def get_queryset(self):
        return User.objects.filter(farm=self.request.user.farm, role="EMPLOYEE").order_by("first_name")


class DeactivateEmployeeView(APIView):
    """Owner disables an employee's access without deleting their history
    (their past logs/counting-sessions stay attributed to them)."""

    permission_classes = [IsFarmOwner]

    def post(self, request, employee_id):
        employee = User.objects.filter(id=employee_id, farm=request.user.farm, role="EMPLOYEE").first()
        if not employee:
            return Response({"detail": "Employee not found on your farm."}, status=status.HTTP_404_NOT_FOUND)
        employee.is_active_employee = False
        employee.is_active = False
        employee.save(update_fields=["is_active_employee", "is_active"])
        return Response({"message": f"{employee.username} deactivated."})


class MeView(APIView):
    """Whoever is logged in — used by the frontend right after login to
    decide whether to route to the Owner dashboard or the Employee task
    view."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
