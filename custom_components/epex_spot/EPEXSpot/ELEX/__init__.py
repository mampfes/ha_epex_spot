"""ELEX API Client for EPEX Spot integration."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import aiohttp

_LOGGER = logging.getLogger(__name__)


class ElexMarketprice:
    """Bulletproof data container expected by EPEX Spot core."""
    def __init__(self, start_time: datetime, end_time: datetime, price_kwh: float):
        self._start_time = start_time
        self._end_time = end_time
        self._market_price_per_kwh = price_kwh

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def market_price_per_kwh(self):
        return self._market_price_per_kwh


class Elex:
    """Client for ELEX Day-Ahead spot prices."""

    URL = "https://api.elex.mk/v1/history/price"

    # The Dictionary Map: "UI Short Code" : "API Expected String"
    # Format: "Short_Code": "Backend_Long_Name"
    MARKET_AREAS = {
        "Albania_AL": "AL",
        "Austria_AT": "AT",
        "Belgium_BE": "BE",
        "Bosnia_BA": "BA",
        "Bulgaria_BG": "BG",
        "Croatia_HR": "HR",
        "Czech_CZ": "CZ",
        "Denmark_DK1": "DK1",
        "Denmark_DK2": "DK2",
        "Estonia_ES": "EE",
        "Finland_FI": "FI",
        "France_FR": "FR",
        "Germany_DE": "DE",
        "Greece_GR": "GR",
        "Hungary_HU": "HU",
        "Ireland_IE": "IE",
        "Italy_IT": "IT",
        "Italy_NORTH": "IT-North",
        "Italy_CNORTH": "IT-CNorth",
        "Italy_CSOUTH": "IT-CSouth",
        "Italy_SOUTH": "IT-South",
        "Italy_SICILY": "IT-Sicily",
        "Italy_SARDINIA": "IT-Sardinia",
        "Italy_CALABRIA": "IT-Calabria",
        "Kosovo_XK": "XK",
        "Latvia_LV": "LV",
        "Lithuania_LT": "LT",
        "Macedonia_MK": "MK",
        "Montenegro_ME": "ME",
        "Netherlands_NL": "NL",
        "Norway_NO1": "NO1",
        "Norway_NO2": "NO2",
        "Norway_NO3": "NO3",
        "Norway_NO4": "NO4",
        "Norway_NO5": "NO5",
        "Poland_PL": "PL",
        "Portugal_PT": "PT",
        "Romania_RO": "RO",
        "Serbia_RS": "RS",
        "Slovakia_SK": "SK",
        "Slovenia_SI": "SI",
        "Spain_ES": "ES",
        "Sweden_SE1": "SE1",
        "Sweden_SE2": "SE2",
        "Sweden_SE3": "SE3",
        "Sweden_SE4": "SE4",
        "Switzerland_CH": "CH",
        "United_Kingdom_UK": "UK",
        "Ukraine_UA": "UA"
    }                               

    SUPPORTED_DURATIONS = (15, 60)

    def __init__(self, market_area: str, api_key: str, duration: int, session: aiohttp.ClientSession):
        self._session = session
        self._market_area = market_area
        self._api_key = api_key
        self._duration = duration
        self._marketdata = []

    @property
    def name(self) -> str:
        return "ELEX Market Data"

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
    def marketdata(self):
        return self._marketdata

    async def fetch(self):
        """Fetch the day-ahead prices from ELEX API."""
        
        # Ensure we use Central European Time to request the correct "today"
        tz_cet = ZoneInfo("Europe/Berlin")
        today_str = datetime.now(tz_cet).strftime("%Y-%m-%d")
        
        # Map the UI short code back to your backend string
        # api_country_string = self.MARKET_AREAS.get(self._market_area, self._market_area)

        params = {
            "country": self._market_area,
            "start_date": today_str,
            "days": 2
        }
        
        headers = {
            "x-api-key": self._api_key
        }

        _LOGGER.debug(f"Fetching ELEX history data for {self._market_area} starting {today_str}")
        

        try:
            async with self._session.get(self.URL, params=params, headers=headers) as resp:
                data = await resp.json()

                # Catch custom API errors (like the Free Tier lock) gracefully
                if resp.status != 200 or data.get("error"):
                    error_msg = data.get("message", f"HTTP {resp.status}")
                    _LOGGER.error(f"ELEX API Error: {error_msg}")
                    raise Exception(f"ELEX Access Denied: {error_msg}")

                self._marketdata = self._extract_marketdata(data, tz_cet)
                
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error communicating with ELEX: {err}")
            raise Exception(f"Network error: {err}")

    def _extract_marketdata(self, json_data, tz_cet):
        """Extract prices from JSON, calculate timestamps, convert to €/kWh."""
        entries = []
        results = json_data.get("result", [])

        for daily_data in results:
            base_date_str = daily_data.get("date")
            if not base_date_str:
                continue
                
            hourly_prices = daily_data.get("hours", [])
            data_points_count = len(hourly_prices)
            
            if data_points_count == 0:
                continue

            # Dynamically calculate if this is a 60-min or 15-min market
            duration_minutes = 1440 // data_points_count
            
            for index, price_mwh in enumerate(hourly_prices):
                minutes_offset = index * duration_minutes
                
                base_dt = datetime.strptime(base_date_str, "%Y-%m-%d")
                start_dt = base_dt + timedelta(minutes=minutes_offset)
                
                # Make timestamps timezone-aware for HA charting
                start_dt_aware = start_dt.replace(tzinfo=tz_cet)
                end_dt_aware = start_dt_aware + timedelta(minutes=duration_minutes)
                
                # Convert ELEX €/MWh to HA expected €/kWh
                price_kwh = float(price_mwh) / 1000.0
                
                entries.append(
                    ElexMarketprice(
                        start_time=start_dt_aware,
                        end_time=end_dt_aware,
                        price_kwh=round(price_kwh, 6),
                    )
                )

        # Sort chronologically before returning to the core integration
        return sorted(entries, key=lambda x: x.start_time)