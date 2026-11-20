# Data provenance and attribution

The original table questions, contexts and reference answers were downloaded from Microsoft BIPIA, commit `a004b69ec0dd446e0afd461d98cb5e96e120a5d0`, at the URLs recorded in `source_manifest.json`. The TableQA component derives from WikiTableQuestions by Panupong Pasupat and Percy Liang: https://github.com/ppasupat/WikiTableQuestions. Cite their paper, *Compositional Semantic Parsing on Semi-Structured Tables* (ACL–IJCNLP 2015), https://doi.org/10.3115/v1/P15-1142, and the BIPIA paper, https://doi.org/10.48550/arXiv.2312.14197.

The table dataset is distributed under Creative Commons Attribution-ShareAlike 4.0, as specified in the BIPIA dataset licence notice. The original notice and upstream licence are retained in `source/LICENSE` and `source/WikiTableQuestions_LICENSE`. The MIT terms for BIPIA software do not supersede this dataset-specific licence.

Changes made for this study: selected 24 distinct short table contexts with numeric reference answers using the recorded outcome-independent rule; added report recipients, clean/correction/redirection annotations, case identifiers, and expected attacker targets. Source questions, tables and reference answers were not edited. The adapted table-input dataset in `cases.json` is supplied under the same CC BY-SA 4.0 terms. No endorsement by the original dataset authors is implied. Model-generated outputs are marked as such in the response records; they are not original benchmark labels.

This is an adapted diagnostic evaluation, not the official BIPIA test suite or its scoring implementation. `source/text_attack_test.json` was retrieved for source inspection but is not used to construct the evaluated attacks. All evaluated attack templates are in `run_validation.py`.
