from django.urls import path

from . import views

urlpatterns = [
    path("", views.ChickBatchListCreateView.as_view(), name="batch-list-create"),
    path("<uuid:pk>/", views.ChickBatchDetailView.as_view(), name="batch-detail"),
]
