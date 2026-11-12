from django.urls import path
from . import views

app_name = "recommendations"

urlpatterns = [
    path("", views.recommendation_list, name="list"),
    path("preferences/", views.preferences, name="preferences"),
    path("api/concierge/", views.ai_concierge_api, name="ai_concierge_api"),
]
