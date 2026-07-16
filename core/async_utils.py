import asyncio

from functools import partial

async def run_sync_in_thread ( func, *args, **kwargs ) :

        """
    Runs a synchronous (blocking) function inside a thread pool,
    so it doesn't block the asyncio event loop.

    USE THIS FOR:
        - yfinance calls (no async version exists)
        - tavily-python SDK calls (no async version)
        - Any other sync-only library

    DO NOT USE FOR:
        - LangChain LLM calls → use llm.ainvoke() instead (true async)
        - httpx calls → use async with httpx.AsyncClient() instead
        - Redis calls → redis-py has aioredis for true async

    The difference:
        Thread pool: offloads blocking wait to an OS thread (costs RAM)
        True async:  OS kernel watches the connection (costs almost nothing)
    """
        
        loop = asyncio . get_event_loop ()
        # get_event_loop gets the currently running event loop

        func_with_args = partial ( func, *args, **kwargs )
        # partial pre fills the functions argument so we can pass it to run_in_exector without arguments

        return await loop . run_in_executor ( None, func_with_args )
    # run_in_executor(None, ...) = "run this in the default thread pool"
    # 'await' here pauses THIS coroutine, but other coroutines
    # can keep running while this thread pool work happens