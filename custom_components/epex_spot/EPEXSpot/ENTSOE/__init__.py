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
    "NL": "10YNL----------L",
    "FR": "10YFR-RTE------C",
    "BE": "10YBE----------2",
    "AT": "10YAT-APG------L",
    "DE-LU": "10YCB-GERMANY--8",
    "BRNN": "10Y1001A1001A699",
    "LRI": "43YLRI--------04",
    "MO": "10YMA-ONE------O",
    "ES": "10YES-REE------0",
    "NO3": "10YNO-3--------J",
    "CORS": "10Y1001A1001A893",
    "AUST": "10Y1001A1001A80L",
    "NIR": "10Y1001A1001A016",
    "FOGN": "10Y1001A1001A72K",
    "SE1": "10Y1001A1001A44P",
    "HR": "10YHR-HEP------M",
    "NO1A": "10Y1001A1001A64J",
    "LBE": "10Y1001A1001A56I",
    "NO5": "10Y1001A1001A48H",
    "PRGP": "10Y1001A1001A76C",
    "BSP": "10YSI-ELES-----O",
    "SVIZ": "10Y1001A1001A68B",
    "SUD": "10Y1001A1001A788",
    "BG": "10YCA-BULGARIA-R",
    "ERI": "38YNPSRUIMP----S",
    "LRE": "43YLRE-------008",
    "FRAN": "10Y1001A1001A81J",
    "NORD": "10Y1001A1001A73I",
    "SE2": "10Y1001A1001A45N",
    "GB1": "10Y1001A1001A57G",
    "ROSN": "10Y1001A1001A77A",
    "CNOR": "10Y1001A1001A70O",
    "DK1": "10YDK-1--------W",
    "MALT": "10Y1001A1001A877",
    "NO4": "10YNO-4--------9",
    "MFTV": "10Y1001A1001A90I",
    "NO1": "10YNO-1--------2",
    "SARD": "10Y1001A1001A74G",
    "SE3": "10Y1001A1001A46L",
    "GREC": "10Y1001A1001A66F",
    "LV": "10YLV-1001A00074",
    "GB2": "10Y1001A1001A58E",
    "PT": "10YPT-REN------W",
    "FI": "10YFI-1--------U",
    "CSUD": "10Y1001A1001A71M",
    "COAC": "10Y1001A1001A885",
    "ROI": "10YIE-1001A00010",
    "LBI": "10Y1001A1001A55K",
    "PLA": "10YDOM-PL-SE-LT2",
    "SICI": "10Y1001A1001A75E",
    "SE4": "10Y1001A1001A47J",
    "LT": "10YLT-1001A0008Q",
    "EE": "10Y1001A1001A39I",
    "SLOV": "10Y1001A1001A67D",
    "NO2": "10YNO-2--------T",
    "PL": "10YPL-AREA-----S",
    "FRE": "10YDOM-1001A084H",
    "DK2": "10YDK-2--------M",
    "DK1A": "10YDK-1-------AA",
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
        """Extract prices (€/MWh → €/kWh) from XML."""
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

        if sequences:
            filtered_timeseries = []
            for ts in all_timeseries:
                seq_el = ts.find(
                    "ns:classificationSequence_AttributeInstanceComponent.position", ns
                )
                if seq_el is not None and seq_el.text == "1":  # SDAC
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
