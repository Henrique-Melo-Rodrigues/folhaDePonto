from __future__ import annotations

import re

from rest_framework import serializers


DAY_TYPES = (
    "trabalho",
    "atividade_teorica",
    "folga",
    "compensacao",
    "feriado",
    "falta",
    "outro",
)

TIME_FIELDS = ("arrival", "lunch_start", "lunch_end", "departure")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


class TimesSerializer(serializers.Serializer):
    arrival = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    lunch_start = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    lunch_end = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    departure = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: dict) -> dict:
        return {field: self._normalize_time(attrs.get(field)) for field in TIME_FIELDS}

    @staticmethod
    def _normalize_time(value: str | None) -> str | None:
        if value in (None, ""):
            return None

        if not isinstance(value, str) or not TIME_RE.fullmatch(value):
            raise serializers.ValidationError("Use horarios no formato HH:MM.")

        hour, minute = value.split(":")
        if int(hour) > 23 or int(minute) > 59:
            raise serializers.ValidationError("Use horarios validos entre 00:00 e 23:59.")

        return value


class TimeRecordInputSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=["%Y-%m-%d"], format="%Y-%m-%d")
    day_type = serializers.ChoiceField(choices=DAY_TYPES)
    times = TimesSerializer(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: dict) -> dict:
        attrs["date"] = attrs["date"].isoformat()
        attrs["times"] = attrs.get("times") or {field: None for field in TIME_FIELDS}
        attrs["notes"] = attrs.get("notes") or ""
        return attrs


class MonthQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)

