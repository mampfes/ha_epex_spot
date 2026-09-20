from datetime import datetime, timedelta, timezone

from custom_components.epex_spot.common import Marketprice
from custom_components.epex_spot.extreme_price_interval import (
    _calc_interval_price,
    _calc_start_times,
    find_extreme_price_interval,
)


def test_calc_start_times_includes_each_market_segment_start():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    marketdata = [
        Marketprice(start, 120, 0.10),
        Marketprice(start + timedelta(hours=2), 120, 0.20),
    ]

    assert _calc_start_times(
        marketdata,
        start,
        start + timedelta(hours=4),
        timedelta(hours=1),
    ) == [
        start,
        start + timedelta(hours=1),
        start + timedelta(hours=2),
        start + timedelta(hours=3),
    ]


def test_calc_interval_price_returns_none_for_missing_market_data():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    marketdata = [
        Marketprice(start, 60, 0.10),
        Marketprice(start + timedelta(hours=2), 60, 0.20),
    ]

    assert _calc_interval_price(marketdata, start, timedelta(hours=2)) is None


def test_find_extreme_price_interval_skips_missing_candidate():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    marketdata = [
        Marketprice(start, 60, 0.10),
        Marketprice(start + timedelta(hours=2), 60, 0.20),
    ]

    result = find_extreme_price_interval(
        marketdata,
        [start, start + timedelta(hours=1), start + timedelta(hours=2)],
        timedelta(hours=1),
        lambda left, right: left < right,
    )

    assert result["start"] == start
    assert result["market_price_per_hour"] == 0.1
