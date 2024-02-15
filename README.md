# tree_crawler
crawl nexus/newick tree
# steps
- fetch article info by `pubmed.py` with `journal list`
- fetch trees by `fetch_tree.py` which depends on `dryad.py` and `figshare.py`
- organize result and do statistics by `organize_result.py`, `stats*.py`
- output results by 
  1. `output_doi_info.py`
  2. `output_tree_info.py`
  3. `output_treefile.py`. This file will also assign taxon to paper
- import to database