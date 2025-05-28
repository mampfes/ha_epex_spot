"""Hofer Gruenstrom API."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

import aiohttp

from ...const import TIMEZONE_HOFER_GRUENSTROM
from custom_components.epex_spot import const

_LOGGER = logging.getLogger(__name__)


def _set_tz_on_date(date):
    """Set timezone on a date object."""
    timezone = ZoneInfo(TIMEZONE_HOFER_GRUENSTROM)

    if date.tzinfo is None:
        return date.replace(tzinfo=timezone)

    return date.astimezone(timezone)


class Marketprice:
    """Marketprice class for Hofer Gruenstrom."""

    def __init__(self, data):
        self._from = datetime.fromisoformat(data["from"])
        self._to = datetime.fromisoformat(data["to"])
        # price does not include vat or other taxes, so it is already in the correct format
        self._price = round(float(data["price"]) / 100, 6)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(start: {self._from.isoformat()}, "
            f"end: {self._to.isoformat()}, price: {self._price} {const.CT_PER_KWH})"
        )

    @property
    def start_time(self):
        return _set_tz_on_date(self._from)

    @property
    def end_time(self):
        return _set_tz_on_date(self._to)

    @property
    def price_per_kwh(self):
        return self._price


class HoferGruenstrom:
    URL = "https://www.xn--hofer-grnstrom-nsb.at/service/energy-manager/spot-prices"

    MARKET_AREAS = ("at",)

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._duration = 15  # default value, can be overwritten by API response
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
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        dates = [today, tomorrow]

        # fetch data for today and tomorrow

        marketdata = []
        for date in dates:
            raw_data = await self._fetch_data_for_date(date)
            if raw_data is None:
                continue

            # get the data key from the response
            data = raw_data.get("data")
            if not data:
                _LOGGER.error("No data found in response for %s", date.isoformat())
                continue
            # extract market data
            for item in data:
                if not item.get("from") or not item.get("to") or not item.get("price"):
                    _LOGGER.warning("Skipping item with missing fields: %s", item)
                    continue
                # create Marketprice instance
                marketdata.append(Marketprice(item))

        self._marketdata = marketdata

    async def _fetch_data_for_date(self, date):
        """Fetch data for a specific date."""
        url = f"{self.URL}?year={date.year}&month={date.month}&day={date.day}"
        async with self._session.get(url) as response:
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
