#!/usr/bin/env python3

import aiohttp

import asyncio

from .EPEXSpot import Awattar
from .const import UOM_EUR_PER_KWH


async def main():
    async with aiohttp.ClientSession() as session:
        durations = [15, 60]
        for duration in durations:
            service = Awattar.Awattar(
                market_area="de", session=session, duration=duration
            )
            print(service.MARKET_AREAS)

            await service.fetch()
            print(f"count = {len(service.marketdata)}")
            for e in service.marketdata:
                print(f"{e.start_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
