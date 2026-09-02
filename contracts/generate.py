#!/usr/bin/env python3
"""Gera o vocabulario de dominio da folha de ponto para backend, web e mobile.

Fonte unica: contracts/time_record.json. Cada alvo recebe apenas o que aquela
ponta consome -- o backend nao usa labels, o web nao calcula status.

Uso:
    python3 contracts/generate.py           # (re)escreve os alvos
    python3 contracts/generate.py --check   # falha se algum alvo estiver fora de sincronia
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONTRACTS_DIR = Path(__file__).resolve().parent
ROOT = CONTRACTS_DIR.parent
CONTRACT_FILE = CONTRACTS_DIR / "time_record.json"

HEADER = (
    "GERADO por contracts/generate.py a partir de contracts/time_record.json. "
    "Nao edite a mao."
)

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# --- helpers de leitura do contrato -----------------------------------------


def keys(entries: list[dict]) -> list[str]:
    return [entry["key"] for entry in entries]


def labels(entries: list[dict], field: str = "label") -> dict[str, str]:
    return {entry["key"]: entry[field] for entry in entries}


# --- helpers de renderizacao -------------------------------------------------


def quoted(value: str) -> str:
    """Literal de string valido em Python, TypeScript e Dart-com-aspas-duplas."""
    return json.dumps(value, ensure_ascii=False)


def pascal_case(key: str) -> str:
    return "".join(part.capitalize() for part in key.split("_"))


def dart_quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'").replace("$", "\\$")
    return f"'{escaped}'"


def block(opening: str, items: list[str], closing: str, indent: str = "    ") -> str:
    body = "".join(f"{indent}{item},\n" for item in items)
    return f"{opening}\n{body}{closing}"


# --- alvo: backend (Python) --------------------------------------------------


def render_python(contract: dict) -> str:
    day_types = contract["day_types"]
    not_worked = [entry["key"] for entry in day_types if not entry["worked"]]

    def tuple_of(name: str, values: list[str]) -> str:
        return block(f"{name} = (", [quoted(value) for value in values], ")")

    parts = [
        f'"""{HEADER}"""',
        "",
        "from __future__ import annotations",
        "",
        tuple_of("DAY_TYPES", keys(day_types)),
        "",
        block(
            "NOT_WORKED_DAY_TYPES = frozenset({",
            [quoted(value) for value in not_worked],
            "})",
        ),
        "",
        tuple_of("STATUSES", keys(contract["statuses"])),
        "",
        tuple_of("TIME_FIELDS", keys(contract["time_fields"])),
        "",
        f'TIME_PATTERN = r"{contract["time_pattern"]}"',
    ]
    return "\n".join(parts) + "\n"


# --- alvo: web (TypeScript) --------------------------------------------------


def render_typescript(contract: dict) -> str:
    day_types = contract["day_types"]

    def const_list(name: str, values: list[str]) -> str:
        return block(f"export const {name} = [", [quoted(value) for value in values], "] as const;", "  ")

    def record(name: str, key_type: str, mapping: dict[str, str]) -> str:
        entries = [
            f"{key if IDENTIFIER_RE.match(key) else quoted(key)}: {quoted(label)}"
            for key, label in mapping.items()
        ]
        return block(f"export const {name}: Record<{key_type}, string> = {{", entries, "};", "  ")

    parts = [
        f"// {HEADER}",
        "",
        const_list("DAY_TYPES", keys(day_types)),
        "",
        "export type DayType = (typeof DAY_TYPES)[number];",
        "",
        record("DAY_TYPE_LABELS", "DayType", labels(day_types)),
        "",
        record("DAY_TYPE_SHORT_LABELS", "DayType", labels(day_types, "short_label")),
        "",
        const_list("STATUSES", keys(contract["statuses"])),
        "",
        "export type RecordStatus = (typeof STATUSES)[number];",
        "",
        record("STATUS_LABELS", "RecordStatus", labels(contract["statuses"])),
        "",
        const_list("TIME_FIELDS", keys(contract["time_fields"])),
        "",
        "export type TimeField = (typeof TIME_FIELDS)[number];",
        "",
        record("TIME_FIELD_LABELS", "TimeField", labels(contract["time_fields"])),
    ]
    return "\n".join(parts) + "\n"


# --- alvo: mobile (Dart) -----------------------------------------------------


def render_dart(contract: dict) -> str:
    day_types = contract["day_types"]
    not_worked = [entry["key"] for entry in day_types if not entry["worked"]]

    def const_list(name: str, values: list[str]) -> str:
        return block(f"const {name} = <String>[", [dart_quoted(value) for value in values], "];", "  ")

    def const_set(name: str, values: list[str]) -> str:
        return block(f"const {name} = <String>{{", [dart_quoted(value) for value in values], "};", "  ")

    def const_map(name: str, mapping: dict[str, str]) -> str:
        entries = [f"{dart_quoted(key)}: {dart_quoted(label)}" for key, label in mapping.items()]
        return block(f"const {name} = <String, String>{{", entries, "};", "  ")

    parts = [
        f"// {HEADER}",
        "",
        const_list("dayTypes", keys(day_types)),
        "",
        const_map("dayTypeLabels", labels(day_types)),
        "",
        const_map("dayTypeShortLabels", labels(day_types, "short_label")),
        "",
        const_set("notWorkedDayTypes", not_worked),
        "",
        const_list("statuses", keys(contract["statuses"])),
        "",
        "\n".join(
            f"const status{pascal_case(key)} = {dart_quoted(key)};"
            for key in keys(contract["statuses"])
        ),
        "",
        const_map("statusLabels", labels(contract["statuses"])),
        "",
        const_list("timeFields", keys(contract["time_fields"])),
        "",
        const_map("timeFieldLabels", labels(contract["time_fields"])),
        "",
        f"const timePattern = r'{contract['time_pattern']}';",
    ]
    return "\n".join(parts) + "\n"


TARGETS = {
    Path("src/backend/apps/time_records/domain_generated.py"): render_python,
    Path("src/web/src/domain.generated.ts"): render_typescript,
    Path("src/mobile/lib/domain/domain.g.dart"): render_dart,
}


def main(argv: list[str]) -> int:
    check_only = "--check" in argv[1:]
    contract = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))

    drifted: list[str] = []
    for relative_path, render in TARGETS.items():
        target = ROOT / relative_path
        expected = render(contract)
        current = target.read_text(encoding="utf-8") if target.exists() else None

        if current == expected:
            continue

        if check_only:
            drifted.append(str(relative_path))
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected, encoding="utf-8")
        print(f"escrito: {relative_path}")

    if drifted:
        print("Fora de sincronia com contracts/time_record.json:", file=sys.stderr)
        for path in drifted:
            print(f"  - {path}", file=sys.stderr)
        print("Rode: python3 contracts/generate.py", file=sys.stderr)
        return 1

    print("ok: alvos em sincronia com o contrato." if check_only else "ok: alvos gerados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
