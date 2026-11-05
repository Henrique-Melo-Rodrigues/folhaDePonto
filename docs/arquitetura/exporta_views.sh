#!/usr/bin/env bash
# Gera o relatório HTML pelo Archi (linha de comando) e copia o PNG de cada view
# para views/, com o nome da view. Uso: docs/arquitetura/exporta_views.sh
set -euo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
unset WAYLAND_DISPLAY
export GDK_BACKEND=x11 GTK_THEME=Adwaita DISPLAY="${DISPLAY:-:0}"
"${ARCHI:-/opt/archi/Archi}" -application com.archimatetool.commandline.app -consoleLog -nosplash \
  --loadModel folha-de-ponto.archimate --html.createReport "$TMP" >/dev/null 2>&1
rm -rf views && mkdir views
python3 -I - "$TMP" <<'PY'
import re, shutil, sys, unicodedata, xml.etree.ElementTree as ET
from pathlib import Path
tmp = Path(sys.argv[1])
T = '{http://www.w3.org/2001/XMLSchema-instance}type'
root = ET.parse('folha-de-ponto.archimate').getroot()
def walk(node, path):
    for f in node.findall('folder'):
        yield from walk(f, path + [f.get('name')])
    for e in node.findall('element'):
        if e.get(T) == 'archimate:ArchimateDiagramModel':
            yield e.get('id'), path, e.get('name')
diagrams = next(f for f in root.findall('folder') if f.get('type') == 'diagrams')
for vid, path, name in walk(diagrams, []):
    png = next(tmp.glob(f'*/images/{vid}.png'))
    prefix = path[0].split(' ')[0] if path else 'visao-geral'
    slug = unicodedata.normalize('NFKD', f'{prefix} {name}').encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^A-Za-z0-9]+', '-', slug).strip('-').lower()
    shutil.copy(png, f'views/{slug}.png')
    print(f'views/{slug}.png')
PY
