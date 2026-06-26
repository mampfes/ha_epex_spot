"""NextEnergy API provider for Dutch electricity market prices."""

from datetime import datetime, timedelta, date as date_type
import logging
import re
from typing import List
import urllib.parse
from zoneinfo import ZoneInfo

import aiohttp

from homeassistant.util import dt as dt_util

from ...common import Marketprice
from ...const import UOM_EUR_PER_KWH

_LOGGER = logging.getLogger(__name__)

TZ_AMSTERDAM = ZoneInfo("Europe/Amsterdam")

URL_VERSION = "https://mijn.nextenergy.nl/Website_CW/moduleservices/moduleversioninfo"
URL_PRICES = "https://mijn.nextenergy.nl/Website_CW/screenservices/Website_CW/Blocks/WB_EnergyPrices/DataActionGetDataPoints"

# The anonymous CSRF token is a constant baked into the OutSystems application JS.
# It is the fallback CSRF token used for unauthenticated (anonymous) sessions.
CSRF_TOKEN = "T6C+9iB49TLra4jEsMeSckDMNhQ="
API_VERSION = "KKzGGxaqgJLBcYSoN9w5oA"


class NextEnergy:
    MARKET_AREAS = ("nl",)
    SUPPORTED_DURATIONS = (60,)

    def __init__(self, market_area: str, duration: int, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._marketdata = []
        self._os_visitor = None  # cached: server only sends this once (100-yr expiry)

    @property
    def name(self) -> str:
        return "NextEnergy"

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
        version_token, cookies = await self._init_session()

        today = dt_util.now().astimezone(TZ_AMSTERDAM).date()
        tomorrow = today + timedelta(days=1)

        marketdata = []
        for fetch_date in (today, tomorrow):
            data = await self._fetch_prices(fetch_date, version_token, cookies)
            marketdata.extend(self._parse_prices(data, fetch_date))

        self._marketdata = sorted(marketdata, key=lambda e: e.start_time)

    async def _init_session(self):
        """Fetch a fresh session from OutSystems and return (version_token, cookies)."""
        async with self._session.get(
            URL_VERSION,
            headers={
                "Accept": "application/json",
                "Referer": "https://mijn.nextenergy.nl/Website_CW/MarketPrices",
            },
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            version_token = data["versionToken"]
            # osVisit is refreshed every 30 min; osVisitor is long-lived (100-yr
            # expiry) so the server only sets it on the very first request.
            if "osVisitor" in resp.cookies:
                self._os_visitor = resp.cookies["osVisitor"].value
            nr2_value = urllib.parse.quote(
                f"crf={CSRF_TOKEN};uid=0;unm=", safe=""
            )
            cookies = {
                "osVisit": resp.cookies["osVisit"].value,
                "osVisitor": self._os_visitor,
                "nr2Users": nr2_value,
            }
            return version_token, cookies

    async def _fetch_prices(self, fetch_date: date_type, version_token: str, cookies: dict) -> list:
        """Fetch hourly prices for a given date."""
        date_str = fetch_date.strftime("%Y-%m-%d")
        payload = {
            "versionInfo": {
                "moduleVersion": version_token,
                "apiVersion": API_VERSION,
            },
            "viewName": "MainFlow.MarketPrices",
            "screenData": {
                "variables": {
                    "Graphsize": 235,
                    "IsOpenPopup": False,
                    "HighchartsJSON": "",
                    "DistributionId": 3,
                    "IsDesktop": False,
                    "IsTablet": False,
                    "IsLoading": True,
                    "NE_StartDate": "2022-07-01",
                    "Filter": {
                        "PriceIncludingVAT": False,
                        "PriceDate": date_str,
                        "CostsLevel": "MarketPrice",
                        "CurrentHour": 0,
                    },
                }
            },
        }
        # Build cookie string manually to preserve nr2Users URL-encoding
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        async with self._session.post(
            URL_PRICES,
            json=payload,
            headers={
                "Accept": "application/json",
                "Referer": "https://mijn.nextenergy.nl/Website_CW/MarketPrices",
                "Origin": "https://mijn.nextenergy.nl",
                "X-CSRFToken": CSRF_TOKEN,
                "Cookie": cookie_str,
            },
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()

        if result.get("exception"):
            raise ValueError(
                f"NextEnergy API error: {result['exception'].get('message')}"
            )

        version_info = result.get("versionInfo", {})
        if version_info.get("hasApiVersionChanged"):
            _LOGGER.warning(
                "NextEnergy API version has changed. "
                "The integration may need to be updated."
            )

        return result["data"]["DataPoints"]["List"]

    def _parse_prices(self, data_points: list, fetch_date: date_type) -> List[Marketprice]:
        """Parse API response into Marketprice objects."""
        entries = []
        for point in data_points:
            tooltip = point.get("Tooltip", "")
            # Tooltip format: "Nh €X.XX" where N is the local hour (0-23)
            match = re.match(r"^(\d+)h", tooltip)
            if not match:
                _LOGGER.warning("Unexpected tooltip format: %s", tooltip)
                continue

            hour = int(match.group(1))
            price_str = point.get("Value", "")
            if not price_str:
                continue

            try:
                price = float(price_str)
            except ValueError:
                _LOGGER.warning("Could not parse price value: %s", price_str)
                continue

            start_time = datetime(
                fetch_date.year,
                fetch_date.month,
                fetch_date.day,
                hour,
                0,
                0,
                tzinfo=TZ_AMSTERDAM,
            )
            entries.append(
                Marketprice(
                    start_time=start_time,
                    duration=60,
                    price=price,
                    unit=UOM_EUR_PER_KWH,
                )
            )

        return entries
