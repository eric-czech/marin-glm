"""Rebuild the SQLite catalogue and self-contained GitHub Pages document, offline."""
from pathlib import Path
import json
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
INSERT_ORDER=['metadata','sources','papers','evidence','models','model_properties','populations','categories','metrics',
              'evaluations','tasks','variants','evaluation_tasks','task_populations','task_categories',
              'protocols','protocol_metrics','counts','model_evaluations','findings','field_evidence']

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
    db.execute('VACUUM')
    db.close()
    temporary.replace(ROOT/'data/catalogue.sqlite')
    compact=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    template=(ROOT/'site/template.html').read_text()
    html=template.replace('/*__STYLE__*/',(ROOT/'site/style.css').read_text()).replace('/*__SCRIPT__*/',(ROOT/'site/app.js').read_text()).replace('__CATALOGUE_JSON__',compact)
    (ROOT/'index.html').write_text(html)
    (ROOT/'data/site-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(payload["tasks"])} task records, {len(payload["evaluations"])} collections, {len(payload["evidence"])} evidence records.')
    print('data/catalogue.sqlite → index.html (self-contained; no network dependency)')

if __name__=='__main__':build()
