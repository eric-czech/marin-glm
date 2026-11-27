# marin-glm

A technical catalogue of genomic language models, papers, benchmark projects, evaluation collections, tasks and protocols. The public site is [eric-czech.github.io/marin-glm](https://eric-czech.github.io/marin-glm/). The single-page [index.html](index.html) also works directly from disk.

Primary model scope: Evo 2, CENO, Carbon, Carbon-X, GENERator, GENERator-v2, BOTANIC-1, NTv3, DeepD, GPN-Star, AIDO.DNA2, Genos-m, PlantCAD2, SpliceAI and SpliceAI2. The latter two are supervised splicing specialists, included for annotation and variant-prediction comparisons. LOAM and other models are retained as additional evaluation sources. Carbon-X has official release documentation; AIDO.DNA2 has an official technical web report. GeneCAD is recorded as a PlantCAD2-family annotation adaptation, not a separate primary foundation model.

The catalogue is a research draft. Registered sources, composite panels awaiting decomposition, paper/protocol audits and selected artifact audits are explicitly distinguished. The number of database records is **not** the number of independently validated biological tasks. The site does not assign ID/OD categories or rank models.

## Files and build

- `data/catalogue.sqlite`: normalized SQLite database; foreign keys and linked evidence.
- `data/catalogue.json`: committed authoring export, organized by database table.
- `data/schema.sql`: relational schema and collection-summary view.
- `data/artifact-inspections.json`: measured public-file statistics, immutable revisions and byte-level SHA-256 hashes. Raw datasets are not committed.
- `data/plantcad-artifact-inspections.json`: pinned PlantCAD Parquet footer counts, selected full-column scans and sampled sequence lengths. Its footer hashes are explicitly **not whole-file hashes**.
- `data/source-snapshots.json`: pinned GitHub files used during the audit.
- `data/site-data.json`: database export consumed by the page build.
- `site/`: HTML template, CSS and JavaScript.
- `scripts/build.py`: offline database rebuild, integrity validation and page generation. Python 3.10+ standard library only.
- `scripts/curate.py`, `scripts/curation/`: research authoring helpers; require the ignored, inspected source cache. Routine page/database builds do not require this cache.

```bash
python scripts/build.py
python -m unittest discover -s tests -p 'test_*.py'
python -m http.server 8000
```

Open `http://localhost:8000`, or open `index.html` directly. Evaluations opens in Coverage, with Tasks and Collections as alternate views. Shared filters, selected matrix cells, taxon detail, sorting, pagination and expanded table rows are encoded in the URL fragment. Existing task links still restore a single expanded record. The CSV export contains all matching records, including those beyond the visible page. Tables default to 100 rows and support 25, 50, 100 or 250 rows per page.

## Evaluation coverage

Coverage plots individual task/panel associations by biological division/species and genomic feature. Four colors distinguish prediction, generation, retrieval/comparison and analysis/diagnostic tasks; six source shapes preserve original Evo 2 attribution separately from later collection membership. Protein-only references use hollow symbols; unresolved panels use faint symbols. Color is a presentation-level aggregation of the cited task type/capabilities, not an additional claim about model architecture.

All 545 task/panel records are retained. Coverage defaults to 14 grouped feature columns, with separate coding-sequence and joint structure targets; individual features remain available. Selected organisms has 48 populated rows and 787 grouped markers (1,005 individual-feature markers); every named species has 87 rows and 919 grouped markers (1,322 individual); clades only has 32 rows and 739 grouped markers (934 individual). A marker is a task-level co-annotation, not proof of a released species × feature subset or an independent biological cohort. Row counts are unique records and cannot be added. Known-origin synthetic constructs stay with their taxa; construction remains an attribute. Broad labels are never projected to all descendants. Assay/sample hosts alone do not qualify a task for an organism filter.

Cell selection narrows the shared task table and remains visible as a removable filter in all three views. Organism/feature filters restrict plotted associations as well as canonical task IDs, avoiding unrelated species markers from a multi-species task. Tables provide sorting, pagination and expandable protocol/count/evidence details; collections without decomposed tasks remain available in Collections. Secondary sections remain Projects, Models, Papers, Data and Audit notes.

The displayed hierarchy retains domains and selected familiar biological divisions, with 30 division headers in the default view. Intermediate ancestry, trait explanations and sources are available in Taxonomy details. Six cited priority coverage questions are below the matrix; positive paper evidence lacking decomposed tasks receives notes rather than invented markers. Neither constitutes a claim of exhaustive dataset absence. No ID/OD policy is assigned.

`coverage_nodes`, `coverage_rows`, `coverage_mappings`, `coverage_notes` and `coverage_settings` store cited assignments and presentation configuration in SQLite. The node graph and its population links are separate from the simplified display. `scripts/coverage_data.py` compiles them with the canonical task classifications and model-use records during the offline build. The page embeds only that compiled representation, not another set of task definitions. `scripts/curation/import_coverage.py` records the one-time promotion of the audited local prototype and its cached taxonomy responses; routine builds require neither the prototype nor its cache. NTv3's two exact-structure tasks now link the 17 explicitly scored held-out species. Verified UniProt/GenBank protein-target origins remain distinct from assay host and native genomic coordinates.

An optional browser check, `tests/browser.py`, requires Playwright and Chromium. It checks actual filtering, taxon ancestry, provenance, direct links, downloads, navigation, JavaScript errors and mobile overflow without external requests.

The generated page and database are committed so GitHub Pages can serve the repository root without a client-side database dependency or a build service. The repository includes CI validation; hosting configuration is separate.

## Outputs and genomic features

Every task/panel has a cited `task_outputs` review separating its prediction form from the unit actually scored. Isolated labels, sampled position labels, dense labels, signal profiles, detected intervals, jointly evaluated structures and diagnostic endpoints are separate. The shared Scored output filter, compact table, detailed task record and CSV expose this distinction. Partial and unresolved reviews remain visible.

`task_feature_scopes` distinguishes CDS-specific targets from mixed region classifiers, broad input context, derived-proteome readouts and protein-only references. Coding-sequence evaluations retain a separate default column. Joint coding/gene and splice-pattern reconstruction have structure columns; individual genomic feature assignments are preserved. UTRs and translation boundaries remain distinct.

[The source audit](docs/output-audit.md) documents the SpliceAI papers and protocols, original BEND decomposition, classification corrections and evidence limits. The original BEND gene-finding MCC measures dense base labels, while GeneCAD/NTv3 and the SpliceAI2 dominant-transcript benchmark provide distinct structure-level endpoints.

## Record unit and evidence

A task is **dataset × prediction target**. Species, accessions, cell types, assay tracks, conditions, dataset revisions and scoring procedures are linked variants or protocols. Where a paper reports an unresolved panel, it remains explicitly marked as a panel rather than silently treated as one decomposed task. Some suites reuse datasets; collection membership is many-to-many and must not be summed as independent evidence.

Application categories describe research functions such as plant breeding, variant interpretation, RNA engineering and regulatory-sequence engineering. These are editorial mappings from the measured target, not assertions of industrial validation. Capabilities describe what the model/interface must support. Genomic-feature and organism assignments cite the corresponding task evidence. An assay host and sequence origin can differ.

Evidence is attached to task definitions, individual fields, classifications, variants, protocols, counts and model usage. Source locators include paper sections/PDF pages, pinned repository lines and pinned dataset files. Unknown values remain unknown. A source registration alone does not constitute a full-text or data audit.

`model_properties` holds cited corpus, architecture, tokenization, training and context details, initially for AIDO.DNA2, Genos-m, PlantCAD2, SpliceAI and SpliceAI2. The latter two are supervised splicing specialists, included for annotation and variant-prediction comparisons. Corpus size, consumed training tokens, pretraining context, inference input size and task-specific pooling are separate properties. These model-level descriptions do not define the future pretraining-data catalogue. AIDO.DNA2 tokenization remains unresolved. Genos-m's reported vocabulary of 128 differs from the released config (256) and tokenizer (17 listed entries); the distinction is explicit.

The current status labels are:

| Status | Meaning |
| --- | --- |
| `artifact-audited` | Selected released files were read/recounted, alongside the available procedure. Checked fields and remaining gaps are stated. This does not certify every label, protocol or pretraining exclusion. |
| `paper-audited` | Task or procedure supported by inspected paper, methods, code or documentation; full data/split verification remains pending. |
| `registered` | Source/manifest entry retained in scope; individual task audit incomplete. |
| `panel-pending` | Composite collection awaiting individual dataset/target decomposition. |

`evidence.basis` records paper, documentation, code, data or curatorial evidence. Field-level evidence takes precedence over a coarse task status. Reported counts and measured file counts are separate rows with units, revisions and filtering qualifiers. A Parquet row may represent a whole genome containing thousands of gene labels. Split-file rows may precede scorer eligibility filtering.

Source hashes refer to the cached representation named by `local_path`; for paper text that can be extracted text rather than the publisher PDF. Dataset-file hashes in `artifact-inspections.json` refer to downloaded file bytes. Paper/report versions and code/data revisions are independent.

## Evo 2 provenance

`model_evaluations.provenance` distinguishes `original-paper`, `original-release`, `external-evaluation` and `released-example`. The original Evo 2 paper used DART tasks 1, 2 and 5, not the full suite. Later LOAM, mRNABench, GENERator-v2 and GPN-Star comparisons are recorded as external evaluations. Source-specific ClinVar cohorts, scoring contexts, readouts and DMS conversions are not merged merely because they use the same resource name. Missing association is unknown, not a verified negative.

## Benchmark projects

A project is a **substantial, primarily dedicated effort to build a reusable standardized evaluation framework or benchmark suite for genomic/nucleotide models**, with documented use by **at least two distinct independent research groups**. This is a conservative catalogue inclusion rule, not a scientific quality ranking. A project can contain multiple benchmark releases; a collection does not need a project to remain in scope.

Concrete evaluation or software use qualifies as adoption. Citation-only mentions, surveys, repository stars, downloads, model wrappers and author-run leaderboards do not. Follow-up evaluations with shared benchmark authorship do not count toward the independent-group threshold. Adoption records identify the actual release, subset, modality and adaptation; copied comparator scores do not count as new experiments. Independence is a cited curatorial assessment of the research groups, not a claim about funding or institutional separation. The review is dated and non-exhaustive: **adoption not established** does not mean **no users exist**.

The first qualifying set is Genomic Benchmarks (2023), DART-Eval, TraitGym, BEND, Genomics LRB, DNALongBench, RNAGym, mRNABench, DGEB and BacBench. Original BEND and BEND 2.0 are separate collections within the BEND project; the external-use evidence currently concerns original BEND. DGEB's protein-only adoption is explicitly identified and does not establish nucleotide-task performance. BacBench is a standalone resource predating the later BacLM addition; LOAM and Genos-m use subsets with different cohorts/protocols. Its related anonymous ICLR submission is registered without asserting equivalence to the current repository or a later publication.

GUE, the original/revised NT benchmarks, Plant Genomic Benchmark and Gene-MTEB remain model-associated collections rather than projects under this definition. Dedicated efforts such as GENEB, GUANinE, OmniGenBench, GFMBench-API, GenBench, DNA Foundation Benchmark, NABench and the newer Genomic Benchmarks QC/audit ecosystem retain their papers and source records, but are not shown as qualified projects where independent adoption was not established. The QC/audit ecosystem is distinct from the 2023 Genomic Benchmarks dataset collection. No published paper is invented for its manuscript in preparation.

The project review revisits every existing evaluation collection. `project_reviews` stores purpose, decision, rationale, search scope and evidence. `projects` contains only qualified entries. `project_review_papers` links introducing/update papers and adoption evidence; `project_review_evaluations` links versioned collections; `project_adoptions` records external use and independence. `project_summary` counts linked **catalogue coverage**, not a project's full published task inventory. Database build checks enforce the purpose and adoption rule. Reviews that do not qualify are collapsed in the Projects view, and remain queryable in SQLite.

The Projects view links to collections, papers and release-specific adoption evidence. A project filter composes with application, taxon, capability, functional-region and Evo 2 provenance filters; CSV exports include project membership. Project membership never changes original Evo 2 attribution. New papers used only to establish adoption do not expand the primary model list.

Original BEND, LRB, DNALongBench, GenBench, DNA Foundation Benchmark and Gene-MTEB are now explicitly registered collections. Individual dataset × target expansion and data/protocol equivalence checks remain pending; no paper-level inventory has been converted into fabricated task records or inherited classifications. Existing tasks, variants, counts, protocols and model-use associations are preserved. GUE and NT collections now link their introducing model papers; GENEB's published conference version is registered separately from its existing arXiv/code task evidence.

## Work remaining

Audit findings are stored in SQLite and shown on the page. Significant remaining work includes exact assay manifests for GPN-Star ProteinGym and seven DeepD panels; RNA structure and NABench assay/split audits; LAMBDA task expansion and BGCs-Bench split-file verification; exact NTv3 track manifests; reconciliation of original/revised releases and reused source assays; and task-specific coordinate and homology checks. Additional model papers remain source registrations until task evidence is established.

The November 26 follow-up audited the 142 previously flagged task/panel records. All 133 manifest registrations now have task-specific artifact or released-procedure evidence: 64 GENEB entries, 59 RNAGym assays and ten Carbon-X tasks. The human DeepD routing panel was replaced by six binary annotation targets; eight other panels retain explicit source-information gaps. A source/protocol audit is not complete raw-data verification.

- GENEB: all 200 pinned CSVs inspected, totaling 3,393,004 rows across 100 configurations. Counts, scalar labels, full sequence-length ranges and exact train/test overlap are recorded per release variant. Twenty-five configurations contain exact sequence strings in both train and test. Coordinate and homology separation are not established by these two-column files. The five configurations categorized as “Mouse Enh.” are GUE mouse TF-binding tasks; the source category is corrected in the task classifications.
- RNAGym: all 70 processed fitness files inspected, totaling 1,117,406 rows, plus all 124 supervised partition files covering 31 assays. Scoring excludes a missing-mutant WT row and drops missing experimental/model scores pairwise. Absolute Spearman, direction-invariant AUROC and absolute MCC are recorded separately. Exact sequence overlap persists in two assays even in the released similarity-heuristic split; it must not be described as guaranteed homology separation. Assay host is distinguished from sequence origin; unverified species remain unassigned.
- Carbon-X: pinned loader, prompt adapter, scorer and aggregation inspected for every task. All five subsets are loaded from an HF split called `train` for evaluation. The pinned public dataset endpoint returned HTTP 401; raw counts, taxon membership and biological partitions remain unavailable. Reported counts are not presented as measurements.
- DeepD: the human routing release specifies CDS, cCRE, DNA-transposon, LINE, LTR and SINE targets with 8K/1M checkpoint variants. Released XGBoost models differ from the paper’s linear probes. Full-split counts are reports in the metrics table; the committed 20,000-base HBB interval is a separate local example. Remaining assay-panel identities and coordinate manifests are not borrowed from another model’s experiments.

Measurements and byte hashes are committed in `data/geneb-artifact-inspections.json`, `data/rnagym-artifact-inspections.json` and `data/rnagym-evo2-prediction-inspections.json`; `scripts/inspect_pending_artifacts.py` reproduces the scans using the research environment. All 70 released Evo 2 prediction members were inspected to verify actual external usage and finite scored-row counts; original Evo 2 paper attribution remains separate. Raw data are not redistributed. The publisher’s RNAGym archive URLs are mutable; hashes identify the inspected bytes. Its public archive host had an incomplete TLS issuer chain during retrieval, so those hashes are not authenticated publisher signatures.

Capability filters now show global record counts and explicit active-filter combinations. Generation is a parent category; conditional generation includes actual prefix/attribute-conditioned sequence outputs. Unconditional generation covers the two reported family-adapted GENERator sampling tasks, with unreported sampling initialization retained as a limitation. Probability-only motif recovery is not automatically treated as a generative experiment. All GeneCAD tasks remain discoverable under dense annotation; BUSCO is labeled downstream validation of annotation. Scalar ATAC count prediction is not a dense output.

AIDO.DNA2 and Genos-m evaluation additions are supported by the inspected report/paper and pinned project documentation, not recounted task artifacts. Genos-m reuses BacBench essentiality and 13 RNAGym assays with separate protocols, while its MIBiG-derived cohorts, VFDB controls and microbiome applications have distinct records. Its documented essentiality cohort differs from the artifact inspected for LOAM. The project labels a benchmark checkpoint `cpt32k` while advertising 1M context; checkpoint correspondence and comparator windowing remain unresolved.

PlantCAD2 has 12 released zero-shot configurations with linked maize/tomato variants, seven released supervised configurations, and separate paper-only endpoints. The [leaderboard](https://huggingface.co/spaces/plantcad/plantcad2-zeroshot-leaderboard) splits the zero-shot configurations into 20 entries; those are not 20 independent dataset/target tasks. Published potato GERP conservation, maximum-across-tissues expression, and Arabidopsis-to-maize expression transfer have no matching named configuration in the inspected HF releases. Known-site motif recovery and core-gene membership do not establish genome-wide site detection. Ribo-seq-derived translation abundance is not direct protein quantitation.

All 39 zero-shot Parquet files were inspected for footer counts, relevant label columns and sampled sequence lengths. Seven supervised files were checked: all translation splits and the maize cell-type accessibility test. The latter contains only chromosome 10 and 92-character binary labels. Translation regression labels match `log10(1 + TPM)` in all splits, whereas the paper describes `log10(TPM)`; binary labels match `TPM > 1`. Translation train and validation both contain Arabidopsis chromosomes 1–5. Most supervised files still have card-reported counts only; sequence lengths were sampled, not exhaustively scanned.

GeneCAD's 2025 preprint froze PlantCAD2 and trained an annotation head on five species. The pinned 2026 release explicitly fine-tunes a 200M PlantCAD2-family backbone on eight species, with random-window validation within chromosomes. Its released coding benchmark converts CDS segments into exon chains and ignores UTRs, with separate default and strict gffcompare scoring. Historical full-annotation tasks, revised coding-only tasks, boundary detection and BUSCO completeness remain separate. Distant plant cohorts and the single experimental vertebrate-model case are linked variants; the vertebrate result is not attributed to the plant-trained checkpoint. Prediction manifests and released results were inspected, but reference genomes and every prediction GFF have not been independently re-scored.

The separate pretraining-data section is intentionally work in progress. No data policy or ID/OD policy is implied by the current categories.

## Query examples

```sql
-- Tasks documented in the original Evo 2 paper
SELECT DISTINCT t.id, t.name, p.name AS protocol
FROM model_evaluations m JOIN tasks t ON t.id=m.task_id
LEFT JOIN protocols p ON p.id=m.protocol_id
WHERE m.model_id='evo2' AND m.provenance='original-paper';

-- Measured counts, their units, and the exact cited file
SELECT t.name, c.split, c.value, c.unit, c.qualifier, e.url
FROM counts c JOIN tasks t ON t.id=c.task_id
JOIN evidence e ON e.id=c.evidence_id
WHERE c.method='measured';

-- Pending composite panels
SELECT id, name, limitations FROM tasks WHERE status='panel-pending';
```

Original repository code and catalogue prose are MIT-licensed. Referenced papers, datasets and third-party code retain their respective terms; the repository distributes catalogue metadata and citations, not their full contents.
