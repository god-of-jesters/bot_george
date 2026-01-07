from repo.user_repo import *
from repo.file_repo import *
import asyncio

async def test():
    got = await get_user(12)
    print("GET =", got)

asyncio.run(test())
