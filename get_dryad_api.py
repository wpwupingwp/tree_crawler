import asyncio
import logging

import aiohttp

log = logging.getLogger('fetch_tree')


async def get_api_token():
    with open('key.txt', 'r') as f:
        client_id = f.readline().strip()
        client_secret = f.readline().strip()
    url = 'https://datadryad.org/oauth/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'charset': 'UTF-8'}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, params={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }) as resp:
            if not resp.ok:
                log.warning(f'Get token fail {resp.status}')
                return None
            return await resp.json()

if __name__ == '__main__':
    result = asyncio.run(get_api_token())
    print(result)