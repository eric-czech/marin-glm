"""Reproduce the NABench target adjudication from two explicitly supplied files.

Inputs are the pinned Gregory_2018_mRNA.csv and Findlay Supplementary Table1.
No network access or data downloads occur. Requires numpy and openpyxl.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import openpyxl

NABENCH_URL='https://github.com/mrzzmrzz/NABench/blob/99c8681ec1eab706e10ff90a5c329dcf184cc1d1/data/Gregory_2018_mRNA.csv'
SOURCE_URL='https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-018-0461-z/MediaObjects/41586_2018_461_MOESM3_ESM.xlsx'


def inspect(nabench_csv, source_table):
    nab=list(csv.DictReader(nabench_csv.open()))
    workbook=openpyxl.load_workbook(source_table,read_only=True,data_only=True)
    rows=list(workbook['Sheet1'].values)
    workbook.close()
    columns=rows[2]
    records=rows[3:]
    assert len(nab)==287 and len(records)==3893
    scores=np.array([float(r['DMS_score']) for r in nab])
    comparisons=[]
    for i,name in enumerate(columns):
        values=np.array([float(r[i]) for r in records if isinstance(r[i],(int,float))])
        if not len(values):continue
        matches=int((np.abs(scores[:,None]-values[None,:]).min(axis=1)<1e-12).sum())
        comparisons.append(dict(column=name,numeric_values=len(values),matching_nabench_rows=matches))
    assert [r['column'] for r in comparisons if r['matching_nabench_rows']==len(nab)]==['d11/lib.loess.r1']
    target=columns.index('d11/lib.loess.r1')
    deltas=np.abs(scores[:,None]-np.array([r[target] for r in records])[None,:])
    pairs=[];offsets=set();consequences=collections.Counter()
    for i,row in enumerate(nab):
        matches=np.where(deltas[i]<1e-12)[0]
        assert len(matches)==1,(i,matches)
        j=int(matches[0]);original=records[j]
        mutation=re.fullmatch(r'([ACGT])(\d+)([ACGT])',row['mutant'])
        assert mutation and mutation[1]==original[7] and mutation[3]==original[8]
        offsets.add(int(mutation[2])+int(original[2]))
        consequences[original[14]]+=1
        pairs.append(dict(nabench_csv_line=i+2,mutant=row['mutant'],score=float(row['DMS_score']),
            source_xlsx_row=j+4,position_hg19=original[2],transcript_variant=original[9],
            source_score=original[target],source_experiment=original[18],
            source_replicate1_function_score=original[39],mean_rna_score=original[47],
            source_transcript_ref=original[7],source_transcript_alt=original[8],consequence=original[14]))
    assert len(offsets)==1 and {p['source_experiment'] for p in pairs}=={'X20'}
    return dict(inspected='2026-11-27',source_url=SOURCE_URL,
        source_sha256=hashlib.sha256(source_table.read_bytes()).hexdigest(),
        nabench_url=NABENCH_URL,nabench_sha256=hashlib.sha256(nabench_csv.read_bytes()).hexdigest(),
        method='Compare every released DMS_score with every numerical source-table column; require one column with287 unique matches at tolerance1e-12, matching transcript-strand alleles and a consistent genomic-position/mutant-index offset.',
        matched_rows=len(pairs),source_rows=len(records),source_column='d11/lib.loess.r1',source_excel_column='AI',
        max_absolute_error=float(deltas.min(axis=1).max()),pairs=pairs,numerical_column_comparisons=comparisons,
        transcript_strand_allele_matches=len(pairs),genomic_position_plus_mutant_index=next(iter(offsets)),
        consequences=dict(consequences),
        interpretation='The released scalar is a day-11/library LOESS-adjusted replicate-1 genomic-DNA selection score from experimentX20, not the mean RNA score or final mean function score. All287 score matches also share one genomic coordinate offset and match transcript-strand reference/alternate alleles.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--nabench-csv',required=True,type=Path)
    p.add_argument('--source-table',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    result=inspect(args.nabench_csv,args.source_table)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'{result["matched_rows"]} unique score/allele/coordinate matches; source column {result["source_column"]}.')
