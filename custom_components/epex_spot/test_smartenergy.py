#!/usr/bin/env python3

from EPEXSpot import smartENERGY

service = smartENERGY.smartENERGY(market_area="at")

service.fetch()
print(f"count = {len(service.marketdata)}")
for e in service.marketdata:
    print(f"{e.start_time}: {e.price_ct_per_kwh} {e.UOM_CT_PER_kWh}")
