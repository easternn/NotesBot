import asyncio
import telegram
import redisdb

MAX_QUESTION_LENGTH = 50
MAX_ANSWER_LENGTH = 120
COM_START_OK = ''
COM_CREATE_OK = 'Введите вопрос'
AFTER_CREATE_QUESTION_OK = 'Ваш ответ'
AFTER_CREATE_QUESTION_LONG = 'Вопрос не должен превышать {} символов'.format(MAX_QUESTION_LENGTH)
AFTER_CREATE_QUESTION_QM = 'Должен стоять единственный вопросительный знак - вконце'
AFTER_CREATE_ANSWER_OK = 'Отлично! Запись сохранена'
AFTER_CREATE_ANSWER_LONG = 'Ответ не должен превышать {} символов'.format(MAX_ANSWER_LENGTH)
AFTER_CREATE_ANSWER_QM = 'В ответе не должно быть вопросительных знаков'


def validate_answer(answer):
    if len(answer) > MAX_ANSWER_LENGTH:
        return -1
    if answer.count('?') != 0:
        return -2
    return 0


def validate_question(question):
    if len(question) > MAX_QUESTION_LENGTH:
        return -1
    if question.count('?') != 1 or question[-1] != '?':
        return -2
    return 0


async def show_all_notes(tg_client: telegram.Bot, user_id, notes):
    for note in notes:
        question, answer = note.split('?')
        question += '?'
        await tg_client.send_message(chat_id=user_id, text='{}\n\n{}'.format(question, answer))


async def COM_start(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    await redisdb.add_user(user_id, upd.effective_chat.first_name, upd.effective_chat.last_name)
    await redisdb.set_status(user_id, 'Default')


async def COM_create(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    await tg_client.send_message(chat_id=user_id, text=COM_CREATE_OK)
    await redisdb.set_status(user_id, 'Awaiting-question')


async def COM_all(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    notes = await redisdb.get_notes(user_id)
    await show_all_notes(tg_client, user_id, notes)
    await redisdb.set_status(user_id, 'Default')


async def AFTER_create_question(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    text = upd.message.text
    valid = validate_question(text)
    if valid == 0:
        await redisdb.add_question(user_id, text)
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_QUESTION_OK)
        await redisdb.set_status(user_id, 'Awaiting-answer')
    elif valid == -1:
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_QUESTION_LONG)
        await asyncio.sleep(1)
        await tg_client.send_message(chat_id=user_id, text=COM_CREATE_OK)
    elif valid == -2:
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_QUESTION_QM)
        await asyncio.sleep(1)
        await tg_client.send_message(chat_id=user_id, text=COM_CREATE_OK)


async def AFTER_create_answer(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    text = upd.message.text
    valid = validate_answer(text)
    if valid == 0:
        await redisdb.add_answer(user_id, text)
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_ANSWER_OK)
        await redisdb.set_status(user_id, 'Default')
    elif valid == -1:
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_ANSWER_LONG)
        await asyncio.sleep(1)
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_QUESTION_OK)
    elif valid == -2:
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_ANSWER_QM)
        await asyncio.sleep(1)
        await tg_client.send_message(chat_id=user_id, text=AFTER_CREATE_QUESTION_OK)


async def handle_update(tg_client: telegram.Bot, upd: telegram.Update):
    if upd is None:
        print('dsfds')
        return
    user_id = upd.effective_chat.id
    text = upd.message.text
    await redisdb.debug(user_id)
    if text == '/start':
        await COM_start(tg_client, upd)
    elif text == '/create':
        await COM_create(tg_client, upd)
    elif text == '/all':
        await COM_all(tg_client, upd)
    else:   # TEXT
        status = await redisdb.get_status(user_id)
        if status == 'Awaiting-question':
            await AFTER_create_question(tg_client, upd)
        elif status == 'Awaiting-answer':
            await AFTER_create_answer(tg_client, upd)


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
