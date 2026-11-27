"""Release-level overlap units, evidence, denominators and example identities."""
import hashlib
import json
import re
import sqlite3
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=sqlite3.connect(ROOT/'data/catalogue.sqlite');cls.db.row_factory=sqlite3.Row
        cls.report=json.loads((ROOT/'data/split-inspections.json').read_text())
    @classmethod
    def tearDownClass(cls):cls.db.close()
    def comparison(self,aid,left,right,kind):
        return self.db.execute('''SELECT c.*,l.name AS lname,r.name AS rname FROM split_comparisons c
          JOIN split_partitions l ON l.id=c.left_partition_id JOIN split_partitions r ON r.id=c.right_partition_id
          WHERE c.audit_id=? AND l.name=? AND r.name=? AND c.overlap_type=?''',(aid,left,right,kind)).fetchone()
    def test_plant_coordinates_spans_and_sequences_are_distinct(self):
        self.assertEqual(self.comparison('split-plantcad-cell','train','test','coordinate-id')['shared_count'],0)
        self.assertEqual(self.comparison('split-plantcad-cell','train','test','interval')['shared_count'],0)
        self.assertEqual(self.comparison('split-plantcad-cell','train','test','exact-sequence')['shared_count'],18)
        x=self.comparison('split-plantcad-cell','train','validation','interval')
        self.assertEqual((x['shared_count'],x['left_affected'],x['right_affected']),(4531,4477,4347))
        p=self.db.execute("SELECT * FROM split_partitions WHERE audit_id='split-plantcad-cell' AND name='test'").fetchone()
        self.assertEqual((p['row_count'],p['unique_sequences']),(243845,243844))
    def test_bend_pairs_are_not_affected_windows(self):
        x=self.comparison('split-bend-gene-finding','train','test','interval')
        self.assertEqual((x['shared_count'],x['left_affected'],x['right_affected']),(126,126,109))
        self.assertEqual(self.comparison('split-bend-gene-finding','train','test','coordinate-id')['shared_count'],0)
    def test_mrna_mapped_groups_and_exact_strings(self):
        rows=self.db.execute("SELECT overlap_type,shared_count FROM split_comparisons WHERE audit_id='split-mrna-mrl-sugimoto'").fetchall()
        values={}
        for r in rows:values.setdefault(r['overlap_type'],[]).append(r['shared_count'])
        self.assertEqual(sorted(values['exact-sequence']),[99,160,181])
        self.assertEqual(values['homology-group'],[0,0,0])
        self.assertEqual(sorted(values['gene-id']),[263,435,489])
    def test_excluded_scopes_have_no_imputed_zero(self):
        bad=self.db.execute('''SELECT a.id FROM split_audits a JOIN split_comparisons c ON c.audit_id=a.id
          WHERE a.status IN ('skipped-size','unavailable','not-applicable')''').fetchall()
        self.assertEqual(bad,[])
        self.assertGreater(self.db.execute("SELECT COUNT(*) FROM split_audits WHERE status='skipped-size'").fetchone()[0],2)
    def test_examples_fixed_lines_and_identity(self):
        lines=[json.loads(s) for s in (ROOT/'data/split-examples.jsonl').read_text().splitlines()]
        self.assertEqual(lines,self.report['examples'])
        self.assertEqual(len(lines),46)
        rc=lambda s:s.upper().translate(str.maketrans('ACGTN','TGCAN'))[::-1]
        for i,x in enumerate(lines,1):
            e=self.db.execute('SELECT * FROM split_examples WHERE id=?',(x['example_id'],)).fetchone()
            self.assertIsNotNone(e)
            self.assertRegex(e['example_url'],r'/blob/[0-9a-f]{40}/data/split-examples.jsonl#L'+str(i)+r'$')
            if x.get('sequence') is not None:
                self.assertEqual(hashlib.sha256(x['sequence'].encode()).hexdigest(),x['sequence_sha256'])
                self.assertEqual(len(x['sequence']),x['sequence_length'])
            if x['kind']=='reverse-complement-only':
                self.assertEqual(rc(x['sequence_left']),x['sequence_right'].upper())
                self.assertNotEqual(x['sequence_left'],x['sequence_right'])
            if x['kind']=='interval':
                l,r=x['left'],x['right'];self.assertEqual(l['chr'],r['chr'])
                self.assertEqual(min(l['end'],r['end'])-max(l['start'],r['start']),x['overlap_bp'])
                self.assertGreater(x['overlap_bp'],0)
    def test_live_plant_rows_match_pinned_coordinates(self):
        rows=[r for x in self.report['examples'] if x['case']=='plantcad-cell' for r in [x['left'],x['right']] ]
        checked={r['viewer_verification']['api_url']:r for r in rows if 'viewer_verification' in r}
        self.assertEqual(len(checked),20)
        self.assertTrue(all(r['viewer_verification']['coordinate_match'] for r in checked.values()))
    def test_every_comparison_has_inspection_evidence_and_compatible_units(self):
        for c in self.db.execute('''SELECT c.*,e.basis,l.row_count AS ln,r.row_count AS rn,
          l.unique_sequences AS lu,r.unique_sequences AS ru FROM split_comparisons c
          JOIN evidence e ON c.evidence_id=e.id JOIN split_partitions l ON l.id=c.left_partition_id
          JOIN split_partitions r ON r.id=c.right_partition_id'''):
            self.assertEqual(c['basis'],'data',c['id'])
            for k,n in [('left_affected','ln'),('right_affected','rn')]:
                if c[k] is not None:self.assertLessEqual(c[k],c[n],c['id'])
            if c['overlap_type']=='exact-sequence':
                for k in ['lu','ru']:
                    if c[k] is not None:self.assertLessEqual(c['shared_count'],c[k],c['id'])
    def test_archive_members_do_not_overwrite_each_other(self):
        for aid in ['split-rnagym-min-similarity-pitt-2010-ribozyme','split-dnafoundation-enhancers-enhancer']:
            fs=self.db.execute('SELECT * FROM split_audit_files WHERE audit_id=?',(aid,)).fetchall()
            self.assertEqual(len(fs),2,aid)
            self.assertEqual(len({r['sha256'] for r in fs}),2)
            self.assertEqual(len({r['partition_id'] for r in fs}),2)
    def test_native_geneb_and_reshuffled_release_kept_separate(self):
        geneb=self.db.execute("SELECT COUNT(*) FROM split_audits WHERE release_name='GENEB'").fetchone()[0]
        dna=self.db.execute("SELECT COUNT(*) FROM split_audits WHERE release_name='DNA Foundation processed release'").fetchone()[0]
        self.assertEqual((geneb,dna),(100,57))
        self.assertEqual(self.comparison('split-geneb-instadeepai-nucleotide-transformer-downstream-tasks-enhancers','train','test','exact-sequence')['shared_count'],100)
    def test_ntv3_species_checks_link_species_variants(self):
        rows=self.db.execute("SELECT a.id,l.variant_id FROM split_audits a JOIN split_audit_tasks l ON l.audit_id=a.id WHERE a.id LIKE 'split-ntv3-intervals-%'").fetchall()
        self.assertEqual(len({r['id'] for r in rows}),11)
        self.assertTrue(all(r['variant_id'] for r in rows))
        self.assertTrue(all(r['variant_id'].endswith('-human') for r in rows if r['id'].endswith('-human')))
    def test_enhancer_lengths_and_label_disagreement_are_retained(self):
        x=self.report['cases']['selected-katarinagresova_Genomic_Benchmarks_human_enhancers_ensembl']['sequence_length_audit']
        self.assertEqual(sum(r['shared_unique_strings'] for r in x['strata'].values()),9502)
        self.assertEqual(sum(r['held_out_unique_strings'] for r in x['strata'].values()),29469)
        self.assertEqual(x['shared_strings_with_single_conflicting_labels'],2)
        self.assertEqual(x['strata']['200+']['shared_unique_strings'],6643)
    def test_no_new_bulk_downloads(self):
        self.assertEqual(self.report['new_dataset_file_download_bytes'],0)
        self.assertEqual(self.report['large_release_metadata']['generator-recovery']['total_parquet_bytes'],5754874772)

if __name__=='__main__':unittest.main()
