"""Full PlantCAD2 maize accessibility release scan; research environment only."""
import requests,json,pathlib,concurrent.futures,collections,hashlib
import pyarrow.parquet as pq
p=pathlib.Path(__file__).resolve().parents[1];cache=p/'research/artifacts/final-audit/plantcad-ft';cache.mkdir(exist_ok=True)
rev='de8bd9b67bb413b1502c4bf9e369ddc46180cb10';tree=json.load(open(p/'research/artifacts/final-audit/plantcad-ft-tree.json'))
files=[f for f in tree if f['path'].startswith('cell_type_specific_acr/') and f['path'].endswith('.parquet')]
def scan(f):
 file=cache/f['path'];file.parent.mkdir(exist_ok=True)
 if not file.exists() or file.stat().st_size!=f['size']:
  r=requests.get(f'https://huggingface.co/datasets/plantcad/PlantCAD2_fine_tuning_tasks/resolve/{rev}/{f["path"]}',timeout=90);r.raise_for_status();file.write_bytes(r.content)
 h=hashlib.sha256(file.read_bytes()).hexdigest();q=pq.ParquetFile(file);ch=collections.Counter();lengths=collections.Counter();ll=collections.Counter();pos=collections.Counter();nonbinary=0;coords=set();seqs=set()
 for b in q.iter_batches(batch_size=8192):
  for r in b.to_pylist():
   ch[r['chr']]+=1;lengths[len(r['sequence'])]+=1;ll[len(r['label'])]+=1;nonbinary+=bool(set(r['label'])-{'0','1'})
   coords.add((r['chr'],r['start'],r['end']));seqs.add(hashlib.sha256(r['sequence'].encode()).digest())
   for i,v in enumerate(r['label']):pos[i]+=v=='1'
 print(f['path'],q.metadata.num_rows,dict(ch),flush=True)
 return dict(path=f['path'],bytes=f['size'],rows=q.metadata.num_rows,sha256=h,chromosomes=dict(ch),sequence_lengths=dict(lengths),label_lengths=dict(ll),nonbinary_labels=nonbinary,positives_by_track_index=dict(pos)),coords,seqs
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(scan,files))
part=collections.defaultdict(set);seqpart=collections.defaultdict(set)
for (r,c,s) in results:
 split=r['path'].split('/')[1].split('-')[0];part[split]|=c;seqpart[split]|=s
out={'repo':'plantcad/PlantCAD2_fine_tuning_tasks','revision':rev,'inspection':'Complete file download and full row/sequence/label/coordinate scan, all six cell-type ACR Parquets','files':[r for r,c,s in results],'distinct_coordinates':{k:len(v) for k,v in part.items()},'coordinate_intersections':{a+'-'+b:len(part[a]&part[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]},'exact_sequence_intersections':{a+'-'+b:len(seqpart[a]&seqpart[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}}
(p/'data/plantcad-cell-artifact-inspections.json').write_text(json.dumps(out,indent=2)+'\n')
