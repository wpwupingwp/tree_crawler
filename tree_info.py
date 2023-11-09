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


def get_word_list(words: str) -> (list, list):
    word_list = re.split(pattern, words)
    species_list = list()
    lineage_list = list()
    for i in range(len(word_list)-1):
        if word_list[i].isupper():
            if word_list[i+1].islower():
                species_list.append(' '.join(word_list[i:i+2]))
            else:
                lineage_list.append(word_list[i])
    return species_list, lineage_list


def get_lineage(word_list: list) -> str:
    # species first, then genus, family or order
    # but return genus rather than species
    genus_name = ''
    family_name = ''
    order_name = ''
    for word in word_list:
        if word in genus_set:
            return word
        elif word in family_set:
            family_name = word
        elif word in order_set:
            order_name = word
    if family_name != '':
        return family_name
    elif order_name != '':
        return order_name
    else:
        return ''


def assign_lineage(record: Result):
    words = ' '.join([record.title, record.abstract])
    word_list = clean_abstract(words)
    record.lineage = get_lineage(word_list)
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