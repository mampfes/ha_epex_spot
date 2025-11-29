from datetime import datetime, timedelta
from typing import List

from .const import UOM_EUR_PER_KWH


class Marketprice:
    """Marketprice class"""

    def __init__(
        self,
        start_time: datetime,
        duration: int,
        price: float,
        unit: str = UOM_EUR_PER_KWH,
    ):
        self._start_time = start_time
        self._end_time = self._start_time + timedelta(minutes=duration)
        self._market_price_per_kwh = price
        self._unit = unit

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._market_price_per_kwh} {self._unit})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    def set_end_time(self, end_time):
        self._end_time = end_time

    @property
    def market_price_per_kwh(self):
        return self._market_price_per_kwh


def compress_marketdata(data: List[Marketprice], duration: int) -> List[Marketprice]:
    entries: List[Marketprice] = []
    start: Marketprice = None
    for entry in data:
        if start is None:
            start = entry
            continue
        is_price_equal = start.market_price_per_kwh == entry.market_price_per_kwh
        is_continuation = start.end_time == entry.start_time
        max_start_time = start.start_time + timedelta(minutes=duration)
        is_same_interval = entry.start_time < max_start_time

        if is_price_equal and is_continuation and is_same_interval:
            start.set_end_time(entry.end_time)
        else:
            entries.append(start)
            start = entry
    if start is not None:
        entries.append(start)
    return entries


def average_marketdata(
    data: List[Marketprice], target_duration: int
) -> List[Marketprice]:
    if not data:
        return []

    entry_duration = int((data[0]._end_time - data[0]._start_time).total_seconds() / 60)

    group_size = target_duration // entry_duration

    result: List[Marketprice] = []

    for i in range(0, len(data), group_size):
        group = data[i : i + group_size]

        avg_price = round(sum(e._market_price_per_kwh for e in group) / len(group), 5)
        start = group[0]._start_time

        result.append(
            Marketprice(start_time=start, duration=target_duration, price=avg_price)
        )

    return result
