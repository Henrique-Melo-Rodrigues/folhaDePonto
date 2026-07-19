from __future__ import annotations

from django.db import models


class TimeRecord(models.Model):
    user_id = models.CharField(max_length=64)
    date = models.CharField(max_length=10)
    day_type = models.CharField(max_length=32)
    arrival = models.CharField(max_length=5, null=True, blank=True)
    lunch_start = models.CharField(max_length=5, null=True, blank=True)
    lunch_end = models.CharField(max_length=5, null=True, blank=True)
    departure = models.CharField(max_length=5, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16)
    created_at = models.CharField(max_length=32)
    updated_at = models.CharField(max_length=32)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id", "date"], name="unique_user_date"),
        ]
        ordering = ["date"]

    def to_document(self) -> dict:
        return {
            "user_id": self.user_id,
            "date": self.date,
            "day_type": self.day_type,
            "times": {
                "arrival": self.arrival,
                "lunch_start": self.lunch_start,
                "lunch_end": self.lunch_end,
                "departure": self.departure,
            },
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
