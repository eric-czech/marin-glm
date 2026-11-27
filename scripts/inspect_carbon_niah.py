from pathlib import Path
import json,collections,concurrent.futures
import pyarrow.parquet as pq
import fsspec
root=Path('research/artifacts/final-audit/root-residual');j=json.load(open(root/'genomic-niah.json'));tree=json.load(open(root/'genomic-niah-tree.json'))
rows=[r for r in tree if r['path'].endswith('.parquet')]
def scan(r):
 url=f'https://huggingface.co/datasets/{j["id"]}/resolve/{j["sha"]}/{r["path"]}'
 try:
  with fsspec.open(url,'rb',block_size=262144,cache_type='readahead') as f:
   p=pq.ParquetFile(f)
   cols=[k for k in ['source','depth','context_length_bp','context_length_tokens','key_len_bp','value_len_bp','num_distractors','mutation_distance'] if k in p.schema_arrow.names]
   t=p.read(columns=cols);c={k:dict(collections.Counter(map(str,t[k].to_pylist()))) for k in cols}
   return dict(path=r['path'],bytes=r['size'],rows=p.metadata.num_rows,columns=p.schema_arrow.names,categories=c,source_lfs=r.get('lfs'),inspection='Complete metadata-column scan and Parquet row counts; DNA payload validation separately covers all four 4k configurations.')
 except Exception as e:return dict(path=r['path'],error=type(e).__name__)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 out=[]
 for result in pool.map(scan,rows):out.append(result);print(result['path'],result.get('rows'),result.get('error'),flush=True)
Path('data/carbon-niah-metadata-inspections.json').write_text(json.dumps({'revision':j['sha'],'files':out},indent=2)+'\n')
