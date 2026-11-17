"""City list loader (robot/cities.csv)."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

CSV = Path(__file__).with_name("cities.csv")


@dataclass(frozen=True)
class City:
    id: str
    habous_id: str
    name_ar: str
    name_fr: str
    region_ar: str
    region_fr: str
    lat: float
    lon: float


def load(path: Path = CSV) -> list[City]:
    with path.open(encoding="utf-8") as f:
        return [City(r["id"], r["habous_id"], r["name_ar"], r["name_fr"], r["region_ar"], r["region_fr"],
                     float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)]
