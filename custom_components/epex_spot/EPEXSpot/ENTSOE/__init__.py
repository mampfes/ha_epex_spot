"""ENTSO-E Transparency API Client."""

from datetime import datetime, timedelta, timezone
import enum
from gettext import find
import logging
import aiohttp
import xml.etree.ElementTree as ET
from typing import List

# Replace this import with your actual Marketprice & compress_marketdata implementations
from ...common import Marketprice, average_marketdata

_LOGGER = logging.getLogger(__name__)

MARKET_AREA_MAP = {
    "AT": "10YAT-APG------L",
    "BE": "10YBE----------2",
    "BG": "10YCA-BULGARIA-R",
    "CH": "10YCH-SWISSGRIDZ",
    "CZ": "10YCZ-CEPS-----N",
    "DE-LU": "10Y1001A1001A82H",
    "DK1": "10YDK-1--------W",
    "DK2": "10YDK-2--------M",
    "EE": "10Y1001A1001A39I",
    "ERI": "38YNPSRUIMP----S",
    "ES": "10YES-REE------0",
    "FI": "10YFI-1--------U",
    "FR": "10YFR-RTE------C",
    "GR": "10YGR-HTSO-----Y",
    "HR": "10YHR-HEP------M",
    "HU": "10YHU-MAVIR----U",
    "IT-Calabria": "10Y1001C--00096J",
    "IT-Centre-North": "10Y1001A1001A70O",
    "IT-Centre-South": "10Y1001A1001A71M",
    "IT-North": "10Y1001A1001A73I",
    "IT-SACOAC": "10Y1001A1001A885",
    "IT-SACODC": "10Y1001A1001A893",
    "IT-Sardinia": "10Y1001A1001A74G",
    "IT-Sicily": "10Y1001A1001A75E",
    "IT-South": "10Y1001A1001A788",
    "LT": "10YLT-1001A0008Q",
    "LV": "10YLV-1001A00074",
    "ME": "10YCS-CG-TSO---S",
    "MK": "10YMK-MEPSO----8",
    "NL": "10YNL----------L",
    "NO1": "10YNO-1--------2",
    "NO2": "10YNO-2--------T",
    "NO2NSL": "50Y0JVU59B4JWQCU",
    "NO3": "10YNO-3--------J",
    "NO4": "10YNO-4--------9",
    "NO5": "10Y1001A1001A48H",
    "PL": "10YPL-AREA-----S",
    "PT": "10YPT-REN------W",
    "RO": "10YRO-TEL------P",
    "RS": "10YCS-SERBIATSOV",
    "SE1": "10Y1001A1001A44P",
    "SE2": "10Y1001A1001A45N",
    "SE3": "10Y1001A1001A46L",
    "SE4": "10Y1001A1001A47J",
    "SI": "10YSI-ELES-----O",
    "SK": "10YSK-SEPS-----K",
    "UA-IPS": "10Y1001C--000182",
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
        if self._duration != 15:
            logging.debug("Averaging market data... from 15 to", self._duration)
            self._marketdata = average_marketdata(self._marketdata, self._duration)

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
        """Extract prices (€/MWh → €/kWh) from XML, filling missing positions."""
        entries: List[Marketprice] = []
        root = ET.fromstring(xml_text)
        ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}

        resolution_map = {"PT15M": 15, "PT60M": 60, "PT30M": 30}

        all_timeseries = root.findall("ns:TimeSeries", ns)

        sequences = []
        for ts in all_timeseries:
            seq = ts.find(
                "ns:classificationSequence_AttributeInstanceComponent.position", ns
            )
            if seq is not None:
                sequences.append(seq.text)

        # Filter SDAC sequence==1 if present
        if sequences:
            filtered_timeseries = []
            for ts in all_timeseries:
                seq_el = ts.find(
                    "ns:classificationSequence_AttributeInstanceComponent.position", ns
                )
                if seq_el is not None and seq_el.text == "1":
                    filtered_timeseries.append(ts)
            timeseries_list = filtered_timeseries
        else:
            timeseries_list = all_timeseries

        for timeseries in timeseries_list:
            for period in timeseries.findall("ns:Period", ns):
                time_interval = period.find("ns:timeInterval", ns)
                start_str = time_interval.find("ns:start", ns).text
                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%MZ").replace(
                    tzinfo=timezone.utc
                )

                resolution = period.find("ns:resolution", ns).text
                duration = resolution_map.get(resolution, 60)

                prev_price_kwh = None
                prev_position = None

                for point in period.findall("ns:Point", ns):
                    position = int(point.find("ns:position", ns).text) - 1
                    price_mwh = float(point.find("ns:price.amount", ns).text)
                    price_kwh = price_mwh / 1000.0

                    if prev_position is not None and position > prev_position + 1:
                        for missing_pos in range(prev_position + 1, position):
                            logging.debug(
                                f"Filling missing position {missing_pos} using previous price {prev_price_kwh} €/kWh"
                            )
                            entries.append(
                                Marketprice(
                                    start_time=start_dt
                                    + timedelta(minutes=missing_pos * duration),
                                    duration=duration,
                                    price=round(prev_price_kwh, 6),
                                )
                            )

                    entries.append(
                        Marketprice(
                            start_time=start_dt
                            + timedelta(minutes=position * duration),
                            duration=duration,
                            price=round(price_kwh, 6),
                        )
                    )

                    prev_price_kwh = price_kwh
                    prev_position = position

        return entries
