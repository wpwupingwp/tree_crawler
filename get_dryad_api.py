import asyncio
import logging

import aiohttp

log = logging.getLogger('fetch_tree')


async def get_api_token() -> dict:
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
                return {}
            access_token = (await resp.json())['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get('https://datadryad.org/api/v2/search',
                               params={'q': '10.1111/jbi.13789'},
                               headers=headers) as resp:
            if not resp.ok:
                log.error('Bad token')
                print(resp.status, resp.text)
                return {}
            else:
                result = await resp.json()
                print(result)
                log.info('Token ok')
    return headers

if __name__ == '__main__':
    result = asyncio.run(get_api_token())
    print('Got token')
    print(result)