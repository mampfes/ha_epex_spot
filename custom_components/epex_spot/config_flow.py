"""Config flow for EPEXSpot component.

Used by UI to setup integration.
"""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (CONF_MARKET_AREA, CONF_SOURCE, CONF_SOURCE_AWATTAR,
                    CONF_SOURCE_EPEX_SPOT_WEB, CONF_SOURCE_SMARD_DE,
                    CONF_SURCHARGE_ABS, CONF_SURCHARGE_PERC, CONF_TAX,
                    DEFAULT_SURCHARGE_ABS, DEFAULT_SURCHARGE_PERC, DEFAULT_TAX,
                    DOMAIN)
from .EPEXSpot import SMARD, Awattar, EPEXSpotWeb

CONF_SOURCE_LIST = (
    CONF_SOURCE_AWATTAR,
    CONF_SOURCE_EPEX_SPOT_WEB,
    CONF_SOURCE_SMARD_DE,
)


class EpexSpotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Component config flow."""

    VERSION = 1

    def __init__(self):
        self._source_name = None

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow.

        Called after integration has been selected in the 'add integration
        UI'. The user_input is set to None in this case. We will open a config
        flow form then.
        This function is also called if the form has been submitted. user_input
        contains a dict with the user entered values then.
        """
        # query top level source
        data_schema = vol.Schema(
            {vol.Required(CONF_SOURCE): vol.In(sorted(CONF_SOURCE_LIST))}
        )

        return self.async_show_form(step_id="source", data_schema=data_schema)

    async def async_step_source(self, user_input=None):
        self._source_name = user_input[CONF_SOURCE]

        if self._source_name == CONF_SOURCE_AWATTAR:
            areas = Awattar.Awattar.MARKET_AREAS
        elif self._source_name == CONF_SOURCE_EPEX_SPOT_WEB:
            areas = EPEXSpotWeb.EPEXSpotWeb.MARKET_AREAS
        elif self._source_name == CONF_SOURCE_SMARD_DE:
            areas = SMARD.SMARD.MARKET_AREAS

        data_schema = vol.Schema(
            {vol.Required(CONF_MARKET_AREA): vol.In(sorted(areas))}
        )

        return self.async_show_form(step_id="market_area", data_schema=data_schema)

    async def async_step_market_area(self, user_input=None):
        if user_input is not None:
            # create an entry for this configuration
            market_area = user_input[CONF_MARKET_AREA]
            title = f"{self._source_name} ({market_area})"

            unique_id = f"{DOMAIN} {self._source_name} {market_area}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=title,
                data={CONF_SOURCE: self._source_name, CONF_MARKET_AREA: market_area},
            )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return EpexSpotOptionsFlow(config_entry)


class EpexSpotOptionsFlow(config_entries.OptionsFlow):
    """Handle the start of the option flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SURCHARGE_PERC,
                        default=self.config_entry.options.get(
                            CONF_SURCHARGE_PERC, DEFAULT_SURCHARGE_PERC
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_SURCHARGE_ABS,
                        default=self.config_entry.options.get(
                            CONF_SURCHARGE_ABS, DEFAULT_SURCHARGE_ABS
                        ),
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_TAX,
                        default=self.config_entry.options.get(CONF_TAX, DEFAULT_TAX),
                    ): vol.Coerce(float),
                }
            ),
        )
