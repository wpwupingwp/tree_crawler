from pathlib import Path
from urllib.request import quote
from zipfile import ZipFile, ZipInfo
import asyncio
import io
import json
from collections import namedtuple
from dataclasses import dataclass

import aiohttp
import aiofile
import dendropy


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
    doi: str = ''
    tree_files: tuple = tuple()

    def empty(self):
        return len(self.tree_files) == 0

    def add_trees(self, trees: list):
        self.tree_files = tuple(trees)


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
    download_url = f'{server}/datasets/{doi}/download'
    return download_url


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
        related_work = result['_embedded']['stash:datasets'][0].get(
            'relatedWorks', None)
        if related_work is None:
            doi = ''
        else:
            doi = related_work[0]['identifier']
        size = result['_embedded']['stash:datasets'][0]['storageSize']
        return identifier, doi, size


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
    for file_ in z.namelist():
        file = Path(file)
        suffix = file.suffix.lower()
        if suffix == '.txt':
            z.extract(file, path=OUT_FOLDER)
            with open(file, 'r') as _:
                content = _.read()
            if is_txt_valid_tree(content):
                yield file
            else:
                file.unlink()
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


async def get_trees_by_title(session, title: str) -> Result:
    tree_files = list()
    identifier, doi, size = await search_title(session, title)
    result = Result(title, identifier, doi)
    download_url = get_dryad_url(identifier)
    ok, bin_data = await download(session, download_url, size)
    if not ok:
        return result
    else:
        tree_files = filter_tree_from_zip(bin_data)
        result.add_trees(tree_files)
    return result


async def main(title_list: list):
    title_trees = dict()
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_by_title(session, title) for title in title_list],
            return_exceptions=True)
    for i in results:
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return title_trees


if __name__ == '__main__':
    asyncio.run(main(test_title))