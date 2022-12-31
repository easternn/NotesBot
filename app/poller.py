import asyncio
import telegram


class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.tg_client = telegram.Bot(token)
        self.queue = queue

    async def _worker(self):
        offset = 0
        while True:
            res = await self.tg_client.get_updates(offset=offset, timeout=60)
            for u in res:
                offset = u.update_id + 1
                # print(u)
                self.queue.put_nowait(u)

    async def start(self):
        asyncio.create_task(self._worker())
