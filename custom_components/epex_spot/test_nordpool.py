#!/usr/bin/env python3

import asyncio

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import Nordpool


async def main():
    async with aiohttp.ClientSession() as session:
        durations = [15, 60]

        for duration in durations:
            service = Nordpool.Nordpool(
                market_area="NL", session=session, duration=duration
            )

            await service.fetch()
            print(f"duration={duration} count = {len(service.marketdata)}")
            for e in service.marketdata:
                print(f"{e.start_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
