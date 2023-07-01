#!/usr/bin/env python3

from EPEXSpot import SMARD

service = SMARD.SMARD(market_area="SW")
# print(service.MARKET_AREAS)

service.fetch()
print(f"count = {len(service.marketdata)}")
for e in service.marketdata:
    print(f"{e.start_time}: {e.price_eur_per_mwh} {e.UOM_EUR_PER_MWh}")
