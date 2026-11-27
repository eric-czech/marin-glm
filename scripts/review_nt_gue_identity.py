"""Reproduce NT/GUE pool identity using bounded, pinned native-file reads.

Verifies previously recorded file hashes, retains partition intersections, and
writes only a summary report; no raw benchmark files are stored. Requires
requests and pyarrow. Run explicitly from the repository root.
"""
import requests,concurrent.futures,io,csv,json,hashlib,collections
import pyarrow.parquet as pq
from pathlib import Path
facts=json.loads(Path('data/existing-benchmark-inspections.json').read_text())['facts']['NT_GUE_FILES']
selected=[r for r in facts if r['file'].split('/')[0]in ['H3','H4'] or any('/emp_'+m+'/'in r['file']for m in ['H3','H4'])]
print([(r['repo'],r['file'])for r in selected],flush=True)
def get(r):
 u=f'https://huggingface.co/datasets/{r["repo"]}/resolve/{r["revision"]}/{r["file"]}'
 q=requests.get(u,timeout=30,stream=True);q.raise_for_status();b=bytearray()
 for chunk in q.iter_content(262144):
  b.extend(chunk)
  if len(b)>10000000:q.close();raise ValueError('Per-file bound exceeded')
 h=hashlib.sha256(b).hexdigest();assert h==r['sha256'],(r['file'],h)
 if r['file'].endswith('.parquet'):rows=pq.read_table(io.BytesIO(b)).to_pylist()
 else:rows=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
 keys=list(rows[0]);seq=next(k for k in ['sequence','text','seq']if k in keys);label=next(k for k in ['label','labels']if k in keys)
 result=[(x[seq].upper(),str(x[label]))for x in rows]
 rec={k:r[k]for k in ['repo','revision','file','rows','sha256']};rec.update(url=u,bytes=len(b),sequence_column=seq,label_column=label,unique_sequences=len({s for s,l in result}),normalization_changed_rows=sum(x[seq]!=x[seq].upper() for x in rows))
 print('read',r['file'],len(b),len(result),flush=True);return rec,result
with concurrent.futures.ThreadPoolExecutor(4)as ex:data=list(ex.map(get,selected))
out=dict(inspected='2026-11-27',method='Complete pinned native files; verify pre-existing SHA-256; compare uppercase sequence–label multisets, separately for full pools and partition pairs. No approximate or coordinate mapping is inferred.',files=[r for r,v in data],comparisons={})
for mark in ['H3','H4']:
 nt={r['file'].split('/')[-1].split('.')[0]:v for r,v in data if r['repo'].startswith('Insta')and r['file'].startswith(mark+'/')}
 gue={r['file'].split('/')[-1].split('.')[0]:v for r,v in data if '/emp_'+mark+'/'in r['file']}
 a=collections.Counter(x for rows in nt.values()for x in rows);b=collections.Counter(x for rows in gue.values()for x in rows)
 cross=[]
 for l,lv in nt.items():
  for rr,rv in gue.items():cross.append(dict(nt_partition=l,gue_partition=rr,shared_sequence_label_rows=sum((collections.Counter(lv)&collections.Counter(rv)).values())))
 out['comparisons'][mark]=dict(nt_rows=sum(a.values()),gue_rows=sum(b.values()),nt_unique_sequences=len({s for s,l in a}),gue_unique_sequences=len({s for s,l in b}),shared_rows=sum((a&b).values()),identical_multisets=a==b,nt_only=sum((a-b).values()),gue_only=sum((b-a).values()),partition_pairs=cross,examples_nt_only=[dict(sequence_sha256=hashlib.sha256(s.encode()).hexdigest(),length=len(s),label=l)for s,l in list((a-b).keys())[:4]],examples_gue_only=[dict(sequence_sha256=hashlib.sha256(s.encode()).hexdigest(),length=len(s),label=l)for s,l in list((b-a).keys())[:4]])
 print(mark,out['comparisons'][mark],flush=True)
Path('data/nt-gue-identity-review.json').write_text(json.dumps(out,indent=2)+'\n')
