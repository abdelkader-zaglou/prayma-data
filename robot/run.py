"""Entry point used by GitHub Actions:  python -m robot.run

Normal run: downloads the Habous month files (current month, and next month from the 20th) and the
official Hijri month starts, validates them, writes signed files. `--demo` publishes CALCULATED
times marked kind=estimate instead (used before the Habous reader existed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from . import build, cities, validate
from .fetch import fetch_hijri, fetch_month
from .morocco import calculate_month
from .parse import HabousMonth, parse_hijri, parse_month


def months_to_fetch(today: date) -> list[str]:
    cur = f"{today.year}-{today.month:02d}"
    if today.day < 20:
        return [cur]
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return [cur, f"{y}-{m:02d}"]


HIJRI_KEEP = 6  # the last six official month starts are enough for the app


def official_month(hm: HabousMonth, year: int, month: int, city_list: list) -> dict[str, list[list[str]]]:
    """Our cities' days from a Habous month. Each city reads its Habous table (habous_id)."""
    if (hm.year, hm.month) != (year, month):
        raise RuntimeError(f"asked {year}-{month:02d}, Habous sent {hm.year}-{hm.month:02d}")
    per_city = {}
    for c in city_list:
        if not c.habous_id or int(c.habous_id) not in hm.cities:
            raise RuntimeError(f"{c.id}: Habous city {c.habous_id!r} not in the file")
        per_city[c.id] = hm.cities[int(c.habous_id)]
    return per_city


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    ap.add_argument("--demo", action="store_true", help="publish calculated times (kind=estimate)")
    args = ap.parse_args()

    key = os.environ.get("PRAYMA_SIGNING_KEY", "").encode()
    if not key:
        print("PRAYMA_SIGNING_KEY is missing", file=sys.stderr)
        return 2

    site = Path(args.site)
    city_list = cities.load()
    old = site / "manifest.json"
    prev_count = 0
    if old.exists():
        months = json.loads(old.read_text("utf-8")).get("months", [])
        if months:
            p = site / months[-1]["path"]
            if p.exists():
                prev_count = len(json.loads(p.read_text("utf-8"))["cities"])

    out, kinds, hijri = {}, {}, []
    if not args.demo:
        hijri = parse_hijri(fetch_hijri())[-HIJRI_KEEP:]
    for i, month in enumerate(months_to_fetch(date.today())):
        y, m = map(int, month.split("-"))
        if args.demo:
            per_city = {c.id: [d.times for d in calculate_month(c.lat, c.lon, y, m)] for c in city_list}
        else:
            raw = fetch_month(y, m)
            if raw is None:
                if i == 0:
                    raise RuntimeError(f"Habous has not published the current month {month}")
                print(f"{month}: not published yet")
                continue
            per_city = official_month(parse_month(raw), y, m, city_list)
        for c in city_list:
            validate.check_city_month(c, y, m, per_city[c.id])
        validate.check_city_count(len(per_city), prev_count)
        out[month] = build.month_file(month, per_city)
        kinds[month] = "estimate" if args.demo else "official"

    changed = build.publish(site, out, kinds, hijri=hijri, private_pem=key)
    print("changed" if changed else "no change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
