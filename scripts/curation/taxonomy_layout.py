"""Place source-named species using cached NCBI lineage, not gene-name guesses."""
import copy
import json
from common import ROOT, Catalogue


class TaxonomyLayout:
    def __init__(self,d):
        self.d=d;self.c=Catalogue(d)
        self.records=json.loads((ROOT/'data/taxonomy-inspections.json').read_text())

    def node(self,id,parent,label,scientific,taxid,rank='clade'):
        if any(n['id']==id for n in self.d['coverage_nodes']):return
        c=self.c
        c.put('populations',dict(id=id,name=scientific,rank=rank,
            parent_id=c.get('coverage_nodes',parent)['population_id'],ncbi_taxid=taxid,
            notes='NCBI lineage; presentation retains only selected taxonomic boundaries.'))
        c.put('coverage_nodes',dict(id=id,parent_id=parent,population_id=id,label=label,
            scientific=scientific,rank=rank.title(),note='',section='cellular',jump=None,
            sources_json=json.dumps(['https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(taxid)])))

    def prepare(self):
        self.node('amoebozoa','eukaryota','Amoebozoans','Amoebozoa',554915)
        self.node('apicomplexa','alveolata','Apicomplexans','Apicomplexa',5794,'phylum')
        self.node('schizosaccharomycetes','ascomycota','Fission yeasts','Schizosaccharomycetes',147554,'class')

    def link(self,task,name,evidence,variant=None,note='Source-named sequence species.',breakout=False):
        c=self.c;self.prepare()
        old=next((p for p in self.d['populations'] if p['name']==name and p.get('ncbi_taxid')),None)
        meta=self.records.get(name)
        if not meta:
            if old:
                c.population(task,old['id'],evidence,note,variant);return old['id']
            raise ValueError('No reviewed taxonomy for '+name)
        tid=meta['tax_id'];current=meta['current_scientific_name']['name'];sid='final-taxonomy-'+str(tid)
        url='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(tid)
        c.source(sid,'NCBI taxonomy: '+current,url,kind='taxonomy',version='NCBI Datasets taxonomy report, 2026-11-27')
        taxev=c.evidence(sid+'-classification',sid,'Full taxonomy report: parents and rank classification',
            f'NCBI taxon {tid}: {current}; classification {json.dumps(meta["classification"],ensure_ascii=False)}. The source name is retained in the linked dataset variant.','documentation')
        pop=next((p for p in self.d['populations'] if p.get('ncbi_taxid')==tid and p['rank'].lower()=='species'),None)
        lineage=set(meta['parents'])|{tid};pops={p['id']:p for p in self.d['populations']}
        nodes={n['id']:n for n in self.d['coverage_nodes']}
        def path(id):
            result=[]
            while id:result.append(id);id=nodes[id]['parent_id']
            return list(reversed(result))
        matches=[n for n in nodes.values() if n.get('population_id') in pops and pops[n['population_id']].get('ncbi_taxid') in lineage]
        if not matches:raise ValueError('No reviewed display lineage for '+name)
        node=max(matches,key=lambda n:len(path(n['id'])));clade=node['id'];chain=path(clade)
        if pop is None:
            pid='taxon-'+str(tid)
            c.put('populations',dict(id=pid,name=current,rank='species',parent_id=node['population_id'],ncbi_taxid=tid,notes='Source identity resolved with NCBI; host context is recorded separately.'))
        else:pid=pop['id']
        previous=next((m for m in self.d['coverage_mappings'] if m['population_id']==pid and not m['clade_row'].endswith('-unresolved')),None)
        if previous and not breakout:
            c.population(task,pid,evidence,note,variant)
            mapping=c.get('coverage_mappings',task+'-mapping-'+pid)
            mapping['supporting_json']=json.dumps([evidence,taxev]);return pid
        c.put('task_populations',dict(task_id=task,population_id=pid,relation='sequence-origin',variant_id=variant,coverage=note,evidence_id=evidence),('task_id','population_id','relation'))
        group='plants' if 33090 in lineage else 'animals' if 33208 in lineage else 'fungi' if 4751 in lineage else 'bacteria' if 2 in lineage else 'archaea' if 2157 in lineage else 'other-euk'
        group_label={'plants':'Viridiplantae','animals':'Animalia','fungi':'Fungi','bacteria':'Bacteria','archaea':'Archaea','other-euk':'Eukaryota'}[group]
        base=dict(group=group,groupLabel=group_label,node=clade,path=chain[1:],lineageLabel=node['label'],
            displayParent=clade,placementStatus=False,displayPath=chain,displayLineage=' → '.join(nodes[n]['label'] for n in chain),
            note='Source-defined species and NCBI ancestry; count derives from current task mappings.')
        if not any(r['id']=='clade:'+clade for r in self.d['coverage_rows']):
            c.put('coverage_rows',dict(id='clade:'+clade,view='clade',row_key=clade,node_id=clade,population_ids_json='[]',
                metadata_json=json.dumps(base|dict(id=clade,label=node['label'],displayLabel=node['label'],common=''),ensure_ascii=False)))
        # New model systems and single-lineage exemplars remain individually
        # recognizable; additional crop taxa share a resolved clade remainder.
        individual=breakout or tid in [44689,5833,4896,10116,9913,4565]
        selected=clade+'-sp-'+str(tid) if individual else clade+'-other'
        allkey=clade+'-sp-'+str(tid)
        for view,key,single in [('species',selected,individual),('allSpecies',allkey,True)]:
            rid=view+':'+key;existing=next((r for r in self.d['coverage_rows'] if r['id']==rid),None)
            members=set(json.loads(existing['metadata_json']).get('members',[]) if existing else []);members.add(current)
            popids=set(json.loads(existing['population_ids_json']) if existing else []);popids.add(pid)
            label=current if single else 'Other named species'
            c.put('coverage_rows',dict(id=rid,view=view,row_key=key,node_id=clade,population_ids_json=json.dumps(sorted(popids)),
                metadata_json=json.dumps(base|dict(id=key,label=label,displayLabel=label,common=meta.get('curator_common_name','') if single else '',
                    kind='species' if single else 'other',members=sorted(members),clade=clade,cladeLabel=node['label'],lineageHint=''),ensure_ascii=False)))
        c.put('coverage_mappings',dict(id=task+'-mapping-'+pid,task_id=task,population_id=pid,evidence_id=evidence,
            supporting_json=json.dumps([evidence,taxev]),basis='Source-named species and NCBI lineage',
            clade_row='clade:'+clade,species_row='species:'+selected,all_species_row='allSpecies:'+allkey,
            metadata_json=json.dumps(dict(name=current,row=selected,species=current,speciesId=tid,clade=clade,allSpeciesRow=allkey,
                basis='Source-named species and NCBI lineage',url=c.get('evidence',evidence)['url'],taxonomy=url),ensure_ascii=False)))
        return pid
