"""Attach measured counts to the actual immutable dataset file, never a paper total."""
from pathlib import Path
import json

def populate(c):
    root=Path(__file__).resolve().parents[2]
    inspections=json.loads((root/'data/artifact-inspections.json').read_text())
    c.source('encode-glossary','ENCODE glossary: cCRE subtypes','https://www.encodeproject.org/glossary/','documentation','Inspected 2026-11-25')
    ontology=c.ev('encode-ccre-ontology','encode-glossary','candidate Cis-Regulatory Element subtypes: PLS, pELS, dELS','PLS is promoter-like; pELS/dELS are enhancer-like signatures. These are biochemical annotation classes, not universal experimental validation.','documentation')
    for i,row in enumerate(inspections):
        if 'error' in row:continue
        repo,path=row['repo'],row['path']
        sid='artifact-'+str(i+1).zfill(3)
        url=f'https://huggingface.co/datasets/{repo}/blob/{row["revision"]}/{path}'
        c.source(sid,repo+': '+path,url,'dataset-file',row['revision'],notes='Inspected without model execution. SHA-256 and derived statistics in data/artifact-inspections.json; raw files are not redistributed.')
        source=c.rows['sources'][-1];source['sha256']=row['sha256']
        ev=c.ev(sid+'-inspection',sid,'Pinned file; row count, column schema, labels and sequence length where available',f'{row["rows"]:,} rows; columns: '+', '.join(row['columns'])+'.','data',url)
        tasks=[];protocol=None;variant=None;split=path.split('/')[-1].split('.')[0].split('-')[0]
        if repo=='InstaDeepAI/nucleotide_transformer_downstream_tasks_revised':
            t='nt-revised-'+path.split('/')[0];tasks=[t];variant=t+'-release'
        elif repo=='GenerTeam/gener-tasks':tasks=['gener-'+path.split('/')[0]]
        elif repo=='GenerTeam/DeepSTARR-enhancer-activity':tasks=['deepstarr-dev','deepstarr-hk']
        elif repo=='biomap-research/DeepD':
            tasks=['gue-H3'];protocol='deepd-h3-example';split=path.split('/')[-1].split('_')[-1].split('.')[0]
        elif repo=='songlab/TraitGym':
            tasks=['traitgym-mendelian' if path.startswith('mendelian') else 'traitgym-complex'];variant=tasks[0]+'-matched9';split='test'
            t=tasks[0]
            mapping={'5_prime_UTR_variant':'utr5','3_prime_UTR_variant':'utr3','intron_variant':'intron','intergenic_variant':'intergenic','non_coding_transcript_exon_variant':'exon','PLS':'promoter','pELS':'enhancer','dELS':'enhancer'}
            present=set()
            for consequence,n in row.get('values',{}).get('consequence',{}).items():
                v=t+'-consequence-'+consequence.lower()
                c.variant(t,v,consequence,ev,revision=row['revision'],context='Observed released consequence/annotation stratum. Flanks remain distinct from elements.')
                c.count(t,n,'variant rows',ev,split='matched-9 test stratum',variant=v,method='measured',qualifier='Rows carrying this exact released consequence label; subsets are not independent tasks.')
                category=mapping.get(consequence)
                if category and category not in present:
                    c.add('task_categories',task_id=t,category_id=category,relation='subset',rationale='This region is actually present in the pinned test file consequence column. Only exact PLS/pELS/dELS labels map to elements; flank categories are not silently treated as element interiors.',evidence_id=ev,attribution='curatorial')
                    c.field('tasks',t,'classification:'+category,ontology if consequence in ('PLS','pELS','dELS') else ev,'Ontology interpretation is separate from observed dataset membership.')
                    present.add(category)
            for label,n in row.get('values',{}).get('label',{}).items():
                c.count(t,n,'variant rows',ev,split='positive' if label=='True' else 'control',variant=variant,method='measured',qualifier='Released boolean label; not an independently established clinical truth for matched controls.')
        elif repo=='tattabio/ec_classification_dna':tasks=['dgeb-ec_dna_classification']
        elif repo=='macwiatrak/bacbench-essential-genes-dna':tasks=['bacbench-essential']
        elif repo=='Nugkta/bgc-bench':
            if path.startswith('splits/t1ml_'):tasks=['bgc-coarse']
            elif path.startswith('splits/t2ml_'):tasks=['bgc-fine']
            elif path.startswith('splits/t3_'):tasks=['bgc-retrieval']
            elif path.startswith('splits/t1_'):tasks=['bgc-chem']
            elif path.startswith('splits/t5_'):tasks=['bgc-adomain']
            # The chemical-property recipe uses t1 split files, with its own eligibility filter.
            elif path=='tasks/chem_descriptors.csv':tasks=['bgc-chem']
            elif path=='tasks/adomain_instances.csv':tasks=['bgc-adomain']
            elif path=='tasks/t2ml_labels.csv':tasks=['bgc-fine']
            if tasks:
                variant='bgc-file-'+str(i+1)
                c.variant(tasks[0],variant,path,ev,revision=row['revision'],notes='File rows can precede scorer eligibility filtering. Total split-file rows are not automatically final scored examples.')
                split='artifact rows'
        for t in tasks:
            if t not in c.ids['tasks']:raise ValueError('Unknown artifact task '+t)
            unit='genomes' if repo=='macwiatrak/bacbench-essential-genes-dna' else 'rows'
            c.count(t,row['rows'],unit,ev,split=split,qualifier='Measured pinned artifact rows; not necessarily post-filter scored examples.',method='measured',variant=variant,protocol=protocol)
            if 'gene_count'in row:c.count(t,row['gene_count'],'gene labels',ev,split=split,qualifier='Flattened genome → contig → gene essentiality labels.',method='measured')
            c.field('tasks',t,'dataset_name',ev,'Artifact membership; does not certify every protocol or biological label.')
            if 'length'in row:
                c.field('tasks',t,'input_description',ev,f'Measured length range {row["length"]["min"]}–{row["length"]["max"]} bases.')
            for name,n in row.get('values',{}).get('split',{}).items():
                c.count(t,n,'split-file rows',ev,split=name,qualifier='Before task scorer eligibility filtering.',method='measured',variant=variant)
        if repo=='Nugkta/bgc-bench' and path=='splits/t5_bgc_grouped_5fold.csv':
            c.finding('bgc-adomain','The pinned five-fold split file has 2,315 rows (463/fold), while the domain-instance table has 2,504 rows. The scorer further restricts labels/classes; split-file rows must not be presented as final scored single-label instances.',ev,severity='discrepancy',suite='bgc')
    # Preserve evidence for every category assignment, including its curatorial status.
    for row in c.rows['task_categories']:
        c.field('tasks',row['task_id'],'classification:'+row['category_id'],row['evidence_id'],row['rationale'])
