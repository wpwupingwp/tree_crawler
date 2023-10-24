#!/usr/bin/python3
import json
import asyncio
import logging
from pathlib import Path

from aiohttp import ClientSession
import coloredlogs

from utils import get_doi, pprint, Result

FMT = '%(asctime)s %(levelname)-8s %(message)s'
DATEFMT = '%H:%M:%S'
logging.basicConfig(format=FMT, datefmt=DATEFMT, level=logging.INFO)
log = logging.getLogger('fetch_tree')
fmt = logging.Formatter(FMT, DATEFMT)
file_handler = logging.FileHandler('log.txt', 'a')
file_handler.setFormatter(fmt)
log.addHandler(file_handler)
coloredlogs.install(level=logging.INFO, fmt=FMT, datefmt=DATEFMT)
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
        async with session.get(QUERY_URL + doi, params=params) as resp:
            r = await resp.json()
            if r['status'] != 'ok':
                print(r)
            msg = r['message']
            # pprint(r)
            if 'DOI' not in msg:
                pprint(msg)
            if doi != msg['DOI']:
                log.error('bad record')
                return {}
            else:
                return msg


def fill_field(record: Result, r: dict) -> Result:
    record.abstract = r['abstract']
    record.author = ','.join([f'{_["given"]} {_["family"]}'
                              for _ in r['author']])
    record.date = '/'.join([str(_) for _ in r['created']['date-parts'][0]])
    record.issue = r['issue']
    record.journal = r['container-title'][0]
    record.title = r['title'][0]
    record.volume = r['volume']
    return record


async def test(doi='10.3732/ajb.1400290'):
    record = Result(doi=doi)
    r = await query_doi(doi)
    new_record = fill_field(record, r)
    print(new_record)


async def main():
    file_list = list(Path('result').glob('*.result.json'))
    for result_json in file_list:
        new_result = Path(str(result_json).replace(
            '.result.json', '.new_result.json'))
        new_result_list = list()
        old_records = json.load(open(result_json, 'r'))
        for raw_record in old_records:
            record = Result(**raw_record)
            if len(record.tree_files) == 0:
                continue
            # record from dryad may have empty fields
            if ('/dryad' in record.author and
                    len(record.identifier) == 0 and
                    len(record.title) == 0 and
                    len(record.journal_name) == 0 and
                    len(record.doi) != 0):
                print(record)
                record.identifier = record.author
                record.doi = get_doi(record.doi)
                r = await query_doi(record.doi)
                record = fill_field(record, r)
                print(record)
            new_result_list.append(record)
        print(new_result, len(old_records))


asyncio.run(main())