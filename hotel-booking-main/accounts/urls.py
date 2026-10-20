from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [path("signup/", views.signup, name="signup"), path("username-availability/", views.username_availability, name="username_availability"), path("dashboard/", views.dashboard, name="dashboard"), path("profile/", views.profile_edit, name="profile_edit"), path("staff/", views.staff_dashboard, name="staff_dashboard")]
