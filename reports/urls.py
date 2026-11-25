from django.urls import path
from reports.views import ReportListCreateView
urlpatterns = [path("", ReportListCreateView.as_view())]
