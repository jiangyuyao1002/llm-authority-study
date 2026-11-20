"""Read-only retrieval of primary citation metadata and upstream data licence."""
import hashlib,json,urllib.request
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Metadata(HTMLParser):
    def __init__(self):super().__init__();self.meta={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):self.meta.setdefault(a['name'],[]).append(a.get('content',''))
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'research-provenance/1.0'}),timeout=30) as r:return r.read()
records=[];entries=[]
for key,aid in [('toolparse','2601.04795'),('tracesafe','2604.07223')]:
    url='https://arxiv.org/abs/'+aid;blob=fetch(url);p=Metadata();p.feed(blob.decode('utf-8'));m=p.meta
    entries.append('@misc{'+key+',\n  title={{'+m['citation_title'][0]+'}},\n  author={'+ ' and '.join(m['citation_author'])+'},\n  year={'+m['citation_date'][0][:4]+'},\n  eprint={'+aid+'},\n  archivePrefix={arXiv},\n  doi={10.48550/arXiv.'+aid+'},\n  url={'+url+'}\n}')
    records.append(dict(key=key,url=url,metadata=m,landing_page_sha256=hashlib.sha256(blob).hexdigest()))
url='https://aclanthology.org/P15-1142.bib';blob=fetch(url);bib=blob.decode('utf-8').replace('@inproceedings{pasupat-liang-2015-compositional,','@inproceedings{wikitable,')
# Preserve acronyms/title capitalization under the manuscript bibliography style.
bib=bib.replace('title = "Compositional Semantic Parsing on Semi-Structured Tables"','title = {{Compositional Semantic Parsing on Semi-Structured Tables}}')
entries.append(bib);records.append(dict(key='wikitable',url=url,bibtex_sha256=hashlib.sha256(blob).hexdigest()))
(ROOT.parent/'references_v2.bib').write_text((ROOT.parent/'references.bib').read_text(encoding='utf-8')+'\n'+'\n\n'.join(entries)+'\n',encoding='utf-8')
url='https://raw.githubusercontent.com/ppasupat/WikiTableQuestions/master/LICENSE';blob=fetch(url)
(ROOT/'source/WikiTableQuestions_LICENSE').write_bytes(blob)
records.append(dict(key='wikitable_license',url=url,sha256=hashlib.sha256(blob).hexdigest()))
(ROOT/'source_metadata_additions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Three additional references and the upstream dataset licence saved.')
