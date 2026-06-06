from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

TEST_API_KEY = "test-api-key-123"


@override_settings(API_KEY=TEST_API_KEY)
class TimeRecordViewTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth = {"HTTP_X_API_KEY": TEST_API_KEY}

    def test_health(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "ok"})

    def test_health_does_not_require_api_key(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)

    def test_endpoint_without_api_key_returns_403(self):
        response = self.client.get("/api/time-records/today/")

        self.assertEqual(response.status_code, 403)

    def test_endpoint_with_wrong_api_key_returns_403(self):
        response = self.client.get(
            "/api/time-records/today/",
            HTTP_X_API_KEY="chave-errada",
        )

        self.assertEqual(response.status_code, 403)

    @patch("apps.time_records.views.get_time_record_service")
    def test_create_time_record(self, get_service):
        service = Mock()
        service.save_record.return_value = {
            "user_id": "usuario_001",
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
            "created_at": "2026-05-27T10:00:00+00:00",
            "updated_at": "2026-05-27T10:00:00+00:00",
        }
        get_service.return_value = service

        response = self.client.post(
            "/api/time-records/",
            {
                "date": "2026-05-27",
                "day_type": "trabalho",
                "times": {
                    "arrival": "07:45",
                    "lunch_start": "12:00",
                    "lunch_end": "13:00",
                    "departure": "14:45",
                },
                "notes": "",
            },
            format="json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "complete")

    @patch("apps.time_records.views.get_time_record_service")
    def test_list_month(self, get_service):
        service = Mock()
        service.list_month.return_value = [{"date": "2026-05-27", "status": "complete"}]
        get_service.return_value = service

        response = self.client.get(
            "/api/time-records/month/?year=2026&month=5",
            **self.auth,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["date"], "2026-05-27")
        service.list_month.assert_called_once_with(2026, 5)

    @patch("apps.time_records.views.get_time_record_service")
    def test_detail_not_found(self, get_service):
        service = Mock()
        service.get_by_date.return_value = None
        get_service.return_value = service

        response = self.client.get("/api/time-records/2026-05-27/", **self.auth)

        self.assertEqual(response.status_code, 404)

    def test_detail_invalid_date_returns_400(self):
        response = self.client.get("/api/time-records/nao-e-uma-data/", **self.auth)

        self.assertEqual(response.status_code, 400)

    def test_detail_invalid_date_format_returns_400(self):
        response = self.client.get("/api/time-records/27-05-2026/", **self.auth)

        self.assertEqual(response.status_code, 400)

    @patch("apps.time_records.views.get_time_record_service")
    def test_delete_time_record(self, get_service):
        service = Mock()
        service.delete.return_value = True
        get_service.return_value = service

        response = self.client.delete("/api/time-records/2026-05-27/", **self.auth)

        self.assertEqual(response.status_code, 204)
        service.delete.assert_called_once_with("2026-05-27")
