# tree_crawler
crawl nexus/newick tree
# steps
- fetch article info by `pubmed.py` with `journal list`
- fetch trees by `fetch_tree.py` which depends on `dryad.py` and `figshare.py`
- organize result and do statistics by `organize_result.py`, `stats*.py`
- output results by 
  1. `output_doi_info.py`
  2. `output_tree_info.py`. This file will assign taxon to paper
  3. `output_treefile.py`. This program generate final json datasets
get new taxon value.
- import to database
 
  - Use `plant_tree_db`'s  `local_batch_submit.py`. Cost hours since it mimics
  submit via web requests.
- integrated with treebase
  - export database
    - See `crawl_out_for_draw.ipynb`
  - fix treebase records
    - Treebase records may have invalid lineage assignment. Use `output*.py` to
    fix
    - Use old-new value table to update database
    - use `count_taxon.ipynb` to generate statistics output
  
