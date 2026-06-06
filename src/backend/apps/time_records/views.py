from __future__ import annotations

import re

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.time_records.permissions import HasAPIKey
from apps.time_records.repositories import TimeRecordRepository
from apps.time_records.serializers import MonthQuerySerializer, TimeRecordInputSerializer
from apps.time_records.services import TimeRecordService

_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")


def get_time_record_service() -> TimeRecordService:
    return TimeRecordService(TimeRecordRepository())


def _invalid_date_response(record_date: str) -> Response | None:
    if not _DATE_RE.fullmatch(record_date):
        return Response(
            {"error": "Data inválida. Use o formato YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class TimeRecordCreateView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        serializer = TimeRecordInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        record = get_time_record_service().save_record(serializer.validated_data)
        return Response(record, status=status.HTTP_201_CREATED)


class TodayTimeRecordView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request):
        record = get_time_record_service().get_today()
        if not record:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(record)


class MonthTimeRecordView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request):
        serializer = MonthQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        records = get_time_record_service().list_month(
            serializer.validated_data["year"],
            serializer.validated_data["month"],
        )
        return Response({"results": records})


class TimeRecordDetailView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request, record_date: str):
        if err := _invalid_date_response(record_date):
            return err
        record = get_time_record_service().get_by_date(record_date)
        if not record:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(record)

    def put(self, request, record_date: str):
        if err := _invalid_date_response(record_date):
            return err
        data = dict(request.data)
        data["date"] = record_date

        serializer = TimeRecordInputSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        record = get_time_record_service().save_record(serializer.validated_data)
        return Response(record)

    def delete(self, request, record_date: str):
        if err := _invalid_date_response(record_date):
            return err
        deleted = get_time_record_service().delete(record_date)
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

