from django.urls import path

from . import views

urlpatterns = [
    path("stock/", views.FeedStockListCreateView.as_view(), name="feed-stock-list-create"),
    path("logs/", views.FeedConsumptionLogListCreateView.as_view(), name="feed-log-list-create"),
]
