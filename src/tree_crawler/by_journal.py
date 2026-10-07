import asyncio

import aiohttp
from pathlib import Path

from dryad import search_journal_in_dryad, get_api_token
from global_vars import log

async def main():
    journal_list = Path('data/journal_list_dryad.txt').resolve()
    since = '2025-01-01'
    with open(journal_list, 'r') as _:
        journal_list = tuple([i.strip() for i in _.readlines()])
    async with aiohttp.ClientSession() as session:
        for journal in reversed(journal_list):
            log.info(f'Start searching {journal}')
            await search_journal_in_dryad(session, journal, since)


if __name__ == '__main__':
    asyncio.run(main())