# %%
import csv
import json
from pathlib import Path

out = Path(r'r:\out2')
out.mkdir(exist_ok=True)


def tid(tree_id: int) -> str:
        """
        Generate TreeID from tree_id in database
        Since postgresql serial is 4*8 bit, if id is too big,
        alter table and return raw number.
        TID format: 'T00A100000'
            first letter, 'T'
            2-4, digit or capital letter, 0-9 and A-Z
            5-10, digit
        Args:
            tree_id: tree_id, postgresql serial number

        Returns:
            tid: str
        """
        if tree_id is None:
             print(tree_id)
             return ''
        max_n = min(36 ** 3 * 100_000, 2 ** (8 * 4 - 1))
        prefix = 'T'
        n = 1_000_00
        if tree_id >= max_n:
            return 'T' + str(tree_id)
        # 0-9 and A-Z
        base = 26 + 10

        a, b = divmod(tree_id, n)
        letters = ''
        while a > 0:
            a, digit = divmod(a, base)
            if digit < 10:
                letters = str(digit) + letters
            else:
                letters = chr(ord('A') + (digit - 10)) + letters
        return prefix + f'{letters:>03}' + f'{b:05d}'
# %%
# use sql to output table from treebase
# %%
"""psql
copy (
select to_json(t) from (
select tmp.name_txt as root, trees.study_id, study.doi,
	treefile.treefile_id, trees.tree_id, trees.tree_label, trees.tree_title, trees.tree_type, trees.tree_kind, 
	trees.root as root_id, trees.tree_quality, trees.upload_date, trees.tree_type_new
from trees inner join study on study.study_id=trees.study_id
inner join treefile on trees.tree_id=treefile.tree_id
left join (select * from ncbi_names where name_class='scientific name') as tmp on trees.root=tmp.tax_id
) as t)
to 'r:\out2\test.json';
"""
# %%
trees = list()
with open(out/'test.json', 'r') as _:
    for line in _:
        # handle escape character from psql
        line2 = line.replace(r'\\', '\\')
        x = json.loads(line2)
        x['tree_file'] = tid(x['tree_id']) + '.nwk'
        if not x['tree_file']:
            print('cannot find', x['tree_id'])
            continue
        trees.append(x)
print(trees[214:216])
json.dump(trees, open(out/'tree.json', 'w'), indent=True)
print(len(trees))
# %%
"""psql
copy (
	select to_json(t) from 
	  (select tree_id,newick from treefile) as t)
to 'r:\out2\treefile.json';
"""
# %%
treefile = list()
with open(out/'treefile.json', 'r') as _:
    for line in _:
        line2 = line.replace(r'\\', '\\')
        t = json.loads(line2)
        filename = tid(t['tree_id']) + '.nwk'
        if not filename:
            print('cannot find', x['tree_id'])
            continue
        with open(out/filename, 'w') as out_:
            out_.write(t['newick'])
# %%
"""psql
copy (
	select to_json(t) from (
select array_agg(treefile.tree_id) as tree_files, study.* from study
left join trees on study.study_id = trees.study_id
left join treefile on trees.tree_id = treefile.tree_id
group by study.study_id
order by study.study_id) as t)
to 'r:\out2\paper.raw';
"""
# %%
paper = list()
with open(out/'paper.raw', 'r') as _:
    for line in _:
        line2 = line.replace(r'\\', '\\')
        t = json.loads(line2)
        t['tree_files'] = [tid(tf)+'.nwk' for tf in t['tree_files']]
        paper.append(t)
print(len(paper))        
                           


# %%
with open(out/'paper.json', 'w') as out_:
    json.dump(paper, out_, indent=True)
# %%
"""
1. import to database
2. output merged final json (paper.json,tree.json) and newick treefiles
3. statistics
"""

# %%
with open(out/'paper.json') as _:
    data2 = json.load(_)
header = data2.pop()
header['tree_files'] = len(header['tree_files'])
print(header)
with open(out/'for_draw.csv', 'w', newline='') as out:
    writer = csv.DictWriter(out, fieldnames=list(header.keys()))
    writer.writeheader()
    writer.writerow(header)
    for record in data2:
        record['tree_files'] = len(record['tree_files'])
        writer.writerow(record)

# %%
# count journal

'''sql
SELECT COUNT(DISTINCT journal)
FROM study;
'''


# %% [markdown]
# 