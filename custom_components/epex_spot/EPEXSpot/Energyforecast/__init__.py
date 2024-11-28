"""Energyforecast.de"""

from datetime import datetime
import logging

import aiohttp

from homeassistant.util import dt as dt_util

from ...const import EUR_PER_MWH, UOM_EUR_PER_KWH

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    """Marketprice class for Energyforecast."""

    def __init__(self, data):
        assert data["unit"].lower() == EUR_PER_MWH.lower()
        self._start_time = datetime.fromisoformat(data["start"])
        self._end_time = datetime.fromisoformat(data["end"])
        self._price_per_kwh = round(float(data["price"]), 6)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, price: {self._price_per_kwh} {UOM_EUR_PER_KWH})" 

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_per_kwh(self):
        return self._price_per_kwh


def toEpochMilliSec(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class Energyforecast:
    URL = "https://www.energyforecast.de/api/v1/predictions/next_96_hours"

    MARKET_AREAS = ("de")

    def __init__(self, market_area, token: str, session: aiohttp.ClientSession):
        self._token = token
        self._session = session
        self._market_area = market_area
        self._marketdata = []

    @property
    def name(self):
        return "Energyforecast API V1"

    @property
    def market_area(self):
        return self._market_area

    @property
    def duration(self):
        return 60

    @property
    def currency(self):
        return "EUR"

    @property
    def marketdata(self):
        return self._marketdata

    async def fetch(self):
        data = await self._fetch_data(self.URL)
        self._marketdata = self._extract_marketdata(data)

    async def _fetch_data(self, url):
        async with self._session.get(
            url, params={"token": self._token}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data:
            entries.append(Marketprice(entry))
        return entries
