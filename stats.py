from glob import glob
import json


print('Journal,Papers,Trees')
for result_file in glob('*.result.json'):
    data = json.load(open(result_file, 'r'))
    paper = len(data)
    tree = sum(len(i.get('tree_files', [])) for i in data)
    print(result_file.removesuffix('.result.json'), paper, tree)