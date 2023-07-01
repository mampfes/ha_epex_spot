import logging
from datetime import datetime, timedelta, timezone

import requests

# from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)

MARKET_AREA_MAP = {
    "DE-LU": 4169,
    "Anrainer DE-LU": 5078,
    "BE": 4996,
    "NO2": 4997,
    "AT": 4170,
    "DK1": 252,
    "DK2": 253,
    "FR": 254,
    "IT (North)": 255,
    "NL": 256,
    "PL": 257,
    "CH": 259,
    "SI": 260,
    "CZ": 261,
    "HU": 262,
}


class Marketprice:
    UOM_EUR_PER_MWh = "EUR/MWh"

    def __init__(self, data):
        self._start_time = datetime.fromtimestamp(data[0] / 1000, tz=timezone.utc)
        self._end_time = self._start_time + timedelta(
            hours=1
        )  # TODO: this will not work for 1/2 updates

        self._price_eur_per_mwh = float(data[1])

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_eur_per_mwh} {self.UOM_EUR_PER_MWh})"

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_eur_per_mwh(self):
        return self._price_eur_per_mwh

    @property
    def price_ct_per_kwh(self):
        return self._price_eur_per_mwh / 10


class SMARD:
    URL = "https://www.smard.de/app/chart_data"

    MARKET_AREAS = MARKET_AREA_MAP.keys()

    def __init__(self, market_area):
        self._market_area = market_area
        self._marketdata = []

    @property
    def name(self):
        return "SMARD.de"

    @property
    def market_area(self):
        return self._market_area

    @property
    def marketdata(self):
        return self._marketdata

    def fetch(self):
        data = self._fetch_data()
        self._marketdata = self._extract_marketdata(data["series"])

    def _fetch_data(self):
        smard_filter = MARKET_AREA_MAP[self._market_area]
        smard_region = "DE"  # self._market_area
        smard_resolution = "hour"

        # get available timestamps for given market area
        url = f"{self.URL}/{smard_filter}/{smard_region}/index_{smard_resolution}.json"
        r = requests.get(url)
        r.raise_for_status()

        j = r.json()
        latest_timestamp = j["timestamps"][-1]

        # get available data
        url = f"{self.URL}/{smard_filter}/{smard_region}/{smard_filter}_{smard_region}_{smard_resolution}_{latest_timestamp}.json"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data:
            if entry[1] is not None:
                entries.append(Marketprice(entry))
        return entries[-72:]  # limit number of entries to protect HA recorder
