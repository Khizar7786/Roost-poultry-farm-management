from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import answer_query


class ChatQuerySerializer(serializers.Serializer):
    query = serializers.CharField(max_length=500)


class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = answer_query(serializer.validated_data["query"])
        return Response(result)
