import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (ATTR_IDENTIFIERS, ATTR_MANUFACTURER,
                                 ATTR_MODEL, ATTR_NAME)
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.util.dt import utcnow

from .const import CONF_SOURCE, CONF_SOURCE_EPEX_SPOT_WEB, DOMAIN

ATTR_DATA = "data"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up platform for a new integration.

    Called by the HA framework after async_setup_platforms has been called
    during initialization of a new integration.
    """
    shell = hass.data[DOMAIN]
    unique_id = config_entry.unique_id

    entities = []

    entities.append(
        EpexSpotPriceSensorEntity(hass, shell.get_source(unique_id), unique_id)
    )
    if config_entry.data[CONF_SOURCE] == CONF_SOURCE_EPEX_SPOT_WEB:
        entities.append(
            EpexSpotBuyVolumeSensorEntity(hass, shell.get_source(unique_id), unique_id)
        )
        entities.append(
            EpexSpotSellVolumeSensorEntity(hass, shell.get_source(unique_id), unique_id)
        )
        entities.append(
            EpexSpotVolumeSensorEntity(hass, shell.get_source(unique_id), unique_id)
        )

    async_add_entities(entities)


class EpexSpotSensorEntity(SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        self._source = source
        self._value = None

        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, f"{source.name} {source.market_area}")},
            ATTR_NAME: "EPEX Spot Data",
            ATTR_MANUFACTURER: source.name,
            ATTR_MODEL: source.market_area,
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def available(self):
        """Return true if value is valid."""
        return self._value is not None

    @property
    def native_value(self):
        """Return the value of the entity."""
        return self._value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "EUR/MWh"


class EpexSpotPriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source, unique_id):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{unique_id} Price"
        self._attr_name = f"EPEX Spot {source.market_area} Price"
        self._attr_icon = "mdi:currency-eur"

    async def async_update(self):
        """Update the value of the entity."""
        now = utcnow()

        self._value = None

        data = []

        for e in self._source.marketprices:
            # find current value
            if e.start_time <= now and e.end_time > now:
                self._value = e.price_eur_per_mwh

            info = {
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "price_eur_per_mwh": e.price_eur_per_mwh,
            }
            data.append(info)

        attributes = {
            ATTR_DATA: data,
        }
        self._attr_extra_state_attributes = attributes

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "EUR/MWh"


class EpexSpotBuyVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source, unique_id):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{unique_id} Buy Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Buy Volume"
        self._attr_icon = "mdi:lightning-bolt"

    async def async_update(self):
        """Update the value of the entity."""
        now = utcnow()

        self._value = None

        data = []

        for e in self._source.marketprices:
            # find current value
            if e.start_time <= now and e.end_time > now:
                self._value = e.buy_volume_mwh

            info = {
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "buy_volume_mwh": e.buy_volume_mwh,
            }
            data.append(info)

        attributes = {
            ATTR_DATA: data,
        }
        self._attr_extra_state_attributes = attributes

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "MWh"


class EpexSpotSellVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source, unique_id):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{unique_id} Sell Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Sell Volume"
        self._attr_icon = "mdi:lightning-bolt"

    async def async_update(self):
        """Update the value of the entity."""
        now = utcnow()

        self._value = None

        data = []

        for e in self._source.marketprices:
            # find current value
            if e.start_time <= now and e.end_time > now:
                self._value = e.sell_volume_mwh

            info = {
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "sell_volume_mwh": e.sell_volume_mwh,
            }
            data.append(info)

        attributes = {
            ATTR_DATA: data,
        }
        self._attr_extra_state_attributes = attributes

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "MWh"


class EpexSpotVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source, unique_id):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{unique_id} Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Volume"
        self._attr_icon = "mdi:lightning-bolt"

    async def async_update(self):
        """Update the value of the entity."""
        now = utcnow()

        self._value = None

        data = []

        for e in self._source.marketprices:
            # find current value
            if e.start_time <= now and e.end_time > now:
                self._value = e.volume_mwh

            info = {
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "volume_mwh": e.volume_mwh,
            }
            data.append(info)

        attributes = {
            ATTR_DATA: data,
        }
        self._attr_extra_state_attributes = attributes

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "MWh"
