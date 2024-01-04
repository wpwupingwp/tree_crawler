import json
import csv

data = json.load(open('assigned_taxon.json', 'r'))
out = open('assigned_taxon.csv', 'w', encoding='utf-8', newline='')
writer = csv.writer(out)
writer.writerow(['doi', 'assigned_taxon', 'method', 'real_taxon'])
for record in data:
    writer.writerow([f'https://dx.doi.org/{record["doi"]}', record['lineage'],
                     record['assign_type'], ''])
