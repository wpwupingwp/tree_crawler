#!/usr/bin/python3
import json
from pathlib import Path

from utils import Result, Tree
from global_vars import log

global species_set, genus_set, family_set, order_set


def get_taxon_list() -> (set, set, set, set):
    species = set()
    genus = set()
    family = set()
    order = set()
    return genus, family, order


def clean_abstract(abstract: str) -> list:
    word_list = list()
    for word in abstract.split(' '):
        first_letter = word[0]
        if first_letter.isupper():
            word_list.append(word)
    return word_list


def get_lineage(word_list: list) -> str:
    # genus first, then family or order
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