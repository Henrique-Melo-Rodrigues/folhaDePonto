from django.urls import path

from apps.time_records.views import (
    HealthView,
    MonthTimeRecordView,
    TimeRecordCreateView,
    TimeRecordDetailView,
    TodayTimeRecordView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("time-records/", TimeRecordCreateView.as_view(), name="time-record-create"),
    path("time-records/today/", TodayTimeRecordView.as_view(), name="time-record-today"),
    path("time-records/month/", MonthTimeRecordView.as_view(), name="time-record-month"),
    path("time-records/<str:record_date>/", TimeRecordDetailView.as_view(), name="time-record-detail"),
]

