import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    UOM_EUR_PER_MWh = "EUR/MWh"

    def __init__(self, data):
        assert data["unit"].lower() == self.UOM_EUR_PER_MWh.lower()
        self._start_time = datetime.fromtimestamp(
            data["start_timestamp"] / 1000, tz=timezone.utc
        )
        self._end_time = datetime.fromtimestamp(
            data["end_timestamp"] / 1000, tz=timezone.utc
        )
        self._price_eur_per_mwh = float(data["marketprice"])

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_eur_per_mwh} {self.UOM_EUR_PER_MWh})"  # noqa: E501

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
    def price_ct_per_kwh(self):
        return round(self._price_eur_per_mwh / 10, 3)


def toEpochMilliSec(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class Awattar:
    URL = "https://api.awattar.{market_area}/v1/marketdata"

    MARKET_AREAS = ("at", "de")

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._url = self.URL.format(market_area=market_area)
        self._marketdata = []

    @property
    def name(self):
        return "Awattar API V1"

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
        data = await self._fetch_data(self._url)
        self._marketdata = self._extract_marketdata(data["data"])

    async def _fetch_data(self, url):
        start = dt.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=1
        )
        end = start + timedelta(days=3)
        async with self._session.get(
            url, params={"start": toEpochMilliSec(start), "end": toEpochMilliSec(end)}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data:
            entries.append(Marketprice(entry))
        return entries
