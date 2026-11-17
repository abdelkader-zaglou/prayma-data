"""Moroccan prayer-time calculation (the fallback rule) and Morocco's legal UTC offset.

Used to sanity-check Habous data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from adhanpy.PrayerTimes import PrayerTimes
from adhanpy.calculation.CalculationParameters import CalculationParameters
from adhanpy.calculation.Madhab import Madhab
from adhanpy.calculation.PrayerAdjustments import PrayerAdjustments

ORDER = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]

# Moroccan calculation method.
FAJR_ANGLE = 19.0
ISHA_ANGLE = 17.0
ADJUST = dict(fajr=0, sunrise=-3, dhuhr=5, asr=0, maghrib=5, isha=0)

# Morocco moved to permanent UTC+0 on 2026-09-20 at 02:00 local (decree 2.26.530, tzdata 2026c).
PERMANENT_GMT_FROM = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)  # 02:00 at +01:00


def morocco_offset(at: datetime) -> timedelta:
    """Legal offset of Morocco at an instant. Only +00:00 matters from 2026-09-20 on.

    Before that date Morocco used +01:00 except during Ramadan; past dates are not needed by
    the robot, so we return +01:00 for them and do not model the Ramadan breaks.
    """
    return timedelta(0) if at >= PERMANENT_GMT_FROM else timedelta(hours=1)


def offset_string(td: timedelta) -> str:
    minutes = int(td.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"{sign}{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass(frozen=True)
class DayTimes:
    day: date
    times: list[str]  # HH:MM local wall-clock, in ORDER


def calculate_day(lat: float, lon: float, day: date) -> DayTimes:
    params = CalculationParameters(
        fajr_angle=FAJR_ANGLE,
        isha_angle=ISHA_ANGLE,
        adjustments=PrayerAdjustments(**ADJUST),
    )
    params.madhab = Madhab.SHAFI  # "standard" shadow = 1x, as used by the Maliki school
    pt = PrayerTimes((lat, lon), datetime(day.year, day.month, day.day), calculation_parameters=params,
                     time_zone=timezone.utc)
    out = []
    for name in ORDER:
        utc = getattr(pt, name)
        local = utc + morocco_offset(utc)
        out.append(local.strftime("%H:%M"))
    return DayTimes(day, out)


def calculate_month(lat: float, lon: float, year: int, month: int) -> list[DayTimes]:
    d = date(year, month, 1)
    days = []
    while d.month == month:
        days.append(calculate_day(lat, lon, d))
        d += timedelta(days=1)
    return days
