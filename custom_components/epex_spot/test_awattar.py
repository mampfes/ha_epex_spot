#!/usr/bin/env python3

import aiohttp
import asyncio

from EPEXSpot import Awattar


async def main():
    async with aiohttp.ClientSession() as session:
        service = Awattar.Awattar(market_area="de", session=session)
        print(service.MARKET_AREAS)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_eur_per_mwh} {e.UOM_EUR_PER_MWh}")


asyncio.run(main())
