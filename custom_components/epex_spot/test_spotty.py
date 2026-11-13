#!/usr/bin/env python3

import asyncio
import os

import aiohttp

from .const import UOM_EUR_PER_KWH
from .EPEXSpot import Spotty


async def main():
    contract_id = os.environ.get("SPOTTY_CONTRACT_ID")
    if not contract_id:
        raise SystemExit(
            "Set SPOTTY_CONTRACT_ID to the contract id from the Spotty customer portal."
        )

    duration = int(os.environ.get("SPOTTY_DURATION", "15"))

    async with aiohttp.ClientSession() as session:
        service = Spotty.Spotty(
            market_area="at",
            duration=duration,
            session=session,
            token=contract_id,
        )

        await service.fetch()
        print(f"count = {len(service.marketdata)}")
        for e in service.marketdata:
            print(
                f"{e.start_time.isoformat()}-{e.end_time.isoformat()}: "
                f"{e.market_price_per_kwh} {UOM_EUR_PER_KWH}"
            )


asyncio.run(main())
