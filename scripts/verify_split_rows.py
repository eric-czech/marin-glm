"""Verify current HF viewer links against pinned PlantCAD2 row examples.

Downloads only bounded API rows and file metadata, never dataset files.
"""
from pathlib import Path
import json,requests,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/split-inspections.json';d=json.loads(p.read_text())
case=d['cases']['plantcad-cell'];repo=case['repo'];rev=case['revision']
s=requests.Session();r=s.get('https://huggingface.co/api/datasets/'+repo,timeout=45);r.raise_for_status();head=r.json()['sha'];assert head==rev
rows={}
for e in d['examples']:
 if e['case']=='plantcad-cell':
  for side in ['left','right']:
   row=e[side];rows[row['split'],row['split_row']]=row

def verify(pair):
 (split,i),row=pair
 params=dict(dataset=repo,config='cell_type_specific_acr',split=split,offset=i,length=1)
 r=requests.get('https://datasets-server.huggingface.co/rows',params=params,timeout=45);r.raise_for_status();value=r.json()['rows'][0]['row']
 assert (value['chr'],value['start'],value['end'])==(row['chr'],row['start'],row['end'])
 return (split,i),dict(api_url=r.url,coordinate_match=True,sequence_sha256=__import__('hashlib').sha256(value['sequence'].encode()).hexdigest(),head_at_verification=head,checked='2026-11-27',viewer_revision_scope='Current dataset viewer, verified against pinned-release coordinates at inspection time; immutable Parquet URL and file row retained separately.')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:verified=dict(pool.map(verify,rows.items()))
for e in d['examples']:
 if e['case']=='plantcad-cell':
  for side in ['left','right']:
   row=e[side];row['viewer_verification']=verified[row['split'],row['split_row']]
   if e['kind']=='exact-sequence':assert row['viewer_verification']['sequence_sha256']==e['sequence_sha256']
d['cases']['plantcad-cell']['viewer_rows_verified']=len(verified)
d['new_dataset_file_download_bytes']=0;d.pop('network_bytes_downloaded',None)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Verified',len(verified),'live viewer rows against pinned file records')
# Small immutable metadata record establishes that the recovery input release is
# multi-GB; no Parquet payload or reference genome is downloaded.
r=requests.get('https://huggingface.co/api/datasets/GenerTeam/sequence-recovery/tree/3ac1de1be0e4c55dd180c719c1f3805a2cdb9be9',params={'recursive':'true'},timeout=45);r.raise_for_status()
files=[{k:f[k] for k in ['path','size']} for f in r.json() if f['type']=='file']
d['large_release_metadata']={'generator-recovery':{'repo':'GenerTeam/sequence-recovery','revision':'3ac1de1be0e4c55dd180c719c1f3805a2cdb9be9','files':files,'total_parquet_bytes':sum(f['size'] for f in files if f['path'].endswith('.parquet')),'metadata_url':r.url}}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Recovery Parquets bytes',d['large_release_metadata']['generator-recovery']['total_parquet_bytes'])
