"""Reconcile Evo 2 original-paper protocols against methods and released artifacts.

Authoring helper, never executed by an ordinary build. Published result summaries,
current examples, upstream assay tables and the original scored cohort are kept
separate. Source-review completion does not imply missing files were released.
"""
from pathlib import Path
import copy
import hashlib
import json
from common import Catalogue, ROOT, DATE

REV = '53f195997257c56c00e5ef8d33a54f5baad143a6'
PG = '144fe22b07dfaeec2b366f2346203a9838a55b4c'
VORTEX = '8b00afebeac745d1f31e7e2788f0e0e39fa47637'
CACHE = 'research/artifacts/final-audit/evo2-review/'
REPO = 'research/artifacts/final-audit/evo2-diagnostics/ArcInstitute-evo2-53f1959/'
PAPER = 'https://www.nature.com/articles/s41586-026-10176-5'
SUPP = 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-026-10176-5/MediaObjects/41586_2026_10176_MOESM1_ESM.pdf'
SD_BASE = SUPP.rsplit('/', 1)[0] + '/'


def populate(d):
    c = Catalogue(d)
    manifest = ROOT / 'data/evo2-artifact-inspections.json'
    if not manifest.exists():
        manifest = ROOT / CACHE / 'artifact-inspections.json'
    audit = json.loads(manifest.read_text())

    def method(id, section, page, text):
        return c.evidence('evo2-review-' + id, 'evo-supp', section + '; PDF page ' + str(page), text,
            url=SUPP + '#page=' + str(page))

    def code(id, file, text, first=1, last=None, repo='ArcInstitute/evo2', rev=REV, path=None):
        url = f'https://github.com/{repo}/blob/{rev}/{file}'
        sid = 'evo2-review-' + id + '-source'
        c.source(sid, repo + ' / ' + file, url, 'repository-file', rev,
            path or (REPO + file if repo == 'ArcInstitute/evo2' else None))
        return c.evidence('evo2-review-' + id, sid, file, text, 'code',
            url + f'#L{first}' + (f'-L{last}' if last else ''))

    def variant(tid, slug, name, eid, context, length=None, revision=None, n=None, unit=None, notes=None):
        vid = tid + '-' + slug
        c.put('variants', dict(id=vid, task_id=tid, name=name, evidence_id=eid, context=context,
            input_length=length, dataset_revision=revision, target_count=n, target_unit=unit, notes=notes))
        return vid

    def task_resource(tid, rid, eid, relation='evaluation-data', vid=None, note=''):
        c.task_resource(tid, rid, eid, relation, vid, note)

    def finding(id, tid, text, eid):
        c.put('findings', dict(id='evo2-review-' + id, task_id=tid, evaluation_id='evo-original',
            severity='discrepancy', description=text, evidence_id=eid))

    release = c.evidence('evo2-review-release', 'evo2-diagnostic-release-inventory',
        'Complete official repository tree at ' + REV + '; linked Savanna and Vortex release trees',
        'Complete official Evo 2 repository, Savanna and Vortex archives were reviewed. The Evo 2 repository includes a BRCA1 example workbook and notebook, '
        '122 sampled exon/intron positions and an inference notebook, and a later gene-completion data/code/results release. '
        'It does not include original-paper filtered ClinVar, SpliceVarDB, BRCA2, DEG/archaea, DepMap, decay, DMS/ncRNA score tables, '
        'original full exon species partition, or full mitochondrial/bacterial/yeast generation panels. Later phage_gen files belong to a separate study.',
        'code', f'https://github.com/ArcInstitute/evo2/tree/{REV}')
    available = c.evidence('evo2-review-data-availability', 'evo-paper',
        'Data availability, supplementary material index and Code availability',
        'The paper explicitly releases OpenGenome2 as pretraining data; mouse ATAC reads under PRJNA1314301; human ATAC reads under PRJNA1314272; '
        'Supplementary Data 1 human variant-effect result summaries; and Supplementary Data 3 experimentally tested chromatin-design sequences. '
        'These resources have different roles and do not establish publication of every processed evaluation cohort.', url=PAPER + '#data-availability')
    c.source('evo2-review-extended-figure-3', 'Evo 2 Extended Data Fig. 3',
        PAPER + '/figures/9', 'figure', 'Nature 2026', CACHE + 'fig9.jpg',
        notes='Complete original figure image visually inspected, including plot axes and context labels.')
    decay_plot = c.evidence('evo2-review-decay-plot', 'evo2-review-extended-figure-3',
        'Panel g: vertical axis',
        'Panel g explicitly labels the mRNA-decay association as Spearman rho. It compares 40B/7B base and extended checkpoints, with negative correlation favorable for the source decay target.',
        'paper', PAPER + '/figures/9')

    # Actual Nature supplementary workbooks: summaries are not row-level VEP data.
    workbooks = {}
    for num, title, kind in [(3, 'Human variant-effect result summaries', 'results'),
                              (5, 'Experimental chromatin-design sequences', 'dataset')]:
        fname = f'41586_2026_10176_MOESM{num}_ESM.xlsx'
        sid = 'evo2-review-supplement-' + str(num)
        url = SD_BASE + fname
        c.source(sid, 'Evo 2 Supplementary Data ' + ('1' if num == 3 else '3') + ': ' + title,
            url, 'spreadsheet', 'Nature 2026 published supplement', CACHE + fname,
            notes='Complete workbook read; worksheet dimensions, content and SHA-256 recorded in data/evo2-artifact-inspections.json.')
        w = audit['workbooks'][fname]
        c.get('sources', sid)['sha256'] = w['sha256']
        if num == 3:
            text = ('Workbook contains one worksheet with 705 model-by-cohort result rows: ClinVar 539, SpliceVarDB 46, BRCA1 76 and BRCA2 44. '
                'Columns include model, dataset, genomic feature, variant type, subcategory, positive/negative counts, total variants, AUROC and AUPRC. '
                'It contains no variant coordinates, mutant DNA sequences or per-variant model scores. Counts depend on the result row and need not match figure captions.')
        else:
            text = ('Workbook contains six mouse design sequences (five 19,968-nt sequences and one 19,584-nt sequence), '
                '50 human construct rows plus the pAF0977 plasmid. Human rows comprise 43 short constructs (including three named controls) and seven long constructs. '
                'A11 and B1 have identical sequence strings; C6 contains one nonbreaking-space character. Two raw-read construct IDs, E1 and E4, are absent. '
                'Human synthesis strings generally include 40 flanking bases in addition to 1,024/4,096 designed bases.')
        eid = c.evidence(sid + '-inspection', sid, 'All worksheets, all nonblank rows and complete sequence strings', text, 'data')
        rid = c.resource(sid + '-resource', sid, title, kind, 'other', url, eid,
            revision=w['sha256'], notes=text)
        c.collection_resource('evo-original', rid, eid, 'results' if kind == 'results' else 'evaluation-data')
        workbooks[num] = (sid, eid, rid)

    # Preserve results for every explicitly defined subset; do not sum overlapping
    # conservation, splice, combined or comparator-specific strata.
    summary = audit['workbooks']['41586_2026_10176_MOESM3_ESM.xlsx']['sheets']['Sheet1']
    data_tasks = {'ClinVar': 'evo-clinvar', 'SpliceVarDB': 'evo-splicevardb', 'BRCA1': 'evo-brca1', 'BRCA2': 'evo-brca2'}
    for row in summary['evo2_rows']:
        tid = data_tasks[row['Data']]
        slug = '-'.join(str(row[k] or 'all') for k in ['Model', 'Genomic_Feature', 'Variant_Type', 'Sub_category']).lower()
        slug = ''.join(x if x.isalnum() or x == '-' else '-' for x in slug).replace('--', '-')
        vid = variant(tid, 'sd1-' + slug, ' / '.join(str(row[k]) for k in ['Model', 'Genomic_Feature', 'Variant_Type', 'Sub_category'] if row[k]),
            workbooks[3][1], 'Published aggregate result row; variant identities not included.',
            length='8,192 bp for Evo 2 variant scoring', revision='Nature Supplementary Data 1',
            n=row['N_variants_total'], unit='source-summary variants',
            notes=f"Positive {row['N_pos']:,}; negative {row['N_neg']:,}; AUROC {row['AUROC']:.6g}; AUPRC {row['AUPRC']:.6g}. Overlapping strata and model rows must not be added.")
        c.count(tid, row['N_variants_total'], 'source-summary variants', workbooks[3][1], variant=vid,
            split='published aggregate result row', qualifier='Exact workbook summary count; not an independently recounted variant cohort.', method='measured-summary')
    for tid in data_tasks.values():
        task_resource(tid, workbooks[3][2], workbooks[3][1], 'results')
        c.limit('tasks', tid, 'original-processed-sequences-and-scores', 'not-released',
            'Supplementary Data 1 supplies aggregate results and counts, rather than per-variant score/coordinate rows. The complete pinned code release does not supply the original filtered scored cohort.', release)
    for tid, text in [
        ('evo-clinvar', 'Main Fig. 3 reports coding SNVs 14,319, noncoding SNVs 34,761 and non-SNV cohorts 1,236/3,894. Data 1 Evo 2 40B rows instead report 14,313/33,747 SNVs and 978/3,623 non-SNVs; combined and subtype rows use further denominators. No row-identity manifest resolves these stages.'),
        ('evo-splicevardb', 'Main Fig. 3 reports 1,181 exonic and 3,769 intronic variants. Data 1 Evo 2 40B rows report 1,179 and 3,708, plus a separate combined 6,068-variant row. The combined count is not the sum of the two filtered feature subsets.'),
        ('evo-brca1', 'Main Fig. 3e reports 2,077 coding SNVs, whereas Data 1 reports 2,768 coding and 1,125 noncoding SNVs, totaling the 3,893 full-cohort SNVs supported by the released example workbook. The figure/workbook coding denominators differ.'),
        ('evo-brca2', 'Data 1 reports 6,837 combined BRCA2 SNVs (1,156 positive, 5,681 negative), while coding/noncoding result rows contain 4,490/663 variants. These subsets do not exhaust the combined cohort. Carbon’s separately reported 6,840 variants remain a separate model protocol.')]:
        finding(tid + '-summary-counts', tid, text, workbooks[3][1])
        c.limit('tasks', tid, 'cohort-count-reconciliation', 'conflicting', text, workbooks[3][1])

    vep = method('vep', 'A.3.12–A.3.15', 17,
        'Evo 2 scores mutant-minus-reference log likelihood in a variant-centered 8,192-bp genomic window. '
        'Non-SNV windows add/remove edge context to keep scored length equal. More negative changes indicate greater deleteriousness. '
        'A.3.13 uses October 2024 nuclear ClinVar with at least two review stars, alleles at most 64 nt and no uncertain-significance labels; '
        'A.3.14 removes low-frequency SpliceVarDB labels; A.3.15 binarizes BRCA saturation-editing study classes.')
    vep_specs = {
        'evo-clinvar': ('Clinical pathogenicity of supplied variants', 'October 2024 ClinVar nuclear variants; pathogenic/likely pathogenic versus benign/likely benign.',
            'ClinVar labels define external evaluation cohorts, stratified by coding/noncoding, SNV/non-SNV, phyloP conservation and splice-site proximity. No downstream classifier is fitted.',
            'Review stars ≥2; both alleles ≤64 nt; VUS removed. Coding is defined using matched RefSeq transcript IDs and GRCh38.p14 annotation. Donor ≤3 bp and acceptor ≤5 bp define proximal variants. A separate arm requires max(SpliceAI,Pangolin) <0.1.'),
        'evo-splicevardb': ('Splice-altering versus non-altering supplied variants', 'Experimental splicing-effect classes from SpliceVarDB; low-frequency class excluded.',
            'External variant cohort split for reporting into exonic and intronic subsets. No downstream fitted head or chromosome-held-out test is defined for Evo 2.',
            'Exact SpliceVarDB version/download date and retained variant IDs are not reported in A.3.14.'),
        'evo-brca1': ('Loss of function versus functional/intermediate BRCA1 SNVs', 'Saturation genome editing: LOF 823 versus FUNC 2,821 plus INT 249.',
            'All 3,893 supplied SNVs are the zero-shot cohort; coding/noncoding and splice-proximity subsets are reporting strata. The position-held-out trained probe is a separate protocol.',
            'Source reference assembly is GRCh37/hg19 in the released example; genomic rather than protein-only context. AUROC/AUPRC use deleterious score direction.'),
        'evo-brca2': ('Loss of function versus functional BRCA2 SNVs', 'Saturation editing classes P strong/moderate/supporting 1,156 versus B strong/moderate/supporting 5,681.',
            'All source SNVs with score and class form the zero-shot cohort; coding/noncoding results are reporting strata. No BRCA2-trained downstream classifier is described.',
            'Variant-centered sequence is parsed from the reference genome assembly used by the original experiment. No original BRCA2 input/scored table is in the inspected Evo 2 code release.')}
    for tid, (target, labels, split, notes) in vep_specs.items():
        t = c.get('tasks', tid)
        t.update(target=target, label_basis=labels, input_description='Supplied reference/alternate variant in genomic context; 8,192 nt for original Evo 2 scoring',
            output_description='One pathogenicity or loss-of-function score per supplied variant; no splice-site localization or whole-isoform recovery',
            limitations='Original filtered variant IDs/scores are not released in the inspected code; the published result workbook gives aggregate counts with explicit figure/subset differences.')
        c.protocol(tid + '-zero', tid, 'Original Evo 2 variant likelihood scoring', 'zero-shot',
            'Mutant-minus-reference autoregressive sequence log likelihood', split, 'supplied variant', vep,
            metrics=[('auroc', 'source-defined variant subset'), ('auprc', 'source-defined variant subset')],
            notes=notes)
        for field in ['target', 'label_basis', 'input_description', 'output_description']:
            c.field('tasks', tid, field, vep)
        c.review('tasks', tid, 'Full original task methods, main/extended figure captions, all Supplementary Data 1 summary rows and complete current code release.',
            [vep, workbooks[3][1], release], 'Original per-variant scored cohort is not released; subset/count conflicts are explicit.')
        c.review('protocols', tid + '-zero', 'Original Evo 2 model interface, source labels, length normalization and cohort reporting strata.', [vep, release])
    c.limit('tasks', 'evo-splicevardb', 'source-database-version', 'not-reported', vep_specs['evo-splicevardb'][3], vep)

    brca_probe = method('brca-probe', 'A.3.16; Fig. 3g–i', 18,
        'BRCA1 positions are split 1,060 train/266 test out of 1,326 unique positions, retaining all alternate alleles together: 3,104 train and 789 test SNVs. '
        'WT/alternate, forward/reverse embeddings are mean pooled around the mutation and concatenated. Ridge regression is selected by five-fold training-only position-group cross-validation: layer 20, pool width 128, alpha 1,000.')
    c.protocol('evo-brca1-probe', 'evo-brca1', 'Original Evo 2 position-held-out BRCA1 ridge probe', 'frozen probe',
        'Four concatenated WT/alternate × forward/reverse pooled embedding views',
        'Random split at genomic positions; 1,060 train positions and 266 test positions. Five-fold grouped CV only within training selects layer, pooling width and ridge penalty.',
        'genomic position', brca_probe, metrics=[('auroc', '789 test SNVs'), ('auprc', '789 test SNVs')],
        embeddings=True, fitted='Ridge regression; alpha 1,000', selection='Layer 20; mean-pooling width 128; training-only five-fold grouped cross-validation.')
    c.review('protocols', 'evo-brca1-probe', 'Full A.3.16 including target grouping, four representation views and fitted/selection protocol.', [brca_probe, release],
        'The exact per-position train/test assignment and fitted ridge coefficients are not released in the inspected repository.')
    c.limit('protocols', 'evo-brca1-probe', 'position-split-manifest', 'not-released',
        'The source supplies partition counts and grouped selection rules but no exact train/test position manifest or original fitted ridge head.', release)
    brca_file = 'notebooks/brca1/41586_2018_461_MOESM3_ESM.xlsx'
    brca_data = code('brca-data', brca_file,
        'Complete upstream Findlay workbook read: 3,893 SNVs across 1,326 positions, FUNC 2,821, INT 249 and LOF 823. This is an actual sequence-variant label resource; Evo 2 scores and original probe split assignments are not columns.')
    c.get('evidence', brca_data)['basis'] = 'data'
    rid = c.resource('evo2-brca-data-resource', c.get('evidence', brca_data)['source_id'],
        'BRCA1 saturation-editing variant labels', 'dataset', 'github',
        f'https://github.com/ArcInstitute/evo2/blob/{REV}/{brca_file}', brca_data, revision=REV)
    task_resource('evo-brca1', rid, brca_data)
    brca_code = code('brca-notebook', 'notebooks/brca1/brca1_zero_shot_vep.ipynb',
        'Notebook constructs 8,192-bp hg19 reference/alternate windows for all 3,893 BRCA1 SNVs, computes alternate-minus-reference sequence scores and AUROC. '
        'It explicitly runs Evo 2 1B base as a demonstration; it does not reproduce the original 7B/40B results or ridge-probe split.')
    rid = c.resource('evo2-brca-code-resource', c.get('evidence', brca_code)['source_id'], 'BRCA1 scoring example',
        'evaluation-code', 'github', f'https://github.com/ArcInstitute/evo2/blob/{REV}/notebooks/brca1/brca1_zero_shot_vep.ipynb', brca_code, revision=REV)
    task_resource('evo-brca1', rid, brca_code, 'evaluation-code')
    c.field('tasks', 'evo-brca1', 'labels', brca_data)
    c.count('evo-brca1', 3893, 'released labelled SNVs', brca_data, split='released upstream workbook', method='measured')

    essential = method('essentiality', 'A.3.10; Fig. 2j and Extended Data Fig. 3h', 16,
        'Original Evo 2 uses binary essentiality from 56 bacterial and two archaeal DEG genomes, plus lambda/P1 CRISPRi binary labels from Piya et al. '
        'Each gene receives symmetric context totaling 8,192 bp (first 8,192 bp if the gene is longer), with TAATAATAATAGTGA inserted 12 nt after the gene start. '
        'Disrupted-minus-reference likelihood ranks genes and AUROC is calculated separately per genome. Base and context-extended 7B/40B checkpoints are compared.')
    for tid, description, split, unit in [
        ('evo-deg', 'Binary gene essentiality from 56 bacterial and two archaeal DEG genomes; compare likelihood change after a fixed stop-rich disruption.',
            'External experimental labels per source genome; no fitted downstream head. Each genome has its own AUROC. DEG and source-study versions are not specified.', 'coding gene within genome'),
        ('evo-phage-essential', 'Binary gene essentiality in lambda (NC_001416) and P1 (NC_005856) from published CRISPRi screens; compare a fixed stop-rich disruption.',
            'External CRISPRi-assigned essential/nonessential genes; lambda and P1 evaluated separately. No downstream classifier or held-out chromosome split.', 'coding gene within phage')]:
        t = c.get('tasks', tid)
        t.update(description=description, input_description='Gene sequence with symmetric flanks to 8,192 nt; fixed stop-rich insertion 12 nt after gene start',
            output_description='One essentiality ranking score per supplied coding gene',
            limitations='Original processed gene/label/score tables and exact per-genome retained counts are absent from the inspected release. No new pretraining exclusion is implied.')
        c.protocol(tid + '-zero', tid, 'Original Evo 2 fixed gene-disruption score', 'zero-shot',
            'Disrupted-minus-reference sequence log likelihood', split, unit, essential,
            metrics=[('auroc', 'one AUROC per source genome')], notes='Fixed insertion TAATAATAATAGTGA at offset 12 nt; 8,192-bp source context. This is distinct from the DepMap shuffled-CDS control.')
        c.review('tasks', tid, 'Full original A.3.10 and relevant captions; exact phage references; independent protocol from shared Evo 1 use.', [essential, release])
        c.review('protocols', tid + '-zero', 'Exact disruption, context, source labels and per-genome aggregation.', [essential, release])
        c.limit('protocols', tid + '-zero', 'processed-gene-label-manifest', 'not-released',
            'The paper-wide retained genes, per-genome class counts, sequence windows and scores are not in the complete pinned official release.', release)
    c.limit('tasks', 'evo-deg', 'deg-version-and-archaeal-identities', 'not-reported',
        'A.3.10 reports DEG and two added archaeal genomes but does not enumerate their accession IDs or a versioned DEG cohort manifest.', essential)

    depmap = method('depmap', 'A.3.11; Extended Data Fig. 3i', 16,
        'DepMap Public 24Q4 ScreenGeneEffect.csv, Gene.csv and AchillesScreenQCReport.csv provide Chronos copy-number-adjusted effects for 1,401 CRISPR screens. '
        'Gene effects are averaged across screens and matched to Ensembl 114 GRCh38 CDS, yielding 16,434 protein-coding genes. '
        'Inputs are CDS alone, truncated to the first 8,192 bp for longer genes; the reference control is dinucleotide-preserving shuffled CDS. The figure reports AUROC/AUPRC.')
    c.get('tasks', 'evo-depmap').update(description='Average Chronos gene effect across 1,401 CRISPR screens for 16,434 protein-coding genes; score CDS against a dinucleotide-preserving shuffled control.',
        label_basis='DepMap Public 24Q4 Chronos screen effects averaged per gene; binary essentiality threshold is not reported in the inspected Evo 2 method/caption.',
        input_description='Ensembl 114 GRCh38 coding sequence only; no flanking padding; first 8,192 bp for long CDS',
        output_description='Gene-level essentiality ranking against aggregated CRISPR gene effects',
        limitations='Exact essential/nonessential threshold, retained gene IDs and shuffled-control seeds are not provided by the Evo 2 release.')
    c.protocol('evo-depmap-zero', 'evo-depmap', 'Original Evo 2 CDS likelihood versus shuffled CDS', 'zero-shot',
        'CDS sequence log likelihood compared with dinucleotide-preserving shuffled-CDS reference',
        'Gene effects averaged across all 1,401 retained screens. No downstream fitted classifier or gene/chromosome split is reported.',
        'protein-coding gene', depmap, metrics=[('auroc', '16,434-gene cohort'), ('auprc', '16,434-gene cohort')],
        notes='No stop insertion is described for this task. The binary classification threshold is not given.')
    c.limit('tasks', 'evo-depmap', 'binary-label-threshold', 'not-reported',
        'A.3.11 defines averaged continuous Chronos effects, while Extended Data Fig. 3i reports binary-classification AUROC/AUPRC without stating the threshold used to construct labels. No standard DepMap threshold is assumed.', depmap)
    c.limit('tasks', 'evo-depmap', 'retained-gene-and-shuffle-manifest', 'not-released',
        'The inspected code release and supplements do not supply the original 16,434 retained gene IDs, binary labels or shuffled-CDS sequences/seeds.', release)
    c.review('tasks', 'evo-depmap', 'Full A.3.11, Extended Data Fig. 3i, all released supplementary workbooks and complete official code inventories.', [depmap, release, available])
    c.review('protocols', 'evo-depmap-zero', 'CDS-only input, Chronos aggregation, control construction and source-specific metric; exact missing threshold identified.', [depmap, release])
    for tid in ['evo-depmap', 'evo-deg', 'evo-phage-essential']:
        c.put('task_feature_scopes', dict(id=tid + '-cds-scope', task_id=tid, feature_id='cds', scope='restricted-target',
            rationale='Scored object is a supplied protein-coding gene/CDS. Flanking context does not change target specificity.', evidence_id=depmap if tid == 'evo-depmap' else essential), ('task_id', 'feature_id'))

    decay = method('decay', 'A.3.8 and B.2; Extended Data Fig. 3g', 15,
        'Human metabolic-RNA-labelling measurements from Karner et al. are averaged across reported cell lines. '
        'Evo 2 7B/40B score full-length mRNA or the longest supported suffix from the transcript end. '
        'LOESS corrects sequence scores for transcript length before comparison with measured decay. No fitted sequence-to-decay head is used. '
        'The text describes negative correlation; the actual Extended Data Fig. 3g plot axis explicitly identifies Spearman rho. The retained transcript count is not given.')
    c.get('tasks', 'evo-mrna-decay').update(description='Relate length-corrected transcript sequence likelihood to average measured human mRNA decay rates.',
        label_basis='Metabolic RNA-labelling decay rates averaged across source-study cell lines',
        input_description='Full mRNA, or longest model-supported suffix taken from its 3′ end', output_description='One length-corrected likelihood score per transcript',
        limitations='Retained transcript IDs/count, exact source-study file and LOESS fit settings/partition are not reported or released in the inspected Evo 2 sources. Spearman rho is identified by the actual plot axis.')
    c.protocol('evo-mrna-decay-zero', 'evo-mrna-decay', 'Original Evo 2 length-adjusted transcript likelihood', 'zero-shot with length correction',
        'Whole-transcript or suffix log likelihood, adjusted by LOESS against transcript length',
        'Cell-line decay rates are averaged; no trained downstream prediction head or train/test partition is described. The LOESS fitting partition is unspecified.',
        'mRNA transcript', decay, notes='LOESS is a statistical correction fitted to score/length, not a biological decay-labelled supervised head. The actual plot axis identifies Spearman rho.')
    # The estimator is supported by the plot itself, not inferred from common use.
    d['protocol_metrics'] = [r for r in d['protocol_metrics'] if r['protocol_id'] != 'evo-mrna-decay-zero']
    c.put('protocol_metrics', dict(protocol_id='evo-mrna-decay-zero', metric_id='spearman',
        aggregation='Correlation of length-adjusted likelihood with averaged experimental decay; negative sign is favorable in the source plot.',
        evidence_id=decay_plot, is_primary=True), ('protocol_id', 'metric_id'))
    c.limit('tasks', 'evo-mrna-decay', 'retained-transcript-count', 'not-reported',
        'A.3.8/B.2 and Extended Data Fig. 3g do not specify a retained transcript count. No count is copied from another mRNA benchmark.', decay)
    c.limit('protocols', 'evo-mrna-decay-zero', 'loess-fitting-partition', 'not-reported',
        'The source specifies length correction by LOESS but not the smoothing hyperparameters or whether its fit used a held-out partition.', decay)
    c.review('tasks', 'evo-mrna-decay', 'Full A.3.8/B.2, source reference, extended caption and actual plot axes, official repository inventory.', [decay, decay_plot, release])
    c.review('protocols', 'evo-mrna-decay-zero', 'Exact transcript orientation/context, length correction, actual plot metric and limits of the described evaluation.', [decay, decay_plot, release])

    exon = method('exon', 'A.3.9; Fig. 2l', 15,
        'Initial 94 PANTHER 19.0 eukaryotes are partitioned 80/10/10 by species; human/mouse/zebrafish are manually placed in test. '
        'Trichomonas vaginalis and Leishmania major are removed for insufficient intron annotations, leaving eight test species. '
        'RefSeq annotations downloaded 2024-11-18 include all constitutive/alternative exons. Frozen Evo 2 7B base final-position embeddings from forward/reverse 8,192-bp contexts are concatenated. '
        'Layer/hyperparameters are selected on validation species using 150 positions/species; final MLP training uses 1,500 positions/species. The scored endpoint is exon/intron at one supplied midpoint, not a decoded gene structure.')
    c.protocol('evo-exon-intron-probe', 'evo-exon-intron', 'Original Evo 2 species-partitioned midpoint MLP', 'frozen probe',
        'Concatenated final-position embeddings from two 8,192-bp strand-oriented views; combined span 16,383 bp',
        'Initial random species partition 80/10/10; human, mouse and zebrafish manually assigned to test; two test species excluded for sparse intron labels. Final test panel: eight named species.',
        'species', exon, metrics=[('auroc', 'per test species')], embeddings=True,
        fitted='One hidden layer, width 1,024; Evo 2 7B base block 26; Adam, weighted binary cross-entropy',
        selection='Validation-species layer selection followed by TPE head tuning on 150 sampled positions/species; final 1,500 positions/species.',
        notes='Learning rate 5e-5, batch 16, weight decay 2e-4. Native dense baselines are reduced to the same midpoint label; this does not assess their full structure output.')
    exon_file = 'notebooks/exon_classifier/samplePositions.tsv'
    exon_data = code('exon-sample', exon_file,
        'Complete samplePositions.tsv read: 122 labelled positions, 61 exon and 61 intron labels, from the eight named test species. '
        'Most species contribute 16 rows; cacao 11 and Selaginella 15. It contains sequences/coordinates and no train/validation split column; it is a demonstration sample, not the full 1,500-position-per-species cohort.')
    c.get('evidence', exon_data)['basis'] = 'data'
    rid = c.resource('evo2-exon-sample-resource', c.get('evidence', exon_data)['source_id'], 'Exon/intron labelled demonstration positions',
        'dataset', 'github', f'https://github.com/ArcInstitute/evo2/blob/{REV}/{exon_file}', exon_data, revision=REV,
        notes='122 actual midpoint examples; not the complete source-paper train/validation/test manifest.')
    task_resource('evo-exon-intron', rid, exon_data)
    vid = variant('evo-exon-intron', 'released-sample', 'Released 122-position demonstration', exon_data,
        'The eight test-species sample in the official inference notebook; no fitting partition supplied.', n=122, unit='labelled positions', revision=REV)
    c.count('evo-exon-intron', 122, 'labelled positions', exon_data, variant=vid, split='released demonstration', method='measured')
    ec = code('exon-notebook', 'notebooks/exon_classifier/exon_classifier.ipynb',
        'The released notebook loads Evo 2 7B base, block 26, concatenates the final forward/reverse embeddings and applies schmojo/evo2-exon-classifier. '
        'It reports AUROC and accuracy at threshold 0.5 on the 122 provided samples. It contains no classifier training or original species-split generator.')
    rid = c.resource('evo2-exon-code-resource', c.get('evidence', ec)['source_id'], 'Exon/intron inference example', 'evaluation-code', 'github',
        f'https://github.com/ArcInstitute/evo2/blob/{REV}/notebooks/exon_classifier/exon_classifier.ipynb', ec, revision=REV)
    task_resource('evo-exon-intron', rid, ec, 'evaluation-code')
    c.get('tasks', 'evo-exon-intron').update(output_description='One exon/intron probability at a supplied sequence midpoint',
        limitations='Eight test species and the 122-position released demonstration are identifiable; full 94-species train/validation assignments, full sampled cohorts and sampling seeds are not released. This is isolated midpoint classification, not dense annotation.')
    c.limit('tasks', 'evo-exon-intron', 'full-species-and-position-manifests', 'not-released',
        'The current official example releases 122 sampled test positions but no full 94-species partition or complete initial/final training, validation and test position manifests.', release)
    c.review('tasks', 'evo-exon-intron', 'Full A.3.9 and all 122 released sample rows; complete inference notebook and official source inventories.', [exon, exon_data, ec, release])
    c.review('protocols', 'evo-exon-intron-probe', 'Source-specific frozen backbone, two views, selected MLP, species split, sample stages and midpoint scoring.', [exon, ec, release])

    fitness_review(c, d, method, code, variant, release)
    generation_review(c, d, method, code, variant, finding, release, available, workbooks, audit)
    named_population_review(c, d, audit)
    dart_review(c, d, method, release)
    viral_review(c, d, method, variant, release, audit)
    upstream_review(c, d, audit)
    model_review(c, d, method, code, release, available)

    c.review('evaluations', 'evo-original',
        'All original indexed Evo 2 task methods; main and extended captions; full current official repository and linked training/inference inventories; '
        'all VEP result and experimental sequence workbook rows; ENA read-run metadata; exact upstream viral assay candidates.',
        [release, available, workbooks[3][1], workbooks[5][1], 'evo2-review-viral-method'],
        'Paper-wide processed cohorts are not uniformly released. Variant-specific counts, source conflicts, access limitations and original-versus-later protocols remain explicit; no external RNAGym/DART model use is relabelled as original Evo 2.')
    d['task_categories'].sort(key=lambda r: (r['task_id'], r['category_id'], r['relation']))
    d['protocol_metrics'].sort(key=lambda r: (r['protocol_id'], r['metric_id']))
    c.review('papers', 'evo', 'Complete article, all task-specific supplementary methods, published supplementary data workbooks and official data/code availability statements.',
        [available, release, workbooks[3][1], workbooks[5][1]])


def fitness_review(c, d, method, code, variant, release):
    protein = method('protein-fitness', 'A.3.6', 14,
        'Nine prokaryotic and six human DMS studies are reused from the Evo 1 source collection where native nucleotide and protein sequences were provided. '
        'All unique nucleotide sequences are scored with their nucleotide-associated fitness values; protein comparators receive their translation when the protein/DNA labels disagree. '
        'Stop-codon variants are retained for nucleotide models and omitted for protein models. Absolute Spearman correlation is calculated per assay from autoregressive likelihood or masked pseudolikelihood. '
        'No downstream fitness-labelled training, chromosome split or retained row-count manifest is specified for this zero-shot protocol.')
    ncrna = method('ncrna-fitness', 'A.3.7', 14,
        'Seven ncRNA studies are reused from Evo 1: Kobori and Andreasson ribozymes, Domingo and Guy tRNAs, Hayden and Pitt ribozymes, and Zhang rRNA. '
        'Experimental fitness values are compared to autoregressive sequence likelihood or masked pseudolikelihood using absolute Spearman correlation. '
        'The method does not report a retained per-study row count or a new downstream train/test partition.')
    for tid in sorted({r['task_id'] for r in d['model_evaluations'] if r['model_id'] == 'evo2' and r['paper_id'] == 'evo' and r['task_id'].startswith(('evo-dms-', 'evo-ncrna-'))}):
        eid = protein if tid.startswith('evo-dms-') else ncrna
        t = c.get('tasks', tid)
        t.update(limitations='The source identifies this assay and its zero-shot scoring rules. The original filtered nucleotide/fitness rows, retained per-study count and exact scored sequence manifest are absent from the inspected Evo 2 release.',
            input_description='Complete unique mutant nucleotide sequences from the source experiment; native nucleotide labels take precedence over translated-protein labels' if tid.startswith('evo-dms-') else 'Mutant ncRNA nucleotide sequences from the source experiment',
            output_description='One sequence likelihood per mutant, correlated with experimental assay fitness; no fitted fitness head')
        c.protocol(tid + '-score', tid, 'Original Evo 2 zero-shot assay likelihood', 'zero-shot',
            'Autoregressive complete-sequence likelihood',
            'External experimental mutant panel; no downstream fitted classifier, label-trained head or newly defined assay split. Complete unique source nucleotide sequences are evaluated.',
            'mutant nucleotide sequence within source assay', eid, metrics=[('abs-spearman', 'one absolute rank correlation per assay')],
            notes='Evo 2 7B and 40B compared with frozen DNA/RNA/protein models. Protein comparators omit stop-codon mutants; nucleotide models retain them.' if tid.startswith('evo-dms-') else
                'The seven ncRNA study identities are explicit. No current RNAGym processed split or score count is substituted for the original Evo 2 panel.')
        c.field('tasks', tid, 'input_description', eid)
        c.field('tasks', tid, 'output_description', eid)
        c.limit('protocols', tid + '-score', 'retained-nucleotide-cohort', 'not-released',
            'The original Evo 2 per-assay nucleotide/fitness/score table and exact retained sequence identities are absent from the inspected complete release. Upstream ProteinGym or later RNAGym files have their own preprocessing and counts.', release)
        c.limit('protocols', tid + '-score', 'retained-count', 'not-reported',
            'A.3.6/A.3.7 name the study panel and filtering rules but do not give the retained nucleotide mutant count for this assay.', eid)
        c.review('tasks', tid, 'Explicit original-paper assay list, DNA/protein label handling, stop-mutant rules, scoring/metric and released-file scope.', [eid, release],
            'Shared Evo 1 and later RNAGym protocols remain separately linked; their counts and splits are not inherited by Evo 2.')
        c.review('protocols', tid + '-score', 'Original Evo 2 source-specific zero-shot scoring, absence of task fitting and per-assay metric.', [eid, release])


def generation_review(c, d, method, code, variant, finding, release, available, workbooks, audit):
    specs = [
        ('evo-gen-completion', 'A.5.1', 23,
            'Complete partially supplied genes and recover the reference amino-acid sequence',
            'Twelve reference genes in six species: Haloferax volcanii, Escherichia coli, Saccharomyces cerevisiae, Chlamydomonas reinhardtii, Arabidopsis thaliana and human. '
            'Prompt with 1,000 bp upstream plus the first 500 bp of Haloferax/E. coli/yeast genes or 1,000 bp for the other species. '
            'Ten generations per prompt, temperature 0.7, top-k 4. Generated DNA is translated, aligned and scored as percent protein recovery.',
            'Known gene prefix and upstream genomic context', 'Generated DNA evaluated by reference protein recovery',
            'percent-aa-recovery', 'Prompted reference gene; ten generated completions per prompt. No randomized supervised train/test split.',
            'Protein sequence identity is a computational reference-recovery endpoint; no cellular gene-function experiment is described.'),
        ('evo-gen-mitochondria', 'A.5.2', 23,
            'Generate human mitochondrial sequences with coherent annotated components and protein complexes',
            'Use NC_012920.1 human mitochondrion, 3,000-bp forward or reverse-complement prefix, Evo 2 7B/40B, temperatures 1.0/0.7, top-k 4. '
            'More than 250 unique 16-kb sequences are analysed using MitoZ counts, synteny, BLASTn, codon usage and selected AlphaFold 3 complex predictions. '
            'Feature labels are temporarily changed to CDS for a synteny renderer; that display conversion is not proof that tRNA/rRNA sequences are coding genes.',
            '3,000-bp prefix of the forward or reverse human mitochondrial reference', 'Generated mitochondrial DNA; predicted component counts and selected protein-structure consistency',
            'generation-validity', 'One reference genome, two orientations, two model sizes and two temperatures; selected gene-complete candidates for complex folding. No held-out experimental viability cohort.',
            'All endpoints are computational. Complete scored generation panel and selection manifest are not released; selected folding examples do not estimate mitochondrial viability.'),
        ('evo-gen-bacterial-genome', 'A.5.3', 24,
            'Generate bacterial genome-length DNA with plausible coding and protein properties',
            'Evo 2 40B receives the first 10.5 kb of the Mycoplasma genitalium reference and generates 35 sequences of 580 kb at temperature 1.0/top-k 4. '
            'Prodigal, Pfam hmmscan E<0.001, ESMFold pLDDT and DSSP assess predicted genes/protein properties; Evo 1 and natural-genome controls are compared.',
            '10.5-kb prefix of the Mycoplasma genitalium genome', 'Generated genome-length DNA; predicted coding, domain and fold distributions',
            'coding-density', 'Thirty-five generated sequences from one reference-prefix condition; no experimental organismal viability test or independent annotation-truth cohort.',
            'The supplement states a pLDDT filter of 0.2. The exact scale/implementation and full generated-sequence/score panel are not supplied; no viable organism is demonstrated.'),
        ('evo-gen-yeast-chr', 'A.5.4', 24,
            'Generate yeast chromosome-length DNA with plausible coding, RNA and promoter composition',
            'Evo 2 40B receives the first 10.5 kb of S. cerevisiae chromosome III and generates 20 sequences of 330 kb at temperature 1.0/top-k 4. '
            'GeneMark-S+ProtHint, fungal OrthoDB, Pfam hmmscan, ESMFold, DSSP, Yeast Genome Annotation Pipeline tRNA calls, Promoter 2.0 and tetranucleotide usage analyse components. '
            'Natural S. cerevisiae chromosome III/IV and S. pombe chromosome III provide composition controls.',
            '10.5-kb prefix of S. cerevisiae chromosome III', 'Generated chromosome-length DNA; predicted feature densities and composition/fold distributions',
            'coding-density', 'Twenty reported 40B chromosome generations from one prefix; auxiliary 7B/40B composition comparisons have no separately enumerated generation manifest.',
            'No experimental chromosome function or complete decoded annotation truth is tested. Complete original generation and component-score tables are absent from the inspected release.'),
        ('evo-gen-mouse-guidance', 'A.6.1–A.6.6; Fig. 6 and Extended Data Fig. 10', 25,
            'Design long DNA with a specified mouse chromatin-accessibility pattern',
            'Evo 2 7B proposes 128-bp chunks under beam search with Enformer/Borzoi accessibility guidance, 40,960-bp upstream context at the Hprt locus, '
            'temperature 1.0/top-k 4, target length 19,968 bp. Six requested patterns include three square/rectangular waves and ARC/LO/EVO2 Morse patterns. '
            'Prediction-defined design AUROC and five-track ensemble agreement assess computational selection; selected constructs are integrated at a single-copy mESC Hprt landing pad and assayed by ATAC-seq.',
            'Native Hprt genomic prefix plus externally specified accessibility pattern', 'Generated DNA; oracle agreement and separate measured ATAC accessibility along selected integrated constructs',
            'auroc', 'Inference-time candidate selection against desired patterns; nine compute budgets compare Evo/uniform/bigram proposals. Wet-lab validation is selected constructs and clones at one landing pad, not a held-out sequence-prediction dataset.',
            'Oracle-optimized AUROC and experimental ATAC readout are distinct endpoints. Construct sequences and raw ATAC metadata are released; the full sampled-candidate/beam trajectory manifest is not.'),
        ('evo-gen-human-guidance', 'A.6.7–A.6.13; Fig. 6g–i and Extended Data Fig. 11', 28,
            'Design DNA with specified shared or cell-type-dependent human chromatin accessibility',
            'Evo 2 7B beam search uses 128-bp chunks, 96 candidates/step, five retained beams, temperature 0.8/top-k 4 and NEBL upstream context. '
            'Enformer/Borzoi guide 1-kb/4-kb patterns in HEK293T/K562. Selected designs are integrated at NEBL using hifiDn29-dCas9 and assayed by ATAC-seq after four weeks. '
            'Measured coverage is normalized to integrated plasmid-backbone reads; two transfection/electroporation populations are averaged. '
            'Main text reports 33/36 within-sequence pattern tests with AUROC>0.8 and 4/24 differential-accessibility designs with >2-fold change.',
            '40,960-bp upstream NEBL context plus requested HEK293T/K562 accessibility pattern', 'Generated DNA; externally predicted and experimentally measured accessibility profiles and cell-line differential activity',
            'auroc', 'Oracle-ranked generated designs, followed by selected construct integration in two cell lines with two biological delivery replicates. Within-sequence and between-cell-line success denominators differ.',
            'Generation A.6.8 says 4,996 bp, whereas A.6.9 and released long synthesis strings support 4,096 designed bases plus 40 flanking bases. Raw read metadata includes E1/E4 absent from the sequence workbook; C6 contains whitespace and A11/B1 are duplicate strings.')]
    metrics = [
        ('percent-aa-recovery', 'Percent amino-acid recovery', 'Source-defined identity of generated amino-acid sequence to a reference; alignment and prompted-region exclusion differ between original and current-release protocols.', 'higher'),
        ('ensemble-icc', 'Predictor ensemble ICC', 'Source-reported intraclass correlation across Enformer/Borzoi tracks; measures oracle agreement, not experimental accuracy.', 'higher'),
        ('measured-accessibility', 'Experimental accessibility pattern', 'ATAC-seq coverage, within-design AUROC and cell-line fold-change endpoints on selected integrated constructs, with source-specific normalization.', 'context-dependent')]
    for id, name, definition, direction in metrics:
        c.put('metrics', dict(id=id, name=name, definition=definition, direction=direction))
    for tid, section, page, target, statement, input, output, metric, split, limits in specs:
        eid = method(tid + '-generation', section, page, statement)
        t = c.get('tasks', tid)
        t.update(target=target, description=statement, input_description=input, output_description=output,
            label_basis='Computational sequence/annotation/folding readouts; no experimental fitness or viability labels' if tid not in ['evo-gen-mouse-guidance', 'evo-gen-human-guidance'] else
                'Specified design pattern, externally predicted accessibility and selected-construct experimental ATAC-seq',
            limitations=limits)
        guided = 'guidance' in tid
        c.protocol(tid + '-sampling', tid, 'Original Evo 2 guided chromatin design' if guided else 'Original Evo 2 prefix-conditioned sequence generation',
            'inference-time guided generation' if guided else 'autoregressive generation',
            'Autoregressive sampling with Enformer/Borzoi candidate scoring' if guided else 'Prefix-conditioned autoregressive nucleotide sampling',
            split, 'generated construct' if guided else 'generated sequence / reference prompt', eid,
            metrics=[(metric, 'source-defined generated-sequence endpoint')], selection='Beam-search accessibility loss; oracle-based candidate selection' if guided else 'Source-defined reference prefix, model and sampling settings',
            notes=limits)
        for r in d['model_evaluations']:
            if r['model_id'] == 'evo2' and r['paper_id'] == 'evo' and r['task_id'] == tid and r['provenance'] == 'original-paper':
                r.update(protocol_id=tid + '-sampling', evidence_id=eid)
        for f in ['target', 'description', 'input_description', 'output_description', 'label_basis']:
            c.field('tasks', tid, f, eid)
        c.review('tasks', tid, 'Full original task-specific generation method, relevant main/extended figure captions, released file inventory and available sequence/read artifacts.',
            [eid, release, available] + ([workbooks[5][1]] if guided else []), limits)
        c.review('protocols', tid + '-sampling', 'Original source-specific prompt, generation budget, oracle/annotation methods, candidate selection and validation endpoint.', [eid, release], limits)
        if not guided:
            c.limit('protocols', tid + '-sampling', 'original-generation-and-score-manifest', 'not-released',
                'A complete original generation/score/selection manifest is absent from the pinned official code release. The later gene-completion release is separately identified when applicable.', release)
        if guided:
            c.category(tid, 'regulatory-engineering', eid, 'Generation is explicitly optimized and experimentally tested for chromatin accessibility.', 'relevance')
            c.category(tid, 'regulatory', eid, 'Specified and measured chromatin-accessibility profiles are the design target, without a fixed promoter/enhancer identity assignment.')
            # Generated DNA remains sequence output even though validation profiles
            # are positional. It is not a genomic annotation labeler.
            c.output(tid, 'sequence', eid, 'Generated DNA sequence with separate predicted and experimental validation profiles',
                'generated construct', rationale='The model output is designed nucleotide sequence. Positional ATAC tracks validate those selected sequences; they are not the model’s annotation output.', limitations=limits)
            task_resource = c.task_resource
            task_resource(tid, workbooks[5][2], workbooks[5][1], 'evaluation-data')
            c.put('protocol_metrics', dict(protocol_id=tid + '-sampling', metric_id='measured-accessibility',
                evidence_id=eid, aggregation='Selected experimentally integrated constructs; separate from optimized oracle score.', is_primary=False), ('protocol_id', 'metric_id'))
        if tid == 'evo-gen-mouse-guidance':
            c.put('protocol_metrics', dict(protocol_id=tid + '-sampling', metric_id='ensemble-icc',
                evidence_id=eid, aggregation='Five predicted accessibility tracks at 32-bp resolution; Enformer upsampled.', is_primary=False), ('protocol_id', 'metric_id'))
        if tid in ['evo-gen-bacterial-genome', 'evo-gen-yeast-chr', 'evo-gen-mitochondria']:
            for mid in ['predicted-fold-confidence', 'generation-validity']:
                c.put('protocol_metrics', dict(protocol_id=tid + '-sampling', metric_id=mid,
                    evidence_id=eid, aggregation='Source-specific computational generated-sequence analysis; not biological viability.', is_primary=False), ('protocol_id', 'metric_id'))
    gene_e = 'evo2-review-evo-gen-completion-generation'
    for tid, n, unit, e in [
        ('evo-gen-completion', 12, 'reference genes', gene_e), ('evo-gen-completion', 6, 'source species', gene_e),
        ('evo-gen-completion', 10, 'generations per original prompt', gene_e),
        ('evo-gen-bacterial-genome', 35, '580-kb generated sequences', 'evo2-review-evo-gen-bacterial-genome-generation'),
        ('evo-gen-yeast-chr', 20, '330-kb generated sequences', 'evo2-review-evo-gen-yeast-chr-generation')]:
        c.count(tid, n, unit, e, protocol=tid + '-sampling')
    c.count('evo-gen-mitochondria', 250, 'unique 16-kb generations (reported lower bound)', 'evo2-review-evo-gen-mitochondria-generation',
        qualifier='Source says more than 250; not an exact retained count.', protocol='evo-gen-mitochondria-sampling')
    for tid, p in [('evo-gen-mouse-guidance', 'PRJNA1314301'), ('evo-gen-human-guidance', 'PRJNA1314272')]:
        url = f'https://www.ebi.ac.uk/ena/browser/view/{p}'
        sid = 'evo2-review-atac-' + p
        c.source(sid, 'Evo 2 ATAC-seq raw-read metadata: ' + p, url, 'read-archive-metadata',
            DATE, CACHE + p + '.json', notes='All read-run metadata rows read through the documented ENA portal API. Large raw read files were not downloaded or realigned.')
        a = audit['raw_atac'][p]
        e = c.evidence(sid + '-inspection', sid, 'Complete read-run metadata response',
            f"{a['runs']} runs and {a['samples']} samples are listed. {a['fastq_links_available']} run records expose FASTQ links in the inspected response. " +
            ('Human metadata has 52 construct IDs across two cell lines and two replicates, including E1/E4 absent from Supplementary Data 3.' if 'human' in tid else
             'Mouse records have six plasmid groups with unequal clone counts; these are 14 sequencing samples, not 14 independent generated designs.'), 'data')
        rid = c.resource(sid + '-resource', sid, p + ' ATAC-seq raw reads', 'dataset', 'other', url, e,
            revision='Accession-linked public records inspected ' + DATE, notes='Metadata and actual read locations verified; no claim of independently recomputing published accessibility profiles.')
        c.task_resource(tid, rid, e, 'evaluation-data')
        c.collection_resource('evo-original', rid, e, 'evaluation-data')
        c.count(tid, a['runs'], 'raw ATAC-seq runs', e, split='released sequencing metadata', method='measured')
        c.limit('tasks', tid, 'candidate-trajectory-and-processed-coverage-manifest', 'not-released',
            'Sequence strings and raw read metadata are public, but the inspected release does not supply the complete beam candidates, final selection traces and all processed coverage/score arrays.', release)
    # Released data versus paper text: provenance matters more than apparent match.
    gene_code = code('gene-completion-release', 'scripts/gene_completion/README.md',
        'Current release supplies 12 gene windows/reference proteins, separate prokaryotic and splice-aware eukaryotic scorers, and results for 1B/7B/20B/40B. '
        'It uses approximately 30% prefixes rather than the original fixed 500/1,000-bp prefixes; default 50 samples rather than ten; eukaryotic temperature 1.0 rather than 0.7. '
        'Published per-gene result files contain variable sample counts. This is a later protocol/reproduction, not byte-identical original-paper generation output.')
    gvid = variant('evo-gen-completion', 'current-release', 'Current 12-gene completion release', gene_code,
        'Later public release with 30% gene/window prompt; prokaryotic global alignment and eukaryotic reference-guided exonerate splicing.',
        revision=REV, n=12, unit='reference genes', notes='Not the original ten-samples/fixed-prefix protocol. Includes the later 20B checkpoint.')
    c.protocol('evo-gen-completion-current', 'evo-gen-completion', 'Current public 12-gene completion implementation', 'autoregressive generation',
        '30% reference prefix; prokaryotic translation/global alignment or eukaryotic exonerate protein2genome alignment',
        'Twelve fixed reference genes; no supervised train/test split. CLI default 50 samples per gene; checked per-gene files use variable sample counts.',
        'reference gene and sampled completion', gene_code, metrics=[('percent-aa-recovery', 'per-gene sample mean then equal mean across 12 genes')],
        selection='Temperature 0.7 prokaryote/1.0 eukaryote, top-k 4; ~30% prefix.', variant=gvid,
        notes='Prokaryotic denominator counts aligned nongap columns after the prompted reference residues. Eukaryotic scorer uses positional identity over the shorter aligned protein suffix, after reference-guided splicing. This is reference recovery, not independent gene-structure annotation.')
    for folder, kind, title, relation in [
        ('data', 'dataset', 'Twelve gene windows and reference proteins', 'evaluation-data'),
        ('scoring.py', 'evaluation-code', 'Current gene-completion scorers', 'evaluation-code'),
        ('results', 'results', 'Current per-gene and summary completion results', 'results')]:
        url = f'https://github.com/ArcInstitute/evo2/' + ('blob' if folder.endswith('.py') else 'tree') + f'/{REV}/scripts/gene_completion/{folder}'
        sid = 'evo2-review-completion-' + folder.replace('.', '-')
        c.source(sid, title, url, 'repository-tree' if not folder.endswith('.py') else 'repository-file', REV)
        rid = c.resource(sid + '-resource', sid, title, kind, 'github', url, gene_code, revision=REV,
            notes='Pinned current release; not automatically the original-paper exact sampling protocol.')
        c.task_resource('evo-gen-completion', rid, gene_code, relation, gvid)
    c.use('evo-gen-completion', 'evo2', 'evo', gene_code, 'evo-gen-completion-current', 'released-example',
        'Later public 12-gene protocol; original-paper method retained separately.')
    c.review('protocols', 'evo-gen-completion-current', 'Complete README, all gene/input/result CSV rows, prompt construction, both scoring functions and CLI sampling defaults.', [gene_code, release])
    finding('completion-original-versus-release', 'evo-gen-completion',
        'The current release describes its 30%-prefix/50-sample defaults as matching the paper, but A.5.1 instead specifies fixed 500/1,000-bp gene prefixes, ten samples and temperature 0.7. Separate linked protocols preserve both. Current result summaries also distinguish recomputed means from paper_reported values.', gene_code)
    c.limit('tasks', 'evo-gen-completion', 'original-versus-current-protocol', 'conflicting',
        'The current gene-completion README/defaults differ from A.5.1 in prompt fractions, sample budget and eukaryote temperature; current results include a later 20B checkpoint.', gene_code)
    c.limit('tasks', 'evo-gen-human-guidance', 'generation-length', 'conflicting',
        'A.6.8 states 4,996 designed bp, A.6.9 uses 4,096, and the seven released long synthesis strings are 4,136 bases including flanks. The source typo is not silently normalized.', 'evo2-review-evo-gen-human-guidance-generation')
    c.limit('tasks', 'evo-gen-human-guidance', 'sequence-to-read-linkage', 'conflicting',
        'ENA contains construct IDs E1/E4 that are absent from the 50-row human sequence panel. A11/B1 have identical sequences and C6 contains a nonbreaking-space character. Original construct-to-normalized-coverage mapping is not supplied.', workbooks[5][1])
    for tid, count, unit in [('evo-gen-mouse-guidance', 6, 'released design sequences'), ('evo-gen-human-guidance', 50, 'released construct rows')]:
        c.count(tid, count, unit, workbooks[5][1], split='Supplementary Data 3', method='measured',
            qualifier='Sequence records, not independently measured successful designs; human includes named controls and a duplicate string.')


def dart_review(c, d, method, release):
    e = method('dart', 'A.3.17', 19,
        'Original Evo 2 uses DART Task 1 cCRE discrimination and Task 2 TF-motif discrimination with sequence likelihood, '
        'and Task 5 caQTL/dsQTL classification with likelihood and embeddings. It does not use DART Tasks 3/4. '
        'Embedding layers include randomly chosen block 13 for 7B/40B and externally BRCA1-selected block 27 for 7B/block 20 for 40B. '
        'No DART variant-label-trained head is described. The >2.3M/~577k/>219k/~28k counts in this method describe upstream source cohorts, not model-specific scored tests.')
    for tid in ['dart-ccre', 'dart-motif', 'dart-caqtl', 'dart-dsqtl']:
        vep = tid in ['dart-caqtl', 'dart-dsqtl']
        pid = tid + '-evo-zero'
        c.protocol(pid, tid, 'Original Evo 2 DART allelic likelihood comparison' if vep else 'Original Evo 2 DART likelihood comparison', 'zero-shot',
            'Allelic sequence-likelihood difference' if vep else 'Sequence likelihood comparison of positive versus matched shuffled control',
            'Fixed source QTL evaluation cohort; no task-label fitting. Published source totals do not identify the exact post-filter scored rows.' if vep else
                'Fixed positive/control sequence pairs; no task-label fitting. Shared DART supervised-task chromosome partitions are not inherited by this likelihood comparison.',
            'supplied QTL variant' if vep else 'positive/control sequence pair', e,
            metrics=[('auroc', 'source-defined QTL cohort'), ('ap', 'source-defined QTL cohort')] if vep else [('accuracy', 'paired sequence comparison')],
            notes='Exact Evo-specific allele aggregation/scored-row manifest is not provided in A.3.17 or the inspected official Evo release.' if vep else
                'DART’s motif benchmark uses inserted consensus motifs and matched synthetic controls; the original Evo method’s description as TF-footprinting data does not change the released DART construction.')
        c.review('protocols', pid, 'Original Evo 2 task-number scope, likelihood-only interface, no task fitting and upstream-versus-scored cohort distinction.', [e, release],
            'Original Evo-specific scored inputs/outputs are not released in the inspected official repository.')
        c.limit('protocols', pid, 'evo-specific-score-manifest', 'not-released',
            'The original Evo 2 filtered sequence/variant rows and scores are not in the inspected Evo 2 official release. The independently released DART framework has separate source-defined cohorts and filters.', release)
        if vep:
            ep = tid + '-evo-embeddings'
            c.protocol(ep, tid, 'Original Evo 2 DART allelic embedding comparison', 'zero-shot embedding comparison',
                'Reference/alternate Evo 2 sequence representations',
                'Fixed QTL cohort; no QTL-label-trained classifier. Block 13 is randomly selected; alternatives were selected externally by BRCA1 training/CV.',
                'supplied QTL variant', e, metrics=[('auroc', 'source-defined QTL cohort'), ('ap', 'source-defined QTL cohort')],
                embeddings=True, selection='Block 13 in both sizes; BRCA1-selected block 27 in 7B and block 20 in 40B.',
                notes='The original source identifies layers but not exact Evo-specific allele pooling/distance. No generic DART encoder implementation is assumed identical.')
            c.use(tid, 'evo2', 'evo', e, ep, 'original-paper', 'Separate from original likelihood scoring; no QTL-label-trained readout.')
            c.review('protocols', ep, 'Exact original Evo 2 layer choices and external selection source; inspected code release for original scorer.', [e, release])
            c.limit('protocols', ep, 'allele-pooling-and-distance', 'not-reported',
                'A.3.17 identifies the embedding layer choices but does not describe Evo-specific sequence pooling and distance formulas; no original scorer is in the inspected Evo repository.', e)
    c.field('evaluations', 'evo-original', 'DART scope', e,
        'Only cCRE, motif and QTL classification are original Evo 2 uses. Independent later DART evaluations and DART sequence-to-activity fitting remain external.')


def viral_review(c, d, method, variant, release, audit):
    e = method('viral-method', 'A.3.6; Extended Data Fig. 2b', 14,
        'The source reports 18 human-virus DMS datasets but its prose enumerates 20 entries, including two unspecified Haddox envelope mentions. '
        'Nucleotide references are manually retrieved through UniProt-linked GenBank; each ProteinGym amino-acid substitution is encoded using the most frequent human codon for that mutant residue. '
        'Absolute Spearman compares full sequence likelihood with experimental protein-assay fitness. This is synthetic encoding of a protein-level experiment, not measured native viral nucleotide fitness. '
        'Exact encoded nucleotide sequences, final assay identity manifest and scored-row counts are not released in the inspected Evo 2 repository.')
    c.source('evo2-review-viral-upstream', 'ProteinGym v1.3 complete substitutions archive',
        'https://zenodo.org/records/15293562/files/DMS_ProteinGym_substitutions.zip', 'dataset-archive', '10.5281/zenodo.15293562',
        CACHE + 'DMS_ProteinGym_substitutions.zip', notes='Complete 43,021,128-byte ZIP downloaded. All 23 viral candidate CSVs fully read and hashed; original Evo-encoded DNA cohorts are not contained in this protein archive.')
    c.get('sources', 'evo2-review-viral-upstream')['sha256'] = audit['viral_upstream']['archive_sha256']
    upstream = c.evidence('evo2-review-viral-upstream-inspection', 'evo2-review-viral-upstream',
        'All rows of 23 candidate assay CSVs plus pinned ProteinGym reference metadata',
        'Complete candidate CSVs have mutant protein sequences and processed DMS_score labels with finite scores. '
        'Exact member names, measured row counts, hashes, raw phenotype names and assay definitions are preserved in data/evo2-artifact-inspections.json. '
        'These are upstream protein-assay data, not proof of the final Evo 2 assay selection or human-codon encoding.', 'data')
    rid = c.resource('evo2-viral-upstream-resource', 'evo2-review-viral-upstream',
        'ProteinGym v1.3 upstream viral DMS tables', 'dataset', 'zenodo',
        'https://zenodo.org/records/15293562/files/DMS_ProteinGym_substitutions.zip', upstream,
        revision='10.5281/zenodo.15293562; SHA-256 ' + audit['viral_upstream']['archive_sha256'],
        notes='Protein mutants/assay labels. Exact Evo 2 nucleotide-encoded panel is a separate unreleased transformation.')
    c.collection_resource('evo-original', rid, upstream, 'upstream-data')
    assays = {r['DMS_id']: r for r in audit['viral_upstream']['assays']}
    # Exact study/protein pairs that unambiguously match the method text. Shared
    # dataset×target records are reused; original Evo scoring is a linked variant.
    unambiguous = [
        ('A0A2Z5U3Z0_9INFA_Wu_2014', 'Influenza hemagglutinin fitness (Wu 2014)', 'taxon-2955291'),
        ('PA_I34A1_Wu_2015', 'Influenza PA fitness (Wu 2015)', 'taxon-2955291'),
        ('NRAM_I33A0_Jiang_2016', 'Influenza neuraminidase fitness (Jiang 2016)', 'taxon-2955291'),
        ('TAT_HV1BR_Fernandes_2016', 'HIV-1 Tat fitness (Fernandes 2016)', 'taxon-3418650'),
        ('REV_HV1H2_Fernandes_2016', 'HIV-1 Rev fitness (Fernandes 2016)', 'taxon-3418650'),
        ('ENV_HV1B9_DuenasDecamp_2016', 'HIV-1 envelope fitness (Duenas-Decamp 2016)', 'taxon-3418650'),
        ('C6KNH7_9INFA_Lee_2018', 'Influenza hemagglutinin fitness (Lee 2018)', 'taxon-2955291'),
        ('A4D664_9INFA_Soh_2019', 'Influenza PB2 fitness (Soh 2019)', 'taxon-2955291'),
        ('A0A140D2T1_ZIKV_Sourisseau_2019', 'Zika envelope fitness (Sourisseau 2019)', 'taxon-3048459'),
        ('POLG_CXB3N_Mattenberger_2021', 'Coxsackievirus capsid fitness (Mattenberger 2021)', 'taxon-3428502'),
        ('CAPSD_AAV2S_Sinai_2021', 'AAV2 capsid production (Sinai 2021)', 'taxon-1511891'),
        ('R1AB_SARS2_Flynn_2022', 'SARS-CoV-2 Mpro growth phenotype (Flynn 2022)', 'taxon-3418604'),
        ('POLG_DEN26_Suphatrakul_2023', 'Dengue NS5 fitness (Suphatrakul 2023)', 'taxon-3052464'),
        ('RDRP_I33A0_Li_2023', 'Influenza PB1 fitness (Li 2023)', 'taxon-2955291')]
    # The source is not exact enough to choose one of the real upstream assays.
    ambiguous = [
        ('evo-viral-qi-hcv', 'HCV protein fitness (Qi): source target conflict', 'taxon-3052230', ['POLG_HCVJF_Qi_2014'],
            'Evo 2 calls this an HCV polymerase assay. The exact Qi 2014 ProteinGym reference is NS5A, a nonstructural protein rather than the RNA polymerase. The source-study link is identifiable; the original encoded target/cohort is not independently resolved.'),
        ('evo-viral-doud-np', 'Influenza nucleoprotein fitness (Doud): strain unresolved', 'taxon-2955291', ['I6TAH8_I68A0_Doud_2015', 'NCAP_I34A1_Doud_2015'],
            'The source names Doud nucleoprotein without strain/year/accession. ProteinGym has two Doud 2015 nucleoprotein homolog assays. The original panel manifest does not identify which was scored or whether both were included.'),
        ('evo-viral-doud-pb1', 'Influenza PB1 fitness (Doud): assay identity unresolved', 'taxon-2955291', [],
            'The source explicitly names a Doud PB1 assay. No matching PB1 assay exists in the complete pinned ProteinGym reference; Doud 2015 assays are nucleoproteins and Doud 2016 is hemagglutinin. Li 2023 PB1 is separately listed by the Evo source. No candidate is silently substituted.'),
        ('evo-viral-haddox-env', 'HIV-1 envelope fitness (Haddox): assay panel unresolved', 'taxon-3418650', ['ENV_HV1BR_Haddox_2016', 'A0A192B1T2_9HIV1_Haddox_2018', 'Q2N0S5_9HIV1_Haddox_2018'],
            'Two separate Haddox-envelope mentions occur in the source’s panel prose, without year/strain/accession. ProteinGym has one 2016 assay and two 2018 homolog assays. These three are candidate upstream variants, not three established original Evo 2 uses or two fabricated exact targets.'),
        ('evo-viral-starr-rbd', 'SARS-CoV-2 RBD DMS (Starr): measured target unresolved', 'taxon-3418604', ['SPIKE_SARS2_Starr_2020_binding', 'SPIKE_SARS2_Starr_2020_expression'],
            'The source names the Starr RBD assay without specifying ACE2 binding versus expression. ProteinGym releases separate binding and expression targets. Neither is asserted to be the sole original Evo 2 target.')]
    for key, meta in audit['taxonomy'].items():
        taxid = meta['tax_id']
        pid = 'taxon-' + str(taxid)
        c.put('populations', dict(id=pid, name=meta['current_scientific_name']['name'], rank='species',
            parent_id='riboviria', ncbi_taxid=taxid, notes='Exact source-study virus resolved through current NCBI taxonomy; encoded DNA is an assay representation, not evidence that the virus naturally has a DNA genome.'))
        species_row(c, d, pid, meta, e)
    def build(tid, name, pop, candidates, limitation, certain):
        exists = any(r['id'] == tid for r in d['tasks'])
        if not exists:
            c.put('tasks', dict(id=tid, name=name, dataset_name='ProteinGym viral DMS / original Evo 2 encoding',
                target='Experimental protein-assay phenotype' if certain else 'Source-reported viral protein DMS phenotype; exact assay/target mapping limited',
                description='Assess correlation of Evo 2 likelihood with source viral protein DMS fitness after human-codon encoding of amino-acid mutations.',
                task_type='regression / rank correlation' if certain else 'source-reported protein fitness correlation',
                label_basis='Experimental protein phenotype from the named DMS study, not measured native viral DNA mutation fitness',
                evidence_id=e, status='paper-audited' if certain else 'source-limited', limitations=limitation,
                input_description='UniProt/GenBank nucleotide reference with ProteinGym amino-acid changes encoded using the most common human codon',
                output_description='One sequence likelihood per synthetically encoded mutant; absolute Spearman versus protein phenotype'))
            for cat in ['protein-engineering', 'model-development', 'variant-effects', 'cds']:
                c.category(tid, cat, e, 'Source measures protein-fitness correlation from nucleotide-encoded coding-sequence mutants; virus origin and assay host are distinct.')
            c.output(tid, 'isolated', e, 'One scalar score per supplied encoded mutant', 'protein mutant',
                rationale='Each supplied mutant is scored once; no genome-wide coding or splice labels are recovered.', limitations=limitation)
            c.put('task_feature_scopes', dict(id=tid + '-cds-scope', task_id=tid, feature_id='cds', scope='restricted-target',
                rationale='The source constructs coding sequences for one protein-assay target; genomic context is not an annotation target.', evidence_id=e), ('task_id', 'feature_id'))
            c.population(tid, pop, e, 'Source-virus protein target; the experimental assay host and synthetic human-codon sequence encoding are separate contexts.')
        vid = variant(tid, 'evo2-human-codon-encoding', 'Original Evo 2 human-codon encoding of protein mutants', e,
            'Human-most-frequent codon encodes each substituted amino acid against manually retrieved GenBank reference; not the later RNAGym nucleotide preprocessing.',
            revision='Evo 2 Supplement A.3.6', notes=limitation)
        pid = tid + '-evo2-viral-score'
        c.protocol(pid, tid, 'Original Evo 2 encoded viral DMS likelihood', 'zero-shot',
            'Full encoded nucleotide sequence log likelihood',
            'Fixed external protein DMS panel; no downstream fitness-label fitting. Exact encoded variant manifest and source-specific retained rows are not released.',
            'synthetically encoded protein mutant', e, metrics=[('abs-spearman', 'one absolute rank correlation per source assay')],
            notes=limitation, variant=vid)
        c.use(tid, 'evo2', 'evo', e, pid, 'original-paper',
            'Original A.3.6 source claim; unambiguous source-study mapping.' if certain else 'Original source claim retained with explicit assay/target identity limits.')
        c.member(tid, 'evo-original', e, vid, 'Original human-virus DMS evaluation; synthetic coding representation is distinct from native viral nucleotide assays.')
        c.task_resource(tid, rid, upstream, 'upstream-data', vid, 'Protein-level assay labels; original Evo 2 encoded nucleotide table is not released.')
        for aid in candidates:
            a = assays[aid]
            av = variant(tid, 'upstream-' + aid.lower().replace('_', '-'),
                ('Matched upstream assay: ' if certain else 'Candidate upstream assay: ') + aid,
                upstream, f"Molecule: {a['molecule_name']}; source phenotype: {a['raw_DMS_phenotype_name']}; source organism: {a['source_organism']}.",
                revision='ProteinGym v1.3, Zenodo 15293562', n=a['rows'], unit='upstream protein mutants',
                notes='All rows read; ' + ('source study/protein match is unambiguous, but original nucleotide encoding is not released.' if certain else 'Candidate only; original source identity is not resolved.'))
            c.count(tid, a['rows'], 'upstream protein mutants', upstream, variant=av,
                split='ProteinGym upstream assay', method='measured', qualifier='Exact archive count; not the original Evo 2 retained encoded-mutant count.')
            # Exact assay identity file, separately typed from a dataset archive.
            sid = 'evo2-review-viral-ref-' + aid.lower().replace('_', '-')
            url = f'https://github.com/OATML-Markslab/ProteinGym/blob/{PG}/reference_files/DMS_substitutions.csv'
            c.source(sid, 'ProteinGym reference entry: ' + aid, url, 'assay-manifest', PG,
                'research/artifacts/final-audit/existing-proteingym-reference/reference_files/DMS_substitutions.csv')
            er = c.evidence(sid + '-entry', sid, 'DMS_id=' + aid,
                f"{aid}: {a['molecule_name']}; processed label DMS_score derives from {a['raw_DMS_phenotype_name']}. "
                f"Complete upstream archive has {a['rows']:,} finite labelled mutants. Selection assay: {a['selection_assay'] or 'not populated in reference entry'}.", 'data')
            c.field('variants', av, 'source-identity', er)
        c.limit('protocols', pid, 'original-encoded-cohort-and-count', 'not-released',
            'Original encoded DNA sequences, selected assay IDs, source-specific codon replacements and retained rows are absent from the complete Evo 2 release. ProteinGym upstream counts are not substituted.', release)
        if not certain:
            c.limit('tasks', tid, 'original-assay-identity', 'conflicting' if 'conflict' in name or 'PB1' in name else 'not-reported', limitation, e)
        c.review('protocols', pid, 'Original A.3.6 viral-specific encoding, metric and absence of task fitting, plus complete original release and exact upstream candidate artifacts.', [e, upstream, release], limitation)
        c.review('tasks', tid, 'Original viral DMS source claim and paper-specific encoding reviewed; complete ProteinGym candidate table(s) and assay-reference metadata inspected.', [e, upstream, release], limitation)
    for aid, name, pop in unambiguous:
        existing = 'rnagym-' + aid.lower().replace('_', '-')
        tid = existing if any(r['id'] == existing for r in d['tasks']) else 'evo-viral-' + aid.lower().replace('_', '-')
        build(tid, name, pop, [aid], 'Exact original encoded nucleotide rows/count are not released. Upstream protein assay is identified; later RNAGym processing and scores remain a separate evaluation protocol.', True)
    for tid, name, pop, candidates, limits in ambiguous:
        build(tid, name, pop, candidates, limits, False)
    c.limit('evaluations', 'evo-original', 'viral-panel-size-and-identities', 'conflicting',
        'A.3.6 says 18 viral datasets but enumerates 20 entries; two Haddox mentions lack exact strain/year, the Doud PB1 description conflicts with ProteinGym reference identities, and Starr binding/expression is unspecified. '
        'The catalogue retains 14 unambiguous study/target matches plus five source-limited claims (merging the two unresolvable Haddox mentions), not a fabricated complete 18-file manifest.', e)


def species_row(c, d, pop, meta, evidence):
    """Resolved named RNA-virus target in existing Riboviria display rows."""
    tid = meta['tax_id']
    name = meta['current_scientific_name']['name']
    url = 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=' + str(tid)
    sid = 'evo2-review-viral-taxonomy-' + str(tid)
    path = CACHE + 'taxonomy-species-' + str(tid) + '.json'
    c.source(sid, 'NCBI taxonomy: ' + name, url, 'taxonomy', DATE, path)
    eid = c.evidence(sid + '-classification', sid, 'NCBI taxonomy classification and parents',
        name + '; taxon ' + str(tid) + '; NCBI lineage places this species in Riboviria. Source-study virus names are retained in task variants.', 'documentation')
    base = c.get('coverage_rows', 'clade:riboviria')
    pops = set(json.loads(base['population_ids_json'])); pops.add(pop)
    base['population_ids_json'] = json.dumps(sorted(pops))
    for view, key, label, kind in [('species', 'riboviria-other', 'Other named species', 'other'),
                                    ('allSpecies', 'riboviria-sp-' + str(tid), name, 'species')]:
        old = next((r for r in d['coverage_rows'] if r['id'] == view + ':' + key), None)
        src = old or copy.deepcopy(base)
        m = json.loads(src['metadata_json'])
        members = set(m.get('members', []) if old else []); members.add(name)
        rp = set(json.loads(old['population_ids_json']) if old else []); rp.add(pop)
        m.update(id=key, label=label, displayLabel=label, clade='riboviria', cladeLabel='Riboviria', kind=kind,
            members=sorted(members), note='Named viral protein-assay target; synthetic DNA encoding is separate from native genome type.')
        c.put('coverage_rows', dict(id=view + ':' + key, view=view, row_key=key, node_id='riboviria',
            population_ids_json=json.dumps(sorted(rp)), metadata_json=json.dumps(m, ensure_ascii=False)))
    # A temporary mapping template lets Catalogue.population copy presentation,
    # while each real task below supplies its own scientific source evidence.
    template = next((r for r in d['coverage_mappings'] if r['population_id'] == pop), None)
    if template is None:
        x = copy.deepcopy(next(r for r in d['coverage_mappings'] if r['population_id'] == 'taxon-2955291'))
        # Do not add an artificial task mapping. Register the population layout on
        # the real source task that unambiguously supplies this virus target.
        task = {3048459: 'evo-viral-a0a140d2t1-zikv-sourisseau-2019', 3428502: 'evo-viral-polg-cxb3n-mattenberger-2021',
                3052230: 'evo-viral-qi-hcv'}[tid]
        x.update(id=task + '-mapping-' + pop, task_id=task, population_id=pop, evidence_id=evidence,
            supporting_json=json.dumps([evidence, eid]), species_row='species:riboviria-other', all_species_row='allSpecies:riboviria-sp-' + str(tid))
        m = json.loads(x['metadata_json']); m.update(name=name, species=name, speciesId=tid, taxonomy=url, url=c.get('evidence', evidence)['url'],
            allSpeciesRow='riboviria-sp-' + str(tid), note='Named source-study viral target; original encoded cohort has separately stated limits.')
        x['metadata_json'] = json.dumps(m, ensure_ascii=False)
        c.put('coverage_mappings', x)


def model_review(c, d, method, code, release, available):
    architecture = method('architecture', 'A.1.1 and Supplementary Table 1', 6,
        'Evo 2 uses StripedHyena 2, alternating input-dependent Hyena-SE/MR/LI convolutions and RoPE self-attention with tied embedding/output weights. '
        'Paper variants: 40.3B parameters, 50 layers, width 8,192, FFN 22,528, 64 heads; 6.5B, 32 layers, width 4,096, FFN 11,264, 32 heads; '
        '1.1B base, 25 layers, width 1,920, FFN 5,120, 15 heads. The headline 40B/7B names are rounded model-family names.')
    training = method('training', 'A.1.2–A.1.5; Supplementary Tables 2–3', 6,
        'Autoregressive cross-entropy downweights annotated repetitive bases to 0.1. Outputs are uppercase bases; initial pretraining inputs can retain lowercase repeat information. '
        '40B base trains on 6.6T tokens at 1,024 context plus 2.1T at 8,192; 7B base on 2.1T at 8,192; 1B base on 1T at 8,192. '
        'Midtraining extends 7B through 32,768/65,536/131,072/262,144/524,288/1,048,576 contexts with 50B tokens each; '
        '40B uses 131,072/262,144/1,048,576 with 200B tokens each. RoPE combines positional interpolation and tenfold base-frequency increase per doubling. '
        'DMS, loss and synthetic categorical-Jacobian needle tests monitor extension; downstream biological evaluations generally use shorter task-specific contexts.')
    corpus = method('corpus', 'A.2.1–A.2.2; Supplementary Tables 8–9', 9,
        'OpenGenome2 contains 8.84 trillion curated nucleotides, distinct from repeated training tokens: 113,379 prokaryotic representative genomes (357B nt), '
        '6.98T eukaryotic genome nt, 854B metagenomic nt, 2.82B organellar nt and 602B functional-window augmentations. '
        'It reuses OpenGenome, expands GTDB from 214.1 to 220.0, curates NCBI eukaryotic references downloaded May 31, 2024, organelles, transcripts/ncRNAs and EPDnew promoters. '
        'Sequences from viruses infecting eukaryotic hosts are excluded. Random corpus validation samples are specified per data component, rather than a universal downstream chromosome/species exclusion.')
    token = method('tokenization', 'A.1 and A.2.2', 6,
        'Paper specifies byte tokenization at single-nucleotide resolution. Stitch marker # joins sequences of the same species with uncertain distance, while @ joins nearby same-contig/same-strand segments. '
        'Transcript augmentation adds upstream sequence and splice overhangs; midtraining stitches much longer genomes and adds uppercase Greengenes-style lineage strings. '
        'Conditioning/stitch tokens are loss-masked. This is not a k-mer or BPE tokenizer.')
    config = code('configuration', 'evo2/configs/evo2-40b-1m.yml',
        'Pinned inference configuration explicitly declares vocab_size=512, hidden_size=8192, num_layers=50, max_seqlen=1048576 and CharLevelTokenizer. '
        'Companion 7B/1B configurations declare the paper-matching hidden widths/layer counts and 1,048,576/8,192 maximum sequence lengths.', 1, 64)
    tokenizer = code('tokenizer-implementation', 'vortex/model/tokenizer.py',
        'CharLevelTokenizer encodes UTF-8 text bytes as integer IDs, with eos/eod 0 and pad 1; configured padded vocabulary is 512. '
        'Nucleotide text therefore has one token per nucleotide, while phylogenetic tags are multi-character token strings.',
        129, 192, repo='Zymrael/vortex', rev=VORTEX,
        path='research/artifacts/final-audit/evo2-diagnostics/Zymrael-vortex-8b00afe/vortex/model/tokenizer.py')
    props = [
        ('architecture', 'Architecture and paper model sizes', 'Original 1B/7B/40B paper family',
            'StripedHyena 2 Hyena-SE/MR/LI + RoPE attention; tied input/output weights. Paper sizes 1.1B/6.5B/40.3B parameters with 25/32/50 layers.', architecture),
        ('tokenization', 'Tokenization', 'Original paper and pinned inference implementation',
            'Single-character byte tokenization; one DNA base per token; padded vocabulary 512. #/@ stitching markers and multi-token lineage strings receive special data-processing/loss treatment.', token),
        ('pretraining', 'Curated corpus', 'OpenGenome2',
            '8.84T curated nucleotides: representative bacterial/archaeal genomes, eukaryotic genomes, metagenomes, organelles, transcripts/ncRNAs, promoter/genic-window augmentations. Data composition and sampling differ by training phase.', corpus),
        ('training', 'Training exposure and objective', '1B base / 7B / 40B',
            'Next-token loss with repeat weight 0.1. 1B base: 1T tokens; 7B: 2.1T base +0.3T extension; 40B: 8.7T base +0.6T extension. Corpus size and token exposure are different quantities.', training),
        ('context', 'Context extension', '7B and 40B',
            '7B extends through six stages from 32,768 to 1,048,576 tokens; 40B through 131,072, 262,144 and 1,048,576. Positional interpolation plus scaled RoPE; loss/DMS/needle evaluation after stages.', training),
        ('evaluation', 'Task-specific contexts and interfaces', 'Original-paper evaluation',
            'Variant/gene-disruption contexts are typically 8,192 bp; exon classification concatenates two 8,192-bp strand views. Generation, oracle guidance and synthetic retrieval have separate longer context protocols. A 1M model capacity is not proof that every biological benchmark used 1M context.', training),
        ('release', 'Original paper versus later releases', 'Pinned repository ' + REV[:12],
            'Original paper describes 1B base, 7B and 40B. Current repository additionally includes later 20B and phage-specialist releases; their separate examples/data are not retroactively assigned to the original study.', release)]
    for category, name, var, text, e in props:
        c.put('model_properties', dict(id='evo2-review-property-' + category, model_id='evo2', category=category,
            name=name, variant=var, value=text, status='source-reported', evidence_id=e,
            notes='Pinned configuration and data artifacts support specified fields; original training was not independently rerun.'))
        c.field('models', 'evo2', category, e)
    c.field('model_properties', 'evo2-review-property-tokenization', 'value', tokenizer)
    c.field('model_properties', 'evo2-review-property-tokenization', 'value', config)
    rev = '84d2a7e690c8bb395d1f4868822dfa031ea561c6'
    url = f'https://huggingface.co/datasets/arcinstitute/opengenome2/tree/{rev}'
    c.source('evo2-review-pretraining-release', 'OpenGenome2 pretraining corpus', url, 'dataset-repository', rev,
        CACHE + 'opengenome2-readme.md', notes='Complete dataset card and API file inventory inspected; very large pretraining shards not independently rescanned.')
    ep = c.evidence('evo2-review-pretraining-release-inspection', 'evo2-review-pretraining-release', 'Pinned dataset README and repository inventory',
        'OpenGenome2 is explicitly the pretraining release and provides component/stage corpus data. These partitions are not original downstream DMS, clinical, annotation or generation scored cohorts.', 'documentation')
    rid = c.resource('evo2-pretraining-resource', 'evo2-review-pretraining-release', 'OpenGenome2 pretraining corpus', 'dataset', 'huggingface', url, ep,
        revision=rev, notes='Model provenance; not counted as a released downstream evaluation dataset.')
    c.collection_resource('evo-original', rid, ep, 'upstream-data')
    c.field('models', 'evo2', 'pretraining_corpus', ep)
    c.review('models', 'evo2', 'Full original architecture/training/corpus/tokenization/context-extension methods; pinned inference configurations/tokenizer; current release scope; full dataset card/inventory.',
        [architecture, training, corpus, token, config, tokenizer, release, available, ep],
        'Weight tensors, pretraining shards and original assay scores were not independently regenerated. Later model releases are separate from original-paper evaluated checkpoints.')


def upstream_review(c, d, audit):
    """Exact source-study resources, without claiming an original Evo cohort."""
    meta = audit['depmap_upstream']
    url = 'https://api.figshare.com/v2/articles/27993248/versions/1'
    c.source('evo2-review-depmap-upstream', 'DepMap Public 24Q4 immutable file manifest', url,
        'dataset-manifest', meta['doi'], CACHE + 'depmap-24q4-metadata.json',
        notes='Complete version-one Figshare metadata/file inventory read. Large screen matrices were not independently rescanned; the Evo-specific gene filter/labels remain unreleased.')
    e = c.evidence('evo2-review-depmap-upstream-files', 'evo2-review-depmap-upstream',
        'Version 1 files: ScreenGeneEffect.csv, Gene.csv, AchillesScreenQCReport.csv',
        'Official immutable 24Q4 release lists the three files explicitly named by A.3.11. File identities, byte sizes and publisher checksums are preserved in the inspection manifest. '
        'The screen matrix is distinct from the model-level CRISPRGeneEffect matrix; no standard dependency threshold is assumed to be Evo 2’s threshold.', 'documentation')
    for item in meta['files']:
        if item['name'] not in ['ScreenGeneEffect.csv', 'Gene.csv', 'AchillesScreenQCReport.csv']:
            continue
        rid = 'evo2-depmap-upstream-' + item['name'].lower().replace('.', '-')
        c.source(rid + '-source', 'DepMap 24Q4 / ' + item['name'], item['download_url'],
            'dataset-file', meta['doi'] + '; ' + item['computed_md5'],
            notes='Exact public file identified through immutable publisher metadata; file values were not independently rescanned.')
        c.resource(rid, rid + '-source', 'DepMap 24Q4 / ' + item['name'], 'dataset', 'other',
            item['download_url'], e, revision=meta['doi'] + '; MD5 ' + item['computed_md5'],
            notes='Original upstream study input; not the Evo-filtered 16,434-gene, shuffled-CDS, binary-label cohort.')
        c.task_resource('evo-depmap', rid, e, 'upstream-data')
    decay = audit['decay_upstream']
    sid = 'evo2-review-decay-upstream'
    c.source(sid, 'GSE301426 breast-cancer SLAM-seq processed source data', decay['url'],
        'dataset-file', 'GSE301426; inspected ' + DATE,
        CACHE + 'GSE301426_BRCA_SLAM_CTratio_gs_counts.txt.gz',
        notes='Complete compressed source-study processed table read. GSE301535 superseries and four subseries metadata separately checked. The exact Evo-specific decay calculation/sequence join is not supplied.')
    c.get('sources', sid)['sha256'] = decay['sha256']
    e = c.evidence(sid + '-inspection', sid, 'Complete source table and GEO SOFT series/subseries metadata',
        f"GSE301426 is the SLAM-seq subseries of the cited Karner study, with {decay['rows']:,} processed source rows and {len(decay['columns'])} table columns. "
        'Its file has one gene identifier and twelve source cell/replicate C/T-ratio measurement columns, rather than a ready-to-use Evo-scored decay cohort. '
        'The source GreyHound repository has model code/weights but no processed decay matrix or Evo-specific sequence-score file.', 'data')
    rid = c.resource('evo2-decay-upstream-resource', sid, 'Karner SLAM-seq C/T-ratio table', 'dataset', 'other', decay['url'], e,
        revision='GSE301426; SHA-256 ' + decay['sha256'],
        notes='Source-study processed observations, not a claim that every source row was retained in the original Evo 2 decay evaluation.')
    c.task_resource('evo-mrna-decay', rid, e, 'upstream-data')
    c.field('tasks', 'evo-mrna-decay', 'upstream-source', e)
    c.limit('tasks', 'evo-mrna-decay', 'evo-specific-decay-sequence-join', 'not-released',
        'The SLAM-seq source table is public, but the original Evo 2 per-transcript decay transformation, source-file/version selection, reference sequence join and final retained score cohort are not in the inspected official release.', e)


def named_population_review(c, d, audit):
    """Replace coarse origins only where exact evaluated source species are given."""
    e_exon = 'evo2-review-exon'
    e_gen = 'evo2-review-evo-gen-completion-generation'
    replacement = {'evo-exon-intron': {'animals', 'plants'}, 'evo-gen-completion': {'bacteria', 'archaea'},
                   'evo-gen-bacterial-genome': {'bacteria'}}
    for table in ['task_populations', 'coverage_mappings']:
        d[table] = [r for r in d[table] if not (r['task_id'] in replacement and r['population_id'] in replacement[r['task_id']])]
    for tid, pop, eid in [
        ('evo-gen-completion', 'ecoli', e_gen), ('evo-gen-completion', 'taxon-2246', e_gen),
        ('evo-exon-intron', 'human', e_exon), ('evo-exon-intron', 'mouse', e_exon),
        ('evo-exon-intron', 'zebrafish', e_exon), ('evo-exon-intron', 'barley', e_exon)]:
        c.population(tid, pop, eid,
            'Explicitly named reference-gene generation species.' if tid == 'evo-gen-completion' else
            'One of eight explicitly named final exon/intron test species; this does not name the entire PANTHER training panel.')
    for filename, meta in audit['named_taxonomy'].items():
        taxid = meta['tax_id']; name = meta['current_scientific_name']['name']
        node = 'mycoplasmatota' if taxid == 2097 else 'lycophytes' if taxid == 88036 else 'eudicots'
        if node == 'lycophytes' and not any(r['id'] == node for r in d['coverage_nodes']):
            c.put('populations', dict(id=node, name='Lycopodiopsida', rank='class', parent_id='vascular', ncbi_taxid=1521260,
                notes='Lycophytes are vascular, spore-producing land plants; separate from seed plants and ferns.'))
            c.put('coverage_nodes', dict(id=node, parent_id='vascular', population_id=node, label='Lycophytes',
                scientific='Lycopodiopsida', rank='Class', note='', section='cellular', jump=None,
                sources_json=json.dumps(['https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1521260'])))
            model = copy.deepcopy(c.get('coverage_rows', 'clade:eudicots'))
            m = json.loads(model['metadata_json'])
            nodes = {n['id']: n for n in d['coverage_nodes']}
            path = []; here = node
            while here:
                path.append(here); here = nodes[here]['parent_id']
            path.reverse()
            m.update(id=node, label='Lycophytes', displayLabel='Lycophytes', node=node, common='',
                path=path[1:], displayPath=path, displayParent=node,
                lineageLabel=' → '.join(nodes[n]['label'] for n in path[1:]),
                displayLineage=' → '.join(nodes[n]['label'] for n in path),
                note='Selaginella supplies a named original Evo 2 exon/intron test species; not a claim of broader lycophyte evaluation.')
            model.update(id='clade:' + node, view='clade', row_key=node, node_id=node,
                population_ids_json='[]', metadata_json=json.dumps(m, ensure_ascii=False))
            c.put('coverage_rows', model)
        pop = 'taxon-' + str(taxid)
        if not any(r['id'] == pop for r in d['populations']):
            c.put('populations', dict(id=pop, name=name, rank='species', ncbi_taxid=taxid,
                parent_id=c.get('coverage_nodes', node)['population_id'], notes='Current NCBI species; original publication synonym retained in task text.'))
        sid = 'evo2-review-named-taxonomy-' + str(taxid)
        url = 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=' + str(taxid)
        c.source(sid, 'NCBI taxonomy: ' + name, url, 'taxonomy', DATE, CACHE + filename)
        te = c.evidence(sid + '-classification', sid, 'Classification and parents',
            name + '; current NCBI taxonomy: ' + json.dumps(meta['classification']) + '. Publication synonym is not interpreted as a separate organism.', 'documentation')
        task = 'evo-gen-bacterial-genome' if taxid == 2097 else 'evo-exon-intron'
        eid = 'evo2-review-evo-gen-bacterial-genome-generation' if taxid == 2097 else e_exon
        c.put('task_populations', dict(task_id=task, population_id=pop, variant_id=None, relation='sequence-origin',
            coverage='Source names this evaluated reference species. Exon-test association does not claim membership of every species in the training panel.', evidence_id=eid),
            ('task_id', 'population_id', 'relation'))
        base = c.get('coverage_rows', 'clade:' + node)
        bp = set(json.loads(base['population_ids_json'])); bp.add(pop); base['population_ids_json'] = json.dumps(sorted(bp))
        cm = json.loads(base['metadata_json']); allkey = node + '-sp-' + str(taxid); specieskey = node + '-other'
        for view, key, named in [('species', specieskey, False), ('allSpecies', allkey, True)]:
            old = next((r for r in d['coverage_rows'] if r['id'] == view + ':' + key), None)
            m = json.loads(old['metadata_json']) if old else copy.deepcopy(cm)
            ps = set(json.loads(old['population_ids_json']) if old else []); ps.add(pop)
            names = set(m.get('members', []) if old else []); names.add(name)
            m.update(id=key, label=name if named else 'Other named species', displayLabel=name if named else 'Other named species',
                clade=node, cladeLabel=cm['label'], kind='species' if named else 'other', common='', members=sorted(names),
                note='Named evaluated species from source methods; no unresolved taxon is implied.')
            c.put('coverage_rows', dict(id=view + ':' + key, view=view, row_key=key, node_id=node,
                population_ids_json=json.dumps(sorted(ps)), metadata_json=json.dumps(m, ensure_ascii=False)))
        c.put('coverage_mappings', dict(id=task + '-mapping-' + pop, task_id=task, population_id=pop,
            basis='Exact named source species and NCBI lineage', evidence_id=eid, supporting_json=json.dumps([eid, te]),
            clade_row='clade:' + node, species_row='species:' + specieskey, all_species_row='allSpecies:' + allkey,
            metadata_json=json.dumps(dict(row=specieskey, name=name, basis='Exact named source species and NCBI lineage',
                species=name, speciesId=taxid, clade=node, allSpeciesRow=allkey, url=c.get('evidence', eid)['url'], taxonomy=url), ensure_ascii=False)))
