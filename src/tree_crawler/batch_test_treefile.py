import csv
from pathlib import Path

import dendropy

from global_vars import log

tree_csv = Path(r'R:\treefiles.csv')
valid_f = tree_csv.with_suffix('.valid.csv')
invalid_f = tree_csv.with_suffix('.invalid.csv')
valid_but_escape_char_f = tree_csv.with_suffix('.valid_but_escape_char.csv')
valid = list()
valid_but_escape_char = list()
invalid = list()
csv.field_size_limit(1_000_000_000)


def is_valid_tree_str(tree_id: str, content: str) -> bool:
    # test if file is newick or nexus tree
    _NEXUS_MARKER = "#NEXUS"
    _MIN_N = 3
    if content.lstrip().upper().startswith(_NEXUS_MARKER):
        schema = 'nexus'
    else:
        schema = 'newick'
    try:
        tree = dendropy.Tree.get(data=content, schema=schema)
    except Exception as e:
        log.error(e)
        log.error(tree_id)
        # raise e
        return False
    if tree is None or tree.seed_node is None:
        log.error('Empty tree')
        return False
    try:
        leaves = list(tree.leaf_nodes())
        internal_nodes = list(tree.internal_nodes())
    except Exception:
        log.error('Empty tree')
        return False
    if len(leaves) < _MIN_N or len(internal_nodes) < 1:
        log.error('Too few leaves')
        return False
    valid_leaves = [f for f in leaves
                    if f.taxon is not None and f.taxon.label is not None
                    and len(f.taxon.label)>=1]
    if len(valid_leaves) < _MIN_N:
        log.error('Too few valid leaves')
        return False
    return True


log.info(f'Reading {tree_csv}')
with open(tree_csv, newline='') as _:
    reader = csv.reader(_, delimiter='\t')
    for row in reader:
        tree_id, newick = row
        newick = newick.strip().rstrip('\\n')
        if is_valid_tree_str(tree_id, newick):
            valid.append(tree_id)
            log.success(f'{tree_id} is valid')
        else:
            newick2 = newick.replace(r"\'", "")
            if is_valid_tree_str(tree_id, newick2):
                valid_but_escape_char.append(tree_id)
                log.info(f'{tree_id} is valid after remove escape character')
            else:
                invalid.append((tree_id, newick))
                log.warning(f'Invalid {tree_id}')
log.success(f'{len(valid)=} {len(valid_but_escape_char)=} {len(invalid)=})')
with open(valid_f, 'w') as _:
    _.write('\n'.join(valid))
with open(invalid_f, 'w') as _:
    for i in invalid:
        _.write(f'{i[0]}\t{i[1]}\n')
with open(valid_but_escape_char_f, 'w') as _:
    _.write('\n'.join(valid_but_escape_char))
log.info('Done')

