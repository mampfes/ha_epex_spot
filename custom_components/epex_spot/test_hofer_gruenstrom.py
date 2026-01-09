#!/usr/bin/env python3

import asyncio

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import HoferGruenstrom


async def main():
    async with aiohttp.ClientSession() as session:
        service = HoferGruenstrom.HoferGruenstrom(market_area="at", session=session, duration=15)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}-{e.end_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


asyncio.run(main())
