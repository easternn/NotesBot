import asyncio
import telegram
import redisdb
from random import shuffle

MAX_QUESTION_LENGTH = 50
MAX_ANSWER_LENGTH = 120
COM_START_OK = ''
COM_CREATE_OK = 'Введите вопрос'
COM_QUIZ_EMPTY_LIST = 'Здесь пусто :/'
COM_QUIZ_END_OK = 'Quiz закончен'
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


async def end_quiz(user_id):
    random_notes = await redisdb.get_random_qrs(user_id)
    saved = set()
    for note in random_notes:
        saved.add(note)
    notes = await redisdb.get_qrs(user_id)
    new_notes = []
    for note in notes:
        if note in saved:
            new_notes.append(note)
    await redisdb.set_qrs(user_id, new_notes)


async def show_all_notes(tg_client: telegram.Bot, user_id, notes):
    i = 0
    for note in notes:
        i += 1
        question, answer = note.split('?')
        question += '?'
        await tg_client.send_message(chat_id=user_id,
                                     text='*{}\) Вопрос:* {}\n\n*Ответ: * {}'.format(i, question, answer),
                                     parse_mode='MarkdownV2')


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
    notes = await redisdb.get_qrs(user_id)
    await show_all_notes(tg_client, user_id, notes)


async def COM_quiz(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    notes = await redisdb.get_qrs(user_id)
    if len(notes) == 0:
        await tg_client.send_message(chat_id=user_id, text=COM_QUIZ_EMPTY_LIST)
        return
    await redisdb.set_status(user_id, 'PROCESS')
    shuffle(notes)
    await redisdb.set_random_qrs(user_id, notes)
    current_qr = (await redisdb.get_processed_random_qr(user_id))[0]
    question = current_qr.split('?')[0] + "?"
    await tg_client.send_message(chat_id=user_id, text='*Вопрос: * {}'.format(question), parse_mode='MarkdownV2')
    await redisdb.set_status(user_id, 'Testing')


async def COM_quiz_end(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    await end_quiz(user_id)
    await tg_client.send_message(chat_id=user_id, text=COM_QUIZ_END_OK)
    await redisdb.set_status(user_id, 'Default')


async def COM_next(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    status = await redisdb.get_status(user_id)
    if status != 'Testing':
        return
    current_qr = (await redisdb.get_processed_random_qr(user_id))[0]
    answer = current_qr.split('?')[1]
    await tg_client.send_message(chat_id=user_id, text='*Ответ: * {}'.format(answer), parse_mode='MarkdownV2')
    await redisdb.move_random_forward(user_id)
    current_qr = (await redisdb.get_processed_random_qr(user_id))[0]
    print(current_qr)
    question = current_qr.split('?')[0] + "?"
    await tg_client.send_message(chat_id=user_id, text='*Вопрос: * {}'.format(question), parse_mode='MarkdownV2')


async def COM_erase(tg_client: telegram.Bot, upd: telegram.Update):
    user_id = upd.effective_chat.id
    status = await redisdb.get_status(user_id)
    if status != 'Testing':
        return
    current_qr = (await redisdb.get_processed_random_qr(user_id))[0]
    answer = current_qr.split('?')[1]
    await tg_client.send_message(chat_id=user_id, text='*Ответ: * {}'.format(answer), parse_mode='MarkdownV2')
    await redisdb.move_random_forward_and_erase(user_id)
    if await redisdb.get_random_qrs_length(user_id) == 0:
        await COM_quiz_end(tg_client, upd)
        return
    current_qr = (await redisdb.get_processed_random_qr(user_id))[0]
    question = current_qr.split('?')[0] + "?"
    await tg_client.send_message(chat_id=user_id, text='*Вопрос: * {}'.format(question), parse_mode='MarkdownV2')


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
        return
    user_id = upd.effective_chat.id
    text = upd.message.text
    status = await redisdb.get_status(user_id)
    if status == 'PROCESS' and text != '/start':
        return
    if text == '/start':
        if status == 'Testing':
            await COM_quiz_end(tg_client, upd)
        await COM_start(tg_client, upd)
    elif text == '/create':
        if status == 'Testing':
            await COM_quiz_end(tg_client, upd)
        await COM_create(tg_client, upd)
    elif text == '/all':
        await COM_all(tg_client, upd)
    elif text == '/quiz':
        await COM_quiz(tg_client, upd)
    elif text == '/next':
        await COM_next(tg_client, upd)
    elif text == '/erase':
        await COM_erase(tg_client, upd)
    elif text == '/quiz_end':
        await COM_quiz_end(tg_client, upd)
    else:  # TEXT
        if status == 'Awaiting-question':
            await AFTER_create_question(tg_client, upd)
        elif status == 'Awaiting-answer':
            await AFTER_create_answer(tg_client, upd)

    await redisdb.debug(user_id) # DEBUG


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
