from dataclasses import dataclass

from .const import ATTR_PRICE_EUR_PER_KWH, ATTR_PRICE_GBP_PER_KWH


@dataclass(frozen=True, slots=True)
class Localize:
    """Class to localize"""

    uom_per_kwh: str
    icon: str
    attr_name_per_kwh: str


CURRENCY_MAPPING = {
    "EUR": Localize(
        uom_per_kwh="€/kWh",
        icon="mdi:currency-eur",
        attr_name_per_kwh=ATTR_PRICE_EUR_PER_KWH,
    ),
    "GBP": Localize(
        uom_per_kwh="£/kWh",
        icon="mdi:currency-gbp",
        attr_name_per_kwh=ATTR_PRICE_GBP_PER_KWH,
    ),
}
