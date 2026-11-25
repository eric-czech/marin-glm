"""Inspect pinned public dataset files. Requires requests and pyarrow; never runs model code."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, StringIO
from pathlib import Path
import csv
import hashlib
import json

import pyarrow.parquet as pq
import pyarrow.compute as pc
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research' / 'artifacts'

def inspect(job):
    repo, revision, path = job
    url = f'https://huggingface.co/datasets/{repo}/resolve/{revision}/{path}'
    local = DEST / repo.replace('/', '--') / path
    try:
        local.parent.mkdir(parents=True, exist_ok=True)
        if not local.exists():
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            local.write_bytes(response.content)
        digest = hashlib.sha256()
        with local.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        raw = None
        if path.endswith('.parquet'):
            parquet = pq.ParquetFile(local)
            columns = parquet.schema_arrow.names
            row_count = parquet.metadata.num_rows
            rows = None
        else:
            raw = local.read_bytes()
            rows = list(csv.DictReader(StringIO(raw.decode('utf-8-sig'))))
            columns = list(rows[0]) if rows else []
            row_count = len(rows)
        out = {'repo': repo, 'revision': revision, 'path': path, 'url': url,
               'sha256': digest.hexdigest(), 'bytes': local.stat().st_size,
               'rows': row_count, 'columns': columns}
        for col in ('split', 'fold', 'label', 'labels', 'Label', 'target', 'organism', 'species', 'genus', 'consequence', 'chrom'):
            if col in columns:
                values = parquet.read(columns=[col]).column(col).to_pylist() if rows is None else [r[col] for r in rows]
                counts = Counter(str(value) for value in values)
                if len(counts) <= 150:
                    out.setdefault('values', {})[col] = dict(counts)
        for col in ('sequence', 'Sequence', 'seq', 'text', 'dna'):
            if col in columns:
                if rows is None:
                    first_batch = next(parquet.iter_batches(batch_size=1, columns=[col]))
                    first = first_batch.column(0)[0].as_py()
                else:
                    first = rows[0][col] if rows else None
                if not isinstance(first, str):
                    continue
                out['sequence_column'] = col
                if rows is None:
                    lower, upper = None, None
                    for batch in parquet.iter_batches(batch_size=64, columns=[col]):
                        lengths = pc.utf8_length(batch.column(0))
                        low, high = pc.min(lengths).as_py(), pc.max(lengths).as_py()
                        if low is not None:
                            lower = low if lower is None else min(low, lower)
                            upper = high if upper is None else max(high, upper)
                    out['length'] = {'min': lower, 'max': upper}
                    sample = [first]
                else:
                    sizes = [len(row[col]) for row in rows]
                    out['length'] = {'min': min(sizes), 'max': max(sizes)}
                    sample = [r[col] for r in rows[:5]]
                out['sequence_alphabet'] = ''.join(sorted(set(''.join(sample))))
                break
        if repo.endswith('bacbench-essential-genes-dna'):
            for col in ('essential',):
                if col in columns:
                    vals = parquet.read(columns=[col]).column(col)
                    # Each row is a genome; its labels are nested contig → gene.
                    out['gene_count'] = pc.sum(pc.list_value_length(pc.list_flatten(vals))).as_py()
        return out
    except Exception as exc:
        return {'repo': repo, 'revision': revision, 'path': path, 'url': url, 'error': str(exc)}

def jobs():
    hf = ROOT / 'research' / 'sources' / 'huggingface'
    selected = {
        'Nugkta/bgc-bench': lambda p: p.startswith('splits/') or p in ('tasks/t2ml_labels.csv', 'tasks/chem_descriptors.csv', 'tasks/adomain_instances.csv', 'provenance/mibig_metadata.csv'),
        'InstaDeepAI/nucleotide_transformer_downstream_tasks_revised': lambda p: p.endswith('.parquet'),
        'GenerTeam/gener-tasks': lambda p: p.endswith('.parquet'),
        'GenerTeam/DeepSTARR-enhancer-activity': lambda p: p.endswith('.parquet'),
        'biomap-research/DeepD': lambda p: p.startswith('fine_tune/H3/') and p.endswith('.csv'),
        'songlab/TraitGym': lambda p: p in ('mendelian_traits_matched_9/test.parquet', 'complex_traits_matched_9/test.parquet'),
        'tattabio/ec_classification_dna': lambda p: p.endswith('.parquet'),
        'macwiatrak/bacbench-essential-genes-dna': lambda p: p.endswith('.parquet'),
    }
    for repo, select in selected.items():
        data = json.loads((hf / repo.replace('/', '--') / 'api.json').read_text())
        for file in data['siblings']:
            if select(file['rfilename']):
                yield repo, data['sha'], file['rfilename']

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(inspect, jobs()))
    (ROOT / 'data' / 'artifact-inspections.json').write_text(json.dumps(rows, indent=2) + '\n')
    for row in rows:
        print(json.dumps({k: row[k] for k in ('repo', 'path', 'rows', 'gene_count', 'error') if k in row}))
