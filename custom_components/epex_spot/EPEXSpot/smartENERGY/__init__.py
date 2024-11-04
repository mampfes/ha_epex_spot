"""smartENERGY API."""

from datetime import datetime, timedelta
import logging

import aiohttp

from ...const import CT_PER_KWH

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    """Marketprice class for smartENERGY."""

    def __init__(self, duration, data):
        self._start_time = datetime.fromisoformat(data["date"])
        self._end_time = self._start_time + timedelta(minutes=duration)
        # price includes austrian vat (20%) -> remove to be consistent with other data sources
        self._price_per_kwh = round(float(data["value"]) / 100.0 / 1.2, 6)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_per_kwh} {CT_PER_KWH})"  # noqa: E501

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


class smartENERGY:
    URL = "https://apis.smartenergy.at/market/v1/price"

    MARKET_AREAS = ("at",)

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._duration = 15  # default value, can be overwritten by API response
        self._marketdata = []

    @property
    def name(self):
        return "smartENERGY API V1"

    @property
    def market_area(self):
        return self._market_area

    @property
    def duration(self):
        return self._duration

    @property
    def currency(self):
        return "EUR"

    @property
    def marketdata(self):
        return self._marketdata

    async def fetch(self):
        data = await self._fetch_data(self.URL)
        self._duration = data["interval"]
        assert data["unit"].lower() == CT_PER_KWH.lower()
        marketdata = self._extract_marketdata(data["data"])
        # override duration and compress data
        self._duration = 60
        self._marketdata = self._compress_marketdata(marketdata)

    async def _fetch_data(self, url):
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data:
            entries.append(Marketprice(self._duration, entry))
        return entries

    def _compress_marketdata(self, data):
        entries = []
        start = None
        for entry in data:
            if start == None:
                start = entry
                continue
            is_price_equal = start.price_per_kwh == entry.price_per_kwh
            is_continuation = start.end_time == entry.start_time
            max_start_time = start.start_time + timedelta(minutes=self._duration)
            is_same_hour = entry.start_time < max_start_time

            if is_price_equal & is_continuation & is_same_hour:
                start.set_end_time(entry.end_time)
            else:
                entries.append(start)
                start = entry
        if start != None:
            entries.append(start)
        return entries
