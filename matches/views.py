from rest_framework import generics
from routo.matches.models import Match
from routo.matches.serializers import MatchSerializer
class MatchListView(generics.ListAPIView):
    serializer_class = MatchSerializer
    def get_queryset(self):
        return Match.objects.filter(passenger=self.request.user) | Match.objects.filter(journey__driver=self.request.user)
