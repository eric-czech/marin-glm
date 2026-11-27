PRAGMA foreign_keys = ON;

CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
  url TEXT NOT NULL, version TEXT, retrieved TEXT, sha256 TEXT,
  local_path TEXT, availability TEXT NOT NULL DEFAULT 'available', notes TEXT
);
CREATE TABLE papers (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, year INTEGER, publication_date TEXT,
  doi TEXT, source_id TEXT NOT NULL REFERENCES sources(id), status TEXT NOT NULL,
  scope TEXT NOT NULL, notes TEXT
);
CREATE TABLE models (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, scope TEXT NOT NULL,
  paper_id TEXT REFERENCES papers(id), description TEXT NOT NULL,
  evidence_id TEXT REFERENCES evidence(id), notes TEXT
);
CREATE TABLE evidence (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  locator TEXT NOT NULL, url TEXT NOT NULL, basis TEXT NOT NULL CHECK
    (basis IN ('paper','documentation','code','data','curatorial')),
  statement TEXT NOT NULL, inspected TEXT NOT NULL
);
CREATE TABLE model_properties (
  id TEXT PRIMARY KEY, model_id TEXT NOT NULL REFERENCES models(id),
  category TEXT NOT NULL, name TEXT NOT NULL, variant TEXT,
  value TEXT NOT NULL, status TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), notes TEXT
);
CREATE TABLE evaluations (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
  paper_id TEXT REFERENCES papers(id), source_id TEXT REFERENCES sources(id),
  status TEXT NOT NULL, scope_note TEXT NOT NULL,
  evidence_id TEXT REFERENCES evidence(id), notes TEXT
);
-- Projects are dedicated benchmark efforts with verified independent adoption.
-- A collection or a model-associated benchmark need not belong to a project.
CREATE TABLE project_reviews (
  id TEXT PRIMARY KEY, name TEXT NOT NULL,
  decision TEXT NOT NULL CHECK(decision IN ('qualified','adoption-not-established','outside-definition')),
  dedicated INTEGER NOT NULL CHECK(dedicated IN (0,1)),
  reviewed TEXT NOT NULL, search_scope TEXT NOT NULL,
  rationale TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE projects (
  id TEXT PRIMARY KEY, name TEXT NOT NULL,
  review_id TEXT NOT NULL UNIQUE REFERENCES project_reviews(id),
  description TEXT NOT NULL, scope_note TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE project_review_papers (
  review_id TEXT NOT NULL REFERENCES project_reviews(id),
  paper_id TEXT NOT NULL REFERENCES papers(id),
  relation TEXT NOT NULL CHECK(relation IN ('introducing','update','associated-model','adoption-evidence','related-report')),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY(review_id,paper_id,relation)
);
CREATE TABLE project_review_evaluations (
  review_id TEXT NOT NULL REFERENCES project_reviews(id),
  evaluation_id TEXT NOT NULL REFERENCES evaluations(id),
  relation TEXT NOT NULL CHECK(relation IN ('defines','successor-release','implements','associated-collection')),
  note TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY(review_id,evaluation_id)
);
CREATE TABLE project_adoptions (
  id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES project_reviews(id),
  paper_id TEXT REFERENCES papers(id), adopter_group TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('evaluation-use','software-use','dataset-reuse','citation-only')),
  independence TEXT NOT NULL CHECK(independence IN ('independent','shared-authorship','not-established')),
  scope TEXT NOT NULL, independence_note TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE VIEW project_summary AS
SELECT p.*,
 (SELECT COUNT(DISTINCT a.adopter_group) FROM project_adoptions a
  WHERE a.review_id=p.review_id AND a.independence='independent' AND a.kind!='citation-only') AS independent_groups,
 (SELECT COUNT(*) FROM project_review_evaluations r WHERE r.review_id=p.review_id) AS collection_count,
 (SELECT COUNT(DISTINCT et.task_id) FROM project_review_evaluations r
  JOIN evaluation_tasks et ON et.evaluation_id=r.evaluation_id
  WHERE r.review_id=p.review_id AND r.relation IN ('defines','successor-release')) AS task_count
FROM projects p;
CREATE TABLE tasks (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, dataset_name TEXT NOT NULL,
  target TEXT NOT NULL, description TEXT NOT NULL, task_type TEXT NOT NULL,
  label_basis TEXT NOT NULL, status TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), limitations TEXT,
  input_description TEXT NOT NULL, output_description TEXT NOT NULL
);
-- The assessed output is independent of the biological feature. A model can
-- emit a dense track while a particular benchmark scores only one selected site.
CREATE TABLE task_outputs (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id),
  category_id TEXT NOT NULL REFERENCES categories(id),
  prediction_form TEXT NOT NULL, scoring_unit TEXT NOT NULL,
  position_axis TEXT NOT NULL CHECK(position_axis IN
    ('none','sampled','contiguous','interval-set','linked','unresolved')),
  structure_scope TEXT NOT NULL CHECK(structure_scope IN
    ('none','coding-chain','full-transcript','splice-pattern','gene-locus','unresolved')),
  status TEXT NOT NULL CHECK(status IN ('supported','partial','unresolved')),
  rationale TEXT NOT NULL, limitations TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE task_feature_scopes (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
  feature_id TEXT NOT NULL REFERENCES categories(id),
  scope TEXT NOT NULL CHECK(scope IN
    ('restricted-target','mixed','context','protein-reference','derived-readout')),
  rationale TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id),
  UNIQUE(task_id,feature_id)
);
-- Track identity is retained without treating every assay track as a new task.
-- Public pages use task/species/assay summaries; the downloadable DB preserves
-- every source row and its biological context.
CREATE TABLE assay_tracks (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  source_track_id TEXT NOT NULL,
  population_id TEXT NOT NULL REFERENCES populations(id),
  assay TEXT NOT NULL,
  metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json)),
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE task_tracks (
  task_id TEXT NOT NULL REFERENCES tasks(id),
  track_id TEXT NOT NULL REFERENCES assay_tracks(id),
  variant_id TEXT REFERENCES variants(id),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY(task_id,track_id)
);
CREATE TABLE evaluation_tasks (
  evaluation_id TEXT NOT NULL REFERENCES evaluations(id),
  task_id TEXT NOT NULL REFERENCES tasks(id),
  variant_id TEXT, note TEXT,
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY (evaluation_id, task_id)
);
CREATE TABLE variants (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), name TEXT NOT NULL,
  dataset_revision TEXT, context TEXT, input_length TEXT, target_count INTEGER,
  target_unit TEXT, notes TEXT, evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE populations (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, rank TEXT NOT NULL,
  parent_id TEXT REFERENCES populations(id), ncbi_taxid INTEGER, notes TEXT
);
CREATE TABLE task_populations (
  task_id TEXT NOT NULL REFERENCES tasks(id),
  population_id TEXT NOT NULL REFERENCES populations(id),
  variant_id TEXT REFERENCES variants(id), relation TEXT NOT NULL,
  coverage TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY (task_id, population_id, relation)
);
CREATE TABLE categories (
  id TEXT PRIMARY KEY, dimension TEXT NOT NULL CHECK
    (dimension IN ('application','capability','region','output')),
  name TEXT NOT NULL, definition TEXT NOT NULL, accommodation TEXT
);
CREATE TABLE task_categories (
  task_id TEXT NOT NULL REFERENCES tasks(id), category_id TEXT NOT NULL REFERENCES categories(id),
  relation TEXT NOT NULL, rationale TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  attribution TEXT NOT NULL CHECK (attribution IN ('source','curatorial')),
  PRIMARY KEY (task_id, category_id, relation)
);
-- Biological placement and display choices are separate. JSON fields contain
-- presentation metadata or lists of evidence IDs, never a second task record.
CREATE TABLE coverage_nodes (
  id TEXT PRIMARY KEY, parent_id TEXT REFERENCES coverage_nodes(id),
  population_id TEXT REFERENCES populations(id), label TEXT NOT NULL,
  scientific TEXT NOT NULL, rank TEXT NOT NULL, note TEXT NOT NULL,
  section TEXT NOT NULL, jump TEXT, sources_json TEXT NOT NULL CHECK(json_valid(sources_json))
);
CREATE TABLE coverage_rows (
  id TEXT PRIMARY KEY, view TEXT NOT NULL CHECK(view IN ('clade','species','allSpecies')),
  row_key TEXT NOT NULL, node_id TEXT NOT NULL REFERENCES coverage_nodes(id),
  population_ids_json TEXT NOT NULL CHECK(json_valid(population_ids_json)),
  metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json)), UNIQUE(view,row_key)
);
CREATE TABLE coverage_mappings (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
  population_id TEXT REFERENCES populations(id), basis TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  supporting_json TEXT NOT NULL CHECK(json_valid(supporting_json)),
  clade_row TEXT NOT NULL REFERENCES coverage_rows(id),
  species_row TEXT NOT NULL REFERENCES coverage_rows(id),
  all_species_row TEXT NOT NULL REFERENCES coverage_rows(id),
  metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json))
);
CREATE TABLE coverage_notes (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('gap','known','context')),
  node_id TEXT NOT NULL REFERENCES coverage_nodes(id),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
);
CREATE TABLE coverage_settings (key TEXT PRIMARY KEY, value_json TEXT NOT NULL CHECK(json_valid(value_json)));
CREATE TABLE protocols (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
  variant_id TEXT REFERENCES variants(id), name TEXT NOT NULL,
  adaptation TEXT NOT NULL, requires_embeddings INTEGER CHECK(requires_embeddings IN (0,1)),
  model_interface TEXT NOT NULL, fitted_component TEXT, selection TEXT,
  split_rule TEXT NOT NULL, split_unit TEXT NOT NULL,
  source_evidence_id TEXT NOT NULL REFERENCES evidence(id), notes TEXT
);
CREATE TABLE metrics (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, definition TEXT NOT NULL, direction TEXT NOT NULL
);
CREATE TABLE protocol_metrics (
  protocol_id TEXT NOT NULL REFERENCES protocols(id), metric_id TEXT NOT NULL REFERENCES metrics(id),
  aggregation TEXT NOT NULL, is_primary INTEGER NOT NULL CHECK(is_primary IN (0,1)),
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY(protocol_id, metric_id)
);
CREATE TABLE counts (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
  variant_id TEXT REFERENCES variants(id), protocol_id TEXT REFERENCES protocols(id),
  split TEXT NOT NULL, value INTEGER NOT NULL CHECK(value >= 0), unit TEXT NOT NULL,
  qualifier TEXT NOT NULL, method TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE model_evaluations (
  id TEXT PRIMARY KEY, model_id TEXT NOT NULL REFERENCES models(id),
  task_id TEXT NOT NULL REFERENCES tasks(id), protocol_id TEXT REFERENCES protocols(id),
  paper_id TEXT REFERENCES papers(id),
  provenance TEXT NOT NULL CHECK(provenance IN ('original-paper','original-release','external-evaluation','released-example')),
  evidence_id TEXT NOT NULL REFERENCES evidence(id), note TEXT NOT NULL
);
CREATE TABLE findings (
  id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks(id),
  evaluation_id TEXT REFERENCES evaluations(id), severity TEXT NOT NULL,
  description TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE field_evidence (
  entity_table TEXT NOT NULL, entity_id TEXT NOT NULL, field TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), note TEXT,
  PRIMARY KEY(entity_table, entity_id, field, evidence_id)
);
-- Completed source review and source availability are different facts. A review
-- cannot make an unpublished split manifest or inaccessible supplement public.
CREATE TABLE source_reviews (
  id TEXT PRIMARY KEY,
  entity_table TEXT NOT NULL CHECK(entity_table IN ('tasks','evaluations','models','papers','protocols')),
  entity_id TEXT NOT NULL, reviewed TEXT NOT NULL, scope TEXT NOT NULL,
  evidence_ids_json TEXT NOT NULL CHECK(json_valid(evidence_ids_json)),
  limitations TEXT NOT NULL, UNIQUE(entity_table,entity_id)
);
CREATE TABLE source_limits (
  id TEXT PRIMARY KEY,
  entity_table TEXT NOT NULL CHECK(entity_table IN ('tasks','evaluations','models','papers','protocols')),
  entity_id TEXT NOT NULL, field TEXT NOT NULL,
  reason TEXT NOT NULL CHECK(reason IN ('not-reported','not-released','not-retrieved','conflicting','access-restricted','not-applicable')),
  detail TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE data_resources (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  title TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('dataset','manifest','evaluation-code','results')),
  host TEXT NOT NULL CHECK(host IN ('huggingface','github','zenodo','other')),
  url TEXT NOT NULL, revision TEXT,
  availability TEXT NOT NULL CHECK(availability IN ('public','restricted','not-released','not-retrieved')),
  evidence_id TEXT NOT NULL REFERENCES evidence(id), notes TEXT NOT NULL
);
CREATE TABLE task_resources (
  task_id TEXT NOT NULL REFERENCES tasks(id), resource_id TEXT NOT NULL REFERENCES data_resources(id),
  relation TEXT NOT NULL CHECK(relation IN ('evaluation-data','upstream-data','split-manifest','identity-manifest','evaluation-code','results')),
  variant_id TEXT REFERENCES variants(id), evidence_id TEXT NOT NULL REFERENCES evidence(id), note TEXT NOT NULL,
  PRIMARY KEY(task_id,resource_id,relation)
);
CREATE TABLE evaluation_resources (
  evaluation_id TEXT NOT NULL REFERENCES evaluations(id), resource_id TEXT NOT NULL REFERENCES data_resources(id),
  relation TEXT NOT NULL CHECK(relation IN ('evaluation-data','upstream-data','split-manifest','identity-manifest','evaluation-code','results')),
  evidence_id TEXT NOT NULL REFERENCES evidence(id), note TEXT NOT NULL,
  PRIMARY KEY(evaluation_id,resource_id,relation)
);
CREATE TABLE task_redirects (
  id TEXT PRIMARY KEY, evaluation_id TEXT NOT NULL REFERENCES evaluations(id),
  replacement_task_id TEXT REFERENCES tasks(id),
  reason TEXT NOT NULL
);
CREATE INDEX task_categories_dimension ON task_categories(category_id, task_id);
CREATE INDEX model_evaluations_task ON model_evaluations(task_id, model_id, provenance);
CREATE INDEX variants_task ON variants(task_id);
CREATE INDEX evidence_source ON evidence(source_id);
CREATE VIEW evaluation_summary AS
  SELECT e.id, e.name, e.status, COUNT(DISTINCT et.task_id) AS catalogued_tasks,
    COUNT(DISTINCT tc.category_id) AS classifications
  FROM evaluations e LEFT JOIN evaluation_tasks et ON et.evaluation_id=e.id
  LEFT JOIN task_categories tc ON tc.task_id=et.task_id GROUP BY e.id;

-- Split definitions and measured separation are distinct. An overlap observation
-- is not, by itself, evidence of an inflated score or a violated source claim.
CREATE TABLE split_strategies (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, split_unit TEXT NOT NULL,
  description TEXT NOT NULL, protection TEXT NOT NULL, limitations TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);
CREATE TABLE split_protocol_strategies (
  protocol_id TEXT NOT NULL REFERENCES protocols(id),
  strategy_id TEXT NOT NULL REFERENCES split_strategies(id),
  note TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id),
  PRIMARY KEY(protocol_id,strategy_id)
);
CREATE TABLE split_audits (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, release_name TEXT NOT NULL,
  evaluation_id TEXT REFERENCES evaluations(id),
  status TEXT NOT NULL CHECK(status IN ('measured','metadata-only','skipped-size','unavailable','not-applicable')),
  finding TEXT NOT NULL CHECK(finding IN ('overlap','no-overlap','limited','not-applicable')),
  scope TEXT NOT NULL, method TEXT NOT NULL, conclusion TEXT NOT NULL,
  limitations TEXT NOT NULL, checked TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), sort_order INTEGER NOT NULL
);
CREATE TABLE split_audit_tasks (
  id TEXT PRIMARY KEY, audit_id TEXT NOT NULL REFERENCES split_audits(id),
  task_id TEXT NOT NULL REFERENCES tasks(id), protocol_id TEXT REFERENCES protocols(id),
  variant_id TEXT REFERENCES variants(id), note TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE split_partitions (
  id TEXT PRIMARY KEY, audit_id TEXT NOT NULL REFERENCES split_audits(id),
  name TEXT NOT NULL, row_count INTEGER CHECK(row_count>=0),
  unique_sequences INTEGER CHECK(unique_sequences>=0),
  row_unit TEXT NOT NULL, detail TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), UNIQUE(audit_id,name)
);
CREATE TABLE split_comparisons (
  id TEXT PRIMARY KEY, audit_id TEXT NOT NULL REFERENCES split_audits(id),
  left_partition_id TEXT NOT NULL REFERENCES split_partitions(id),
  right_partition_id TEXT NOT NULL REFERENCES split_partitions(id),
  overlap_type TEXT NOT NULL, shared_count INTEGER NOT NULL CHECK(shared_count>=0),
  unit TEXT NOT NULL, left_affected INTEGER CHECK(left_affected>=0),
  right_affected INTEGER CHECK(right_affected>=0), note TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE split_audit_files (
  id TEXT PRIMARY KEY, audit_id TEXT NOT NULL REFERENCES split_audits(id),
  partition_id TEXT REFERENCES split_partitions(id), url TEXT NOT NULL,
  revision TEXT, sha256 TEXT, bytes INTEGER CHECK(bytes>=0),
  row_count INTEGER CHECK(row_count>=0), scope TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
CREATE TABLE split_examples (
  id TEXT PRIMARY KEY, comparison_id TEXT NOT NULL REFERENCES split_comparisons(id),
  sequence_sha256 TEXT, sequence_length INTEGER CHECK(sequence_length>=0),
  left_json TEXT NOT NULL CHECK(json_valid(left_json)),
  right_json TEXT NOT NULL CHECK(json_valid(right_json)),
  example_url TEXT NOT NULL, note TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id)
);
