import aiohttp
import asyncio
from urllib.request import quote
import json

server = 'https://datadryad.org/api/v2'
q = 'Contrasting physiological traits of shade tolerance in Pinus and Podocarpaceae native to a tropical Vietnamese forest: Insight from an aberrant flat-leaved pine'


def get_dryad_url(identifier='doi:10.5061/dryad.1g1jwstss') -> str:
    # dryad requires escaped url
    doi = identifier.replace(':', '%3A').replace('/', '%2F')
    doi_url = f'{server}/datasets/{doi}'
    print(identifier, doi_url)
    return doi_url


def download():
    pass
async def search_title(session:aiohttp.ClientSession, title: str) -> (str, int):
    search_url = f'{server}/search'
    params = {'q': title, 'page': 1, 'per_page': 1}
    async with session.get(search_url, params=params) as resp:
        if not resp.ok:
            raise Exception(resp.status)
        result = await resp.json()
        count = result['count']
        if count == 0 or count > 1:
            # bad search result
            print(f'{count=}')
            return '', -1
        identifier = result['_embedded']['stash:datasets'][0]['identifier']
        size = result['_embedded']['stash:datasets'][0]['storageSize']
        print(f'{count=},{identifier=}')
        return identifier, size


async def main():
    async with aiohttp.ClientSession() as session:
        identifier, size = await search_title(session, q)
        dataset_url = get_dryad_url(identifier)
        async with session.get(dataset_url) as resp:
            if not resp.ok:
                raise Exception(f'{resp.status}, {url}')
            json_ = await resp.json()
            print(json_)
            # print(pokemon['name'])

asyncio.run(main())