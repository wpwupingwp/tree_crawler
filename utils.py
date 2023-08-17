from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import re

import aiohttp
import aiofile
import dendropy

MAX_SIZE = 1024 * 1024 * 10

NEXUS_SUFFIX = '.nex,.nexus'.split(',')
TREE_SUFFIX = set('.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(','))
TXT_SUFFIX = set(['.txt'])
ZIP_SUFFIX = set(['.zip'])
OUT_FOLDER = Path(r'R:\dryad_out')
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()


@dataclass
class Result:
    abstract: str = ''
    author: str = ''
    # should be '10.xxxx/yyyyy' format
    doi: str = ''
    identifier: str = ''
    issue: int = 0
    journal_name: str = ''
    # 2000/01/01
    pub_date: str = ''
    title: str = ''
    volume: int = 0
    tree_files: tuple = tuple()

    def empty(self):
        return len(self.tree_files) == 0

    # todo: add tree content and info
    def add_trees(self, trees: list[Path]):
        self.tree_files = tuple(trees)

    def to_dict(self):
        return asdict(self)

    def to_sql(self):
        pass


def get_doi(raw_doi: str, doi_type='default') -> str:
    # doi of article
    # 10.1234/12345
    doi_pattern = re.compile(r'\d+\.\d+/[^ ]+')
    match = re.search(doi_pattern, raw_doi)
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


def is_valid_tree(tmpfile: Path) -> bool:
    # test if file is newick or nexus tree
    # if not, DELETE the file
    content = tmpfile.read_text(errors='ignore')
    try:
        _ = dendropy.Tree.get(data=content, schema='newick')
        return True
    except Exception:
        pass
    try:
        _ = dendropy.Tree.get(data=content, schema='nexus')
        return True
    except Exception:
        pass
    return False


def extract_tree(z: ZipFile):
    # todo: no valid tree?
    for file in z.namelist():
        suffix = Path(file).suffix.lower()
        if suffix in TXT_SUFFIX or suffix in NEXUS_SUFFIX:
            z.extract(file, path=OUT_FOLDER)
            tmpfile = OUT_FOLDER / file
            if is_valid_tree(tmpfile):
                yield file
            else:
                print('\t', file, 'is not tree file')
                tmpfile.unlink()
        elif suffix in TREE_SUFFIX:
            z.extract(file, path=OUT_FOLDER)
            yield file
        elif suffix in ZIP_SUFFIX:
            print('\t', 'Extracting', file)
            z.extract(file, path=OUT_FOLDER)
            with ZipFile(OUT_FOLDER / file, 'r') as zz:
                yield from extract_tree(zz)
        else:
            print('\t', file, 'is not tree file')


def filter_tree_from_zip(file_bin: bytes) -> list:
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    with ZipFile(BytesIO(file_bin), 'r') as z:
        for tree_file in extract_tree(z):
            tree_files.append(tree_file)
    return tree_files