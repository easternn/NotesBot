from redis import asyncio as aioredis

r = aioredis.from_url('redis://localhost', decode_responses=True)


async def debug(user_Id):
    name = await r.get("user:{}".format(user_Id))
    processed_q = await r.get("user:{}:q".format(user_Id))
    qrs = await r.lrange("user:{}:qrs".format(user_Id), 0, -1)
    random_qrs = await r.lrange("user:{}:random_qrs".format(user_Id), 0, -1)
    random_id = await r.get("user:{}:random_id".format(user_Id))
    status = await r.get("user:{}:status".format(user_Id))
    print("##########")
    print("Used-id: {}".format(user_Id))
    print("Name: {}".format(name))
    print("processed_q: {}".format(processed_q))
    print("qrs: {}".format(qrs))
    print("random_qrs: {}".format(random_qrs))
    print("random_id: {}".format(random_id))
    print("status: {}".format(status))
    print("##########")
    print()


async def get_status(user_Id):
    return await r.get("user:{}:status".format(user_Id))


async def get_notes(user_Id):
    return await r.lrange("user:{}:qrs".format(user_Id), 0, -1)


async def get_processed_random_qr(user_Id):
    random_id = await r.get("user:{}:random_id".format(user_Id))
    return await r.lrange("user:{}:random_qrs".format(user_Id), random_id, random_id)


async def set_status(user_Id, status):
    await r.set("user:{}:status".format(user_Id), status)


async def set_random_qrs(user_Id, notes):
    await r.delete("user:{}:random_qrs".format(user_Id))
    for note in notes:
        await r.rpush("user:{}:random_qrs".format(user_Id), note)
    await r.set("user:{}:random_id".format(user_Id), 0)


async def add_user(user_Id, first_name, last_name):
    user = await r.get("user:{}".format(user_Id))
    if user is None:
        await r.set("user:{}".format(user_Id), "{} {}".format(first_name, last_name))


async def add_question(user_Id, question):
    await r.set("user:{}:q".format(user_Id), question)


async def add_answer(user_Id, answer):
    question = await r.get("user:{}:q".format(user_Id))
    await r.rpush("user:{}:qrs".format(user_Id), "{}{}".format(question, answer))


async def move_random_forward(user_Id):
    random_id = int(await r.get("user:{}:random_id".format(user_Id)))
    length = await r.llen("user:{}:random_qrs".format(user_Id))
    random_id = (random_id + 1) % length
    await r.set("user:{}:random_id".format(user_Id), random_id)