"""Explicit, evidence-linked authoring operations for completed source reviews.

The committed catalogue is the source of truth. Research helpers edit that
document deliberately; routine builds never execute historical import scripts.
"""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DATE = '2026-11-27'


class Catalogue:
    def __init__(self, data):
        self.data = data

    def get(self, table, id):
        return next(r for r in self.data[table] if r.get('id') == id)

    def put(self, table, row, keys=('id',)):
        rows = self.data.setdefault(table, [])
        old = next((r for r in rows if all(r[k] == row[k] for k in keys)), None)
        if old is None:
            rows.append(row)
        else:
            old.update(row)
        return row.get('id')

    def source(self, id, title, url, kind='paper', version=None, path=None, notes=None):
        file = ROOT / path if path else None
        return self.put('sources', dict(id=id, title=title, url=url, kind=kind,
            version=version, local_path=path, retrieved=DATE, availability='available',
            sha256=hashlib.sha256(file.read_bytes()).hexdigest() if file and file.is_file() else None,
            notes=notes))

    def evidence(self, id, source, locator, statement, basis='paper', url=None):
        return self.put('evidence', dict(id=id, source_id=source, locator=locator,
            statement=statement, basis=basis, url=url or self.get('sources', source)['url'], inspected=DATE))

    def field(self, table, id, field, evidence, note=None):
        self.put('field_evidence', dict(entity_table=table, entity_id=id, field=field,
            evidence_id=evidence, note=note), ('entity_table', 'entity_id', 'field', 'evidence_id'))

    def category(self, task, category, evidence, rationale, relation='target'):
        self.put('task_categories', dict(task_id=task, category_id=category,
            evidence_id=evidence, rationale=rationale, relation=relation,
            attribution='curatorial'), ('task_id', 'category_id', 'relation'))

    def output(self, task, form, evidence, prediction, unit, axis='none', structure='none',
               status='supported', rationale=None, limitations=''):
        self.put('task_outputs', dict(id=task+'-output-review', task_id=task,
            category_id='output-'+form, evidence_id=evidence, prediction_form=prediction,
            scoring_unit=unit, position_axis=axis, structure_scope=structure, status=status,
            rationale=rationale or 'The source defines the assessed output and scoring unit explicitly.',
            limitations=limitations))
        self.data['task_categories'] = [r for r in self.data['task_categories']
            if not (r['task_id']==task and self.get('categories', r['category_id'])['dimension']=='output')]
        self.category(task, 'output-'+form, evidence, rationale or 'Source-defined assessed output.', 'measured')

    def population(self, task, population, evidence, note, variant=None):
        self.put('task_populations', dict(task_id=task, population_id=population,
            evidence_id=evidence, relation='sequence-origin', variant_id=variant, coverage=note),
            ('task_id', 'population_id', 'relation'))
        # Use an existing display assignment for this population. This copies
        # presentation coordinates, never the other task's scientific evidence.
        template = next((r for r in self.data['coverage_mappings'] if r['population_id']==population), None)
        if template is None:
            raise ValueError('Explicit coverage layout needed for '+population)
        m=copy.deepcopy(template)
        m.update(id=task+'-mapping-'+population, task_id=task, population_id=population,
            evidence_id=evidence, supporting_json=json.dumps([evidence]), basis='source-defined population')
        meta=json.loads(m['metadata_json'])
        meta.update(basis='source-defined population',url=self.get('evidence',evidence)['url'])
        m['metadata_json']=json.dumps(meta,ensure_ascii=False)
        self.put('coverage_mappings',m)

    def unknown_origin(self, task, evidence, note):
        template=next(r for r in self.data['coverage_mappings'] if r['species_row']=='species:unknown')
        m=copy.deepcopy(template)
        m.update(id=task+'-mapping-unknown',task_id=task,population_id=None,
            evidence_id=evidence,supporting_json=json.dumps([evidence]),basis='metadata gap')
        meta=json.loads(m['metadata_json'])
        meta.update(basis='metadata gap',url=self.get('evidence',evidence)['url'],note=note)
        m['metadata_json']=json.dumps(meta,ensure_ascii=False)
        self.put('coverage_mappings',m)

    def protocol(self, id, task, name, adaptation, interface, split, unit, evidence,
                 metrics=(), embeddings=False, fitted=None, selection=None, notes=None, variant=None):
        self.put('protocols', dict(id=id, task_id=task, name=name, adaptation=adaptation,
            model_interface=interface, split_rule=split, split_unit=unit, source_evidence_id=evidence,
            requires_embeddings=embeddings, fitted_component=fitted, selection=selection,
            notes=notes, variant_id=variant))
        for metric,aggregation in metrics:
            self.put('protocol_metrics',dict(protocol_id=id,metric_id=metric,evidence_id=evidence,
                aggregation=aggregation,is_primary=True),('protocol_id','metric_id'))
        return id

    def count(self, task, n, unit, evidence, split='evaluation', protocol=None, variant=None,
              qualifier='', method='reported'):
        key='-'.join(str(v).replace(' ','-') for v in [task,protocol or variant or 'source',split,n,unit])
        self.put('counts',dict(id=key,task_id=task,value=n,unit=unit,evidence_id=evidence,
            split=split,protocol_id=protocol,variant_id=variant,qualifier=qualifier,method=method))

    def use(self, task, model, paper, evidence, protocol=None, provenance='original-paper', note=''):
        self.put('model_evaluations',dict(id='-'.join([paper,model,task,protocol or 'paper']),
            task_id=task,model_id=model,paper_id=paper,evidence_id=evidence,protocol_id=protocol,
            provenance=provenance,note=note))

    def member(self, task, evaluation, evidence, variant=None, note=None):
        self.put('evaluation_tasks',dict(task_id=task,evaluation_id=evaluation,
            evidence_id=evidence,variant_id=variant,note=note),('task_id','evaluation_id'))

    def review(self, table, id, scope, evidence, limitations=''):
        self.put('source_reviews',dict(id=table+'-'+id+'-review',entity_table=table,
            entity_id=id,reviewed=DATE,scope=scope,evidence_ids_json=json.dumps(sorted(set(evidence))),
            limitations=limitations),('entity_table','entity_id'))

    def limit(self, table, id, field, reason, detail, evidence):
        self.put('source_limits',dict(id='-'.join([table,id,field,reason]),entity_table=table,
            entity_id=id,field=field,reason=reason,detail=detail,evidence_id=evidence))

    def resource(self, id, source, title, kind, host, url, evidence, revision=None,
                 availability='public', notes=''):
        self.put('data_resources',dict(id=id,source_id=source,title=title,kind=kind,host=host,
            url=url,revision=revision,availability=availability,evidence_id=evidence,notes=notes))
        return id

    def task_resource(self, task, resource, evidence, relation='evaluation-data', variant=None, note=''):
        self.put('task_resources',dict(task_id=task,resource_id=resource,evidence_id=evidence,
            relation=relation,variant_id=variant,note=note),('task_id','resource_id','relation'))

    def collection_resource(self, collection, resource, evidence, relation='evaluation-data', note=''):
        self.put('evaluation_resources',dict(evaluation_id=collection,resource_id=resource,
            evidence_id=evidence,relation=relation,note=note),('evaluation_id','resource_id','relation'))
