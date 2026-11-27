"""Reconcile DNA Foundation Benchmark with its full paper and deposited archive."""
import json
from common import Catalogue, ROOT

REV='3f4c81ce066f3c47422a83466b085aac1a6be902'
HFREV='1a3a47ef2de823de858a2e26bad510fab513648d'
REPO='https://github.com/ChongWuLab/dna_foundation_benchmark'
HF='https://huggingface.co/datasets/hfeng3/dna_foundation_benchmark_dataset'
PAPER='https://www.nature.com/articles/s41467-025-65823-8'
SUPP='https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-025-65823-8/MediaObjects/41467_2025_65823_MOESM1_ESM.pdf'


def populate(d):
    c=Catalogue(d)
    inspection=json.loads((ROOT/'data/dnafoundation-artifact-inspections.json').read_text())
    files={r['path']:r for r in inspection['files']}
    c.source('dnafoundation-fulltext','DNA Foundation Benchmark: complete primary paper',PAPER,
        version='Nature Communications 16, 10780 (2025); DOI 10.1038/s41467-025-65823-8',
        path='research/artifacts/final-audit/dnafoundation-paper.xml')
    c.source('dnafoundation-supplement','DNA Foundation Benchmark supplementary methods and dataset mapping',SUPP,
        version='Published Supplementary Information, 11 pages',path='research/artifacts/final-audit/41467_2025_65823_MOESM1_ESM.pdf')
    c.source('dnafoundation-release','DNA Foundation Benchmark processed data archive',HF+f'/blob/{HFREV}/data_processed.zip',
        kind='dataset',version=HFREV,path='research/artifacts/final-audit/dnafoundation-data.zip')
    c.source('dnafoundation-code','DNA Foundation Benchmark evaluation implementation',REPO+f'/tree/{REV}',
        kind='repository',version=REV)
    method=c.evidence('dnafoundation-classification-method','dnafoundation-fulltext','Methods: Sequence classification benchmark; Fig. 1',
        'The 57 datasets comprise 52 binary and five multiclass problems. Final-layer embeddings are frozen; mean, maximum or summary-token pooling is followed by a fitted classifier. This is supervised prediction from frozen representations, not a zero-shot prediction protocol. Original splits are kept where clearly defined; DNABERT-2/NT-derived datasets are reshuffled into a stratified random 70:30 partition. The paper specifies fivefold classifier tuning; the released scripts use fourfold tuning.',url=PAPER+'#Sec14')
    identity=c.evidence('dnafoundation-dataset-identity','dnafoundation-supplement','Supplementary Notes 1–2, pp. 1–4',
        'The supplement maps all 57 renamed datasets to their original sources: seven Genomic Benchmarks datasets, 33 DNABERT-2/NT datasets, eight iPro-WAEL promoter datasets, six Deep4mC datasets, two iDNA-ABF datasets and one iDHS-EL dataset. Labels and dataset variants are not equated across releases solely because their display names resemble one another.',url=SUPP+'#page=1')
    artifact=c.evidence('dnafoundation-complete-archive','dnafoundation-release','Complete ZIP member scan; data/dnafoundation-artifact-inspections.json',
        'The deposited 1,110,455,538-byte archive contains 57 pairs of classification train/test CSVs, eight QTL VCFs, one pathogenic-variant table and TAD sequences/coordinates. All classification rows, labels, sequence lengths and exact train/test sequence intersections were counted. Whole-archive and per-file hashes are retained. Human individual genomes and expression targets are not included.','data')
    code=c.evidence('dnafoundation-classification-code','dnafoundation-code','job_scripts/classify_cadph.py: random_forest_classification and metric calculations',
        'GridSearchCV uses cv=4, optimizing AUROC for binary tasks and accuracy for multiclass tasks. This differs from the paper’s fivefold statement. Random forest is the main readout; naïve Bayes and elastic-net logistic regression are alternative fitted readouts. The supplied train/test embeddings are loaded without constructing chromosome partitions.','code',REPO+f'/blob/{REV}/job_scripts/classify_cadph.py#L49-L90')
    c.resource('dnafoundation-data','dnafoundation-release','DNA Foundation Benchmark processed archive','dataset','huggingface',
        HF+f'/blob/{HFREV}/data_processed.zip',artifact,HFREV,notes='Archive member paths and measured counts are linked to each release variant. Includes classification, QTL, pathogenic variants and TAD data; excludes protected GTEx individuals.')
    c.resource('dnafoundation-code','dnafoundation-code','DNA Foundation Benchmark code','evaluation-code','github',
        REPO+f'/tree/{REV}',code,REV,notes='Dataset-specific workflows and model interfaces; some scripts retain server-specific paths.')
    c.collection_resource('dna-foundation','dnafoundation-data',artifact)
    c.collection_resource('dna-foundation','dnafoundation-code',code,'evaluation-code')
    direct={
        'enhancers/enhancer':'nt-original-enhancers',
        'enhancers/enhancer_strength':'nt-original-enhancers_types',
        'splice/donors':'nt-original-splice_sites_donors',
        'splice/acceptors':'nt-original-splice_sites_acceptors',
        'splice/splice_site_type_NT':'nt-original-splice_sites_all',
        'splice/splice_site_type_DNABERT':'geneb-leannmlindsey-gue-splice-reconstructed',
        'virus/covid_variants':'geneb-leannmlindsey-gue-virus-covid',
        'genomic_benchmark/enhancer_ensembl':'gb-human_enhancers_ensembl',
        'genomic_benchmark/enhancer_cohn':'gb-human_enhancers_cohn',
        'genomic_benchmark/promoter_notata_251bps':'gb-human_nontata_promoters',
        'genomic_benchmark/open_chromatin_region':'gb-human_ocr_ensembl',
        'genomic_benchmark/coding':'gb-demo_coding_vs_intergenomic_seqs',
        'genomic_benchmark/regulatory_region_type':'gb-human_ensembl_regulatory',
        'genomic_benchmark/human_vs_worm':'gb-demo_human_or_worm'}
    for name in ['H3','H3K14ac','H3K36me3','H3K4me1','H3K4me2','H3K4me3','H3K79me3','H3K9ac','H4','H4ac']:
        direct['EMP/Yeast_'+name]='geneb-leannmlindsey-gue-emp-'+name.lower()
    for n in range(1,6):
        direct['tf/Human_TFBS_'+str(n)]='geneb-leannmlindsey-gue-human-tf-'+str(n-1)
        direct['mouse/mouse_TFBS_'+str(n)]='geneb-leannmlindsey-gue-mouse-'+str(n-1)
    for size,upstream in [('70bps','core'),('300bps','300')]:
        for label,slug in [('all','all'),('tata','tata'),('notata','notata')]:
            direct['prom/promoter_'+label+'_'+size]='geneb-leannmlindsey-gue-prom-'+upstream+'-'+slug
    for name in ['A.thaliana','C.elegans','D.melanogaster','E.coli','G.pickeringii','G.subterraneus']:
        direct['deep4mc/'+name+'_4mC']='geneb-deep4mc-'+name.lower()+'-4mc'
    for name in ['5mC','6mA']:direct['iDNA_ABF/'+name]='geneb-idna-abf-'+name.lower()
    for name in ['Arabidopsis_NonTATA','Arabidopsis_TATA','B_amyloliquefaciens','R_capsulatus','GM12878','HUVEC','Hela-S3','NHEK']:
        direct['iPro-WAEL/Promoter_'+name]='geneb-ipro-wael-promoter-'+name.lower().replace('_','-')
    direct['iDHS-EL/DNase_I']='geneb-idhs-el-dnase-i'
    dirs={r['path'][5:-10] for r in inspection['files'] if r['path'].endswith('/train.csv')}
    assert dirs==set(direct),(dirs-set(direct),set(direct)-dirs)
    assert len(dirs)==57
    for directory,tid in direct.items():
        c.member(tid,'dna-foundation',identity,note='Same source dataset and biological target; the DNA Foundation processed partition is a separate release variant and readout.')
        vid='dnafoundation-'+directory.replace('/','-').lower()
        pair=[files['data/'+directory+'/'+split+'.csv'] for split in ['train','test']]
        sizes=sorted({int(k) for r in pair for k in r['sequence_lengths']})
        labels=sorted({k for r in pair for k in r['labels']})
        overlap=inspection['exact_sequence_overlap']['data/'+directory]
        c.put('variants',dict(id=vid,task_id=tid,name='DNA Foundation / '+directory,dataset_revision=HFREV,
            context='Processed source dataset with this study’s released partitions; labels '+', '.join(labels)+'.',
            input_length=f'{min(sizes)}–{max(sizes)} nt (complete release scan)',target_count=len(labels),target_unit='classes',
            notes=f'Archive member data/{directory}/. {overlap} distinct exact sequences occur in both train and test. This is a sequence-only check, not a locus or homology leakage audit.',evidence_id=artifact))
        for split,r in zip(['train','test'],pair):
            c.count(tid,r['rows'],'sequence rows',artifact,split=split,variant=vid,method='measured',
                qualifier=f"DNA Foundation archive member {r['path']}; labels {r['labels']}. These are release rows before model-specific filtering.")
        pid='dnafoundation-'+tid+'-rf'
        c.protocol(pid,tid,'DNA Foundation frozen-representation classifier','frozen representation probe',
            'Final-layer sequence representation; mean/max/summary-token pooling, followed by a fitted random forest. DNABERT-2, NT-v2, HyenaDNA, Caduceus-Ph and GROVER are compared.',
            'Use deposited train/test CSVs. Paper: retain clear original partitions, otherwise stratified random 70:30; DNABERT-2/NT-derived data are reshuffled. Paper classifier tuning: fivefold; released implementation: fourfold GridSearchCV.',
            'supplied sequence row',code,[(('accuracy' if len(labels)>2 else 'auroc'),'Primary paper metric on this dataset; macro F1 and other code metrics are secondary.')],
            embeddings=True,fitted='Random forest; alternative naïve Bayes and elastic-net classifiers',variant=vid,
            selection='Training-only cross-validation; no full-foundation-model fine-tuning.')
        c.task_resource(tid,'dnafoundation-data',artifact,variant=vid,note='Archive member data/'+directory+'/train.csv and test.csv. This link identifies the processed release, not the native benchmark split.')
        c.task_resource(tid,'dnafoundation-code',code,'evaluation-code',variant=vid)
        if overlap:
            c.limit('tasks',tid,'dnafoundation_exact_sequence_overlap','conflicting',f'The DNA Foundation release contains {overlap} distinct exact sequences in both train and test for {directory}. This measured finding applies to this variant, not every release of the target.',artifact)
        c.review('tasks',tid,'DNA Foundation source identity mapping, complete released classification CSVs and fitted-readout implementation; native source definitions and protocols remain separately attributed.',[method,identity,artifact,code],
            limitations='Classification files do not retain genome coordinates or per-row species identifiers. Their partition does not establish chromosome, locus or homology exclusion.')
    c.limit('evaluations','dna-foundation','classifier_tuning_folds','conflicting','Main methods state fivefold tuning; the pinned released classification scripts use GridSearchCV cv=4.',code)
    # Standalone targets beyond short-sequence classification.
    exp=c.evidence('dnafoundation-personal-expression-method','dnafoundation-fulltext','Methods: gene-expression dataset and gene-expression prediction benchmark; Table 4',
        'Whole-blood GTEx v8 personal-expression prediction uses 610 individuals and 21,004 genes at nominal 6 kb context, and 768 genes retained for long context. A separate regressor is fitted per gene. Subjects are split 75:25, with fivefold training CV; MSE and Pearson correlation are measured across people for each gene. Allele representations are averaged. GROVER receives 2,048 bp; long Caduceus receives 131,072 bp, while long HyenaDNA and Enformer receive 196,608 bp.',url=PAPER)
    expcode=c.evidence('dnafoundation-personal-expression-code','dnafoundation-code','analysis/GTEX_regression.py and GTEX_cov_out.py',
        'The implementation chooses 75% of subject columns using seed 42, fits separate random-forest/XGBoost regressors per gene and uses fivefold negative-MSE tuning. It excludes genes with insufficient nonmissing training/test subjects. These are subject splits, not held-out genes or species. Regressed covariates and personal sequences are separate processing steps.','code',REPO+f'/blob/{REV}/analysis/GTEX_regression.py')
    var=c.evidence('dnafoundation-variant-method','dnafoundation-fulltext','Methods: genetic-variant datasets and variant-effect quantification benchmark',
        'Reference/alternate embedding differences feed a fitted random forest, rather than a native zero-shot likelihood score. Three outer chromosome groups rotate as test sets: {3,6,9,12,16,18,19,21}; {2,5,11,14,17,20,22,X}; {1,4,7,8,10,13,15}. Fourfold inner CV is also grouped by chromosome. Final AUROC and Cohen’s d average the three outer tests. The whole-blood Borzoi fine-mapped targets are eQTL, sQTL, intronic-polyadenylation QTL and polyadenylation QTL, each compared with matched negatives.',url=PAPER)
    varcode=c.evidence('dnafoundation-variant-code','dnafoundation-code','analysis/patho_classification.py, causal_classification.py and causal_generate.py',
        'The classification scripts implement the three outer groups and fourfold GroupKFold inner tuning. QTL generation uses inclusive coordinates from pos−window through pos+window, producing 2×window+1 bases (6,001 or 196,609). Pathogenic generation instead slices [pos−window:pos+window−1], producing 2×window−1 bases (5,999 or 196,607). The paper reports 6,000 or 196,608. Generators exclude chrY, missing chromosomes, boundary failures and allele/reference mismatches as implemented. Released source-table counts are not final scored totals.','code',REPO+f'/blob/{REV}/analysis/causal_generate.py#L40-L102')
    tad=c.evidence('dnafoundation-tad-attention-method','dnafoundation-fulltext','Methods: TAD-region recognition dataset and benchmark',
        'NT-v2 attentions are averaged across all layers, heads and 1,500 TAD-centered or 1,500 background sequences. The central 400 tokens represent 2,400 bp within each nominal 6 kb input. The analysis compares aggregate attention heatmaps; it does not fit or score a dense boundary predictor or a contact-map regressor.',url=PAPER)
    tadcode=c.evidence('dnafoundation-tad-attention-code','dnafoundation-code','analysis/tad_interpret.py; job_scripts/tad_ntv2.py; archive TAD FASTA and BED files',
        'The released interpretation script subtracts group-averaged attention arrays and plots a heatmap. The archive supplies TAD/background sequences and intervals. No held-out accuracy, AUROC or per-boundary retrieval score is defined for this diagnostic.','code',REPO+f'/blob/{REV}/analysis/tad_interpret.py')
    specs=[
        ('dnafoundation-expression','GTEx whole blood: personal expression','GTEx v8 whole-blood personal gene expression','Per-gene expression across individuals','regression',exp,['gene','genome'],['functional-prediction','long-context','regulatory-engineering']),
        ('dnafoundation-pathogenic','Pathogenic versus common coding variants: representation probe','LRB pathogenic/common SNPs, deposited coding subset','Pathogenic versus common coding-variant label','binary classification',var,['cds','genome'],['variant-effects','variant-interpretation','long-context']),
        ('dnafoundation-eqtl','Whole-blood causal eQTLs','Borzoi / GTEx v8 whole-blood eQTL','Fine-mapped causal versus matched noncausal eQTL','binary classification',var,['gene','genome'],['variant-effects','variant-interpretation','long-context']),
        ('dnafoundation-sqtl','Whole-blood causal sQTLs','Borzoi / GTEx v8 whole-blood sQTL','Fine-mapped causal versus matched noncausal splicing QTL','binary classification',var,['gene','genome'],['variant-effects','variant-interpretation','long-context']),
        ('dnafoundation-ipaqtl','Whole-blood causal intronic-polyadenylation QTLs','Borzoi / GTEx v8 whole-blood ipaQTL','Fine-mapped causal versus matched noncausal intronic-polyadenylation QTL','binary classification',var,['intron','polya','genome'],['variant-effects','variant-interpretation','long-context']),
        ('dnafoundation-paqtl','Whole-blood causal polyadenylation QTLs','Borzoi / GTEx v8 whole-blood paQTL','Fine-mapped causal versus matched noncausal polyadenylation QTL','binary classification',var,['polya','genome'],['variant-effects','variant-interpretation','long-context']),
        ('dnafoundation-tad','TAD-centered attention contrast','IMR90 insulation-derived TAD boundaries','Average attention difference between TAD-centered and background sequences','diagnostic analysis',tad,['chromatin-boundary'],['interpretability','model-development'])]
    for tid,name,dataset,target,typ,eid,features,cats in specs:
        c.put('tasks',dict(id=tid,name=name,dataset_name=dataset,target=target,task_type=typ,
            description='Source-specific evaluation of '+target.lower()+'.',label_basis='GTEx observed expression / fine-mapping, curated variant labels or reference insulation boundaries, as specified by the task.',
            status='paper-audited' if tid=='dnafoundation-expression' else 'artifact-audited',evidence_id=eid,
            input_description='Human genomic sequence; nominal 6 kb and up to 196,608 bp contexts for prediction; 6 kb for attention analysis.',
            output_description=target,limitations='Reported biological target and actual scoring unit are distinguished from the length of the supplied sequence.'))
        for category in features+cats:c.category(tid,category,eid,'Source-defined target or input context; long input alone does not imply dense output.')
        if tid=='dnafoundation-pathogenic':
            c.put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope='restricted-target',
                rationale='Every row in the deposited variant table has at least one coding consequence (missense, synonymous, stop/start, frameshift or in-frame). Flanking genome sequence is context, not an additional label target.',evidence_id=artifact))
        c.population(tid,'human',eid,'Human genomic origin. Whole blood or IMR90 describes the measured context, not a separate species.')
        c.member(tid,'dna-foundation',eid)
        c.output(tid,'diagnostic' if tid=='dnafoundation-tad' else 'isolated',eid,
            'Group-averaged attention matrix contrast' if tid=='dnafoundation-tad' else 'One value or class score per supplied gene/individual or variant',
            'aggregate group contrast' if tid=='dnafoundation-tad' else 'individual within gene' if tid=='dnafoundation-expression' else 'variant',
            axis='sampled' if tid=='dnafoundation-tad' else 'none',rationale='The evaluated unit is a supplied entity or diagnostic group. It is not genome-wide dense annotation or whole-gene structure recovery.')
        c.task_resource(tid,'dnafoundation-code',tadcode if tid=='dnafoundation-tad' else expcode if tid=='dnafoundation-expression' else varcode,'evaluation-code')
        if tid!='dnafoundation-expression':c.task_resource(tid,'dnafoundation-data',artifact,note='Exact archive scope: TAD/ attention inputs, pathogenic/ variant table or causal/ named QTL VCFs.')
        if tid=='dnafoundation-expression':
            c.protocol(tid+'-regression',tid,'Per-gene frozen-representation regression','frozen representation probe',
                'Average sequence representations of the two personal alleles; fit a separate random-forest or XGBoost regressor per gene.',
                '75:25 subject split with seed 42; fivefold training CV; genes with too few nonmissing subjects excluded. Gene identities are shared between train and test.',
                'individual',expcode,[('mse','Across held-out individuals per gene, then summarized across genes.'),('pearson','Across held-out individuals per gene, then summarized across genes.')],embeddings=True,fitted='Random forest / XGBoost')
            for n,unit in [(610,'individuals'),(21004,'genes in short-context panel'),(768,'genes retained in long-context panel')]:c.count(tid,n,unit,exp,qualifier='Paper panel size, not a count of independent gene–individual observations.')
            c.source('dnafoundation-gtex-access','GTEx protected individual data access','https://gtexportal.org/home/protectedDataAccess',kind='data-access-documentation')
            c.resource('dnafoundation-gtex','dnafoundation-gtex-access','GTEx individual genomes','dataset','other','https://gtexportal.org/home/protectedDataAccess',exp,
                availability='restricted',notes='An approved GTEx access request is required. Public expression aggregates do not replace personal genotypes.')
            c.task_resource(tid,'dnafoundation-gtex',exp)
            c.limit('tasks',tid,'personal_genotypes_and_targets','access-restricted','The processed individual-level benchmark is excluded from the public archive. Protected GTEx genomes require approved access; exact model-wise retained rows were not independently counted.',exp)
        elif tid=='dnafoundation-tad':
            c.protocol(tid+'-attention',tid,'Unfitted attention contrast','unfitted diagnostic analysis','NT-v2 attention matrices, averaged across layers, heads and sequences; not hidden embeddings or model predictions.',
                '1,500 source-selected TAD-centered sequences and 1,500 random matched-length controls; no fitted train/test split.',
                'sequence group',tadcode,embeddings=False,notes='Qualitative heatmap comparison; the source defines no scalar held-out prediction metric.')
            for f in ['tad','background']:c.count(tid,files['data/TAD/'+f+'_6kb_sequences.fa']['records'],'sequences',artifact,split=f,method='measured',qualifier='Complete deposited FASTA scan; 6,000 bp per sequence.')
            c.limit('tasks',tid,'predictive_metric','not-applicable','This is an aggregate attention diagnostic with no scalar predictive metric or trained boundary classifier.',tadcode)
        else:
            c.protocol(tid+'-rf',tid,'Chromosome-grouped variant representation probe','frozen representation probe',
                'Alternate minus reference representation; fitted random forest. Model-specific hidden representations or track outputs; not a native likelihood score.',
                'Rotate three disjoint outer chromosome groups; fourfold chromosome-grouped inner CV. G1:3,6,9,12,16,18,19,21; G2:2,5,11,14,17,20,22,X; G3:1,4,7,8,10,13,15.',
                'chromosome',varcode,[('auroc','Mean over three outer chromosome groups.'),('cohens-d','Predicted-score separation, averaged over the three outer test groups.')],embeddings=True,fitted='Random forest')
            c.limit('tasks',tid,'input_length','conflicting','Paper reports 6,000/196,608 bp. QTL generator emits 6,001/196,609 bp; pathogenic generator emits 5,999/196,607 bp, before model-specific cropping.',varcode)
            c.limit('tasks',tid,'final_scored_cohort','not-released','Released source variant tables precede boundary, reference-allele and model-specific finite-score filtering. They are not a complete manifest of the final shared scored intersections.',artifact)
            if tid!='dnafoundation-pathogenic':
                kind=tid.removeprefix('dnafoundation-')
                for label in ['pos','neg']:
                    f=files[f'data/causal/{kind}/blood_{label}.vcf']
                    c.count(tid,f['rows'],'source variant rows',artifact,split='positive' if label=='pos' else 'negative',method='measured',qualifier='Complete deposited VCF scan before sequence extraction and model-specific exclusions.')
            else:
                c.count(tid,files['data/pathogenic/vep_pathogenic_coding.csv']['rows'],'source variant rows',artifact,method='measured',qualifier='Complete deposited coding-consequence table before context extraction: 22,254 pathogenic and 17,398 common SNPs. The supplied split column is not the rotating chromosome-CV protocol.')
        c.review('tasks',tid,'Complete primary methods, pinned implementation, all corresponding public archive members and exact resource availability.',[eid,artifact,tadcode if tid=='dnafoundation-tad' else expcode if tid=='dnafoundation-expression' else varcode],
            limitations='No model inference is rerun. Source input tables, reported cohorts and actually scored intersections remain distinct.')
    c.put('metrics',dict(id='cohens-d',name='Cohen’s d',definition='Difference of group means divided by pooled standard deviation.',direction='higher'))
    c.get('evaluations','dna-foundation').update(status='artifact-audited',source_id='dnafoundation-fulltext',evidence_id=method,
        description='Frozen-representation classification, personal expression and chromosome-grouped variant probes, plus an attention diagnostic.',
        scope_note='57 source-mapped classification targets are reused as release-specific variants. Seven additional records represent personal expression, five variant targets and the TAD attention diagnostic. Frozen embeddings do not make the fitted predictions zero-shot.',
        notes='Full paper and supplement, the complete 1.1 GB public archive, all classification rows and pinned code reviewed. GTEx individual data are protected. Paper/code tuning-fold and input-length discrepancies are explicit.')
    c.get('papers','dna-foundation').update(source_id='dnafoundation-fulltext',publication_date='2025-11-28',
        notes='Complete journal XML, all 11 supplementary pages and the deposited data/code reviewed. Release-specific discrepancies and protected-data access are recorded with the tasks.')
    c.review('evaluations','dna-foundation','Complete primary article, all 11 supplementary pages, all 57 classification file pairs, eight QTL VCFs, pathogenic table, TAD inputs and pinned evaluation implementation.',
        [method,identity,artifact,code,exp,expcode,var,varcode,tad,tadcode],limitations='Protected GTEx individuals are not public; measured source rows are not final model-wise scored cohorts.')
    return d
