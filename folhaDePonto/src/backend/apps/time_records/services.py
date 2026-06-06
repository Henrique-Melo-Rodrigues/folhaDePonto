from __future__ import annotations

from datetime import date

from django.conf import settings
from django.utils import timezone

from apps.time_records.serializers import TIME_FIELDS


NOT_WORKED_DAY_TYPES = {
    "atividade_teorica",
    "folga",
    "compensacao",
    "feriado",
    "falta",
    "outro",
}


class TimeRecordService:
    def __init__(self, repository, user_id: str | None = None) -> None:
        self.repository = repository
        self.user_id = user_id or settings.FIXED_USER_ID

    def save_record(self, data: dict) -> dict:
        record_date = self._date_to_string(data["date"])
        times = self._normalize_times(data.get("times"))
        existing = self.repository.get_by_date(self.user_id, record_date)
        now = timezone.now().replace(microsecond=0).isoformat()

        document = {
            "user_id": self.user_id,
            "date": record_date,
            "day_type": data["day_type"],
            "times": times,
            "notes": data.get("notes") or "",
            "status": self.calculate_status(data["day_type"], times),
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }
        return self.repository.upsert(document)

    def get_today(self) -> dict | None:
        return self.get_by_date(timezone.localdate().isoformat())

    def get_by_date(self, record_date: str) -> dict | None:
        return self.repository.get_by_date(self.user_id, record_date)

    def list_month(self, year: int, month: int) -> list[dict]:
        return self.repository.list_month(self.user_id, year, month)

    def delete(self, record_date: str) -> bool:
        return self.repository.delete(self.user_id, record_date)

    @staticmethod
    def calculate_status(day_type: str, times: dict) -> str:
        values = [times.get(field) for field in TIME_FIELDS]
        has_any_time = any(values)
        has_all_times = all(values)

        if day_type in NOT_WORKED_DAY_TYPES and not has_any_time:
            return "not_worked"

        if has_all_times:
            return "complete"

        return "incomplete"

    @staticmethod
    def _normalize_times(times: dict | None) -> dict:
        times = times or {}
        return {field: times.get(field) or None for field in TIME_FIELDS}

    @staticmethod
    def _date_to_string(value: date | str) -> str:
        return value.isoformat() if isinstance(value, date) else value

