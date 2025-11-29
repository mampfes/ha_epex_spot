"""Constants for the component."""

# Component domain, used to store component data in hass data.
DOMAIN = "epex_spot"

ATTR_DATA = "data"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_BUY_VOLUME_MWH = "buy_volume_mwh"
ATTR_SELL_VOLUME_MWH = "sell_volume_mwh"
ATTR_VOLUME_MWH = "volume_mwh"
ATTR_RANK = "rank"
ATTR_QUANTILE = "quantile"
ATTR_PRICE_PER_KWH = "price_per_kwh"

CONFIG_VERSION = 2
CONF_SOURCE = "source"
CONF_MARKET_AREA = "market_area"
CONF_TOKEN = "token"

# possible values for CONF_SOURCE
CONF_SOURCE_AWATTAR = "Awattar"
CONF_SOURCE_SMARD_DE = "SMARD.de"
CONF_SOURCE_SMARTENERGY = "smartENERGY.at"
CONF_SOURCE_TIBBER = "Tibber"
CONF_SOURCE_ENERGYFORECAST = "Energyforecast.de"
CONF_SOURCE_ENTSOE = "ENTSO-E-Transparency"
CONF_SOURCE_ENERGYCHARTS = "Energy-Charts.info"

# configuration options for total price calculation
CONF_SURCHARGE_PERC = "percentage_surcharge"
CONF_SURCHARGE_ABS = "absolute_surcharge"
CONF_TAX = "tax"

# service call
CONF_EARLIEST_START_TIME = "earliest_start"
CONF_EARLIEST_START_POST = "earliest_start_post"
CONF_LATEST_END_TIME = "latest_end"
CONF_LATEST_END_POST = "latest_end_post"
CONF_DURATION = "duration"

DEFAULT_SURCHARGE_PERC = 3.0
DEFAULT_SURCHARGE_ABS = 0.1193
DEFAULT_TAX = 19.0
DEFAULT_DURATION = 60

EMPTY_EXTREME_PRICE_INTERVAL_RESP = {
    "start": None,
    "end": None,
    "market_price_per_kwh": None,
    "total_price_per_kwh": None,
}

UOM_EUR_PER_KWH = "€/kWh"
UOM_MWH = "MWh"

EUR_PER_MWH = "EUR/MWh"
CT_PER_KWH = "ct/kWh"


TIBBER_DEMO_TOKEN = "3A77EECF61BD445F47241A5A36202185C35AF3AF58609E19B53F3A8872AD7BE1-1"
