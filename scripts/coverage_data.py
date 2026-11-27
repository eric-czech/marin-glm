"""Derive the coverage display from the same SQLite export as the task table."""
import collections
import json


def export_coverage(db):
    settings={r['key']:json.loads(r['value_json']) for r in db['coverage_settings']}
    nodes=[dict(id=n['id'],parent=n['parent_id'],population=n['population_id'],label=n['label'],
                scientific=n['scientific'],rank=n['rank'],note=n['note'],section=n['section'],
                jump=n['jump'],sources=json.loads(n['sources_json'])) for n in db['coverage_nodes']]
    lookup={n['id']:n for n in nodes}
    rows={}
    for r in db['coverage_rows']:
        value=json.loads(r['metadata_json'])
        value['populations']=json.loads(r['population_ids_json'])
        rows[r['id']]=value
    taskmaps=collections.defaultdict(list)
    evidence_ids={e['id'] for e in db['evidence']}
    for m in db['coverage_mappings']:
        value=json.loads(m['metadata_json'])
        value.update(population=m['population_id'],evidence=m['evidence_id'],
                     supporting=json.loads(m['supporting_json']),
                     clade=rows[m['clade_row']]['id'],row=rows[m['species_row']]['id'],
                     allSpeciesRow=rows[m['all_species_row']]['id'])
        if not set(value['supporting'])<=evidence_ids:raise ValueError('Unknown mapping evidence: '+m['id'])
        for field,view in [('clade_row','clade'),('species_row','species'),('all_species_row','allSpecies')]:
            if not m[field].startswith(view+':'):raise ValueError('Coverage view mismatch: '+m['id'])
        taskmaps[m['task_id']].append(value)
    cats=collections.defaultdict(set)
    for c in db['task_categories']:cats[c['task_id']].add(c['category_id'])
    memberships=collections.defaultdict(set)
    for m in db['evaluation_tasks']:memberships[m['task_id']].add(m['evaluation_id'])
    original={u['task_id'] for u in db['model_evaluations'] if u['model_id']=='evo2' and u['provenance']=='original-paper'}
    tasks=[]
    for t in db['tasks']:
        maps=taskmaps[t['id']]
        if not maps:raise ValueError('Coverage mapping missing: '+t['id'])
        typ=t['task_type'].lower();cs=cats[t['id']];sids=memberships[t['id']]
        mode=3 if any(x in typ for x in ('diagnostic','analysis','case study','computational','ortholog completeness')) else 1 if 'generation' in cs else 2 if any(x in typ for x in ('retrieval','clustering','bigene','eds')) else 0
        source=0 if t['id'] in original else 1 if sids&{'plantcad2-zero','plantcad2-ft','genecad'} else 2 if sids&{'nt-original','nt-revised','gue','gb','geneb'} else 3 if sids&{'rnagym','proteingym'} else 4 if sids&{'bacbench','dgeb','bgc','bgcs'} else 5
        features=[f['id'] for f in settings['features'] if f['id'] in cs] or ['unspecified']
        tasks.append(dict(id=t['id'],features=features,mode=mode,source=source,
                          protein=t['input_description'].startswith('PROTEIN'),mappings=maps))
    views={}
    for view,field in [('clade','clade'),('species','row'),('allSpecies','allSpeciesRow')]:
        rs=[rows[r['id']] for r in db['coverage_rows'] if r['view']==view]
        rowtasks={r['id']:[] for r in rs};cells=collections.defaultdict(list)
        for i,t in enumerate(tasks):
            assigned={m[field] for m in t['mappings']}
            # Known-origin constructs stay with their taxa; construction is an attribute.
            if 'synthetic' in assigned and assigned-{'synthetic','unknown'}:assigned.remove('synthetic')
            for rid in sorted(assigned):
                if rid not in rowtasks:raise ValueError('Unknown coverage row: '+rid)
                rowtasks[rid].append(i)
                for feature in t['features']:cells[rid+'|'+feature].append(i)
        if {i for ids in rowtasks.values() for i in ids}!=set(range(len(tasks))):raise ValueError('Coverage lost tasks')
        for r in rs:
            path=[];n=lookup[r['displayParent']];seen=set()
            while n:
                if n['id'] in seen:raise ValueError('Taxonomy cycle: '+n['id'])
                seen.add(n['id']);path.insert(0,n['id']);n=lookup.get(n['parent'])
            if path!=r['displayPath']:raise ValueError('Stale coverage lineage: '+r['id'])
        views[view]=dict(rows=rs,cells=dict(cells),rowTasks=rowtasks)
    notes={kind:[json.loads(r['payload_json'])|{'evidence':r['evidence_id']} for r in db['coverage_notes'] if r['kind']==kind] for kind in ['gap','known','context']}
    return dict(tasks=tasks,features=settings['features'],featureGroups=settings['featureGroups'],
                modes=settings['modes'],sources=settings['sources'],references=settings['references'],populationGroups=settings.get('populationGroups',{}),
                presentation=dict(nodes=nodes,views=views,sections=settings['sections'],
                                  gaps=notes['gap'],known=notes['known'],context=notes['context']))
