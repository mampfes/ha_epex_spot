#!/usr/bin/env python3

import aiohttp
import asyncio

from EPEXSpot import Awattar

from const import UOM_EUR_PER_KWH

from pprint import pprint


async def main():
    async with aiohttp.ClientSession() as session:
        service = Awattar.Awattar(market_area="de", session=session)
        print(service.MARKET_AREAS)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
