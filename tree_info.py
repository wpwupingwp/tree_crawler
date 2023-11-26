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


def assign_taxon_by_text(record: Result) -> Result:
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
    if len(genus_count) > 0:
        top = sorted(genus_count.items(), key=lambda x:x[1], reverse=True)[0]
        log.debug(f'{top[0]} {top[1]} times, set as tree taxon')
        return top[0]
    else:
        return ''


def fix_path(old: str) -> Path:
    new = str(old)
    if old.startswith('/Users'):
        new = old.replace('/Users/wuping/Ramdisk/trees', r'R:/tree_crawl_out')
    new = Path(new)
    log.debug(f'{old}, {new}')
    return new


def assign_taxon_by_tree(record: Result) -> Result:
    # todo: test
    # assume one paper for one taxon
    taxon = ''
    for tree_file in record.tree_files:
        tree_file = fix_path(tree_file)
        if not tree_file.exists():
            log.warning(f'{tree_file} not found')
            continue
        with open(tree_file, 'r') as _:
            line = _.readline()
            if line.startswith('#NEXUS'):
                schema = 'nexus'
            else:
                schema = 'newick'
            try:
                tree = dendropy.Tree.get(path=tree_file, schema=schema)
            except Exception:
                log.warning('Invalid tree format')
                return record
            names_raw = tree.taxon_namespace
            names = [_.label.replace('_', ' ').split(' ')[0] for _ in names_raw]
            taxon = get_taxon_by_names(names)
            if taxon:
                break
    record.lineage = taxon
    return record


def assign_taxon(record: Result) -> (Result, str):
    record = assign_taxon_by_text(record)
    kind = ''
    if record.lineage:
        kind = 'by_text'
        log.info(f'Assign {record.lineage} to {record.doi} by text')
        return record, kind
    else:
        log.warning(f'{record.doi} cannot find lineage in abstract')
    record = assign_taxon_by_tree(record)
    if record.lineage:
        kind = 'by_tree'
        log.info(f'Assign {record.lineage} to {record.doi} by tree')
        return record, kind
    else:
        log.warning(f'{record.doi} cannot find lineage in tree')
    return record, 'not_found'



def main():
    get_taxon_list()
    file_list = list(Path('result').glob('*.result.json.new'))
    total_paper = 0
    total_tree = 0
    assign_count = dict(total=0, by_text=0, by_tree=0)
    for result_json in file_list:
        log.info(f'Process {result_json}')
        old_records = json.load(open(result_json, 'r'))
        new_records = list()
        new_result_file = result_json.with_suffix('.json.new2')
        for raw_record in old_records:
            record = Result(**raw_record)
            if not record.tree_files:
                continue
            total_paper += 1
            total_tree += len(record.tree_files)
            record = assign_taxon_by_text(record)
            if record.lineage:
                assigned += 1
                assigned_by_text += 1
                log.info(f'Assign {record.lineage} to {record.doi} by text')
            else:
                log.warning(f'{record.doi} cannot find lineage in abstract')
                try:
                    record = assign_taxon_by_tree(record)
                except FileNotFoundError:
                    continue
                if record.lineage:
                    assigned += 1
                    assigned_by_tree += 1
                    log.info(f'Assign {record.lineage} to {record.doi} by tree')
                else:
                    log.warning(f'{record.doi} cannot find lineage in tree')
            new_records.append(record.to_dict())
        with open(new_result_file, 'w') as f:
            json.dump(new_records, f)
            log.info(f'Write result to {new_result_file}')
        # break
    print(f'{total=},{assigned=}')
    return


if __name__ == '__main__':
    main()