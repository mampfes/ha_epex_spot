"""ENTSO-E Transparency API Client."""

from datetime import datetime, timedelta, timezone
import enum
import logging
import aiohttp
import xml.etree.ElementTree as ET
from typing import List

# Replace this import with your actual Marketprice & compress_marketdata implementations
from ...common import Marketprice, compress_marketdata

_LOGGER = logging.getLogger(__name__)

MARKET_AREA_MAP = {
    "BE": "10YBE----------2",
    "BG": "10YBG----------L",
    "CZ": "10YCZ----------N",
    "DK_W": "10YDK-1--------W",
    "DK_E": "10YDK-2--------M",
    "EE": "10YEE----------2",
    "FI": "10YFI----------P",
    "FR": "10YFR-RTE-----C",
    "DE_ENBW": "10YDE-ENBW-----N",
    "DE_RWE": "10YDE-RWE------C",
    "DE_TSO": "10YDE-TSO-----T",
    "DE_VATTEN": "10YDE-VATTEN---L",
    "DE_TRANSNETBW": "10YDE-VE-------2",
    "GR": "10YGR-HTSO-----Y",
    "HU": "10YHU-MAVIR----U",
    "IE": "10YIE----------1",
    "IT": "10YIT-GRTN-----B",
    "IT_N": "10YIT-NORD-----T",
    "IT_S": "10YIT-SUD-----H",
    "LT": "10YLT-1001A0008Q",
    "LV": "10YLV-1001A00074",
    "NL": "10YNL----------L",
    "NO_S": "10YNOS---------T",
    "PL": "10YPL-AREA-----S",
    "PT": "10YPT-TSO-----S",
    "RO": "10YRO-TEL------P",
    "SE_1": "10YSE-1--------K",
    "SE_2": "10YSE-2--------K",
    "SE_3": "10YSE-3--------J",
    "SE_4": "10YSE-4--------K",
    "SI": "10YSI-ELES-----O",
    "GB": "10YGB----------A",
    "CH": "10YCH-SWISSGRIDZ",
    "AT": "10YAT-APG------L",
}


class MarketAgreementType(enum.Enum):
    DAY_AHEAD = "A01"
    INTRADAY = "A07"


class EntsoeTransparency:
    """Client for ENTSO-E Transparency Platform day-ahead and current prices."""

    URL = "https://web-api.tp.entsoe.eu/api"

    MARKET_AREAS = MARKET_AREA_MAP.keys()

    SUPPORTED_DURATIONS = (15, 60)

    def __init__(
        self,
        market_area: str,
        duration: int,
        session: aiohttp.ClientSession,
        token: str,
    ):
        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._token = token
        self._marketdata: List[Marketprice] = []

    @property
    def name(self):
        return "ENTSO-E Transparency API"

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
        """Fetch both day-ahead and current/intraday prices."""

        day_ahead_data = await self._fetch_day_ahead()

        self._marketdata = sorted(day_ahead_data, key=lambda x: x.start_time)

        # Compress if needed
        if self._duration != 60:
            self._marketdata = compress_marketdata(self._marketdata, self._duration)

    async def _fetch_day_ahead(self) -> List[Marketprice]:
        """Fetch day-ahead electricity prices (A44)."""
        now = datetime.now(timezone.utc)  # Align to full hour
        start_dt = now.replace(minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=2)  # next 2 days
        params = {
            "securityToken": self._token,
            "documentType": "A44",  # Day-ahead prices
            "in_Domain": MARKET_AREA_MAP[self._market_area],
            "out_Domain": MARKET_AREA_MAP[self._market_area],
            "periodStart": start_dt.strftime("%Y%m%d%H%M"),
            "periodEnd": end_dt.strftime("%Y%m%d%H%M"),
            "contract_MarketAgreement.type": MarketAgreementType.DAY_AHEAD.value,
            "offset": 0,
        }

        xml_text = await self._fetch_data(self.URL, params)
        return self._extract_marketdata(xml_text)

    async def _fetch_data(self, url, params):
        """Perform the HTTP GET request."""
        async with self._session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.text()

    def _extract_marketdata(self, xml_text) -> List[Marketprice]:
        """Extract prices (€/MWh → €/kWh) from XML."""
        entries: List[Marketprice] = []
        root = ET.fromstring(xml_text)
        ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}

        resolution_map = {"PT15M": 15, "PT60M": 60, "PT30M": 30}

        for timeseries in root.findall("ns:TimeSeries", ns):
            for period in timeseries.findall("ns:Period", ns):
                time_interval = period.find("ns:timeInterval", ns)
                start_str = time_interval.find("ns:start", ns).text
                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%MZ").replace(
                    tzinfo=timezone.utc
                )

                resolution = period.find("ns:resolution", ns).text
                duration = resolution_map.get(resolution, 60)

                for point in period.findall("ns:Point", ns):
                    position = int(point.find("ns:position", ns).text) - 1
                    price_mwh = float(point.find("ns:price.amount", ns).text)
                    price_kwh = price_mwh / 1000.0

                    entries.append(
                        Marketprice(
                            start_time=start_dt
                            + timedelta(minutes=position * duration),
                            duration=duration,
                            price=round(price_kwh, 6),
                        )
                    )
        return entries
