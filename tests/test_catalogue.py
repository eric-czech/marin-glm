"""Integrity and scientifically material provenance checks for the published catalogue."""
from pathlib import Path
import json
import sqlite3
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=sqlite3.connect(ROOT/'data/catalogue.sqlite')
        cls.db.row_factory=sqlite3.Row
    @classmethod
    def tearDownClass(cls):cls.db.close()
    def test_foreign_keys(self):
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertEqual(self.db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_all_tasks_have_cited_membership(self):
        self.assertEqual(self.db.execute('SELECT t.id FROM tasks t LEFT JOIN evaluation_tasks e ON e.task_id=t.id WHERE e.task_id IS NULL').fetchall(),[])
    def test_original_evo_attribution_requires_its_paper(self):
        self.assertEqual(self.db.execute("SELECT id FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper' AND paper_id!='evo'").fetchall(),[])
        actual={r[0] for r in self.db.execute("SELECT DISTINCT m.task_id FROM model_evaluations m JOIN evaluation_tasks e ON e.task_id=m.task_id WHERE m.model_id='evo2' AND m.provenance='original-paper' AND e.evaluation_id='dart'")}
        self.assertEqual(actual,{'dart-ccre','dart-motif','dart-caqtl','dart-dsqtl'})
    def test_generator2_does_not_imply_evo_fine_tuning(self):
        self.assertEqual(self.db.execute("SELECT m.id FROM model_evaluations m JOIN protocols p ON p.id=m.protocol_id WHERE m.model_id='evo2' AND m.paper_id='generator2' AND p.adaptation='full fine-tune'").fetchall(),[])
    def test_gpn_reuses_traitgym_but_not_evo_clinvar_cohort(self):
        ids={r[0] for r in self.db.execute("SELECT task_id FROM evaluation_tasks WHERE evaluation_id='gpn-evals'")}
        self.assertTrue({'traitgym-mendelian','traitgym-complex','gpn-clinvar','gpn-rare-arabidopsis'}<=ids)
        self.assertNotIn('evo-clinvar',ids)
        taxa={r[0] for r in self.db.execute("SELECT population_id FROM task_populations WHERE task_id LIKE 'gpn-rare-%'")}
        self.assertEqual(taxa,{'human','mouse','fly','worm','chicken','arabidopsis'})
    def test_revised_nt_is_human_and_multiclass_is_not_multilabel(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'nt-revised-%'").fetchone()[0],18)
        self.assertEqual(self.db.execute("SELECT DISTINCT population_id FROM task_populations WHERE task_id LIKE 'nt-revised-%'").fetchall()[0][0],'human')
        self.assertEqual(self.db.execute("SELECT task_type FROM tasks WHERE id='nt-revised-enhancers_types'").fetchone()[0],'multiclass classification')
    def test_genome_rows_are_not_gene_counts(self):
        rows=self.db.execute("SELECT value,unit FROM counts WHERE task_id='bacbench-essential' AND method='measured' AND split='test'").fetchall()
        self.assertIn((9,'genomes'),[tuple(r) for r in rows])
        self.assertIn((27666,'gene labels'),[tuple(r) for r in rows])
    def test_every_measured_count_has_data_evidence(self):
        self.assertEqual(self.db.execute("SELECT c.id FROM counts c JOIN evidence e ON c.evidence_id=e.id WHERE c.method='measured' AND e.basis!='data'").fetchall(),[])
    def test_pgb_hosts_are_distinct_from_sequence_origin(self):
        rows=self.db.execute("SELECT population_id,relation FROM task_populations WHERE task_id='pgb-promoter-strength'").fetchall()
        values={tuple(r) for r in rows}
        self.assertTrue({('maize','sequence-origin'),('maize','assay-host'),('tobacco','assay-host'),('sorghum','sequence-origin')}<=values)
    def test_traitgym_region_tags_come_from_observed_rows(self):
        rows=self.db.execute("SELECT category_id FROM task_categories WHERE task_id='traitgym-mendelian' AND relation='subset'").fetchall()
        self.assertTrue({'utr5','utr3','promoter','enhancer','intron'}<={r[0] for r in rows})
        positive=self.db.execute("SELECT value FROM counts WHERE task_id='traitgym-mendelian' AND split='positive' AND method='measured'").fetchone()[0]
        self.assertEqual(positive,338)
    def test_new_model_context_and_tokenization_evidence(self):
        scopes=dict(self.db.execute("SELECT id,scope FROM models WHERE id IN ('aido2','genosm')").fetchall())
        self.assertEqual(scopes,{'aido2':'primary','genosm':'primary'})
        props={r['id']:r for r in self.db.execute("SELECT * FROM model_properties WHERE model_id IN ('aido2','genosm')")}
        self.assertEqual(props['aido2-tokenizer']['status'],'unresolved')
        self.assertIn('17 listed entries',props['genosm-tokenizer']['value'])
        self.assertIn('256',props['genosm-tokenizer']['value'])
        self.assertIn('128',props['genosm-tokenizer']['value'])
        self.assertIn('local sliding-window',props['aido2-coverage-context']['value'])
        self.assertNotEqual(props['aido2-coverage-context']['evidence_id'],props['aido2-curriculum']['evidence_id'])
    def test_genosm_reuses_assays_and_retains_source_cohort(self):
        rows=self.db.execute("SELECT task_id FROM evaluation_tasks WHERE evaluation_id='genosm-evals' AND task_id LIKE 'rnagym-%'").fetchall()
        self.assertEqual(len(rows),13)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'genosm-phenotype-%'").fetchone()[0],5)
        rows=self.db.execute("SELECT value,variant_id FROM counts WHERE task_id='bacbench-essential' AND split='test' AND unit='genomes'").fetchall()
        self.assertIn((11,'genosm-essential-cohort'),[tuple(r) for r in rows])
        self.assertTrue(any(r['value']==9 and r['variant_id']!='genosm-essential-cohort' for r in rows))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE paper_id IN ('aido2','genosm') AND model_id='evo2' AND provenance='original-paper'").fetchone()[0],0)
    def test_site_embeds_database_export(self):
        html=(ROOT/'index.html').read_text()
        raw=html.split('<script id="catalogue" type="application/json">',1)[1].split('</script>',1)[0]
        data=json.loads(raw)
        self.assertEqual(len(data['tasks']),self.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        self.assertIn('gpnstar',{m['id'] for m in data['models']})
        self.assertNotIn('__CATALOGUE_JSON__',html)

if __name__=='__main__':unittest.main()
