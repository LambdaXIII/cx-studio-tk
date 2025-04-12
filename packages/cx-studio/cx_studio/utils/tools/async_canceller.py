import asyncio


class AsyncCanceller:
    def __init__(self):
        self._cancel_event = asyncio.Event()
        self._checking_cond = asyncio.Condition()

    def cancel(self):
        self._cancel_event.set()

    async def is_cancelling_async(self,auto_skip=False):
        if auto_skip and self._checking_cond.locked():
            return False
        
        result = False
        async with self._checking_cond:
            result = self.is_cancelling()
        return result
            

    def is_cancelling(self):
        result = False
        if self._cancel_event.is_set():
                result = True
                self._cancel_event.clear()
        return result
            
