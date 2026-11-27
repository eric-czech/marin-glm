"""Map original Evo 2 likelihood diagnostics and their exact source species.

These source-defined analyses have no experimental fitness labels. Reference
annotations and genetic-code expectations are not mutational fitness assays.
"""
from pathlib import Path
import copy
import hashlib
import json

from common import Catalogue

ROOT=Path(__file__).resolve().parents[2]
DATE='2026-11-27'
SUPP='https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-026-10176-5/MediaObjects/41586_2026_10176_MOESM1_ESM.pdf'
REV='53f195997257c56c00e5ef8d33a54f5baad143a6'

PROK=[
 ('Escherichia coli','GCF_000005845.2'),('Bacillus subtilis','GCF_000009045.1'),
 ('Synechocystis sp. PCC 6803','GCF_000019485.1'),('Mycobacterium tuberculosis','GCF_002357975.1'),
 ('Bacteroides thetaiotaomicron','GCF_001314975.1'),('Methanococcus maripaludis','GCF_002945325.1'),
 ('Nitrosopumilus maritimus','GCF_000018465.1'),('Acinetobacter baumannii','GCF_001628795.1'),
 ('Enterococcus faecium','GCF_009734005.1'),('Klebsiella pneumoniae','GCF_000968155.1'),
 ('Neisseria gonorrhoeae','GCF_023822665.1'),('Neisseria meningitidis','GCF_015679665.1'),
 ('Pseudomonas aeruginosa','GCF_000626655.2'),('Staphylococcus aureus','GCF_003609855.1'),
 ('Methanocaldococcus jannaschii','GCF_000091665.1'),('Sulfolobus solfataricus','GCF_000968435.2'),
 ('Haloferax volcanii','GCF_010692905.1'),('Thermococcus kodakarensis','GCF_028471865.1'),
 ('Nanoarchaeum equitans','GCF_000008085.1'),('Streptomyces coelicolor','GCF_008931305.1')]
EUK=[
 ('Arabidopsis thaliana','GCF_000001735.4'),('Caenorhabditis elegans','GCA_000002985.3'),
 ('Callithrix jacchus','GCA_011100555.1'),('Chlamydomonas reinhardtii','GCA_000002595.3'),
 ('Drosophila melanogaster','GCF_000001215.4'),('Danio rerio','GCA_000002035.4'),
 ('Homo sapiens','GCF_000001405.40'),('Macaca mulatta','GCF_003339765.1'),
 ('Mus musculus','GCF_000001635.27'),('Nicotiana attenuata','GCA_001879085.1'),
 ('Oryza sativa','GCA_001433935.1'),('Paramecium tetraurelia','GCA_000165425.1'),
 ('Saccharomyces cerevisiae','GCA_000146045.2'),('Thalassiosira pseudonana','GCA_000149405.2'),
 ('Tetrahymena thermophila','GCA_000189635.1'),('Xenopus tropicalis','GCF_000004195.4')]
CODE=[('Arabidopsis thaliana','GCF_000001735.4'),('Homo sapiens','GCF_000001405.40'),
 ('Mycoplasma pneumoniae','GCF_900660465.1'),('Thalassiosira pseudonana','GCA_000149405.2'),
 ('Tetrahymena thermophila','GCA_000189635.1')]
RAMP=[('Homo sapiens','GCF_000001405.40'),('Saccharomyces cerevisiae','GCF_000146045.2'),
 ('Aeropyrum pernix','GCF_000011125.1'),('Escherichia coli','GCF_000005845.2')]


def populate(d):
    c=Catalogue(d)
    def put(table,r,keys=('id',)):return c.put(table,r,keys)
    def evidence(id,section,page,text,source='evo-supp'):
        return c.evidence(id,source,section,text,'paper',SUPP+f'#page={page}' if source=='evo-supp' else c.get('sources',source)['url'])
    def limit(table,id,field,reason,detail,eid):
        put('source_limits',dict(id=id+'-'+field+'-source-limit',entity_table=table,entity_id=id,
            field=field,reason=reason,detail=detail,evidence_id=eid))
    def review(table,id,scope,eids,limitations):
        put('source_reviews',dict(id=id+'-diagnostic-source-review',entity_table=table,entity_id=id,
            reviewed=DATE,scope=scope,evidence_ids_json=json.dumps(eids),limitations=limitations),('entity_table','entity_id'))
    release_sid=c.source('evo2-diagnostic-release-inventory','Evo 2 complete current official release',
        f'https://github.com/ArcInstitute/evo2/tree/{REV}','repository-tree',REV,
        'research/artifacts/final-audit/evo2-diagnostics/tree.json',
        'Complete recursive tree and complete archive inspected; no per-species synthetic-mutation/cohort manifests for Supplement A.3.1–A.3.5 are present.')
    release=c.evidence('evo2-diagnostic-release-scope',release_sid,'Complete repository inventory',
        'Official release has scoring utilities and selected BRCA1, exon-classifier, SAE, generation, gene-completion and later phage-generation examples. It does not contain the original boundary/mutation-preference/genetic-code/codon-ramp processed cohort arrays or the synthetic retrieval evaluation implementation. These six original-paper tasks are paper-audited, not artifact-audited.','documentation')
    for repo,rev in [('savanna','7b819b8609ce0b29deff79358a294b59d8299d07'),('vortex','8b00afebeac745d1f31e7e2788f0e0e39fa47637')]:
        sid=c.source('evo2-diagnostic-'+repo+'-inventory','Evo 2 linked '+repo+' release inventory',
            f'https://github.com/zymrael/{repo}/tree/{rev}','repository-tree',rev,
            'research/artifacts/final-audit/evo2-diagnostics/'+repo+'-tree.json',
            'Complete archive and recursive tree retrieved; targeted search for original mutation/codon/needle diagnostics. Savanna longeval.py is an unrelated text-based evaluation, not the paper’s DNA categorical-Jacobian task.')
        e=c.evidence(sid+'-inspection',sid,'Complete inventory; targeted source search',
            'The source-linked repository contains model training/inference code but no identified original Evo 2 mutation-cohort/score manifests or DNA categorical-Jacobian retrieval harness. Presence of general long-context text evaluation code is not counted as the DNA diagnostic implementation.','documentation')
        c.field('evidence',release,'statement',e,'Additional official linked repository inventory checked before recording artifact limits.')
    boundary=evidence('evo2-boundary-diagnostic-method','Supplement A.3.1; Fig. 2b and Extended Data Fig. 3a, b',11,
        'Twenty prokaryotic and sixteen eukaryotic references. Randomly select 1,024 coding genes/species except Nanoarchaeum equitans (all 536). Mutate every position from 20 bp upstream to 20 bp downstream of the start-codon first base to all three alternate bases. Evo 2 7B scores 8,192 nt contexts centered on the mutation, averaging original/reverse-complement likelihoods. Average delta likelihood over alternate bases and genes at each relative position. Repeat around stop codons. These profiles have no experimental mutation-effect labels.')
    prok=evidence('evo2-prok-mutation-diagnostic-method','Supplement A.3.2; Fig. 2c',12,
        'Twenty named bacterial/archaeal reference assemblies. Per species sample 5,000 CDS positions and 2,000 positions each from rRNA, tRNA, ncRNA and non-annotated/intergenic bases. CDS: three alternate SNVs and 1 bp deletion; noncoding groups:10 bp deletion. Extend flanks after deletion to preserve 8,192 bp context. Use standard codon table for synonymous/missense/nonsense grouping. Compare likelihood changes, not experimental fitness. The main Figure 2 caption identifies Evo 2 7B; the supplement abbreviates this as Evo 7B.')
    euk=evidence('evo2-euk-mutation-diagnostic-method','Supplement A.3.3; Fig. 2d and Extended Data Fig. 3c',12,
        'Sixteen named eukaryotic assemblies. Artificial synonymous/nonsynonymous/premature-stop substitutions and 1 bp CDS frameshift deletions;10 bp deletions in UTRs, introns, intergenic regions and annotated noncoding RNA exons. Species-specific codon tables. Keep 8,192 bp context by extending deletion flanks. Sample up to 200,000 sequences across types and at most 20 mutations per unique region coordinate; summarize median likelihood change by region/mutation type. Primary Figure 2d uses 7B; Extended Data Fig. 3c compares 40B versus 7B across the plotted coding and noncoding classes on the same sequences. Exact per-species/type retained counts are not reported.')
    code=evidence('evo2-genetic-code-diagnostic-method','Supplement A.3.4; Fig. 2e and Extended Data Fig. 3f',13,
        'Supplement lists five species and tests seven replacement codons (TAA, TAG, TGA, AGG, TCA, AGA, TTA), which are not all stop codons under each genetic code. Random CDS/codon positions, pseudogenes excluded; source minimum length threshold 10 and maximum 200,000 sequences/genome. Evo 2 7B contexts 100–8,192 bp; median mutation likelihood changes per codon/species, z-standardized across seven codons. Ciliate recoding replaces TAA/TAG glutamine codons with randomly selected standard glutamine codons. Supplement names Thalassiosira pseudonana as ciliate-code; main Figure 2e instead identifies Paramecium tetraurelia. This taxon/code discrepancy is retained explicitly.')
    code_main=evidence('evo2-genetic-code-main-figure','Main Fig. 2e caption; Extended Data Fig. 3f caption',1,
        'Main Figure 2e reports five species and approximately 4,100 random mutation loci, identifies Mycoplasma pneumoniae and Paramecium tetraurelia, and compares genetic-code-specific mutation likelihoods. Extended Data Fig. 3f describes two ciliate genomes across six context lengths. These descriptions conflict with the supplementary-method attribution of Thalassiosira pseudonana to ciliate nuclear code.',source='evo-paper')
    ramp=evidence('evo2-codon-ramp-diagnostic-method','Supplement A.3.5; Extended Data Fig. 3d, e',13,
        'Four named species: human, yeast, Aeropyrum pernix, E. coli. Use previously calculated tRNA-adaptation-index values to separate synonymous substitutions into increased versus decreased tAI. Average model log-likelihood changes across sampled genes/codon positions; rolling five-codon smoothing. Main Extended Data Fig. 3d additionally depicts tAI along first/last 100 codons after z-normalization. tAI is a genomic/codon-usage proxy, not an experimental protein-fitness target. Exact sampled gene/mutation counts and checkpoint size are not specified in this section.')
    needle=evidence('evo2-needle-diagnostic-method','Supplement A.1.6; Extended Data Fig. 1',8,
        'Uniform-random 100 bp needle and DNA haystack; haystack lengths 512–1,048,576 bp in powers of two. Insert needle at 10–90% context depths by 10% increments and exact query copy at suffix. Retrieval strength is mean matching-position categorical-Jacobian magnitude across 100 needle/query positions; success threshold r ≥ 0.8 chosen by manual inspection. Null validation: eight lengths 512–65,536, ten depths 10–100%, 13 independent shuffles, 1,040 scores; maximum 0.037 and reported P < 0.001 at 0.8. This is a perturbation-based repeated-pattern diagnostic on synthetic DNA, not natural-genome retrieval accuracy.')
    for id,name,definition in [
        ('delta-likelihood','Mutation Δ likelihood','Source-defined change in model sequence likelihood after an artificial mutation; aggregation/context/normalization are protocol-specific. No experimental effect-size label is implied.'),
        ('z-delta-likelihood','Standardized mutation Δ likelihood','Median model likelihood change by tested codon and species, z-score standardized across the seven tested replacement codons.'),
        ('categorical-jacobian-retrieval','Categorical-Jacobian retrieval strength','Mean magnitude of matched-position query-logit changes following needle-token perturbations, as defined in the Evo 2 supplement.'),
        ('retrieval-threshold-success','Retrieval-strength threshold success','Whether categorical-Jacobian retrieval strength reaches the manually selected 0.8 threshold; not sequence exact-match generation accuracy.')]:
        put('metrics',dict(id=id,name=name,definition=definition,direction='descriptive'))
    specs=[
        ('evo-boundary-likelihood','Coding-boundary mutation likelihood','NCBI36-reference boundary mutation panel','Mutation likelihood versus distance from start/stop codon',boundary,PROK+EUK,
         ['translation-start','translation-stop'],['sequence-modeling'], 'delta-likelihood',
         'Relative gene-boundary position; mean across alternate alleles and sampled genes',
         'No fitted readout or supervised test partition. Reference genes and artificial SNVs are randomly sampled within each named assembly; no pretraining species/chromosome exclusion is asserted.'),
        ('evo-prok-mutation-preferences','Prokaryotic region/mutation likelihood','NCBI20-reference prokaryotic mutation panel','Likelihood response by annotated region and mutation class',prok,PROK,
         ['cds','rrna','trna','ncrna','intergenic'],['sequence-modeling'], 'delta-likelihood',
         'Source-defined region/mutation class within species',
         'Random within-reference position draws, stratified by annotation; no fitted head or supervised train/test split. These 20 taxa are reference contexts, not experimentally assayed fitness cohorts.'),
        ('evo-euk-mutation-preferences','Eukaryotic region/mutation likelihood','Ensembl/NCBI16-reference eukaryotic mutation panel','Likelihood response by annotated region and mutation class',euk,EUK,
         ['cds','utr5','utr3','intron','lncrna','ncrna','trna','rrna','intergenic'],['sequence-modeling'], 'delta-likelihood',
         'Median mutation likelihood per region/mutation type, then species-level comparison',
         'Random synthetic mutation sampling within annotated references, capped at 200,000 sequences and 20 mutations per region coordinate. No fitted head, independent experimental labels or demonstrated pretraining exclusion.'),
        ('evo-genetic-code-preferences','Genetic-code-dependent codon likelihood','NCBI genetic-code mutation/recoding panel','Relative likelihood response to tested codon replacements and genome recoding',code,CODE,
         ['cds'],['sequence-modeling','long-context'], 'z-delta-likelihood',
         'Tested replacement codon within species and context/recoding condition',
         'Random coding sequence/codon positions; pseudogenes excluded; source cap 200,000 sequences/genome. Context/recoding variants reuse this diagnostic design; no experimental fitness test or held-out species test.'),
        ('evo-codon-ramp','Synonymous-codon likelihood and tAI','Four-reference tAI/synonymous-codon diagnostic','Position-specific likelihood preference for increased/decreased tAI',ramp,RAMP,
         ['cds'],['sequence-modeling'], 'delta-likelihood',
         'Gene-relative codon position; higher/lower-tAI mutation group; rolling five-codon average',
         'Random genes/codon positions within four reference genomes. No supervised predictor split; tAI values are external annotations/proxies rather than experimental mutation labels.'),
        ('evo-needle-haystack','Repeated-pattern retrieval in synthetic DNA','Uniform-random repeated 100 bp DNA needle/haystack','Long-context dependence of query predictions on an earlier exact pattern',needle,[],
         ['genome'],['long-context','sequence-retrieval','sequence-modeling'], 'categorical-jacobian-retrieval',
         'Synthetic needle/haystack context and needle depth; shuffled-pattern null separately',
         'Synthetic random sequences across context/depth conditions, with a separate shuffled-pattern null. Threshold chosen by manual inspection, not an independent held-out threshold-training split. Natural-genome species/chromosome splits are inapplicable.')]
    taxonomy=Taxonomy(d,c)
    for tid,name,dataset,target,eid,species,features,caps,metric,unit,split in specs:
        statement=c.get('evidence',eid)['statement']
        put('tasks',dict(id=tid,name=name,dataset_name=dataset,target=target,description=statement,
            task_type='synthetic context-dependence diagnostic' if not species else 'annotation-stratified likelihood diagnostic',
            label_basis='Synthetic pattern identity / perturbation control' if not species else 'Reference annotations, codon/genetic-code expectations or tAI; no experimental fitness labels',
            evidence_id=eid,status='paper-audited',
            limitations='Full source-method review; processed mutation IDs, seeds, complete score arrays and source-specific evaluator are not released in the inspected official repository. Counts are source-reported requests/caps or conditions, not independently recounted scored examples.',
            input_description='Synthetic random DNA with repeated 100 bp pattern' if not species else 'Named reference assembly with source-defined synthetic substitutions/deletions and contextual scoring',
            output_description='Source-defined model-response statistic; no measured biological outcome target'))
        c.member(tid,'evo-original',eid,note='Original Evo 2 paper diagnostic; separately classified from experimentally labelled variant-effect assays.')
        for cat in ['model-development','comparative-genomics']+features+caps:
            c.category(tid,cat,eid,'Source-defined input/analysis target; this diagnostic does not independently validate biological function.')
        pid=tid+'-protocol'
        c.protocol(pid,tid,'Original Evo 2 '+name,'zero-shot model-response analysis',
            'Token logits and categorical Jacobian' if not species else 'Reference/alternate contextual sequence likelihood',
            split,unit,eid,metrics=[(metric,unit)],embeddings=False,
            selection='Manually selected retrieval-strength threshold 0.8; shuffled-pattern null validation.' if not species else
                'Source-defined random sampling and annotation filters; no learned downstream classifier.')
        if tid in ['evo-boundary-likelihood','evo-prok-mutation-preferences','evo-euk-mutation-preferences','evo-genetic-code-preferences']:
            c.get('protocols',pid)['model_interface']='Evo 2 7B reference/alternate contextual sequence likelihood'
        if tid=='evo-euk-mutation-preferences':
            c.get('protocols',pid)['notes']='Extended Data Fig. 3c compares the 40B and 7B models across the plotted coding and noncoding classes on the same sequences. The exact per-species/type retained score manifest remains unavailable.'
        c.use(tid,'evo2','evo',eid,pid,provenance='original-paper',note='Original-paper source-method diagnostic, not experimentally labelled fitness prediction.')
        c.output(tid,'diagnostic',eid,'Aggregate response of model likelihood/logits to source-defined perturbations',unit,
            rationale=statement,limitations='The statistical endpoint is explicit. Missing processed score/coordinate artifacts remain source limits; no prediction-label accuracy is invented.')
        if 'cds'in features:
            scope='restricted-target' if features==['cds'] else 'mixed'
            put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope=scope,
                rationale='CDS-only codon substitution/recoding target.' if scope=='restricted-target' else
                    'Mixed annotation-stratified diagnostic; CDS is one of several distinct region classes, not a CDS-only cohort.',evidence_id=eid),('task_id','feature_id'))
        for name_,assembly in species:
            pop,meta=taxonomy.resolve(name_)
            vid=tid+'-'+str(meta['tax_id'])
            put('variants',dict(id=vid,task_id=tid,name=name_+' / '+assembly,evidence_id=eid,
                context='Source-named reference assembly; current taxonomic name: '+meta['current_scientific_name']['name'],
                input_length='8,192 nt' if tid in ['evo-boundary-likelihood','evo-prok-mutation-preferences','evo-euk-mutation-preferences'] else
                    '100–8,192 bp (context variants)' if tid=='evo-genetic-code-preferences' else 'Not specified in the inspected tAI section',
                dataset_revision=assembly,target_count=None,target_unit=None,
                notes='Artificial source mutations are not experimental fitness measurements.'))
            taxonomy.link(tid,pop,meta,eid,vid)
            upstream(c,d,tid,vid,name_,assembly,eid)
        if not species:
            c.population(tid,'synthetic',eid,'Uniform-random synthetic DNA; no biological source species.')
        limit('tasks',tid,'processed_mutation_manifest','not-released',
            'Complete pinned official release does not provide the paper-specific mutation coordinates, sampling seeds, full score arrays or this diagnostic evaluator.',release)
        if tid in ['evo-prok-mutation-preferences','evo-euk-mutation-preferences']:
            limit('tasks',tid,'species_by_region_counts','not-released',
                'Source reports annotation classes and reference taxa but no released retained-count/coordinate matrix for each species×region combination. Task-level species associations do not independently verify every ncRNA class in every named reference.',release)
        review('tasks',tid,'Complete original supplementary-method section and linked main/extended-data captions; exact species/assembly list; official code-release inventory.',
            [eid,release], 'No raw score cohort or experimental mutation-effect labels are supplied for independent artifact validation.')
        review('protocols',pid,'Source-specific sampling, perturbation, scoring and aggregation; no generic model-wide split inherited.',
            [eid,release], 'Random within-genome diagnostic sampling is not a supervised train/test or unseen-species split.')
        c.field('tasks',tid,'target',eid)
        c.field('protocols',pid,'split_rule',eid)
    # Source-reported sample plans and caps are explicit units, not totals made
    # by multiplying every requested draw across possibly overlapping labels.
    c.count('evo-boundary-likelihood',36,'reference species',boundary)
    c.count('evo-boundary-likelihood',1024,'requested coding genes per species',boundary,qualifier='Except Nanoarchaeum equitans; random draw request, not a held-out gene count.')
    c.count('evo-boundary-likelihood',536,'Nanoarchaeum coding genes',boundary,qualifier='All protein-coding genes of the source reference, as reported by the supplement.')
    c.count('evo-prok-mutation-preferences',20,'reference species',prok)
    c.count('evo-prok-mutation-preferences',5000,'sampled CDS positions per species',prok)
    for target in ['rRNA','tRNA','ncRNA','intergenic']:
        c.count('evo-prok-mutation-preferences',2000,'sampled positions per species',prok,split=target)
    c.count('evo-euk-mutation-preferences',16,'reference species',euk)
    c.count('evo-euk-mutation-preferences',200000,'sequence-sampling cap',euk,qualifier='Source says up to 200,000 across sequence types; not a measured total or unambiguous per-species retained count.')
    c.count('evo-euk-mutation-preferences',20,'mutation cap per unique region coordinate',euk)
    c.count('evo-genetic-code-preferences',5,'source-reported species',code,qualifier='Taxon identity differs between main figure and supplement; alternative source claims are recorded as variants, not six confirmed assay cohorts.')
    c.count('evo-genetic-code-preferences',7,'tested replacement codons',code)
    c.count('evo-genetic-code-preferences',200000,'sequence-sampling cap per genome',code)
    c.count('evo-genetic-code-preferences',4100,'approximately sampled mutation loci',code_main,qualifier='Main figure caption approximation; not substituted for the supplementary sampling cap.')
    c.count('evo-codon-ramp',4,'reference species',ramp)
    c.count('evo-needle-haystack',100,'needle/query base pairs',needle)
    c.count('evo-needle-haystack',1040,'shuffled-pattern null scores',needle,split='null validation',qualifier='8 lengths×10 depths×13 shuffles; not independent natural-genome examples.')
    for power in range(9,21):
        n=2**power
        put('variants',dict(id='evo-needle-haystack-context-'+str(n),task_id='evo-needle-haystack',
            name=f'{n:,}bp random haystack',evidence_id=needle,context='Nine main needle depths:10% through 90% at 10% increments; exact query copy at suffix.',
            input_length=f'{n:,}bp haystack plus source-defined inserted needle/query',dataset_revision='Original Evo 2 Supplement A.1.6',
            target_count=None,target_unit=None,notes='The separate shuffled null includes 100% depth and only lengths through 65,536 bp. Main-trial replicate count is not specified.'))
    put('protocol_metrics',dict(protocol_id='evo-needle-haystack-protocol',metric_id='retrieval-threshold-success',
        evidence_id=needle,aggregation='Binary success at strength ≥0.8 per source-defined length/depth condition.',is_primary=False),
        ('protocol_id','metric_id'))
    put('variants',dict(id='evo-genetic-code-standard-recoding',task_id='evo-genetic-code-preferences',
        name='Ciliate-code sequence recoded to standard glutamine codons',evidence_id=code,
        context='All source-called TAA/TAG glutamine codons replaced by randomly selected standard-code glutamine codons; original versus recoded context compared.',
        input_length='100–8,192 bp; extended-data caption reports six context lengths',
        dataset_revision='Original Evo2 Supplement A.3.4',target_count=7,target_unit='replacement codons',
        notes='Supplementary source includes the disputed Thalassiosira identity; the main figure instead names Paramecium. No exact processed sequence/recoding manifest is released.'))
    # Resolve the genetic-code discrepancy rather than treating a diatom as a
    # ciliate or silently replacing a source-named organism.
    pop,meta=taxonomy.resolve('Paramecium tetraurelia')
    vid='evo-genetic-code-preferences-main-figure-paramecium'
    put('variants',dict(id=vid,task_id='evo-genetic-code-preferences',name='Main-figure ciliate assignment: Paramecium tetraurelia',
        evidence_id=code_main,context='Alternative source identity: main Fig. 2e versus supplementA.3.4 Thalassiosira entry.',
        input_length='Source-specific context variants',dataset_revision=None,target_count=None,target_unit=None,
        notes='Main figure identifies Paramecium; this does not independently establish which processed mutation cohort generated the figure.'))
    taxonomy.link('evo-genetic-code-preferences',pop,meta,code_main,vid,
        note='Main-figure target identity; supplementary-method taxon assignment conflicts.')
    diatom=taxonomy.meta('Thalassiosira pseudonana')
    tax_e=taxonomy.evidence('Thalassiosira pseudonana',diatom)
    put('findings',dict(id='evo-genetic-code-taxon-conflict',task_id='evo-genetic-code-preferences',evaluation_id='evo-original',
        severity='discrepancy',description='Supplement A.3.4 names the diatom Thalassiosira pseudonana as ciliate-code, whereas main Fig. 2e names Paramecium tetraurelia. NCBI assigns T. pseudonana standard nuclear code 1, and Paramecium/Tetrahymena ciliate nuclear code 6. Both source identity claims remain explicit; the supplement’s label is not used as taxonomy.',evidence_id=tax_e))
    limit('tasks','evo-genetic-code-preferences','species_identity','conflicting',
        'Main Fig. 2e identifies Paramecium tetraurelia; supplementary A.3.4 identifies Thalassiosira pseudonana and calls it ciliate-code. The released processed score manifest does not resolve the discrepancy.',code_main)
    figure_sid=c.source('evo2-genetic-code-figure-source','Evo 2 Extended Data Fig. 3f',
        'https://www.nature.com/articles/s41586-026-10176-5/figures/9','figure','Nature 2026',
        'research/artifacts/final-audit/evo2-review/fig9.jpg',
        'Original published high-resolution image visually inspected, including taxon and context-length labels.')
    figure=c.evidence('evo2-genetic-code-figure-contexts',figure_sid,'Panel f: organism names and horizontal axes',
        'The actual figure names Paramecium tetraurelia and Tetrahymena thermophila and labels six context lengths: 50, 100, 500, 1,000, 4,000 and 8,192 bp. This supplies exact plotted contexts, whereas A.3.4 states a 100–8,192 bp range.','paper')
    for length in [50,100,500,1000,4000,8192]:
        put('variants',dict(id='evo-genetic-code-context-'+str(length),task_id='evo-genetic-code-preferences',
            name=f'{length:,} bp plotted ciliate context',evidence_id=figure,
            context='Extended Data Fig. 3f; original versus standard-code recoded Paramecium/Tetrahymena contexts.',
            input_length=f'{length:,} bp',dataset_revision='Published Extended Data Fig. 3f',target_count=7,target_unit='tested replacement codons',
            notes='The figure’s 50-bp condition is absent from the A.3.4 stated minimum of 100 bp; no intermediate lengths are inferred.'))
    limit('tasks','evo-genetic-code-preferences','context_range','conflicting',
        'Extended Data Fig. 3f explicitly plots 50 bp as the shortest context, while A.3.4 states 100–8,192 bp. Exact plotted conditions are preserved separately.',figure)
    for species in ['Paramecium tetraurelia','Tetrahymena thermophila']:
        te=taxonomy.evidence(species,taxonomy.meta(species))
        c.field('findings','evo-genetic-code-taxon-conflict','description',te,
            'NCBI primary nuclear genetic-code assignment for this named ciliate.')
    review('tasks','evo-genetic-code-preferences',
        'Full supplementary method and main/extended-data captions; exact source identity conflict; NCBI taxonomy and nuclear genetic-code metadata; complete official release inventory.',
        [code,code_main,figure,tax_e,'evo2-taxonomy-5888-classification','evo2-taxonomy-5911-classification',release],
        'The sources disagree on one target organism; its processed mutation cohort is not released. Neither source identity is silently substituted for the other.')
    limit('tasks','evo-codon-ramp','checkpoint','not-reported',
        'The tAI method/caption does not specify a parameter-size/checkpoint for the likelihood-ramp readout.',ramp)
    limit('tasks','evo-needle-haystack','main_trial_replicates','not-reported',
        'The 1040 null-score construction is explicit; main-grid trial count/seed manifest is not reported.',needle)
    # Each of these exact notes is removed only after its named species has an
    # actual task and a resolved taxonomy mapping above.
    if all(any(m['task_id']=='evo-boundary-likelihood' and m['population_id']==taxonomy.resolve(name)[0]
        for m in d['coverage_mappings']) for name,_ in PROK+EUK):
        d['coverage_notes']=[r for r in d['coverage_notes'] if r['id'] not in ['known-'+str(i)for i in range(6)]]
    d['task_categories'].sort(key=lambda r:(r['task_id'],r['category_id'],r['relation']))


def upstream(c,d,task,variant,name,assembly,evidence):
    sid='evo2-diagnostic-reference-'+assembly
    url='https://www.ncbi.nlm.nih.gov/datasets/genome/'+assembly+'/'
    c.source(sid,name+' reference assembly',url,'reference-assembly',assembly,
        notes='Exact accession named by the original Evo 2 supplementary method. Upstream reference, not a released processed mutation/scoring cohort; sequences not independently downloaded in this diagnostic audit.')
    c.put('data_resources',dict(id=sid,source_id=sid,title=name+' / '+assembly,kind='dataset',host='other',url=url,
        revision=assembly,availability='public',evidence_id=evidence,
        notes='Upstream reference assembly; artificial mutation IDs and source scoring rows are not released here.'))
    c.put('task_resources',dict(task_id=task,resource_id=sid,relation='upstream-data',variant_id=variant,evidence_id=evidence,
        note='Source-named input reference, not an evaluation split manifest.'),('task_id','resource_id','relation'))
    c.put('evaluation_resources',dict(evaluation_id='evo-original',resource_id=sid,relation='upstream-data',evidence_id=evidence,
        note='Input reference for original model-response diagnostics.'),('evaluation_id','resource_id','relation'))


class Taxonomy:
    """Use cached NCBI lineage/code records; every named species stays resolved."""
    def __init__(self,d,c):
        self.d=d;self.c=c
        self.records={}
        self.queries={}
        for file in (ROOT/'research/artifacts/final-audit/taxonomy').glob('*.json'):
            query=file.stem.replace('_',' ')
            meta=json.loads(file.read_text())['reports'][0]['taxonomy']
            self.records[query]=meta
            self.queries[meta['tax_id']]=query

    def meta(self,name):
        return self.records[name]

    def evidence(self,name,meta):
        tid=meta['tax_id'];sid='evo2-taxonomy-'+str(tid)
        path='research/artifacts/final-audit/taxonomy/'+self.queries[tid].replace(' ','_')+'.json'
        url='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(tid)
        self.c.source(sid,'NCBI taxonomy: '+meta['current_scientific_name']['name'],url,'taxonomy',DATE,path)
        cls=meta['classification'];code=meta.get('genetic_code',{}).get('primary')
        return self.c.evidence(sid+'-classification',sid,'NCBI Datasets taxonomy report:classification, parents, primary genetic code',
            'NCBI taxon'+str(tid)+':'+meta['current_scientific_name']['name']+'; classification '+json.dumps(cls,ensure_ascii=False)+
            '; primary genetic code '+json.dumps(code)+'. Historical source names are preserved in task variants.','documentation')

    def resolve(self,name):
        m=self.meta(name);tid=m['tax_id'];cls=m['classification'];eid=self.evidence(name,m)
        pop=next((p for p in self.d['populations'] if p.get('ncbi_taxid')==tid and p['rank'].lower()=='species'),None)
        clade=self.clade(m)
        if pop is None:
            pid='taxon-'+str(tid)
            self.c.put('populations',dict(id=pid,name=m['current_scientific_name']['name'],rank='species',
                parent_id=self.c.get('coverage_nodes',clade)['population_id'],ncbi_taxid=tid,
                notes='Current NCBI taxonomy; source synonym and exact reference accession retained in linked task variants.'))
        else:pid=pop['id']
        return pid,m

    def clade(self,m):
        cls=m['classification'];dom=cls['domain']['name'];ph=cls.get('phylum',{});cl=cls.get('class',{})
        if dom in ['Bacteria','Archaea']:
            id=ph['name'].lower();parent=dom.lower()
            if not any(n['id']==id for n in self.d['coverage_nodes']):
                self.node(id,parent,ph['name'],ph['name'],'Phylum',ph['id'])
            self.clade_row(id,dom,dom.lower(),ph['name'])
            return id
        if cl.get('id')==8292:
            self.node('amphibia','tetrapods','Amphibians','Amphibia','Class',8292)
            self.clade_row('amphibia','Animalia','animals','Amphibia')
            return 'amphibia'
        if cl.get('id')==40674:return 'mammalia'
        if ph.get('name')=='Chordata':return 'teleostei'
        if ph.get('name')=='Arthropoda':return 'insecta'
        if ph.get('name')=='Nematoda':return 'nematoda'
        if ph.get('name')=='Ciliophora':return 'alveolata'
        if ph.get('name')=='Bacillariophyta':return 'stramenopiles'
        if ph.get('name')=='Chlorophyta':return 'chlorophyta'
        if ph.get('name')=='Ascomycota':return 'saccharomycotina'
        if m['tax_id']==4530:return 'poaceae'
        if m['tax_id']in[3702,49451]:return 'eudicots'
        raise ValueError('Explicit Evo 2 diagnostic clade required: '+m['current_scientific_name']['name'])

    def node(self,id,parent,label,scientific,rank,taxid):
        self.c.put('populations',dict(id=id,name=scientific,rank=rank.lower(),parent_id=self.c.get('coverage_nodes',parent)['population_id'],
            ncbi_taxid=taxid,notes='NCBI taxonomic lineage; display node does not imply comprehensive evaluation coverage.'))
        self.c.put('coverage_nodes',dict(id=id,parent_id=parent,population_id=id,label=label,scientific=scientific,
            rank=rank,note='',section='cellular',jump=None,
            sources_json=json.dumps(['https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(taxid)])))

    def path(self,node):
        nodes={n['id']:n for n in self.d['coverage_nodes']};out=[]
        while node:
            out.append(node);node=nodes[node]['parent_id']
        return list(reversed(out))

    def clade_row(self,id,group_label,group,label):
        if any(r['id']=='clade:'+id for r in self.d['coverage_rows']):return
        path=self.path(id);nodes={n['id']:n for n in self.d['coverage_nodes']}
        meta=dict(id=id,label=label,note='Named reference genomes in original Evo 2 likelihood diagnostics; experimental fitness coverage is separate.',
            group=group,groupLabel=group_label,common='',node=id,path=path[1:],lineageLabel=' → '.join(nodes[n]['label']for n in path[1:]),
            displayParent=id,placementStatus=False,displayPath=path,displayLineage=' → '.join(nodes[n]['label']for n in path),displayLabel=label)
        self.c.put('coverage_rows',dict(id='clade:'+id,view='clade',row_key=id,node_id=id,population_ids_json='[]',metadata_json=json.dumps(meta,ensure_ascii=False)))

    def link(self,task,pop,m,eid,variant,note='Exact species/reference named by source; model-response diagnostic, not experimental fitness labels.'):
        clade=self.clade(m)
        taxeid=self.evidence(self.queries[m['tax_id']],m)
        self.c.put('task_populations',dict(task_id=task,population_id=pop,variant_id=variant,
            relation='sequence-origin',coverage=note,evidence_id=eid),('task_id','population_id','relation'))
        if not any(r['id']=='clade:'+clade for r in self.d['coverage_rows']):
            group='other-euk';label=self.c.get('coverage_nodes',clade)['label']
            self.clade_row(clade,'Eukaryota',group,label)
        # Existing named species keep their established default/all-species rows.
        previous=next((x for x in self.d['coverage_mappings']if x['population_id']==pop),None)
        if previous and not previous['clade_row'].endswith('-unresolved'):
            x=copy.deepcopy(previous);x.update(id=task+'-mapping-'+pop,task_id=task,evidence_id=eid,
                supporting_json=json.dumps([eid,taxeid]),basis='Exact source species and NCBI lineage')
            meta=json.loads(x['metadata_json']);meta.update(basis='Exact source species and NCBI lineage',url=self.c.get('evidence',eid)['url'])
            x['metadata_json']=json.dumps(meta,ensure_ascii=False);self.c.put('coverage_mappings',x);return
        cr=self.c.get('coverage_rows','clade:'+clade);cm=json.loads(cr['metadata_json'])
        taxid=m['tax_id'];name=m['current_scientific_name']['name'];common=m.get('curator_common_name','')
        # Individual breakout where an established model system has distinct
        # diagnostic coverage; remaining named species share a resolved clade row.
        breakout=taxid in [8364,9544,5888,5911,35128,1773,1902,818,2246,39152]
        specieskey=clade+'-sp-'+str(taxid) if breakout else clade+'-other'
        allkey=clade+'-sp-'+str(taxid)
        for view,key,individual in [('species',specieskey,breakout),('allSpecies',allkey,True)]:
            rid=view+':'+key
            old=next((r for r in self.d['coverage_rows']if r['id']==rid),None)
            members=set(json.loads(old['metadata_json']).get('members',[])if old else[]);members.add(name)
            pops=set(json.loads(old['population_ids_json'])if old else[]);pops.add(pop)
            meta=dict(id=key,label=name if individual else 'Other named species',common=common if individual else '',
                note='Source-defined original Evo 2 likelihood diagnostics; named species, not an unresolved taxon.',
                group=cm['group'],groupLabel=cm['groupLabel'],clade=clade,cladeLabel=cm['label'],kind='species'if individual else'other',
                members=sorted(members),node=clade,path=cm['path'],lineageLabel=cm['lineageLabel'],
                displayParent=clade,placementStatus=False,displayPath=cm['displayPath'],displayLineage=cm['displayLineage'],
                displayLabel=name if individual else'Other named species')
            self.c.put('coverage_rows',dict(id=rid,view=view,row_key=key,node_id=clade,population_ids_json=json.dumps(sorted(pops)),metadata_json=json.dumps(meta,ensure_ascii=False)))
        pops=set(json.loads(cr['population_ids_json']));pops.add(pop);cr['population_ids_json']=json.dumps(sorted(pops))
        self.c.put('coverage_mappings',dict(id=task+'-mapping-'+pop,task_id=task,population_id=pop,
            basis='Exact source species and NCBI lineage',evidence_id=eid,supporting_json=json.dumps([eid,taxeid]),
            clade_row='clade:'+clade,species_row='species:'+specieskey,all_species_row='allSpecies:'+allkey,
            metadata_json=json.dumps(dict(row=specieskey,name=name,basis='Exact source species and NCBI lineage',
                url=self.c.get('evidence',eid)['url'],taxonomy='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(taxid),
                species=name,speciesId=taxid,clade=clade,allSpeciesRow=allkey),ensure_ascii=False)))
