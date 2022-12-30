import asyncio
import os

from poller import Poller
from worker import Worker


async def start():
    q = asyncio.Queue()
    poller = Poller(os.getenv("BOT_TOKEN"), q)
    await poller.start()
    worker = Worker(os.getenv("BOT_TOKEN"), q, 2)
    await worker.start()


def run():
    loop = asyncio.get_event_loop()

    try:
        print('bot has been started')
        loop.create_task(start())
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    run()
