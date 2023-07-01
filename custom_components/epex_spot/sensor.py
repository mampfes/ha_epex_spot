import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (ATTR_IDENTIFIERS, ATTR_MANUFACTURER,
                                 ATTR_MODEL, ATTR_NAME)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (CONF_SOURCE, CONF_SOURCE_EPEX_SPOT_WEB, DOMAIN,
                    UPDATE_SENSORS_SIGNAL)

ATTR_DATA = "data"
ATTR_PRICE_EUR_PER_MWH = "price_eur_per_mwh"
ATTR_PRICE_CT_PER_KWH = "price_ct_per_kwh"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up platform for a new integration.

    Called by the HA framework after async_setup_platforms has been called
    during initialization of a new integration.
    """
    shell = hass.data[DOMAIN]
    unique_id = config_entry.unique_id

    entities = [
        EpexSpotPriceSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotNetPriceSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotRankSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotQuantileSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotLowestPriceSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotHighestPriceSensorEntity(hass, shell.get_source(unique_id)),
        EpexSpotAveragePriceSensorEntity(hass, shell.get_source(unique_id)),
    ]

    if config_entry.data[CONF_SOURCE] == CONF_SOURCE_EPEX_SPOT_WEB:
        entities.extend(
            [
                EpexSpotBuyVolumeSensorEntity(hass, shell.get_source(unique_id)),
                EpexSpotSellVolumeSensorEntity(hass, shell.get_source(unique_id)),
                EpexSpotVolumeSensorEntity(hass, shell.get_source(unique_id)),
            ]
        )

    async_add_entities(entities)


class EpexSpotSensorEntity(SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        self._source = source

        self._attr_should_poll = False
        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, f"{source.name} {source.market_area}")},
            ATTR_NAME: "EPEX Spot Data",
            ATTR_MANUFACTURER: source.name,
            ATTR_MODEL: source.market_area,
            "entry_type": DeviceEntryType.SERVICE,
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, UPDATE_SENSORS_SIGNAL, self._on_update_sensor_x
            )
        )

        self._on_update_sensor_x()

    @callback
    def _on_update_sensor_x(self):
        try:
            self._on_update_sensor()
            self._attr_available = True
        except Exception:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = None

        self.async_write_ha_state()

    def to_net_price(self, price_eur_per_mwh):
        return self._source.to_net_price(price_eur_per_mwh)


def to_ct_per_kwh(price_eur_per_mwh):
    return price_eur_per_mwh / 10


class EpexSpotPriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Price"
        self._attr_name = f"EPEX Spot {source.market_area} Price"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "EUR/MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = self._source.marketdata_now.price_eur_per_mwh

        data = [
            {
                ATTR_START_TIME: e.start_time.isoformat(),
                ATTR_END_TIME: e.end_time.isoformat(),
                ATTR_PRICE_EUR_PER_MWH: e.price_eur_per_mwh,
                ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(e.price_eur_per_mwh),
            }
            for e in self._source.marketdata
        ]

        self._attr_extra_state_attributes = {
            ATTR_DATA: data,
            ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(self._attr_native_value),
        }


class EpexSpotNetPriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Net Price"
        self._attr_name = f"EPEX Spot {source.market_area} Net Price"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "ct/kWh"
        self._attr_suggested_display_precision = 2

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = self.to_net_price(
            self._source.marketdata_now.price_eur_per_mwh
        )

        data = [
            {
                ATTR_START_TIME: e.start_time.isoformat(),
                ATTR_END_TIME: e.end_time.isoformat(),
                ATTR_PRICE_CT_PER_KWH: self.to_net_price(e.price_eur_per_mwh),
            }
            for e in self._source.marketdata
        ]

        self._attr_extra_state_attributes = {ATTR_DATA: data}


class EpexSpotBuyVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Buy Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Buy Volume"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = self._source.marketdata_now.buy_volume_mwh

        data = [
            {
                ATTR_START_TIME: e.start_time.isoformat(),
                ATTR_END_TIME: e.end_time.isoformat(),
                "buy_volume_mwh": e.buy_volume_mwh,
            }
            for e in self._source.marketdata
        ]

        self._attr_extra_state_attributes = {
            ATTR_DATA: data,
        }


class EpexSpotSellVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Sell Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Sell Volume"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = self._source.marketdata_now.sell_volume_mwh

        data = [
            {
                ATTR_START_TIME: e.start_time.isoformat(),
                ATTR_END_TIME: e.end_time.isoformat(),
                "sell_volume_mwh": e.sell_volume_mwh,
            }
            for e in self._source.marketdata
        ]

        self._attr_extra_state_attributes = {
            ATTR_DATA: data,
        }


class EpexSpotVolumeSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Volume"
        self._attr_name = f"EPEX Spot {source.market_area} Volume"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = self._source.marketdata_now.volume_mwh

        data = [
            {
                ATTR_START_TIME: e.start_time.isoformat(),
                ATTR_END_TIME: e.end_time.isoformat(),
                "volume_mwh": e.volume_mwh,
            }
            for e in self._source.marketdata
        ]

        self._attr_extra_state_attributes = {
            ATTR_DATA: data,
        }


class EpexSpotRankSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Rank"
        self._attr_name = f"EPEX Spot {source.market_area} Rank"
        self._attr_native_unit_of_measurement = ""

    def _on_update_sensor(self):
        """Update the value of the entity."""
        self._attr_native_value = [
            e.price_eur_per_mwh for e in self._source.sorted_marketdata_today
        ].index(self._source.marketdata_now.price_eur_per_mwh)


class EpexSpotQuantileSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Quantile"
        self._attr_name = f"EPEX Spot {source.market_area} Quantile"
        self._attr_suggested_display_precision = 2
        self._attr_native_unit_of_measurement = ""

    def _on_update_sensor(self):
        """Update the value of the entity."""
        current_price = self._source.marketdata_now.price_eur_per_mwh
        min_price = self._source.sorted_marketdata_today[0].price_eur_per_mwh
        max_price = self._source.sorted_marketdata_today[-1].price_eur_per_mwh
        self._attr_native_value = (current_price - min_price) / (max_price - min_price)


class EpexSpotLowestPriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Lowest Price"
        self._attr_name = f"EPEX Spot {source.market_area} Lowest Price"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "EUR/MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        min = self._source.sorted_marketdata_today[0]
        self._attr_native_value = min.price_eur_per_mwh

        attributes = {
            ATTR_START_TIME: min.start_time.isoformat(),
            ATTR_END_TIME: min.end_time.isoformat(),
            ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(self._attr_native_value),
        }
        self._attr_extra_state_attributes = attributes


class EpexSpotHighestPriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Highest Price"
        self._attr_name = f"EPEX Spot {source.market_area} Highest Price"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "EUR/MWh"

    def _on_update_sensor(self):
        """Update the value of the entity."""
        max = self._source.sorted_marketdata_today[-1]
        self._attr_native_value = max.price_eur_per_mwh

        attributes = {
            ATTR_START_TIME: max.start_time.isoformat(),
            ATTR_END_TIME: max.end_time.isoformat(),
            ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(self._attr_native_value),
        }
        self._attr_extra_state_attributes = attributes


class EpexSpotAveragePriceSensorEntity(EpexSpotSensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    def __init__(self, hass, source):
        EpexSpotSensorEntity.__init__(self, hass, source)
        self._attr_unique_id = f"{source.unique_id} Average Price"
        self._attr_name = f"EPEX Spot {source.market_area} Average Price"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_unit_of_measurement = "EUR/MWh"
        self._attr_suggested_display_precision = 2

    def _on_update_sensor(self):
        """Update the value of the entity."""
        s = sum(e.price_eur_per_mwh for e in self._source.sorted_marketdata_today)
        self._attr_native_value = s / len(self._source.sorted_marketdata_today)

        attributes = {
            ATTR_PRICE_CT_PER_KWH: to_ct_per_kwh(self._attr_native_value),
        }
        self._attr_extra_state_attributes = attributes
