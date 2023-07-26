import aiohttp
import re

# figshare item type id
DATASET = 3
DOI = re.compile(r'\d+\.\d+/[^ ]+')
SERVER = 'https://api.figshare.com/v2'


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
https://api.figshare.com/v2/articles/{article_id}"

def search_doi(session: aiohttp.ClientSession, raw_doi='10.1021/ja953595k'
               ) -> (str, str):
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
            return '', ''
        article_list = await resp.json()
        if len(article_list) != 1:
            return '', ''
        article = article_list[0]
        article_id = article['id']
        # article doi
        resource_doi = article['resource_doi']
    return article_id, resource_doi

print(r.json())