#!/usr/bin/python3
import dataclasses
import json
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import dendropy
from utils import Result
from global_vars import log

pattern = re.compile(r'\W')


# def get_word_list() -> (set, set, set, set):
    # from barcodefinder
    # https://www.ef.edu/english-resources/english-vocabulary/top-1000-words/
with open('data/1000_frequent_words .txt', 'r') as _:
    english_set_ = list(_.read().strip().split(','))
    english_set = {word.capitalize() for word in english_set_}
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
    # return genus_set, family_set, order_set, english_set


def get_words(record: Result) -> set:
    word_set = set()
    for content in (record.title, record.abstract):
        if content is None:
            content = ''
        for word in re.split(pattern, content):
            if word and len(word) > 1 and word[0].isupper():
                word_set.add(word)
    word_set.difference_update(english_set)
    return word_set


def assign_taxon_by_text(record: Result) -> str:
    # todo: test
    word_set = get_words(record)
    order_name = word_set & order_set
    if order_name:
        return order_name.pop()
    family_name = word_set & family_set
    if family_name:
        return family_name.pop()
    genus_name = word_set & genus_set
    if genus_name:
        return genus_name.pop()
    return ''


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


def assign_taxon_by_tree(record: Result) -> str:
    # todo: test
    # assume one paper for one taxon
    taxon = ''
    for tree_file in record.tree_files:
        tree_file = fix_path(tree_file)
        if not tree_file.exists():
            log.warning(f'{tree_file} not found')
            continue
        with open(tree_file, 'r', encoding='utf-8', errors='ignore') as _:
            # print(tree_file)
            line = _.readline()
            if line.startswith('#NEXUS'):
                schema = 'nexus'
            else:
                schema = 'newick'
            try:
                tree = dendropy.Tree.get(path=tree_file, schema=schema)
            except Exception:
                log.warning(f'Invalid tree format {tree_file}')
                return taxon
            names = list()
            for name in tree.taxon_namespace:
                maybe_taxon_name = name.label.replace('_', ' ').split(' ')
                names.extend(maybe_taxon_name)
            taxon = get_taxon_by_names(maybe_taxon_name)
            if taxon:
                break
    return taxon


def assign_taxon(record: Result) -> (str, str):
    text_taxon = assign_taxon_by_text(record)
    tree_taxon = assign_taxon_by_tree(record)
    if (not text_taxon) and (not tree_taxon):
        lineage = ''
        kind = 'fail'
    elif text_taxon and (not tree_taxon):
        lineage = text_taxon
        kind = 'by_text'
    elif tree_taxon and (not text_taxon):
        lineage = tree_taxon
        kind = 'by_tree'
    elif text_taxon and tree_taxon:
        lineage = text_taxon
        if text_taxon == tree_taxon:
            kind = 'both'
        else:
            # diffrent result from tree and text
            kind = 'by_text_bad'
    else:
        assert False, f'{text_taxon}, {tree_taxon}'
    return lineage, kind


def wrap_for_parallel(result_json: Path) -> (int, int, list):
    total_paper = 0
    total_tree = 0
    log.info(f'Process {result_json}')
    old_records = json.load(open(result_json, 'r'))
    updated_record = list()
    # new_result_file = result_json.with_suffix('.json.new2')
    fields = {i.name for i in dataclasses.fields(Result)}
    # sometimes Result may have unwanted fields in kwargs
    for raw_record in old_records:
        keys = list(raw_record.keys())
        for key in keys:
            if key not in fields:
                raw_record.pop(key)
        record = Result(**raw_record)
        if not record.tree_files:
            continue
        total_paper += 1
        total_tree += len(record.tree_files)
        lineage, kind = assign_taxon(record)
        if kind == 'fail':
            log.error(f'Cannot assign taxon to {record.doi}')
        else:
            log.info(f'Assign {lineage} to {record.doi} {kind}')
        record.lineage = lineage
        record.assign_type = kind
        updated_record.append(record.to_dict())
    return total_paper, total_tree, updated_record


def remove_duplicate(filename):
    # remove repeat record in assigned_taxon.json
    with open(filename, 'r') as f:
        raw = json.load(f)
    new = dict()
    for record in raw:
        if record['doi'] == '':
            key = Path(record['tree_files'][0]).name
        else:
            key = record['doi']
        new[key] = record
    new_name = filename.with_suffix('.new.json')
    with open(new_name, 'w') as out:
        json.dump(new, out, indent=True)
    return new_name


def main():
    # get_word_list()
    file_list = list(Path('.').glob('*.result.json.new'))
    # file_list = [Path(r'R:\paper.json')]
    assign_count = dict(fail=0, by_text=0, by_tree=0, both=0, by_text_bad=0)
    output = Path('assigned_taxon.json')
    # output = Path(r'R:\out.json')
    new_records = list()
    total_paper = 0
    total_tree = 0
    with ProcessPoolExecutor(max_workers=8) as executor:
        for n_paper, n_tree, updated in executor.map(
                wrap_for_parallel, file_list):
            new_records.extend(updated)
            total_paper += n_paper
            total_tree += n_tree
    for _ in new_records:
        assign_count[_['assign_type']] += 1
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(new_records, f, indent=True)
    log.info(f'Write result to {output}')
    log.info(f'{list(assign_count.items())},{total_paper=},{total_tree=}')
    log.info(f'Remove duplicate entries from {output}')
    new_out = remove_duplicate(output)
    log.info(f'Final output {new_out}')
    log.info('Done.')
    return


if __name__ == '__main__':
    main()