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


async def query_doi(session: ClientSession, doi: str) -> dict:
    """
    50/s rate limit
    cannot use "select"
    'select': ('DOI,abstract,author,volume,title,issue,'
               'container-title,published')}
    """
    params = {'mailto': EMAIL}
    await asyncio.sleep(0.022)
    async with session.get(QUERY_URL + doi, params=params) as resp:
        if resp.status != 200:
            print((await resp.text()))
            return {}
        r = await resp.json()
        msg = r['message']
        # pprint(r)
        if 'DOI' not in msg:
            pprint(msg)
        if doi != msg['DOI']:
            log.error('bad record')
            return {}
        else:
            return msg


def fill_field(record: Result, msg: dict) -> Result:
    record.abstract = msg.get('abstract', '')
    if len(msg['author']) > 0:
        author = list()
        for name in msg['author']:
            if 'given' in name and 'family' in name:
                author.append(f"{name['given']} {name['family']}")
        record.author = ','.join(author)
    if ('created' in msg and 'date-parts' in msg['created'] and
            len(msg['created']['date-parts']) > 0):
        record.pub_date = '/'.join(
            [str(_) for _ in msg['created']['date-parts'][0]])
    record.issue = msg.get('issue', '')
    if len(msg['container-title']) > 0:
        record.journal_name = msg['container-title'][0]
    if len(msg['title']) > 0:
        record.title = msg['title'][0]
    record.volume = msg.get('volume', '')
    return record


async def test(doi='10.3732/ajb.1400290'):
    record = Result(doi=doi)
    r = await query_doi(doi)
    new_record = fill_field(record, r)
    print(new_record)


async def main():
    file_list = list(Path('result').glob('*.result.json'))
    for result_json in file_list:
        session = ClientSession()
        new_result = result_json.with_suffix('.json.new')
        # new_result = Path(str(result_json).replace( '.result.json', '.new_result.json'))
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
                msg = await query_doi(session, record.doi)
                if not msg:
                    continue
                try:
                    record = fill_field(record, msg)
                except KeyError:
                    print(msg)
                    raise Exception
                print(record)
            new_result_list.append(record.to_dict())
        print(new_result, len(old_records))
        await session.close()
        json.dump(new_result_list, open(new_result, 'w'), indent=True)


asyncio.run(main())