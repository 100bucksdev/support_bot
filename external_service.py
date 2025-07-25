import asyncio
from typing import Literal

from aiohttp import ClientSession, ClientTimeout

from config import CHATS_MANAGER_URL

async def make_request(
    url: str,
    method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET',
    data: dict = None,
    params: dict = None,
    base_url: str = CHATS_MANAGER_URL,
) -> dict:
    attempts = 3
    attempt = 0

    url = f'{base_url}{url}'

    while True:
        try:
            async with ClientSession(timeout=ClientTimeout(10)) as session:
                async with session.request(method, url, json=data, params=params) as response:
                    content = await response.json()
                    print(content)
                    return {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'body': content,
                    }
        except Exception as e:
            print(e)
            attempt += 1
            await asyncio.sleep(1)
            if attempt == attempts:
                return {
                        'status': 500,
                        'headers': {},
                        'body': {},
                }