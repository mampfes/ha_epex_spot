from dataclasses import dataclass


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
        attr_name_per_mwh="price_eur_per_mwh",
        attr_name_per_kwh="price_ct_per_kwh",
    ),
    "GBP": Localize(
        uom_per_mwh="GBP/MWh",
        uom_per_kwh="pence/kWh",
        icon="mdi:currency-gbp",
        attr_name_per_mwh="price_gbp_per_mwh",
        attr_name_per_kwh="price_pence_per_kwh",
    ),
}
