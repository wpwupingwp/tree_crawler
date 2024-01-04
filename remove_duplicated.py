import json
from pathlib import Path

# remove repeat record in assigned_taxon.json, which generated from tree_info.py


with open('assigned_taxon.json', 'r') as f:
    raw = json.load(f)
new = dict()
for record in raw:
    if record['doi'] == '':
        key = Path(record['tree_files'][0]).name
    else:
        key = record['doi']
    new[key] = record
with open('assigned_taxon.new.json', 'w') as out:
    json.dump(new, out, indent=True)