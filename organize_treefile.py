#!/usr/bin/python3
import json
from pathlib import Path
from shutil import copyfile

import pandas as pd

from utils import Tree, get_doi

def main():
    table = pd.read_excel('R:\\assigned_taxon.new_20240205-modified.xlsx')
    doi_old_new = dict()
    x = table[['doi','assigned_taxon', 'New_name']]
    for index, row in x.iterrows():
        doi = get_doi(row.doi, doi_type='normal')
        doi_old_new[doi] = (row.assigned_taxon, row.New_name)
    # assign unique filename, parse path info
    data = json.load(open('assigned_taxon.new.json', 'r'))
    merge = dict()
    out_path = Path(r'R:\\out')
    # out_path.mkdir()
    trees = list()
    bad = list()
    good = 0
    for doi in data:
        record = data[doi]
        # try to rename
        if doi in doi_old_new:
            old, new = doi_old_new[doi]
            if old != new:
                print(doi, old, 'to', new)
                record['lineage'] = new
            else:
                print(doi, old, new, 'same!')
        else:
            print(doi, 'not found')
        new_tree_files = list()
        merge[doi] = dict(record)
        merge[doi]['tree_files'] = list()
        for n, tree_path in enumerate(record['tree_files']):
            tree_file = Path(tree_path)
            if not tree_file.exists():
                bad.append(data[doi])
                continue
            # 3 parents, r drive,treeout,doi
            # -1, filename
            path_info = tree_file.parts[3:-1]
            if path_info:
                description = ', '.join(path_info).replace('_', ' ')
            else:
                description = ''
            name = tree_file.stem
            _ = get_doi(doi, doi_type='folder')
            new_filename = f'{_}_{n}_{good:06d}_{tree_file.name}'
            t = Tree(root=record['lineage'], tree_title=name,
                     tree_label=description, tree_file=new_filename, doi=doi)
            new_file = out_path / new_filename
            if new_file.exists():
                print(new_file)
                raise Exception
            copyfile(tree_file, new_file)
            new_tree_files.append(str(new_file))
            t_dict = t.to_dict()
            trees.append(t_dict)
            merge[doi]['tree_files'].append(t_dict)
            good += 1
        record['tree_files'] = new_tree_files
    with open(out_path/'paper.json', 'w') as out_json:
        json.dump(data, out_json, indent=True)
    with open(out_path/'tree.json', 'w') as out_json2:
        json.dump(trees, out_json2, indent=True)
    with open(out_path/'bad.json', 'w') as out_json3:
        json.dump(bad, out_json3, indent=True)
    with open(out_path/'merge.json', 'w') as out_json4:
        json.dump(merge, out_json4, indent=True)
    print(good, len(bad))


if __name__ == '__main__':
    main()