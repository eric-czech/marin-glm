"""Inspect cached original BEND BED files and the enhancer label HDF5.

Raw files are available from the URLs recorded in the resulting manifest.
The optional h5py/numpy dependencies are for this research inspection only;
the routine catalogue build remains Python-standard-library only.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/artifacts/splice-audit'


def inspect():
    results=[]
    for task in ['gene_finding','enhancer_annotation']:
        path=CACHE/(task+'.bed')
        rows=list(csv.DictReader(path.open(),delimiter='\t'))
        id_column='transcript_id' if task=='gene_finding' else 'gene'
        ids=Counter(r[id_column] for r in rows)
        spans=[int(r['end'])-int(r['start']) for r in rows]
        split_counts=Counter(r['split'] for r in rows)
        by_split={s:{r[id_column] for r in rows if r['split']==s} for s in sorted(split_counts)}
        stat=dict(task=task,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            bytes=path.stat().st_size,rows=len(rows),split_counts=dict(split_counts),unique_ids=len(ids),
            duplicate_ids={k:v for k,v in ids.items() if v>1},
            url=f'https://sid.erda.dk/share_redirect/aNQa0Oz2lY/data/{task}/{task}.bed',
            coordinate_span_min=min(spans),coordinate_span_max=max(spans),
            row_id_overlap_between_splits={a+' / '+b:len(by_split[a]&by_split[b]) for a in by_split for b in by_split if a<b})
        if task=='gene_finding':
            stat['flank_metadata_totals']=dict(Counter(int(r['flank_left'])+int(r['flank_right']) for r in rows))
            stat['duplicates_within_train_only']=all(all(r['split']=='train' for r in rows if r[id_column]==id) for id in stat['duplicate_ids'])
        else:
            import h5py
            import numpy as np
            stat['fold_chromosomes']={s:sorted({r['chromosome'] for r in rows if r['split']==s}) for s in by_split}
            hpath=CACHE/'enhancer_annotation.hdf5'
            with h5py.File(hpath) as h:
                dataset=h['labels']
                vectors=dataset[...]
                values,counts=np.unique(np.concatenate(vectors),return_counts=True)
                stat['label_hdf5']=dict(dataset='labels',container_shape=list(dataset.shape),dtype=str(dataset.dtype),
                    vector_lengths=dict(Counter(len(v) for v in vectors)),
                    values={str(v):int(n) for v,n in zip(values,counts)},
                    sha256=hashlib.sha256(hpath.read_bytes()).hexdigest(),bytes=hpath.stat().st_size)
        results.append(stat)
    return results


if __name__=='__main__':
    path=ROOT/'data/bend-output-artifact-inspections.json'
    path.write_text(json.dumps(inspect(),ensure_ascii=False,indent=2)+'\n')
