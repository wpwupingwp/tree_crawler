from pathlib import Path
import asyncio
import json

import aiohttp

from dryad import get_trees_dryad
from figshare import get_trees_figshare


async def main():
    # pubmed result json
    input_jsons = list(Path().glob('2*.json'))
    results = list()
    for input_json in input_jsons[:1]:
        print(input_json)
        data = json.load(input_json.open())
        count = 0
        count_have_tree = 0
        # test = ['10.1002/ajb2.1682', '10.1002/ajb2.1738', '10.1002/ajb2.1797']
        # test2 = [{'doi': i} for i in test]
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
        output_json = input_json.with_suffix('.result.json')
        print('Writing results', output_json)
        with open('result.json', 'w') as f:
            json.dump(results, f)
    return


if __name__ == '__main__':
    asyncio.run(main())