"""Reproduce measurements for the 2026-11-26 task-audit follow-up.

Downloads are cached outside the published catalogue. No model inference is run.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import io
import json
import collections
import math
import requests
import zipfile
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research/artifacts/audit-followup'
CACHE.mkdir(parents=True, exist_ok=True)

def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        # This public archive host omits its issuer chain. No credentials are sent;
        # hashes identify the retrieved bytes, not an authenticated publisher signature.
        response = requests.get(url, timeout=180,
                                verify=False if url.startswith('https://marks.hms.harvard.edu/') else True)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path

def measure_csv(path, sequence, label):
    raw = path.read_bytes()
    labels = collections.Counter()
    lengths = collections.Counter()
    missing = collections.Counter()
    seqs = set()
    numeric = []
    eligible = 0
    n = 0
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        n += 1
        labels[row.get(label, '')] += 1
        seq = row.get(sequence, '')
        lengths[len(seq)] += 1
        seqs.add(hashlib.sha256(seq.encode()).hexdigest())
        for k, v in row.items():
            if v in ('', 'NaN', 'nan', 'NA'): missing[k] += 1
        if label == 'DMS_score':
            try:score=float(row[label])
            except (TypeError,ValueError):score=float('nan')
            if math.isfinite(score):
                numeric.append(score)
                if row.get('mutant','') not in ('','NaN','nan','NA'):eligible+=1
    return dict(rows=n, columns=next(csv.reader(io.StringIO(raw.decode('utf-8-sig')))),
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                label_counts=dict(labels) if len(labels) <= 50 else None,
                label_distinct=len(labels), length_min=min(lengths), length_max=max(lengths),
                missing=dict(missing), distinct_sequences=len(seqs),
                numeric_score_range=[min(numeric),max(numeric)] if numeric else None,
                scored_mutant_rows_before_model_missingness=eligible if label=='DMS_score' else None), seqs

def geneb():
    spec=json.loads((ROOT/'research/sources/darlednik--GENEB/benchmark/benchmark_spec.json').read_text())
    repo=spec['dataset']['repo_id']; rev=spec['dataset']['revision']
    base=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/'
    download(base+'README.md',CACHE/'geneb/README.md')
    ids=[r['id'] for r in spec['tasks']]
    def one(args):
        task,split=args
        path=f'tasks/{task}/{split}.csv'
        file=download(base+path,CACHE/'geneb'/path)
        stats,seqs=measure_csv(file,'text','label')
        return dict(task=task,split=split,repo=repo,revision=rev,path=path,**stats),seqs
    rows=[]; hashes={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(one,(task,split)) for task in ids for split in ('train','test')]):
            try:
                row,seqs=f.result();rows.append(row);hashes[(row['task'],row['split'])]=seqs
                if len(rows)%20==0:print('GENEB files',len(rows),flush=True)
            except Exception as e:print('GENEB ERROR',repr(e),flush=True);raise
    for row in rows:
        row['train_test_exact_sequence_overlap']=len(hashes[(row['task'],'train')] & hashes[(row['task'],'test')])
    (ROOT/'data/geneb-artifact-inspections.json').write_text(json.dumps(sorted(rows,key=lambda x:(x['task'],x['split'])),indent=2)+'\n')

def rnagym():
    rows=[]; sequence_hashes={}
    for name in ('fitness_processed_assays','fitness_CV_splits'):
        url=f'https://marks.hms.harvard.edu/rnagym/fitness_prediction/{name}.zip'
        archive=download(url,CACHE/(name+'.zip'))
        with zipfile.ZipFile(archive) as z:
            members=[x for x in z.namelist() if x.endswith('.csv') and '__MACOSX' not in x]
            for member in members:
                dest=CACHE/'rnagym'/member
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member))
                with dest.open() as f: fields=next(csv.reader(f))
                seq=next((x for x in ('mutated_sequence','sequence','mutant_sequence') if x in fields),None)
                if not seq: print('RNAGym no sequence',member,fields,flush=True);continue
                stat,seqs=measure_csv(dest,seq,'DMS_score')
                stat.update(archive=name,archive_url=url,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),member=member,sequence_column=seq)
                if name=='fitness_CV_splits':
                    sequence_hashes[member]=seqs
                    records=list(csv.DictReader(dest.open()))
                    stat['folds']={key:dict(collections.Counter(r[key] for r in records)) for key in fields if 'fold' in key.lower() or 'split' in key.lower()}
                rows.append(stat)
        print(name,len(members),'files',flush=True)
    for stat in rows:
        if stat['archive']=='fitness_CV_splits':
            member=stat['member'];other=member.replace('/train/','/val/').replace('_train.csv','_val.csv') if '/train/' in member else member.replace('/val/','/train/').replace('_val.csv','_train.csv')
            stat['train_validation_exact_sequence_overlap']=len(sequence_hashes[member] & sequence_hashes[other])
    (ROOT/'data/rnagym-artifact-inspections.json').write_text(json.dumps(rows,indent=2)+'\n')

def rnagym_evo2_predictions():
    # Range reads avoid downloading unrelated model predictions. Each selected
    # member is decompressed and checked against its ZIP CRC, then SHA-256 hashed.
    url='https://marks.hms.harvard.edu/rnagym/fitness_prediction/model_predictions.zip'
    head=requests.head(url,timeout=60,verify=False);head.raise_for_status()
    size=int(head.headers['Content-Length'])
    def ranged(start,end):
        response=requests.get(url,headers={'Range':f'bytes={start}-{end}'},timeout=90,verify=False,stream=True)
        if response.status_code!=206:
            response.close();raise RuntimeError('Publisher did not honor the requested byte range')
        return response.content
    tail=ranged(size-65558,size-1)
    end=tail.rfind(b'PK\x05\x06')
    if end<0:raise RuntimeError('ZIP end record not found')
    directory_offset=struct.unpack('<4s4H2LH',tail[end:end+22])[-2]
    directory=ranged(directory_offset,size-1)
    sparse=CACHE/'rna-predictions-central-directory.zip'
    with sparse.open('wb') as f:f.seek(directory_offset);f.write(directory)
    with zipfile.ZipFile(sparse) as z:
        infos=[x for x in z.infolist() if x.filename.startswith('model_predictions/evo2/') and x.filename.endswith('.csv')]
    def one(info):
        path=CACHE/'rnagym-predictions'/info.filename
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            raw=ranged(info.header_offset,info.header_offset+30+len(info.filename.encode())+1000+info.compress_size)
            fields=struct.unpack('<4s5H3L2H',raw[:30]);offset=30+fields[-2]+fields[-1]
            if info.compress_type!=8:raise RuntimeError('Unsupported ZIP compression')
            payload=zlib.decompress(raw[offset:offset+info.compress_size],-15)
            if zlib.crc32(payload)!=info.CRC:raise RuntimeError('ZIP CRC mismatch')
            path.write_bytes(payload)
        payload=path.read_bytes()
        if zlib.crc32(payload)!=info.CRC:raise RuntimeError('Cached member differs from archive CRC')
        records=list(csv.DictReader(io.StringIO(payload.decode())))
        columns=list(records[0]);scores=[x for x in columns if 'score' in x.lower() and x!='DMS_score']
        def finite(value):
            try:return math.isfinite(float(value))
            except (TypeError,ValueError):return False
        counts={col:sum(bool(r.get('mutant')) and finite(r.get('DMS_score')) and finite(r.get(col)) for r in records) for col in scores}
        return dict(member=info.filename,rows=len(records),columns=columns,score_columns=scores,scored_rows=counts,sha256=hashlib.sha256(payload).hexdigest(),zip_crc32=format(info.CRC,'08x'),archive_url=url)
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(one,infos))
    (ROOT/'data/rnagym-evo2-prediction-inspections.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('RNAGym Evo 2 prediction files',len(rows),flush=True)

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(geneb),pool.submit(rnagym),pool.submit(rnagym_evo2_predictions)]):future.result()
