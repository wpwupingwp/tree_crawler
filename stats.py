from pathlib import Path
import json


print('Journal,Article,Have_Tree,Trees')
result_jsons = Path().glob('*.result.json')
for result_file in result_jsons:
    input_json = Path(result_file.name.removesuffix('.result.json')+'.json')
    data = json.load(open(result_file, 'r'))
    if not input_json.exists():
        data2 = json.load(open(result_file, 'r'))
        have_tree_paper = len([i for i in data2 if len(i['tree_files']) != 0])
    else:
        data2 = json.load(open(input_json, 'r'))
        have_tree_paper = len(data)
    paper = len(data2)
    tree = sum(len(i.get('tree_files', [])) for i in data)
    print(result_file.stem, paper, have_tree_paper, tree, sep=',')