"""Component for EPEX Spot support."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt

from .const import (CONF_MARKET_AREA, CONF_SOURCE, CONF_SOURCE_AWATTAR,
                    CONF_SOURCE_EPEX_SPOT_WEB, CONF_SOURCE_SMARD_DE,
                    CONF_SURCHARGE_ABS, CONF_SURCHARGE_PERC, CONF_TAX,
                    DEFAULT_SURCHARGE_ABS, DEFAULT_SURCHARGE_PERC, DEFAULT_TAX,
                    DOMAIN, UPDATE_SENSORS_SIGNAL)
from .EPEXSpot import SMARD, Awattar, EPEXSpotWeb

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up component from a config entry, config_entry contains data from config entry database."""
    # store shell object
    shell = hass.data.setdefault(DOMAIN, EpexSpotShell(hass))

    # add market area to shell
    shell.add_entry(entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(on_update_options_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        shell = hass.data[DOMAIN]
        shell.remove_entry(config_entry)
        if shell.is_idle():
            # also remove shell if not used by any entry any more
            del hass.data[DOMAIN]

    return unload_ok


async def on_update_options_listener(hass, entry):
    """Handle options update."""
    # update all sensors immediately
    dispatcher_send(hass, UPDATE_SENSORS_SIGNAL)


class SourceDecorator:
    def __init__(self, config_entry, source):
        self._source = source
        self._config_entry = config_entry
        self._marketdata_now = None
        self._sorted_marketdata_today = []
        self._cheapest_sorted_marketdata_today = None
        self._most_expensive_sorted_marketdata_today = None

    @property
    def unique_id(self):
        return self._config_entry.unique_id

    @property
    def name(self):
        return self._source.name

    @property
    def marketdata(self):
        return self._source.marketdata

    @property
    def market_area(self):
        return self._source.market_area

    @property
    def marketdata_now(self):
        return self._marketdata_now

    @property
    def sorted_marketdata_today(self):
        return self._sorted_marketdata_today

    def fetch(self):
        self._source.fetch()

    def update_time(self):
        if (len(self.marketdata)) == 0:
            self._marketdata_now = None
            self._sorted_marketdata_today = []
            return

        now = dt.now()

        # find current entry in marketdata list
        try:
            self._marketdata_now = next(
                filter(
                    lambda e: e.start_time <= now and e.end_time > now, self.marketdata
                )
            )
        except StopIteration:
            _LOGGER.error(f"no data found for {self._source}")
            self._marketdata_now = None
            self._sorted_marketdata_today = []

        # get list of entries for today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        sorted_marketdata_today = filter(
            lambda e: e.start_time >= start_of_day and e.end_time <= end_of_day,
            self.marketdata,
        )
        sorted_sorted_marketdata_today = sorted(
            sorted_marketdata_today, key=lambda e: e.price_eur_per_mwh
        )
        self._sorted_marketdata_today = sorted_sorted_marketdata_today

    def to_net_price(self, price_eur_per_mwh):
        surcharge_pct = self._config_entry.options.get(
            CONF_SURCHARGE_PERC, DEFAULT_SURCHARGE_PERC
        )
        surcharge_abs = self._config_entry.options.get(
            CONF_SURCHARGE_ABS, DEFAULT_SURCHARGE_ABS
        )
        tax = self._config_entry.options.get(CONF_TAX, DEFAULT_TAX)

        net_p = price_eur_per_mwh / 10  # convert from EUR/MWh to ct/kWh
        net_p *= 1 + (surcharge_pct / 100)
        net_p += surcharge_abs
        net_p *= 1 + (tax / 100)

        return net_p


class EpexSpotShell:
    """Shell object for EPEX Spot. Stored in hass.data."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the instance."""
        self._hass = hass
        self._sources = {}
        self._timer_listener_hour_change = None
        self._timer_listener_fetch = None

    def is_idle(self) -> bool:
        return not bool(self._sources)

    def get_source(self, unique_id):
        return self._sources[unique_id]

    def add_entry(self, config_entry: ConfigEntry):
        """Add entry."""
        is_idle = self.is_idle()

        if config_entry.data[CONF_SOURCE] == CONF_SOURCE_AWATTAR:
            source = Awattar.Awattar(market_area=config_entry.data[CONF_MARKET_AREA])
        elif config_entry.data[CONF_SOURCE] == CONF_SOURCE_EPEX_SPOT_WEB:
            source = EPEXSpotWeb.EPEXSpotWeb(
                market_area=config_entry.data[CONF_MARKET_AREA]
            )
        elif config_entry.data[CONF_SOURCE] == CONF_SOURCE_SMARD_DE:
            source = SMARD.SMARD(market_area=config_entry.data[CONF_MARKET_AREA])

        source = SourceDecorator(config_entry, source)
        self._sources[config_entry.unique_id] = source

        self._hass.add_job(lambda: self._fetch_source_and_dispatch(source))

        source.update_time()

        if is_idle:
            # This is the first entry, therefore start the timers
            self._timer_listener_hour_change = async_track_time_change(
                self._hass, self._on_hour_change, hour=None, minute=0, second=0
            )
            self._timer_listener_fetch = async_track_time_change(
                self._hass, self._on_fetch_sources, hour=None, minute=58, second=0
            )

    def remove_entry(self, config_entry: ConfigEntry):
        """Remove entry."""
        self._sources.pop(config_entry.unique_id)

        if self.is_idle():
            # This was the last source, therefore stop the timers
            remove_listener = self._timer_listener_hour_change
            if remove_listener is not None:
                remove_listener()

            remove_listener = self._timer_listener_fetch
            if remove_listener is not None:
                remove_listener()

    def _fetch_source_and_dispatch(self, source):
        try:
            source.fetch()
            source.update_time()
            dispatcher_send(self._hass, UPDATE_SENSORS_SIGNAL)
        except BaseException as error:
            _LOGGER.error(f"fetch and dispatch failed : {error}")

    @callback
    def _on_fetch_sources(self, *_):
        self._hass.add_job(lambda: self._fetch_sources())

    def _fetch_sources(self):
        for source in self._sources.values():
            try:
                source.fetch()
            except Exception as error:
                _LOGGER.error(f"fetch failed : {error}")

    @callback
    def _on_hour_change(self, *_):
        # adjust marketdata in all sources to current hour
        for source in self._sources.values():
            try:
                source.update_time()
            except Exception as error:
                _LOGGER.error(f"hourly update failed : {error}")

        # update all sensors immediately
        dispatcher_send(self._hass, UPDATE_SENSORS_SIGNAL)
