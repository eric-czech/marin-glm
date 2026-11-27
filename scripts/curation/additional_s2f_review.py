'Source review of AlphaGenome 2 and Cerberus, including shared AG1 targets.\n\nDataset × target is the record unit. Assay channels, conditions, scorer choices,\ncohort subsets and model configurations are linked variants/protocols. Public\ntrack inventories are not substituted for released labelled evaluation cohorts.\n'
import json
import csv
from common import Catalogue, ROOT, DATE

CACHE = 'research/artifacts/final-audit/other-models/'
API = '67d9080d70283173f6060a1d9850942736350547'
RESEARCH = '3eecf48e58d7babbbc53525a8a0cf29a179e20a6'
BASK = '4330a9281e8d3b060c03249a05047a4fb37d2576'
AG2PDF = 'https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphagenome-2-deciphering-how-cells-read-dna-to-better-understand-disease/alphagenome-2.pdf'
AG1PDF = 'https://storage.googleapis.com/deepmind-media/papers/alphagenome.pdf'
VARIANT_SPLIT = ('Zero-shot variant reporting uses test chromosomes 3, 6, 9, 12, 16, 18, 19 and 21. '
    'Chromosomes 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 15, 17, 20, 22 and X guide AG2 model/scorer selection. '
    'The all-folds sequence model has seen reference-genome sequence at test loci: this partition holds out variant-effect labels from model/scorer selection, not reference DNA from supervised sequence-to-function training.')
INTERVAL_SPLIT = ('Eight-fold contiguous genomic-block partition inherited from AG1/Borzoi: six blocks training, one validation, one test. '
    'Expand 196,608-bp targets to 1,048,576-bp inputs and exclude validation/test windows overlapping a training input. '
    'Fold-1 teacher scores its held-out test targets, cropping 425,984 bp from each flank. Human GRCh38/GENCODE v46; mouse GRCm38/vM23.')
IMPUTATION_SPLIT = ('All-folds sequence training with test/validation assay tracks masked, not a held-out sequence split. '
    '184 test tracks across 30 human conditions; 26 validation tracks across 12 conditions; 32 distinct conditions across those sets. '
    'Evaluation uses 1,749 fold-5 intervals and the central 196,608 bp of each 1,048,576-bp input. '
    'All bulk PBMC/astrocyte tracks are additionally masked for the corresponding primary-cell experiments.')


def populate(d, inspected=None):
    c = Catalogue(d)
    track_index={row['id']:row for row in d.setdefault('assay_tracks',[])}
    task_track_index={(row['task_id'],row['track_id']):row for row in d.setdefault('task_tracks',[])}
    def put_track(row):
        old=track_index.get(row['id'])
        if old is None: d['assay_tracks'].append(row);track_index[row['id']]=row
        else: old.update(row)
    def put_task_track(row):
        key=(row['task_id'],row['track_id']);old=task_track_index.get(key)
        if old is None:d['task_tracks'].append(row);task_track_index[key]=row
        else:old.update(row)
    if inspected is None:
        p = ROOT / 'data/additional-s2f-artifact-inspections.json'
        if not p.exists(): p = ROOT / CACHE / 'artifact-inspections.json'
        inspected = json.loads(p.read_text())
    c.source('alphagenome2-paper', 'AlphaGenome 2 complete author report', AG2PDF, 'paper',
        '78-page author report linked to bioRxiv10.64898/2026.11.11.765857 v1', CACHE + 'alphagenome2.pdf',
        notes='All report methods, figures, supplementary figures and the embedded Supplementary Table 1 inspected. Separate referenced Supplementary Tables 2–19 were not retrieved from the rate-limited publisher.')
    c.source('ag1-original-report', 'AlphaGenome 1 complete author report', AG1PDF, 'paper',
        'Complete 103-page author report; related version of Nature 649, 1206–1218', CACHE + 'alphagenome.pdf')
    c.source('ag2-api-release', 'AlphaGenome API release and documentation',
        f'https://github.com/google-deepmind/alphagenome/tree/{API}', 'repository', API,
        CACHE + f'alphagenome-{API}/README.md',
        notes='Complete immutable repository tree downloaded and inspected. AG2 client, scorer interfaces and examples are public; original AG2 model weights and paper-wide labelled evaluation tables are not in this release.')
    c.source('ag1-evaluation-example', 'AlphaGenome research variant evaluation notebook',
        f'https://github.com/google-deepmind/alphagenome_research/blob/{RESEARCH}/colabs/variant_eval_examples.ipynb',
        'repository-file', RESEARCH, CACHE + f'alphagenome_research-{RESEARCH}/colabs/variant_eval_examples.ipynb',
        notes='Complete pinned research repository inspected; notebook links original AlphaGenome evaluation labels/predictions in public GCS Feather files. It is not an AG2 benchmark release.')
    c.source('cerberus-release', 'Cerberus official Baskerville release',
        f'https://github.com/calico/baskerville/tree/{BASK}/releases/cerberus', 'repository', BASK,
        CACHE + f'baskerville-{BASK}/releases/cerberus/README.md',
        notes='Complete repository downloaded; README, params, full human/mouse target tables, model/split/data construction and generic evaluation implementation inspected. No processed Cerberus train/test corpus or paper-specific matched GTEx cohort is in this tree.')
    c.source('cerberus-metadata', 'Cerberus primary bioRxiv metadata and complete abstract',
        'https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.02.756377', 'metadata', 'bioRxiv v1 dated 2026-10-09',
        CACHE + 'cerberus-metadata.json')
    c.source('ag2-metadata', 'AlphaGenome 2 primary bioRxiv metadata',
        'https://api.biorxiv.org/details/biorxiv/10.64898/2026.11.11.765857', 'metadata', 'bioRxiv v1 dated 2026-11-17',
        CACHE + 'ag2-metadata.json')
    c.source('ag2-downloads', 'Official AlphaGenome downloads inventory',
        'https://deepmind.google.com/science/alphagenome/downloads', 'release-index', '2026-11-27 snapshot', CACHE + 'ag2-downloads.html',
        notes='Public HTML download inventory inspected; downloadable model outputs and atlas results are not the paper-wide original evaluation cohorts.')

    def ev(slug, page, text, ag2=True):
        return c.evidence('s2f-' + slug, 'alphagenome2-paper' if ag2 else 'ag1-original-report',
            'PDF page ' + str(page), text, url=(AG2PDF if ag2 else AG1PDF) + '#page=' + str(page))
    def prop(model, category, name, value, evidence, notes='', status='reported'):
        c.put('model_properties', dict(id='s2f-' + model + '-' + name.replace(' ', '-').lower(), model_id=model,
            category=category, name=name, variant=None, value=value, status=status, evidence_id=evidence, notes=notes))
    def variant(tid, suffix, name, evidence, n=None, unit=None, context='', notes=''):
        vid=tid+'-'+suffix
        c.put('variants',dict(id=vid,task_id=tid,name=name,evidence_id=evidence,context=context,
            dataset_revision='AlphaGenome 2 report v1' if tid.startswith('ag2-') else 'Source-defined cohort',
            target_count=n,target_unit=unit,input_length=1048576,notes=notes))
        return vid
    meta = c.evidence('s2f-ag2-bibliography','ag2-metadata','Primary metadata record, title/date/version/DOI',
        'AlphaGenome 2 predicts regulatory activity and variant effects across cell states; Gayoso et al.; bioRxiv DOI 10.64898/2026.11.11.765857, version 1 posted 17 November 2026. The author announcement is dated 11 November; report bibliographic date uses the primary preprint metadata.', 'documentation')
    c.get('papers','alphagenome2').update(title='AlphaGenome 2 predicts regulatory activity and variant effects across cell states',doi='10.64898/2026.11.11.765857',publication_date='2026-11-17',status='preprint',notes='Full 78-page author-hosted report inspected; primary bioRxiv metadata supplies the posting date.')
    c.field('papers','alphagenome2','bibliography',meta)
    cm = c.evidence('s2f-cerberus-bibliography','cerberus-metadata','Primary metadata record and complete abstract',
        'Kelley, Yuan, Huang and Linder; Cerberus: bidirectional state space blocks improve accuracy and efficiency of regulatory sequence models; bioRxiv10.64898/2026.10.02.756377 v1 posted 9 October 2026. Abstract reports held-out coverage prediction, GTEx v11 eQTL/sQTL/paQTL causality, eQTL magnitude and Hydra interaction-range interpretation.', 'documentation')
    c.get('papers','cerberus').update(doi='10.64898/2026.10.02.756377',publication_date='2026-10-09',status='preprint',notes='Complete primary abstract and author release inspected. Full publisher article, PDF and JATS could not be retrieved because the publisher returned HTTP 429.')
    c.field('papers','cerberus','bibliography',cm)
    access = c.evidence('s2f-cerberus-access','cerberus-metadata','Retrieval scope on 2026-11-27',
        'Publisher versioned full text and article return HTTP 429; the publisher-provided JATS URL https://www.biorxiv.org/content/early/2026/10/09/2026.10.02.756377.source.xml also returns HTTP 429. Parent independently tried the normal full PDF. Official Baskerville complete pinned release and primary bioRxiv metadata/abstract were successfully inspected. Full methods have not been inspected.', 'documentation')
    c.limit('papers','cerberus','full-text-methods','not-retrieved','Versioned article, full text, full PDF and the primary metadata-linked JATS endpoint were rate limited. This is an access failure, not evidence that methods were not published.',access)
    release = c.evidence('s2f-ag2-release-scope','ag2-api-release','Complete pinned API/research release trees; report Code/Data availability p.53',
        'AG2 API client and tutorials are public. Report states AG2 model source and weights will be provided upon final publication. The separately pinned alphagenome_research repository implements the original AlphaGenome model and original evaluation examples, not AG2 training or the original AG2 benchmark cohorts. Public atlas outputs are predictions, not labels or original held-out evaluation manifests.', 'code')
    c.limit('models','alphagenome2','local-model-weights-and-training-code','not-released','Report p.53 explicitly defers model source and weights until final publication; current public release supplies the API client.',release)
    c.limit('papers','alphagenome2','separate-supplementary-tables','not-retrieved','Tables 2–19 referenced throughout the report are separate from the retrieved 78-page report; versioned publisher supplemental access was rate limited. Embedded Table 1 and all supplementary figures were inspected. Exact referenced accession/condition tables are not represented as inspected artifacts.',release)
    arch = ev('ag2-model', '20–29',
        'One-hot DNA input (1,048,576×4), human/mouse taxonomy and a 256-dimensional condition embedding; seven-stage convolutional encoder/decoder with U-Net skips, 11 multi-query-attention blocks at 128-bp resolution (8,192 positions), and pair blocks at 2,048 bp. FiLM conditions normalized features throughout the sequence backbone. Reference ontology embeddings or a frozen scRNA autoencoder embedding plus trained adapter supply conditions. Four stages: supervised pretraining, condition refinement, eight-teacher distillation, expression-conditioning post-training. This is supervised sequence-to-function prediction, not autoregressive nucleotide generation.')
    corpus = ev('ag2-corpus','2; 16–20; 31–32',
        'Pretraining combines the AG1 human/mouse functional-genomics corpus with 36 single-cell studies, CpG methylation across 185 human reference conditions and scRNA/scATAC pseudobulks. Stage-4 encoder/post-training uses 107 million human single-cell expression profiles, including CELLxGENE Discover snapshot 16 March 2026. Sequence-model pretraining excludes disease/perturbed cells; encoder corpus retains disease samples. Fold-1 temporal models hold out datasets published after 1 October 2025, whereas all-folds models use all datasets.')
    heads = ev('ag2-heads','25–27',
        'Fourteen supervised heads plus a Stage-4 denoised expression head. RNA/CAGE/accessibility coverage at 1 bp, TF/histone ChIP at 128 bp, contacts at 2,048 bp, scalar gene-expression outputs, five-class per-base splice sites, splice-site usage and donor–acceptor junction counts. Gene masks use known GENCODE annotations; junction inference first thresholds predicted sites (probability≥0.1, up to 512 sites per role/strand). These output types do not establish full isoform recovery or an independently scored dense-annotation task.')
    contexts = ev('ag2-context','20; 29; 35',
        'All reported core inputs are 1,048,576 bp; interval scoring crops to 196,608 bp while variant and enhancer scores use 1 Mb context. Distillation uses 95% full 1 Mb examples and 5% segment-packed 8–512 kb examples with 1,024 bp isolation gaps and block-diagonal attention. This shorter-context training protocol is not itself a long-context benchmark result.')
    for cat,name,value,e in [('architecture','Backbone and conditioning','Convolutional U-Net; 11 attention blocks; 256-dimensional FiLM biological conditioning',arch),('tokenization','DNA encoding','One-hot A/C/G/T at one position per nucleotide; no learned subword tokenizer',arch),('pretraining','Training corpus','Supervised human/mouse bulk and single-cell functional genomics; 107 million human scRNA profiles for encoder/post-training',corpus),('context','Context and packing','1,048,576-bp inputs; interval scoring central 196,608 bp; 5% packed 8–512 kb distillation examples',contexts),('evaluation','Output heads','Coverage, scalar expression, pairwise contacts/junctions, splice-site labels/usage, methylation',heads),('release','Release scope','API client public; AG2 model weights and source deferred until final publication',release)]: prop('alphagenome2',cat,name,value,e)
    c.get('models','alphagenome2').update(description='Human/mouse supervised sequence-to-function model with 1 Mb DNA and explicit tissue/cell-state conditioning; reference ontology embeddings or scRNA-derived embeddings; coverage, expression, splicing and interaction readouts.')

    def collection(id,name,paper,source,evidence,note):
        c.put('evaluations',dict(id=id,name=name,description=note,paper_id=paper,source_id=source,
            status='paper-audited',scope_note='Model-associated evaluation collection; not a dedicated independently adopted benchmark framework.',evidence_id=evidence,notes=note))
        rid=id+'-project-definition-review'
        c.put('project_reviews',dict(id=rid,name=name,decision='outside-definition',dedicated=0,reviewed=DATE,
            search_scope='Full available primary report/release and current official repository reviewed for purpose and benchmark status.',
            rationale='Evaluations accompany a sequence-to-function model; this is not primarily a dedicated standardized gLM evaluation framework.',evidence_id=evidence))
        primary_sid=c.get('papers',paper)['source_id']
        pe=evidence
        if c.get('evidence',pe)['source_id']!=primary_sid:
            pe=c.evidence(id+'-primary-paper-link',primary_sid,'Primary paper: model-associated evaluation purpose',note)
        c.put('project_review_papers',dict(review_id=rid,paper_id=paper,relation='associated-model',evidence_id=pe),('review_id','paper_id','relation'))
        c.put('project_review_evaluations',dict(review_id=rid,evaluation_id=id,relation='associated-collection',note=note,evidence_id=evidence),('review_id','evaluation_id'))
    collection('alphagenome2-original','AlphaGenome 2 evaluations','alphagenome2','alphagenome2-paper',arch,
        'Condition-specific molecular prediction, held-out-track imputation, temporal expression conditioning, variant effects and perturbation-validated enhancer links. Protocols retain the distinct holdout axes. Atlas yields and selected-locus illustrations are not treated as experimental genome-annotation labels.')
    ag1paper=c.get('papers','alphagenome');ag1e=c.evidence('s2f-ag1-collection',ag1paper['source_id'],'Article Methods: variant benchmarks',
        'AlphaGenome benchmarks variant effects using source-specific splicing, polyadenylation and chromatin-QTL datasets; AG2 explicitly inherits selected targets and scorers. Original source datasets and per-model cohort variants/protocols remain distinct.')
    collection('alphagenome-original','AlphaGenome 1 shared evaluations','alphagenome',ag1paper['source_id'],ag1e,
        'Shared original AlphaGenome and AlphaGenome 2 variant-effect targets; original and updated model protocols are separately recorded.')
    # The collection's primary evidence must identify its own paper, even though
    # the accessible method evidence can be a related earlier author version.
    ce=c.evidence('s2f-cerberus-collection','cerberus-paper','Primary abstract and linked official release',
        'Cerberus evaluates held-out functional-genomics coverage and GTEx v11 eQTL/sQTL/paQTL prediction. Detailed task limits are explicit because full article methods were not retrievable.', 'paper')
    collection('cerberus-original','Cerberus evaluations','cerberus','cerberus-paper',ce,
        'Official released architecture and complete assay inventories; primary abstract-defined coverage/QTL evaluation claims. Exact original biological test cohorts and full methods are not retrievable in the inspected releases.')
    api_e=c.evidence('s2f-ag2-api-interface','ag2-api-release','src/alphagenome/models/v2 and tutorials; complete immutable tree',
        'The released AG2 API accepts DNA/interval, species and reference condition or expression-conditioning embedding; scorer interfaces compare predicted ALT and REF outputs. It supplies inference/scoring interfaces, not all original benchmark preprocessing and label-matching implementations.', 'code')
    api_r=c.resource('ag2-api-scoring-code','ag2-api-release','AlphaGenome 2 API variant scoring and conditioning interfaces','evaluation-code','github',
        f'https://github.com/google-deepmind/alphagenome/tree/{API}/src/alphagenome/models/v2',api_e,revision=API,
        notes='Client-side interface, not AG2 local model implementation or a complete reproduction of the original benchmarks.')
    c.collection_resource('alphagenome2-original',api_r,api_e,'evaluation-code')

    def add(tid,name,dataset,target,description,e,features,metrics,split,n=None,unit='example',
            model='alphagenome2',paper='alphagenome2',coll='alphagenome2-original',form='isolated',axis='none',
            task_type='regression',label='Experimental molecular measurements',notes='',populations=('human',),adaptation='supervised sequence-to-function pretraining; no task-specific fitting',
            interface='1,048,576-bp DNA plus biological condition → source-defined model readout',selection='Model/scorer selection uses the source-designated validation axis; final test labels are not used for this selection.',review_scope=None,status='paper-audited'):
        c.put('tasks',dict(id=tid,name=name,dataset_name=dataset,target=target,description=description,task_type=task_type,
            label_basis=label,evidence_id=e,status=status,limitations=notes,input_description=interface,output_description=target))
        c.member(tid,coll,e,note='Source-defined dataset × target; conditions/channels/model configurations are linked variants or protocol details.')
        for cat in list(dict.fromkeys(['functional-prediction','context-specific']+features)):
            c.category(tid,cat,e,'The cited method identifies the experimental target, biological context and model readout.', 'target' if c.get('categories',cat)['dimension']=='region' else 'relevance')
        if not any(c.get('categories',cat)['dimension']=='application' for cat in features):
            application='model-development' if 'cell-encoder' in tid else ('variant-interpretation' if 'variant-effects' in features else 'regulatory-engineering')
            c.category(tid,application,e,'The measured molecular prediction or companion model diagnostic supports this research function; it is not a clinical-use claim.','relevance')
        c.output(tid,form,e,target,unit,axis=axis,rationale=description,limitations=notes)
        if 'cds' in features:
            c.put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope='restricted-target' if features==['cds'] else 'mixed',rationale='Explicit coding-sequence target/stratum in source.',evidence_id=e),('task_id','feature_id'))
        pid=tid+'-'+model+'-protocol'
        c.protocol(pid,tid,'Original '+c.get('models',model)['name']+' source protocol',adaptation,interface,split,unit,e,
            metrics=[x if isinstance(x,tuple) else (x,'Source-defined aggregation') for x in metrics],
            fitted='Modality-specific supervised prediction heads in the pretrained model',selection=selection,notes=notes)
        c.use(tid,model,paper,e,pid,'original-paper','Source-defined benchmark protocol; no Evo 1/Evo 2 use is inferred.')
        for pop in populations:c.population(tid,pop,e,'Source sequence/target origin explicitly identified by the report/release.')
        for field in ['target','task_type','label_basis','input_description','output_description']:c.field('tasks',tid,field,e)
        if n is not None:c.count(tid,n,unit,e,protocol=pid,qualifier='Source-reported retained evaluation count; does not denote the number of pretraining examples.')
        if model=='alphagenome2':c.task_resource(tid,api_r,api_e,'evaluation-code',note='Inference/scorer interface; original processed benchmark cohort is separate.')
        c.review('tasks',tid,review_scope or 'Complete source-specific method, relevant figure/count definitions, model configuration and release-scope comparison.',[e,release if model=='alphagenome2' else ce],notes)
        c.review('protocols',pid,'Readout, adaptation, held-out axis, experimental labels, scoring unit, metric aggregation and source availability.',[e],notes)
        return pid

    intervals=ev('ag2-interval-targets','32–34',
        'Fold-1 teacher predictions are scored on central 196,608-bp held-out targets. Bulk RNA uses protein-coding exonic read-density aggregation; scRNA uses direct scalar gene expression; scATAC averages base-level signal per consensus peak. Per-feature log activity is centered across comparison conditions. Pearson correlation is computed across genes/peaks per condition and averaged; pooled LFC R² measures cross-condition variance explained. ChIP evaluates consensus peaks active in other conditions as negatives, selecting 250 condition-specific peaks per condition for each of 10 TFs and 11 histone marks. This regional/gene aggregation does not evaluate dense annotation or full isoforms.')
    interval_specs=[
        ('gtex-lfc','GTEx tissue expression differences','GTEx bulk RNA-seq','Condition-centered log expression across GTEx tissues',['gene'],('human',)),
        ('encode-rna-lfc','ENCODE cell-line expression differences','ENCODE paired-end total RNA-seq','Condition-centered log expression across 18 cell lines',['gene'],('human',)),
        ('scrna-lfc','Atlas single-cell expression differences','AG2 curated human/mouse single-cell atlas pseudobulks','Condition-centered log gene expression within tissue/lineage/assay/source groups',['gene'],('human','mouse')),
        ('scatac-lfc','Atlas single-cell accessibility differences','AG2 curated human/mouse scATAC atlas consensus peaks','Condition-centered log accessibility within tissue/lineage/assay/source groups',['regulatory'],('human','mouse'))]
    for slug,name,dataset,target,features,pops in interval_specs:
        tid='ag2-'+slug
        add(tid,name,dataset,target,'Predict condition-specific molecular activity across genes or supplied peak regions; evaluate aggregated values, not dense base labels.',intervals,
            features+['signal-profile-prediction','target-discovery'],[('pearson','Mean per-condition cross-feature LFC Pearson r'),('r2','Pooled feature×condition LFC variance explained')],INTERVAL_SPLIT,populations=pops,
            notes='Exact retained genes/peaks and comparison-group membership require the separate referenced Supplementary Table 8, which was not retrieved.')
        c.limit('tasks',tid,'retained-feature-and-condition-manifest','not-retrieved','Separate Supplementary Table 8 specifies the comparison groups; exact retained interval/feature tables are not in the retrieved report/API release.',release)
    for slug,label_name,n in [('tf','TF',10),('histone','histone-modification',11)]:
        tid='ag2-'+slug+'-condition-peaks'
        add(tid,label_name+' condition-specific peak classification','ENCODE '+label_name+' ChIP-seq consensus peaks',
            'Whether a supplied consensus peak is experimentally called active in a condition',
            'Rank consensus regions by mean predicted 128-bp signal; negatives are peaks active in other conditions, testing cell specificity rather than generic genomic background.',intervals,
            ['regulatory','tfbs'] if slug=='tf' else ['regulatory'],[('auprc','Per condition, then average within target; mean across evaluated targets')],INTERVAL_SPLIT,
            unit='consensus peak × condition',task_type='binary classification',label='ENCODE experimentally called peak presence',
            notes='250 active regions per condition are selected without replacement across conditions, prioritizing peaks active in few conditions. Total retained peak count and species allocation of the EFO comparison conditions are not reported in the retrieved report.', populations=())
        c.count(tid,n,'assayed molecular targets',intervals,qualifier='Ten named transcription factors or 11 named histone marks; a target count, not an example count.')
        c.unknown_origin(tid,intervals,'The method lists molecular targets and ENCODE EFO comparison groups but does not enumerate their species. The model training corpus alone is not evidence that both species were scored here.')
        c.limit('tasks',tid,'scored-condition-species','not-retrieved','Exact EFO comparison-group species/identities require the separate study/condition tables, which were not retrieved. No human-only or dual-species evaluation origin is inferred from the training corpus.',release)
    c.count('ag2-encode-rna-lfc',18,'cell-line conditions',intervals)
    groupcounts=ev('ag2-interval-group-counts', '6',
        'Figure 2 b caption reports 51 scRNA comparison groups (11 mouse/40 human) and 27 scATAC groups (10 mouse/17 human), rather than per-gene/per-peak example counts.')
    for tid,n in [('ag2-scrna-lfc',51),('ag2-scatac-lfc',27)]:c.count(tid,n,'comparison groups',groupcounts)

    ablation=ev('ag2-conditioning-ablation','27; 62',
        'Conditioning-placement ablations train fold-1 Stage-1 models from scratch, three seeds per configuration, alongside an unconditioned multitask baseline on matched bulk datasets. Supplementary Figure4b reports ENCODE-cell-line and GTEx-tissue expression LFC Pearson and TF/histone consensus-peak AUPRC. These are not the two-stage teacher checkpoints used for the main interval comparisons.')
    for tid in ['ag2-encode-rna-lfc','ag2-tf-condition-peaks','ag2-histone-condition-peaks']:
        p=c.get('protocols',tid+'-alphagenome2-protocol')
        p.update(name='AlphaGenome2 Stage-1 conditioning ablation',adaptation='End-to-end supervised Stage-1 models; three replicate seeds per conditioning configuration',
            split_rule=INTERVAL_SPLIT.replace('Fold-1 teacher','Fold-1 Stage-1 ablation model'),
            selection='Seven source-defined conditioning configurations plus the matched unconditioned baseline; three seeds; held-out fold-1 intervals.',source_evidence_id=ablation)
        c.field('protocols',p['id'],'model_configuration',ablation)
        c.review('protocols',p['id'],'Complete Stage-1 ablation setup, source-specific target, split and metric; no Stage-2 teacher protocol is borrowed.',[ablation,intervals])
        if tid=='ag2-encode-rna-lfc':
            d['protocol_metrics']=[r for r in d['protocol_metrics'] if not(r['protocol_id']==p['id'] and r['metric_id']=='r2')]
    p=c.protocol('ag2-gtex-lfc-stage1-ablation','ag2-gtex-lfc','AlphaGenome2 GTEx Stage-1 conditioning ablation',
        'Supervised Stage-1 models; three seeds per conditioning configuration',
        '1Mb DNA plus conditioning → exonic RNA aggregation → tissue-centered gene expression',
        INTERVAL_SPLIT.replace('Fold-1 teacher','Fold-1 Stage-1 ablation model'),'gene × tissue',ablation,
        metrics=[('pearson','Mean cross-gene LFC Pearson across GTEx tissues')],selection='Source-defined conditioning placement ablation; same target, separate training configuration.')
    c.use('ag2-gtex-lfc','alphagenome2','alphagenome2',ablation,p)
    c.review('protocols',p,'Full conditioning-placement experiment and source-specific GTEx Pearson target.',[ablation,intervals])
    qtl=ev('ag2-eqtl-methods','35–37',
        'GTEx v11 uses SuSiE SNVs deduplicated per variant–gene–tissue by maximum PIP. TenK10K uses 28 PBMC cell types; IBDverse eQTL Catalogue r8 QTS000045 retains 47 intestinal cell types and 3,524 causal pairs after excluding non-test-chromosome variants used in other QTL validation sets and types with<10 positives. Causality positives PIP>0.9 versus PIP<0.01 controls matched 1:1 on active-regulatory-element overlap stratum and nearest target-TSS distance. Counts: GTEx 67,674 (33,837 positives); TenK10K 12,692 (6,346); IBDverse 7,048 (3,524). Sign/magnitude: GTEx 33,829, TenK10K 6,346, IBDverse 3,524. Sign uses accuracy–recall AUC and tissue/cell-weighted AUROC; magnitude uses weighted Spearman. Bulk scorer sums exonic RNA coverage; scRNA scorer log(CPM_ALT+0.001)−log(CPM_REF+0.001).')
    c.put('metrics',dict(id='sign-accuracy-recall-auc',name='Sign accuracy–recall AUC',definition='Area under cumulative effect-direction accuracy versus fraction of examples retained after ranking by predicted absolute effect magnitude.',direction='higher'))
    ibd_split=('All chromosomes, excluding every variant appearing on non-test chromosomes in GTEx eQTL/sQTL and TenK10K eQTL/caQTL causality validation sets. '
        'Remove cell types with fewer than 10 PIP>0.9 positives. IBDverse is not used for model or scorer selection. '
        'This is a variant-label holdout design; reference sequence is available to the all-folds S2F model.')
    for cohort,title,classn,pos in [('gtex11','GTEx v11',67674,33837),('tenk10k','TenK10K PBMC',12692,6346),('ibdverse','IBDverse intestinal',7048,3524)]:
        for target_kind in ['causality','sign','magnitude']:
            tid='ag2-'+cohort+'-eqtl-'+target_kind
            n=classn if target_kind=='causality' else (33829 if cohort=='gtex11' else pos)
            mets=[('auprc','Pooled precision–recall and tissue/cell-type-weighted AUPRC')] if target_kind=='causality' else ([('sign-accuracy-recall-auc','Pooled effect-direction accuracy over magnitude-ranked recall'),('auroc','Tissue/cell-type-weighted direction AUROC')] if target_kind=='sign' else [('spearman','Tissue/cell-type-weighted observed versus predicted effect magnitude')])
            add(tid,title+' eQTL '+target_kind,title+' SuSiE fine-mapped eQTLs',
                {'causality':'Fine-mapped causal versus matched non-causal variant–gene pair','sign':'Direction of expression effect for a high-confidence causal variant–gene pair','magnitude':'Observed allelic fold change or regression slope of a causal variant–gene pair'}[target_kind],
                'Assess expression-regulatory variant effects in the source tissue/cell type using reference-condition or expression-conditioned prediction.',qtl,
                ['gene','regulatory','variant-effects','variant-interpretation'],mets,ibd_split if cohort=='ibdverse' else VARIANT_SPLIT,n=n,unit='variant–gene–condition pair',
                task_type='binary classification' if target_kind in ['causality','sign'] else 'regression',
                label='Statistical fine-mapping PIP and observed eQTL effect estimates, not experimental variant perturbations',
                notes='Exact processed label/negative-match files and per-condition denominators are not supplied in the inspected API repository. Noncausal labels are statistical controls, not experimentally proven absence of effect.')
            c.limit('tasks',tid,'processed-cohort-files','not-released','Full API/research release trees do not contain the original AG2 matched QTL tables; referenced supplementary mappings were not retrieved. Source methods/counts are available.',release)
            if target_kind=='causality':c.count(tid,pos,'positive variant–gene–condition pairs',qtl)
            if cohort!='gtex11' and target_kind!='magnitude':
                cond=ev('ag2-expression-conditioned-qtl','37',
                    'TenK10K expression-conditioning uses an independent Gong PBMC dataset, up to one million cells and 25/28 matched cell types; 1/16/128 cells per type with 10 trials assess cell-count sensitivity. IBDverse expression-conditioning uses its own donor-majority-tissue scRNA cells and the same 47 cell types. The scRNA measurement conditions the model; variant-effect labels remain separate.')
                cv=variant(tid,'expression-conditioned','Expression-conditioned subset/protocol',cond,context='TenK10K 25 matched cell types versus full 28; IBDverse 47. No new dataset×target record is created for a conditioning pathway.')
            if cohort!='gtex11' and target_kind!='magnitude':
                cp=tid+'-expression-conditioned-protocol'
                c.protocol(cp,tid,'AlphaGenome 2 expression-conditioned '+title+' '+target_kind,
                    'Frozen all-folds Stage-4 model; no cohort-specific backbone fitting',
                    'Independent/scRNA cohort cell profiles → averaged encoder embedding → denoised gene-expression ALT/REF score',
                    ibd_split if cohort=='ibdverse' else VARIANT_SPLIT,
                    'variant–gene–cell-type pair',cond,metrics=mets,embeddings=True,variant=cv,
                    selection='TenK10K uses an independent Gong expression dataset and 25/28 matched cell types; IBDverse uses its own expression profiles and all 47 types. QTL effect labels are not encoder conditioning input.',
                    notes='Conditioning subset is not assumed to have the same example count as the full reference-conditioned cohort.')
                c.use(tid,'alphagenome2','alphagenome2',cond,cp)
                c.review('protocols',cp,'Complete expression-conditioned subset, cell embedding source, cell-count trials and separate variant-label split.',[cond,qtl],
                    'Exact retained variant count for the 25-type TenK10K conditioning subset is not stated.')
            if cohort=='gtex11':variant(tid,'tissue-specific','Tissue-specific versus nonspecific strata',qtl,context='7,169 tissue-specific and 26,660 nonspecific causal pairs by GTEx expression-cluster/PIP criterion; these counts apply to sign/magnitude eligible variants, not matched negative pairs.')
    caqtl=ev('ag2-tenk-caqtl','37',
        'TenK10K single-cell caQTLs evaluate 24 mapped PBMC cell types on variant test chromosomes. In-peak PIP>0.9 positives:5,116. For causality,4:1 controls are in-peak AF>0.1, nominalP>0.1, absent from credible sets, from a peak with some nominal association; match peak-midpoint distance within cell type without replacement, yielding 25,580 pairs. Coefficient task correlates predicted 1201-bp center-mask log 2 count differences with caQTL slopes over 5,116 positives; cell-type-weighted Spearman.')
    for kind,n,mets in [('causality',25580,[('auprc','Cell-type/pooled causality precision–recall')]),('magnitude',5116,[('spearman','Cell-type-weighted effect-size correlation')])]:
        add('ag2-tenk10k-caqtl-'+kind,'TenK10K chromatin QTL '+kind,'TenK10K SuSiE single-cell caQTLs',
            'Causal peak-associated variant class' if kind=='causality' else 'Observed caQTL effect slope',
            'Score supplied in-peak variants using condition-matched predicted accessibility; this is a variant-effect task, not dense peak discovery.',caqtl,
            ['regulatory','variant-effects','variant-interpretation'],mets,VARIANT_SPLIT,n=n,unit='variant–peak–cell-type pair',
            task_type='binary classification' if kind=='causality' else 'regression',label='Statistical fine-mapping and observed caQTL slopes')
    pd=ev('ag2-parkinson-qtl','39',
        'Unseen Parkinson disease substantia nigra/cingulate cortex cohort is scored natively on T2T-CHM13v2.0. caQTL-ASCA labels require concordant cis-caQTL and within-individual ASCA FDR<0.1:43,526 positive-direction and 43,070 negative-direction instances. eQTL FDR<0.05 overlaps the same variant/cell/region caQTL-ASCA tuple, minimumP per gene/cell/region; 1,620/1,739 remain inside 1 Mb (846 positive/774 negative). Mean cohort scRNA embeddings condition AG2. Both tasks pool instances and report sign accuracy versus magnitude-ranked recall; Scooby comparison has 276 scored eQTLs and treats others as abstentions.')
    for kind,n in [('chromatin',86596),('expression',1620)]:
        tid='ag2-parkinson-'+kind+'-direction'
        add(tid,'Parkinson cohort '+kind+' QTL direction','Sigalova Parkinson disease single-nucleus multiome cohort',
            'Allelic direction of accessibility imbalance' if kind=='chromatin' else 'Allelic direction of eGene expression change',
            'Evaluate condition-specific direction using an unseen disease cohort and native T2T sequence/annotations.',pd,
            (['regulatory'] if kind=='chromatin' else ['gene','regulatory'])+['variant-effects','variant-interpretation'],
            [('accuracy','Cumulative sign accuracy versus magnitude-ranked recall'),('recall','At matched baseline sign-accuracy operating points')],
            'Study is unseen during AG2 pretraining; cohort scRNA profiles supply conditioning. Source does not apply the GRCh38 QTL chromosome holdout to this native-T2T cohort.',
            n=n,unit='variant–cell-type–brain-region instance',task_type='effect-direction classification',
            notes='Chromosome split is not stated for this cohort; do not copy the standard GRCh38 benchmark split. Conditioning on measured cohort expression is explicit.')
        c.limit('tasks',tid,'chromosome-partition','not-reported','The cohort-specific method specifies native-T2T scoring and cohort selection but no validation/test chromosome partition.',pd)

    imp=ev('ag2-imputation','41–43',
        'Imputation-split model holds out 184 bulk tracks,181 after RNA strand merging:176 chromatin tracks and 5 gene-expression tracks. Chromatin assays are ATAC, DNase, histone ChIP and TF ChIP. Mean signal at consensus peaks classifies active versus other-condition-only peaks; support-weighted AUPRC uses positive-peak fraction as track weight. Continuous genome-wide Pearson uses 32 bp bins; 1 bp tracks sum-pool,128 bp ChIP repeats with signal-preserving scaling. RNA gene-body aggregation uses quantile-normalized condition-centered LFC Pearson. Scoring includes 1,749 central 196,608 bp fold-5 targets but the model has been trained on sequence throughout the genome.')
    for ass,title in [('atac','ATAC-seq'),('dnase','DNase-seq'),('histone','Histone ChIP-seq'),('tf','TF ChIP-seq')]:
        for readout in ['profile','peak']:
            tid='ag2-impute-'+ass+'-'+readout
            add(tid,title+' held-out-track '+('signal' if readout=='profile' else 'peak activity'),
                'AG2 held-out human '+title+' tracks',
                'Continuous genomic signal in an unmeasured condition–channel track' if readout=='profile' else 'Active versus inactive supplied consensus peak in an unmeasured track',
                'Predict a modality omitted for a condition during supervised training using modalities available for that condition.',imp,
                ['regulatory','signal-profile-prediction']+(['tfbs'] if ass=='tf' else []),
                [('pearson','Per-track continuous 32 bp profiles concatenated over 1,749 targets; mean by modality')] if readout=='profile' else [('auprc','Per-track consensus-peak AUPRC; support-weighted mean within modality; peak-frequency strata')],
                IMPUTATION_SPLIT,unit='genomic 32 bp bin × held-out track' if readout=='profile' else 'consensus peak × held-out track',
                form='signal-profile' if readout=='profile' else 'isolated',axis='contiguous' if readout=='profile' else 'none',
                task_type='regression' if readout=='profile' else 'binary classification',
                notes='Modality-specific track identities/counts are in separately referenced Table 4, not retrieved. The 176 chromatin-track total is shared across four assays, not 176 per task.')
            c.limit('tasks',tid,'individual-test-track-manifest','not-retrieved','Separate Supplementary Table 4 defines exact track identities, training/validation/test masking and per-modality counts; unavailable to this inspection.',release)
    add('ag2-impute-rna-lfc','RNA-seq held-out-track expression differences','AG2 held-out human bulk RNA-seq tracks',
        'Cross-condition gene-body expression LFC','Infer gene expression in unobserved RNA tracks using other assays for those conditions.',imp,
        ['gene','signal-profile-prediction'],[('pearson','Mean per-track Pearson across quantile-normalized, centered gene-expression values')],IMPUTATION_SPLIT,
        unit='protein-coding gene × held-out track',notes='Five evaluated RNA tracks after merging eight stranded input tracks; total scored gene count not stated.')
    c.count('ag2-impute-rna-lfc',5,'evaluated merged RNA tracks',imp)
    pbmc=ev('ag2-pbmc-enhancers','43',
        'Nine primary PBMC reference conditions have all bulk tracks withheld and train only on scRNA/scATAC pseudobulks. Candidate rDHSs are ENCODE ENCFF708KEK. Enhancer labels: accessible nonpromoter sites (z-scATAC≥1.67, midpoint≥200 bp from protein-coding/lncRNA TSS), positive if withheld Mint-ChIP H3K27ac z≥1.67. H3K27ac uses rDHS±500 bp signal, not full-gene annotation. AUPRC compares imputed H3K27ac with observed scATAC/cell-line proxies; a separate centered-rDHS signal Pearson tests condition specificity across all nine types.')
    for slug,target,metric in [('classification','Presence of a primary-cell enhancer-like H3K27ac signature','auprc'),('specificity','Condition-centered H3K27ac signal at supplied rDHS regions','pearson')]:
        add('ag2-pbmc-enhancer-'+slug,'PBMC enhancer '+slug,'ENCODE primary PBMC Mint-ChIP / rDHS',target,
            'Test cross-modality imputation in primary immune cells with experimentally measured histone signal withheld from model training.',pbmc,
            ['enhancer','regulatory'],[(metric,'Per-cell-type AUPRC' if metric=='auprc' else 'Pearson over pooled centered rDHS×cell-type signals')],IMPUTATION_SPLIT,
            unit='rDHS × PBMC cell type',task_type='binary classification' if metric=='auprc' else 'regression',
            notes='Exact retained rDHS counts are not reported. Enhancer-like labels are a thresholded histone/activity proxy, not direct perturbation validation.')
    temporal=ev('ag2-cellxgene-expression','38–39; 30–32',
        '167 human CELLxGENE evaluation groups compare 5–10 related cell types sharing dataset/tissue/assay/suspension/lineage.147 groups derive from 120 training-split datasets/118 collections; 20 groups derive from 16 datasets/16 collections published after 1 October 2025. These datasets are absent from reference-condition pretraining. The temporal encoder/post-training holds out the latter datasets. Fold-1 sequence model predicts gene-expression LFC from mean cell embeddings versus group-specific 5,000-step fine-tuning of only embeddings/FiLM layers on fold-1 training intervals. The dedicated Evaluation paragraph explicitly reports held-out fold-1 validation intervals, although the surrounding section describes held-out intervals generally.')
    tid='ag2-cellxgene-expression-lfc'
    pid=add(tid,'CELLxGENE expression conditioning','CELLxGENE temporal expression-conditioning groups',
        'Cell-type-specific gene-expression log fold change','Predict cell-type expression differences using scRNA-derived conditioning; compare frozen-backbone conditioning against per-dataset adaptation.',temporal,
        ['gene','target-discovery'],[('pearson','Cross-gene LFC Pearson, averaged within 5–10 related cell types and reported per group')],
        'Temporal single-cell split at 1 October 2025 plus reference genomic fold-1. Encoder/post-training excludes 16 new datasets; both approaches are evaluated on fold-1 validation intervals according to the dedicated Evaluation paragraph. Fine-tuning baseline uses only fold-1 training intervals.',
        n=167,unit='cell-type comparison group',adaptation='Stage-4 expression conditioning; comparison with per-group embeddings/FiLM fine-tuning',
        notes='The temporal holdout is 20 groups, not 167 held-out datasets. Per-gene predictions use known gene annotations; no full transcript recovery. Separate Table 13 group identities were not retrieved.')
    for suffix,n in [('seen',147),('temporal-test',20)]:variant(tid,suffix,suffix+' CELLxGENE groups',temporal,n,'comparison groups')
    c.limit('tasks',tid,'interval-label-wording','conflicting','Data-split/overview text describes held-out test intervals, whereas the dedicated CELLxGENE Evaluation paragraph explicitly says fold-1 validation intervals not used for model selection in these comparisons. The protocol preserves the dedicated statement.',temporal)
    vaccination=ev('ag2-vaccination-accessibility','39–40',
        'Held-out SARS-CoV-2 vaccination atlas conditions on post-vaccination CITE-seq cell embeddings pooled over days 11/28. Independent ASAP-seq defines 236,854 consensus 501 bp peaks across level-2 PBMC states. Compare vaccine-induced groupA CD 8 cells versus CD 8 effector-memory; retain 37,035 peaks predicted accessible(CPM≥5 in either state). Correlate observed versus imputed log(CPM+1) differences using Pearson. Selection uses predicted accessibility, not an unfiltered peak population.')
    add('ag2-vaccine-accessibility-lfc','Vaccine-induced accessibility differences','Zhang SARS-CoV-2 vaccination CITE-seq/ASAP-seq atlas',
        'Accessibility log fold change between vaccine-induced and effector-memory CD 8 states',
        'Test prediction of an unmeasured epigenetic modality from expression conditioning in a new induced immune state.',vaccination,
        ['regulatory','signal-profile-prediction'],[('pearson','Observed versus imputed peak LFC across 37,035 selected peaks')],
        'Unseen multimodal vaccination cohort; expression cells supply conditioning and separate ASAP-seq cells supply observed accessibility. Days 11 and 28 pooled; all-folds AG2. No separate genomic test fold specified for this cohort.',
        n=37035,unit='consensus peak',notes='The evaluated peaks are selected using predicted accessibility. This is peak-aggregate regression, not dense peak-boundary annotation.')
    denoise=ev('ag2-cell-encoder-diagnostics','40–41',
        'The separate scRNA autoencoder is evaluated without DNA input. Denoising uses 16 temporally held-out datasets: average embeddings from 1,2,4,8,16,32,64 cells or all cells; 20 subsampling trials; decode and compare condition-centered gene-expression LFC to full pseudobulk. Integration uses 113,897 vaccination-atlas cells,6 donors,30 level-2 types, comparing 256-dimensional frozen encoder embeddings with a dataset-trained scVI baseline. scib-metrics reports k-means NMI/ARI, cLISI, cell-type silhouette and donor batch silhouette; overall 0.6 biological+0.4 batch, without min–max rescaling.')
    for slug,target,mets,n,unit in [('denoising','Pseudobulk cell-type expression differences reconstructed from few cells',[('pearson','Cross-gene LFC Pearson; mean 20 trials; median across datasets')],16,'held-out expression datasets'),('integration','Cell-type conservation and donor mixing of scRNA embeddings',[('cluster-agreement','scib-metrics NMI/ARI/cLISI/silhouettes; 0.6 biological+0.4 batch score')],113897,'single cells')]:
        add('ag2-cell-encoder-'+slug,'Cell encoder '+slug,'CELLxGENE temporal test datasets' if slug=='denoising' else 'Vaccination PBMC CITE-seq expression atlas',
            target,'Assess the expression-conditioning encoder separately from the DNA sequence backbone.',denoise,['gene','embedding-analysis'],mets,
            'Temporal held-out 16 datasets for denoising; unseen vaccination dataset for embedding comparison. No DNA sequence input or chromosome partition applies.',n=n,unit=unit,
            form='diagnostic',task_type='expression-encoder diagnostic',interface='Raw single-cell UMI counts →256-dimensional expression embedding/reconstruction; no DNA input',
            adaptation='Frozen pretrained scRNA expression autoencoder; scVI baseline fitted on the vaccination dataset',
            notes='Companion expression-encoder evaluation, not a genomic sequence-only model test. The all-folds unmasked encoder is used for integration; the temporal encoder is used for denoising.')

    e2g=ev('ag2-e2g','43–45',
        'Gene-centered 1 Mb input; readout is log predicted gene expression using observed bulk RNA or scalar scRNA channels. Score candidate element by mean absolute input-gradient attribution in a 2400 bp Gaussian(σ300) window; no window-wide normalization. Outside±524,288 bp receives zero. Held-out ENCODE-rE2G:4,378 pairs/190 positives across K 562, WTC 11, HCT 116, Jurkat, GM 12878, weighted by direct-effect probability. K 562:10,356/471 originally, minus 3 negative missing-GENCODE genes →10,353/471. Astrocyte:1,902/122; permissive hits(FDR<0.1, negative expression LFC) overlapping cCREs. Astrocyte training includes its 47,577-cell screen pseudobulk; perturbation labels are separate. AUPRC all pairs and distance strata. Expression-conditioned and all-bulk-astrocyte-withheld variants are evaluated separately.')
    for tid,title,dataset,n,pos in [('ag2-re2g-heldout','ENCODE-rE2G held-out cell-line links','ENCODE-rE2G held-out CRISPRi pairs',4378,190),('ag2-astrocyte-links','Astrocyte enhancer–gene links','Human astrocyte CRISPRi enhancer screen',1902,122)]:
        add(tid,title,dataset,'Perturbation-supported enhancer-to-gene regulatory link',
            'Rank supplied element–gene pairs against experimental CRISPRi expression effects; this is pairwise relationship prediction, not dense element or transcript annotation.',e2g,
            ['enhancer','gene','genetic-interactions','target-discovery'],[('auprc','Direct-effect-probability weighted for held-out rE2G; unweighted for astrocytes; whole set and TSS-distance strata')],
            'All-folds AG2; ENCODE-rE2G held-out pairs exclude the rE2G training set. Astrocyte reference condition includes unperturbed screen pseudobulk; perturbation labels are not trained on. No chromosome split is specified for these pair cohorts.',
            n=n,unit='candidate element–gene pair',form='pairwise',axis='linked',task_type='binary link classification',label='Experimental CRISPRi expression perturbation labels',
            notes='Pair distance may exceed the DNA input window; scores are zero for out-of-window elements rather than dropping those examples.')
        c.count(tid,pos,'positive element–gene pairs',e2g)
        if 'astrocyte' in tid:
            variant(tid,'no-bulk','No observed bulk astrocyte training tracks',e2g,context='Imputation split retains only the screen scRNA pseudobulk for this reference condition; all bulk astrocyte modalities excluded.')
            variant(tid,'expression-conditioned','Screen scRNA expression conditioning',e2g,context='Mean encoder embedding of screen cells replaces the reference ontology embedding; same element–gene target.')
    c.member('ntv3-re2g','alphagenome2-original',e2g,note='Same ENCODE-rE2G K 562 binary linking target; AG2 filters three source-negative pairs with genes absent from GENCODE v46.')
    v=variant('ntv3-re2g','ag2-gencode46','AlphaGenome 2 GENCODE v46 eligible K 562 pairs',e2g,10353,'element–gene pairs',notes='471 positives; distinct from NTv3 common-scored 3,826-pair subset.')
    p=c.protocol('ntv3-re2g-alphagenome2-protocol','ntv3-re2g','AlphaGenome 2 K 562 enhancer-link protocol','Supervised pretrained S2F; no task-specific fitting',
        'Gaussian-weighted absolute input gradient of log predicted expression',
        'All-folds model; original K 562 CRISPRi source cohort with three negative missing-GENCODE genes excluded; no chromosome split.',
        'element–gene pair',e2g,metrics=[('auprc','All pairs and TSS-distance strata')],variant=v,
        selection='Gradient normalization choice evaluated across the reported CRISPRi benchmarks; calibrated atlas cutoffs are separate from ranked AUPRC.')
    c.use('ntv3-re2g','alphagenome2','alphagenome2',e2g,p,'original-paper','Shared dataset×binary target; no new duplicate task.')
    c.count('ntv3-re2g',10353,'element–gene pairs',e2g,protocol=p,variant=v)
    c.review('protocols',p,'Complete AG2 enhancer-scoring and K 562 cohort method; same underlying dataset/target as existing NTv3 record.',[e2g])
    for tid in ['ag2-astrocyte-links','ntv3-re2g']:
        v=variant(tid,'ag2-expression-conditioned','AlphaGenome 2 expression-conditioned enhancer linking',e2g,
            context='Mean encoder embedding from the corresponding screen scRNA profiles; denoised scalar target-gene expression; same Gaussian-weighted gradient scorer and binary link target.')
        pid=tid+'-ag2-expression-conditioned-protocol'
        c.protocol(pid,tid,'AlphaGenome 2 expression-conditioned enhancer linking',
            'Frozen Stage-4 sequence model conditioned on screen scRNA embeddings; no link-label fitting',
            'Screen scRNA → mean cell embedding → target-gene expression gradient over candidate enhancer',
            'Same source CRISPRi pair cohort as the reference-conditioned protocol; scRNA profiles supply conditioning rather than perturbation labels.',
            'element–gene pair',e2g,metrics=[('auprc','Average precision on the same source-defined cohort')],embeddings=True,variant=v)
        c.use(tid,'alphagenome2','alphagenome2',e2g,pid)
        c.review('protocols',pid,'Full reference- versus expression-conditioned enhancer-scoring method and original screen cohort.',[e2g])
    pid='ag2-astrocyte-links-no-bulk-protocol'
    c.protocol(pid,'ag2-astrocyte-links','AlphaGenome 2 enhancer linking without bulk astrocyte tracks',
        'All-folds imputation-split model; screen scRNA pseudobulk is the only retained training data for this reference condition',
        'Reference brain-astrocyte condition → single-cell gene-expression input gradient',
        IMPUTATION_SPLIT+' Original 1,902-pair astrocyte CRISPRi cohort is retained.',
        'element–gene pair',e2g,metrics=[('auprc','Average precision over the same 1,902 pairs')],variant='ag2-astrocyte-links-no-bulk')
    c.use('ag2-astrocyte-links','alphagenome2','alphagenome2',e2g,pid)
    c.review('protocols',pid,'Complete assay-masking and astrocyte link-scoring method; retained screen scRNA is explicit.',[e2g,imp])
    trait=ev('ag2-traitgym','45–46',
        'TraitGym complex-traits evaluates 11,400 noncoding variants with 1:9 causal: matched-control ratio. AG2 scores 500 primary single-cell reference conditions, keeping experimentally observed channels. Eight profile modalities use the 1 Mb L2 norm of log1p ALT−REF differences; scalar scRNA expression uses L2 over gene-level log fold changes. Final score is maximum across observed tracks and 9 modalities. AUPRC average precision; optional AG2/GPN-Star ensemble min–max scales each across the benchmark and averages. This score normalization uses the full benchmark score range, not labels.')
    c.member('traitgym-complex','alphagenome2-original',trait)
    p=c.protocol('traitgym-complex-ag2-protocol','traitgym-complex','AlphaGenome 2 zero-shot TraitGym scoring','Supervised pretrained S2F; no TraitGym labels fitted',
        'Maximum observed-channel multimodal 1 Mb variant effect norm across 500 conditions',
        'Full unified 11,400-variant TraitGym benchmark, not the QTL chromosome subset; optional min–max score ensemble uses all benchmark scores.',
        'variant',trait,metrics=[('auprc','Average precision over all 11,400 variants')],selection='Observed tracks only; maximum over nine modalities and 500 primary reference conditions.')
    c.use('traitgym-complex','alphagenome2','alphagenome2',trait,p)
    c.review('protocols',p,'Complete report TraitGym scorer, channel selection, baseline ensemble and benchmark inclusion method.',[trait])

    atlas=ev('ag2-atlas-diagnostics','12; 48–51',
        'GWAS atlas analysis uses 6,822,130 common/credible-set SNVs across 510 human conditions. Calls require|expressionLFC|>0.1 and log(predictedCPM+1)>1.5. TenK10K calibration sweeps 112 threshold pairs over 6,362 causal SNVs,1,235,667 unassociated background SNVs and 14,010 on-target triplets across 26 reference conditions. Subsequent analyses compare conservation(phyloP≥2.27, within TSS-distance strata), ENCODE cCRE v4 overlap and maximum GWAS PIP. Select the most enriched condition per trait by Fisher/BH; 17/28 traits pass FDR≤10−7; PIP analyses contain 1,333,700 trait–SNV pairs. LoF burden-direction concordance uses 65 nominated trait–gene pairs,13 non-nearest-gene subset; majority-matched phenotype terms, exact binomial test against 0.5. These are calibration/enrichment/association diagnostics, not new experimentally validated dense annotation labels.')
    for slug,name,dataset,target,mets,n,unit in [
        ('tenk-calibration','TenK10K atlas call calibration','TenK10K all-chromosome protein-coding eQTL calibration','On-target/background enrichment and causal-SNV recall',[('enrichment','On-target versus off-target and causal versus background call-rate ratios'),('recall','Fraction of 6,362 causal SNVs called on target')],6362,'causal SNVs'),
        ('conservation','Called-variant conservation enrichment','AG2 GWAS/common-SNV atlas × Zoonomia phyloP','Conservation of called versus uncalled variants within TSS-distance bins',[('enrichment','Distance-stratified conserved fraction; 1 Mb block-bootstrap confidence intervals')],6822130,'candidate SNVs'),
        ('ccre-overlap','Called-variant cCRE overlap','AG2 GWAS/common-SNV atlas × ENCODE cCRE v4','Overlap of called versus uncalled variants with reference cCRE annotations',[('enrichment','Called/uncalled overlap fractions by distance and specificity')],6822130,'candidate SNVs'),
        ('pip-enrichment','GWAS call enrichment by fine-mapping PIP','Open Targets 26.03 SuSiE credible sets × AG2 calls','Call-rate enrichment across fine-mapping PIP bins',[('enrichment','Rate versusPIP≤0.01; trait-matched versus any condition; colocalized/noncolocalized strata')],1333700,'trait–SNV pairs'),
        ('burden-direction','GWAS/LoF direction concordance','Open Targets 26.03 GWAS and rare-variant burden results','Agreement of predicted dosage effect with the opposite LoF burden direction',[('accuracy','Concordant fraction of 65 nominated trait–gene pairs; 13 non-nearest subset')],65,'trait–gene pairs')]:
        tid='ag2-atlas-'+slug
        add(tid,name,dataset,target,'Assess a source-defined aspect of the predicted variant atlas against external association/annotation evidence.',atlas,
            ['gene','regulatory','variant-effects','target-discovery'],mets,
            'All-chromosome atlas. TenK10K labels calibrate score/expression thresholds; trait-matched cell condition is selected using the same GWAS enrichment data subsequently summarized. These are descriptive/calibration analyses, not independent held-out predictive accuracy estimates.',
            n=n,unit=unit,form='diagnostic',task_type='association/calibration diagnostic',label='Statistical fine-mapping, genomic reference annotations or rare-variant burden associations',
            notes='Exact per-variant processed call/annotation join and all negative/off-target denominators are not released in the inspected API tree. Full atlas output counts are not equivalent to experimental validation examples.')
    c.count('ag2-atlas-tenk-calibration',1235667,'background SNVs',atlas)
    c.count('ag2-atlas-tenk-calibration',14010,'on-target variant–gene–condition triplets',atlas)
    c.count('ag2-atlas-burden-direction',13,'non-nearest-gene trait–gene pairs',atlas)

    # Shared targets. Public original-AG1 scores are fully scanned; the report
    # final cohorts are kept distinct from multi-scorer/all-chromosome releases.
    shared=ev('ag1-shared-variant-methods','46–47; 52–53',
        'Original AlphaGenome variant test chromosomes are 3,6,9,12,16,18,19,21. GTEx/eQTL Catalogue sQTL dataset is described as 21,514 causal and 21,514 matched negative variant–tissue pairs across 49 tissues. Rare splicing outliers use GTEx FRASER 2/DROP 1.3.3, gnomAD 4 AF<0.1%,≤2 individuals, within 250 bp of aberrant junction; 5,819 positives among>one million rare variants. Chromatin tasks from ChromBPNet include African/European LCL caQTL, Yoruba dsQTL causality/magnitude and microglia/SMC coefficients. AG1 center-mask 501 bp log 2 count difference; GM 12878 DNase, suppressor-macrophageDNase for microglia, left-atriumATAC for SMC. Final paQTL report:613 positive/1,950 candidate negatives,100 matched permutations,400 bp PAS masks, zero for insufficient/missing PAS coverage.',False)
    inherited=ev('ag2-inherited-variant-methods','37; 60',
        'AG2 explicitly reuses AG1 datasets/scorers/metrics for GTEx sQTL causality, rare splicing-outlier causality, five chromatin-QTL coefficient sets, three chromatin-QTL causality sets and paQTL causality. Corresponding reference conditions replace AG1 parallel-head indexing. paQTL final positives by distance threshold 50/100/200/300/500/2,000/10,000 bp are 111/156/202/249/281/407/613; each threshold uses 100 matched-control permutations. SPI 1 bQTL is not listed or plotted for AG2 and no AG2 use is inferred.')
    notebook=c.evidence('s2f-ag1-release-interpretation','ag1-evaluation-example','Variant evaluation notebook: configurations, calculate_tissue_weighted_metric and paqtl_auprc',
        'Notebook downloads original AG1 Feather labels/predictions. Tissue aggregation drops missing labels/predictions, computes per-tissue metrics and weights by retained row count. Its paQTL illustration samples one matched pair perPI once; it does not reproduce 100 permutations and does not prefilter scorer configuration/chromosome in the displayed helper. Original report and released-table row counts therefore remain separately identified.', 'code')
    notebook_r=c.resource('ag1-variant-evaluation-notebook','ag1-evaluation-example','Original AlphaGenome variant evaluation notebook','evaluation-code','github',
        f'https://github.com/google-deepmind/alphagenome_research/blob/{RESEARCH}/colabs/variant_eval_examples.ipynb',notebook,revision=RESEARCH)
    c.collection_resource('alphagenome-original',notebook_r,notebook,'evaluation-code')
    shared_specs=[('sqtl','GTEx sQTL causal-variant class','GTEx/eQTL Catalogue splicing QTLs','sqtl_variant_causality_gene_human','causality',['splice','splice-junction'], 'auprc'),
        ('paqtl','GTEx polyadenylation-QTL causal-variant class','GTEx/eQTL Catalogue polyadenylation QTLs','paqtl_variant_causality_human','causality',['polya','utr3'],'auprc')]
    for cohort,title in [('caqtl_african','African-ancestry LCL caQTL'),('caqtl_european','European-ancestry LCL caQTL'),('dsqtl_yoruba','Yoruba LCL dsQTL')]:
        for kind in ['causality','coefficient']:
            shared_specs.append((cohort+'-'+kind,title+' '+kind,'ChromBPNet '+title,cohort+'_variant_'+kind+'_human',kind,['regulatory'],'auprc' if kind=='causality' else 'pearson'))
    for cohort,title in [('caqtl_microglia','Microglia caQTL'),('caqtl_smc','Coronary smooth-muscle caQTL')]:
        shared_specs.append((cohort+'-coefficient',title+' magnitude','ChromBPNet '+title,cohort+'_variant_coefficient_human','coefficient',['regulatory'],'pearson'))
    for slug,title,dataset,fileid,kind,features,metric in shared_specs:
        tid='ag-shared-'+slug.replace('_','-'); file=fileid+'.feather';url='https://storage.googleapis.com/alphagenome/evals/'+fileid+'_predictions.feather'
        c.source(tid+'-data','Original AlphaGenome '+title+' labels and predictions',url,'dataset-file',
            'Public original AlphaGenome evaluation snapshot inspected 2026-11-27',CACHE+'ag1-evals/'+file,
            notes='Full Feather file read; hashes, labelled/non-null rows and chromosome subsets recorded in the artifact-inspection manifest. It is not automatically the original AG2 processed cohort.')
        info=inspected[fileid]
        datae=c.evidence(tid+'-artifact',tid+'-data','All Feather rows, columns, label nulls, variants and chromosomes',
            'Fully scanned '+str(info['n'])+' released rows; '+str(info['test_rows_with_target'])+' non-null-target rows on variant test chromosomes, representing '+str(info['test_distinct_variants'])+' distinct variant IDs. '
            'Rows can repeat a variant for tissue/gene or scorer configuration. These measured release counts must not be substituted for the report final cohort. SHA256 '+info['sha256']+'.','data')
        notes=('The release contains multiple scorer configurations/all-chromosome candidate rows; final processed cohorts and counted unit are separate. '
            'For sQTL,1,370,360/1,423,950 rows have no target; test-chromosome non-null subset has 14,722 positive/14,194 negative pairs, differing from the report 21,514/21,514. '
            'For paQTL, eight scorer variants (160/400 bp, scaling/drop-single-PAS choices) each contain 3,689 rows; do not pool their repeated identities.') if slug in ['sqtl','paqtl'] else 'Public file contains test-chromosome labels/predictions; source genomic build, matching study and scorer remain explicit.'
        add(tid,title,dataset,'Causal regulatory variant class' if kind=='causality' else 'Observed causal-QTL effect size',
            'Predict the stated molecular phenotype of a supplied variant, not a dense genomic annotation or full transcript.',shared,
            features+['variant-effects','variant-interpretation'],[(metric,'Tissue-weighted for sQTL; 100 matched permutations for paQTL; whole-cohort metric for chromatin QTL')],VARIANT_SPLIT,
            model='alphagenome',paper='alphagenome',coll='alphagenome-original',unit='variant–tissue/gene association' if slug in ['sqtl','paqtl'] else 'variant association',
            task_type='binary classification' if kind=='causality' else 'regression',label='Statistical fine-mapping/molecular-QTL measurements',notes=notes,status='artifact-audited')
        c.member(tid,'alphagenome2-original',inherited,note='AG2 explicitly reuses this source dataset and target; original AG1 release is linked as a related-version artifact.')
        p=tid+'-alphagenome2-protocol'
        c.protocol(p,tid,'AlphaGenome 2 inherited '+title+' protocol','Supervised pretrained S2F; zero-shot variant scorer',
            'Corresponding condition and inherited AG1 molecular variant scorer',VARIANT_SPLIT,'supplied variant association',inherited,
            metrics=[(metric,'Same dataset/scorer/metric as AG1, except source-defined paQTL distance strata')],
            selection='Source variant validation chromosomes guide model/scorer selection; test chromosomes report final metrics.',notes=notes)
        c.use(tid,'alphagenome2','alphagenome2',inherited,p)
        c.review('protocols',p,'Full AG2 inherited-dataset statement and supplementary plotted target/metric; cross-check original AG1 method and public full-data release.',[shared,inherited,datae,notebook],notes)
        c.review('tasks',tid,'Original and AG2 inherited complete methods/figures; full original released Feather scan and notebook cohort/metric behavior.',[shared,inherited,datae,notebook],notes)
        c.field('tasks',tid,'released-cohort-count',datae)
        c.count(tid,info['n'],'released Feather rows',datae,split='released artifact',method='measured',qualifier='Includes null labels/repeated scorer identities where documented; not a final test example count.')
        if slug not in ['sqtl','paqtl']:
            c.count(tid,info['test_rows_with_target'],'test variant-association rows',datae,split='test',method='measured')
        else:c.limit('tasks',tid,'report-to-release-cohort-reconstruction','not-reported','Released multi-scorer/candidate rows and source-described cohort counts use different subsets/units. Exact source-specific filtering sufficient to reconstruct the reported denominator is not exposed by the notebook.',datae)
        r=c.resource(tid+'-resource',tid+'-data',title+' original labelled variant table','dataset','other',url,datae,
            revision=info['sha256'],notes='Original AG1 labels and scores. Source limitations distinguish released candidate/configuration rows from the final AG1/AG2 cohort.')
        c.task_resource(tid,r,datae,'evaluation-data');c.task_resource(tid,notebook_r,notebook,'evaluation-code')
        c.collection_resource('alphagenome-original',r,datae,'evaluation-data')
        c.limit('tasks',tid,'ag2-specific-predictions-and-cohort','not-released','The inspected official AG2 API tree does not contain original AG2 predictions/processed cohorts for this inherited benchmark. Original AG1 source labels are publicly available as linked data.',release)
    outlier='ag-shared-splicing-outlier'
    add(outlier,'GTEx rare splicing-outlier variant class','GTEx FRASER 2/DROP/AbSplice rare variants',
        'Rare variant associated with a tissue-specific aberrant splice junction',
        'Classify supplied rare variants by association with observed aberrant splicing; individual junction scores are not complete isoform reconstruction.',shared,
        ['splice','splice-junction','variant-effects','variant-interpretation'],[('auprc','Across tissues, assigning negatives to tissues according to positive tissue distribution')],VARIANT_SPLIT,
        model='alphagenome',paper='alphagenome',coll='alphagenome-original',unit='rare variant–tissue association',task_type='binary classification',
        label='Observed RNA-seq splicing outliers associated with rare variants',notes='The 5,819 positive/>one million candidate count is the source-wide cohort, not the final held-out test count. Original report has zero-shot and supervised Explainable Boosting alternatives; AG2 reports inherited zero-shot scorers.')
    c.count(outlier,5819,'source positive rare variants',shared,split='source cohort',qualifier='Source-wide count; final test-subset denominator not stated.')
    c.member(outlier,'alphagenome2-original',inherited)
    p=c.protocol(outlier+'-ag2-protocol',outlier,'AlphaGenome 2 inherited rare-splicing scoring','Pretrained S2F; zero-shot variant scoring',
        'Inherited RNA/splice-site/usage/junction and composite scorers',VARIANT_SPLIT,'variant–tissue association',inherited,metrics=[('auprc','Across tissue-assigned variants')])
    c.use(outlier,'alphagenome2','alphagenome2',inherited,p)
    c.review('protocols',p,'Full inherited AG2 target/metric and original rare-variant construction, distinguishing zero-shot from original supervised alternative.',[shared,inherited])
    c.limit('tasks',outlier,'processed-test-cohort','not-released','Full pinned original research repository lists no rare-splicing-outlier Feather in its evaluation notebook; AG2 release has no original processed outlier tables. No exact test denominator is asserted.',release)

    # Cerberus: the author release is inspectable, but the original full report
    # is rate limited. Register exactly supported claims and field limitations.
    cr=c.evidence('s2f-cerberus-model','cerberus-release','releases/cerberus/README.md and params.json; complete pinned release',
        'Released dual-species Cerberus has 138.3 million parameters,786,432 bp one-hot DNA input,32 bp output bins(24,576 positions), a convolution tower followed by 8 Hydra bidirectional Mamba-2 blocks and human/mouse output heads. No attention or U-Net decoder. Human 8,361 and mouse 3,102 targets; 8 model folds. Training recipe in params uses Poisson/multinomial loss, AdamW, LR 0.003, batch 2, maximum 50 epochs. Release README explicitly says processed training data release is pending. The public forward-pass verification references check weight/implementation reproducibility; they are not independent biological evaluation labels.', 'code')
    cq=c.evidence('s2f-cerberus-qtl','cerberus-metadata','Complete primary abstract: benchmark and readout statements',
        'Abstract reports GTEx v11 fine-mapped eQTL, sQTL, paQTL benchmarks, negatives matched on allele frequency, gene expression and phenotype-specific positional annotations. eQTL mean AUPRC 0.692 across 48 tissues, observed/predicted effect-size Spearman 0.379. It does not state exact PIP cutoffs, matched cohort counts, chromosome split, scorer windows or complete tissue/variant manifests. Claims of released training/benchmark data in the abstract differ from the current release README, which says processed training data are pending.', 'paper')
    for cat,name,value in [('architecture','Backbone','138.3 M dual-head model; convolutional encoder and 8 Hydra bidirectional Mamba-2 blocks; no attention/decoder'),('tokenization','DNA encoding','One-hot A/C/G/T, one position per nucleotide'),('context','Input and output resolution','786,432 bp input; 24,576 contiguous 32 bp output bins'),('pretraining','Supervised corpus','Human hg38 and mouse mm10 functional-genomics tracks:8,361/3,102, per-track accession/source/transform inventory released'),('training','Released training recipe','AdamW, LR 0.003, batch 2, up to 50 epochs, Poisson/multinomial loss; eight genomic folds'),('release','Model and data availability','Eight fold checkpoints and inference/evaluation code public; processed training corpus not released in the inspected official release')]:prop('cerberus',cat,name,value,cr)
    c.get('models','cerberus').update(description='Supervised human/mouse regulatory sequence-to-function model; 786 kb one-hot DNA, convolutional encoder and bidirectional Hydra state-space blocks; dense 32 bp functional-genomics profiles.')
    c.limit('models','cerberus','processed-training-data','not-released','The official pinned model README explicitly marks processed training-data release pending; target tables are assay identity manifests, not processed sequence/label partitions.',cr)
    c.limit('models','cerberus','abstract-release-claim','conflicting','Primary abstract says training data and benchmark sets are released; the current official README states processed training data release is pending and the complete tree exposes no Cerberus processed train/test corpus.',cq)
    codeurl=f'https://github.com/calico/baskerville/blob/{BASK}/src/baskerville/scripts/hound_eval.py'
    c.source('cerberus-eval-code','Cerberus/Baskerville held-out track evaluator',codeurl,'repository-file',BASK,
        CACHE+f'baskerville-{BASK}/src/baskerville/scripts/hound_eval.py')
    ccode=c.evidence('s2f-cerberus-eval-implementation','cerberus-eval-code','hound_eval.py and metrics.py; complete implementation',
        'Generic evaluator loads a selected dataset split, predicts transformed binned coverage, and writes per-track Pearson r/R²; optional Spearman uses --rank. It can score cross-track specificity if target histograms/groups are available. These implementation options do not establish the exact flags, transformed-versus-raw scoring units or biological cohort used in the inaccessible Cerberus report.', 'code')
    code_r=c.resource('cerberus-track-evaluator','cerberus-eval-code','Baskerville held-out functional-track evaluator','evaluation-code','github',codeurl,ccode,revision=BASK,
        notes='Actual evaluator implementation; original Cerberus cohort and flags are not supplied by this file.')
    c.collection_resource('cerberus-original',code_r,ccode,'evaluation-code')
    manifests={}
    for sp in ['human','mouse']:
        path=f'releases/cerberus/targets_{sp}.txt';url=f'https://github.com/calico/baskerville/blob/{BASK}/'+path
        sid='cerberus-'+sp+'-targets'
        c.source(sid,'Cerberus '+sp+' full assay identity manifest',url,'repository-file',BASK,CACHE+f'baskerville-{BASK}/'+path)
        m=inspected['cerberus-'+sp]
        e=c.evidence(sid+'-inspection',sid,'All target-table rows: identifier, source, assay, clip, scale, sum_stat, strand_pair, description, group',
            'Full manifest has '+str(m['n'])+' rows, assay counts '+json.dumps(m['assays'],sort_keys=True)+'. Human 3′RNA has 1,739 rna3 tracks plus 2 PAS annotation tracks; mouse 212 plus 2. README combines these into 3′RNA totals 1,741/214. Track count is the number of assay output channels, not independent test sequences. Full-table SHA256 '+m['sha256']+'.','data')
        r=c.resource(sid+'-resource',sid,'Cerberus '+sp+' assay identifiers and transforms','manifest','github',url,e,revision=BASK,
            notes='Identity/transform inventory only. Does not contain train/validation/test genomic intervals or measured per-window coverage.')
        c.collection_resource('cerberus-original',r,e,'identity-manifest')
        # These rows identify supervised output channels, not held-out examples.
        table=ROOT / CACHE / f'baskerville-{BASK}/' / path
        if table.exists():
            target_rows=list(csv.DictReader(table.open(),delimiter='\t'))
        else:
            target_rows=[json.loads(t['metadata_json']) for t in d.get('assay_tracks',[])
                if t['source_id']==sid]
        if len(target_rows)!=m['n']:
            raise ValueError('Complete inspected Cerberus '+sp+' target manifest is required for authoring.')
        for target_row in target_rows:
            index=target_row['']
            track_id='cerberus-'+sp+'-track-'+str(index)
            metadata=dict(target_row)
            metadata['inventory_role']='Supervised output-channel identity and transform; not a held-out evaluation example'
            put_track(dict(id=track_id,source_id=sid,source_track_id=target_row['identifier'],
                population_id=sp,assay=target_row['assay'],metadata_json=json.dumps(metadata,sort_keys=True),evidence_id=e))
        manifests[sp]=(e,r)
    foldnote=('Eight released models use different held-out genomic folds according to the author README. '
        'The exact Cerberus fold assignment, training/validation/test interval coordinates, and final scored counts are absent from the inspected release. '
        'Generic data-construction code supports chromosome, proportional and cross-fold splits; those options are not evidence of which original split was used.')
    for assay,title,regions in [('rna','RNA-seq coverage',['gene']),('rna3','3′ RNA-seq coverage',['gene','utr3']),('cage','CAGE signal',['promoter']),('dnase','DNase-seq signal',['regulatory']),('atac','ATAC-seq signal',['regulatory']),('chip','ChIP-seq signal',['regulatory']),('clip','RNA-binding CLIP-seq signal',['mrna'])]:
        tid='cerberus-tracks-'+assay
        pops=('human',) if assay=='clip' else ('human','mouse')
        add(tid,'Cerberus '+title,'Cerberus released functional-genomics target corpus',
            'Contiguous 32 bp '+title+' profile',
            'Predict a source-defined assay profile across the DNA input; this is continuous signal prediction, not gene-structure annotation.',cr,
            regions+['signal-profile-prediction'],[],foldnote,model='cerberus',paper='cerberus',coll='cerberus-original',
            unit='genomic 32 bp bin × assay channel',form='signal-profile',axis='contiguous',populations=pops,
            interface='786,432 bp one-hot DNA →24,576 bins × species-specific assay channels',
            adaptation='End-to-end supervised sequence-to-function training; fold ensemble; no embedding probe',
            notes='Primary abstract reports held-out binned coverage; per-assay score breakdown, exact metric flags and sequence/label partition cannot be verified without the full report/cohort. Channel inventory is artifact-audited; biological result/cohort fields are source-limited.',status='source-limited',
            label='Experimental functional-genomics coverage, with source-specific transforms; original processed cohort not released')
        for sp in pops:
            de,r=manifests[sp];n=inspected['cerberus-'+sp]['assays'].get(assay,0)
            variant(tid,sp,sp+' target channels',de,n,'assay channels',context='Species-specific output inventory; no per-example test partition is encoded in the manifest.')
            c.count(tid,n,sp+' assay channels',de,split='released target inventory',method='measured',qualifier='All model target channels, not a held-out example count.')
            c.task_resource(tid,r,de,'identity-manifest')
            for track in d.get('assay_tracks',[]):
                if track['source_id']=='cerberus-'+sp+'-targets' and track['assay']==assay:
                    put_task_track(dict(task_id=tid,track_id=track['id'],variant_id=tid+'-'+sp,evidence_id=de))

        c.task_resource(tid,code_r,ccode,'evaluation-code')
        for field,reason,detail,e in [('original-test-cohort','not-released','Complete pinned official release has target inventories and forward-pass reference arrays, but no processed original sequence/coverage test corpus or fold-coordinate manifest.',cr),('paper-metric-and-aggregation','not-retrieved','Full report methods were rate limited. Current evaluator implements Pearson/R² and optional Spearman/specificity, but paper flags/aggregation cannot be inferred from optional code paths.',access)]:c.limit('tasks',tid,field,reason,detail,e)
        c.review('tasks',tid,'Complete official assay inventory, architecture/output shapes and generic evaluation implementation; primary abstract claim; explicit failed full-method retrieval.',[cr,cq,ccode,access]+[manifests[sp][0] for sp in pops],foldnote)
        c.review('protocols',tid+'-cerberus-protocol','Source-defined output/interface and fold claim reviewed; exact original cohort/metric unavailable and not replaced with generic code defaults.',[cr,cq,ccode,access],foldnote)
    # Reuse the same GTEx v11 eQTL dataset×targets; matching/scoring differences
    # belong to Cerberus's cohort variant and protocol, not duplicate tasks.
    for target_kind in ['causality','magnitude']:
        tid='ag2-gtex11-eqtl-'+target_kind
        c.member(tid,'cerberus-original',cq,note='Same GTEx v11 eQTL target; Cerberus matched controls/scoring are a source-limited cohort variant, not the AG2 matched table.')
        v=variant(tid,'cerberus','Cerberus GTEx v11 source cohort',cq,context='48 tissues reported; AF/expression/positional matching differs from AG2. Exact cohort files, cutoffs/counts and chromosome partition not retrievable.')
        p=tid+'-cerberus-protocol';metric='auprc' if target_kind=='causality' else 'spearman'
        c.protocol(p,tid,'Cerberus GTEx v11 eQTL '+target_kind,'Supervised S2F model; source-defined variant scoring',
            '786 kb sequence-to-function variant readout; exact ALT/REF aggregation not retrievable',
            'Primary abstract names GTEx v11; exact variant test chromosomes/sampling partition not stated there and full methods were not retrieved.',
            'variant–gene–tissue association',cq,metrics=[(metric,'Mean across 48 tissues' if target_kind=='causality' else 'Effect-size Spearman; exact tissue aggregation not available in the abstract')],variant=v,
            selection='Exact source model/scorer-selection cohort is not retrievable; no AG2 chromosome rule is imported.',
            notes='Public abstract reports 0.692 mean eQTL AUPRC and 0.379 Spearman. These are results, not a cohort count.')
        c.use(tid,'cerberus','cerberus',cq,p)
        if target_kind=='causality':c.count(tid,48,'Cerberus eQTL tissues',cq,protocol=p,variant=v)
        for field in ['cohort-counts-and-matching','variant-label-split','variant-scorer']:
            c.limit('protocols',p,field,'not-retrieved','Full article methods/PDF/JATS were rate limited; complete author release does not supply the exact matched GTEx v11 cohort and original scoring configuration.',access)
        c.review('protocols',p,'Primary complete abstract, exact reported dataset/target/metric, complete public author release search and failed article/PDF/JATS retrieval.',[cq,cr,access], 'Source-limited original protocol; AG2 cohort counts/splits are not borrowed.')
    for kind,regions in [('sqtl',['splice','splice-junction']),('paqtl',['polya','utr3'])]:
        tid='cerberus-gtex11-'+kind+'-causality'
        add(tid,'Cerberus GTEx v11 '+kind+' causality','GTEx v11 fine-mapped '+kind+'s',
            'Fine-mapped causal versus matched noncausal molecular-QTL variant',
            'Assess a supplied variant’s association with splicing or polyadenylation phenotype; no full-isoform recovery is claimed by this endpoint.',cq,
            regions+['variant-effects','variant-interpretation'],[('auprc','Primary abstract reports comparative classification; exact per-tissue weighting not retrievable')],
            'Exact variant-label train/validation/test partition not stated in the available abstract; full methods not retrieved. Do not inherit AG1/AG2 partitions or v8 cohort counts.',
            model='cerberus',paper='cerberus',coll='cerberus-original',unit='variant molecular-QTL association',task_type='binary classification',status='source-limited',
            label='GTEx v11 fine-mapping and source-matched statistical controls',
            notes='Abstract specifies AF, gene-expression and phenotype-specific positional matching; exact PIP thresholds, sample sizes and scorers are not retrievable.')
        c.limit('tasks',tid,'cohort-and-full-methods','not-retrieved','Versioned article/full text/PDF/JATS could not be retrieved. The complete pinned official release contains no exact matched GTEx v11 sQTL/paQTL benchmark files.',access)
        c.review('tasks',tid,'Complete primary abstract and official release; claim and available matching details retained, exact unavailable fields individually identified.',[cq,cr,access])

    # Complete source reviews retain their actual inspection scope. Missing
    # artifacts remain limitations instead of being disguised as pending work.
    for model,paper,collection_id,ids,lim in [
        ('alphagenome2','alphagenome2','alphagenome2-original',[meta,arch,corpus,heads,contexts,intervals,qtl,imp,temporal,e2g,trait,atlas,release],
         'Separate referenced Supplementary Tables 2–19 were not retrieved; original AG2 labelled evaluation cohorts and local model weights/source are not in the inspected public release. Task-specific counts/splits/metrics derive from the full report, not the abstract.'),
        ('cerberus','cerberus','cerberus-original',[cm,cr,cq,ccode,access]+[x[0] for x in manifests.values()],
         'Full article methods/PDF/JATS not retrieved because ofHTTP 429; model architecture/code and all assay identities were inspected. Exact original processed train/test/QTL cohorts are absent from the pinned author release; no optional evaluator flag is asserted as the paper protocol.')]:
        c.review('models',model,'Complete identified available primary report/abstract and pinned official release, with architecture, input encoding, corpus, output targets, context, split claims and release availability distinguished.',ids,lim)
        c.review('papers',paper,'Bibliographic primary metadata plus complete available report/abstract, source-specific methods/figures when accessible, linked release and explicit nonretrieved artifacts.',ids,lim)
        c.review('evaluations',collection_id,'Task-level decomposition by dataset and target; independent split axes and source-specific model protocols; real data versus identities/code/results differentiated.',ids,lim)
    c.review('evaluations','alphagenome-original','Full original report methods for the explicitly inherited targets; complete pinned evaluation notebook and 10 full released Feather files; final cohort and candidate/configuration counts distinguished.',[ag1e,shared,inherited,notebook],
        'Shared original AlphaGenome/AlphaGenome 2 splicing, polyadenylation and chromatin-QTL targets; task-specific original release limitations remain explicit.')
    for r in d['tasks']:
        if r['id'].startswith('ag2-') and r['id'] not in ['ag2-cell-encoder-denoising','ag2-cell-encoder-integration']:
            c.limit('tasks',r['id'],'original-ag2-processed-cohort','not-released','The inspected complete official API/research release does not include the original AG2 processed benchmark label tables and exact scored instance manifests. Full report methods/counts are cited; separate supplementary tables were not retrieved.',release)

    d['task_categories'].sort(key=lambda row: (row['task_id'], row['category_id'], row['relation']))
