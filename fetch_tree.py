from pathlib import Path
import asyncio
import json

import aiohttp

from dryad import get_trees_dryad
from figshare import get_trees_figshare


async def main():
    # pubmed result json
    input_json = list(Path().glob('2*.json'))
    results = list()
    for result_json in input_json[:1]:
        print(result_json)
        data = json.load(result_json.open())
    count = 0
    count_have_tree = 0
    async with aiohttp.ClientSession() as session:
        for record in data:
            # API limit
            await asyncio.sleep(2)
            count += 1
            doi = record['doi']
            print(doi, 'figshare')
            result = await get_trees_figshare(session, doi)
            if not result.have_tree():
                print(doi, 'dryad')
                result = await get_trees_dryad(session, doi)
            if not result.have_tree():
                print('No result', doi)
                continue
            count_have_tree += 1
            record['tree_files'] = tuple(result.tree_files)
            results.append(record)
    print(count, 'records')
    print(count_have_tree, 'have trees')
    print('Writing results...')
    with open('result.json', 'w') as f:
        json.dump(results, f)
    return


if __name__ == '__main__':
    asyncio.run(main())