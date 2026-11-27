"""Full translation split/target checks; research environment only."""
import requests,json,pathlib,concurrent.futures,collections,hashlib,math
import pyarrow.parquet as pq
p=pathlib.Path(__file__).resolve().parents[1];cache=p/'research/artifacts/final-audit/plantcad-ft';cache.mkdir(exist_ok=True)
rev='de8bd9b67bb413b1502c4bf9e369ddc46180cb10';tree=json.load(open(p/'research/artifacts/final-audit/plantcad-ft-tree.json'))
files=[f for f in tree if f['path'].startswith(('cross_species_leaf_absolute_translation/','cross_species_leaf_on_off_translation/')) and f['path'].endswith('.parquet')]
def scan(f):
 file=cache/f['path'];file.parent.mkdir(exist_ok=True)
 if not file.exists() or file.stat().st_size!=f['size']:
  r=requests.get(f'https://huggingface.co/datasets/plantcad/PlantCAD2_fine_tuning_tasks/resolve/{rev}/{f["path"]}',timeout=90);r.raise_for_status();file.write_bytes(r.content)
 q=pq.ParquetFile(file);ch=collections.Counter();lengths=collections.Counter();genes=set();seqs=set();mismatch=0;maxerr=0
 for b in q.iter_batches(batch_size=8192):
  for r in b.to_pylist():
   ch[r['chr']]+=1;lengths[len(r['sequence'])]+=1;genes.add(r['gene']);seqs.add(hashlib.sha256(r['sequence'].encode()).digest())
   if 'on_off' in f['path']:mismatch+=int(r['label'])!=int(r['tpm']>1)
   else:maxerr=max(maxerr,abs(r['label']-math.log10(1+r['tpm'])))
 out=dict(path=f['path'],bytes=f['size'],rows=q.metadata.num_rows,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),chromosomes=dict(ch),sequence_lengths=dict(lengths),gene_ids=len(genes),binary_label_mismatches=mismatch,log10_1_plus_TPM_max_abs_error=maxerr)
 print(f['path'],out['rows'],flush=True);return out,genes,seqs
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(scan,files))
by={}
for r,g,s in results:by[r['path'].split('/')[0]+'|'+r['path'].split('/')[1].split('-')[0]]=(g,s)
inter={}
for task in ['cross_species_leaf_absolute_translation','cross_species_leaf_on_off_translation']:
 inter[task]={a+'-'+b:{'gene_ids':len(by[task+'|'+a][0]&by[task+'|'+b][0]),'exact_sequences':len(by[task+'|'+a][1]&by[task+'|'+b][1])} for a,b in [('train','validation'),('train','test'),('validation','test')]}
out={'revision':rev,'files':[r for r,g,s in results],'intersections':inter}
(p/'data/plantcad-translation-artifact-inspections.json').write_text(json.dumps(out,indent=2)+'\n')
