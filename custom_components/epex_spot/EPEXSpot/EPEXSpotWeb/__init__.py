import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import aiohttp
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


def _to_float(v):
    return float(v.replace(",", ""))


def _as_date(v):
    return v.strftime("%Y-%m-%d")


MARKET_AREA_MAP = {
    "GB-30": {"auction": "30-call-GB", "market_area": "GB", "duration": 30},
    "GB": {"auction": "GB", "market_area": "GB", "duration": 60},
    "CH": {"auction": "CH", "market_area": "CH", "duration": 60},
}


class Marketprice:
    UOM_EUR_PER_MWh = "EUR/MWh"
    UOM_MWh = "MWh"

    def __init__(
        self, start_time, end_time, buy_volume_mwh, sell_volume_mwh, volume_mwh, price
    ):
        self._start_time = start_time
        self._end_time = end_time
        self._buy_volume_mwh = _to_float(buy_volume_mwh)
        self._sell_volume_mwh = _to_float(sell_volume_mwh)
        self._volume_mwh = _to_float(volume_mwh)
        self._price_eur_per_mwh = _to_float(price)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, buy_volume_mwh: {self._buy_volume_mwh} {self.UOM_MWh}, sell_volume_mwh: {self._sell_volume_mwh} {self.UOM_MWh}, volume_mwh: {self._volume_mwh} {self.UOM_MWh}, marketprice: {self._price_eur_per_mwh} {self.UOM_EUR_PER_MWh})"  # noqa: E501

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
        return round(self._price_eur_per_mwh / 10, 3)

    @property
    def buy_volume_mwh(self):
        return self._buy_volume_mwh

    @property
    def sell_volume_mwh(self):
        return self._sell_volume_mwh

    @property
    def volume_mwh(self):
        return self._volume_mwh


class EPEXSpotWeb:
    URL = "https://www.epexspot.com/en/market-results"

    MARKET_AREAS = (
        "AT",
        "BE",
        "CH",
        "DE-LU",
        "DK1",
        "DK2",
        "FI",
        "FR",
        "GB",
        "GB-30",
        "NL",
        "NO1",
        "NO2",
        "NO3",
        "NO4",
        "NO5",
        "PL",
        "SE1",
        "SE2",
        "SE3",
        "SE4",
    )

    def __init__(self, market_area, session: aiohttp.ClientSession):
        self._session = session

        self._market_area = market_area
        item = MARKET_AREA_MAP.get(market_area)
        if item is None:
            self._int_market_area = market_area
            self._duration = 60
            self._auction = "MRC"
        else:
            self._int_market_area = item["market_area"]
            self._duration = item["duration"]
            self._auction = item["auction"]

        self._marketdata = []

    @property
    def name(self):
        return "EPEX Spot Web Scraper"

    @property
    def market_area(self):
        return self._market_area

    @property
    def duration(self):
        return self._duration

    @property
    def currency(self):
        return "GBP" if self._market_area.startswith("GB") else "EUR"

    @property
    def marketdata(self):
        return self._marketdata

    async def fetch(self):
        delivery_date = datetime.now(ZoneInfo("Europe/Berlin"))
        # get data for remaining day and upcoming day
        # Data for the upcoming day is typically available at 12:45
        marketdata = await self._fetch_day(delivery_date) + await self._fetch_day(
            delivery_date + timedelta(days=1)
        )
        # overwrite cached marketdata only on success
        self._marketdata = marketdata

    async def _fetch_day(self, delivery_date):
        data = await self._fetch_data(delivery_date)
        invokes = self._extract_invokes(data)

        # check if there is an invoke command with selector ".js-md-widget"
        # because this contains the table with the results
        table_data = invokes.get(".js-md-widget")
        if table_data is None:
            # no data for this day
            return []
        return self._extract_table_data(delivery_date, table_data)

    async def _fetch_data(self, delivery_date):
        trading_date = delivery_date - timedelta(days=1)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"  # noqa
        }
        params = {
            "market_area": self._int_market_area,
            "trading_date": _as_date(trading_date),
            "delivery_date": _as_date(delivery_date),
            "auction": self._auction,
            #          "underlying_year": None,
            "modality": "Auction",
            "sub_modality": "DayAhead",
            #          "technology": None,
            "product": self._duration,
            "data_mode": "table",
            #          "period": None,
            #          "production_period": None,
            "ajax_form": 1,
            #          "_wrapper_format": "html",
            #          "_wrapper_format": "drupal_ajax",
        }
        data = {
            #          "filters[modality]": "Auction",  # optional
            #          "filters[sub_modality]": "DayAhead", # optional
            #          "filters[trading_date]": None,
            #          "filters[delivery_date]": None,
            #          "filters[product]": 60,
            #          "filters[data_mode]": "table",
            #          "filters[market_area]": "AT",
            #          "triggered_element": "filters[market_area]",
            #          "first_triggered_date": None,
            #          "form_build_id": "form-fwlBrltLn1Oh2ak-YdbDNeXBpEPle4M8hmu0omAd4nU",  # noqa: E501
            "form_id": "market_data_filters_form",
            "_triggering_element_name": "submit_js",
            #          "_triggering_element_value": None,
            #          "_drupal_ajax": 1,
            #          "ajax_page_state[theme]": "epex",
            #          "ajax_page_state[theme_token]": None,
            #          "ajax_page_state[libraries]": "bootstrap/popover,bootstrap/tooltip,core/html5shiv,core/jquery.form,epex/global-scripts,epex/global-styling,epex/highcharts,epex_core/data-disclaimer,epex_market_data/filters,epex_market_data/tables,eu_cookie_compliance/eu_cookie_compliance_default,statistics/drupal.statistics,system/base",  # noqa: E501
        }

        async with self._session.post(
            self.URL, headers=headers, params=params, data=data, verify_ssl=True
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_invokes(self, data):
        """Extract invoke commands from JSON response.

        The returned JSON data consist of a list of commands. A command can be
        either an invoke or an insert. This method returns a dictionary with
        all invoke commands. The key is the so called selector, which is
        basically a kind of target.
        """
        invokes = {}
        for entry in data:
            if entry["command"] == "invoke":
                invokes[entry["selector"]] = entry
        return invokes

    def _extract_table_data(self, delivery_date, data):
        """Extract table with results from response.

        The response contains HTML data. The wanted information is stored in
        a table. Each line is an 1 hour window.
        """
        soup = BeautifulSoup(data["args"][0], features="html.parser")

        # the headline contains the current date
        # example: Auction > Day-Ahead > 60min > AT > 24 December 2022
        # headline = soup.find("div", class_="table-container").h2.string

        try:
            table = soup.find("table", class_="table-01 table-length-1")
            body = table.tbody
            rows = body.find_all_next("tr")
        except AttributeError:
            return []  # no data available

        start_time = delivery_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # convert timezone to UTC (and adjust timestamp)
        start_time = start_time.astimezone(timezone.utc)

        marketdata = []
        for row in rows:
            end_time = start_time + timedelta(minutes=self._duration)
            buy_volume_col = row.td
            sell_volume_col = buy_volume_col.find_next_sibling("td")
            volume_col = sell_volume_col.find_next_sibling("td")
            price_col = volume_col.find_next_sibling("td")
            marketdata.append(
                Marketprice(
                    start_time=start_time,
                    end_time=end_time,
                    buy_volume_mwh=buy_volume_col.string,
                    sell_volume_mwh=sell_volume_col.string,
                    volume_mwh=volume_col.string,
                    price=price_col.string,
                )
            )
            start_time = end_time

        return marketdata
