"""Inspect cached primary artifacts; research step, never part of an offline build.

Run with the research environment (pyarrow/openpyxl). Files are downloaded from
their pinned official releases before this script is run.
"""
from pathlib import Path
import collections
import csv
import hashlib
import json
import math
import pyarrow.parquet as pq
import openpyxl

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/artifacts/final-audit/root-residual'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(4*1024*1024):h.update(block)
    return h.hexdigest()


def scan_carbon():
    out=[]
    aa='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
    codons=[a+b+c for a in 'TCAG' for b in 'TCAG' for c in 'TCAG']
    table=dict(zip(codons,aa))
    def translate(seq):return ''.join(table.get(seq[i:i+3],'?') for i in range(0,len(seq)-2,3))
    categorical=['species','source','condition','depth','context_length_bp','key_len_bp','value_len_bp',
        'label','type','region_group','region_subtype','clinical_significance_terms','coding_status',
        'script_version','annotation_source','recoding_mode','mutation_distance','num_distractors','subset']
    for dataset in ['clinvar-vep','perturbation-bench','carbon-dream','genomic-niah']:
        for path in sorted((CACHE/dataset).rglob('*.parquet')):
            p=pq.ParquetFile(path);cs={k:collections.Counter() for k in categorical if k in p.schema_arrow.names}
            lengths=collections.defaultdict(collections.Counter);checks=collections.Counter()
            for batch in p.iter_batches(batch_size=4096):
                for r in batch.to_pylist():
                    for k,c in cs.items():c[str(r[k])]+=1
                    for k in ['sequence','original_sequence','prompt','positive_sequence','negative_sequence']:
                        if isinstance(r.get(k),str):lengths[k][len(r[k])]+=1
                    if 'activity' in r:checks['nonfinite_activity']+=not math.isfinite(r['activity'])
                    if dataset=='perturbation-bench':
                        ref,alt=r['original_sequence'],r['sequence']
                        checks['same_length']+=len(ref)==len(alt)
                        checks['identical_pair']+=ref==alt
                        if 'patch_start_in_seq' in r:
                            a,b=r['patch_start_in_seq'],r['patch_end_in_seq']
                            checks['outside_patch_unchanged']+=ref[:a]==alt[:a] and ref[b:]==alt[b:]
                            checks['patch_exceeds_annotated_cds']+=a<r['cds_start_in_seq'] or b>r['cds_end_in_seq']
                        if path.parts[-2] in ['syn_human','syn_mouse']:
                            a,b=r['cds_start_in_seq'],r['cds_end_in_seq']
                            checks['same_amino_acids_in_any_frame']+=any(translate(ref[a+i:b])==translate(alt[a+i:b]) for i in range(3))
                    if dataset=='genomic-niah':
                        checks['positive_is_prompt_plus_value']+=r['positive_sequence']==r['prompt']+r['value']
                        checks['prompt_ends_in_key']+=r['prompt'].endswith(r['key'])
                        checks['key_value_present_in_context']+=(r['key']+r['value']) in r['prompt'][:-len(r['key'])]
            out.append(dict(dataset=dataset,path=str(path.relative_to(CACHE/dataset)),rows=p.metadata.num_rows,
                bytes=path.stat().st_size,sha256=digest(path),columns=p.schema_arrow.names,
                categories={k:dict(v) for k,v in cs.items()},lengths={k:dict(v) for k,v in lengths.items()},checks=dict(checks)))
            print(dataset,path.name,p.metadata.num_rows,dict(checks),flush=True)
    (ROOT/'data/carbon-artifact-inspections.json').write_text(json.dumps(out,indent=2)+'\n')


def scan_ntv3():
    path=CACHE/'ntv3-complete-media-1.xlsx'
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    sheets=[]
    for sheet in w:
        it=iter(sheet.values);header=next(it);rows=[]
        for row in it:
            if not any(v is not None for v in row):continue
            rows.append({str(k):v for k,v in zip(header,row) if k is not None})
        sheets.append(dict(name=sheet.title,rows=rows))
    metadata=list(csv.DictReader((CACHE/'ntv3-benchmark/benchmark_metadata.tsv').open(),delimiter='\t'))
    splits=[]
    for path in sorted((CACHE/'ntv3-benchmark').glob('*/splits.bed')):
        records=[];counts=collections.Counter();bp=collections.Counter();chroms=collections.defaultdict(set)
        for row in csv.reader(path.open(),delimiter='\t'):
            if not row or row[0].startswith('#'):continue
            chrom,a,b,split=row[:4]
            assert float(a).is_integer() and float(b).is_integer(), row
            a=int(float(a));b=int(float(b))
            records.append([chrom,a,b,split]);counts[split]+=1;bp[split]+=b-a;chroms[split].add(chrom)
        overlap=[]
        for chrom in {r[0] for r in records}:
            ordered=sorted((r for r in records if r[0]==chrom),key=lambda r:r[1])
            for a,b in zip(ordered,ordered[1:]):
                if a[2]>b[1]:overlap.append([a,b])
        splits.append(dict(species=path.parent.name,rows=len(records),partitions=dict(counts),bases=dict(bp),
            chromosomes={k:sorted(v) for k,v in chroms.items()},overlapping_intervals=overlap,
            sha256=digest(path),intervals=records))
    out=dict(workbook_sha256=digest(CACHE/'ntv3-complete-media-1.xlsx'),sheets=sheets,
        benchmark_metadata=metadata,benchmark_metadata_sha256=digest(CACHE/'ntv3-benchmark/benchmark_metadata.tsv'),splits=splits)
    (ROOT/'data/ntv3-artifact-inspections.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('NTv3',[(s['name'],len(s['rows'])) for s in sheets],flush=True)


if __name__=='__main__':
    scan_carbon();scan_ntv3()
