from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    def has_permission(self, request, view) -> bool:
        key = request.headers.get("X-Api-Key", "")
        return bool(key and key == settings.API_KEY)
