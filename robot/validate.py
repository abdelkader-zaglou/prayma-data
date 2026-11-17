"""Safety checks before anything is published. All must pass."""
from __future__ import annotations

import re
from calendar import monthrange

from .cities import City
from .morocco import calculate_month

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
MAX_DIFF_FROM_CALC = 15   # minutes
MAX_DAY_TO_DAY = 3        # minutes
MIN_CITY_SHARE = 0.9      # of the previous run


class ValidationError(Exception):
    pass


def _m(t: str) -> int:
    return int(t[:2]) * 60 + int(t[3:])


def check_city_month(city: City, year: int, month: int, days: list[list[str]]) -> None:
    n = monthrange(year, month)[1]
    where = f"{city.id} {year}-{month:02d}"
    if len(days) != n:
        raise ValidationError(f"{where}: {len(days)} days, expected {n}")
    calc = calculate_month(city.lat, city.lon, year, month)
    for i, day in enumerate(days):
        if len(day) != 6:
            raise ValidationError(f"{where} day {i+1}: {len(day)} times, expected 6")
        for t in day:
            if not HHMM.match(t):
                raise ValidationError(f"{where} day {i+1}: bad time {t!r}")
        mins = [_m(t) for t in day]
        if mins != sorted(mins) or len(set(mins)) != 6:
            raise ValidationError(f"{where} day {i+1}: times not in order {day}")
        for k, (a, b) in enumerate(zip(mins, (_m(t) for t in calc[i].times))):
            if abs(a - b) > MAX_DIFF_FROM_CALC:
                raise ValidationError(f"{where} day {i+1} prayer {k}: {day[k]} vs calculated {calc[i].times[k]}")
        if i > 0:
            prev = [_m(t) for t in days[i - 1]]
            for k in range(6):
                if abs(mins[k] - prev[k]) > MAX_DAY_TO_DAY:
                    raise ValidationError(f"{where} day {i+1} prayer {k}: jump {prev[k]}->{mins[k]} min")


def check_city_count(new_count: int, previous_count: int) -> None:
    if previous_count and new_count < MIN_CITY_SHARE * previous_count:
        raise ValidationError(f"only {new_count} cities, previous run had {previous_count}")
