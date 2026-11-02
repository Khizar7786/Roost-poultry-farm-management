from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFarmOwner

from .models import Shed
from .serializers import FarmSerializer, ShedSerializer


class MyFarmView(APIView):
    """The single farm the logged-in user belongs to — Owner or Employee."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.farm:
            return Response({"detail": "You are not attached to a farm yet."}, status=404)
        return Response(FarmSerializer(request.user.farm).data)


class ShedListCreateView(generics.ListCreateAPIView):
    """Owner manages sheds; Employees can view them (e.g. to file a
    counting session against the right shed)."""

    serializer_class = ShedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Shed.objects.filter(farm=self.request.user.farm)

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            raise PermissionDenied("Only the farm owner can add sheds.")
        serializer.save(farm=self.request.user.farm)
