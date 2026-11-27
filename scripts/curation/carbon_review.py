"""Carbon paper, complete small releases and selective long-context artifact audit."""
import json
from common import Catalogue, ROOT

REV='4ca3ce3e5c55e5821d6068bac5c6e3806027a26f'
BASE='https://github.com/huggingface/carbon/blob/'+REV+'/'


def populate(d):
    c=Catalogue(d)
    def code(slug,path,statement):
        sid=c.source('carbon-final-'+slug,'Carbon: '+path,BASE+path,'repository-file',REV)
        return c.evidence(sid,sid,path,statement,'code')
    inspection=c.source('carbon-final-inspections','Carbon release artifact inspection',
        'https://github.com/eric-czech/marin-glm/blob/main/data/carbon-artifact-inspections.json',
        'dataset',path='data/carbon-artifact-inspections.json')
    measured=c.evidence('carbon-final-measured',inspection,'All files; columns, hashes, labels, lengths and sequence checks',
        'Full Parquet row scan: both ClinVar files, all six perturbation files, all seven DREAM files and the four 4k-token NIAH configurations. '+
        'The larger NIAH DNA columns were not downloaded; every metadata row in all 24 configurations was checked separately.', 'data')
    meta_sid=c.source('carbon-final-niah-metadata','Genomic-NIAH complete metadata-column inspection',
        'https://github.com/eric-czech/marin-glm/blob/main/data/carbon-niah-metadata-inspections.json','dataset',
        path='data/carbon-niah-metadata-inspections.json')
    meta=c.evidence('carbon-final-niah-metadata',meta_sid,'24 configurations × 500 metadata rows',
        'All 12,000 metadata rows checked. Each cell has 125 haystacks in each source bin animalia/fungi/plantae/protista and 100 needles at each depth 10/25/50/75/90. '+
        'Keys/values are 24 bp; near-needle configurations have eight distractors. The four shortest DNA payloads were fully scanned; larger payloads received metadata-column inspection.', 'data')
    def hf(slug,repo,rev,title,statement):
        sid=c.source('carbon-final-data-'+slug,title,'https://huggingface.co/datasets/'+repo+'/tree/'+rev,'dataset',rev)
        ev=c.evidence('carbon-final-data-'+slug,sid,'Pinned dataset inventory and complete cached Parquet inspection',statement,'data')
        rid=c.resource('carbon-final-data-'+slug,sid,title,'dataset','huggingface',
            'https://huggingface.co/datasets/'+repo+'/tree/'+rev,ev,revision=rev)
        c.collection_resource('carbon-evals',rid,ev)
        return ev,rid
    clin,clinres=hf('clinvar','HuggingFaceBio/clinvar-vep','8bb56328a144030c718cd430610ce601a0cd57c0',
        'Carbon coding and noncoding ClinVar variants',
        'Coding: 39,473 rows (17,231 benign, 22,242 pathogenic). Noncoding: 15,258 balanced rows, comprising 10,310 intronic, 4,174 5′ UTR and 774 3′ UTR variants. These are Carbon-specific retained cohorts, not Evo 2 ClinVar cohorts.')
    pert,pertres=hf('perturbations','HuggingFaceBio/perturbation-bench','a251a7e8316c1eac02cf70b8fc2a5d1540a61edc',
        'Carbon paired sequence perturbations',
        'Current configurations: motif_human 20,000 pairs, syn_human 20,000, syn_mouse 20,000, promoter_revcomp 16,451. '+
        'All current pairs retain 8,192-bp length and unchanged sequence outside the patch. CAG replacement exceeds the annotated CDS in 3,669 rows; one pair is identical. '+
        'Synonymous patches remain within CDS and preserve translation in at least one independently checked reading frame. Two older 5,000-row files are separate legacy cohorts.')
    niah,niahres=hf('niah','HuggingFaceBio/genomic-niah','cb8f5903383761a82b10247a20276cc39737e1c7',
        'Genomic-NIAH key–value retrieval',
        '24 configurations: four difficulty settings × six context lengths, 500 examples each. Context length is reported in 6-mer tokens (4,096–131,072), corresponding to 24,576–786,432 DNA bases before query overhead.')
    dream,dreamres=hf('dream','HuggingFaceBio/random-promoter-dream-2022','095ecf8da1e69d70c21812af809df7b19c7d8a84',
        'Random Promoter DREAM supervised library',
        'The two training shards contain 6,065,325 rows; validation 673,925 and labeled test 71,103. Separate unlabeled test and membership files do not add labeled supervised test examples. All activity labels were finite.')
    vepcode=code('vep-code','carbon/evaluation/README.md',
        'The evaluator distinguishes terminal-base 24-kb ClinVar scoring from centered 8,192-bp BRCA2 and TraitGym full-sequence likelihood differences. '+
        'BRCA2 PR area is trapezoidal; TraitGym uses sklearn average precision, aggregated with chromosome weights.')
    clinscorer=code('clinvar-scorer','carbon/evaluation/clinvar_vep_eval.py',
        'ClinVar score is log(P(ref)/P(alt)) from the terminal-next-token base marginal. AUROC uses pathogenic label 1; PR area is sklearn auc(recall, precision) over precision_recall_curve, including each region breakdown. This is trapezoidal area, not sklearn average precision.')
    sharedscorer=code('shared-vep-scorer','carbon/evaluation/vep_eval.py',
        'Global BRCA2 PR area uses trapezoidal auc(recall, precision). TraitGym headline uses per-chromosome average_precision_score, weights by retained classified row count, excludes chromosomes without both classes and renormalizes remaining weights. Global PR area and chromosome-weighted AP are both saved but are different metrics. Reference/alternate full-window likelihood delta is negated for LOF classification.')
    pertcode=code('perturbation-code','carbon/evaluation/perturbation_tasks.py',
        'TASKS maps four configurations to mean sequence likelihood preference accuracy. The released motif task uses replacement, not a length-expanding insertion; promoter_revcomp is a separately supported release example.')
    niahcode=code('niah-code','carbon/evaluation/genome_niah_eval.py',
        'The release supports paired positive/negative likelihood discrimination and greedy value generation, scored by exact match and base-level accuracy. Retrieval is synthetic; genomic haystack sequence does not make it a regulatory assay.')
    # Use the inspected path rather than implying that a results table is raw data.
    mal=code('malinois-code','carbon/training/finetuning/malinois/malinois_train.py',
        'Gosai MPRA labels: K562/HepG2/SK-N-SH log2 fold changes. Validation chromosomes 19,21, X; test 7,13. '+
        'Full fine-tuning with train-fitted z scores, MSE, reverse-complement train duplication, high-activity duplication and reverse-complement averaged evaluation. Validation mean Pearson selects the checkpoint.')
    malsource=c.source('carbon-final-malinois-data','Gosai et al. source MPRA table',
        'https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41586-024-08070-z/MediaObjects/41586_2024_8070_MOESM4_ESM.txt','dataset')
    malres=c.resource('carbon-final-malinois-data',malsource,'Gosai MPRA source activity table','dataset','other',
        c.get('sources',malsource)['url'],mal,notes='Original upstream table URL used by the released Carbon loader; not a Carbon-specific training-subset manifest.')
    c.task_resource('carbon-malinois',malres,mal,'upstream-data')
    dreamcode=c.source('carbon-final-dream-construction','DREAM dataset conversion script',
        'https://huggingface.co/datasets/HuggingFaceBio/random-promoter-dream-2022/blob/095ecf8da1e69d70c21812af809df7b19c7d8a84/create_dataset.py',
        'repository-file','095ecf8da1e69d70c21812af809df7b19c7d8a84')
    dreamev=c.evidence('carbon-final-dream-construction',dreamcode,'SOURCE_FILES; build_supervised_dataset',
        'Conversion retains the separate Zenodo 10633252 train.txt, val.txt and filtered_test_data_with_MAUDE_expression.txt files; it does not create a fresh chromosome split or random repartition.', 'code')
    for tid in ['carbon-clinvar-coding','carbon-clinvar-noncoding']:
        c.get('tasks',tid).update(status='artifact-audited',limitations='This release differs from Evo 2 ClinVar in cohort and scoring context. Source-defined train/test names do not imply pretraining exclusion.')
        c.task_resource(tid,clinres,clin)
        c.protocol(tid+'-protocol',tid,'Carbon terminal-base ClinVar scoring','zero-shot',
            'Marginalized nucleotide probability from the terminal 6-mer; 24-kb upstream DNA context',
            'External retained ClinVar cohort; no downstream fitted classifier. Coding and balanced intron/UTR cohorts are scored separately.',
            'variant',clinscorer,metrics=[('auroc','per coding/noncoding cohort'),('auprc','Trapezoidal sklearn auc(recall, precision), not average precision; per coding/noncoding cohort')])
        c.count(tid,39473 if tid.endswith('-coding') else 15258,'variants',clin,method='measured')
        c.field('tasks',tid,'label_basis',clin)
        c.review('tasks',tid,'Full report methods, released evaluator and complete variant/label metadata scan.',[clin,measured,vepcode,clinscorer])
    for tid in ['carbon-clinvar-coding','carbon-clinvar-noncoding']:
        c.output(tid,'isolated',clinscorer,'Scalar pathogenicity score from terminal-base reference/alternate probabilities','variant',
            rationale='The current Carbon-specific cohort is scored one variant at a time; coding/noncoding labels do not define a dense position axis.')
    for pid,tid,is_trait in [('carbon-evo-brca2','evo-brca2',False),('carbon-traitgym-mendelian','traitgym-mendelian',True)]:
        d['protocol_metrics']=[r for r in d['protocol_metrics'] if r['protocol_id']!=pid]
        metrics=[('ap','Chromosome-row-weighted sklearn AP; omit single-class chromosomes and renormalize weights'),('auroc','Chromosome-row-weighted AUROC; same eligible chromosome set')] if is_trait else [('auroc','Global LOF versus FUNC/INT'),('auprc','Global trapezoidal sklearn auc(recall, precision), not AP')]
        c.protocol(pid,tid,'Carbon centered-window '+('TraitGym Mendelian' if is_trait else 'BRCA2')+' scoring','zero-shot',
            'Full-sequence alternate-minus-reference likelihood on centered 8,192 bp windows; reverse-complement averaging enabled for TraitGym',
            'No downstream fitted classifier. BRCA2 informed training ablation selection; TraitGym Mendelian was held out from that selection.',
            'variant',sharedscorer,metrics=metrics,
            notes='Release README gives 6,836 BRCA2 rows versus 6,840 source measurements in the report; canonical original-study cohort counts are not overwritten by this adapter count. TraitGym headline AP and global PR area have different numerical definitions.')
        if is_trait:
            for metric in d['protocol_metrics']:
                if metric['protocol_id']==pid and metric['metric_id']=='auroc':metric['is_primary']=False
        c.review('protocols',pid,'Complete pinned likelihood adapter, binary-label handling and distinct global/chromosome aggregation code inspected.',[sharedscorer,vepcode])
    trait_rev='6eceaea880a6bc503b95fe4da5550acf4b9bf59e'
    trait_sid=c.source('carbon-final-traitgym-window-data','Carbon TraitGym centered-window derivative',
        'https://huggingface.co/datasets/HuggingFaceBio/traitgym/blob/'+trait_rev+'/mendelian_traits_vep.parquet',
        'dataset-file',trait_rev)
    shared_inspection=c.source('carbon-final-shared-inspections','Carbon shared-target artifact inspection',
        'https://github.com/eric-czech/marin-glm/blob/main/data/existing-benchmark-inspections.json','dataset',
        path='data/existing-benchmark-inspections.json')
    trait=c.evidence('carbon-final-traitgym-window-inspection',shared_inspection,'residual.carbon_traitgym',
        'Complete Carbon Mendelian derivative: 3,380 unique SNVs, 338 positives and 3,042 matched controls across 19 chromosomes. All reference/alternate sequences are 8,192 bp and differ only at position 4,096 with the declared alleles. '+
        'All variant keys and eight shared label/matching fields match native songlab/TraitGym matched-9 revision 1fde19555fe8c0a55b1382bdf4c6f7082209f566 after key alignment; chromosome sorting changes row order. The derivative adds DNA windows and adapter class strings; LOF here means the causal label, not an experimentally measured loss-of-function assay.', 'data')
    traitres=c.resource('carbon-final-traitgym-window-data',trait_sid,'TraitGym Mendelian: Carbon 8,192-bp windows','dataset','huggingface',
        c.get('sources',trait_sid)['url'],trait,revision=trait_rev,
        notes='Fully scanned derivative of the native matched-9 variant cohort. Native TraitGym data and Carbon window preprocessing are distinct resources.')
    traitvid='traitgym-mendelian-carbon-8192bp'
    c.put('variants',dict(id=traitvid,task_id='traitgym-mendelian',name='Carbon centered-window matched-9 derivative',
        evidence_id=trait,context='Same native variant identities/labels; Carbon-prepared hg38 DNA windows and class-string adapter',
        input_length='8192 bp',dataset_revision=trait_rev,target_count=1,target_unit='causal versus matched-control label',
        notes='338 positive and 3,042 control rows. Causal labels are encoded as LOF solely for the shared scorer interface.'))
    c.get('protocols','carbon-traitgym-mendelian')['variant_id']=traitvid
    c.count('traitgym-mendelian',3380,'variants',trait,split='Carbon matched-9 test',variant=traitvid,protocol='carbon-traitgym-mendelian',method='measured')
    c.task_resource('traitgym-mendelian',traitres,trait,variant=traitvid)
    c.collection_resource('carbon-evals',traitres,trait)
    c.field('protocols','carbon-traitgym-mendelian','variant_id',trait)
    brca_sid=c.source('carbon-final-brca2-data-access','Carbon BRCA2 evaluation dataset API',
        'https://huggingface.co/api/datasets/HuggingFaceBio/brca2-vep','dataset')
    c.get('sources',brca_sid)['availability']='not-retrieved'
    brca_access=c.evidence('carbon-final-brca2-data-access',brca_sid,'Public dataset API, 2026-11-27',
        'The official public API returned HTTP 401. The released evaluation README names brca2_vep.parquet and reports 6,836 rows, while the Carbon report states 6,840 source measurements; the retained Carbon cohort cannot be independently equated to the original Evo cohort.', 'documentation')
    brcares=c.resource('carbon-final-brca2-data',brca_sid,'Carbon BRCA2 retained evaluation cohort','dataset','huggingface',
        'https://huggingface.co/datasets/HuggingFaceBio/brca2-vep',brca_access,availability='not-retrieved',
        notes='Official dataset API returned 401. No inference about private/gated/deleted status or exact cohort membership is made.')
    c.task_resource('evo-brca2',brcares,brca_access,note='Carbon-specific cohort; access and report/README count difference are recorded on the Carbon protocol.')
    c.collection_resource('carbon-evals',brcares,brca_access)
    c.limit('protocols','carbon-evo-brca2','retained-cohort','not-retrieved',
        'The Carbon BRCA2 API returned 401; its retained row IDs, exact count and equivalence to other published BRCA2 cohorts are not independently established. Report: 6,840 source measurements; current README: 6,836 retained rows.',brca_access)
    for feature in ['intron','utr5','utr3']:
        c.category('carbon-clinvar-noncoding',feature,clin,'Actual released noncoding rows carry this region subtype.','target')
    c.get('tasks','carbon-triplet').update(name='CAG-repeat replacement diagnostic',target='Natural versus CAG-replaced sequence likelihood',
        description='Compare natural human sequence windows with a 30-bp (CAG)10 replacement. The released patch is length-preserving and is not confined to CDS in every example.',
        status='artifact-audited',limitations='The report calls this an insertion/expansion in CDS. The release replaces 30 bases, extends beyond annotated CDS in 3,669 of 20,000 rows, and contains one identical pair. Neither version measures an experimental disease phenotype.')
    c.put('task_feature_scopes',dict(id='carbon-triplet-cds-scope',task_id='carbon-triplet',feature_id='cds',scope='mixed',
        rationale='The actual release contains 3,669 patches extending beyond annotated CDS; this is not a CDS-only evaluated target.',evidence_id=pert),('task_id','feature_id'))
    c.limit('tasks','carbon-triplet','paper-release-perturbation','conflicting',c.get('tasks','carbon-triplet')['limitations'],pert)
    c.get('tasks','carbon-synonymous').update(status='artifact-audited',
        description='Natural human/mouse CDS-containing windows versus highest-frequency synonymous replacements; released patches stay inside annotated CDS.',
        limitations='This is a sequence-likelihood diagnostic, not a measured functional effect. Human and mouse releases each contain 20,000 pairs; the report’s 20,000-example summary is not their combined count.')
    for tid,config,n in [('carbon-triplet','motif_human',20000),('carbon-synonymous','syn_human',20000),('carbon-synonymous','syn_mouse',20000)]:
        vid=tid+'-'+config
        c.put('variants',dict(id=vid,task_id=tid,name=config,evidence_id=pert,context='Current public 8,192-bp paired release',
            input_length='8192 bp',dataset_revision='a251a7e8316c1eac02cf70b8fc2a5d1540a61edc',target_count=1,target_unit='paired preference',notes='Distinct from legacy 5,000-row files.'))
        c.count(tid,n,'sequence pairs',pert,variant=vid,method='measured')
        c.task_resource(tid,pertres,pert)
        c.protocol(tid+'-protocol',tid,'Carbon natural/modified likelihood diagnostic','zero-shot',
            'Mean autoregressive sequence log likelihood; natural score must exceed modified score',
            'Fixed diagnostic release; no fitted head or train/test partition. These tasks informed model development.',
            'sequence pair',pertcode,metrics=[('accuracy','per released configuration')])
        c.output(tid,'diagnostic',pert,'Natural/modified mean-likelihood preference','sequence pair')
        c.review('tasks',tid,'Full report methods, complete paired DNA/annotation scan and released scoring code.',[pert,measured,pertcode])
    tid='carbon-promoter-revcomp'
    c.put('tasks',dict(id=tid,name='Promoter reverse-complement perturbation',dataset_name='Carbon promoter_revcomp release',
        target='Natural versus reversed promoter likelihood',description='Reverse-complement a 300-bp EPDnew human promoter segment inside an unchanged 8,192-bp window.',
        task_type='paired sequence diagnostic',label_basis='Constructed sequence perturbation; no measured expression label',evidence_id=pert,
        status='artifact-audited',limitations='Supported by the current released harness; no original Carbon paper result is asserted. Legacy CDS-named coordinate columns do not make this a coding task.',
        input_description='Natural/modified DNA pair',output_description='Mean-likelihood preference accuracy'))
    c.member(tid,'carbon-evals',pert)
    c.population(tid,'human',pert,'EPDnew 006 human hg38 promoters.')
    for cat in ['model-development','sequence-modeling','promoter']:c.category(tid,cat,pert,'Released promoter-specific paired diagnostic.')
    c.protocol(tid+'-protocol',tid,'Released promoter perturbation example','zero-shot','Paired mean sequence log likelihood',
        'One fixed diagnostic cohort, not a train/test split. No original-paper result is asserted.','sequence pair',pertcode,metrics=[('accuracy','all released pairs')])
    c.use(tid,'carbon','carbon',pertcode,provenance='released-example',note='Released harness supports this dataset; it is not a result in the original report.')
    c.count(tid,16451,'sequence pairs',pert,method='measured')
    c.task_resource(tid,pertres,pert)
    c.output(tid,'diagnostic',pert,'Natural/modified mean-likelihood preference','sequence pair')
    c.review('tasks',tid,'Complete released DNA pair scan and evaluator; source membership separated from original-paper results.',[pert,measured,pertcode])
    c.get('tasks','carbon-niah').update(status='artifact-audited',limitations='Synthetic key–value retrieval in genomic backgrounds. Source metadata bins are not a complete species manifest; “protista” is not a monophyletic taxon. Every metadata row and the shortest DNA contexts were checked; larger DNA payloads were not fully downloaded.')
    c.protocol('carbon-niah-protocol','carbon-niah','Carbon genomic key–value retrieval','zero-shot generation',
        'Greedy continuation of a supplied repeated key; also paired likelihood preference',
        'Four difficulty settings × six lengths; fixed 500-row test cells. Carbon uses 500 examples per cell; reported Evo 2 largest-length runs use 100/60 examples, not the full Carbon denominator.',
        'synthetic key–value example',niahcode,metrics=[('exact-match','all 24 generated bases'),('accuracy','per-base recovery and separately paired likelihood preference')],
        notes='Native training context 32k tokens; report applies YaRN extension. DNA bases and 6-mer tokens are distinct units.')
    c.output('carbon-niah','sequence',niahcode,'Greedy-decoded24 bp value following the query key','synthetic value string',axis='contiguous',
        rationale='The primary endpoint emits and exactly scores a nucleotide string; candidate likelihood discrimination is a separate auxiliary diagnostic, not the headline retrieval score.')
    for metric in d['protocol_metrics']:
        if metric['protocol_id']=='carbon-niah-protocol' and metric['metric_id']=='accuracy':
            metric.update(is_primary=False,aggregation='Auxiliary per-base accuracy over the 24 generated bases; distinct from exact-match retrieval')
    c.protocol('carbon-niah-likelihood-diagnostic','carbon-niah','Genomic-NIAH auxiliary likelihood preference','zero-shot likelihood diagnostic',
        'Compare positive versus negative continuation likelihood over value tokens only',
        'Same fixed public rows as generation; no fitted classifier. The negative value has 24 incorrect bases, so likelihood discrimination can be high despite failed exact retrieval.',
        'positive/negative value pair',niahcode,metrics=[('accuracy','Auxiliary strict LL(positive)>LL(negative); not paper headline')],
        notes='Official README explicitly excludes likelihood preference from the headline retrieval comparison.')
    for metric in d['protocol_metrics']:
        if metric['protocol_id']=='carbon-niah-likelihood-diagnostic':metric['is_primary']=False
    for cap in ['generation','conditional-generation']:c.category('carbon-niah',cap,niahcode,'Greedy generation of the value conditional on a query key and context.','measured')
    c.count('carbon-niah',12000,'released examples',meta,method='measured',qualifier='24 cells × 500; not all baselines scored every released row.')
    c.task_resource('carbon-niah',niahres,niah)
    c.review('tasks','carbon-niah','Full protocol/code, all 24 configuration metadata columns and complete DNA checks for the four shortest configurations.',[niah,meta,measured,niahcode])
    niahpaper=c.evidence('carbon-final-niah-comparison','carbon-paper','§6.5; Figure 5; Table 5',
        'The report uses 500 Carbon examples per context, but reports 100 Evo 2 examples at 64k tokens and 60 at 128k. Figure 5 and Table 5 include 3B under a 4× extension to 128k, despite prose describing its 2× extension to 64k.',
        url=c.get('sources','carbon-paper')['url']+'#page=19')
    niahreadme=c.evidence('carbon-final-niah-readme','carbon-final-vep-code','Genomic-NIAH: metrics; Note on Evo 2 numbers',
        'The pinned official README identifies exact-match generation as the headline, base accuracy and likelihood preference as auxiliary. It documents Evo 2 samples of 100 at 16–32k and 20 at 64k, differing from report Section 6.5.', 'documentation')
    c.field('protocols','carbon-niah-protocol','split_rule',niahpaper)
    c.limit('protocols','carbon-niah-protocol','evo2-comparison-denominators','conflicting',
        'Section 6.5 reports Evo 2 sample counts of 100 at 64k tokens and 60 at 128k. The pinned evaluator README instead documents 100 at 16–32k and 20 at 64k. No complete per-run retained-row manifest connects these different descriptions.',niahreadme)
    c.get('tasks','carbon-dream').update(status='artifact-audited',
        limitations='The report fine-tunes on a 200,000-row training subset; its exact retained IDs are not released. Public source training is larger. Reported simple correlations are not the official weighted DREAM challenge score.')
    c.protocol('carbon-dream-protocol','carbon-dream','Carbon DREAM reporter fine-tuning','full fine-tune',
        'Backbone with scalar activity head; Pearson–Huber objective, one epoch, maximum 512 tokens',
        'Retains upstream separate training, validation and designed-promoter test files. Carbon uses a 200,000-row training subset whose exact IDs are not provided.',
        'reporter construct','carbon-eval-methods',metrics=[('pearson','71,103 labeled test constructs'),('spearman','same test constructs')],
        fitted='Backbone and regression head',selection='Validation selection')
    for split,n in [('source training',6065325),('source validation',673925),('source test',71103)]:c.count('carbon-dream',n,'constructs',dream,split=split,method='measured')
    c.task_resource('carbon-dream',dreamres,dream)
    c.limit('tasks','carbon-dream','training-subset-ids','not-released','The exact 200,000 training example IDs used by Carbon are not supplied by the report or inspected recipe.',dreamev)
    c.review('tasks','carbon-dream','Complete seven-file release scan; source conversion and report-specific training subset/metrics.',[dream,measured,dreamev,'carbon-eval-methods'])
    c.get('tasks','carbon-malinois').update(status='paper-audited',limitations='Training recipe and source table definition inspected; 62,582 test elements are report counts, not an independently reprocessed MPRA cohort.')
    c.protocol('carbon-malinois-protocol','carbon-malinois','Carbon Gosai/Malinois MPRA fine-tuning','full fine-tune',
        'Three-target sequence regressor; MSE on train-z-scored K562/HepG2/SK-N-SH log2FC',
        'Validation chr19/21/X; test chr7/13; remaining eligible chromosomes train. Reverse complements augment training and are averaged at evaluation.',
        'chromosome',mal,metrics=[('pearson','per cell type and mean'),('spearman','per cell type and mean')],
        fitted='Backbone and three-output head',selection='Best validation mean Pearson across three targets')
    c.count('carbon-malinois',62582,'test elements','carbon-eval-methods',split='test')
    c.review('tasks','carbon-malinois','Report regulatory appendix and complete current training/normalization/selection recipe.',[mal,'carbon-eval-methods'])
    transfer=c.evidence('carbon-final-supervised-transfer','carbon-paper','Appendix E.1–E.4; Tables S2–S5',
        'DeepSTARR uses dataset-provided Dev_log2_enrichment_scaled and Hk_log2_enrichment_scaled targets with full fine-tuning and MSE. Reported selected runs use validation checkpoint selection, AdamW, zero weight decay, 5% warmup, maximum 512 tokens: DeepSTARR learning rate 2e-5, batch 64,3 epochs, reduce-on-plateau; DREAM learning rate 2e-5, batch 16,1 epoch, cosine; Malinois learning rate 1e-5, batch 256,3 epochs, reduce-on-plateau.',
        url=c.get('sources','carbon-paper')['url']+'#page=45')
    for tid in ['deepstarr-dev','deepstarr-hk']:
        pid='carbon-'+tid+'-protocol'
        c.protocol(pid,tid,'Carbon DeepSTARR scaled-activity regression','full fine-tune',
            'Joint Dev/Hk sequence-level regression head on dataset-provided scaled log2-enrichment values',
            'Native 402,296/40,570/41,186 train/validation/test rows. Original DeepSTARR holds out chr2R: first half validation, second half test; all released rows include reverse complements.',
            'source genomic interval / augmented construct',transfer,metrics=[('pearson','Per Dev/Hk output; source mean is arithmetic mean of both target correlations')],
            fitted='Full backbone and joint two-output MSE head',selection='Best validation checkpoint;3 epochs, learning rate 2e-5, batch 64,5% warmup, zero weight decay, maximum 512 tokens, reduce-on-plateau scheduler',
            notes='Native and GenerTeam sequence/ID identity and chromosome partitions were separately verified in the DeepSTARR artifact audit. Scaled labels differ from raw GenBench loader targets.')
        if any(e['id']=='final-deepstarr-native-inspection' for e in d['evidence']):
            c.field('protocols',pid,'split_rule','final-deepstarr-native-inspection','Original genomic-coordinate split verified from complete native files; not inferred from the row totals.')
        c.review('protocols',pid,'Full Carbon transfer report and scaled-target protocol; original data lineage/partition evidence retained separately.',[transfer,'carbon-dev-deepstarr' if tid.endswith('-dev') else 'carbon-hk-deepstarr'])
    c.get('protocols','carbon-dream-protocol')['selection']='Best validation checkpoint; one epoch, learning rate 2e-5, batch 16,5% warmup, zero weight decay, maximum 512 tokens, cosine scheduler'
    c.get('protocols','carbon-malinois-protocol')['notes']='Report Table S5: 3 epochs, learning rate 1e-5, batch 256,5% warmup, zero weight decay, maximum 512 tokens, reduce-on-plateau. Scaled target normalization is fitted on training rows only.'
    recovery=code('recovery-code','carbon/evaluation/sequence_recovery.py',
        'Loads GenerTeam/sequence-recovery, with 6,144-bp prompts and 30-base recovery. Taxonomic categories are reporting strata, not a held-out-species protocol.')
    c.member('generator-recovery','carbon-evals',recovery,note='Same underlying sequence-recovery target; Carbon-specific scoring protocol retained.')
    c.protocol('carbon-recovery-protocol','generator-recovery','Carbon RefSeq continuation evaluation','zero-shot generation',
        '6,144-bp prompt; predict next 30 bases (five 6-mer tokens for Carbon)',
        'Released eukaryote/bacteria/others configurations; no established pretraining species or chromosome exclusion.',
        'sequence segment',recovery,metrics=[('accuracy','position-wise 30-base recovery')])
    c.use('generator-recovery','carbon','carbon',recovery,protocol='carbon-recovery-protocol')
    c.review('protocols','carbon-recovery-protocol','Exact released Carbon continuation adapter and shared source identity.',[recovery])
    for p in [r for r in d['protocols'] if r['task_id'].startswith('carbon-')]:
        c.review('protocols',p['id'],'Source-specific interface, adaptation, split/selection and metric review.',[p['source_evidence_id']])
    c.get('evaluations','carbon-evals').update(status='audited',description='Variant likelihood scoring, paired sequence diagnostics, conditional recovery/retrieval and supervised reporter prediction.',
        notes='Complete release inspections and paper/release discrepancies are recorded by task. Added released promoter perturbation is explicitly separate from original-paper results.')
    c.review('evaluations','carbon-evals','All indexed targets decomposed; complete small release scans and selected long-context artifact columns.',[measured,meta,vepcode,pertcode,mal,dreamev,recovery])
    # Carbon-X: raw rows are inaccessible, but the entire released task adapter/scorer
    # implementation is available. Keep source limits instead of invented labels.
    access='carbonx-data-access-result'
    cxres=c.resource('carbonx-dnaintelligence-resource','carbonx-data-access','DNAIntelligenceIndex evaluation subsets',
        'dataset','huggingface','https://huggingface.co/datasets/HuggingFaceBio/DNAIntelligenceIndex/tree/2e156b12ef70c0d2295394f90c885ec450c5c79f',access,
        revision='2e156b12ef70c0d2295394f90c885ec450c5c79f',availability='not-retrieved',notes='Public API/pinned revision returned 401; no claim about the access restriction mechanism.')
    c.collection_resource('carbonx-evals',cxres,access)
    for t in [r for r in d['tasks'] if r['id'].startswith('carbonx-')]:
        ev='carbonx-scorer-'+t['id'].removeprefix('carbonx-')
        t['status']='source-limited'
        c.task_resource(t['id'],cxres,access)
        c.limit('tasks',t['id'],'raw-evaluation-rows','not-retrieved',
            'Pinned public dataset API returned 401. Raw prompts, retained IDs, per-category counts, species composition and biological grouping cannot be established from the public scorer.',access)
        c.review('tasks',t['id'],'Complete released loader, prompt construction, answer verifier and aggregation; official card/report claims cross-checked.',[ev,'carbonx-released-evaluator',access],t['limitations'])
        for p in [r for r in d['protocols'] if r['task_id']==t['id']]:c.review('protocols',p['id'],'Released implementation and exact remaining row-access limits.',[ev,access])
    c.get('evaluations','carbonx-evals')['status']='audited'
    c.review('evaluations','carbonx-evals','All ten dataset × target adapters/scorers and aggregate definitions; failed raw-release access explicitly retained.',
        ['carbonx-released-evaluator','carbonx-evals',access])
    for model,paper,evidences in [('carbon','carbon',['carbon-eval-methods',measured,recovery]),('carbonx','carbonx',['carbonx-evals','carbonx-released-evaluator',access])]:
        c.review('models',model,'Official model/report, evaluation interfaces and original versus current released evaluation use.',evidences)
        c.review('papers',paper,'Full available report/card and released evaluation methods; publication type preserved.',evidences)
    return d
