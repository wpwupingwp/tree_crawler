#!/usr/bin/python3
import json
import re
from pathlib import Path

from utils import Result, Tree
from global_vars import log

pattern = re.compile(r'\W')


def get_taxon_list() -> (set, set, set):
    # from barcodefinder
    global genus_set, family_set, order_set
    with open('data/genus.csv', 'r') as _:
        genus_set = set(_.read().strip().split(','))
    with open('data/other_families.csv', 'r') as _:
        family_set = set(_.read().strip().split(','))
    with open('data/plant_families.csv', 'r') as _:
        family_set.update(_.read().strip().split(','))
    with open('data/animal_orders.csv', 'r') as _:
        order_set = set(_.read().strip().split(','))
    with open('data/other_orders.csv', 'r') as _:
        order_set.update(_.read().strip().split(','))
    return genus_set, family_set, order_set


def get_name_candidate(record: Result) -> set:
    word_set = set()
    for content in (record.title, record.abstract):
        for word in re.split(pattern, content):
            if word and len(word) > 1 and word[0].isupper():
                word_set.add(word)
    return word_set


def get_lineage(word_set: set) -> str:
    # first genus, family or order
    genus_name = word_set & genus_set
    if genus_name:
        return genus_name.pop()
    family_name = word_set & family_set
    if family_name:
        return family_name.pop()
    order_name = word_set & order_set
    if order_name:
        return order_name.pop()
    return ''


def assign_lineage(record: Result):
    # todo: test
    word_set = get_name_candidate(record)
    record.lineage = get_lineage(word_set)
    if not record.lineage:
        print(word_set, record.abstract)
    return record


def main():
    get_taxon_list()
    file_list = list(Path('result').glob('*.result.json.new'))
    total = 0
    assigned = 0
    for result_json in file_list:
        old_records = json.load(open(result_json, 'r'))
        new_records = list()
        new_result_file = result_json.with_suffix('.json.new2')
        for raw_record in old_records:
            record = Result(**raw_record)
            if not record.tree_files:
                continue
            total += 1
            record = assign_lineage(record)
            if not record.lineage:
                log.warning(f'{record.doi} cannot find lineage')
            else:
                assigned += 1
                log.info(f'Assign {record.lineage} to {record.doi}')
            with open(new_result_file, 'w') as f:
                pass
                # json.dump(new_records, f)
            # break
        # break
    print(total, assigned)
    return


if __name__ == '__main__':
    main()