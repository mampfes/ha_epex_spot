"""Nordpool API Client."""

from datetime import date, datetime, timedelta, timezone
import logging
import aiohttp
from typing import List, Optional

from ...common import Marketprice

_LOGGER = logging.getLogger(__name__)

BIDDING_ZONES = {
    "EE", "LT", "LV", "AT", "BE", "FR", "GER", "NL", "PL", "DK1", "DK2", "FI", "NO1", "NO2", "NO3", "NO4", "NO5", "SE1",
    "SE2", "SE3", "SE4"
}


class Nordpool:
    """Client for Nordpool day-ahead electricity prices."""
    URL = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPriceIndices"

    MARKET_AREAS = BIDDING_ZONES

    SUPPORTED_DURATIONS = (15, 30, 60)

    def __init__(self, market_area: str, duration: int, session: aiohttp.ClientSession):
        if market_area not in self.MARKET_AREAS:
            raise ValueError(f"Unsupported bidding zone: {market_area}")

        if duration not in self.SUPPORTED_DURATIONS:
            raise ValueError(f"Unsupported duration: {duration}")

        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._marketdata: List[Marketprice] = []

    @property
    def name(self):
        return "Nordpool API"

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
        try:
            today = date.today()
            json_data = await self._fetch_data(fetch_date=today)
            marketdata = self._extract_marketdata(json_data)
        except Exception as err:
            _LOGGER.debug(f"Unexpected error fetching today data: {err}")
            raise

        try:
            tomorrow = today + timedelta(days=1)
            json_data = await self._fetch_data(fetch_date=tomorrow)
            marketdata.extend(self._extract_marketdata(json_data))
        except Exception as err:
            _LOGGER.debug(f"Unexpected error fetching tomorrow data: {err}")

        self._marketdata = marketdata

    #
    # HTTP request
    #
    async def _fetch_data(self, fetch_date: date):
        params = {
            "indexNames": self._market_area,
            "date": fetch_date.isoformat(),
            "market": "DayAhead",
            "resolutionInMinutes": self._duration,
            "currency": self.currency,
        }

        async with self._session.get(self.URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    #
    # Convert raw JSON array to Marketprice objects
    #
    def _extract_marketdata(
            self, data
    ) -> List[Marketprice]:
        extract: List[Marketprice] = []

        entries = data.get("multiIndexEntries", [])
        for entry in entries:
            entry_per_area = entry.get("entryPerArea", {})
            if self._market_area not in entry_per_area:
                continue

            start_utc = datetime.fromisoformat(entry['deliveryStart'])
            end_utc = datetime.fromisoformat(entry['deliveryEnd'])
            duration = int((end_utc - start_utc).total_seconds() / 60)
            price = (entry_per_area[self._market_area]) / 1000
            extract.append(Marketprice(start_time=start_utc, duration=duration, price=price))

        return extract
