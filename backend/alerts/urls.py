from django.urls import path

from . import views

urlpatterns = [
    path("", views.AlertListView.as_view(), name="alert-list"),
    path("<uuid:pk>/acknowledge/", views.AcknowledgeAlertView.as_view(), name="alert-acknowledge"),
    path("escalate-overdue/", views.EscalateOverdueAlertsView.as_view(), name="alert-escalate-overdue"),
]
