import logging
from datetime import datetime, time, timedelta

import homeassistant.util.dt as dt_util

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
            mp.price_per_kwh
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        start_time = mp.end_time

    return round(total_price, 6)


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


def find_extreme_price_interval(marketdata, start_times, duration: timedelta, cmp):
    """Find the lowest/highest price for all given start times.

        The argument cmp is a lambda which is used to differentiate between
    lowest and highest price.
    """
    interval_price: float | None = None
    interval_start_time: timedelta | None = None

    for start_time in start_times:
        ip = _calc_interval_price(marketdata, start_time, duration)

        if ip is None:
            return None

        if interval_price is None or cmp(ip, interval_price):
            interval_price = ip
            interval_start_time = start_time

    if interval_start_time is None:
        return None

    interval_price = round(interval_price, 6)

    return {
        "start": dt_util.as_local(interval_start_time),
        "end": dt_util.as_local(interval_start_time + duration),
        "interval_price": interval_price,
        "price_per_hour": round(
            interval_price * SECONDS_PER_HOUR / duration.total_seconds(), 6
        ),
    }


def get_start_times(
    marketdata,
    earliest_start_time: time,
    earliest_start_post: int,
    latest_end_time: time,
    latest_end_post: int,
    latest_market_datetime: datetime,
    duration: timedelta,
):
    # first calculate start and end datetime
    now = dt_util.now()

    earliest_start: datetime = (
        now
        if earliest_start_time is None
        else now.replace(
            hour=earliest_start_time.hour,
            minute=earliest_start_time.minute,
            second=earliest_start_time.second,
            microsecond=earliest_start_time.microsecond,
        )
    )
    if earliest_start_post is not None:
        earliest_start += timedelta(days=earliest_start_post)

    if latest_end_time is None:
        latest_end = latest_market_datetime
    else:
        latest_end: datetime = now.replace(
            hour=latest_end_time.hour,
            minute=latest_end_time.minute,
            second=latest_end_time.second,
            microsecond=latest_end_time.microsecond,
        )

        if latest_end_post is not None:
            latest_end += timedelta(days=latest_end_post)
        elif latest_end <= earliest_start:
            latest_end += timedelta(days=1)

        if latest_end > latest_market_datetime:
            if latest_market_datetime <= earliest_start:
                # no data available, return immediately to avoid exception
                _LOGGER.debug(
                    f"no data available yet: earliest_start={earliest_start}, latest_end={latest_end}"  # noqa: E501
                )
                return []

            latest_end = latest_market_datetime

    if latest_end <= earliest_start:
        raise ValueError(
            f"latest_end {latest_end} is earlier or equal to earliest_start {earliest_start}"  # noqa: E501
        )

    _LOGGER.debug(
        f"extreme price service call: earliest_start={earliest_start}, latest_end={latest_end}"  # noqa: E501
    )

    return _calc_start_times(
        marketdata,
        earliest_start=dt_util.as_utc(earliest_start),
        latest_end=dt_util.as_utc(latest_end),
        duration=duration,
    )
