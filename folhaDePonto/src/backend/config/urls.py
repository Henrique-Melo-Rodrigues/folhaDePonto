from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.time_records.urls")),
]

