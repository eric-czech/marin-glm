"""Task-level review of Evo 2 SAE evaluation methods and released examples.

Annotation-guided feature search, regional discrimination, dense base scoring and
internal perturbation diagnostics have separate protocol/output records. An SAE
is a fitted readout on a frozen backbone, even when fitted without target labels.
"""
import copy
import json
from common import Catalogue, ROOT, DATE
from evo2_review import REV, REPO, CACHE, PAPER, SUPP, SD_BASE


def populate(d, inspected=None):
    c = Catalogue(d)
    if inspected is None:
        manifest = ROOT / 'data/evo2-artifact-inspections.json'
        if not manifest.exists():
            manifest = ROOT / CACHE / 'artifact-inspections.json'
        inspected = json.loads(manifest.read_text())

    def method(slug, section, page, text):
        return c.evidence('evo2-sae-' + slug, 'evo-supp', section + '; PDF page ' + str(page), text,
            url=SUPP + '#page=' + str(page))

    def figure(slug, number, locator, text):
        sid = 'evo2-sae-figure-' + str(number)
        c.source(sid, 'Evo 2 figure ' + str(number), PAPER + '/figures/' + str(number), 'figure',
            'Nature 2026', CACHE + 'fig' + str(number) + '.jpg',
            notes='Complete high-resolution figure visually inspected, including feature identifiers, metric labels and source-scored units.')
        return c.evidence('evo2-sae-' + slug, sid, locator, text, 'paper')

    def variant(tid, suffix, name, evidence, context, n=None, unit=None, notes=''):
        vid = tid + '-' + suffix
        c.put('variants', dict(id=vid, task_id=tid, name=name, evidence_id=evidence, context=context,
            dataset_revision='Evo 2 Nature 2026 Supplement A.4', target_count=n, target_unit=unit,
            input_length=None, notes=notes))
        return vid

    trained = method('training', 'A.4.1–A.4.2', 19,
        'Frozen Evo 2 7B after 262,144-context extension supplies residual activations after block 26. BatchTopK SAE expands 4,096 activations to 32,768 latents with k=64. '
        'The mixed SAE trains on one billion shuffled activations from 16,384-nt chunks drawn from 2,752 complete representative GTDB 220 genomes and genic regions of 16 eukaryotic species. '
        'The eukaryotic-only SAE uses the same architecture/training recipe with one billion activations from the eukaryotic subset. '
        'Adam learning rate 5e-5, batch 16,384, one epoch, five-percent ramp-up/down. Biological labels subsequently guide feature selection, so target-label-free SAE fitting does not make every reported feature evaluation independent of labels.')
    release = c.evidence('evo2-sae-release-scope', 'evo2-diagnostic-release-inventory',
        'Complete pinned official repository and SAE inference notebook',
        'The official SAE notebook releases a feature-extraction and plotting example with the mixed SAE and Evo 2 7B 262k backbone. '
        'It loads Goodfire/Evo-2-Layer-26-Mixed and exposes matching E. coli and human feature IDs. '
        'It does not supply original 100-genome prophage windows, complete region-score tables, the three human mutation-subset manifests, 50,000-promoter coordinates, '
        '50 human feature-selection segments, 1,000 scored genes, or original feature-ablation input/score arrays.', 'code',
        f'https://github.com/ArcInstitute/evo2/blob/{REV}/notebooks/sparse_autoencoder/sparse_autoencoder.ipynb')
    # The source path is verified from the actual immutable tree, rather than a
    # guessed code/data link; no claim that this example implements every metric.
    notebook = next(p for p in inspected['sae']['repository_paths'] if p.endswith('sparse_autoencoder.ipynb'))
    codeurl = f'https://github.com/ArcInstitute/evo2/blob/{REV}/{notebook}'
    c.get('evidence', release)['url'] = codeurl
    c.source('evo2-sae-notebook', 'Evo 2 released SAE feature extraction example', codeurl,
        'repository-file', REV, REPO + notebook)
    code_e = c.evidence('evo2-sae-notebook-implementation', 'evo2-sae-notebook',
        'BatchTopKTiedSAE, model/checkpoint loading, get_feature_ts, selected feature plots',
        'Notebook implements a tied SAE with ReLU and global batch TopK, loads the mixed expansion-eight k64 weights and Evo 2 7B 262k, '
        'and plots selected features. Human features 15680/28339/1050/25666 and bacterial ORF/RNA/intergenic features match the reported identifiers. '
        'It contains feature plotting rather than the complete original held-out assay evaluators.', 'code')
    code_resource = c.resource('evo2-sae-code-resource', 'evo2-sae-notebook', 'SAE feature extraction and plotting example',
        'evaluation-code', 'github', codeurl, code_e, revision=REV,
        notes='Released computational interface; original paper-wide labelled cohorts and exact metric implementations are separate and not included.')
    c.collection_resource('evo-original', code_resource, code_e, 'evaluation-code')
    weight_rev = inspected['sae']['mixed_checkpoint']['sha']
    c.source('evo2-sae-mixed-weights', 'Goodfire mixed Evo 2 SAE checkpoint card and inventory',
        'https://huggingface.co/Goodfire/Evo-2-Layer-26-Mixed/tree/' + weight_rev,
        'model-release', weight_rev, CACHE + 'Evo-2-Layer-26-Mixed-README.md',
        notes='Public card and full file inventory inspected. Tensor values not downloaded. Only this mixed Evo checkpoint appears in the inspected public Goodfire Evo model list.')
    weights = c.evidence('evo2-sae-mixed-weights-scope', 'evo2-sae-mixed-weights', 'Pinned model card and public file inventory',
        'The public mixed SAE release contains sae-layer26-mixed-expansion_8-k_64.pt and identifies itself as the mixed prokaryote/eukaryote SAE used in the paper. '
        'It is a model checkpoint, not an evaluation dataset. The public Goodfire Evo model listing does not expose an eukaryotic-only SAE checkpoint.', 'documentation')
    c.field('models', 'evo2', 'SAE readout release', weights)
    c.limit('models', 'evo2', 'eukaryotic-only-sae-checkpoint', 'not-released',
        'A.4.1 defines an eukaryotic-only SAE and A.4.6–7 use it. The inspected public Goodfire listing exposes only the mixed SAE; the official notebook loads only mixed weights. No exact public eukaryotic-only checkpoint is identified.', weights)
    c.put('categories', dict(id='prophage', dimension='region', name='Prophage regions',
        definition='Integrated bacteriophage regions explicitly supplied or labelled by the task source. Not synonymous with repetitive DNA.', accommodation=None))
    metrics = [
        ('feature-response', 'SAE feature activation response', 'Source-defined mean or per-position SAE activation after controlled sequence perturbation; no experimental phenotype target.', 'descriptive'),
        ('cross-entropy-change', 'Cross-entropy change after feature ablation', 'Difference or ratio of next-token cross-entropy after setting a selected SAE latent to zero and reconstructing the backbone activation; not biological effect size.', 'descriptive')]
    for id, name, definition, direction in metrics:
        c.put('metrics', dict(id=id, name=name, definition=definition, direction=direction))

    def add(tid, name, dataset, target, description, evidence, features, output, form, unit,
            split, metrics, populations, selection, notes='', axis='none', structure='none', adaptation=None,
            task_type='binary discrimination', label_basis='Reference genomic annotations', input_description=None):
        c.put('tasks', dict(id=tid, name=name, dataset_name=dataset, target=target, description=description,
            task_type=task_type, label_basis=label_basis, evidence_id=evidence, status='paper-audited',
            limitations=notes, input_description=input_description or 'Frozen Evo 2 sequence embeddings processed through a fitted SAE; source-defined feature selected using annotations',
            output_description=form))
        c.member(tid, 'evo-original', evidence, note='Original Evo 2 mechanistic-interpretability evaluation; selected SAE features are distinct from a generally trained genome annotator.')
        for cat in ['interpretability', 'embedding-analysis'] + features:
            c.category(tid, cat, evidence, 'The task source defines the specific feature/target and scored output. SAE fitting and annotation-guided feature selection are recorded separately.')
        c.output(tid, output, evidence, form, unit, axis=axis, structure=structure,
            rationale=description, limitations=notes)
        if 'cds' in features:
            c.put('task_feature_scopes', dict(id=tid + '-cds-scope', task_id=tid, feature_id='cds', scope='restricted-target' if features == ['cds'] else 'mixed',
                rationale='Target is specifically coding-sequence membership or a coding-sequence protein/mutation property.' if features == ['cds'] else
                    'Coding sequence is one of multiple explicitly assessed annotation strata.', evidence_id=evidence), ('task_id', 'feature_id'))
        pid = tid + '-protocol'
        c.protocol(pid, tid, 'Original Evo 2 SAE feature evaluation', adaptation or 'frozen backbone; unsupervised SAE; annotation-guided feature selection',
            'Evo 2 block-26 representations → SAE latent activation', split, unit, evidence, metrics=metrics,
            embeddings=True, fitted='BatchTopK SAE; 32,768 latents, k=64; frozen Evo 2 7B 262k backbone',
            selection=selection, notes=notes)
        c.use(tid, 'evo2', 'evo', evidence, pid, 'original-paper',
            'Source-defined SAE readout/diagnostic; no experimental fitness labels or whole-transcript decoder is inferred.')
        for pop, note in populations:
            c.population(tid, pop, evidence, note)
        c.task_resource(tid, code_resource, code_e, 'evaluation-code',
            note='Feature extraction example only; not a complete evaluator or released original cohort for this task.')
        c.limit('tasks', tid, 'original-cohort-and-scorer', 'not-released',
            'Exact source-specific coordinates, feature-selection identities, per-example activations and final scored cohort/scorer are absent from the complete pinned official release. Paper-defined methods and visible figure metrics remain the evidence.', release)
        c.review('tasks', tid, 'Full A.4 task method, relevant main/extended figure including labels/metrics, official SAE inference implementation and public model release scope.',
            [evidence, trained, release, code_e, weights], notes)
        c.review('protocols', pid, 'Exact fitted readout, annotation-guided feature selection, scored unit, aggregation, source split and absence of released cohort manifest.',
            [evidence, trained, release, code_e], notes)
        return pid

    prophage = method('prophage-method', 'A.4.3; Extended Data Fig. 7b', 20,
        'Contrastive search uses 100-kb windows centered on geNomad prophage annotations in 100 randomly chosen GTDB genomes. '
        'Feature 19746 maximizes mean activation difference. Prophage-region mean activations are compared with length-matched non-phage regions from the same genomes, sampled without replacement. '
        'Source figure reports AUROC 0.95 on these regional means. Separate E. coli genome-scale tracks use 50-kb chunks and visual denoising; those tracks are not a dense coordinate-accuracy test.')
    pf = figure('prophage-figure', 13, 'Extended Data Fig. 7b and c',
        'Panel b reports AUROC 0.95 from mean f/19746 activation in annotated prophage versus matched-length non-phage sequences. '
        'Panel c separately shows natural E. coli CRISPR locus and three scrambling conditions; it has activation profiles rather than phenotype/annotation-accuracy labels.')
    pid = add('evo-sae-prophage', 'Prophage-region SAE discrimination', 'GTDB/geNomad selected prophage windows',
        'Annotated prophage versus length-matched bacterial background region',
        'Selected latent f/19746 is evaluated on regional mean activation, not as a genome-wide boundary decoder.', prophage,
        ['prophage'], 'isolated', 'One mean latent activation per supplied annotated/background region', 'annotated sequence region',
        'One hundred source GTDB genomes supply annotation-guided feature search and regional comparison. A separate search/test genome split is not specified.',
        [('auroc', 'Mean activation per annotated or matched-length region')], [('bacteria', 'Bacterial host-genome context with embedded prophage; exact 100-genome accessions not enumerated.')],
        'Choose feature with maximum average annotated-versus-background activation difference.',
        notes='No independent feature-selection/test separation or exact window count is stated. geNomad predictions supply labels, rather than experimentally validated prophage boundaries.')
    c.count('evo-sae-prophage', 100, 'GTDB genomes used for feature search', prophage, protocol=pid,
        qualifier='Genome count, not a count of independent scored prophage/background regions.')
    c.field('tasks', 'evo-sae-prophage', 'metric', pf)
    c.limit('tasks', 'evo-sae-prophage', 'selection-test-independence', 'not-reported',
        'The same described 100-genome source provides contrastive selection and feature-value analysis; an independent genome/region partition is not stated.', prophage)

    crispr = method('crispr-method', 'A.4.3; Extended Data Fig. 7c', 21,
        'The E. coli CRISPR locus from Fig. 4b is perturbed by independently scrambling spacers, replacing direct repeats with one constant scramble, '
        'or replacing direct repeats with different scrambles. f/19746 activation profiles are compared to natural sequence. '
        'Spacer scrambling retains activation, while repeat scrambling changes downstream spacer activation. This is a selected-locus internal-feature diagnostic, not an experimental CRISPR-function assay.')
    pid = add('evo-sae-crispr-scrambling', 'CRISPR-context SAE perturbation', 'E. coli selected CRISPR locus',
        'Dependence of phage-associated latent activation on CRISPR repeats and spacers',
        'Three controlled scrambling conditions compare the internal activation pattern with the natural CRISPR array.', crispr,
        ['crispr-array'], 'diagnostic', 'Per-position latent-activation profiles under reference/sequence-scrambling conditions', 'sequence perturbation condition',
        'One selected natural CRISPR locus plus three artificial perturbation conditions; no random experimental validation cohort.',
        [('feature-response', 'Selected-locus activation profiles')], [('ecoli', 'NC_000913.3 E. coli K12 MG1655 CRISPR context.')],
        'Use the prophage-associated feature 19746 identified by annotation contrastive search.',
        notes='Scrambled strings, random seeds and numerical activation arrays are not released. Neither repeat/spacer functional activity nor experimentally measured phage resistance is tested.',
        task_type='controlled internal-response diagnostic', label_basis='Natural/scrambled sequence conditions; no biological outcome labels')
    c.count('evo-sae-crispr-scrambling', 1, 'selected CRISPR locus', crispr, protocol=pid)
    c.count('evo-sae-crispr-scrambling', 3, 'scrambling conditions', crispr, protocol=pid)

    ecoli = method('ecoli-region-method', 'A.4.4; Extended Data Fig. 7e,f', 21,
        'E. coli K12 MG1655 NC_000913.3 activations are computed in nonoverlapping 50-kb chunks. RefSeq classes are plus-strand ORF, minus-strand ORF, tRNA, rRNA and intergenic. '
        'Intergenic means all bases outside ORF/tRNA/rRNA, not a separately experimentally verified regulatory class. '
        'Feature search combines annotation contrast and manual inspection. Final AUROC uses mean activation per supplied annotation region; consecutive intergenic bases are merged into regions.')
    ef = figure('ecoli-region-figure', 13, 'Extended Data Fig. 7e,f',
        'ORF features 13606 and 15680 have region-mean AUROC 0.99 each; plus-ORF 11734 AUROC 0.87; minus-ORF 24568 AUROC 0.93; '
        'intergenic 26069/15481 AUROC 0.94/0.75; tRNA 30262 AUROC 1.00; rRNA 2812 AUROC 0.99. '
        'Per-base illustrative tracks do not change the regional aggregation used by these quantitative discrimination panels.')
    region_specs = [
        ('orf', 'ORF membership', ['cds'], [(13606, .99), (15680, .99)]),
        ('plus-orf', 'Plus-strand ORF membership', ['cds'], [(11734, .87)]),
        ('minus-orf', 'Minus-strand ORF membership', ['cds'], [(24568, .93)]),
        ('intergenic', 'Intergenic membership', ['intergenic'], [(26069, .94), (15481, .75)]),
        ('trna', 'tRNA membership', ['trna'], [(30262, 1.00)]),
        ('rrna', 'rRNA membership', ['rrna'], [(2812, .99)])]
    for slug, name, features, feats in region_specs:
        tid = 'evo-sae-ecoli-' + slug
        pid = add(tid, 'E. coli SAE ' + name, 'E. coli RefSeq annotation regions', name,
            'Discriminate the stated annotation class using mean activation of an annotation-selected SAE feature for each supplied region.', ecoli,
            features, 'isolated', 'One mean latent score per supplied annotation region', 'annotated genomic region',
            'Full E. coli reference annotation is used for feature search/inspection and regional score summaries. No held-out chromosome or independent region partition is described.',
            [('auroc', 'Mean latent activation per region; positive annotation class versus other supplied classes')],
            [('ecoli', 'Single NC_000913.3 reference; scored origin, not the phenotype of E. coli grown under an assay.')],
            'Contrastive annotation-guided feature search plus manual inspection; exact manual criteria not enumerated.',
            notes='No full region-ID/count manifest or independent feature-selection/test partition is released. These regional AUROCs do not measure dense base-label accuracy or gene structure recovery.')
        for fid, auroc in feats:
            variant(tid, 'feature-' + str(fid), 'SAE feature ' + str(fid), ef,
                'Selected latent; printed regional AUROC ' + str(auroc) + '. No new biological target is created for another latent of the same class.')
        c.field('tasks', tid, 'scoring_unit', ef)
        c.category(tid, 'genome-annotation', ecoli, 'Evaluates annotation-associated signals, using supplied region aggregates rather than a complete annotation pipeline.', 'relevance')
        c.limit('tasks', tid, 'selection-test-independence', 'not-reported',
            'Feature selection and metric summaries use the E. coli annotation; a disjoint feature-selection/test interval split is not specified.', ecoli)

    secondary = method('secondary-method', 'A.4.5; Extended Data Fig. 7g', 21,
        'All E. coli CDS supply features for contrastive secondary-structure search. DSSP applied to AlphaFold DB predicted structures supplies helix/sheet labels. '
        'Features are selected by highest mean per-CDS Pearson correlation: alpha helix 28741 and beta sheet 22326. '
        'The final plotted AUROC aggregates feature activation over positions of each secondary-structure type per protein. Selected protein/tRNA structural overlays are illustrative, smoothed with a Gaussian width-ten kernel.')
    sf = figure('secondary-figure', 13, 'Extended Data Fig. 7g',
        'Printed AUROC 0.97 for alpha-helix feature 28741 and 0.92 for beta-sheet feature 22326. The caption defines these from mean activations of positions annotated as a structure type per protein, rather than a per-residue confusion matrix.')
    for slug, target, fid in [('helix', 'Alpha-helix association', 28741), ('sheet', 'Beta-sheet association', 22326)]:
        tid = 'evo-sae-protein-' + slug
        add(tid, 'Protein ' + target + ' in Evo 2 SAE', 'E. coli CDS / AlphaFold DB / DSSP', target,
            'Assess secondary-structure association in an annotation-selected coding-sequence latent, with per-protein region averaging.', secondary,
            ['cds'], 'isolated', 'Mean feature activation in structure-type positions within each protein', 'protein × secondary-structure class',
            'Features are selected and summarized across all source E. coli CDS; independent held-out proteins or organismal transfer is not specified.',
            [('auroc', 'Mean activation by structure type per protein'), ('pearson', 'Feature-selection correlation along each CDS, averaged across CDS')],
            [('ecoli', 'Coding sequences from E. coli K12 MG1655; labels are derived from predicted structures, not a wet-lab structure assay.')],
            'Select latent ' + str(fid) + ' by maximum mean per-CDS Pearson correlation with the target structure annotation.',
            notes='DSSP labels derive from AlphaFold DB model structures. No independent selection/test protein manifest or original region-level score array is released.',
            label_basis='DSSP assignments on AlphaFold-predicted protein structures')
        c.field('tasks', tid, 'scoring_unit', sf)
        c.category(tid, 'protein-engineering', secondary, 'Secondary-structure-associated sequence features may support protein analysis; this does not validate engineered protein function.', 'relevance')
        c.category(tid, 'structure-prediction', secondary, 'Secondary-structure annotation is the tested label, not tertiary-structure generation.')

    mutation = method('coding-mutation-method', 'A.4.6; Extended Data Fig. 8a,b', 21,
        'The eukaryotic-only SAE is searched using 100 artificial human coding-mutation loci in 8,192-bp windows. '
        'Top-20 features for frameshift and premature-stop responses are intersected, then top synonymous/nonsynonymous responders excluded. '
        'Three features remain and 24278 is manually selected. A separate 100-sequence subset supplies response profiles and a separate 500-sequence subset supplies precision/recall/F1. '
        'Any nonzero feature activation within 100 bp after a mutation is treated as a positive response. These labels are synthetic mutation types, not experimental loss-of-function phenotypes.')
    mf = figure('coding-mutation-figure', 14, 'Extended Data Fig. 8a,b',
        'f/24278 is evaluated separately for frameshift, premature stop, nonsynonymous and synonymous changes. '
        'F1/precision/recall are 0.812/0.935/0.718 for frameshift; 0.702/0.919/0.568 for premature stop; '
        '0.264/0.762/0.160 for nonsynonymous; 0.091/0.500/0.050 for synonymous. These are controlled mutation response summaries.')
    tid = 'evo-sae-coding-mutation-response'
    pid = add(tid, 'SAE response to coding mutation classes', 'Artificial human CDS mutation panel',
        'Frameshift/premature-stop-selective activation of a selected latent',
        'A selected latent responds preferentially to artificial frameshift and premature-stop changes; a supplied variant is reduced to any activation in the following 100 bp.', mutation,
        ['cds'], 'diagnostic', 'Binary response within 100 bp after a supplied mutation, summarized by synthetic mutation class', 'supplied synthetic mutation',
        '100 loci for annotation-guided feature selection; separate 100 sequences for positional visualization; separate 500 sequences for metrics. Source does not state per-class counts or locus-level overlap between these subsets.',
        [('f1', 'Per synthetic mutation class'), ('precision', 'Per synthetic mutation class'), ('recall', 'Per synthetic mutation class')],
        [('human', 'Synthetic coding mutations on human reference context; no human experimental fitness outcome labels.')],
        'Top-20 feature contrasts, intersection/exclusion across mutation types, then manual choice of f/24278 from three survivors.',
        notes='This is an internal synthetic-response diagnostic, not independent prediction of experimentally measured variant pathogenicity. Exact per-class denominators and confusion-matrix construction are not specified.',
        task_type='synthetic mutation-response diagnostic', label_basis='Known artificial frameshift, premature-stop, nonsynonymous and synonymous mutation labels')
    for n, unit, split in [(100, 'selection loci', 'feature selection'), (100, 'profile sequences', 'positional display'), (500, 'metric sequences', 'feature response evaluation')]:
        c.count(tid, n, unit, mutation, protocol=pid, split=split)
    for slug, name, f1, precision, recall in [
        ('frameshift', 'Frameshift', .812, .935, .718), ('stop', 'Premature stop', .702, .919, .568),
        ('nonsynonymous', 'Nonsynonymous substitution', .264, .762, .160), ('synonymous', 'Synonymous substitution', .091, .500, .050)]:
        variant(tid, slug, name, mf, f'Printed F1 {f1}; precision {precision}; recall {recall}. Same selected feature 24278; per-class sample denominator not given.')
    c.limit('tasks', tid, 'metric-label-construction', 'not-reported',
        'A.4.6 defines the 100-bp nonzero activation rule and a 500-sequence subset but does not give complete per-class denominators or an executable confusion-matrix scorer.', mutation)
    c.limit('protocols', pid, 'eukaryotic-sae-checkpoint', 'not-released',
        'The source uses the eukaryotic-only SAE; the identified public checkpoint and inference notebook supply the mixed SAE instead.', weights)

    motif = method('motif-method', 'A.4.7; Extended Data Fig. 8f; Supplementary Data 2', 22,
        'Random 50,000 GRCh38 promoter sequences are 1 kb upstream of GENCODE v46 TSSs. Eukaryotic-only SAE features yield up to 10,000 activations above 1e-4 each, '
        'with 31-bp centered windows converted to PWMs. TOMTOM v5.5.7 Sandelin–Wasserman q<0.01 defines HOCOMOCO v12 CORE motif matches. '
        'SEA defines promoter-enriched motifs against 50,000 randomly chosen genic background regions. HOMER discovers 2,000 motifs each of lengths 8/10/12 on the same promoter set. '
        'Reported endpoint is reference-motif recall, not TF occupancy or a dense binding-site predictor; motif matching can yield false positives and multiple latent matches to one motif.')
    mt = figure('motif-figure', 14, 'Extended Data Fig. 8f',
        'At q=0.01, the plotted SAE recalls 58.4% of all H12CORE motifs and 69.6% of promoter-enriched motifs; HOMER recalls 13.8% and 35.1%, respectively. '
        'The plotted denominator is the motif set, not 50,000 promoter sequences or the number of latent activations.')
    tid = 'evo-sae-tf-motif-recall'
    pid = add(tid, 'SAE transcription-factor motif recall', 'Human promoter PWMs / HOCOMOCO v12 CORE',
        'Recall of reference TF motif identities from selected latent-activation sequence windows',
        'Compare feature-derived PWMs with a reference motif database and count recalled motifs, with a separate promoter-enriched reference subset.', motif,
        ['promoter', 'tfbs'], 'diagnostic', 'Recalled reference motif identities from feature-derived PWMs', 'reference TF motif',
        '50,000 promoters supply feature windows and motif discovery; a separate 50,000 genic regions define enrichment background. No held-out promoter test for biological TF occupancy is described.',
        [('recall', 'Fraction of all reference motifs and separately promoter-enriched motifs matched at q<0.01')],
        [('human', 'Promoter sequence source is GRCh38 human; the HOCOMOCO human/mouse reference motif catalogue does not make these mouse evaluation sequences.')],
        'Use eukaryotic-only SAE, activations >1e-4, at most 10,000 per feature; TOMTOM q threshold 0.01.',
        notes='Unsupervised motif discovery plus reference matching; no label-fitted TF activity head or experimental occupancy validation. Raw promoter/background coordinates and PWM/TOMTOM result arrays are not released in the inspected code.',
        task_type='reference motif recovery', label_basis='HOCOMOCO reference motif identities and source-defined promoter enrichment')
    c.field('tasks', tid, 'metric', mt)
    c.count(tid, 50000, 'promoter sequences', motif, protocol=pid, split='motif discovery')
    c.count(tid, 50000, 'genic background sequences', motif, protocol=pid, split='motif enrichment background')
    c.limit('protocols', pid, 'eukaryotic-sae-checkpoint', 'not-released',
        'The source uses the eukaryotic-only SAE; the identified public checkpoint and inference notebook supply only mixed weights.', weights)
    report = inspected['sae']['motif_report']
    sid = 'evo2-sae-motif-report-source'
    url = SD_BASE + '41586_2026_10176_MOESM4_ESM.pdf'
    c.source(sid, 'Evo 2 Supplementary Data 2: TF motif and SAE feature matches', url,
        'results-document', 'Nature 2026', CACHE + '41586_2026_10176_MOESM4_ESM.pdf',
        notes='Entire 72-page PDF retrieved and all text rows parsed; motif/feature IDs, q-values and strands are preserved in the compact inspection manifest. Logo images are results, not source genomic windows.')
    c.get('sources', sid)['sha256'] = report['sha256']
    rd = c.evidence('evo2-sae-motif-report-inspection', sid, 'All 72 pages, all 191 motif blocks and 573 feature-match rows',
        'Published report has 191 distinct promoter-enriched H12CORE motif IDs, three feature matches per motif (573 rows), and 282 distinct feature IDs. '
        'Parsing every listed q-value yields 133 motifs with at least one hit q<0.01, independently reproducing the plotted 69.6% promoter-enriched recall. '
        'The report does not contain source promoter coordinates/sequences or the full all-H12CORE result matrix.', 'data')
    rid = c.resource('evo2-sae-motif-report-resource', sid, 'Promoter-enriched motif matches and feature IDs',
        'results', 'other', url, rd, revision=report['sha256'], notes='Complete 191-motif results report; not a promoter-sequence dataset.')
    c.task_resource(tid, rid, rd, 'results')
    c.collection_resource('evo-original', rid, rd, 'results')
    c.count(tid, 191, 'promoter-enriched reference motifs in report', rd, protocol=pid, split='published motif report', method='measured')
    c.count(tid, 133, 'reference motifs with q<0.01 match', rd, protocol=pid, split='published motif report', method='measured')
    c.review('tasks', tid, 'Full A.4.7, original plot axes/values, complete 72-page Supplementary Data 2 report and all 573 parsed motif/feature/q/strand rows; released SAE scope.',
        [motif, mt, rd, trained, code_e, weights, release],
        'Motif-set recovery has artifact-audited summary evidence. Original promoter/window/PWM arrays and the exact eukaryotic SAE weights remain unavailable in the inspected release.')

    human = method('human-base-method', 'A.4.8; Extended Data Fig. 8c–e', 22,
        'Select features from 50 exon-rich 8,192-bp human chromosome 1 segments by top-20 annotation-weighted activation sums and manual consistency inspection. '
        'Selection labels for exon starts/ends cover first/last 50 exonic bases. Final precision/recall/F1 is scored at individual bases across 1,000 random genes with at least five exons. '
        'CDS and intron use reference annotation masks; exon-start evaluation instead uses first 25 bases of an exon following an intron, and exon-end evaluation uses the last base before an intron. '
        'Nonzero activation is the positive prediction. A separate region-mean AUROC analysis averages each feature over CDS, intron and boundary loci. No gene-chain/isoform decoder is constructed.')
    hf = figure('human-base-figure', 14, 'Extended Data Fig. 8c–e',
        'Features 15680 CDS, 28339 intron, 1050 exon start and 25666 exon end are evaluated at individual bases in panel d. '
        'Their F1/precision/recall are 0.403/0.699/0.283; 0.332/0.912/0.203; 0.645/0.692/0.604; 0.438/0.294/0.859, respectively. '
        'Separate panel e mean-activation AUROCs are 0.63/0.58/0.80/0.93. These base and region metrics have different aggregation units.')
    human_specs = [
        ('cds', 'Coding-sequence membership', ['cds'], 15680, 'Reference CDS mask at every scored base'),
        ('intron', 'Intron membership', ['intron'], 28339, 'Reference intron mask at every scored base'),
        ('exon-start', 'Exon-start-associated positions', ['exon', 'splice-junction'], 1050, 'First 25 exonic bases after an intron, rather than a canonical splice-acceptor dinucleotide'),
        ('exon-end', 'Exon-end position', ['exon', 'splice-junction'], 25666, 'Last exonic nucleotide before an intron, rather than a complete transcript chain')]
    for slug, target, features, fid, label in human_specs:
        tid = 'evo-sae-human-' + slug
        pid = add(tid, 'Human SAE ' + target, 'Human GRCh38 annotation / 1,000 multi-exon genes', target,
            'A selected latent is thresholded at nonzero activation for dense base-label precision/recall/F1; region-mean AUROC is a separate linked scoring protocol.', human,
            features, 'dense-labels', 'Binary selected-feature label at every assessed base of sampled gene regions', 'genomic base',
            'Feature search/manual choice on 50 chromosome 1 segments; score 1,000 random genes with ≥5 exons. No explicit exclusion of selection segments, chromosome holdout or independent gene-identity split is reported.',
            [('f1', 'Individual bases across 1,000 genes'), ('precision', 'Individual bases across 1,000 genes'), ('recall', 'Individual bases across 1,000 genes')],
            [('human', 'GRCh38 genomic annotation targets; 1,000 sampled multi-exon genes.')],
            'Annotation-weighted top-20 contrastive feature search plus manual inspection; selected feature ' + str(fid) + '.',
            notes='Dense element labels are assessed, but no linked exon/intron chain, transcript isoforms or full gene structure is recovered. Feature-selection/test overlap is not reported. ' + label + '.',
            axis='contiguous', task_type='dense binary element labeling', label_basis=label)
        c.category(tid, 'dense-annotation', human, 'The quantitative source evaluates true/false labels at individual bases across sampled gene regions.')
        c.category(tid, 'genome-annotation', human, 'Predict an individual annotated element throughout sampled loci; no assembly of a complete gene/transcript structure.', 'relevance')
        c.field('task_outputs', tid + '-output-review', 'scoring_unit', hf)
        c.count(tid, 50, 'feature-selection segments', human, protocol=pid, split='feature search')
        c.count(tid, 1000, 'sampled genes with at least five exons', human, protocol=pid, split='base-level scoring')
        rp = tid + '-region-mean'
        c.protocol(rp, tid, 'Original Evo 2 human SAE region-mean discrimination',
            'frozen backbone; fitted SAE and annotation-guided latent selection',
            'Mean latent activation over each annotated CDS/intron/boundary region',
            'Same source set of 1,000 sampled genes; regional aggregation is separate from the dense base-level confusion matrix.',
            'annotated genomic element region', human, metrics=[('auroc', 'Mean activation per annotated region')], embeddings=True,
            fitted='Selected SAE feature ' + str(fid), selection='Use the feature already selected by the annotation contrastive/manual procedure.',
            notes='This protocol alone does not support the dense-label classification; that is established by the separate per-base F1/precision/recall protocol.')
        c.use(tid, 'evo2', 'evo', human, rp, 'original-paper', 'Separate region-level aggregation on the same source-selected feature/gene cohort.')
        c.review('protocols', rp, 'Full A.4.8 and actual Extended Data Fig. 8e region aggregation; separated from base-level scoring.', [human, hf, release])
        c.limit('tasks', tid, 'selection-test-independence', 'not-reported',
            'The 1,000 genes are randomly sampled for metrics, but the source does not explicitly exclude the 50 search segments or specify a chromosome/gene-disjoint split.', human)
        c.limit('tasks', tid, 'paper-sae-variant', 'not-reported',
            'A.4.8 does not restate whether this panel uses mixed or eukaryotic-only weights. The official notebook loads mixed weights with the same four feature IDs; that supports the released interface but is not a paper-time weight-byte manifest.', code_e)

    ablate = method('ablation-method', 'A.4.9; Extended Data Fig. 7h', 23,
        'A selected SAE latent is set to zero at all token positions, decoded to replace the model activation, and the forward pass resumes. '
        'Cross-entropy is compared with an unperturbed run. The figure separates within-annotation and outside-annotation cross-entropy changes and ablated/original ratios for eleven ORF/RNA/prophage/intergenic/secondary-structure latents. '
        'This tests contribution to the model’s own computation; no organismal phenotype or independently correct annotation is the endpoint.')
    af = figure('ablation-figure', 13, 'Extended Data Fig. 7h',
        'Plots percentage change in average next-token cross-entropy and mean per-nucleotide ablated/original CE ratio, separately within and outside each feature’s annotated region. '
        'Eleven features are 15680, 13606, 11734, 24568, 30262, 2812, 19746, 15481, 26069, 28741 and 22326. No full row-level cohort sizes or species/accession list is printed for this ablation panel.')
    tid = 'evo-sae-latent-ablation'
    pid = add(tid, 'Effect of SAE latent ablation on sequence loss', 'Selected Evo 2 biological-feature ablations',
        'Change in next-token cross-entropy after removing a selected latent',
        'Internal latent ablation is evaluated using sequence prediction loss within and outside source-defined annotation regions.', ablate,
        ['cds', 'trna', 'rrna', 'prophage', 'intergenic'], 'diagnostic', 'Change and ratio of model cross-entropy after internal feature removal', 'source-defined token or annotation stratum',
        'Selected features/annotation strata; no supervised train/test biological target. Exact ablation input sequence IDs, sample count and uncertainty calculation are not reported.',
        [('cross-entropy-change', 'Within versus outside annotation; both average CE difference and mean per-token CE ratio')],
        [('bacteria', 'Prokaryotic feature panel in Extended Data Fig. 7; exact ablation input accessions are not reported and are not assumed to equal the complete E. coli reference.')],
        'Use eleven previously identified high-association biological-feature latents; ablate after SAE encoding before resuming the same model computation.',
        notes='Exact input genomes/coordinates and numerical per-token ablation arrays are not released. This is a model-mechanism diagnostic, not biological knockout validation.',
        adaptation='frozen backbone; fitted SAE; targeted latent intervention', task_type='internal causal perturbation diagnostic', label_basis='Original versus ablated model loss, stratified by source annotation')
    c.field('tasks', tid, 'scoring_unit', af)
    c.category(tid, 'sequence-modeling', ablate, 'Endpoint is the model’s next-token loss after an internal intervention.')
    c.count(tid, 11, 'ablated latent features', af, protocol=pid)
    for fid, target in [(15680, 'ORF'), (13606, 'ORF'), (11734, 'plus ORF'), (24568, 'minus ORF'),
                        (30262, 'tRNA'), (2812, 'rRNA'), (19746, 'prophage'), (15481, 'intergenic'),
                        (26069, 'intergenic'), (28741, 'alpha helix'), (22326, 'beta sheet')]:
        variant(tid, str(fid), 'Feature ' + str(fid) + ' / ' + target, af, 'Within versus outside the associated annotation; CE difference and CE ratio are distinct summaries.')
    c.limit('tasks', tid, 'ablation-input-genomes', 'not-reported',
        'A.4.9 describes the intervention, and Fig. 7h identifies the features/strata, but neither gives the exact input accession/coordinate manifest or an explicit ablation-species list.', ablate)

    # Actual available annotation data, deliberately separate from scored cohorts.
    gb = inspected['sae']['ecoli_genbank']
    path = 'notebooks/sparse_autoencoder/NC_000913.gb'
    url = f'https://github.com/ArcInstitute/evo2/blob/{REV}/{path}'
    c.source('evo2-sae-ecoli-genbank', 'E. coli reference genome and annotations in SAE example', url,
        'dataset-file', REV, REPO + path,
        notes='Complete GenBank record read: header accession/version, full sequence length and all feature-table keys checked. This is upstream annotation, not an original scored-region manifest.')
    c.get('sources', 'evo2-sae-ecoli-genbank')['sha256'] = gb['sha256']
    ge = c.evidence('evo2-sae-ecoli-genbank-inspection', 'evo2-sae-ecoli-genbank', 'NC_000913.3 GenBank header, complete ORIGIN and all feature-table entries',
        'Released record is 4,641,652 nt with 4,315 CDS features, 86 tRNA features, 22 rRNA features, 99 other ncRNA features and 4,639 gene features. '
        'These are counts of source annotation entries, not independently recounted scored rows for the paper’s region means or dense labels.', 'data')
    gr = c.resource('evo2-sae-ecoli-genbank-resource', 'evo2-sae-ecoli-genbank', 'E. coli sequence and source annotations',
        'dataset', 'github', url, ge, revision=REV, notes='Complete annotation reference in official SAE example; scored cohorts/filters remain separate.')
    tasks = [r['id'] for r in d['tasks'] if r['id'].startswith('evo-sae-')]
    for t in tasks:
        if t.startswith(('evo-sae-ecoli-', 'evo-sae-protein-')) or t == 'evo-sae-crispr-scrambling':
            c.task_resource(t, gr, ge, 'upstream-data')
    c.collection_resource('evo-original', gr, ge, 'upstream-data')
    # Add source-review evidence to the existing collection/paper reviews without
    # displacing the original task-specific protocol or availability statements.
    for table, entity in [('evaluations', 'evo-original'), ('papers', 'evo')]:
        r = next(x for x in d['source_reviews'] if x['entity_table'] == table and x['entity_id'] == entity)
        refs = set(json.loads(r['evidence_ids_json'])); refs.update([trained, release, pf, ef, sf, mf, mt, rd, human, hf, ablate, af, ge])
        r['evidence_ids_json'] = json.dumps(sorted(refs))
        phrase = ' Quantitative A.4.3–A.4.9 SAE tasks are decomposed by target and scored unit, including annotation-guided selection and internal-response diagnostics.'
        if phrase.strip() not in r['scope']:
            r['scope'] += phrase
    d['task_categories'].sort(key=lambda r: (r['task_id'], r['category_id'], r['relation']))
    d['protocol_metrics'].sort(key=lambda r: (r['protocol_id'], r['metric_id']))
