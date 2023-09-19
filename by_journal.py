import asyncio
import logging

import aiohttp
import coloredlogs

from dryad import search_journal_in_dryad, get_api_token

FMT = '%(asctime)s %(levelname)-8s %(message)s'
DATEFMT = '%H:%M:%S'
logging.basicConfig(format=FMT, datefmt=DATEFMT, level=logging.INFO)
log = logging.getLogger('fetch_tree')
fmt = logging.Formatter(FMT, DATEFMT)
file_handler = logging.FileHandler('log.txt', 'a')
file_handler.setFormatter(fmt)
log.addHandler(file_handler)
coloredlogs.install(level=logging.INFO, fmt=FMT, datefmt=DATEFMT)


async def main():
    with open('journal_list_dryad.txt', 'r') as _:
        journal_list = tuple([i.strip() for i in _.readlines()])
    headers = await get_api_token()
    async with aiohttp.ClientSession() as session:
        for journal in reversed(journal_list):
            log.info(f'Start searching {journal}')
            await search_journal_in_dryad(session, headers, journal)


if __name__ == '__main__':
    asyncio.run(main())