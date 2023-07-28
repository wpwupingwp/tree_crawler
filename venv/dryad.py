from pathlib import Path
from urllib.request import quote
from zipfile import ZipFile, ZipInfo
import asyncio
import io
import json
import re
from collections import namedtuple
from dataclasses import dataclass

import aiohttp
import aiofile
import dendropy

DOI = re.compile(r'\d+\.\d+/[^ ]+')
server = 'https://datadryad.org/api/v2'
MAX_SIZE = 1024 * 1024 * 10
TREE_SUFFIX = '.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(',')
NEXUS_SUFFIX = '.nex,.nexus'.split(',')
ZIP_SUFFIX = '.zip'
OUT_FOLDER = Path(r'R:\dryad_out')
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()


@dataclass
class Result:
    title: str = ''
    identifier: str = ''
    # should be '10.xxxx/yyyyy' format
    doi: str = ''
    tree_files: tuple = tuple()

    def empty(self):
        return len(self.tree_files) == 0

    def add_trees(self, trees: list):
        self.tree_files = tuple(trees)


test_doi = ['10.1101/2020.10.08.331355',
            '10.1111/jbi.13789',
            '10.1111/njb.03941',
            '10.3767/persoonia.2018.41.01',
            '10.1206/0003-0090.457.1.1',
            '10.3897/bdj.5.e12581',
            '10.1093/sysbio/49.2.278',
            '10.1098/rspb.2021.2178',
            '10.1111/evo.12614']


def get_doi(raw_doi: str, doi_type='default') -> str:
    # doi of article
    # 10.1234/12345
    match = re.search(DOI, raw_doi)
    if match is not None:
        doi = match.group()
    else:
        doi = raw_doi
    if doi_type == 'default':
        return doi
    elif doi_type == 'with_prefix':
        return f'doi:{doi}'
    elif doi_type == 'dryad':
        return f'doi%3A{doi.replace("/", "%2F")}'
    else:
        return doi


def get_dryad_url(identifier: str) -> str:
    # dryad doi looks lie 'doi:10.5061/dryad.1g1jwstss'
    # convert dryad doi to dryad download url
    # dryad requires escaped url
    dryad_doi = identifier.replace(':', '%3A').replace('/', '%2F')
    download_url = f'{server}/datasets/{dryad_doi}/download'
    return download_url


async def search_doi(session: aiohttp.ClientSession, doi: str) -> (
        str, str, int):
    search_url = f'{server}/search'
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


async def download(session: aiohttp.ClientSession, download_url: str,
                   size: int) -> (bool, bytes):
    if size > MAX_SIZE:
        print(download_url, 'too big', size, 'bp')
        return False, b''
    print('Downloading', download_url.removesuffix('/download'), size, 'bp')
    async with session.get(download_url) as resp:
        if not resp.ok:
            print(f'Download {download_url} fail', resp.status)
            return False, b''
        bin_data = await resp.read()
    print('Got', download_url)
    return True, bin_data


def is_valid_tree(content: str) -> bool:
    # test if txt is newick or nexus
    try:
        tree = dendropy.Tree.get(data=content, schema='newick')
        return True
    except Exception:
        pass
    try:
        tree = dendropy.Tree.get(data=content, schema='nexus')
        return True
    except Exception:
        pass
    return False


def extract_tree(z: ZipFile):
    for file in z.namelist():
        suffix = Path(file).suffix.lower()
        if suffix == '.txt':
            z.extract(file, path=OUT_FOLDER)
            _ = OUT_FOLDER / file
            content = _.read_text(errors='ignore')
            if is_valid_tree(content):
                yield file
            else:
                _.unlink()
                print('\t', file, 'is not tree file')
        elif suffix in TREE_SUFFIX:
            z.extract(file, path=OUT_FOLDER)
            yield file
        elif suffix == ZIP_SUFFIX:
            print('\t', 'Extracting', file)
            z.extract(file, path=OUT_FOLDER)
            with ZipFile(OUT_FOLDER / file, 'r') as zz:
                yield from extract_tree(zz)
        else:
            print('\t', file, 'is not tree file')


def filter_tree_from_zip(file_bin: bytes) -> tuple:
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    with ZipFile(io.BytesIO(file_bin), 'r') as z:
        for tree_file in extract_tree(z):
            tree_files.append(tree_file)
    return tree_files


async def get_trees_by_doi(session, doi_raw: str) -> Result:
    doi = get_doi(doi_raw)
    tree_files = list()
    identifier, title, size = await search_doi(session, doi)
    result = Result(title, identifier, doi)
    if identifier == '':
        return result
    download_url = get_dryad_url(identifier)
    ok, bin_data = await download(session, download_url, size)
    if not ok:
        return result
    else:
        tree_files = filter_tree_from_zip(bin_data)
        result.add_trees(tree_files)
    return result


async def main(doi_list: list):
    title_trees = dict()
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_by_doi(session, doi) for doi in doi_list])
    for i in results:
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return title_trees


if __name__ == '__main__':
    asyncio.run(main(test_doi))