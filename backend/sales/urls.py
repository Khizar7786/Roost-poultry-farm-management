from django.urls import path

from . import views

urlpatterns = [
    path("", views.SaleRecordListCreateView.as_view(), name="sale-list-create"),
    path("<uuid:pk>/", views.SaleRecordDetailView.as_view(), name="sale-detail"),
]
