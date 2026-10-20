from django.urls import path
from . import views
app_name = "hotels"
urlpatterns = [path("", views.home, name="home"), path("rooms/", views.room_list, name="room_list"), path("rooms/<int:pk>/", views.room_detail, name="room_detail")]
