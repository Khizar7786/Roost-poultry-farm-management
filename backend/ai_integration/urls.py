from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.AIServiceStatusView.as_view(), name="ai-status"),
]
