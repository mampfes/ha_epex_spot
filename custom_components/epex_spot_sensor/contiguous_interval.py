import logging
from datetime import datetime, timedelta


_LOGGER = logging.getLogger(__name__)

SECONDS_PER_HOUR = 60 * 60


def _find_market_price(marketdata, dt: datetime):
    for mp in marketdata:
        if dt >= mp.start_time and dt < mp.end_time:
            return mp

    return None


def _calc_interval_price(marketdata, start_time: datetime, duration: timedelta):
    """Calculate price for given start time and duration."""
    total_price = 0
    stop_time = start_time + duration

    while start_time < stop_time:
        mp = _find_market_price(marketdata, start_time)

        if mp.end_time > stop_time:
            active_duration_in_this_segment = stop_time - start_time
        else:
            active_duration_in_this_segment = mp.end_time - start_time

        total_price += (
            mp.price_eur_per_mwh
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        start_time = mp.end_time

    return total_price


def _calc_start_times(
    marketdata, earliest_start: datetime, latest_end: datetime, duration: timedelta
):
    """Calculate list of meaningful start times."""
    start_times = set()
    start_time = earliest_start

    # add earliest possible start (if duration matches)
    if earliest_start + duration <= latest_end:
        start_times.add(earliest_start)

    for md in marketdata:
        # add start times for market data segment start
        if md.start_time >= earliest_start and md.start_time + duration <= latest_end:
            start_times.add(earliest_start)

        # add start times for market data segment end
        start_time = md.end_time - duration
        if md.end_time <= latest_end and earliest_start <= start_time:
            start_times.add(start_time)

    # add latest possible start (if duration matches)
    start_time = latest_end - duration
    if earliest_start <= start_time:
        start_times.add(start_time)

    return sorted(start_times)


def _find_extreme_price_interval(
    marketdata, start_times, duration: timedelta, most_expensive: bool = False
):
    """Find the lowest/highest price for all given start times.

        The argument cmp is a lambda which is used to differentiate between
    lowest and highest price.
    """
    interval_price: float | None = None
    interval_start_time: timedelta | None = None

    if most_expensive:

        def cmp(a, b):
            return a > b

    else:

        def cmp(a, b):
            return a < b

    for start_time in start_times:
        ip = _calc_interval_price(marketdata, start_time, duration)

        if ip is None:
            return None

        if interval_price is None or cmp(ip, interval_price):
            interval_price = ip
            interval_start_time = start_time

    if interval_start_time is None:
        return None

    return {
        "start": interval_start_time,
        "end": interval_start_time + duration,
        "interval_price": interval_price,
        "price_per_hour": interval_price * SECONDS_PER_HOUR / duration.total_seconds(),
    }


def calc_interval_for_contiguous(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = True,
):
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    start_times = _calc_start_times(
        marketdata,
        earliest_start=earliest_start,
        latest_end=latest_end,
        duration=duration,
    )

    return _find_extreme_price_interval(
        marketdata, start_times, duration, most_expensive
    )
