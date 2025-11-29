#!/usr/bin/env python3

import asyncio
import os

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import ENTSOE


async def main():
    token = os.getenv("ENTSOE_API_KEY")

    if not token:
        raise RuntimeError(
            "Please set the ENTSOE_API_KEY environment variable.\n"
            "Example: export ENTSOE_API_KEY=yourtokenhere"
        )

    async with aiohttp.ClientSession() as session:
        durations = [15, 60]

        for duration in durations:
            print(f"\n=== Testing ENTSO-E Duration: {duration} minutes ===")

            service = ENTSOE.EntsoeTransparency(
                market_area="FR",
                duration=duration,
                session=session,
                token=token,
            )

            await service.fetch()
            md = service.marketdata

            print(f"Fetched entries: {len(md)}")

            for e in service.marketdata:
                print(f"{e.start_time}: {e.market_price_per_kwh} {UOM_EUR_PER_KWH}")


if __name__ == "__main__":
    asyncio.run(main())
