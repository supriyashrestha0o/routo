from django.urls import path
from routo.accounts.views import AccountLinkView, MeView

urlpatterns = [path("link/", AccountLinkView.as_view()), path("me/", MeView.as_view())]
