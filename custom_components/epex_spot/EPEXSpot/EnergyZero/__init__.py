"""EnergyZero API."""

from datetime import datetime
import aiohttp
import logging

from ...common import Marketprice

_LOGGER = logging.getLogger(__name__)


class EnergyZero:
    URL = "https://public.api.energyzero.nl/public/v1/prices"

    MARKET_AREAS = ("nl",)
    SUPPORTED_DURATIONS = (15, 60)

    def __init__(
        self,
        market_area: str,
        duration: int,
        session: aiohttp.ClientSession,
    ):
        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._marketdata = []

    @property
    def name(self):
        return f"EnergyZero ({'Quarterly' if self._duration == 15 else 'Hourly'})"

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
        """Fetch market price data using EnergyZero's rolling data window."""
        now = datetime.now()

        date_str = now.strftime("%d-%m-%Y")
        interval = "INTERVAL_QUARTER" if self._duration == 15 else "INTERVAL_HOUR"

        params = {
            "date": date_str,
            "interval": interval,
            "energyType": "ENERGY_TYPE_ELECTRICITY"
        }

        try:
            marketdata: list[Marketprice] = []
            async with self._session.get(self.URL, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if "base" in data:
                    for entry in data["base"]:
                        start_time = datetime.fromisoformat(entry["start"])
                        price = float(entry["price"]["value"])

                        marketdata.append(
                            Marketprice(
                                duration=self._duration,
                                start_time=start_time,
                                price=round(price, 6)
                            )
                        )

            minimal_points = int(23 * 60 / self._duration)
            if len(marketdata) < minimal_points:
                raise ValueError(
                    f"Received incomplete data from EnergyZero. Expected at least {minimal_points} points, got {len(marketdata)}."
                )

            marketdata.sort(key=lambda x: x.start_time)
            self._marketdata = marketdata

        except Exception as e:
            _LOGGER.error(f"Error fetching EnergyZero data for date {date_str}: {e}")
