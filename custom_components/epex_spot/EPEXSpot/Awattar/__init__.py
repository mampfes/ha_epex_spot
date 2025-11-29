"""Awattar API."""

from datetime import datetime, timedelta, timezone
import logging
from typing import List

import aiohttp

from homeassistant.util import dt as dt_util

from ...common import Marketprice, compress_marketdata
from ...const import EUR_PER_MWH, UOM_EUR_PER_KWH

_LOGGER = logging.getLogger(__name__)


class AwattarMarketprice(Marketprice):
    """Marketprice class for Awattar."""

    def __init__(self, data):
        assert data["unit"].lower() == EUR_PER_MWH.lower()
        self._start_time = datetime.fromtimestamp(
            data["start_timestamp"] / 1000, tz=timezone.utc
        )
        self._end_time = datetime.fromtimestamp(
            data["end_timestamp"] / 1000, tz=timezone.utc
        )
        self._market_price_per_kwh = round(float(data["marketprice"]) / 1000.0, 6)
        self._unit = UOM_EUR_PER_KWH


def toEpochMilliSec(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class Awattar:
    URL = "https://api.awattar.{market_area}/v1/marketdata"

    MARKET_AREAS = ("at", "de")
    SUPPORTED_DURATIONS = (60,)

    def __init__(self, market_area: str, duration: int, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._url = self.URL.format(market_area=market_area)
        self._marketdata = []
        self._duration = duration

    @property
    def name(self) -> str:
        return "Awattar API V1"

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
    def marketdata(self) -> List[Marketprice]:
        return self._marketdata

    async def fetch(self):
        data = await self._fetch_data(self._url)
        marketdata = self._extract_marketdata(data["data"])
        if self._duration > 15:
            marketdata = compress_marketdata(marketdata, self._duration)
        self._marketdata = marketdata

    async def _fetch_data(self, url):
        start = dt_util.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        end = start + timedelta(days=3)
        async with self._session.get(
            url, params={"start": toEpochMilliSec(start), "end": toEpochMilliSec(end)}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data) -> List[Marketprice]:
        entries = []
        for entry in data:
            entries.append(AwattarMarketprice(entry))
        return entries
