import json
import csv

data = json.load(open('assigned_taxon.new.json', 'r'))
out = open('assigned_taxon.new.csv', 'w', encoding='utf-8', newline='')
writer = csv.writer(out)
writer.writerow(['Paper doi', 'id', 'assigned_taxon', 'method', 'real_taxon', 'trees'])
for key in data:
    writer.writerow(
        [f'https://dx.doi.org/{data[key]["doi"]}', data[key]['identifier'],
         data[key]['lineage'],
         data[key]['assign_type'], '', data[key]['tree_files'][0]])