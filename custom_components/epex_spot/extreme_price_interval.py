from datetime import datetime, time, timedelta

import homeassistant.util.dt as dt_util

SECONDS_PER_HOUR = 60 * 60


def _calc_interval_price(price_map, start_time: datetime, duration: timedelta):
    """Calculate price for given start time and duration."""
    total_price = 0
    stop_time = start_time + duration

    while start_time < stop_time:
        start_of_current_h = start_time.replace(minute=0, second=0, microsecond=0)

        start_of_next_h = start_of_current_h + timedelta(hours=1)

        if start_of_next_h > stop_time:
            active_duration_in_this_h = stop_time - start_time
        else:
            active_duration_in_this_h = start_of_next_h - start_time

        if start_of_current_h not in price_map:
            return None

        price = price_map[start_of_current_h]

        total_price += (
            price * active_duration_in_this_h.total_seconds() / SECONDS_PER_HOUR
        )

        start_time = start_of_next_h

    return total_price


def _calc_start_times(
    earliest_start: datetime, latest_end: datetime, duration: timedelta
):
    """Calculate list of meaningful start times."""
    start_times = set()
    start_time = earliest_start

    # add start times which are aligned by full hour start
    while start_time + duration <= latest_end:
        start_times.add(start_time)

        start_of_current_h = start_time.replace(minute=0, second=0, microsecond=0)
        start_of_next_h = start_of_current_h + timedelta(hours=1)
        start_time = start_of_next_h

    # add start time which are aligned by full hour end
    end_time = latest_end.replace(minute=0, second=0, microsecond=0)
    while earliest_start < end_time - duration:
        start_times.add(end_time - duration)
        end_time = end_time - timedelta(hours=1)

    # add latest possible start (if duration matches)
    start_time = latest_end - duration
    if earliest_start < start_time:
        start_times.add(start_time)

    return sorted(start_times)


def find_extreme_price_interval(price_map, start_times, duration: timedelta, cmp):
    """Find the lowest/highest price for all given start times.

        The argument cmp is a lambda which is used to differentiate between
    lowest and highest price.
    """
    interval_price: float | None = None
    interval_start_time: timedelta | None = None

    for start_time in start_times:
        ip = _calc_interval_price(price_map, start_time, duration)

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
        "price": interval_price,
    }


def get_start_times(
    earliest_start_time: time,
    latest_end_time: time,
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

    latest_end: datetime = (
        latest_market_datetime
        if latest_end_time is None
        else earliest_start.replace(
            hour=latest_end_time.hour,
            minute=latest_end_time.minute,
            second=latest_end_time.second,
            microsecond=latest_end_time.microsecond,
        )
    )

    if latest_end_time is not None and latest_end <= earliest_start:
        latest_end += timedelta(days=1)

    print(f"{earliest_start} - {latest_end}")
    return _calc_start_times(
        earliest_start=dt_util.as_utc(earliest_start),
        latest_end=dt_util.as_utc(latest_end),
        duration=duration,
    )
