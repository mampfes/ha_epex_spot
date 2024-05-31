#!/usr/bin/env python3

import aiohttp
import asyncio

from EPEXSpot import smartENERGY


async def main():
    async with aiohttp.ClientSession() as session:
        service = smartENERGY.smartENERGY(market_area="at", session=session)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(f"{e.start_time}: {e.price_ct_per_kwh} {e.UOM_CT_PER_kWh}")


asyncio.run(main())
