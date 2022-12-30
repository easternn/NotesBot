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


async def validate_answer(answer):
    return True


async def validate_question(question):
    return True


async def add_user(user_Id, first_name, last_name):
    print("START add_user")
    await debug(user_Id)
    user = await r.get("user:{}".format(user_Id))
    if user is None:
        await r.set("user:{}".format(user_Id), "{} {}".format(first_name, last_name))
    await r.set("user:{}:status".format(user_Id), "Default")
    print("END add_user")
    await debug(user_Id)


async def plan_question(user_Id):
    print("START plan_question")
    await debug(user_Id)
    await r.set("user:{}:status".format(user_Id), "Awaiting-question")
    print("END plan_question")
    await debug(user_Id)


async def add_question(user_Id, question):
    print("START add_question")
    await debug(user_Id)
    status = await r.get("user:{}:status".format(user_Id))
    if status != "Awaiting-question":
        return
    if not await validate_question(question):
        return
    await r.set("user:{}:q".format(user_Id), question)
    await r.set("user:{}:status".format(user_Id), "Awaiting-response")
    print("END add_question")
    await debug(user_Id)


async def add_answer(user_Id, answer):
    print("START add_answer")
    await debug(user_Id)
    status = await r.get("user:{}:status".format(user_Id))
    if status != "Awaiting-response":
        return
    if not await validate_answer(answer):
        return
    question = await r.get("user:{}:q".format(user_Id))
    await r.rpush("user:{}:qrs".format(user_Id), "{}{}".format(question, answer))
    await r.set("user:{}:status".format(user_Id), "Default")
    print("END add_answer")
    await debug(user_Id)


async def get_notes(user_Id):
    qrs = await r.lrange("user:{}:qrs".format(user_Id), 0, -1)
    return qrs
