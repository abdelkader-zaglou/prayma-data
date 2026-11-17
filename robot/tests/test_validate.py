import pytest

from robot.cities import load
from robot.morocco import calculate_month
from robot.validate import ValidationError, check_city_count, check_city_month

CASA = next(c for c in load() if c.id == "casablanca")


def month():
    return [d.times[:] for d in calculate_month(CASA.lat, CASA.lon, 2026, 11)]


def test_calculated_month_passes():
    check_city_month(CASA, 2026, 11, month())


@pytest.mark.parametrize("mutate", [
    lambda d: d.pop(),                                   # missing day
    lambda d: d[3].pop(),                                # missing time
    lambda d: d[3].__setitem__(0, "5:30"),               # bad format
    lambda d: d[3].__setitem__(1, "04:00"),              # out of order
    lambda d: d[3].__setitem__(5, "20:30"),              # far from calculation
])
def test_bad_data_is_rejected(mutate):
    d = month()
    mutate(d)
    with pytest.raises(ValidationError):
        check_city_month(CASA, 2026, 11, d)


def test_city_count_drop_is_rejected():
    with pytest.raises(ValidationError):
        check_city_count(10, 33)
    check_city_count(33, 33)
