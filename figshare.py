import re
from dataclasses import dataclass
from pathlib import Path
import asyncio

from aiohttp import ClientSession

from dryad import filter_tree_from_zip, is_valid_tree
from dryad import download, Result, get_doi

# figshare item type id
DATASET = 3
SERVER = 'https://api.figshare.com/v2'
TREE_SUFFIX = '.nwk,.newick,.nex,.nexus,.tre,.tree,.treefile'.split(',')
MAX_SIZE = 1024 * 1024 * 10

NEXUS_SUFFIX = '.nex,.nexus'.split(',')
ZIP_SUFFIX = '.zip'
OUT_FOLDER = Path(r'R:\dryad_out')
if not OUT_FOLDER.exists():
    OUT_FOLDER.mkdir()
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


async def search_doi(session: ClientSession, raw_doi: str) -> list:
    # search article doi in figshare
    # some article do not have doi info in figshare
    # searching article title in figshare return unrelated articles
    # consider search by "phylogeny" and time range?
    search_url = f'{SERVER}/articles/search'
    doi = get_doi(raw_doi=raw_doi)
    # search_for = ':title: phylogeny'
    params = {'item_type': DATASET, 'search_for': f':resource_doi: {doi}'}
    async with session.post(search_url, params=params) as resp:
        if not resp.ok:
            print(raw_doi, resp.ok)
            return list()
        article_list = await resp.json()
        if len(article_list) == 0:
            return list()
    article_urls = [article['url'] for article in article_list]
    return article_urls


async def get_trees_by_doi(session: ClientSession, doi: str) -> Result:
    article_urls = await search_doi(session, doi)
    if len(article_urls) == 0:
        return Result(doi=doi)
    to_download = list()
    for article_url in article_urls:
        async with session.get(article_url) as resp:
            if not resp.ok:
                return Result(doi=doi)
            article_info = await resp.json()
            # repeat assignment?
            title = article_info['resource_title']
            identifier = article_info['doi']
            for i in article_info['files']:
                filename = Path(i['name'])
                file_id = i['id']
                download_url = f'{SERVER}/file/download/{file_id}'
                file_suffix = filename.suffix.lower()
                # figshare have name info before download and extraction
                if (file_suffix not in TREE_SUFFIX) and (
                        file_suffix not in ('.txt', '.zip')):
                    print('Skip', filename, 'in', doi)
                    continue
                else:
                    print(filename, 'may be a tree file')
                to_download.append((download_url, i['size'], filename))
    result = Result(title, identifier, doi)
    downloads = await asyncio.gather(*[download(session, download_url, size) for
                                       download_url, size, _ in to_download], )
    all_tree_files = list()
    for x, y in zip(downloads, to_download):
        ok, bin_data = x
        *_, filename = y
        out_file = OUT_FOLDER / filename
        if not ok:
            continue
        if filename in TREE_SUFFIX:
            # todo: assume filenames are all unique!
            out_file.write_bytes(bin_data)
            all_tree_files.append(out_file)
        elif filename.suffix.lower() == '.zip':
            tree_files = filter_tree_from_zip(bin_data)
            all_tree_files.extend(tree_files)
        elif filename.suffix.lower() == '.txt':
            content = bin_data.decode()
            if is_valid_tree(content):
                out_file.write_bytes(bin_data)
                all_tree_files.append(out_file)
            else:
                print('not valid tree', filename)
        else:
            pass
    result.add_trees(all_tree_files)
    return result


async def main(doi_list: list):
    title_trees = dict()
    async with ClientSession() as session:
        results = await asyncio.gather(
            *[get_trees_by_doi(session, doi) for doi in doi_list],
            return_exceptions=True)
    for i in results:
        if isinstance(i, Exception):
            raise i
        if i.empty():
            print('Empty', i)
        else:
            print(i)
    return title_trees


if __name__ == '__main__':
    asyncio.run(main(test_doi))