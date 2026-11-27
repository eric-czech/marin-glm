"""Complete the Evo 1 source review and distinguish code, weights and assay data.

Authoring helper only. It requires the already integrated evo1_audit records and
uses the compact committed inspection manifest, not the ignored research cache.
"""
import json
from common import Catalogue, ROOT

INSPECTIONS = json.loads((ROOT / 'data/evo1-artifact-inspections.json').read_text())
REV = INSPECTIONS['repository']['revision']
PDF = 'https://arcinstitute.org/publications/science.ado9336.pdf'


def populate(d):
    c = Catalogue(d)
    availability = c.evidence('evo1-data-availability', 'evo1-paper',
        'Data and materials availability, article p. 21; PDF page 22',
        'The paper identifies four original checkpoints, the OpenGenome pretraining train/validation/test release, '
        'the shared GitHub repository and Zenodo code archive. Generated experimental DNA/RNA/protein sequences '
        'are assigned to Data S1. These are distinct resources; the pretraining corpus is not a downstream evaluation dataset.',
        url=PDF + '#page=22')

    # Exact fixed archive named by the paper; inspected files are recorded locally.
    z = INSPECTIONS['zenodo']
    zurl = 'https://zenodo.org/records/12693561/files/evo-main.zip'
    c.source('evo1-original-code-archive', 'Evo 1 original Zenodo code release', zurl,
        'repository-archive', '10.5281/zenodo.12693561; ' + z['checksum'],
        notes='Complete original 4,837,008-byte ZIP inspected; member identities and hashes are in data/evo1-artifact-inspections.json.')
    c.get('sources', 'evo1-original-code-archive')['sha256'] = z['sha256']
    zenodo = c.evidence('evo1-original-code-archive-review', 'evo1-original-code-archive',
        'Complete ZIP member inspection',
        'The original archive contains the Evo inference/scoring/generation package, configuration files, example sequence file and scripts. '
        'It does not contain the filtered DMS, ncRNA, promoter, essentiality or selected-generation assay tables. '
        'It is a code release, rather than Data S1 or an evaluation dataset.', 'data')
    zr = c.resource('evo1-original-code-resource', 'evo1-original-code-archive',
        'Evo 1 original code archive', 'evaluation-code', 'zenodo', zurl, zenodo,
        revision='10.5281/zenodo.12693561',
        notes='Original archived inference/scoring code. No filtered evaluation cohort tables are included.')
    c.collection_resource('evo1-original', zr, zenodo, 'evaluation-code')

    ghurl = f'https://github.com/evo-design/evo/tree/{REV}'
    c.source('evo1-repository-inventory', 'Evo shared repository at the inspected revision',
        ghurl, 'repository-tree', REV,
        notes='Tracked file inventory is in data/evo1-artifact-inspections.json. Later semantic-design and phage-generation data are not the 2024 evaluation cohorts.')
    gh = c.evidence('evo1-repository-scope-review', 'evo1-repository-inventory',
        'Pinned tracked-file inventory, README checkpoint table and dated news',
        'The pinned shared repository includes the original inference/scoring package alongside later semantic_design and phage_gen work. '
        'The later phage FASTA/GFF files and semantic-design prompts do not establish release of the original Science 2024 evaluation cohorts.', 'code')
    gr = c.resource('evo1-pinned-code-resource', 'evo1-repository-inventory',
        'Evo 1 pinned shared code repository', 'evaluation-code', 'github', ghurl, gh,
        revision=REV, notes='Contains later studies as well as original Evo 1 inference; original-paper scope is tracked separately.')
    c.collection_resource('evo1-original', gr, gh, 'evaluation-code')

    # The paper states the source-data role; PMC supplies the actual file identity.
    surl = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12057570/'
    s1url = surl.replace('/PMC12057570/', '/instance/12057570/bin/NIHMS2055853-supplement-S1.zip')
    c.source('evo1-supplement-index', 'Evo 1 PMC supplementary material index', surl,
        'article-supplement-index', 'PMC12057570; inspected 2026-11-27',
        notes='Full article HTML inspected. It links Supplement.pdf, S1.zip and Checklist.pdf; the file requests returned a browser download challenge rather than PDF/ZIP bytes.')
    c.get('sources', 'evo1-supplement-index')['sha256'] = INSPECTIONS['supplementary_material']['landing_sha256']
    supp = c.evidence('evo1-supplement-availability-review', 'evo1-supplement-index',
        'Supplementary material links and recorded retrieval responses',
        'PMC lists NIHMS2055853-supplement-S1.zip and NIHMS2055853-supplement-Supplement.pdf. '
        'The exact linked file requests returned a Preparing to download browser challenge; Europe PMC supplementaryFiles reports that this article is not open access. '
        'The file contents were not retrieved, so Data S1 sequences and supplementary tables have not been artifact-audited.', 'documentation')
    sr = c.resource('evo1-data-s1-resource', 'evo1-supplement-index',
        'Evo 1 Data S1: generated validation sequences', 'dataset', 'other', s1url, supp,
        revision='NIHMS2055853-supplement-S1.zip', availability='not-retrieved',
        notes='Primary article assigns generated validation sequences to Data S1. File identity verified in PMC; download returned a browser challenge, and archive contents were not read.')
    c.collection_resource('evo1-original', sr, availability,
        note='Generated experimental sequence resource; does not certify all downstream filtered assay cohorts.')

    # Weight repositories are model release sources, never mislabeled as datasets.
    hf_evidence = []
    for slug in ['8k', '131k', 'crispr', 'transposon']:
        row = INSPECTIONS['huggingface'][slug]
        name, revision = row['id'], row['revision']
        url = f'https://huggingface.co/{name}/blob/{revision}/config.json'
        sid = 'evo1-hf-' + slug
        c.source(sid, name + ': pinned model configuration', url, 'model-configuration', revision,
            notes='Public repository metadata, card and configuration inspected. Weight filenames verified; multi-gigabyte tensor values were not downloaded.')
        c.get('sources', sid)['sha256'] = row['config_sha256']
        cfg = row['config']
        text = f'Public {name} repository at commit {revision}: 32 layers, hidden width 4096, 512-token vocabulary, maximum sequence length {cfg["max_seqlen"]:,}.'
        if slug in ['8k', '131k']:
            text += ' The inspected revision is the corrected 1.1_fix branch, not proof that its tensor bytes match the checkpoint used in the 2024 experiments.'
        else:
            text += ' Fine-tuned specialist checkpoint identified by the original paper; current repository main is pinned separately.'
        eid = c.evidence(sid + '-review', sid, 'Pinned config.json, README and public repository file inventory', text, 'data')
        hf_evidence.append(eid)
        c.field('models', 'evo1', 'release', eid, 'Pinned model weights source; distinct from evaluation data.')
        c.field('model_properties', 'evo1-release', 'value', eid, 'Current inspected checkpoint revision; no claim of paper-time byte identity.')
    c.get('model_properties', 'evo1-release')['notes'] = (
        'Original checkpoints: togethercomputer/evo-1-8k-base, togethercomputer/evo-1-131k-base, '
        'LongSafari/evo-1-8k-crispr and LongSafari/evo-1-8k-transposon. Current pinned configurations and file inventories verified; '
        'the original Science assay scores were not independently regenerated with these revisions.')

    og = INSPECTIONS['huggingface']['open-genome']
    ogurl = f'https://huggingface.co/datasets/LongSafari/open-genome/tree/{og["revision"]}'
    c.source('evo1-open-genome-release', 'OpenGenome pretraining dataset release', ogurl,
        'dataset-repository', og['revision'],
        notes='Dataset card and full file inventory inspected; large Parquet shards not rescanned. This is pretraining data, not a filtered downstream assay release.')
    oge = c.evidence('evo1-open-genome-release-review', 'evo1-open-genome-release',
        'Pinned README configurations and file inventory',
        'The release declares stage1 and stage2 train/validation/test configurations; stage1 lists GTDB and IMG/PR Parquet files, and stage2 has separate combined files. '
        'A sample configuration reuses stage2 validation. The declared corpus partitions do not specify the source-study assay partitions used for downstream evaluation.', 'documentation')
    ogr = c.resource('evo1-open-genome-resource', 'evo1-open-genome-release',
        'OpenGenome: Evo 1 pretraining corpus', 'dataset', 'huggingface', ogurl, oge,
        revision=og['revision'], notes='Upstream pretraining corpus only; no downstream evaluation cohort membership is inferred.')
    c.collection_resource('evo1-original', ogr, oge, 'upstream-data',
        note='Pretraining corpus; listed for model provenance, not counted as an evaluation dataset.')
    c.field('models', 'evo1', 'pretraining_corpus', oge)

    # Main article methods support detailed protocol records even where a released
    # per-example table cannot be inspected. Limits identify those exact fields.
    members = [r['task_id'] for r in d['evaluation_tasks'] if r['evaluation_id'] == 'evo1-original']
    for tid in members:
        own = tid.startswith('evo1-')
        generation = own and any(word in tid for word in ['crispr', 'transposon', 'genome-'])
        eid = c.get('tasks', tid)['evidence_id'] if own else (
            'evo1-essentiality' if tid in ['evo-deg', 'evo-phage-essential'] else 'evo1-fitness')
        protocols = [r for r in d['protocols'] if r['task_id'] == tid and r['id'].startswith('evo1-')]
        for protocol in protocols:
            pid = protocol['id']
            c.review('protocols', pid,
                'Original Science 2024 model use, fitting, context, sampling/selection, partition unit and scored endpoint.',
                [eid, 'evo1-score-code-review', 'evo1-release-review', availability, zenodo],
                'Paper-audited protocol; generic public inference code is not a per-example assay manifest.')
            if not generation:
                c.limit('protocols', pid, 'retained-evaluation-rows', 'not-released',
                    'A source-study filtered sequence/label table or row-identity manifest for this Evo 1 protocol is absent from the inspected original Zenodo archive and pinned shared code repository. '
                    'Source-reported counts remain paper evidence, rather than independently recounted artifact counts.', zenodo)
            if tid.startswith(('evo-dms-', 'evo-ncrna-')):
                c.limit('protocols', pid, 'retained-example-count', 'access-restricted',
                    'The inspected main article names the assay panel and nucleotide filtering rules but does not state a retained row count for each study. '
                    'Supplementary tables could not be read because linked file retrieval returned a browser challenge; counts from another model protocol are not inherited.', supp)
            if tid == 'evo-deg':
                c.limit('protocols', pid, 'database-version-and-gene-manifest', 'not-reported',
                    'The main article reports 56 bacterial DEG studies and reference genome retrieval, without a DEG release version or full retained gene-identity manifest. '
                    'It does not establish pretraining exclusion of these genomes.', 'evo1-essentiality')
        if own:
            c.review('tasks', tid,
                'Dataset × target, prediction versus generation, genomic elements, output granularity, sequence origin/design context, fitting, counts, splits and readout.',
                [eid, availability, zenodo, gh, supp],
                'Paper-audited target and protocol. The original code archive does not provide the filtered assay table; Data S1 content was not retrieved.' if generation
                else 'Paper-audited target, count and study-level test partition; original filtered evaluation table is not included in inspected code releases.')
            c.task_resource(tid, gr, gh, 'evaluation-code', note='Generic inference/scoring interface; not an assay-specific reproduction script.')
            if generation:
                c.task_resource(tid, sr, availability,
                    note='Paper assigns generated validation sequences to Data S1; exact archive content not retrieved.')
                c.limit('tasks', tid, 'generated-sequences', 'access-restricted',
                    'The article assigns generated experimental sequences to Data S1; the exact linked ZIP returned a browser download challenge. '
                    'Generated sequences and their mapping to selected assays were not read from the archive.', supp)
                if tid == 'evo1-genome-folds':
                    c.limit('tasks', tid, 'retained-protein-count', 'not-reported',
                        'The main methods define 16 generated genomes and a 100–1024-amino-acid filter for Prodigal calls, but do not provide a total number of retained protein-fold predictions. '
                        'The 16-genome cohort count is not a protein count.', 'evo1-genome')

    # Preserve specific mathematical readouts behind broad generation endpoints.
    def append_once(row, field, text):
        if text not in (row.get(field) or ''):
            row[field] = (row.get(field) or '') + text

    for tid in ['evo1-genome-coding', 'evo1-genome-rna', 'evo1-genome-folds']:
        append_once(c.get('protocols', tid + '-generation'), 'notes',
            ' Sixteen genomes are four generations per species-specific prompt. The prompt describes a design target, rather than a natural-source assembly. '
            'Sampling uses temperature 1.0 and top-k 4; recurrent decoding extends beyond the 131,072-token training context.')
    append_once(c.get('protocols', 'evo1-genome-folds-generation'), 'model_interface',
        ' Prodigal-defined 100–1024-aa ORFs feed ESMFold; report mean backbone pLDDT and secondary-structure proportions. '
        'Foldseek structural matches require mean(query TM-score, target TM-score) > 0.4; matched UniRef50 GO terms are transferred annotations, not experimental protein-function labels.')
    append_once(c.get('protocols', 'evo1-transposon-activity-generation'), 'model_interface',
        ' Selected TnpA systems are tested with cognate DNA substrates; catalytic Y-to-A mutants and natural systems are controls. '
        'Nanopore reads are filtered for expected primer structure and mapped to substrate jump maps to inspect excision/insertion products.')

    collection_evidence = ['evo1-architecture', 'evo1-training', 'evo1-fitness', 'evo1-regulatory',
        'evo1-essentiality', 'evo1-crispr', 'evo1-transposon', 'evo1-genome',
        'evo1-score-code-review', 'evo1-release-review', availability, zenodo, gh, supp, oge] + hf_evidence
    c.review('evaluations', 'evo1-original',
        'All 36 original-paper dataset × target associations, including 24 reused targets with distinct Evo 1 protocols; downstream fitting, selected generation denominators and released-resource identities.',
        collection_evidence,
        'Source review complete. Exact retained assay-row manifests are absent from inspected code releases. Main paper methods are available; Supplement/Data S1 links are verified but file access returned a browser challenge. '
        'No later Evo 1.5 or phage-generation dataset is substituted for an original 2024 cohort.')
    c.review('papers', 'evo1',
        'Complete 21-page Science article and main methods, plus cover; bibliographic identity, architecture, corpus, original experiments, data availability and supplement index.',
        collection_evidence,
        'Supplementary text/tables and Data S1 contents were not retrieved; main article and primary release metadata are reviewed separately.')
    c.review('models', 'evo1',
        'Original model architecture/tokenization/training/context, specialist variants, current corrected weight revisions and inference-code version scope.',
        collection_evidence,
        'Current public weight metadata/configurations were inspected; large weight tensors were not downloaded and original published assay scores were not reproduced.')
    c.limit('papers', 'evo1', 'supplementary-files', 'access-restricted',
        'The exact PMC-linked Supplement.pdf and S1.zip requests returned browser download challenges. Europe PMC supplementaryFiles reports that this author manuscript is not open access. '
        'The complete main Science article is available from Arc; this access limit concerns supplementary files only.', supp)
    c.limit('models', 'evo1', 'paper-time-checkpoint-byte-identity', 'not-reported',
        'The paper names original checkpoint repositories but does not give immutable checkpoint commits. The current corrected 1.1_fix configurations are pinned separately and are not asserted byte-identical to experiment-time weights.',
        availability)
    return d
