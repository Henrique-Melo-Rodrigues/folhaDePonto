from __future__ import annotations

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views import View


class FrontendView(View):
    """Serve o index.html do build do Vite para qualquer rota que não seja da API."""

    def get(self, request, *args, **kwargs):
        index_file = settings.FRONTEND_DIST / "index.html"
        if not index_file.exists():
            return HttpResponse(
                "Frontend não encontrado. Rode `npm run build` em src/web.",
                status=503,
                content_type="text/plain; charset=utf-8",
            )
        return FileResponse(index_file.open("rb"), content_type="text/html")
