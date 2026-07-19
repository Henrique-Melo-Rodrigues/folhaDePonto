from django.test import TestCase

from apps.time_records.repositories import TimeRecordRepository


def make_document(**overrides) -> dict:
    document = {
        "user_id": "usuario_teste",
        "date": "2026-05-27",
        "day_type": "trabalho",
        "times": {
            "arrival": "07:45",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "departure": "14:45",
        },
        "notes": "",
        "status": "complete",
        "created_at": "2026-05-27T10:00:00-03:00",
        "updated_at": "2026-05-27T10:00:00-03:00",
    }
    document.update(overrides)
    return document


class TimeRecordRepositoryTests(TestCase):
    def setUp(self):
        self.repository = TimeRecordRepository()

    def test_upsert_and_get_by_date_roundtrip(self):
        document = make_document()
        self.repository.upsert(document)

        stored = self.repository.get_by_date("usuario_teste", "2026-05-27")

        self.assertEqual(stored, document)

    def test_get_by_date_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_date("usuario_teste", "2026-05-27"))

    def test_upsert_replaces_existing_record(self):
        self.repository.upsert(make_document())
        self.repository.upsert(make_document(day_type="folga", status="not_worked"))

        stored = self.repository.get_by_date("usuario_teste", "2026-05-27")

        self.assertEqual(stored["day_type"], "folga")
        self.assertEqual(stored["status"], "not_worked")

    def test_list_month_filters_and_sorts(self):
        self.repository.upsert(make_document(date="2026-05-28"))
        self.repository.upsert(make_document(date="2026-05-02"))
        self.repository.upsert(make_document(date="2026-06-01"))
        self.repository.upsert(make_document(date="2026-05-10", user_id="outro_usuario"))

        records = self.repository.list_month("usuario_teste", 2026, 5)

        self.assertEqual([record["date"] for record in records], ["2026-05-02", "2026-05-28"])

    def test_delete(self):
        self.repository.upsert(make_document())

        self.assertTrue(self.repository.delete("usuario_teste", "2026-05-27"))
        self.assertFalse(self.repository.delete("usuario_teste", "2026-05-27"))
