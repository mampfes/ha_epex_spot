"""SMARD.de API."""

from datetime import datetime, timezone
import logging
from typing import List

import aiohttp

from ...const import UOM_EUR_PER_KWH
from ...common import Marketprice

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


class SMARD:
    URL = "https://www.smard.de/app/chart_data"

    MARKET_AREAS = MARKET_AREA_MAP.keys()
    SUPPORTED_DURATIONS = (15, 60)

    def __init__(self, market_area: str, duration: int, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._marketdata = []
        self._duration = duration
        self._resolution = "hour" if duration == 60 else "quarterhour"

    @property
    def name(self):
        return "SMARD.de"

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
        smard_filter = MARKET_AREA_MAP[self._market_area]
        smard_region = self._market_area

        # get available timestamps for given market area
        url = f"{self.URL}/{smard_filter}/{smard_region}/index_{self._resolution}.json"
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            j = await resp.json()

        # fetch last 2 data-series, because on sunday noon starts a new series
        # and then some data is missing
        latest_timestamp = j["timestamps"][-2:]

        entries: List[Marketprice] = []

        for lt in latest_timestamp:
            # get available data
            data = await self._fetch_data(
                lt, smard_filter, smard_region, self._resolution
            )

            for entry in data["series"]:
                if entry[1] is not None:
                    entries.append(
                        Marketprice(
                            start_time=datetime.fromtimestamp(
                                entry[0] / 1000, tz=timezone.utc
                            ),
                            duration=self._duration,
                            price=round(float(entry[1]) / 1000.0, 6),
                            unit=UOM_EUR_PER_KWH,
                        )
                    )

        if entries[-1].start_time.date() == datetime.today().date():
            # latest data is on the same day, only return 48 entries
            # that's yesterday and today
            self._marketdata = entries[
                -2 * 24 * 60 // self._duration :
            ]  # limit number of entries to protect HA recorder
        else:
            # latest data is tomorrow, return 72 entries
            # that's yesterday, today and tomorrow
            self._marketdata = entries[
                -3 * 24 * 60 // self._duration :
            ]  # limit number of entries to protect HA recorder

    async def _fetch_data(self, timestamp, market, region, resolution):
        # get available data
        url = f"{self.URL}/{market}/{region}/{market}_{region}_{resolution}_{timestamp}.json"  # noqa: E501
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
