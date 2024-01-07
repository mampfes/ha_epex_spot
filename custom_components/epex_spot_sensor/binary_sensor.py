"""Support for monitoring if a sensor value is below/above a threshold."""
from __future__ import annotations

import logging
from typing import Any

from datetime import time, timedelta, datetime

import homeassistant.util.dt as dt_util
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITY_ID,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.typing import EventType

from .const import (
    ATTR_DATA,
    ATTR_RANK,
    ATTR_INTERVAL_ENABLED,
    ATTR_START_TIME,
    ATTR_END_TIME,
    PriceModes,
    IntervalModes,
    CONF_EARLIEST_START_TIME,
    CONF_LATEST_END_TIME,
    CONF_DURATION,
    CONF_PRICE_MODE,
    CONF_INTERVAL_MODE,
)
from .util import (
    get_marketdata_from_sensor_attrs,
)
from .intermittent_interval import (
    calc_intervals_for_intermittent,
    is_now_in_intervals,
)
from .contiguous_interval import calc_interval_for_contiguous

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize threshold config entry."""
    registry = er.async_get(hass)
    entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_ENTITY_ID]
    )

    source_entity = registry.async_get(entity_id)
    dev_reg = dr.async_get(hass)
    # Resolve source entity device
    if (
        (source_entity is not None)
        and (source_entity.device_id is not None)
        and (
            (
                device := dev_reg.async_get(
                    device_id=source_entity.device_id,
                )
            )
            is not None
        )
    ):
        device_info = DeviceInfo(
            identifiers=device.identifiers,
            connections=device.connections,
        )
    else:
        device_info = None

    async_add_entities(
        [
            BinarySensor(
                hass,
                unique_id=config_entry.entry_id,
                name=config_entry.title,
                entity_id=entity_id,
                earliest_start_time=config_entry.options[CONF_EARLIEST_START_TIME],
                latest_end_time=config_entry.options[CONF_LATEST_END_TIME],
                duration=config_entry.options[CONF_DURATION],
                interval_mode=config_entry.options[CONF_INTERVAL_MODE],
                price_mode=config_entry.options[CONF_PRICE_MODE],
                device_info=device_info,
            )
        ]
    )


class BinarySensor(BinarySensorEntity):
    """Representation of a EPEX Spot binary sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str,
        name: str,
        entity_id: str,
        earliest_start_time: time,
        latest_end_time: time,
        duration: timedelta,
        interval_mode: str,
        price_mode: str,
        device_info: DeviceInfo | None = None,
    ) -> None:
        """Initialize the EPEX Spot binary sensor."""
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._attr_name = name

        # configuration options
        self._entity_id = entity_id
        self._earliest_start_time = cv.time(earliest_start_time)
        self._latest_end_time = cv.time(latest_end_time)
        self._duration = cv.time_period_dict(duration)
        self._price_mode = price_mode
        self._interval_mode = interval_mode

        # price sensor values
        self._sensor_attributes = None

        # calculated values
        self.sensor_value: float | None = None  # TODO: remove
        self._interval_enabled: bool = False
        self._state: bool | None = None
        self._intervals = []

        def _on_price_sensor_state_update() -> None:
            """Handle sensor state changes."""

            # set to unavailable by default
            self._sensor_attributes = None
            self._state = None

            if (new_state := hass.states.get(self._entity_id)) is None:
                # _LOGGER.warning(f"Can't get states of {self._entity_id}")
                return

            try:
                self._sensor_attributes = new_state.attributes
            except (ValueError, TypeError):
                _LOGGER.warning(f"Can't get attributes of {self._entity_id}")
                return

            self._update_state()

        @callback
        def async_price_sensor_state_listener(
            event: EventType[EventStateChangedData],
        ) -> None:
            """Handle sensor state changes."""
            _on_price_sensor_state_update()
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                hass, [entity_id], async_price_sensor_state_listener
            )
        )

        # check every minute for new states
        self.async_on_remove(
            async_track_time_change(hass, async_price_sensor_state_listener, second=0)
        )
        _on_price_sensor_state_update()

    @property
    def is_available(self) -> bool | None:
        """Return true if sensor is available."""
        return self._state is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            ATTR_ENTITY_ID: self._entity_id,
            CONF_EARLIEST_START_TIME: self._earliest_start_time,
            CONF_LATEST_END_TIME: self._latest_end_time,
            CONF_DURATION: str(self._duration),
            CONF_PRICE_MODE: self._price_mode,
            CONF_INTERVAL_MODE: self._interval_mode,
            ATTR_INTERVAL_ENABLED: self._interval_enabled,
            ATTR_DATA: self._intervals,
        }

    @callback
    def _update_state(self) -> None:
        now = dt_util.now()
        now_time = now.time()

        # earliest_start always refers to today
        earliest_start = datetime.combine(now, self._earliest_start_time, now.tzinfo)

        # latest_end may refer to today or tomorrow
        latest_end = datetime.combine(now, self._latest_end_time, now.tzinfo)

        if self._latest_end_time > self._earliest_start_time:
            # start and end refer to the same day (which is today for now)
            self._interval_enabled = (
                self._earliest_start_time <= now_time < self._latest_end_time
            )
        else:
            # start refers to today, end refers to tomorrow
            # -> there are 2 intervals: from start to midnight and from midnight to end
            self._interval_enabled = (
                self._earliest_start_time <= now_time
                or now_time < self._latest_end_time
            )
            latest_end += timedelta(days=1)

        if self._interval_mode == IntervalModes.INTERMITTENT.value:
            self._update_state_for_intermittent(earliest_start, latest_end, now)
        elif self._interval_mode == IntervalModes.CONTIGUOUS.value:
            self._update_state_for_contigous(earliest_start, latest_end, now)
        else:
            _LOGGER.error(f"invalid interval mode: {self._interval_mode}")

    def _update_state_for_intermittent(
        self, earliest_start: time, latest_end: time, now: datetime
    ):
        marketdata = get_marketdata_from_sensor_attrs(self._sensor_attributes)

        intervals = calc_intervals_for_intermittent(
            marketdata=marketdata,
            earliest_start=earliest_start,
            latest_end=latest_end,
            duration=self._duration,
            most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
        )

        if intervals is None:
            return

        self._state = is_now_in_intervals(now, intervals)

        # try to calculate intervals for next day also
        earliest_start += timedelta(days=1)
        if earliest_start >= latest_end:
            # do calculation only if latest_end is limited to 24h from earliest_start,
            # --> avoid calculation if latest_end includes all available marketdata
            latest_end += timedelta(days=1)
            intervals2 = calc_intervals_for_intermittent(
                marketdata=marketdata,
                earliest_start=earliest_start,
                latest_end=latest_end,
                duration=self._duration,
                most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
            )

            if intervals2 is not None:
                intervals = [*intervals, *intervals2]

        self._intervals = [
            {
                ATTR_START_TIME: dt_util.as_local(e.start_time).isoformat(),
                ATTR_END_TIME: dt_util.as_local(e.end_time).isoformat(),
                ATTR_RANK: e.rank,
                # ATTR_PRICE_PER_MWH: e.price_eur_per_mwh,
                # ATTR_PRICE_PER_KWH: e.price_eur_per_mwh / 10,
            }
            for e in sorted(intervals, key=lambda e: e.start_time)
        ]

    def _update_state_for_contigous(
        self, earliest_start: time, latest_end: time, now: datetime
    ):
        marketdata = get_marketdata_from_sensor_attrs(self._sensor_attributes)

        result = calc_interval_for_contiguous(
            marketdata,
            earliest_start=earliest_start,
            latest_end=latest_end,
            duration=self._duration,
            most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
        )

        if result is None:
            return

        self._state = result["start"] <= now < result["end"]

        self._intervals = [
            {
                ATTR_START_TIME: dt_util.as_local(result["start"]).isoformat(),
                ATTR_END_TIME: dt_util.as_local(result["end"]).isoformat(),
                # "interval_price": result["interval_price"],
            }
        ]

        # try to calculate intervals for next day also
        earliest_start += timedelta(days=1)
        if earliest_start >= latest_end:
            # do calculation only if latest_end is limited to 24h from earliest_start,
            # --> avoid calculation if latest_end includes all available marketdata
            latest_end += timedelta(days=1)
            result = calc_interval_for_contiguous(
                marketdata,
                earliest_start=earliest_start,
                latest_end=latest_end,
                duration=self._duration,
                most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
            )

            if result is None:
                return

            self._intervals.append(
                {
                    ATTR_START_TIME: dt_util.as_local(result["start"]).isoformat(),
                    ATTR_END_TIME: dt_util.as_local(result["end"]).isoformat(),
                }
            )
