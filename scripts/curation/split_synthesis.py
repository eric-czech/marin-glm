"""Cited partition-construction summaries and shorter supporting explanations."""
from common import Catalogue


def populate(d):
    c = Catalogue(d)
    for table in ['split_synthesis_sections', 'split_synthesis_paragraphs',
                  'split_synthesis_evidence', 'split_synthesis_summary_evidence']:
        d[table] = []
    source_id = 'split-borzoi-paper'
    c.source(source_id, 'Predicting RNA-seq coverage from DNA sequence as a unifying model of gene regulation',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC11985352/', version='Nature Genetics (2025)',
             notes='Full article XML inspected through the Europe PMC API; no sequence data downloaded.')
    c.get('sources', source_id)['retrieved'] = '2026-11-28'
    c.evidence('split-borzoi-construction', source_id, 'Methods: Data; Training',
        'Human hg38 and mouse mm10 chromosomes are fragmented; orthologous regions are paired into the same partition. Fragment groups are randomly assigned to eight approximately equal partitions. One supplies validation, another test, and six training. All assay targets for a held-out sequence are withheld. Four released replicates share the same partition assignment.')
    c.get('evidence', 'split-borzoi-construction')['inspected'] = '2026-11-28'
    source_id = 'split-borzoi-construction-code'
    c.source(source_id, 'Borzoi paper data-construction recipe',
        'https://github.com/calico/borzoi-paper/blob/ace52175bba712872daaada4ed9e4f1cafb28049/data/training/Makefile#L20-L37', 'code',
        version='ace52175bba712872daaada4ed9e4f1cafb28049')
    c.get('sources', source_id)['retrieved'] = '2026-11-28'
    c.evidence('split-borzoi-construction-code', source_id, 'Makefile lines 20–37',
        'Construction passes the human–mouse syntenic alignment net and assembly gap files to hound_data_align.py, with --break 2097152, eight folds, 524288-bp inputs and 163840-bp crops. The break argument caps initial chromosome fragments; it is not a claim that each final partition is one contiguous 2-Mb block.', 'code')
    c.get('evidence', 'split-borzoi-construction-code')['inspected'] = '2026-11-28'
    c.evidence('split-ag2-region-construction', 'alphagenome2-paper', 'Methods: Data processing, Genomic interval split',
        'Predefined 196608-bp genomic target intervals are assigned to eight regional groups. A training configuration uses six for training, one for validation and one for test. Expand targets to 1048576-bp input windows and remove validation/test windows overlapping training inputs. These are grouped genomic regions rather than an independently randomized split of every extracted example.')
    c.get('evidence', 'split-ag2-region-construction')['inspected'] = '2026-11-28'
    c.source('split-ag1-fold-roles', 'AlphaGenome genomic partition lookup',
        'https://github.com/google-deepmind/alphagenome/blob/67d9080d70283173f6060a1d9850942736350547/src/alphagenome/data/fold_intervals.py#L40-L58', 'code',
        version='67d9080d70283173f6060a1d9850942736350547')
    c.get('sources', 'split-ag1-fold-roles')['retrieved'] = '2026-11-28'
    c.evidence('split-ag1-fold-roles', 'split-ag1-fold-roles', 'Validation/test lookup dictionaries; model-version mapping',
        'AlphaGenome model configuration FOLD_1 validates on Borzoi regional group fold3 and tests on group fold4; its other six regional groups supply training. The model-configuration index and the underlying Borzoi region-group index are different identifiers.', 'code')
    c.get('evidence', 'split-ag1-fold-roles')['inspected'] = '2026-11-28'
    evidence = {e['id'] for e in d['evidence']}

    def section(key, title, paragraphs, kind='strategy', summary=None):
        row = dict(id=key, title=title, kind=kind, sort_order=len(d['split_synthesis_sections']))
        if summary:
            unit, rule, examples, limitation, sources = summary
            row.update(assignment_unit=unit, construction_rule=rule, examples=examples, limitation=limitation)
            for eid in sources.split():
                assert eid in evidence, eid
                d['split_synthesis_summary_evidence'].append(dict(section_id=key, evidence_id=eid))
        d['split_synthesis_sections'].append(row)
        for i, (body, citations) in enumerate(paragraphs):
            pid = key + '-' + str(i + 1)
            d['split_synthesis_paragraphs'].append(dict(id=pid, section_id=key, body=body, sort_order=i))
            for eid in citations.split():
                assert eid in evidence, eid
                d['split_synthesis_evidence'].append(dict(paragraph_id=pid, evidence_id=eid))

    section('overview', '', [(
        'Splits apply separately to pretraining, supervised training and model selection. Evo 2’s species-held-out exon/intron probe excludes those species from readout fitting. AlphaGenome’s chromosome-held-out QTL labels exclude those labels from scorer selection; its final sequence model is trained across all genomic partitions. Neither rule establishes exclusion of the corresponding reference DNA from pretraining.',
        'evo2-review-exon s2f-ag1-shared-variant-methods s2f-ag2-eqtl-methods')], 'overview')

    section('random', 'Random examples', [(
        'Shuffle examples, then allocate fixed proportions to each set. Stratification preserves label proportions. Genomic Benchmarks’ Cohn enhancer and non-TATA promoter notebooks split each class approximately 75/25; its open-chromatin and regulatory helper uses 80/20. DNALongBench splits eQTL gene–variant pairs 80/10/10, stratified by label. Genes can recur across sets. GB’s human-versus-worm task includes both species in both sets.',
        'split-gb-human_enhancers_cohn split-gb-human_nontata_promoters split-gb-ensembl-helper final-dnalongbench-loaders-evidence split-gb-demo_human_or_worm')], summary=(
        'Sequence row or gene–variant pair', 'Random assignment within label classes: GB examples use 75/25; DNALongBench eQTL pairs use 80/10/10.',
        'Genomic Benchmarks; DNALongBench eQTL', 'Repeated genes, loci or similar sequences can cross sets.',
        'split-gb-human_enhancers_cohn final-dnalongbench-loaders-evidence'))

    section('chromosomes', 'Whole chromosomes', [(
        'Assign all eligible loci on a chromosome together. The revised 18-task Nucleotide Transformer benchmark tests on human chr20/21. DART’s trained regulatory readouts validate on chr6/21 and test on chr5/10/14/18/20/22. TraitGym fits on all but one chromosome and predicts the omitted chromosome, repeating for each chromosome. Repeats and homologous genes on different chromosomes remain possible.',
        'split-nt-revised-native final-dart-methods split-traitgym-outer')], summary=(
        'Chromosome', 'Reserve named chromosomes, or rotate the omitted chromosome.',
        'Revised NT; DART trained readouts; TraitGym fitted models', 'Separates loci; does not remove cross-chromosome homology.',
        'split-nt-revised-native final-dart-methods split-traitgym-outer'))

    section('regions', 'Genomic regions and full input windows', [(
        'Borzoi fragments human and mouse chromosomes, groups orthologous fragments together, and randomly assigns those groups to eight roughly equal partitions. Each partition contains multiple regions from both genomes. Six partitions supply training, one validation and one test. The published construction recipe caps initial fragments at 2,097,152 bp before grouping. NTv3 reuses the human/mouse region assignments, merges neighboring intervals with the same membership, and extracts new input windows. The labels fold3 and fold4 identify its test and validation groups; they do not describe the construction rule.',
        'split-borzoi-construction split-borzoi-construction-code ntv3-final-native-protocol'), (
        'For other species, NTv3 starts with 1-Mb windows and extends boundaries to include complete genes. It links windows containing homologous genes, clusters the resulting graph, and assigns whole clusters to training, validation or test. Weak homology links are removed in Arabidopsis, worm and rice when needed to reach the target partition sizes.',
        'ntv3-final-native-protocol'), (
        'AlphaGenome 2 also uses eight groups of genomic regions, with six for training, one for validation and one for test. It expands each 196,608-bp target to a 1,048,576-bp input, then removes validation/test inputs that overlap training inputs. This checks the entire visible sequence. NTv3’s DeepFARM comparison separately reports exclusion of only the 200-bp scored bin and exclusion of the full 1-Mb input; those cohorts provide different guarantees.',
        'split-ag2-region-construction ntv3-final-deepfarm')], summary=(
        'Contiguous region; optionally linked regions in different genomes',
        'Borzoi: randomly assign ortholog-linked chromosome fragments to eight balanced groups. AlphaGenome 2 also excludes overlapping full 1-Mb inputs.',
        'Borzoi / NTv3; AlphaGenome 2', 'A held-out target can still have input flanks in training unless full windows are excluded.',
        'split-borzoi-construction ntv3-final-native-protocol split-ag2-region-construction'))

    section('entities', 'Genes, elements and parent clusters', [(
        'Assign every observation from the same gene, regulatory element or parent biosynthetic gene cluster (BGC) together. BEND 2.0 divides OpenSplice genes into five groups, fitting on four and evaluating the fifth in turn. Its context tasks keep an element and related backgrounds together. BGC-Bench similarly groups A-domains by their parent BGC. Homologous genes or domains in different groups may remain.',
        'final-bend2-fixed-ridge final-bgc-substrate-scorer')], summary=(
        'Gene, regulatory element or parent BGC', 'Assign all variants or measurements of an entity together.',
        'BEND 2.0 OpenSplice/context tasks; BGC-Bench A-domains', 'Distinct entities may contain homologous or identical sequence.',
        'final-bend2-fixed-ridge final-bgc-substrate-scorer'))

    section('similarity', 'Homology and sequence similarity', [(
        'Original BEND gene finding partitions examples using an 80% global identity threshold on translated mature proteins. mRNABench keeps genes with the same supplied HomoloGene family assignment together. LAMBDA groups phage genomes at 95% average nucleotide identity before sampling fragments. Protein identity, mapped gene families and whole-genome identity constrain different sequences.',
        'bend1-gene-method split-mrna-unmapped-code final-lambda-evo-interfaces-evidence'), (
        'RNAGym’s min_similarity procedure instead swaps examples from a random 80/20 split for at most 10,000 iterations to reduce high-similarity pairs. It does not enforce a strict threshold; six distinct Pitt validation strings still occur in training. mRNABench assigns unmapped rows independently, allowing repeated genes despite disjoint mapped families.',
        'rnagym-split-audit split-evidence-da86f10ed88ccfc9 split-mrna-unmapped-code')], summary=(
        'Homology family or sequence cluster', 'BEND: 80% global protein identity. LAMBDA phages: 95% average nucleotide identity. mRNABench: mapped families. RNAGym: similarity-reducing swaps.',
        'BEND gene finding; mRNABench; LAMBDA; RNAGym', 'Specify similarity object, threshold, algorithm and handling of unmapped rows.',
        'bend1-gene-method split-mrna-unmapped-code final-lambda-evo-interfaces-evidence rnagym-split-audit'))

    section('taxa', 'Species, genera and larger clades', [(
        'Assign all examples from each taxon together. Evo 2’s exon/intron probe holds out species. Native BacBench essentiality assigns 55 genomes to 37 training, 9 validation and 9 test genomes with disjoint genera. NTv3 annotation excludes test genera from supervised training and validation, although validation species may share genera with training. PlantCAD2’s potato experiment reports a different exclusion: the Solanaceae family is absent from pretraining.',
        'evo2-review-exon final-bacbench-essential-native-test final-bacbench-essential-scorer ntv3-final-annotation plantcad2-potato')], summary=(
        'Species, genus or larger clade', 'Assign complete taxa together: species for Evo 2 probes; genera for BacBench and NTv3 annotation; pretraining-family exclusion for PlantCAD2 potato.',
        'Evo 2 exon/intron; BacBench essentiality; NTv3 annotation; PlantCAD2 potato', 'Taxonomic separation does not exclude conserved sequence or imply pretraining exclusion.',
        'evo2-review-exon final-bacbench-essential-scorer ntv3-final-annotation plantcad2-potato'))

    section('positions', 'Mutation positions', [(
        'Keep alternative alleles at a position together. Evo 2’s BRCA1 readout assigns 1,060 positions to training and 266 to test; tuning also groups by position within training. NABench divides the wild-type sequence into five contiguous position blocks and holds out one block at a time. Its released assay CSVs do not specify how multimutants spanning blocks are assigned. These evaluations retain the same gene or sequence background.',
        'evo2-review-brca-probe nabench-complete-methods')], summary=(
        'Mutation position or contiguous position block', 'Keep alleles at one position together; optionally hold out adjacent positions as a block.',
        'Evo 2 BRCA1 readout; NABench', 'Tests new positions within a represented sequence; multimutants need an explicit assignment rule.',
        'evo2-review-brca-probe nabench-complete-methods'))

    section('individuals', 'Individuals and gene regions', [(
        'Assign all observations of a person together. DNA Foundation Benchmark’s personal-expression task uses a 75/25 subject split with shared genes. MAGE holds out people and also reports a stricter setting that excludes gene regions, grouping overlapping 8-kb windows. Person-level separation alone tests new people at represented genes; gene-region separation additionally tests new loci.',
        'dnafoundation-personal-expression-code final-mage-setting')], summary=(
        'Person; optionally person × gene region', 'Group by person (DNA Foundation: 75/25); MAGE additionally reports gene-region exclusion.',
        'DNA Foundation personal expression; MAGE', 'The same genes can remain represented when only people are held out.',
        'dnafoundation-personal-expression-code final-mage-setting'))

    section('experiments', 'Assays, conditions and studies', [(
        'Remove selected assay labels or whole studies from fitting. AlphaGenome 2 withholds 184 test tracks across 30 human conditions and 26 validation tracks across 12 conditions; the sets share some conditions. NABench fits source assays and evaluates another assay. Genos-m separately reports within-study cross-validation and training on one of 14 colorectal-cancer cohorts while testing on another. Study separation does not establish participant disjointness when repeated-sample handling is unspecified.',
        's2f-ag2-imputation nabench-complete-methods genosm-crc')], summary=(
        'Assay track, condition or study', 'Withhold designated labels/conditions, or train on complete source studies and test another.',
        'AlphaGenome 2 track imputation; NABench assay transfer; Genos-m cohorts', 'New labels or studies can reuse reference DNA and participants.',
        's2f-ag2-imputation nabench-complete-methods genosm-crc'))

    section('time', 'Publication dates', [(
        'Separate datasets by publication date. AlphaGenome 2 excludes 16 single-cell datasets published after 1 October 2025 from cell-encoder training and subsequent expression-conditioning training. Its expression comparison also scores genomic regions excluded from sequence-model training: the validation group in the eight-part regional split described above. The paper states that these regions were not used for fine-tuning or model selection in this comparison. New measurements can still concern previously represented genes or participants.',
        's2f-ag2-cellxgene-expression split-ag2-region-construction')], summary=(
        'Dataset publication date', 'AlphaGenome 2 excludes 16 studies published after 1 October 2025 from cell-encoder and expression-conditioning training.',
        'AlphaGenome 2 single-cell expression', 'Combine with locus/participant exclusions when those are required; dates alone do not provide them.',
        's2f-ag2-cellxgene-expression'))

    section('chemistry', 'Product scaffolds and biosynthetic families', [(
        'BGC-Bench groups clusters by their first product’s ring-and-linker scaffold (Bemis–Murcko), or by supplied BiG-SCAPE gene-cluster-family assignments based on biosynthetic similarity. Each split reserves 20% of those groups for test; ring-free products form one scaffold group. Its retrieval task also holds out each biosynthetic class in turn. Parent-BGC, family and product-scaffold grouping constrain different relationships and can yield different cross-set intersections.',
        'final-bgc-release final-bgc-substrate-scorer')], summary=(
        'Product scaffold, BGC family or biosynthetic class', 'Reserve 20% of first-product scaffold groups or BGC families for test; retrieval also omits whole biosynthetic classes.',
        'BGC-Bench', 'Chemical scaffold separation is not DNA-identity separation; families can cross scaffold splits.',
        'final-bgc-release'))

    section('interpretation', 'Overlap and model selection', [(
        'PlantCAD2 has disjoint training/test chromosomes but 18 distinct shared DNA strings. BEND’s protein-based grouping leaves 109 of 597 test input windows overlapping training spans. Neither construction rule promises the other form of independence. These measured intersections do not quantify their effect on prediction scores.',
        'split-evidence-face9b470c556621 split-evidence-a295180f3dd84b7c'), (
        'Tuning must respect the evaluation boundary. TraitGym selects regularization using chromosome groups inside each outer training set. SpliceAI2’s human-only 352-gene reconstruction instead uses chr21/22 for both validation and evaluation. Revised NT repeats fitting ten times against the same test cohort; those runs do not create ten independent biological test sets.',
        'split-traitgym-inner spliceai2-top-transcript-method split-nt-revised-native'), (
        'Fixed zero-shot assays need not have a downstream training split. A withheld generation suffix, a chromosome-weighted metric or a dataset partition named train does not establish exclusion from model training.',
        'traitgym-definition evo2-review-brca-probe evo2-review-evo-gen-completion-generation')], 'interpretation')

    # Keep the task-linked source details as explicit as the page synthesis.
    borzoi = ('Human/mouse chromosomes are fragmented; orthologous fragments are grouped and '
              'randomly assigned together to eight roughly equal regional partitions.')
    regional = ('Genomic intervals are assigned to eight regional groups: six training, one validation '
                'and one test. Validation/test 1-Mb inputs overlapping training inputs are removed.')
    rules = {
        'design-ntv3-tracks': (borzoi + ' NTv3 uses regional group 3 for test and 4 for validation. '
            'Other species use gene-complete 1-Mb windows grouped by a homology graph before assignment.',
            'split-borzoi-construction ntv3-final-native-protocol', borzoi),
        'design-aido': (borzoi + ' AIDO.DNA2 trains on groups 0–2 and 5–7, validates on group 4 and tests on group 3.',
            'split-borzoi-construction aido2-coverage', borzoi),
        'design-ntv3-ag': (borzoi + ' Five assay-specific NTv3 fine-tunes score regional group 4, '
            'which is NTv3’s native validation group and AlphaGenome configuration 1’s test group.',
            'split-borzoi-construction split-ag1-fold-roles ntv3-final-alphagenome', borzoi),
        'design-ag2-sequence': (regional + ' Targets are the central 196,608 bp of each 1,048,576-bp input.',
            'split-ag2-region-construction', regional),
        'design-ag2-time': ('Exclude 16 studies published after 1 October 2025 from cell-encoder and '
            'expression-conditioning training. Genomic regions are independently assigned to eight groups '
            '(six training, one validation, one test); this expression comparison scores the validation group, '
            'which is excluded from fine-tuning and model selection in the comparison.',
            'split-ag2-region-construction s2f-ag2-cellxgene-expression', regional),
    }
    for did, (rule, refs, explanation) in rules.items():
        c.get('split_designs', did)['partition_rule'] = rule
        for eid in refs.split():
            c.put('split_design_evidence', dict(design_id=did, field='partition_rule', evidence_id=eid),
                  ('design_id', 'field', 'evidence_id'))
        for link in d['split_design_protocols']:
            if link['design_id'] != did:continue
            p = c.get('protocols', link['protocol_id'])
            # Exact protocol text is retained; this adds the construction behind
            # the release-specific labels. Guard against repeated authoring runs.
            if explanation not in p['split_rule']:
                p['split_rule'] += ' ' + explanation
            for eid in refs.split():c.field('protocols', p['id'], 'split_rule', eid)
