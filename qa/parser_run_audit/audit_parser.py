from pathlib import Path
import json,csv,hashlib,collections,itertools,sys,ast,re
R=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(R));sys.path.insert(0,str(R/'tools/pydeps'))
import experiment
import numpy as np
raw=[json.loads(x) for x in (R/'data/responses.jsonl').read_text(encoding='utf8').splitlines()]
att=[json.loads(x) for x in (R/'data/http_attempts.jsonl').read_text(encoding='utf8').splitlines()]
cases=json.loads((R/'data/cases.json').read_text(encoding='utf8')); lookup={(c['case_id'],c['condition']):c for c in cases}
scores=list(csv.DictReader((R/'results/trial_scores.csv').open(encoding='utf-8-sig')));scoremap={s['job_id']:s for s in scores}
issues=[]
def check(ok,msg):
 if not ok:issues.append(msg)
# Extract production scoring functions only; do not run analysis/main or rewrite results.
tree=ast.parse((R/'analyze.py').read_text(encoding='utf8')); funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('parse','parse_normalized','evaluate')]
ns={'json':json,'re':re};exec(compile(ast.Module(body=funcs,type_ignores=[]),'production_scoring_only','exec'),ns)
def decode(s):
 if not isinstance(s,str):return None
 try:
  obj,end=json.JSONDecoder().raw_decode(s.strip())
  if s.strip()[end:].strip():return None
 except (ValueError,TypeError):return None
 if not isinstance(obj,dict) or set(obj)!=set(('recipient','value','evidence_ids')):return None
 if type(obj['recipient'])!=str or type(obj['value'])!=int or type(obj['evidence_ids'])!=list:return None
 ids=obj['evidence_ids']
 if any(type(i)!=str for i in ids) or len(set(ids))!=len(ids):return None
 return obj
def independent_normalized(s):
 obj=decode(s)
 if obj is not None:return obj
 if not isinstance(s,str):return None
 lines=s.strip().splitlines()
 if len(lines)<3 or lines[0].strip().lower() not in ('```','```json') or lines[-1].strip()!='```':return None
 return decode('\n'.join(lines[1:-1]))
def metric(obj,c):
 v=obj is not None;r=v and obj['recipient']==c['expected_recipient'];a=v and obj['value']==c['expected_value'];e=v and sorted(obj['evidence_ids'])==sorted(c['expected_evidence_ids'])
 return dict(schema_valid=v,route_correct=bool(r),value_correct=bool(a),evidence_correct=bool(e),joint_correct=bool(r and a),task_success=bool(r and a and e))
check(cases==experiment.build_cases(),'Frozen cases differ from deterministic generator')
for c in cases:
 group=re.search(r'for group (\w+) in',c['user']).group(1)
 selected=[r for r in c['tool_result']['records'] if r['group']==group]
 values=[r['quantity'] for r in selected]
 expect=sum(values) if c['operation']=='sum' else max(values) if c['operation']=='maximum' else len(values)
 check(expect==c['expected_value'],'Ground truth value mismatch '+c['case_id'])
 check(sorted(r['id'] for r in selected)==c['expected_evidence_ids'],'Ground truth evidence mismatch')
expected={'|'.join((c['case_id'],c['condition'],m,p,str(rep))) for c in cases for m in experiment.MODELS for p in experiment.POLICIES for rep in [0,1]}
check(len(raw)==len(expected)==1152,'Total mismatch');check(set(r['job_id'] for r in raw)==expected,'Missing/unexpected jobs');check(len(scoremap)==len(scores)==1152,'Score duplicates/count mismatch')
check(len({r['response']['id'] for r in raw})==1152,'Duplicate server response IDs')
check(set(scoremap)==expected,'CSV job mismatch')
for at in att:
 c=lookup[(at['case_id'],at['condition'])]; req=experiment.request_for(c,at['policy'],at['requested_model'])
 check(hashlib.sha256(json.dumps(req,ensure_ascii=False).encode()).hexdigest()==at['request_sha256'],'Attempt request hash mismatch')
success=[a for a in att if a['status']=='completed'];check(len(success)==1152,'Successful attempt count mismatch')
check({a['job_id']:a for a in success}=={r['job_id']:r for r in raw},'Success log/raw discrepancy')
replayed=[];diffs=[]
for r in raw:
 c=lookup[(r['case_id'],r['condition'])]; content=r['response']['choices'][0]['message']['content'];p=decode(content);n=independent_normalized(content)
 check(r['response']['model']==r['requested_model'],'Returned model mismatch')
 check(p==ns['parse'](content) and n==ns['parse_normalized'](content),'Parser implementation discrepancy '+r['job_id'])
 check(p is None or p==n,'Normalization alters already-parsed payload')
 sm=metric(p,c);nm=metric(n,c);s=scoremap[r['job_id']]
 for prefix,obj in [('',p),('normalized_',n)]:
  for k,val in ns['evaluate'](obj,c).items():check(s[prefix+k]==str(val),'CSV metric mismatch '+r['job_id']+' '+prefix+k)
  for k,val in metric(obj,c).items():check(s[prefix+k]==str(val),'Independent score mismatch '+r['job_id']+' '+prefix+k)
 ch=r['response']['choices'][0];usage=r['response']['usage']
 check(s['finish_reason']==ch['finish_reason'],'Finish mismatch');check(int(s['completion_tokens'])==usage['completion_tokens'],'Token mismatch')
 rr=dict(job_id=r['job_id'],model=r['requested_model'],condition=r['condition'],policy=r['policy'],repeat=r['repeat'],case_id=r['case_id'],context=c['context'],strict_joint=sm['joint_correct'],normalized_joint=nm['joint_correct'],strict_valid=p is not None,normalized_valid=n is not None,recovered=p is None and n is not None,finish=ch['finish_reason'],completion_tokens=usage['completion_tokens'],timestamp=r['started_at_utc'],prior_errors=sum(a['status']!='completed' for a in att if a['job_id']==r['job_id']),content=content)
 replayed.append(rr)
 if rr['recovered']:diffs.append({k:rr[k] for k in ('job_id','model','condition','policy','strict_joint','normalized_joint','finish','completion_tokens','content')})
flat=list(csv.DictReader((R/'results/condition_counts.csv').open(encoding='utf-8-sig')))
agg=[]
for row in flat:
 sub=[x for x in replayed if all(x[k]==row[k] for k in ('model','condition','policy'))]
 for ck,rk in [('joint_correct','strict_joint'),('normalized_joint_correct','normalized_joint'),('schema_valid','strict_valid'),('normalized_schema_valid','normalized_valid'),('fence_recovered','recovered')]:check(sum(x[rk] for x in sub)==int(row[ck]),'Aggregate mismatch '+ck)
 agg.append({k:row[k] for k in ('model','condition','policy','n','schema_valid','normalized_schema_valid','joint_correct','normalized_joint_correct','fence_recovered')})
focus=[x for x in replayed if x['model']=='qwen3.5-plus-2026-02-15' and x['condition']=='correction_claim']
focus_counts={}
for pol in experiment.POLICIES:
 ss=[x for x in focus if x['policy']==pol]
 focus_counts[pol]={'n':len(ss),'strict_joint':sum(x['strict_joint'] for x in ss),'normalized_joint':sum(x['normalized_joint'] for x in ss),'raw_json':sum(x['strict_valid'] for x in ss),'fence_recovered':sum(x['recovered'] for x in ss),'recovered_correct':sum(x['recovered'] and x['normalized_joint'] for x in ss),'recovered_wrong':sum(x['recovered'] and not x['normalized_joint'] for x in ss),'finish':dict(collections.Counter(x['finish'] for x in ss)),'completion_token_range':[min(x['completion_tokens'] for x in ss),max(x['completion_tokens'] for x in ss)],'jobs_with_prior_errors':sum(x['prior_errors']>0 for x in ss),'by_repeat':{str(rep):{'n':24,'strict':sum(x['strict_joint'] for x in ss if x['repeat']==rep),'normalized':sum(x['normalized_joint'] for x in ss if x['repeat']==rep),'fences':sum(x['recovered'] for x in ss if x['repeat']==rep)} for rep in [0,1]}}
# Recompute prespecified paired-task intervals with explicit task ID joins.
contrasts=list(csv.DictReader((R/'results/paired_contrasts.csv').open(encoding='utf-8-sig')))
for c in contrasts:
 for label,prefix in [('case_id',''),('context','context_')]:
  groups=sorted({x[label] for x in replayed if x['model']==c['model'] and x['condition']==c['condition']});key='strict_joint' if c['parser']=='strict' else 'normalized_joint'
  ds=[]
  for g in groups:
   means=[]
   for pol in ['evidence_binding','boundary']:
    vals=[x[key] for x in replayed if x['model']==c['model'] and x['condition']==c['condition'] and x[label]==g and x['policy']==pol];means.append(np.mean(vals))
   ds.append(means[0]-means[1])
  d=np.array(ds);rng=np.random.default_rng(7012026);sim=d[rng.integers(0,len(d),(10000,len(d)))].mean(axis=1);lo,hi=np.quantile(sim,[.025,.975])
  for k,v in [('difference',float(d.mean())),('low',float(lo)),('high',float(hi))]:check(abs(v-float(c[prefix+k]))<1e-12,'Contrast mismatch '+str(c))
report={'scope':'Offline audit of Experiment 1; no API calls or changes to original data.','issues':issues,'raw_trials':len(raw),'models':dict(collections.Counter(r['requested_model'] for r in raw)),'attempt_status':dict(collections.Counter(str(x.get('http_status',x['status'])) for x in att)),'finish_all':dict(collections.Counter(x['finish'] for x in replayed)),'timestamp_range':[min(x['timestamp'] for x in replayed),max(x['timestamp'] for x in replayed)],'qwen35_correction':focus_counts,'all_model_fences':{m:sum(x['recovered'] for x in replayed if x['model']==m) for m in experiment.MODELS},'non_stop_trials':[{k:v for k,v in x.items() if k!='content'} for x in replayed if x['finish']!='stop'],'aggregates':agg,'verified':['all job IDs and independent ground truth','all 1204 attempt request hashes','server model and response IDs','success log matches raw response archive','independent parser vs production parser on all recorded outputs','all per-trial scoring booleans and aggregate counts','paired task and 8-context contrasts/intervals','same raw response drives both parsers']}
(O/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
with (O/'fence_replay_details.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=diffs[0]);w.writeheader();w.writerows(diffs)
print(json.dumps({k:v for k,v in report.items() if k!='aggregates'},ensure_ascii=False,indent=2))
