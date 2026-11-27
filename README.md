# marin-glm

A technical catalogue of genomic language models, papers, benchmark projects, evaluation collections, tasks and protocols.

[Public site](https://eric-czech.github.io/marin-glm/) · [SQLite](data/catalogue.sqlite) · [Authoring JSON](data/catalogue.json)

The primary models are Evo 1, Evo 2, CENO, Carbon, Carbon-X, GENERator, GENERator-v2, BOTANIC-1, NTv3, DeepD, GPN-Star, AIDO.DNA2, Genos-m, PlantCAD2, SpliceAI and SpliceAI2. SpliceAI and SpliceAI2 are supervised specialists. GeneCAD is a PlantCAD2-family annotation adaptation. Additional models and papers document related evaluations and independent benchmark use.

All indexed task definitions and collections have completed source reviews. A review can establish that a publication omits a field or that a release is inaccessible; it cannot supply missing evidence. Those limitations remain explicit. The catalogue does not assign ID/OD categories or rank models, and record counts are not counts of independent biological assays.

## Build and verification

```bash
python scripts/build.py
python -m unittest discover -s tests -p 'test_*.py'
python -m http.server 8000
```

Open `http://localhost:8000`, or open [index.html](index.html) directly. The generated page is self-contained and uses no external requests. Ordinary builds require Python 3.10+ and its standard library; research dependencies are not required.

The optional browser check, `python tests/browser.py`, requires Playwright and Chromium. It exercises filters, table pagination, deep links, marker tooltips, downloads, taxonomy and mobile layout. GitHub Actions rebuilds the catalogue, checks its integrity and verifies the committed page/export.

GitHub Pages serves the repository root. Source, generated HTML and the downloadable database are committed together.

## Record structure

A task is **dataset × prediction target**. Species, cell types, assay tracks, conditions, revisions and scoring procedures are linked variants or protocols. Collection membership is many-to-many. Reused tasks share one identity while retaining different source cohorts, transformations and readouts. PlantCAD2 and BOTANIC-1 maize cell-type accessibility share a target, while their reported chromosome partitions and context protocols remain distinct. Retired duplicate IDs redirect to their replacements.

| Tables | Purpose |
| --- | --- |
| `papers`, `sources`, `evidence`, `field_evidence` | Publication/release identity, exact locators and field-level support. |
| `models`, `model_properties`, `model_evaluations` | Model details and documented task use, including original/external provenance. |
| `evaluations`, `tasks`, `evaluation_tasks`, `variants` | Collections, dataset–target identities and source-specific variants. |
| `protocols`, `protocol_metrics`, `counts` | Adaptation, interfaces, split/selection rules, metrics and qualified counts. |
| `assay_tracks`, `task_tracks` | Individual released track identities and biological contexts without creating one task per track. |
| `categories`, `task_categories`, `task_outputs`, `task_feature_scopes` | Application, capability, feature and evaluated-output decisions. |
| `source_reviews`, `source_limits` | Completed review scope and precise unreported, unreleased, inaccessible or conflicting fields. |
| `data_resources`, `task_resources`, `evaluation_resources` | Explicit dataset, manifest, code and result links. |
| `project_reviews`, `projects`, `project_adoptions` | Dedicated benchmark qualification and independent use. |
| `coverage_nodes`, `coverage_rows`, `coverage_mappings`, `coverage_settings` | Cited taxonomy assignments and simplified presentation. |

[data/schema.sql](data/schema.sql) defines keys and constraints. [data/catalogue.json](data/catalogue.json) is the committed authoring document; the build inserts it into SQLite and queries SQLite to produce the page payload. Research helpers in `scripts/curation/` are authoring operations, not a chain of migrations run during a normal build.

Inspection manifests in `data/*inspections.json` preserve measured counts, checked columns, revisions and hashes. A whole-file hash, a Parquet footer hash, a metadata-column scan and a full sequence scan are different inspections and are identified as such. Raw third-party datasets and full papers are not redistributed. Ignored research caches are unnecessary for building or using the site.

## Evidence and source limits

Evidence attaches separately to definitions, classifications, organisms, variants, protocols, counts and model use. Locators include paper sections/pages, pinned GitHub files and pinned Hugging Face artifacts. Application assignments are cited editorial interpretations of the actual target, not claims of industrial validation.

Task evidence levels describe the evidence inspected:

| Level | Meaning |
| --- | --- |
| Paper and selected artifacts | Specific released data, manifests or evaluation code were inspected. The review states which fields were checked. |
| Paper and methods | The available primary text/procedure defines the task. Data access and omitted fields remain qualified. |
| Source-limited definition | The source reports an evaluation whose assay identity, cohort or procedure cannot be fully resolved from the available material. The claim remains visible with explicit limits. |

These levels are not work queues and are not filter options. `source_reviews` records a completed, dated scope. `source_limits.reason` distinguishes `not-reported`, `not-released`, `not-retrieved`, `access-restricted`, `conflicting` and `not-applicable`. A missing manifest is not borrowed from another model because its panel has the same name or size.

Reported, measured and derived counts remain separate, with units and filtering qualifiers. A genome row may contain thousands of gene labels; a variant may have multiple tissue/scorer rows; a released split may precede score eligibility filtering. Counts are not additive across such views.

Data links distinguish **HF/GH data**, **manifests**, **evaluation code** and **results**. A code repository is not presented as a dataset, and a result table is not a released input cohort. Availability and revision are shown in task/collection details.

## Evaluations interface

Evaluations opens in **Coverage**, with **Tasks** and **Collections** as alternate views. Shared filters cover application, organism/clade, model capability, genomic feature, scored output, collection, project and Evo 2 provenance. Cell selection narrows the same task table. Sorting, pagination, filters and expanded records are retained in URL fragments. CSV exports include every matching task, including off-page results.

Coverage uses four colors for prediction, generation, retrieval/comparison and analysis/diagnostics. Source shapes are ordered as follows:

1. Evo 1 / Evo 2
2. RNAGym / ProteinGym / TraitGym
3. PlantCAD2 / GeneCAD / Botanic-1
4. NT / GUE / GB / GENEB
5. BacBench / DGEB / BGC
6. Other papers / benchmarks

Original Evo attribution takes precedence over collection membership in the shape assignment. Hover or keyboard focus identifies the task, evaluated output, associated collections, papers and models. Protein-only references are hollow; source-limited definitions are faint.

The hierarchy separates cellular domains, selected eukaryotic lineages and viruses, with synthetic/unplaced contexts distinguished from taxa. Familiar biological divisions remain visible; intermediate ancestry and sources are available in Taxonomy details. Selected model organisms have individual rows. Broad source labels are not projected onto every descendant. Assay host and sequence origin are separate.

A marker is a task association, not an independent cohort. Species-specific feature restrictions are used where released identities resolve them; otherwise task-level co-annotation does not establish a released species × feature subset. Priority coverage questions are catalogue-relative and do not assert exhaustive absence from every broad panel.

## Outputs and features

Scored output describes what the evaluation measures, independently of the model's native output:

- isolated labels/values or nonpositional vectors;
- sampled position labels;
- dense position labels or quantitative signal profiles;
- matched elements/boundaries or jointly scored structures;
- pairwise/contact outputs;
- sequence generation/recovery, retrieval or diagnostics.

A cell-type vector has no genomic position axis. Dense splice labels do not establish a valid transcript chain. A whole-gene or splice-pattern match does not establish UTR, transcript-end, coding-phase, abundance or all-isoform accuracy unless those are actually scored.

Coverage retains **coding sequence** separately from mixed gene elements. Joint gene structures and spliced transcript structures have their own columns. UTRs, translation boundaries, splice sites/junctions and regulatory elements remain distinguishable in the detailed feature view. Complete-structure tasks are not repeated under every constituent feature in the grouped view.

[Output audit and source decisions](docs/output-audit.md) explains the important distinctions, including SpliceAI/SpliceAI2, GeneCAD, NTv3, BEND, routing/SAE analyses and sequence diagnostics.

## Provenance and projects

`model_evaluations.provenance` distinguishes `original-paper`, `original-release`, `external-evaluation` and `released-example`. Evo 1 and Evo 2 are separate model/publication records. Later evaluations of Evo 2 do not become original Evo 2 results. The original Evo 2 paper uses DART tasks 1, 2 and 5, not the whole DART suite. Source-specific ClinVar/DMS cohorts and readouts remain separate.

A project must primarily develop a substantial reusable genomic/nucleotide evaluation framework or suite, with documented evaluation/software use by at least **two distinct independent research groups**. Citation-only mentions, wrappers, stars, downloads and author-run leaderboards do not meet that rule. Shared benchmark authorship does not count as independent adoption. This is an inclusion rule, not a quality ranking.

Adoption records specify release, subset, modality and adaptation. A project may contain multiple collections; a useful collection need not qualify as a project. Adoption-evidence papers do not automatically expand the primary model scope.

## Queries

```sql
-- Original Evo 2 use, distinct from later evaluations of Evo 2.
SELECT DISTINCT t.id, t.name, p.name AS protocol
FROM model_evaluations m JOIN tasks t ON t.id=m.task_id
LEFT JOIN protocols p ON p.id=m.protocol_id
WHERE m.model_id='evo2' AND m.provenance='original-paper';

-- Exact data resources and their release/availability.
SELECT t.name, r.title, r.kind, r.host, r.revision, r.availability, r.url
FROM tasks t JOIN task_resources l ON l.task_id=t.id
JOIN data_resources r ON r.id=l.resource_id;

-- Source limits, not unfinished catalogue work.
SELECT entity_table, entity_id, field, reason, detail
FROM source_limits;
```

Original repository code and catalogue prose are MIT-licensed. Referenced papers, datasets and code retain their respective terms.
