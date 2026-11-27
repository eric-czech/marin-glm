"""Integrity and scientifically material provenance checks for the published catalogue."""
import os
import subprocess
import sys
from pathlib import Path
from collections import Counter
import json
import re
import sqlite3
import unittest
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]

class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=sqlite3.connect(ROOT/'data/catalogue.sqlite')
        cls.db.row_factory=sqlite3.Row
        cls.payload=json.loads((ROOT/'data/site-data.json').read_text())
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
        self.assertEqual(props['aido2-tokenizer']['status'],'not disclosed in technical report')
        self.assertIn('17 listed entries',props['genosm-tokenizer']['value'])
        self.assertIn('256',props['genosm-tokenizer']['value'])
        self.assertIn('128',props['genosm-tokenizer']['value'])
        self.assertIn('local sliding-window',props['aido2-coverage-context']['value'])
        self.assertNotEqual(props['aido2-coverage-context']['evidence_id'],props['aido2-curriculum']['evidence_id'])
    def test_nullable_protocol_fields_have_specific_dispositions(self):
        for field in ('requires_embeddings','fitted_component','selection'):
            missing=self.db.execute(f'''SELECT p.id FROM protocols p LEFT JOIN protocol_field_reviews r
                ON r.protocol_id=p.id AND r.field=? WHERE p.{field} IS NULL AND r.protocol_id IS NULL''',(field,)).fetchall()
            self.assertEqual(missing,[])
        state=self.db.execute("SELECT state,detail FROM protocol_field_reviews WHERE protocol_id='pgb-polya-protocol' AND field='requires_embeddings'").fetchone()
        self.assertEqual(state['state'],'model-dependent')
        self.assertIn('end-to-end',state['detail'])
        self.assertEqual(self.db.execute("SELECT requires_embeddings FROM protocols WHERE id='ceno-enhancer-design-protocol'").fetchone()[0],0)
        row=self.db.execute("SELECT state FROM protocol_field_reviews WHERE protocol_id='nabench-fuente-selection-nabench-random' AND field='requires_embeddings'").fetchone()
        self.assertEqual(row[0],'conflicting')
    def test_selection_rules_are_not_generic_missing_values(self):
        trait=self.db.execute("SELECT selection FROM protocols WHERE id='traitgym-mendelian-probe'").fetchone()[0]
        self.assertIn('GroupKFold',trait)
        self.assertIn('average precision',trait)
        geneb=self.db.execute("SELECT selection FROM protocols WHERE id='geneb-instadeepai-nucleotide-transformer-downstream-tasks-h3-probe'").fetchone()[0]
        self.assertIn('no development-set tuning',geneb)
        mrna=self.db.execute("SELECT selection FROM protocols WHERE id='mrna-rna-loc-fazal-protocol'").fetchone()[0]
        self.assertIn('no classification-penalty search',mrna)
    def test_original_inventory_and_aggregate_use_are_separate(self):
        original={r[0] for r in self.db.execute("SELECT DISTINCT task_id FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper'")}
        inventory={r[0] for r in self.db.execute("SELECT task_id FROM evaluation_tasks WHERE evaluation_id='evo-original'")}
        self.assertEqual(original,inventory)
        self.assertEqual(len(inventory),83)
        self.assertEqual({r[0]for r in self.db.execute("SELECT model_id FROM model_collection_evaluations WHERE evaluation_id='nabench'")},{'evo1','evo2','generator'})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE paper_id='na'").fetchone()[0],0)
    def test_context_variants_and_origin_assignments(self):
        rows=self.db.execute("SELECT id FROM variants WHERE task_id='plantcad2-ft-cross_species_acr_train_on_arabidopsis' AND id LIKE '%-context-%'").fetchall()
        self.assertEqual([r[0]for r in rows],['plantcad2-ft-cross_species_acr_train_on_arabidopsis-context-600'])
        self.assertEqual(self.db.execute("SELECT population_id FROM task_populations WHERE task_id='rnagym-domingo-2018-trna' AND relation='sequence-origin'").fetchone()[0],'yeast')
        self.assertEqual(self.db.execute("SELECT population_id FROM task_populations WHERE task_id='rnagym-janzen-2022-fam21-ribozyme' AND relation='sequence-origin'").fetchone()[0],'synthetic')
        self.assertIsNone(self.db.execute("SELECT id FROM categories WHERE id='output-unresolved'").fetchone())
    def test_nabench_findlay_target_is_directly_adjudicated(self):
        r=json.loads((ROOT/'data/nabench-findlay-target-review.json').read_text())
        self.assertEqual(r['matched_rows'],287)
        self.assertEqual(r['transcript_strand_allele_matches'],287)
        self.assertLess(r['max_absolute_error'],1e-12)
        self.assertEqual({x['source_experiment']for x in r['pairs']},{'X20'})
        self.assertEqual([x['column']for x in r['numerical_column_comparisons']if x['matching_nabench_rows']==287],['d11/lib.loess.r1'])
        self.assertEqual(sum(r['consequences'].values()),287)
        t=self.db.execute("SELECT target FROM tasks WHERE id='nabench-findlay-readout'").fetchone()[0]
        self.assertIn('d11/lib.loess.r1',t)
        self.assertIsNone(self.db.execute("SELECT id FROM source_limits WHERE entity_id='nabench-findlay-readout' AND field='target'").fetchone())
        self.assertIsNone(self.db.execute("SELECT task_id FROM task_categories WHERE task_id='nabench-findlay-readout' AND category_id='rna-engineering'").fetchone())
    def test_nt_gue_pool_identity_preserves_distinct_partitions(self):
        r=json.loads((ROOT/'data/nt-gue-identity-review.json').read_text())
        for mark,n in [('H3',14965),('H4',14601)]:
            x=r['comparisons'][mark]
            self.assertTrue(x['identical_multisets'])
            self.assertEqual(x['shared_rows'],n)
            self.assertEqual(sum(v['shared_sequence_label_rows']for v in x['partition_pairs']),n)
            new='nt-original-'+mark
            self.assertIsNone(self.db.execute('SELECT id FROM tasks WHERE id=?',('gue-'+mark,)).fetchone())
            self.assertEqual(self.db.execute('SELECT replacement_task_id FROM task_redirects WHERE id=?',('gue-'+mark,)).fetchone()[0],new)
            self.assertEqual(self.db.execute("SELECT variant_id FROM protocols WHERE id=?",('deepd-gue-'+mark,)).fetchone()[0],'deepd-gue-'+mark+'-source-cohort')
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
        self.assertEqual({r[0] for r in self.db.execute("SELECT id FROM models WHERE scope='primary'")},
            {'evo1','evo2','ceno','carbon','carbonx','generator','generator2','botanic1',
             'ntv3','deepd','gpnstar','genosm','aido2','plantcad2','spliceai','spliceai2'})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE paper_id IN ('dnachunker','patchdna','genezip','ribospan','mimic')").fetchone()[0],0)
    def test_followup_records_have_artifact_counts_and_specific_source_gaps(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE status='registered'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'rnagym-%' AND status='artifact-audited'").fetchone()[0],70)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id LIKE 'deepd-human-routing-%'").fetchone()[0],6)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM tasks WHERE id='deepd-annotation-human'").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT id FROM tasks WHERE status='panel-pending'").fetchall(),[])
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
        for view in ['species','allSpecies','clade']:
            values=coverage['presentation']['views'][view]
            self.assertEqual(len(values['rows']),self.db.execute(
                'SELECT COUNT(*) FROM coverage_rows WHERE view=?',(view,)).fetchone()[0])
            self.assertEqual({coverage['tasks'][i]['id'] for ids in values['cells'].values() for i in ids},tasks)
            self.assertTrue(all(len(ids)==len(set(ids)) for ids in values['cells'].values()))
            field={'species':'row','allSpecies':'allSpeciesRow','clade':'clade'}[view]
            for cell,indices in values['cells'].items():
                row,feature=cell.split('|',1)
                for i in indices:
                    self.assertTrue(any(m[field]==row and feature in m['features']
                        for m in coverage['tasks'][i]['mappings']),(view,cell,coverage['tasks'][i]['id']))
        self.assertEqual({t['id'] for t in coverage['tasks'] if t['protein']},
            {r[0] for r in self.db.execute("SELECT id FROM tasks WHERE input_description GLOB 'PROTEIN*'")})
        self.assertEqual(len(coverage['presentation']['gaps']),6)
        self.assertEqual(coverage['presentation']['known'],[])
        self.assertEqual(self.db.execute("SELECT id FROM coverage_notes WHERE kind='known'").fetchall(),[])

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
            'genosm-sae-orf':'diagnostic','deepd-maize-routing-cds':'sampled-positions'}
        expected.update({'bend1-gene-finding':'dense-labels','bend1-enhancer-annotation':'dense-labels',
                         'bend1-accessibility':'isolated','bend1-cpg':'isolated'})
        for task,form in expected.items():
            self.assertEqual(records[task]['category_id'],'output-'+form,task)
        self.assertEqual(records['spliceai2-top-transcript']['structure_scope'],'splice-pattern')
        self.assertEqual(records['deepd-human-routing-cds']['status'],'partial')
        self.assertEqual(records['aido2-coverage-rna']['category_id'],'output-signal-profile')
        self.assertIsNone(self.db.execute("SELECT id FROM tasks WHERE id='deepd-annotation-maize'").fetchone())
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
        comparators=self.db.execute("SELECT protocol_id,note FROM model_evaluations WHERE model_id='spliceai' AND paper_id='spliceai2'").fetchall()
        self.assertGreater(len(comparators),0)
        self.assertTrue(all(r['protocol_id'] is None and 'SpliceAI2-specific protocol metadata does not apply' in r['note'] for r in comparators))
        self.assertGreater(self.db.execute("SELECT COUNT(*) FROM model_evaluations WHERE model_id='spliceai2' AND protocol_id IS NOT NULL").fetchone()[0],0)
        self.assertGreater(self.db.execute("SELECT COUNT(DISTINCT task_id) FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper' AND paper_id='evo'").fetchone()[0],0)

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
        feature_ids={f['id'] for f in c['groupedFeatures']}
        self.assertEqual(len(feature_ids),len(c['groupedFeatures']))
        self.assertTrue({'gene-structures','coding-sequence','gene-elements','transcript-structures',
            'splice-elements','regulatory-elements','crispr-arrays'}<=feature_ids)
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
        tasks=self.db.execute("SELECT id FROM tasks WHERE id IN ('ntv3-annotation-exon','ntv3-annotation-gene')").fetchall()
        self.assertEqual({t['id'] for t in tasks},{'ntv3-annotation-exon','ntv3-annotation-gene'})
        for task in tasks:
            rows=self.db.execute('''SELECT m.*,p.name,p.rank FROM coverage_mappings m JOIN populations p
              ON p.id=m.population_id WHERE m.task_id=?''',(task['id'],)).fetchall()
            self.assertEqual(len(rows),17)
            self.assertTrue(all(r['rank']=='species' for r in rows))
            self.assertTrue(all(r['evidence_id']=='ntv3-final-annotation-panel' for r in rows))
            self.assertNotIn('Drosophila melanogaster',{r['name'] for r in rows})
            esch=next(r for r in rows if r['name']=='Eschscholzia californica')
            self.assertEqual(esch['clade_row'],'clade:eudicots')
            evidence=[self.db.execute('SELECT statement FROM evidence WHERE id=?',(eid,)).fetchone()[0] for eid in json.loads(esch['supporting_json'])]
            self.assertTrue(any('201 assemblies' in text for text in evidence))
            self.assertTrue(all(r['population_id'] not in {'human','arabidopsis','fly'} for r in rows))

    def test_display_remainders_are_not_new_biological_clades(self):
        self.assertIsNone(self.db.execute("SELECT 1 FROM populations WHERE id='monocots-other'").fetchone())
        self.assertEqual(self.db.execute("SELECT population_id FROM coverage_nodes WHERE id='monocots-other'").fetchone()[0],'monocots')
        self.assertEqual(self.db.execute("SELECT id FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper' AND paper_id!='evo'").fetchall(),[])

    def test_completed_source_reviews_cover_every_indexed_entity(self):
        evidence={r[0] for r in self.db.execute('SELECT id FROM evidence')}
        for table in ['tasks','evaluations','models','papers','protocols']:
            missing=self.db.execute(f'''SELECT a.id FROM {table} a LEFT JOIN source_reviews r
              ON r.entity_table=? AND r.entity_id=a.id WHERE r.id IS NULL''',(table,)).fetchall()
            self.assertEqual(missing,[],table)
        for row in self.db.execute('SELECT * FROM source_reviews'):
            ids=json.loads(row['evidence_ids_json'])
            self.assertTrue(ids,row['id'])
            self.assertTrue(set(ids)<=evidence,row['id'])
            self.assertTrue(row['scope'].strip(),row['id'])
            self.assertIsNotNone(self.db.execute(
                f'SELECT id FROM {row["entity_table"]} WHERE id=?',(row['entity_id'],)).fetchone(),row['id'])
        self.assertEqual(self.db.execute('''SELECT e.id FROM evaluations e LEFT JOIN evaluation_tasks t
            ON t.evaluation_id=e.id GROUP BY e.id HAVING COUNT(t.task_id)=0''').fetchall(),[])
        statuses={r[0] for r in self.db.execute('SELECT DISTINCT status FROM tasks')}
        self.assertTrue(statuses<={'paper-audited','artifact-audited','source-limited'})
        self.assertFalse(statuses&{'registered','panel-pending'})

    def test_source_limits_are_fields_not_unfinished_audits(self):
        limited=self.db.execute("SELECT id FROM tasks WHERE status='source-limited'").fetchall()
        self.assertTrue(limited)
        allowed={'not-reported','not-released','not-retrieved','conflicting','access-restricted','size-excluded','not-applicable'}
        for task in limited:
            rows=self.db.execute("SELECT * FROM source_limits WHERE entity_table='tasks' AND entity_id=?",(task[0],)).fetchall()
            self.assertTrue(rows,task[0])
            for row in rows:
                self.assertIn(row['reason'],allowed,row['id'])
                self.assertTrue(row['field'].strip(),row['id'])
                self.assertGreater(len(row['detail'].strip()),30,row['id'])
                self.assertNotRegex(row['detail'].lower(),r'\baudit incomplete\b|\bdecomposition pending\b|\bwill audit\b')
                self.assertIsNotNone(self.db.execute('SELECT id FROM evidence WHERE id=?',(row['evidence_id'],)).fetchone())

    def test_evo1_evo2_original_papers_and_external_uses_are_separate(self):
        self.assertEqual(dict(self.db.execute("SELECT id,paper_id FROM models WHERE id IN ('evo1','evo2')")),
            {'evo1':'evo1','evo2':'evo'})
        for model,paper,collection in [('evo1','evo1','evo1-original'),('evo2','evo','evo-original')]:
            uses=self.db.execute("SELECT task_id,paper_id FROM model_evaluations WHERE model_id=? AND provenance='original-paper'",(model,)).fetchall()
            self.assertTrue(uses,model)
            self.assertTrue(all(r['paper_id']==paper for r in uses),model)
            members={r[0] for r in self.db.execute('SELECT task_id FROM evaluation_tasks WHERE evaluation_id=?',(collection,))}
            self.assertTrue({r['task_id'] for r in uses}<=members,model)
        first={r[0] for r in self.db.execute("SELECT task_id FROM model_evaluations WHERE model_id='evo1' AND provenance='original-paper'")}
        second={r[0] for r in self.db.execute("SELECT task_id FROM model_evaluations WHERE model_id='evo2' AND provenance='original-paper'")}
        self.assertTrue({'evo-dms-blat-firnberg','evo-deg','evo-phage-essential'}<=first&second)
        self.assertIn('evo1-crispr-cleavage',first)
        self.assertNotIn('evo1-crispr-cleavage',second)
        self.assertIn('evo-exon-intron',second)
        self.assertNotIn('evo-exon-intron',first)
        external=self.db.execute("SELECT * FROM model_evaluations WHERE model_id='evo2' AND paper_id='ntv3'").fetchall()
        self.assertTrue(external)
        self.assertTrue(all(r['provenance']=='external-evaluation' for r in external))

    def test_source_legend_order_and_family_membership(self):
        sources=self.payload['coverage']['sources']
        self.assertEqual([r['label'] for r in sources[:3]],
            ['Evo 1 / Evo 2','RNAGym / ProteinGym / TraitGym','PlantCAD2 / GeneCAD / Botanic-1'])
        self.assertEqual(set(sources[0]['originalModels']),{'evo1','evo2'})
        self.assertEqual(set(sources[1]['evaluations']),{'rnagym','proteingym','traitgym'})
        self.assertTrue({'plantcad2-zero','plantcad2-ft','genecad','botanic1-evals'}<=set(sources[2]['evaluations']))
        self.assertEqual(sum(bool(s.get('fallback')) for s in sources),1)
        self.assertTrue(sources[-1]['fallback'])
        self.assertEqual(len({s['shape'] for s in sources}),len(sources))

    def test_data_resources_distinguish_data_code_manifests_and_results(self):
        resources={r['id']:dict(r) for r in self.db.execute('SELECT * FROM data_resources')}
        self.assertTrue(resources)
        for row in resources.values():
            parsed=urlparse(row['url'])
            self.assertEqual(parsed.scheme,'https',row['id'])
            if row['host']=='huggingface':
                self.assertEqual(parsed.netloc,'huggingface.co',row['id'])
                self.assertTrue(parsed.path.startswith(('/datasets/','/spaces/')) or row['kind']=='results',row['id'])
            elif row['host']=='github':
                self.assertIn(parsed.netloc,{'github.com','raw.githubusercontent.com'},row['id'])
            elif row['host']=='zenodo':
                self.assertEqual(parsed.netloc,'zenodo.org',row['id'])
            if row['host'] in {'huggingface','github'} and row['availability']=='public':
                self.assertRegex(row['revision'] or '',r'^[0-9a-f]{40}$',row['id'])
                self.assertIn(row['revision'],parsed.path,row['id'])
            if row['kind']=='dataset':
                self.assertNotRegex(parsed.path,r'\.(?:py|ipynb|js|ts|sh)$',row['id'])
        for table in ['task_resources','evaluation_resources']:
            for link in self.db.execute('SELECT * FROM '+table):
                row=resources[link['resource_id']]
                if link['relation']=='evaluation-code':self.assertEqual(row['kind'],'evaluation-code',row['id'])
                if link['relation']=='identity-manifest':self.assertEqual(row['kind'],'manifest',row['id'])
                if link['relation']=='results':self.assertEqual(row['kind'],'results',row['id'])
                if row['kind']=='evaluation-code':self.assertEqual(link['relation'],'evaluation-code',row['id'])

    def test_source_proven_aliases_reuse_targets_and_keep_release_protocols(self):
        names={'human_nontata_promoters','drosophila_enhancers_stark','dummy_mouse_enhancers_ensembl',
            'human_enhancers_cohn','human_enhancers_ensembl','demo_human_or_worm','human_ensembl_regulatory',
            'human_ocr_ensembl','demo_coding_vs_intergenomic_seqs'}
        expected={'geneb-katarinagresova-genomic-benchmarks-'+n.replace('_','-'):'gb-'+n for n in names}
        expected.update({'geneb-leannmlindsey-gue-emp-h3':'nt-original-H3','geneb-leannmlindsey-gue-emp-h4':'nt-original-H4',
            'generator2-recovery':'generator-recovery',
            'botanic1-long-atac':'plantcad2-ft-cell_type_specific_acr'})
        self.assertEqual(len(expected),13)
        redirects={r['id']:r['replacement_task_id'] for r in self.db.execute('SELECT * FROM task_redirects')}
        for old,new in expected.items():
            self.assertEqual(redirects[old],new)
            self.assertIsNone(self.db.execute('SELECT id FROM tasks WHERE id=?',(old,)).fetchone())
            self.assertIsNotNone(self.db.execute('SELECT id FROM tasks WHERE id=?',(new,)).fetchone())
            self.assertGreaterEqual(self.db.execute('SELECT COUNT(*) FROM evaluation_tasks WHERE task_id=?',(new,)).fetchone()[0],2)
            self.assertGreaterEqual(self.db.execute('SELECT COUNT(*) FROM protocols WHERE task_id=?',(new,)).fetchone()[0],2)
            self.assertIsNotNone(self.db.execute("SELECT 1 FROM field_evidence WHERE entity_table='tasks' AND entity_id=? AND field='dataset_identity'",(new,)).fetchone())
        inspection=json.loads((ROOT/'data/existing-benchmark-inspections.json').read_text())['identity_comparisons']
        self.assertEqual({r['dataset'] for r in inspection['GB_GENEB']},names)
        self.assertTrue(all(r['geneb_rows_all_present_with_same_label'] for r in inspection['GB_GENEB']))
        self.assertTrue(all(r['rowwise_sequence_label_equal'] for arm in inspection['GUE_GENEB'].values() for r in arm.values()))

    def test_coverage_export_is_reproducible_across_hash_seeds(self):
        code='import hashlib,json,sys;sys.path.insert(0,"scripts");from coverage_data import export_coverage;d=json.load(open("data/catalogue.json"));print(hashlib.sha256(json.dumps(export_coverage(d),ensure_ascii=False).encode()).hexdigest())'
        hashes=[subprocess.check_output([sys.executable,'-c',code],cwd=ROOT,
            env={**os.environ,'PYTHONHASHSEED':seed},text=True).strip() for seed in ['1','42']]
        self.assertEqual(hashes[0],hashes[1])

    def test_shared_maize_target_keeps_distinct_paper_partitions(self):
        target='plantcad2-ft-cell_type_specific_acr'
        botanic=self.db.execute("SELECT * FROM protocols WHERE id='botanic1-long-atac-protocol'").fetchone()
        self.assertEqual(botanic['task_id'],target)
        self.assertIn('chr9/10',botanic['split_rule'])
        self.assertIsNotNone(botanic['variant_id'])
        native=self.db.execute("SELECT split_rule FROM protocols WHERE task_id=? AND id LIKE 'plantcad2-%'",(target,)).fetchall()
        self.assertTrue(native)
        self.assertTrue(all('chr10' in p[0] and 'chr1–9' in p[0] for p in native))
        self.assertEqual(self.db.execute('SELECT category_id FROM task_outputs WHERE task_id=?',(target,)).fetchone()[0],'output-isolated')

    def test_cag_replacement_is_mixed_but_synonymous_recoding_is_cds(self):
        scopes=dict(self.db.execute("SELECT task_id,scope FROM task_feature_scopes WHERE feature_id='cds' AND task_id IN ('carbon-triplet','carbon-synonymous')"))
        self.assertEqual(scopes,{'carbon-triplet':'mixed','carbon-synonymous':'restricted-target'})
        tasks={r['id']:r for r in self.payload['coverage']['tasks']}
        self.assertNotIn('coding-sequence',tasks['carbon-triplet']['groupedFeatures'])
        self.assertIn('coding-sequence',tasks['carbon-synonymous']['groupedFeatures'])
        rows=json.loads((ROOT/'data/carbon-artifact-inspections.json').read_text())
        cag=next(r for r in rows if r['path']=='motif_human/test-00000-of-00001.parquet')
        self.assertEqual(cag['checks']['patch_exceeds_annotated_cds'],3669)
        synonymous=[r for r in rows if r['path'].startswith(('syn_human/','syn_mouse/'))]
        self.assertEqual(len(synonymous),2)
        self.assertTrue(all(r['checks']['patch_exceeds_annotated_cds']==0 and
            r['checks']['same_amino_acids_in_any_frame']==r['rows'] for r in synonymous))

    def test_plantcad_cell_task_preserves_full_scan_and_real_overlap(self):
        m=json.loads((ROOT/'data/plantcad-cell-artifact-inspections.json').read_text())
        self.assertEqual(len(m['files']),6)
        self.assertEqual(m['distinct_coordinates'],{'train':2517259,'validation':629315,'test':243845})
        self.assertTrue(all(v==0 for v in m['coordinate_intersections'].values()))
        self.assertEqual(m['exact_sequence_intersections'],{'train-validation':69,'train-test':18,'validation-test':6})
        by_split={'train':[],'validation':[],'test':[]}
        for row in m['files']:
            split='validation' if '/validation-' in row['path'] else 'test' if '/test-' in row['path'] else 'train'
            by_split[split].append(row)
            self.assertEqual(row['sequence_lengths'],{'600':row['rows']})
            self.assertEqual(row['label_lengths'],{'92':row['rows']})
            self.assertEqual(row['nonbinary_labels'],0)
        for split in ['train','validation']:
            self.assertEqual({c for row in by_split[split] for c in row['chromosomes']},{'chr'+str(i) for i in range(1,10)})
        self.assertEqual({c for row in by_split['test'] for c in row['chromosomes']},{'chr10'})
        task='plantcad2-ft-cell_type_specific_acr'
        counts={r['split']:r['value'] for r in self.db.execute("SELECT split,value FROM counts WHERE task_id=? AND unit='released windows' AND method='measured'",(task,))}
        self.assertEqual(counts,m['distinct_coordinates'])
        for row in self.db.execute("SELECT split_rule FROM protocols WHERE task_id=? AND id LIKE 'plantcad2-%'",(task,)):
            self.assertIn('chr1–9',row[0]);self.assertIn('chr10',row[0])

    def test_track_links_have_cited_metadata_and_owned_variants(self):
        for table,field,target in [('counts','variant_id','variants'),('counts','protocol_id','protocols'),
            ('protocols','variant_id','variants'),('model_evaluations','protocol_id','protocols'),
            ('task_resources','variant_id','variants'),('task_tracks','variant_id','variants')]:
            self.assertEqual(self.db.execute(f'''SELECT a.task_id FROM {table} a JOIN {target} b
                ON a.{field}=b.id WHERE a.task_id!=b.task_id''').fetchall(),[],(table,field))
        self.assertEqual(self.db.execute('''SELECT t.track_id FROM task_tracks t JOIN variants v ON v.id=t.variant_id
            WHERE v.task_id!=t.task_id''').fetchall(),[])
        unlinked=self.db.execute('''SELECT a.* FROM assay_tracks a LEFT JOIN task_tracks t ON a.id=t.track_id
            WHERE t.track_id IS NULL''').fetchall()
        # These four published PAS output channels are inventory identities.
        # No standalone scored PAS-profile result is asserted by the available
        # Cerberus abstract/release, so do not manufacture evaluation links.
        self.assertEqual({r['id'] for r in unlinked},{
            'cerberus-human-track-8359','cerberus-human-track-8360',
            'cerberus-mouse-track-3100','cerberus-mouse-track-3101'})
        self.assertTrue(all(r['assay']=='pas' for r in unlinked))
        for row in self.db.execute('SELECT * FROM assay_tracks'):
            self.assertTrue(json.loads(row['metadata_json']),row['id'])
            self.assertIsNotNone(self.db.execute('SELECT id FROM evidence WHERE id=?',(row['evidence_id'],)).fetchone())
        actual=dict(self.db.execute('SELECT task_id,COUNT(*) FROM task_tracks GROUP BY task_id'))
        self.assertEqual({r['task_id']:r['tracks'] for r in self.payload['task_track_counts']},actual)
        self.assertNotIn('assay_tracks',self.payload)
        self.assertNotIn('task_tracks',self.payload)

    def test_ntv3_track_inventories_and_missing_result_rows(self):
        m=json.loads((ROOT/'data/ntv3-artifact-inspections.json').read_text())
        def sheet(n):return next(s['rows'] for s in m['sheets'] if s['name'].startswith(f'Supp Table {n} '))
        for prefix,key,rows,source in [('ntv3-native-','file_id',sheet(1),'ntv3-complete-workbook'),
            ('ntv3-benchmark-','file_id',m['benchmark_metadata'],'ntv3-benchmark-metadata'),
            ('ntv3-borzoi-','Track ID',sheet(7),'ntv3-complete-workbook'),
            ('ntv3-ag-','Track ID',sheet(8),'ntv3-complete-workbook')]:
            tracks=self.db.execute('SELECT * FROM assay_tracks WHERE id LIKE ? AND source_id=?',(prefix+'%',source)).fetchall()
            actual={r['source_track_id'] for r in tracks}
            expected={str(r[key]) for r in rows}
            self.assertEqual(actual,expected,prefix)
            self.assertEqual(len(actual),len(rows),prefix)
            source_rows={str(r[key]):r for r in rows}
            for track in tracks:
                metadata=json.loads(track['metadata_json'])
                self.assertEqual(metadata,source_rows[track['source_track_id']],track['id'])
                self.assertEqual(track['assay'],metadata.get('assay',metadata.get('Assay')),track['id'])
        native={r['file_id'] for r in sheet(1)};results={r['file_id'] for r in sheet(5)}
        self.assertEqual((len(native),len(results)),(16262,16260))
        self.assertEqual(native-results,{'SRX11246453','SRX12330305'})
        wheat=[r for r in sheet(1) if r['species']=='Triticum aestivum']
        self.assertEqual(Counter(r['assay'] for r in wheat),{'RNA-seq':762,'Histone ChIP-seq':14})
        histone=self.db.execute('''SELECT COUNT(*) FROM task_tracks t JOIN assay_tracks a ON a.id=t.track_id
            JOIN populations p ON p.id=a.population_id WHERE t.task_id='ntv3-tracks-histone' AND p.name='Triticum aestivum' ''').fetchone()[0]
        self.assertEqual(histone,14)
        self.assertEqual(self.db.execute('''SELECT COUNT(*) FROM task_tracks t JOIN assay_tracks a ON a.id=t.track_id
            JOIN populations p ON p.id=a.population_id WHERE t.task_id='ntv3-tracks-atac' AND p.name='Triticum aestivum' ''').fetchone()[0],0)

    def test_reference_rna_origin_is_not_the_experimental_host(self):
        expected={
            'rnagym-soo-2021-ribozyme':'taxon-5911',
            'evo-ncrna-zhang':'taxon-671',
            'rnagym-peri-2022-ribozyme':'taxon-418699',
            'rnagym-kobori-2015-ribozyme-j12':'synthetic',
            'rnagym-kobori-2018-ribozyme':'synthetic',
            'rnagym-tome-2014-nelfe-aptamer':'synthetic',
            'rnagym-roberts-2023-hdv-ribozyme':'taxon-12475',
            'rnagym-roberts-2023-hp-ribozyme':'taxon-31504',
            'rnagym-roberts-2023-tw-ribozyme':'rice',
            'rnagym-zhang-2020-cpeb3-ribozyme':'human'}
        for task,pop in expected.items():
            actual={r[0] for r in self.db.execute(
                "SELECT population_id FROM task_populations WHERE task_id=? AND relation='sequence-origin'",(task,))}
            self.assertEqual(actual,{pop},task)
            self.assertEqual(self.db.execute(
                'SELECT COUNT(*) FROM coverage_mappings WHERE task_id=? AND population_id IS NULL',(task,)).fetchone()[0],0)
        parents=dict(self.db.execute('SELECT id,parent_id FROM populations'))
        self.assertEqual(parents['taxon-12475'],'ribozyviria')
        self.assertEqual(parents['taxon-31504'],'rna-satellites')
        for task in ['rnagym-kobori-2015-ribozyme-tw','rnagym-roberts-2023-hh-ribozyme']:
            limit=self.db.execute("SELECT detail FROM source_limits WHERE entity_id=? AND field='reference_organism'",(task,)).fetchone()[0]
            self.assertIn('reference',limit)

    def test_no_placeholder_outputs_or_unreviewed_retrieval_states(self):
        self.assertEqual(self.db.execute("SELECT id FROM tasks WHERE output_description='Target prediction'").fetchall(),[])
        self.assertEqual(self.db.execute("SELECT id FROM source_limits WHERE reason='not-retrieved'").fetchall(),[])
        self.assertEqual(self.db.execute("SELECT id FROM data_resources WHERE availability='not-retrieved'").fetchall(),[])

    def test_profile_gene_vector_and_linked_structure_targets_remain_distinct(self):
        outputs={r['task_id']:dict(r) for r in self.db.execute('SELECT * FROM task_outputs')}
        for tid in ['ntv3-tracks-rna','ntv3-ag-rna','ntv3-benchmark-ribo','ntv3-benchmark-eclip']:
            self.assertEqual(outputs[tid]['category_id'],'output-signal-profile')
            self.assertEqual(outputs[tid]['position_axis'],'contiguous')
            self.assertIsNone(self.db.execute("SELECT 1 FROM task_categories WHERE task_id=? AND category_id='dense-annotation'",(tid,)).fetchone())
        self.assertEqual(outputs['ntv3-danio']['category_id'],'output-isolated')
        self.assertEqual(outputs['ntv3-annotation-exon']['category_id'],'output-element-set')
        self.assertEqual(outputs['ntv3-annotation-gene']['structure_scope'],'coding-chain')
        self.assertEqual(outputs['spliceai2-top-transcript']['structure_scope'],'splice-pattern')
        self.assertEqual(outputs['ntv3-whole-blood-response']['category_id'],'output-diagnostic')
        self.assertIsNone(self.db.execute("SELECT id FROM tasks WHERE id='ntv3-design-plant'").fetchone())
        for tid,feature in [('ntv3-design-plant-promoter','promoter'),('ntv3-design-plant-enhancer','enhancer')]:
            self.assertEqual(outputs[tid]['category_id'],'output-sequence')
            self.assertIsNotNone(self.db.execute('SELECT 1 FROM task_categories WHERE task_id=? AND category_id=?',(tid,feature)).fetchone())

if __name__=='__main__':unittest.main()
