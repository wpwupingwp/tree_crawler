#!/usr/bin/python3
import json
import re
from pathlib import Path

from utils import Result, Tree
from global_vars import log

global species_set, genus_set, family_set, order_set
pattern = re.compile(r'\W')


def get_taxon_list() -> (set, set, set, set):
    species = set()
    genus = set()
    family = set()
    order = set()
    return species, genus, family, order


def get_word_list(words: str) -> (set, set):
    word_list = re.split(pattern, words)
    species_alike = set()
    lineage_alike = set()
    for i in range(len(word_list)-1):
        if word_list[i].isupper():
            if word_list[i+1].islower():
                species_alike.add(' '.join(word_list[i:i+2]))
            else:
                lineage_alike.add(word_list[i])
    return species_alike, lineage_alike


def get_lineage(species_alike, lineage_alike: set) -> str:
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
    words = ' '.join([record.title, record.abstract])
    species_list, lineage_list = get_word_list(words)
    record.lineage = get_lineage(species_list, lineage_list)
    return record


def main():
    file_list = list(Path('result').glob('*.result.json.new'))
    for result_json in file_list:
        old_records = json.load(open(result_json, 'r'))
        new_result_file = result_json.with_suffix('.json.new2')
        for raw_record in old_records:
            record = Result(**raw_record)
            record = assign_lineage(record)
            print(record)
            with open(result_json, 'w') as f:
                json.dump(old_records, f)
            log.info(f'{record.identifier} lineage assigned')
            # break
        # break
    return


if __name__ == '__main__':
    main()