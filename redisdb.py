from redis import asyncio as aioredis

r = aioredis.from_url('redis://localhost')


async def add_user(user_Id, first_name, last_name):
    user = await r.get("user:{}".format(user_Id))
    if user is None:
        await r.set("user:{}".format(user_Id), "{} {}".format(first_name, last_name))
    else:
        print(user)
