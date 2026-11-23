"""Retrieve citation metadata directly from the original arXiv landing pages."""
import json, urllib.request
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES=[('greshake','2302.12173'),('bipia','2312.14197'),('struq','2402.06363'),('injecagent','2403.02691'),('hierarchy','2404.13208'),('agentdojo','2406.13352'),('camel','2503.18813')]
class Metadata(HTMLParser):
    def __init__(self):super().__init__();self.meta={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):self.meta.setdefault(a['name'],[]).append(a.get('content',''))
def esc(s):
    for a,b in [('眉',r'\"u'),('枚',r'\"o'),('盲',r'\"a'),('猫',r'\`e'),('茅',r"\'e"),('膰',r"\'c"),('拧',r'\v{s}'),('&',r'\&')]:s=s.replace(a,b)
    return s
entries=[];allmeta=[]
for key,aid in SOURCES:
    url='https://arxiv.org/abs/'+aid
    req=urllib.request.Request(url,headers={'User-Agent':'citation-verification/1.0'})
    with urllib.request.urlopen(req,timeout=30) as r:html=r.read().decode()
    p=Metadata();p.feed(html);m=p.meta
    title=m['citation_title'][0];authors=' and '.join(m['citation_author']);year=m['citation_date'][0][:4]
    entries.append('@misc{'+key+',\n  title={{'+esc(title)+'}},\n  author={'+esc(authors)+'},\n  year={'+year+'},\n  eprint={'+aid+'},\n  archivePrefix={arXiv},\n  doi={10.48550/arXiv.'+aid+'},\n  url={'+url+'}\n}')
    allmeta.append({'key':key,'url':url,'metadata':m})
(ROOT/'references.bib').write_text('\n\n'.join(entries)+'\n',encoding='utf-8')
(ROOT/'data/reference_metadata.json').write_text(json.dumps(allmeta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Verified',len(entries),'reference records against primary landing pages.')
