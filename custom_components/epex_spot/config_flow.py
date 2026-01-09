"""Config flow for EPEXSpot component.

Used by UI to setup integration.
"""

import voluptuous as vol
from typing import List, Tuple

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithReload
from homeassistant.core import callback

from .const import (
    CONF_MARKET_AREA,
    CONF_SOURCE,
    CONF_SOURCE_AWATTAR,
    CONF_SOURCE_ENTSOE,
    CONF_SOURCE_SMARD_DE,
    CONF_SOURCE_SMARTENERGY,
    CONF_SOURCE_TIBBER,
    CONF_SOURCE_ENERGYFORECAST,
    CONF_SOURCE_ENERGYCHARTS,
    CONF_SOURCE_HOFER_GRUENSTROM,
    CONF_SURCHARGE_ABS,
    CONF_SURCHARGE_PERC,
    CONF_TAX,
    CONF_TOKEN,
    CONF_DURATION,
    CONFIG_VERSION,
    DEFAULT_DURATION,
    DEFAULT_SURCHARGE_ABS,
    DEFAULT_SURCHARGE_PERC,
    DEFAULT_TAX,
    DOMAIN,
)
from .EPEXSpot import (
    SMARD,
    Awattar,
    Tibber,
    smartENERGY,
    Energyforecast,
    ENTSOE,
    EnergyCharts,
    HoferGruenstrom,
)

CONF_SOURCE_LIST = (
    CONF_SOURCE_AWATTAR,
    CONF_SOURCE_ENTSOE,
    CONF_SOURCE_SMARD_DE,
    CONF_SOURCE_SMARTENERGY,
    CONF_SOURCE_TIBBER,
    CONF_SOURCE_ENERGYFORECAST,
    CONF_SOURCE_ENERGYCHARTS,
    CONF_SOURCE_HOFER_GRUENSTROM,
)


class EpexSpotConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore
    """Component config flow."""

    VERSION = CONFIG_VERSION

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
            {
                vol.Required(CONF_SOURCE): vol.In(
                    sorted(CONF_SOURCE_LIST, key=lambda s: s.casefold())
                )
            }
        )

        return self.async_show_form(
            step_id="source", data_schema=data_schema, last_step=False
        )

    async def async_step_source(self, user_input=None):
        self._source_name = user_input[CONF_SOURCE]

        areas, durations, requires_token = getParametersForSource(self._source_name)

        data_schema = (
            vol.Schema(
                {
                    vol.Required(CONF_MARKET_AREA): vol.In(areas),
                    vol.Required(CONF_DURATION): vol.In(durations),
                    vol.Required(CONF_TOKEN): vol.Coerce(str),
                }
            )
            if requires_token
            else vol.Schema(
                {
                    vol.Required(CONF_MARKET_AREA): vol.In(areas),
                    vol.Required(CONF_DURATION): vol.In(durations),
                },
            )
        )

        # Add warning for HoferGruenstrom about disabled SSL
        description_placeholders = {}
        if self._source_name == CONF_SOURCE_HOFER_GRUENSTROM:
            description_placeholders = {
                "ssl_warning": "Warning: SSL certificate verification is disabled for this source."
            }

        return self.async_show_form(
            step_id="market_area",
            data_schema=data_schema,
            description_placeholders=description_placeholders,
        )

    async def async_step_market_area(self, user_input=None):
        if user_input is not None:
            # create an entry for this configuration
            market_area = user_input[CONF_MARKET_AREA]
            title = f"{self._source_name} ({market_area})"

            unique_id = f"{DOMAIN} {self._source_name} {market_area}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            data = {CONF_SOURCE: self._source_name, CONF_MARKET_AREA: market_area}
            if CONF_TOKEN in user_input:
                data[CONF_TOKEN] = user_input[CONF_TOKEN]
            options = {CONF_DURATION: DEFAULT_DURATION}
            if CONF_DURATION in user_input:
                options[CONF_DURATION] = user_input[CONF_DURATION]

            return self.async_create_entry(
                title=title,
                data=data,
                options=options,
            )
        return None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowWithReload:
        """Create the options flow."""
        return EpexSpotOptionsFlow()


class EpexSpotOptionsFlow(OptionsFlowWithReload):
    """Handle the start of the option flow."""

    def __init__(self) -> None:
        """Initialize options flow."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        _, durations, _ = getParametersForSource(
            self.config_entry.data.get(CONF_SOURCE)
        )

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
                    vol.Required(
                        CONF_DURATION,
                        default=self.config_entry.options.get(
                            CONF_DURATION, DEFAULT_DURATION
                        ),
                    ): vol.In(durations),
                }
            ),
        )


def getParametersForSource(
    source_name: str,
) -> Tuple[List[str], List[int], bool]:
    """
    returns sorted market areas, durations and if given source requires a token
    """
    # market areas and durations are generally sorted in classes so no need to sort
    if source_name == CONF_SOURCE_AWATTAR:
        return (
            Awattar.Awattar.MARKET_AREAS,
            Awattar.Awattar.SUPPORTED_DURATIONS,
            False,
        )
    if source_name == CONF_SOURCE_ENERGYFORECAST:
        return (
            Energyforecast.Energyforecast.MARKET_AREAS,
            Energyforecast.Energyforecast.SUPPORTED_DURATIONS,
            True,
        )
    if source_name == CONF_SOURCE_TIBBER:
        return (
            Tibber.Tibber.MARKET_AREAS,
            Tibber.Tibber.SUPPORTED_DURATIONS,
            True,
        )
    if source_name == CONF_SOURCE_SMARD_DE:
        return (
            sorted(SMARD.SMARD.MARKET_AREAS),  # not sorted so sort here
            SMARD.SMARD.SUPPORTED_DURATIONS,
            False,
        )
    if source_name == CONF_SOURCE_SMARTENERGY:
        return (
            smartENERGY.smartENERGY.MARKET_AREAS,
            smartENERGY.smartENERGY.SUPPORTED_DURATIONS,
            False,
        )
    if source_name == CONF_SOURCE_ENTSOE:
        return (
            sorted(ENTSOE.EntsoeTransparency.MARKET_AREAS),
            ENTSOE.EntsoeTransparency.SUPPORTED_DURATIONS,
            True,
        )
    if source_name == CONF_SOURCE_ENERGYCHARTS:
        return (
            sorted(EnergyCharts.EnergyCharts.MARKET_AREAS),
            EnergyCharts.EnergyCharts.SUPPORTED_DURATIONS,
            False,
        )
    if source_name == CONF_SOURCE_HOFER_GRUENSTROM:
        return (
            HoferGruenstrom.HoferGruenstrom.MARKET_AREAS,
            HoferGruenstrom.HoferGruenstrom.SUPPORTED_DURATIONS,
            False,
        )

    return ([], [], False)
