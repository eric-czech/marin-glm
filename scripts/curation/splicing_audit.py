"""Reconcile the November 2026 SpliceAI source audit into the authoring tables.

Run explicitly, before output_audit.py. Routine offline builds do not fetch or
depend on the ignored source cache. Existing dataset × target records are reused.
"""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DATE = '2026-11-27'
PDF1 = 'https://www.scn2a.org/pdf/ARTICLE%20PAP_Splicing_Cell_2019.pdf'
PDF2 = 'https://assets.illumina.com/content/dam/illumina-marketing/images/genomics-research/articles/spliceai2/SpliceAI2.pdf'
REV1 = '03f42437aaf56dc5dfd822c4ccee5aec1a705079'
REV2 = '1dcd2a1882a8223095e7529982ae70bcb658340a'


def populate(d):
    def put(table, row, keys=('id',)):
        old = next((r for r in d[table] if all(r[k] == row[k] for k in keys)), None)
        if old is None:
            d[table].append(row)
        else:
            old.update(row)
        return row.get('id')

    def source(id, title, url, path=None, version=None, kind='paper', notes=None):
        f = ROOT / path if path else None
        return put('sources', dict(id=id, title=title, kind=kind, url=url, version=version,
                   retrieved=DATE, sha256=hashlib.sha256(f.read_bytes()).hexdigest() if f and f.exists() else None,
                   local_path=path, availability='available', notes=notes))

    def ev(id, sid, locator, statement, url=None, basis='paper'):
        s = next(s for s in d['sources'] if s['id'] == sid)
        return put('evidence', dict(id=id, source_id=sid, locator=locator,
                   url=url or s['url'], basis=basis, statement=statement, inspected=DATE))

    def code(id, model, file, statement, first=1, last=None):
        rev = REV1 if model == 'SpliceAI' else REV2
        url = f'https://github.com/Illumina/{model}/blob/{rev}/{file}'
        sid = id + '-source'
        source(sid, model + ' / ' + file, url,
               f'research/artifacts/splice-audit/{model}/{file}', rev, 'repository-file')
        return ev(id, sid, f'{file}, lines {first}' + (f'–{last}' if last else ''), statement,
                  url + f'#L{first}' + (f'-L{last}' if last else ''), 'code')

    source('spliceai-paper', 'SpliceAI: Cell 2019 full article and STAR Methods', PDF1,
           'research/artifacts/splice-audit/spliceai.pdf', 'Cell 176:535–548.e24; 39-page author PDF',
           notes='Primary article mirrored by the SCN2A Foundation; publication DOI 10.1016/j.cell.2018.12.015. PDF includes methods and supplemental figures.')
    source('spliceai2-paper', 'SpliceAI2: complete author manuscript', PDF2,
           'research/artifacts/splice-audit/spliceai2.pdf', 'bioRxiv v1, 2026-10-11; 57 pages',
           notes='Preprint v1; DOI 10.64898/2026.10.08.757673; full text also at PMC13692246.')
    for id, title, year, date, doi, status in [
        ('spliceai', 'Predicting Splicing from Primary Sequence with Deep Learning', 2019, '2019-01-24', '10.1016/j.cell.2018.12.015', 'journal'),
        ('spliceai2', 'A unified framework for quantitative splicing and transcript prediction', 2026, '2026-10-11', '10.64898/2026.10.08.757673', 'preprint')]:
        put('papers', dict(id=id, title=title, year=year, publication_date=date, doi=doi,
                          source_id=id+'-paper', status=status, scope='primary-model',
                          notes='Supervised splicing specialist; not a self-supervised genomic language model. Included explicitly for comparison of annotation capabilities.'))

    def pe(id, paper, page, loc, text):
        return ev(id, paper+'-paper', loc + f'; PDF page {page}', text,
                  (PDF1 if paper=='spliceai' else PDF2)+f'#page={page}')

    arch1 = pe('spliceai-architecture', 'spliceai', 17, 'STAR Methods: architecture; model training and testing',
        'Dilated residual convolutional sequence-to-sequence model; one-hot A/C/G/T; 80/400/2,000/10,000 total flanking bases, half on each side. Predict donor/acceptor/neither at every output base; 5,000-base training outputs. Five independently trained replicas are averaged.')
    split1 = pe('spliceai-partitions', 'spliceai', 17, 'STAR Methods: model training and testing, pp.17–18',
        'GENCODE V24lift37 principal protein-coding transcripts, hg19. Training pool: 13,384 genes and 130,796 donor–acceptor pairs on chr2/4/6/8/10–22/X/Y; 10% of training genes randomly held for early stopping. Test: 1,652 genes and 14,289 pairs on chr1/3/5/7/9 after excluding genes with any Ensembl paralog. Variant-analysis model adds GTEx junctions found in at least five individuals, while evaluated variants occur in at most four individuals.')
    linc = pe('spliceai-linc-eval', 'spliceai', 18, 'STAR Methods: model evaluation on lincRNAs',
        'Longest-exonic transcript per lincRNA gene; retain transcripts accounting for at least 95% of junction reads and with every junction observed. 781 transcripts, 1,047 junctions; score all transcript positions with donor/acceptor top-k accuracy and PR-AUC. This is an annotation-filtered lincRNA evaluation, not a whole-isoform reconstruction benchmark.')
    inclusion = pe('spliceai-exon-inclusion-method', 'spliceai', 19, 'STAR Methods: exon inclusion; Fig.1c',
        'GTEx exon inclusion from flanking and exon-skipping junction counts, excluding first/last GENCODE exons; compare with the larger of donor/acceptor predictions. This scores a value at each known exon, not full transcript structures.')
    variants1 = pe('spliceai-gtex-method', 'spliceai', 21, 'STAR Methods pp.21–26: GTEx processing, validation, effect size, sensitivity',
        '149 GTEx individuals with WGS and multi-tissue RNA-seq. Autosomal gene-body SNVs observed in at most four people; personalized reference alignments. Gains and losses use distinct private-junction/quantitative criteria and expression/coverage eligibility; only 55% of high-score gains and 44% of high-score losses are ascertainable. Sensitivity truth requires effects at least 0.3 and SNVs within 20 nt of affected sites, excluding essential dinucleotides. Validation, sensitivity and effect-size denominators differ.')
    tissue1 = pe('spliceai-tissue-analysis', 'spliceai', 27, 'STAR Methods: detection of tissue-specific splice-gain variants; Fig.3c',
        'Chi-square test of tissue heterogeneity of observed novel-junction usage in GTEx carriers. SpliceAI is tissue-agnostic; this analysis establishes tissue dependence of variant outcomes and does not evaluate tissue-conditioned model predictions.')
    pop1 = pe('spliceai-population-method', 'spliceai', 27, 'STAR Methods pp.27–28: ExAC and gnomAD; Fig.4',
        'ExAC v0.3.1 exonic/near-intronic and gnomAD genomes v2.0.1 deep-intronic singleton versus common-variant depletion analyses. Score bins, variant consequences and gene constraint stratify enrichment. These are population diagnostics, not splice-label or transcript exact-match tests.')
    disease1 = pe('spliceai-disease-method', 'spliceai', 28, 'STAR Methods: DDD/ASD cohort and gene enrichment, pp.28–29; Fig.5',
        'Published de novo variants in 3,953 ASD, 4,293 DDD probands and 2,073 controls; quality/consequence filtering, scaled burden and gene-level mutation-rate enrichment. Cohorts are not supervised fitting folds.')
    lcl1 = pe('spliceai-lcl-method', 'spliceai', 29, 'STAR Methods pp.29–30: LCL validation; Fig.5f and S6',
        'Selected de novo predictions in SSC lymphoblastoid cell lines; gain score >0.5 and loss >0.1, using an earlier model without GTEx novel-junction training. Figure S6 describes 36 selected sites; summary reports 21 of 28 assessable patients validated. These units and ascertainment denominators must not be interchanged.')
    motif1 = pe('spliceai-motif-method', 'spliceai', 19, 'STAR Methods pp.19–20: motif perturbation; Fig.S2c,d',
        'Insert TACTAAC or GAAGAA at controlled offsets around the 14,289 held-out splice-site pairs and measure changes of site scores. This is a model response experiment, not independently measured splicing for the inserted sequences.')
    arch2 = pe('spliceai2-architecture', 'spliceai2', 20, 'Methods: inputs, architecture and outputs, pp.20–22',
        'Approximately 13M parameters; 20 MetaFormer blocks with depthwise dilated convolutions, pooling/upsampling, 256 channels. One-hot bases plus ten species channels. 196,608-base sense-strand input; dense donor/acceptor usage over central 65,536 bases; pairwise junction logits among top 1,024 predicted sites. RoPE dot-product junction heads and dynamic-programming transcript paths; two-model ensemble.')
    corpus2 = pe('spliceai2-training-data', 'spliceai2', 19, 'Methods: short/long-read RNA-seq, pp.19–20; Fig.1a',
        '314,745 short-read RNA-seq samples and 67,493,026 junctions across human, chimpanzee, baboon, crab-eating/rhesus macaques, cow, sheep, pig, mouse and rat. Long-read data: 189 human and 141 mouse samples; filtered to known protein-coding genes and short-read-supported sites. Intron-chain-equivalent isoforms are merged. Retained long-read sets contain 14,257 human/13,491 mouse genes and 593,157/379,729 transcripts. These totals are source/training resources, not held-out evaluation counts.')
    split2 = pe('spliceai2-training-split', 'spliceai2', 24, 'Methods: training; variant prediction, pp.24–26',
        'Human chr21/22 held for validation; remaining genes and nonhuman species train the main model. BCE for cube-root-transformed short-read site/junction usage; graph-based transcript distribution loss from long reads. 50 epochs, Muon/AdamW, two replicas. Shared candidate sites across alleles support delta scoring; junction changes are excluded from the reported summary score because they gave no net improvement.')
    top2 = pe('spliceai2-top-transcript-method', 'spliceai2', 28, 'Methods: top transcript benchmark; Fig.1b,c (PDF pp.11–12)',
        '352 human genes on chr21/22; multi-exon, most abundant transcript has at least twice the second transcript’s read support. Exact match only from 10 bp upstream of first splice site to 10 bp downstream of last. Human-only models prevent ortholog leakage for this reference-sequence comparison. Figure 1c includes site-only, site+junction and long-read-supervised arms. Held-out chromosomes are also called validation chromosomes; no independent third test is specified. This is not TSS/TES recovery or recovery/quantification of every isoform.')
    gtag2 = pe('spliceai2-gtag-method', 'spliceai2', 28, 'Methods: GTEx/GEL GT/AG, pp.28–29; Fig.1d,4g',
        'Rare SNVs creating GT/AG dinucleotides; matched personalized-diploid RNA-seq establishes novel-site support. Exclude essential splice variants. GTEx: 4,545 cryptic and 573,967 null variants; GEL: 3,065 cryptic and 1,775,800 null. Detection uses auPRC; quantitative GTEx usage uses only the 4,545 cryptic positives and normalizes novel junction counts by the gene maximum donor/acceptor count. Independent variant observations are not a chromosome-disjoint reference sequence test.')
    sqtl2 = pe('spliceai2-sqtl-method', 'spliceai2', 29, 'Methods: GTEx sQTL; Fig.1d',
        'GTEx v8 significant variant–junction pairs within 50 bp of either junction end, averaged across significant tissues. Fine-mapped PIP≥0.9 in at least one tissue versus PIP<0.1 in all tissues and |mean effect|<0.5; essential splice variants excluded. 2,385 fine-mapped and 3,824 null variants; auROC classification and Spearman on fine-mapped effect sizes are different targets.')
    open2 = pe('spliceai2-opensplice-method', 'spliceai2', 29, 'Methods: OpenSplice MPRA, pp.29–30; Fig.1d',
        '283,121 single-base substitutions across 599 OpenSplice exons. SpliceAI2 delta-PSI is the mean of alternate-minus-reference donor/acceptor usage at the measured exon’s boundaries. Comparator scores are released OpenSplice scores. Spearman against experimental delta-PSI; essential splice variants excluded. BEND’s full intervention set and macro-gene fitting/scoring protocol are separate variants of this dataset × target.')
    tissue2 = pe('spliceai2-tissue-method', 'spliceai2', 30, 'Methods: tissue architecture/training and junction evaluation, pp.30–32; Fig.2b',
        'Full fine-tuning conditions on 147 RBP expression values across 48 GTEx tissues. Input uses 1-kb flanks and capped 64-kb genes/segments, not the 196,608-base base-model protocol. Train chr2/4/6/8/10–22/X; validate chr1/3/5/7/9. Candidate anchor-based junction usages are normalized among partners. Evaluation in genes≤64 kb compares top/bottom 24 tissues per junction, after read/depth filters and logit transforms; 14,712,948 pairwise comparisons, not distinct genes or independent samples.')
    tve2 = pe('spliceai2-tissue-variant-method', 'spliceai2', 32, 'Methods pp.32–33: tissue-specific variant effect; Extended Data Fig.4c',
        'GTEx variants within 20 bp of splice sites; 24 tissues pooled into ten meta-tissues. Coverage and differential-effect filters. Ridge regression (alpha=1, standardized features) compares measured reference usage alone to reference usage plus predicted alternate probabilities; fivefold cross-validation grouped by chromosome. Tissue-specific model predictions added no benefit in the authors’ comparison.')
    rbp2 = pe('spliceai2-rbp-method', 'spliceai2', 33, 'Methods: RBP motifs and ISM; Fig.2c, Extended Data4b',
        'Motif matches in differentially used junctions; 51-base ISM windows. Select the 400 strongest windows per RBP, then compare mean absolute ISM effects across 48 tissues to RBP expression by OLS. Discovery uses chr1–22 and the same biology guides selection. This is selected-feature interpretation, not an unselected held-out regulatory prediction benchmark.')
    disease2 = pe('spliceai2-disease-context-method', 'spliceai2', 34, 'Methods: SF3B1 uveal melanoma and MBNL1 myotonic dystrophy, pp.34–35; Fig.2d,e',
        'SF3B1: 18 mutant/62 wild-type UVM tumors, two RBP signatures and identical DNA; report held-out-gene junction differences, with cumulative acceptor-spacing/polypyrimidine/branch-point filters. DM1: 44 affected and 11 controls in four signatures (11/15/14/15 biopsies), six condition pairs and read/difference filters. Scores are Pearson on clipped/logit junction-usage differences. Cohort totals are donors/biopsies, not held-out junction counts; fine-tuning partition details beyond the stated held-out genes are not separately specified here.')
    pop2 = pe('spliceai2-population-method', 'spliceai2', 35, 'Methods: population genetics; Fig.3a–c',
        'gnomAD v3.1.2, TOPMed freeze8 and UKB ~450k; absent versus common AF≥0.01% protein-coding gene splice-near SNVs within 30 bp, trinucleotide-matched near 1:1 and excluding essential splice. Percent depletion=(1−1/OR)×100 and score–allele-count Spearman; population proxy, not experimentally verified splicing or transcript labels.')
    protein2 = pe('spliceai2-protein-method', 'spliceai2', 36, 'Methods: UKB proteomics; Fig.3d–f',
        '6,149 rare splice-region variants in 1,656 selected genes; 36,764 participants have plasma protein measurements. Regressed Olink residuals averaged in ≥2 unrelated European-ancestry carriers, exclude co-carried rare coding alleles and essential splice; score nearest canonical splice site, signed loss/gain delta. Pearson with mean carrier protein level; observational variant-level target, not protein sequence or full transcript prediction.')
    gel2 = pe('spliceai2-gel-enrichment-method', 'spliceai2', 37, 'Methods pp.37–38: disease-panel enrichment; Fig.4a–e',
        'GEL: 8,778 probands with <100 confirmed/probable panel genes, with dominant-gene analysis in 7,504. Exclude panel genes with TIER1 diagnosis and specified coding/essential splice consequences. Singleton rare SNVs/indels, phenotype-panel match odds ratio/excess versus ten collision-minimized panel shuffles. Null shuffles are not train/test splits or proof of individual-variant causality.')
    rna2 = pe('spliceai2-gel-rna-method', 'spliceai2', 38, 'Methods pp.38–39: RNA-seq validation; Fig.4f',
        '5,435 GEL probands with WGS/RNA-seq; 47,783,068 called variants, 292,651 with SpliceAI2>0.1; after junction eligibility 41,959 variant–gene pairs. Carrier junction percentile≤5th for loss or≥95th for gain against ≥1,000 coverage-qualified samples. Score-ascertained validation rate, not unselected sensitivity or whole-isoform recovery.')
    comparative2 = pe('spliceai2-comparators', 'spliceai2', 26, 'Methods: competing methods, pp.26–28',
        'SpliceAI release1.3.1 modified for position-resolved predictions, five bundled models, no masking, reference/alternate signed deltas at specified effect sites for GTEx/GEL GT/AG, sQTL and UKB. Population/disease analyses instead use standard summaries without masking. AlphaGenome raw composite selected over 40 configurations for average performance across eight evaluations; no held-out score-selection cohort specified. OpenSplice uses released comparator scores.')
    code('spliceai2-code-decoder', 'SpliceAI2', 'spliceai2/utils.py',
         'decode_topk_tx returns k×L exonic/intronic arrays by k-best dynamic programming; no independent TSS/TES prediction head.', 4, 35)
    code('spliceai2-code-data', 'SpliceAI2', 'spliceai2/dataset.py',
         'Training has separate site, junction and transcript tensors and masks; selects junction candidates from observed site usages at training; graph transcript mask uses top observed transcript endpoints. Species one-hot channels and strand reversal are explicit.', 7, 160)
    code('spliceai2-code-split', 'SpliceAI2', 'spliceai2/train.py',
         'Main training entry point puts only GRCh38 chr21/22 in validation; other assemblies remain in training. This does not itself implement the human-only transcript benchmark arm.', 29, 37)
    code('spliceai-code-variants', 'SpliceAI', 'spliceai/utils.py',
         'get_delta_scores evaluates dense per-base donor/acceptor probabilities but emits per-variant gain/loss deltas and offsets; variant evaluation is distinct from dense site-label evaluation.', 96, 203)

    for id, description, evidence in [
        ('spliceai', 'Supervised dilated convolutional splicing specialist: base-wise donor/acceptor labels and variant deltas; full transcript examples do not constitute a general isoform reconstruction benchmark.', arch1),
        ('spliceai2', 'Supervised quantitative splicing specialist: dense site usage, candidate junction graph and decoded transcript paths. Main multispecies model, human-only top-transcript comparison and tissue-conditioned adaptations are distinguished.', arch2)]:
        put('models', dict(id=id, name='SpliceAI' if id=='spliceai' else 'SpliceAI2', scope='primary',
                          paper_id=id, description=description, evidence_id=evidence,
                          notes='Not self-supervised pretraining. Model output capabilities do not imply every benchmark scores those outputs.'))

    def prop(model, slug, category, name, value, evidence, variant=None, notes=None):
        put('model_properties', dict(id=model+'-'+slug, model_id=model, category=category,
            name=name, variant=variant, value=value, status='reported / source-audited', evidence_id=evidence, notes=notes))
    prop('spliceai','architecture','architecture','Architecture / tokenization', '32-layer dilated residual CNN in the 10k architecture; one-hot bases, not learned subword tokens. Position-aligned donor/acceptor/neither softmax; ensemble of five replicas.',arch1)
    prop('spliceai','training','training','Supervised source and partitions', 'GENCODE V24lift37/hg19 principal coding transcripts; chromosome and paralog-filtered reference test. Variant model additionally uses frequent GTEx junctions; evaluation variants occur in ≤4 individuals.',split1)
    prop('spliceai','context','context','Context protocol','80/400/2,000/10,000 total flanking bases; 40/200/1,000/5,000 each side. 5,000-base central outputs during training; 15,000-base input for SpliceAI-10k. Separately trained context architectures are compared; this is not a same-weights inference-length ablation or a 10-kb maximum gene length.',arch1)
    prop('spliceai2','architecture','architecture','Architecture / tokenization','Approximately 13M parameters; 20 MetaFormer blocks, 256 channels, dilated depthwise convolutions, pooling/upsampling. One-hot bases plus ten species channels; pairwise RoPE attention heads. Graph/path decoder on top of site/junction logits.',arch2)
    prop('spliceai2','corpus','training','Supervised training corpus','314,745 short-read samples from ten mammals plus 330 long-read human/mouse samples. No self-supervised genomic pretraining stage is reported. Gene filtering, intron-chain merging and label normalization matter.',corpus2)
    prop('spliceai2','context','context','Base-model context and outputs','196,608-bp input; central 65,536-bp site outputs; top 1,024 candidate positions for pairwise junctions. Two-model ensemble. The 200-kb input does not imply a 200-kb fully scored output.',arch2)
    prop('spliceai2','target-transform','training','Usage target transformations','Short-read site/junction targets are normalized by the gene maximum donor/acceptor count and cube-root transformed. Long-read transcript counts are normalized within gene. These are different target definitions, not interchangeable PSI measurements.',split2)
    prop('spliceai2','transcript','evaluation','Transcript benchmark scope','352 human genes on chr21/22; human-only training arms. Dominant multi-exon transcript exact splice-pattern match across first-to-last junction ±10 bp. Neither all-isoform recall nor start/end accuracy is established.',top2)
    prop('spliceai2','tissue','context','Tissue-conditioned protocol','147 RBP expression inputs; 48 tissues; full fine-tuning with 1-kb flanks and capped 64-kb sequence inputs. Different chromosome partition and inference interface from the main model.',tissue2)
    hf = json.loads((ROOT/'research/artifacts/splice-audit/hf-model.json').read_text())
    source('spliceai2-hf-manifest','SpliceAI2 model release metadata', 'https://huggingface.co/illumina-ai/SpliceAI2/tree/'+hf['sha'],
           'research/artifacts/splice-audit/hf-tree.json', hf['sha'], 'repository-manifest',
           'Public tree metadata inspected; gated model weights were not downloaded. Two multispecies 13M directories. No benchmark label/coordinate files are in this root manifest.')
    release=ev('spliceai2-release-inspection','spliceai2-hf-manifest','Public model tree API; two model directories',
        'Two multispecies checkpoints listed; weights not inspected. Source code and manuscript audited; per-benchmark data manifests, eligibility recounts and exact released human-only/tissue checkpoints are not established by the inspected root tree.','https://huggingface.co/illumina-ai/SpliceAI2/tree/'+hf['sha'],'documentation')
    prop('spliceai2','release','release','Release inspection limits','Pinned source code and public checkpoint tree inspected; gated weights and full RNA-seq benchmark labels were not downloaded. Do not promote paper benchmark totals to measured file counts.',release)

    def cat(tid, cid, eid, relation='measured', rationale='Assigned from the cited target and scoring procedure.'):
        put('task_categories',dict(task_id=tid,category_id=cid,relation=relation,rationale=rationale,
                                  evidence_id=eid,attribution='curatorial'),('task_id','category_id','relation'))

    def collection(model, evidence):
        id=model+'-evals'
        put('evaluations',dict(id=id,name=('SpliceAI' if model=='spliceai' else 'SpliceAI2')+' paper evaluations',
            description='Dense reference annotation, variant-level outcomes and biological validation are separate tasks and protocols.' if model=='spliceai' else 'Dominant transcript reconstruction, cryptic variants, sQTLs, OpenSplice, tissue/disease conditioning and population/clinical validation.',
            paper_id=model,source_id=model+'-paper',status='paper-audited',
            scope_note='Model-associated experiments, not an independent standardized benchmark project. Source-reported cohorts and units retained; no missing test manifest is inferred.',
            evidence_id=evidence,notes='Supervised specialist; original Evo 2 provenance is unchanged. Paper audit and selected interface-code inspection do not establish a full benchmark artifact audit.'))
        put('project_reviews',dict(id=model,name=('SpliceAI' if model=='spliceai' else 'SpliceAI2')+' model paper',
            decision='outside-definition',dedicated=0,reviewed=DATE,
            search_scope='Primary paper, official source repository and released checkpoint manifest.',
            rationale='Primarily a model-development and biological-validation paper, not a dedicated standardized gLM evaluation framework. Independent reuse of the model does not make its author evaluation panel a benchmark project.',evidence_id=evidence))
        put('project_review_papers',dict(review_id=model,paper_id=model,relation='associated-model',evidence_id=evidence),('review_id','paper_id','relation'))
        put('project_review_evaluations',dict(review_id=model,evaluation_id=id,relation='associated-collection',note='Model paper evaluation collection.',evidence_id=evidence),('review_id','evaluation_id'))
    collection('spliceai',split1);collection('spliceai2',top2)

    def count(tid, value, unit, eid, split='evaluation', variant=None, qualifier='Paper-reported; not independently recounted.'):
        id=tid+'-count-'+str(value)+'-'+split.replace(' ','-')+'-'+(variant or 'main')
        put('counts',dict(id=id,task_id=tid,variant_id=variant,protocol_id=None,split=split,value=value,
                         unit=unit,qualifier=qualifier,method='reported',evidence_id=eid))

    def use(tid, model, paper, eid, protocol=None, note=None):
        put('model_evaluations',dict(id=paper+'-'+model+'-'+tid+'-'+(protocol or 'paper'),model_id=model,
            task_id=tid,protocol_id=protocol,paper_id=paper,provenance='original-paper' if model==paper else 'external-evaluation',
            evidence_id=eid,note=note or 'Author-reported evaluation; benchmark-specific eligibility and scoring are recorded in the linked protocol.'))

    def protocol(tid, model, eid, adaptation, split, metrics, notes=None, variant=None, name=None, interface=None, fitted=None):
        id=model+'-'+tid+'-protocol'
        put('protocols',dict(id=id,task_id=tid,variant_id=variant,name=name or 'Author paper protocol',
            adaptation=adaptation,requires_embeddings=False,
            model_interface=interface or 'Native position-wise splice probabilities / decoded paths; selected readout as specified.',
            fitted_component=fitted or ('All model weights' if 'from scratch' in adaptation else 'Encoder and tissue/signature decoder weights' if 'fine-tune' in adaptation else 'None added for this benchmark; use the specified supervised predictor'),selection='Source-defined eligibility and thresholds; see qualification and source locator.',
            split_rule=split,split_unit='gene / chromosome' if 'chr' in split else 'variant / junction / individual as specified',
            source_evidence_id=eid,notes=notes))
        for metric in metrics:
            put('protocol_metrics',dict(protocol_id=id,metric_id=metric,aggregation='Source-specific cohort and eligibility; see target and protocol.',is_primary=1,evidence_id=eid),('protocol_id','metric_id'))
        use(tid,model,model,eid,id)
        return id

    # New task records are dataset × target. Assay tracks and scoring strata are
    # variants; dense outputs in a model do not automatically make its eval dense.
    def task(id, model, name, dataset, target, desc, typ, eid, features=('splice',), apps=('variant-interpretation',),
             caps=('variant-effects',), input='Sense-strand reference/alternate human DNA; context and readout are protocol-specific.',
             output='Per-variant splicing score', labels='Source RNA-seq / annotation eligibility as specified in the cited methods.', limits=None):
        put('tasks',dict(id=id,name=name,dataset_name=dataset,target=target,description=desc,task_type=typ,
            label_basis=labels,status='paper-audited',evidence_id=eid,
            limitations=limits or 'Paper-reported cohort; individual labels and exact eligibility counts have not been reconstructed from released benchmark files. No pretraining or split exclusion is inferred.',
            input_description=input,output_description=output))
        put('evaluation_tasks',dict(evaluation_id=model+'-evals',task_id=id,variant_id=None,note='Author paper; source and scoring unit audited.',evidence_id=eid),('evaluation_id','task_id'))
        put('task_populations',dict(task_id=id,population_id='human',variant_id=None,relation='sequence-origin',coverage='Human evaluation cohort only; multispecies training is recorded at model level.',evidence_id=eid),('task_id','population_id','relation'))
        for cid in features:cat(id,cid,eid,'target')
        for cid in apps+caps:cat(id,cid,eid)
        m=copy.deepcopy(next(m for m in d['coverage_mappings'] if m['task_id']=='evo-clinvar' and m['population_id']=='human'))
        m.update(id=id+'-mapping-0',task_id=id,evidence_id=eid)
        md=json.loads(m['metadata_json']);md.update(url=next(e['url'] for e in d['evidence'] if e['id']==eid),note='Evaluation cohort is human; training species are not mapped as evaluated taxa.')
        m['metadata_json']=json.dumps(md,ensure_ascii=False);put('coverage_mappings',m)
        return id

    refsplit='Train chr2/4/6/8/10–22/X/Y; random 10% training-gene early stopping; test chr1/3/5/7/9, genes without any annotated paralog. GENCODE V24lift37/hg19.'
    for id,name,dataset,eid in [
        ('spliceai-sites-coding','SpliceAI: dense coding-gene splice-site labels','GENCODE V24lift37 principal coding transcripts',split1),
        ('spliceai-sites-linc','SpliceAI: dense lincRNA splice-site labels','GENCODE V24lift37 / GTEx-filtered lincRNAs',linc)]:
        task(id,'spliceai',name,dataset,'Donor / acceptor / neither at every transcript position',
             'Score every position in reference pre-mRNA sequences. Top-k and PR-AUC evaluate site detection; exact CFTR/LINC00467 illustrations are not a cohort-wide isoform exact-match metric.',
             'dense multiclass classification',eid,('splice','lncrna') if id.endswith('linc') else ('splice',),('genome-annotation',),('dense-annotation','functional-prediction','long-context') if id.endswith('coding') else ('dense-annotation','functional-prediction'),
             input='Unspliced genomic transcript with symmetric flanking context; models compared at 80/400/2,000/10,000 total flank bases.',output='Three probabilities per base over the central output sequence')
        protocol(id,'spliceai',eid,'supervised training from scratch',refsplit if id.endswith('coding') else 'lincRNA genes not used for coding-gene training; longest transcript and GTEx junction-support filters. Not an independently chromosome-held-out lincRNA panel.',('top-k-site-accuracy','auprc'),notes='Top-k threshold uses the known number of true sites; average donor/acceptor metrics. Dense site recovery does not establish junction pairing or all-isoform reconstruction.')
    count('spliceai-sites-coding',1652,'test genes',split1);count('spliceai-sites-coding',14289,'test donor–acceptor pairs',split1)
    count('spliceai-sites-coding',13384,'training-pool genes',split1,'training pool',qualifier='Before random 10% early-stopping holdout; not final fitted-gene count.')
    count('spliceai-sites-linc',781,'retained transcripts',linc);count('spliceai-sites-linc',1047,'junctions',linc)
    task('spliceai-exon-inclusion','spliceai','SpliceAI: known-exon inclusion','GTEx / GENCODE internal exons','Inclusion fraction at a known exon','Compare annotated internal-exon inclusion to max donor/acceptor score. Known exon boundaries are supplied.','regression',inclusion,('exon','splice'),('rna-engineering',),('functional-prediction',),output='One inclusion-associated value per known exon')
    protocol('spliceai-exon-inclusion','spliceai',inclusion,'supervised pretrained predictor; no new readout fitting','Internal exons of GENCODE test transcripts; first/last exons excluded; counts pooled across GTEx samples.',('pearson',))
    for id,name,target,typ,eid,metrics in [
        ('spliceai-gtex-detection','SpliceAI: GTEx cryptic splicing','Splice-altering gain/loss validation and detection','binary classification',variants1,('validation-rate','recall')),
        ('spliceai-gtex-effect','SpliceAI: GTEx splice-effect magnitude','RNA-seq estimated fraction of aberrant transcripts','regression',variants1,('effect-size-trend',)),
        ('spliceai-gtex-tissue','SpliceAI: tissue dependence of cryptic gains','Heterogeneity of observed novel-junction usage','association analysis',tissue1,('heterogeneity-p',)),
        ('spliceai-population','SpliceAI: population depletion','Deleterious fraction / singleton versus common depletion','enrichment analysis',pop1,('enrichment',)),
        ('spliceai-disease-burden','SpliceAI: neurodevelopmental disease burden','Excess de novo cryptic splice mutations','enrichment analysis',disease1,('enrichment','discoveries')),
        ('spliceai-lcl-validation','SpliceAI: SSC cell-line RNA validation','RNA validation of selected de novo predictions','binary classification',lcl1,('validation-rate',))]:
        task(id,'spliceai',name,'GTEx v6' if 'gtex' in id else 'ExAC / gnomAD' if 'population' in id else 'ASD / DDD / control cohorts' if 'burden' in id else 'SSC lymphoblastoid cell lines',target,
             next(e['statement'] for e in d['evidence'] if e['id']==eid),typ,eid,output='Variant-level outcome / source-defined cohort statistic')
        protocol(id,'spliceai',eid,'native supervised predictor; no benchmark probe fitting',
            'Frequent GTEx junctions (≥5 individuals) augment training; evaluated SNVs occur in ≤4 individuals; train/test chromosome strata reported separately.' if 'gtex' in id else 'Observed cohort analysis; no additional supervised benchmark train/test fit. LCL predictions use an earlier GENCODE-only model.' if 'lcl' in id else 'External observed cohorts, source-specific filtering; training and held-out chromosome strata are reported in Fig.S4, not all variants excluded from training chromosomes.',metrics)
    count('spliceai-gtex-detection',149,'WGS/RNA-seq individuals',variants1,qualifier='Source cohort, not eligible variant count.')
    for n,unit in [(3953,'ASD probands'),(4293,'DDD probands'),(2073,'healthy controls')]:count('spliceai-disease-burden',n,unit,disease1)
    count('spliceai-lcl-validation',36,'selected predicted sites',lcl1,qualifier='Fig.S6 site count; main summary uses 28 assessable patients. Do not divide patient successes by site count.')
    task('spliceai-motif-perturbation','spliceai','SpliceAI: controlled motif perturbation','Held-out GENCODE splice sites with synthetic motif insertions','Splice-score response to motif position','Controlled TACTAAC/GAAGAA insertion and in-silico mutagenesis; no measured outcome for the inserted sequences.','sequence diagnostic',motif1,('splice',),('model-development',),('interpretability',),output='Score change at a specified splice site')
    protocol('spliceai-motif-perturbation','spliceai',motif1,'native supervised predictor; in silico perturbation',refsplit,('effect-size-trend',))

    task('spliceai2-top-transcript','spliceai2','SpliceAI2: dominant transcript splice-chain reconstruction','ENCODE human long-read dominant transcripts / chr21–22','Exact dominant-transcript splicing structure',
        'Decode the highest-scoring transcript path and compare the complete internal splice pattern. This is a structured reconstruction task with explicit endpoint and dominance restrictions.',
        'structured prediction',top2,('transcript','splice','splice-junction','exon','intron'),('genome-annotation','rna-engineering'),('structured-annotation','dense-annotation'),
        input='Human sense-strand genomic sequence; known gene/strand and read-supported benchmark span.',output='Decoded dominant transcript exon/intron path',
        limits='352 dominance-filtered multi-exon human genes; exact match only first-to-last splice site ±10 bp. TSS/TES and all-isoform recall/abundance are not evaluated. Human-only training arms differ from the multispecies released ensemble; chr21/22 also serve as validation chromosomes.')
    protocol('spliceai2-top-transcript','spliceai2',top2,'supervised training from scratch; human-only ablations',
        'Train human genes outside chr21/22; evaluate 352 eligible chr21/22 genes. Same chromosomes held for validation; no independent third split specified. Nonhuman data excluded to prevent ortholog leakage.',('exact-match',),notes='Site-only/site+junction/long-read-supervised arms in Fig.1c. Exact boundary pattern, not just independent site accuracy.')
    count('spliceai2-top-transcript',352,'eligible evaluation genes',top2)
    # Five benchmark targets; classification and quantitative targets use linked
    # cohorts, not duplicated tasks for exonic/intronic reporting strata.
    scalar = [
        ('gtag-detection','GTEx cryptic-site activation','GTEx WGS / matched RNA-seq','Cryptic gain versus null','binary classification',gtag2,('auprc',)),
        ('gtag-usage','GTEx cryptic-site usage','GTEx WGS / matched RNA-seq','Usage of experimentally supported new splice site','regression',gtag2,('spearman',)),
        ('sqtl-detection','GTEx sQTL fine-mapping','GTEx v8 SuSiE variant–junction pairs','Fine-mapped versus low-PIP null variant','binary classification',sqtl2,('auroc',)),
        ('sqtl-effect','GTEx sQTL effect magnitude','GTEx v8 fine-mapped variant–junction pairs','Average significant-tissue effect size','regression',sqtl2,('spearman',)),
        ('gel-gtag','GEL cryptic-site activation','GEL WGS / matched RNA-seq','Cryptic gain versus null','binary classification',gtag2,('auprc',))]
    for slug,name,dataset,target,typ,eid,metrics in scalar:
        tid='spliceai2-'+slug
        task(tid,'spliceai2','SpliceAI2: '+name,dataset,target,
             'Variant-level evaluation from matched sequence and RNA-seq or fine-mapping; site-local outputs are selected from the model, rather than scoring its whole dense output or transcript paths.',typ,eid,
             ('splice','splice-junction') if 'sqtl' in slug else ('splice',))
        p=protocol(tid,'spliceai2',eid,'native supervised predictor; no benchmark probe fitting',
            'Main model: human chr21/22 validation and other human/nonhuman genes training. Variant cohort is not limited to chr21/22; no test-only gene or homology exclusion is stated for this benchmark.',metrics,notes='Essential splice variants excluded. SpliceAI comparator uses modified position-resolved signed deltas; no direct isoform-level metric.')
        use(tid,'spliceai','spliceai2',comparative2,p,'External comparison in SpliceAI2 paper; not an original SpliceAI 2019 experiment.')
    for tid,nums,eid in [
        ('spliceai2-gtag-detection',[(4545,'cryptic variants'),(573967,'null variants')],gtag2),
        ('spliceai2-gtag-usage',[(4545,'cryptic variants')],gtag2),
        ('spliceai2-sqtl-detection',[(2385,'fine-mapped variants'),(3824,'null variants')],sqtl2),
        ('spliceai2-sqtl-effect',[(2385,'fine-mapped variants')],sqtl2),
        ('spliceai2-gel-gtag',[(3065,'cryptic variants'),(1775800,'null variants')],gtag2)]:
        for n,unit in nums:count(tid,n,unit,eid)

    # Reuse OpenSplice's existing dataset × delta-PSI target.
    tid='bend-opensplice';vid='spliceai2-opensplice-snv'
    put('variants',dict(id=vid,task_id=tid,name='SpliceAI2 paper SNV subset',dataset_revision='OpenSplice released comparator scores; exact file/version not specified in SpliceAI2 paper',context='Human minigene exon-inclusion assay; essential splice variants excluded.',input_length='Native genomic context for model scoring; assay minigene context differs',target_count=599,target_unit='exons',notes='283,121 SNVs; not BEND’s full 590,104 intervention cohort or macro-gene readout protocol.',evidence_id=open2))
    put('evaluation_tasks',dict(evaluation_id='spliceai2-evals',task_id=tid,variant_id=vid,note='Same OpenSplice delta-PSI target; different eligibility, comparator scores and Spearman aggregation from BEND.',evidence_id=open2),('evaluation_id','task_id'))
    p=protocol(tid,'spliceai2',open2,'native supervised predictor; no new readout fitting',
        'Published experimental SNV benchmark; SpliceAI2 paper does not specify an exon/gene holdout from training for this subset.',('spearman',),variant=vid,name='SpliceAI2 paper OpenSplice SNV protocol',notes='Mean donor/acceptor delta at the measured exon. Global Spearman, not BEND macro-gene Spearman. RNA-seq labels used for model fitting differ from MPRA variant labels; gene overlap is not thereby excluded.')
    use(tid,'spliceai','spliceai2',open2,p,'Released OpenSplice comparator scores; distinct from original-paper SpliceAI use.')
    count(tid,283121,'SNV assay measurements',open2,variant=vid);count(tid,599,'exons',open2,variant=vid)

    for slug,name,dataset,target,typ,eid,features,metrics in [
        ('tissue-junction','tissue-pair splice-junction differences','GTEx v8, 48 tissues','Logit junction-usage difference between tissues','pairwise regression',tissue2,('splice-junction',),('pearson',)),
        ('tissue-variant','tissue-specific variant effects','GTEx v8, ten meta-tissues','Carrier-minus-noncarrier differential junction usage','regression',tve2,('splice-junction','splice'),('pearson',)),
        ('sf3b1','SF3B1-associated splicing differences','TCGA uveal melanoma','Mutant-minus-wild-type logit junction usage','pairwise regression',disease2,('splice-junction',),('pearson',)),
        ('dm1','myotonic-dystrophy splicing differences','GSE86356 tibialis-anterior biopsies','Condition-pair logit junction usage differences','pairwise regression',disease2,('splice-junction',),('pearson',)),
        ('rbp-ism','RBP motif and tissue-effect interpretation','ATtRACT/oRNAment motifs / GTEx tissues','Association of selected motif ISM response with RBP expression','association analysis',rbp2,('splice-junction',),('pearson',)),
        ('population','population depletion and allele count','gnomAD / TOPMed / UK Biobank','Splice-score association with selection proxy','enrichment analysis',pop2,('splice',),('enrichment','spearman')),
        ('protein','splice-variant plasma protein abundance','UK Biobank WGS / Olink proteomics','Mean adjusted carrier plasma protein level','regression',protein2,('splice',),('pearson',)),
        ('gel-panel','rare-disease panel enrichment','GEL 100,000 Genomes rare disease','Phenotype-panel enrichment of scored variants','enrichment analysis',gel2,('splice',),('enrichment','discoveries')),
        ('gel-rna','RNA validation of selected GEL predictions','GEL WGS / blood RNA-seq','Coverage-qualified carrier junction validation','binary classification',rna2,('splice','splice-junction'),('validation-rate',))]:
        tid='spliceai2-'+slug
        task(tid,'spliceai2','SpliceAI2: '+name,dataset,target,next(e['statement'] for e in d['evidence'] if e['id']==eid),typ,eid,
             features,('rna-engineering','variant-interpretation'),('context-specific',) if slug in ('tissue-junction','sf3b1','dm1') else ('interpretability',) if slug=='rbp-ism' else ('variant-effects',),
             input='Genomic DNA plus 147 RBP expression values for tissue/disease-conditioned arms.' if slug in ('tissue-junction','tissue-variant','sf3b1','dm1','rbp-ism') else 'Human reference/alternate genomic sequence; variant and cohort eligibility as cited.',
             output='Junction-specific usage difference' if typ=='pairwise regression' else 'Variant-level outcome / cohort association statistic')
        adaptation='full fine-tune with tissue signature' if slug in ('tissue-junction','sf3b1','dm1','rbp-ism') else 'tissue-conditioned predictor plus fitted ridge regression' if slug=='tissue-variant' else 'native supervised predictor; no additional benchmark fitting'
        split='Fivefold ridge CV grouped by chromosome; reference-usage-only versus reference-plus-model features.' if slug=='tissue-variant' else 'Fine-tuning: train chr2/4/6/8/10–22/X; validate chr1/3/5/7/9. Evaluate filtered junctions from held-out genes.' if slug=='tissue-junction' else 'Paper reports held-out genes for disease-context evaluation; independent disease-specific coordinate manifests and participant holdouts not established.' if slug in ('sf3b1','dm1') else 'Selected motif matches across chr1–22, selected by the same model response before tissue association; no independent motif test set.' if slug=='rbp-ism' else 'External observational cohort / score-selected validation; no supervised benchmark train/test partition reported. No automatic gene/chromosome exclusion inferred.'
        p=protocol(tid,'spliceai2',eid,adaptation,split,metrics,fitted='Ridge regression alpha=1' if slug=='tissue-variant' else None)
        if slug in ('population','protein','gel-panel'):
            use(tid,'spliceai','spliceai2',comparative2,p,'Comparator settings vary by benchmark: position-resolved for protein, standard summaries for population/panel enrichment.')
    for tid,nums,eid in [
        ('spliceai2-tissue-junction',[(14712948,'filtered junction × tissue-pair comparisons'),(48,'tissues')],tissue2),
        ('spliceai2-sf3b1',[(18,'mutant tumors'),(62,'wild-type tumors')],disease2),
        ('spliceai2-dm1',[(44,'affected biopsies'),(11,'control biopsies')],disease2),
        ('spliceai2-protein',[(6149,'eligible variants'),(1656,'selected genes'),(36764,'source participants')],protein2),
        ('spliceai2-gel-panel',[(8778,'source probands'),(7504,'dominant-gene analysis probands')],gel2),
        ('spliceai2-gel-rna',[(5435,'source probands'),(41959,'coverage-qualified variant–gene pairs')],rna2)]:
        for n,unit in nums:count(tid,n,unit,eid,qualifier='Paper-reported unit. Participants, junction-pair comparisons and variants are different denominators and are not additive.')

    # Original-paper use remains attached to Evo 2; SpliceAI is an external
    # comparator reported by that paper, not an extra Evo 2 task.
    e=ev('spliceai-evo-comparison','evo-paper','Fig.3b,d and supplementary variant comparisons',
        'Evo 2 compares supervised SpliceAI on ClinVar and SpliceVarDB. These are external SpliceAI evaluations in the Evo 2 paper, not original SpliceAI 2019 experiments.','https://www.nature.com/articles/s41586-026-10176-5#Fig3')
    for tid in ('evo-clinvar','evo-splicevardb'):use(tid,'spliceai','evo',e,note='External specialist baseline in splice-relevant strata. Does not establish evaluation on every ClinVar consequence. No new original Evo 2 task association.')
    e=ev('spliceai-bend-comparison','bend-paper','Table1; mutation effect prediction; specialist baseline',
        'BEND 2.0 compares native SpliceAI outputs on OpenSplice (macro-gene Spearman), separately from frozen linear readouts on foundation-model embeddings.')
    use('bend-opensplice','spliceai','bend',e,note='External BEND 2.0 native-output specialist baseline; not a newly fitted foundation-model probe.')

    # Experimental dataset paper identity and actual scalar readout artifacts.
    # Its full preprint could not be fetched here; do not label that paper audited.
    rev='3e4ad8c037c216b952f1a8945f8f498669bff589'
    file='benchmarking_predictors/scripts/processing/process_spliceai_genome_outputs.py'
    url=f'https://github.com/lehner-lab/OpenSplice/blob/{rev}/{file}'
    source('opensplice-canonical-processing','OpenSplice canonical-site output processing',url,
        'research/artifacts/splice-audit/OpenSplice/'+file,rev,'repository-file',
        'Source readout inspected; neither model inference nor all assay table rows re-run in this follow-up.')
    oe=ev('opensplice-canonical-readout','opensplice-canonical-processing','Module docstring and process_spliceai_genome_file',
        'Released processing selects canonical donor/acceptor positions per exon and compares each mutant with WT. This reduces dense native scores to exon/variant-level deltas, not an isoform-reconstruction output.',url+'#L1-L16','code')
    source('opensplice-paper','OpenSplice experimental dataset preprint','https://doi.org/10.64898/2026.05.22.727141',
        version='bioRxiv v1, 2026-05-23',notes='Paper identity and associated code verified. Full-text retrieval returned HTTP403 in this audit; no full-paper audit is claimed. Official repository provides assay processing and predictor scripts.')
    put('papers',dict(id='opensplice',title='OpenSplice: the impact of half a million mutations on the alternative splicing of 600 human exons',year=2026,
        publication_date='2026-05-23',doi='10.64898/2026.05.22.727141',source_id='opensplice-paper',status='preprint; associated artifacts inspected',scope='evaluation-source',
        notes='Primary experimental dataset reused by BEND 2.0 and SpliceAI2. Counts differ by release and eligibility. Full preprint not retrieved in this follow-up; do not conflate repository inspection with full-text audit.'))
    put('field_evidence',dict(entity_table='tasks',entity_id='bend-opensplice',field='output_description',evidence_id=oe,note='Canonical site readout in original dataset code; BEND and SpliceAI2 protocol variants remain separate.'),('entity_table','entity_id','field','evidence_id'))
    d['task_categories']=[r for r in d['task_categories'] if not(r['task_id'] in ('spliceai-motif-perturbation','spliceai2-rbp-ism') and r['category_id']=='tfbs')]

    # Metrics specific to these source protocols.
    for id,name,definition,direction in [
        ('top-k-site-accuracy','Top-k splice-site accuracy','Fraction of true sites recovered among k predictions, with k equal to the known number of true sites; donor/acceptor averaged.','higher'),
        ('validation-rate','RNA validation rate','Fraction of eligible selected predictions meeting the specified RNA-seq criteria; not unselected sensitivity.','higher'),
        ('effect-size-trend','Score / measured-effect trend','Source score-bin distributions or controlled score changes; no single independent predictive correlation asserted.','context-dependent'),
        ('heterogeneity-p','Tissue heterogeneity test','Source chi-square p-value for observed novel-junction usage heterogeneity; not accuracy of a tissue-specific model.','context-dependent')]:
        put('metrics',dict(id=id,name=name,definition=definition,direction=direction))
    return d


if __name__ == '__main__':
    path=ROOT/'data/catalogue.json'
    path.write_text(json.dumps(populate(json.loads(path.read_text())),ensure_ascii=False,indent=2)+'\n')
