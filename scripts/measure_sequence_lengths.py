"""Interpret the selected GENEB overlap without a new download or alignment.

Read the same complete bounded pair (130,970 rows) and preserve length strata
and label-set differences. Shared unique strings are not affected rows.
"""
from pathlib import Path
import collections
import csv
import json
ROOT=Path(__file__).resolve().parents[1]
config='katarinagresova_Genomic_Benchmarks_human_enhancers_ensembl'
root=ROOT/'research/artifacts/audit-followup/geneb/tasks'/config
maps={};row_counts={}
for split in ['train','test']:
    labels=collections.defaultdict(set);rows=collections.Counter()
    with (root/(split+'.csv')).open() as f:
        for r in csv.DictReader(f):labels[r['text']].add(r['label']);rows[r['text']]+=1
    maps[split]=labels;row_counts[split]=rows
shared=maps['train'].keys()&maps['test'].keys()
assert len(shared)==9502
bucket=lambda n:'1–9' if n<10 else '10–49' if n<50 else '50–199' if n<200 else '200+'
strata={}
for b in ['1–9','10–49','50–199','200+']:
    strata[b]={'shared_unique_strings':sum(bucket(len(s))==b for s in shared),
        'held_out_unique_strings':sum(bucket(len(s))==b for s in maps['test'])}
audit=dict(method='Complete same pinned train/test CSVs, exact case-sensitive strings, lengths and label sets; no alignment or score-bias experiment.',
    length_unit='nucleotides',strata=strata,shared_string_length_min=min(map(len,shared)),shared_string_length_max=max(map(len,shared)),
    shared_strings_with_different_label_sets=sum(maps['train'][s]!=maps['test'][s] for s in shared),
    shared_strings_with_single_conflicting_labels=sum(len(maps['train'][s])==len(maps['test'][s])==1 and maps['train'][s]!=maps['test'][s] for s in shared),
    train_rows_with_shared_string=sum(row_counts['train'][s] for s in shared),
    test_rows_with_shared_string=sum(row_counts['test'][s] for s in shared))
p=ROOT/'data/split-inspections.json';d=json.loads(p.read_text());d['cases']['selected-'+config]['sequence_length_audit']=audit
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(audit,indent=2))
