#!/usr/bin/python3
import json
import re
from pathlib import Path

import dendropy

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


def get_words(record: Result) -> set:
    word_set = set()
    for content in (record.title, record.abstract):
        for word in re.split(pattern, content):
            if word and len(word) > 1 and word[0].isupper():
                word_set.add(word)
    return word_set


def get_taxon_by_words(word_set: set) -> str:
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


def assign_taxon_by_text(record: Result):
    # todo: test
    word_set = get_words(record)
    record.lineage = get_taxon_by_words(word_set)
    if not record.lineage:
        print(word_set, record.abstract)
    return record


def get_taxon_by_names(names: list[str]) -> str:
    genus_count = dict()
    for name in names:
        if name in genus_set:
            genus_count[name] = genus_count.get(name, 0) + 1
    top = sorted(genus_count.items(), key=lambda x:x[1], reverse=True)[0]
    log.info(f'{top[0]} {top[1]} times, set as tree taxon')
    return top[0]


def assign_taxon_by_tree(record: Result) -> str:
    # todo: test
    # assume one paper for one taxon
    taxon = ''
    for tree_file in record.tree_files:
        with open(tree_file, 'r') as _:
            line = _.readline()
            if line.startswith('#NEXUS'):
                schema = 'nexus'
            else:
                schema = 'newick'
            try:
                tree = dendropy.Tree.get(path=tree_file, schema=schema)
            except Exception:
                return taxon
            names_raw = tree.taxon_namespace
            names = [_.label.replace('_', ' ').split(' ')[0] for _ in names_raw]
            taxon = get_taxon_by_names(names)
            if taxon:
                return taxon
    return taxon


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
            record = assign_taxon_by_text(record)
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