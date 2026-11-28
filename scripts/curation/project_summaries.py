"""Cited project comparisons and short descriptions of established external use."""
from common import Catalogue


def populate(d):
    c = Catalogue(d)
    d['project_summaries'] = []
    d['field_evidence'] = [r for r in d['field_evidence'] if r['entity_table'] != 'project_summaries']

    def row(id, coverage, procedures, coverage_refs, procedure_refs):
        c.put('project_summaries', dict(id=id, coverage=coverage, procedures=procedures))
        for field, refs in [('coverage', coverage_refs), ('procedures', procedure_refs)]:
            for ref in refs.split():
                c.get('evidence', ref)
                c.field('project_summaries', id, field, ref)

    row('gb',
        'Regulatory-sequence classification in human, mouse and fruit fly; transcript versus intergenic DNA; human versus worm sequence origin. Includes demonstration datasets.',
        'Binary and multiclass classification. Model papers supply their own probes or fine-tuning; dataset construction and negative examples differ.',
        'gb-definition gb-human_enhancers_cohn gb-drosophila_enhancers_stark',
        'gb-definition')
    row('dart',
        'Human regulatory elements, transcription-factor motifs, cell-type specificity, accessibility and regulatory variant effects.',
        'Likelihood and embedding comparisons, trained heads on frozen embeddings, and LoRA fine-tuning. Trained evaluations hold out chromosomes.',
        'dart-definition', 'final-dart-methods')
    row('traitgym',
        'Human noncoding variants: Mendelian regulatory disease and fine-mapped complex traits, evaluated against matched controls.',
        'Zero-shot scores and fitted combinations of model scores/features. Chromosome-grouped fitting; weighted precision–recall metrics.',
        'traitgym-definition traitgym-mendelian-data traitgym-complex-data',
        'traitgym-definition traitgym-mendelian-model traitgym-complex-model')
    row('bend',
        'Original BEND: seven human gene-annotation, chromatin, methylation and variant tasks. BEND 2.0 adds sequence recovery, mutation effects and candidate selection.',
        'Original: frozen embeddings with trained heads, or embedding distances for variants. BEND 2.0: zero-shot scores and fixed ridge readouts; group-based validation.',
        'project-bend-intent bend1-gene-method',
        'bend1-gene-method bend1-variant-readout final-bend2-fixed-ridge')
    row('lrb',
        'Human expression, transcription-initiation profiles, chromatin labels, regulatory regions and variant effects. Nine released targets; three benchmarked in the workshop paper.',
        'Configurable input length. Workshop experiments train multilayer perceptrons on frozen embeddings; model-selection and test regions differ by task.',
        'project-lrb-intent final-lrb-loader-evidence', 'final-lrb-workshop-protocol')
    row('dnalongbench',
        'Enhancer–gene and variant–gene links, chromatin contact maps, regulatory measurements along DNA, and transcription-initiation profiles; human and mouse targets.',
        'Long-input supervised prediction with task-specific heads. Published baselines fine-tune model weights; independent uses also fit linear probes.',
        'final-dnalongbench-tasks final-dnalongbench-loaders-evidence',
        'final-dnalongbench-tasks')
    row('rna',
        'RNA and coding-sequence variant fitness. The paper also introduces RNA structure benchmarks; this catalogue indexes the 70-assay fitness release.',
        'Model scores ranked against measured fitness. Supervised releases provide random and similarity-reducing splits; the latter does not guarantee disjoint sequences.',
        'rnagym-definition', 'rnagym-scorer-audit rnagym-split-audit')
    row('mrna',
        'Mature/reporter mRNA and untranslated regions: binding, function, localization, stability, translation and variant effects.',
        'Frozen embeddings with ridge or logistic-regression probes. Dataset-specific targets and split configurations are retained separately.',
        'mrna-catalog', 'final-mrna-probe-semantics')
    row('dgeb',
        'DNA/protein embeddings: enzyme and gene-cluster function, clustering, gene relationships, phylogenetic distances and retrieval across multiple taxa.',
        'Frozen embeddings with logistic/nearest-neighbor classifiers, clustering, distance correlations and retrieval. DNA and protein tasks are separate.',
        'dgeb-definition', 'final-dgeb-scorers')
    row('bacbench',
        'Bacterial gene essentiality, operons, protein interactions, antibiotic resistance and organism phenotypes. Input modality varies by task.',
        'Embedding-based probes/classifiers and zero-shot comparisons. Essentiality and phenotype protocols group genomes by genus; other tasks use different splits.',
        'project-bacbench-intent',
        'final-bacbench-essential-scorer final-bacbench-phenotype-scorer final-bacbench-essential-native-train')

    summaries = {
        'adoption-gb-chunker': 'DNAChunker: sequence classification.',
        'adoption-gb-generator': 'GENERator: sequence classification.',
        'adoption-dart-patch': 'PatchDNA: tasks 1–5, with zero-shot and frozen-embedding protocols.',
        'adoption-dart-evo': 'Evo 2: tasks 1, 2 and 5; task 5 uses accessibility-variant endpoints.',
        'adoption-trait-carbon': 'Carbon: Mendelian regulatory variants.',
        'adoption-trait-ceno': 'CENO: Mendelian and complex-trait variants.',
        'adoption-trait-gpn': 'GPN-Star: related-author follow-up; excluded from the independent-group count.',
        'adoption-bend-chunker': 'DNAChunker: original BEND’s seven tasks.',
        'adoption-bend-patch': 'PatchDNA: original BEND annotation, chromatin and variant tasks. No BEND 2.0 adoption asserted.',
        'adoption-lrb-patch': 'PatchDNA: transcription-initiation (CAGE) subset.',
        'adoption-lrb-factory': 'Genome-Factory: aggregate benchmark result; individual task cohorts are not identified.',
        'adoption-dnalong-chunker': 'DNAChunker: five task families using linear probes.',
        'adoption-dnalong-genezip': 'GeneZip: four task families; excludes regulatory activity.',
        'adoption-rna-ribospan': 'RiboSpan: RNA fitness, without documented use of the structure tasks.',
        'adoption-rna-genosm': 'Genos-m: 13 prokaryote-related fitness assays.',
        'adoption-mrna-ribospan': 'RiboSpan: six mature-transcript task families.',
        'adoption-mrna-mimic': 'MIMIC: probe experiments; some inputs also use protein/codon information.',
        'adoption-dgeb-loam': 'LOAM: DNA enzyme classification only.',
        'adoption-dgeb-protberta': 'ProtBERTa: protein-only evaluation.',
        'adoption-bacbench-loam': 'LOAM: essentiality with frozen probes.',
        'adoption-bacbench-genosm': 'Genos-m: essentiality and phenotypes; cohorts differ from LOAM.',
        'adoption-guanine-factory': 'Genome-Factory: GUANinE v1.0 aggregate; metric reconciliation remains a source discrepancy.',
    }
    assert {r['id'] for r in d['project_adoptions']} == summaries.keys()
    for adoption in d['project_adoptions']:
        adoption['summary'] = summaries[adoption['id']]
    # Coverage/procedure summaries can cite multiple existing task and protocol
    # definitions. External-use evidence belongs to the original adoption rows.
    for id, refs in {
        'bend': 'final-bend2-prior-scoring final-bend2-fixed-ridge',
        'dnalongbench': 'project-chunker-dnalong',
    }.items():
        for ref in refs.split():
            c.get('evidence', ref)
            c.field('project_summaries', id, 'coverage' if id == 'bend' else 'procedures', ref)
