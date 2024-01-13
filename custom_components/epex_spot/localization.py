from dataclasses import dataclass

from .const import (
    ATTR_PRICE_CT_PER_KWH,
    ATTR_PRICE_EUR_PER_MWH,
    ATTR_PRICE_GBP_PER_MWH,
    ATTR_PRICE_PENCE_PER_KWH,
)


@dataclass(frozen=True, slots=True)
class Localize:
    uom_per_mwh: str
    uom_per_kwh: str
    icon: str
    attr_name_per_mwh: str
    attr_name_per_kwh: str


CURRENCY_MAPPING = {
    "EUR": Localize(
        uom_per_mwh="EUR/MWh",
        uom_per_kwh="ct/kWh",
        icon="mdi:currency-eur",
        attr_name_per_mwh=ATTR_PRICE_EUR_PER_MWH,
        attr_name_per_kwh=ATTR_PRICE_CT_PER_KWH,
    ),
    "GBP": Localize(
        uom_per_mwh="GBP/MWh",
        uom_per_kwh="pence/kWh",
        icon="mdi:currency-gbp",
        attr_name_per_mwh=ATTR_PRICE_GBP_PER_MWH,
        attr_name_per_kwh=ATTR_PRICE_PENCE_PER_KWH,
    ),
}
