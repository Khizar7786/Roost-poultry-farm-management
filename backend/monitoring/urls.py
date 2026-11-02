from django.urls import path

from . import views

urlpatterns = [
    path("counting-sessions/", views.CountingSessionListCreateView.as_view(), name="counting-session-list-create"),
    path("mortality-events/", views.MortalityEventListCreateView.as_view(), name="mortality-event-list-create"),
    path("price-predictions/", views.PricePredictionListView.as_view(), name="price-prediction-list"),
    path("price-predictions/trigger/", views.TriggerPricePredictionView.as_view(), name="price-prediction-trigger"),
]
