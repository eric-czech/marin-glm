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
    def test_plantcad_species_variants_do_not_duplicate_task_units(self):
        released={r[0] for r in self.db.execute("SELECT task_id FROM evaluation_tasks WHERE evaluation_id='plantcad2-zero'")}
        self.assertEqual(len(released),14)  # 12 released targets + potato + pretraining diagnostic
        self.assertIn('plantcad2-potato-gerp',released)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'plantcad2-%_recovery'").fetchone()[0],4)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evaluation_tasks WHERE evaluation_id='plantcad2-ft'").fetchone()[0],9)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE model_id='evo2' AND paper_id LIKE 'plantcad2%' AND provenance='original-paper'").fetchone()[0],0)
    def test_genecad_is_an_adaptation_with_versioned_training(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM models WHERE id='genecad'").fetchone()[0],0)
        legacy=self.db.execute("SELECT adaptation,requires_embeddings FROM protocols WHERE id='genecad-legacy-cds-frozen'").fetchone()
        self.assertEqual(tuple(legacy),('frozen backbone; trained annotation head',1))
        current=self.db.execute("SELECT adaptation FROM protocols WHERE id='genecad-cds-transcript-strict'").fetchone()[0]
        self.assertEqual(current,'full fine-tune')
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id LIKE 'genecad-cds-%' AND category_id IN ('utr5','utr3')").fetchone()[0],0)
        marmoset=self.db.execute("SELECT COUNT(*) FROM task_populations WHERE task_id LIKE 'genecad-cds-%' AND population_id='marmoset'").fetchone()[0]
        self.assertEqual(marmoset,6)
    def test_plantcad_translation_and_motif_targets_are_distinct(self):
        task=self.db.execute("SELECT task_type FROM tasks WHERE id='plantcad2-tis_recovery'").fetchone()[0]
        self.assertEqual(task,'sequence reconstruction')
        label=self.db.execute("SELECT target FROM tasks WHERE id='plantcad2-ft-cross_species_leaf_absolute_translation'").fetchone()[0]
        self.assertIn('Ribo-seq',label)
        region=self.db.execute("SELECT category_id FROM task_categories WHERE task_id='plantcad2-tis_recovery' AND category_id='translation-start'").fetchone()
        self.assertIsNotNone(region)
        self.assertIn('1 +',label)
        rows=json.loads((ROOT/'data/plantcad-artifact-inspections.json').read_text())
        regressions=[r for r in rows if r['path'].startswith('cross_species_leaf_absolute_translation/')]
        self.assertEqual(len(regressions),3)
        self.assertTrue(all(r['label_transform_checks']['log10_1_plus_tpm_max_abs_error']<1e-12 for r in regressions))
    def test_site_embeds_database_export(self):
        html=(ROOT/'index.html').read_text()
        raw=html.split('<script id="catalogue" type="application/json">',1)[1].split('</script>',1)[0]
        data=json.loads(raw)
        self.assertEqual(len(data['tasks']),self.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        self.assertIn('gpnstar',{m['id'] for m in data['models']})
        self.assertNotIn('__CATALOGUE_JSON__',html)
    def test_projects_require_dedicated_purpose_and_independent_adoption(self):
        projects=self.db.execute('SELECT * FROM project_summary').fetchall()
        self.assertTrue(projects)
        for p in projects:
            self.assertGreaterEqual(p['independent_groups'],2,p['id'])
            r=self.db.execute('SELECT * FROM project_reviews WHERE id=?',(p['review_id'],)).fetchone()
            self.assertEqual((r['decision'],r['dedicated']),('qualified',1))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM projects WHERE id IN ('geneb','omnigenbench','gfmbench','guanine')").fetchone()[0],0)
    def test_every_collection_has_an_explicit_project_review(self):
        self.assertEqual(self.db.execute('''SELECT e.id FROM evaluations e
          LEFT JOIN project_review_evaluations r ON e.id=r.evaluation_id
          WHERE r.review_id IS NULL''').fetchall(),[])
        for id in ('gue','nt-original','nt-revised','pgb','gene-mteb'):
            r=self.db.execute('''SELECT r.decision FROM project_reviews r
              JOIN project_review_evaluations e ON e.review_id=r.id WHERE e.evaluation_id=?''',(id,)).fetchone()
            self.assertEqual(r[0],'outside-definition',id)
    def test_adoption_is_version_subset_and_modality_specific(self):
        links={tuple(r) for r in self.db.execute("SELECT evaluation_id,relation FROM project_review_evaluations WHERE review_id='bend'")}
        self.assertEqual(links,{('bend-original','defines'),('bend','successor-release')})
        original=self.db.execute("SELECT scope FROM project_adoptions WHERE id='adoption-dart-evo'").fetchone()[0]
        self.assertIn('1,2,5 only',original)
        self.assertEqual(self.db.execute("SELECT independence FROM project_adoptions WHERE id='adoption-trait-gpn'").fetchone()[0],'shared-authorship')
        self.assertIn('Protein-only',self.db.execute("SELECT scope FROM project_adoptions WHERE id='adoption-dgeb-protberta'").fetchone()[0])
        # Adoption papers do not manufacture primary models or model-use claims.
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM models WHERE scope='primary'").fetchone()[0],15)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE paper_id IN ('dnachunker','patchdna','genezip','ribospan','mimic')").fetchone()[0],0)
    def test_followup_records_have_artifact_counts_and_specific_source_gaps(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE status='registered'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'rnagym-%' AND status='artifact-audited'").fetchone()[0],70)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'deepd-human-routing-%'").fetchone()[0],6)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id='deepd-annotation-human'").fetchone()[0],0)
        pending=self.db.execute("SELECT id FROM tasks WHERE status='panel-pending'").fetchall()
        self.assertEqual(len(pending),8)
        for t in pending:
            self.assertTrue(self.db.execute("SELECT 1 FROM field_evidence WHERE entity_table='tasks' AND entity_id=? AND field='limitations'",(t[0],)).fetchone())
        summaries=json.loads((ROOT/'data/geneb-artifact-inspections.json').read_text())
        self.assertEqual(len(summaries),200)
        self.assertEqual(sum(x['rows'] for x in summaries),3393004)
        self.assertEqual(sum(x['split']=='test' and x['train_test_exact_sequence_overlap']>0 for x in summaries),25)
        self.assertIn('401',self.db.execute("SELECT limitations FROM tasks WHERE id='carbonx-frontier'").fetchone()[0])
    def test_rnagym_metric_semantics_and_split_counts(self):
        self.assertEqual({r[0] for r in self.db.execute("SELECT metric_id FROM protocol_metrics WHERE protocol_id='rnagym-andreasson-2020-ribozyme-rnagym'")},{'abs-spearman','symmetric-auroc','abs-mcc'})
        rows=json.loads((ROOT/'data/rnagym-artifact-inspections.json').read_text())
        assays=[x for x in rows if x['archive']=='fitness_processed_assays']
        self.assertEqual(len(assays),70)
        self.assertEqual(sum(x['rows'] for x in assays),1117406)
        self.assertEqual(len([x for x in rows if x['archive']=='fitness_CV_splits']),124)
        self.assertTrue(any(x.get('train_validation_exact_sequence_overlap',0)>0 for x in rows))
    def test_capability_parent_membership_and_genecad_dense_outputs(self):
        self.assertEqual(self.db.execute("""SELECT task_id FROM task_categories c
          WHERE category_id IN ('conditional-generation','unconditional-generation') AND NOT EXISTS
          (SELECT 1 FROM task_categories p WHERE p.task_id=c.task_id AND p.category_id='generation')""").fetchall(),[])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id LIKE 'genecad-%' AND category_id='dense-annotation'").fetchone()[0],14)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id='botanic1-atac-counts' AND category_id='dense-annotation'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id LIKE 'geneb-leannmlindsey-gue-mouse-%' AND category_id='enhancer'").fetchone()[0],0)
    def test_project_paper_links_cite_their_own_source(self):
        self.assertEqual(self.db.execute('''SELECT r.review_id,r.paper_id FROM project_review_papers r
          JOIN papers p ON p.id=r.paper_id JOIN evidence e ON e.id=r.evidence_id
          WHERE r.relation!='adoption-evidence' AND e.source_id!=p.source_id''').fetchall(),[])
        self.assertEqual(self.db.execute('''SELECT r.evaluation_id FROM project_review_evaluations r
          JOIN evaluations e ON e.id=r.evaluation_id
          WHERE r.relation='successor-release' AND r.evidence_id!=e.evidence_id''').fetchall(),[])

    def test_coverage_uses_canonical_tasks_and_preserves_every_view(self):
        payload=json.loads((ROOT/'data/site-data.json').read_text())
        coverage=payload['coverage']
        tasks={r['id'] for r in payload['tasks']}
        self.assertEqual({t['id'] for t in coverage['tasks']},tasks)
        for view,expected_rows,expected_marks in [('species',48,1005),('allSpecies',87,1322),('clade',32,934)]:
            values=coverage['presentation']['views'][view]
            self.assertEqual(len(values['rows']),expected_rows)
            self.assertEqual(sum(len(ids) for ids in values['cells'].values()),expected_marks)
            self.assertEqual({coverage['tasks'][i]['id'] for ids in values['cells'].values() for i in ids},tasks)
            self.assertTrue(all(len(ids)==len(set(ids)) for ids in values['cells'].values()))
        self.assertEqual(sum(t['protein'] for t in coverage['tasks']),14)
        self.assertEqual(len(coverage['presentation']['gaps']),6)
        self.assertEqual(len(coverage['presentation']['known']),6)

    def test_output_review_distinguishes_components_structures_and_diagnostics(self):
        records={r['task_id']:dict(r) for r in self.db.execute('SELECT * FROM task_outputs')}
        self.assertEqual(set(records),{r[0] for r in self.db.execute('SELECT id FROM tasks')})
        expected={
            'evo-exon-intron':'isolated','botanic1-regions':'isolated','botanic1-tis':'isolated',
            'botanic1-atac-counts':'isolated','botanic1-atac-profile':'signal-profile',
            'plantcad2-ft-cell_type_specific_acr':'isolated','plantcad2-donor_recovery':'sequence',
            'ntv3-seiplant':'isolated','ntv3-tracks-rna':'signal-profile',
            'bgcs-cds':'dense-labels','genecad-cds-base':'dense-labels',
            'genecad-cds-exon':'element-set','genecad-cds-chain':'linked-structure',
            'genecad-cds-transcript':'linked-structure','genecad-busco':'diagnostic',
            'spliceai-sites-coding':'dense-labels','spliceai-exon-inclusion':'isolated',
            'spliceai2-top-transcript':'linked-structure','spliceai2-gtag-detection':'isolated',
            'spliceai2-tissue-junction':'pairwise','deepd-human-routing-cds':'sampled-positions',
            'genosm-sae-orf':'sampled-positions','deepd-annotation-maize':'unresolved'}
        expected.update({'bend1-gene-finding':'dense-labels','bend1-enhancer-annotation':'dense-labels',
                         'bend1-accessibility':'isolated','bend1-cpg':'isolated'})
        for task,form in expected.items():
            self.assertEqual(records[task]['category_id'],'output-'+form,task)
        self.assertEqual(records['spliceai2-top-transcript']['structure_scope'],'splice-pattern')
        self.assertEqual(records['deepd-human-routing-cds']['status'],'partial')
        self.assertEqual(records['aido2-coverage-rna']['status'],'partial')
        for task in ['evo-exon-intron','botanic1-regions','botanic1-conservation','botanic1-tis','botanic1-tts','genecad-busco']:
            self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id=? AND category_id='dense-annotation'",(task,)).fetchone()[0],0,task)
        self.assertIn('coding phase',self.db.execute("SELECT limitations FROM tasks WHERE id='genecad-cds-chain'").fetchone()[0])

    def test_splicing_models_protocols_and_heldout_units(self):
        self.assertEqual(self.db.execute("SELECT status FROM papers WHERE id='spliceai'").fetchone()[0],'journal')
        self.assertEqual(self.db.execute("SELECT status FROM papers WHERE id='spliceai2'").fetchone()[0],'preprint')
        self.assertEqual(self.db.execute("SELECT value FROM counts WHERE task_id='spliceai2-top-transcript'").fetchone()[0],352)
        source=self.db.execute("SELECT statement FROM evidence WHERE id='spliceai2-top-transcript-method'").fetchone()[0]
        for term in ['human-only','10 bp','validation','TSS/TES','every isoform']:self.assertIn(term.lower(),source.lower())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_populations WHERE task_id LIKE 'spliceai%' AND population_id!='human'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM counts WHERE task_id='spliceai-sites-coding' AND value=14289 AND unit='test donor–acceptor pairs'").fetchone()[0],1)
        # A native dense model's variant benchmark is not a new dense annotation task.
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_outputs WHERE task_id LIKE 'spliceai2-%' AND category_id='output-dense-labels'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper'").fetchone()[0],42)
        self.assertEqual(self.db.execute("SELECT COUNT(DISTINCT task_id) FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper'").fetchone()[0],41)

    def test_opensplice_reuses_target_and_preserves_protocol_counts(self):
        task=self.db.execute("SELECT task_id,variant_id FROM evaluation_tasks WHERE evaluation_id='spliceai2-evals' AND task_id='bend-opensplice'").fetchone()
        self.assertEqual(tuple(task),('bend-opensplice','spliceai2-opensplice-snv'))
        self.assertEqual(self.db.execute("SELECT value FROM counts WHERE task_id='bend-opensplice' AND variant_id='spliceai2-opensplice-snv' AND unit='SNV assay measurements'").fetchone()[0],283121)
        p=self.db.execute("SELECT adaptation,notes FROM protocols WHERE id='spliceai2-bend-opensplice-protocol'").fetchone()
        self.assertIn('no new readout',p['adaptation'])
        self.assertIn('not BEND macro-gene',p['notes'])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'spliceai2-opensplice%'").fetchone()[0],0)

    def test_grouped_features_require_joint_structure_evidence(self):
        c=json.loads((ROOT/'data/site-data.json').read_text())['coverage']
        tasks={t['id']:t for t in c['tasks']}
        self.assertEqual(len(c['groupedFeatures']),14)
        self.assertEqual(tasks['spliceai2-top-transcript']['groupedFeatures'],['transcript-structures'])
        self.assertEqual(tasks['genecad-cds-transcript']['groupedFeatures'],['gene-structures'])
        for tid in ['evo-exon-intron','spliceai-sites-coding','genecad-cds-base','genecad-busco','genecad-boundary-donor']:
            self.assertFalse(set(tasks[tid]['groupedFeatures'])&{'gene-structures','transcript-structures'},tid)
        for t in tasks.values():
            self.assertTrue(t['groupedFeatures'],t['id'])
            self.assertEqual(len(t['groupedFeatures']),len(set(t['groupedFeatures'])))

    def test_cds_specific_targets_survive_compaction_without_mixed_panels(self):
        data=json.loads((ROOT/'data/site-data.json').read_text())
        tasks={t['id']:t for t in data['coverage']['tasks']}
        for tid in ['evo-dms-blat-firnberg','carbon-clinvar-coding','genosm-amr','bgcs-cds','genecad-cds-base','genecad-cds-exon']:
            self.assertIn('coding-sequence',tasks[tid]['groupedFeatures'],tid)
        for tid in ['genosm-gene-class','bend1-gene-finding','aido2-human-elements','plantcad2-potato-gerp','evo-gen-bacterial-genome','mrna-go-bp']:
            self.assertNotIn('coding-sequence',tasks[tid]['groupedFeatures'],tid)
        for tid in ['genecad-cds-chain','genecad-cds-transcript','ntv3-annotation-gene']:
            self.assertEqual(tasks[tid]['groupedFeatures'],['gene-structures'])
            self.assertIsNotNone(self.db.execute("SELECT 1 FROM task_feature_scopes WHERE task_id=? AND feature_id='cds' AND scope='restricted-target'",(tid,)).fetchone())

    def test_bend_original_artifact_counts_and_scoring_units_remain_distinct(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evaluation_tasks WHERE evaluation_id='bend-original'").fetchone()[0],7)
        s=json.loads((ROOT/'data/bend-output-artifact-inspections.json').read_text())
        self.assertEqual((s[0]['rows'],s[0]['unique_ids']),(5977,5974))
        self.assertEqual(s[0]['split_counts'],{'train':4783,'test':597,'valid':597})
        self.assertTrue(s[0]['duplicates_within_train_only'])
        self.assertFalse(any(s[0]['row_id_overlap_between_splits'].values()))
        self.assertEqual(s[1]['label_hdf5']['vector_lengths'],{'782':285})
        self.assertEqual(s[1]['label_hdf5']['values'],{'0.0':220185,'1.0':2685})
        values={tuple(r) for r in self.db.execute("SELECT method,value FROM counts WHERE task_id='bend1-gene-finding' AND split='train'")}
        self.assertTrue({('reported',4780),('measured',4783)}<=values)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM task_categories WHERE task_id='bend1-gene-finding' AND category_id='structured-annotation'").fetchone()[0],0)

    def test_coverage_assignments_have_cited_origins_not_host_inference(self):
        self.assertEqual(self.db.execute('''SELECT t.id FROM tasks t LEFT JOIN coverage_mappings m
          ON m.task_id=t.id WHERE m.id IS NULL''').fetchall(),[])
        for row in self.db.execute('SELECT * FROM coverage_mappings'):
            for eid in json.loads(row['supporting_json']):
                self.assertIsNotNone(self.db.execute('SELECT 1 FROM evidence WHERE id=?',(eid,)).fetchone())
            if row['basis']=='metadata gap':self.assertIsNone(row['population_id'])
        targets=self.db.execute("SELECT COUNT(*) FROM coverage_mappings WHERE basis='protein-target' AND population_id IS NOT NULL").fetchone()[0]
        self.assertGreater(targets,30)

    def test_ntv3_coverage_is_the_scored_heldout_panel(self):
        tasks=self.db.execute("SELECT id FROM tasks WHERE name IN ('Exact CDS-exon structures','Exact whole-gene structures')").fetchall()
        self.assertEqual(len(tasks),2)
        for task in tasks:
            rows=self.db.execute('''SELECT m.*,p.name,p.rank FROM coverage_mappings m JOIN populations p
              ON p.id=m.population_id WHERE m.task_id=?''',(task['id'],)).fetchall()
            self.assertEqual(len(rows),17)
            self.assertTrue(all(r['basis']=='paper-test-panel' and r['rank']=='species' for r in rows))
            self.assertNotIn('Drosophila melanogaster',{r['name'] for r in rows})
            esch=next(r for r in rows if r['name']=='Eschscholzia californica')
            evidence=[self.db.execute('SELECT statement FROM evidence WHERE id=?',(eid,)).fetchone()[0] for eid in json.loads(esch['supporting_json'])]
            self.assertTrue(any('Ranunculales' in text and 'EUDICOTS' in text for text in evidence))

    def test_display_remainders_are_not_new_biological_clades(self):
        self.assertIsNone(self.db.execute("SELECT 1 FROM populations WHERE id='monocots-other'").fetchone())
        self.assertEqual(self.db.execute("SELECT population_id FROM coverage_nodes WHERE id='monocots-other'").fetchone()[0],'monocots')
        self.assertEqual(self.db.execute("SELECT COUNT(DISTINCT task_id) FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper'").fetchone()[0],41)

if __name__=='__main__':unittest.main()
