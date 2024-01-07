"""Config flow for EPEX Spot Sensor component."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .const import (
    PriceModes,
    IntervalModes,
    CONF_EARLIEST_START_TIME,
    CONF_LATEST_END_TIME,
    CONF_INTERVAL_MODE,
    CONF_PRICE_MODE,
    CONF_DURATION,
    DOMAIN,
)


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EARLIEST_START_TIME): selector.TimeSelector(),
        vol.Required(CONF_LATEST_END_TIME): selector.TimeSelector(),
        vol.Required(CONF_DURATION, default={"hours": 1}): selector.DurationSelector(),
        vol.Required(
            CONF_PRICE_MODE, default=PriceModes.CHEAPEST
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                translation_key=CONF_PRICE_MODE,
                mode=selector.SelectSelectorMode.LIST,
                options=[e.value for e in PriceModes],
            )
        ),
        vol.Required(
            CONF_INTERVAL_MODE, default=IntervalModes.INTERMITTENT
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                translation_key=CONF_INTERVAL_MODE,
                mode=selector.SelectSelectorMode.LIST,
                options=[e.value for e in IntervalModes],
            )
        ),
        #        vol.Required(
        #            CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS
        #        ): selector.NumberSelector(
        #            selector.NumberSelectorConfig(
        #                mode=selector.NumberSelectorMode.BOX, step="any"
        #            ),
        #        ),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN)
        ),
    }
).extend(OPTIONS_SCHEMA.schema)

CONFIG_FLOW = {"user": SchemaFlowFormStep(CONFIG_SCHEMA)}

OPTIONS_FLOW = {"init": SchemaFlowFormStep(OPTIONS_SCHEMA)}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Threshold."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        name: str = options[CONF_NAME]
        return name
