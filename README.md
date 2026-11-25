# marin-glm

A technical catalogue of genomic language models, papers, evaluation collections, tasks and protocols. The local, single-page draft is [index.html](index.html). It works directly from disk and can be served unchanged by GitHub Pages.

Primary model scope: Evo 2, CENO, Carbon, Carbon-X, GENERator, GENERator-v2, BOTANIC-1, NTv3, DeepD, GPN-Star, AIDO.DNA2 and Genos-m. LOAM and other models are retained as additional evaluation sources. Carbon-X has official release documentation; AIDO.DNA2 has an official technical web report.

The catalogue is a research draft. Registered sources, composite panels awaiting decomposition, paper/protocol audits and selected artifact audits are explicitly distinguished. The number of database records is **not** the number of independently validated biological tasks. The site does not assign ID/OD categories or rank models.

## Files and build

- `data/catalogue.sqlite`: normalized SQLite database; foreign keys and linked evidence.
- `data/catalogue.json`: committed authoring export, organized by database table.
- `data/schema.sql`: relational schema and collection-summary view.
- `data/artifact-inspections.json`: measured public-file statistics, immutable revisions and byte-level SHA-256 hashes. Raw datasets are not committed.
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

Open `http://localhost:8000`, or open `index.html` directly. Filters are encoded in the URL fragment. Task links restore a single expanded record. The CSV export contains all matching records, including those beyond the visible page.

An optional browser check, `tests/browser.py`, requires Playwright and Chromium. It checks actual filtering, taxon ancestry, provenance, direct links, downloads, navigation, JavaScript errors and mobile overflow without external requests.

The generated page and database are committed so GitHub Pages can serve the repository root without a client-side database dependency or a build service. The repository includes CI validation; hosting configuration is separate.

## Record unit and evidence

A task is **dataset × prediction target**. Species, accessions, cell types, assay tracks, conditions, dataset revisions and scoring procedures are linked variants or protocols. Where a paper reports an unresolved panel, it remains explicitly marked as a panel rather than silently treated as one decomposed task. Some suites reuse datasets; collection membership is many-to-many and must not be summed as independent evidence.

Application categories describe research functions such as plant breeding, variant interpretation, RNA engineering and regulatory-sequence engineering. These are editorial mappings from the measured target, not assertions of industrial validation. Capabilities describe what the model/interface must support. Functional-region and organism assignments cite the corresponding task evidence. An assay host and sequence origin can differ.

Evidence is attached to task definitions, individual fields, classifications, variants, protocols, counts and model usage. Source locators include paper sections/PDF pages, pinned repository lines and pinned dataset files. Unknown values remain unknown. A source registration alone does not constitute a full-text or data audit.

`model_properties` holds cited corpus, architecture, tokenization, training and context details, initially for AIDO.DNA2 and Genos-m. Corpus size, consumed training tokens, pretraining context, inference input size and task-specific pooling are separate properties. These model-level descriptions do not define the future pretraining-data catalogue. AIDO.DNA2 tokenization remains unresolved. Genos-m's reported vocabulary of 128 differs from the released config (256) and tokenizer (17 listed entries); the distinction is explicit.

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

## Work remaining

Audit findings are stored in SQLite and shown on the page. Significant remaining work includes individual assay decomposition for GPN-Star ProteinGym and DeepD panels; RNA structure and NABench assay/split audits; LAMBDA task expansion and BGCs-Bench split-file verification; exact NTv3 track manifests; reconciliation of original/revised releases and reused source assays; and completion of task-specific count, coordinate and homology checks. GENEB and RNAGym manifest entries are not all independently audited. Additional model papers remain source registrations until task evidence is established.

AIDO.DNA2 and Genos-m evaluation additions are supported by the inspected report/paper and pinned project documentation, not recounted task artifacts. Genos-m reuses BacBench essentiality and 13 RNAGym assays with separate protocols, while its MIBiG-derived cohorts, VFDB controls and microbiome applications have distinct records. Its documented essentiality cohort differs from the artifact inspected for LOAM. The project labels a benchmark checkpoint `cpt32k` while advertising 1M context; checkpoint correspondence and comparator windowing remain unresolved.

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
