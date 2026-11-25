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
CREATE TABLE tasks (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, dataset_name TEXT NOT NULL,
  target TEXT NOT NULL, description TEXT NOT NULL, task_type TEXT NOT NULL,
  label_basis TEXT NOT NULL, status TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id), limitations TEXT,
  input_description TEXT NOT NULL, output_description TEXT NOT NULL
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
    (dimension IN ('application','capability','region')),
  name TEXT NOT NULL, definition TEXT NOT NULL, accommodation TEXT
);
CREATE TABLE task_categories (
  task_id TEXT NOT NULL REFERENCES tasks(id), category_id TEXT NOT NULL REFERENCES categories(id),
  relation TEXT NOT NULL, rationale TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES evidence(id),
  attribution TEXT NOT NULL CHECK (attribution IN ('source','curatorial')),
  PRIMARY KEY (task_id, category_id, relation)
);
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
CREATE INDEX task_categories_dimension ON task_categories(category_id, task_id);
CREATE INDEX model_evaluations_task ON model_evaluations(task_id, model_id, provenance);
CREATE INDEX variants_task ON variants(task_id);
CREATE INDEX evidence_source ON evidence(source_id);
CREATE VIEW evaluation_summary AS
  SELECT e.id, e.name, e.status, COUNT(DISTINCT et.task_id) AS catalogued_tasks,
    COUNT(DISTINCT tc.category_id) AS classifications
  FROM evaluations e LEFT JOIN evaluation_tasks et ON et.evaluation_id=e.id
  LEFT JOIN task_categories tc ON tc.task_id=et.task_id GROUP BY e.id;
