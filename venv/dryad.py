from pathlib import Path
from urllib.request import quote
from zipfile import ZipFile, ZipInfo
import asyncio
import io
import json

import aiohttp
import aiofile

server = 'https://datadryad.org/api/v2'
MAX_SIZE = 1024*1024*100
TREE_SUFFIX = '.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(',')
ZIP_SUFFIX = '.zip'
OUT_FOLDER = Path(r'R:\dryad_out')
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()

q = ('Contrasting physiological traits of shade tolerance in Pinus and '
     'Podocarpaceae native to a tropical Vietnamese forest: Insight from '
     'an aberrant flat-leaved pine')


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


async def download(session: aiohttp.ClientSession, dataset_url: str) -> (
        bool, bytes):
    download_url = f'{dataset_url}/download'
    async with session.get(download_url) as resp:
        if not resp.ok:
            return False, '', b''
        bin_data = await resp.read()
    return True, bin_data


def extract_tree(z: ZipFile):
    for file in z.namelist():
        suffix = Path(file.lower()).suffix
        if suffix in TREE_SUFFIX:
            z.extract(file, path=OUT_FOLDER)
            yield file
        elif suffix == ZIP_SUFFIX:
            print('Handle', file)
            z.extract(file, path=OUT_FOLDER)
            with ZipFile(OUT_FOLDER/file, 'r') as zz:
                yield from extract_tree(zz)
        else:
            print(file, 'is not tree file')


def filter_tree_file(file_bin: bytes):
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    with ZipFile(io.BytesIO(file_bin), 'r') as z:
        for tree_file in extract_tree(z):
            tree_files.append(tree_file)
    print(tree_files)
    return tree_files


async def main():
    async with aiohttp.ClientSession() as session:
        identifier, size = await search_title(session, q)
        if size > MAX_SIZE:
            print(identifier, 'too big', size, 'bp')
            return
        dataset_url = get_dryad_url(identifier)
        # filename = OUT_FOLDER / (identifier.replace(':', '_').replace('/', '_') + '.zip')
        ok, bin_data = await download(session, dataset_url)
        if not ok:
            print(f'Download dataset {dataset_url} fail')
        else:
            print('Got', dataset_url)
        filter_tree_file(bin_data)


if __name__ == '__main__':
    asyncio.run(main())