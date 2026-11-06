# CLAUDE.md: Folha de Ponto Pessoal (v2)

App de folha de ponto pessoal, **100% offline no celular**, em **Python com uv**.
O porquê está em `docs/decisions/ADR-002-app-python-offline-no-celular.md`.

## Antes de mudar algo
- Casos de uso e regras: `docs/casos-de-uso.md` (UC01–UC11, RN01–RN10, RNF01–RNF06).
- Arquitetura: `docs/arquitetura/README.md` (ArchiMate/TOGAF ADM). Mudou a arquitetura?
  Edite `docs/arquitetura/gera_modelo.py`, rode `uv run docs/arquitetura/gera_modelo.py`
  e depois `docs/arquitetura/exporta_views.sh`. Nunca edite o `.archimate` à mão.
- Roadmap: README (WP1–WP7). Trabalhe um pacote de trabalho por vez.

## Estrutura

```
src/folha_ponto/
  dominio/     regras do dia (Python puro; Core). vocabulario.py = fonte única dos termos
  calendario/  feriados (lib holidays), facultativos, emendas, datas manuais
  dados/       repositório SQLite (único módulo que fala SQL)
  exportacao/  folha do mês (texto/CSV) e backup JSON
  ui/          servicos.py (casos de uso, sem Flet) + telas/ Flet finas
tests/         pytest (tests/dados/casos_status.json = vetores golden da RN03)
```

## Comandos

```bash
uv sync
uv run pytest
uv run folha-ponto     # app no PC
uv run flet build apk   # APK (normalmente pelo CI: .github/workflows/ci.yml)
```

## Regras
- **Offline:** nada de rede no pacote (`tests/test_sem_rede.py` reprova) e o APK sem a
  permissão INTERNET (`[tool.flet.android.permission]`; `tests/test_apk.py` e o CI conferem).
- **Camadas:** a UI não fala SQL; só `dados/` usa `sqlite3`; `dominio/` não importa Flet.
- **Testes junto com a mudança:** regra nova ou bug corrigido vem com teste.
- **Linguagem ubíqua:** use os termos do glossário (marcação, lançamento, tipo do dia,
  pendência, folha, emenda) em código, testes e mensagens.
- **Domínio:** emenda = folga; ponto facultativo = folga por padrão (preferência pode
  desligar); jornada padrão 07:45–12:00 e 13:00–14:45; cidade Cubatão/SP.
- **Dados pessoais:** PDFs são ignorados pelo git (`*.[pP][dD][fF]`). Nunca copie dados
  da folha oficial (nome, CTPS, matrícula) para código, testes ou docs.
- **Git:** o Claude faz commits detalhados (o quê, por quê e como foi verificado), mas
  **nunca** roda `git push`, `git pull` ou `git fetch`. Isso é sempre com o usuário:
  pergunte a ele.
