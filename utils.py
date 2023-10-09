from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipfile
import asyncio
import json
import logging
import re

import aiohttp
import dendropy

MAX_SIZE = 1024 * 1024 * 100
proxy = 'http://127.0.0.1:7890'

NEXUS_SUFFIX = set('.nex,.nexus'.split(','))
TREE_SUFFIX = set('.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(','))
TXT_SUFFIX = {'.txt'}
ZIP_SUFFIX = {'.zip'}
TARGET_SUFFIX = TREE_SUFFIX | ZIP_SUFFIX | TXT_SUFFIX | NEXUS_SUFFIX
OUT_FOLDER = Path(r'R:\tree_crawl_out').absolute()
# OUT_FOLDER = Path('/Users/wuping/Ramdisk/trees').absolute()
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()

log = logging.getLogger('fetch_tree')

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
    tree_files: tuple[str] = tuple()

    def __hash__(self):
        return hash(self.doi)

    def empty(self):
        return len(self.tree_files) == 0

    # todo: add tree content and info
    def add_trees(self, trees: list[Path]):
        self.tree_files = tuple([str(i) for i in trees])

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
        return re.sub(r'[^A-z0-9_.]', '_', doi)
    else:
        return doi


async def download(session: aiohttp.ClientSession, download_url: str,
                   size: int, headers: dict) -> (bool, bytes):
    ok = False
    bin_data = b''
    retry_n = 10
    if size > MAX_SIZE:
        log.warning(f'{download_url} too big {size} bp')
        return ok, bin_data
    log.info(f'Downloading {download_url.removesuffix("/download")} {size} bp')
    while retry_n > 0:
        retry_n -= 1
        try:
            async with session.get(download_url, proxy=proxy, headers=headers
                                   ) as resp:
                if not resp.ok:
                    log.warning(f'Download {download_url} fail {resp.status}')
                    log.warning(f'Does headers invalid? {repr(headers)}')
                    await asyncio.sleep(1.0)
                    continue
                bin_data = await resp.read()
            target_size = int(resp.headers.get('content-length', 0))
            actual_size = len(bin_data)
            if target_size != len(bin_data):
                log.warning(
                    f'Size mismatch {target_size} != {actual_size}')
                await asyncio.sleep(0.5)
            else:
                ok = True
                break
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            log.warning(f'Download {download_url} fail {e}')
            await asyncio.sleep(0.5)
    if ok:
        log.info(f'Got {download_url}')
    else:
        log.error(f'Download {download_url} fail with many tries')
    return ok, bin_data


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
            log.warning(f'{file} is not tree')
            continue
        # tmpfile = out_folder / file
        try:
            actual_filename = z.extract(file, path=out_folder)
            tmpfile = Path(actual_filename)
        except FileNotFoundError:
            continue
        if (suffix in TXT_SUFFIX or suffix in NEXUS_SUFFIX or
                suffix in TREE_SUFFIX):
            if is_valid_tree(tmpfile):
                yield tmpfile
            else:
                log.warning(f'{file} is not tree')
                tmpfile.unlink()
        elif suffix in ZIP_SUFFIX:
            log.info(f'Extracting {file}')
            target_filename = out_folder / file
            # filename contain '..'
            if not target_filename.exists():
                continue
            with ZipFile(target_filename, 'r') as zz:
                yield from extract_tree(zz, out_folder)
            tmpfile.unlink()
        else:
            pass


def filter_tree_from_zip(file_bin: bytes, out_folder: Path) -> list:
    # filter tree files from zip
    # extract trees into OUT_FOLDER/
    tree_files = list()
    try:
        with ZipFile(BytesIO(file_bin), 'r') as z:
            for tree_file in extract_tree(z, out_folder):
                tree_files.append(tree_file)
    except BadZipfile:
        log.critical('Bad zip file')
    return tree_files


def pprint(raw: dict):
    print(json.dumps(raw, indent=True))