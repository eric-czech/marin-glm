"""Column definitions and targeted corrections from the independent reading review."""
import json


def populate(d):
    definitions = {
        'gene-structures': 'Recover a gene’s connected exon–intron structure and score the structure as a whole. Requirements for coding boundaries, reading frame and untranslated regions vary by task.',
        'coding-sequence': 'Tasks restricted to protein-coding DNA: coding-region classification, variant effects, coding function or sequence generation. Outlined symbols are protein-input reference tasks.',
        'gene-elements': 'Identify or classify gene components, such as exons and introns. These tasks score individual regions, intervals or base labels rather than a connected gene structure.',
        'utrs': 'Tasks on 5′ or 3′ untranslated regions (UTRs): the parts of a transcript before or after its protein-coding sequence.',
        'translation-boundaries': 'Locate or evaluate the start and stop codons of protein translation. These differ from the positions where a transcript starts and ends.',
        'transcript-structures': 'Recover which splice junctions connect into a transcript. Tasks may score the splice pattern without testing transcript ends or recovery of every isoform.',
        'splice-elements': 'Predict splice donor or acceptor sites, or individual junctions between exons. Connecting them into a transcript is evaluated under Splice isoforms.',
        'regulatory-elements': 'Tasks on promoters, enhancers, transcription-factor binding sites and other sequences that regulate gene expression. Outputs include activity scores, labels, measurements along a sequence and designed sequences.',
        'chromatin-organization': 'Classify or design sequences at boundaries between chromatin domains, including topologically associating domains (TADs).',
        'rna-features': 'Tasks on mature or reporter mRNA, noncoding RNA and functional RNA sequences. Reconstructing transcripts from genomic DNA is shown under Splice isoforms.',
        'clusters-operons': 'Tasks on biosynthetic gene clusters or operons: groups of genes involved in a biosynthetic pathway or transcribed together. Some tasks use supplied regions or gene pairs.',
        'crispr-arrays': 'Tasks on CRISPR repeat–spacer arrays or their components, including sequence generation and analysis of model scores.',
        'repetitive': 'Tasks on repetitive DNA or transposable elements (TEs), which can move or copy themselves within a genome.',
        'intergenic-context': 'Tasks on DNA between genes, including region classification and analysis of model scores.',
        'broad-context': 'Whole-genome, mixed-region or other tasks that do not isolate a specific genomic feature. Presence here does not establish coverage of each feature.',
    }
    setting = next(r for r in d['coverage_settings'] if r['key'] == 'groupedFeatures')
    features = json.loads(setting['value_json'])
    assert {r['id'] for r in features} == definitions.keys()
    for row in features:
        row['definition'] = definitions[row['id']]
    setting['value_json'] = json.dumps(features, ensure_ascii=False)

    findings = {r['id']: r for r in d['findings']}
    findings['final-bacbench-operon-negative']['description'] = (
        'OperonDB negative candidates are contiguous gene windows from the same contig. '
        'The code does not explicitly exclude known operons from these candidates. '
        'The task therefore measures ranking within each candidate set, not classification '
        'of independently validated positive and negative gene pairs.'
    )
    findings['finding-037']['description'] = (
        'PlantCAD2 Methods report 36,668 translation-initiation sites (26,653/10,015), '
        'while Table 1 and the Hugging Face card report 36,662 (26,650/10,012). '
        'Non-initiation sites also differ: 183,687 in Methods versus 183,685 in the card. '
        'Reported counts and counts measured from released files are retained separately.'
    )
    findings['finding-039']['description'] = findings['finding-039']['description'].replace('PaperTable', 'Paper Table')
    for table in ['findings', 'tasks', 'evidence']:
        for row in d[table]:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = value.replace('all287', 'all 287').replace('All287', 'All 287')
    # These records previously confused an accessible abstract/release with
    # retrieval of the full paper. Their existing notes document the distinction.
    for paper in d['papers']:
        if paper['id'] in {'cerberus', 'opensplice', 'gfmbench'}:
            source = next(r for r in d['sources'] if r['id'] == paper['source_id'])
            source['availability'] = 'not-retrieved'
            if not source['notes']:
                source['notes'] = paper['notes']
