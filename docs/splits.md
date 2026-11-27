# Splits: methods and interpretation

[Interactive section](https://eric-czech.github.io/marin-glm/#view=splits)

Splitting rules define a separation axis. Measurements test particular properties of the released partitions. An observed intersection is not automatically a contradiction of the stated rule, evidence of pretraining contamination, or a measured change in predictive performance.

The catalogue records the task, release, fitting protocol where resolved, inspected files, units, source evidence and limitations separately. A native benchmark, a processed mirror and a reconstructed source-library split are different cohorts even when they share a target. Fixed zero-shot assays have no downstream fitting split; probes and fine-tunes on the same targets may have one.

## Measurements

Selected complete cached files were checked for exact full-string identity. Selected DNA checks also used uppercase reverse-complement equivalence; **additional RC-only** classes exclude every class already represented by an exact intersection. An RC class count is not directly interchangeable with an exact-string count. No alignment-based or approximate-homology search was performed.

Intervals use half-open coordinates and must share at least one base. Equality of `(chromosome, start, end)` IDs is a separate, weaker check. Both overlapping interval **pairs** and distinct **affected rows** are retained. Supplied taxonomic and homology-group IDs were compared as IDs, without re-clustering sequences.

The sequence plots divide the number of **distinct shared strings** by the number of **distinct strings in the held-out partition**. They do not estimate the fraction of affected rows. The interval plots divide **held-out windows overlapping any training span** by **all held-out windows**. All figures query the same relational records used by the detailed tables and CSV export. They use a labeled linear percentage axis; values beyond a selected zoom range have an overflow marker.

## Selected results

| Release and check | Result | Interpretation |
| --- | --- | --- |
| PlantCAD2 maize cell-type accessibility, 600-bp core inputs | 18 train/test, 69 train/validation and 6 validation/test distinct exact strings. Test denominator: 243,844 distinct strings in 243,845 windows. | Released test is chr10, train/validation chr1–9. Test chromosome separation holds; exact DNA uniqueness does not. |
| Same PlantCAD2 inputs, genomic spans | 0 train/test and validation/test interval overlaps. Train/validation: 4,531 interval pairs, affecting 4,477 train and 4,347 validation windows. | The earlier finding of disjoint coordinate IDs did **not** establish disjoint spans. The source chromosome-test claim does not promise chromosome-held-out validation. |
| GENEB copy of original NT enhancers | 100 / 400 distinct test strings also occur in train. | A result for the pinned GENEB configuration, not all original or revised NT cohorts. |
| Original NT / GUE yeast H3 and H4 | Identical complete pools: 14,965 H3 and 14,601 H4 sequence–label pairs. NT train contains 1,347 / 1,497 GUE H3 test strings and 1,336 / 1,461 GUE H4 test strings. | Cross-release exposure from different partition assignments, not within-release overlap. The reverse-direction counts and all partition intersections are retained in the [complete comparison](../data/nt-gue-identity-review.json). No published model is assumed to have mixed these releases. |
| GENEB copy of GB human Ensembl enhancers | 9,502 / 29,469 distinct test strings also occur in train; 7 additional RC-only classes. | Exact strings and RC-equivalence classes have different units. GENEB caps training at 100,000 rows here. Shared strings span 2–573 nt; 6,643 are ≥200 nt. Five have different cross-partition label sets, including two with single conflicting labels. |
| RNAGym Pitt ribozyme, `min_similarity` archive | 6 / 35 distinct validation strings recur in training. | The similarity-reducing heuristic is not a strict identity-threshold partition. This is a supervised CV release, not Evo 1/2’s fixed zero-shot cohort. |
| mRNABench Sugimoto, reconstructed default seed 2541 | 181 / 1,694 distinct test strings recur in training; 489 gene names shared. Supplied mapped homology groups have zero intersection. | Every shared gene name lacks a mapping in the supplied human HomoloGene table. The source function assigns unmapped rows independently. |
| BEND original gene finding | 126 train/test interval pairs, affecting 109 / 597 test windows (18.26%); exact coordinate-ID intersection is zero. | Protein-identity grouping does not imply nonoverlapping genomic spans. This is not a count of identical full input strings or proteins. |
| BacBench native essential genes | Genera disjoint. Four exact CDS strings recur train/validation; zero exact CDS strings recur train/test or validation/test. | CDS extraction uses the pinned helper with `promoter_len=0`; it does not reproduce every model’s flanking contexts. The 55-genome native release is distinct from Genos-m’s 51-genome cohort. |
| NTv3 standard benchmark, 11 species | All supplied train/validation/test block spans have zero pairwise overlap. | Metadata result only. Expanded 1-Mb inputs, reference DNA and bulk signal matrices were not compared. |
| BGC-Bench A domains | Parent-BGC folds separate BGC/domain IDs while sharing some GCF IDs. Separate GCF holdout has no shared supplied GCF IDs. | Different grouping levels answer different questions; the less restrictive partition is not thereby a failed GCF holdout. |

The [pinned measurement report](https://github.com/eric-czech/marin-glm/blob/6ff5201fc1734a76f14d647784de90a4692e849c/data/split-inspections.json) contains source revisions, methods and hashes. [Illustrative pairs](https://github.com/eric-czech/marin-glm/blob/6ff5201fc1734a76f14d647784de90a4692e849c/data/split-examples.jsonl) preserve physical file rows, nested indices where needed, coordinates and sequence hashes. Long sequences need not be copied into every example.

PlantCAD2’s [chromosome-test methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13576720/#sec2.6), RNAGym’s [split routine](https://github.com/MarksLab-DasLab/RNAGym/blob/2828cf99316d75daaa8d832a2573cbb25bbd35fe/fitness/utils/cv_split.py#L22-L61), mRNABench’s [mapped-group/row fallback](https://github.com/morrislab/mRNABench/blob/778d691ab91c51c03addeb9219229f2ec81d195c/mrna_bench/data_splitter/homology_split.py#L13-L70), and the [original BEND methods](https://arxiv.org/html/2311.12570v4) provide the claims against which the measurements must be interpreted. These sources do not all promise the same kind of independence.

## Source access and bounds

The original survey reused whole-file inspections and selected cached releases. A subsequent NT/GUE comparison streamed ten small pinned native files without storing raw copies; its separate report records bytes, hashes and all partition intersections. New sequence scans were limited to 1.5 million rows per selected case. PlantCAD2’s original complete sequence counts were reused; lightweight coordinates were scanned completely, and bounded sequence reads recovered examples and held-out unique-string denominators.

Twenty unique PlantCAD2 rows were checked against the documented HF `/rows` API. Their coordinates and sequence hashes matched the pinned release at inspection time. Interactive viewer links address the current release; immutable Parquet links and zero-based physical row indices remain in the examples. JSONL line links preserve small directly inspectable examples independently of viewer behavior.

The 5,754,874,772 compressed bytes of GENERator recovery Parquets, PGB’s multi-million-row oversampled training files, GUANinE’s full training archives and NTv3’s expanded long-input/signal data were excluded from exhaustive overlap scanning. Their records state the unmeasured scope rather than filling it with zero. Access-limited original scored cohorts, including SpliceAI2 and DART inputs, are identified separately from measured releases. Follow-up checks found public DART Synapse metadata but HTTP403 for anonymous file-handle access on the two task5 inputs. The original SpliceAI BaseSpace share redirects to login. [Access receipts](../data/completion-source-checks.json).

Raw research downloads are removed after inspection. The [cleanup record](../data/research-cleanup.json) records 24,366,859,385 bytes removed across 15,364 files. Small reports, file hashes, revisions, example pointers and the source audit remain sufficient to build the site offline. The historical inspection scripts require the indicated upstream data and research dependencies to rerun; routine builds never invoke them.

## Data model

- `split_strategies` and `split_protocol_strategies`: survey definitions and cited source protocols.
- `split_audits` and `split_audit_tasks`: release/cohort scope, linked tasks, conclusion and limits.
- `split_partitions`, `split_comparisons`: denominators, units, intersections and affected windows.
- `split_audit_files`, `split_examples`: file/revision/hash provenance and observed pairs.

Checks are searchable and paginated by release, finding and inspection scope. CSV exports all matching comparisons, including off-page results. Task details link back to associated checks. No count sums across repeated assays, targets or mirrors are presented as independent benchmark evidence.

The NT/GUE H3/H4 follow-up establishes identical complete pools with different partitions, and reports cross-release exposure separately from within-release contamination. [Results and interpretation](source-review.md#dataset-identity-and-phenotype), [pinned files and partition intersections](../data/nt-gue-identity-review.json).
