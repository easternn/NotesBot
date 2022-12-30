import asyncio
import telegram
import redisdb


async def show_all_notes(tg_client: telegram.Bot, user_id, notes):
    for note in notes:
        question, answer = note.split('?')
        question += '?'
        await tg_client.send_message(chat_id=user_id, text='{}\n\n{}'.format(question, answer))


async def handle_update(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    text = upd.message.text
    if text == '/start':
        await redisdb.add_user(user_id, upd.effective_chat.first_name, upd.effective_chat.last_name)
    elif text == '/create':
        await redisdb.plan_question(user_id)
    elif text == '/all':
        notes = await redisdb.get_notes(user_id)
        await show_all_notes(tg_client, user_id, notes)
    else:
        status = await redisdb.get_status(user_id)
        print(status)
        if status == 'Awaiting-question':
            await redisdb.add_question(user_id, text)
        elif status == 'Awaiting-response':
            await redisdb.add_answer(user_id, text)


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
