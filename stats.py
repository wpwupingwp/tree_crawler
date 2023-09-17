from pathlib import Path
import json


print('Journal,Article,Have_Tree,Trees')
result_jsons = Path().glob('*.result.json')
for result_file in result_jsons:
    input_json = Path(result_file.name.removesuffix('.result.json')+'.json')
    data = json.load(open(result_file, 'r'))
    data2 = json.load(open(input_json, 'r'))
    paper = len(data2)
    have_tree_paper = len(data)
    tree = sum(len(i.get('tree_files', [])) for i in data)
    print(result_file.stem, paper, have_tree_paper, tree, sep=',')