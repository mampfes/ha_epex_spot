"""Constants for the EPEX Spot Sensor integration."""
from enum import Enum

DOMAIN = "epex_spot_sensor"

CONF_EARLIEST_START_TIME = "earliest_start_time"
CONF_LATEST_END_TIME = "latest_end_time"
CONF_DURATION = "duration"

CONF_INTERVAL_MODE = "interval_mode"


class IntervalModes(Enum):
    """Work modes for config validation."""

    CONTIGUOUS = "contiguous"
    INTERMITTENT = "intermittent"


CONF_PRICE_MODE = "price_mode"


class PriceModes(Enum):
    """Price modes for config validation."""

    CHEAPEST = "cheapest"
    MOST_EXPENSIVE = "most_expensive"


ATTR_INTERVAL_ENABLED = "enabled"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_RANK = "rank"
ATTR_DATA = "data"
ATTR_PRICE_PER_MWH = "price_per_mwh"
ATTR_PRICE_PER_KWH = "price_per_kwh"
