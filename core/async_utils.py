import asyncio

from functools import partial

async def run_sync_in_thread ( func, *args, **kwargs ) :

        """
    Runs a synchronous (blocking) function inside a thread pool,
    so it doesn't block the asyncio event loop.

    This is the bridge between sync libraries (yfinance, tavily)
    and our async agent functions.
    """
        
        loop = asyncio . get_event_loop ()
        # get_event_loop gets the currently running event loop

        func_with_args = partial ( func, *args, **kwargs )
        # partial pre fills the functions argument so we can pass it to run_in_exector without arguments

        return await loop . run_in_executor ( None, func_with_args )
    # run_in_executor(None, ...) = "run this in the default thread pool"
    # 'await' here pauses THIS coroutine, but other coroutines
    # can keep running while this thread pool work happens