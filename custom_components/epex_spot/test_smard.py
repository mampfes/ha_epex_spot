#!/usr/bin/env python3

import asyncio

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import SMARD


async def main():
    async with aiohttp.ClientSession() as session:
        service = SMARD.SMARD(market_area="DE-LU", session=session)
        # print(service.MARKET_AREAS)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
