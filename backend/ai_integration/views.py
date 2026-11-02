from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import engine


class AIServiceStatusView(APIView):
    """Inference now runs in-process inside Django (no separate service
    to reach), so this is mostly a compatibility no-op — kept in case a
    future deployment splits inference back out into its own service."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"ai_engine_healthy": engine.health_check()})
