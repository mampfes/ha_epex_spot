import logging

from homeassistant.helpers import (
    config_validation as cv,
)

_LOGGER = logging.getLogger(__name__)


class Marketprice:
    def __init__(self, entry):
        self._start_time = cv.datetime(entry["start_time"])
        self._end_time = cv.datetime(entry["end_time"])
        if x := entry.get("price_eur_per_mwh"):
            self._price_eur_per_mwh = x
            self._uom = "EUR/MWh"
        elif x := entry.get("price_gbp_per_mwh"):
            self._price_eur_per_mwh = x
            self._uom = "GBP/MWH"
        else:
            raise KeyError()

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price_eur_per_mwh} {self._uom})"  # noqa: E501

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
    def price_eur_per_mwh_name(self):
        self._price_eur_per_mwh_name


def get_marketdata_from_sensor_attrs(attributes):
    """Convert sensor attributes to market price list."""
    try:
        data = attributes["data"]
    except (KeyError, TypeError):
        _LOGGER.error("price sensor attributes invalid")
        return []

    return [Marketprice(e) for e in data]
