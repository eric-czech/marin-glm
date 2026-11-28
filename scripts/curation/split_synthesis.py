"""Cited analysis of partition mechanisms, derived from the audited designs.

The designs remain available in SQLite and through task-specific links. They
are evidence for this synthesis, not the page's organizing interface.
"""


def populate(d):
    for table in ['split_synthesis_sections', 'split_synthesis_paragraphs', 'split_synthesis_evidence']:
        d[table] = []
    evidence = {e['id'] for e in d['evidence']}

    def section(key, title, paragraphs, kind='strategy'):
        d['split_synthesis_sections'].append(dict(
            id=key, title=title, kind=kind, sort_order=len(d['split_synthesis_sections'])))
        for i, (body, citations) in enumerate(paragraphs):
            pid = key + '-' + str(i + 1)
            d['split_synthesis_paragraphs'].append(dict(
                id=pid, section_id=key, body=body, sort_order=i))
            for eid in citations.split():
                assert eid in evidence, eid
                d['split_synthesis_evidence'].append(dict(paragraph_id=pid, evidence_id=eid))

    section('overview', '', [(
        'The useful distinction is what is kept together before assigning partitions: individual rows, nearby loci, related sequences, biological entities or experimental contexts. The mechanisms below recur in the audited collections; they are not a ranking from weak to strong. A split can combine several mechanisms, and the same benchmark can use different ones for different tasks.',
        'final-bgc-release final-mage-setting final-dart-methods'), (
        'First identify the fitting step. Evo 2’s species-held-out exon/intron probe tests a readout on new species, not exclusion of those genomes from pretraining. AlphaGenome 1 / 2’s chromosome-held-out QTL labels concern variant-effect selection; the final all-folds sequence model has seen reference DNA at those loci. A statement such as “chromosome held out” is incomplete without this distinction.',
        'evo2-review-exon s2f-ag1-shared-variant-methods s2f-ag2-eqtl-methods')], 'overview')

    section('random', 'Random rows, usually stratified by label', [(
        'Assign examples independently, optionally preserving label proportions. Genomic Benchmarks’ Cohn enhancer and non-TATA promoter notebooks use class-wise random approximately 75/25 train/test splits; its pinned OCR and regulatory helper uses 80/20. DNALongBench’s eQTL task uses label-stratified 80/10/10 gene–variant pairs. These estimate performance on more examples drawn from the represented mixture; they do not require new genes, species or sequence families.',
        'split-gb-human_enhancers_cohn split-gb-human_nontata_promoters split-gb-ensembl-helper final-dnalongbench-loaders-evidence'), (
        'The row definition matters more than the ratio. DNALongBench permits the same gene in multiple partitions. In GB’s human-versus-worm task, both species occur in training and test: species is the prediction label, not a held-out biological group.',
        'final-dnalongbench-loaders-evidence split-gb-demo_human_or_worm')])

    section('chromosomes', 'Whole chromosomes', [(
        'Assign every eligible locus on a chromosome to one partition. The revised 18-task Nucleotide Transformer benchmark reserves human chr20/21 for test. DART-Eval’s trained regulatory readouts reserve chr6/21 for validation and chr5/10/14/18/20/22 for test. TraitGym’s fitted feature models instead cycle through leave-one-chromosome-out evaluation. These separate genomic locations within represented species; repeats and homologous genes can still cross the boundary.',
        'split-nt-revised-native final-dart-methods split-traitgym-outer')])

    section('regions', 'Genomic blocks and full input windows', [(
        'Partition contiguous regions rather than entire chromosomes. NTv3’s human/mouse track tasks use Borzoi’s fold3 for test and fold4 for validation; other species use gene-aware 1-Mb windows and homology-based grouping. AlphaGenome 2 uses eight genomic folds, with six for training, one for validation and one for test. This permits regional holdouts while retaining training data from the same chromosomes.',
        'ntv3-final-native-protocol s2f-ag2-interval-targets'), (
        'The excluded span must be specified. AlphaGenome 2 expands 196,608-bp targets to 1,048,576-bp inputs and removes validation/test inputs that overlap training inputs. NTv3’s DeepFARM comparison explicitly distinguishes a held-out 200-bp scoring bin from a stricter whole-1-Mb-context holdout. Nonoverlapping targets alone do not establish nonoverlapping model inputs; the distinction grows with context length.',
        's2f-ag2-conditioning-ablation s2f-ag2-interval-targets ntv3-final-deepfarm')])

    section('entities', 'Genes, regulatory elements and parent clusters', [(
        'Keep all observations of one biological entity together. BEND 2.0’s OpenSplice readout holds out whole genes in five folds; its context tasks keep an element and related backgrounds together. BGC-Bench’s A-domain evaluation groups domains by parent biosynthetic gene cluster (BGC). This tests new genes, elements or clusters rather than new measurements of an entity already represented in training. Distinct entities may still contain homologous or identical sequences.',
        'final-bend2-fixed-ridge final-bgc-substrate-scorer')])

    section('similarity', 'Homology groups and sequence-similarity thresholds', [(
        'Group related entities using a homology map or an explicit similarity procedure. Original BEND gene finding uses GraphPart at 80% global mature-protein identity, whereas mRNABench groups mapped HomoloGene families. LAMBDA groups phage genomes at 95% average nucleotide identity before sampling fragments. These operate on different objects: translated proteins, mapped gene families and whole genomes. None directly guarantees uniqueness of complete genomic input windows.',
        'bend1-gene-method split-mrna-unmapped-code final-lambda-evo-interfaces-evidence'), (
        'A threshold, a heuristic and a fallback are different guarantees. RNAGym’s min_similarity routine starts from a random 80/20 split and swaps examples for at most 10,000 iterations; it does not enforce a strict maximum similarity. The inspected Pitt split retains six shared validation strings. mRNABench assigns unmapped rows independently, so disjoint mapped families can coexist with shared genes and DNA. Construction code is essential here.',
        'rnagym-split-audit split-evidence-da86f10ed88ccfc9 split-mrna-unmapped-code')])

    section('taxa', 'Species, genera and larger clades', [(
        'Assign complete taxa, not their individual sequence rows. Evo 2’s exon/intron probe holds out species; native BacBench essentiality separates 55 genomes into 37/9/9 with disjoint genera. NTv3 gene annotation excludes test genera from supervised training and validation, although validation species may share genera with training. The rank and the validation rule change the transfer being measured; “multispecies evaluation” alone establishes neither.',
        'evo2-review-exon final-bacbench-essential-native-test final-bacbench-essential-scorer ntv3-final-annotation'), (
        'Pretraining exclusion is a separate claim. PlantCAD2’s potato conservation endpoint reports exclusion of the Solanaceae family from pretraining. That differs from holding species out only while fitting a task head, and it still does not imply absence of conserved sequences shared with other plant families.',
        'plantcad2-potato')])

    section('positions', 'Mutation positions within a sequence', [(
        'Keep alternative alleles at a position together, or hold out contiguous blocks of mutation positions. Evo 2’s fitted BRCA1 readout uses 1,060 training and 266 test positions, with position-grouped cross-validation inside training. NABench describes five contiguous position blocks. These test mutations at new positions in a represented sequence background, not unseen genes or assays. NABench’s released assay CSVs do not resolve fold assignment for multimutants spanning blocks.',
        'evo2-review-brca-probe nabench-complete-methods')])

    section('individuals', 'Individuals, optionally crossed with genes', [(
        'Keep a person’s observations together. DNA Foundation Benchmark’s personal-expression task uses a 75/25 subject split while retaining the same genes across partitions. MAGE evaluates held-out people and a stricter setting that also holds out gene regions, grouping overlapping 8-kb windows. The first asks about new individuals at represented genes; the second additionally asks about new regions. Donor and locus separation are independent axes, not interchangeable safeguards.',
        'dnafoundation-personal-expression-code final-mage-setting')])

    section('experiments', 'Assays, conditions and study cohorts', [(
        'Withhold an experimental context rather than necessarily withholding DNA. AlphaGenome 2 masks 184 test tracks across 30 human conditions and 26 validation tracks across 12 conditions; 32 conditions occur across those sets, so track exclusion is not complete condition exclusion in every case. NABench’s cross-assay setting fits source assays and evaluates another assay. These assess transfer of measured functions or conditions, with sequence-family exclusion requiring a separate rule.',
        's2f-ag2-imputation nabench-complete-methods'), (
        'A study can also be the grouping unit. Genos-m distinguishes within-cohort tenfold cross-validation from train-one/test-another evaluation across 14 colorectal-cancer cohorts. This tests transfer across study distributions. The paper does not establish participant disjointness or repeated-sample handling across cohorts, so a study holdout should not be described as an audited donor holdout.',
        'genosm-crc')])

    section('time', 'Release dates and prospective datasets', [(
        'Choose a cutoff before evaluating newly released measurements. AlphaGenome 2 excludes 16 single-cell datasets released after 1 October 2025 from encoder/post-training; that evaluation separately uses fold1 validation genomic intervals. Temporal separation addresses access to future measurements, while genomic folds address locations. A new dataset can still measure previously represented genes, loci or participants.',
        's2f-ag2-cellxgene-expression')])

    section('chemistry', 'Chemical scaffolds and biosynthetic families', [(
        'Group by the product or biosynthetic family when that is the intended unit of transfer. BGC-Bench provides first-product Bemis–Murcko scaffold and BiG-SCAPE gene-cluster-family (GCF; c=0.7) holdouts alongside random splits; its retrieval task also holds out biosynthetic classes. A new product scaffold, new GCF and new parent BGC are different claims. Chemical grouping does not establish DNA-similarity exclusion, and parent-BGC folds can share GCFs without violating their stated rule.',
        'final-bgc-release final-bgc-substrate-scorer')])

    section('interpretation', 'What follows from these comparisons', [(
        'Separate location, identity and provenance. PlantCAD2’s maize test chromosome is disjoint from training loci, yet 18 distinct test strings recur in training. Original BEND’s protein-identity grouping still leaves 109 of 597 test windows overlapping training spans. These are intersections on axes different from the construction rule; they are not, by themselves, measurements of score inflation. The contamination figures above quantify the inspected releases.',
        'split-evidence-face9b470c556621 split-evidence-a295180f3dd84b7c'), (
        'Model selection needs its own separation. TraitGym performs chromosome-grouped tuning inside each outer training set. By contrast, SpliceAI2’s 352-gene human-only transcript reconstruction uses chr21/22 for both validation and evaluation, rather than a third independent test. The revised NT benchmark’s ten runs reuse the same test cohort. Report the biological holdout, selection cohort and repeated-run uncertainty separately.',
        'split-traitgym-inner spliceai2-top-transcript-method split-nt-revised-native'), (
        'Do not count evaluation arrangements as additional split strategies. A fixed zero-shot assay, a withheld suffix in a generation prompt or chromosome-weighted reporting does not itself construct independent train/test groups. Nor does an HF partition name specify how membership was chosen. The most informative report names the assignment unit, exclusion criterion, full input span, fitting step and selection rule; the cited examples show why each changes the interpretation.',
        'traitgym-definition evo2-review-brca-probe evo2-review-evo-gen-completion-generation final-dart-methods')], 'interpretation')
