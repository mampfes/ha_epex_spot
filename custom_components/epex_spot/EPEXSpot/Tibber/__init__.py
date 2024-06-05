import aiohttp
from datetime import datetime, timedelta

TIBBER_QUERY = """
{
  viewer {
    homes {
      currentSubscription{
        priceInfo{
          today {
            total
            energy
            tax
            startsAt
            currency
          }
          tomorrow {
            total
            energy
            tax
            startsAt
            currency
          }
        }
      }
    }
  }
}
"""


class Marketprice:
    UOM_CT_PER_kWh = "ct/kWh"

    def __init__(self, data):
        self._start_time = datetime.fromisoformat(data["startsAt"])
        self._end_time = self._start_time + timedelta(hours=1)
        # Tibber already returns the actual net price for the customer
        # so we can use that
        self._price_ct_per_kwh = round(float(data["total"]) * 100, 3)

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_ct_per_kwh} {self.UOM_CT_PER_kWh})"  # noqa: E501

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price_eur_per_mwh(self):
        return round(self._price_ct_per_kwh * 10, 2)

    @property
    def price_ct_per_kwh(self):
        return self._price_ct_per_kwh


class Tibber:
    # DEMO_TOKEN = "5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE"
    #               123456789.123456789.123456789.123456789.123
    URL = "https://api.tibber.com/v1-beta/gql"

    MARKET_AREAS = ("de", "nl", "no", "se")

    def __init__(self, market_area, token: str, session: aiohttp.ClientSession):
        self._session = session
        self._token = token
        self._market_area = market_area
        self._duration = 60
        self._marketdata = []

    @property
    def name(self):
        return "Tibber API v1-beta"

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
        data = await self._fetch_data(self.URL)
        self._marketdata = self._extract_marketdata(
            data["data"]["viewer"]["homes"][0]["currentSubscription"]["priceInfo"]
        )

    async def _fetch_data(self, url):
        async with self._session.post(
            self.URL,
            data={"query": TIBBER_QUERY},
            headers={"Authorization": "Bearer {}".format(self._token)},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    def _extract_marketdata(self, data):
        entries = []
        for entry in data["today"]:
            entries.append(Marketprice(entry))
        for entry in data["tomorrow"]:
            entries.append(Marketprice(entry))
        return entries
