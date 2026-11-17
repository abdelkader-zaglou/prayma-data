"""Read the Habous month and Hijri files."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

EXPECTED_COLS = ["Fajr", "Chorouq", "Dhuhr", "Asr", "Maghrib", "Ishae"]
WRAPPER = re.compile(r"^\s*\(window\.HORAIRES_MOIS=window\.HORAIRES_MOIS\|\|\[\]\)\.push\((.*)\);?\s*$", re.S)
HIJRI_ENTRY = re.compile(
    r"\{\s*debut:\s*'(\d{4}-\d{2}-\d{2})'\s*,\s*mois:\s*(\d{1,2})\s*,\s*annee:\s*(\d{4})\s*,\s*duree:\s*(\d+|null)\s*\}"
)


class ParseError(Exception):
    """The file does not have the shape we know."""


@dataclass(frozen=True)
class HabousMonth:
    year: int
    month: int
    timezone: str
    cities: dict[int, list[list[str]]]
    names: dict[int, str]


def parse_month(raw: str) -> HabousMonth:
    m = WRAPPER.match(raw)
    if not m:
        raise ParseError("unknown wrapper: Habous changed the file format")
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ParseError(f"bad JSON: {e}") from e
    if data.get("cols") != EXPECTED_COLS:
        raise ParseError(f"unexpected columns {data.get('cols')}")
    if data.get("fuseau") != "GMT":
        raise ParseError(f"unexpected time zone {data.get('fuseau')}")
    cities, names = {}, {}
    for v in data["villes"]:
        cities[int(v["c"])] = [list(day) for day in v["h"]]
        names[int(v["c"])] = v["n"]
    return HabousMonth(int(data["annee"]), int(data["mois"]), data["fuseau"], cities, names)


def parse_hijri(raw: str) -> list[dict]:
    """Official month starts for the manifest: [{"y": 1448, "m": 6, "start": "2026-11-11", "official": true}]."""
    entries = [{"y": int(y), "m": int(mo), "start": start, "official": True} for start, mo, y, _ in HIJRI_ENTRY.findall(raw)]
    if not entries:
        raise ParseError("no Hijri month found")
    return sorted(entries, key=lambda e: e["start"])
