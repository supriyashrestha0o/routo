from django.urls import path
from routo.matches.views import MatchListView
urlpatterns = [path("", MatchListView.as_view())]
