import json


with open('assigned_taxon.new.json') as f:
    data = json.load(f)
articles = len(data)
journals = {data[i]['journal_name'] for i in data}
journal_n = len(journals)
tree = sum(len(data[i].get('tree_files', [])) for i in data)
print(f'{articles=},{journal_n=},{tree=}')