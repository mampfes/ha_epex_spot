from datetime import datetime, timedelta


SECONDS_PER_HOUR = 60 * 60


class Interval:
    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        price_eur_per_mwh: float,
        rank: int,
    ):
        self._start_time = start_time
        self._end_time = end_time
        self._price_eur_per_mwh = price_eur_per_mwh
        self._rank = rank

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_eur_per_mwh(self):
        return self._price_eur_per_mwh

    @property
    def rank(self):
        return self._rank

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_eur_per_mwh}, rank: {self._rank})"  # noqa: E501


def calc_intervals_for_intermittent(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = False,
):
    """Calculate price for given start time and duration."""
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    # filter intervals which fit to start- and end-time (including overlapping)
    marketdata = [
        e
        for e in marketdata
        if earliest_start < e.end_time and latest_end > e.start_time
    ]

    # sort by price
    marketdata.sort(key=lambda e: e.price_eur_per_mwh, reverse=most_expensive)

    active_time: timedelta = timedelta(seconds=0)
    intervals = []

    for count, mp in enumerate(marketdata):
        interval_start_time = (
            earliest_start if mp.start_time < earliest_start else mp.start_time
        )
        interval_end_time = latest_end if mp.end_time > latest_end else mp.end_time

        active_duration_in_this_segment = interval_end_time - interval_start_time

        if active_time + active_duration_in_this_segment > duration:
            # we don't need the full active_duration_in_this_segment
            active_duration_in_this_segment = duration - active_time

        price = (
            mp.price_eur_per_mwh
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        intervals.append(
            Interval(
                start_time=interval_start_time,
                end_time=interval_start_time + active_duration_in_this_segment,
                price_eur_per_mwh=price,
                rank=count,
            )
        )

        active_time += active_duration_in_this_segment

        if active_time == duration:
            break

    return intervals


def is_now_in_intervals(now: datetime, intervals):
    for e in intervals:
        if now >= e.start_time and now < e.end_time:
            return True

    return False
