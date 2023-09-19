import asyncio
import logging
import json
from pathlib import Path

import aiohttp

from utils import get_doi, Result, download
from utils import filter_tree_from_zip
from utils import OUT_FOLDER

DRYAD_SERVER = 'https://datadryad.org/api/v2'
NEXUS_SUFFIX = '.nex,.nexus'.split(',')
log = logging.getLogger('fetch_tree')

test_doi = ['10.1101/2020.10.08.331355',
            '10.1111/jbi.13789',
            '10.1111/njb.03941',
            '10.3767/persoonia.2018.41.01',
            '10.1206/0003-0090.457.1.1',
            '10.3897/bdj.5.e12581',
            '10.1093/sysbio/49.2.278',
            '10.1098/rspb.2021.2178',
            '10.1111/evo.12614']


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


def get_dryad_url(identifier: str) -> str:
    # dryad doi looks lie 'doi:10.5061/dryad.1g1jwstss'
    # convert dryad doi to dryad download url
    # dryad requires escaped url
    dryad_doi = identifier.replace(':', '%3A').replace('/', '%2F')
    download_url = f'{DRYAD_SERVER}/datasets/{dryad_doi}/download'
    return download_url


async def search_in_dryad(session: aiohttp.ClientSession, headers: dict,
                          q: str, page=1, per_page=2) -> dict:
    # search in dryad, return json dict
    search_url = f'{DRYAD_SERVER}/search'
    params = {'q': q, 'page': page, 'per_page': per_page}
    async with session.get(search_url, params=params, headers=headers) as resp:
        if not resp.ok:
            raise ConnectionError(resp.status)
        return await resp.json()


def parse_result(result: dict) -> (str, str, str, str, int, int):
    empty_result = ('', '', '', '', -1, -1)
    count = result['count']
    total = result['total']
        # if count > 1:
        #     # bad search result
        #     return empty_result
    if count == 0:
        yield empty_result
    for dataset in result['_embedded']['stash:datasets']:
        identifier = dataset['identifier']
        # dataset title, not paper's
        title = dataset['title']
        related_work = dataset.get('relatedWorks', None)
        if related_work is None:
            doi_ = ''
        else:
            doi_ = related_work[0]['identifier']
        size = dataset.get('storageSize', 0)
        yield identifier, title, size, doi_, count, total


def write_tree(result, doi, bin_data) -> None:
    out_folder = OUT_FOLDER / get_doi(doi, doi_type='folder')
    out_folder.mkdir(exist_ok=True)
    tree_files = filter_tree_from_zip(bin_data, out_folder)
    result.add_trees(tree_files)


async def search_doi_in_dryad(session: aiohttp.ClientSession, doi: str,
                              headers: dict) -> (str, str, int):
    result = await search_in_dryad(session, headers, doi)
    # if more than 2 result for one doi, only accept the first
    identifier, title, size, *_ = next(parse_result(result))
    return identifier, title, size


async def search_journal_in_dryad(session: aiohttp.ClientSession,
                                  headers: dict, journal: str):
    results = list()
    output_json = journal.replace(' ', '_') + '.result.json'
    if Path(output_json).exists():
        log.info(f'{journal} already searched.')
        return ''
    count_have_tree = 0
    max_per_page = 100
    try_search_result = await search_in_dryad(session, headers, journal, page=1,
                                              per_page=1)
    *_, count, total = next(parse_result(try_search_result))
    if count == 0:
        log.error(f'0 record found for {journal}')
        return ''
    log.info(f'Got {total} records from journal {journal}')
    for page in range(1, total//max_per_page + 2):
        log.info(f'{page}-{page*max_per_page}')
        search_result = await search_in_dryad(session, headers, journal,
                                              page=page, per_page=max_per_page)
        for n, record in enumerate(parse_result(search_result)):
            identifier, title, size, doi_, count, total = record
            log.info(f'{n}\t{identifier}')
            if identifier == '':
                continue
            result = Result(title, identifier, doi_)
            download_url = get_dryad_url(identifier)
            ok, bin_data = await download(session, download_url, size,
                                          headers=headers)
            if not ok:
                continue
            else:
                write_tree(result, doi_, bin_data)
                count_have_tree += 1
                results.append(result.to_dict())
    log.info(f'{count_have_tree} have trees')
    log.info(f'Writing results {output_json}')
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=True)


async def get_trees_dryad(session: aiohttp.ClientSession, doi_raw: str,
                          headers: dict) -> Result:
    doi = get_doi(doi_raw)
    identifier, title, size = await search_doi_in_dryad(session, doi,
                                                        headers=headers)
    result = Result(title, identifier, doi)
    if identifier == '':
        return result
    download_url = get_dryad_url(identifier)
    ok, bin_data = await download(session, download_url, size,
                                  headers=headers)
    if not ok:
        return result
    else:
        write_tree(result, doi, bin_data)
    return result


async def dryad_main(doi_list: list) -> tuple:
    headers = await get_api_token()
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_dryad(session, doi, headers) for doi in doi_list])
    for i in results:
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return results


if __name__ == '__main__':
    asyncio.run(dryad_main(test_doi))
