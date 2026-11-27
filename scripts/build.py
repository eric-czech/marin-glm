"""Rebuild the SQLite catalogue and self-contained GitHub Pages document, offline."""
from pathlib import Path
import json
import sqlite3
from coverage_data import export_coverage

ROOT=Path(__file__).resolve().parents[1]
INSERT_ORDER=['metadata','sources','papers','evidence','models','model_properties','populations','categories','metrics',
              'evaluations','tasks','task_outputs','task_feature_scopes','variants','evaluation_tasks','task_populations','task_categories',
              'protocols','protocol_metrics','counts','model_evaluations','findings',
              'project_reviews','projects','project_review_papers','project_review_evaluations','project_adoptions','field_evidence',
              'coverage_nodes','coverage_rows','coverage_mappings','coverage_notes','coverage_settings']

def build():
    data=json.loads((ROOT/'data/catalogue.json').read_text())
    temporary=ROOT/'data/catalogue.sqlite.tmp'
    temporary.unlink(missing_ok=True)
    db=sqlite3.connect(temporary)
    db.row_factory=sqlite3.Row
    db.executescript((ROOT/'data/schema.sql').read_text())
    with db:
        for table in INSERT_ORDER:
            for row in data[table]:
                columns=list(row)
                db.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',[row[k] for k in columns])
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
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
    for table,column in [('counts','protocol_id'),('counts','variant_id'),('protocols','variant_id'),('model_evaluations','protocol_id')]:
        target='protocols' if column=='protocol_id' else 'variants'
        bad=db.execute(f'SELECT a.id FROM {table} a JOIN {target} b ON a.{column}=b.id WHERE a.task_id!=b.task_id').fetchall()
        if bad:raise ValueError(f'{table}.{column} task mismatch: {bad}')
    for row in db.execute('SELECT * FROM field_evidence'):
        if row['entity_table'] not in INSERT_ORDER:raise ValueError('Unknown evidence table')
        if not db.execute(f'SELECT 1 FROM {row["entity_table"]} WHERE id=?',(row['entity_id'],)).fetchone():raise ValueError('Missing field evidence entity: '+row['entity_id'])
    # The web payload is queried from SQLite, not independently maintained content.
    payload={table:[dict(r) for r in db.execute('SELECT * FROM '+table)] for table in INSERT_ORDER}
    payload['evaluation_summary']=[dict(r) for r in db.execute('SELECT * FROM evaluation_summary')]
    payload['project_summary']=[dict(r) for r in db.execute('SELECT * FROM project_summary')]
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
    script=(ROOT/'site/coverage.js').read_text()+'\n'+(ROOT/'site/app.js').read_text()
    html=template.replace('/*__STYLE__*/',(ROOT/'site/style.css').read_text()).replace('/*__SCRIPT__*/',script).replace('__CATALOGUE_JSON__',compact)
    (ROOT/'index.html').write_text(html)
    (ROOT/'data/site-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(payload["tasks"])} task records, {len(payload["evaluations"])} collections, {len(payload["evidence"])} evidence records.')
    print('data/catalogue.sqlite → index.html (self-contained; no network dependency)')

if __name__=='__main__':build()
