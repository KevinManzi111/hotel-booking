from django.urls import path
from . import views
app_name = "bookings"
urlpatterns = [path("", views.booking_list, name="list"), path("new/<int:room_id>/", views.create_booking, name="create"), path("<int:pk>/", views.booking_detail, name="detail"), path("<int:pk>/cancel/", views.cancel_booking, name="cancel")]
