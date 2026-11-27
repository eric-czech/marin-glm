"""Import the audited local coverage prototype into the catalogue authoring data.

One-time curation: pass the prototype directory, including its cached taxonomy
responses. Routine builds use only the committed catalogue; no network or cache.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]


def import_coverage(directory):
    prototype=json.loads((directory/'coverage-data.json').read_text())
    data=json.loads((ROOT/'data/catalogue.json').read_text())
    tree=prototype['presentation'];lookup={n['id']:n for n in tree['nodes']}
    pops={p['id']:p for p in data['populations']}
    evidences={e['id']:e for e in data['evidence']}
    source_by_url={s['url']:s['id'] for s in data['sources']}
    evidence_by_url={e['url']:e for e in data['evidence']}
    taxa={};names={}
    for file in sorted(directory.glob('taxonomy*.xml')):
        for taxon in ET.parse(file).getroot().findall('Taxon'):
            for t in taxon.findall('LineageEx/Taxon')+[taxon]:
                taxa[int(t.findtext('TaxId'))]=dict(name=t.findtext('ScientificName'),rank=t.findtext('Rank'))
            for name in [taxon.findtext('ScientificName')]+[x.text for x in taxon.findall('OtherNames/*') if x.text]:
                names[name.lower()]=int(taxon.findtext('TaxId'))

    def evidence(url,statement,locator='Coverage audit; source organism / biological classification',basis=None):
        key='coverage-'+hashlib.sha256((url+'\n'+statement).encode()).hexdigest()[:18]
        if key in evidences:return key
        prior=evidence_by_url.get(url)
        sid=prior['source_id'] if prior else source_by_url.get(url)
        if not sid:
            sid='coverage-source-'+hashlib.sha256(url.encode()).hexdigest()[:16]
            data['sources'].append(dict(id=sid,title=locator,kind='documentation',url=url,
                version='Inspected coverage-prototype source',retrieved='2026-11-27',sha256=None,
                local_path=None,availability='available',notes='Imported from the cited local coverage audit; no full-text or whole-dataset verification is implied.'))
            source_by_url[url]=sid
        item=dict(id=key,source_id=sid,locator=locator,url=url,basis=basis or (prior['basis'] if prior else 'documentation'),statement=statement,inspected='2026-11-27')
        data['evidence'].append(item);evidences[key]=item
        return key

    def add_population(pid,name,parent,taxid=None,rank='clade',notes=None):
        if pid not in pops:
            p=dict(id=pid,name=name,rank=rank,parent_id=parent,ncbi_taxid=taxid,notes=notes)
            pops[pid]=p;data['populations'].append(p)
        return pid

    aliases={'eukaryota':'euk','mammalia':'mammals','aves':'birds','teleostei':'teleosts','insecta':'insects','nematoda':'nematodes'}
    node_pop={}
    for n in tree['nodes']:
        if n['id'] in ('unplaced','bryophytes'):continue
        if n['id']=='monocots-other':
            node_pop[n['id']]=node_pop['monocots']
            continue  # A named remainder is not a biological clade.
        pid=aliases.get(n['id'],n['id']);parent=node_pop.get(n['parent'])
        sci={'Angiosperms':'Magnoliopsida','Animals':'Metazoa'}.get(n['scientific'] or n['label'],n['scientific'] or n['label'])
        taxid=names.get(sci.lower())
        if not taxid:
            taxid=next((int(re.search(r'id=(\d+)',u)[1]) for u in n['sources'] if re.search(r'id=(\d+)',u)),None)
        rank=n.get('rank','').lower() or taxa.get(taxid,{}).get('rank') or 'clade'
        add_population(pid,n['scientific'] or n['label'],parent,taxid,rank)
        pops[pid].update(parent_id=parent)
        if n['id']=='plants':pops[pid]['rank']='clade'
        node_pop[n['id']]=pid
        for url in n['sources']:
            eid=evidence(url,f"{n['label']} is placed within {lookup[n['parent']]['label'] if n['parent'] else 'its displayed root section'}. {n['note']}",'Biological classification / '+n['label'])
            if not any(x['entity_table']=='populations' and x['entity_id']==pid and x['field']=='parent_id' and x['evidence_id']==eid for x in data['field_evidence']):
                data['field_evidence'].append(dict(entity_table='populations',entity_id=pid,field='parent_id',evidence_id=eid,note='Biological ancestry; the display may omit intermediate ancestors.'))

    # Existing family-level nodes retain their detail beneath the new backbone.
    for pid,parent in [('brassicaceae','eudicots'),('solanaceae','eudicots'),('fabaceae','eudicots'),('bryophytes','land')]:
        pops[pid]['parent_id']=node_pop.get(parent,parent)
    for p in pops.values():
        if p['parent_id']=='monocots-other':p['parent_id']='monocots'
    data['populations']=[p for p in data['populations'] if p['id']!='monocots-other']
    pops.pop('monocots-other',None)
    data['field_evidence']=[r for r in data['field_evidence'] if not(r['entity_table']=='populations' and r['entity_id']=='monocots-other')]

    by_taxid={p['ncbi_taxid']:p['id'] for p in pops.values() if p['ncbi_taxid']}
    by_name={p['name'].lower():p['id'] for p in pops.values()}
    allrows={r['id']:r for r in tree['views']['allSpecies']['rows']}

    def mapping_population(m):
        if m['clade']=='unknown':return None
        if m['clade']=='synthetic':return 'synthetic'
        taxid=m.get('speciesId')
        name=m.get('species') or m['name']
        pid=by_taxid.get(taxid) if taxid else None
        pid=pid or by_name.get(name.lower())
        parent=node_pop[allrows[m['allSpeciesRow']]['displayParent']]
        if taxid:
            pid=pid or 'taxon-'+str(taxid)
            add_population(pid,name,parent,taxid,'species','Species ancestor from cached NCBI taxonomy; task evidence identifies the evaluated sequence origin or protein target, not the assay host.')
            pops[pid]['ncbi_taxid']=taxid
            # Keep a more detailed existing family parent when it is compatible.
            ancestor=pops[pid]['parent_id'];seen=set();lineage=[]
            while ancestor and ancestor not in seen:
                seen.add(ancestor);lineage.append(ancestor);ancestor=pops[ancestor]['parent_id']
            if parent not in lineage:pops[pid]['parent_id']=parent
            by_taxid[taxid]=pid;by_name[name.lower()]=pid
            return pid
        return pid or parent

    data['coverage_nodes']=[dict(id=n['id'],parent_id=n['parent'],population_id=node_pop.get(n['id']),
        label=n['label'],scientific=n['scientific'],rank=n.get('rank',''),note=n['note'],section=n['section'],
        jump=n.get('jump'),sources_json=json.dumps(n['sources'],ensure_ascii=False)) for n in tree['nodes']]
    imported=[];mapping_pops={}
    for task in prototype['tasks']:
        for i,m in enumerate(task['mappings']):
            pid=mapping_population(m);mapping_pops[(task['id'],i)]=pid
            statement=m.get('note') or f"Evaluated origin/target assignment: {m['name']}. Basis: {m['basis']}."
            eid=evidence(m['url'],statement,'Task organism / '+task['name'])
            supporting=[evidence(u,statement,'Task organism supporting evidence / '+task['name']) for u in dict.fromkeys([m.get('taxonomy')]+m.get('links',[])) if u]
            if m.get('species')=='Eschscholzia californica':
                supporting.append(evidence('https://www.mobot.org/MOBOT/research/APweb/introductionnew.htm',
                    'Ranunculales is nested within EUDICOTS in APweb. This bridges the missing intermediate eudicot node in the cached Eschscholzia lineage.',
                    'APweb classification: EUDICOTS / Ranunculales',basis='documentation'))
            imported.append(dict(id=task['id']+'-mapping-'+str(i),task_id=task['id'],population_id=pid,basis=m['basis'],
                evidence_id=eid,supporting_json=json.dumps(supporting),clade_row='clade:'+m['clade'],species_row='species:'+m['row'],
                all_species_row='allSpecies:'+m['allSpeciesRow'],metadata_json=json.dumps(m,ensure_ascii=False)))
            if pid and (m.get('species') or m['basis']!='catalogue sequence origin'):
                relation='protein-target' if m['basis']=='protein-target' or task['protein'] else 'sequence-origin'
                key=(task['id'],pid,relation)
                if not any((r['task_id'],r['population_id'],r['relation'])==key for r in data['task_populations']):
                    data['task_populations'].append(dict(task_id=task['id'],population_id=pid,variant_id=None,relation=relation,
                        coverage=statement,evidence_id=eid))
    data['coverage_mappings']=imported
    # The NTv3 scored test panel supersedes the previous unresolved routing tags.
    ntv3={t['id'] for t in prototype['tasks'] if t['name'] in ('Exact CDS-exon structures','Exact whole-gene structures')}
    data['task_populations']=[r for r in data['task_populations'] if not(r['task_id'] in ntv3 and r['relation']=='sequence-origin' and pops[r['population_id']]['rank']!='species')]

    data['coverage_rows']=[]
    for view,value in tree['views'].items():
        field={'clade':'clade','species':'row','allSpecies':'allSpeciesRow'}[view]
        for row in value['rows']:
            ids={mapping_pops[(t['id'],i)] for t in prototype['tasks'] for i,m in enumerate(t['mappings']) if m[field]==row['id']}
            data['coverage_rows'].append(dict(id=view+':'+row['id'],view=view,row_key=row['id'],node_id=row['displayParent'],
                population_ids_json=json.dumps(sorted(x for x in ids if x)),metadata_json=json.dumps(row,ensure_ascii=False)))
    data['coverage_notes']=[]
    for kind,field in [('gap','gaps'),('known','known'),('context','context')]:
        for i,n in enumerate(tree[field]):
            eid=evidence(n['source'],n['why'],'Coverage '+kind+' / '+n['label'])
            data['coverage_notes'].append(dict(id=kind+'-'+str(i),kind=kind,node_id=n['parent'],evidence_id=eid,payload_json=json.dumps(n,ensure_ascii=False)))
    settings={k:prototype[k] for k in ['features','featureGroups','modes','sources']}
    settings.update(sections=tree['sections'],references=tree['references'])
    # Explicit catalogue groups overlap biological ancestry. They are filter
    # memberships, not new taxonomic parents or expansions of broad task labels.
    settings['populationGroups']={
        'bryophytes':[node_pop['mosses'],node_pop['liverworts']],
        'phages':[by_name[name] for name in ('lambdavirus lambda','punavirus p1') if name in by_name],
    }
    data['coverage_settings']=[dict(key=k,value_json=json.dumps(v,ensure_ascii=False)) for k,v in settings.items()]

    # Parent-first order makes the authoring export valid with immediate FKs.
    def ordered(rows,key='parent_id'):
        result=[];done=set()
        while rows:
            ready=[r for r in rows if not r[key] or r[key] in done]
            if not ready:raise ValueError('Cyclic or missing parent')
            result+=ready;done.update(r['id'] for r in ready);rows=[r for r in rows if r not in ready]
        return result
    data['populations']=ordered(data['populations'])
    data['coverage_nodes']=ordered(data['coverage_nodes'])
    for row in data['metadata']:
        if row['key']=='updated':row['value']='2026-11-27'
    (ROOT/'data/catalogue.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f"Imported {len(imported)} cited mappings, {len(data['coverage_rows'])} display rows and {len(data['coverage_nodes'])} biological nodes.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('prototype',type=Path)
    import_coverage(parser.parse_args().prototype)
