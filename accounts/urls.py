from django.urls import path
from accounts.views import AccountLinkView, MeView

urlpatterns = [path("link/", AccountLinkView.as_view()), path("me/", MeView.as_view())]
