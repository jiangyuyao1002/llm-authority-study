"""Check source preservation and deterministic sampling independently of model answers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'source_manifest.json').read_text(encoding='utf-8'))
for name,info in manifest['files'].items():assert digest(ROOT/'source'/name)==info['sha256']
source=[json.loads(x) for x in (ROOT/'source/table_test.jsonl').read_text(encoding='utf-8').splitlines()]
cc=json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))
for c in cc:
    s=source[c['source_row_zero_based']]
    assert (c['question'],c['table'],c['expected_answer'])==(s['question'],s['context'],s['ideal'])
    assert hashlib.sha256(c['table'].encode()).hexdigest()==c['table_sha256']
assert len(cc)==72 and len({c['task_id'] for c in cc})==24 and len({c['table_sha256'] for c in cc})==24
report={'source_files_hash_verified':len(manifest['files']),'source_questions':len(source),'selected_unique_questions':24,'selected_unique_table_contexts':24,'question_table_reference_preservation':'all exact matches to source rows','source_reference_labels_edited':False,'independent_human_label_review':False,'scope_note':'Selection is limited to numeric labels and short contexts. Reference agreement is not an independent factual audit. Time-relative or underspecified questions remain in the frozen primary set.'}
(ROOT/'source_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
