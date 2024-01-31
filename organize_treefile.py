#!/usr/bin/python3
import json
from pathlib import Path
from shutil import copyfile

from utils import Tree, get_doi


def main():
    # assign unique filename, parse path info
    data = json.load(open('assigned_taxon.new.json', 'r'))
    out_path = Path(r'R:\\out')
    # out_path.mkdir()
    trees = list()
    bad = list()
    good = 0
    for doi in data:
        record = data[doi]
        new_tree_files = list()
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
                     tree_label=description, tree_file=new_filename)
            new_file = out_path / new_filename
            if new_file.exists():
                print(new_file)
                raise Exception
            copyfile(tree_file, new_file)
            new_tree_files.append(str(new_file))
            trees.append(t.to_dict())
            good += 1
        record['tree_files'] = new_tree_files
    with open(out_path/'new.json', 'w') as out_json:
        json.dump(data, out_json)
    with open(out_path/'tree.json', 'w') as out_json2:
        json.dump(trees, out_json2)
    with open(out_path/'bad.json', 'w') as out_json3:
        json.dump(bad, out_json3)
    print(good, bad)


if __name__ == '__main__':
    main()