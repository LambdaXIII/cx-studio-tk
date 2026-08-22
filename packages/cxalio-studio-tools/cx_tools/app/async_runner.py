"""手动 event loop 运行协程，不覆盖 SIGINT handler。

asyncio.run() 在 Python 3.13 会安装自己的 SIGINT handler，
覆盖应用层注册的 signal.signal(SIGINT, ...)。本函数直接用
loop.run_until_complete 运行，保留应用层的信号 handler。
"""

import asyncio


def run_async(coro):
    """在手动 event loop 中运行协程，不覆盖 SIGINT handler。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)
