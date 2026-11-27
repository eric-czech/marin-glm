"""Resolve the original BEND outputs; never substitute BEND 2.0 protocols."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
REV='58ad41011125cfca339d511e9b8eb536a54b582a'


def populate(d):
    def put(table,row,keys=('id',)):
        old=next((r for r in d[table] if all(r[k]==row[k] for k in keys)),None)
        if old is None:d[table].append(row)
        else:old.update(row)
    def evidence(id,locator,statement,source='project-paper-bend-original',url=None,basis='paper'):
        s=next(r for r in d['sources'] if r['id']==source)
        put('evidence',dict(id=id,source_id=source,locator=locator,statement=statement,url=url or s['url'],basis=basis,inspected='2026-11-27'))
        return id
    def code(slug,file,statement):
        id='bend1-'+slug
        url=f'https://github.com/frederikkemarin/BEND/blob/{REV}/{file}'
        path='research/artifacts/splice-audit/BEND/'+file
        put('sources',dict(id=id+'-source',title='Original BEND / '+file,kind='repository-file',url=url,version=REV,
            retrieved='2026-11-27',sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),local_path=path,availability='available',notes='Selected release interface inspected; dataset labels not independently validated.'))
        return evidence(id,file,statement,id+'-source',url+'#L1','code')
    dims=code('dimensions','conf/datadims/label_dims.yaml','Release declares nine gene labels, one enhancer output, 125 accessibility labels, 18 histone outputs and seven methylation outputs.')
    code('gene-readout','conf/supervised_tasks/gene_finding.yaml','Frozen embedding CNN with nine positional class outputs, cross-entropy and MCC; source also offers supervised one-hot baselines.')
    code('enhancer-readout','conf/supervised_tasks/enhancer_annotation.yaml','CNN positional output downsampled to128-bp bins; BCE, positive weight82.86, auPRC; chromosome-fold protocol.')
    code('label-utility','bend/utils/sequences.py','Available label_dict includes a nine-class strand-aware CDS/intron/donor/acceptor/noncoding map in which UTRs are noncoding. Other alternative label maps also exist; presence of those maps does not establish additional released UTR targets.')
    variants=code('variant-readout','scripts/predict_variant_effects.py','Frozen reference/alternate embedding cosine distance at a configured embedding index; autoregressive models have only left context. No new supervised variant classifier is fitted.')
    gene=evidence('bend1-gene-method','§3.1, Table1, AppendixA.1.1 andA.7',
        'Paper reports 5,976 gene-centred instances, 1,433–14,000 bp; nine strand-aware exon/intron/donor/acceptor/noncoding labels. GENCODE 44 HAVANA coding genes with transcript support and confidence levels 1 or 2; choose the best-supported isoform, breaking ties randomly. GraphPart/global protein alignments split at 80% mature-protein identity; Table 1 reports 4,780/597/597 train/validation/test. Primary MCC over all bases; no cohort-wide chain exact-match score. AUGUSTUS comparison requires exactly one gene with UTR prediction off. This is dense mixed labeling, not an all-isoform or UTR recovery benchmark.')
    enhancer=evidence('bend1-enhancer-method','§3.2, Table1, AppendixA.1.2 andA.7',
        '285 human TSS-centred 100,096-bp windows; 782 binary 128-bp labels per window. CRISPRi-validated enhancer–gene links within 50,048 bp; ABC-only predicted links excluded; multiple enhancers can be positive in a window. Ten chromosome groups for cross-validation; auPRC over labels. Negative/unlabelled bins are not an exhaustive experimentally disproven enhancer set.')
    chrom=evidence('bend1-chromatin-method','§3.3, Table1, AppendixA.1.3',
        '2,005,617 supplied 512-bp windows with 125 cell-type accessibility labels, not 125 genomic positions. Test chr1/8/9: 372,153; validation chr2/4: 279,422; remaining training: 1,354,042. Mean per-label AUROC. Released config names GRCh37 for accessibility while gene/other configs name GRCh38; exact coordinate-build verification is not replaced by a blanket assembly assumption.')
    hist=evidence('bend1-histone-method','§3.4, Table1, AppendixA.1.4',
        '512-bp windows with 18 ChIP experiment outputs covering 11 histone marks in K562. Training: 420,713; validation: 70,801 on chr2/4; test: 120,567 on chr1/8/9. The output vector indexes experiments, not genome positions; mean per-label AUROC.')
    cpg=evidence('bend1-cpg-method','§3.5, Table1, AppendixA.1.5',
        '959,039 supplied CpG-centred 512-bp windows; seven cell-line WGBS labels. Require at least four reads, ≥90%/<10% methylation and measurements in all seven experiments. Training: 743,095; validation: 109,717 on chr5/9/22; test: 106,227 on chr4/13/19/21. Appendix composition says 19 labels, inconsistent with §3.5/Table 1 and the released seven-output config; do not propagate 19 as a measured target count.')
    expr=evidence('bend1-expression-method','§3.6, Table1, AppendixA.1.6',
        'DeepSEA/GRASP expression-associated versus 1000 Genomes background SNVs; fold 0, liftOver and reference-base concordance filters; 512-bp paper context. Table 1 reports 105,263 evaluation variants. Appendix source counts of 98,221 background and 8,000 positive variants must not be silently equated to the filtered total. Whole-cohort embedding-distance AUROC; no additional benchmark fitting.')
    disease=evidence('bend1-disease-method','§3.6, Table1, AppendixA.1.7',
        'ClinVar noncoding SNV pathogenicity: 295,495 variants in Table 1. Use 512-bp context and reference/alternate embedding distance, with zero-shot AUROC. Source-specific consequence/review filtering; exact eligibility not independently reconstructed in this follow-up.')
    specs=[
        ('gene-finding','Dense gene-element labeling','GENCODE44/HAVANA','Nine strand-aware gene-element labels','dense multiclass classification',gene,['gene','cds','exon','intron','splice','intergenic'],['genome-annotation'],['dense-annotation'],9,'1,433–14,000bp',[(4780,'train'),(597,'validation'),(597,'test')],'GraphPart at80% global mature-protein identity;80/10/10gene-instance splits. Not chromosome holdout.','mcc'),
        ('enhancer-annotation','Dense gene-linked enhancer labels','CRISPRi enhancer–gene links','Enhancer membership per128bpbin','dense binary classification',enhancer,['enhancer'],['regulatory-engineering','target-discovery'],['dense-annotation','functional-prediction'],782,'100,096bp',[(285,'all ten folds')],'Ten chromosome groups: chr7/8/18;10/X/13;14/22/6;20/3;11/12;19;4/5;15/21/2;1/16;17/9.','auprc'),
        ('accessibility','Window chromatin accessibility','ENCODE DNase peaks','125cell-type open/closed labels','multilabel classification',chrom,['regulatory'],['regulatory-engineering'],['functional-prediction'],125,'512bp',[(1354042,'train'),(279422,'validation'),(372153,'test')],'Testchr1/8/9;validationchr2/4;otherchromosomes train.','auroc'),
        ('histone','Window histone modifications','ENCODE K562 ChIP peaks','18experiment peak labels /11histone marks','multilabel classification',hist,['genome'],['regulatory-engineering'],['functional-prediction'],18,'512bp',[(420713,'train'),(70801,'validation'),(120567,'test')],'Testchr1/8/9;validationchr2/4;otherchromosomes train.','auroc'),
        ('cpg','Known-CpG methylation','ENCODE WGBS','Seven cell-line methylation states at suppliedCpG','multilabel classification',cpg,['genome'],['genome-annotation'],['functional-prediction'],7,'512bp',[(743095,'train'),(109717,'validation'),(106227,'test')],'Testchr4/13/19/21;validationchr5/9/22;remainingchromosomes train.','auroc'),
        ('expression-variant','Expression-associated noncoding variants','DeepSEA/GRASP/1000Genomes','Expression-associated versus background SNV','binary classification',expr,['genome'],['variant-interpretation','target-discovery'],['variant-effects'],1,'512bp',[(105263,'evaluation')],'Entire filteredfold0variant cohort; noadditional supervised fitting.','auroc'),
        ('disease-variant','Clinical noncoding variants','ClinVar / original BEND release','Noncoding SNV pathogenicity','binary classification',disease,['genome'],['variant-interpretation'],['variant-effects'],1,'512bp',[(295495,'evaluation')],'Entire filteredClinVarcohort; noadditional supervised fitting.','auroc')]
    for slug,name,dataset,target,typ,eid,features,apps,caps,n,length,counts,split,metric in specs:
        tid='bend1-'+slug
        statement=next(e['statement'] for e in d['evidence'] if e['id']==eid)
        put('tasks',dict(id=tid,name='Original BEND: '+name,dataset_name=dataset,target=target,description=statement,
            task_type=typ,label_basis='Reference annotations or experimental measurements with source-specific eligibility.',status='paper-audited',evidence_id=eid,
            limitations='Paper and selected release configuration/scoring code inspected; counts are reported, not measured artifact rows. This is original BEND, not BEND2. Exact label and partition artifacts remain separate checks.',
            input_description=length+'human genomic sequence; frozen position-aligned embeddings for main framework.',output_description=target))
        put('evaluation_tasks',dict(evaluation_id='bend-original',task_id=tid,variant_id=None,note='Original seven-task BEND release; do not substitute BEND2.',evidence_id=eid),('evaluation_id','task_id'))
        put('task_populations',dict(task_id=tid,population_id='human',variant_id=None,relation='sequence-origin',coverage='Human reference/variant cohort specified by original BEND.',evidence_id=eid),('task_id','population_id','relation'))
        for cid in features+apps+caps:
            put('task_categories',dict(task_id=tid,category_id=cid,relation='target',rationale='Original BEND target definition and release output dimensions.',evidence_id=eid,attribution='curatorial'),('task_id','category_id','relation'))
        pid=tid+'-protocol';zero='variant' in slug
        put('protocols',dict(id=pid,task_id=tid,variant_id=None,name='Original BEND frozen-embedding protocol',adaptation='zero-shot embedding distance' if zero else 'frozen backbone; trained CNN head',
            requires_embeddings=True,model_interface='Reference/alternate cosine distance at configured embedding index' if zero else 'Position-aligned embeddings → shallow CNN, optionally pooled/binned',
            fitted_component='None' if zero else 'Task-specific CNN head',selection='Training/checkpoint settings inAppendixA.7; exact artifact reconciliation remains qualified.',
            split_rule=split,split_unit='variant' if zero else 'protein-identity group' if slug=='gene-finding' else 'chromosome',source_evidence_id=variants if zero else eid,
            notes='Paper cohort and released scoring interface; no original Evo2 evaluation claimed. Input assembly/token-to-position upsampling varies by task/model.'))
        put('protocol_metrics',dict(protocol_id=pid,metric_id=metric,aggregation='All assessed positions/bins' if slug in ('gene-finding','enhancer-annotation') else 'Mean per-output AUROC' if not zero else 'All eligible variants',is_primary=1,evidence_id=eid),('protocol_id','metric_id'))
        put('variants',dict(id=tid+'-targets',task_id=tid,name='Original BEND target dimensions',dataset_revision='arXivv4 / pinned release config',context='Human genomic coordinates; target classes/experiments, not new tasks.',input_length=length,target_count=n,target_unit='position bins' if slug=='enhancer-annotation' else 'classes / outputs',notes='Gene finding has nine classes at everybase; enhancer has one binary channel over782bins; assay vectors are not positional.',evidence_id=dims))
        for i,(value,part) in enumerate(counts):
            put('counts',dict(id=tid+'-reported-'+str(i),task_id=tid,variant_id=None,protocol_id=pid,split=part,value=value,unit='sequence windows' if not zero else 'variants',qualifier='Reported Table1; post-filter evaluation count may differ from upstream source counts. Not an artifact recount.',method='reported',evidence_id=eid))
        m=copy.deepcopy(next(m for m in d['coverage_mappings'] if m['task_id']=='evo-clinvar' and m['population_id']=='human'))
        m.update(id=tid+'-mapping-0',task_id=tid,evidence_id=eid)
        md=json.loads(m['metadata_json']);md.update(url='https://arxiv.org/html/2311.12570v4',note='Original BEND human evaluation; no projection from model training taxa.')
        m['metadata_json']=json.dumps(md,ensure_ascii=False);put('coverage_mappings',m)
    suite=next(r for r in d['evaluations'] if r['id']=='bend-original')
    suite.update(status='paper-audited',scope_note='Seven dataset × target tasks decomposed from the original paper. Reported counts and selected code inspection do not certify data/split artifacts.',
        notes='Gene finding is dense mixed gene-element labeling scored byMCC, not whole-chain exact matching. Enhancer annotation is a binary positional track, not continuous assay-signal regression. Assay-label vectors are window-level.',evidence_id=gene)
    stats=json.loads((ROOT/'data/bend-output-artifact-inspections.json').read_text())
    for st in stats:
        tid='bend1-'+('gene-finding' if st['task']=='gene_finding' else 'enhancer-annotation')
        sid=tid+'-released-bed';path='research/artifacts/splice-audit/'+st['file']
        put('sources',dict(id=sid,title='Original BEND released '+st['file'],kind='dataset-file',url=st['url'],version='ERDA public share; retrieved2026-11-27; byte SHA-256 recorded',retrieved='2026-11-27',sha256=st['sha256'],local_path=path,availability='available',notes='Complete BED scanned. Mutable share is identified by recorded byte hash; not an immutable release claim.'))
        eid=evidence(sid+'-inspection','Complete BED scan; data/bend-output-artifact-inspections.json',
            f"{st['rows']:,} rows; split counts {st['split_counts']}; {st['unique_ids']:,} unique identifiers; coordinate spans {st['coordinate_span_min']:,}–{st['coordinate_span_max']:,} bp. Duplicate IDs: {st['duplicate_ids']}. Cross-split identifier overlap: {st['row_id_overlap_between_splits']}. Does not verify protein homology, nucleotide overlap or label truth.",sid,basis='data')
        task=next(r for r in d['tasks'] if r['id']==tid)
        task.update(status='artifact-audited',limitations=task['limitations']+' Complete released BED scanned; reported and measured counts differ for gene finding. The gene-label HDF5 was not downloaded; coordinate and protein-homology overlap are not certified.')
        for split,value in st['split_counts'].items():
            put('counts',dict(id=tid+'-measured-'+split,task_id=tid,variant_id=None,protocol_id=tid+'-protocol',split=split,value=value,
                unit='BED coordinate rows',qualifier='Complete released BED scan; includes repeated identifiers where present. Not an independently validated biological-example count.',method='measured',evidence_id=eid))
        put('field_evidence',dict(entity_table='tasks',entity_id=tid,field='input_description',evidence_id=eid,note='Released coordinate lengths and partition rows; paper input ranges are retained separately.'),('entity_table','entity_id','field','evidence_id'))
        if st['task']=='gene_finding':
            put('findings',dict(id='bend1-gene-count-discrepancy',task_id=tid,evaluation_id='bend-original',severity='discrepancy',
                description='Paper Table 1 reports 5,976 instances and 4,780/597/597 train/validation/test (sum 5,974). Released BED has 5,977 rows: 4,783 train, 597 valid, 597 test, with 5,974 distinct transcript IDs. Three duplicate IDs are within train only; no cross-split transcript IDs overlap. BED spans 1,433–13,000 bp; paper reports up to 14,000 bp and BED also carries flank metadata. Actual historical precomputed-input lengths and the gene-label HDF5 remain unverified. Counts are retained by source/stage, not silently replaced.',evidence_id=eid))
        else:
            h=st['label_hdf5'];url=st['url'].replace('.bed','.hdf5');hsid=tid+'-label-file'
            put('sources',dict(id=hsid,title='Original BEND enhancer label HDF5',kind='dataset-file',url=url,version='ERDA share; retrieved2026-11-27',retrieved='2026-11-27',sha256=h['sha256'],local_path='research/artifacts/splice-audit/enhancer_annotation.hdf5',availability='available',notes='Complete label dataset scanned; does not independently validate the underlying CRISPRi experiments.'))
            he=evidence(hsid+'-inspection','HDF5 labels; complete285-vector scan',
                '285 vectors, each with 782 entries; values 0.0/1.0 only; 220,185 negative and 2,685 positive bins, 222,870 total. BED windows all span 100,096 bp and partition chromosomes match the paper. This is dense binary annotation, not a quantitative assay profile.',hsid,basis='data')
            task['limitations']='Complete BED and enhancer-label HDF5 inspected; shapes, binary values, counts and chromosome groups verified. Underlying CRISPRi label validity and full historical inference/scoring were not independently reproduced.'
            put('counts',dict(id=tid+'-measured-positive-bins',task_id=tid,variant_id=None,protocol_id=tid+'-protocol',split='all ten folds',value=2685,unit='positive128bpoutput bins',qualifier='Complete label-array scan; bins are not independent enhancer loci or experimental interventions.',method='measured',evidence_id=he))
            for field in ['output_description','label_basis']:
                put('field_evidence',dict(entity_table='tasks',entity_id=tid,field=field,evidence_id=he,note='Full label-array shape and values inspected.'),('entity_table','entity_id','field','evidence_id'))
    return d


if __name__=='__main__':
    p=ROOT/'data/catalogue.json';p.write_text(json.dumps(populate(json.loads(p.read_text())),ensure_ascii=False,indent=2)+'\n')
