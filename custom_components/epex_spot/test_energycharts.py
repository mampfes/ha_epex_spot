#!/usr/bin/env python3

import asyncio
import os

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import EnergyCharts


async def main():
    async with aiohttp.ClientSession() as session:
        durations = [15, 60]

        for duration in durations:
            print(f"\n=== Testing EnergyCharts: {duration} minutes ===")

            service = EnergyCharts.EnergyCharts(
                market_area="FR",
                duration=duration,
                session=session,
            )

            await service.fetch()
            md = service.marketdata

            print(f"Fetched entries: {len(md)}")

            for e in service.marketdata:
                print(f"{e.start_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


if __name__ == "__main__":
    asyncio.run(main())
