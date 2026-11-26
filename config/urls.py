
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse

from config.health import health


def home(request):
    return HttpResponse("Route API is running successfully!")

urlpatterns = [
    path('', home, name='home'),
    path('health', health, name='health'),
    path('health/', health, name='health-slash'),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/journeys/', include('journeys.urls')),
    path('api/ride-requests/', include('ride_requests.urls')),
    path('api/matches/', include('matches.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/reports/', include('reports.urls')),
]
