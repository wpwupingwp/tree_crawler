#!/usr/bin/python3
import json

from utils import Result
from global_vars import log

global genus_set, family_set, order_set


def get_taxon_list() -> (set, set, set):
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


def assign_lineage(Tree):
    pass


def main():
    return


if __name__ == '__main__':
    main()