"""SMARD.de API."""

from datetime import datetime, timedelta, timezone
import logging

import aiohttp

from ...const import UOM_EUR_PER_KWH

# from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)

MARKET_AREA_MAP = {
    "DE-LU": 4169,
    "Anrainer DE-LU": 5078,
    "BE": 4996,
    "NO2": 4997,
    "AT": 4170,
    "DK1": 252,
    "DK2": 253,
    "FR": 254,
    "IT (North)": 255,
    "NL": 256,
    "PL": 257,
    "CH": 259,
    "SI": 260,
    "CZ": 261,
    "HU": 262,
}


class Marketprice:
    """Marketprice class for SMARD.de."""

    def __init__(self, data):
        self._start_time = datetime.fromtimestamp(data[0] / 1000, tz=timezone.utc)
        self._end_time = self._start_time + timedelta(
            hours=1
        )  # TODO: this will not work for 1/2h updates

        self._price_per_kwh = round(float(data[1]) / 1000.0, 6)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_per_kwh} {UOM_EUR_PER_KWH})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_per_kwh(self):
        return self._price_per_kwh


class SMARD:
    URL = "https://www.smard.de/app/chart_data"

    MARKET_AREAS = MARKET_AREA_MAP.keys()

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._marketdata = []

    @property
    def name(self):
        return "SMARD.de"

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
        smard_filter = MARKET_AREA_MAP[self._market_area]
        smard_region = self._market_area
        smard_resolution = "hour"

        # get available timestamps for given market area
        url = f"{self.URL}/{smard_filter}/{smard_region}/index_{smard_resolution}.json"
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            j = await resp.json()

        # fetch last 2 data-series, because on sunday noon starts a new series
        # and then some data is missing
        latest_timestamp = j["timestamps"][-2:]

        entries = []

        for lt in latest_timestamp:
            # get available data
            data = await self._fetch_data(
                lt, smard_filter, smard_region, smard_resolution
            )

            for entry in data["series"]:
                if entry[1] is not None:
                    entries.append(Marketprice(entry))

        if entries[-1].start_time.date() == datetime.today().date():
            # latest data is on the same day, only return 48 entries
            # thats yesterday and today
            self._marketdata = entries[
                -48:
            ]  # limit number of entries to protect HA recorder
        else:
            # latest data is tomorrow, return 72 entries
            # thats yesterday, today and tomorrow
            self._marketdata = entries[
                -72:
            ]  # limit number of entries to protect HA recorder

    async def _fetch_data(
        self, latest_timestamp, smard_filter, smard_region, smard_resolution
    ):
        # get available data
        url = f"{self.URL}/{smard_filter}/{smard_region}/{smard_filter}_{smard_region}_{smard_resolution}_{latest_timestamp}.json"  # noqa: E501
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
