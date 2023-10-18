#!/usr/bin/python3

import json
import asyncio
from pathlib import Path

from aiohttp import ClientSession

from utils import get_doi, pprint


QUERY_URL = 'https://api.crossref.org/works/'
EMAIL = 'wpwupingwp@outlook.com'


async def query_doi(doi: str):
    """
    50/s rate limit
    cannot use "select"
    'select': ('DOI,abstract,author,volume,title,issue,'
               'container-title,published')}
    """
    params = {'mailto': EMAIL}
    async with ClientSession() as session:
        await asyncio.sleep(0.022)
        async with session.get(QUERY_URL+doi, params=params) as resp:
            r = await resp.json()
            if doi != r['DOI']:
                print('bad record')
    #issue,abstract,DOI,created,title,volume,author,
    journal = container-title
    author = ','.join([f'{i["given"]} {i["family"]}' for i in author])
    title = title[0]
    date = '/'.join(created['date-parts'][0])
    pprint(r)
    pass
asyncio.run(query_doi('10.3732/ajb.1400290'))

def main():
    file_list = list(Path('result').glob('*.result.json'))
    for result_json in file_list:
        new_result = Path(str(result_json).replace(
            '.result.json', '.new_result.json'))
        old_records = json.load(open(result_json, 'r'))
        for record in old_records:
            n_trees = len(record['tree_files'])
            if n_trees == 0:
                continue
            if '/dryad' in record['author'] and len(record['identifier']) == 0:
                record['identifier'] = record['author']
            record['doi'] = get_doi(record['doi'])
            print(record)

            pass
        print(new_result, len(old_records))