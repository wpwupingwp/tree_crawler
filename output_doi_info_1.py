#!/usr/bin/python3
import json
import asyncio
import logging
from pathlib import Path

from aiohttp import ClientSession
import coloredlogs

from utils import get_doi, pprint, Result
from global_vars import log

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
    proxy = 'http://127.0.0.1:7890'
    await asyncio.sleep(0.03)
    async with session.get(QUERY_URL + doi, params=params, proxy=proxy) as resp:
        if resp.status != 200:
            print((await resp.text()))
            return {}
        r = await resp.json()
        msg = r['message']
        # pprint(r)
        if 'DOI' not in msg:
            print(doi, 'not found')
            # pprint(msg)
            return {}
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


async def test(session, doi='10.3732/ajb.1400290'):
    record = Result(doi=doi)
    r = await query_doi(session, doi)
    new_record = fill_field(record, r)
    print(new_record)


async def batch_query_doi():
    # doi, year
    session = ClientSession()
    result = []
    with open('R:\\doi_list.csv', 'r') as _, open('R:\\doi_result.csv', 'a') as out:
        for line in _:
            doi, year_db = line.strip().split(',')
            try:
                msg = await query_doi(session, doi)
            except Exception as e:
                await asyncio.sleep(0.1)
                out.write(f'retry {doi}\n')
                continue
            if 'published-print' in msg:
                year_doi = msg['published-print']['date-parts'][0][0]
            elif 'published-online' in msg:
                year_doi = msg['published-online']['date-parts'][0][0]
            else:
                year_doi = 0
            print(doi, year_db, msg.get('DOI', ''), year_doi)
            year_doi = str(year_doi)
            if year_doi != '0' and year_doi != year_db and year_db == '2022':
                result.append((doi, year_doi))
                print('write')
                out.write(f'{doi},{year_doi}\n')
                out.flush()
    await session.close()


async def main():
    # use api to fetch article info by doi
    file_list = list(Path('.').glob('*.result.json'))
    for result_json in file_list:
        session = ClientSession()
        new_result = result_json.with_suffix('.json.new')
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
# asyncio.run(batch_query_doi())
