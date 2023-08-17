from pathlib import Path
import asyncio
import json

from dryad import dryad_main
from figshare import figshare_main

result_jsons = list(Path().glob('*.json'))
for result_json in result_jsons[:1]:
    print(result_json)
    data = json.load(result_json.open())
    doi_list = [i['doi'] for i in data][:10]
    figshare_result = asyncio.run(figshare_main(doi_list))
    dryad_result = asyncio.run(dryad_main(doi_list))
    with open('dryad.json', 'w') as f:
        json.dump([i.to_dict() for i in dryad_result], f)
    with open('figshare.json', 'w') as f:
        json.dump([i.to_dict() for i in figshare_result], f)