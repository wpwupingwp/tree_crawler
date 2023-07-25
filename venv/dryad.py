from pathlib import Path
from urllib.request import quote
from zipfile import ZipFile, ZipInfo
import asyncio
import io
import json

import aiohttp
import aiofile

server = 'https://datadryad.org/api/v2'
MAX_SIZE = 1024 * 1024 * 10
TREE_SUFFIX = '.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(',')
NEXUS_SUFFIX = '.nex,.nexus'.split(',')
ZIP_SUFFIX = '.zip'
OUT_FOLDER = Path(r'R:\dryad_out')
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()

test_title = [
    'Contrasting physiological traits of shade tolerance in Pinus and '
    'Podocarpaceae native to a tropical Vietnamese forest: Insight from '
    'an aberrant flat-leaved pine',
    'Phylogeny, classification, and character evolution of tribe Citharexyleae (Verbenaceae)',
    'Differential patterns of floristic phylogenetic diversity across a post-glacial landscape',
    'Four new species of Viola (Violaceae) from southern China',
    'New species from Phytophthora Clade 6a: evidence for recent radiation',
    'Craniodental Morphology and Phylogeny of Marsupials']


def get_dryad_url(identifier: str) -> str:
    # dryad doi looks lie 'doi:10.5061/dryad.1g1jwstss'
    # convert dryad doi to dryad download url
    # dryad requires escaped url
    doi = identifier.replace(':', '%3A').replace('/', '%2F')
    doi_url = f'{server}/datasets/{doi}/download'
    return doi_url


async def search_title(session: aiohttp.ClientSession, title: str) -> (
        str, int):
    search_url = f'{server}/search'
    params = {'q': title, 'page': 1, 'per_page': 2}
    async with session.get(search_url, params=params) as resp:
        if not resp.ok:
            raise Exception(resp.status)
        result = await resp.json()
        count = result['count']
        if count == 0 or count > 1:
            # bad search result
            return '', -1
        # print(json.dumps(result, indent=True))
        identifier = result['_embedded']['stash:datasets'][0]['identifier']
        doi = result['_embedded']['stash:datasets'][0]['relatedWorks'][0]['identifier']
        size = result['_embedded']['stash:datasets'][0]['storageSize']
        return identifier, doi, size


async def download(session: aiohttp.ClientSession, download_url: str) -> (
        bool, bytes):
    async with session.get(download_url) as resp:
        if not resp.ok:
            print(resp.status, download_url)
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
            print('\t', 'Extracting', file)
            z.extract(file, path=OUT_FOLDER)
            with ZipFile(OUT_FOLDER / file, 'r') as zz:
                yield from extract_tree(zz)
        else:
            print('\t', file, 'is not tree file')


def filter_tree_file(file_bin: bytes):
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    with ZipFile(io.BytesIO(file_bin), 'r') as z:
        for tree_file in extract_tree(z):
            tree_files.append(tree_file)
    return tree_files


async def get_trees_by_title(session, title: str) -> (str, str, list):
    tree_files = list()
    identifier, doi, size = await search_title(session, title)
    if size > MAX_SIZE:
        print(identifier, 'too big', size, 'bp')
        return tree_files
    dataset_url = get_dryad_url(identifier)
    print('Downloading', dataset_url, size, 'bp')
    ok, bin_data = await download(session, dataset_url)
    if not ok:
        print(f'Download dataset {dataset_url} fail')
        return tree_files
    else:
        print('Got', dataset_url)
        tree_files = filter_tree_file(bin_data)
    return identifier, doi, tree_files


async def main(title_list=test_title):
    title_trees = dict()
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_by_title(session, title) for title in title_list],
            return_exceptions=True)
    title_trees = dict(zip(title_list, results))
    print(title_trees.items())
    return title_trees


if __name__ == '__main__':
    asyncio.run(main())