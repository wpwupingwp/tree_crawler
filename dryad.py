import asyncio
from time import sleep

import aiohttp

from utils import get_doi, Result, download
from utils import filter_tree_from_zip
from utils import OUT_FOLDER

DRYAD_SERVER = 'https://datadryad.org/api/v2'
NEXUS_SUFFIX = '.nex,.nexus'.split(',')

test_doi = ['10.1101/2020.10.08.331355',
            '10.1111/jbi.13789',
            '10.1111/njb.03941',
            '10.3767/persoonia.2018.41.01',
            '10.1206/0003-0090.457.1.1',
            '10.3897/bdj.5.e12581',
            '10.1093/sysbio/49.2.278',
            '10.1098/rspb.2021.2178',
            '10.1111/evo.12614']


def get_dryad_url(identifier: str) -> str:
    # dryad doi looks lie 'doi:10.5061/dryad.1g1jwstss'
    # convert dryad doi to dryad download url
    # dryad requires escaped url
    dryad_doi = identifier.replace(':', '%3A').replace('/', '%2F')
    download_url = f'{DRYAD_SERVER}/datasets/{dryad_doi}/download'
    return download_url


async def search_doi_in_dryad(session: aiohttp.ClientSession, doi: str) -> (
        str, str, int):
    search_url = f'{DRYAD_SERVER}/search'
    # todo: search doi?
    params = {'q': doi, 'page': 1, 'per_page': 2}
    async with session.get(search_url, params=params) as resp:
        if not resp.ok:
            raise Exception(resp.status)
        result = await resp.json()
        count = result['count']
        if count == 0 or count > 1:
            # bad search result
            return '', '', -1
        # print(json.dumps(result, indent=True))
        identifier = result['_embedded']['stash:datasets'][0]['identifier']
        # dataset title, not paper's
        title = result['_embedded']['stash:datasets'][0]['title']
        related_work = result['_embedded']['stash:datasets'][0].get(
            'relatedWorks', None)
        if related_work is None:
            doi = ''
        else:
            doi = related_work[0]['identifier']
        size = result['_embedded']['stash:datasets'][0]['storageSize']
        return identifier, title, size


async def get_trees_dryad(session, doi_raw: str) -> Result:
    doi = get_doi(doi_raw)
    identifier, title, size = await search_doi_in_dryad(session, doi)
    result = Result(title, identifier, doi)
    if identifier == '':
        return result
    download_url = get_dryad_url(identifier)
    ok, bin_data = await download(session, download_url, size)
    if not ok:
        return result
    else:
        out_folder = OUT_FOLDER / get_doi(doi, doi_type='folder')
        out_folder.mkdir(exist_ok=True)
        tree_files = filter_tree_from_zip(bin_data, out_folder)
        result.add_trees(tree_files)
    return result


async def dryad_main(doi_list: list) -> list:
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_dryad(session, doi) for doi in doi_list])
    for i in results:
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return results


if __name__ == '__main__':
    asyncio.run(dryad_main(test_doi))