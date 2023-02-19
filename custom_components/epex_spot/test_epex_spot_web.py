#!/usr/bin/env python3

import EPEXSpot.EPEXSpotWeb

service = EPEXSpot.EPEXSpotWeb.EPEXSpotWeb(market_area="DE-LU")
print(service.MARKET_AREAS)

service.fetch()
print(f"count = {len(service.marketdata)}")
for e in service.marketdata:
    print(f"{e.start_time}: {e.price_eur_per_mwh} {e.UOM_EUR_PER_MWh}")
