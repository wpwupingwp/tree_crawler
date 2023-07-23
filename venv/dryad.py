import aiohttp
import aiofile
import asyncio
from urllib.request import quote
import json

server = 'https://datadryad.org/api/v2'
MAX_SIZE = 1024*1024*100
q = 'Contrasting physiological traits of shade tolerance in Pinus and Podocarpaceae native to a tropical Vietnamese forest: Insight from an aberrant flat-leaved pine'


def get_dryad_url(identifier='doi:10.5061/dryad.1g1jwstss') -> str:
    # dryad requires escaped url
    doi = identifier.replace(':', '%3A').replace('/', '%2F')
    doi_url = f'{server}/datasets/{doi}'
    print(identifier, doi_url)
    return doi_url


async def search_title(session:aiohttp.ClientSession, title: str) -> (str, int):
    search_url = f'{server}/search'
    params = {'q': title, 'page': 1, 'per_page': 2}
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


async def download(session: aiohttp.ClientSession, dataset_url: str,
                   filename: str) -> (bool, str):
    download_url = f'{dataset_url}/download'
    async with session.get(url) as resp:
        if not resp.ok:
            return False, ''
        bin = await resp.content()
    async with aiofile.async_open(filename, 'wb') as handle:
        handle.write(bin)
    return True, filename


async def main():
    async with aiohttp.ClientSession() as session:
        identifier, size = await search_title(session, q)
        if size > MAX_SIZE:
            print(identifier, 'too big', size, 'bp')
            return
        dataset_url = get_dryad_url(identifier)
        filename = await download(session, dataset_url, filename)

asyncio.run(main())