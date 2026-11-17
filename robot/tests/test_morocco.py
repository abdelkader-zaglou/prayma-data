from datetime import date, datetime, timezone

from robot.morocco import calculate_day, morocco_offset


def test_offset_switches_to_gmt_on_2026_09_20():
    assert morocco_offset(datetime(2026, 9, 20, 0, 59, tzinfo=timezone.utc)).total_seconds() == 3600
    assert morocco_offset(datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)).total_seconds() == 0
    assert morocco_offset(datetime(2027, 2, 20, tzinfo=timezone.utc)).total_seconds() == 0  # no Ramadan change


def test_casablanca_14_nov_2026():
    # Casablanca, 14 Nov 2026.
    assert calculate_day(33.5731, -7.5898, date(2026, 11, 14)).times == \
        ["05:30", "06:58", "12:20", "15:07", "17:33", "18:49"]


def test_matches_published_morocco_method_el_hajeb():
    # Bladi.net (Morocco/Habous method), El Hajeb, 11 Oct 2026: Fajr 04:56, Dhuhr 12:13, Asr 15:24,
    # Maghrib 17:58, Isha 19:11. Allow 1 minute for rounding.
    t = calculate_day(33.6879, -5.3710, date(2026, 10, 11)).times
    expected = {0: "04:56", 2: "12:13", 3: "15:24", 4: "17:58", 5: "19:11"}
    for i, e in expected.items():
        a = int(t[i][:2]) * 60 + int(t[i][3:])
        b = int(e[:2]) * 60 + int(e[3:])
        assert abs(a - b) <= 1, (i, t[i], e)
