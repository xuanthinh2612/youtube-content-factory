from __future__ import annotations
import asyncio


async def gather_cancel_on_error(*aws):
    """Gather awaitables, cancelling siblings immediately if one fails.

    asyncio.gather() propagates the first exception but does not reliably stop
    already-running sibling work. For costly LLM branches that can leak token
    spend after a project has already failed, use this helper instead.
    """
    tasks=[asyncio.create_task(aw) for aw in aws]
    try:
        return await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        raise
