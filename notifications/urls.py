from django.urls import path
from routo.notifications.views import DeviceTokenDeleteView, DeviceTokenListCreateView
urlpatterns = [path("devices/", DeviceTokenListCreateView.as_view()), path("devices/<int:token_id>/", DeviceTokenDeleteView.as_view())]
