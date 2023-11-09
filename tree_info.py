#!/usr/bin/python3
import json
import re
from pathlib import Path

from utils import Result, Tree
from global_vars import log

pattern = re.compile(r'\W')


def get_taxon_list() -> (set, set, set, set):
    # from barcodefinder
    global species_set, genus_set, family_set, order_set
    with open('data/species.csv', 'r') as _:
        species_set = set(_.read().strip().split(','))
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
    return species_set, genus_set, family_set, order_set


def get_name_candidate(words: str) -> (set, set):
    word_list = [i for i in re.split(pattern, words) if i]
    species_alike = set()
    lineage_alike = set()
    for i in range(len(word_list)-1):
        if word_list[i][0].isupper():
            if word_list[i+1][0].islower():
                species_alike.add(' '.join(word_list[i:i+2]))
            else:
                lineage_alike.add(word_list[i])
    return species_alike, lineage_alike


def get_lineage(species_alike: set, lineage_alike: set) -> str:
    # species first, then genus, family or order
    # but return genus rather than species
    species_name = species_alike & species_set
    if species_name:
        return species_name.pop().split(' ')[0]
    genus_name = lineage_alike & genus_set
    if genus_name:
        return genus_name.pop()
    family_name = lineage_alike & family_set
    if family_name:
        return family_name.pop()
    order_name = lineage_alike & order_set
    if order_name:
        return order_name.pop()
    return ''


def assign_lineage(record: Result):
    # todo: test
    words = ' '.join([record.title, record.abstract]).strip()
    species_alike, lineage_alike = get_name_candidate(words)
    print(species_alike, lineage_alike)
    record.lineage = get_lineage(species_alike, lineage_alike)
    if not record.lineage:
        log.warning(f'{record.doi} cannot find lineage')
    else:
        log.info(f'Assign {record.lineage} to {record.doi}')
    return record


def main():
    get_taxon_list()
    file_list = list(Path('result').glob('*.result.json.new'))
    for result_json in file_list:
        old_records = json.load(open(result_json, 'r'))
        new_records = list()
        new_result_file = result_json.with_suffix('.json.new2')
        for raw_record in old_records:
            record = Result(**raw_record)
            if not record.tree_files:
                continue
            record = assign_lineage(record)
            with open(new_result_file, 'w') as f:
                pass
                # json.dump(new_records, f)
            # break
        # break
    return


if __name__ == '__main__':
    main()