"""Constants for the component."""

# Component domain, used to store component data in hass data.
DOMAIN = "epex_spot"

CONF_SOURCE = "source"
CONF_MARKET_AREA = "market_area"

# possible values for CONF_SOURCE
CONF_SOURCE_AWATTAR = "Awattar"
CONF_SOURCE_EPEX_SPOT_WEB = "EPEX Spot Web Scraper"

UPDATE_SENSORS_SIGNAL = f"{DOMAIN}_update_sensors_signal"