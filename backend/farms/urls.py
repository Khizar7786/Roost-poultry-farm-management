from django.urls import path

from . import views

urlpatterns = [
    path("mine/", views.MyFarmView.as_view(), name="my-farm"),
    path("sheds/", views.ShedListCreateView.as_view(), name="shed-list-create"),
]
