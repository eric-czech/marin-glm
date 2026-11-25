"""Versioned task registries; unverified manifest entries stay registered."""
from pathlib import Path
import ast
import csv
import json
import re
ROOT=Path(__file__).resolve().parents[2]

def hf(c,id,repo,statement,needle=None):
    folder=ROOT/'research/sources/huggingface'/repo.replace('/','--')
    api=json.loads((folder/'api.json').read_text())
    sid='src-'+id
    url=f'https://huggingface.co/datasets/{repo}/blob/{api["sha"]}/README.md'
    c.source(sid,repo+' dataset card',url,'dataset-card',api['sha'],str((folder/'README.md').relative_to(ROOT)))
    return c.ev(id,sid,'Pinned dataset card'+(': '+needle if needle else ''),statement,'documentation')

def populate(c):
    nt(c); gb(c); dgeb(c); geneb(c); rna(c); plant(c)
    e=c.ev('lambda-registration','lambda-paper','Benchmark paper / release registration','LAMBDA is in scope as a prophage-detection evaluation source; task variants await full-text and artifact reconciliation.')
    c.suite('lambda','LAMBDA','Prophage detection and localization benchmark.',e,'lambda',status='registered',notes='Pending: labels, host/clade coverage, splits, units, metrics and released-file audit. No unverified performance claims are included.')

def nt(c):
    e=hf(c,'nt-revised-card','InstaDeepAI/nucleotide_transformer_downstream_tasks_revised','Revised NT has 18 human tasks, genomic negatives and chromosome-held-out tests; K562 histone marks, SCREEN enhancers, EPD promoters and GENCODE v44 splice sites.')
    c.suite('nt-revised','Nucleotide Transformer revised benchmark','18 human sequence-classification targets; chromosome-held-out test cohorts. Keep separate from original NT.',e,status='partial',notes='Actual pinned Parquet rows, scalar label vocabularies and sequence lengths were inspected. Chromosome membership is reported by the card; coordinates have not been independently reconstructed.')
    marks=['H2AFZ','H3K27ac','H3K27me3','H3K36me3','H3K4me1','H3K4me2','H3K4me3','H3K9ac','H3K9me3','H4K20me1']
    specs=[(m,m+' peak presence',1000,('genome',),2) for m in marks]
    specs +=[(x,target,length,(reg,),classes) for x,target,length,reg,classes in [('promoter_all','Any promoter presence',300,'promoter',2),('promoter_tata','TATA promoter presence',300,'promoter',2),('promoter_no_tata','Non-TATA promoter presence',300,'promoter',2),('enhancers','Enhancer presence',400,'enhancer',2),('enhancers_types','Tissue-specific / invariant / no enhancer',400,'enhancer',3),('splice_sites_all','Donor / acceptor / no splice site',600,'splice',3),('splice_sites_donors','Splice donor presence',600,'splice',2),('splice_sites_acceptors','Splice acceptor presence',600,'splice',2)]]
    for slug,target,length,regions,classes in specs:
        t='nt-revised-'+slug
        c.task(t,'nt-revised',target,'NT revised / '+slug,target,'Classify fixed-length human genomic windows using release-specific annotations and genome-derived negatives.','binary classification' if classes==2 else 'multiclass classification','Experimental peak / reference feature annotation',e,applications=('genome-annotation','regulatory-engineering'),capabilities=('functional-prediction',),regions=regions,populations=('human',),status='artifact-audited',input=f'{length}-bp DNA window',limitations='Artifact audit verifies rows, scalar labels and lengths. It does not yet verify sequence homology, reference-coordinate consistency or chromosome separation.')
        c.variant(t,t+'-release','Pinned NT revised release',e,length=str(length)+' bp',revision='851f9946252e90c665cdb3cc3eedb78f1f26197c',targets=classes,target_unit='mutually exclusive classes')
    c.finding('nt-revised-enhancers_types','The card calls this multi-label, but the pinned Parquet contains one scalar integer label per row in {0,1,2}. The released task is represented as multiclass; the terminology discrepancy is retained.',e,severity='discrepancy',suite='nt-revised')
    old=c.ev('nt-original-definition','generator-paper','Sequence understanding benchmark description','Original NT tasks are a separate benchmark version; original histone tasks include yeast, unlike the all-human revised release.')
    c.suite('nt-original','Nucleotide Transformer original benchmark','Original NT target collection. Do not transfer revised-release species, negative construction or chromosome splits to this version.',old,status='partial')
    for mark in ['H3','H3K14ac','H3K36me3','H3K4me1','H3K4me2','H3K4me3','H3K79me3','H3K9ac','H4','H4ac']:
        c.task('nt-original-'+mark,'nt-original',mark+' original histone target','NT original / '+mark,mark+' histone annotation','Original yeast histone-mark classification; dataset version differs from NT revised.','binary classification','Histone annotation',old,applications=('genome-annotation',),capabilities=('functional-prediction',),regions=('genome',),populations=('yeast',),input='Original benchmark DNA windows',limitations='Exact original released split counts and source assay reconstruction pending.')
    for slug,target,region,classes in [('promoter_all','Any promoter','promoter',2),('promoter_tata','TATA promoter','promoter',2),('promoter_no_tata','Non-TATA promoter','promoter',2),('enhancers','Enhancer presence','enhancer',2),('enhancers_types','Enhancer type','enhancer',3),('splice_sites_all','Splice-site type','splice',3),('splice_sites_acceptors','Splice acceptor','splice',2),('splice_sites_donors','Splice donor','splice',2)]:
        c.task('nt-original-'+slug,'nt-original',target+' (original NT)','NT original / '+slug,target,'Original NT classification target, separate from the revised release. Do not inherit revised negative construction, counts or chromosome splits.','binary classification' if classes==2 else 'multiclass classification','Original reference/assay annotations',old,applications=('genome-annotation',),capabilities=('functional-prediction',),regions=(region,),populations=('human',),input='Original NT DNA windows',limitations='Original source version and coordinate/split lineage remain pending; revised-release facts do not apply automatically.')
    ge=c.code('gue-registration','biomap-research/DeepD','notebook/fine_tune/README.md','GUE H3','DeepD explicitly identifies its released H3 example as GUE. Do not assume its processing/splits are identical to original NT H3.',basis='documentation')
    c.suite('gue','GUE regulatory tasks','Source suite for the released DeepD H3 example; complete suite expansion pending.',ge,status='partial')
    for mark in ('H3','H4'):
        c.task('gue-'+mark,'gue',mark+' histone classification','GUE / '+mark,mark+' histone annotation','Yeast histone prediction from DNA. GUE and NT versions may share source assays but their split lineage must be verified before merging records.','binary classification','Histone assay annotation',ge,applications=('genome-annotation',),capabilities=('functional-prediction',),regions=('genome',),populations=('yeast',),input='DNA sequence / released embeddings',limitations='H3 release has inspected label files; exact source sequence lineage and H4 artifact remain pending.')

def gb(c):
    repo='ML-Bioinfo-CEITEC/genomic_benchmarks'
    specs=[('human_enhancers_cohn','Enhancer activity class',('human',),('enhancer',)),('human_enhancers_ensembl','Enhancer annotation',('human',),('enhancer',)),('human_nontata_promoters','Non-TATA promoter annotation',('human',),('promoter',)),('human_ocr_ensembl','Open-chromatin annotation',('human',),('regulatory',)),('human_ensembl_regulatory','Enhancer / open chromatin / promoter class',('human',),('enhancer','promoter','regulatory')),('drosophila_enhancers_stark','Developmental enhancer annotation',('fly',),('enhancer',)),('demo_human_or_worm','Human versus worm sequence origin',('human','worm'),('genome',)),('demo_coding_vs_intergenomic_seqs','Transcript-derived versus intergenic sequence',('human',),('exon','intergenic')),('dummy_mouse_enhancers_ensembl','Mouse enhancer annotation',('mouse',),('enhancer',))]
    e=c.code('gb-definition',repo,'docs/human_ensembl_regulatory/README.md','#','Genomic Benchmarks includes binary and multiclass DNA datasets; original sources and negative construction differ.',basis='documentation')
    c.suite('gb','Genomic Benchmarks','Nine repository datasets, including demonstration and dummy datasets. Individual provenance matters.',e,'gb')
    for slug,target,pops,regions in specs:
        ev=c.code('gb-'+slug,repo,'docs/'+slug+'/README.md','#',target+' source documentation.',basis='documentation')
        c.task('gb-'+slug,'gb',target,'Genomic Benchmarks / '+slug,target,'Use the dataset-specific positives, controls and partition documented at the pinned source.','classification','Reference annotations / assay source; dataset-specific',ev,applications=('model-development',) if slug.startswith(('demo','dummy')) else ('genome-annotation',),capabilities=('functional-prediction',),regions=regions,populations=pops,input='DNA window; length varies by dataset',limitations='Demo/dummy names describe intended example use. Do not assume equal quality or a common chromosome-held-out split across this suite.')
        c.protocol('gb-'+slug,'gb-'+slug+'-protocol','Released dataset partition',ev,'probe / fine-tune depends on model paper','Task-specific sequence classifier','Use source dataset train/test partition. Split construction has not been uniformly reconstructed; consult the individual source.','sequence',embeddings=None)

def dgeb(c):
    repo='TattaBio/DGEB'
    e=c.code('dgeb-definition',repo,'dgeb/tasks/classification_tasks.py','Classification tasks','DGEB provides multiple DNA, RNA and protein tasks; task metadata pins each HF dataset revision.')
    c.suite('dgeb','DGEB','Embedding-based classification, pair comparison, clustering, phylogenetic distance, retrieval and orthology/mining.',e,'dgeb',notes='Protein-only entries are comparison tasks, not direct nucleotide-model requirements. An HF split called train is sometimes the complete zero-shot evaluation collection.')
    files=list((ROOT/'research/sources/TattaBio--DGEB/dgeb/tasks').glob('*_tasks.py'))
    for file in sorted(files):
        tree=ast.parse(file.read_text())
        for cls in (x for x in tree.body if isinstance(x,ast.ClassDef)):
            meta=next((x.value for x in cls.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='metadata' for t in x.targets)),None)
            if not isinstance(meta,ast.Call):continue
            kw={x.arg:x.value for x in meta.keywords}
            def val(key):
                x=kw.get(key)
                return x.value if isinstance(x,ast.Constant) else (x.attr if isinstance(x,ast.Attribute) else '')
            slug=val('id'); modality=val('modality'); typ=val('type'); name=val('display_name'); desc=val('description')
            if not slug:continue
            path=str(file.relative_to(ROOT/'research/sources/TattaBio--DGEB'))
            ev=c.code('dgeb-'+slug,repo,path,'class '+cls.name,desc)
            datasets=[]
            for call in ast.walk(kw['datasets']):
                if isinstance(call,ast.Call):
                    ds={x.arg:x.value.value for x in call.keywords if isinstance(x.value,ast.Constant)}
                    if 'path'in ds:datasets.append(ds)
            t='dgeb-'+slug
            pops=[]
            # Taxon restrictions come from literal task descriptions, not a kingdom guess from model training.
            if 'Archae' in name or 'Arch ' in name:pops.append('archaea')
            if 'Bacterial' in name or 'BacArch' in name:pops.append('bacteria')
            if 'BacArch' in name:pops.append('archaea')
            if 'Euk' in name:pops.append('euk')
            if 'E.coli' in name:pops.append('ecoli')
            regions=('rrna',) if '16S' in name or '18S'in name else ('operon',) if 'Operon'in name else () if 'RNA Clustering'in name else ('bgc',) if 'MIBiG'in name else ('cds',)
            caps=('evolutionary-inference',) if typ=='eds' else ('sequence-retrieval',) if typ in ('retrieval','bigene_mining') else ('functional-prediction',)
            c.task(t,'dgeb',name+' ['+modality+']',datasets[0]['path'] if datasets else name,desc,desc,typ,'Phylogenetic distances / curated annotations, task-dependent',ev,applications=('comparative-genomics','microbial-genomics'),capabilities=caps,regions=regions,populations=tuple(dict.fromkeys(pops)),input=modality+' sequences; frozen embeddings',limitations='Code-level task and protocol audit. Dataset-specific counts and full source taxon distributions remain pending. Protein tasks require a protein interface.')
            for i,ds in enumerate(datasets):
                c.variant(t,t+'-data'+str(i),'Pinned '+ds['path'],ev,revision=ds.get('revision'),notes='https://huggingface.co/datasets/'+ds['path']+'/tree/'+ds.get('revision','main'))
            metric={'classification':'f1','pair_classification':'ap','clustering':'v-measure','eds':'pearson','retrieval':'map5','bigene_mining':'f1'}.get(typ)
            if slug=='modac_paralogy_bigene':metric='recall50'
            c.protocol(t,t+'-protocol','DGEB '+typ,ev,'frozen probe' if typ=='classification' else 'zero-shot embedding comparison','Frozen '+modality+' embeddings','Classification uses released train/test. Distance, clustering and pair tasks may read the entire evaluation collection from its HF train split; no biological training partition is implied by that name.','sequence / pair / dataset',metrics=(metric,) if metric else (),embeddings=True,fitted='Logistic regression; MIBiG has a multioutput KNN recipe' if typ=='classification' else None,selection='Layer and distance-metric comparisons require selection provenance; top-score metrics are retrospective maxima where the evaluator chooses them.',notes=('EDS reports the maximum Pearson correlation over cosine, Manhattan and Euclidean distances. ' if typ=='eds' else '')+'Primary source metric identifier: '+val('primary_metric_id')+'. Preserve the evaluator’s aggregation rather than treating all family scores identically.')
    # LOAM uses only the DNA EC dataset and its own fixed readout.
    t='dgeb-ec_dna_classification'
    e=c.code('loam-ec','Soilytix/gLMBench','docs/task_dgeb_ec_classification.md','#','LOAM evaluates DNA EC classification with 128 classes, four train and one test gene per class.',basis='documentation')
    c.member('loam-evals',t,e)
    for layer in ('last','sweep'):
        p=c.protocol(t,'loam-ec-'+layer,'LOAM DNA EC '+layer,e,'frozen probe','Frozen raw block-output DNA embeddings','512 train and 128 test genes, four/one per class. No validation split; best-layer protocol chooses by test macro-F1.','gene',metrics=(('f1','Macro across 128 EC classes'),),embeddings=True,fitted='Fixed logistic regression readout',selection='Fixed last layer' if layer=='last' else 'Highest test macro-F1; retrospective selection')
        c.use('loam',t,e,'loam',protocol=p)
        c.use('evo2',t,e,'loam','external-evaluation',protocol=p)
    c.finding(t,'The LOAM EC test set has one example per class and layer selection maximizes test macro-F1. Treat its layer-sweep as a different protocol from a fixed readout.',e,suite='loam-evals')

def geneb(c):
    path='benchmark/benchmark_spec.json';repo='darlednik/GENEB'
    spec=json.loads((ROOT/'research/sources/darlednik--GENEB'/path).read_text())
    e=c.code('geneb-spec',repo,path,'"schema_version"','GENEB declares 100 task configurations, frozen mean embeddings, logistic regression, five seeds and full/one-shot/ten-shot training.')
    c.suite('geneb','GENEB','Manifest of 100 classification configurations from existing datasets, evaluated under a common embedding readout.',e,'geneb',notes='Overlaps other suites. Revised NT entries reuse their task records. Other manifest-only entries remain registered until target/sequence/source audits are complete.')
    regions={'Histone Mod.':('genome',),'Promoters':('promoter',),'Enhancers':('enhancer',),'DNA Methyl.':('genome',),'Splice Sites':('splice',),'lncRNA':('lncrna',),'Mouse Enh.':('enhancer',),'TF Binding':('tfbs',),'Species Clf.':('genome',),'Regulatory':('regulatory',),'Virus/Phage':('genome',),'Coding/NC':('gene',),'Chromatin Acc.':('regulatory',)}
    for row in spec['tasks']:
        rid=row['id']; slug='geneb-'+rid.lower().replace('_','-')
        if rid.startswith('InstaDeepAI_nucleotide_transformer_downstream_tasks_revised_'):
            suffix=rid.removeprefix('InstaDeepAI_nucleotide_transformer_downstream_tasks_revised_')
            suffix={'splice_sites_acceptor':'splice_sites_acceptors','splice_sites_donor':'splice_sites_donors'}.get(suffix,suffix)
            t='nt-revised-'+suffix
        elif rid.startswith('InstaDeepAI_nucleotide_transformer_downstream_tasks_') and 'nt-original-'+rid.split('_tasks_')[-1] in c.ids['tasks']:
            t='nt-original-'+rid.split('_tasks_')[-1]
        else:
            t=slug
            c.task(t,'geneb',row['label'],rid,'Classification target: '+row['label'],'GENEB manifest configuration in category '+row['category']+'. Original source target semantics and artifact lineage have not yet been fully reconciled.','classification','Upstream dataset labels; detailed construction pending',e,applications=('model-development',),capabilities=('functional-prediction',),regions=regions.get(row['category'],()),status='registered',input='DNA sequence → frozen mean embedding',limitations='This record is a manifest registration. Species, exact target schema, lengths and counts are intentionally unassigned until primary artifacts establish them.')
        c.member('geneb',t,e,'GENEB configuration '+rid)
        c.variant(t,slug+'-release','GENEB '+row['label'],e,revision=spec['dataset']['revision'],notes='HF darlednik/geneb-tasks / tasks/'+rid+'/{train,test}.csv')
        c.protocol(t,slug+'-probe','GENEB full / 1-shot / 10-shot',e,'frozen probe','Mean over model tokens; extractor-specific pooling','Fixed public train/test files. Few-shot subsample is drawn from train; biological split construction depends on the upstream dataset.','sequence; upstream grouping pending',metrics=('mcc','accuracy','f1'),embeddings=True,fitted='LogisticRegression(max_iter=1000); seeds 13,17,42,123,997',notes='Task configuration: '+rid+'; target/source audit status is separate from the common harness audit.')

def rna(c):
    e=c.code('rnagym-definition','MarksLab-DasLab/RNAGym','README.md','RNAGym is','RNAGym includes fitness and secondary/tertiary structure benchmarks; structure tasks are separate from protein-coding RNA fitness.',basis='documentation')
    c.suite('rnagym','RNAGym','RNA fitness and structure evaluation source. The pinned fitness manifest has 70 assay entries.',e,'rna',notes='Fitness metadata audited; most individual assay rows and structure split files are not yet checked. LOAM uses only 11 protein-coding bacterial assays.')
    repo='MarksLab-DasLab/RNAGym';path='fitness/reference_sheet_final.csv'
    rows=list(csv.DictReader((ROOT/'research/sources/MarksLab-DasLab--RNAGym'/path).read_text(encoding='utf-8-sig').splitlines()))
    em=c.code('rnagym-manifest',repo,path,'DMS_ID','Pinned 70-assay fitness reference sheet; assay descriptions identify constructs and measured targets.',basis='data')
    # LOAM’s explicit assay IDs provide source evidence for bacterial assignment.
    loam_manifest=(ROOT/'research/sources/Soilytix--gLMBench/src/glmbench/tasks/data/rnagym/prok_coding_manifest.yaml').read_text()
    selected=dict(re.findall(r'dms_id: (\S+).*?n_rows: (\d+)',loam_manifest,re.S))
    el=c.code('loam-rna','Soilytix/gLMBench','docs/task_rnagym_dms.md','#','LOAM scores 11 prokaryotic protein-coding RNAGym assays; causal mean-token likelihood or masked marginal LLR; absolute Spearman.',basis='documentation')
    for row in rows:
        rid=row['DMS_ID'];t='rnagym-'+rid.lower().replace('_','-')
        typ=row['RNA_TYPE'].lower(); region={'ribozyme':'ribozyme','trna':'trna','rrna':'rrna','mrna-coding':'cds','aptamer':'aptamer'}.get(typ,'ncrna')
        desc=row['ASSAY_DESCRIPTION'] or row['TITLE']
        ev=c.code('rnagym-assay-'+rid.lower().replace('_','-'),repo,path,rid,desc,basis='data')
        c.task(t,'rnagym',rid, rid,'Assay fitness / activity',desc,'regression / ranking','Experimental assay; construct/host details require original-source audit',ev,applications=('protein-engineering',) if region=='cds' else ('rna-engineering',),capabilities=('variant-effects',),regions=(region,),populations=('bacteria',) if rid in selected else (),status='paper-audited' if rid in selected else 'registered',input='Mutant nucleotide sequence',limitations='Reference-sheet entry inspected. Taxonomic origin and assay host are not inferred from gene-name abbreviations; counts/processing require the assay file.')
        if rid in selected:
            c.member('loam-evals',t,el,'Explicit LOAM prokaryotic coding assay subset.')
            c.count(t,int(selected[rid]),'mutant sequences',el,qualifier='Vendored LOAM manifest reports processed assay rows; not independently recounted.')
            p=c.protocol(t,t+'-loam','LOAM RNAGym likelihood scoring',el,'zero-shot','Causal mean per-token log-likelihood or masked marginal LLR (sum over mutant sites)','No fitted readout. Exclude over-context sequences; an assay with no scored variants drops out of the macro.','mutant sequence / assay',metrics=(('abs-spearman','Per-assay absolute Spearman; macro across retained assays'),),embeddings=False,notes='MLM multi-site score is additive on the wild-type background; causal and masked estimators are distinct. One short-context model skips all 697 variants of one assay.')
            c.use('loam',t,el,'loam',protocol=p);c.use('evo2',t,el,'loam','external-evaluation',protocol=p)
    c.finding(None,'The pinned fitness reference sheet contains 70 entries. This is a manifest count, not 70 independently artifact-audited tasks. RNA structure targets and their split cohorts remain to be expanded.',em,suite='rnagym')
    en=c.code('nabench-manifest','mrzzmrzz/NABench','metadata.csv','DMS_ID','Pinned NABench manifest has 170 entries. Some annotations conflict with source study identity; do not infer functional region from every RNA_TYPE field.',basis='data')
    c.suite('nabench','NABench','Nucleotide-model fitness predictions across regulatory constructs, coding assays, catalytic RNA and binding libraries.',en,'na',status='registered',notes='170 manifest entries located. Individual task registration awaits conflict resolution and released assay/split audit; no blanket region/taxon attribution is made.')
    bad=c.code('nabench-brca1-discrepancy','mrzzmrzz/NABench','metadata.csv','Gregory_2018_mRNA','BRCA1 saturation-genome-editing entry is labeled enhancer in the RNA_TYPE columns.',basis='data')
    c.finding(None,'NABench metadata includes a BRCA1 coding assay labeled as enhancer. Functional-region assignments require source study/artifact reconciliation before importing the manifest wholesale.',bad,severity='discrepancy',suite='nabench')

def plant(c):
    e=hf(c,'pgb-card','InstaDeepAI/plant-genomic-benchmark','Plant Genomic Benchmark includes polyA, splice, lncRNA, chromatin, expression and reporter tasks with species and assay variants.')
    c.suite('pgb','Plant Genomic Benchmark','Plant regulatory, RNA-processing and gene-expression targets, with species/assay-specific variants.',e,'pgb',notes='Dataset counts in the card do not always equal numbers of distinct species: two tissues/conditions and rice accessions are not separate species.')
    records=[('polya','Polyadenylation-site presence','binary classification',('polya',),('arabidopsis','rice','clover','medicago','chlamydomonas'),'400 bp'),('splice-donor','Splice donor presence','binary classification',('splice',),('arabidopsis',),'398 bp'),('splice-acceptor','Splice acceptor presence','binary classification',('splice',),('arabidopsis',),'398 bp'),('lncrna','lncRNA versus coding RNA','binary classification',('lncrna','mrna'),('cassava','maize','soybean','tomato','wheat','sorghum'),'101–6,000 bp'),('promoter-strength','Reporter promoter strength','regression',('promoter',),('arabidopsis','maize','sorghum'),'170 bp'),('terminator-strength','Reporter terminator strength','regression',('terminator',),('arabidopsis','maize','synthetic'),'170 bp'),('chromatin','Chromatin accessibility / histone tracks','multilabel prediction',('regulatory',),('arabidopsis','rice','maize','setaria','brachypodium','sorghum'),'1,000 bp'),('gene-expression','Gene expression profile','multioutput regression',('gene','promoter'),('arabidopsis','rice','maize','soybean','tomato','cassava'),'6,000 bp'),('enhancer','Cassava transcribed enhancer regions','binary classification',('enhancer',),('cassava',),'1,000 bp')]
    for slug,target,typ,regions,pops,length in records:
        t='pgb-'+slug
        c.task(t,'pgb',target,'Plant Genomic Benchmark / '+slug,target,'Release-specific plant sequence-to-function target. Species, accession, tissue and assay condition are linked variants, not interchangeable dataset counts.',typ,'Reference annotation / measured reporter or expression assay',e,applications=('plant-breeding','regulatory-engineering'),capabilities=('functional-prediction',),regions=regions,populations=pops,input=length+' DNA sequence',limitations='Card-level audit. Species-specific labels, counts and split coordinate files must be checked before interpreting transfer. Training-sampling counts are not assumed to be unique genomic examples.')
        c.variant(t,t+'-card','Reported PGB input',e,length=length,revision='78ec8156c2ffb3e5475277fdb7eb603294224e53')
        c.protocol(t,t+'-protocol','PGB source task partition',e,'supervised / adaptation-specific','Sequence predictor or frozen representations depending on model paper','Species/accession-specific source partitions. Exact coordinate/homology grouping remains pending.','sequence / gene / chromosome; source-specific',embeddings=None)
    c.finding(None,'The card groups eight task families; donor/acceptor targets are separate records here. Promoter/terminator leaf and protoplast measurements are conditions, not separate species. Rice accessions likewise must not inflate species counts.',e,suite='pgb')
    # Primary full-text methods resolve details absent from the terse dataset card.
    pe=c.ev('pgb-primary-methods','pgb-paper','Methods: Polyadenylation site prediction; Splicing site prediction; lncRNA prediction; Promoter and terminator strength; Chromatin profiles; Gene expression; Cassava mutagenesis','Defines actual sequence origins, experimental hosts, negative controls and biological split units.',url='https://www.nature.com/articles/s42003-024-06465-2')
    rules={
        'pgb-polya':('A sampled chromosome held out for test within each species; exact chromosome is species-specific.','chromosome','auprc','400 bp: 300 upstream +100 downstream of PAC; predict polyA at position 301. Two negatives per positive shift the center by 1–50 bp, rather than removing all polyA sequence.'),
        'pgb-splice-donor':('Arabidopsis chromosome 5 is the test set.','chromosome','auprc','398-bp source splice windows; strongly imbalanced donor/non-donor labels.'),
        'pgb-splice-acceptor':('Arabidopsis chromosome 5 is the test set.','chromosome','auprc','398-bp source splice windows; strongly imbalanced acceptor/non-acceptor labels.'),
        'pgb-lncrna':('One sampled chromosome held out per species; wheat test chromosomes 1A/1B/1D.','chromosome','auprc','GreeNC v2 lncRNA versus length/GC-matched mRNA negatives; sequences ≤6 kb. Original AgroNT adaptation pools the six species.'),
        'pgb-promoter-strength':('Use Jores et al. published training/test libraries; exact sequence-family partition pending artifact audit.','reporter construct','r2','170-bp promoters from Arabidopsis, maize and sorghum; measured in tobacco leaves or maize protoplasts. Source species and assay host are distinct.'),
        'pgb-terminator-strength':('Use Gorjifard et al. published training/test libraries; exact sequence-family partition pending artifact audit.','reporter construct','r2','170-bp terminators from Arabidopsis/maize plus GC-varied random sequences; assay systems include tobacco leaves and maize protoplasts.'),
        'pgb-chromatin':('Reuse Zhao et al. species-specific validation/test chromosomes. Exact per-species chromosome lists pending upstream artifact audit.','chromosome','auprc','1-kb DNA input; label each tissue positive if an OCR overlaps more than half of the central 200 bp. Six species, seven accession datasets.'),
        'pgb-gene-expression':('BLAST-derived within-species gene-family graph clusters assigned to train/test, approximately 80/20. Released validation counts are separately documented by the card.','gene family','r2','5 kb upstream +1 kb downstream of TSS. Expression across tissues; cassava is added separately to the five-species atlas analyses.'),
        'pgb-enhancer':('Cassava chr17 test; chr9 validation; remaining chromosomes train.','chromosome','auroc','1-kb windows centered on PRO-seq intergenic peaks, ≥1 kb from genes. Negatives from the same chromosome, outside PRO-seq peaks and within five GC percentage points.'),
    }
    for t,(rule,unit,metric,note) in rules.items():
        c.protocol(t,t+'-agro-methods','Original AgroNT / PGB procedure',pe,'parameter-efficient fine-tune','AgroNT sequence encoder plus IA3 / task head',rule,unit,metrics=(metric,),embeddings=False,fitted='Task head and IA3 weights; some tasks unfreeze final layers',notes=note)
        c.field('tasks',t,'input_description',pe,note)
    c.add('populations',id='tobacco',name='Tobacco (assay host)',rank='reported host',parent_id='solanaceae',ncbi_taxid=None,notes='Primary PGB passage reports tobacco; this record does not guess the Nicotiana species.')
    for t in ('pgb-promoter-strength','pgb-terminator-strength'):
        for pop in ('tobacco','maize'):
            c.add('task_populations',task_id=t,population_id=pop,variant_id=None,relation='assay-host',coverage='STARR-seq assay host; distinct from sequence origin.',evidence_id=pe)
    # Reported counts are not an independent row recount.
    card=(ROOT/'research/sources/huggingface/InstaDeepAI--plant-genomic-benchmark/README.md').read_text()
    families={'poly_a':'pgb-polya','splicing':'pgb-splice-donor','lncrna':'pgb-lncrna','promoter_strength':'pgb-promoter-strength','terminator_strength':'pgb-terminator-strength','gene_exp':'pgb-gene-expression','chromatin_access':'pgb-chromatin','pro_seq':'pgb-enhancer'}
    for line in card.splitlines():
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells)!=4 or '.' not in cells[0]:continue
        family=cells[0].split('.')[0]
        if family not in families:continue
        t=families[family]
        if family=='splicing' and cells[0].endswith('acceptor'):t='pgb-splice-acceptor'
        v='pgb-card-'+cells[0].replace('.','-')
        c.variant(t,v,cells[0],e,revision='78ec8156c2ffb3e5475277fdb7eb603294224e53',notes='Dataset/accession/assay condition from the release card. Species and host assignments are recorded separately.')
        for split,value in zip(('train','validation','test'),cells[1:]):
            if value.isdigit():c.count(t,int(value),'reported samples',e,split=split,variant=v,qualifier='Card total; chromatin training counts describe sampled sequence draws, not verified unique loci.' if family=='chromatin_access' else 'Card-reported split rows; processed files not independently recounted.')
