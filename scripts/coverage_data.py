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
    original_models=collections.defaultdict(set)
    for u in db['model_evaluations']:
        if u['provenance'] in ('original-paper','original-release'):
            original_models[u['task_id']].add(u['model_id'])
    tasks=[]
    outputs={r['task_id']:r for r in db['task_outputs']}
    cds_scopes={r['task_id']:r['scope'] for r in db['task_feature_scopes'] if r['feature_id']=='cds'}
    feature_families={
        'gene-elements':{'gene','cds','exon','intron'},
        'splice-elements':{'splice','splice-junction'},
        'utrs':{'utr','utr5','utr3'},'translation-boundaries':{'translation-start','translation-stop'},
        'regulatory-elements':{'promoter','enhancer','tfbs','regulatory','polya','terminator'},
        'chromatin-organization':{'chromatin-boundary'},
        'rna-features':{'mrna','ncrna','lncrna','rrna','trna','ribozyme','aptamer'},
        'clusters-operons':{'bgc','operon'},'crispr-arrays':{'crispr-array'},'repetitive':{'repeat'},
        'intergenic-context':{'intergenic'},'broad-context':{'genome','prophage','unspecified'}}
    def group_features(features,output,task_id):
        if output['category_id']=='output-linked-structure':
            return ['transcript-structures' if output['structure_scope']=='splice-pattern' else 'gene-structures']
        grouped=[key for key,values in feature_families.items() if values & set(features)]
        if cds_scopes.get(task_id) in ('restricted-target','protein-reference'):
            grouped=[g for g in grouped if g not in ('gene-elements','splice-elements','intergenic-context')]
            grouped.insert(0,'coding-sequence')
        return grouped
    for t in db['tasks']:
        maps=taskmaps[t['id']]
        if not maps:raise ValueError('Coverage mapping missing: '+t['id'])
        typ=t['task_type'].lower();cs=cats[t['id']];sids=memberships[t['id']]
        mode=3 if any(x in typ for x in ('diagnostic','analysis','case study','computational','ortholog completeness')) else 1 if 'generation' in cs else 2 if any(x in typ for x in ('retrieval','clustering','bigene','eds')) else 0
        source=next(i for i,s in enumerate(settings['sources'])
            if s.get('fallback') or original_models[t['id']] & set(s.get('originalModels',[]))
            or sids & set(s.get('evaluations',[])))
        features=[f['id'] for f in settings['features'] if f['id'] in cs] or ['unspecified']
        output=outputs[t['id']]
        grouped=group_features(features,output,t['id'])
        for mapping in maps:
            # Where a released manifest resolves species × target composition,
            # do not project all collection-wide features onto every species.
            mapping['features']=mapping.get('featureIds',features)
            if not set(mapping['features'])<=set(features):raise ValueError('Unknown species-specific feature: '+t['id'])
            mapping['groupedFeatures']=group_features(mapping['features'],output,t['id'])
        if not grouped:raise ValueError('Grouped feature assignment missing: '+t['id'])
        tasks.append(dict(id=t['id'],features=features,mode=mode,source=source,
                          groupedFeatures=grouped,output=output['category_id'],
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
                for feature in {f for m in t['mappings'] if m[field]==rid for f in m['features']}:cells[rid+'|'+feature].append(i)
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
                groupedFeatures=settings['groupedFeatures'],
                modes=settings['modes'],sources=settings['sources'],references=settings['references'],populationGroups=settings.get('populationGroups',{}),
                presentation=dict(nodes=nodes,views=views,sections=settings['sections'],
                                  gaps=notes['gap'],known=notes['known'],context=notes['context']))
