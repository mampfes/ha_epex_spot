from datetime import datetime, timedelta
import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    UOM_CT_PER_kWh = "ct/kWh"

    def __init__(self, duration, data):
        self._start_time = datetime.fromisoformat(data["date"])
        self._end_time = self._start_time + timedelta(minutes=duration)
        # price includes austrian vat (20%) -> remove to be consistent with other data sources
        self._price_ct_per_kwh = round(float(data["value"]) / 1.2, 3)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_ct_per_kwh} {self.UOM_CT_PER_kWh})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_eur_per_mwh(self):
        return self._price_ct_per_kwh * 10

    @property
    def price_ct_per_kwh(self):
        return self._price_ct_per_kwh


class smartENERGY:
    URL = "https://apis.smartenergy.at/market/v1/price"

    MARKET_AREAS = ("at",)

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._duration = 15 # default value, can be overwritten by API response
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
        assert data["unit"].lower() == Marketprice.UOM_CT_PER_kWh.lower()
        self._marketdata = self._extract_marketdata(data["data"])

    async def _fetch_data(self, url):
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data:
            entries.append(Marketprice(self._duration, entry))
        return entries
