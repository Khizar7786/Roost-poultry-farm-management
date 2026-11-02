from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterFarmView.as_view(), name="register-farm"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="login-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("employees/", views.EmployeeListView.as_view(), name="employee-list"),
    path("employees/register/", views.RegisterEmployeeView.as_view(), name="employee-register"),
    path("employees/<uuid:employee_id>/deactivate/", views.DeactivateEmployeeView.as_view(), name="employee-deactivate"),
]
