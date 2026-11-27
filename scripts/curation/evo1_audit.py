"""Evo 1 original Science paper: shared targets, distinct source protocols.

The 2025 semantic-design and 2026 phage-generation additions in the current
repository are not experiments from the 2024 Evo 1 paper.
"""
from pathlib import Path
import json
from common import Catalogue, ROOT

PDF='https://arcinstitute.org/publications/science.ado9336.pdf'
REV='6856bba48bd0b212fb10919bdafc34795338e154'


def populate(d):
    c=Catalogue(d)
    c.source('evo1-paper','Evo 1: complete Science article and methods',PDF,
        version='Science 386 eado9336, 2024-11-15',path='research/artifacts/final-audit/evo1-main.pdf',
        notes='22-page author-hosted version of record. The cover precedes the 21 article pages; PDF page anchors account for it.')
    c.put('papers',dict(id='evo1',title='Sequence modeling and design from molecular to genome scale with Evo',
        year=2024,publication_date='2024-11-15',doi='10.1126/science.ado9336',source_id='evo1-paper',
        status='journal',scope='primary-model',notes='Original Evo 1 paper; distinct from Evo 1.5 semantic design and subsequent phage-generation work.'))
    def pe(slug,page,locator,statement):
        return c.evidence('evo1-'+slug,'evo1-paper',locator+'; PDF page '+str(page),statement,url=PDF+'#page='+str(page))
    architecture=pe('architecture',11,'Materials and methods: architecture, positional embeddings and tokenization, pp.10–11',
        'Seven-billion-parameter autoregressive StripedHyena: 32 blocks, width 4096, 29 Hyena and three rotary-attention layers. Single-nucleotide UTF-8 byte tokenizer with 512 total characters and four effective nucleotide tokens during base pretraining. Context extension uses linear RoPE interpolation.')
    training=pe('training',12,'OpenGenome datasets; Training procedure; Dataloading, pp.11–12',
        'OpenGenome: 300 billion nucleotides from GTDB v214.1 bacterial/archaeal representative genomes, high-confidence IMG/VR v4 prokaryotic viruses and IMG/PR plasmid representatives. Two-stage training at 8192 then 131072 tokens, approximately 340 billion tokens processed. Contig EOS packing; taxonomic prefixes in the long-context stage. Genomic corpus partitions are separate from downstream assay cohorts.')
    fitness=pe('fitness',14,'Protein and ncRNA function prediction, p.13',
        'Nine prokaryotic coding DMS studies and six human studies with original nucleotide-level information; seven ncRNA mutagenesis studies. Evo 8k scores each retained nucleotide sequence with prepended EOS; Spearman against source nucleotide fitness. Synonymous codon variants remain separate observations; stop-codon variants stay in nucleotide evaluation but are excluded from protein-model comparison. No downstream fitting or supervised assay split.')
    regulatory=pe('regulatory',14,'Gene expression prediction from regulatory DNA, pp.13–14',
        'LaFleur: 5193 promoters split randomly into 4673 training / 520 validation, plus a second 5391-promoter validation set. Separate-study test cohorts: Hossain 4350, Urtecho 10898, Yu 1493, Kosuri 12243 promoter–RBS pairs. Background trimmed using the Promoter Calculator maximum-initiation subsequence. Targets are promoter-associated expression and, separately for Kosuri, protein expression. Frozen last-Hyena embeddings feed ridge regression or a CNN; zero-shot likelihood and one-hot baselines are separate. All fitted models train only on LaFleur. Sequence GC and source-study identity are controls, not chromosome partitions.')
    essentiality=pe('essentiality',19,'Gene essentiality prediction, p.18',
        '56 bacterial DEG genome-wide binary essentiality studies, plus lambda NC_001416 and P1 NC_005856 CRISPRi labels from Piya. Gene-only, 8192-bp and 65536-bp contexts; gene-disruption likelihood differences; AUROC and average precision per genome, with 100000 label permutations. Zero-shot, no fitted head; genomes are not asserted absent from pretraining. Evo 1 does not report the two archaeal studies added in Evo 2.')
    crispr=pe('crispr',15,'CRISPR-Cas fine-tuning, sampling evaluation and selected in-vitro validation, pp.14–15; Fig.3',
        'Evo 8k is fine-tuned on CRISPR-Cas loci with Cas9/12/13 class prompts. Generated-locus computational criteria include a Cas profile hit plus CRISPR array, sequence identity/degeneracy and structure filters. Approximately 2 million Cas9 generations were filtered to 11 manually selected candidates for initial in-vitro cleavage; one EvoCas9-1 was active, then the purified complex was characterized. These are selected synthetic candidates, not random held-out natural test sequences or assays of all sampled Cas12/13 systems.')
    transposon=pe('transposon',16,'IS200/IS605 generation, interpretation and experimental validation, pp.15–18; Fig.4',
        'Class-conditioned generation after fine-tuning on IS200/IS605 loci. Profile, identity, structure and RNA filters select candidates; ESMFold evaluates 200 proteins per identity bin, nine bins, three protein contexts (5400 predictions). Selected 24 IS200-like and 24 IS605-like candidates undergo excision/insertion assays; experimental outcome is distinct from predicted fold confidence and sequence annotation. Categorical Jacobian examples test sequence couplings in three natural IS605 loci; no independent contact-prediction cohort.')
    genome=pe('genome',19,'Genome-scale generation and evaluation, pp.18–19; Fig.6',
        'Evo 131k samples 16 approximately 1-Mb sequences, four each from E. coli, K. pneumoniae, S. aureus and M. genitalium taxonomic prompts. CheckM coding density on nonoverlapping crops up to 131072 bp, compared with 100 GTDB genomes and 1000 uniform random 131072-bp sequences. tRNAscan-SE/barrnap locate RNA features. Predicted protein folds are restricted to 100–1024 aa; ESMFold pLDDT, secondary structure and Foldseek/GO annotations are assessed. No experimental whole-genome viability or complete gene-annotation truth.')
    c.put('models',dict(id='evo1',name='Evo 1',scope='primary',paper_id='evo1',description='Autoregressive StripedHyena genomic model trained on prokaryotic genomes, plasmids and phage; 8k and 131k checkpoints with separately fine-tuned CRISPR/transposon models.',evidence_id=architecture,
        notes='Original 2024 model. Current shared repository also contains later Evo 1.5 and phage-design work; those releases do not establish original-paper use.'))
    for slug,category,name,value,eid in [
        ('architecture','architecture','Architecture','7B; 32 blocks; 4096 hidden width; 29 Hyena + 3 rotary-attention layers.',architecture),
        ('tokenizer','tokenization','Tokenization','Single-nucleotide UTF-8 byte representation; 512-character vocabulary. Special characters support downstream class/taxonomy prompts.',architecture),
        ('corpus','pretraining','Pretraining corpus','OpenGenome 300B nt: GTDB v214.1 bacterial/archaeal genomes, IMG/VR v4 prokaryotic viruses, IMG/PR plasmids. Approximately 340B tokens processed.',training),
        ('context','context','Context protocols','8192-token pretraining followed by 131072-token extension with linear RoPE interpolation. Molecular fitness uses the 8k checkpoint; essentiality tests gene-only/8k/64k contexts; genome generation uses the 131k checkpoint with recurrent decoding beyond context.',essentiality),
        ('release','release','Checkpoints and versions','8k base, 131k base, 8k CRISPR and 8k transposon checkpoints cited in the 2024 paper. Current code loads corrected 1.1_fix base revisions; README records an inference bug fixed in v0.3 after 2024-12-16.',training)]:
        c.put('model_properties',dict(id='evo1-'+slug,model_id='evo1',category=category,name=name,variant=None,value=value,status='reported / source-audited',evidence_id=eid,notes=None))
    code_url=f'https://github.com/evo-design/evo/blob/{REV}/evo/scoring.py'
    c.source('evo1-score-code','Evo 1 sequence scoring implementation',code_url,'repository-file',REV,
        'research/artifacts/final-audit/evo1/evo/scoring.py')
    score=c.evidence('evo1-score-code-review','evo1-score-code','prepare_batch and score_sequences, lines 9–98',
        'Prepends tokenizer.eod_id, removes padding and allows mean/sum loglikelihood reduction. This generic release code is not the released filtered assay table or a full reproduction of each paper protocol.','code',code_url+'#L9-L98')
    c.source('evo1-release-readme','Evo releases and inference correction',f'https://github.com/evo-design/evo/blob/{REV}/README.md','repository-file',REV,'research/artifacts/final-audit/evo1/README.md')
    release=c.evidence('evo1-release-review','evo1-release-readme','Checkpoint table and News: 2024-12-17',
        'README distinguishes original Evo 1 checkpoints from Evo 1.5 and later phage work, and documents the Nov 15–Dec 16, 2024 inference bug fixed in release 0.3.','documentation')
    c.get('model_properties','evo1-release')['evidence_id']=release
    c.put('evaluations',dict(id='evo1-original',name='Evo 1 original-paper evaluations',description='Coding/ncRNA fitness, regulatory expression, bacterial/phage essentiality and selected generation experiments in the 2024 Science paper.',paper_id='evo1',source_id='evo1-paper',status='paper-audited',scope_note='Dataset–target records shared with Evo 2 retain separate model protocols and cohort variants. Original use means documented by the 2024 paper, not later code in the same repository.',evidence_id=fitness,notes='Generated-locus filters, predicted structure scores and selected experimental outcomes have different denominators. No whole-genome viability claim.'))
    # The original paper lists the same 15 coding studies and seven ncRNA
    # studies subsequently reused by Evo 2. Preserve canonical IDs/deep links.
    shared=[t['id'] for t in d['tasks'] if t['id'].startswith(('evo-dms-','evo-ncrna-'))]
    for tid in shared:
        t=c.get('tasks',tid)
        t['dataset_name']=t['dataset_name'].replace('Evo 2 selected DMS: ','DMS study: ').replace('Evo 2 selected ncRNA assay: ','ncRNA mutagenesis study: ')
        c.member(tid,'evo1-original',fitness,note='Same named original study as Evo 2; retained nucleotide variants/counts are protocol-specific.')
        pid=c.protocol('evo1-'+tid+'-score',tid,'Evo 1 original-paper likelihood ranking','zero-shot','8k base checkpoint; EOS-prefixed full nucleotide sequence likelihood; no learned assay readout.',
            'No downstream train/validation/test fitting. Retain original unique nucleotide variants, including synonymous codon variants and stop variants for nucleotide models. Original study eligibility is not a pretraining holdout.',
            'retained nucleotide variant within source assay',fitness,[('spearman','Per original source study; prokaryotic, human and ncRNA panels summarized separately.')])
        c.use(tid,'evo1','evo1',fitness,pid,note='Original Science 2024 experiment; separate source protocol from Evo 2.')
        c.field('tasks',tid,'dataset_name',fitness,'Original named study is reused; no new assay is created by another model comparison.')
    for tid in ['evo-deg','evo-phage-essential']:
        c.member(tid,'evo1-original',essentiality,note='Evo 1 reports 56 bacterial genomes and two phages; does not include the Evo 2 archaeal addition.')
        vid='evo1-'+tid+'-cohort'
        c.put('variants',dict(id=vid,task_id=tid,name='Evo 1 Science 2024 cohort',dataset_revision='DEG release version not specified in the inspected method' if tid=='evo-deg' else 'Piya 2018 lambda/P1',context='Gene-only / 8192 bp / 65536 bp',input_length='Variable gene / 8192 / 65536 nt',target_count=1,target_unit='binary gene-essentiality label',notes='Evo 1 uses bacterial studies only in DEG; the canonical task also has an Evo 2 archaeal extension.',evidence_id=essentiality))
        pid=c.protocol('evo1-'+tid+'-score',tid,'Evo 1 original-paper gene disruption','zero-shot','Disrupted-minus-reference sequence loglikelihood; gene-only, 8k and 64k contexts.',
            'External genome-wide labels; no fitted classifier or downstream chromosome split. Per-genome evaluation. Pretraining exclusion is not established by this protocol.',
            'coding gene within genome',essentiality,[('auroc','Per genome; 100000-label-permutation significance.'),('ap','Per genome.')],variant=vid)
        c.use(tid,'evo1','evo1',essentiality,pid,note='Original Evo 1 genome-level assay cohort.')
        c.count(tid,56 if tid=='evo-deg' else 2,'bacterial genomes' if tid=='evo-deg' else 'phage genomes',essentiality,protocol=pid,variant=vid)
    c.get('tasks','evo-deg')['dataset_name']='Database of Essential Genes (DEG)'

    def task(slug,name,dataset,target,description,eid,features,pops,applications,capabilities,
             typ='regression',form='isolated',unit='supplied sequence',limitations=''):
        tid='evo1-'+slug
        c.put('tasks',dict(id=tid,name=name,dataset_name=dataset,target=target,description=description,
            task_type=typ,label_basis='Experimental source measurements' if form=='isolated' else 'Generated sequence; source-defined computational or experimental assessment',status='paper-audited',
            evidence_id=eid,limitations=limitations,input_description='Nucleotide sequence and source-defined conditioning/context.',output_description=target))
        for cat in features+applications+capabilities:c.category(tid,cat,eid,'Assigned from the cited target and evaluation procedure.')
        if 'cds' in features:c.put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope='mixed' if len(features)>1 else 'restricted-target',rationale='Generation of genomic loci contains coding and noncoding components.' if len(features)>1 else 'The target concerns coding sequence specifically.',evidence_id=eid))
        for pop in pops:c.population(tid,pop,eid,'Known sequence/construct origin or stated design context; not inferred from assay host.')
        c.output(tid,form,eid,'Nucleotide sequence' if form=='sequence' else target,unit,limitations=limitations)
        c.member(tid,'evo1-original',eid)
        return tid

    for slug,name,n in [('hossain','Hossain',4350),('urtecho','Urtecho',10898),('yu','Yu',1493),('kosuri','Kosuri',12243)]:
        tid=task('expression-'+slug,name+': promoter-associated expression',name+' promoter activity dataset','Reporter expression associated with promoter DNA',
            'Predict one expression value per supplied promoter/construct. Test data originate in another experimental study than the LaFleur fitted-head training data.',regulatory,['promoter'],['ecoli'],['regulatory-engineering'],['functional-prediction'])
        for arm in ['likelihood','ridge','cnn']:
            pid=c.protocol(tid+'-'+arm,tid,'Evo 1 '+arm+' readout','zero-shot' if arm=='likelihood' else 'frozen embedding probe',
                'EOS-prefixed sequence loglikelihood' if arm=='likelihood' else 'Final Hyena-layer embeddings; sequence-mean 4096-vector for ridge, position-preserving matrix for CNN.',
                'Independent source-study test cohort. Supervised heads fit 4673 LaFleur promoters; random 520 LaFleur validation plus 5391 additional validation. No chromosome partition. Zero-shot uses no downstream fitting.',
                'promoter or promoter–RBS construct',regulatory,[('spearman','Over source-study test examples.')],embeddings=arm!='likelihood',
                fitted=None if arm=='likelihood' else 'RidgeCV on frozen embeddings' if arm=='ridge' else 'Two-layer CNN on frozen embeddings',
                selection='Two LaFleur validation sets guide model development.' if arm!='likelihood' else None)
            c.use(tid,'evo1','evo1',regulatory,pid)
            c.count(tid,n,'constructs',regulatory,split='test',protocol=pid)
        c.count(tid,4673,'promoters',regulatory,split='fitted-head training')
        c.count(tid,520,'promoters',regulatory,split='validation1')
        c.count(tid,5391,'promoters',regulatory,split='validation2')
    tid=task('kosuri-protein','Kosuri: promoter–RBS protein expression','Kosuri 2013 promoter–RBS combinatorial library','Reporter protein expression',
        'Score all 12243 constructs, comparing promoter-only, RBS-only and concatenated inputs. Repeated promoter/RBS sequences remain repeated across constructs.',regulatory,['promoter','utr5'],['ecoli'],['regulatory-engineering'],['functional-prediction'])
    pid=c.protocol(tid+'-score',tid,'Evo 1 promoter/RBS input comparison','zero-shot','EOS-prefixed likelihood; three input variants: promoter, RBS, promoter + RBS.',
        'All 12243 experimental constructs scored without fitting. Repeated subsequences are duplicated to keep the comparison over the same construct cohort.',
        'promoter–RBS construct',regulatory,[('spearman','All 12243 constructs; no deduplication of single-component inputs.')])
    c.use(tid,'evo1','evo1',regulatory,pid);c.count(tid,12243,'constructs',regulatory,protocol=pid)

    generated=[
        ('crispr-loci','CRISPR-Cas locus generation','Evo1 class-conditioned CRISPR-Cas generations','Cas-subtype / array co-occurrence and novelty',crispr,['cds','ncrna','repeat'],['bacteria'],['gene-therapy','protein-engineering'],None),
        ('crispr-cleavage','Selected Cas9–guide cleavage','Eleven selected Evo 1 generated Cas9 systems','In-vitro activity of codesigned protein/guide',crispr,['cds','ncrna'],['bacteria'],['gene-therapy','protein-engineering'],11),
        ('transposon-folds','Transposon-system generation','Evo 1 IS200/IS605 generations','Protein/functional-RNA component plausibility',transposon,['cds','ncrna','repeat'],['bacteria'],['strain-engineering','protein-engineering'],5400),
        ('transposon-activity','Selected transposon activity','Evo 1 generated IS200/IS605 candidates','Cognate protein–DNA excision/insertion activity',transposon,['cds','repeat'],['bacteria'],['strain-engineering'],48),
        ('genome-coding','Generated-genome coding density','Sixteen Evo 1 approximately 1-Mb genomes','Predicted coding density and nucleotide composition',genome,['genome'],['bacteria'],['strain-engineering','microbial-genomics'],16),
        ('genome-rna','Generated-genome RNA content','Sixteen Evo 1 approximately 1-Mb genomes','Predicted tRNA/rRNA occurrence',genome,['trna','rrna','genome'],['bacteria'],['strain-engineering','microbial-genomics'],16),
        ('genome-folds','Generated-genome protein structures','Predicted 100–1024-aa proteins from Evo 1 genomes','Predicted fold confidence and structural matches',genome,['cds','genome'],['bacteria'],['strain-engineering','protein-engineering'],16)]
    for slug,name,dataset,target,eid,features,pops,apps,n in generated:
        limitations='Selected/computational assessment; generation count, filtered-candidate count and functional-success count are distinct. No independent natural-sequence test partition or whole-genome viability inference.'
        tid=task(slug,name,dataset,target,'Generate nucleotide sequences under the source-defined class/taxonomic prompt, then assess the specified endpoint.',eid,features,pops,apps,['generation','conditional-generation'],typ='sequence generation',form='sequence',unit='generated locus/genome or selected experimental construct',limitations=limitations)
        pid=c.protocol(tid+'-generation',tid,'Evo 1 original-paper generation assessment','full fine-tune then generation' if 'crispr' in slug or 'transposon' in slug else 'pretrained generation',
            'Class-conditioned 8k specialist' if 'crispr' in slug or 'transposon' in slug else 'Taxonomy-conditioned 131k model; recurrent generation beyond training context.',
            'No supervised evaluation train/test split. Generated candidates are assessed with explicit computational filters or selected experimental validation; nearest-training sequence comparisons are novelty checks, not a homology-held-out test.',
            'generated or selected sequence',eid,notes=limitations)
        c.use(tid,'evo1','evo1',eid,pid)
        if n:c.count(tid,n,'predicted protein folds' if slug=='transposon-folds' else 'selected constructs' if 'activity' in slug or 'cleavage' in slug else 'generated genomes',eid,protocol=pid,
            qualifier='5400 is structure-prediction count, not distinct functional systems.' if slug=='transposon-folds' else 'Source-reported cohort unit; repeated targets across records are not independent cohorts.')
    # These source-defined numerical or qualitative readouts are not replaced
    # with an invented common generation accuracy.
    for id,name,definition in [('generation-validity','Generated component validity','Source-specific proportion/count of generations containing the required annotated components.'),
        ('predicted-fold-confidence','Predicted fold confidence','Distribution of structure-prediction confidence; not experimentally validated folding.'),
        ('selected-activity','Selected experimental activity','Source-defined cleavage or transposition readout in selected candidates; not an unbiased generation success rate.'),
        ('coding-density','Predicted coding density','Fraction of sequence called coding by the specified annotation tool; not true label accuracy.'),
        ('rna-occurrence','Predicted RNA occurrence','Counts of RNA features called by tRNAscan-SE/barrnap; not experimentally verified transcripts.')]:
        c.put('metrics',dict(id=id,name=name,definition=definition,direction='context-dependent'))
    for slug,metric in [('crispr-loci','generation-validity'),('crispr-cleavage','selected-activity'),('transposon-folds','predicted-fold-confidence'),('transposon-activity','selected-activity'),('genome-coding','coding-density'),('genome-rna','rna-occurrence'),('genome-folds','predicted-fold-confidence')]:
        tid='evo1-'+slug;eid=c.get('tasks',tid)['evidence_id']
        c.put('protocol_metrics',dict(protocol_id=tid+'-generation',metric_id=metric,aggregation='Per source-defined cohort and endpoint; computational versus experimental units remain separate.',is_primary=True,evidence_id=eid),('protocol_id','metric_id'))
    return d


if __name__=='__main__':
    p=ROOT/'data/catalogue.json';p.write_text(json.dumps(populate(json.loads(p.read_text())),ensure_ascii=False,indent=2)+'\n')
