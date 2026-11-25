from django.urls import path
from routo.ride_requests.views import DecideRideRequestView, JourneyRideRequestsView, MyRideRequestsView, RideRequestCreateView
urlpatterns = [path("", RideRequestCreateView.as_view()), path("mine/", MyRideRequestsView.as_view()), path("journeys/<int:journey_id>/", JourneyRideRequestsView.as_view()), path("<int:request_id>/<str:decision>/", DecideRideRequestView.as_view())]
