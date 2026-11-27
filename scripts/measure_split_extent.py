"""Add unique-string denominators for selected already cached split files.

Only PlantCAD2 test/validation sequence columns are read. Full training and
reference-genome data are not reloaded. No network or dataset downloads.
"""
from pathlib import Path
import hashlib,json,collections
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/split-inspections.json';d=json.loads(p.read_text());r=d['cases']['plantcad-cell']
r['distinct_sequences']={};r['duplicate_sequence_rows']={}
for split in ['test','validation']:
    f=ROOT/'research/artifacts/final-audit/plantcad-ft/cell_type_specific_acr'/f'{split}-00000-of-00001.parquet'
    counts=collections.Counter()
    for b in pq.ParquetFile(f).iter_batches(columns=['sequence'],batch_size=8192):
        counts.update(hashlib.sha256(s.encode()).digest() for s in b.column(0).to_pylist())
    r['distinct_sequences'][split]=len(counts)
    r['duplicate_sequence_rows'][split]=sum(counts.values())-len(counts)
    print(split,r['partition_rows'][split],len(counts),'excess repeated rows',r['duplicate_sequence_rows'][split])
r['denominator_method']='Complete test and validation DNA columns read from the same pinned cached Parquets to count distinct exact strings. No new training sequence scan. Shared-string percentages use this unique-string denominator, not an affected-row denominator.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
