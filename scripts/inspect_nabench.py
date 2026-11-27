"""Measure every CSV in the pinned NABench data directory; no model inference."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'research/artifacts/final-audit/registered-nabench'
REV='99c8681ec1eab706e10ff90a5c329dcf184cc1d1'


def inspect():
    metadata=list(csv.DictReader((RELEASE/'metadata.csv').open()))
    names={r['DMS_ID'] for r in metadata}
    scans=[]
    for file in sorted((RELEASE/'data').glob('*.csv')):
        with file.open() as handle:
            reader=csv.DictReader(handle)
            cols=reader.fieldnames
            rows=list(reader)
        lengths=collections.Counter(len(r['sequence']) for r in rows)
        alphabet=collections.Counter(c for r in rows for c in r['sequence'])
        scores=[float(r['DMS_score']) for r in rows if r['DMS_score']]
        finite=[v for v in scores if math.isfinite(v)]
        scans.append(dict(id=file.stem,path='data/'+file.name,rows=len(rows),columns=cols,
            bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
            unique_sequences=len({r['sequence'] for r in rows}),length_min=min(lengths),length_max=max(lengths),
            alphabet=dict(alphabet),missing_score_rows=len(rows)-len(scores),nonfinite_score_rows=len(scores)-len(finite),
            score_min=min(finite),score_max=max(finite),in_manifest=file.stem in names))
    files={r['id'] for r in scans}
    result=dict(revision=REV,manifest_rows=len(metadata),manifest_unique_ids=len(names),
        data_files=len(scans),data_rows=sum(s['rows'] for s in scans),
        manifest_ids_without_files=sorted(names-files),files_without_manifest_entries=sorted(files-names),files=scans)
    (ROOT/'data/nabench-artifact-inspections.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k not in ('files','manifest_ids_without_files')})


if __name__=='__main__':inspect()
