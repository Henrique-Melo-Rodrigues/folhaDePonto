"""Esquema do SQLite e migrações versionadas por `PRAGMA user_version` (RNF03).

Regra: migração publicada nunca é editada. Mudou o esquema? Acrescente uma
nova entrada no fim de MIGRACOES.
"""

from __future__ import annotations

import sqlite3

MIGRACOES: tuple[str, ...] = (
    # 1 — esquema inicial da v2
    """
    CREATE TABLE lancamentos (
        data          TEXT PRIMARY KEY,          -- AAAA-MM-DD (RN04: um por data)
        tipo          TEXT NOT NULL,
        entrada       TEXT,                      -- HH:MM
        saida_almoco  TEXT,
        volta_almoco  TEXT,
        saida         TEXT,
        entrada_extra TEXT,
        saida_extra   TEXT,
        observacao    TEXT NOT NULL DEFAULT '',
        criado_em     TEXT NOT NULL,             -- ISO 8601 com fuso
        atualizado_em TEXT NOT NULL
    );

    -- Datas do calendário (UC06, UC10). Uma data pode ter mais de uma origem.
    CREATE TABLE datas_especiais (
        data      TEXT NOT NULL,
        nome      TEXT NOT NULL,
        natureza  TEXT NOT NULL,                 -- feriado | facultativo | emenda | emenda_sugerida
        origem    TEXT NOT NULL,                 -- ver Origem em repositorio.py
        recorrente INTEGER NOT NULL DEFAULT 0,   -- datas manuais que repetem todo ano (MM-DD)
        oculta    INTEGER NOT NULL DEFAULT 0,    -- datas da lib não são apagadas, só ocultadas
        fonte     TEXT NOT NULL DEFAULT '',      -- ex.: "holidays 0.108" (RN09)
        PRIMARY KEY (data, nome)
    );
    CREATE INDEX datas_especiais_por_origem ON datas_especiais (origem, data);

    CREATE TABLE preferencias (
        chave TEXT PRIMARY KEY,
        valor TEXT NOT NULL                      -- JSON
    );
    """,
)

VERSAO_ATUAL = len(MIGRACOES)


class BancoMaisNovoQueOApp(RuntimeError):
    """O arquivo foi gravado por uma versão mais nova do app (ex.: backup restaurado)."""


def migrar(conexao: sqlite3.Connection) -> int:
    """Leva o banco até VERSAO_ATUAL. Cada migração roda numa transação própria."""
    versao = conexao.execute("PRAGMA user_version").fetchone()[0]
    if versao > VERSAO_ATUAL:
        raise BancoMaisNovoQueOApp(
            f"O banco está na versão {versao}, mas este app conhece até a {VERSAO_ATUAL}. Atualize o app."
        )
    for numero in range(versao + 1, VERSAO_ATUAL + 1):
        script = MIGRACOES[numero - 1]
        # executescript faz COMMIT implícito antes; BEGIN/COMMIT explícitos tornam a migração atômica.
        conexao.executescript(f"BEGIN;\n{script}\nPRAGMA user_version = {numero};\nCOMMIT;")
    return VERSAO_ATUAL
