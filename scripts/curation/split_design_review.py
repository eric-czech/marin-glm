"""Source-specific partition designs, separate from measured intersections.

Selectors below name reviewed protocol families. They are not a classifier
inferring a split from a task name, organism or an HF split label.
"""
import json
from common import Catalogue, ROOT


def populate(d):
    c=Catalogue(d)
    protocols={p['id']:p for p in d['protocols']}
    tables=['split_designs','split_design_evaluations','split_design_protocols',
            'split_design_strategies','split_design_evidence']
    for table in tables:d[table]=[]

    def family(prefix='',suffix='',evidence=None):
        rows=[p['id'] for p in d['protocols'] if p['id'].startswith(prefix)
              and p['id'].endswith(suffix) and (not evidence or p['source_evidence_id']==evidence)]
        assert rows,(prefix,suffix,evidence)
        return rows

    def source(id,title,url,locator,statement,basis='code'):
        c.source(id,title,url,'documentation' if basis=='documentation' else 'code' if basis=='code' else 'paper')
        c.evidence(id,id,locator,statement,basis,url)
        return id

    trait_outer=source('split-traitgym-outer','TraitGym chromosome prediction loop',
        'https://github.com/songlab-cal/TraitGym/blob/4d80fe889415ffc02d45c7cb5446a326288819bd/workflow/rules/model.smk#L25-L45',
        'run_classifier, lines 25–45',
        'In chrom mode, iterate over chromosomes, fit on all other chromosomes and predict the omitted chromosome. odd_even and pos_quarter are separate modes, not the headline chrom protocol.')
    trait_inner=source('split-traitgym-inner','TraitGym training-only chromosome-grouped model selection',
        'https://github.com/songlab-cal/TraitGym/blob/4d80fe889415ffc02d45c7cb5446a326288819bd/workflow/rules/common.smk#L515-L550',
        'train_predict and train_logistic_regression, lines 515–550',
        'The outer-training chromosomes are passed to GroupKFold inside GridSearchCV. Ten C values from 1e-8 to 1 are selected by average precision; imputation and standardization are inside the fitted pipeline.')
    for pid in ['traitgym-mendelian-probe','traitgym-complex-probe']:
        p=protocols[pid]
        p['split_rule']='Leave one chromosome out: fit on all other chromosomes and predict the omitted chromosome. Training-only GroupKFold selects logistic-regression C by average precision; imputation and standardization are fitted inside the CV pipeline.'
        p['selection']='Training-only GroupKFold by chromosome inside GridSearchCV over ten logarithmically spaced C values, 1e-8 to 1; optimize average precision. Outer test chromosome is excluded.'
        c.field('protocols',pid,'split_rule',trait_outer)
        c.field('protocols',pid,'split_rule',trait_inner)
        c.field('protocols',pid,'selection',trait_inner)

    nt_native=source('split-nt-revised-native','Nucleotide Transformer final-paper downstream splits',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC11810778/',
        'Methods: Dataset splits and performance evaluation; Fine-tuning / Probing',
        'The final 18-task human benchmark reserves chromosomes 20 and 21 for test. Training-only tenfold validation selects checkpoints and repeats evaluation on the same test set; ten reported runs are not ten independent biological test cohorts.', 'paper')

    notebook_review=json.loads((ROOT/'data/split-construction-review.json').read_text())
    gb_evidence={}
    for r in notebook_review['notebooks']:
        if not r['first_split_line']:continue
        url=r['url']+'#L'+str(r['first_split_line'])
        eid=source('split-gb-'+r['dataset'],'Genomic Benchmarks construction: '+r['dataset'],url,
            'Creation notebook; cells '+', '.join(str(v['cell']) for v in r['cells'] if 'train_test_split(' in v['code']),
            'Each class is shuffled and split independently with random_state=42. Recorded outputs give approximately 75% train and 25% test; no chromosome, gene-family or species holdout is applied.')
        gb_evidence[r['dataset']]=eid
        pid='gb-'+r['dataset']+'-protocol'
        p=protocols[pid]
        p['split_rule']='Class-wise shuffled random 75/25 train/test partition, random_state=42, as recorded in the source creation notebook. No third validation partition and no chromosome/species/homology grouping.'
        p['split_unit']='source interval / sequence row, separately within each class'
        c.field('protocols',pid,'split_rule',eid)
    gb_helper=source('split-gb-ensembl-helper','Pinned Ensembl scraper partition helper',
        'https://github.com/katarinagresova/ensembl_scraper/blob/6d3bba8e6be7f5ead58a3bbaed6a4e8cd35e62fd/scraper/preprocessing.py#L29-L33',
        'split_to_csv, lines 29–33',
        'split_to_csv uses train_test_split(test_size=0.2, random_state=42), called independently for positive and negative intervals. The OCR and regulatory construction notebooks pin this dependency; the human/mouse enhancer notebooks do not pin a revision.')
    enhancer_evidence=[]
    for task in ['human_enhancers_ensembl','dummy_mouse_enhancers_ensembl']:
        notebook=next(r for r in notebook_review['notebooks'] if r['dataset']==task)
        enhancer_evidence.append(source('split-gb-unpinned-'+task,'Genomic Benchmarks unpinned construction dependency: '+task,notebook['url'],
            'Creation notebook: package installation and scraper invocation',
            'The notebook installs ensembl_scraper without a revision and delegates partition construction to it. The notebook itself supplies no chromosome or gene-family exclusion rule; inspecting a later helper cannot prove the historical executable version.'))
    for task in ['human_ocr_ensembl','human_ensembl_regulatory']:
        notebook=next(r for r in notebook_review['notebooks'] if r['dataset']==task)
        eid=source('split-gb-'+task,'Genomic Benchmarks pinned scraper use: '+task,notebook['url'],
            'Creation notebook, dependency installation and scraper invocation',
            'The notebook installs ensembl_scraper at 6d3bba8e6be7f5ead58a3bbaed6a4e8cd35e62fd. Regulatory class files preserve the scraper train/test membership before promoter segments are shortened.')
        gb_evidence[task]=eid
        p=protocols['gb-'+task+'-protocol']
        p['split_rule']='Class-wise random 80/20 train/test, random_state=42, via the pinned Ensembl scraper. Regulatory class files retain membership when combined; promoter segments are shortened after splitting. No chromosome or homology grouping.' if task=='human_ensembl_regulatory' else 'Positive and genome-background intervals are split independently with test_size=0.2 and random_state=42 in the pinned Ensembl scraper. No chromosome or homology grouping.'
        c.field('protocols',p['id'],'split_rule',eid)
        c.field('protocols',p['id'],'split_rule',gb_helper)

    extras=[
        ('gene','Genes or regulatory elements','gene / element identity','Keep variants, isoforms or backgrounds belonging to the same source gene or element together.','Separates measured entities rather than individual rows.','Distinct genes may still be homologous; a gene-ID split is not a sequence-identity threshold.'),
        ('assay','Assays or study cohorts','assay / study cohort','Fit on one experimental library or study cohort and evaluate another.','Tests transfer between the named measurement sources.','Shared genes, sequences, participants or laboratory effects need separate controls.'),
        ('released','Released partitions; construction unspecified','released row membership','Use named source train/validation/test files when the grouping algorithm is not documented.','Preserves the specified release membership.','File names and train/test proportions alone establish no chromosome, taxon or homology exclusion.'),
        ('synthetic','Synthetic prompts or selected designs','prompt / generated design','Construct synthetic prompts or evaluate selected generated candidates.','Defines a generation or diagnostic cohort rather than a natural-genome training holdout.','Prompt selection, oracle training and experimental candidate selection are distinct sources of exposure.'),
    ]
    for i,(key,name,unit,description,protection,limitations) in enumerate(extras,12):
        c.put('split_strategies',dict(id='split-strategy-'+key,name=name,split_unit=unit,description=description,protection=protection,limitations=limitations,sort_order=i))
    c.get('split_strategies','split-strategy-gene-family').update(name='Homology groups or gene families',split_unit='homology group / gene family',description='Group related genes, transcripts or proteins using the named homology map or similarity procedure before partitioning.')

    # A short comparative record links back to the exact source protocols. A
    # model-specific use of a shared task never inherits another user's split.
    def design(key,name,evals,axes,layer,rule,selection,limits,pids=(),eids=(),selection_eids=None,limit_eids=None):
        did='design-'+key
        assert all(pid in protocols for pid in pids),[pid for pid in pids if pid not in protocols]
        assert eids,did
        c.put('split_designs',dict(id=did,name=name,layer=layer,partition_rule=rule,selection_rule=selection,interpretation=limits,sort_order=len(d['split_designs'])))
        for eid in evals.split():c.put('split_design_evaluations',dict(design_id=did,evaluation_id=eid),('design_id','evaluation_id'))
        for pid in dict.fromkeys(pids):c.put('split_design_protocols',dict(design_id=did,protocol_id=pid),('design_id','protocol_id'))
        for axis in axes.split():c.put('split_design_strategies',dict(design_id=did,strategy_id='split-strategy-'+axis),('design_id','strategy_id'))
        for field,ids in [('partition_rule',eids),('selection_rule',selection_eids or eids),('interpretation',limit_eids or eids)]:
            for eid in dict.fromkeys(ids):c.put('split_design_evidence',dict(design_id=did,field=field,evidence_id=eid),('design_id','field','evidence_id'))

    design('evo2-species','Evo 2: exon/intron probe','evo-original','taxon','probe',
        'Initial 94-species panel split 80/10/10 by species; human, mouse and zebrafish manually moved to test. Two sparsely annotated test species removed; eight test species remain.',
        'Layer and probe settings selected using validation species; final fit uses 1,500 positions per training species.',
        'Species exclusion concerns the exon/intron readout. It does not exclude those genomes from Evo 2 pretraining.',
        ['evo-exon-intron-probe'],['evo2-review-exon'])
    design('evo2-brca','Evo 2: fitted BRCA1 readout','evo-original','position','probe',
        'All alleles at one genomic position stay together: 1,060 training positions / 266 test positions, containing 3,104 / 789 SNVs.',
        'Fivefold position-grouped CV inside training chooses embedding layer, pooling width and ridge penalty.',
        'Tests new mutation positions within the same gene. The zero-shot BRCA1/BRCA2 results use fixed cohorts instead.',
        ['evo-brca1-probe'],['evo2-review-brca-probe'])
    design('plantcad-acr','PlantCAD2: cross-species accessibility','plantcad2-ft','taxon chromosome','supervised',
        'Arabidopsis-trained arm uses Arabidopsis chromosome validation and ten other species for test. Nine-species-trained arm reserves maize and barley for test.',
        'LoRA fitting uses the released validation cohorts. These are different training panels, not interchangeable random folds.',
        'Species holdout applies to adaptation. It does not imply those species or homologous regulatory DNA were absent from pretraining.',
        family('plantcad2-ft-cross_species_acr'),['plantcad2-acr'])
    design('plantcad-cell','PlantCAD2: maize cell-type accessibility','plantcad2-ft botanic1-evals','chromosome','supervised',
        'Test is maize chr10; both training and validation contain chr1–9. Released core inputs are 600 bp, with separately evaluated extended contexts.',
        'Validation is a within-training-chromosomes partition; it is not a chromosome-held-out validation set.',
        'Core train/test spans are disjoint, but 18 distinct DNA strings recur across them. Train/validation spans also overlap. The linked measurements do not cover extended input flanks.',
        ['plantcad2-ft-cell_type_specific_acr-lora'],['plantcad2-acr','plantcad-final-cell-inspection'],limit_eids=['split-evidence-face9b470c556621'])
    design('ntv3-tracks','NTv3: native functional tracks','ntv3-evals','blocks gene-family','supervised',
        'Human/mouse use Borzoi fold 3 test and fold 4 validation. Other species use gene-aware 1-Mb windows, a BioMart homology graph and MCL clusters assigned to partitions.',
        'MCL inflation is chosen by graph modularity; prediction checkpoints and training-only target scaling use validation and training respectively.',
        'Not a species holdout: the same supervised species occur in all partitions. Pruning low-weight homology edges in three genomes means this is not a strict identity-threshold guarantee.',
        family('ntv3-tracks-'),['ntv3-final-native-protocol'])
    design('ntv3-annotation','NTv3: gene annotation','ntv3-evals','taxon','supervised',
        'Separate mammal, plant and insect models; test genera excluded from supervised training and validation. Test panels contain 2 mammals, 5 plants and 10 insects.',
        'Checkpoint chosen by mean validation-species gene F1. Validation species may share genera with training.',
        'Genus separation is stronger than validation-species separation here. OpenGenome2 pretraining exposure remains a separate question.',
        family(evidence='ntv3-final-annotation')+family(evidence='ntv3-final-protein-annotation'),['ntv3-final-annotation'])
    design('bacbench-essential','BacBench: essentiality','bacbench loam-evals','taxon','probe',
        'Native 55-genome release: 37 training / 9 validation / 9 test genomes, with pairwise disjoint genus sets.',
        'Keep the validation set distinct from final test; LOAM and Genos-m reuse protocols below have different selection or cohort rules.',
        'The released test has no exact CDS string shared with training in the bounded complete comparison. Genus separation alone does not exclude homologous genes.',
        ['bacbench-essential-protocol'],['final-bacbench-essential-scorer','final-bacbench-essential-native-test'])
    design('spliceai','SpliceAI: coding-gene annotation','spliceai-evals','chromosome gene-family','supervised',
        'Test chr1/3/5/7/9 and exclude test genes with any annotated paralog. Train on the other listed chromosomes, using GENCODE V24lift37/hg19.',
        'Random 10% of training genes reserved for early stopping.',
        'Combines chromosome holdout and an annotated-paralog exclusion. It is not a quantitative DNA identity threshold, and external variant cohorts have different eligibility.',
        family('spliceai-spliceai-sites-coding')+['spliceai-spliceai-exon-inclusion-protocol'],['spliceai-partitions'])
    design('spliceai2-transcript','SpliceAI2: top transcript reconstruction','spliceai2-evals','chromosome','supervised',
        'Human-only model trains outside chr21/22; reconstruction evaluates 352 eligible multi-exon genes on chr21/22. Nonhuman training is omitted in this arm to limit ortholog exposure.',
        'The held-out chromosomes also serve validation; the paper does not define a third independent test for this arm.',
        'This split applies to reconstruction, not every SpliceAI2 variant benchmark. Matching covers the splice chain, not transcript start/end recovery or all-isoform recall.',
        ['spliceai2-spliceai2-top-transcript-protocol'],['spliceai2-top-transcript-method'])
    design('bend-gene','BEND original: gene finding','bend-original','gene-family similarity','probe',
        'GraphPart groups gene instances at 80% global mature-protein identity; paper reports 4,780 / 597 / 597 train / validation / test instances.',
        'Train the downstream model on train; use the supplied validation partition for selection.',
        'The similarity object is translated mature protein, not full genomic DNA. The same chromosome can appear in multiple partitions, and flanking genomic spans can overlap.',
        ['bend1-gene-finding-protocol'],['bend1-gene-method'])
    design('bend-chromatin','BEND original: accessibility and histones','bend-original','chromosome','probe',
        'Test chr1/8/9; validation chr2/4; remaining released chromosomes train.',
        'Source-defined validation chromosomes support downstream-model selection.',
        'Whole-chromosome reference separation differs from the gene-finding protein-similarity split. It does not eliminate repeated DNA or backbone pretraining exposure.',
        ['bend1-accessibility-protocol','bend1-histone-protocol'],['bend1-chromatin-method','bend1-histone-method'])
    design('bend-enhancers','BEND original: enhancer annotation','bend-original','chromosome','probe',
        'Ten chromosome groups. Each run holds one group for test, the next for validation, and the other eight for training.',
        'Validation group rotates with the test group; report across held-out groups.',
        'This is chromosome-group cross-validation, not ten random sequence splits.',
        ['bend1-enhancer-annotation-protocol'],['bend1-enhancer-method'])
    design('bend-cpg','BEND original: CpG methylation','bend-original','chromosome','probe',
        'Test chr4/13/19/21; validation chr5/9/22; other released chromosomes train.',
        'Validation uses the named chromosomes.',
        'A task-specific chromosome assignment; do not copy the accessibility/histone chromosome list to this task.',
        ['bend1-cpg-protocol'],['bend1-cpg-method'])
    design('dart-training','DART-Eval: trained regulatory readouts','dart','chromosome','mixed',
        'Validation chr6/21; test chr5/10/14/18/20/22; remaining chromosomes train for cCRE, cell-type and accessibility training.',
        'Frozen CNN readouts and LoRA fine-tunes select the lowest validation-loss checkpoint.',
        'Applies to reference-sequence supervised training. The fixed likelihood, motif and QTL scoring cohorts do not inherit this downstream fitting split.',
        family(evidence='final-dart-methods',suffix='supervised')+family('dart-',suffix='lora'),['final-dart-methods'])
    design('traitgym-fitted','TraitGym: fitted feature models','traitgym','chromosome','probe',
        'Leave one chromosome out: predict that chromosome using a model fitted on all remaining chromosomes.',
        'Inside each outer training set, chromosome-grouped GridSearchCV chooses logistic-regression C. Imputation and scaling are training-fitted pipeline operations.',
        'A genuine chromosome holdout for the readout. Chromosome-weighted zero-shot AUPRC alone does not imply this fitting protocol.',
        ['traitgym-mendelian-probe','traitgym-complex-probe'],[trait_outer],selection_eids=[trait_inner],limit_eids=[trait_outer,'traitgym-definition'])
    design('nt-native','Nucleotide Transformer: revised human benchmark','nt-revised','chromosome','dataset',
        'Final 18-task benchmark reserves human chr20/21 for test; other chromosomes supply training. The revised dataset card explicitly distinguishes this from the older benchmark.',
        'Training-only 90/10 validation repeated ten times; selected models are evaluated on the same held-out test set.',
        'Ten test scores do not represent ten independent test cohorts. Sequence-only HF columns do not independently reconstruct chromosome coordinates.',
        (),[nt_native,'nt-revised-card'])
    design('genecad','GeneCAD: released genome annotation revision','genecad','taxon random','supervised',
        'Adaptation uses eight training plant species. Validation samples windows within those species/chromosomes; held-out angiosperms, maize and distant genomes are separate test panels.',
        'Within-training-species random-window validation; source revision and comparator exposures are recorded separately from the older five-training-species paper.',
        'Unseen species at annotation fine-tuning is distinct from unseen pretraining species. Validation is not itself a held-out-species test.',
        family('genecad-',evidence='genecad-release-evaluator-ev')+family(evidence='genecad-release-structure-code-ev'),['genecad-release-evaluator-ev','genecad-release-structure-code-ev'])
    design('lambda','LAMBDA: bacterial/phage fragments','lambda','taxon similarity','supervised',
        'Bacterial genomes grouped by genus; phages grouped by 95% ANI clusters. Assign 80/10/10 before sampling fragment windows.',
        'Fragment-model validation uses the held-out groups. Separate whole-genome smoothing/threshold grid searches optimize on the supplied reference genomes.',
        'ANI is a genome-cluster criterion, not a guarantee that short fragments share no identical DNA. Whole-genome parameter selection and fragment test accuracy are different protocols.',
        family('lambda-segments-'),['final-lambda-evo-interfaces-evidence'],limit_eids=['final-lambda-evo-interfaces-evidence','final-lambda-intervals-evidence'])
    design('rnagym-random','RNAGym: supervised random split','rnagym','random','probe',
        'Within each of 26 supplied assays, random 80/20 train/validation split at seed 42.',
        'These archives expose train and validation, not a third test partition.',
        'Shares the assayed molecule and often related mutants across partitions. Evo 1/2 fixed zero-shot assay scoring does not fit on this training subset.',
        family(suffix='-cv-random-protocol'),['rnagym-split-audit'])
    design('rnagym-similarity','RNAGym: minimum-similarity heuristic','rnagym','similarity','probe',
        'Start from the seeded 80/20 random split; swap examples when sampled train/validation alignment similarity exceeds 0.8, for at most 10,000 iterations.',
        'A similarity-reduction preprocessing objective; no independent test partition is supplied.',
        'Not a strict maximum-identity partition. Six distinct Pitt validation strings still occur in training in the inspected archive.',
        family(suffix='-cv-min_similarity-protocol'),['rnagym-split-audit'],limit_eids=['rnagym-split-audit','split-evidence-da86f10ed88ccfc9'])
    design('nabench-random','NABench: random and few-shot readouts','nabench','random','probe',
        'Random fivefold variant-level CV; a separate few-shot setting fits ridge on ten labeled examples.',
        'Exact row assignments and few-shot sampling manifests are not released.',
        'Variant holdout within an assay does not imply new genes, mutation positions or sequence families.',
        family(suffix='-nabench-random')+family(suffix='-nabench-few-shot'),['nabench-complete-methods'])
    design('nabench-position','NABench: mutation-position blocks','nabench','position','probe',
        'Divide the wild-type sequence into five contiguous position blocks and hold out a mutation-position block.',
        'The paper describes position CV but supplies no immutable fold assignments.',
        'Multimutants spanning blocks require an assignment rule; that handling is not resolved by the released assay CSVs.',
        family(suffix='-nabench-position'),['nabench-complete-methods'])
    design('nabench-transfer','NABench: cross-assay transfer','nabench','assay','probe',
        'Fit on complete source assays and score a different target assay.',
        'Exact donor/recipient combinations and row manifests are not released for every catalogue entry.',
        'Assay transfer does not by itself establish unseen sequence-family or species transfer.',
        family(suffix='-nabench-transfer'),['nabench-complete-methods'])

    design('gb-random','Genomic Benchmarks: notebook-defined random splits','gb','random','dataset',
        'Cohn human enhancers, non-TATA promoters, Stark fly enhancers, human-versus-worm and coding-versus-intergenic demos: class-wise shuffled approximately 75/25 train/test, seed 42.',
        'Creation notebooks supply two partitions. Any validation split is a downstream user decision.',
        'Human and worm both occur in training and test: predicting species labels is not testing unseen species. No gene-family or chromosome grouping is applied.',
        ['gb-'+key+'-protocol' for key in gb_evidence if key not in ['human_ocr_ensembl','human_ensembl_regulatory']],list(gb_evidence[key] for key in gb_evidence if key not in ['human_ocr_ensembl','human_ensembl_regulatory']))
    design('gb-scraper','Genomic Benchmarks: OCR and regulatory classes','gb','random','dataset',
        'Pinned Ensembl scraper makes class-wise random 80/20 train/test with seed 42. The regulatory task combines source class files without changing their assignments.',
        'No third partition in these construction scripts; regulatory promoter pieces are shortened after their parent interval is assigned.',
        'The human/mouse Ensembl enhancer notebooks instead install an unpinned helper. This inspected helper revision cannot establish their exact historical split construction.',
        ['gb-human_ocr_ensembl-protocol','gb-human_ensembl_regulatory-protocol'],[gb_helper,gb_evidence['human_ocr_ensembl'],gb_evidence['human_ensembl_regulatory']])
    design('gb-unpinned','Genomic Benchmarks: human / mouse Ensembl enhancers','gb','released','dataset',
        'Native train/test membership is released, but the creation notebooks delegate splitting to an unpinned Ensembl scraper dependency.',
        'The notebooks define no independent validation cohort.',
        'The inspected helper uses random 80/20, but its exact historical version is not fixed by these notebooks. Do not claim a reconstructed chromosome or family holdout.',
        ['gb-human_enhancers_ensembl-protocol','gb-dummy_mouse_enhancers_ensembl-protocol'],enhancer_evidence+[gb_helper])
    design('geneb','GENEB: frozen-embedding benchmark release','geneb nt-original gue','released','probe',
        '100 configurations use fixed released train/test CSVs; upstream validation/dev rows are excluded. Few-shot examples are sampled only from train.',
        'The interface supplies no development partition. Do not infer additional validation or biological grouping from two sequence/label columns.',
        'Native NT, GUE and GENEB partitions are different cohorts. Original NT/GUE H3 and H4 reuse identical full pools but assign rows differently.',
        family('geneb-',suffix='-probe'),['geneb-spec'],limit_eids=['geneb-spec','completion-nt-gue-H3','completion-nt-gue-H4'])
    design('dnafoundation-random','DNA Foundation Benchmark: sequence classification','dna-foundation','random released','probe',
        'Paper retains clear source partitions, otherwise uses stratified random 70/30. NT/DNABERT-2-derived cohorts are reshuffled; deposited processed files define the evaluated membership.',
        'Paper states fivefold classifier tuning; released random-forest GridSearchCV uses four folds.',
        'Repartitioned mirrors do not inherit native chromosome exclusions. Keep paper/CV-code discrepancy separate from measured duplicate-sequence intersections.',
        family('dnafoundation-',suffix='-rf',evidence='dnafoundation-classification-code'),['dnafoundation-classification-code'])
    design('dnafoundation-variants','DNA Foundation Benchmark: fitted variant classifiers','dna-foundation','chromosome','probe',
        'Rotate three disjoint outer chromosome groups: {3,6,9,12,16,18,19,21}; {2,5,11,14,17,20,22,X}; {1,4,7,8,10,13,15}.',
        'Fourfold chromosome-grouped inner CV within the outer training chromosomes.',
        'Chromosome holdout applies to variant-label readout fitting, not necessarily to unsupervised backbone DNA exposure.',
        family(evidence='dnafoundation-variant-code'),['dnafoundation-variant-code'])
    design('dnafoundation-donors','DNA Foundation Benchmark: personal expression','dna-foundation','donor','probe',
        '75/25 subject split, seed 42; train and test share gene identities.',
        'Fivefold training CV; omit genes with insufficient nonmissing subjects.',
        'Tests new individuals for represented genes, not prediction for new genes or new species.',
        ['dnafoundation-expression-regression'],['dnafoundation-personal-expression-code'])
    design('genbench-alias','GenBench: converted classification / DeepSTARR / LRB','genbench','released','supervised',
        'Released GB/GUE/DeepSTARR/LRB loaders reuse source files but alias requested validation to test. Converted SpliceAI arrays similarly expose train/test without an independent third set.',
        'If validation drives early stopping, the final reported test file has also served selection.',
        'A loader-level difference from the source benchmark. Do not present native chromosome partitions as proof of an untouched test in this interface.',
        family(evidence='final-genbench-gb-loader-evidence')+family(evidence='final-genbench-gue-loader-evidence')+family(evidence='final-genbench-deepstarr-loader-evidence')+family(evidence='final-genbench-lrb-loader-evidence')+family(evidence='final-genbench-splice-loader-evidence'),
        ['final-genbench-gb-loader-evidence','final-genbench-gue-loader-evidence','final-genbench-deepstarr-loader-evidence','final-genbench-lrb-loader-evidence','final-genbench-splice-loader-evidence'])
    design('genbench-species','GenBench: species classification','genbench','chromosome','supervised',
        'Within each represented species, validation uses listed chr1/3/12/13 and test chr5/7/9/10/11; other listed chromosomes train.',
        'Separate source chromosome lists define the three membership sets.',
        'Known species occur in every partition. The task predicts species identity rather than transfer to a species absent from training.',
        ['genbench-species-finetune'],['final-genbench-species-loader-evidence'])
    design('genbench-contact','GenBench: contact maps','genbench','chromosome','supervised',
        'Sampler declares validation chr8 and test chr9/10.',
        'Released test_dataloader returns the validation loader.',
        'The code does not establish an independent third-set result even though a separate test chromosome list exists.',
        family(evidence='final-genbench-contact-scorer-evidence'),['final-genbench-contact-scorer-evidence'])
    design('deepstarr','DeepSTARR: native enhancer activity','deepstarr','chromosome blocks','supervised',
        'Training excludes Drosophila chr2R; its first half is validation and second half test. Native rows: 402,296 / 40,570 / 41,186, including both orientations.',
        'Source train/validation/test membership is retained in the checked GenerTeam re-release and Carbon protocols.',
        'Validation and test share a chromosome but use different chromosome regions. Converted GenBench validation aliases are a separate interface.',
        family(evidence='final-deepstarr-native-inspection')+family(evidence='carbon-final-supervised-transfer'),['final-deepstarr-native-inspection','carbon-final-supervised-transfer'])
    design('generator-cv','GENERator / v2: benchmark adaptation','generator-evals generator2-evals gener-tasks','random chromosome released','supervised',
        'Original GENERator code creates shuffled training/validation folds within supplied training when validation is absent; supplied test remains separate. v2 reports tenfold revised-NT evaluation.',
        'Training-fold validation drives checkpoint selection. Historical CLI values and immutable fold-index manifests are not released.',
        'Training-only random folds do not imply random test assignment. Revised NT retains its native chromosome test; report mean folds as repeated fits on that test.',
        family(evidence='generator-nt-use')+family(evidence='generator-split-code')+family(evidence='final-generator2-protocol'),['generator-split-code','final-generator2-protocol'])
    design('pgb-chromosomes','Plant Genomic Benchmark: chromosome-defined tasks','pgb','chromosome','dataset',
        'Arabidopsis splice tests use chr5; poly(A) and lncRNA tasks reserve species-specific chromosomes (wheat 1A/1B/1D). Cassava PRO-seq: test chr17, validation chr9.',
        'Accessibility partitions are species/assembly-specific; native validation/test chromosome membership was checked from released sequence headers.',
        'Pooling six training species for lncRNA classification is not species holdout. Repeated sampled windows are not independent genomic loci.',
        ['pgb-polya-protocol','pgb-splice-donor-protocol','pgb-splice-acceptor-protocol','pgb-lncrna-protocol','pgb-chromatin-protocol','pgb-enhancer-protocol'],['final-pgb-primary-methods'])
    design('pgb-expression','Plant Genomic Benchmark: tissue expression','pgb','gene-family','supervised',
        'Protein-similarity gene-family graph grouping, approximately 80/20 source train/held-out; native files further name validation and test.',
        'Use the released membership rather than independently shuffling genes for model selection.',
        'Native gene IDs do not contain the family graph or clustering decisions; grouping cannot be independently reconstructed from IDs alone.',
        ['pgb-gene-expression-protocol'],['final-pgb-primary-methods'])
    design('pgb-reporters','Plant Genomic Benchmark: promoter / terminator activity','pgb','released','supervised',
        'Retain source Jores promoter and Gorjifard terminator reporter train/validation/test libraries, separately scored in leaf and protoplast assays.',
        'Use the source validation library; assay organism is separate from the species supplying the candidate sequence.',
        'These are short reporter constructs, not chromosome-held-out native genomic windows. Headers do not encode a sequence-family grouping key.',
        ['pgb-promoter-strength-protocol','pgb-terminator-strength-protocol'],['final-pgb-primary-methods'])
    design('botanic-transfer','BOTANIC-1: splice / translation-site transfer','botanic1-evals','taxon chromosome','probe',
        'Arabidopsis source training; site tasks use chr1–4 train and upstream chr5 validation as reported within-species test. Same readout transfers to rice, sorghum and maize.',
        'Cross-species panels sample 500 positives and 4,500 negatives with prevalence correction; within-species and development caps differ.',
        'Species transfer and chromosome transfer are different comparisons using one probe. Reported within-species test inherits an upstream validation cohort.',
        ['botanic1-tis-protocol','botanic1-tts-protocol']+family('botanic1-cross-'),['botanic-final-sizes'])
    design('botanic-conservation','BOTANIC-1: conservation and genomic elements','botanic1-evals','chromosome taxon','probe',
        'Conservation: sorghum chr1–9 train, chr10 within-species test, maize external test. Region-class probes use chromosome-held-out windows within four plant genomes.',
        'Uniform 20,000 training / 5,000 evaluation caps; region-class paper does not list every held-out chromosome ID.',
        'Region classification within each species does not inherit the external maize species holdout from the separate conservation task.',
        ['botanic1-conservation-protocol','botanic1-regions-protocol'],['botanic-final-pooling'])
    design('botanic-atac','BOTANIC-1: ATAC and TF readouts','botanic1-evals','chromosome','mixed',
        'ATAC: Arabidopsis validation chr2/test chr4; maize validation chr4/test chr1/9. TF family classification: chr1–3 train, chr4 validation, chr5 test.',
        'Remaining eligible chromosomes train; separate long-context maize accessibility uses chr9/10 test and matched peaks/labels across context lengths.',
        'Different BOTANIC tasks reserve different chromosomes. Extending context requires checking the full input span, beyond preserving target labels.',
        family(evidence='botanic-final-atac-methods')+family(evidence='botanic-final-tf-methods')+family(evidence='botanic-final-long-atac'),['botanic-final-atac-methods','botanic-final-tf-methods','botanic-final-long-atac'])
    design('botanic-pgb','BOTANIC-1: PGB adaptation','botanic1-evals','chromosome released','mixed',
        'Reuse task-specific PGB source partitions. Frozen probes cap or resample those rows; full adaptation evaluates separate task/backbone/regime runs.',
        'Full adaptation tunes on a separate validation grid then retrains from scratch on the full source training set. Immutable validation-row assignments are not supplied.',
        'Do not confuse prevalence-corrected splice development subsets, final frozen probes and full adaptation as one common test cohort.',
        family(evidence='botanic-final-probe-methods')+family(evidence='botanic-final-pgb-adaptation'),['botanic-final-probe-methods','botanic-final-pgb-adaptation'])
    design('plantcad-expression','PlantCAD2: expression across species / accessions','plantcad2-ft','taxon','supervised',
        'Andropogoneae training panel; validation species Tripsacum zopilotense and Zea diploperennis; test across 26 maize NAM genomes.',
        'Leaf on/off, absolute expression and maximum-expression endpoints share the stated species-transfer setting; the maximum endpoint lacks a matching per-example release.',
        'Test accessions are many genomes of maize, not 26 held-out species. Orthogroup-level evaluation does not imply that orthogroups were separated in training.',
        family('plantcad2-ft-cross_species_leaf_',suffix='expression-lora')+family(evidence='final-plantcad-expression-scope'),['plantcad2-expression','final-plantcad-expression-scope'])
    design('plantcad-translation','PlantCAD2: Arabidopsis-to-maize translation','plantcad2-ft','taxon','supervised',
        'Per target: 21,894 Arabidopsis training genes, 5,492 Arabidopsis validation genes and 39,035 maize test genes. Both Arabidopsis partitions include chr1–5.',
        'Released gene-row validation is not a chromosome holdout.',
        'No shared gene IDs or exact 500-bp sequences across these partitions in the full scans. That is not a general homology exclusion.',
        family('plantcad2-ft-cross_species_leaf_',suffix='translation-lora'),['plantcad-final-translation-inspection'])
    design('plantcad-zero','PlantCAD2: zero-shot / MLM cohorts','plantcad2-zero','fixed released','zero-shot',
        'Recovery, conservation and simulated-deletion configs are released as test-only cohorts. MLM diagnostics use paper-designated held-out pretraining sequences.',
        'No downstream task-label head for these scores. MLM masking/context ablations do not themselves define a taxonomic split.',
        'The current pretraining card reports a corrected release with train/validation/test names but no biological grouping or historical-run mapping. Do not infer species/chromosome exclusion from those names.',
        family(evidence='plantcad2-refprob')+family(evidence='plantcad2-motif-metric')+family(evidence='plantcad2-sv-score')+family(evidence='plantcad2-mlm-diagnostic'),['plantcad2-zero-card-ev','plantcad2-mlm-diagnostic','final-plantcad-pretraining-release'])
    design('bacbench-amr','BacBench: antibiotic resistance','bacbench','random','probe',
        'Default per-antibiotic sample-level 70/10/20 train/validation/test; binary labels stratified when feasible. CLI seeds 1, 2, 3.',
        'Select by validation AUROC for binary classification or R2 for MIC. Optional group splitting can fall back to sample-level ShuffleSplit.',
        'The default is not genus holdout. A requested grouping option is not proof of the grouping actually used in a particular run.',
        ['bacbench-amr-binary-protocol','bacbench-amr-mic-protocol'],['final-bacbench-amr-scorer'])
    design('bacbench-phenotype','BacBench: phenotypes and interaction pairs','bacbench','taxon','probe',
        'Phenotype default: genus-grouped 70/10/20, with sample-split fallback when grouping is unavailable or fails. Interaction release declares genus-held-out 159/49/53 genomes.',
        'Record actual grouping outcome; source interaction percentages 60/10/20 do not match the declared counts.',
        'Do not apply essentiality’s 37/9/9 cohort or AMR’s default random split to these tasks.',
        ['bacbench-phenotype-protocol']+family(evidence='final-bacbench-ppi-cosine'),['final-bacbench-phenotype-scorer','final-bacbench-ppi-cosine'])
    design('genosm-essential','Genos-m: essentiality and phenotypes','genosm-evals','taxon','probe',
        'Essentiality: 51 genomes, genus-disjoint 30/10/11 (described as 60/20/20). Phenotypes: genus-disjoint 70/10/20; documented seeds 1, 2, 3.',
        'Use the documented validation partitions; exact membership is not interchangeable with the native 55-genome BacBench release.',
        'Cross-genus testing controls taxonomic grouping, not necessarily homologous CDS sequences or pretraining exposure.',
        family(evidence='genosm-doc-essential')+family(evidence='genosm-doc-phenotype'),['genosm-doc-essential','genosm-doc-phenotype'])
    design('genosm-random','Genos-m: promoter, virulence and BGC probes','genosm-evals','random released','probe',
        'Promoter rows are random within each species; virulence uses label-stratified 80/20. BGC classification uses 80/10/10 with label-distribution preservation.',
        'The gene-class task separately reports tenfold CV without fold membership; AMR documentation conflicts between 80/20 prose and counts close to 90/10.',
        'Source omissions and conflicting ratios do not establish a genus, family or chromosome holdout.',
        family(evidence='genosm-doc-promoter')+family(evidence='genosm-doc-virulence')+family(evidence='genosm-doc-bgc-binary')+family(evidence='genosm-doc-gene-class')+family(evidence='genosm-doc-amr'),['genosm-doc-promoter','genosm-doc-virulence','genosm-doc-bgc-binary','genosm-doc-gene-class','genosm-doc-amr'])
    design('loam-selection','LOAM / gLMBench: readout and layer selection','loam-evals','taxon released','probe',
        'Essentiality inherits 37/9/9 genome membership, but gLMBench does not embed validation. EC classification has 512 training and 128 test genes, four/one per class.',
        'The best-layer sweep chooses by test performance; last-layer results are a separate protocol.',
        'A biologically held-out test used to choose the layer is not an untouched final selection set.',
        family(evidence='loam-essential')+family(evidence='loam-ec'),['loam-essential','loam-ec'])
    design('bgc','BGC-Bench: cluster, scaffold and domain splits','bgc','random bgc','probe',
        'Random 80/20, first-product Bemis–Murcko scaffold, and BiG-SCAPE c=0.7 GCF holdouts are distinct splits. Retrieval adds biosynthetic-class holdout; A-domains use parent-BGC fivefold groups plus a separate GCF holdout.',
        'Use task/split-specific training and test membership; parent-BGC and GCF grouping are different resolutions.',
        'Scaffold separation is a chemical grouping, not sequence identity. Distinct BGCs can share domains; identical domain/BGC identifiers require separate checks.',
        family('bgc-',suffix='-probe'),['final-bgc-release','final-bgc-substrate-scorer'])
    design('bgcs','BGCs-Bench: balanced folds','bgcs','bgc','probe',
        'Five biosynthetic/taxonomic-balanced folds. Dense annotation release has five accession/BGC folds of 16 clusters each.',
        'Annotation metadata calls the fold column split, while code expects fold; harmonize explicitly before evaluation.',
        'Parent-BGC grouping does not establish GCF, species or homology disjointness. This is a different project from BGC-Bench.',
        family(evidence='bgcs-methods')+family(evidence='final-bgcs-cds-interface'),['bgcs-methods','final-bgcs-cds-interface'])
    design('guanine-chrom','GUANinE: accessibility / expression proxies','guanine','chromosome','probe',
        'Development chr21 and test chr22. Checked 1% training artifacts use other chromosomes.',
        'Regularization is selected on development data before test inference.',
        'Full main training archive was excluded by size; the inspected few-shot/development/test membership supports this chromosome assignment, not an all-archive sequence-overlap claim.',
        [p['id'] for p in d['protocols'] if p['source_evidence_id']=='final-guanine-probe' and p['split_rule'].startswith('Development chr 21')],['final-guanine-probe'])
    design('guanine-other','GUANinE: conservation, reporter and ClinVar cohorts','guanine','random time fixed','mixed',
        'Conservation windows are random partitions spanning the same chromosomes; synthetic GPRA promoters have no genomic coordinates. ClinVar has development/test release-defined cohorts and no training split.',
        'Fit probes or calibrate zero-shot-incompatible models on the appropriate development cohort.',
        'Disjoint exact coordinate or variant keys are not chromosome exclusion. The ClinVar source/version separation is distinct from a sequence holdout.',
        [p['id'] for p in d['protocols'] if p['source_evidence_id']=='final-guanine-probe' and not p['split_rule'].startswith('Development chr 21')],['final-guanine-probe'])
    design('mrna-groups','mRNABench: gene / HomoloGene grouping','mrnabench','gene-family','probe',
        'Nominal 70/15/15 after dropping rows missing the selected targets. Supplied HomoloGene groups stay together; correct species mapping is required.',
        'Generate partitions with the named source runner and seed. Source default reconstruction is not an immutable published benchmark manifest.',
        'Unmapped rows are assigned independently, including repeated names for the same gene. The checked Sugimoto reconstruction has no mapped-group overlap but does have shared genes and exact strings.',
        [p['id'] for p in d['protocols'] if p['id'].startswith('mrna-') and ('HomoloGene' in p['split_rule'])],['split-mrna-unmapped-code','final-mrna-probe-semantics'])
    design('mrna-random','mRNABench: random-row datasets','mrnabench','random','probe',
        'Nominal 70/15/15 from two unstratified sklearn train_test_split calls, after dropping missing selected labels.',
        'The default regenerates membership; it does not preserve an original study test set.',
        'Random rows do not guarantee separation of repeated genes, constructs or related sequence families.',
        [p['id'] for p in d['protocols'] if p['id'].startswith('mrna-') and p['split_rule'].startswith('Unstratified random')],['final-mrna-probe-semantics'])
    design('bend2-groups','BEND 2.0: intervention readouts','bend','gene','probe',
        'OpenSplice holds out whole genes in five folds. Context/background tasks keep the complete element and its related backgrounds together; design tasks evaluate held-out elements.',
        'Fixed ridge alpha=10 avoids a label-driven penalty search in these protocols.',
        'Gene/element grouping separates variants of one measured entity; it does not promise a sequence-family identity threshold.',
        family(evidence='final-bend2-fixed-ridge'),['final-bend2-fixed-ridge'])
    design('bend2-atlas','BEND 2.0: atlas sequence-family transfer','bend','gene-family','probe',
        '5,246 source constructs versus 2,411 candidate constructs; exclude 27 source constructs whose sequence families touch the candidates.',
        'Select penalty on 4,223 / 1,023 source training/validation constructs, then refit all source constructs. Candidate outcomes are read after choices are stored.',
        'Separates sequence families for design selection; candidate cell requests are not a held-out-species split.',
        ['bend-atlas-protocol'],['final-bend2-atlas-selection'])
    design('bend2-tissue','BEND 2.0: tissue identification','bend','gene','probe',
        '12,146 training / 1,350 validation / 5,786 original test genes; common-prediction exclusions leave 5,782 scored genes. Same 51 tissue types in each cohort.',
        'One shared ridge penalty selected on validation-gene MSE; training-only scaling, no train+validation refit.',
        'Tests held-out genes for represented tissues, not unseen tissue types. Whole-gene bootstrap is uncertainty estimation, not another training split.',
        ['bend-tissue-protocol'],['final-bend2-tissue-retrieval'])
    design('compass-transfer','COMPASS: strict OpenSplice transfer','compass bend','assay gene','probe',
        'Remove exact overlaps and all 23 shared genes from both assays. Train/validate OpenSplice on 398/45 genes; test 4,618 COMPASS variants in 88 genes.',
        'No COMPASS labels select the readout.',
        'The separate interaction analysis removes exact sequence overlaps but retains shared genes, spanning 110 genes. It is a weaker transfer exclusion.',
        family(evidence='final-compass-transfer')+family(evidence='final-compass-interaction'),['final-compass-transfer','final-compass-interaction'])
    design('trip','TRIP: reporter editing efficiency','trip bend','chromosome','probe',
        '1,196 reporter insertion loci over 23 chromosomes; five CV folds keep whole chromosomes together.',
        'Fixed ridge alpha=1,000; separate alternative uses threefold CV within training chromosomes.',
        'The reporter is shared across loci. Whole-chromosome bootstrap quantifies uncertainty without refitting and is not the partition algorithm.',
        ['trip-bend-probe'],['final-trip-setting'])
    design('mage','MAGE: personal-genome expression','mage bend','donor gene blocks','probe',
        'Both settings hold out people. The stricter setting also holds out gene regions and keeps overlapping 8-kb windows together.',
        'Genotype shuffling is within population and partition; whole-gene bootstrap estimates uncertainty.',
        'A one-hot baseline over 729 people and 557 chr22 genes. It is not evidence that an indexed gLM has been evaluated on this personal-genome task.',
        ['mage-personal'],['final-mage-setting'])
    design('lrb-chrom','Genomics Long-Range Benchmark: chromosome tasks','lrb','chromosome','mixed',
        'eQTL test chr9/10; coding ClinVar and bulk expression test chr8. Histone/accessibility/promoter/enhancer interfaces use test chr8/9 and training chr1–7/10–22.',
        'Workshop eQTL and bulk-expression procedures use five training chromosomes as validation folds.',
        'Task-specific chromosome lists differ. Test-only OMIM and the CAGE regional split do not inherit these assignments.',
        ['lrb-eqtl-workshop','lrb-clinvar-release-interface','lrb-bulk-workshop','lrb-histone-release-interface','lrb-accessibility-release-interface','lrb-promoter-release-interface','lrb-enhancer-release-interface'],['final-lrb-workshop-protocol','final-lrb-loader-evidence'])
    design('lrb-cage','Genomics Long-Range Benchmark: CAGE','lrb','blocks random','supervised',
        'Retain Basenji-derived 33,891 / 2,195 / 1,922 train / validation / test regions.',
        'Workshop combines source train/validation and samples 10% for validation folds; source test stays separate.',
        'Regional membership is not whole-chromosome holdout. A downstream workshop validation procedure is distinct from source validation assignment.',
        ['lrb-cage-workshop'],['final-lrb-workshop-protocol'])
    design('dnalong-eqtl','DNALongBench: eQTL gene–variant pairs','dnalongbench','random','supervised',
        'Label-stratified random 80/10/10 gene–variant pair split; eligible genes require at least one positive and one negative in training and validation.',
        'Use the supplied validation pair cohort for adaptation.',
        'A gene can occur in all partitions. Neither gene holdout nor chromosome holdout follows from this pair-level split.',
        ['dnalong-eqtl-finetune'],['final-dnalongbench-loaders-evidence'])
    design('dnalong-context','DNALongBench: contact maps and regulatory profiles','dnalongbench','blocks','supervised',
        'Contact: randomly assigned nonoverlapping virtual contigs, nominal 80/10/10. Regulatory profiles: original Enformer region assignments, human 34,021/2,213/1,937 and mouse 29,295/2,209/2,017.',
        'Retain task-specific source validation regions.',
        'Virtual contigs and Enformer regions are not whole chromosomes. Expanded context must be checked separately from the scored region.',
        ['dnalong-contact-finetune','dnalong-regulatory-finetune'],['final-dnalongbench-loaders-evidence'])
    design('dnalong-initiation','DNALongBench: transcription initiation','dnalongbench','chromosome','supervised',
        'Validation chr10, test chr8/9, other chromosomes train; 100-kb windows at 50-kb steps.',
        'Training loader caps at 100,000 sampled windows.',
        'The central 50 kb is scored. Overlapping windows within one chromosome partition are intentional and distinct from cross-partition leakage.',
        ['dnalong-initiation-finetune'],['final-dnalongbench-loaders-evidence'])
    design('dnalong-enhancers','DNALongBench: enhancer–gene pairs','dnalongbench','released','supervised',
        'Supplied train/validation/test pair files define membership.',
        'Use source validation pairs; the main text does not report their construction.',
        'No chromosome, gene or enhancer-family exclusion can be established from file names alone.',
        ['dnalong-enhancer-gene-finetune'],['final-dnalongbench-loaders-evidence'])
    design('gpn','GPN-Star: annotation probe and trait aggregation','gpn-evals','chromosome assay','mixed',
        'Annotation readout: leave one chromosome out. Rare-variant aggregation: 21 training phenotypes, 34 evaluation phenotypes including those 21 and 13 additional phenotypes.',
        'Phenotype-trained aggregation and fixed zero-shot variant likelihoods are distinct fitting layers.',
        'The 34-phenotype panel is not wholly held out. Pretraining validation chromosomes and block-jackknife uncertainty do not define these downstream splits.',
        ['gpn-annotation-probe','gpn-rvat-protocol'],['gpn-annotation','gpn-association'])
    design('carbon','Carbon: regulatory adaptation and benchmark selection','carbon-evals','chromosome released fixed','mixed',
        'Malinois: validation chr19/21/X, test chr7/13. DREAM keeps source training/validation/designed-promoter test libraries; Carbon samples 200,000 training rows.',
        'BRCA2 is used for model-development ablations; TraitGym Mendelian is withheld from that selection.',
        'A benchmark withheld from ablation selection is different from excluding its DNA from pretraining. DREAM subset row IDs are not supplied.',
        ['carbon-malinois-protocol','carbon-dream-protocol','carbon-evo-brca2','carbon-traitgym-mendelian'],['carbon-final-malinois-code','carbon-eval-methods','carbon-final-shared-vep-scorer'])
    design('ceno-probes','CENO: chromatin probes and design oracle','ceno-evals','blocks condition chromosome','mixed',
        'TAD/boundary probes use five genomic-region GroupKFold splits; cross-cell fits train on all source-cell examples. Mouse accessibility oracle reserves validation chr8/10 and test chr9/18.',
        'Oracle-training partitions and generator development/candidate ranking are separate.',
        'Region fold IDs are not published. Cross-cell transfer does not itself establish new DNA coordinates; generated designs have separate candidate-selection exposure.',
        ['ceno-tad-protocol','ceno-mouse-accessibility-protocol'],['final-ceno-position-probes','final-ceno-accessibility-oracle'])
    design('ceno-vep','CENO: variant benchmark development','ceno-evals','fixed','variant-selection',
        'Selected VEP subtasks inform RegMix model development; subsequent fixed variant cohorts are scored without a task-specific classifier.',
        'The inspected release does not provide a complete per-example development-exclusion manifest.',
        'Zero-shot inference does not make a benchmark independent of model development. Do not invent held-out rows or chromosome assignments.',
        family(evidence='ceno-eval-methods',prefix='ceno-evo-')+family('ceno-traitgym-'),['ceno-eval-methods'])
    design('deepd','DeepD: released probes versus paper panels','deepd-evals','released','probe',
        'Released H3 demonstration supplies train/valid/test CSVs without coordinate or homology keys. Human routing example reports 72,000 / 9,000 / 9,000 rows.',
        'Paper-specific head/split settings for other regulatory and routing panels are not supplied in available methods or per-panel manifests.',
        'Named files and an 80/10/10 count do not establish random, chromosome or species grouping. The H3 demonstration is not proof of every paper-panel protocol.',
        ['deepd-h3-example']+family(evidence='deepd-routing-model-release'),['deepd-h3-code','deepd-routing-model-release'])
    design('dgeb','DGEB: fitted and nonfitted task interfaces','dgeb','released fixed taxon','mixed',
        'Classification loads released train/test without development. Cross-domain retrieval uses bacterial corpus and archaeal/eukaryotic queries; paired-sequence retrieval and clustering score fixed collections.',
        'HF train can name an evaluation corpus rather than a supervised training set; clustering fits and scores one collection.',
        'Corpus/query taxonomy is not classifier-training taxon exclusion. The classification schema does not establish chromosome, species or homology disjointness.',
        family(evidence='final-dgeb-scorers'),['final-dgeb-scorers'])
    design('genemteb','Gene-MTEB: classification and fragment clustering','gene-mteb','random','probe',
        'Seed-42 random row splits; classification samples few labeled training examples. Reference clustering uses 90% held-out genomes; segment clustering chunks references first and then randomly assigns 99.5% of fragments to test.',
        'Training-pool fractions and eight-examples-per-class caps depend on the dataset/evaluator.',
        'Sibling fragments are not grouped by parent genome in the segment setting. A held-out fragment is not necessarily from an unseen organism or genome.',
        family(evidence='final-genemteb-classification-evaluator-evidence')+family(evidence='final-genemteb-hmp-multilabel-evidence')+family(evidence='final-genemteb-clustering-evaluator-evidence'),['final-genemteb-classification-evaluator-evidence','final-genemteb-hmp-multilabel-evidence','final-genemteb-clustering-evaluator-evidence'])
    design('aido','AIDO.DNA2: Borzoi profile adaptation','aido2-evals','blocks','supervised',
        'Original eight-fold Borzoi partition: training folds 0–2 and 5–7, validation fold4, test fold3.',
        'Adapters fit the named output modalities on those source folds.',
        'These are genomic region folds, not whole-species holdouts. ClinVar zero-shot and embedding projections do not inherit a downstream fitting split.',
        family(evidence='aido2-coverage'),['aido2-coverage'])
    design('ntv3-ag','NTv3: AlphaGenome comparison','ntv3-evals','blocks','supervised',
        'Five assay-specific fine-tunes evaluated on AlphaGenome’s released fold4, which is NTv3’s native validation fold.',
        'No gradient training on that fold; its native selection role remains.',
        'A held-out training fold need not be an independent selection-free test.',
        family('ntv3-ag-'),['ntv3-final-alphagenome'])
    design('ntv3-benchmark','NTv3: released 11-species benchmark','ntv3-evals','blocks','supervised',
        'Use the exact released species-specific train/validation/test intervals.',
        'Validation Pearson selects checkpoints; three seeds except one for Evo 2.',
        'Species are represented in training and test. Shared chromosomes alone do not imply overlapping genomic intervals.',
        family(evidence='ntv3-final-benchmark-protocol'),['ntv3-final-benchmark-protocol'])
    design('seiplant','SeiPlant: external-species comparison','seiplant ntv3-evals','taxon chromosome','zero-shot',
        'Five species excluded from NTv3 functional post-training and SeiPlant training; source-held-out chromosomes are evaluated without new fitting.',
        'Use the released within-family and cross-family SeiPlant arms.',
        'Functional-supervision exclusion does not establish absence from unsupervised genome pretraining.',
        ['ntv3-seiplant-protocol'],['ntv3-final-seiplant'])
    design('deepfarm','DeepFARM: score-bin versus whole-context exclusion','deepfarm ntv3-evals','blocks','zero-shot',
        'NTv3 reports scored-bin-held-out and stricter whole-1-Mb-context-held-out variants.',
        'External bird/pig assay labels are not fitted for this comparison.',
        'A held-out 200-bp target bin can have input flanks crossing training partitions. The two cohorts must stay separate.',
        family(evidence='ntv3-final-deepfarm'),['ntv3-final-deepfarm'])
    design('danio','DanioDecima: held-out genes / chromosomes','daniodecima ntv3-evals','chromosome blocks','supervised',
        'Published held-out-chromosome gene split; stricter NTv3 follow-up retains 264 test genes whose full contexts avoid native training regions.',
        'Comparator estimates use the full published test, not necessarily the same strict subset.',
        'Target-gene chromosome exclusion and whole-context exclusion answer different exposure questions.',
        ['ntv3-danio-protocol','ntv3-danio-context-disjoint-protocol'],['ntv3-final-danio','ntv3-final-external-results'])
    design('re2g','ENCODE-rE2G: perturbation-pair evaluation','re2g alphagenome2-original','assay fixed','zero-shot',
        'K562 CRISPRi pairs are external labels. NTv3 reports full and common-pair cohorts; AG2 additionally evaluates source-held-out rE2G pairs excluding rE2G training pairs.',
        'No perturbation-label fitting for the sequence-model score; reference expression may supply cell conditioning.',
        'Assay-label separation does not imply the all-folds sequence model has not seen the reference DNA.',
        family(evidence='ntv3-final-re2g')+family(evidence='s2f-ag2-e2g'),['ntv3-final-re2g','s2f-ag2-e2g'])
    design('ag2-sequence','AlphaGenome 2: sequence-to-function training','alphagenome2-original','blocks','supervised',
        'Eight genomic folds: six training, one validation, one test. Expand 196,608-bp targets to 1,048,576-bp inputs; remove validation/test windows overlapping a training input.',
        'Fold-specific teachers and ablation models score their held-out targets, cropping 425,984 bp from each flank.',
        'This full-context sequence exclusion is different from the final all-folds model’s variant-label reporting split.',
        family(evidence='s2f-ag2-interval-targets')+family(evidence='s2f-ag2-conditioning-ablation'),['s2f-ag2-interval-targets','s2f-ag2-conditioning-ablation'])
    design('ag-variants','AlphaGenome 1 / 2: QTL label selection','alphagenome-original alphagenome2-original','chromosome','variant-selection',
        'Variant-effect reporting uses chr3/6/9/12/16/18/19/21; other chromosomes guide AG2 model/scorer selection. IBDverse uses all chromosomes after excluding specified selection-cohort variants.',
        'IBDverse is not used for AG2 model/scorer selection.',
        'The all-folds sequence model has seen reference DNA at test loci. Chromosome exclusion here concerns variant-effect labels, not reference sequence training.',
        family(evidence='s2f-ag2-eqtl-methods')+family(evidence='s2f-ag1-shared-variant-methods'),['s2f-ag2-eqtl-methods','s2f-ag1-shared-variant-methods'])
    design('ag2-condition','AlphaGenome 2: held-out tracks / conditions','alphagenome2-original','condition','supervised',
        'Mask 184 test tracks across 30 human conditions and 26 validation tracks across 12 conditions; 32 distinct conditions across those sets.',
        'Assay labels are masked during all-folds sequence training. Some primary-cell arms additionally mask bulk PBMC/astrocyte tracks.',
        'This is track/condition exclusion, not a held-out-DNA split; evaluation uses 1,749 fold5 intervals.',
        family(evidence='s2f-ag2-imputation'),['s2f-ag2-imputation'])
    design('ag2-time','AlphaGenome 2: newly released single-cell data','alphagenome2-original','time blocks','supervised',
        'Temporal cutoff 1 October 2025: exclude 16 new datasets from encoder/post-training. Dedicated evaluation uses fold1 validation genomic intervals.',
        'Fine-tuning baseline uses fold1 training intervals; temporal and genomic exclusion apply to different layers.',
        'An unseen study is not necessarily an unseen locus or unseen participant. The genomic evaluation split is called validation in the source.',
        ['ag2-cellxgene-expression-lfc-alphagenome2-protocol'],['s2f-ag2-cellxgene-expression'])
    design('cerberus','Cerberus: released genomic-fold ensemble','cerberus-original','blocks released','supervised',
        'Author README describes eight models with different held-out genomic folds.',
        'The inspected release does not provide original fold-to-region assignments, exact split coordinates or final scored counts.',
        'Generic data-building code supports several splitting modes; available options do not establish the split used by the paper. Do not import AG1/AG2 QTL chromosomes into Cerberus.',
        family(evidence='s2f-cerberus-model')+family(evidence='s2f-cerberus-qtl'),['s2f-cerberus-model','s2f-cerberus-qtl'])
    design('evo1-promoters','Evo 1: promoter readouts and fixed scores','evo1-original','random assay fixed','mixed',
        'Supervised heads fit 4,673 LaFleur promoters; 520 random LaFleur validation promoters plus 5,391 additional validation constructs. Evaluate independent source-study test cohorts.',
        'Zero-shot promoter likelihoods are a separate arm with no readout fitting.',
        'Synthetic construct/source-study separation does not mean chromosome holdout.',
        family(evidence='evo1-regulatory'),['evo1-regulatory'])
    design('fitness-fixed','Evo 1 / Evo 2, RNAGym and ProteinGym: fixed assay scoring','evo1-original evo-original rnagym proteingym','fixed','zero-shot',
        'Score eligible external mutation libraries without downstream fitness-label fitting. Evo nucleotide assays retain unique native DNA variants; protein-only viral encodings are separate cohorts.',
        'No new downstream train/validation/test assignment. Pairwise missing-score filtering can change the scored assay subset across models.',
        'Fixed-assay scoring is not the supervised RNAGym split. It does not demonstrate that the base model excluded the assayed gene or species.',
        family(evidence='evo1-fitness')+family(evidence='evo2-review-protein-fitness')+family(evidence='evo2-review-ncrna-fitness')+family(evidence='rnagym-scorer-audit'),['evo1-fitness','evo2-review-protein-fitness','evo2-review-ncrna-fitness','rnagym-scorer-audit'])
    design('traitgym-zero','TraitGym: fixed zero-shot variants','traitgym','fixed','zero-shot',
        'Score fixed matched/full causal-variant cohorts without a fitted head; chromosome-weighted AUPRC aggregates scores within chromosomes.',
        'AG2 complex-trait evaluation uses the full 11,400 variants, not its QTL test-chromosome subset. Optional score ensemble uses benchmark-wide min–max normalization.',
        'Chromosome-weighted reporting does not hold out chromosomes from training. Separate fitted TraitGym models do use outer chromosome holdout.',
        ['traitgym-mendelian-zero','traitgym-complex-zero','traitgym-complex-ag2-protocol'],['traitgym-definition','s2f-ag2-traitgym'])
    design('carbonx','Carbon-X: DNA Intelligence Index','carbonx-evals','fixed','zero-shot',
        'Load the pinned DNAIntelligenceIndex benchmark subsets from the HF partition named train.',
        'This train name denotes the released evaluation collection; the scorer does not fit on these labels.',
        'The interface does not identify a chromosome/species holdout. Dataset partition names are not sufficient evidence of model fitting.',
        family(evidence='carbonx-scorer-coding'),['carbonx-scorer-coding'])
    design('recovery-design','Evo 2 / GENERator / Carbon / CENO: continuation and synthetic contexts','evo-original generator-evals generator2-evals carbon-evals ceno-evals','synthetic fixed','generation',
        'Gene continuation withholds a suffix from a supplied reference prompt; GENERator/Carbon recovery samples taxonomic configurations. NIAH creates synthetic context/depth cells.',
        'Oracle-ranked designs and experimental candidate selection are separate from benchmark partitioning.',
        'A withheld suffix, generated DNA or synthetic prompt is not evidence that its source genome was excluded from pretraining.',
        ['evo-gen-completion-sampling','generator-recovery-protocol','carbon-recovery-protocol','ceno-gene-continuation-protocol','carbon-niah-protocol','ceno-niah-protocol'],['evo2-review-evo-gen-completion-generation','generator-eval-methods','carbon-final-recovery-code','final-ceno-gene-continuation','carbon-final-niah-code','final-ceno-niah-protocol'])
    design('evo-essentiality','Evo 1 / Evo 2: zero-shot essentiality','evo1-original evo-original','fixed','zero-shot',
        'Source genome-wide experimental labels are scored per genome without fitting an essentiality head. Evo 1 uses 56 bacterial studies and lambda/P1; Evo 2 adds two archaeal studies and a separate human DepMap cohort.',
        'No new supervised gene, chromosome or taxon partition is defined by these zero-shot protocols.',
        'Reporting a score for another genome does not establish that the genome was withheld from pretraining. Do not substitute BacBench’s genus-held-out fitted protocol.',
        family(evidence='evo1-essentiality')+family(evidence='evo2-review-essentiality')+['evo-depmap-zero'],['evo1-essentiality','evo2-review-essentiality','evo2-review-depmap'])
    design('evo-variants','Evo 2 / DART: fixed variant and likelihood cohorts','evo-original dart','fixed','zero-shot',
        'ClinVar, SpliceVarDB and BRCA saturation-editing cohorts are scored without a variant-label-trained head. Evo 2 DART likelihood/embedding comparisons use fixed source cohorts.',
        'BRCA1 embedding probe is separate. Coding/noncoding, exonic/intronic and splice-proximity subsets are reporting strata.',
        'DART supervised-task chromosome partitions do not automatically apply to these comparisons. Some embedding layers were selected externally on BRCA1 rather than on DART labels.',
        ['evo-clinvar-zero','evo-splicevardb-zero','evo-brca1-zero','evo-brca2-zero']+family(evidence='evo2-review-dart'),['evo2-review-vep','evo2-review-dart'])
    design('spliceai2-variants','SpliceAI2: main variant-effect benchmarks','spliceai2-evals','fixed','zero-shot',
        'Main multispecies model uses human chr21/22 for validation, with other human and nonhuman genes in training. GT>GC, GT>AT, OpenSplice and other variant cohorts are not restricted to those chromosomes.',
        'The paper does not specify test-only gene/homology exclusion for these variant cohorts.',
        'The human-only, chr21/22 top-transcript reconstruction arm is a separate model/protocol; its ortholog exclusion cannot be generalized to main variant results.',
        family(evidence='spliceai2-gtag-method')+['spliceai2-bend-opensplice-protocol'],['spliceai2-gtag-method','spliceai2-opensplice-method','spliceai2-top-transcript-method'])
    design('spliceai2-tissue','SpliceAI2: tissue-specific junctions and variant readout','spliceai2-evals','chromosome','mixed',
        'Tissue fine-tuning trains on chr2/4/6/8/10–22/X and validates on chr1/3/5/7/9, then evaluates filtered junctions from held-out genes.',
        'Separate tissue-variant ridge analysis uses fivefold chromosome-grouped CV, comparing reference-usage-only and reference-plus-model features.',
        'The fine-tuned sequence model and the fitted variant-feature readout are different fitting layers, even when both use chromosome groups.',
        ['spliceai2-spliceai2-tissue-junction-protocol','spliceai2-spliceai2-tissue-variant-protocol'],['spliceai2-tissue-method','spliceai2-tissue-variant-method'])
    design('gpn-fixed','GPN-Star: fixed multispecies variant cohorts','gpn-evals','fixed','zero-shot',
        'ClinVar, DMS, rare/common and other label-selected variant cohorts are scored without a downstream prediction head. Species-specific allele-frequency definitions and score intersections determine eligibility.',
        'Common-score intersections are cohort alignment, not a new train/test split. Pretraining validation chromosomes are a separate layer.',
        'Evaluating a named species is not evidence that the species was withheld from model training.',
        family(evidence='gpn-scoring')+family(evidence='gpn-benchmarks'),['gpn-scoring','gpn-benchmarks'])
    design('plantcad-potato','PlantCAD2: potato conservation transfer','plantcad2-zero','taxon fixed','zero-shot',
        'Paper-only potato GERP endpoint; the source states that Solanaceae was excluded from PlantCAD2 pretraining.',
        'No downstream task-label fitting; conservation thresholds define evaluation labels.',
        'A claimed family-level pretraining exclusion, distinct from holding species out of adaptation. It does not assert zero sequence similarity to other plant families.',
        ['plantcad2-potato-gerp-paper'],['plantcad2-potato'])
    design('genosm-cohorts','Genos-m: within-study and cross-study microbiome prediction','genosm-evals','assay released','probe',
        'Colorectal-cancer prediction reports within-cohort tenfold CV and pairwise train-one-cohort/test-another evaluation across 14 cohorts.',
        'The paper does not specify nested model-selection partitions, repeat-sample handling or participant overlap across cohorts.',
        'A cohort holdout is not evidence of participant-disjoint validation or controlled collection-site effects.',
        ['genosm-crc-within','genosm-crc-cross'],['genosm-crc'])

    # Derive task-level associations from the reviewed cohort/layer mapping,
    # preserving differences between protocols that reuse a benchmark.
    d['split_protocol_strategies']=[]
    per_design={r['id']:r for r in d['split_designs']}
    ev_by_design={}
    for r in d['split_design_evidence']:
        if r['field']=='partition_rule':ev_by_design.setdefault(r['design_id'],r['evidence_id'])
    axes={}
    for r in d['split_design_strategies']:axes.setdefault(r['design_id'],[]).append(r['strategy_id'])
    def protocol_axes(key,p,default):
        """Preserve differences within a comparative row, without a Cartesian
        product between that row's strategies and all its source protocols."""
        pid=p['id'];task=p['task_id']
        if key=='design-plantcad-acr':return ['taxon','chromosome'] if pid.endswith('train_on_arabidopsis-lora') else ['taxon']
        if key=='design-generator-cv':return ['random','chromosome'] if '-nt-revised-' in pid else ['random','released']
        if key=='design-botanic-transfer':return ['taxon'] if pid.startswith('botanic1-cross-') else ['taxon','chromosome']
        if key=='design-botanic-conservation':return ['chromosome','taxon'] if 'conservation' in pid else ['chromosome']
        if key=='design-botanic-pgb':return ['released'] if task in ['pgb-promoter-strength','pgb-terminator-strength'] else ['chromosome']
        if key=='design-plantcad-zero':return ['released'] if pid.startswith('plantcad2-pretraining-') else ['fixed']
        if key=='design-genosm-random':return ['random'] if pid in ['genosm-promoter-mlp','genosm-virulence-mlp'] else ['released']
        if key=='design-loam-selection':return ['taxon'] if pid.startswith('loam-essential-') else ['released']
        if key=='design-bgc':return ['bgc'] if pid=='bgc-adomain-probe' else ['random','bgc']
        if key=='design-guanine-other':return ['time','fixed'] if pid=='guanine-clinvar_snv-protocol' else ['random']
        if key=='design-compass-transfer':return ['assay','gene'] if p['source_evidence_id']=='final-compass-transfer' else ['assay']
        if key=='design-gpn':return ['chromosome'] if pid=='gpn-annotation-probe' else ['assay']
        if key=='design-carbon':return ['chromosome'] if pid=='carbon-malinois-protocol' else ['released'] if pid=='carbon-dream-protocol' else ['fixed']
        if key=='design-ceno-probes':return ['blocks','condition'] if pid=='ceno-tad-protocol' else ['chromosome']
        if key=='design-dgeb':
            if 'classification' in pid:return ['released']
            return ['fixed','taxon'] if p['split_rule'].startswith('Bacterial corpus') else ['fixed']
        if key=='design-danio':return ['chromosome','blocks'] if 'context-disjoint' in pid else ['chromosome']
        if key=='design-cerberus':return ['blocks','released'] if pid.startswith('cerberus-tracks-') else ['released']
        if key=='design-evo1-promoters':return ['fixed'] if p['adaptation']=='zero-shot' else ['random','assay']
        if key=='design-recovery-design':return ['synthetic'] if 'niah' in pid else ['fixed']
        if key=='design-genosm-cohorts':return ['assay'] if pid=='genosm-crc-cross' else ['released']
        # Remaining multiple-axis entries explicitly apply their joint rule to
        # the protocol (e.g. chromosome + paralog exclusion, donor + gene region).
        return [axis.removeprefix('split-strategy-') for axis in default]
    for r in d['split_design_protocols']:
        for axis in protocol_axes(r['design_id'],protocols[r['protocol_id']],axes[r['design_id']]):
            c.put('split_protocol_strategies',dict(protocol_id=r['protocol_id'],strategy_id='split-strategy-'+axis,
                note=per_design[r['design_id']]['partition_rule'],evidence_id=ev_by_design[r['design_id']]),('protocol_id','strategy_id'))
    # New source review evidence belongs with the updated protocols too.
    for pid in ['traitgym-mendelian-probe','traitgym-complex-probe']+['gb-'+key+'-protocol' for key in gb_evidence]:
        evidence=[r['evidence_id'] for r in d['field_evidence'] if r['entity_table']=='protocols' and r['entity_id']==pid and r['field']=='split_rule']
        previous=next(r for r in d['source_reviews'] if r['entity_table']=='protocols' and r['entity_id']==pid)
        evidence+=json.loads(previous['evidence_ids_json'])
        c.review('protocols',pid,'Partition construction and model-selection review against pinned source code; retain all task-specific scoring details.',evidence,previous['limitations'])
    return d
