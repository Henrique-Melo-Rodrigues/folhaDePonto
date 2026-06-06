from django.test import SimpleTestCase

from apps.time_records.serializers import TimeRecordInputSerializer


class TimeRecordInputSerializerTests(SimpleTestCase):
    def test_accepts_valid_work_record(self):
        serializer = TimeRecordInputSerializer(
            data={
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

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["date"], "2026-05-27")
        self.assertEqual(serializer.validated_data["times"]["arrival"], "07:45")

    def test_rejects_invalid_day_type(self):
        serializer = TimeRecordInputSerializer(
            data={"date": "2026-05-27", "day_type": "plantao", "times": {}}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("day_type", serializer.errors)

    def test_rejects_invalid_time(self):
        serializer = TimeRecordInputSerializer(
            data={
                "date": "2026-05-27",
                "day_type": "trabalho",
                "times": {"arrival": "25:00"},
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("times", serializer.errors)

