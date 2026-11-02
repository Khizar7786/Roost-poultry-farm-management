from django.urls import path

from . import views

urlpatterns = [
    path("ask/", views.ChatbotView.as_view(), name="chatbot-ask"),
]
