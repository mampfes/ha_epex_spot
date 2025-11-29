"""Energyforecast.de"""

from datetime import datetime
import logging

import aiohttp


from ...const import UOM_EUR_PER_KWH

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    """Marketprice class for Energyforecast."""

    def __init__(self, data):
        self._start_time = datetime.fromisoformat(data["start"])
        self._end_time = datetime.fromisoformat(data["end"])
        self._market_price_per_kwh = round(float(data["price"]), 6)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._market_price_per_kwh} {UOM_EUR_PER_KWH})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def market_price_per_kwh(self):
        return self._market_price_per_kwh


class Energyforecast:
    URL = "https://www.energyforecast.de/api/v1/predictions/prices_for_ha"

    MARKET_AREAS = ("de",)
    SUPPORTED_DURATIONS = (15, 60)

    def __init__(
        self,
        market_area: str,
        duration: int,
        token: str,
        session: aiohttp.ClientSession,
    ):
        self._token = token
        self._session = session
        self._market_area = market_area
        self._marketdata = []
        self._duration = duration
        self._resolution = "HOURLY" if duration == 60 else "QUARTER_HOURLY"

    @property
    def name(self) -> str:
        return "Energyforecast API V1"

    @property
    def market_area(self) -> str:
        return self._market_area

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def currency(self) -> str:
        return "EUR"

    @property
    def marketdata(self):
        return self._marketdata

    async def fetch(self):
        data = await self._fetch_data(self.URL)
        self._marketdata = self._extract_marketdata(data["forecast"]["data"])

    async def _fetch_data(self, url):
        async with self._session.get(
            url,
            params={
                "token": self._token,
                "fixed_cost_cent": 0,
                "vat": 0,
                "resolution": self._resolution,
            },
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        return [Marketprice(entry) for entry in data]
