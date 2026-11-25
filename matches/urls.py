from django.urls import path
from matches.views import MatchListView
urlpatterns = [path("", MatchListView.as_view())]
