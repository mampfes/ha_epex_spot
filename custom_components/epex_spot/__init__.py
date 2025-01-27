"""Component for EPEX Spot support."""

import asyncio
import logging
import random
from typing import Any, Callable

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
    async_get as dr_async_get,
)
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_DATA,
    CONF_DURATION,
    CONF_EARLIEST_START_POST,
    CONF_EARLIEST_START_TIME,
    CONF_LATEST_END_POST,
    CONF_LATEST_END_TIME,
    CONF_SURCHARGE_ABS,
    CONFIG_VERSION,
    DOMAIN,
)
from .localization import CURRENCY_MAPPING
from .SourceShell import SourceShell

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

GET_EXTREME_PRICE_INTERVAL_SCHEMA = vol.Schema(
    {
        **cv.ENTITY_SERVICE_FIELDS,  # for device_id
        vol.Optional(CONF_EARLIEST_START_TIME): cv.time,
        vol.Optional(CONF_EARLIEST_START_POST): cv.positive_int,
        vol.Optional(CONF_LATEST_END_TIME): cv.time,
        vol.Optional(CONF_LATEST_END_POST): cv.positive_int,
        vol.Required(CONF_DURATION): cv.positive_time_period,
    }
)
FETCH_DATA_SCHEMA = vol.Schema(
    {
        **cv.ENTITY_SERVICE_FIELDS,  # for device_id
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up component from a config entry."""

    source = SourceShell(entry, async_get_clientsession(hass))

    try:
        await source.fetch()
        source.update_time()
    except Exception as err:  # pylint: disable=broad-except
        ex = ConfigEntryNotReady()
        ex.__cause__ = err
        raise ex

    coordinator = EpexSpotDataUpdateCoordinator(hass, source=source)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(on_update_options_listener))

    entry.async_on_unload(
        async_track_time_change(
            hass, coordinator.on_refresh, hour=None, minute=0, second=0
        )
    )
    if source.duration == 30 or source.duration == 15:
        entry.async_on_unload(
            async_track_time_change(
                hass, coordinator.on_refresh, hour=None, minute=30, second=0
            )
        )
    if source.duration == 15:
        entry.async_on_unload(
            async_track_time_change(
                hass, coordinator.on_refresh, hour=None, minute=15, second=0
            )
        )
        entry.async_on_unload(
            async_track_time_change(
                hass, coordinator.on_refresh, hour=None, minute=45, second=0
            )
        )

    entry.async_on_unload(
        async_track_time_change(
            hass, coordinator.fetch_source, hour=None, minute=50, second=0
        )
    )

    # service call handling
    async def get_lowest_price_interval(call: ServiceCall) -> ServiceResponse:
        """Get the time interval during which the price is at its lowest point."""
        return _find_extreme_price_interval(call, lambda a, b: a < b)

    async def get_highest_price_interval(call: ServiceCall) -> ServiceResponse:
        """Get the time interval during which the price is at its highest point."""
        return _find_extreme_price_interval(call, lambda a, b: a > b)

    async def fetch_data(call: ServiceCall) -> None:
        entries = hass.data[DOMAIN]
        if ATTR_DEVICE_ID in call.data:
            device_id = call.data[ATTR_DEVICE_ID][0]
            device_registry = dr_async_get(hass)
            if not (device_entry := device_registry.async_get(device_id)):
                raise HomeAssistantError(f"No device found for device id: {device_id}")
            coordinators = [entries[next(iter(device_entry.config_entries))]]
        else:
            coordinators = entries.values()

        for c in coordinators:
            await c.source.fetch()
            await c.on_refresh()

    def _find_extreme_price_interval(
        call: ServiceCall, cmp: Callable[[float, float], bool]
    ) -> ServiceResponse:
        entries = hass.data[DOMAIN]
        if ATTR_DEVICE_ID in call.data:
            device_id = call.data[ATTR_DEVICE_ID][0]
            device_registry = dr_async_get(hass)
            if not (device_entry := device_registry.async_get(device_id)):
                raise HomeAssistantError(f"No device found for device id: {device_id}")
            coordinator = entries[next(iter(device_entry.config_entries))]
        else:
            coordinator = next(iter(entries.values()))

        if coordinator is None:
            return None

        return coordinator.source.find_extreme_price_interval(
            call_data=call.data, cmp=cmp
        )

    hass.services.async_register(
        DOMAIN,
        "get_lowest_price_interval",
        get_lowest_price_interval,
        schema=GET_EXTREME_PRICE_INTERVAL_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "get_highest_price_interval",
        get_highest_price_interval,
        schema=GET_EXTREME_PRICE_INTERVAL_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "fetch_data", fetch_data, schema=FETCH_DATA_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def on_update_options_listener(hass, entry):
    """Handle options update."""
    # update all sensors immediately
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_request_refresh()


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry data to the new entry schema."""

    data = config_entry.data.copy()

    current_version = data.get("version", 1)

    if current_version != CONFIG_VERSION:
        _LOGGER.info(
            "Migrating entry %s to version %s", config_entry.entry_id, CONFIG_VERSION
        )
        new_options = {**config_entry.options}

        if (
            CONF_SURCHARGE_ABS in config_entry.options
            and config_entry.options[CONF_SURCHARGE_ABS] is not None
        ):
            new_options[CONF_SURCHARGE_ABS] = (
                config_entry.options[CONF_SURCHARGE_ABS] * 0.01
            )

        hass.config_entries.async_update_entry(
            config_entry, options=new_options, version=CONFIG_VERSION
        )

        _LOGGER.info(
            "Migration of entry %s to version %s successful",
            config_entry.entry_id,
            CONFIG_VERSION,
        )

    return True


class EpexSpotDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching AccuWeather data API."""

    source: SourceShell

    def __init__(
        self,
        hass: HomeAssistant,
        source: SourceShell,
    ) -> None:
        """Initialize."""
        self.source = source
        self._error_count = 0

        super().__init__(hass, _LOGGER, name=DOMAIN)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        self.source.update_time()

    async def on_refresh(self, *args: Any):
        await self.async_refresh()

    async def fetch_source(self, *args: Any):
        # spread fetch over 9 minutes to reduce peak load on servers
        await asyncio.sleep(random.uniform(0, 9 * 60))
        try:
            await self.source.fetch()
            self._error_count = 0
        except Exception:  # pylint: disable=broad-except
            self._error_count += 1
            if self._error_count >= 3:
                raise


class EpexSpotEntity(CoordinatorEntity, Entity):
    """A entity implementation for EPEX Spot service."""

    _coordinator: EpexSpotDataUpdateCoordinator
    _source: SourceShell
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({ATTR_DATA})

    def __init__(
        self, coordinator: EpexSpotDataUpdateCoordinator, description: EntityDescription
    ):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._source = coordinator.source
        self._localized = CURRENCY_MAPPING[coordinator.source.currency]
        self._attr_unique_id = f"{self._source.unique_id} {description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._source.name} {self._source.market_area}")},
            name="EPEX Spot Data",
            manufacturer=self._source.name,
            model=self._source.market_area,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return super().available and self._source._marketdata_now is not None
