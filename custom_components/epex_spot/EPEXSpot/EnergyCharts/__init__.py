"""Energy-Charts API Client."""

from datetime import date, datetime, timezone, timedelta
import logging
import aiohttp
from typing import List

from ...common import Marketprice, average_marketdata

_LOGGER = logging.getLogger(__name__)

BIDDING_ZONES = {
    "AT",
    "BE",
    "BG",
    "CH",
    "CZ",
    "DE-LU",
    "DE-AT-LU",
    "DK1",
    "DK2",
    "EE",
    "ES",
    "FI",
    "FR",
    "GR",
    "HR",
    "HU",
    "IT-Calabria",
    "IT-Centre-North",
    "IT-Centre-South",
    "IT-North",
    "IT-SACOAC",
    "IT-SACODC",
    "IT-Sardinia",
    "IT-Sicily",
    "IT-South",
    "LT",
    "LV",
    "ME",
    "NL",
    "NO1",
    "NO2",
    "NO2NSL",
    "NO3",
    "NO4",
    "NO5",
    "PL",
    "PT",
    "RO",
    "RS",
    "SE1",
    "SE2",
    "SE3",
    "SE4",
    "SI",
    "SK",
}


class EnergyCharts:
    """Client for Energy-Charts day-ahead electricity prices."""

    URL = "https://api.energy-charts.info/price"

    MARKET_AREAS = BIDDING_ZONES

    SUPPORTED_DURATIONS = (15, 60)

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
        return "Energy-Charts API"

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
        """Fetch electricity prices and auto-detect resolution."""

        json_data = await self._fetch_data()

        unix_seconds = json_data.get("unix_seconds", [])
        prices = json_data.get("price", [])
        unit = json_data.get("unit", "EUR/MWh")

        if not unix_seconds or not prices:
            _LOGGER.error("Energy-Charts API returned empty data")
            self._marketdata = []
            return

        durations = []
        for i in range(1, len(unix_seconds)):
            delta_min = int((unix_seconds[i] - unix_seconds[i - 1]) / 60)
            durations.append(delta_min)

        base_duration = max(set(durations), key=durations.count)
        _LOGGER.debug("Detected Energy-Charts base duration: %d minutes", base_duration)

        marketdata = self._extract_marketdata(unix_seconds, prices, base_duration, unit)

        #
        # 3) Compress if user requests coarser data
        #
        if self._duration != base_duration:
            _LOGGER.debug(
                "Averaging market data from %d to %d minutes",
                base_duration,
                self._duration,
            )
            marketdata = average_marketdata(marketdata, self._duration)

        self._marketdata = marketdata

    #
    # HTTP request
    #

    async def _fetch_data(self):
        # Compute start = today, end = tomorrow (daily format)
        start_date = date.today()
        end_date = start_date + timedelta(days=1)

        params = {
            "bzn": self._market_area,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

        async with self._session.get(self.URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    #
    # Convert raw JSON arrays to Marketprice objects
    #
    def _extract_marketdata(
        self, unix_seconds, prices, duration, unit
    ) -> List[Marketprice]:
        entries: List[Marketprice] = []

        for ts, price_mwh in zip(unix_seconds, prices):
            start_time = datetime.fromtimestamp(ts, tz=timezone.utc)
            price_kwh = float(price_mwh) / 1000.0

            entries.append(
                Marketprice(
                    start_time=start_time,
                    duration=duration,
                    price=round(price_kwh, 6),
                )
            )

        return entries
