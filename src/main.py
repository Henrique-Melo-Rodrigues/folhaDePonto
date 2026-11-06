"""Ponto de entrada do APK (`flet build apk` procura `main.py` em tool.flet.app.path).

No PC, use `uv run folha-ponto`.
"""

import flet as ft

from folha_ponto.ui.app import main

ft.run(main)
