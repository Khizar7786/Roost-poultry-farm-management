from django.urls import path

from . import views

urlpatterns = [
    path("vaccinations/", views.VaccinationListCreateView.as_view(), name="vaccination-list-create"),
    path("vaccinations/<uuid:pk>/administer/", views.MarkAdministeredView.as_view(), name="vaccination-administer"),
]
