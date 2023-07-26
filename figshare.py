import aiohttp
import re

# figshare item type id
DATASET = 3
DOI = re.compile(r'\d+\.\d+/[^ ]+')
def get_doi(raw_doi: str, doi_type='default'):
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
def main():
                              # 'search_for': ':resource_doi: 10.1021/ja953595k',
                              'search_for': ':resource_title: Relative benefits of amino-acid, codon, degeneracy, DNA, and purine-pyrimidine character coding for phylogenetic analyses of exons',
                              'item_type': 3})
    url = 'https://api.figshare.com/v2/articles/search'
    async with aiohttp.ClientSession() as session:
        doi
        async with session.post(url, params={'search_for': 'Phylogeny treefiles',
                                             'item_type': DATASET}) as resp:
            if not resp.ok:
                print(url, resp.ok)
                return None
            article_list = await resp.json()
            for article in article_list:
                article_url = article['url']

print(r.json())