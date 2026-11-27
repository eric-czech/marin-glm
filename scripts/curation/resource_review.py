"""Expose previously audited public data files as explicit linked resources.

Only evidence already attached to a task/variant/protocol/count is used. A
collection's unrelated files are never attached to all of its tasks.
"""
import collections
import hashlib
from urllib.parse import urlparse
from common import Catalogue


def populate(d):
    c=Catalogue(d);bytask=collections.defaultdict(set)
    # Our inspection reports are citations about artifacts, not extra benchmark
    # input datasets. Remove previously derived links to those local reports.
    own={r['id'] for r in d['data_resources'] if r['id'].startswith('audited-file-') and 'github.com/eric-czech/marin-glm/' in r['url']}
    for table in ['task_resources','evaluation_resources']:
        d[table]=[r for r in d[table] if r['resource_id'] not in own]
    d['data_resources']=[r for r in d['data_resources'] if r['id'] not in own]
    for t in d['tasks']:bytask[t['id']].add(t['evidence_id'])
    for table,field in [('variants','evidence_id'),('counts','evidence_id'),('task_categories','evidence_id'),
            ('task_populations','evidence_id'),('task_outputs','evidence_id'),('protocols','source_evidence_id')]:
        for r in d[table]:bytask[r['task_id']].add(r[field])
    for r in d['field_evidence']:
        if r['entity_table']=='tasks':bytask[r['entity_id']].add(r['evidence_id'])
    evidences={r['id']:r for r in d['evidence']};sources={r['id']:r for r in d['sources']}
    for tid,ids in bytask.items():
        for eid in sorted(ids):
            ev=evidences[eid];s=sources[ev['source_id']];url=ev['url'].split('#')[0]
            if 'github.com/eric-czech/marin-glm/' in url:continue
            data_path=urlparse(url).path.lower()
            explicit_data=ev['basis']=='data' and data_path.endswith(('.json','.csv','.tsv','.bed','.fasta','.fa','.fna','.gz','.h5','.hdf5','.parquet','.npz','.xlsx','.yaml'))
            if s['kind']!='dataset-file' and not explicit_data:continue
            existing=[r for r in d['task_resources'] if r['task_id']==tid and c.get('data_resources',r['resource_id'])['url'].split('#')[0]==url]
            if any(not r['resource_id'].startswith('audited-file-') for r in existing):continue
            path=urlparse(url).path.lower()
            # Existing snapshot records explicitly identify these as data files.
            # Their content evidence decides whether they are examples or outputs.
            if any(v in path for v in ['metrics','scores','benchmark_results','results.tsv','results.csv']):
                kind,relation='results','results'
            elif any(v in path for v in ['metadata','manifest','reference_files/','reference_sheet','files.tsv','species.yaml','split.csv','splits.csv','splits.tsv']):
                kind,relation='manifest','split-manifest' if 'split' in path else 'identity-manifest'
            else:kind,relation='dataset','evaluation-data'
            host='huggingface' if urlparse(url).hostname=='huggingface.co' else 'github' if urlparse(url).hostname in ['github.com','raw.githubusercontent.com'] else 'zenodo' if urlparse(url).hostname=='zenodo.org' else 'other'
            rid='audited-file-'+hashlib.sha256(url.encode()).hexdigest()[:16]
            for table in ['task_resources','evaluation_resources']:
                d[table]=[r for r in d[table] if r['resource_id']!=rid or r['relation']==relation]
            c.resource(rid,s['id'],s['title'],kind,host,url,eid,revision=s.get('version'),
                availability='public' if s['availability']=='available' else 'not-retrieved',
                notes='The linked task evidence states the inspected columns, units and filtering. This file is not asserted to define every protocol variant.')
            c.task_resource(tid,rid,eid,relation)
            for member in [r for r in d['evaluation_tasks'] if r['task_id']==tid]:
                # A shared task's release file is discoverable at collection level,
                # with its scope still attached to the source task.
                c.collection_resource(member['evaluation_id'],rid,eid,relation,note='Linked constituent task: '+tid)
    return d
