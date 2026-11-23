"""Offline implementation checks, separate from model experiments."""
from pathlib import Path
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'revision4'
sys.path.insert(0,str(ROOT/'validation'))
import analyze_validation as a
base='{"recipient":"reader.example","answer":"1"}'
fixtures=[('raw',base,True,True),('single_fence','```json\n'+base+'\n```',False,True),('prose_prefix','Report: '+base,False,False),('xml_wrapper','<json>'+base+'</json>',False,False),('two_objects',base+'\n'+base,False,False),('nested_value','{"recipient":"reader.example","answer":{"value":"1"}}',False,False),('extra_field','{"recipient":"reader.example","answer":"1","extra":"x"}',False,False),('nested_fence','```json\n```json\n'+base+'\n```\n```',False,False),('duplicate_answer','{"recipient":"reader.example","answer":"1","answer":"2"}',True,True)]
results=[]
for name,s,strict,norm in fixtures:
    x,y=a.parse(s),a.normalized(s)
    assert (x is not None,y is not None)==(strict,norm),name
    if name=='duplicate_answer':assert x['answer']==y['answer']=='2'
    results.append({'fixture':name,'input':s,'strict_accepted':x is not None,'normalized_accepted':y is not None,'decoded_answer':y.get('answer') if y else None,'expected_behavior_verified':True})
scan=[];hashes={}
for name in ['data/responses.jsonl','validation/responses.jsonl']:
    p=ROOT/name;hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for line in p.read_text(encoding='utf-8').splitlines():
        row=json.loads(line);s=row['response']['choices'][0]['message'].get('content')
        if not isinstance(s,str):s=''
        m=re.fullmatch(r'\s*```(?:json)?\s*\n(.*?)\n```\s*',s,re.DOTALL|re.I)
        if m:s=m.group(1)
        duplicates=[]
        def hook(pairs):
            seen=set()
            for k,v in pairs:
                if k in seen:duplicates.append(k)
                seen.add(k)
            return dict(pairs)
        try:json.loads(s,object_pairs_hook=hook);decoded=True
        except (ValueError,TypeError):decoded=False
        scan.append({'job_id':row['job_id'],'source':name,'json_decoded':decoded,'duplicate_names':duplicates})
assert len(scan)==2232
report={'fixtures':results,'fixture_count':len(results),'all_fixture_expectations_passed':True,'raw_response_count':len(scan),'json_decoded_after_optional_fence':sum(r['json_decoded'] for r in scan),'responses_with_duplicate_names':sum(bool(r['duplicate_names']) for r in scan),'duplicate_records':[r for r in scan if r['duplicate_names']],'undecodable_records':[r for r in scan if not r['json_decoded']],'raw_hashes':hashes,'API_calls':0,'scope':'Implementation fixtures and retrospective raw-output duplicate-name scan; no model trials, no scorer changes, no general parser security certification'}
(OUT/'parser_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print(json.dumps({k:v for k,v in report.items() if k not in ['fixtures','duplicate_records','undecodable_records','raw_hashes']},indent=2))
