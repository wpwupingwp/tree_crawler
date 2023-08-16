import aiofile
from Bio import Entrez
from aiohttp import ClientSession
from calendar import month_abbr
from io import BytesIO
import asyncio
import json

from utils import Result

BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
MONTH2NUM = {month_abbr[i]: f'{i:02d}' for i in range(1, 13)}
# max fetch id number per request
RETMAX = 1000
# fetch article info per request
BATCH_SIZE = 100
# todo
API_KEY = ''
Entrez.email = 'test@example.org'


def get_journal_list() -> tuple:
    with open('journal_list.txt', 'r') as _:
        journal_list = tuple([i.strip() for i in _.readlines()])
    return journal_list


def print2(data):
    text = json.dumps(data, indent=True)
    print(text)
    return


def date2str(date_raw: dict) -> str:
    year = date_raw['Year']
    month = MONTH2NUM[date_raw['Month']]
    try:
        day = date_raw['Day']
    except KeyError:
        day = '01'
    return f'{year}/{month}/{day}'


def parse_entrez_result(data: bytes) -> dict:
    # Entrez.read require file-like object
    tmp = BytesIO()
    tmp.write(data)
    tmp.seek(0)
    parsed = Entrez.read(tmp)
    return parsed


async def fetch_id_list(session: ClientSession, query_str: str,
                        retmax: int) -> list:
    search_url = BASE_URL + 'esearch.fcgi'
    params = {'db': 'pubmed', 'term': query_str, 'retmax': retmax}
    async with session.get(search_url, params=params) as resp:
        if not resp.ok:
            return []
        content = await resp.read()
        parsed = parse_entrez_result(content)
        return parsed['IdList']


async def fetch_article_info(session: ClientSession, id_list: str) -> dict:
    fetch_url = BASE_URL + 'efetch.fcgi'
    params = {'db': 'pubmed', 'id': id_list}
    async with session.get(fetch_url, params=params) as resp:
        if not resp.ok:
            return {}
        content = await resp.read()
        parsed = parse_entrez_result(content)
    return parsed['PubmedArticle']


def parse_article_info(info: dict) -> Result:
    article = info['MedlineCitation']['Article']
    # print2(article)
    pub_date = date2str(article['Journal']['JournalIssue']['PubDate'])
    volume = article['Journal']['JournalIssue']['Volume']
    issue = article['Journal']['JournalIssue']['Issue']
    article_id_list = article['ELocationID']
    doi = ''
    for _ in article_id_list:
        if _.attributes['EIdType'] == 'doi':
            doi = str(_)
            break
    # article_id_list2 = info['PubmedData']['ArticleIdList']
    journal_name = article['Journal']['Title']
    title = article['ArticleTitle']
    if 'Abstract' in article:
        abstract = ''.join(article['Abstract']['AbstractText'])
    else:
        abstract = ''
    if 'AuthorList' in article:
        author = ''
        for a in article['AuthorList']:
            if 'ForeName' in a and 'LastName' in a:
                author += f', {a["ForeName"]} {a["LastName"]}'
    else:
        author = ''
    return Result(doi=doi, journal_name=journal_name, title=title,
                  pub_date=pub_date, author=author, abstract=abstract,
                  volume=volume, issue=issue)


async def main(start_date: str, end_date: str, journal: str):
    query_str = (f'''("{journal}"[Journal]) AND 
    ("{start_date}"[Date - Publication] : "{end_date}"[Date - Publication])''')
    out = (start_date.replace('/', '') + '_' +
           end_date.replace('/', '') + '_' +
           journal.replace(' ', '') + '.json')
    handle = await aiofile.async_open(out, 'w', encoding='utf-8')
    session = ClientSession()
    print(query_str)
    id_list = await fetch_id_list(session, query_str, retmax=RETMAX)
    print(len(id_list), 'records')
    for i in range(0, len(id_list), BATCH_SIZE):
        print('\t', i, i + BATCH_SIZE)
        batch_id_list = ','.join(id_list[i:(i + BATCH_SIZE)])
        # NCBI limit 3 requests per second
        await asyncio.sleep(0.3)
        batch_article_info = await fetch_article_info(session, batch_id_list)
        for record in batch_article_info:
            article_info = parse_article_info(record)
            print('\t', article_info.doi)
            json_result = article_info.to_dict()
            await handle.write(json.dumps(json_result) + '\n')
    await session.close()
    await handle.close()
    print('Output file', out)
    return


if __name__ == '__main__':
    # journal = 'Molecular Biology and Evolution'
    # start_date = '2023/07/01'
    # end_date = '2022/07/15'
    start_date = '2022/01/01'
    end_date = '2022/01/02'
    for journal in get_journal_list():
        print(journal)
        asyncio.run(main(start_date, end_date, journal))