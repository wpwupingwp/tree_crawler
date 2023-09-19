from pathlib import Path
import asyncio
import json
import logging

import aiohttp
import coloredlogs

from dryad import get_trees_dryad, get_api_token
from figshare import get_trees_figshare

FMT = '%(asctime)s %(levelname)-8s %(message)s'
DATEFMT = '%H:%M:%S'
logging.basicConfig(format=FMT, datefmt=DATEFMT, level=logging.INFO)
log = logging.getLogger('fetch_tree')
fmt = logging.Formatter(FMT, DATEFMT)
file_handler = logging.FileHandler('log.txt', 'a')
file_handler.setFormatter(fmt)
log.addHandler(file_handler)
coloredlogs.install(level=logging.INFO, fmt=FMT, datefmt=DATEFMT)

CHECK_SIZE = 50


async def main():
    # pubmed result json
    json_files = list(Path().glob('2010*.json'))
    input_jsons = [i for i in json_files if 'result' not in i.name]
    for input_json in input_jsons:
        headers = await get_api_token()
        log.info(input_json)
        output_json = input_json.with_suffix('.result.json')
        checkpoint = input_json.with_suffix('.checkpoint')
        if checkpoint.exists():
            checkpoint_n = int(checkpoint.read_text().strip())
            log.info(f'Load {checkpoint_n} records from checkpoint')
            results = json.load(open(output_json, 'r'))
        else:
            results = list()
            checkpoint_n = 0
        data = json.load(input_json.open())
        log.info(f'{len(data)} records')
        count = 0
        count_have_tree = 0
        test = ['10.1002/ajb2.1682', '10.1002/ajb2.1738', '10.1002/ajb2.1797',
                '10.1002/ajb2.1453']
        test2 = [{'doi': i} for i in test]
        async with aiohttp.ClientSession() as session:
            # for record in test2:
            for record in data[checkpoint_n:]:
                # API limit
                # 120/min
                await asyncio.sleep(0.5)
                doi = record['doi']
                log.info(f'{count+checkpoint_n+1} {doi}')
                result = await get_trees_figshare(session, doi)
                if not result.have_tree():
                    result = await get_trees_dryad(session, doi, headers)
                count += 1
                if result.have_tree():
                    log.info(f'Found trees in {doi}')
                    count_have_tree += 1
                    record['tree_files'] = tuple(result.tree_files)
                    results.append(record)
                if count % CHECK_SIZE == 0:
                    log.warning(f'Processed {count} records')
                    checkpoint.write_text(str(count+checkpoint_n))
                    log.warning(f'Writing results {output_json}')
                    with open(output_json, 'w') as f:
                        json.dump(results, f)
        log.info(f'{count} records')
        log.info(f'{count_have_tree} have trees')
        log.info(f'Writing results {output_json}')
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=True)
        checkpoint.write_text(str(count + checkpoint_n))
    return


if __name__ == '__main__':
    asyncio.run(main())