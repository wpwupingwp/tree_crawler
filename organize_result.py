import json
import csv
from pathlib import Path


no_tree = list()
have_tree = list()
total = dict()
stats = dict()
doi_list = set()


def main():
    file_list = list(Path('result').glob('*.result.json'))
    for filename in file_list:
        journal_name = filename.stem.split('.')[0].split('-')[-1]
        if journal_name not in total:
            # record, all paper, clean paper, have_tree, trees
            total[journal_name] = [0, 0, 0, 0, 0]
        stats[journal_name] = list()
        raw_data = json.load(open(filename, 'r'))
        for record in raw_data:
            if len(record['journal_name']) == 0:
                record['journal_name'] = journal_name
            total[journal_name][0] += 1
            doi = record['doi']
            if len(doi) != 0:
                total[journal_name][1] += 1
                if doi in doi_list:
                    continue
                total[journal_name][2] += 1
                doi_list.add(journal_name)
            n_trees = len(record['tree_files'])
            if n_trees == 0:
                no_tree.append(record)
            else:
                total[journal_name][3] += 1
                total[journal_name][4] += n_trees
                stats[journal_name].append(n_trees)
                have_tree.append(record)
    with open('have_tree.json', 'w') as out1:
        json.dump(have_tree, out1, indent=True)
    with open('no_tree.json', 'w') as out2:
        json.dump(no_tree, out2, indent=True)
    with open('total.csv', 'w', newline='') as out3:
        writer = csv.writer(out3)
        writer.writerow('journal,record,paper,clean_paper,have_tree,trees'.split(','))
        for key in total:
            writer.writerow([key, *total[key]])
    with open('stats.json', 'w') as out4:
        json.dump(stats, out4, indent=True)
    print('done')


if __name__ == '__main__':
    main()