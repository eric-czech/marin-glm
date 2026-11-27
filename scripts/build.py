"""Rebuild the SQLite catalogue and self-contained GitHub Pages document, offline."""
from pathlib import Path
import json
import sqlite3
from coverage_data import export_coverage

ROOT=Path(__file__).resolve().parents[1]
INSERT_ORDER=['metadata','sources','papers','evidence','models','model_properties','populations','categories','metrics',
              'evaluations','tasks','task_outputs','task_feature_scopes','variants','assay_tracks','task_tracks','evaluation_tasks','task_populations','task_categories',
              'protocols','protocol_field_reviews','protocol_metrics','counts','model_evaluations','model_collection_evaluations','findings',
              'source_reviews','source_limits','data_resources','task_resources','evaluation_resources','task_redirects',
              'project_reviews','projects','project_review_papers','project_review_evaluations','project_adoptions','field_evidence',
              'coverage_nodes','coverage_rows','coverage_mappings','coverage_notes','coverage_settings',
              'split_strategies','split_protocol_strategies','split_audits','split_audit_tasks',
              'split_partitions','split_comparisons','split_audit_files','split_examples']

def load_catalogue(data, db):
    """Insert and validate an authoring document in a supplied SQLite connection."""
    db.row_factory=sqlite3.Row
    db.executescript((ROOT/'data/schema.sql').read_text())
    with db:
        for table in INSERT_ORDER:
            for row in data.get(table,[]):
                columns=list(row)
                db.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',[row[k] for k in columns])
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    # A publication can omit data; the catalogue cannot omit its review. Source
    # limits are explicit records, never a queue of unfinished catalogue tasks.
    for table in ['tasks','evaluations','models','papers','protocols']:
        bad=db.execute(f'''SELECT a.id FROM {table} a LEFT JOIN source_reviews r
          ON r.entity_table=? AND r.entity_id=a.id WHERE r.id IS NULL''',(table,)).fetchall()
        if bad:raise ValueError(f'{table}: completed source review missing: {[r[0] for r in bad]}')
    bad=db.execute("SELECT id FROM tasks WHERE status NOT IN ('artifact-audited','paper-audited','source-limited')").fetchall()
    if bad:raise ValueError(f'Unfinished task status: {[r[0] for r in bad]}')
    for field in ('requires_embeddings','fitted_component','selection'):
        bad=db.execute(f'''SELECT p.id FROM protocols p LEFT JOIN protocol_field_reviews r
          ON r.protocol_id=p.id AND r.field=? WHERE p.{field} IS NULL AND r.protocol_id IS NULL''',(field,)).fetchall()
        if bad:raise ValueError(f'Protocol field interpretation missing ({field}): {[r[0] for r in bad]}')
    bad=db.execute("SELECT id FROM model_properties WHERE status IN ('unresolved','pending','incomplete')").fetchall()
    if bad:raise ValueError(f'Unfinished model property: {[r[0] for r in bad]}')
    bad=db.execute("SELECT id FROM source_limits WHERE reason='not-retrieved'").fetchall()
    if bad:raise ValueError(f'Unfinished source retrieval: {[r[0] for r in bad]}')
    bad=db.execute("SELECT id FROM data_resources WHERE availability='not-retrieved'").fetchall()
    if bad:raise ValueError(f'Unreviewed data resource availability: {[r[0] for r in bad]}')
    bad=db.execute("SELECT id FROM tasks WHERE output_description='Target prediction'").fetchall()
    if bad:raise ValueError(f'Placeholder task output: {[r[0] for r in bad]}')
    bad=db.execute('''SELECT t.id FROM tasks t LEFT JOIN source_limits l
      ON l.entity_table='tasks' AND l.entity_id=t.id
      WHERE t.status='source-limited' GROUP BY t.id HAVING COUNT(l.id)=0''').fetchall()
    if bad:raise ValueError(f'Source-limited task without specific limits: {[r[0] for r in bad]}')
    bad=db.execute('''SELECT e.id FROM evaluations e LEFT JOIN evaluation_tasks t
      ON t.evaluation_id=e.id GROUP BY e.id HAVING COUNT(t.task_id)=0''').fetchall()
    if bad:raise ValueError(f'Collection without decomposed tasks: {[r[0] for r in bad]}')
    bad=db.execute("SELECT c.id FROM counts c JOIN evidence e ON e.id=c.evidence_id WHERE c.method='measured' AND e.basis!='data'").fetchall()
    if bad:raise ValueError(f'Measured count without data inspection: {[r[0] for r in bad]}')
    if db.execute("SELECT 1 FROM coverage_notes WHERE kind='known'").fetchone():
        raise ValueError('Reported evaluation claim still lacks a mapped task')
    bad=db.execute('''SELECT t.id FROM tasks t LEFT JOIN task_outputs o ON o.task_id=t.id
      WHERE o.id IS NULL''').fetchall()
    if bad:raise ValueError(f'Task output review missing: {bad}')
    bad=db.execute('''SELECT o.id FROM task_outputs o JOIN categories c ON c.id=o.category_id
      WHERE c.dimension!='output' ''').fetchall()
    if bad:raise ValueError(f'Wrong output category dimension: {bad}')
    bad=db.execute('''SELECT o.task_id FROM task_outputs o LEFT JOIN task_categories tc
      ON tc.task_id=o.task_id AND tc.category_id=o.category_id
      WHERE tc.task_id IS NULL
      UNION SELECT tc.task_id FROM task_categories tc JOIN categories c ON c.id=tc.category_id
      JOIN task_outputs o ON o.task_id=tc.task_id WHERE c.dimension='output' AND tc.category_id!=o.category_id''').fetchall()
    if bad:raise ValueError(f'Inconsistent output classification: {bad}')
    bad=db.execute('''SELECT tc.task_id FROM task_categories tc LEFT JOIN task_feature_scopes s
      ON s.task_id=tc.task_id AND s.feature_id='cds'
      WHERE tc.category_id='cds' AND s.id IS NULL''').fetchall()
    if bad:raise ValueError(f'CDS scope review missing: {bad}')
    for table in ('populations','coverage_nodes'):
        parents=dict(db.execute('SELECT id,parent_id FROM '+table))
        for key in parents:
            seen=set();current=key
            while current:
                if current in seen:raise ValueError(f'{table} ancestry cycle: {key}')
                seen.add(current);current=parents[current]
    # Project status requires dedicated purpose and two independent user groups.
    bad=db.execute("""SELECT p.id FROM project_summary p JOIN project_reviews r ON r.id=p.review_id
      WHERE r.decision!='qualified' OR r.dedicated!=1 OR p.independent_groups<2""").fetchall()
    if bad:raise ValueError(f'Project inclusion rule not met: {bad}')
    bad=db.execute("""SELECT r.id FROM project_reviews r LEFT JOIN projects p ON p.review_id=r.id
      WHERE r.decision='qualified' AND p.id IS NULL""").fetchall()
    if bad:raise ValueError(f'Qualified review missing project: {bad}')
    # A variant/protocol count cannot silently belong to a different task.
    for table,column in [('counts','protocol_id'),('counts','variant_id'),('protocols','variant_id'),('model_evaluations','protocol_id'),('task_resources','variant_id'),('task_tracks','variant_id')]:
        target='protocols' if column=='protocol_id' else 'variants'
        bad=db.execute(f'SELECT a.task_id FROM {table} a JOIN {target} b ON a.{column}=b.id WHERE a.task_id!=b.task_id').fetchall()
        if bad:raise ValueError(f'{table}.{column} task mismatch: {bad}')
    bad=db.execute('''SELECT r.id FROM task_redirects r JOIN tasks t ON t.id=r.id''').fetchall()
    if bad:raise ValueError(f'Redirect shadows a current task: {[r[0] for r in bad]}')
    for table in ['split_comparisons','split_audit_files']:
        cols=['left_partition_id','right_partition_id'] if table=='split_comparisons' else ['partition_id']
        for col in cols:
            bad=db.execute(f'SELECT a.id FROM {table} a JOIN split_partitions p ON a.{col}=p.id WHERE a.audit_id!=p.audit_id').fetchall()
            if bad:raise ValueError('Cross-audit partition reference: '+table+'.'+col)
    bad=db.execute('''SELECT c.id FROM split_comparisons c
      JOIN split_audits a ON a.id=c.audit_id JOIN evidence e ON e.id=c.evidence_id
      JOIN split_partitions l ON l.id=c.left_partition_id JOIN split_partitions r ON r.id=c.right_partition_id
      WHERE e.basis!='data' OR a.status NOT IN ('measured','metadata-only')
        OR l.id=r.id OR c.left_affected>l.row_count OR c.right_affected>r.row_count
        OR (c.overlap_type='exact-sequence' AND (c.shared_count>l.unique_sequences OR c.shared_count>r.unique_sequences))''').fetchall()
    if bad:raise ValueError('Invalid measured split comparison or denominator: '+str([r[0] for r in bad]))
    bad=db.execute('''SELECT a.id FROM split_audits a LEFT JOIN split_audit_tasks l ON l.audit_id=a.id
      WHERE l.id IS NULL''').fetchall()
    if bad:raise ValueError('Split inspection without linked task: '+str([r[0] for r in bad]))
    bad=db.execute('''SELECT x.id FROM split_examples x JOIN split_comparisons c ON c.id=x.comparison_id
      WHERE c.shared_count=0''').fetchall()
    if bad:raise ValueError('Overlap example attached to a zero comparison: '+str([r[0] for r in bad]))
    for column,target in [('protocol_id','protocols'),('variant_id','variants')]:
        bad=db.execute(f'SELECT a.id FROM split_audit_tasks a JOIN {target} p ON a.{column}=p.id WHERE a.task_id!=p.task_id').fetchall()
        if bad:raise ValueError('Split audit task ownership mismatch: '+column)
    for row in db.execute('SELECT * FROM field_evidence'):
        if row['entity_table'] not in INSERT_ORDER:raise ValueError('Unknown evidence table')
        if not db.execute(f'SELECT 1 FROM {row["entity_table"]} WHERE id=?',(row['entity_id'],)).fetchone():raise ValueError('Missing field evidence entity: '+row['entity_id'])
    for table in ['source_reviews','source_limits']:
        for row in db.execute('SELECT * FROM '+table):
            if not db.execute(f'SELECT 1 FROM {row["entity_table"]} WHERE id=?',(row['entity_id'],)).fetchone():
                raise ValueError('Missing review entity: '+row['entity_id'])
            if table=='source_reviews':
                evidence_ids=json.loads(row['evidence_ids_json'])
                if not evidence_ids:raise ValueError('Review without evidence: '+row['id'])
                for eid in evidence_ids:
                    if not db.execute('SELECT 1 FROM evidence WHERE id=?',(eid,)).fetchone():raise ValueError('Unknown review evidence: '+eid)


def build():
    data=json.loads((ROOT/'data/catalogue.json').read_text())
    temporary=ROOT/'data/catalogue.sqlite.tmp'
    temporary.unlink(missing_ok=True)
    db=sqlite3.connect(temporary)
    load_catalogue(data,db)
    # The web payload is queried from SQLite, not independently maintained content.
    payload={table:[dict(r) for r in db.execute('SELECT * FROM '+table)] for table in INSERT_ORDER}
    payload['evaluation_summary']=[dict(r) for r in db.execute('SELECT * FROM evaluation_summary')]
    payload['project_summary']=[dict(r) for r in db.execute('SELECT * FROM project_summary')]
    payload['task_track_counts']=[dict(r) for r in db.execute('SELECT task_id, COUNT(*) AS tracks FROM task_tracks GROUP BY task_id')]
    # The downloadable SQLite/authoring JSON retain individual track contexts.
    # Do not embed thousands of unused track rows in every browser session.
    payload.pop('assay_tracks')
    payload.pop('task_tracks')
    payload['coverage']=export_coverage(payload)
    # Layout and mapping tables are normalized in SQLite/catalogue.json. The
    # page receives only their compiled form, without embedding both copies.
    for table in INSERT_ORDER:
        if table.startswith('coverage_'):payload.pop(table)
    db.execute('VACUUM')
    db.close()
    temporary.replace(ROOT/'data/catalogue.sqlite')
    compact=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    template=(ROOT/'site/template.html').read_text()
    script='\n'.join((ROOT/path).read_text() for path in ['site/coverage.js','site/splits.js','site/app.js'])
    html=template.replace('/*__STYLE__*/',(ROOT/'site/style.css').read_text()).replace('/*__SCRIPT__*/',script).replace('__CATALOGUE_JSON__',compact)
    (ROOT/'index.html').write_text(html)
    (ROOT/'data/site-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(payload["tasks"])} task records, {len(payload["evaluations"])} collections, {len(payload["evidence"])} evidence records.')
    print('data/catalogue.sqlite → index.html (self-contained; no network dependency)')

if __name__=='__main__':build()
