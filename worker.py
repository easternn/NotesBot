import asyncio
import telegram
import redisdb


async def handle_update(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    text = upd.message.text
    if text == '/start':
        await redisdb.add_user(user_id, upd.effective_chat.first_name, upd.effective_chat.last_name)


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, concurrent_workers: int):
        self.tg_client = telegram.Bot(token)
        self.queue = queue
        self.concurrent_workers = concurrent_workers

    async def _worker(self):
        while True:
            upd = await self.queue.get()
            await handle_update(self.tg_client, upd)

    async def start(self):
        for _ in range(self.concurrent_workers):
            asyncio.create_task(self._worker())
