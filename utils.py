from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import re

import aiohttp
import asyncio
import dendropy

MAX_SIZE = 1024 * 1024 * 10

NEXUS_SUFFIX = set('.nex,.nexus'.split(','))
TREE_SUFFIX = set('.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(','))
TXT_SUFFIX = {'.txt'}
ZIP_SUFFIX = {'.zip'}
TARGET_SUFFIX = TREE_SUFFIX | ZIP_SUFFIX | TXT_SUFFIX | NEXUS_SUFFIX
OUT_FOLDER = Path(r'R:\tree_crawl_out').absolute()
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
    tree_files: tuple[Path] = tuple()

    def __hash__(self):
        return hash(self.doi)

    def empty(self):
        return len(self.tree_files) == 0

    # todo: add tree content and info
    def add_trees(self, trees: list[Path]):
        self.tree_files = tuple(trees)

    def have_tree(self):
        return len(self.tree_files) > 0

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
    elif doi_type == 'folder':
        return doi.replace('/', '_')
    else:
        return doi


async def download(session: aiohttp.ClientSession, download_url: str,
                   size: int) -> (bool, bytes):
    if size > MAX_SIZE:
        print(download_url, 'too big', size, 'bp')
        return False, b''
    print('Downloading', download_url.removesuffix('/download'), size, 'bp')
    await asyncio.sleep(0.5)
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


def extract_tree(z: ZipFile, out_folder: Path):
    # since one paper one folder, it's hardly to overwrite existed file
    for file in z.namelist():
        suffix = Path(file).suffix.lower()
        if suffix not in TARGET_SUFFIX:
            print('\t', file, 'is not tree file')
            continue
        tmpfile = out_folder / file
        z.extract(file, path=out_folder)
        if suffix in TXT_SUFFIX or suffix in NEXUS_SUFFIX:
            if is_valid_tree(tmpfile):
                yield tmpfile
            else:
                print('\t', file, 'is not tree file')
                tmpfile.unlink()
        elif suffix in TREE_SUFFIX:
            z.extract(file, path=out_folder)
            yield tmpfile
        elif suffix in ZIP_SUFFIX:
            print('\t', 'Extracting', file)
            z.extract(file, path=out_folder)
            with ZipFile(out_folder / file, 'r') as zz:
                yield from extract_tree(zz, out_folder)
            tmpfile.unlink()
        else:
            pass


def filter_tree_from_zip(file_bin: bytes, out_folder: Path) -> list:
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    with ZipFile(BytesIO(file_bin), 'r') as z:
        for tree_file in extract_tree(z, out_folder):
            tree_files.append(tree_file)
    return tree_files