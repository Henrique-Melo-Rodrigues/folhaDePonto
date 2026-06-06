from django.test import SimpleTestCase, override_settings

from apps.time_records.services import TimeRecordService


class FakeRepository:
    def __init__(self):
        self.documents = {}

    def get_by_date(self, user_id, record_date):
        return self.documents.get((user_id, record_date))

    def list_month(self, user_id, year, month):
        prefix = f"{year:04d}-{month:02d}-"
        return [
            document
            for (_, record_date), document in sorted(self.documents.items())
            if record_date.startswith(prefix)
        ]

    def upsert(self, document):
        self.documents[(document["user_id"], document["date"])] = document
        return document

    def delete(self, user_id, record_date):
        return self.documents.pop((user_id, record_date), None) is not None


@override_settings(FIXED_USER_ID="usuario_teste")
class TimeRecordServiceTests(SimpleTestCase):
    def setUp(self):
        self.repository = FakeRepository()
        self.service = TimeRecordService(self.repository)

    def test_marks_full_work_day_as_complete(self):
        record = self.service.save_record(
            {
                "date": "2026-05-27",
                "day_type": "trabalho",
                "times": {
                    "arrival": "07:45",
                    "lunch_start": "12:00",
                    "lunch_end": "13:00",
                    "departure": "14:45",
                },
                "notes": "Dia normal",
            }
        )

        self.assertEqual(record["user_id"], "usuario_teste")
        self.assertEqual(record["status"], "complete")

    def test_marks_non_worked_day_without_times(self):
        record = self.service.save_record(
            {
                "date": "2026-05-26",
                "day_type": "atividade_teorica",
                "times": {},
                "notes": "Atividade teorica",
            }
        )

        self.assertEqual(record["status"], "not_worked")

    def test_marks_partial_work_day_as_incomplete(self):
        record = self.service.save_record(
            {
                "date": "2026-05-28",
                "day_type": "trabalho",
                "times": {"arrival": "07:45"},
                "notes": "",
            }
        )

        self.assertEqual(record["status"], "incomplete")

    def test_preserves_created_at_when_updating(self):
        first = self.service.save_record(
            {"date": "2026-05-27", "day_type": "trabalho", "times": {}, "notes": ""}
        )
        second = self.service.save_record(
            {"date": "2026-05-27", "day_type": "folga", "times": {}, "notes": ""}
        )

        self.assertEqual(first["created_at"], second["created_at"])
        self.assertEqual(second["status"], "not_worked")

