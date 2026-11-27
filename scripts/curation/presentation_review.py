"""Final presentation rules derived from the reviewed canonical task records."""
import collections
import json
from common import Catalogue


def populate(d):
    c=Catalogue(d)
    settings={r['key']:json.loads(r['value_json']) for r in d['coverage_settings']}
    sources=[
        dict(id='evo',label='Evo 1 / Evo 2',shape='circle',originalModels=['evo1','evo2'],
             note='Documented original-paper/release use takes priority. Exact Evo 2 original attribution remains a separate filter and task field.'),
        dict(id='rna',label='RNAGym / ProteinGym / TraitGym',shape='diamond',evaluations=['rnagym','proteingym','traitgym'],
             note='Fitness and regulatory-variant collections. Protein-only inputs remain hollow markers.'),
        dict(id='plantcad',label='PlantCAD2 / GeneCAD / Botanic-1',shape='square',evaluations=['plantcad2-zero','plantcad2-ft','genecad','botanic1-evals'],
             note='PlantCAD2 evaluations, GeneCAD annotation fine-tuning and Botanic-1 evaluations.'),
        dict(id='classification',label='NT / GUE / GB / GENEB',shape='triangle',evaluations=['nt-original','nt-revised','gue','gb','geneb'],
             note='Related classification collections; exact datasets, releases and readouts remain distinct in the task details.'),
        dict(id='microbial',label='BacBench / DGEB / BGC',shape='hexagon',evaluations=['bacbench','dgeb','bgc','bgcs'],
             note='BacBench, DGEB, BGC-Bench and BGCs-Bench. These collections also contain nonbacterial or protein-only reference tasks.'),
        dict(id='other',label='Other papers / benchmarks',shape='cross',fallback=True,
             note='Every remaining collection. The marker tooltip and task record identify its actual evaluation, paper and model associations.')]
    settings['sources']=sources
    features=settings['features']
    for id,label,group,after in [('utr','UTRs (unspecified)','Gene structure','utr3'),('crispr-array','CRISPR arrays','Sequence context / multi-gene regions','operon'),('prophage','Prophage regions','Sequence context / multi-gene regions','crispr-array')]:
        if id not in {r['id'] for r in features}:
            cat=c.get('categories',id)
            features.insert(next(i for i,r in enumerate(features) if r['id']==after)+1,
                dict(id=id,label=label,group=group,definition=cat['definition']))
    settings['featureGroups']=[dict(label=g,ids=[r['id'] for r in features if r['group']==g]) for g in dict.fromkeys(r['group'] for r in features)]
    grouped=settings['groupedFeatures']
    if 'crispr-arrays' not in {r['id'] for r in grouped}:
        grouped.insert(next(i for i,r in enumerate(grouped) if r['id']=='clusters-operons')+1,
            dict(id='crispr-arrays',label='CRISPR arrays',group='Microbial regions',definition='CRISPR repeat/spacer arrays or their components. The output distinguishes sequence generation, supplied components and local diagnostics.'))
    next(r for r in grouped if r['id']=='utrs')['definition']='5′, 3′ or pooled untranslated-region targets. Translation start/stop detection is separate.'
    for key,value in settings.items():
        c.put('coverage_settings',dict(key=key,value_json=json.dumps(value,ensure_ascii=False)),('key',))
    # Remove frozen prototype counts and memberships. Counts are unique task
    # IDs per actual mapping, not sums of collection or species memberships.
    byrow=collections.defaultdict(list)
    for mapping in d['coverage_mappings']:
        for key in ['clade_row','species_row','all_species_row']:byrow[mapping[key]].append(mapping)
    pops={r['id']:r for r in d['populations']}
    for row in d['coverage_rows']:
        mappings=byrow[row['id']]
        ids=sorted({r['population_id'] for r in mappings if r['population_id']})
        row['population_ids_json']=json.dumps(ids)
        meta=json.loads(row['metadata_json'])
        if 'members' in meta:meta['members']=sorted({pops[id]['name'] for id in ids})
        meta['note']=f"{len({r['task_id'] for r in mappings})} unique mapped task records. Task-level associations do not establish a released species × feature subset."
        row['metadata_json']=json.dumps(meta,ensure_ascii=False)
    # Coverage questions are explicitly catalogue-relative. Broad source panels
    # with missing taxa do not justify a verified species-absence claim.
    tasks={r['id']:r for r in d['tasks']}
    for note in d['coverage_notes']:
        if note['kind']!='gap':continue
        g=json.loads(note['payload_json'])
        if g['id']=='chimp':g['match']=['Pan troglodytes']
        matches={p['id'] for p in d['populations'] if p['name'] in g.get('match',[]) or g.get('matchPrefix') and p['name'].startswith(g['matchPrefix']) or p['name']==g['species']}
        tids=sorted({r['task_id'] for r in d['coverage_mappings'] if r['population_id'] in matches})
        g.update(mappedTasks=len(tids),expected=len(tids),status='Limited mapped task coverage' if tids else 'No species-resolved task mapped',
            coverageSources=[dict(task=id,name=tasks[id]['name'],url=c.get('evidence',tasks[id]['evidence_id'])['url']) for id in tids],
            scope='All current task mappings and the reviewed source inventories. A source panel without a released species manifest cannot establish either species presence or species absence.')
        if g['id']=='chimp':
            g['coverage']='Chimpanzee sequence examples occur in the original NT donor/acceptor release. This supplies local splice-site classification coverage; it does not establish chimpanzee regulatory-variant, expression, complete-isoform or generation evaluation.'
            g['caveat']='Pretraining genomes and homologous alignment context are separate from the target-species evaluation evidence listed here.'
        elif tids:
            g['coverage']=f'{len(tids)} catalogue task records have a resolved source association. See the linked task definitions for the actual biological targets and release overlap.'
        else:
            g['coverage']='No species-resolved task association is established by the reviewed release inventories.'
        if g['id']=='prochlorococcus':g['caveat']='Resolved cyanobacterial tasks include other genera. Broad microbial panels without complete per-sequence origin metadata do not establish Prochlorococcus inclusion or exclusion.'
        if g['id']=='sponge-symbionts':g['caveat']='Bacterial biosynthetic targets are distinct from the sponge host genome. No Entotheonella-resolved task is established by the reviewed BGC inventories.'
        note['payload_json']=json.dumps(g,ensure_ascii=False)
    return d
