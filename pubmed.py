from Bio import Entrez
import json
from calendar import month_abbr

MONTH2NUM = {month_abbr[i]: f'{i:02d}' for i in range(1, 13)}
# max fetch id number per request
RETMAX = 2
# fetch article info per request
BATCH_SIZE = 3


def print2(data):
    text = json.dumps(data, indent=True)
    print(text)
    return


def date2str(date_raw: dict) -> str:
    year = date_raw['Year']
    month = MONTH2NUM[date_raw['Month']]
    day = date_raw['Day']
    return f'{year}/{month}/{day}'


journal = 'Molecular Biology and Evolution'
start_date = '2023/06/01'
end_date = '2023/07/01'
query_str = (f'''("{journal}"[Journal]) AND 
("{start_date}"[Date - Publication] : "{end_date}"[Date - Publication])''')
Entrez.email = 'test@example.org'
query = Entrez.read(Entrez.esearch(db='pubmed', term=query_str, retmax=RETMAX))
print(query_str)
print(query)
id_list = query['IdList']
print2(id_list)
for i in range(0, len(id_list), BATCH_SIZE):
    print(i, i+BATCH_SIZE)
    batch_id_list = ','.join(id_list[i:(i+BATCH_SIZE)])
    batch_article_info = Entrez.read(Entrez.efetch(db='pubmed', id=batch_id_list))
    for record in batch_article_info['PubmedArticle']:
        article = record['MedlineCitation']['Article']
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
        # article_id_list2 = record['PubmedData']['ArticleIdList']
        journal_name = article['Journal']['Title']
        article_title = article['ArticleTitle']
        if 'Abstract' in article:
            abstract = article['Abstract']['AbstractText']
        else:
            abstract = ''
        if 'AuthorList' in article:
            author = ''
            for a in article['AuthorList']:
                author += f', {a["ForeName"]} {a ["LastName"]}'
        else:
            author = ''
        print(f'{doi=} {journal_name=} {article_title=} {pub_date=} {author=} {abstract=} {article_id_list=} {volume=} {issue=}')
