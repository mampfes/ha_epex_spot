from datetime import datetime, timedelta
from typing import List

from .const import CT_PER_KWH


class Marketprice:
    """Marketprice class"""

    def __init__(
        self, start_time: datetime, duration: int, price: float, unit: str = CT_PER_KWH
    ):
        self._start_time = start_time
        self._end_time = self._start_time + timedelta(minutes=duration)
        self._price_per_kwh = price
        self._unit = unit

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_per_kwh} {self._unit})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    def set_end_time(self, end_time):
        self._end_time = end_time

    @property
    def price_per_kwh(self):
        return self._price_per_kwh


def compress_marketdata(data: List[Marketprice], duration: int) -> List[Marketprice]:
    entries: List[Marketprice] = []
    start: Marketprice = None
    for entry in data:
        if start is None:
            start = entry
            continue
        is_price_equal = start.price_per_kwh == entry.price_per_kwh
        is_continuation = start.end_time == entry.start_time
        max_start_time = start.start_time + timedelta(minutes=duration)
        is_same_interval = entry.start_time < max_start_time

        if is_price_equal & is_continuation & is_same_interval:
            start.set_end_time(entry.end_time)
        else:
            entries.append(start)
            start = entry
    if start is not None:
        entries.append(start)
    return entries
