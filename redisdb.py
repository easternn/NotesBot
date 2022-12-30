from redis import asyncio as aioredis

r = aioredis.from_url('redis://localhost', decode_responses=True)


async def debug(user_Id):
    name = await r.get("user:{}".format(user_Id))
    processed_q = await r.get("user:{}:q".format(user_Id))
    qrs = await r.lrange("user:{}:qrs".format(user_Id), 0, -1)
    status = await r.get("user:{}:status".format(user_Id))
    print("##########")
    print("Used-id: {}".format(user_Id))
    print("Name: {}".format(name))
    print("processed_q: {}".format(processed_q))
    print(qrs)
    print("status: {}".format(status))
    print("##########")
    print()


async def get_status(user_Id):
    return await r.get("user:{}:status".format(user_Id))


async def set_status(user_Id, status):
    await r.set("user:{}:status".format(user_Id), status)


async def add_user(user_Id, first_name, last_name):
    user = await r.get("user:{}".format(user_Id))
    if user is None:
        await r.set("user:{}".format(user_Id), "{} {}".format(first_name, last_name))


async def add_question(user_Id, question):
    await r.set("user:{}:q".format(user_Id), question)


async def add_answer(user_Id, answer):
    question = await r.get("user:{}:q".format(user_Id))
    await r.rpush("user:{}:qrs".format(user_Id), "{}{}".format(question, answer))


async def get_notes(user_Id):
    return await r.lrange("user:{}:qrs".format(user_Id), 0, -1)
