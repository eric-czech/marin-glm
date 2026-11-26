"""Inspect pinned PlantCAD Parquet footers, labels and sampled sequences via HTTP ranges.

No model code is executed. Footer hashes are not whole-file hashes. Sequence lengths
are sampled per file; row counts and label counts cover all rows of each scanned file.
Requires requests and pyarrow. Research helper, not part of the offline site build.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import ast,hashlib,io,json,math,re
import pyarrow as pa
import pyarrow.compute as pc
import requests
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/sources/plantcad'
OUT=ROOT/'data/plantcad-artifact-inspections.json'

class Remote(io.RawIOBase):
    def __init__(self,url):
        super().__init__();self.url=url;self.session=requests.Session();self.pos=0;self.cache={};self.bytes_read=0
        r=self.session.get(url,headers={'Range':'bytes=-8'},params={'audit_range':'tail8'},timeout=60)
        r.raise_for_status();assert r.status_code==206,r.status_code
        self.size=int(r.headers['Content-Range'].split('/')[-1]);self.tail=r.content;self.download_url=r.url;assert self.tail[-4:]==b'PAR1'
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,pos,whence=0):
        self.pos=pos if whence==0 else self.pos+pos if whence==1 else self.size+pos;return self.pos
    def range(self,start,end):
        r=self.session.get(self.download_url,headers={'Range':f'bytes={start}-{end-1}'},timeout=90)
        r.raise_for_status();assert r.status_code==206,(r.status_code,self.url)
        assert r.headers['Content-Range'].startswith(f'bytes {start}-{end-1}/'),r.headers['Content-Range']
        assert len(r.content)==end-start;self.bytes_read+=len(r.content);return r.content
    def read(self,n=-1):
        end=self.size if n<0 else min(self.pos+n,self.size);chunks=[];block=65536
        while self.pos<end:
            k=self.pos//block
            if k not in self.cache:self.cache[k]=self.range(k*block,min((k+1)*block,self.size))
            b=self.cache[k];start=self.pos-k*block;part=b[start:min(end-k*block,len(b))];chunks.append(part);self.pos+=len(part)
        return b''.join(chunks)
    def close(self):
        if hasattr(self,'session'):self.session.close()
        super().close()

def inspect(job):
    repo,sha,path,scan_labels=job;url=f'https://huggingface.co/datasets/{repo}/resolve/{sha}/{path}'
    raw=Remote(url);footer_len=int.from_bytes(raw.tail[:4],'little');footer=raw.range(raw.size-8-footer_len,raw.size)
    # Metadata can be read from a minimal container; original column offsets remain valid.
    metadata=pq.read_metadata(io.BytesIO(b'PAR1'+footer))
    pf=pq.ParquetFile(raw);names=pf.schema_arrow.names
    result=dict(repo=repo,revision=sha,path=path,url=f'https://huggingface.co/datasets/{repo}/blob/{sha}/{path}',
                bytes=raw.size,rows=metadata.num_rows,row_groups=metadata.num_row_groups,columns=names,
                footer_sha256=hashlib.sha256(footer).hexdigest(),method='Pinned Parquet footer; full selected-label column scan; first4 sequence rows sampled per file',
                inspected='2026-11-26')
    if scan_labels and 'label' in names:
        label=pf.read(columns=['label']).column('label')
        if pa.types.is_floating(label.type):
            result['continuous_label_summary']={'min':pc.min(label).as_py(),'max':pc.max(label).as_py(),'mean':pc.mean(label).as_py(),'null_count':label.null_count}
        elif pa.types.is_string(label.type) and (str(label[0].as_py()).startswith('[') or (len(str(label[0].as_py()))>2 and set(str(label[0].as_py()))<={'0','1'})):
            lengths=Counter();positives=None
            for chunk in label.chunks:
                for value in chunk.to_pylist():
                    vector=ast.literal_eval(value) if value.startswith('[') else [int(v) for v in value];lengths[len(vector)]+=1
                    if positives is None:positives=[0]*len(vector)
                    assert len(vector)==len(positives)
                    for i,v in enumerate(vector):
                        assert v in (0,1);positives[i]+=int(v)
            result['label_vector_lengths']=dict(lengths);result['positive_counts_by_target_index']=positives
        else:
            counts=Counter()
            for chunk in label.chunks:counts.update(str(v) for v in chunk.to_pylist())
            result['label_counts']=dict(counts)
    for col in ['chr','genome','species']:
        if col in names:
            values=Counter()
            for batch in pf.iter_batches(columns=[col],batch_size=100000):values.update(str(v) for v in batch.column(0).to_pylist())
            result[col+'_counts']=dict(values)
    if 'tpm' in names and 'label' in names:
        values=pf.read(columns=['tpm','label']).to_pydict()
        pairs=list(zip(values['tpm'],values['label']))
        if 'absolute_translation/' in path:
            result['label_transform_checks']={
                'log10_1_plus_tpm_max_abs_error':max(abs(y-math.log10(1+t)) for t,y in pairs),
                'positive_tpm_log10_max_abs_error':max(abs(y-math.log10(t)) for t,y in pairs if t>0),
                'zero_tpm_rows':sum(t==0 for t,y in pairs)}
        elif 'on_off_translation/' in path:
            result['label_transform_checks']={'tpm_gt1_mismatches':sum(y!=int(t>1) for t,y in pairs)}
    result['sequence_samples']={}
    for col in ['sequence','RefSeq','MutSeq']:
        if col in names:
            batch=next(pf.iter_batches(columns=[col],batch_size=4));seqs=batch.column(0).to_pylist()
            result['sequence_samples'][col]=[dict(length=len(s),center=s[max(0,len(s)//2-3):len(s)//2+4]) for s in seqs]
    result['range_bytes_read']=raw.bytes_read;raw.close();return result

def main():
    jobs=[]
    for api_name,repo in [('PlantCAD2_zero_shot_tasks-api.json','plantcad/PlantCAD2_zero_shot_tasks'),('plantcad2-finetune-api.json','plantcad/PlantCAD2_fine_tuning_tasks')]:
        a=json.loads((CACHE/api_name).read_text())
        for row in a['siblings']:
            path=row['rfilename']
            if not path.endswith('.parquet'):continue
            # All zero-shot files; supervised inputs selected to verify labels/chromosomes/sequence format.
            selected=repo.endswith('zero_shot_tasks') or any(path.startswith(prefix) for prefix in ['cell_type_specific_acr/test-', 'cross_species_leaf_absolute_translation/', 'cross_species_leaf_on_off_translation/'])
            if selected:jobs.append((repo,a['sha'],path,True))
    previous=json.loads(OUT.read_text()) if OUT.exists() else []
    done={(r['repo'],r['revision'],r['path']) for r in previous};pending=[j for j in jobs if j[:3] not in done]
    results=list(previous)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(inspect,j):j for j in pending}
        for f in as_completed(futures):
            job=futures[f]
            try:
                r=f.result();results.append(r);OUT.write_text(json.dumps(sorted(results,key=lambda r:(r['repo'],r['path'])),indent=2)+'\n');print(r['path'],r['rows'],'rows; selected columns inspected',flush=True)
            except Exception as e:print('ERROR',job[2],repr(e),flush=True)
if __name__=='__main__':main()
