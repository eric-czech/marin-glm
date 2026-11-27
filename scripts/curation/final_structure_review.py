"""Completed original BEND, SpliceAI and SpliceAI2 source/resource reviews.

Uses pinned source evidence and complete BEND artifact inspections. No canonical
files are written; populate(d) is an explicit authoring operation.
"""
import json
from common import Catalogue, ROOT

INSPECTIONS = json.loads((ROOT / 'data/structure-artifact-inspections.json').read_text())


def populate(d):
    c = Catalogue(d)

    def code(repo, file, slug, statement, first=1, last=None):
        revision = INSPECTIONS['repositories'][repo]['revision']
        owner = 'frederikkemarin' if repo == 'BEND' else 'Illumina'
        url = f'https://github.com/{owner}/{repo}/blob/{revision}/{file}'
        sid = 'final-structure-' + slug
        c.source(sid, repo + ': ' + file, url, 'repository-file', revision,
            notes='Pinned source file inspected; byte hash is retained in the committed structural audit manifest.')
        c.get('sources', sid)['sha256'] = INSPECTIONS['source_files'][repo + '/' + file]
        anchor = f'#L{first}' + (f'-L{last}' if last else '')
        return c.evidence(sid + '-review', sid, file + f', lines {first}' + (f'–{last}' if last else ''),
            statement, 'code', url + anchor)

    bend_readme = code('BEND', 'README.md', 'bend-readme',
        'Original BEND supplies coordinate/partition BED files and matching HDF5 labels where needed, on the ERDA public share. '
        'It defines five frozen-embedding supervised tasks plus two whole-cohort unsupervised variant tasks. Dataset files are separate from GitHub implementation code.', 18, 43)
    bend_embed = code('BEND', 'bend/io/sequtils.py', 'bend-embedding-input',
        'The loader extracts reference sequence from BED start:end, applies an explicit flank parameter (default zero), and matches each HDF5 vector by row. '
        'Comma-separated BED labels are sparse active class indices converted to multi-hot vectors; a vector of assay labels is not a position axis.', 112, 165)
    bend_build = code('BEND', 'conf/embedding/embed.yaml', 'bend-assemblies',
        'Current pinned config uses GRCh38 for gene finding, enhancer, histone and methylation tasks, and GRCh37.no-chr.fa for accessibility. '
        'Gene finding has no extra flank override. BED flank_left/flank_right metadata are not automatically added to extraction coordinates.', 106, 137)
    bend_selection = code('BEND', 'bend/utils/task_trainer.py', 'bend-selection',
        'When no checkpoint is supplied, test() selects the epoch maximizing the recorded validation metric and loads that checkpoint for test evaluation. '
        'The docstring says lowest validation loss, which disagrees with the implemented idxmax validation-metric selection.', 522, 550)
    bend_labels = code('BEND', 'bend/utils/sequences.py', 'bend-label-map',
        'The nine-class strand-aware map labels CDS/start codon, introns, donor/acceptor boundaries and noncoding background. '
        'UTRs, ordinary exon annotations and stop codons are background in this map; alternative label dictionaries do not establish additional released targets.', 15, 31)
    c.source('final-structure-bend-fold-code', 'Original BEND cross-validation loader',
        'https://github.com/frederikkemarin/BEND/blob/' + INSPECTIONS['repositories']['BEND']['revision'] + '/bend/utils/data_downstream.py',
        'repository-file', INSPECTIONS['repositories']['BEND']['revision'])
    bend_folds = c.evidence('final-structure-bend-fold-review', 'final-structure-bend-fold-code',
        'get_data, lines 170–186',
        'For an enhancer cross-validation partition, the current loader uses that partition for test, the next partition (wrapping to the first) for validation, and all remaining partitions for training.', 'code',
        c.get('sources', 'final-structure-bend-fold-code')['url'] + '#L170-L186')

    # Every original BEND BED was read, together with both positional label files.
    task_slugs = {'gene_finding': 'gene-finding', 'enhancer_annotation': 'enhancer-annotation',
        'chromatin_accessibility': 'accessibility', 'histone_modification': 'histone',
        'cpg_methylation': 'cpg', 'variant_effects_disease': 'disease-variant',
        'variant_effects_expression': 'expression-variant'}
    bend_evidence = [bend_readme, bend_embed, bend_build, bend_selection, bend_labels, bend_folds]
    for st in INSPECTIONS['bend_data']:
        slug = task_slugs[st['task']]
        tid = 'bend1-' + slug
        sid = 'final-structure-bend-data-' + slug
        c.source(sid, 'Original BEND released ' + st['task'] + '.bed', st['url'], 'dataset-file',
            'ERDA public share; retrieved 2026-11-27; byte SHA-256 recorded',
            notes='Complete artifact scanned. ERDA is mutable; the recorded byte hash identifies the inspected file.')
        c.get('sources', sid)['sha256'] = st['sha256']
        statement = (f"Complete BED has {st['rows']:,} rows; split field counts {st['split_counts']}; "
            f"coordinate spans {st['coordinate_span_min']:,}–{st['coordinate_span_max']:,} bp. ")
        if st.get('label_indices_or_classes'):
            classes = sorted(map(int, st['label_indices_or_classes']))
            statement += 'Observed label indices/classes: ' + str(classes) + '. '
        if 'clinical_labels' in st:
            statement += 'Clinical labels: ' + str(st['clinical_labels']) + '. '
        if st['task'].startswith('variant_effects'):
            statement += 'Every row is stored with split=train; the native zero-shot scorer evaluates all supplied rows, so this field is not supervised benchmark training. '
        eid = c.evidence(sid + '-review', sid,
            'Complete BED scan; data/structure-artifact-inspections.json', statement, 'data')
        bend_evidence.append(eid)
        rid = c.resource(sid + '-resource', sid, 'Original BEND ' + st['task'] + ' data',
            'dataset', 'other', st['url'], eid, revision='SHA-256 ' + st['sha256'],
            notes='Coordinates, labels where inline, and partition fields. Reference sequence is extracted separately.')
        c.collection_resource('bend-original', rid, eid)
        c.task_resource(tid, rid, eid)
        if not st['task'].startswith('variant_effects'):
            c.task_resource(tid, rid, eid, 'split-manifest', note='Actual per-row release partition membership, not a task-identity list.')
        t = c.get('tasks', tid)
        t['status'] = 'artifact-audited'
        t['input_description'] = (
            'Human genomic BED coordinate; frozen reference/alternate embeddings in the original 512-bp variant protocol.'
            if st['task'].startswith('variant_effects') else
            f"Human genomic windows spanning {st['coordinate_span_min']:,}–{st['coordinate_span_max']:,} bp in the released BED. Reference assembly and frozen embedding interface are task-specific.")
        t['limitations'] = ('Complete released coordinates, split membership and labels inspected. Underlying experimental/annotation label validity and published model scores were not independently reproduced.'
            if st['task'] not in ['gene_finding', 'enhancer_annotation'] else
            'Complete released BED and positional HDF5 labels inspected. Underlying annotation/CRISPRi label validity and published model scores were not independently reproduced.')
        c.field('tasks', tid, 'input_description', eid, 'Measured released coordinates; paper context ranges remain separately cited.')
        for split, value in st['split_counts'].items():
            c.count(tid, value, 'released BED rows', eid,
                split='evaluation (stored split=train)' if st['task'].startswith('variant_effects') else split,
                protocol=tid + '-protocol', method='measured',
                qualifier='Complete released file scan; row counts are not independently validated biological-example counts.')

        # Preserve observed consequence strata as linked variants, not new tasks.
        if st.get('consequences'):
            for consequence, value in st['consequences'].items():
                vid = tid + '-consequence-' + consequence.replace('_', '-')
                c.put('variants', dict(id=vid, task_id=tid, name='Released VEP stratum: ' + consequence,
                    dataset_revision='SHA-256 ' + st['sha256'], context='Actual released Consequence column; same binary prediction target.',
                    input_length='Original 512-bp model context', target_count=1, target_unit='binary variant label',
                    notes='A reporting stratum, not a separately held-out or independently fitted task.', evidence_id=eid))
                c.count(tid, value, 'variant rows', eid, split='released consequence stratum',
                    protocol=tid + '-protocol', variant=vid, method='measured', qualifier='Exact released Consequence value; no new genomic reannotation.')
            region_map = {'utr5': ['5_prime_UTR_variant'], 'utr3': ['3_prime_UTR_variant'],
                'intron': ['intron_variant'], 'intergenic': ['intergenic_variant'],
                'splice': [k for k in st['consequences'] if k.startswith('splice_')],
                'ncrna': ['non_coding_transcript_exon_variant', 'mature_miRNA_variant'],
                'regulatory': ['regulatory_region_variant'], 'tfbs': ['TF_binding_site_variant']}
            for feature, strata in region_map.items():
                n = sum(st['consequences'].get(s, 0) for s in strata)
                if n:
                    c.category(tid, feature, eid,
                        f'{n:,} released rows have relevant VEP consequences, recorded as linked variants. This is a subset of a heterogeneous binary variant cohort, not dense region annotation.', 'contains')
            coding = {k: v for k, v in st['consequences'].items() if k in ['missense_variant', 'synonymous_variant', 'stop_lost', 'stop_gained']}
            if coding:
                c.limit('tasks', tid, 'noncoding-eligibility', 'conflicting',
                    'The nominally noncoding release retains VEP consequence values ' + str(coding) + '. '
                    'The paper’s GENCODE-based noncoding filtering and the released VEP column therefore are not perfectly concordant. '
                    'These labels were not silently removed or treated as proof of a dedicated CDS benchmark.', eid)

        pid = tid + '-protocol'
        protocol = c.get('protocols', pid)
        protocol['selection'] = ('No fitted benchmark classifier or checkpoint selection; all supplied reference/alternate variants are scored.'
            if st['task'].startswith('variant_effects') else
            'Train the task head for 100 epochs; select the epoch maximizing the validation metric in the released trainer.')
        protocol['split_rule'] = {
            'gene_finding': 'GraphPart at 80% global mature-protein identity; 80%/10%/10% gene-instance partitions. Chromosomes can occur in multiple partitions.',
            'enhancer_annotation': 'Ten chromosome groups. For each test partition, the next partition is validation and the remaining eight are training.',
            'chromatin_accessibility': 'Test chr1/8/9; validation chr2/4; remaining released chromosomes are training.',
            'histone_modification': 'Test chr1/8/9; validation chr2/4; remaining released chromosomes are training.',
            'cpg_methylation': 'Test chr4/13/19/21; validation chr5/9/22; remaining released chromosomes are training.',
            'variant_effects_disease': 'Entire released ClinVar cohort scored without supervised fitting; stored split=train is not a model-training partition.',
            'variant_effects_expression': 'Entire released DeepSEA fold-0 variant cohort scored without supervised fitting; stored split=train is not a model-training partition.',
        }[st['task']]
        if st['task'] == 'enhancer_annotation':
            protocol['notes'] = ('Chromosome groups: 7/8/18; 10/X/13; 14/22/6; 20/3; 11/12; 19; 4/5; 15/21/2; 1/16; 17/9. '
                'Dense binary bins over a TSS-centred input. No original Evo 2 paper use is claimed.')
        readable_targets = {'chromatin_accessibility': '125 cell-type open/closed labels',
            'histone_modification': '18 experiment peak labels covering 11 histone marks',
            'cpg_methylation': 'Seven cell-line methylation states at a supplied CpG'}
        if st['task'] in readable_targets:
            t['target'] = t['output_description'] = readable_targets[st['task']]
        target_variant = c.get('variants', tid + '-targets')
        target_variant['dataset_revision'] = 'Original BEND paper / pinned release config; exact artifact hashes recorded separately'
        target_variant['notes'] = 'Gene finding has nine classes at every input base; enhancer has one binary channel over 782 bins; assay-label vectors index experiments.'
        if st['task'] != 'gene_finding':
            target_variant['input_length'] = '512 bp' if st['task'] != 'enhancer_annotation' else '100,096 bp'
        c.review('protocols', pid,
            'Original BEND context, embedding interface, task-head fitting, partition construction, checkpoint selection and metric aggregation.',
            [t['evidence_id'], eid, bend_embed, bend_build, bend_selection, bend_folds],
            'Published model scores were not rerun; current artifact counts and paper counts remain separate.')
        c.review('tasks', tid,
            'Dataset × target, dense versus window/variant output, complete release label values/shapes and coordinate/partition counts, fitting and metrics.',
            [t['evidence_id'], eid, bend_embed, bend_build, bend_labels],
            t['limitations'])

    # Resolve the earlier uninspected gene label file and maintain the paper/release distinction.
    gene_st = next(r for r in INSPECTIONS['bend_data'] if r['task'] == 'gene_finding')
    h = gene_st['label_hdf5']
    hurl = gene_st['url'].replace('.bed', '.hdf5')
    c.source('final-structure-bend-gene-labels', 'Original BEND complete gene label HDF5', hurl,
        'dataset-file', 'ERDA public share; retrieved 2026-11-27; byte SHA-256 recorded')
    c.get('sources', 'final-structure-bend-gene-labels')['sha256'] = h['sha256']
    he = c.evidence('final-structure-bend-gene-label-review', 'final-structure-bend-gene-labels',
        'All 5,977 HDF5 vectors scanned and matched row-wise to BED spans',
        'HDF5 labels contains 5,977 float64 vectors, each 1,433–13,000 entries. Every vector length equals its BED end−start span; no row mismatch. '
        'All values are integer classes 0–8. The nine-class map distinguishes strand-specific CDS, introns and donor/acceptor boundaries, with a shared noncoding class; it does not have distinct UTR or transcript-end outputs.', 'data')
    hr = c.resource('final-structure-bend-gene-label-resource', 'final-structure-bend-gene-labels',
        'Original BEND dense gene labels', 'dataset', 'other', hurl, he, revision='SHA-256 ' + h['sha256'])
    c.collection_resource('bend-original', hr, he)
    c.task_resource('bend1-gene-finding', hr, he)
    c.field('tasks', 'bend1-gene-finding', 'output_description', he)
    c.get('tasks', 'bend1-gene-finding')['target'] = 'Nine strand-aware CDS / intron / donor / acceptor / noncoding labels'
    c.get('tasks', 'bend1-gene-finding')['output_description'] = 'One of nine classes at every genomic input base; UTRs are background, not distinct labels.'
    c.get('variants', 'bend1-gene-finding-targets')['input_length'] = 'Released BED/HDF5: 1,433–13,000 bp; paper: up to 14,000 bp'
    c.get('findings', 'bend1-gene-count-discrepancy')['description'] = (
        'Paper Table 1 reports 5,976 instances and 4,780/597/597 train/validation/test (sum 5,974). Release has 5,977 BED rows: '
        '4,783 train, 597 valid, 597 test, with 5,974 distinct transcript IDs and three duplicate IDs confined to train. '
        'All 5,977 HDF5 label vectors match BED spans of 1,433–13,000 bp; the pinned embedding config adds no extra flanks. '
        'The paper reports up to 14,000 bp. Historical paper-time input artifacts are not identified by a release checksum, so reported and measured ranges/counts remain distinct.')
    bend_evidence.append(he)
    for slug, field, detail in [
        ('gene-finding', 'paper-release-cohort', 'Paper gene-instance totals, split totals and maximum context disagree with the inspected BED/HDF5; the exact paper-time artifact revision is not specified.'),
        ('accessibility', 'training-count', 'Paper: 1,354,042 train and 2,005,617 total. Release: 1,410,554 train and 2,062,129 total. Validation 279,422 and test 372,153 agree. The source does not explain the 56,512 additional training rows.'),
        ('histone', 'training-count', 'Paper: 420,713 train and 612,081 total. Release: 433,861 train and 625,229 total. Validation 70,801 and test 120,567 agree. The source does not explain the 13,148 additional training rows.'),
        ('cpg', 'target-count', 'Appendix A.1.5 says 19 outputs, while the main paper/config and actual released sparse labels use seven cell-line indices 0–6. The verified release supports seven outputs.'),
        ('disease-variant', 'paper-release-label-counts', 'Appendix A.1.7 lists 274,399 benign +21,524 pathogenic rows (295,923). Table 1 and actual release have 295,495 rows; actual labels are 274,037 benign +21,458 pathogenic. The source does not reconcile the appendix cohort to the final label counts.')]:
        evidence = he if slug == 'gene-finding' else 'final-structure-bend-data-' + slug + '-review'
        c.limit('tasks', 'bend1-' + slug, field, 'conflicting', detail, evidence)
    c.get('tasks', 'bend1-disease-variant')['description'] = (
        'Classify clinical pathogenicity from reference/alternate embedding distance. ClinVar variant_summary 2023-07-02; SNVs with at least one review star; '
        'merge likely/pathogenic and likely/benign, exclude ClinVar protein annotations and GENCODE 43 CDS/start/stop overlaps and chrM; '
        'retain VEP most-severe consequence as a reporting stratum. Actual release has 295,495 rows; no supervised benchmark split.')
    c.get('tasks', 'bend1-enhancer-annotation')['output_description'] = '782 binary 128-bp enhancer bins per 100,096-bp window; one channel, not 782 assays.'
    enhancer_source = c.get('sources', 'bend1-enhancer-annotation-label-file')
    er = c.resource('final-structure-bend-enhancer-label-resource', enhancer_source['id'],
        'Original BEND dense enhancer labels', 'dataset', 'other', enhancer_source['url'],
        'bend1-enhancer-annotation-label-file-inspection', revision='SHA-256 ' + INSPECTIONS['bend_enhancer_labels']['sha256'])
    c.task_resource('bend1-enhancer-annotation', er, 'bend1-enhancer-annotation-label-file-inspection')
    c.collection_resource('bend-original', er, 'bend1-enhancer-annotation-label-file-inspection')
    br = c.resource('final-structure-bend-code-resource', 'final-structure-bend-readme',
        'Original BEND pinned evaluation implementation', 'evaluation-code', 'github',
        'https://github.com/frederikkemarin/BEND/tree/' + INSPECTIONS['repositories']['BEND']['revision'], bend_readme,
        revision=INSPECTIONS['repositories']['BEND']['revision'])
    c.collection_resource('bend-original', br, bend_readme, 'evaluation-code')
    for tid in task_slugs.values():
        c.task_resource('bend1-' + tid, br, bend_readme, 'evaluation-code')
    c.get('evaluations', 'bend-original').update(
        status='artifact-audited', scope_note='Seven original BEND dataset × target tasks. All released BEDs and both dense-label HDF5 files inspected; paper-time and current release counts retained separately.',
        notes='Frozen embedding heads for five tasks; whole-cohort embedding-distance scores for two variant tasks. Dense class tracks, dense enhancer bins and window-level assay vectors are distinct outputs.')
    c.get('sources', 'project-paper-bend-original')['notes'] = 'Main task definitions, Appendix A.1/A.6/A.7 and linked current release artifacts reviewed; numerical model results not independently reproduced.'
    c.review('evaluations', 'bend-original',
        'Original seven-task framework, full release coordinates/partition fields/labels, readout shape, fitting, model interface, metrics and paper/release discrepancies.',
        bend_evidence + ['bend1-gene-method', 'bend1-enhancer-method', 'bend1-chromatin-method', 'bend1-histone-method', 'bend1-cpg-method', 'bend1-expression-method', 'bend1-disease-method'],
        'Mutable ERDA artifacts are identified by SHA-256; original paper-time artifacts have no verified immutable revision. Underlying assay truth and published model scores were not revalidated.')
    c.review('papers', 'bend-original',
        'Main seven task definitions; Appendix A.1 composition/eligibility, A.6 token upsampling and A.7 task fitting/scoring; linked artifact reconciliation.',
        bend_evidence,
        'Reported values are preserved alongside complete current release measurements; paper/release disagreements are explicit source limits.')

    # SpliceAI source release includes inference weights and annotations, not an
    # automatically accessible copy of every original benchmark table.
    splice1 = code('SpliceAI', 'README.md', 'spliceai-readme',
        'Pinned release includes five Keras models, GRCh37/38 annotation tables and an inference interface. The current BaseSpace share supplies precomputed predictions. '
        'The paper identifies a different original BaseSpace share for training/testing data and RNA-seq validation results.', 1, 19)
    splice2 = code('SpliceAI2', 'README.md', 'spliceai2-readme',
        'Native SpliceAI2 supplies site, junction and transcript-path interfaces. The public source repository contains no benchmark TSV or per-gene split manifest. '
        'The two-model multispecies release and precomputed scores are distinct from the human-only top-transcript and tissue-conditioned experiments.', 1, 20)
    weight_url = ('https://github.com/Illumina/SpliceAI/tree/' +
        INSPECTIONS['repositories']['SpliceAI']['revision'] + '/spliceai/models')
    c.source('final-structure-spliceai-weight-inventory', 'SpliceAI bundled model artifacts',
        weight_url, 'model-file-inventory', INSPECTIONS['repositories']['SpliceAI']['revision'],
        notes='All five local HDF5 model files opened; hashes and architecture/weight-array metadata are in data/structure-artifact-inspections.json. Inference was not rerun.')
    weights = c.evidence('final-structure-spliceai-weight-review', 'final-structure-spliceai-weight-inventory',
        'Five complete bundled HDF5 model/configuration inspections',
        'The pinned package contains five distinct 3,131,720-byte Keras HDF5 model files. Each has an embedded model configuration and 206 weight arrays. '
        'These are predictor weights, not original benchmark labels or per-example evaluation manifests.', 'data')
    c.put('model_properties', dict(id='spliceai-release', model_id='spliceai', category='release',
        name='Bundled predictor and original data release', variant=None,
        value='Five bundled HDF5 predictors and GRCh37/38 annotation tables in the pinned GitHub release. The original paper separately names a BaseSpace share for benchmark data.',
        status='reported / source-audited', evidence_id=weights,
        notes='Model files and configurations inspected; exact original benchmark tables remain a separate data resource.'))

    # This omitted paper panel assesses association with measured chromatin,
    # rather than accuracy of splicing labels or transcript reconstruction.
    nuc = c.evidence('spliceai-nucleosome-method', 'spliceai-paper',
        'Role of nucleosomes in splicing; enrichment at novel exons; PDF pages 19–20; Fig. 1G/H and S2E/F',
        'At one million random intergenic positions at least 100 kb from canonical genes, insert donor/acceptor/branch-point/poly-pyrimidine motifs '
        'to define a potential 150-nt exon, then correlate the mean predicted acceptor/donor score with K562 nucleosome signal averaged over 50 nt; stratify GC in 0.02 bins. '
        'A second arm relates 14,289 held-out donors and 14,289 acceptors to exon-side/intron-side nucleosome signal. '
        'A selected 128-site private cryptic-gain arm compares mean shifted K562/GM12878 profiles against 1,000 matched-size sets of low-score singleton variants, using an empirical p-value. '
        'These are model-response/chromatin associations, not measured outcomes of the synthetic motif edits.',
        url=c.get('sources', 'spliceai-paper')['url'] + '#page=20')
    tid = 'spliceai-nucleosome-association'
    c.put('tasks', dict(id=tid, name='SpliceAI: nucleosome association diagnostics',
        dataset_name='UCSC K562 / GM12878 nucleosome signals and human genomic positions',
        target='Association of splice-score responses with nucleosome positioning',
        description='Compare model-defined potential exon/site scores and selected cryptic-gain loci with measured nucleosome signals; retain intergenic, annotated-site and selected-variant arms separately.',
        task_type='association analysis', label_basis='Experimental nucleosome signal; synthetic motif placements and model-ascertained locus selection are not splicing truth.',
        status='paper-audited', evidence_id=nuc,
        limitations='Selected interpretation experiment; no supervised nucleosome predictor or independently measured splicing response to the synthetic edits. Exact sampled positions and UCSC track identifiers are not specified in the paper.',
        input_description='Human genomic DNA with synthetic motif insertions, held-out annotated splice sites, or selected GTEx singleton loci; SpliceAI-10k and native SpliceAI-80nt comparison.',
        output_description='Scalar model response versus measured nucleosome signal, plus selected-cohort enrichment summaries.'))
    for feature in ['genome', 'intergenic', 'exon', 'splice']:
        c.category(tid, feature, nuc, 'The cited diagnostic explicitly samples this sequence context; these are not dense splicing truth labels.', 'contains')
    for capability in ['interpretability', 'model-development']:
        c.category(tid, capability, nuc, 'Source-defined model-response association and controlled-context analysis.')
    c.population(tid, 'human', nuc, 'Human reference/GTEx positions and human-cell-line nucleosome signal; not the model training-species panel.')
    c.output(tid, 'isolated', nuc, 'Scalar sequence/site response and cohort nucleosome-association statistic',
        'Sampled genomic locus or selected cohort', limitations='Averaged signal curves summarize cohorts; they are not dense predicted nucleosome tracks or isoform labels.')
    c.member(tid, 'spliceai-evals', nuc, note='Original paper exploratory association diagnostic, distinct from splice-site truth and isoform reconstruction.')
    c.put('metrics', dict(id='empirical-p', name='Empirical p-value',
        definition='Tail fraction under the source-defined resampled null; not a predictive-accuracy score.', direction='context-dependent'))
    for slug, name, split, metrics, count, unit in [
        ('intergenic', 'Synthetic exon score versus K562 nucleosome signal',
            'One million randomly sampled intergenic positions at least 100 kb from canonical genes; no downstream supervised fitting or independent nucleosome test split. GC strata use width 0.02.',
            [('spearman', 'Across one million sampled positions, overall and within GC strata.')], 1000000, 'sampled intergenic positions'),
        ('annotated-sites', 'Annotated splice scores versus nucleosome enrichment',
            'Original 14,289 held-out coding-gene donor–acceptor pairs; correlate plotted/smoothed native scores with exon-side/intron-side signal ratio. Not a fitted nucleosome task.',
            [('effect-size-trend', 'Score/enrichment trend at held-out donor/acceptor sites; 2,500-position smoothing as in the exon-length analysis.')], 14289, 'held-out donor–acceptor pairs'),
        ('selected-gains', 'Nucleosome enrichment at selected private cryptic gains',
            '128 model-selected private cryptic gain sites in singleton carriers, at least 750 nt from annotated exons; compare with 1,000 sets of 128 low-score singleton loci (delta score <0.01). Not an unselected variant test.',
            [('empirical-p', 'Fraction of 1,000 null sets with central averaged signal at least as high as the 128 selected sites.')], 128, 'selected gain sites')]:
        vid = tid + '-' + slug
        c.put('variants', dict(id=vid, task_id=tid, name=name,
            dataset_revision='Original Cell 2019 methods; exact UCSC track versions not reported',
            context='Related diagnostic arm; same measured nucleosome-association target.',
            input_length='SpliceAI-10k symmetric flanks; SpliceAI-80nt comparison for annotated sites',
            target_count=1, target_unit='nucleosome signal/association', notes=split, evidence_id=nuc))
        pid = 'spliceai-' + vid + '-protocol'
        c.protocol(pid, tid, name, 'native supervised predictor; no diagnostic readout fitting',
            'Model splice probabilities selected at source-defined motif/site positions; compare with measured nucleosome signal.',
            split, 'sampled locus / splice site / selected variant cohort', nuc, metrics,
            fitted='None; no nucleosome prediction head', selection='Source-defined random positions or explicitly model-ascertained loci.', variant=vid)
        c.count(tid, count, unit, nuc, protocol=pid, variant=vid,
            qualifier='Paper-reported diagnostic cohort, not experimentally validated splicing edits.')
        c.use(tid, 'spliceai', 'spliceai', nuc, pid)
    c.limit('tasks', tid, 'nucleosome-track-identifiers', 'not-reported',
        'The methods name K562/GM12878 nucleosome signals downloaded from UCSC but do not provide exact track accessions, versions or a sampled-coordinate manifest.', nuc)

    # The native exon/intron-length response shares the existing held-out-site
    # model-response target, with its own unedited input cohort and denominator.
    length_e = c.evidence('spliceai-length-response-method', 'spliceai-paper',
        'Role of exon and intron lengths in splicing; PDF page 19; Fig. 1F',
        'Remove first/last test-set exons, leaving 12,637 internal exons from 14,289 intervals. Compare mean acceptor/donor scores from SpliceAI-80nt and SpliceAI-10k versus exon length, with a 2,500-position averaging window. '
        'The intron-length arm retains 14,289 intervals. This is a native model-score response diagnostic, not measured outcomes after changing exon or intron length.',
        url=c.get('sources', 'spliceai-paper')['url'] + '#page=19')
    mt = c.get('tasks', 'spliceai-motif-perturbation')
    mt['name'] = 'SpliceAI: sequence and context response diagnostics'
    mt['dataset_name'] = 'Held-out GENCODE splice sites with controlled motif or native length strata'
    mt['description'] = 'Study motif placement and native exon/intron-length effects on predicted site scores. Experimental outcomes for the inserted motifs or changed lengths are not measured.'
    mt['target'] = 'Splice-score response to motif position or exon/intron context'
    for feature in ['exon', 'intron']:
        c.category(mt['id'], feature, length_e, 'Known exon/intron intervals define length-response reporting strata.', 'contains')
    vid = 'spliceai-native-length-response'
    c.put('variants', dict(id=vid, task_id=mt['id'], name='Native exon/intron-length response',
        dataset_revision='Original GENCODE V24lift37 test transcripts', context='Unedited natural intervals, unlike synthetic motif-placement arm.',
        input_length='SpliceAI-80nt versus SpliceAI-10k flanking-context architectures', target_count=1,
        target_unit='native splice-score response', notes='12,637 internal exons; 14,289 introns; plotted/smoothed score trends, not experimental length-edit labels.', evidence_id=length_e))
    pid = 'spliceai-native-length-response-protocol'
    c.protocol(pid, mt['id'], 'Native exon/intron-length response', 'native supervised predictors; no diagnostic readout fitting',
        'Mean acceptor/donor probability at known boundaries; compare separately trained 80-nt and 10-kb context architectures.',
        'Use original held-out transcript intervals; exclude first/last exons for the exon-length arm. No newly fitted benchmark head.',
        'known exon/intron interval', length_e, [('effect-size-trend', 'Predicted score versus length; 2,500-position smoothing.')], variant=vid)
    c.count(mt['id'], 12637, 'internal exons', length_e, protocol=pid, variant=vid)
    c.count(mt['id'], 14289, 'introns', length_e, protocol=pid, variant=vid)
    c.use(mt['id'], 'spliceai', 'spliceai', length_e, pid)
    for model, eid in [('spliceai', splice1), ('spliceai2', splice2)]:
        repo = 'SpliceAI' if model == 'spliceai' else 'SpliceAI2'
        revision = INSPECTIONS['repositories'][repo]['revision']
        sid = 'final-structure-' + model + '-readme'
        rid = c.resource('final-structure-' + model + '-code-resource', sid,
            repo + ' pinned inference/training implementation', 'evaluation-code', 'github',
            f'https://github.com/Illumina/{repo}/tree/{revision}', eid, revision=revision)
        c.collection_resource(model + '-evals', rid, eid, 'evaluation-code')
        for member in [r for r in d['evaluation_tasks'] if r['evaluation_id'] == model + '-evals']:
            c.task_resource(member['task_id'], rid, eid, 'evaluation-code', variant=member['variant_id'])

    c.source('final-structure-spliceai-original-share', 'SpliceAI original paper data share',
        'https://basespace.illumina.com/s/5u6ThOblecrh', 'data-portal', 'Paper link; inspected 2026-11-27',
        notes='HTTP 200 returns a JavaScript application shell without a file inventory; individual benchmark archives were not retrieved.')
    original = c.evidence('final-structure-spliceai-original-data-review', 'spliceai-paper',
        'Data and software availability; PDF page 30',
        'The original paper declares training/testing data, RNA-seq validation results/junctions and precomputed scores at BaseSpace share 5u6ThOblecrh. '
        'The current package README links a different score share, otSPW8hnhaZR. Direct requests to both return application HTML, not an exposed benchmark file inventory.',
        url=c.get('sources', 'spliceai-paper')['url'] + '#page=30')
    spr = c.resource('final-structure-spliceai-original-data-resource', 'final-structure-spliceai-original-share',
        'SpliceAI original training/test and validation data share', 'dataset', 'other',
        'https://basespace.illumina.com/s/5u6ThOblecrh', original,
        revision='Original paper share identifier', availability='not-retrieved',
        notes='Paper-declared public release; file inventory/row data were not exposed by the returned application shell.')
    c.collection_resource('spliceai-evals', spr, original)

    lclurl = 'https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-7351'
    c.source('final-structure-spliceai-lcl-study', 'SpliceAI LCL RNA-seq: E-MTAB-7351',
        lclurl, 'study-metadata', 'E-MTAB-7351; released 2018-11-25')
    c.get('sources', 'final-structure-spliceai-lcl-study')['sha256'] = INSPECTIONS['spliceai_lcl_study']['metadata_sha256']
    lcle = c.evidence('final-structure-spliceai-lcl-study-review', 'final-structure-spliceai-lcl-study',
        'BioStudies primary study metadata',
        'E-MTAB-7351 is titled RNA-seq of 36 individuals with autism spectrum disorder. It is the original LCL RNA-seq deposit named by the SpliceAI paper. '
        'Raw sequencing metadata are not a processed validation-label table and do not make 36 patients equivalent to the paper’s 28 assessable-patient denominator.', 'data')
    lr = c.resource('final-structure-spliceai-lcl-rna-resource', 'final-structure-spliceai-lcl-study',
        'SpliceAI original LCL RNA-seq deposit', 'dataset', 'other', lclurl, lcle, revision='E-MTAB-7351',
        notes='Primary raw sequencing study; public metadata inspected, raw reads not rescanned.')
    c.task_resource('spliceai-lcl-validation', lr, lcle, 'upstream-data')
    c.collection_resource('spliceai-evals', lr, lcle, 'upstream-data')

    # Exact HF benchmark artifacts are listed publicly but gated file downloads
    # return 401. These are restricted datasets, not missing inferred releases.
    hf = INSPECTIONS['spliceai2_huggingface']['dataset']
    revision = hf['revision']
    hurl = f'https://huggingface.co/datasets/illumina-ai/SpliceAI2-data/tree/{revision}/benchmarks'
    c.source('final-structure-spliceai2-benchmark-release', 'SpliceAI2 released benchmark file inventory',
        hurl, 'dataset-repository', revision,
        notes='Public API inventory and root README inspected; each benchmark TSV and benchmark README request returned HTTP 401. No gated terms were accepted.')
    hfe = c.evidence('final-structure-spliceai2-benchmark-release-review', 'final-structure-spliceai2-benchmark-release',
        'Pinned complete file inventory, root README and recorded download responses',
        'The benchmark release contains GTEx_GTAG.tsv, GTEx_sQTL.tsv and OpenSplice_MPRA.tsv. The root card explicitly calls benchmarks evaluation datasets. '
        'Public metadata marks access gated; direct pinned requests for the three TSVs and benchmarks/README.md return 401. '
        'The complete inventory has no dominant-transcript, tissue/disease junction, GEL or UKB benchmark table. Precomputed whole-genome prediction files are separate from benchmark truth.', 'documentation')
    benchmark_tasks = {'GTEx_GTAG.tsv': ['spliceai2-gtag-detection', 'spliceai2-gtag-usage'],
        'GTEx_sQTL.tsv': ['spliceai2-sqtl-detection', 'spliceai2-sqtl-effect'],
        'OpenSplice_MPRA.tsv': ['bend-opensplice']}
    for filename, tasks in benchmark_tasks.items():
        url = f'https://huggingface.co/datasets/illumina-ai/SpliceAI2-data/blob/{revision}/benchmarks/{filename}'
        rid = c.resource('final-structure-spliceai2-data-' + filename.removesuffix('.tsv').lower(),
            'final-structure-spliceai2-benchmark-release', 'SpliceAI2 benchmark: ' + filename,
            'dataset', 'huggingface', url, hfe, revision=revision, availability='restricted',
            notes='Exact released file identity verified. Gated file bytes, column schema and rows were not read.')
        c.collection_resource('spliceai2-evals', rid, hfe)
        for tid in tasks:
            c.task_resource(tid, rid, hfe, variant='spliceai2-opensplice-snv' if tid == 'bend-opensplice' else None)
            c.limit('protocols', 'spliceai2-' + tid + '-protocol', 'released-benchmark-rows', 'access-restricted',
                'The exact HF benchmark file ' + filename + ' exists at the pinned revision, but downloading it returned HTTP 401. '
                'Paper-reported cohort counts and eligibility are retained; no row-level recount or equivalence to another OpenSplice release is claimed.', hfe)
    c.get('model_properties', 'spliceai2-release')['value'] = (
        'Source code and two gated multispecies 13M checkpoints inspected by public metadata. A separate gated HF data release lists exact GTEx GT/AG, GTEx sQTL and OpenSplice benchmark TSVs; their file downloads returned HTTP 401.')
    c.get('model_properties', 'spliceai2-release')['notes'] = (
        'The public model inventory contains only two multispecies checkpoints; human-only and tissue-conditioned checkpoint identities are not present in that inspected release. '
        'Paper benchmark totals remain reported counts, not measured rows.')
    c.get('model_properties', 'spliceai2-release')['evidence_id'] = hfe
    c.field('models', 'spliceai2', 'release', hfe)

    c.source('final-structure-spliceai2-controlled-data', 'SpliceAI2 controlled cohort access statements',
        c.get('sources', 'spliceai2-paper')['url'] + '#page=48', 'paper-section', 'Preprint v1')
    controlled = c.evidence('final-structure-spliceai2-controlled-data-review', 'spliceai2-paper',
        'Acknowledgements and Data and code availability; PDF pages 47–49',
        'The authors identify GTEx dbGaP phs000424.v9.p2, UK Biobank application 33751 and Genomics England project 754. '
        'NGRL variants, RNA-seq and clinical/panel data remain in the secure Genomics England Research Environment under approved researcher/project access. '
        'The published GEL validation totals are not a public per-variant benchmark manifest.',
        url=c.get('sources', 'spliceai2-paper')['url'] + '#page=48')
    gelr = c.resource('final-structure-gel-data-resource', 'final-structure-spliceai2-controlled-data',
        'Genomics England NGRL: restricted study cohorts', 'dataset', 'other',
        'https://www.genomicsengland.co.uk/research', controlled, availability='restricted',
        notes='Source data remain in the secure research environment; this is an access portal, not a public benchmark download.')
    for tid in ['spliceai2-gel-gtag', 'spliceai2-gel-panel', 'spliceai2-gel-rna']:
        c.task_resource(tid, gelr, controlled, 'upstream-data')
        c.limit('tasks', tid, 'participant-level-data', 'access-restricted',
            'NGRL variants, RNA-seq and clinical data are available only through the approved secure Genomics England environment. '
            'The public HF inventory does not include this GEL benchmark cohort.', controlled)
    c.collection_resource('spliceai2-evals', gelr, controlled, 'upstream-data')

    # Entity-specific review proofs and field-specific source limits replace
    # previous generic statements that suggested unfinished future work.
    for collection, model, release_evidence in [('spliceai-evals', 'spliceai', [splice1, original, lcle, weights]),
                                               ('spliceai2-evals', 'spliceai2', [splice2, hfe, controlled])]:
        paper_source = model + '-paper'
        paper_evidence = [e['id'] for e in d['evidence'] if e['source_id'] == paper_source]
        for member in [r for r in d['evaluation_tasks'] if r['evaluation_id'] == collection]:
            tid = member['task_id']
            if not tid.startswith(model + '-'):
                # OpenSplice's task belongs to a separately reviewed dataset;
                # only the SpliceAI2 protocol/resource variant is owned here.
                continue
            t = c.get('tasks', tid)
            eid = t['evidence_id']
            if tid not in ['spliceai2-top-transcript', 'spliceai-nucleosome-association']:
                t['limitations'] = ('Original paper methods define the target, eligibility and readout. The declared BaseSpace data share returned application HTML; its per-example tables were not retrieved.'
                    if model == 'spliceai' else
                    'Paper-specific target, eligibility and readout; exact cohort availability is recorded in linked resources and source limits. Multispecies training does not establish evaluation in all training species.')
            c.review('tasks', tid,
                'Paper methods and figures for this dataset × target: assay/annotation truth, eligibility, counts/units, fitting, partition construction, native readout versus dense/linked structure, and released resource identity.',
                [eid] + release_evidence,
                t['limitations'])
            for p in [r for r in d['protocols'] if r['task_id'] == tid and r['id'].startswith(model + '-')]:
                c.review('protocols', p['id'],
                    'Source-defined supervised model use or adaptation, context/candidate/threshold selection, cohort partition and metric aggregation for this task.',
                    [p['source_evidence_id']] + release_evidence,
                    'Source-reviewed protocol; published model inference and statistical results were not independently rerun.')
            if model == 'spliceai':
                c.task_resource(tid, spr, original,
                    note='Original paper-declared dataset share; actual file inventory/rows not retrieved.')
                c.limit('tasks', tid, 'original-release-tables', 'not-retrieved',
                    'The original paper declares data at BaseSpace share 5u6ThOblecrh. Requests return a JavaScript application shell rather than file identities or data. '
                    'The specific filtered benchmark table was therefore not read; the paper-defined task remains fully represented.', original)
            elif tid not in {x for tasks in benchmark_tasks.values() for x in tasks} and not tid.startswith('spliceai2-gel-'):
                c.limit('tasks', tid, 'public-cohort-manifest', 'not-released',
                    'No task-specific sequence/label/coordinate manifest for this experiment is included in the inspected complete SpliceAI2 GitHub tree or HF benchmark inventory. '
                    'This statement concerns those releases; upstream study data may have separate public or controlled access.', hfe)
        c.review('evaluations', collection,
            'All original model-paper dataset × target tasks, source-specific cohort/selection units, fitting and metric definitions, dense versus isolated/structured outputs, primary code and actual released-data inventory.',
            paper_evidence + release_evidence,
            'Original-paper use and later external comparisons remain separate. Public code, restricted data and source-reported numerical cohorts are identified explicitly.')
        c.review('models', model,
            'Supervised architecture/input representation, training labels and species, context/output sizes, ensemble and native versus benchmark-selected readout, public code/weight inventory.',
            paper_evidence + release_evidence,
            'Specialist supervised predictor; no self-supervised pretraining corpus is inferred. Published assay scores were not reproduced.')
        c.review('papers', model,
            'Complete article/manuscript including methods and available supplemental/extended-data figures; task decomposition, model protocols, eligibility/units, external comparisons and data availability.',
            paper_evidence + release_evidence,
            'Access-limited participant/benchmark data remain distinct from completion of the paper and release-source review.')

    for tid in ['spliceai2-sf3b1', 'spliceai2-dm1']:
        c.limit('tasks', tid, 'disease-specific-split', 'not-reported',
            'The disease-context methods report evaluation on held-out genes, but do not separately specify a disease-specific coordinate manifest or an independent participant holdout. '
            'Source patient counts are not substituted for scored junction counts.', 'spliceai2-disease-context-method')
    c.limit('tasks', 'spliceai2-top-transcript', 'independent-third-test', 'not-reported',
        'The 352-gene benchmark uses human chr21/22, which are also the stated validation chromosomes. The paper does not specify a separate third chromosome/gene partition for this comparison.',
        'spliceai2-top-transcript-method')
    c.limit('models', 'spliceai2', 'specialist-checkpoints', 'not-released',
        'The inspected public HF model inventory contains two multispecies 13M checkpoints; no human-only top-transcript or tissue-conditioned checkpoint appears in that release.',
        'spliceai2-release-inspection')
    # The paired OpenSplice protocol has its own target owner, but is fully reviewed here.
    c.review('protocols', 'spliceai2-bend-opensplice-protocol',
        'Original SpliceAI2 OpenSplice SNV eligibility, native delta-PSI readout, global Spearman, reported count and exact gated HF benchmark resource.',
        ['spliceai2-opensplice-method', hfe, 'opensplice-canonical-readout'],
        'Gated HF TSV not read; no equivalence to the BEND 2.0 released subset or aggregation is assumed.')
    for table, entity, extra in [
        ('tasks', 'bend1-gene-finding', [he, bend_labels]),
        ('tasks', 'bend1-enhancer-annotation', ['bend1-enhancer-annotation-label-file-inspection']),
        ('tasks', 'spliceai-motif-perturbation', [length_e])]:
        review = next(r for r in d['source_reviews'] if r['entity_table'] == table and r['entity_id'] == entity)
        review['evidence_ids_json'] = json.dumps(sorted(set(json.loads(review['evidence_ids_json']) + extra)))
    c.field('tasks', 'spliceai-motif-perturbation', 'description', length_e,
        'Native length-response arm retained as a linked diagnostic variant.')
    c.get('evidence', 'spliceai2-release-inspection')['statement'] = (
        'The complete inspected model file inventory lists two multispecies 13M checkpoints, without human-only top-transcript or tissue-conditioned checkpoints. '
        'Weight bytes were not downloaded. A separate HF data repository contains three gated benchmark TSVs, whose identities and access limits are documented separately.')
    c.get('model_properties', 'spliceai2-release')['name'] = 'Released artifacts'
    c.get('evaluations', 'spliceai-evals')['description'] = (
        'Dense reference splice-site labels, exon inclusion, variant outcomes, clinical validation and sequence/nucleosome response diagnostics from the original Cell 2019 paper.')
    c.get('evaluations', 'spliceai-evals')['scope_note'] = (
        'Eleven dataset × target tasks; native length and nucleosome diagnostic arms are linked variants. Dense site labels, selected responses and transcript illustrations have different scoring semantics.')
    c.get('evaluations', 'spliceai2-evals')['scope_note'] = (
        'Model-associated experiments; dominant transcript structure, variant assays and tissue/disease/cohort associations remain separate targets. '
        'Exact HF benchmark files are linked with their actual gated access; controlled clinical data are identified separately.')
    for tid, text in [
        ('bend1-gene-finding', 'Dense CDS/intron/splice/background labels and base-level MCC; UTRs are not distinct output classes and transcript chains are not matched.'),
        ('bend1-enhancer-annotation', 'Sparse experimental positives become a dense binary 128-bp track; unlabelled bins are not exhaustively disproven enhancers.'),
        ('spliceai-sites-coding', 'Dense site labels; top-k uses the known number of sites. Junction pairing, complete transcript ends and all-isoform recovery are not scored.'),
        ('spliceai-sites-linc', 'Annotation- and read-support-filtered lincRNA panel; dense site detection does not establish full lincRNA isoform reconstruction.'),
        ('spliceai2-top-transcript', 'Exact dominant internal splice pattern in 352 genes, restricted to first-to-last junction ±10 bp. TSS/TES and all-isoform recall or abundance are not evaluated.')]:
        c.get('task_outputs', tid + '-output-review')['limitations'] = text
    # Keep the new output assignment's insertion position stable on repeated use.
    new_output = [r for r in d['task_categories'] if r['task_id'] == 'spliceai-nucleosome-association' and r['category_id'] == 'output-isolated']
    d['task_categories'] = [r for r in d['task_categories'] if r not in new_output] + new_output
    return d
