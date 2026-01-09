"""Hofer Gruenstrom API."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

import aiohttp

from ...common import Marketprice, compress_marketdata
from ...const import TIMEZONE_HOFER_GRUENSTROM

_LOGGER = logging.getLogger(__name__)


def _set_tz_on_date(date: datetime):
    """Set timezone on a date object."""
    timezone = ZoneInfo(TIMEZONE_HOFER_GRUENSTROM)

    if date.tzinfo is None:
        return date.replace(tzinfo=timezone)

    return date.astimezone(timezone)


class HoferGruenstrom:
    URL = "https://www.xn--hofer-grnstrom-nsb.at/service/energy-manager/spot-prices"

    MARKET_AREAS = ("at",)
    SUPPORTED_DURATIONS = (
        15,
        60,
    )

    def __init__(self, market_area: str, duration: int, session: aiohttp.ClientSession):
        if market_area not in self.MARKET_AREAS:
            raise ValueError(f"Unsupported bidding zone: {market_area}")

        if duration not in self.SUPPORTED_DURATIONS:
            raise ValueError(f"Unsupported duration: {duration}")

        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._marketdata = []

    @property
    def name(self):
        return "Hofer Gruenstrom API"

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
        # get todays and tomorrows date components
        today = datetime.now(ZoneInfo(TIMEZONE_HOFER_GRUENSTROM))
        tomorrow = today + timedelta(days=1)
        dates = [today, tomorrow]

        # fetch data for today and tomorrow

        marketdata: list[Marketprice] = []
        for date in dates:
            raw_data = await self._fetch_data_for_date(date)
            if raw_data is None:
                continue

            # get the data key from the response
            data = raw_data.get("data")
            if not data:
                _LOGGER.error("No data found in response for %s", date.isoformat())
                continue

            duration = self._get_duration_from_data(data)
            # extract market data
            complete_marketdata = self._extract_marketdata(data, duration)
            if duration < self.duration:
                complete_marketdata = compress_marketdata(
                    complete_marketdata, self.duration
                )

            marketdata += complete_marketdata

        self._marketdata = marketdata

    def _extract_marketdata(self, data, duration):
        entries: list[Marketprice] = []
        for entry in data:
            entries.append(
                Marketprice(
                    start_time=_set_tz_on_date(datetime.fromisoformat(entry["from"])),
                    duration=duration,
                    price=round(float(entry["price"]) / 100, 6),
                )
            )
        return entries

    async def _fetch_data_for_date(self, date):
        """Fetch data for a specific date."""
        url = f"{self.URL}?year={date.year}&month={date.month}&day={date.day}"
        # unfortunately it is required to set `ssl` to false since the certificate is not publicly trusted.
        # the main reason for this might be that the API is not really meant to be used externally, but just from
        # Hofer Grünstrom's website (https://www.hofer-grünstrom.at/tarife-zum-geld-sparen#spot).
        async with self._session.get(url, ssl=False) as response:
            if response.status != 200:
                if response.status == 204:
                    _LOGGER.debug("No data available for %s yet.", date.isoformat())
                    return None
                _LOGGER.error(
                    "Failed to fetch data from Hofer Gruenstrom API: %s",
                    response.status,
                )
                return None
            return await response.json()

    def _get_duration_from_data(self, data):
        if not data:
            _LOGGER.error("Empty data received in _get_duration_from_data")
            raise ValueError("Cannot determine duration from empty data")
        start_date: datetime = datetime.fromisoformat(data[0]["from"])
        end_date: datetime = datetime.fromisoformat(data[0]["to"])
        duration: timedelta = end_date - start_date
        return int(duration.total_seconds() / 60)
