"""NTv3 v2: task/track decomposition from complete methods and released manifests.

Authoring only; populate(d) never writes canonical files. Assay identities and BED
partitions are artifact-inspected; raw BigWig signals and gated weights are not.
"""
import copy
import json
from collections import Counter, defaultdict
from common import Catalogue, ROOT
from taxonomy_layout import TaxonomyLayout

ART = json.loads((ROOT / 'data/ntv3-artifact-inspections.json').read_text())
SRC = json.loads((ROOT / 'data/ntv3-source-inspections.json').read_text())
PMC = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13733737/'
XLS = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/13733737/bin/media-1.xlsx'
SUP = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/13733737/bin/NIHPP2025.12.22.695963v2-supplement-2.pdf'


def populate(d):
    c = Catalogue(d)
    layout = TaxonomyLayout(d)
    for name, payload in SRC.get('taxonomy_additions', {}).items():
        layout.records[name] = payload['reports'][0]['taxonomy']
    sheet = lambda n: next(s['rows'] for s in ART['sheets'] if s['name'].startswith(f'Supp Table {n} '))
    def pe(slug, locator, text):
        return c.evidence('ntv3-final-' + slug, 'ntv3-paper', locator, text)
    def we(slug, n, text):
        return c.evidence('ntv3-final-' + slug, 'ntv3-complete-workbook', f'Supplementary Table C.{n}; complete worksheet inspection', text, 'data')
    c.source('ntv3-complete-workbook', 'NTv3 v2 complete supplementary workbook', XLS,
        'supplementary-data', 'bioRxiv v2, 2026-10-29; media-1.xlsx',
        notes='All ten worksheets read. Exact rows are committed in data/ntv3-artifact-inspections.json; track identities/results are not raw signal tensors.')
    c.get('sources', 'ntv3-complete-workbook')['sha256'] = ART['workbook_sha256']
    c.source('ntv3-complete-supplement', 'NTv3 v2 complete supplementary notes and figures', SUP,
        'supplementary-paper', 'bioRxiv v2, 2026-10-29; 38 pages',
        notes='Complete supplement inspected, including dataset processing, annotation grammar, protein analyses, BUSCO and benchmark qualifications.')
    c.get('sources', 'ntv3-complete-supplement')['sha256'] = SRC['supplement']['sha256']
    architecture = pe('architecture', 'Methods 4.1–4.2',
        '703M-parameter U-Net backbone, 711M with functional head: seven 2-fold pooling stages to 128-bp tokens, a 14-layer global-attention transformer, and seven upsampling stages with skip connections. '
        'Eight query/two KV heads, 192-dimensional heads. Single-base vocabulary: 11 tokens during pretraining, expanded to 16 with lowercase soft-masked bases for tracks/annotation. '
        'Species conditioning acts only on the functional head; annotation and diffusion are separate adapted checkpoints.')
    training = pe('training', 'Methods 4.2, 4.3 and 4.3.9',
        'Filtered OpenGenome2 contributes approximately 8T unique nucleotides; sequences under 1 kb and eukaryotic-genome sequences under 32 kb are removed. '
        'MLM uses 15% selected positions with 80/10/10 mask/random/unchanged corruption. Pretraining processes 5.6T tokens at mixed 1–8 kb, then seven roughly 50B-token context extensions through 1 Mb. '
        'Functional post-training updates the backbone/head at 131,072 bp for 2.5T tokens, then 1,048,576 bp for 1T; only central 37.5% is supervised. '
        'A later mixed-length checkpoint samples 16 kb–1 Mb and is selected after 5B tokens on validation accuracy at shorter lengths.')
    native = pe('native-protocol', 'Methods 4.3.1–4.3.9',
        'Human/mouse use Borzoi fold 3 test, fold 4 validation and other folds training. Other species use 1-Mb gene-aware intervals, BioMart homology-weighted connectivity and MCL, selecting inflation by modularity and assigning clusters to partitions. '
        'Low-homology edges are pruned when needed for Arabidopsis, worm and rice. Training inputs overlap at stride 0.1% of input length; evaluation strides by the central 37.5% so scored centers abut. '
        'Track scaling divides by a reported training-split nonzero mean, applies power 0.75 to RNA-seq assays and soft clipping above 10. '
        'Test Pearson concatenates all central positions per track, predominantly after log1p, then averages tracks within species/assay; human ATAC is the stated raw-signal exception.')
    manifest = we('native-manifest', 1,
        'C.1 has 16,262 rows and 16,262 unique file IDs in 15 species. RNA library labels remain in metadata; DNASE-seq and DNase-seq are the same assay family. '
        'Wheat has 762 RNA-seq and 14 histone ChIP-seq tracks, with no ATAC entry. Mouse has 2,450 rows including ten GRO-seq tracks. '
        'These counts are track identities, not sequence windows or independently validated experimental examples.')
    result_panel = we('native-results-panel', 5,
        'C.5 has 16,260 unique track result rows, including ten mouse GRO-seq tracks. Relative to C.1 it omits rice SRX11246453 (H3K9me2) and maize SRX12330305 (H3K4me3), without adding or duplicating IDs. '
        'The prose total 16,252 excludes GRO-seq and is not the C.5 row count.')
    for slug, category, name, value, eid in [
        ('architecture', 'architecture', 'Architecture', '703M backbone / 711M with tracks head; U-Net at 1-bp output resolution; 128-fold compression; 14 global-attention layers at 2048 width.', architecture),
        ('tokenization', 'tokenization', 'Tokenization', 'Single-base tokens; 11-token pretraining vocabulary, 16-token soft-masked tracks/annotation vocabulary; learned pooling is architectural compression, not k-mer tokenization.', architecture),
        ('pretraining', 'pretraining', 'Pretraining corpus and objective', 'Approximately 8T unique filtered OpenGenome2 nucleotides; MLM. Mixed 1–8 kb initial training followed by seven context extensions to 1 Mb.', training),
        ('context', 'context', 'Training and evaluated context', 'MLM to 1 Mb; functional post-training 131 kb then 1 Mb with 37.5% scored centers. Main results use single-length 1-Mb weights; mixed-length release is a distinct checkpoint. Standardized adaptation uses 32,768-bp input / 12,288-bp output.', training),
        ('functional-data', 'training', 'Functional supervision', '16,262 individually indexed assay tracks across 15 species; exact species × assay identity is linked to tasks. C.5 reports 16,260 track results.', manifest)]:
        c.put('model_properties', dict(id='ntv3-final-' + slug, model_id='ntv3', category=category,
            name=name, variant=None, value=value, status='reported / source-audited', evidence_id=eid,
            notes='October 2026 v2 family; earlier 100M/650M NTv3 checkpoints in external papers are not asserted equivalent.'))

    def clear_pops(tid):
        d['task_populations'] = [r for r in d['task_populations'] if r['task_id'] != tid]
        d['coverage_mappings'] = [r for r in d['coverage_mappings'] if r['task_id'] != tid]
    def new_task(tid, name, dataset, target, typ, eid, features, capabilities,
                 description, output='One source-defined value per example', form='isolated', structure='none', apps=('genome-annotation',), limitations=''):
        c.put('tasks', dict(id=tid, name=name, dataset_name=dataset, target=target, task_type=typ,
            description=description, label_basis='Source-defined experimental/reference target; linked protocols distinguish diagnostic responses.',
            status='paper-audited', evidence_id=eid, limitations=limitations,
            input_description='DNA sequence with source-specific context, conditioning and preprocessing.', output_description=output))
        for cat in features + list(capabilities) + list(apps):
            c.category(tid, cat, eid, 'Classification follows the source-defined target, input context and scored output.')
        c.output(tid, form, eid, output, 'Source-defined example / locus',
            axis='contiguous' if form in ['dense-labels', 'signal-profile'] else 'linked' if form == 'linked-structure' else 'none',
            structure=structure, limitations=limitations)
        if 'cds' in features:
            c.put('task_feature_scopes', dict(id=tid + '-cds-scope', task_id=tid, feature_id='cds',
                scope='restricted-target', rationale='Scored structures/proteins explicitly derive from CDS; UTR-inclusive outputs are not implied.', evidence_id=eid))
        c.member(tid, 'ntv3-evals', eid)
        return tid
    def variant(tid, vid, name, eid, length, tracks=None, notes='', revision='NTv3 v2 complete supplementary workbook'):
        c.put('variants', dict(id=vid, task_id=tid, name=name, dataset_revision=revision,
            context=notes, input_length=length, target_count=tracks, target_unit='tracks / source-specific outputs', notes=notes, evidence_id=eid))
    # Track tables are large; keyed upserts avoid quadratic scans.
    track_index = {r['id']: r for r in d.setdefault('assay_tracks', [])}
    task_track_index = {(r['task_id'], r['track_id']): r for r in d.setdefault('task_tracks', [])}
    def track(tid, sid, prefix, row, pop, assay, eid, vid, key='file_id'):
        rid = prefix + str(row[key])
        r = dict(id=rid, source_id=sid, source_track_id=str(row[key]), population_id=pop,
            assay=assay, metadata_json=json.dumps(row, ensure_ascii=False), evidence_id=eid)
        if rid in track_index: track_index[rid].update(r)
        else: d['assay_tracks'].append(r); track_index[rid] = r
        r = dict(task_id=tid, track_id=rid, variant_id=vid, evidence_id=eid)
        if (tid, rid) in task_track_index: task_track_index[(tid, rid)].update(r)
        else: d['task_tracks'].append(r); task_track_index[(tid, rid)] = r

    family = {'ATAC-seq': 'atac', 'DNase-seq': 'dnase', 'DNASE-seq': 'dnase', 'CAGE': 'cage',
        'RNA-seq': 'rna', 'total RNA-seq': 'rna', 'polyA plus RNA-seq': 'rna',
        'Histone ChIP-seq': 'histone', 'TF ChIP-seq': 'tf', 'GRO-seq': 'gro',
        'ribo-seq': 'ribo', 'PRO-cap': 'procap', 'eCLIP': 'eclip', 'ChIP-seq': 'chip'}
    labels = {'atac': 'ATAC-seq accessibility', 'dnase': 'DNase-seq accessibility', 'cage': 'CAGE transcription initiation',
        'rna': 'RNA-seq coverage', 'histone': 'Histone ChIP-seq signal', 'tf': 'TF ChIP-seq signal',
        'gro': 'GRO-seq nascent transcription', 'ribo': 'Ribo-seq footprint coverage', 'procap': 'PRO-cap transcription initiation',
        'eclip': 'eCLIP RNA-binding signal', 'chip': 'ChIP-seq signal with unspecified target family'}
    regions = {'atac': ['regulatory'], 'dnase': ['regulatory'], 'cage': ['promoter'], 'rna': ['gene'],
        'histone': ['genome'], 'tf': ['tfbs'], 'gro': ['gene'], 'ribo': ['gene'], 'procap': ['promoter'], 'eclip': ['gene'], 'chip': ['genome']}
    groups = defaultdict(list)
    for row in sheet(1): groups[(family[row['assay']], row['species'])].append(row)
    for slug in sorted({g[0] for g in groups}):
        tid = 'ntv3-tracks-' + slug
        if not any(t['id'] == tid for t in d['tasks']):
            new_task(tid, labels[slug], 'NTv3 15-species functional-track corpus', labels[slug], 'profile regression', manifest,
                regions[slug], ['signal-profile-prediction', 'context-specific', 'long-context'],
                'Predict quantitative base-resolution tracks under a species-conditioned functional head.',
                output='Position × assay-track nonnegative quantitative signal', form='signal-profile')
        t = c.get('tasks', tid)
        t.update(description='Base-resolution assay coverage; exact per-track identities and source species are indexed from C.1. RNA library types remain metadata variants.',
            output_description='Position × assay-track quantitative signal; not a categorical annotation track.',
            input_description='1,048,576-bp genomic input; species-conditioned head; central 393,216-bp scored output.',
            limitations='Track identities and result-table membership inspected; raw signal tensors and published correlations were not independently recomputed.', evidence_id=manifest)
        clear_pops(tid)
        # Remove the superseded broad, uncounted output variant.
        d['variants'] = [v for v in d['variants'] if v['id'] != tid + '-tracks']
        c.output(tid, 'signal-profile', manifest, t['output_description'], 'Genomic base × track', axis='contiguous', limitations=t['limitations'])
        c.category(tid, 'signal-profile-prediction', native, 'The quantitative positional target requires a native profile head.')
        pid = tid + '-protocol'
        c.protocol(pid, tid, 'Native 1-Mb functional-track post-training', 'functional post-training; all backbone/head weights updated',
            'DNA → shared trunk → species-conditioned functional head; central 37.5% of each input.',
            'Human/mouse: Borzoi fold 3 test / fold 4 validation. Other species: gene-aware 1-Mb homology graph/MCL partitions; train and evaluated windows follow source-specific strides.',
            'Genomic interval / homology cluster', native, [('pearson', 'Concatenate scored bases per track; log1p except stated raw human ATAC analysis; unweighted mean over tracks within species/assay.')],
            fitted='All trunk and functional-head parameters', selection='Select post-training checkpoints on validation partitions.', notes=t['limitations'])
        c.use(tid, 'ntv3', 'ntv3', native, pid)
    native_pops = {}
    for (slug, species), rows in sorted(groups.items()):
        tid = 'ntv3-tracks-' + slug
        vid = tid + '-' + species.lower().replace(' ', '-')
        variant(tid, vid, species + ': ' + labels[slug], manifest, '1,048,576 bp input; 393,216 bp output', len(rows),
            notes='RNA library labels, strand, biosample, assay target and source file ID are retained on individual track rows.')
        pop = layout.link(tid, species, manifest, vid, note='Exact C.1 functional supervision/evaluation species for this assay; no extrapolation from training taxonomy.')
        native_pops[species] = pop
        c.count(tid, len(rows), 'source track identities', manifest, split='native corpus', variant=vid, method='measured',
            qualifier='Complete C.1 identity-table scan; not sequence-window count or raw-signal validation.')
        for row in rows: track(tid, 'ntv3-complete-workbook', 'ntv3-native-', row, pop, row['assay'], manifest, vid)
    c.limit('evaluations', 'ntv3-evals', 'native-source-counts', 'conflicting',
        'C.1: 16,262 identities, including ten GRO-seq tracks; C.5: 16,260 distinct result rows. C.5 omits rice SRX11246453 and maize SRX12330305, both histone tracks. '
        'The prose 16,252 total excludes GRO-seq. Main Table 5 places wheat’s 14 non-RNA tracks differently; C.1 identifies them as histone ChIP-seq, not ATAC.', result_panel)

    # Standardized 155-track release: seven dataset × target assay families.
    benchrev = SRC['benchmark']['revision']
    benchroot = f'https://huggingface.co/datasets/{SRC["benchmark"]["id"]}'
    c.source('ntv3-benchmark-metadata', 'NTv3 revised benchmark track manifest',
        benchroot + f'/blob/{benchrev}/benchmark_metadata.tsv', 'dataset-manifest', benchrev,
        notes='All 155 metadata rows and all eleven split BEDs inspected. BigWig signal arrays and reference FASTA bases were not rescanned.')
    c.get('sources', 'ntv3-benchmark-metadata')['sha256'] = ART['benchmark_metadata_sha256']
    bmeta = c.evidence('ntv3-final-benchmark-manifest', 'ntv3-benchmark-metadata',
        'All 155 track records; eleven complete split BED scans',
        'Release has 155 tracks across eleven species: seven assay families when RNA library variants are retained together, with Ribo-seq, eCLIP and PRO-cap distinct from RNA coverage. '
        'Split BEDs list non-overlapping genomic intervals, not whole-chromosome holdouts in every species. Same chromosomes can contribute distinct intervals to multiple partitions.', 'data')
    bprotocol = pe('benchmark-protocol', 'Methods 4.6; Table 7; Supplementary C.4',
        'Every model is adapted at 32,768-bp input with 12,288 central 1-bp outputs; one multi-output head per species–dataset, all backbone parameters updated. '
        'Ten epochs, effective batch 32; select best validation mean Pearson from twenty evaluations/epoch on up to 1,000 sampled windows. '
        'Three seeds except Evo 2 one seed. Evo 2 is the 1B 8k checkpoint extended during fine-tuning, evaluated only on human/Arabidopsis/rice/maize/tomato and uses Adam/BF16/FP32 gradient accumulation. '
        'Other pretrained backbones use AdamW; random-init convolutional baselines are not released SpliceAI weights. Test correlations are computed in transformed target space.')
    space_rev = SRC['space']['revision']
    tutfile = 'notebooks_tutorials/02_fine_tuning_bigwig_tracks.ipynb'
    tuturl = f'https://huggingface.co/spaces/{SRC["space"]["id"]}/blob/{space_rev}/{tutfile}'
    c.source('ntv3-benchmark-tutorial', 'NTv3 pinned benchmark fine-tuning tutorial', tuturl,
        'notebook', space_rev, notes='Benchmark and small frozen-trunk Colab modes are separate. Full notebook source inspected.')
    c.get('sources', 'ntv3-benchmark-tutorial')['sha256'] = next(x['sha256'] for x in SRC['source_files'] if x['file'] == tutfile)
    tutorial = c.evidence('ntv3-final-benchmark-tutorial', 'ntv3-benchmark-tutorial',
        'GenomeBigWigDataset, TargetsScaler, benchmark configuration and random_subset',
        'Benchmark mode updates the trunk and samples up to 1,000 fixed random validation and test windows. Candidate windows fit entirely inside a BED interval; validation/test stride is 32,768 bp. '
        'Training overlap 0.999 gives a 32-bp integer stride. Metadata means are applied directly, RNA-seq uses power 0.75 and soft clipping, and NaN BigWig values become zero. '
        'Colab mode freezes the trunk and is not the paper’s full-backbone comparison.', 'code')
    bgr = defaultdict(list)
    for row in ART['benchmark_metadata']: bgr[(family[row['assay']], row['species_common_name'])].append(row)
    bspecies = {r['species_common_name']: ('Homo sapiens' if r['species_name'] == 'human' else r['species_name'].replace('_', ' ').capitalize()) for r in ART['benchmark_metadata']}
    splitrows = {r['species']: r for r in ART['splits']}
    for slug in sorted({g[0] for g in bgr}):
        tid = 'ntv3-benchmark-' + slug
        new_task(tid, 'NTv3 Benchmark: ' + labels[slug], 'NTv3 revised 155-track benchmark', labels[slug], 'profile regression', bmeta,
            regions[slug], ['signal-profile-prediction'],
            'Joint multi-output species adaptation; individual tracks retain experiment, assembly and assay identity.',
            output='12,288 positions × matched species assay tracks', form='signal-profile',
            limitations='Metadata and split intervals inspected; source signal tensors were not read. Candidate windows differ from sampled evaluation windows.')
        for (f, species), rows in sorted(bgr.items()):
            if f != slug: continue
            vid = tid + '-' + species
            variant(tid, vid, bspecies[species] + ': ' + labels[slug], bmeta, '32,768 bp input / 12,288 bp output', len(rows),
                notes='All species tracks are jointly optimized even though assay-family targets are catalogued separately.', revision=benchrev)
            pop = layout.link(tid, bspecies[species], bmeta, vid, note='Exact benchmark metadata sequence species; training corpus is not used as evaluation coverage.')
            pid = vid + '-finetune'
            c.protocol(pid, tid, 'Common full-backbone species adaptation', 'full fine-tune',
                'Replace released head with normalization/linear/softplus output head; jointly fit every target track of this species.',
                'Use exact released genomic train/val/test intervals; overlapping chromosomes do not imply overlapping intervals. Select validation checkpoint; evaluate held-out test windows.',
                'Genomic interval / sampled window', bprotocol, [('pearson', 'Per track over evaluated central positions in transformed space; mean across tracks, then seed mean.')],
                fitted='All backbone parameters plus new head', selection='Best validation mean Pearson; ten-epoch budget; three seeds for NTv3.', variant=vid,
                notes='Public tutorial benchmark mode uses up to 1,000 fixed random test windows; small Colab frozen-head mode is separate.')
            c.use(tid, 'ntv3', 'ntv3', bprotocol, pid)
            for row in rows: track(tid, 'ntv3-benchmark-metadata', 'ntv3-benchmark-', row, pop, row['assay'], bmeta, vid)
            c.count(tid, len(rows), 'assay track identities', bmeta, variant=vid, protocol=pid, method='measured', qualifier='Complete metadata scan; tracks are not sequence examples.')
            st = splitrows[species]
            for part, value in st['partitions'].items():
                c.count(tid, value, 'released genomic intervals', bmeta, split=part, variant=vid, protocol=pid, method='measured', qualifier='Complete split BED; an interval can yield many windows.')
                c.count(tid, st['bases'][part], 'partition bp', bmeta, split=part, variant=vid, protocol=pid, method='measured', qualifier='Sum of nonoverlapping BED spans; not a window count.')
                if part in ['val', 'test']:
                    candidates = sum(max(0, (int(r[2]) - int(r[1]) - 32768) // 32768 + 1) for r in st['intervals'] if r[3] == part)
                    c.count(tid, min(1000, candidates), 'tutorial sampled windows', tutorial, split=part, variant=vid, protocol=pid,
                        method='derived', qualifier='Derived exactly from BED intervals and pinned tutorial 32,768-bp stride / 1,000-window cap. Not asserted to identify historical paper-time random draws.')
            # Explicit model/species coverage of the independently evaluated Evo 2 baseline.
            if species in ['human', 'arabidopsis', 'rice', 'maize', 'tomato']:
                ep = vid + '-evo2-finetune'
                c.protocol(ep, tid, 'Evo 2 1B 8k checkpoint adapted to 32 kb', 'full fine-tune',
                    'evo2/1b-8k-bf16:1.0 backbone plus new profile head; 32,768-bp inputs, beyond native 8,192-token pretraining context.',
                    'Same released species genomic intervals as the NTv3 comparison; one seed, same ten-epoch nominal budget.',
                    'Genomic interval / sampled window', bprotocol, [('pearson', 'Per track over evaluated transformed targets; one seed, no seed error bar.')],
                    fitted='All backbone/head parameters; Adam, BF16 parameters, FP32 accumulation, gradient clip 1.0', variant=vid)
                c.use(tid, 'evo2', 'ntv3', bprotocol, ep, provenance='external-evaluation',
                    note='Independent NTv3 benchmark baseline, not an original Evo 2 paper evaluation; this species/assay only.')
            if species in ['arabidopsis', 'rice', 'maize', 'tomato'] and any(m['id'] == 'plantcad2' for m in d['models']):
                c.use(tid, 'plantcad2', 'ntv3', bprotocol, pid, provenance='external-evaluation',
                    note='PlantCAD2 Small backbone fully fine-tuned in this independent species benchmark.')
            rid = 'ntv3-benchmark-split-' + species
            sid = rid + '-source'
            url = benchroot + f'/blob/{benchrev}/{species}/splits.bed'
            c.source(sid, 'NTv3 benchmark ' + species + ' genomic partitions', url, 'split-manifest', benchrev,
                notes='Complete BED read; no overlapping coordinate intervals across partitions in the inspected file.')
            c.get('sources', sid)['sha256'] = st['sha256']
            c.resource(rid, sid, species + ': train/validation/test intervals', 'manifest', 'huggingface', url, bmeta, revision=benchrev)
            c.task_resource(tid, rid, bmeta, 'split-manifest', vid)
    c.limit('evaluations', 'ntv3-evals', 'benchmark-normalization-mean', 'conflicting',
        'Methods 4.3 describes training-split-only nonzero track means; the released benchmark card/tutorial describes metadata means as genome-wide and applies them directly. '
        'Raw signals were not recomputed to resolve the normalization-statistic provenance; this is not asserted to prove data leakage.', tutorial)
    return _finish(c, layout, pe, we, new_task, variant, track, clear_pops, manifest, native, bmeta, bprotocol, tutorial)


def _finish(c, layout, pe, we, new_task, variant, track, clear_pops, manifest, native, bmeta, bprotocol, tutorial):
    """Other primary-paper tasks and final source/resource reviews."""
    d = c.data
    sheet = lambda n: next(s['rows'] for s in ART['sheets'] if s['name'].startswith(f'Supp Table {n} '))
    fam = {'ATAC-seq': 'atac', 'DNase-seq': 'dnase', 'CAGE': 'cage', 'RNA-seq': 'rna',
        'Histone ChIP-seq': 'histone', 'TF ChIP-seq': 'tf', 'ChIP-seq': 'chip', 'PRO-cap': 'procap'}
    region = {'atac': ['regulatory'], 'dnase': ['regulatory'], 'cage': ['promoter'], 'rna': ['gene'],
        'histone': ['genome'], 'tf': ['tfbs'], 'chip': ['genome'], 'procap': ['promoter']}
    borzoi = pe('borzoi', 'Methods 4.5: Borzoi comparison; Supplementary C.7',
        'Borzoi comparison uses fold 3 final test and fold 4 validation, with fold-4 scores separately published for comparison to AlphaGenome. '
        'Native 32-bp Borzoi predictions are repeated to 1-bp targets after inverse scaling, then log1p-scored; this does not create sub-bin information. '
        'A separate all-parameter NTv3 fine-tune replaces the head with the 7,611-track human Borzoi panel and scores matched 32-bp outputs. GTEx tracks are excluded from this matched comparison.')
    borzoi_meta = we('borzoi-track-panel', 7,
        'C.7 lists 7,611 unique human track IDs with assay and per-track fold/resolution/model results: 232 ATAC, 674 DNase, 1,276 CAGE, 1,543 RNA, 1,959 histone, 1,833 TF and 94 untyped ChIP tracks. '
        'The latter are not silently assigned to histone or TF families. This panel is not presumed identical to the incompletely identified AIDO.DNA2 subset.')
    shared = {'tf': 'aido2-coverage-tf-chip', 'histone': 'aido2-coverage-histone-chip',
        'dnase': 'aido2-coverage-dnase', 'cage': 'aido2-coverage-cage', 'rna': 'aido2-coverage-rna'}
    by_assay = defaultdict(list)
    for row in sheet(7): by_assay[fam[row['Assay']]].append(row)
    borzoi_tids = []
    for slug, rows in sorted(by_assay.items()):
        tid = shared.get(slug, 'ntv3-borzoi-' + slug)
        if slug not in shared:
            new_task(tid, 'Borzoi: ' + rows[0]['Assay'] + ' profile', 'Borzoi human functional-track release',
                rows[0]['Assay'] + ' coverage', 'profile regression', borzoi,
                region[slug], ['signal-profile-prediction', 'long-context'],
                'Predict the human functional-track release with source-specific resolution and adaptation protocols.',
                output='Genomic position/bin × assay track quantitative signal', form='signal-profile')
        else:
            t = c.get('tasks', tid)
            t.update(name='Borzoi: ' + rows[0]['Assay'] + ' profile', dataset_name='Borzoi functional-track release',
                description='Dense assay coverage prediction; NTv3 and AIDO.DNA2 have distinct fitting, target-panel and context variants.',
                input_description='Protocol-specific genomic windows and native or adapted track heads.',
                output_description='Genomic position/bin × assay track quantitative signal',
                limitations='AIDO.DNA2 does not identify its complete per-family panel or geometry. The NTv3 comparison identifies its human C.7 panel and resolution/fold protocols separately; their exact cohort equivalence is not assumed.')
            c.field('tasks', tid, 'dataset_name', borzoi_meta, 'Same named dataset × assay target reused; model-specific panels remain variants.')
        borzoi_tids.append(tid)
        c.member(tid, 'ntv3-evals', borzoi, note='NTv3-specific panel and protocols; not an AIDO adapter experiment.')
        vid = 'ntv3-borzoi-' + slug + '-human-tracks'
        variant(tid, vid, 'NTv3 human Borzoi comparison panel', borzoi_meta,
            '1-Mb NTv3 input; native 32-bp or matched 1-bp scored targets', len(rows),
            notes='C.7 track IDs; separate native 1-bp/log1p evaluation and all-parameter 32-bp adaptation.')
        pop = layout.link(tid, 'Homo sapiens', borzoi_meta, vid, note='Human-only NTv3 Borzoi comparison panel; AIDO species eligibility remains protocol-specific.')
        for row in rows: track(tid, 'ntv3-complete-workbook', 'ntv3-borzoi-', row, pop, row['Assay'], borzoi_meta, vid, 'Track ID')
        for arm, adaptation, output in [('native-1bp', 'native functional predictor; no benchmark fitting', 'Native functional outputs inverted to physical scale then log1p; Borzoi 32-bp bins repeated at 1 bp.'),
                                         ('matched-32bp', 'full fine-tune', 'Replace head with human 7,611-track panel; update all backbone/head parameters at matched 32-bp target resolution.')]:
            pid = 'ntv3-borzoi-' + slug + '-' + arm
            c.protocol(pid, tid, 'NTv3 / Borzoi ' + arm, adaptation, output,
                'Borzoi fold 4 model selection; fold 3 final test. Fold 4 also reported for comparison to published AlphaGenome results, with its selection role retained.',
                'Borzoi genomic fold', borzoi, [('pearson', 'Per track across complete evaluated regions; unweighted assay mean.')],
                variant=vid, fitted='All trunk and new head parameters' if arm == 'matched-32bp' else 'None added',
                notes='Human panel only. Native grids, transforms and different adaptation arms are not conflated.')
            c.use(tid, 'ntv3', 'ntv3', borzoi, pid)
        c.count(tid, len(rows), 'human assay tracks', borzoi_meta, variant=vid, method='measured', qualifier='Complete C.7 track-identity/result table; not sequence-window count.')

    ag = pe('alphagenome', 'Methods 4.5: AlphaGenome comparison; Supplementary C.8',
        'Five separate all-parameter NTv3 fine-tunes use released human 1-bp ATAC, DNase, CAGE, PRO-cap and RNA targets, each at 1-Mb input with a new assay head. '
        'Score 6,853 held-out 196,608-bp windows corresponding to Borzoi fold 4 (NTv3 validation), forward/RC averaged; shift RC DNase one base. '
        'Pearson per track and unweighted assay mean: raw accessibility, log1p CAGE/PRO-cap/RNA. ChIP 128-bp and pairwise splice tasks are excluded.')
    ag_meta = we('alphagenome-panel', 8,
        'C.8 lists 1,643 unique track IDs: 167 ATAC, 305 DNase, 546 CAGE, 12 PRO-cap and 613 RNA. '
        'Only NTv3 has per-track values here; the AlphaGenome column is its published assay mean repeated for context, not per-track measurements.')
    agr = defaultdict(list)
    for row in sheet(8): agr[fam[row['Assay']]].append(row)
    for slug, rows in sorted(agr.items()):
        tid = 'ntv3-ag-' + slug
        t = c.get('tasks', tid)
        t.update(description='Separate assay-specific full-backbone adaptation on AlphaGenome’s released human 1-bp task data.',
            input_description='1,048,576-bp input; score centered held-out 196,608-bp windows.',
            output_description='Position × human assay track quantitative signal', evidence_id=ag,
            limitations='Fold 4 was excluded from gradient training but is also NTv3’s validation fold; it is not an independent third test. Raw target arrays were not reread.')
        c.output(tid,'signal-profile',ag,t['output_description'],'Assay track × scored genomic base',axis='contiguous',
            rationale='Assay-specific regression over every scored genomic base; it does not reconstruct categorical elements or linked transcripts.',limitations=t['limitations'])
        c.use(tid,'ntv3','ntv3',ag,tid + '-protocol')
        vid = tid + '-matched-tracks'
        variant(tid, vid, 'Matched human assay panel', ag_meta, '1,048,576 bp input; 196,608 bp scored window', len(rows))
        pop = layout.link(tid, 'Homo sapiens', ag_meta, vid)
        for row in rows: track(tid, 'ntv3-complete-workbook', 'ntv3-ag-', row, pop, row['Assay'], ag_meta, vid, 'Track ID')
        c.protocol(tid + '-protocol', tid, 'Assay-specific matched AlphaGenome adaptation', 'full fine-tune',
            'New species-conditioned assay head; all backbone/head parameters updated; forward/RC prediction averaging.',
            'AlphaGenome held-out split = Borzoi fold 4, also NTv3 validation; no gradient exposure, but no third independent selection-free test.',
            'Borzoi genomic fold / window', ag, [('pearson', 'Per track over full evaluation set; raw accessibility, log1p transcription assays; unweighted assay mean.')],
            variant=vid, fitted='All model parameters')
        c.count(tid, len(rows), 'human assay tracks', ag_meta, variant=vid, method='measured', qualifier='Complete C.8 identity/result table.')
        c.count(tid, 6853, 'evaluation windows', ag, qualifier='Reported 196,608-bp test windows, not assay-track count.')

    annotation = pe('annotation', 'Methods 4.4.1–4.4.3; Supplementary B.6/C.2/C.3',
        'Separate mammals/plants/insects models: 1-Mb inputs, 15 phase-aware CDS/intron/splice/start/stop/background states, all parameters fine-tuned, inference-only constrained HMM/Viterbi decoder. '
        'Inference scores central 75% =786,432 bp, both strands independently; drop predictions under 201 CDS bp or with internal stops. '
        'Test genera are excluded from supervised training/validation; validation is only species-held-out. Broad unsupervised OpenGenome2 exposure is not excluded by that supervised split. '
        'Whole-assembly reference/prediction filtering is shared between callers; exact exon match includes contig/start/end/strand/phase, exact gene match requires the entire CDS-exon set. '
        'Primary longest-CDS isoform and separately scored any-annotated-isoform rules differ; neither assesses UTR ends or all-isoform recall.')
    ann_meta = we('annotation-panel', 2,
        'C.2 lists 201 assemblies: mammals 28 train/2 validation/2 test; plants 53/2/5; insects 93/6/10. '
        'The 17 scored test species have exact assembly accession and annotation provider. Source annotated-gene counts precede evaluator filtering and are not assumed final scored-locus counts.')
    ann_results = we('annotation-results', 3,
        'C.3 reports per-species CDS-exon/gene precision, recall and F1 under longest and any-isoform matching, plus seconds/Mb. '
        'Rows are caller × species results, not independent replicate trainings; annotation models use one seed per arm.')
    test_species = [r for r in sheet(2) if r['Split'] == 'Test']
    for tid in ['ntv3-annotation-exon', 'ntv3-annotation-gene']:
        t = c.get('tasks', tid)
        t.update(evidence_id=annotation, dataset_name='NTv3 / Tiberius 17-assembly coding annotation benchmark',
            description='Whole-assembly coding annotation with phase-aware decoding; exact CDS-exon and complete coding-chain scoring are separate targets.',
            input_description='Soft-masked whole-genome FASTA; 1-Mb inputs, central 786,432-bp prediction windows; both strands independently decoded.',
            output_description='Exact phase-aware CDS-exon coordinates' if tid.endswith('exon') else 'Exact complete CDS-exon chain per reference locus',
            limitations='Source assembly/reference identities and reported results inspected. Gated released prediction files were not read; broad MLM corpus exposure is separate from supervised genus exclusion.')
        clear_pops(tid)
        if tid.endswith('gene'):
            c.output(tid,'linked-structure',annotation,t['output_description'],'Complete reference coding gene chain',axis='linked',structure='coding-chain',
                rationale='Exact whole-CDS exon-set matching assesses a complete linked coding structure; transcript UTR ends and all-isoform recall are outside this target.',limitations=t['limitations'])
        else:
            c.output(tid,'element-set',annotation,t['output_description'],'Phase-aware individual CDS exon',axis='interval-set',
                rationale='Score individual coding-exon coordinate/strand/phase matches across complete assemblies; this is not full linked-gene correctness.',limitations=t['limitations'])
        for row in test_species:
            name = row['Species']
            name = {'Osmia bicornis bicornis':'Osmia bicornis','Mimulus guttatus':'Erythranthe guttata'}.get(name,name)
            vid = tid + '-' + name.lower().replace(' ', '-')
            variant(tid, vid, row['Species'] + ': ' + row['Accession ID'], ann_meta,
                '1,048,576 bp input; 786,432 bp predicted center', notes=json.dumps(row, ensure_ascii=False))
            layout.link(tid, name, ann_meta, vid, note='Exact supervised held-out test assembly in C.2; named subspecies retained in variant metadata.')
            c.count(tid, int(row['#Genes']), 'source annotation genes', ann_meta, split='test assembly before scoring filters', variant=vid,
                qualifier='C.2 source annotation count; not the final pseudogene/conflict-filtered scoring denominator.')
        for rule in ['longest', 'any-isoform']:
            pid = tid + '-protocol' if rule == 'longest' else tid + '-' + rule + '-protocol'
            c.protocol(pid, tid, 'Coding annotation: ' + rule + ' reference rule', 'full fine-tune with structured decoding',
                'Phase-aware positional head → fixed constrained HMM/Viterbi → GFF3 coding gene models; no RNA/protein evidence at inference.',
                'Supervised test genera excluded from train/validation; select checkpoint by mean validation-species gene F1. Test 2 mammals/5 plants/10 insects; validation species can share training genera.',
                'Species / genus', annotation, [('precision', 'Exact CDS-exon or complete coding-chain matches per species.'), ('recall', 'Exact matches per filtered reference set.'), ('f1', 'Per species; unweighted clade mean.')],
                fitted='All backbone/annotation-head parameters; decoder grammar fixed',
                selection='One seed per arm; best validation-species gene F1, not the test species.',
                notes='Longest-CDS is primary. Any-isoform expands accepted structures and reference exon union; UTR-inclusive transcript accuracy is not measured.')
            c.use(tid, 'ntv3', 'ntv3', annotation, pid)
            if any(m['id'] in ['genecad','plantcad2'] for m in d['models']):
                for row in [r for r in test_species if r['Clade'] == 'Plants']:
                    name = {'Mimulus guttatus':'Erythranthe guttata'}.get(row['Species'],row['Species'])
                    vid = tid + '-' + name.lower().replace(' ', '-')
                    gp = pid + '-genecad-' + name.lower().replace(' ', '-')
                    c.protocol(gp,tid,'GeneCAD plant comparison: ' + rule,'released GeneCAD v0.3.0 annotation pipeline',
                        'GeneCAD coding predictions scored with the common NTv3 evaluator; frame-aware decoding.',
                        'This plant test assembly only, under the shared longest / any-isoform reference rule. No mammal or insect result is implied.',
                        'Plant assembly',annotation,[('precision','Exact coding-exon / coding-chain matches.'),('recall','Shared filtered reference.'),('f1','Per plant species.')],
                        variant=vid,fitted='No extra NTv3 benchmark-label head')
                    c.use(tid,'genecad' if any(m['id']=='genecad' for m in d['models']) else 'plantcad2','ntv3',annotation,gp,provenance='external-evaluation',
                        note='Only the linked plant assembly; GeneCAD is the PlantCAD fine-tuned coding annotator, evaluated independently in NTv3 rather than trained as NTv3.')
        c.put('task_feature_scopes', dict(id=tid + '-cds-scope', task_id=tid, feature_id='cds', scope='restricted-target',
            rationale='Exact coding structures explicitly exclude UTRs; full coding chains remain distinct from CDS-exon coordinate matches.', evidence_id=annotation))
    protein = pe('protein-annotation', 'Methods 4.4.3 protein analyses; Supplementary B.6.2 / Fig. A.7',
        'Cow/beluga analysis splices CDS, reverse-complements minus-strand genes, trims initial phase/trailing incomplete codons and translates with standard code; proteins shorter than 20 aa excluded. '
        'Best same-strand overlapping predicted protein is globally aligned to each reference; identity uses the longer sequence as denominator, scored at exact/95/90/50%. '
        'Valid ORF starts with methionine and has no internal stop. Intron-chain match ignores outer coding coordinates but requires every internal splice boundary. '
        'Protein analyses cover staged contigs with 99.3% cow/98.9% beluga reference loci, unlike whole-assembly structural scoring.')
    busco = c.evidence('ntv3-final-busco', 'ntv3-complete-supplement', 'Supplementary B.6.2 and Table B.2',
        'BUSCO v5.7.1 protein mode, mammalia_odb10 with 9,226 markers, uses the same staged contigs for reference and both callers. '
        'Complete single-copy plus duplicated markers determine completeness; unfiltered reference is the ceiling. Cow NTv3/Tiberius/reference completeness: 98.1/97.0/98.9%; beluga:96.0/95.6/97.7%.', 'paper', SUP + '#page=35')
    for mid, name, definition, direction in [
        ('protein-identity-recovery', 'Protein identity recovery', 'Fraction of reference proteins with a same-strand overlapping prediction meeting the source-defined global identity threshold.', 'higher'),
        ('valid-orf-fraction', 'Valid ORF fraction', 'Fraction of predicted coding proteins beginning with methionine and lacking internal stops; syntactic diagnostic, not functional validation.', 'higher'),
        ('busco-completeness', 'BUSCO completeness', 'Complete single-copy plus duplicated conserved markers as a fraction of the specified BUSCO lineage panel.', 'higher'),
        ('seconds-per-mb', 'Seconds per Mb', 'End-to-end annotation wall-clock seconds divided by assembly size; hardware and timing boundary must be stated.', 'lower')]:
        c.put('metrics', dict(id=mid, name=name, definition=definition, direction=direction))
    for slug, target, eid, form, scope, metric in [
        ('intron-chain', 'Complete internal coding intron-chain match', protein, 'linked-structure', 'splice-pattern', 'f1'),
        ('protein-identity', 'Translated coding-protein identity recovery', protein, 'isolated', 'none', 'protein-identity-recovery'),
        ('valid-orf', 'Predicted coding ORF validity', protein, 'isolated', 'none', 'valid-orf-fraction'),
        ('busco', 'Predicted mammalian proteome completeness', busco, 'isolated', 'none', 'busco-completeness')]:
        tid = 'ntv3-annotation-' + slug
        new_task(tid, 'NTv3 annotation: ' + target, 'Cow / beluga coding annotation panel', target,
            'structured prediction' if form == 'linked-structure' else 'annotation diagnostic', eid,
            ['cds', 'splice', 'intron'] if slug == 'intron-chain' else ['cds'], ['structured-annotation'],
            'Assess the specified downstream property of complete decoded coding-gene predictions; source-specific protein/contig eligibility is retained.',
            output=target, form=form, structure=scope,
            limitations='Cow/beluga only; whole-assembly exon/gene scores, staged-contig protein recovery, ORF grammar and marker completeness are different targets.')
        for sp in ['Bos taurus', 'Delphinapterus leucas']: layout.link(tid, sp, eid)
        pid = tid + '-protocol'
        c.protocol(pid, tid, target, 'use supervised annotation predictor; no additional fitted probe',
            'Decoded coding GFF3 → reference-chain matching or translated proteome readout.',
            'Two supervised genus-held-out mammalian test assemblies; staged contigs for translated-protein analyses. No new fitting split.',
            'Reference locus / predicted protein / conserved marker', eid, [(metric, 'Per species with source-defined match/filter/denominator.')],
            fitted='No added benchmark head; use fine-tuned mammal annotator')
        c.use(tid, 'ntv3', 'ntv3', eid, pid)
        if slug == 'protein-identity':
            for thresh in ['exact', '95%', '90%', '50%']:
                variant(tid, tid + '-' + thresh.replace('%', 'pct'), 'Global protein identity: ' + thresh, protein,
                    'Whole predicted/reference CDS translated to protein', notes='Best overlapping same-strand prediction; identical residues divided by longer protein length.')
        elif slug == 'busco': c.count(tid, 9226, 'lineage markers per proteome', busco, qualifier='Shared mammalia_odb10 marker panel; not unique biological examples across callers/species.')
        elif slug == 'valid-orf':
            c.count(tid, 6, 'invalid predicted cow ORFs', protein, qualifier='Source Fig. A.7; full predicted-protein denominator not inferred from rounded percentage.')
            c.count(tid, 0, 'invalid predicted beluga ORFs', protein, qualifier='Source Fig. A.7; valid syntax is not experimental function.')
    runtime = pe('annotation-runtime', 'Methods 4.4.3 throughput; Supplementary B.6.3',
        'One H100 80-GB GPU; whole soft-masked FASTA to written annotation including loading/compilation/inference/decoding/output, excluding repeat masking and evaluation. '
        'Single runtime per assembly; seconds/Mb unweighted assembly means, with 13 assemblies having mean contig >1 Mb separated from four fragmented assemblies. '
        'NTv3 uses bfloat16 compute with FP32 stored/head weights, central 75% outputs; padding every contig to a whole input raises cost for fragmented assemblies.')
    tid = 'ntv3-annotation-runtime'
    new_task(tid, 'NTv3 annotation: end-to-end runtime', 'NTv3 17-assembly annotation panel', 'Whole-genome annotation seconds per Mb',
        'runtime benchmark', runtime, ['genome'], ['long-context'], 'Measure annotation wall-clock time with explicit hardware, contig and compilation scope.',
        apps=('genome-annotation', 'model-development'))
    for row in test_species:
        layout.link(tid, {'Osmia bicornis bicornis':'Osmia bicornis','Mimulus guttatus':'Erythranthe guttata'}.get(row['Species'],row['Species']), ann_meta)
    c.protocol(tid + '-protocol', tid, 'One-H100 end-to-end annotation', 'native fine-tuned annotation model',
        'Whole-assembly inference, constrained decoding and GFF3 output on one H100 80 GB.',
        'Same 17 genus-held-out test assemblies; runtime is one run per assembly, not repeated training.', 'Assembly', runtime,
        [('seconds-per-mb', 'Unweighted mean over assemblies, separately for 13 contiguous / four fragmented assemblies.')])
    c.use(tid, 'ntv3', 'ntv3', runtime, tid + '-protocol')
    return _external_and_design(c, layout, pe, we, new_task, variant, manifest, native, bmeta, bprotocol,
        tutorial, borzoi, borzoi_meta, ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids)


def _external_and_design(c, layout, pe, we, new_task, variant, manifest, native, bmeta, bprotocol,
        tutorial, borzoi, borzoi_meta, ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids):
    d = c.data
    sheet = lambda n: next(s['rows'] for s in ART['sheets'] if s['name'].startswith(f'Supp Table {n} '))
    def clear_pops(tid):
        d['task_populations'] = [r for r in d['task_populations'] if r['task_id'] != tid]
        d['coverage_mappings'] = [r for r in d['coverage_mappings'] if r['task_id'] != tid]
    def remove_cat(tid, cats):
        d['task_categories'] = [r for r in d['task_categories'] if not (r['task_id'] == tid and r['category_id'] in cats)]
    external = we('external-results', 9,
        'C.9 has 101 benchmark-result rows: SeiPlant five-species H3K4me3; AgroNT expression in four plants and Ribo-seq proxy in maize only; 46 DeepFARM chicken/pig track results; DanioDecima full and 264-gene context-disjoint arms. '
        'Rows with repeated species/track and different baselines are not additional biological examples. Expression includes a 262-kb arm absent from the Methods context list.')
    sei = pe('seiplant', 'Methods 4.7: SeiPlant; Fig. 3c; C.9',
        'Zero-shot H3K4me3 transfer uses 23 ChIP-Hub experiments in five species absent from both NTv3 functional post-training and SeiPlant training. '
        'NTv3 borrows the Arabidopsis token/head, averages its H3K4me3 columns, inverts target transforms and averages physical signal over the central 128 bp of the common 1,024-bp grid. '
        'NTv3 input is 1 Mb; forward strand only, common non-ACGT mask. Pearson is median across chromosomes then median across experiments; compare within-/cross-family SeiPlant weights.')
    tid = 'ntv3-seiplant'
    new_task(tid, 'SeiPlant: H3K4me3 signal transfer', 'SeiPlant / ChIP-Hub held-out plant panel', 'H3K4me3 experimental signal / peak status',
        'regression / classification', sei, ['genome'], ['functional-prediction', 'long-context'],
        'Species transfer with an existing functional head; the source panel contains H3K4me3 only, not all seven SeiPlant marks.',
        output='One H3K4me3 score per central 128-bp bin', apps=('plant-breeding',),
        limitations='C.9 provides species/experiment counts and Pearson/auPRC summaries; individual experiment IDs, scored-bin counts and per-chromosome masks are not included there.')
    clear_pops(tid)
    for sp, n in [('Arabidopsis lyrata', 1), ('Brassica napus', 16), ('Arabis alpina', 1), ('Brachypodium distachyon', 4), ('Hordeum vulgare', 1)]:
        vid = tid + '-' + sp.lower().replace(' ', '-')
        variant(tid, vid, sp + ': H3K4me3', external, 'NTv3 1 Mb; SeiPlant 1,024 bp; common 128-bp scored bin', n,
            notes='Within-family and cross-family SeiPlant comparators share this species cohort; no adaptation to its labels.')
        layout.link(tid, sp, external, vid)
        c.count(tid, n, 'ChIP-Hub experiments', external, variant=vid, qualifier='Species experiment count in C.9; not input-window count.')
    c.protocol(tid + '-protocol', tid, 'Cross-species native-head transfer', 'zero-shot existing functional head',
        'Arabidopsis conditioning/head; matched physical-signal 128-bp outputs, forward strand, common non-ACGT mask.',
        'Five species absent from functional post-training and SeiPlant training; source held-out chromosome evaluation, without new fitting.',
        'Species / chromosome', sei, [('pearson', 'Median across chromosomes per experiment, then median across experiments within species.'),
            ('auprc', 'Species result reported in C.9; precise peak-threshold/bin reduction is not specified in Methods.')],
        fitted='None', notes='The source prose specifies Pearson; C.9 additionally reports auPRC. The latter is retained without inventing its label-processing implementation.')
    c.use(tid, 'ntv3', 'ntv3', sei, tid + '-protocol')
    c.limit('tasks', tid, 'bin-and-experiment-membership', 'not-reported',
        'C.9 supplies 23 experiments by species but not their accession IDs, exact scored chromosome membership, per-bin labels or retained-bin counts. Public ChIP-Hub is upstream data, not an NTv3 scoring manifest.', sei)
    c.limit('protocols', tid + '-protocol', 'auprc-reduction', 'not-reported',
        'C.9 reports auPRC, while Methods details the Pearson reduction. Its exact binary peak-label threshold and auPRC reduction are not stated.', external)
    agro = pe('agro', 'Methods 4.7: gene-level expression and protein abundance in plants; C.9',
        'Gene expression uses log1p TPM recomputed from AgroNT gene counts and collapsed exon lengths, replacing the original DESeq2 normalization. '
        'TSS-centered inputs are 5,888 / 32,000 / 131,072 bp, retaining only genes extractable at all contexts, with homology/MCL-based gene partitions. '
        'Ribo-seq StringTie -e -A TPM is a protein-synthesis proxy, not measured protein abundance. All-parameter regression adaptation: Adam 5e-5, batch 16, up to 200,000 updates; validate every 2,000, patience ten, seed 0, best validation checkpoint.')
    scientific = {'Maize': 'Zea mays', 'Rice': 'Oryza sativa', 'Thale cress': 'Arabidopsis thaliana', 'Tomato': 'Solanum lycopersicum'}
    for tid, target, source_target in [('ntv3-agro-expression', 'Gene-level log1p TPM expression', 'gene expression'),
                                       ('ntv3-agro-translation', 'Gene-level Ribo-seq TPM synthesis proxy', 'protein abundance')]:
        new_task(tid, 'AgroNT transfer: ' + target, 'AgroNT-derived gene-level plant targets', target, 'multioutput regression', agro,
            ['gene', 'promoter'], ['functional-prediction', 'long-context'],
            'Predict one gene-level target vector across source tissues; RNA coverage is reduced to a gene value rather than scored as dense genomic labels.',
            output='Gene × tissue expression or ribosome-footprint abundance vector', apps=('plant-breeding',),
            limitations='NTv3-specific retained gene IDs, partition memberships and per-partition example counts are not supplied in C.9. Original AgroNT preprocessing/splits cannot be assumed identical.')
        clear_pops(tid)
        rows = [r for r in sheet(9) if r['Benchmark'] == 'Agronomics (AgroNT)' and r['Task'] == source_target]
        for sp in sorted({r['Species'] for r in rows}):
            layout.link(tid, scientific[sp], external, note='Actual C.9 reported species; translation-proxy results occur only in maize.')
            for row in [r for r in rows if r['Species'] == sp]:
                vid = tid + '-' + sp.lower().replace(' ', '-') + '-' + row['Input length'].replace(' ', '')
                variant(tid, vid, scientific[sp] + ': ' + row['Input length'], external, row['Input length'] + ' TSS-centered',
                    notes=json.dumps(row, ensure_ascii=False))
        c.protocol(tid + '-protocol', tid, 'Gene-level full-backbone plant adaptation', 'full fine-tune',
            'TSS-centered sequence → jointly updated backbone and gene-level regression head.',
            'Homology/MCL gene partitions; common retained genes across contexts. Seed 0; best validation checkpoint, up to 200,000 updates.',
            'Gene / homology cluster', agro, [('r2', 'Mean R² across source tissue targets, as reported in Fig. 3d / C.9.')],
            fitted='All parameters', selection='Validation every 2,000 steps; patience ten; Adam 5e-5, batch 16')
        c.use(tid, 'ntv3', 'ntv3', agro, tid + '-protocol')
        c.limit('tasks', tid, 'exact-gene-cohort-and-counts', 'not-reported',
            'The NTv3 source describes cohort construction and homology-based partitioning but does not list the retained gene identities or partition counts for its changed target normalization/context filters.', agro)
    c.limit('tasks', 'ntv3-agro-expression', 'evaluated-context-list', 'conflicting',
        'C.9 reports a 262-kb expression arm in all four species; Methods lists only 5,888 / 32,000 / 131,072 bp. The 262-kb result is indexed as reported without fabricating an exact input length or changed cohort.', external)
    deep = pe('deepfarm', 'Methods 4.7: DeepFARM; Fig. 3e,f; C.9',
        'DeepFARM supplies 200-bp binary peak bins; a single peak must cover at least half a bin. NTv3 is evaluated zero-shot with existing species heads, aligned on the same global grid, against released DanQ weights using 1,000-bp context. '
        'Matched outputs are 30/97 chicken tracks and 16/80 pig tracks. Primary evaluation requires the entire NTv3 input context inside native held-out intervals; secondary analysis requires only the scored bin. '
        'Whole windows must fit within chromosomes; same jointly predictable bins and tracks are used for both models. Per-track auROC uses paired 25-kb block bootstrap. '
        'NTv3 saw the same assay/tissue types in different European FAANG studies; this is not an unseen-assay claim. Original peak data are GSE158430 / Ensembl 104.')
    for tid, label, wanted, features in [('ntv3-deepfarm', 'Histone peak classification', False, ['genome']),
        ('ntv3-deepfarm-ctcf', 'CTCF peak classification', True, ['tfbs'])]:
        new_task(tid, 'DeepFARM: ' + label, 'DeepFARM / FAANG GSE158430 matched panel', label,
            'multilabel binary classification', deep, features, ['functional-prediction', 'long-context'],
            'Classify experimental 200-bp peak bins using existing native functional tracks; histogram marks and CTCF binding are separate targets.',
            output='Binary peak score per sampled 200-bp genomic bin and matched assay track', apps=('regulatory-engineering', 'target-discovery'),
            limitations='Exact per-track identities and 46 results are in C.9; NTv3’s retained bin coordinates/counts and fixed cross-study head mapping are not released in that table.')
        remove_cat(tid, ['tfbs'] if not wanted else ['genome'])
        clear_pops(tid)
        rows = [r for r in sheet(9) if r['Benchmark'] == 'DeepFARM' and (r['Task'] == 'CTCF') == wanted]
        for sp in sorted({r['Species'] for r in rows}):
            name = {'Chicken': 'Gallus gallus', 'Pig': 'Sus scrofa'}[sp]
            for mark in sorted({r['Task'] for r in rows if r['Species'] == sp}):
                panel = [r for r in rows if r['Species'] == sp and r['Task'] == mark]
                vid = tid + '-' + sp.lower() + '-' + mark.lower()
                variant(tid, vid, name + ': ' + mark, external, 'NTv3 1 Mb / DanQ 1,000 bp; 200-bp bin', len(panel),
                    notes=json.dumps(panel, ensure_ascii=False))
                layout.link(tid, name, external, vid)
                c.count(tid, len(panel), 'matched tissue/replicate tracks', external, variant=vid, method='measured',
                    qualifier='Exact C.9 species × mark rows; not sequence bins.')
        for arm in ['whole-context-held-out', 'bin-held-out']:
            pid = tid + '-protocol' if arm == 'whole-context-held-out' else tid + '-' + arm + '-protocol'
            c.protocol(pid, tid, 'DeepFARM: ' + arm, 'zero-shot existing functional head',
                'Native species head → quantitative output averaged on the fixed 200-bp grid; rank against peak-presence labels.',
                'Entire 1-Mb context inside NTv3 held-out regions.' if arm == 'whole-context-held-out' else 'Only the 200-bp scored bin is required inside native held-out regions; context can cross partitions.',
                'Genomic region / 200-bp bin', deep, [('auroc', 'Per matched track; paired model differences with contiguous 25-kb block bootstrap.')],
                fitted='None; the track mapping is fixed before inference', notes='Same assay/tissue types appeared in functional supervision from distinct studies; this is a genomic-region transfer evaluation.')
            c.use(tid, 'ntv3', 'ntv3', deep, pid)
        c.limit('tasks', tid, 'scored-bin-identities-and-counts', 'not-released',
            'Methods describes strict and bin-only scoring masks, but the inspected release supplies no NTv3-specific retained-bin manifest or before/after mask count.', deep)
    danio = pe('danio', 'Methods 4.7: DanioDecima; C.9',
        'GRCz11 / Ensembl 116 gene-start anchored 524,288-bp inputs include 163,840 bp upstream, strand correction and a gene-body mask; outputs pool over 196,608 bp from gene start. '
        'ZebraHub raw counts aggregate by fine ontology class × stage, producing 304 log1p-CPM pseudobulks over ten stages. '
        'Published chromosome gene splits give 18,368 train / 6,110 validation / 7,289 test genes. NTv3 full fine-tuning uses zebrafish token, up to 40 epochs, LR 3e-5, batch 20, best validation checkpoint. '
        'Report Pearson across pseudobulks per gene and across genes per pseudobulk. Split-half cell labels with Spearman–Brown correction estimate label reliability, not a model accuracy score.')
    tid = 'ntv3-danio'
    new_task(tid, 'DanioDecima: zebrafish pseudobulk expression', 'DanioDecima / ZebraHub', '304-pseudobulk gene expression profile',
        'multioutput regression', danio, ['gene', 'promoter'], ['functional-prediction', 'long-context', 'context-specific'],
        'Gene-level expression across cell populations and developmental stages; output dimensions are pseudobulks rather than genomic positions.',
        output='One 304-pseudobulk log1p-CPM vector per gene', apps=('regulatory-engineering', 'target-discovery'),
        limitations='The NTv3 context-disjoint subset has 264 genes; published comparator scores are for the full test set, so the subset comparison is not cohort matched.')
    clear_pops(tid); layout.link(tid, 'Danio rerio', danio)
    for arm, n in [('full-test', 7289), ('context-disjoint', 264)]:
        vid = tid + '-' + arm
        variant(tid, vid, 'DanioDecima ' + arm, external, '524,288 bp; pooled 196,608 bp', 304,
            notes='Full published gene split.' if arm == 'full-test' else 'C.9 leak-free subset; baselines retain full-test cohort and are not a matched-subset comparison.')
        pid = tid + '-protocol' if arm == 'full-test' else vid + '-protocol'
        c.protocol(pid, tid, 'DanioDecima ' + arm, 'full fine-tune',
            'Zebrafish token/backbone plus gene-level expression head; gene-body mask, pooled sequence and Poisson–multinomial loss across pseudobulks.',
            'Published held-out chromosome gene split.' if arm == 'full-test' else '264 full-context-disjoint test genes retained from published test split; comparator numbers are full-test estimates.',
            'Chromosome / gene', danio if arm == 'full-test' else external,
            [('pearson', 'Mean per-gene Pearson across 304 pseudobulks, and mean per-pseudobulk Pearson across the specified gene cohort.')],
            variant=vid, fitted='All backbone/head parameters', selection='Best validation score, up to 40 epochs, LR 3e-5, batch 20')
        c.count(tid, n, 'test genes', external if arm == 'context-disjoint' else danio, variant=vid, protocol=pid)
        c.use(tid, 'ntv3', 'ntv3', danio if arm == 'full-test' else external, pid)
    c.limit('tasks', tid, 'context-disjoint-comparator-cohort', 'not-reported',
        'C.9 pairs 264-gene NTv3 subset results with baseline full-test results; no re-scored comparator predictions on those 264 genes are supplied.', external)
    eqtl = pe('eqtl', 'Methods 4.8.2: quantitative eQTL benchmark; C.10',
        '48 GTEx tissue classification cohorts use chromosomes 3, 6, 9, 12, 16, 18, 19, 21. Score 1-Mb allele-centered inputs using exon-averaged RNA signal over all contained GENCODE genes and matched tissue tracks; max absolute log2FC over tracks/genes, averaged over forward/RC. '
        'The full input is used, including positions outside the functional supervised center. Per-tissue auROC/auPRC reduce by tissue-entry weights; 400 tissue-stratified paired bootstraps. '
        'AlphaGenome contributes a published aggregate auROC only; no invented tissue/auPRC values. Both single- and mixed-length NTv3 checkpoints are compared at 1 Mb.')
    eqtl_counts = we('eqtl-counts', 10,
        'The 48 tissue rows total 21,241 variant–tissue entries, 10,324 positive and 10,917 control entries. The final aggregate row is not a 49th tissue. '
        'Without a site-identity manifest, this total is not asserted to represent 21,241 distinct genomic variant sites.')
    tid = 'ntv3-eqtl'
    new_task(tid, 'GTEx: expression-QTL discrimination', 'GTEx / AlphaGenome chromosome-restricted eQTL panel', 'Positive/control eQTL classification per tissue',
        'binary classification', eqtl, ['regulatory'], ['variant-effects', 'long-context'],
        'Zero-shot regulatory allele scoring using native tissue RNA predictions; quantitative effect scores are evaluated against binary benchmark classes.',
        output='One absolute RNA-effect score per variant–tissue entry', apps=('variant-interpretation', 'target-discovery'),
        limitations='Published result and tissue-class counts are audited; exact NTv3 input allele/label manifest was not found in the inspected release. Tissue entries are not unique variant sites.')
    clear_pops(tid); layout.link(tid, 'Homo sapiens', eqtl)
    # Correct the earlier unqualified site count in place rather than leaving a conflicting duplicate.
    for r in d['counts']:
        if r['task_id'] == tid and r['value'] == 21241:
            r.update(unit='variant–tissue entries', evidence_id=eqtl_counts, qualifier='Sum of 48 tissue cohorts; unique genomic-site count not established.')
    for row in sheet(10):
        if row['# variants'] is None: continue
        if not row['Tissue'] or str(row['Tissue']).lower().startswith(('overall','weighted','all ','tissue-weighted')): continue
        # The last row is an aggregate, with no cohort counts in the workbook.
        vid = tid + '-' + row['Tissue'].lower().replace(' ', '-')
        variant(tid, vid, row['Tissue'], eqtl_counts, '1,048,576 bp allele-centered', notes=json.dumps(row, ensure_ascii=False))
        for n, unit in [(int(row['# variants']), 'variant–tissue entries'), (int(row['# causal (positive) variants']), 'positive entries'),
                        (int(row['# variants'] - row['# causal (positive) variants']), 'control entries')]:
            c.count(tid, n, unit, eqtl_counts, variant=vid, qualifier='Within this tissue; the same variant can occur in another tissue.')
    for arm in ['single-length', 'mixed-length']:
        pid = tid + '-protocol' if arm == 'single-length' else tid + '-mixed-length-protocol'
        c.protocol(pid, tid, 'GTEx ' + arm + ' checkpoint', 'zero-shot existing functional head',
            'Allele-centered 1-Mb native RNA outputs, exon-average signal, max absolute log2FC across matched genes/tracks, forward/RC average.',
            'Published zero-shot test chromosomes 3, 6, 9, 12, 16, 18, 19, 21; no eQTL-label fitting.',
            'Variant–tissue entry / chromosome', eqtl,
            [('auroc', 'Per tissue and tissue-entry-weighted mean; 400 paired tissue-stratified bootstraps.'), ('auprc', 'Same reduction; AlphaGenome supplies no published per-tissue/auPRC result.')],
            fitted='None; ' + arm + ' tracks checkpoint', notes='Uses predictions across the whole input, including outside its supervised center.')
        c.use(tid, 'ntv3', 'ntv3', eqtl, pid)
    c.limit('tasks', tid, 'allele-label-identity-manifest', 'not-released',
        'The inspected paper workbook supplies tissue counts and performance, not the complete NTv3 allele/control identity list or deduplicated genomic-site count.', eqtl_counts)
    re2g = pe('re2g', 'Methods 4.8.2 enhancer–gene linking; Supplementary B.7 / Fig. A.21',
        'K562 ENCODE-rE2G has 10,356 element–gene pairs, 471 positive; 3,826 common scored pairs have 410 positives. '
        'Use TSS-centered 1-Mb sequence, native RNA exon objective and input×gradient; score a 2,400-bp enhancer window with Gaussian σ300, missing outside-context pairs zero. '
        'No enhancer–gene labels fitted. Report auPRC, auROC and precision at 70% recall in distance bins, alongside inverse-distance baseline; AlphaGenome numbers are published, not re-scored. '
        'All-set bins <10 / 10–100 / 100–2,500 kb contain 223/1,597/8,536 pairs and 133/256/82 positives; matched bins 218/1,524/2,084 and 128/240/42 positives.')
    c.put('metrics', dict(id='precision-at-70-recall', name='Precision at 70% recall', definition='Precision at the source operating point attaining 70% recall.', direction='higher'))
    tid = 'ntv3-re2g'
    new_task(tid, 'ENCODE-rE2G: enhancer–gene linking', 'ENCODE-rE2G K562 CRISPRi', 'Experimentally regulated element–gene pair ranking',
        'binary classification / ranking', re2g, ['enhancer', 'promoter'], ['functional-prediction', 'long-context', 'interpretability'],
        'Prioritize regulatory element–gene links from native RNA attribution without training on the benchmark pair labels.',
        output='One regulatory-link score per enhancer–gene pair', form='pairwise', apps=('regulatory-engineering', 'target-discovery'),
        limitations='All-pair and common-coverage cohorts differ greatly in prevalence; missing-context pairs scored zero remain in the all-pair cohort.')
    clear_pops(tid); layout.link(tid, 'Homo sapiens', re2g)
    for arm, counts in [('all-pairs', [(10356,471),(223,133),(1597,256),(8536,82)]),
                        ('matched-pairs', [(3826,410),(218,128),(1524,240),(2084,42)])]:
        for label, (n, pos) in zip(['all-distances', 'under-10kb', '10-100kb', '100-2500kb'], counts):
            vid = tid + '-' + arm + '-' + label
            variant(tid, vid, arm + ': ' + label, re2g, '1,048,576 bp centered on gene TSS',
                notes='Missing input coverage → zero in all-pair arm; matched arm requires common scoring by all three models.')
            c.count(tid, n, 'element–gene pairs', re2g, variant=vid)
            c.count(tid, pos, 'regulated positive pairs', re2g, variant=vid)
    for arm in ['single-length', 'mixed-length']:
        pid = tid + '-protocol' if arm == 'single-length' else tid + '-mixed-length-protocol'
        c.protocol(pid, tid, 'ENCODE-rE2G ' + arm, 'zero-shot native RNA attribution',
            'TSS-centered input → exon-summed native RNA objective → input×gradient → Gaussian-weighted absolute enhancer attribution.',
            'Independent K562 CRISPRi pair labels; no label fitting. All 10,356 pairs and common 3,826 pairs scored separately by distance.',
            'Enhancer–gene pair', re2g, [('auprc', 'Per distance/cohort.'), ('auroc', 'Per distance/cohort.'),
                ('precision-at-70-recall', 'Per distance/cohort; published AlphaGenome comparator is not re-scored.')], fitted='None; ' + arm + ' checkpoint')
        c.use(tid, 'ntv3', 'ntv3', re2g, pid)
    return _generation_diagnostics_resources(c, layout, pe, we, new_task, variant, manifest, native, bmeta, bprotocol,
        tutorial, borzoi, borzoi_meta, ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids,
        external, sei, agro, deep, danio, eqtl, eqtl_counts, re2g)


def _generation_diagnostics_resources(c, layout, pe, we, new_task, variant, manifest, native, bmeta, bprotocol,
        tutorial, borzoi, borzoi_meta, ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids,
        external, sei, agro, deep, danio, eqtl, eqtl_counts, re2g):
    d = c.data
    def clear_pops(tid):
        d['task_populations'] = [r for r in d['task_populations'] if r['task_id'] != tid]
        d['coverage_mappings'] = [r for r in d['coverage_mappings'] if r['task_id'] != tid]
    generation = pe('generation', 'Methods 4.9: conditioned sequence generation, data and fine-tuning',
        'Separate plant-promoter, plant-enhancer and fly-enhancer models adapt the tracks backbone with MDLM and condition embeddings in adaptive layer normalization. '
        'Only the 170 / 249-bp candidate insert is corrupted/generated inside a fixed reporter context. All parameters update; AdamW, batch 32, EMA 0.9999; conditions dropped in 10% of examples. '
        'Sampling uses 50 steps and classifier-free guidance. An unconditional pass supports guidance but does not constitute an independently evaluated unconditional-generation task. '
        'Source-study train/validation/test assignments are retained; no new species/chromosome holdout is claimed for these reporter tasks.')
    plant_prom = pe('design-plant-promoter', 'Methods 4.9: plant promoters',
        'Promoter source sequences are from Arabidopsis, sorghum and maize, each 170 bp, assayed in tobacco leaf and maize protoplast. '
        'Outer join on species/gene/sequence permits one or both assay measurements. pPSup Addgene 149416 supplies a 154-bp 35S enhancer and species-specific H3 5′ UTR; full constructs 5,858 / 5,892 bp, padded to 6,016 bp. '
        'Conditioning is assay system and five activity bins with cutpoints −2.5 / 0 / 2.5 / 5. Leaf/protoplast host species are not the sequence-origin species.')
    plant_enh = pe('design-plant-enhancer', 'Methods 4.9: plant enhancers',
        'Enhancer source DNA is 170 bp accessible-chromatin candidates from Arabidopsis/sorghum/maize/tomato, with original source train/validation/test labels. '
        'Only four tobacco-leaf channels enter the model: light / dark / 35°C / 10°C; maize-protoplast channel excluded. '
        'Modified pPSntF Addgene 256230 has a 35S minimal promoter, maize H3 5′ UTR, fixed 18-bp barcode and EGFP; 5,670-bp construct padded to 5,760 bp. '
        'Five activity bins have cutpoints −2 / −1 / 0 / 1. These plant designs have independent activity-oracle/composition assessments, not new wet-lab activity validation.')
    fly = pe('design-fly-data', 'Methods 4.9: fly enhancers and fine-tuning',
        'DeepSTARR provides 484,052 distinct 249-bp Drosophila sequences (402,296 train / 40,570 validation / 41,186 test), each measured in DSCP and RpS12 contexts, giving 968,104 sequence–activity pairs. '
        'Each reporter is cropped to 4,096 bp, retaining source partitions; five equal-width activity bins use each promoter’s training range. '
        'Only the 249-bp insert is generated. Promoter-selective generation uses the same requested activity in target/background reporters; selectivity comes from context-specific guidance, not a lower background-bin request.')
    oracle = pe('design-oracle-realism', 'Methods 4.9: in-silico oracles, sequence realism and D3 comparison; Fig. 6/A.13–A.17',
        'Independent assay activity predictors assess designs against activity-matched native held-out sequences; DeepSTARR is the fly oracle. GC/k-mer/BLAST comparisons assess composition and novelty. '
        'Reported realism CNN uses four stratified folds × five seeds, 25 epochs, Adam 1e-3, no early stopping, with native/native and native/dinucleotide-shuffle controls at matched pool sizes. '
        'Also report pooled 4-mer Jensen–Shannon divergence in bits and 6-mer Jensen–Shannon distance, with source-matched shuffle controls. '
        'D3 comparison uses its DeepSTARR/EvoAug oracle, opposite held-out halves and five draws, comparing activity-matched NTv3 rather than only uniform-bin sampling. '
        'Paired continuous-conditioning fidelity and marginal-conditioning metrics are deliberately not reported because bin-prompted designs do not have equivalent conditioning.')
    wet = pe('design-fly-wetlab', 'Methods 4.9: selection and experimental validation; Fig. 6 / A.18',
        'For activity, select 60 per activity bin×five bins×two reporter contexts = 600 from 1,024 candidates/bin/context. '
        'For specificity, select 150 (75/context) from 10,240 generated candidates, plus 100 dual-high designs; compare 150 oracle-selected random uniform-DNA designs (75/context). '
        'Selection used the earlier first NTv3 checkpoint; v2 re-scores the designs, rather than generating a fresh v2 experimental cohort. '
        'UMI-STARR-seq in Drosophila S2 measures both DSCP/RpS12; require ≥10 input UMIs in every corresponding replicate. '
        'Activity is DESeq2 quantified, ordered-bin Spearman computed per reporter; calibration is median oracle minus median measured activity per bin. '
        'Specificity uses only valid paired reporter measurements and target/alternative fold change; geometric means and 95% CIs are computed in log2 space. Counts are before quality control.')
    for mid, name, definition, direction in [
        ('js-divergence', 'Jensen–Shannon divergence', 'Jensen–Shannon divergence in bits between source-defined pooled distributions; distinct from its square-root distance.', 'lower'),
        ('generation-separability', 'Generated/native sequence separability', 'Out-of-fold auROC of a generated/native sequence classifier, interpreted with native/native and native/dinucleotide-shuffle controls at the same pool size.', 'lower'),
        ('promoter-specificity', 'Promoter specificity', 'Geometric mean target-to-alternative reporter activity fold change, with confidence limits calculated in log2 space.', 'higher'),
        ('cosine-similarity', 'Cosine similarity', 'Cosine of the angle between the two source-defined vector outputs.', 'higher'),
        ('one-minus-js-divergence', 'One minus Jensen–Shannon divergence', 'One minus base-2 Jensen–Shannon divergence between specified normalized attention profiles.', 'higher'),
        ('motif-seqlet-fraction', 'Motif-group seqlet fraction', 'Fraction of activating TF-MoDISco enhancer seqlets assigned to each source-defined motif family; descriptive composition, not motif-recognition accuracy.', 'none'),
        ('mean-log2-effect', 'Mean log2 fold change', 'Mean source-defined log2 response over the specified positions and experimental or shuffled replicates.', 'none')]:
        c.put('metrics', dict(id=mid, name=name, definition=definition, direction=direction))
    design_ids = []
    for slug, eid, features, species, length, condition in [
        ('promoter', plant_prom, ['promoter'], ['Arabidopsis thaliana', 'Sorghum bicolor', 'Zea mays'], '170-bp insert in 6,016-bp padded reporter', 'tobacco leaf / maize protoplast and activity bin'),
        ('enhancer', plant_enh, ['enhancer'], ['Arabidopsis thaliana', 'Sorghum bicolor', 'Zea mays', 'Solanum lycopersicum'], '170-bp insert in 5,760-bp padded reporter', 'four tobacco-leaf conditions and activity bin')]:
        tid = 'ntv3-design-plant-' + slug
        new_task(tid, 'NTv3 plant ' + slug + ' generation', 'Published plant ' + slug + ' STARR-seq reporter data',
            'Conditioned reporter ' + slug + ' sequence design', 'conditional sequence generation', eid, features,
            ['generation', 'conditional-generation'], 'Generate only the candidate insert while retaining assay-specific reporter context; compare independent oracle response and native sequence controls.',
            output='170-bp designed DNA insert', form='sequence', apps=('plant-breeding', 'regulatory-engineering'),
            limitations='Activity validation is computational in this paper; no newly measured plant design cohort is reported. Assay host and native sequence provenance are distinct.')
        design_ids.append(tid)
        for sp in species:
            vid = tid + '-' + sp.lower().replace(' ', '-')
            variant(tid, vid, sp + ': ' + condition, eid, length,
                notes='Source DNA species; tobacco/maize assay-host labels do not add native source species.')
            layout.link(tid, sp, eid, vid)
        pid = tid + '-protocol'
        c.protocol(pid, tid, 'Conditional masked-diffusion reporter design', 'all-parameter conditional MDLM fine-tune',
            'Fixed reporter backbone with only the 170-bp insert generated; condition on ' + condition + '.',
            'Retain original source-study train/validation/test assignments; activity-matched native test sequences serve as reference.',
            'Native sequence / reporter condition', generation,
            [('selected-activity', 'Independent assay-specific activity oracle; requested-bin distributions versus matched native references.'),
             ('generation-separability', 'CNN native/generated auROC, four folds × five seeds, controlled for pool size/activity composition.'),
             ('js-divergence', 'Pooled 4-mer profiles versus species-matched native/shuffle references.'),
             ('js-distance', '6-mer square-root Jensen–Shannon divergence; distinct from 4-mer divergence.')],
            fitted='All generator weights and new condition embeddings; separate assay oracles and realism classifiers',
            selection='Source-reported diffusion EMA; independent classifier validation is out-of-fold, not best-test epoch.',
            notes='Null-condition training supports classifier-free guidance; no standalone unconditional score is inferred.')
        c.use(tid, 'ntv3', 'ntv3', generation, pid)
        c.limit('tasks', tid, 'partition-and-design-counts', 'not-reported',
            'Methods defines source partitions, insert/backbone and conditions but does not give exact per-partition usable construct counts or generated-pool counts for this plant task.', eid)
    # Replace the fly composite target with activity only; specificity is a separate dataset × target.
    for tid, target, evidence_id in [('ntv3-design-fly', 'Requested enhancer activity', fly),
                                     ('ntv3-design-fly-specificity', 'Core-promoter selectivity', wet)]:
        new_task(tid, 'NTv3 fly enhancer generation: ' + target.lower(), 'DeepSTARR / NTv3 UMI-STARR-seq design panel', target,
            'conditional sequence generation', evidence_id, ['enhancer'], ['generation', 'conditional-generation', 'context-specific'],
            'Generate 249-bp enhancers within fixed DSCP/RpS12 reporter contexts; independent oracle, native-sequence controls and new reporter measurements assess the stated target.',
            output='249-bp designed enhancer insert', form='sequence', apps=('regulatory-engineering',),
            limitations='The measured selection cohort was generated/filtered with the first checkpoint and rescored with v2. Selected counts precede input-UMI/paired-measurement quality control.')
        clear_pops(tid); layout.link(tid, 'Drosophila melanogaster', fly)
        design_ids.append(tid)
        pid = tid + '-protocol'
        c.protocol(pid, tid, 'Fly enhancer conditional diffusion and independent oracle', 'all-parameter conditional MDLM fine-tune',
            '249-bp insert inside 4,096-bp reporter; five activity bins per promoter, 50-step classifier-free guidance.',
            'Original DeepSTARR 402,296 / 40,570 / 41,186 sequence partitions; shared sequences across two reporter contexts retain their original assignment.',
            'Native enhancer / reporter context', fly,
            [('selected-activity', 'Independent DeepSTARR activity oracle versus condition-matched native held-out sequences.'),
             ('generation-separability', 'Four-fold × five-seed CNN comparison with matched native and shuffle brackets.'),
             ('js-divergence', 'Pooled 4-mer divergence in bits.'), ('js-distance', '6-mer Jensen–Shannon distance, including activity-matched D3 comparison.')],
            fitted='All generator parameters plus condition embeddings/activity-ranking head; independent oracle and realism classifier',
            notes='D3 arm uses the released D3 EvoAug oracle and opposite held-out halves; five draws. Unmatched uniform-bin NTv3 is a separately reported diagnostic arm.')
        c.use(tid, 'ntv3', 'ntv3', fly, pid)
        for part, n in [('train',402296), ('validation',40570), ('test',41186)]:
            c.count(tid, n, 'distinct native enhancer sequences', fly, split=part, qualifier='Each sequence has two promoter-context measurements; not twice as many distinct DNA sequences.')
        c.count(tid, 968104, 'native sequence–activity pairs', fly, split='all source partitions', qualifier='484,052 sequences × two core-promoter contexts.')
        vid = tid + '-earlier-checkpoint-wetlab'
        variant(tid, vid, 'First-checkpoint designs: S2 experimental reporter validation', wet,
            '249-bp insert in DSCP/RpS12 reporter; 300-bp synthesis oligonucleotide',
            notes='Earlier checkpoint generated/selected; v2 re-scored. Valid activity requires at least 10 input UMIs in every corresponding replicate.')
        wp = tid + '-wetlab-protocol'
        metrics = [('spearman', 'Ordinal requested bin versus measured activity per construct, separately for DSCP/RpS12.'),
            ('selected-activity', 'Per-bin measured activity distributions; median oracle-minus-measured calibration.')]
        if tid.endswith('specificity'):
            metrics = [('promoter-specificity', 'Valid paired reporters only; geometric mean target/alternative activity ratio and 95% CI in log2 space.')]
        c.protocol(wp, tid, 'Designed enhancer UMI-STARR-seq validation', 'generate and rank before independent reporter assay',
            'Select earlier-checkpoint designs; synthesize and assay both reporter contexts in Drosophila S2; DESeq2-normalized reporter activity.',
            'New experimental designs follow generation/ranking; these are not held-out natural genomic regions. Input representation QC and paired reporter eligibility precede specificity scoring.',
            'Designed enhancer / biological reporter replicate', wet, metrics, variant=vid,
            fitted='Generator/ranking head fitted before selection; no activity label fitting on the new design measurements',
            notes='Selection and oracle scores are distinct from experimental readout; effective post-QC denominator is not supplied as a single count.')
        c.use(tid, 'ntv3', 'ntv3', wet, wp)
        if tid.endswith('specificity'):
            c.count(tid, 150, 'selected promoter-specific designs', wet, variant=vid, protocol=wp,
                qualifier='75/context from 10,240 generated candidates; before paired activity QC.')
            c.count(tid, 100, 'selected dual-high designs', wet, variant=vid, protocol=wp,
                qualifier='Additional dual-context high-activity condition; not part of the 150 selective set.')
            c.count(tid, 150, 'oracle-selected random DNA controls', wet, variant=vid, protocol=wp,
                qualifier='75/context selected from a uniform-ACGT candidate pool; separate from generator output.')
        else:
            c.count(tid, 600, 'selected graded-activity designs', wet, variant=vid, protocol=wp,
                qualifier='60/bin×five bins×two contexts from 1,024 candidates/bin/context; before reporter QC.')
        c.limit('tasks', tid, 'experimental-post-qc-count', 'not-reported',
            'Selection sizes and input-UMI/paired-context QC rules are reported; a single exact retained design count for every scored group is not tabulated in the inspected source.', wet)
        c.limit('tasks', tid, 'new-design-raw-data-accession', 'not-reported',
            'The data-availability statement names upstream resources but provides no explicit accession or downloadable candidate/count matrix for the newly synthesized NTv3 reporter library.', wet)
    diagnostics = pe('checkpoint-diagnostics', 'Methods 4.3.9; Supplementary Fig. A.4d',
        'Single-length versus mixed-length checkpoints use 24 random test genes/species in all 15 functional species (360 genes), above median measured TSS RNA, ≥10 kb TSS spacing and ≤1% N (2% in sheep). '
        'Identical 1-Mb TSS-centered inputs: median per-track Pearson(log1p) over 393,216 central bp; cosine similarity of mean-centered input×gradient maps over 49,152 bp; '
        'one minus base-2 Jensen–Shannon divergence of head-averaged last-layer TSS attention profiles over 49,152 bp. Attribution objective is log summed RNA over first 2 kb downstream. '
        'These measure checkpoint agreement, not independent functional truth or effect causality.')
    motif = pe('motif-discovery', 'Methods 4.8.2 multispecies motif discovery / ortholog turnover; Fig. 5j,k',
        'Sample 1,000 enhancers/species (seed 20260902) from source-specific catalogs: ENCODE v4 dELS / pELS(human/mouse), lifted FlyBase S2 / BG3 state 3, RegAtlas GSE141213 worm, AraENCODE Arabidopsis. '
        'All 1,000 sequences are valid; whole 1-Mb context eligibility leaves 989 human / 998 mouse / 963 fly / 948 worm / 948 Arabidopsis. '
        'Species ATAC/DNase mean objective → mean-centered gradients → TF-MoDISco-lite 2.4 (1,000-bp crop, 500-bp analysis, maximum 2,000 seqlets) → pooled JASPAR 2026 / TOMTOM-lite p ≤ 1e-3. '
        'Broad cores >24 bp separate; CTCF requires p ≤ 1e-8. Output is activating-seqlet group composition, not held-out motif-site accuracy. One 300-bp human–mouse ortholog with 40-bp AP-1 inspection is a separate illustration.')
    hbe = pe('hbe1-restoration', 'Methods 4.8.2 enhancer–promoter task; Fig. 5c,d',
        'Human HBE1 window hg38 chr11:4,744,107–5,792,683 contains five HS1–HS5 elements. Dinucleotide-shuffle all five, then restore one at a time with five independent shuffled replicates/background-condition. '
        'Native K562 CAGE CNhs11250 score is mean per-base log2FC in 384 bp centered at HBE1 TSS 5,269,945; reported per-enhancer means/s.d. '
        'Fig. 5d compares five predicted effects with prior measured enhancer activity (Spearman 1.0, P = 0.017). This single locus and its reused native assay context are not a genome-wide held-out linking benchmark.')
    vep = pe('whole-blood-diagnostic', 'Methods 4.8.2 VEP task; Fig. 5f–i',
        'Inspect 3,792 GTEx Whole Blood variants on hg38 with 1-Mb allele-centered contexts, excluding chromosome-boundary crossings. '
        'Three named native GTEx RNA heads supply predicted central signal and nucleotide attributions; local hypothetical A/T/C/G gradients are compared directly. '
        'GENCODE v44 and Ensembl VEP are external context labels for selected examples, not NTv3-predicted transcript annotations. No cohort-level independent variant-effect accuracy score is defined for this diagnostic.')
    diag_ids = []
    native_species = sorted({r['species'] for r in next(s['rows'] for s in ART['sheets'] if s['name'].startswith('Supp Table 1 '))})
    for slug, target, metric in [('tracks', 'Functional-track checkpoint agreement', 'pearson'),
        ('attributions', 'RNA attribution checkpoint agreement', 'cosine-similarity'),
        ('attention', 'TSS attention checkpoint agreement', 'one-minus-js-divergence')]:
        tid = 'ntv3-checkpoint-agreement-' + slug
        new_task(tid, 'NTv3: ' + target.lower(), 'NTv3 360-gene checkpoint comparison', target,
            'model-output agreement diagnostic', diagnostics, ['gene', 'promoter'], ['interpretability', 'long-context'],
            'Compare single-length and mixed-length checkpoints on identical source-selected test gene contexts; high agreement is not a functional accuracy metric.',
            output='One agreement statistic per selected gene and modality', form='diagnostic', apps=('model-development',),
            limitations='Source describes the selection rule and aggregate agreement; exact sampled gene identity list is not released in the inspected tables.')
        diag_ids.append(tid)
        for sp in native_species:
            vid = tid + '-' + sp.lower().replace(' ', '-')
            variant(tid, vid, sp + ': 24 selected genes', diagnostics, '1,048,576-bp TSS-centered input',
                notes='Test genes with above-median TSS RNA and ≥10 kb spacing; N cutoff 1%, 2% in sheep.')
            layout.link(tid, sp, diagnostics, vid)
            c.count(tid, 24, 'selected test genes', diagnostics, variant=vid)
        pid = tid + '-protocol'
        c.protocol(pid, tid, 'Paired checkpoint agreement', 'inference-only comparison',
            'Identical species-token/context inputs; native track, attribution or attention readout.',
            '24 selected native-test genes per species; no new fitted probe and no independent accuracy labels.', 'Selected test gene', diagnostics,
            [(metric, 'Per gene using the modality-specific 393,216 / 49,152-bp window; summarize per species.')], fitted='None')
        c.use(tid, 'ntv3', 'ntv3', diagnostics, pid)
        c.limit('tasks', tid, 'sampled-gene-identity-list', 'not-released', 'The inspected source defines 360 selected test genes but does not release their exact identity/coordinate manifest.', diagnostics)
    tid = 'ntv3-motif-discovery'
    new_task(tid, 'NTv3: multispecies enhancer motif discovery', 'Five independent native enhancer catalogs', 'Activating enhancer-seqlet motif composition',
        'interpretation diagnostic', motif, ['enhancer', 'tfbs'], ['interpretability'],
        'Summarize motifs underlying model attribution in independent source-defined active enhancers, preserving differing regulatory catalog ontologies.',
        output='Activating seqlet fractions by motif-family/broad-pattern group', form='diagnostic', apps=('comparative-genomics', 'regulatory-engineering'),
        limitations='Motif matches and sequence composition are descriptive; the paper does not define a supervised held-out motif-site accuracy task.')
    diag_ids.append(tid)
    for sp, retained in [('Homo sapiens',989),('Mus musculus',998),('Drosophila melanogaster',963),('Caenorhabditis elegans',948),('Arabidopsis thaliana',948)]:
        vid = tid + '-' + sp.lower().replace(' ', '-')
        variant(tid, vid, sp + ': independent enhancer catalog', motif, '1-Mb attribution; 1,000-bp crop / 500-bp analysis')
        layout.link(tid, sp, motif, vid)
        c.count(tid, 1000, 'sampled enhancer sequences', motif, variant=vid, split='sequence-valid cohort')
        c.count(tid, retained, 'whole-context eligible enhancers', motif, variant=vid, split='attribution cohort')
    c.protocol(tid + '-protocol', tid, 'Enhancer attribution and motif grouping', 'native attribution; unsupervised motif aggregation',
        'Species-matched accessibility objective → mean-centered nucleotide gradients → TF-MoDISco-lite → JASPAR/TOMTOM motif-family grouping.',
        'Independent source-specific active enhancer catalogs, 1,000 random intervals/species; boundary filter for whole 1-Mb context. No train/test motif-label split.',
        'Enhancer / activating seqlet', motif, [('motif-seqlet-fraction', 'Percentage of activating seqlets by source-defined motif group, per species.')], fitted='TF-MoDISco unsupervised motif aggregation; no supervised prediction probe')
    c.use(tid, 'ntv3', 'ntv3', motif, tid + '-protocol')
    tid = 'ntv3-hbe1-restoration'
    new_task(tid, 'NTv3: HBE1 enhancer restoration', 'Human HBE1 HS1–HS5 experimental locus', 'Relative enhancer sufficiency for K562 promoter output',
        'perturbation / association diagnostic', hbe, ['enhancer', 'promoter'], ['interpretability', 'long-context'],
        'Compare restoration effects in dinucleotide-shuffled enhancer backgrounds with prior measured relative enhancer activity at one locus.',
        output='Promoter-window mean log2 CAGE effect per restored enhancer', form='diagnostic', apps=('regulatory-engineering',),
        limitations='Five enhancer observations at one native locus; prior assays and track context overlap functional supervision. This does not establish genome-wide causal recovery.')
    diag_ids.append(tid); layout.link(tid, 'Homo sapiens', hbe)
    c.count(tid, 5, 'tested enhancer elements', hbe, qualifier='HS1–HS5 in one HBE1 locus; each effect averages five independently shuffled replicates.')
    c.protocol(tid + '-protocol', tid, 'Single-enhancer restoration on ablated background', 'zero-shot sequence perturbation',
        'Shuffle all five HS sites, restore one, score native K562 CAGE across 384-bp HBE1 promoter; five shuffles/condition.',
        'One selected human locus; no task-label fitting or independent locus holdout.', 'Enhancer / shuffled background', hbe,
        [('mean-log2-effect', 'Mean ± s.d. over five shuffle replicates.'), ('spearman', 'Five enhancer scores against prior measured activity; Fig. 5d ρ = 1.0, P = 0.017.')], fitted='None')
    c.use(tid, 'ntv3', 'ntv3', hbe, tid + '-protocol')
    tid = 'ntv3-whole-blood-response'
    new_task(tid, 'NTv3: Whole Blood allele-response inspection', 'GTEx Whole Blood selected variants', 'Native RNA and attribution response to allele substitution',
        'model-response diagnostic', vep, ['regulatory', 'splice'], ['variant-effects', 'interpretability', 'long-context'],
        'Inspect paired native RNA/attribution responses at selected alleles; external transcript/consequence annotations provide interpretation context only.',
        output='Allele-specific native signal and local hypothetical gradient changes', form='diagnostic', apps=('variant-interpretation',),
        limitations='No source-defined cohort accuracy metric, causal validation or predicted whole-isoform annotation is asserted. The 3,792 input count is not an established post-boundary-filter count.')
    diag_ids.append(tid); layout.link(tid, 'Homo sapiens', vep)
    c.count(tid, 3792, 'source variants', vep, qualifier='Reported analyzed/source cohort; exact retained count after full-context chromosome-boundary exclusion is not separately tabulated.')
    c.protocol(tid + '-protocol', tid, 'Paired Whole Blood allele readout', 'zero-shot native prediction and attribution',
        'Matched 1-Mb allele-centered inputs; native three Whole Blood RNA tracks; hypothetical A/T/C/G gradients.',
        'Selected GTEx Whole Blood SNVs; exclude out-of-chromosome contexts. No independent benchmark-label split.', 'SNV / local response', vep,
        [], fitted='None', notes='Qualitative/model-response diagnostic; no cohort-level accuracy metric is defined.')
    c.use(tid, 'ntv3', 'ntv3', vep, tid + '-protocol')
    c.limit('protocols', tid + '-protocol', 'accuracy-metric', 'not-applicable', 'The source defines response inspection and representative examples, not a cohort-level supervised prediction metric.', vep)
    return _resources_and_reviews(c, layout, pe, manifest, native, bmeta, bprotocol, tutorial, borzoi, borzoi_meta,
        ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids, external, sei, agro, deep,
        danio, eqtl, eqtl_counts, re2g, generation, plant_prom, plant_enh, fly, oracle, wet, diagnostics, motif, hbe, vep, design_ids, diag_ids)


def _resources_and_reviews(c, layout, pe, manifest, native, bmeta, bprotocol, tutorial, borzoi, borzoi_meta,
        ag, ag_meta, annotation, ann_meta, ann_results, protein, runtime, borzoi_tids, external, sei, agro, deep,
        danio, eqtl, eqtl_counts, re2g, generation, plant_prom, plant_enh, fly, oracle, wet, diagnostics, motif, hbe, vep, design_ids, diag_ids):
    d = c.data
    owned = {t['id'] for t in d['tasks'] if t['id'].startswith('ntv3-') and t['id'] != 'ntv3-design-plant'}
    # The plant record combined two distinct released datasets/targets, so retire it.
    obsolete = 'ntv3-design-plant'
    obsolete_protocols = {p['id'] for p in d['protocols'] if p['task_id'] == obsolete}
    obsolete_variants = {v['id'] for v in d['variants'] if v['task_id'] == obsolete}
    for table in ['tasks', 'evaluation_tasks', 'variants', 'task_populations', 'task_categories', 'protocols', 'counts',
                  'model_evaluations', 'coverage_mappings', 'task_outputs', 'task_feature_scopes', 'task_resources', 'task_tracks']:
        if table not in d: continue
        d[table] = [r for r in d[table] if r.get('task_id', r.get('id') if table == 'tasks' else None) != obsolete]
    d['protocol_metrics'] = [r for r in d['protocol_metrics'] if r['protocol_id'] not in obsolete_protocols]
    for table in ['field_evidence', 'source_reviews', 'source_limits']:
        d[table] = [r for r in d[table] if not (r.get('entity_table') == 'tasks' and r.get('entity_id') == obsolete)
            and not (r.get('entity_table') == 'protocols' and r.get('entity_id') in obsolete_protocols)]
    c.put('task_redirects', dict(id=obsolete, evaluation_id='ntv3-evals', replacement_task_id=None,
        reason='Split dataset × target into ntv3-design-plant-promoter and ntv3-design-plant-enhancer; distinct reporter data, source-species cohorts, conditioning and constructs.'))
    # Every source file linked below was read or its gated response/file inventory inspected.
    rev = SRC['space']['revision']
    space = f'https://huggingface.co/spaces/{SRC["space"]["id"]}'
    codebase = space + '/blob/' + rev + '/'
    c.source('ntv3-pinned-space', 'NTv3 release: tutorials and coding annotation evaluator', space + '/tree/' + rev,
        'code', rev, notes='Fourteen code/notebook files inspected; hashes in data/ntv3-source-inspections.json. Public tutorials are distinct from gated model weights.')
    code = c.evidence('ntv3-final-space-code', 'ntv3-pinned-space',
        'src/genome_annotation/{data,decoding,evaluation,proteins,analysis}.py; notebooks_tutorials',
        'Released evaluator exact CDS key is contig/start/end/strand/phase; whole-gene equality compares the entire coding-exon set. '
        'Reference filtering removes no-CDS/overlapping-CDS/readthrough/shared-CDS conflicts and same-strand envelope conflicts; predictions below 201 CDS bp and pseudogene-only overlaps away from references are filtered. '
        'Decoder imposes phase-aware start/splice/stop grammar and drops internal-stop models. Tutorials separate annotation training, structured decoding and reference evaluation.', 'code',
        codebase + 'src/genome_annotation/evaluation.py#L118-L146')
    code_resource = c.resource('ntv3-annotation-evaluation-code', 'ntv3-pinned-space', 'NTv3 coding annotation evaluator',
        'evaluation-code', 'huggingface', codebase + 'src/genome_annotation/evaluation.py', code, revision=rev,
        notes='Evaluation implementation, not reference annotations or predicted GFF data.')
    tutorial_resource = c.resource('ntv3-benchmark-finetuning-code', 'ntv3-benchmark-tutorial', 'NTv3 benchmark fine-tuning tutorial',
        'evaluation-code', 'huggingface', c.get('sources','ntv3-benchmark-tutorial')['url'], tutorial, revision=rev,
        notes='Includes dataset window enumeration, target scaling, full-backbone benchmark mode and separate frozen-trunk Colab mode.')
    design_resource = c.resource('ntv3-diffusion-tutorial-code', 'ntv3-pinned-space', 'NTv3 masked diffusion and plant promoter tutorials',
        'evaluation-code', 'huggingface', codebase + 'notebooks_tutorials/05_diffusion_fine_tuning.ipynb', generation, revision=rev,
        notes='Generation/fine-tuning tutorial; not a released new-design reporter measurement matrix.')
    book_resource = c.resource('ntv3-full-workbook-manifest', 'ntv3-complete-workbook', 'NTv3 complete assay/assembly identity workbook',
        'manifest', 'other', XLS, manifest, notes='C.1 native track identities; C.2 annotation assemblies/partitions; C.4 benchmark track identities. Track identities are not a split-coordinate manifest.')
    results_resource = c.resource('ntv3-full-workbook-results', 'ntv3-complete-workbook', 'NTv3 per-track, per-species and tissue benchmark results',
        'results', 'other', XLS, ann_results, notes='C.3–C.10 published results; performance rows are not biological dataset examples.')
    supplement_results = c.resource('ntv3-supplement-results', 'ntv3-complete-supplement', 'NTv3 supplementary figures and analysis results',
        'results', 'other', SUP, oracle, notes='Generation, interpretation, protein and regulatory-linking results; exact figure/method references are linked to individual tasks.')
    benchrev = SRC['benchmark']['revision']
    bench = f'https://huggingface.co/datasets/{SRC["benchmark"]["id"]}'
    metadata_resource = c.resource('ntv3-benchmark-track-identities', 'ntv3-benchmark-metadata', 'NTv3 Benchmark: 155-track metadata rows',
        'manifest', 'huggingface', bench + '/blob/' + benchrev + '/benchmark_metadata.tsv', bmeta, revision=benchrev,
        notes='Exact experiment/assembly/assay identities inspected; split membership is in the separate per-species BED files.')
    bench_resource = c.resource('ntv3-benchmark-signal-data', 'ntv3-benchmark-metadata', 'NTv3 Benchmark: 11-species FASTA and BigWig data',
        'dataset', 'huggingface', bench + '/tree/' + benchrev, bmeta, revision=benchrev,
        notes='Public file inventory verified. FASTA bases and raw BigWig signals were not downloaded for this catalogue audit; all 155 metadata rows and 11 split BEDs were fully read.')
    for rid, eid, relation in [(book_resource,manifest,'identity-manifest'),(results_resource,ann_results,'results'),
        (metadata_resource,bmeta,'identity-manifest'),(bench_resource,bmeta,'evaluation-data'),(supplement_results,oracle,'results'),
        (tutorial_resource,tutorial,'evaluation-code'),(code_resource,code,'evaluation-code'),(design_resource,generation,'evaluation-code')]:
        c.collection_resource('ntv3-evals', rid, eid, relation)
    for r in [x for x in d['data_resources'] if x['id'].startswith('ntv3-benchmark-split-')]:
        c.collection_resource('ntv3-evals', r['id'], bmeta, 'split-manifest')
    # Exact immutable model release identities and restricted annotation predictions.
    checkpoint = c.evidence('ntv3-final-checkpoint-inventory', 'ntv3-pinned-space',
        'HF model API file inventories / six pinned model revisions; data/ntv3-source-inspections.json',
        'Six released checkpoint repositories have manual gating. The 1-Mb single-length and mixed-length track repositories are distinct revisions. '
        'Annotation repositories list 17 test-assembly GFF3.gz prediction files across mammals/plants/insects; one file request per clade returned 401. '
        'The inventory establishes released file identity, not inspection of gated GFF content or model tensors.', 'documentation', space + '/tree/' + rev)
    for key, meta in SRC['models'].items():
        sid = 'ntv3-checkpoint-' + key.lower().replace('_','-')
        url = 'https://huggingface.co/' + meta['id'] + '/tree/' + meta['revision']
        c.source(sid, meta['id'] + ' checkpoint files', url, 'model-card', meta['revision'],
            notes='Model API inventory inspected; manually gated model/file content. No inference execution or tensor inspection is claimed.')
        eid = c.evidence(sid + '-inventory', sid, 'HF API siblings/revision/gated fields',
            'Verified revision ' + meta['revision'] + ' and manual gating. Exact file inventory is committed in data/ntv3-source-inspections.json.', 'documentation')
        c.field('models','ntv3','checkpoints',eid, key + ' is a distinct released checkpoint, not a new independently benchmarked model family.')
        for file in meta['files']:
            if not file.startswith('annot_results/') or not file.endswith('.gff3.gz'): continue
            rid = 'ntv3-result-' + file.rsplit('/',1)[1].replace('.gff3.gz','')
            resource = c.resource(rid, sid, file.rsplit('/',1)[1], 'results', 'huggingface',
                'https://huggingface.co/' + meta['id'] + '/blob/' + meta['revision'] + '/' + file,
                eid, revision=meta['revision'], availability='restricted',
                notes='Predicted coding gene models, not reference truth. Repository requires manual access; representative result request in this clade returned 401.')
            c.collection_resource('ntv3-evals', resource, eid, 'results')
            for tid in ['ntv3-annotation-exon','ntv3-annotation-gene']:
                c.task_resource(tid, resource, eid, 'results', note='Source assembly is explicit in the file name; all seventeen output files remain source-specific.')
    c.limit('models','ntv3','restricted-release-content','access-restricted',
        'Six pinned repositories list checkpoint/code files publicly but require manual access. Track metadata file and representative clade GFF result requests return401; the public C.1/C.2 workbook supplies identities independently.', checkpoint)
    for tid in owned | set(borzoi_tids):
        if tid in design_ids or tid in diag_ids or tid == 'ntv3-re2g' or tid in ['ntv3-annotation-intron-chain','ntv3-annotation-protein-identity','ntv3-annotation-valid-orf','ntv3-annotation-busco']:
            c.task_resource(tid, supplement_results, c.get('tasks',tid)['evidence_id'], 'results', note='Source-specific figure or supplementary analysis; this task has no dedicated result worksheet in C.1–C.10.')
        else:
            c.task_resource(tid, results_resource, c.get('tasks',tid)['evidence_id'], 'results', note='Task-specific worksheet/result panel; source limits state any absent example identities.')
        if tid.startswith(('ntv3-tracks-','ntv3-annotation-','ntv3-benchmark-')) or tid in borzoi_tids or tid.startswith('ntv3-ag-'):
            c.task_resource(tid, book_resource, manifest, 'identity-manifest', note='See the task-specific C.1/C.2/C.4/C.7/C.8 panel; not a raw-signal or coordinate-split substitute.')
        if tid.startswith('ntv3-benchmark-'):
            c.task_resource(tid, metadata_resource, bmeta, 'identity-manifest')
            c.task_resource(tid, bench_resource, bmeta, 'evaluation-data')
            c.task_resource(tid, tutorial_resource, tutorial, 'evaluation-code')
        if tid.startswith('ntv3-annotation-'):
            c.task_resource(tid, code_resource, code, 'evaluation-code')
            c.field('tasks',tid,'output-and-reference-matching',code,'Pinned evaluator distinguishes phase-aware exon sets, complete coding chains and filtered reference eligibility.')
        if tid in design_ids:
            c.task_resource(tid, design_resource, generation, 'evaluation-code')
    # Verified upstream data links from the primary methods. They are not asserted
    # to reproduce NTv3-specific masks or changed gene preprocessing by themselves.
    upstream = [
        ('ntv3-chiphub', 'ChIP-Hub H3K4me3 source experiments', 'https://biobigdata.nju.edu.cn/ChIPHub_download', sei, ['ntv3-seiplant']),
        ('ntv3-deepfarm-geo', 'DeepFARM / FAANG peak-call source GSE158430', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE158430', deep, ['ntv3-deepfarm','ntv3-deepfarm-ctcf']),
        ('ntv3-worm-regatlas', 'RegAtlas worm regulatory elements GSE141213', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE141213', motif, ['ntv3-motif-discovery']),
        ('ntv3-human-enhancers', 'ENCODE human enhancer catalog ENCFF420VPZ', 'https://www.encodeproject.org/files/ENCFF420VPZ/', motif, ['ntv3-motif-discovery']),
        ('ntv3-mouse-enhancers', 'ENCODE mouse enhancer catalog ENCFF167FJQ', 'https://www.encodeproject.org/files/ENCFF167FJQ/', motif, ['ntv3-motif-discovery'])]
    for sid,title,url,eid,tids in upstream:
        c.source(sid,title,url,'dataset',notes='Exact upstream accession/link in NTv3 Methods; NTv3-specific derived interval masks are separately qualified.')
        resource = c.resource(sid + '-data',sid,title,'dataset','other',url,eid,
            notes='Upstream experimental source; NTv3-specific preprocessing/scoring cohorts are not asserted byte-identical to the full archive.')
        for tid in tids: c.task_resource(tid,resource,eid,'upstream-data')
        c.collection_resource('ntv3-evals',resource,eid,'upstream-data')
    # Existing original DeepSTARR data release is already artifact-audited by a
    # separate collection review; reuse that exact resource, without claiming a
    # released NTv3 reporter-context transform or new-design count matrix.
    for rid in ['final-deepstarr-original-data','final-data-GenerTeam-DeepSTARR-enhancer-activity']:
        if any(r['id']==rid for r in d['data_resources']):
            for tid in ['ntv3-design-fly','ntv3-design-fly-specificity']:
                c.task_resource(tid,rid,fly,'upstream-data',note='Native DeepSTARR training/evaluation sequences; not the newly synthesized NTv3 designs.')
    # Scope each review to the source-defined target and linked protocol group.
    evidence_for = {}
    for tid in owned:
        t = c.get('tasks',tid)
        eids = {t['evidence_id']}
        eids.update(p['source_evidence_id'] for p in d['protocols'] if p['task_id']==tid)
        eids.update(v['evidence_id'] for v in d['variants'] if v['task_id']==tid)
        eids.update(r['evidence_id'] for r in d['counts'] if r['task_id']==tid)
        if tid.startswith('ntv3-tracks-'): eids.update([manifest,native])
        if tid.startswith('ntv3-annotation-'): eids.update([annotation,ann_meta,ann_results,code])
        if tid in design_ids: eids.update([generation,oracle])
        evidence_for[tid] = sorted(eids)
        if tid.startswith('ntv3-checkpoint-agreement-') or tid == 'ntv3-whole-blood-response':
            t['label_basis'] = 'Paired model readouts; no independent functional accuracy labels are defined for this diagnostic.'
        elif tid == 'ntv3-motif-discovery':
            t['label_basis'] = 'Independent source-defined enhancer catalogs seed model attribution; motif grouping is a descriptive model-readout analysis.'
        c.review('tasks',tid,
            'NTv3 v2 target, source population, output/scoring unit, fitting, split rules, available counts, metrics and linked release identities reviewed against the complete Methods and task-specific supplementary tables; code/metadata inspected where explicitly cited.',
            evidence_for[tid], t.get('limitations',''))
        for field in ['target','task_type','input_description','output_description','limitations']:
            c.field('tasks',tid,field,t['evidence_id'],'Task-specific primary source; linked protocol/variant evidence provides finer distinctions.')
        if tid.startswith('ntv3-tracks-'):
            c.limit('tasks',tid,'native-window-count','not-reported',
                'C.1 gives exact track identities and Methods gives window/crop/partition construction; a complete per-species native evaluation-window count is not tabulated.',native)
            c.limit('tasks',tid,'raw-track-signal-recomputation','not-retrieved',
                'All C.1/C.5 identities and source results were read; underlying multi-species raw signal tensors were not downloaded/recomputed. This audit establishes source-defined tracks, not independent reproduction of correlations.', manifest)
    for tid in borzoi_tids:
        old = next((r for r in d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==tid),None)
        old_eids = json.loads(old['evidence_ids_json']) if old else []
        addition = 'NTv3 C.7 human panel and distinct native 1-bp / full-adaptation 32-bp protocols reviewed; released track IDs are indexed, without assuming equivalence to the AIDO subset.'
        scope = old['scope'] if old and addition in old['scope'] else (old['scope'] + ' ' if old else '') + addition
        c.review('tasks',tid,scope,old_eids + [borzoi,borzoi_meta],c.get('tasks',tid).get('limitations',''))
    for p in d['protocols']:
        if p['task_id'] not in owned and not p['id'].startswith('ntv3-borzoi-'): continue
        c.review('protocols',p['id'],
            'Source-specific fitting, model interface, partition/cohort eligibility, scored output geometry, selection and metric reduction reviewed; unavailable identities or counts are recorded at task/collection level.',
            [p['source_evidence_id']], p.get('notes') or '')
    ev = c.get('evaluations','ntv3-evals')
    ev.update(source_id='ntv3-paper', status='source-reviewed', evidence_id=manifest,
        description='NTv3 v2 native functional profiles, standardized 11-species adaptation, human matched panels, coding annotation, external transfer, regulatory linking/variants, reporter generation and quantitative interpretation diagnostics.',
        scope_note='Dataset × target tasks retain source-specific species/assay/assembly/context and protocol variants; track identity is separate from sequence-example count.',
        notes='Full paper, 38-page supplementary notes and ten-sheet workbook reviewed; all native/benchmark/matched-panel track identities indexed. Public metadata/splits are artifact-inspected; raw signal and gated model/prediction content are not asserted reproduced.')
    full_eids = [manifest,native,bmeta,bprotocol,tutorial,borzoi,borzoi_meta,ag,ag_meta,annotation,ann_meta,ann_results,protein,runtime,
        external,sei,agro,deep,danio,eqtl,eqtl_counts,re2g,generation,plant_prom,plant_enh,fly,oracle,wet,diagnostics,motif,hbe,vep,code,checkpoint]
    c.review('evaluations','ntv3-evals',
        'Complete NTv3 v2 primary text, all 38 supplement pages and all ten workbook sheets; task decomposition, native 16,262 / benchmark 155 / Borzoi 7,611 / AlphaGenome 1,643 track identities, exact public benchmark intervals, annotation 17-species cohorts, reporter context and quantitative diagnostics reviewed.',
        full_eids,
        'Metadata and source-reported results audited, not independent raw-signal performance reproduction. Restricted model/GFF content and source-unreleased derived cohorts are identified per field.')
    for table,id in [('models','ntv3'),('papers','ntv3')]:
        c.review(table,id,
            'October 2026 v2 full report and complete supplement/workbook: corpus/objective, architecture/token vocabulary, staged context protocols, distinct checkpoint roles, target-specific evaluation and release availability reviewed.',
            full_eids,
            'Public file inventories distinguish manual-gated checkpoints and GFF outputs. Earlier first-checkpoint experimental designs are not relabeled as new v2-generated sequences.')
    for eid,tids,source_eid in [('seiplant',['ntv3-seiplant'],sei),('deepfarm',['ntv3-deepfarm','ntv3-deepfarm-ctcf'],deep),
        ('daniodecima',['ntv3-danio'],danio),('re2g',['ntv3-re2g'],re2g)]:
        ev = c.get('evaluations',eid)
        ev.update(status='source-reviewed',evidence_id=source_eid,
            scope_note='Scope is the NTv3 re-evaluation subset and linked protocols; no broader original-release task inventory or original-paper full-text review is implied.',
            notes='NTv3 primary methods/results reviewed; source-specific masks, transformed targets and restricted/common cohorts remain explicit.')
        for tid in tids: c.member(tid,eid,source_eid,note='NTv3-specific protocol/subset; original release scope is not expanded by inference.')
        c.review('evaluations',eid,
            'NTv3 full Methods re-evaluation and complete supplementary result panel for the named source; source target, population and comparator restrictions audited. Original source full text was not reviewed in this pass.',
            [source_eid,external if eid!='re2g' else re2g],
            'Collection covers indexed NTv3 re-evaluation claims; original source data availability and unindexed tasks are not generalized from citations.')
        for r in d['task_resources']:
            if r['task_id'] in tids:
                c.collection_resource(eid,r['resource_id'],r['evidence_id'],r['relation'],note=r.get('note') or '')
    # Remove superseded unspecific audit-work notes only when their NTv3 claim
    # has now been replaced with the explicit protocol/source-limit records.
    for f in d['findings']:
        if 'ntv3' in str(f).lower() and any(w in str(f).lower() for w in ['pending','remain to be checked','incomplete']):
            f.update(description='NTv3 native C.1 lists 16,262 tracks; C.5 reports 16,260 unique results, omitting one rice and one maize histone track. The standardized benchmark has 155 tracks in 11 species; Evo 2 is independently fine-tuned only in five. Original and external model evaluations remain distinct.', evidence_id=manifest)
    # Quantitative profiles are not categorical dense annotation; native or
    # adapted profile heads retain their dedicated capability classification.
    profile_ids = {r['task_id'] for r in d['task_outputs'] if r['category_id']=='output-signal-profile' and r['task_id'] in owned}
    d['task_categories'] = [r for r in d['task_categories'] if not (r['task_id'] in profile_ids and r['category_id']=='dense-annotation')]
    # Refresh the older generic category rationales against the now-specific
    # target/source record; application relevance remains an interpretation.
    outputs = {r['task_id']:r for r in d['task_outputs']}
    dimensions = {r['id']:r['dimension'] for r in d['categories']}
    for row in d['task_categories']:
        if row['task_id'] not in owned: continue
        tid = row['task_id']; task = c.get('tasks',tid)
        dim = dimensions[row['category_id']]
        if dim == 'output':
            row.update(evidence_id=outputs[tid]['evidence_id'],rationale=outputs[tid]['rationale'])
        elif not row['evidence_id'].startswith('ntv3-final-'):
            row.update(evidence_id=task['evidence_id'],rationale=
                ('Application relevance of the source-defined target; not an independently validated industrial result. ' if dim == 'application' else '') +
                'Target: ' + task['target'] + '. ' + task['description'])
    # Stable order after common.output replaces an output classification.
    changed = owned | set(borzoi_tids)
    population_links = {(r['task_id'],r['population_id']):r for r in d['task_populations']}
    populations = {r['id']:r for r in d['populations']}
    for row in d['coverage_mappings']:
        if row['task_id'] not in changed or not row['population_id']: continue
        pop = populations[row['population_id']];link = population_links.get((row['task_id'],row['population_id']))
        url = c.get('evidence',row['evidence_id'])['url']
        row['basis'] = 'Source-named evaluation population'
        taxev = 'final-taxonomy-' + str(pop.get('ncbi_taxid')) + '-classification'
        row['supporting_json'] = json.dumps([row['evidence_id']] + ([taxev] if any(e['id']==taxev for e in d['evidence']) else []))
        row['metadata_json'] = json.dumps(dict(name=pop['name'],row=row['species_row'].split(':',1)[-1],
            species=pop['name'],speciesId=pop.get('ncbi_taxid'),clade=row['clade_row'].split(':',1)[-1],
            allSpeciesRow=row['all_species_row'].split(':',1)[-1],basis='Source-named evaluation population',
            url=url,links=[url],taxonomy='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(pop['ncbi_taxid']) if pop.get('ncbi_taxid') else '',
            note=link['coverage'] if link else 'Source-named evaluation population.'),ensure_ascii=False)
    d['task_categories'] = [r for r in d['task_categories'] if r['task_id'] not in changed] + sorted(
        [r for r in d['task_categories'] if r['task_id'] in changed], key=lambda r:(r['task_id'],r['category_id'],r['relation']))
    for table in ['task_populations','coverage_mappings']:
        d[table] = [r for r in d[table] if r['task_id'] not in changed] + sorted(
            [r for r in d[table] if r['task_id'] in changed], key=lambda r:(r['task_id'],r.get('population_id') or '',r.get('relation') or '',r.get('id') or ''))
    return {'tasks':len(owned), 'native_tracks':16262, 'benchmark_tracks':155, 'borzoi_tracks':7611, 'alphagenome_tracks':1643,
        'new_design_targets':design_ids, 'quantitative_diagnostics':diag_ids}
