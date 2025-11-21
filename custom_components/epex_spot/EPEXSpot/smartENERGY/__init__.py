"""smartENERGY API."""

from datetime import datetime
import logging

import aiohttp

from ...common import Marketprice, compress_marketdata
from ...const import CT_PER_KWH

_LOGGER = logging.getLogger(__name__)


class smartENERGY:
    URL = "https://apis.smartenergy.at/market/v1/price"

    MARKET_AREAS = ("at",)
    SUPPORTED_DURATIONS = (15, 60)

    def __init__(self, market_area, duration: int, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._duration = duration
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
        duration = data["interval"]
        assert data["unit"].lower() == CT_PER_KWH.lower()
        self._marketdata = self._extract_marketdata(data["data"], duration)

        # compress data if required
        if duration < self._duration:
            self._marketdata = compress_marketdata(self.marketdata, self._duration)

    async def _fetch_data(self, url):
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data, duration):
        entries = []
        for entry in data:
            entries.append(
                Marketprice(
                    start_time=datetime.fromisoformat(entry["date"]),
                    duration=duration,
                    # price includes austrian vat (20%)
                    # -> remove to be consistent with other data sources
                    price=round(float(entry["value"]) / 100.0 / 1.2, 6),
                )
            )
        return entries
