"""Spotty Energie API Client.

Spotty Energie (https://www.spottyenergie.at) offers a per-customer endpoint
returning the day-ahead prices in 15 minute resolution for the current and the
next day. Prices are given in ct/kWh and the payload neither contains an end
timestamp nor a declared resolution, so both have to be derived from the data.

The endpoint is documented in the Spotty help center
(https://hilfe.spotty.app/kb/article/96-schnittstelle-marktpreis-api/). It is
addressed by a contract id (UUID) which is a secret and therefore never logged.
"""

import asyncio
from datetime import datetime, timedelta
import json
import logging
import math
from typing import Any, List
from uuid import UUID
from zoneinfo import ZoneInfo

import aiohttp

from ...common import Marketprice, average_marketdata
from ...const import TIMEZONE_SPOTTY

_LOGGER = logging.getLogger(__name__)

API_URL = "https://at.spotty.app/api/prices/MARKET/{contract_id}"
TIMEZONE = ZoneInfo(TIMEZONE_SPOTTY)


class SpottyError(Exception):
    """Error while talking to the Spotty API."""


class SpottyContractError(SpottyError):
    """The configured contract id is unknown or not authorized."""


class SpottySeriesError(SpottyError):
    """The contract does not include the MARKET price series."""


class Spotty:
    MARKET_AREAS = ("at",)
    SUPPORTED_DURATIONS = (
        15,
        60,
    )

    def __init__(
        self,
        market_area: str,
        duration: int,
        session: aiohttp.ClientSession,
        token: str,
    ):
        if market_area not in self.MARKET_AREAS:
            raise ValueError(f"Unsupported bidding zone: {market_area}")

        if duration not in self.SUPPORTED_DURATIONS:
            raise ValueError(f"Unsupported duration: {duration}")

        # The contract id is used as part of the request URL, so it is
        # validated and normalized instead of being taken over verbatim.
        try:
            contract_id = str(UUID(str(token).strip()))
        except (AttributeError, TypeError, ValueError) as err:
            raise ValueError("Invalid Spotty contract id") from err

        self._session = session
        self._market_area = market_area
        self._duration = duration
        self._contract_id = contract_id
        self._marketdata: List[Marketprice] = []

    @property
    def name(self):
        return "Spotty Energie API"

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
        payload = await self._fetch_prices()

        marketdata = self._extract_marketdata(payload)
        base_duration = self._detect_duration(
            [entry.start_time for entry in marketdata]
        )

        if self._duration < base_duration:
            _LOGGER.warning(
                "Requested interval of %d minutes is shorter than the %d minute "
                "interval provided by Spotty, keeping the original interval",
                self._duration,
                base_duration,
            )
        elif self._duration > base_duration:
            group_size = self._duration // base_duration
            if group_size > 1:
                if len(marketdata) % group_size:
                    # average_marketdata() groups by index, so an incomplete
                    # trailing group would produce a wrong average.
                    dropped = len(marketdata) % group_size
                    _LOGGER.warning(
                        "Dropping %d trailing slot(s) which do not fill a "
                        "complete %d minute interval",
                        dropped,
                        self._duration,
                    )
                    marketdata = marketdata[: len(marketdata) - dropped]

                base_slots = marketdata
                marketdata = average_marketdata(base_slots, self._duration)

                # average_marketdata() derives the end time from the slot
                # length, which is ambiguous when DST ends. The end of the
                # averaged slot is the end of its last base slot.
                for index, entry in enumerate(marketdata):
                    last_slot = base_slots[
                        min((index + 1) * group_size, len(base_slots)) - 1
                    ]
                    entry.set_end_time(last_slot.end_time)

        self._marketdata = marketdata

    async def _fetch_prices(self) -> Any:
        url = API_URL.format(contract_id=self._contract_id)

        try:
            async with self._session.get(url, params={"timezone": "at"}) as response:
                status = response.status
                body = await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SpottyError("Error connecting to Spotty API") from err

        if status == 404:
            raise SpottySeriesError(
                "The configured Spotty contract does not include the MARKET "
                "price series"
            )

        if status in (401, 403):
            raise SpottyContractError("Spotty rejected the configured contract id")

        if status != 200:
            raise SpottyError(f"Spotty API returned HTTP status {status}")

        try:
            return json.loads(body)
        except ValueError as err:
            # Spotty answers an unknown contract id with HTTP 200 and a plain
            # text body ("Kein Abonnement gefunden ..."). The body echoes the
            # contract id, which is a secret, so it must not be logged.
            raise SpottyContractError(
                "Spotty did not return price data, check the contract id"
            ) from err

    @staticmethod
    def _extract_marketdata(payload: Any) -> List[Marketprice]:
        if not isinstance(payload, list) or not payload:
            raise SpottyError("Spotty API returned no price data")

        parsed = []
        for item in payload:
            if not isinstance(item, dict):
                raise SpottyError("Spotty API returned an unexpected payload")

            try:
                start_time = datetime.fromisoformat(str(item["from"]))
                price = float(item["price"])
            except (KeyError, TypeError, ValueError) as err:
                raise SpottyError(
                    "Spotty API returned an unexpected price entry"
                ) from err

            if start_time.tzinfo is None:
                raise SpottyError("Spotty API returned a timestamp without timezone")

            if not math.isfinite(price):
                raise SpottyError("Spotty API returned a non-finite price")

            parsed.append((start_time.astimezone(TIMEZONE), price))

        parsed.sort(key=lambda entry: entry[0].timestamp())

        for (start, _), (next_start, _) in zip(parsed, parsed[1:]):
            # Comparing datetimes of the same zone compares their wall clock,
            # which is ambiguous when DST ends (02:00 exists twice).
            if next_start.timestamp() <= start.timestamp():
                raise SpottyError("Spotty API returned unsorted price entries")

        base_duration = Spotty._detect_duration([entry[0] for entry in parsed])
        marketdata = [
            Marketprice(
                start_time=start_time,
                duration=base_duration,
                price=round(price / 100, 6),
            )
            for start_time, price in parsed
        ]

        # Spotty does not deliver an end timestamp. The end of a slot is the
        # start of the following one; the last slot inherits the length of its
        # predecessor. Using the provided offsets keeps this correct on DST
        # transition days, which have 92 resp. 100 slots instead of 96.
        for entry, next_entry in zip(marketdata, marketdata[1:]):
            entry.set_end_time(next_entry.start_time)

        if len(marketdata) > 1:
            last_duration = timedelta(
                seconds=marketdata[-1].start_time.timestamp()
                - marketdata[-2].start_time.timestamp()
            )
            marketdata[-1].set_end_time(marketdata[-1].start_time + last_duration)

        return marketdata

    @staticmethod
    def _detect_duration(starts: List[datetime]) -> int:
        """Return the smallest distance between two consecutive starts."""
        deltas = [
            int((next_start.timestamp() - start.timestamp()) // 60)
            for start, next_start in zip(starts, starts[1:])
        ]

        if not deltas:
            return 15

        # Smallest distance is the resolution of the payload; gaps caused by
        # missing slots must not raise the assumed resolution.
        return min(deltas)
