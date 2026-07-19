from __future__ import annotations

from apps.time_records.models import TimeRecord


class TimeRecordRepository:
    """Acesso a dados de registros de ponto via Django ORM (SQLite)."""

    def get_by_date(self, user_id: str, record_date: str) -> dict | None:
        record = TimeRecord.objects.filter(user_id=user_id, date=record_date).first()
        return record.to_document() if record else None

    def list_month(self, user_id: str, year: int, month: int) -> list[dict]:
        month_prefix = f"{year:04d}-{month:02d}-"
        records = TimeRecord.objects.filter(
            user_id=user_id, date__startswith=month_prefix
        ).order_by("date")
        return [record.to_document() for record in records]

    def upsert(self, document: dict) -> dict:
        times = document.get("times") or {}
        TimeRecord.objects.update_or_create(
            user_id=document["user_id"],
            date=document["date"],
            defaults={
                "day_type": document["day_type"],
                "arrival": times.get("arrival"),
                "lunch_start": times.get("lunch_start"),
                "lunch_end": times.get("lunch_end"),
                "departure": times.get("departure"),
                "notes": document.get("notes") or "",
                "status": document["status"],
                "created_at": document["created_at"],
                "updated_at": document["updated_at"],
            },
        )
        return document

    def delete(self, user_id: str, record_date: str) -> bool:
        deleted_count, _ = TimeRecord.objects.filter(
            user_id=user_id, date=record_date
        ).delete()
        return deleted_count == 1
