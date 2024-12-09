#!/usr/bin/env python3

import aiohttp
import asyncio

from .EPEXSpot import Energyforecast
from .const import UOM_EUR_PER_KWH

DEMO_TOKEN = "demo_token" # The "demo_token" token only provides up to 24 hours of forecast data into the future.

async def main():
    async with aiohttp.ClientSession() as session:
        service = Energyforecast.Energyforecast(market_area="DE-LU", token=DEMO_TOKEN, session=session)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
