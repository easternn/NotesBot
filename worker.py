import asyncio
import telegram


async def handle_update(upd):
    print("before", upd)
    await asyncio.sleep(1)
    print("after", upd)


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, concurrent_workers: int):
        self.tg_client = telegram.Bot(token)
        self.queue = queue
        self.concurrent_workers = concurrent_workers

    async def _worker(self):
        while True:
            upd = await self.queue.get()
            await handle_update(upd)

    async def start(self):
        for _ in range(self.concurrent_workers):
            asyncio.create_task(self._worker())
