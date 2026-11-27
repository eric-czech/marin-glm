"""Resolve stale review notes and distinguish source omissions from protocol choices.

This is an explicit authoring operation, not an import run by normal builds.
Source-specific decisions below accompany the retained field-level evidence.
"""
import collections
import json
import re
from common import Catalogue, ROOT, DATE


def populate(data):
    c=Catalogue(data)
    ev={r['id']:r for r in data['evidence']}
    protocols={r['id']:r for r in data['protocols']}
    original_nulls={field:[p['id'] for p in data['protocols'] if p[field] is None]
                    for field in ('requires_embeddings','fitted_component','selection')}
    previous_report=ROOT/'data/completion-review.json'
    baseline=json.loads(previous_report.read_text())['initial_nulls'] if previous_report.exists() else {f:len(v) for f,v in original_nulls.items()}

    def e(id,source,locator,statement,url=None,basis='paper'):
        c.evidence(id,source,locator,statement,basis,url)
        return id

    plant=e('completion-plantcad-context','plantcad2-paper',
        'Results: Fine-tuning PlantCAD2 accurately predicts cross-species chromatin accessible regions; Fig.4C–G',
        'Fig.4D varies 600–4,600-bp inputs in the multispecies ACR experiment evaluated on maize/barley; Fig.4G varies context in maize 92-cell-type prediction. The Arabidopsis-only experiment uses 600-bp windows. The source does not assign the extended-context runs to that arm.')
    removed={r['id'] for r in data['variants'] if r['task_id']=='plantcad2-ft-cross_species_acr_train_on_arabidopsis'
             and '-context-' in r['id'] and not r['id'].endswith('-600')}
    # These were unsupported duplicate experiment assignments, not missing data.
    for table in ('protocols','counts','evaluation_tasks','task_populations','model_evaluations',
                  'task_resources','task_tracks','split_audit_tasks'):
        assert not any(r.get('variant_id') in removed for r in data[table]),table
    data['variants']=[r for r in data['variants'] if r['id'] not in removed]
    for v in data['variants']:
        if v['task_id'] in ('plantcad2-ft-cross_species_acr_train_on_arabidopsis',
                            'plantcad2-ft-cross_species_acr_train_on_nine_species',
                            'plantcad2-ft-cell_type_specific_acr') and '-context-' in v['id']:
            figure='4B' if 'arabidopsis' in v['task_id'] else '4D' if 'nine_species' in v['task_id'] else '4G'
            v['notes']=f'Figure {figure}. The target remains the central 600-bp region; input length is a context condition, not a different target or additional independent cohort.'
            v['evidence_id']=plant

    bot=e('completion-botanic-donor','botanic-paper','§4.8.3, PDFpp.59–60; Fig.8i–k',
        'Classification uses 885 intermediate-usage donors, 885 constitutive donors and 885 decoy GT sites (2,655 total). Features/thresholds maximize balanced accuracy. A separate broader panel of 3,254 donors supports activation–PSU Spearman correlation; added donors are excluded from feature/threshold fitting. A chromosome validation/test split is stated, but its separate membership and held-out classification denominator are not supplied.',
        'https://huggingface.co/spaces/living-models/botanic1-report/resolve/1a1826804938e6320e20f037956b3818b9c40700/botanic1-report-v3.pdf#page=59')
    t=c.get('tasks','botanic1-sae-splice-usage')
    t['limitations']='The classification panel contains 2,655 sites; the correlation panel contains 3,254 donors. The report states chromosome-separated validation/test, but supplies neither that assignment nor a separate held-out classification denominator. Supplied donor-usage prediction does not assess junction pairing or whole-isoform recovery.'
    p=protocols['botanic1-sae-splice-usage-protocol']
    p['selection']='Predefined two-level tree; choose SAE features and thresholds to maximize balanced accuracy. Added correlation-panel donors do not participate in this fitting.'
    c.field('protocols',p['id'],'selection',bot)
    for r in data['source_reviews']:
        if r['entity_table']=='tasks' and r['entity_id']==t['id']:
            r['limitations']=t['limitations']
            r['evidence_ids_json']=json.dumps(sorted(set(json.loads(r['evidence_ids_json'])+[bot])))
    c.field('tasks',t['id'],'limitations',bot)

    probe=e('completion-botanic-probe','botanic-paper','§4.3.6.2, PDFp.47',
        'Frozen XGBoost probes use fixed task-family/pooling settings. TIS/TTS/conservation allow 1,000 rounds with early stopping after 10 non-improving rounds; region classification allows 100 rounds with patience 3. Other probe families retain the stated fixed settings, with encoder/decoder splicing differences.',
        'https://huggingface.co/spaces/living-models/botanic1-report/resolve/1a1826804938e6320e20f037956b3818b9c40700/botanic1-report-v3.pdf#page=47')
    geneb=e('completion-geneb-selection','src-geneb-spec','harness/run_GENEB.py: fit_eval; benchmark_spec.json: protocol',
        'The harness directly fits LogisticRegression(max_iter=1000,n_jobs=32,random_state=seed) for each of five seeds; it implements no development-set hyperparameter search. Few-shot training samples up to k examples per class from train.',
        'https://github.com/darlednik/GENEB/blob/9642d481e40c0af23995dcd162b779613f789f97/harness/run_GENEB.py#L62-L86',basis='code')
    ntselect=e('completion-ntv3-selection','ntv3-paper','Methods: NTv3 Benchmark; annotation optimization/checkpoint selection; Borzoi comparison',
        'NTv3 Benchmark selects the checkpoint maximizing mean validation Pearson, separately by seed, over ten epochs and twenty validation checks per epoch; validation samples up to 1,000 windows. Native annotation models select highest mean gene-level F1 on validation species. Borzoi comparison uses fold4 for selection and fold3 for final evaluation.',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC13733737/')
    trait=e('completion-traitgym-selection','src-traitgym-mendelian-model','workflow/rules/common.smk, lines520–547; model.smk outer masks',
        'The logistic pipeline imputes missing values and standardizes features within cross-validation, uses class_weight=balanced and seed42, and tunes ten C values log-spaced from 1e-8 to1 with average_precision scoring and chromosome-grouped GroupKFold. The enclosing rule supplies the outer chromosome split.',
        'https://github.com/songlab-cal/TraitGym/blob/4d80fe889415ffc02d45c7cb5446a326288819bd/workflow/rules/common.smk#L520-L547',basis='code')
    c.source('completion-mrna-probe','mRNABench linear-probe implementation',
        'https://github.com/morrislab/mRNABench/blob/778d691ab91c51c03addeb9219229f2ec81d195c/mrna_bench/linear_probe/linear_probe.py',kind='code',version='778d691ab91c51c03addeb9219229f2ec81d195c')
    mrna=e('completion-mrna-selection','completion-mrna-probe','linear_models, lines31–41; run_linear_probe, lines151–163',
        'Classification uses fixed LogisticRegression(max_iter=5000,n_jobs=-1), wrapped in MultiOutputClassifier for multilabel targets. The implementation fits train and reports validation/test metrics; it does not tune the classification penalty on validation. Regression separately uses RidgeCV, with a fixed Ridge fallback.',basis='code')
    legacy=e('completion-genecad-selection','genecad-paper','Model Training and Optimization; Post-Prediction Refinement and Validation',
        'The 2025 GeneCAD paper monitors token/interval F1 on validation windows and explicitly states no early stopping. Optional protein plausibility filtering selects its threshold on validation; no further checkpoint-selection criterion is supplied.')
    gener=e('completion-generator-selection','generator-paper','§2.4; AppendixC.4 and TablesS8–S11',
        'Downstream fine-tuning searches nine learning rates (1e-5 through5e-3) and batch sizes64/128/256/512, with reduce-on-plateau and early-stopping patience5. Paper states tenfold evaluation; released adapters define their own validation split. This does not establish nested hyperparameter tuning.')
    sae=e('completion-botanic-sae-selection','botanic-paper','§4.8.2: finding interpretable features; Eq.10',
        'Genomic-concept features and thresholds are ranked by MCC on validation; the selected feature/threshold is then used for reported annotation diagnostics.',
        'https://huggingface.co/spaces/living-models/botanic1-report/resolve/1a1826804938e6320e20f037956b3818b9c40700/botanic1-report-v3.pdf#page=59')
    # Correct additional selection fields from implementation, rather than
    # treating a missing normalized value as a missing published procedure.
    for p in data['protocols']:
        pid=p['id'];selection=None;eid=None
        if pid in ('traitgym-mendelian-probe','traitgym-complex-probe'):
            selection='Inner chromosome-grouped GroupKFold maximizes average precision over ten C values from 1e-8 to 1; imputation and scaling occur within the pipeline. Outer chromosome masks define final predictions.';eid=trait
        elif pid in ('mrna-rna-loc-fazal-protocol','mrna-mirna-target-protocol'):
            selection='Fixed logistic-regression configuration (max_iter=5000); no classification-penalty search in the released probe. Train fitting and validation/test reporting remain separate.';eid=mrna
        elif pid.startswith('genecad-legacy-'):
            selection='Monitor token/interval F1 on validation windows; no early stopping. Protein-filter threshold uses validation. The source supplies no additional checkpoint-selection rule.';eid=legacy
        elif pid in ('gener-gene_classification-generator-ft','gener-taxonomic_classification-generator-ft','generator-deepstarr-dev-protocol','generator-deepstarr-hk-protocol'):
            selection='Paper grid: learning rates 1e-5,2e-5,5e-5,1e-4,2e-4,5e-4,1e-3,2e-3,5e-3; batches64,128,256,512. Reduce-on-plateau and early-stopping patience5; released validation partitions are recorded separately. A nested tuning split is not specified.';eid=gener
        elif pid in ('botanic1-sae-region-concepts-protocol','botanic1-sae-site-concepts-protocol','botanic1-sae-codon-phase-protocol'):
            selection='Select feature and threshold maximizing MCC on the validation split (§4.8.2); report the corresponding diagnostic on the source-defined evaluation cohort.';eid=sae
        if selection:
            p['selection']=selection;c.field('protocols',pid,'selection',eid)
    for p in data['protocols']:
        if p['selection'] is not None:continue
        if p['source_evidence_id']=='geneb-spec':
            p['selection']='Fixed logistic-regression configuration; five seeds (13,17,42,123,997). The harness has no development-set tuning step.'
            c.field('protocols',p['id'],'selection',geneb)
        elif p['task_id'] in ('botanic1-conservation','botanic1-tis','botanic1-tts','botanic1-cross-donor','botanic1-cross-acceptor'):
            p['selection']='Fixed XGBoost settings by task family and pooling protocol; validation early stopping: patience 3 for region classification, 10 for TIS/TTS/conservation (maximum 100 and 1,000 rounds respectively). See §4.3.6.2 for the remaining family settings.'
            c.field('protocols',p['id'],'selection',probe)
        elif p['source_evidence_id']=='ntv3-final-benchmark-protocol':
            p['selection']='Per-seed checkpoint maximizing mean validation Pearson; up to 1,000 validation windows, twenty checks per epoch, ten epochs, no early stopping.'
            c.field('protocols',p['id'],'selection',ntselect)
        elif p['source_evidence_id']=='ntv3-final-borzoi' and p['adaptation']=='full fine-tune':
            p['selection']='Borzoi fold 4 for model selection; fold 3 for final evaluation.'
            c.field('protocols',p['id'],'selection',ntselect)
        elif p['source_evidence_id']=='ntv3-final-annotation' and p['adaptation']=='released GeneCAD v0.3.0 annotation pipeline':
            p['selection']='Use the released GeneCAD v0.3.0 predictor in this comparison; no additional comparator fitting or checkpoint selection on these test species.'
            c.field('protocols',p['id'],'selection',p['source_evidence_id'])
        elif p['source_evidence_id']=='dnafoundation-personal-expression-code':
            p['selection']='Fivefold cross-validation within the 75% training subjects, optimizing negative mean squared error.'
            c.field('protocols',p['id'],'selection',p['source_evidence_id'])
        elif p['source_evidence_id']=='dnafoundation-variant-code':
            p['selection']='Fourfold GroupKFold tuning within each outer training partition.'
            c.field('protocols',p['id'],'selection',p['source_evidence_id'])

    # A source-null Boolean combined distinct, known interfaces. Preserve these
    # alternatives rather than assert that every model consumes hidden states.
    data['protocol_field_reviews']=[]
    def review(p,field,state,detail,evidence=None):
        c.put('protocol_field_reviews',dict(protocol_id=p['id'],field=field,state=state,
            detail=detail,evidence_id=evidence or p['source_evidence_id']),('protocol_id','field'))
    for p in data['protocols']:
        if p['requires_embeddings'] is not None:continue
        a=p['adaptation']
        if p['id'] in ('ceno-enhancer-design-protocol','ceno-structure-design-protocol'):
            p['requires_embeddings']=False
            c.field('protocols',p['id'],'requires_embeddings',p['source_evidence_id'])
        elif p['source_evidence_id']=='nabench-complete-methods':
            review(p,'requires_embeddings','conflicting',
                'The paper defines hidden-representation features; the released Evo extractor instead saves per-position nucleotide log probabilities. Exported hidden embeddings are required by the paper-defined arm, but are not the released Evo interface. No downstream runner reconciles the scored feature arrays.',
                'nabench-complete-methods')
            c.field('protocols',p['id'],'requires_embeddings','nabench-evo-readout-review')
        elif a in ('supervised training; model-dependent','dataset partition definition; adaptation is model-specific','probe / fine-tune depends on model paper'):
            review(p,'requires_embeddings','model-dependent','This record defines a dataset/partition or common benchmark task. A frozen-embedding probe requires exported representations; an end-to-end fine-tune does not. Model-specific protocols define the actual interface.')
        elif a=='frozen linear probe / source-specific zero-shot variants':
            review(p,'requires_embeddings','model-dependent','Frozen-feature linear probes require representations; direct native model-score variants do not. The source defines both paths, with development-selected calibration where required.')
        elif a=='frozen probe / score combination':
            review(p,'requires_embeddings','model-dependent','Feature sets may use embeddings, evolutionary scores, sequence-to-function scores, or their combinations; embeddings are required only for an embedding feature set.')
        elif a=='counterfactual evaluation of frozen-probe / LoRA sequence-to-activity model':
            review(p,'requires_embeddings','model-dependent','The frozen-probe arm consumes representations. The LoRA sequence-to-activity arm updates the predictor directly and does not require a separate embedding export.')
        elif p['id']=='botanic1-population-constraint-protocol':
            review(p,'requires_embeddings','model-dependent','Likelihood-ratio scoring does not require embeddings. The separately reported reference/alternative embedding dot-product arm does.')
        else:raise ValueError('Unreviewed embedding interface: '+p['id'])

    dataset_modes={'supervised training; model-dependent','dataset partition definition; adaptation is model-specific','probe / fine-tune depends on model paper'}
    # These modes score an already fitted/native model, or define an unfitted
    # diagnostic. "None" is scoped to additional evaluation fitting, not to the
    # historical training of the base model, SAE or sequence-to-function head.
    no_fit_modes={
        'zero-shot','zero-shot representation score','zero-shot model-response analysis','autoregressive generation',
        'zero-shot generation','pretrained generation','inference-time guided generation','zero-shot diagnostic',
        'Supervised pretrained S2F; zero-shot variant scorer','Frozen all-folds Stage-4 model; no cohort-specific backbone fitting',
        'conditional generation','zero-shot existing functional head','zero-shot embedding comparison',
        'Frozen Stage-4 sequence model conditioned on screen scRNA embeddings; no link-label fitting',
        'Supervised S2F model; source-defined variant scoring','zero-shot with length correction',
        'representation diagnostic','inference','zero-shot reconstruction','post-trained chat inference',
        'unfitted diagnostic analysis','native supervised predictors; no diagnostic readout fitting',
        'post-hoc diagnostic','native fine-tuned annotation model','zero-shot likelihood diagnostic',
        'Supervised pretrained S2F; no task-specific fitting',
        'All-folds imputation-split model; screen scRNA pseudobulk is the only retained training data for this reference condition',
        'Supervised pretrained S2F; no TraitGym labels fitted','Pretrained S2F; zero-shot variant scoring'}
    for p in data['protocols']:
        if p['fitted_component'] is not None:continue
        a=p['adaptation']
        if a in dataset_modes:
            review(p,'fitted_component','model-dependent','The dataset/partition definition prescribes no single fitted component. The associated model protocol specifies a probe, adapter or backbone fit.')
        elif a in no_fit_modes:
            p['fitted_component']='No additional component fitted for this evaluation; use the cited pretrained/post-trained model or native score.'
            c.field('protocols',p['id'],'fitted_component',p['source_evidence_id'])
        elif a in ('full fine-tune then generation','family-specific fine-tune + sampling'):
            p['fitted_component']='Autoregressive backbone fine-tuned on the source-defined locus/family corpus before sampling.'
            c.field('protocols',p['id'],'fitted_component',p['source_evidence_id'])
        elif p['id']=='ceno-enhancer-design-protocol':
            p['fitted_component']='Sequence generator: supervised fine-tuning followed by reinforcement learning against the frozen activity oracle.'
        elif p['id']=='ceno-structure-design-protocol':
            p['fitted_component']='No new model weights; source-defined inference-time sequence optimization with frozen predictors.'
        elif p['id']=='deepd-mouse-tf-protocol':
            review(p,'fitted_component','not-reported','Frozen representations and a downstream TF classifier are reported, but the main paper/release does not identify the classifier architecture or its fit settings. The separately linked DC2 methods document returned HTTP 429 on recheck.')
        elif p['id']=='ag2-gtex-lfc-stage1-ablation':
            p['fitted_component']='Stage-1 sequence-to-function model and heads, trained under each source-defined conditioning configuration; no eQTL-cohort readout fitting.'
        else:raise ValueError('Unreviewed fitted component: '+p['id'])

    selection_no_fit=no_fit_modes|{
        'native functional predictor; no benchmark fitting','use supervised annotation predictor; no additional fitted probe',
        'inference-only comparison','zero-shot native RNA attribution','native attribution; unsupervised motif aggregation',
        'zero-shot sequence perturbation','zero-shot native prediction and attribution'}
    for p in data['protocols']:
        if p['selection'] is not None:continue
        a=p['adaptation']
        if a in dataset_modes:
            review(p,'selection','model-dependent','The dataset/split specification does not prescribe model selection. Use the selection rule from the model-specific probe or fine-tuning protocol.')
        elif a in selection_no_fit:
            review(p,'selection','not-applicable','No new downstream predictor is fitted in this evaluation. The score, representation or generation conditions are defined by the cited protocol; this does not assert that the base model was trained without validation.')
        elif p['source_evidence_id']=='nabench-complete-methods':
            review(p,'selection','not-reported','§3.4.4/3.5 defines ridge regression, fivefold random/position splits or ten training labels, but supplies no ridge-penalty selection rule, inner-validation procedure or released fold/run manifest.')
        elif a in ('frozen embedding analysis','representation diagnostic'):
            review(p,'selection','not-applicable','Descriptive projection/embedding analysis; no held-out supervised model-selection step is defined. Projection settings are recorded under fitted component.')
        else:
            # This is a bounded negative about the cited protocol, not a claim
            # that a validation procedure could never exist elsewhere.
            eid=p['source_evidence_id'];locator=ev[eid]['locator']
            review(p,'selection','not-reported',f'The cited {p["name"]} method ({locator}) does not specify a separate validation/checkpoint or hyperparameter selection rule. Its fitting method and partition rule are recorded above.')

    # Complete the wording of source-limited definitions, without filling absent
    # manuscript fields from another model or an assumed standard procedure.
    updates={
        'deepd-h3-example':{'split_rule':'Released H3_train/H3_valid/H3_test CSVs define the partitions. They contain sequence/label rows without chromosome, coordinate or homology-group identifiers; the release does not document their biological grouping.'},
        'deepd-mouse-tf-protocol':{'split_rule':'The main paper and released TF examples provide no paper-specific split manifest or partition rule. The separately linked DC2 methods document returned HTTP 429, including on the 2026-11-27 recheck.'},
        'genosm-gene-class-mlp':{'split_rule':'Tenfold cross-validation is reported. The paper and unchanged released benchmark documentation provide no fold membership or inner validation subdivision.'},
        'genosm-amr-mlp':{'split_rule':'Conflicting source specifications: 8:2 train/test is stated alongside approximately 14,500 train and 1,600 test examples (approximately 9:1). No released cohort manifest selects between them.'},
        'genosm-crc-within':{'split_rule':'Within-cohort tenfold cross-validation is reported. Subject grouping, repeat-sample handling and nested model-selection partitions are not specified in the paper or released documentation.'},
    }
    for id,fields in updates.items():protocols[id].update(fields)
    for id in ('genosm-bgc-binary-mlp','genosm-bgc-types-mlp'):
        protocols[id]['notes']='The benchmark documentation allows truncation or sliding-window aggregation beyond a comparator’s context but does not specify the transformation per checkpoint. Table 9 labels the Genos-m comparator cpt32k; this is not evidence that each BGC was scored with the final 1-Mb checkpoint.'
        protocols[id]['selection']='The paper and released benchmark documentation do not specify the validation-based selection criterion.'
    for p in data['protocols']:
        if (p.get('notes')or'').endswith('record that auxiliary information.'):
            p['notes']=p['notes'].replace('record that auxiliary information.','CADD is therefore an auxiliary source for those converted nucleotide scores.')

    for id in ('aido2-ssu','aido2-lsu','aido2-human-elements'):
        t=c.get('tasks',id)
        t['input_description']='Source-defined rRNA sequences' if id!='aido2-human-elements' else 'Annotated human genomic-element sequences'
        t['limitations']='The technical report gives cohort totals and UMAP settings but does not identify the sequence-source accession list, length distribution, filtering, duplicate handling or class balance. It reports a visualization, not held-out classification accuracy.'
    for id in ('cross_species_leaf_on_off_translation','cross_species_leaf_absolute_translation'):
        t=c.get('tasks','plantcad2-ft-'+id)
        t['input_description']='500-bp upstream DNA. The paper does not identify whether the anchor is the transcript start or translation start; released rows have gene IDs and sequence but no anchor coordinates.'
        for v in data['variants']:
            if v['task_id']==t['id']:v['input_length']='500 bp upstream DNA; anchor coordinates are not supplied'
    name_updates={
        'evo-viral-doud-np':'Influenza nucleoprotein fitness (Doud)',
        'evo-viral-doud-pb1':'Influenza PB1 fitness (Doud source attribution)',
        'evo-viral-haddox-env':'HIV-1 envelope fitness (Haddox panel)',
        'evo-viral-starr-rbd':'SARS-CoV-2 RBD DMS (Starr)',
    }
    for id,name in name_updates.items():c.get('tasks',id)['name']=name
    # A discarded, unused output category was still offered as a filter option.
    assert not any(r['category_id']=='output-unresolved' for r in data['task_outputs'])
    assert not any(r['category_id']=='output-unresolved' for r in data['task_categories'])
    data['categories']=[r for r in data['categories'] if r['id']!='output-unresolved']
    # Previously missing editorial classifications, with the original task
    # evidence retained. BUSCO remains an aggregate completeness diagnostic;
    # it is not reassigned to dense labeling or exact structure recovery.
    for id,category in [('evo-exon-intron','functional-prediction'),('generator2-umap','embedding-analysis'),
                        ('botanic1-regions','functional-prediction'),('botanic1-conservation','evolutionary-inference'),
                        ('botanic1-tis','functional-prediction'),('botanic1-tts','functional-prediction')]:
        t=c.get('tasks',id);c.category(id,category,t['evidence_id'],'The cited task predicts a supplied functional label or evaluates the specified representation/constraint diagnostic. This assignment does not imply dense annotation.')
    for id in ('evo-sae-prophage','evo-sae-crispr-scrambling','evo-sae-coding-mutation-response','evo-sae-tf-motif-recall','evo-sae-latent-ablation'):
        t=c.get('tasks',id);c.category(id,'model-development',t['evidence_id'],'Feature interpretation and intervention diagnose the internal representation and loss response; no application-specific prospective validation is implied.')
    for category in ('ncrna','trna','rrna'):
        c.category('dgeb-ecoli_rna_clustering',category,c.get('tasks','dgeb-ecoli_rna_clustering')['evidence_id'],'The released task definition explicitly clusters E.coli sRNA, tRNA and rRNA segments.')
    for id in ('genosm-crc','genosm-lowdepth-stability','genosm-lowdepth-mixture','genosm-lowdepth-geography','genosm-lowdepth-enterotype'):
        c.category(id,'genome',c.get('tasks',id)['evidence_id'],'Whole microbial genomes or randomly sampled metagenomic reads are used without a region-specific selection criterion; human is the sample host, not sequence origin.')
    # Natural sequence origin and synthetic selection are not interchangeable.
    # These upstream primary papers identify the previously unplaced assays.
    origins=[
        ('completion-domingo','Pairwise and higher order genetic interactions during the evolution of a tRNA','https://pmc.ncbi.nlm.nih.gov/articles/PMC6193533/',
         'Methods1; main experiment','The reference is S.cerevisiae HSX1/Arg-CCU tRNA; combinatorial variants incorporate substitutions observed in close budding-yeast orthologs and are assayed in S.cerevisiae.',
         ['rnagym-domingo-2018-trna','evo-ncrna-domingo'],'yeast'),
        ('completion-guy','Identification of determinants of tRNA function and susceptibility to rapid tRNA decay','https://pmc.ncbi.nlm.nih.gov/articles/PMC4117946/',
         'Abstract; SUP4oc reporter design','The assayed reference is the S.cerevisiae SUP4oc suppressor tRNA, with variant activity measured in yeast.',
         ['rnagym-guy-2014-trna','evo-ncrna-guy'],'yeast'),
        ('completion-julien','The complete local genotype–phenotype landscape for alternative splicing of a human exon','https://www.nature.com/articles/ncomms11558',
         'Abstract; Results: mutagenesis library','The target is human FAS/CD95 exon6. The benchmark sequence is the mutated exon, not a whole transcript or chromosome annotation.',
         ['rnagym-julien-2016-mrna'],'human'),
        ('completion-ke','Saturation mutagenesis reveals manifold determinants of exon definition','https://genome.cshlp.org/content/28/1/11',
         'Results: Saturation mutagenesis strategy','The target is the human WT1 exon5 in a minigene with hamster dhfr flanks. RNAGym’s target sequence is the 51-nt exon, so the sequence-origin assignment applies to that exon rather than every minigene component.',
         ['rnagym-ke-2017-mrna'],'human'),
        ('completion-janzen','Emergent properties as by-products of prebiotic evolution of aminoacylation ribozymes','https://www.nature.com/articles/s41467-022-31387-0',
         'Introduction; aminoacylation substrates and mutant-pool design','Five ribozymes from three motifs were found by in-vitro selection from sequence space and mutagenized; they are synthetic constructs, not a species-held-out natural panel.',
         ['rnagym-janzen-2022-fam1a1-ribozyme','rnagym-janzen-2022-fam1b1-ribozyme','rnagym-janzen-2022-fam21-ribozyme','rnagym-janzen-2022-fam22-ribozyme','rnagym-janzen-2022-fam31-ribozyme'],'synthetic')]
    for sid,title,url,locator,statement,ids,pop in origins:
        c.source(sid,title,url);eid=e(sid,sid,locator,statement)
        for tid in ids:
            data['coverage_mappings']=[m for m in data['coverage_mappings'] if not(m['task_id']==tid and m['population_id'] is None)]
            c.population(tid,pop,eid,statement)
            c.field('tasks',tid,'sequence_origin',eid)
            r=next(r for r in data['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==tid)
            r['evidence_ids_json']=json.dumps(sorted(set(json.loads(r['evidence_ids_json'])+[eid])))
    for r in data['coverage_rows']:
        if r['row_key']=='unknown':
            m=json.loads(r['metadata_json'])
            for f in ('label','cladeLabel','lineageLabel','displayLabel'):m[f]='Taxa not specified by source'
            m['displayLineage']='The cited cohort does not supply a taxonomic assignment'
            r['metadata_json']=json.dumps(m,ensure_ascii=False)
        else:
            m=json.loads(r['metadata_json'])
            for f in ('label','displayLabel','cladeLabel','lineageLabel'):
                if isinstance(m.get(f),str):m[f]=re.sub('unresolved','not specified',m[f],flags=re.I)
            r['metadata_json']=json.dumps(m,ensure_ascii=False)
        m=json.loads(r['metadata_json'])
        if isinstance(m.get('note'),str):m['note']=re.sub(r'^\d+ unique mapped task records\.\s*','',m['note'])
        r['metadata_json']=json.dumps(m,ensure_ascii=False)
    for m in data['coverage_mappings']:
        if m['population_id'] is None:
            meta=json.loads(m['metadata_json']);meta['name']='Taxa not specified by source'
            m['metadata_json']=json.dumps(meta,ensure_ascii=False)
    # Do not leave an older broad limitation contradicting the completed exact
    # CDS comparison in Splits. Approximate homology remains a different check.
    p=protocols['bacbench-essential-protocol']
    p['split_rule']=p['split_rule'].replace('Genus sets inspected are pairwise disjoint; exact sequence homology is not established.',
        'Genus sets are pairwise disjoint. The complete released CDS comparison in Splits finds four exact train/validation strings and none shared with test. Approximate homology and whole-genome alignment were not measured.')
    c.field('protocols',p['id'],'split_rule','split-evidence-c4b7ab675d3330da')
    for v in data['variants']:
        if v['id']=='aido2-clinvar-snv-balanced':
            v['notes']='The report does not give the balancing algorithm, retained variant IDs or final balanced count; the count is not inferred from the pathogenic total.'
        if v['id'] in ('genosm-bgc-binary-context','genosm-bgc-types-context'):
            v['input_length']='8 kb–1 Mb+ source regions; per-comparator truncation/windowing settings are not supplied'
        if v['id']=='plantcad2-structural_variant_effect_prediction-phastCons':
            v['notes']='FigureS6 reports a phastCons-based target. The released SV table does not identify a separate matching phastCons label/cohort; it is not counted as another independently released dataset.'
    for id in ('generator-family-p450','generator-family-histone'):
        c.get('tasks',id)['limitations']='The paper reports family-specific fine-tuning followed by sampling without an example-specific biological prompt. The official release contains no family-generation initialization implementation. The generation classification therefore follows the paper protocol. Deduplication against training is not unseen-family testing; sequence/protein-structure diagnostics do not measure new enzyme activity or organismal function.'
    c.get('models','genosm')['notes']='Paper/card vocabulary128 differs from released configuration256 and tokenizer17 entries. Table9 labels its benchmark checkpoint cpt32k; neither source supplies a mapping from that checkpoint to the final 1M-context weights or per-comparator BGC window settings.'
    for t in data['tasks']:
        if t['id'].startswith('genosm-lowdepth-'):
            t['limitations']='The analyses include in-house samples. The release supplies no complete participant/cohort manifest linking them to pretraining or to other panels. These are microbial-community sample analyses, not human-genome prediction.'
    for f in data['findings']:
        if f['id'] in ('finding-095','finding-096','finding-097','finding-098','finding-101'):
            f['description']='The DeepD main paper, DC1 captions and pinned public examples do not supply the molecular assay IDs or paper-specific split manifests for this panel. Its separately linked DC2 methods document returned HTTP429 on recheck. The numbered source configurations are retained without invented assay identities.'
        if f['id']=='finding-102':
            f['description']='The GPN-Star supplement specifies this panel protocol but supplies no assay-ID/retained-variant manifest that maps it to the similarly named 31-assay GPN-MSA panel. They remain distinct source cohorts; matching assay names or counts would not establish identity.'
    details={
        'genosm-lowdepth-stability':'UMAP visualization and embedding consistency; the report does not name a numerical consistency statistic.',
        'genosm-lowdepth-geography':'AUROC for geographic-origin classification; the report does not specify multiclass averaging.',
        'genosm-lowdepth-enterotype':'Agreement with full-depth enterotypes; the report specifies cosine K-means versus PAM/Jensen–Shannon but not the cluster-label matching rule.'}
    for id,s in details.items():
        c.get('tasks',id)['output_description']=s
        for p in data['protocols']:
            if p['task_id']==id:p['notes']=s

    # A finite numerical and allele/coordinate match resolves the target that
    # the benchmark paper/filename did not identify. Do not retain the old
    # phenotype ambiguity alongside this measured adjudication.
    findlay=json.loads((ROOT/'data/nabench-findlay-target-review.json').read_text())
    assert findlay['matched_rows']==findlay['transcript_strand_allele_matches']==287
    c.source('completion-findlay-table','Findlay et al.2018 Supplementary Table1: BRCA1 SGE scores',
        findlay['source_url'],kind='dataset',notes='Sheet1 header row3; 3,893 source variants. SHA-256 '+findlay['source_sha256'])
    c.source('completion-findlay-comparison','NABench Gregory_2018_mRNA target adjudication',
        'https://github.com/eric-czech/marin-glm/blob/main/data/nabench-findlay-target-review.json',
        kind='inspection-report',path='data/nabench-findlay-target-review.json')
    fe=e('completion-findlay-target','completion-findlay-comparison','All287 released rows; unique scores, coordinate offset, reference/alternate alleles; source columnAI',
        'All287 NABench scores match uniquely to d11/lib.loess.r1 in Findlay Supplementary Table1, maximum absolute error8.9e-16. Every row also matches transcript-strand alleles and one genomic coordinate offset. All are experimentX20. No other numeric column matches all287; neither mean.rna.score nor function.score.mean does. This data comparison identifies the released target; the NABench paper/filename did not name the column.',basis='data')
    e('completion-findlay-table-definition','completion-findlay-table','Sheet1 row3, columnAI; Supplementary Informationp.5 table legend',
        'Source columns distinguish day11 (d11), library (lib), LOESS positional-bias correction and biological replicate1 (r1). Mean RNA and mean function scores are separate columns. Data derive from HAP1-Lig4KO selection experiments.',basis='data')
    tid='nabench-findlay-readout';t=c.get('tasks',tid)
    t.update(name='NABench BRCA1 exon20: day-11 selection score',
        target='Findlay2018 d11/lib.loess.r1: replicate-1 LOESS-adjusted day-11/library genomic-DNA selection score',
        description='Predict the source experimentX20 BRCA1 selection score from the released 100-character sequence. Target identity is established by matching all287 scores, alleles and genomic-coordinate offsets to the original source table.',
        label_basis='Original BRCA1 saturation-genome-editing selection score, replicate1; matched to source table columnAI',
        limitations='NABench does not release evaluation-fold or ten-label subset membership, ridge-selection settings or a complete downstream runner. Supplied sequences include an X separator and coding/intronic/splice-region variants; this is not a CDS-only or RNA-abundance task.',
        output_description='One replicate-1 day-11 genomic-DNA selection score per supplied variant sequence')
    data['source_limits']=[r for r in data['source_limits'] if not(r['entity_table']=='tasks' and r['entity_id']==tid and r['field']=='target')]
    data['task_categories']=[r for r in data['task_categories'] if not(r['task_id']==tid and r['category_id']=='rna-engineering')]
    for cat,why in [('variant-interpretation','Human BRCA1 functional selection across coding and splice-related variants.'),
                    ('variant-effects','A mutant sequence is scored against an experimentally measured variant effect.'),
                    ('intron','85 source variants have the Intronic consequence label.'),
                    ('cds','149 variants are explicitly missense, synonymous or nonsense; other positional labels can also include coding positions.')]:
        c.category(tid,cat,fe,why,'subset' if cat in ('intron','cds') else 'target')
    c.put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope='mixed',
        rationale='The source-matched cohort contains coding, intronic and splice-related variants, not an exclusively CDS-targeted cohort.',evidence_id=fe))
    o=next(r for r in data['task_outputs'] if r['task_id']==tid)
    o.update(status='supported',evidence_id=fe,scoring_unit='BRCA1 exon20-region SNV / supplied sequence',
        rationale='All released target values map to one defined original-source column; each row is a scalar variant score.',limitations=t['limitations'])
    for v in data['variants']:
        if v['task_id']==tid:
            v.update(context='BRCA1 experimentX20; 287 source-matched variants',notes='Released filename Gregory_2018_mRNA is retained as the artifact name; its scalar values are genomic-DNA selection scores, not mean RNA scores.',evidence_id=fe)
    for field in ('target','label_basis','limitations','output_description','application'):
        c.field('tasks',tid,field,fe)
    c.category(tid,'output-isolated',fe,'The matched source column supplies one scalar variant score.','measured')
    c.resource('completion-findlay-original-table','completion-findlay-table','Original BRCA1 SGE score table','dataset','other',
        findlay['source_url'],'completion-findlay-table-definition',notes='Sheet1, columnAI (d11/lib.loess.r1); NABench matches experimentX20. Other source columns are different targets.')
    c.task_resource(tid,'completion-findlay-original-table',fe,relation='upstream-data',note='All287 NABench targets, alleles and coordinate offsets match this source table; row IDs are retained in the comparison report.')
    for label,n in findlay['consequences'].items():
        c.count(tid,n,'source-annotated variants',fe,split='consequence: '+label,
            qualifier='Mutually exclusive source-table consequence labels within the287-row cohort; not additional independent examples.',method='measured')
    r=next(r for r in data['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==tid)
    r['limitations']=t['limitations'];r['evidence_ids_json']=json.dumps(sorted(set(json.loads(r['evidence_ids_json'])+[fe])))
    c.put('findings',dict(id='completion-findlay-target-finding',task_id=tid,evaluation_id='nabench',severity='discrepancy',
        description='The released Gregory_2018_mRNA filename does not identify the scored phenotype. Direct comparison maps all287 values to the original BRCA1 exon20-region replicate-1 day-11/library genomic-DNA selection column, with matching alleles and coordinates. It is not the original mean RNA or mean function score.',evidence_id=fe))

    properties={r['id']:r for r in data['model_properties']}
    properties['aido2-tokenizer']['status']='not disclosed in technical report'
    properties['aido2-tokenizer']['value']='The report does not disclose sequence segmentation or vocabulary size. The official GenBio model index and an exact-name HF search expose no AIDO.DNA2 checkpoint/configuration in the inspected responses.'
    properties['aido2-tokenizer']['notes']='The predecessor AIDO.DNA tokenizer and the masked-recovery objective do not identify AIDO.DNA2 tokenization.'
    properties['aido2-capacity']['value']='Small 235M; medium 470M; large 1B total sparse parameters. The report does not disclose active parameters per token, layer counts or hidden widths.'
    properties['aido2-tokens']['value']='The large-8K-4T diagnostic checkpoint consumed 4T tokens. The report does not give token totals for the other checkpoint variants.'
    properties['genosm-curriculum']['value']='8K→32K→128K→1M bp curriculum with stage-specific sampling. Exact token budgets per stage are not reported.'
    properties['genosm-tokenizer']['notes']='The release lists 17 biological/special token entries. Report/card vocabulary size 128 and inference configuration 256 are distinct source values; neither source explains that difference.'

    # Keep aggregate participation at collection level. There is no justification
    # for propagating the NABench model list to all 162 assays and all arms.
    nab=e('completion-nabench-models','nabench-release-readme','Baseline Models table; pinned full repository tree',
        'NABench lists Evo-1, Evo2-7B(-base), GENERator, and an AIDO predecessor among its baseline models. It does not release a complete model×assay×arm execution manifest or downstream fitting runner. The AIDO predecessor is not AIDO.DNA2.',
        'https://github.com/mrzzmrzz/NABench/blob/99c8681ec1eab706e10ff90a5c329dcf184cc1d1/README.md#baseline-models',basis='documentation')
    for model in ('evo1','evo2','generator'):
        c.put('model_collection_evaluations',dict(id='nabench-'+model,model_id=model,
            evaluation_id='nabench',paper_id='na',provenance='external-evaluation',
            scope='Listed benchmark participant. Aggregate participation does not establish execution on every linked assay, protocol arm or model checkpoint.',evidence_id=nab))
    e('completion-evo2-inventory','evo-supp','Original Evo 2 manuscript and Supplementary Methods A.3–A.10; catalogue evo-original collection',
        'The finite original-paper inventory is represented by 83 dataset–target/panel records. Original-paper model associations match that inventory exactly. Other catalogue records are not listed in this inventory; later independent benchmark use is a separate, source-scoped association.')
    c.field('evaluations','evo-original','model_usage_inventory','completion-evo2-inventory')
    c.field('models','evo2','original_paper_inventory','completion-evo2-inventory')

    # Small, identified source rechecks: preserve response status and hashes, not
    # copies of model weights or benchmark payloads.
    receipts=ROOT/'data/completion-source-checks.json'
    if receipts.is_file():
        c.source('completion-source-checks','Primary release and access rechecks, 27 November 2026',
            'https://github.com/eric-czech/marin-glm/blob/main/data/completion-source-checks.json',
            kind='audit-report',path='data/completion-source-checks.json')
        e('completion-access-review','completion-source-checks','Per-URL status, revision, SHA-256 and inspection scope',
            'DeepD DC2, Cerberus/LOAM XML and AlphaGenome2 supplements returned429; Carbon dataset APIs returned401. BaseSpace redirects to Illumina login. Public Synapse entity metadata succeeds, but tested task5 version2 file-handle endpoints return403 anonymously. Five DOI-specific Dataverse requests return403. Official GenBio model index/search expose no AIDO.DNA2 checkpoint in the inspected responses; model repositories retain their inspected revisions. Cerberus release documentation says processed training data are pending.',basis='documentation')
        c.field('model_properties','aido2-tokenizer','availability','completion-access-review')
        for l in data['source_limits']:
            if l['reason']=='not-retrieved' and any(w in l['detail'].lower() for w in ('http 429','returned 429','rate-limit','rate limit')):
                l['reason']='access-restricted'
                l['detail']+=' The identified publisher endpoint again returned HTTP 429 on 2026-11-27; no missing field is inferred from that response.'
                # ID remains stable; reason is a field rather than an ID parser.
                c.field(l['entity_table'],l['entity_id'],'availability','completion-access-review')
        for l in data['source_limits']:
            if l['reason']!='not-retrieved':continue
            detail=l['detail']
            if 'DC2 Method Details' in detail:
                l['reason']='access-restricted'
                l['detail']='The identified DeepD DC2 methods-document endpoint again returned HTTP429 on 2026-11-27. The main paper, DC1 figures/captions and complete pinned releases were inspected; their omissions are not asserted to be omissions from inaccessible DC2.'
            elif 'Dataverse endpoint' in detail:
                l['reason']='access-restricted'
                l['detail']='All five DOI-specific Dataverse API requests returned HTTP403 on recheck. The exact deposits, task definitions and pinned loaders are identified. Tensor files were not inspected, and counts remain explicitly source-reported.'
            elif 'Synapse source' in detail:
                l['reason']='access-restricted'
                l['detail']='Synapse entity metadata is public. File-handle requests for the two task5 QTL inputs (syn60756043/version2 and syn60756039/version2) return403: anonymous users have READ-only access. Scored cohort files were not downloaded; source counts and code filters are recorded without an independent scored-row count.'
            elif 'BaseSpace share' in detail:
                l['reason']='access-restricted'
                l['detail']='A browser visit to the original BaseSpace share5u6ThOblecrh redirects to Illumina login. No original filtered benchmark file inventory or payload is available anonymously at that share. The paper protocol and separately released training annotations remain distinct sources.'
            elif 'API returned 401' in detail:
                l['reason']='access-restricted'
                l['detail']=detail+' The public dataset API again returned401 on recheck; no authenticated access was attempted.'
            elif 'Multi-hundred-MB' in detail or 'above 80MB' in detail or 'multi-gigabyte' in detail or 'large external experimental master' in detail:
                l['reason']='size-excluded'
            elif 'Separate Supplementary Table' in detail or 'separate study/condition tables' in detail or 'separate study/condition' in detail:
                l['reason']='access-restricted'
                l['detail']=detail+' The AlphaGenome2 publisher supplementary-material landing returned429 on recheck; the official author report, blog and public release were inspected without obtaining these separate tables.'
            elif 'article/full text/PDF/JATS' in detail or 'primary bioRxiv' in detail:
                l['reason']='access-restricted'
                l['detail']=detail+' The identified primary full-text endpoint again returned429; metadata, available primary descriptions and pinned releases were inspected.'
            if l['reason']!='not-retrieved':c.field(l['entity_table'],l['entity_id'],'availability','completion-access-review')
        # Re-running models on multi-species raw signals was never a catalogue
        # field. Retain that boundary in review scope, not as seven pending items.
        raw=[l for l in data['source_limits'] if l['field']=='raw-track-signal-recomputation']
        for l in raw:
            r=next(r for r in data['source_reviews'] if r['entity_table']==l['entity_table'] and r['entity_id']==l['entity_id'])
            sentence='All C.1/C.5 track identities and source results were inspected; model correlations were not independently rerun from raw signal tensors.'
            if sentence not in r['scope']:r['scope']+=' '+sentence
        data['source_limits']=[l for l in data['source_limits'] if l['field']!='raw-track-signal-recomputation']
        for r in data['data_resources']:
            if r['id'].startswith('final-dnalong-data-'):
                r['availability']='restricted'
                r['notes']='The exact DOI is linked by the pinned primary repository. Its DOI-specific Dataverse API returned403 in this environment on recheck. Paper definitions/loaders are inspected; the tensor payload is not independently scanned.'
            elif r['id']=='final-structure-spliceai-original-data-resource':
                r['availability']='restricted'
                r['notes']='The original BaseSpace share redirects to Illumina login in a browser. Its filtered benchmark file inventory and rows are not available anonymously; paper-defined protocols and public training annotations are separate sources.'
            elif r['id'] in ('carbonx-dnaintelligence-resource','carbon-final-brca2-data'):
                r['availability']='restricted'
                r['notes']='The official public dataset API returned401 on recheck. This records failed anonymous access without inferring whether the repository is private, gated, deleted or otherwise unavailable.'
            elif r['id']=='evo1-data-s1-resource':
                r['availability']='restricted'
                r['notes']='The exact PMC DataS1 ZIP link returns an HTML browser challenge rather than ZIP bytes (HTTP200,text/html), including on recheck. The primary article identifies the archive; its contents are not asserted to have been inspected.'
            elif r['id']=='final-mrna-rna-loc-fazal-upstream-resource':
                r['availability']='public'
                r['notes']='The original APEX-seq spreadsheet returns200 with Excel content and ZIP signature on a bounded read (reported599,366bytes). This verifies raw-resource availability, not a redistributed processed mRNABench cohort or its partitions.'
            elif r['id']=='final-mrna-mirna-target-upstream-resource':
                r['availability']='public'
                r['notes']='The original MirTarClash CSV returns200 with a CSV gene-ID header on a bounded read (reported10,030,260bytes). No full-file or processed benchmark count is inferred; mRNABench does not redistribute its processed target cohort.'
        c.source('completion-dart-synapse','DART-Eval Synapse project and file metadata',
            'https://www.synapse.org/Synapse:syn59522070',kind='dataset-catalogue',notes='Entity metadata retrieved; anonymous version2 file-handle requests for both task5 inputs return403. Receipts are retained in completion-source-checks.json.')
        dart=e('completion-dart-synapse-access','completion-dart-synapse','Pinned DART README data links; current entity/version metadata; task5 file-handle responses',
            'The primary repository links the DART-Eval Synapse project, including raw and processed inputs. Current task5 variant files are version2; anonymous entity metadata succeeds and file-handle access returns403. This access check does not establish identity of current file contents with historical scored cohorts.',basis='documentation')
        c.resource('completion-dart-synapse-project','completion-dart-synapse','DART-Eval data on Synapse','dataset','other',
            'https://www.synapse.org/Synapse:syn59522070',dart,availability='restricted',
            notes='Project metadata is public; tested file access requires more than anonymous READ permission. No claim that all project files were downloaded.')
        c.collection_resource('dart','completion-dart-synapse-project',dart,note='Official raw/processed data project, linked by the pinned DART README.')
        for row in data['evaluation_tasks']:
            if row['evaluation_id']=='dart':c.task_resource(row['task_id'],'completion-dart-synapse-project',dart,note='Whole project; task5 input versions and access responses are documented separately from historical paper cohorts.')

    # Complete-pool identity, rather than matching task names, supports these
    # two additional consolidations. Partition membership is NOT equated.
    from task_identity_review import IdentityReview
    identity=json.loads((ROOT/'data/nt-gue-identity-review.json').read_text())
    c.source('completion-nt-gue-comparison','Original NT / GUE H3 and H4 complete-pool comparison',
        'https://github.com/eric-czech/marin-glm/blob/main/data/nt-gue-identity-review.json',
        kind='inspection-report',path='data/nt-gue-identity-review.json')
    merger=IdentityReview(data)
    for mark in ('H3','H4'):
        facts=identity['comparisons'][mark];assert facts['identical_multisets']
        assert facts['nt_unique_sequences']==facts['gue_unique_sequences']==facts['nt_rows']
        old='gue-'+mark;new='nt-original-'+mark
        eid=e('completion-nt-gue-'+mark,'completion-nt-gue-comparison',
            mark+': all native train/dev/test rows; SHA-256 verified against earlier complete-file inspections',
            f'Original NT and GUE {mark} have exactly the same complete sequence–label multiset ({facts["nt_rows"]:,} rows), but different partitions. The report retains every NT×GUE partition intersection. This establishes dataset–target identity, not an identical train/test procedure.',basis='data')
        for tid in (old,new):
            for table in ('counts','evaluation_tasks'):
                for row in data[table]:
                    if row.get('task_id')==tid and row.get('variant_id') is None:
                        row['variant_id']=tid+'-native-release'
        merger.merge(old,new,eid,'gue','Identical complete native sequence–label pools, with different source-specific partitions. NT and GUE protocols and release variants are preserved.')
        for r in data['task_redirects']:
            if r.get('replacement_task_id')==old:r['replacement_task_id']=new
        t=c.get('tasks',new)
        t.update(name='Yeast '+mark+' histone annotation',dataset_name='Yeast histone annotation / NT '+mark+' / GUE emp_'+mark,
            description='Binary yeast '+mark+' histone annotation. Complete original NT and GUE sequence–label pools match exactly, while train/dev/test assignments differ. GENEB and other reuse protocols retain their own release variants.',
            limitations='The complete native pools are identical, but repartitioned; a model trained on one release can have seen test rows from the other. Genomic coordinates and a homology-group manifest are not included. Source-specific counts, evaluation heads and partitions are retained separately.')
        r=next(r for r in data['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==new)
        r['limitations']=t['limitations']
        for f in ('dataset_identity','description','limitations'):c.field('tasks',new,f,eid)
        c.put('findings',dict(id='completion-nt-gue-'+mark+'-partitions',task_id=new,evaluation_id='gue',severity='overlap',
            description=f'NT and GUE {mark} contain the same {facts["nt_rows"]:,} sequence–label pairs with different partition assignments. These are one dataset–target with different protocols. The cross-release partition table quantifies exposure; this is not evidence of within-release train/test overlap.',evidence_id=eid))
        aid='split-nt-gue-'+mark.lower()
        c.put('split_audits',dict(id=aid,title='Yeast '+mark+': NT / GUE cross-release partition exposure',
            release_name='Original NT / GUE',evaluation_id='gue',status='measured',finding='overlap',
            scope='Complete original NT train/test and GUE train/dev/test files; identical full pools, different assignments.',
            method='Uppercase sequence–label multiset comparison with source-file SHA-256 verification. Each native partition has unique sequences; full native NT train/test pools are disjoint, so the equivalent complete GUE pool is unique as well.',
            conclusion='The releases reuse exactly the same complete dataset. Cross-release train/test exposure is substantial; within-release overlap is a separate question. No claim is made that a published model was fitted on one release and tested on the other.',
            limitations='No approximate homology or pretraining comparison. These measurements concern explicit labeled benchmark rows and cannot establish a model-specific historical fitting cohort.',
            checked=DATE,evidence_id=eid,sort_order=15 if mark=='H3' else 16))
        for prefix,variant in [('NT',new+'-native-release'),('GUE',old+'-native-release')]:
            c.put('split_audit_tasks',dict(id=aid+'-'+prefix, audit_id=aid,task_id=new,protocol_id=None,
                variant_id=variant,note=prefix+' native partitions; no model-specific cohort is inferred.',evidence_id=eid))
        part_ids={}
        for file in identity['files']:
            if not(file['file'].startswith(mark+'/') or '/emp_'+mark+'/' in file['file']):continue
            prefix='NT' if file['repo'].startswith('InstaDeepAI/') else 'GUE'
            assert file['unique_sequences']==file['rows']
            split=file['file'].split('/')[-1].split('.')[0];name=prefix+' '+split
            pid=aid+'-'+prefix.lower()+'-'+split;part_ids[(prefix,split)]=pid
            c.put('split_partitions',dict(id=pid,audit_id=aid,name=name,row_count=file['rows'],unique_sequences=file['unique_sequences'],
                row_unit='sequence rows',detail='Native '+prefix+' '+split+' partition, before source-specific probe/fine-tuning changes.',evidence_id=eid))
            c.put('split_audit_files',dict(id=pid+'-file',audit_id=aid,partition_id=pid,url=file['url'],
                revision=file['revision'],sha256=file['sha256'],bytes=file['bytes'],row_count=file['rows'],
                scope='Complete file streamed and checked against its previously recorded hash; no raw copy retained.',evidence_id=eid))
        for row in facts['partition_pairs']:
            left=part_ids[('NT',row['nt_partition'])];right=part_ids[('GUE',row['gue_partition'])];n=row['shared_sequence_label_rows']
            c.put('split_comparisons',dict(id=left+'--'+right,audit_id=aid,left_partition_id=left,right_partition_id=right,
                overlap_type='exact-sequence',shared_count=n,unit='unique sequences with matching labels',left_affected=n,right_affected=n,
                note='Cross-release comparison. Full pools are identical and sequences unique; this count does not assert overlap within either release.',evidence_id=eid))
        # Model-paper provenance does not establish its processed cohort equals
        # the upstream native split, even after the upstream pools are equated.
        for p in data['protocols']:
            if p['task_id']!=new:continue
            if p['id'].startswith('geneb-instadeepai-'):
                p['variant_id']='geneb-instadeepai-nucleotide-transformer-downstream-tasks-'+mark.lower()+'-release'
            elif p['id'].startswith('deepd-gue-') or p['id']=='deepd-h3-example':
                demo=p['id']=='deepd-h3-example';vid=p['id']+'-source-cohort'
                c.put('variants',dict(id=vid,task_id=new,name='DeepD '+mark+(' released MLP example' if demo else ' reported paper cohort'),
                    dataset_revision='b1b888e2482a06a51b6bf03fa5091f40b9b57e96' if demo else None,
                    context='Pinned released demonstration partitions' if demo else 'Source reports this target but supplies no paper-specific cohort or fold manifest.',
                    input_length='Source-defined yeast sequence windows',target_count=2,target_unit='classes',
                    notes='The native NT/GUE pool comparison does not assert identity of this model-specific processed cohort.',evidence_id=p['source_evidence_id']))
                p['variant_id']=vid

    # Preserve true source contradictions; eliminate old instructions to the
    # catalogue author. These are explicit source dispositions, not TODOs.
    for f in data['findings']:
        if f['id']=='finding-034':
            f['description']='Genos-m Table 9 names checkpoint cpt32k and also gives 1M maximum context. Neither the paper nor released benchmark documentation connects that checkpoint to the final weights or supplies per-model BGC truncation/windowing settings. The reported 1M inference capability does not specify this benchmark protocol.'
        if f['id'] in ('finding-042','finding-044'):
            f['description']='Translation train and validation files both contain Arabidopsis chromosomes 1–5; test contains maize chromosomes 1–10. This is species-transfer testing with validation on shared chromosomes. No gene-level validation-selection rule is supplied by the paper or released preparation code.'
    for s in data['source_reviews']:
        if s['entity_table']=='protocols':
            p=protocols[s['entity_id']]
            ids=set(json.loads(s['evidence_ids_json']))
            ids.update(r['evidence_id'] for r in data['protocol_field_reviews'] if r['protocol_id']==p['id'])
            ids.update(r['evidence_id'] for r in data['field_evidence'] if r['entity_table']=='protocols' and r['entity_id']==p['id'])
            s['evidence_ids_json']=json.dumps(sorted(ids))
    report=dict(reviewed=DATE,scope='All indexed protocols and remaining undecided UI states',
        initial_nulls=baseline,
        resolved_source_fields={f:baseline[f]-sum(p[f] is None for p in data['protocols']) for f in baseline},
        interpretations=dict(collections.Counter(r['state'] for r in data['protocol_field_reviews'])),
        removed_unsupported_variants=['plantcad2-ft-cross_species_acr_train_on_arabidopsis-context-'+str(n) for n in (1600,2600,3600,4600)],
        original_evo2_inventory=83,
        consolidated_task_ids={'gue-H3':'nt-original-H3','gue-H4':'nt-original-H4'},
        field_reviews=data['protocol_field_reviews'])
    (ROOT/'data/completion-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
