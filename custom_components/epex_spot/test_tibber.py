#!/usr/bin/env python3

import aiohttp
import asyncio

from EPEXSpot import Tibber

DEMO_TOKEN = "5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE"


async def main():
    async with aiohttp.ClientSession() as session:
        service = Tibber.Tibber(market_area="de", token=DEMO_TOKEN, session=session)
        print(service.MARKET_AREAS)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_ct_per_kwh} {e.UOM_CT_PER_kWh}")


asyncio.run(main())
