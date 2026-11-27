"""Resolve reference-RNA origins from primary assay papers, not assay hosts.

Explicit authoring helper. It requires only the retained inspection receipts;
routine catalogue builds neither fetch papers nor run this helper.
"""
import copy
import json
from common import Catalogue, ROOT, DATE


def populate(data):
    c=Catalogue(data)
    decisions=[]

    def source(key,title,url,locator,statement,tasks,population=None):
        sid='rna-origin-'+key
        c.source(sid,title,url)
        c.evidence(sid,sid,locator,statement)
        decisions.append(dict(evidence_id=sid,tasks=tasks,population=population,
                              locator=locator,conclusion=statement,url=url))
        for tid in tasks:
            if population:
                data['coverage_mappings']=[m for m in data['coverage_mappings']
                    if not(m['task_id']==tid and m['population_id'] is None)]
                c.population(tid,population,sid,statement)
            else:
                for m in data['coverage_mappings']:
                    if m['task_id']==tid and m['population_id'] is None:
                        meta=json.loads(m['metadata_json'])
                        meta.update(note=statement,url=url)
                        m.update(evidence_id=sid,supporting_json=json.dumps([sid]),
                                 metadata_json=json.dumps(meta,ensure_ascii=False))
                c.limit('tasks',tid,'reference_organism','not-reported',statement,sid)
            c.field('tasks',tid,'sequence_origin',sid)
            review=next(r for r in data['source_reviews']
                        if r['entity_table']=='tasks' and r['entity_id']==tid)
            review['evidence_ids_json']=json.dumps(sorted(set(json.loads(review['evidence_ids_json'])+[sid])))
        return sid

    def add_reference_population(id,name,taxid,parent,node,template_population,
                                 new_node=None,rank='species'):
        """Add an explicit display assignment without copying assay evidence."""
        url='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(taxid)
        c.put('populations',dict(id=id,name=name,rank=rank,parent_id=parent,
            ncbi_taxid=taxid,notes='Primary assay reference; experimental hosts are separate.'))
        data['coverage_mappings']=[m for m in data['coverage_mappings']if not
            (m['population_id']==id and (m['evidence_id'].startswith('rna-origin-') or m['id'].startswith('rna-reference-layout-')))]
        template=next(m for m in data['coverage_mappings'] if m['population_id']==template_population)
        if new_node:
            c.put('coverage_nodes',dict(id=node,parent_id='viruses',population_id=parent,
                label=new_node[0],scientific=new_node[1],rank=new_node[2],note=new_node[3],
                section='viruses',jump=None,sources_json=json.dumps([url])))
        template_all=next(r for r in data['coverage_rows'] if r['id']==template['all_species_row'])
        meta0=json.loads(template_all['metadata_json'])
        rowkey=node+'-sp-'+str(taxid)
        for view in (('species','allSpecies') if new_node else ('allSpecies',)):
            meta=copy.deepcopy(meta0)
            meta.update(id=rowkey,label=name,common='',kind='species',members=[name],
                clade=node,cladeLabel=node,path=[node],node=node,
                lineageLabel=new_node[0] if new_node else meta0['lineageLabel'],
                displayParent=node,displayPath=['viruses',node] if new_node else meta0['displayPath'],
                displayLineage='Viruses → '+new_node[0] if new_node else meta0['displayLineage'],
                displayLabel=name,placementStatus=False,
                note='Mutational assay of this reference; this is not species-wide validation.')
            c.put('coverage_rows',dict(id=view+':'+rowkey,view=view,row_key=rowkey,node_id=node,
                population_ids_json=json.dumps([id]),metadata_json=json.dumps(meta,ensure_ascii=False)))
        if new_node:
            meta.update(id=node,label=new_node[0],kind='clade')
            c.put('coverage_rows',dict(id='clade:'+node,view='clade',row_key=node,node_id=node,
                population_ids_json=json.dumps([id]),metadata_json=json.dumps(meta,ensure_ascii=False)))
        else:
            data['coverage_rows']=[r for r in data['coverage_rows']if r['id']!='species:'+rowkey]
            r=next(r for r in data['coverage_rows']if r['id']=='clade:'+node)
            r['population_ids_json']=json.dumps(sorted(set(json.loads(r['population_ids_json'])+[id])))
            r=next(r for r in data['coverage_rows']if r['id']==template['species_row'])
            r['population_ids_json']=json.dumps(sorted(set(json.loads(r['population_ids_json'])+[id])))
            meta=json.loads(r['metadata_json'])
            meta['members']=sorted(set(meta.get('members',[])+[name]))
            r['metadata_json']=json.dumps(meta,ensure_ascii=False)
        m=copy.deepcopy(template)
        m.update(id='rna-reference-layout-'+id,task_id='rnagym-peri-2022-ribozyme',
            population_id=id,clade_row='clade:'+node,
            species_row='species:'+rowkey if new_node else template['species_row'],
            all_species_row='allSpecies:'+rowkey)
        meta=dict(row=rowkey if new_node else template['species_row'].split(':',1)[1],name=name,clade=node,allSpeciesRow=rowkey,
                  species=name,speciesId=taxid,taxonomy=url)
        m['metadata_json']=json.dumps(meta,ensure_ascii=False)
        # The temporary template is consumed by Catalogue.population below.
        return m

    c.source('rna-origin-taxonomy','NCBI taxonomy of reference RNA sources',
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id=12475,31504,418699&retmode=xml',kind='taxonomy')
    c.evidence('rna-origin-taxonomy','rna-origin-taxonomy','TaxIds12475,31504,418699; complete returned lineages',
        'Hepatitis delta virus belongs to Ribozyviria. Tobacco ringspot virus satellite RNA is an unclassified RNA satellite, not the helper virus in Riboviria. DQ103524.1 is Azoarcus olearius (historical name Azoarcus sp.BH72), within Pseudomonadota.',basis='data')
    c.put('populations',dict(id='ribozyviria',name='Ribozyviria',rank='realm',parent_id='viruses',ncbi_taxid=None,notes=None))
    c.put('populations',dict(id='rna-satellites',name='RNA satellites',rank='unranked group',parent_id='viruses',ncbi_taxid=None,
        notes='NCBI unclassified satellite group; not the taxonomic lineage of its helper virus.'))
    templates=[
        add_reference_population('taxon-418699','Azoarcus olearius',418699,'pseudomonadota','pseudomonadota','taxon-666'),
        add_reference_population('taxon-671','Vibrio proteolyticus',671,'pseudomonadota','pseudomonadota','taxon-666'),
        add_reference_population('taxon-12475','Hepatitis delta virus',12475,'ribozyviria','ribozyviria','taxon-2955291',
            ('Hepatitis delta virus lineage','Ribozyviria','Realm','HDV reference RNA; distinct from Riboviria.'),rank='no rank'),
        add_reference_population('taxon-31504','Tobacco ringspot virus satellite RNA',31504,'rna-satellites','rna-satellites','taxon-2955291',
            ('RNA satellites','','Unranked group','The reference is satellite RNA, not the helper virus genome or plant host.'))]
    for m in templates:
        m.update(evidence_id='rna-origin-taxonomy',supporting_json='["rna-origin-taxonomy"]')
        c.put('coverage_mappings',m)

    # The Hayden paper identifies Azoarcus, without a species accession. Keep
    # the supported phylum assignment without borrowing the Peri accession.
    template=next(m for m in data['coverage_mappings']if m['population_id']=='taxon-666')
    rowkey='pseudomonadota-unspecified-species'
    for view in ('species','allSpecies'):
        meta=dict(id=rowkey,label='Species not specified',common='',kind='clade',
            group='bacteria',groupLabel='Bacteria',clade='pseudomonadota',
            cladeLabel='Proteobacteria',node='pseudomonadota',path=['pseudomonadota'],
            lineageLabel='Proteobacteria',displayParent='pseudomonadota',
            placementStatus=False,displayPath=['bacteria','pseudomonadota'],
            displayLineage='Bacteria → Proteobacteria',displayLabel='Species not specified',
            note='The assay identifies the reference genus Azoarcus; no exact species accession is supplied.')
        c.put('coverage_rows',dict(id=view+':'+rowkey,view=view,row_key=rowkey,node_id='pseudomonadota',
            population_ids_json='["pseudomonadota"]',metadata_json=json.dumps(meta)))
    m=copy.deepcopy(template)
    m.update(id='rna-reference-layout-pseudomonadota',task_id='evo-ncrna-hayden',population_id='pseudomonadota',
        species_row='species:'+rowkey,all_species_row='allSpecies:'+rowkey,
        metadata_json=json.dumps(dict(row=rowkey,name='Pseudomonadota',clade='pseudomonadota',
            allSpeciesRow=rowkey,species=None,speciesId=None)))
    c.put('coverage_mappings',m)
    r=next(r for r in data['coverage_rows']if r['id']=='clade:pseudomonadota')
    r['population_ids_json']=json.dumps(sorted(set(json.loads(r['population_ids_json'])+['pseudomonadota'])))
    source('hayden','Cryptic genetic variation promotes rapid evolutionary adaptation in an RNA enzyme',
        'https://pubmed.ncbi.nlm.nih.gov/21637259/',
        'Primary study organism indexing: Azoarcus/enzymology; cited reference group-I intron',
        'The study identifies the bacterial Azoarcus group-I ribozyme. The genus belongs to Pseudomonadota; no exact species accession for Evo’s retained cohort is inferred from the separate Peri study.',
        ['evo-ncrna-hayden'],'pseudomonadota')

    source('andreasson','Comprehensive sequence-to-function mapping of cofactor-dependent RNA catalysis in the glmS ribozyme',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC7125110/',
        'Results: consensus core glmS construct; Methods: RNA library design',
        'The reference is a consensus bacterial glmS ribozyme core, with designed linkers. This supports bacterial-family relevance, not a sampled natural species or a species-wide cohort.',
        ['rnagym-andreasson-2020-ribozyme','evo-ncrna-andreasson'],'bacteria')
    source('beck','Predicting higher-order mutational effects in an RNA enzyme by machine learning of high-throughput experimental data',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC9421044/',
        'Introduction; Results: CPEB3 mutant library',
        'The reference is a mammalian CPEB3 intronic ribozyme. The source describes this lineage but does not identify a species accession for the 69-nt reference; human origin is not inferred merely from the family name.',
        ['rnagym-beck-2022-ribozyme'],'mammals')
    source('kobori2015-chimeras','High-throughput assay and engineering of self-cleaving ribozymes by sequencing',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC4513843/',
        'Results: Design of ribozyme libraries; Figure2B–C',
        'Lib-J1/2 and Lib-P4 fuse the Anopheles gambiae drz-Agam-2-1 ribozyme with a Bacillus subtilis guanine aptamer and randomized connectors. They are engineered chimeras, not natural single-species RNA cohorts.',
        ['rnagym-kobori-2015-ribozyme-j12','rnagym-kobori-2015-ribozyme-p4'],'synthetic')
    source('kobori2015-environment','High-throughput assay and engineering of self-cleaving ribozymes by sequencing',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC4513843/',
        'Results: Design of ribozyme libraries; Figure2A',
        'Lib-Tw uses the twister reference described as an environmental DNA sequence, with modified termini and five randomized bases. This source does not identify its organism. Evo’s Kobori panel cites this paper, which also contains cross-species engineered aptazymes; the original panel does not provide a retained-row manifest distinguishing these arms.',
        ['rnagym-kobori-2015-ribozyme-tw','evo-ncrna-kobori'])
    source('kobori2018','Deep Sequencing Analysis of Aptazyme Variants Based on a Pistol Ribozyme',
        'https://pubs.acs.org/asbcd6/article/6/7/1283/730954/Deep-Sequencing-Analysis-of-Aptazyme-Variants',
        'Results and Discussion; Figure1a',
        'The aptazyme library fuses a pistol ribozyme from Alistipes putredinis with the Bacillus subtilis xpt-pbuX guanine aptamer and randomized connecting bases. This is an engineered chimera, not one natural organism.',
        ['rnagym-kobori-2018-ribozyme'],'synthetic')
    source('li2016','The fitness landscape of a tRNA gene',
        'https://public.websites.umich.edu/~zhanglab/publications/2016/Li_2016_Science.pdf#page=1',
        'Main text: native-locus gene replacement and library design',
        'The reference is the S.cerevisiae single-copy Arg-CCU tRNA. Mutant strains replace that gene at its native locus; the high-temperature growth assay does not represent multiple species.',
        ['rnagym-li-2016-trna'],'yeast')
    source('li2018','Multi-environment fitness landscapes of a tRNA gene',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC5966336/',
        'Results: Mapping multi-environment FLs of a tRNA gene',
        'The reference is S.cerevisiae HSX1/Arg-CCU tRNA, replaced at its native locus and assayed across environments. Environment labels are not distinct species.',
        ['nabench-li-environments'],'yeast')
    source('peri','Dynamic RNA Fitness Landscapes of a Group I Ribozyme during Changes to the Experimental Environment',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC8890501/',
        'Introduction: reference accession DQ103524.1; Methods: DNA template',
        'The reference derives from the Azoarcus group-I tRNA intron, accession DQ103524.1. Current GenBank identifies Azoarcus olearius, formerly Azoarcus sp.BH72. The study mutates seven sites and assays in vitro at eight magnesium concentrations; this is reference-RNA origin, not a panel of bacterial organisms.',
        ['rnagym-peri-2022-ribozyme'],'taxon-418699')
    source('pitt','Rapid Construction of Empirical RNA Fitness Landscapes',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC3392653/',
        'Main text: choice of class-II ligase and isolate a4-11',
        'The reference is the in-vitro-selected class-II ligase isolate a4-11. The experiment mutagenizes and reselects that artificial RNA; its comparison to viral population evolution does not assign it a viral organism.',
        ['rnagym-pitt-2010-ribozyme','evo-ncrna-pitt'],'synthetic')
    for key,pop,tasks,statement in [
        ('cpeb3','mammals',['rnagym-roberts-2023-cepeb3-ribozyme'],'The assayed reference is described as a mammalian CPEB3 ribozyme. No species accession is assigned to this 69-nt construct; it is not assumed identical to another CPEB3 assay.'),
        ('hdv','taxon-12475',['rnagym-roberts-2023-hdv-ribozyme'],'The reference is a hepatitis delta virus ribozyme. Its lineage is Ribozyviria, not Riboviria; the in-vitro assay is not evidence of a human genomic RNA target.'),
        ('twister','rice',['rnagym-roberts-2023-tw-ribozyme'],'The reference is explicitly an Oryza sativa twister ribozyme. A rice-derived RNA mutant assay does not establish genome-wide plant prediction.'),
        ('hairpin','taxon-31504',['rnagym-roberts-2023-hp-ribozyme'],'The hairpin reference derives from tobacco ringspot virus satellite RNA. The satellite RNA, helper virus and tobacco host are distinct; the assignment follows the satellite reference.'),
        ('hammerhead',None,['rnagym-roberts-2023-hh-ribozyme'],'The assayed construct is a type-III hammerhead ribozyme. The paper compares it with sTRSV structural data but supplies no organism accession for this exact 45-nt reference; structural comparison alone does not establish its natural taxon.')]:
        source('roberts-'+key,'RNA sequence to structure analysis from comprehensive pairwise mutagenesis of multiple self-cleaving ribozymes',
            'https://pmc.ncbi.nlm.nih.gov/articles/PMC9901934/',
            'Results: Comprehensive analysis of mutational effects; Figures1–5; Methods: library preparation',statement,tasks,pop)
    source('soo','Fitness landscape of a dynamic RNA structure',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC7877785/',
        'Introduction; Results: in-vivo selection of group-I intron variants',
        'The reference intron is from Tetrahymena thermophila. E.coli is the assay host, not the origin of the mutated intron sequence.',
        ['rnagym-soo-2021-ribozyme'],'taxon-5911')
    tome=source('tome','Comprehensive Analysis of RNA-Protein Interactions by High Throughput Sequencing-RNA Affinity Profiling',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC4073888/',
        'Main text; Online Methods: construction of HiTS-RAP halting templates; references16–17',
        'The inputs are mutagenized GFP-binding and NELF-E-binding aptamers from selection studies. They are selected RNA constructs; the GFP or Drosophila protein target does not establish a natural species origin for the aptamer RNA.',
        ['rnagym-tome-2014-gfp-aptamer','rnagym-tome-2014-nelfe-aptamer'],'synthetic')
    for key,title,url,statement in [
        ('gfp-selex','RNA aptamers that functionally interact with green fluorescent protein and its derivatives','https://pmc.ncbi.nlm.nih.gov/articles/PMC3300005/','The GFP aptamers were selected from a random-core RNA pool and optimized by deletion, substitution and additional SELEX.'),
        ('nelf-selex','Defining NELF-E RNA Binding in HIV-1 and Promoter-Proximal Pause Regions','https://pmc.ncbi.nlm.nih.gov/articles/PMC3894171/','The NELF-E aptamer selection starts from a 70-nucleotide randomized region with constant amplification flanks. A separate nascent-genomic-RNA selection is not the origin of this random-library aptamer.')]:
        eid=source(key,title,url,'Results: aptamer selection; Methods: SELEX',statement,[])
        tid='rnagym-tome-2014-'+('gfp' if key.startswith('gfp') else 'nelfe')+'-aptamer'
        c.field('tasks',tid,'sequence_origin',eid)
    source('zhang2020','Accurate inference of the full base-pairing structure of RNA by deep mutational scanning and covariation-induced deviation of activity',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC7026644/',
        'Introduction: 81-nucleotide CPEB3 reference',
        'The source explicitly places its 81-nt CPEB3 ribozyme in an intron of the human CPEB3 gene. This human-origin assignment does not equate its cohort with the separate 69-nt CPEB3 assays.',
        ['rnagym-zhang-2020-cpeb3-ribozyme'],'human')
    source('zhang2024','Minimal twister sister-like self-cleaving ribozymes in the human genome revealed by deep mutational scanning',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC11620745/',
        'Results: LINE-1 and OR4K15 ribozyme identification and deep mutational scanning',
        'The full/mini LINE-1 and OR4K15 references are identified in human genomic sequence. This is reference-sequence origin; in-vitro cleavage does not assess whole-gene or transcript recovery.',
        ['rnagym-zhang-2024-line1-mini-ribozyme','rnagym-zhang-2024-line1-full-ribozyme','rnagym-zhang-2024-or4k15-ribozyme'],'human')
    source('mcrae','Cryo-EM structure and functional landscape of an RNA polymerase ribozyme',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC10801858/',
        'Introduction; Results: evolved polymerase ribozyme and 5TU/t1 components',
        'The reference is an in-vitro-evolved RNA polymerase ribozyme, including the active 5TU and inactive t1 components. The study does not assign these selected constructs to a natural species.',
        ['rnagym-mcrae-2024-5tu-ribozyme','rnagym-mcrae-2024-t1-ribozyme'],'synthetic')
    source('kobori2016','High-Throughput Mutational Analysis of a Twister Ribozyme',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC5113685/',
        'Main text: Osa-1-4 reference and library design',
        'The 54-nt reference is Oryza sativa Osa-1-4; 48 positions are randomized for mutational analysis. The source names rice, rather than an unresolved environmental twister.',
        ['rnagym-kobori-2016-osa-ribozyme'],'rice')
    source('doud','Accurate Measurement of the Effects of All Amino-Acid Mutations on Influenza Hemagglutinin',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC4926175/',
        'Methods: virus and HA mutant libraries',
        'The target is A/WSN/1933 (H1N1) influenza hemagglutinin. The sequence assignment follows influenza A, not the mammalian culture host used to measure viral growth.',
        ['rnagym-a0a2z5u3z0-9infa-doud-2016'],'taxon-2955291')
    source('zhang2009','Rapid in vivo exploration of a 5S rRNA neutral network',
        'https://zdzlab.einsteinmed.edu/m/publications/19041908.pdf#page=2',
        '§§2.1–2.2: pCV251 and pCV5S',
        'The assayed 5S rRNA reference is Vibrio proteolyticus. The compensatory construct retains E.coli promoters/terminator and is assayed in an E.coli knockout host; the mutated 5S reference is not E.coli.',
        ['evo-ncrna-zhang'],'taxon-671')
    # Remove the temporary layout rows; all real associations now carry their
    # own assay evidence rather than the taxonomy/template task.
    data['coverage_mappings']=[m for m in data['coverage_mappings']if not m['id'].startswith('rna-reference-layout-')]
    for limit in data['source_limits']:
        if limit['evidence_id']=='nabench-complete-methods' and limit['entity_id'].startswith('rnagym-') and limit['field']=='split_manifest':
            limit['detail']='NABench reuse protocol: the paper defines random/position/assay splits but releases no fold assignment or ten-label subset manifest. This omission does not apply to RNAGym’s original zero-shot evaluation, which fits no benchmark training fold.'
    # Replace an old import default with the already audited output definition.
    outputs={o['task_id']:o for o in data['task_outputs']}
    for task in data['tasks']:
        if task['output_description']=='Target prediction':
            output=outputs[task['id']]
            task['output_description']=output['prediction_form']
            c.field('tasks',task['id'],'output_description',output['evidence_id'])
    for row in data['coverage_settings']:
        if row['key']=='sources':
            values=json.loads(row['value_json'])
            values[0]['note']='Original Evo1/Evo2 paper or release use takes priority in shape assignment. Original-paper use and later benchmark participation remain separate source associations.'
            row['value_json']=json.dumps(values,ensure_ascii=False)
    path=ROOT/'data/rna-reference-review.json'
    report=json.loads(path.read_text())
    report.update(reviewed=DATE,decisions=decisions)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
