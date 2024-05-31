#!/usr/bin/env python3

import aiohttp
import asyncio

import EPEXSpot.EPEXSpotWeb


async def main():
    async with aiohttp.ClientSession() as session:
        service = EPEXSpot.EPEXSpotWeb.EPEXSpotWeb(market_area="DE-LU", session=session)
        print(service.MARKET_AREAS)

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(
                f"{e.start_time}-{e.end_time}: {e.price_eur_per_mwh} {e.UOM_EUR_PER_MWh}"  # noqa
            )


asyncio.run(main())
