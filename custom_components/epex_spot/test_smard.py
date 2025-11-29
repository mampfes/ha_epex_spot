#!/usr/bin/env python3

import asyncio

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import SMARD


async def main():
    async with aiohttp.ClientSession() as session:
        durations = [15, 60]

        for duration in durations:
            service = SMARD.SMARD(
                market_area="DE-LU", session=session, duration=duration
            )
            # print(service.MARKET_AREAS)

            await service.fetch()
            print(f"duration={duration} count = {len(service.marketdata)}")
            for e in service.marketdata:
                print(f"{e.start_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
