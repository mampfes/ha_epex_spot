import logging
from statistics import median

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_BUY_VOLUME_MWH,
    ATTR_DATA,
    ATTR_END_TIME,
    ATTR_QUANTILE,
    ATTR_RANK,
    ATTR_SELL_VOLUME_MWH,
    ATTR_START_TIME,
    ATTR_VOLUME_MWH,
    CONF_SOURCE,
    CONF_SOURCE_EPEX_SPOT_WEB,
    DOMAIN,
)
from . import EpexSpotEntity, EpexSpotDataUpdateCoordinator as DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up platform for a new integration.

    Called by the HA framework after async_setup_platforms has been called
    during initialization of a new integration.
    """
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        EpexSpotPriceSensorEntity(coordinator),
        EpexSpotNetPriceSensorEntity(coordinator),
        EpexSpotRankSensorEntity(coordinator),
        EpexSpotQuantileSensorEntity(coordinator),
        EpexSpotLowestPriceSensorEntity(coordinator),
        EpexSpotHighestPriceSensorEntity(coordinator),
        EpexSpotAveragePriceSensorEntity(coordinator),
        EpexSpotMedianPriceSensorEntity(coordinator),
    ]

    if config_entry.data[CONF_SOURCE] == CONF_SOURCE_EPEX_SPOT_WEB:
        entities.extend(
            [
                EpexSpotBuyVolumeSensorEntity(coordinator),
                EpexSpotSellVolumeSensorEntity(coordinator),
                EpexSpotVolumeSensorEntity(coordinator),
            ]
        )

    async_add_entities(entities)


class EpexSpotPriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Price",
        name="Price",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        return self._source.marketdata_now.price_per_kwh

    @property
    def extra_state_attributes(self):
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                self._localized.attr_name_per_kwh: e.price_per_kwh,
            }
            for e in self._source.marketdata
        ]

        return {
            ATTR_DATA: data,
            self._localized.attr_name_per_kwh: self.native_value,
        }


class EpexSpotNetPriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Net Price",
        name="Net Price",
        suggested_display_precision=6,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        return self._source.to_net_price(self._source.marketdata_now.price_per_kwh)

    @property
    def extra_state_attributes(self):
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                self._localized.attr_name_per_kwh: self._source.to_net_price(
                    e.price_per_kwh
                ),
            }
            for e in self._source.marketdata
        ]

        return {ATTR_DATA: data}


class EpexSpotBuyVolumeSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Buy Volume",
        name="Buy Volume",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement="MWh",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        return self._source.marketdata_now.buy_volume_mwh

    @property
    def extra_state_attributes(self):
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_BUY_VOLUME_MWH: e.buy_volume_mwh,
            }
            for e in self._source.marketdata
        ]

        return {ATTR_DATA: data}


class EpexSpotSellVolumeSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Sell Volume",
        name="Sell Volume",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement="MWh",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        return self._source.marketdata_now.sell_volume_mwh

    @property
    def extra_state_attributes(self):
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_SELL_VOLUME_MWH: e.sell_volume_mwh,
            }
            for e in self._source.marketdata
        ]

        return {ATTR_DATA: data}


class EpexSpotVolumeSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Volume",
        name="Volume",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement="MWh",
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        return self._source.marketdata_now.volume_mwh

    @property
    def extra_state_attributes(self):
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_VOLUME_MWH: e.volume_mwh,
            }
            for e in self._source.marketdata
        ]

        return {ATTR_DATA: data}


class EpexSpotRankSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Rank",
        name="Rank",
        native_unit_of_measurement="",
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        return [e.price_per_kwh for e in self._source.sorted_marketdata_today].index(
            self._source.marketdata_now.price_per_kwh
        )

    @property
    def extra_state_attributes(self):
        sorted_prices = [e.price_per_kwh for e in self._source.sorted_marketdata_today]
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_RANK: sorted_prices.index(e.price_per_kwh),
            }
            for e in self._source.sorted_marketdata_today
        ]

        return {ATTR_DATA: data}


class EpexSpotQuantileSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Quantile",
        name="Quantile",
        native_unit_of_measurement="",
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)

    @property
    def native_value(self) -> StateType:
        current_price = self._source.marketdata_now.price_per_kwh
        min_price = self._source.sorted_marketdata_today[0].price_per_kwh
        max_price = self._source.sorted_marketdata_today[-1].price_per_kwh
        return (current_price - min_price) / (max_price - min_price)

    @property
    def extra_state_attributes(self):
        min_price = self._source.sorted_marketdata_today[0].price_per_kwh
        max_price = self._source.sorted_marketdata_today[-1].price_per_kwh
        data = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_QUANTILE: (e.price_per_kwh - min_price) / (max_price - min_price),
            }
            for e in self._source.sorted_marketdata_today
        ]

        return {ATTR_DATA: data}


class EpexSpotLowestPriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Lowest Price",
        name="Lowest Price",
        suggested_display_precision=6,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        min = self._source.sorted_marketdata_today[0]
        return min.price_per_kwh

    @property
    def extra_state_attributes(self):
        min = self._source.sorted_marketdata_today[0]
        return {
            ATTR_START_TIME: dt_util.as_local(min.start_time).isoformat(),
            ATTR_END_TIME: dt_util.as_local(min.end_time).isoformat(),
            self._localized.attr_name_per_kwh: self.native_value,
        }


class EpexSpotHighestPriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Highest Price",
        name="Highest Price",
        suggested_display_precision=6,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        max = self._source.sorted_marketdata_today[-1]
        return max.price_per_kwh

    @property
    def extra_state_attributes(self):
        max = self._source.sorted_marketdata_today[-1]
        return {
            ATTR_START_TIME: dt_util.as_local(max.start_time).isoformat(),
            ATTR_END_TIME: dt_util.as_local(max.end_time).isoformat(),
            self._localized.attr_name_per_kwh: self.native_value,
        }


class EpexSpotAveragePriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Average Price",
        name="Average Price",
        suggested_display_precision=6,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        s = sum(e.price_per_kwh for e in self._source.sorted_marketdata_today)
        return s / len(self._source.sorted_marketdata_today)

    @property
    def extra_state_attributes(self):
        return {
            self._localized.attr_name_per_kwh: self.native_value,
        }


class EpexSpotMedianPriceSensorEntity(EpexSpotEntity, SensorEntity):
    """Home Assistant sensor containing all EPEX spot data."""

    entity_description = SensorEntityDescription(
        key="Median Price",
        name="Median Price",
        suggested_display_precision=6,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: DataUpdateCoordinator):
        super().__init__(coordinator, self.entity_description)
        self._attr_icon = self._localized.icon
        self._attr_native_unit_of_measurement = self._localized.uom_per_kwh

    @property
    def native_value(self) -> StateType:
        return median([e.price_per_kwh for e in self._source.sorted_marketdata_today])

    @property
    def extra_state_attributes(self):
        return {
            self._localized.attr_name_per_kwh: self.native_value,
        }
