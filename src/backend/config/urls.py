from django.urls import include, path, re_path

from config.views import FrontendView

urlpatterns = [
    path("api/", include("apps.time_records.urls")),
    re_path(r"^(?!api/|assets/|static/).*$", FrontendView.as_view(), name="frontend"),
]
