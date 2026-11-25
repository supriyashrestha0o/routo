from django.urls import path
from routo.reports.views import ReportListCreateView
urlpatterns = [path("", ReportListCreateView.as_view())]
