from pathlib import Path
import asyncio
import logging

from aiohttp import ClientSession

from utils import filter_tree_from_zip, is_valid_tree
from utils import download, Result, get_doi
from utils import TREE_SUFFIX, ZIP_SUFFIX, TXT_SUFFIX, OUT_FOLDER

# figshare item type id
DATASET = 3
FIGSHARE_SERVER = 'https://api.figshare.com/v2'
log = logging.getLogger('fetch_tree')

# https://api.figshare.com/v2/file/download/17716346 fail 403
test_doi = ['10.1021/ja953595k'
            '10.1371/journal.pbio.0040073',
            '10.1371/journal.pcbi.0030003',
            '10.1371/journal.pone.0000296',
            '10.1371/journal.pone.0000522',
            '10.1371/journal.pone.0000621',
            '10.1371/journal.pone.0000995',
            '10.1371/journal.pone.0001764',
            '10.1186/s12862-019-1505-1',
            '10.1186/s12864-019-6114-2']


async def search_doi_in_figshare(session: ClientSession, raw_doi: str) -> list:
    # search article doi in figshare
    # some article do not have doi info in figshare
    # searching article title in figshare return unrelated articles
    # consider search by "phylogeny" and time range?
    search_url = f'{FIGSHARE_SERVER}/articles/search'
    doi = get_doi(raw_doi=raw_doi)
    # search_for = ':title: phylogeny'
    params = {'item_type': DATASET, 'search_for': f':resource_doi: {doi}'}
    async with session.post(search_url, params=params) as resp:
        if not resp.ok:
            log.error(f'Search fail {raw_doi} {resp.ok}')
            return list()
        article_list = await resp.json()
        if len(article_list) == 0:
            return list()
    article_urls = [article['url'] for article in article_list]
    return article_urls


async def get_trees_figshare(session: ClientSession, doi: str) -> Result:
    emtpy_headers = {}
    article_urls = await search_doi_in_figshare(session, doi)
    if len(article_urls) == 0:
        return Result(doi=doi)
    to_download = list()
    for article_url in article_urls:
        async with session.get(article_url) as resp:
            if not resp.ok:
                return Result(doi=doi)
            article_info = await resp.json()
            if 'files' not in article_info:
                # no files in this article
                return Result(doi=doi)
            # repeat assignment?
            title = article_info['resource_title']
            identifier = article_info['doi']
            for i in article_info['files']:
                filename = Path(i['name'])
                file_id = i['id']
                download_url = f'{FIGSHARE_SERVER}/file/download/{file_id}'
                file_suffix = filename.suffix.lower()
                # figshare have name info before download and extraction
                if (file_suffix not in TREE_SUFFIX) and (
                        file_suffix not in ('.txt', '.zip')):
                    log.info(f'Skip {filename} in {doi}')
                    continue
                else:
                    log.info(f'{filename} may be a tree file')
                to_download.append((download_url, i['size'], filename))
    result = Result(title, identifier, doi)
    downloads = await asyncio.gather(*[download(session, download_url,
                                                size, emtpy_headers) for
                                       download_url, size, _ in to_download], )
    all_tree_files = list()
    for x, y in zip(downloads, to_download):
        ok, bin_data = x
        download_url, filesize, filename = y
        if not ok:
            continue
        file_id = download_url.split('/')[-1]
        out_folder = OUT_FOLDER / file_id
        out_folder.mkdir(exist_ok=True)
        out_file = out_folder / filename
        if filename in TREE_SUFFIX:
            # todo: assume filenames are all unique!
            out_file.write_bytes(bin_data)
            all_tree_files.append(out_file)
        elif filename.suffix.lower() in ZIP_SUFFIX:
            tree_files = filter_tree_from_zip(bin_data, out_folder)
            all_tree_files.extend(tree_files)
        elif filename.suffix.lower() in TXT_SUFFIX:
            out_file.write_bytes(bin_data)
            if is_valid_tree(out_file):
                all_tree_files.append(out_file)
            else:
                log.info(f'{filename} is not valid tree')
                out_file.unlink()
                out_folder.rmdir()
        else:
            out_folder.rmdir()
    result.add_trees(all_tree_files)
    return result


async def figshare_main(doi_list: list) -> list:
    async with ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_figshare(session, doi) for doi in doi_list],
            return_exceptions=True)
    for i in results:
        if isinstance(i, Exception):
            raise i
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return results


if __name__ == '__main__':
    asyncio.run(figshare_main(test_doi))