"""Final source reviews of established evaluation releases.

The committed inspection manifest records measurements made on 2026-11-27. A completed
source review records what the publication/release establishes; it is not a
claim to have reproduced biological experiments or every historical model run.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DATE = '2026-11-27'

INSPECTIONS = json.loads((ROOT / 'data/existing-benchmark-inspections.json').read_text())
DGEB_FILES = INSPECTIONS['facts']['DGEB_FILES']
GUANINE_FILES = INSPECTIONS['facts']['GUANINE_FILES']
DGEB_OVERLAPS = INSPECTIONS['facts']['DGEB_OVERLAPS']
GUANINE_OVERLAPS = INSPECTIONS['facts']['GUANINE_OVERLAPS']
BACBENCH_FILES = INSPECTIONS['facts']['BACBENCH_FILES']
BGC_FILTERED = INSPECTIONS['facts']['BGC_FILTERED']
BGCS_STATS = INSPECTIONS['facts']['BGCS_STATS']
NT_GUE_FILES = INSPECTIONS['facts']['NT_GUE_FILES']
NT_SPLICE_MNEMONICS = INSPECTIONS['facts']['NT_SPLICE_MNEMONICS']
BEND2_FILES = INSPECTIONS['facts']['BEND2_FILES']
NT_NAMED_TAXA = INSPECTIONS['facts']['NT_NAMED_TAXA']
PROTEINGYM_RNAGYM = INSPECTIONS['facts']['PROTEINGYM_RNAGYM']
EVO_PROTEINGYM_IDS = INSPECTIONS['facts']['EVO_PROTEINGYM_IDS']
PROTEINGYM_CANONICAL = INSPECTIONS['facts']['PROTEINGYM_CANONICAL']

def populate(d):
    audit = Audit(d)
    audit.dgeb()
    audit.guanine()
    audit.dart()
    audit.bacbench()
    audit.bend2()
    audit.bgc()
    audit.sequence_benchmarks()
    audit.generator()
    audit.ceno()
    audit.plantcad()
    audit.existing_measured()
    audit.final_details()
    return d


class Audit:
    def __init__(self, d):
        self.d = d
        for table in ('source_reviews', 'source_limits'):
            d.setdefault(table, [])

    def put(self, table, row, keys=('id',)):
        old = next((r for r in self.d[table] if all(r.get(k) == row.get(k) for k in keys)), None)
        if old is None:
            self.d[table].append(row)
        else:
            old.update(row)
        return row

    def row(self, table, id):
        return next(r for r in self.d[table] if r.get('id') == id)

    def ev(self, id, source, locator, statement, basis='paper', url=None):
        s = self.row('sources', source)
        self.put('evidence', dict(id=id, source_id=source, locator=locator, statement=statement,
            basis=basis, url=url or s['url'], inspected=DATE))
        return id

    def code(self, id, repo, rev, file, statement, start=1, end=None, local=None, kind='repository-file'):
        url=f'https://github.com/{repo}/blob/{rev}/{file}'
        path=ROOT/local/file if local else None
        digest=INSPECTIONS['source_file_sha256'].get(str(path.relative_to(ROOT))) if path else None
        source='final-'+id+'-source'
        self.put('sources', dict(id=source, title=repo+' / '+file, kind=kind, url=url, version=rev,
            retrieved=DATE, sha256=digest, local_path=str(path.relative_to(ROOT)) if path and path.exists() else None,
            availability='available', notes='Pinned release source inspected during final source review.'))
        return self.ev('final-'+id, source, file, statement, 'code', url+f'#L{start}'+(f'-L{end}' if end else ''))

    def data(self, id, spec, statement):
        url=f'https://huggingface.co/datasets/{spec["repo"]}/blob/{spec["revision"]}/{spec["file"]}'
        source='final-'+id+'-file'
        path='research/artifacts/final-audit/existing-hf/'+spec['repo'].replace('/','--')+'/'+spec['file']
        self.put('sources', dict(id=source,title=spec['repo']+' / '+spec['file'],kind='dataset-file',url=url,
            version=spec['revision'],retrieved=DATE,sha256=spec['sha256'],local_path=path,
            availability='available',notes='Complete released file scanned; row counts are not independent biological observations.'))
        return self.ev('final-'+id,source,'Complete file scan; schema, rows, labels and identifiers',statement,'data')

    def field(self, table, id, field, eid, note):
        self.put('field_evidence', dict(entity_table=table, entity_id=id,field=field,evidence_id=eid,note=note),
            ('entity_table','entity_id','field','evidence_id'))

    def limit(self, table, id, field, reason, detail, eid):
        self.put('source_limits', dict(id='final-'+table+'-'+id+'-'+field.replace(':','-'),entity_table=table,
            entity_id=id,field=field,reason=reason,detail=detail,evidence_id=eid))

    def review(self, table, id, scope, eids, limitations=''):
        eids=list(dict.fromkeys(x for x in eids if x))
        self.put('source_reviews',dict(id='final-'+table+'-'+id,entity_table=table,entity_id=id,
            reviewed=DATE,scope=scope,evidence_ids_json=json.dumps(eids),limitations=limitations),('entity_table','entity_id'))

    def metric(self, pid, mid, agg, eid, primary=1):
        self.put('protocol_metrics',dict(protocol_id=pid,metric_id=mid,aggregation=agg,is_primary=primary,evidence_id=eid),('protocol_id','metric_id'))

    def count(self, tid, value, unit, split, eid, vid=None, pid=None, suffix=None, qualifier='Complete release file scan; no model-specific missingness filter.'):
        id='final-'+tid+'-'+(suffix or split.replace('/','-').replace(' ','-'))
        self.put('counts',dict(id=id,task_id=tid,value=value,unit=unit,split=split,evidence_id=eid,
            qualifier=qualifier,method='measured',variant_id=vid,protocol_id=pid))

    def finding(self,id,tid,evaluation,description,eid):
        self.put('findings',dict(id='final-'+id,task_id=tid,evaluation_id=evaluation,severity='discrepancy',description=description,evidence_id=eid))

    def members(self, collection):
        ids={x['task_id'] for x in self.d['evaluation_tasks'] if x['evaluation_id']==collection}
        return [t for t in self.d['tasks'] if t['id'] in ids]

    def family(self, collection, scope, eids, limitations=''):
        self.review('evaluations',collection,scope,eids,limitations)
        for t in self.members(collection):
            if not any(r['entity_table']=='tasks' and r['entity_id']==t['id'] for r in self.d['source_reviews']):
                self.review('tasks',t['id'],scope,[t['evidence_id']]+eids,limitations)

    def dgeb(self):
        repo='TattaBio/DGEB'; rev='1b187e607e278a34ba7338b8b43747c57add4134'; local='research/artifacts/final-audit/existing-dgeb'
        scorer=self.code('dgeb-scorers',repo,rev,'dgeb/evaluators.py',
            'Classification: LogisticRegression(max_iter=1000, random_state=42), macro-F1. MIBiG: five-neighbour cosine KNN over binarized comma-separated classes, macro-F1. Clustering: MiniBatchKMeans with cluster count equal to number of reference labels, V-measure on the same cohort. EDS: Pearson correlation with cosine, Manhattan and Euclidean distances; top_corr is the maximum on the evaluation cohort. Pair classification top_ap maximizes AP over the compared distances; it is not validation-selected.',75,590,local)
        utils=self.code('dgeb-pairing',repo,rev,'dgeb/eval_utils.py',
            'Operon scoring pairs consecutive embeddings and uses labels[:-1], so N released gene rows yield N−1 assessed adjacent pairs. MIBiG mean-pools all embeddings with the same Entry ID.',61,105,local)
        eds=self.code('dgeb-eds-id',repo,rev,'dgeb/tasks/eds_tasks.py',
            'The evaluator maps Entry to its final row index using a dictionary before joining phylogenetic-distance pairs. Repeated identical Entry IDs therefore do not create extra leaves.',22,43,local)
        retrieval=self.code('dgeb-retrieval-contract',repo,rev,'dgeb/tasks/retrieval_tasks.py',
            'The protein corpus is the first dataset train split, queries are its test split, and fuzz_ratio in the second dataset supplies graded annotation-name relevance. The pinned code calls map on the full qrels Dataset Dict, whose released test split lacks query_id/corpus_id/fuzz_ratio; this is a source interface inconsistency, not a reproduced score.',22,45,local)
        grouped={}
        for v in self.d['variants']:
            if v['task_id'].startswith('dgeb-') and '/datasets/' in (v.get('notes') or ''):
                repo_id=v['notes'].split('/datasets/')[1].split('/tree/')[0]
                grouped.setdefault(v['task_id'],[]).append((repo_id,v))
        for tid,items in grouped.items():
            eids=[];summaries=[]
            for repo_id,v in items:
                for s in [s for s in DGEB_FILES if s['repo']==repo_id]:
                    part=s['file'].split('/')[-1].split('-')[0]
                    desc=f"Pinned file has {s['rows']:,} rows; columns {', '.join(s['columns'])}."
                    if s['unique_ids'] is not None:desc+=f" {s['unique_ids']:,} distinct Entry identifiers."
                    if s['labels'] is not None:desc+=f" {s['labels']} observed Label values."
                    if s['lengths']:desc+=f" Sequence lengths {s['lengths'][0]}–{s['lengths'][1]}."
                    if repo_id.endswith('_qrels'):desc+=' Qrels train rows are relevance pairs; qrels test rows repeat the query-sequence table and are not relevance pairs.'
                    overlap=DGEB_OVERLAPS.get(repo_id.replace('/','--'),{}).get('exact_sequence_train_test_overlap')
                    if overlap is not None:desc+=f' Exact Sequence-string overlap between released train/test is {overlap}; no reverse-complement or homology comparison is implied.'
                    eid=self.data('dgeb-'+repo_id.split('/')[-1]+'-'+part,s,desc);eids.append(eid)
                    unit='phylogenetic distance pairs' if 'distance' in s['columns'] else 'graded relevance pairs' if 'query_id' in s['columns'] else 'protein pairs' if 'Seq1' in s['columns'] else 'released sequence rows'
                    split=repo_id.split('/')[-1]+' / '+part
                    self.count(tid,s['rows'],unit,split,eid,v['id'],suffix=repo_id.split('/')[-1]+'-'+part)
                    if s['unique_ids'] is not None and s['unique_ids'] != s['rows']:
                        self.count(tid,s['unique_ids'],'distinct Entry identifiers',split,eid,v['id'],suffix=repo_id.split('/')[-1]+'-'+part+'-ids')
                    summaries.append(desc)
            t=self.row('tasks',tid)
            t['limitations']='Complete pinned task files, source schema and evaluator reviewed. Species-level taxonomic distributions are not supplied in many sequence tables; identifiers alone are not treated as a complete organism manifest. Exact-string comparisons do not establish homology-disjoint evaluation.'
            t['status']='artifact-audited'
            p=self.row('protocols',tid+'-protocol'); p['source_evidence_id']=scorer
            if 'classification' in tid:
                p.update(split_rule='Released train/test sequence collections; no development partition is loaded by this evaluator. No chromosome-, species- or homology-disjoint split is established by the file schema.',
                    fitted_component='Five-neighbour cosine KNN after Entry-level mean pooling' if 'MIBIG' in tid else 'Logistic regression, max_iter=1000, random_state=42',selection='Fixed evaluator hyperparameters. Reported best-layer comparisons require separate layer-selection provenance.')
                self.metric(p['id'],'f1','Macro-average F1; MIBiG binarizes comma-separated class labels.',scorer)
            elif 'clustering' in tid:
                p.update(adaptation='unsupervised clustering of frozen embeddings',fitted_component='MiniBatchKMeans, k equal to reference class count, batch_size=500',split_rule='Whole released HF train collection is fitted and scored as one clustering cohort. No downstream train/test split.',selection='No held-out cluster or label tuning specified.')
                self.metric(p['id'],'v-measure','All released sequences in the clustering cohort',scorer)
            elif 'phylogeny' in tid:
                p.update(adaptation='zero-shot embedding-distance comparison',fitted_component='None',split_rule='All released sequence leaves and their supplied evolutionary-distance pairs; HF train names a fixed evaluation collection. Pairs share leaves and are not independent held-out genes.',selection='top_corr is the retrospective maximum of Pearson correlation for three embedding distances.',notes='No fitted evolutionary-distance head; source tree/label generation is inherited. '+('FeFe has 429 sequence rows but 384 unique Entry IDs; repeated IDs have identical sequences and final-row lookup selects one.' if 'fefe' in tid else ''))
                self.metric(p['id'],'pearson','Maximum Pearson over cosine, Manhattan and Euclidean embedding distances (top_corr).',scorer)
            elif 'operonic_pair' in tid:
                p.update(adaptation='zero-shot embedding-distance comparison',fitted_component='None',split_rule='Consecutive genes within the one released reference-ordered collection; N genes yield N−1 assessed adjacent pairs. No readout-training split.',selection='top_ap is the retrospective maximum over compared similarity/distance scores.')
                rows=next(s['rows'] for s in DGEB_FILES if s['repo']==items[0][0]);self.count(tid,rows-1,'adjacent gene pairs','scored adjacent pairs',utils,pid=p['id'],suffix='adjacent-pairs',qualifier='Derived exactly from released row count and paired_dataset slicing; benchmark model scores were not regenerated.')
                self.row('counts','final-'+tid+'-adjacent-pairs')['method']='derived'
                self.field('counts','final-'+tid+'-adjacent-pairs','value',eids[0],'N−1 adjacent pairs derived from the complete measured N-row sequence table and the cited paired_dataset slice.')
                self.metric(p['id'],'ap','Maximum average precision over declared embedding distance/similarity variants.',scorer)
            elif 'bigene' in tid:
                p.update(adaptation='zero-shot nearest-neighbour matching',fitted_component='None',split_rule='Whole released paired-sequence collection is a query/gallery evaluation cohort; matching gold is row alignment, not downstream supervised fitting.',selection='Fixed cosine matching; top-k=50 for ModAC, top-k=1 for BacArch.')
            elif 'retrieval' in tid:
                p.update(adaptation='zero-shot protein retrieval',fitted_component='None',split_rule='Bacterial corpus is HF train; archaeal/eukaryotic query proteins are HF test. The qrels HF train table supplies relevance links; this is corpus/query separation, not classifier training.',selection='MAP@5 over query proteins; relevance derives from fuzzy protein-annotation matching, not direct experimental functional equivalence.',notes='Pinned qrels test schema is inconsistent with mapping over all Dataset Dict splits; see linked source discrepancy.')
                self.limit('tasks',tid,'executable_release','conflicting','Pinned retrieval code maps all qrels splits but qrels/test is a query sequence table without required relevance keys. Source interface inspected; no model benchmark rerun claimed.',retrieval)
            self.field('protocols',p['id'],'split_rule',utils if 'operonic_pair' in tid else scorer,'Evaluator semantics checked independently of nominal HF split names.')
            self.review('tasks',tid,'All pinned task Parquets scanned, task loader and scorer reviewed; sequence rows, target units, metrics and adaptation distinguished.',eids+[scorer,utils,eds,retrieval],t['limitations'])
            self.limit('tasks',tid,'taxon_by_split','not-reported','Many pinned sequence tables expose only accession, Sequence and target; no complete species/rank manifest is released with those rows.',eids[0])
        self.finding('dgeb-mibig-overlap','dgeb-MIBIG_dna_classification','dgeb',
            'Pinned MIBiG DNA splits share one exact Sequence string; protein splits share 279 distinct exact protein Sequence strings. BGC Entry identifiers remain distinct targets and protein vectors are pooled within Entry. Exact-string recurrence is not a full homology or pretraining audit.','final-dgeb-mibig_classification_dna-test')
        self.finding('dgeb-fefe-ids','dgeb-fefe_phylogeny','dgeb',
            'The FeFe sequence table has 429 rows but only 384 unique Entry IDs; 45 repeated IDs all have identical sequences. Its 73,536 distance rows equal 384 choose 2. The evaluator selects the final sequence row for each ID, so 429 must not be reported as the number of tree leaves.','final-dgeb-fefe_phylogeny_sequences-train')
        self.finding('dgeb-qrels-schema',None,'dgeb',
            'Both pinned retrieval qrels repositories include train relevance-pair tables and test query-sequence tables. The pinned evaluator maps qrels_dict_init over the full Dataset Dict, although the test split lacks query_id, corpus_id and fuzz_ratio. This source code/data interface conflict is retained explicitly.',retrieval)
        self.review('evaluations','dgeb','All 22 task definitions and 41 pinned task/data Parquets reviewed, including auxiliary distances and relevance tables. Counts distinguish sequences, BGCs, pairs and query/corpus units.',[scorer,utils,eds,retrieval]+['final-dgeb-'+s['repo'].split('/')[-1]+'-'+s['file'].split('/')[-1].split('-')[0] for s in DGEB_FILES],
            'Complete rank distributions are absent from several tables; retrieval qrels loader mismatch and exact sequence recurrence are documented, not treated as validated executions.')

    def guanine(self):
        repo='ni-lab/guanine';rev='c0a2e6b3dc88f8e2197083efb021d55f8a37befa';local='research/artifacts/final-audit/existing-guanine'
        scorer=self.code('guanine-scoring',repo,rev,'docs/scoring.rst',
            'Benchmark scoring uses signed Spearman correlation; most test labels are withheld, development results accompany submissions, tied predictions are checked by jitter. This differs from AUROC even on binary labels.',1,100,local)
        probe=self.ev('final-guanine-probe','project-guanine-update','Methods / feature extraction and linear evaluation',
            'GUANinE v1.1 extracts frozen model features and fits linear probes, selecting regularization on development data before test inference. ClinVar has no training set; calibration uses its development cohort for models that cannot zero-shot. The published Ridge/logistic regularization parameter names are retained as reported, rather than silently corrected.')
        for slug in ['dnase_propensity','ccre_propensity','cons30','cons100','gpra_c','gpra_d','cadd_snv','clinvar_snv']:
            tid='guanine-'+slug; t=self.row('tasks',tid);p=self.row('protocols',tid+'-protocol');eids=[]
            for s in [s for s in GUANINE_FILES if s['repo']=='guanine/'+slug]:
                part=s['file'].split('/')[-2];target=s['file'].split('/')[-1].split('.')[0]
                desc=f"Complete {s['file']} has {s['rows']:,} rows; columns {', '.join(s['columns'])}."
                if s['chromosomes']:desc+=' Chromosomes: '+', '.join(s['chromosomes'])+'.'
                desc+=' Test labels are absent.' if part=='test' and 'y' not in s['columns'] else ' Numerical y labels are public.'
                if s['lengths']:desc+=f" Released seq strings are uniformly {s['lengths'][0]}–{s['lengths'][1]} nt (80 randomized promoter bases plus the supplied scaffold)."
                eid=self.data('guanine-'+slug+'-'+part+'-'+target,s,desc);eids.append(eid)
                vid=tid+'-released-'+target if slug=='ccre_propensity' and target not in ['1per','dev','test'] else tid+'-released'
                self.put('variants',dict(id=vid,task_id=tid,name='Released '+('marker '+target if vid.endswith(target) else slug)+' files',evidence_id=eid,context='Public train/few-shot/development/test metadata; target availability differs by task.',input_length='110 nt; 80 random +30 scaffold' if slug.startswith('gpra') else 'Model-selected reference context around supplied coordinate',dataset_revision=s['revision'],target_count=1,target_unit='scalar ordinal/binary target per row',notes='https://huggingface.co/datasets/guanine/'+slug+'/tree/'+s['revision']))
                self.count(tid,s['rows'],'sequence rows' if slug.startswith('gpra') else 'coordinate / variant rows',part+(' / '+target if slug=='ccre_propensity' and target not in ['1per','dev','test'] else ''),eid,vid,suffix=part+'-'+target)
                self.field('tasks',tid,'counts',eid,'Full released file scan; main training archives were not required for few-shot protocol review.')
            if slug in ['dnase_propensity','ccre_propensity','cadd_snv']:
                split='Development chr 21; test chr 22; inspected 1% training rows use other chromosomes. Full main training archive was not downloaded; partition identity is established for the inspected few-shot/development/test artifacts.'
            elif slug in ['cons30','cons100']:
                split='Random sequence/window partitions, not chromosome holdouts. Inspected 1% training, development and test coordinates span the same chromosome set, including chr 21/22. Exact coordinate keys are disjoint across the inspected partitions; interval-overlap and sequence homology were not tested.'
            elif slug.startswith('gpra'):
                split='Random synthetic-promoter partitions; no reference chromosome coordinates. Complete 1% training/development/test files have no exact seq-string overlap. Public test file omits y.'
            else:
                split='No training split. Test derives from the CADD ClinVar evaluation cohort intersected with August 2025 ClinVar; development uses other newly released ClinVar variants. Both span shared chromosomes; exact variant keys are disjoint, not chromosome-held-out.'
            p.update(adaptation='frozen linear probe / source-specific zero-shot variants',requires_embeddings=None,model_interface='Frozen model representations or declared model score, depending on model/task',fitted_component='Development-selected regularized linear readout; none for direct zero-shot scores',selection='Select regularization on development; ClinVar calibration uses development because no training set is released.',split_rule=split,split_unit='synthetic promoter' if slug.startswith('gpra') else 'variant / source-date cohort' if slug=='clinvar_snv' else 'reference coordinate / chromosome' if slug in ['dnase_propensity','ccre_propensity','cadd_snv'] else 'reference coordinate / random window',source_evidence_id=probe,notes='A 1% few-shot panel is a subset of training, not an independent benchmark test. Scoring uses signed Spearman; target bins remain ordinal rather than a continuous assay scale.')
            self.metric(p['id'],'spearman','Signed Spearman correlation with task y labels; cCRE includes four marker-specific readouts.',scorer)
            if slug.startswith('gpra'):t['input_description']='Released 110-nt DNA sequence: 80 randomized promoter bases and 30 nt scaffold; models may add external context according to their adapter.'
            if slug=='dnase_propensity':t.update(task_type='ordinal regression',output_description='Scalar ordinal accessibility propensity, integer 0–4; tissue identity is integrated out.')
            if slug in ['cons30','cons100']:t.update(task_type='ordinal regression',output_description='Scalar binned mean phyloP conservation, integer 0–24; not per-base profile prediction.')
            if slug=='ccre_propensity':t.update(task_type='ordinal multitask regression',output_description='Separate scalar 0–4 propensities for DNase, CTCF, H3K27ac, H3K4me3, represented in linked marker variants; rows identify task, not genome position outputs.')
            if slug=='clinvar_snv':t['limitations']='No training split exists. The public test BED contains 5,982 pathogenic and 5,982 benign noncoding SNVs; matching controls TSS distance, consequence and maximum group allele frequency. This is a controlled ClinVar subset enriched for splicing mechanisms, not general clinical pathogenicity.'
            elif slug=='cadd_snv':t['limitations']='Derived-versus-simulated labels are evolutionary proxies. The inspected release has a balanced 760,328-row 1% training panel and 1,033,654-row development panel; test has 1,036,402 unlabelled variants. The task page does not publish a complete construction recipe; full training rows and source simulation were not independently regenerated.'
            else:t['limitations']='Complete few-shot/development/test files and source scoring specification reviewed. Most test labels are withheld; full training archives, external reference sequence extraction and original assay/conservation-score generation were not independently reproduced. Context length is adapter-specific.'
            t['status']='artifact-audited'
            for f in ['input_description','output_description','limitations']:self.field('tasks',tid,f,eids[0] if f!='limitations' else probe,'Final source review; released schemas and publication treated separately.')
            self.review('tasks',tid,'Task page, full v1.0/v1.1 methods, scoring guide and complete public few-shot/development/test files reviewed.',[probe,scorer]+eids,t['limitations'])
            if slug!='clinvar_snv':self.limit('tasks',tid,'full_training_recount','not-retrieved','Complete 1% training, development and test artifacts were scanned. Multi-hundred-MB full training archive was not downloaded; no measured full-training count is claimed.',eids[0])
            if slug!='clinvar_snv':self.limit('tasks',tid,'test_labels','not-released','Pinned public test file omits target y. Test row counts, inputs and partitions are measured; labels/score reproduction are unavailable from the public release.',eids[-1])
            self.field('protocols',p['id'],'split_rule',eids[0],'Observed chromosome membership checked for each released partition; publication supplies random/date construction intent.')
        self.finding('guanine-gpra-input','guanine-gpra_c','guanine','GPRA assay randomization spans 80 bases, but released seq values are 110 nt because 30 nt of scaffold are included. Previous 80 bp input description conflated randomized region with released model input.','final-guanine-gpra_c-1per-1per')
        self.finding('guanine-clinvar-labels','guanine-clinvar_snv','guanine','The general scoring guide says most test labels are private, but pinned ClinVar test includes public y labels and 11,964 rows. It has no training set and uses source/date cohort separation, not a chromosome holdout.','final-guanine-clinvar_snv-test-test')
        self.review('evaluations','guanine','All eight task definitions, v1.0/v1.1 methods and scoring guide checked; 35 complete public few-shot/development/test files scanned with row counts, labels, input lengths, chromosome membership and exact-key intersections.',[scorer,probe]+['final-guanine-'+s['repo'].split('/')[-1]+'-'+s['file'].split('/')[-2]+'-'+s['file'].split('/')[-1].split('.')[0] for s in GUANINE_FILES],
            'Most public tests omit y; full training archives and original experimental/raw conservation processing are outside the inspected artifacts. cCRE markers are linked variants within the shared ordinal propensity task.')
    def dart(self):
        methods=self.ev('final-dart-methods','dart-paper','AppendixC.1–C.4,D.1–D.3,E.1–E.5',
            'DART distinguishes likelihood comparison, embedding-distance comparison, frozen CNN probes and LoRA fine-tuning. Trained tasks use validation chr 6/21, test chr 5/10/14/18/20/22, others train; select lowest validation loss. Frozen probe repeats token embeddings by spanned nucleotides, projects to 32 channels, two width 8 convolutions with 32 filters, sum pooling and linear output. LoRA rank 8, alpha 16, dropout 0.05 adapts linear/convolutional layers and classifier. Accessibility is a scalar log-read-count target over the central 1000 bp of 2114 bp input; ChromBPNet profile head is not compared to DNALMs. Quantitative QTL effect correlations use allele differences from sequence-to-activity models trained on reference DNase targets, not a QTL-label-trained model.')
        targets=self.ev('final-dart-targets','dart-paper','AppendixC.2–C.4;TablesS2,S4;E.2–E.5',
            'Motifs:1,443 HOCOMOCOv12 motifs, 200 positive/control pairs per motif; embedding setting adds matched neutral sequences. Cell identity: five cell lines, DESeq2 logFC>1 and adjusted p<0.001, unique active cell type; zero-shot clustering uses top 5000 per cell, k=50 and 100 runs, scored AMI. Full differential peak counts are 45,184/49,208/33,948/50,783/37,623. caQTL source 219,382 variants is reduced to 6,821 significant+77,999 controls in paper; dsQTL source 28,309 reduced to 560 significant+26,813 controls. These are publication-specific counts before model-missingness and code-specific filters.')
        # Resolve the already registered pinned revision; do not guess a new branch head.
        rev=self.row('sources','src-dart-definition')['version']
        filters=self.code('dart-counterfactual-filters','kundajelab/DART-Eval',rev,
            'src/dnalm_bench/task_2_5_single/experiments/task_5_variant_effect_prediction/variant_tasks.py',
            'African zero-shot filters IsUsed and in_peaks; Yoruba uses var.isused with positive 1/control −1. Probed African counts filter IsUsed plus pval thresholds, with allele2−allele1 for quantitative logFC. Cohort identity differs by scoring path; effect sign and filtering must be declared per protocol.',73,170,'research/artifacts/final-audit/existing-dart')
        shared='Trained readout: validation chr 6/21, test chr 5/10/14/18/20/22, remaining chromosomes train; checkpoint minimizing validation loss. This partitions reference sequence-to-activity/classifier training; fixed zero-shot motif/QTL cohorts do not inherit those training partitions.'
        for tid in ['dart-ccre','dart-celltype','dart-accessibility']:
            t=self.row('tasks',tid);base=self.row('protocols',tid+'-supervised')
            base.update(name='DART frozen CNN probe',adaptation='frozen probe',requires_embeddings=True,
                model_interface='Position-aligned final-layer embeddings; token spans expanded to nucleotides',fitted_component='32 channel projection; two width 8 CNN layers; sum pool; linear output',selection='Lowest validation loss; Adam learning rate 0.002',split_rule=shared,source_evidence_id=methods,notes='Frozen probe; separate LoRA recipe is a linked protocol. Reference sequence targets are used for training.')
            ft=dict(base);ft.update(id=tid+'-lora',name='DART LoRA fine-tuning',adaptation='parameter-efficient fine-tune',requires_embeddings=False,model_interface='DNA sequence through adapted encoder and task head',fitted_component='LoRA on linear/convolutional layers; rank 8, alpha 16, dropout 0.05; trained classifier',selection='Lowest validation loss; AdamW learning rate 0.0001, weight decay 0.01')
            self.put('protocols',ft)
            for m in [x for x in self.d['protocol_metrics'] if x['protocol_id']==base['id']]:
                self.metric(ft['id'],m['metric_id'],m['aggregation'],methods,m['is_primary'])
            t['limitations']='Full task construction and adaptation recipes reviewed. Synapse processed HDF5 inputs and per-model score tables were not downloaded; publication cohort sizes are reported rather than measured post-filter scored rows. Each protocol has separate filters and training/selection semantics.'
            self.field('protocols',base['id'],'split_rule',methods,'Paper explicitly gives shared trained-task chromosome partitions; zero-shot cohorts remain distinct.')
        c=self.row('tasks','dart-celltype');c.update(target='Five-cell-line accessibility identity',output_description='Single cell-line identity among GM12878, H1ESC, HepG2, IMR90, K562; separate representation-clustering metric.',description='Five-way classification of differentially accessible reference regions; separate frozen-embedding clustering on the top 5000 regions per cell line.')
        self.put('metrics',dict(id='adjusted-mutual-information',name='Adjusted mutual information',definition='Adjusted mutual information between inferred clusters and reference class labels.',direction='higher'))
        self.put('protocols',dict(id='dart-celltype-clustering',task_id='dart-celltype',variant_id=None,name='DART frozen-embedding cell clustering',adaptation='unsupervised clustering',requires_embeddings=True,model_interface='Mean final-layer sequence embedding; BPE token mean weighted by nucleotide span',fitted_component='K-means,k=50',selection='100 clustering runs; cell labels do not train feature extractor or define bag-of-motif variance selection.',split_rule='Top 5000 differential peaks per cell line, 25000 total; same fixed cohort clustered and compared with reference cell labels, not a supervised train/test task.',split_unit='regulatory sequence',source_evidence_id=methods,notes='Distinct from the five-way supervised readout.'))
        self.metric('dart-celltype-clustering','adjusted-mutual-information','Mean across 100 K-means runs; source conservative 95% interval',targets)
        a=self.row('tasks','dart-accessibility');a.update(input_description='2114 bp window around DNase peak or GC matched background; central 1000 bp determines read count label.',output_description='Scalar log DNase read count per cell line; five linked cell-line contexts, not a per-base profile.')
        for p in [x for x in self.d['protocols'] if x['task_id']=='dart-accessibility']:
            p['notes']='Regression metrics across peaks and across peaks+background are separate; IDR-positive peak versus background AUROC/AP are auxiliary. Peak:negative training batch ratio 10:1; half reverse complemented, shift up to 500 bp.'
            self.metric(p['id'],'pearson','Within each cell line across peaks, and separately peaks+background',methods)
            self.metric(p['id'],'spearman','Within each cell line across peaks, and separately peaks+background',methods,0)
            self.metric(p['id'],'auroc','Auxiliary high confidence IDR peak/background discrimination',methods,0)
            self.metric(p['id'],'ap','Auxiliary high confidence IDR peak/background discrimination',methods,0)
        for slug in ['caqtl','dsqtl']:
            for suffix in ['', '-magnitude']:
                t=self.row('tasks','dart-'+slug+suffix)
                t['limitations']='Paper cohort counts and released filter/scorer code reviewed. Model-specific final scored rows depend on coordinate join,used/in-peakfilters and score availability. Synapse processed input/scoretables were not downloaded; sourcecount is not asserted to equal every model’s scored cohort.'
                if suffix:
                    p=self.row('protocols',t['id']+'-protocol');p.update(adaptation='counterfactual evaluation of frozen-probe / LoRA sequence-to-activity model',requires_embeddings=None,
                        model_interface='Signed alternate-minus-reference DNase count prediction from GM12878 sequence-to-activity model',fitted_component='Sequence-to-activity readout trained on reference DNase regions; no QTL-label readout',selection='Reference sequence-to-activity model selected on validation chromosomes; QTL effect correlation is a separate fixed-cohort evaluation.',split_rule='GM12878 DNase reference model uses DART chromosome holdouts. QTLs form a fixed external variant cohort after dataset-specific eligibility; no new QTL train/test fit.',source_evidence_id=methods,notes='Pearson/Spearman use signed effects and the stated effect column; absolute allelic change is used for classification, not copied into direction-sensitive correlation.')
                self.review('tasks',t['id'],'Full DART methods and matching QTL eligibility/scorer inspected, including difference between DNase-trained counterfactual models and zero-shot QTL likelihood/embeddingscores.',[methods,targets,filters],t['limitations'])
        for tid in ['dart-ccre','dart-motif']:
            t=self.row('tasks',tid);t['limitations']='Likelihood and embedding comparison, matched synthetic controls, source cohort construction and trained settings reviewed. The released Synapse processed inputs/model outputs were not downloaded, so nominal publication counts are not an independent scored-row recount.'
        for t in self.members('dart'):
            self.review('tasks',t['id'],'Full DART paper Appendices C–E and pinned source task interfaces inspected; target,adaptation,selection,metrics and reference-training versus fixed cohorts separated.',[methods,targets,filters,t['evidence_id']],t['limitations'])
            self.limit('tasks',t['id'],'measured_scored_cohort','not-retrieved','Synapse source and processed datasets are identified in the pinned README but were not downloaded. Reported source counts and code-specific filters are recorded separately; no independent scored-row count is claimed.',filters)
        self.finding('dart-count-vs-profile','dart-accessibility','dart','DART compares only ChromBPNet’s total-count head to DNALMs, not its base-level profile head. Quantitative QTL effects are counterfactual outputs of DNase-trained sequence-to-activity models, not directly QTL-trained probes.',methods)
        self.family('dart','Full paper task construction, adaptation and split methods plus pinned task scorers reviewed; original Evo 2 protocol associations retained without expanding them to all DART settings.',[methods,targets,filters],'Synapse processed HDF5 and model score tables were not downloaded; every count remains labeled reported or measured.')

    def bacbench(self):
        repo='macwiatrak/BacBench';rev='64b7d45823b2ff2ef88458e3aa235caa461a12aa';local='research/artifacts/final-audit/existing-bacbench'
        ess=self.code('bacbench-essential-scorer',repo,rev,'bacbench/tasks/essential_genes/run_train_cls.py',
            'Frozen gene embeddings feed LayerNorm, dropout and a single linear logit. Train on embedded split labels, select checkpoint/early stop by validation per-genome median AUROC. Final table reports each genome AUROC/AP and printed macro mean/median. Test=False default returns validation predictions; a test flag is required for final test.',49,354,local)
        op=self.code('bacbench-operondb-scorer',repo,rev,'bacbench/tasks/operon/run_evaluation_operondb.py',
            'Each known operon is one positive candidate, scored by mean pairwise cosine among its gene embeddings. Compare with 10 random contiguous same-length gene windows from the same contig for each of five seeds 1, 12,123, 1234, 12345. The sampler does not explicitly exclude known operons or overlapping positive windows. AUROC/AP per operon/seed, no downstream fit.',53,110,local)
        long=self.code('bacbench-longread-scorer',repo,rev,'bacbench/tasks/operon/run_evaluation_long_read_rna_seq.py',
            'All adjacent gene pairs are labeled from the min-to-max indices of each annotated operon. Score is rescaled cosine similarity; opposite-strand pairs forced to zero. Pool contig pairs by strain and report per-strain AUROC/AP plus macro mean/std. Whole 5-strain test cohort, no fitting or training partition.',10,135,local)
        amr=self.code('bacbench-amr-scorer',repo,rev,'bacbench/tasks/antibiotic_resistance/train_and_predict_linear.py',
            'Separate MLP per antibiotic. Drop missing target/embedding rows; default sample-level 70/10/20 split with stratification for classification when feasible, otherwise ShuffleSplit. Optional groups use GroupShuffleSplit and can fallback to sample-level split. Fit/checkpoint by validation AUROC (binary) or R2(MIC), test only with test after train. Three CLI seeds 1, 2, 3. Binary AUROC/AP/F1/balanced accuracy/accuracy; MIC R2/Pearson, source values are not implicitly log transformed.',72,163,local)
        pheno=self.code('bacbench-phenotype-scorer',repo,rev,'bacbench/tasks/phenotypic_traits/train_and_predict_linear.py',
            'Pinned CLI and run default to split=genus, train/validation/test 70/10/20, and CLI seeds 1, 2, 3. Labels are merged with genus metadata; grouped phenotype lists specify target columns. If requested group column is missing, warn and fallback to random. Group-split failures can fallback to sample ShuffleSplit. All traits, including quantitative ones, are categorical; rare classes<50 removed. Test is opt-in; validation checkpoints and per-trait metrics retained.',705,916,local)
        ppi=self.code('bacbench-ppi-cosine',repo,rev,'bacbench/tasks/ppi/run_unsupervised_eval.py',
            'Zero-shot protein embedding cosine baseline evaluates only test strains, thresholding STRING score/1000 at 0.6. Defaults cap 6000 proteins and 2 million pairs; valid per-genome AUROC/AP and mean/median/std are reported, so full STRING pair count is not automatically the scored count.',45,147,local)
        notes={
            'essential':('Native genome-level splits are genus-disjoint:37 train/9 validation/9 test genomes. Whole released nested essential-label arrays contain 136278/29269/27666 genes and 14167/3886/3573 essential labels. Genus sets inspected are pairwise disjoint; exact sequence homology is not established.',ess,'frozen linear probe','LayerNorm+dropout+singlelinearlogit','Select checkpoint by validation median per-genome AUROC; early stop with patience 10; test reporting opt-in.'),
            'operondb':('Fixed known operon cohort; each positive compared with 10 contiguous same-contig windows, sampled independently for five fixed seeds. Not a supervised gene-pair train/test split.',op,'zero-shot candidate-set discrimination','None','No fitted readout; random negative windows may overlap known operons.'),
            'operon-longread':('All five released test strains; adjacent pairs pooled within strain. No downstream fit.',long,'zero-shot adjacent-gene scoring','None','Fixedcosinescorewithoppositestrandveto.'),
            'ppi':('Use embedded genus-held-out split labels. Small release card declares 159 train/49 validation/53 test genomes; published percentage 60/10/20 sums 90 and does not match actual declared rows. No raw pair recount claimed.',ppi,'frozen probe / separate zero-shot baseline','MLP for supervised recipe; none for cosine baseline','Supervised test reporting opt-in; cosine baseline uses test only with protein/pair caps.'),
            'amr-binary':('Per antibiotic 70/10/20 sample-level split by default, three CLI seeds 1/2/3, stratification when feasible. Optional groups can fallback to sample ShuffleSplit; actual genus disjointness requires manifest of that particular run.',amr,'frozen MLP probe','OneMLPperantibiotic','Checkpoint and early stop by validation AUROC; test reporting opt-in.'),
            'amr-mic':('Per antibiotic 70/10/20 random sample-level split by default, three CLI seeds 1/2/3. Optional groups can fallback to sample ShuffleSplit; actual run must record groups.',amr,'frozen MLP probe','OneMLPregressorperantibiotic','Checkpoint and early stop by validation R2; test reporting opt-in.'),
            'phenotype':('Pinned default is genus-grouped 70/10/20, not random; merged labels supply genus. Missing group column or failed group split can fallback to sample ShuffleSplit; record actual split outcome.',pheno,'frozen MLP probe','OnecategoricalMLPperphenotypetarget','Rare classes<50 removed; validation-selected checkpoints; test reporting opt-in.')}
        for slug,(split,eid,adapt,fitted,selection) in notes.items():
            tid='bacbench-'+slug;t=self.row('tasks',tid);p=self.row('protocols',tid+'-protocol')
            p.update(split_rule=split,adaptation=adapt,fitted_component=fitted,selection=selection,source_evidence_id=eid,notes='Source scorer reviewed; LOAM readout is a separate fixed sklearn protocol and does not inherit BacBench training defaults.')
            t['limitations']='Pinned loader, task definition, fitting/split and scorer reviewed. Whole-genome labels are incomplete across targets; retained/scored examples depend on embedding availability, target filters and run arguments. Source-declared genome counts and measured label counts are separate.'
            if slug=='operondb':t.update(target='Known-operon candidate-set discrimination',task_type='candidate-set binary ranking',description='Score a known operon against same-sized contiguous gene windows from the same contig; per-operon AUROC/AP, not a fitted general gene pair classifier.')
            for metric in (['r2','pearson'] if slug=='amr-mic' else ['auroc','ap']):self.metric(p['id'],metric,'Per-target or per-genome as declared; mean/median are separate summaries.',eid)
            self.field('protocols',p['id'],'split_rule',eid,'Actual pinned scoring/training script rather than README summary inspected.')
            self.review('tasks',tid,'Pinned task README and full fit/split/scorers inspected; available HF cards and label tables reviewed. Native BacBench and LOAM protocols are separate.',[eid,t['evidence_id']],t['limitations'])
        self.row('tasks','bacbench-operon-longread')['limitations']='Five-strain test only release and entire zero-shot scorer reviewed. No training partition exists; underlying long-read transcript annotation was not regenerated.'
        # Keep supervised and zero-shot PPI adaptations separately navigable.
        p=dict(self.row('protocols','bacbench-ppi-protocol'));p.update(id='bacbench-ppi-cosine',name='BacBench PPI cosine baseline',adaptation='zero-shot embedding comparison',fitted_component='None',selection='Fixed 0.6 STRING threshold; 6000 proteins/2 million pair default caps.',source_evidence_id=ppi)
        self.put('protocols',p)
        for mid in ['auroc','ap']:self.metric(p['id'],mid,'Per-genome;macro mean/median/std.',ppi)
        self.finding('bacbench-pheno-default','bacbench-phenotype','bacbench','Pinned phenotype code defaults to genus grouped 70/10/20, whereas task README describes random as the default. Labels supply genus, so the random fallback is not the default intended protocol. Actual group failure fallback still requires run provenance.',pheno)
        self.finding('bacbench-operon-negative','bacbench-operondb','bacbench','OperonDBnegativecandidatesarecontiguoussame-contigwindowsandarenotexplicitlycheckedtoexcludeknownoperons.Thetaskassessescandidate-setdiscriminationratherthanindependentlyvalidatedpositive/negativegene-pairclassification.',op)
        self.family('bacbench','All active task definitions and pinned training/scorers reviewed; distinct native genus, sample, candidate and test only protocols recorded. No deprecated strain clustering task added.',[ess,op,long,amr,pheno,ppi],'Full PPI genomes/pair arrays are not retrieved; source card counts are not measured pair counts. Run-specific eligible cohorts remain explicit.')
        self.family('loam-evals','All three native target families and fixed last-layer/test-selected layer-sweep readouts checked against pinned docs; previous measured essential/DNA EC and RNAGym artifacts retained.',
            [ess,'loam-essential','loam-ec'],'LOAM test-selected maximum layers must remain separate from fixed last-layer results; it does not validate a BacBench-wide claim.')
    def bend2(self):
        repo='machinelearninglifescience/BEND2';rev='3ab8ae98109a1f37e1ea5091cff1006eead7ebbf';local='research/artifacts/final-audit/existing-bend2'
        readout=self.code('bend2-fixed-ridge',repo,rev,'src/bend2/readouts.py',
            'Intervention readout uses alternate-minus-reference embedding differences, length change and training-fitted one-hot context/intervention indicators. Five GroupKFold folds hold out whole genes/elements. Ridge alpha=10, LSQR tolerance1e−4; no label-driven hyperparameter search. Report mean within-group Spearman, with whole-group bootstrap.',62,173,local)
        atlas=self.code('bend2-atlas-selection',repo,rev,'src/bend2/_tasks/atlas_profile.py',
            'Atlas tunes a shared ridge penalty on 4,223 training and 1,023 validation source constructs, then refits all 5,246 source constructs. Family separation excludes 27 source constructs linked to 2,411 candidates. Choose 10 candidates for each of 16 on/off-cell requests using predicted minimum on-target minus clipped maximum off-target activity. Candidate assay outcomes are read only after all choices are stored; score gain over intent-matched random selection, separately for two experimental replicates.',63,145,local)
        tissue=self.code('bend2-tissue-retrieval',repo,rev,'src/bend2/_tasks/tissue_identification.py',
            'GTEx prediction fits 51 ridge outputs on 12,146 genes; select one shared penalty from 10000, 1000,100, 10, 1, 0.1 by 1,350 validation-gene standardized MSE. Features and targets scale on training genes only; no train+validation refit. Rank 51 predicted tissue profiles against 51 observed profiles using Spearman across 5,782 common test genes. Top 1 tissue identity uses fractional ties; whole-gene 10000-draw bootstrap preserves all 51 tissue queries. This tests represented tissue profiles, not unseen tissue transfer.',1,177,local)
        prior=self.code('bend2-prior-scoring',repo,rev,'src/bend2/_tasks/prior.py',
            'One central masked nucleotide per 1,200 bp reference window, 512 evaluation windows from separate 1 Mb blocks and 1,024 baseline-training windows. Primary mean negative log 2 true-base probability; no probability clipping. One-query accuracy grants fractional tie credit; multi-query adapters average query losses/accuracy within each window before resampling.',8,94,local)
        definitions=self.ev('final-bend2-dataset-scope','src-bend-data','Bundled tables, frozen asset manifest and docs/data.md',
            'Complete bundled files inspected: prior panel 1536 rows (1024 baseline training/512 evaluation); Atlas population 7684 rows (4223 train/1023 validation/2411 candidate/27 excluded), source activity 5246 rows and candidate activity 2411 rows with 24 replicate-cell columns; Siraj direct outcomes 181458 IDs; numerical reference 340584 records ×4 columns; GTEx truth 19282 genes ×51 tissues with 12146 train/1350 validation/5786 original test indices. These confirm bundled tables, not a recount of downloaded OpenSplice/Siraj source archives.','data')
        for t in self.members('bend'):
            slug=t['id'].removeprefix('bend-')
            if slug not in ['prior','opensplice','context','background','repair','cell-selective','atlas','tissue']:continue
            p=self.row('protocols',t['id']+'-protocol')
            p['selection']='Fixed alpha 10 ridge and five whole-group folds; no task-specific search.' if slug in ['opensplice','context','background','repair','cell-selective'] else 'Validation-selected ridge; exact source-only fitting membership recorded.' if slug in ['atlas','tissue'] else 'No fitted task readout; baseline-fitting and evaluation panels are separate.'
            if slug in ['opensplice','context','background','repair','cell-selective']:p['fitted_component']='Ridge(alpha=10,solver=LSQR,tolerance1e−4) on embedding differences and declared covariates'
            p['source_evidence_id']={'atlas':atlas,'tissue':tissue,'prior':prior}.get(slug,readout)
            t['limitations']='Pinned task preparation and complete scorers reviewed. Bundled reference tables and target shapes were scanned; the 425 MB OpenSplice master table and 93 MB Siraj source archive were not retrieved. Reported canonical intervention counts come from the source loader/cohort seal rather than an independent source-archive rebuild.'
            self.review('tasks',t['id'],'Pinned task preparation, selection and scoring reviewed; complete bundled tables/arrays inspected. Individual group/candidate/gene units retained.',[p['source_evidence_id'],definitions,t['evidence_id']],t['limitations'])
            if slug in ['opensplice','context','background','repair','cell-selective']:
                self.limit('tasks',t['id'],'upstream_archive_recount','not-retrieved','The released preparation code and bundled numerical reference were inspected. The large external experimental master/archive was not downloaded; raw-to-canonical cohort regeneration is not claimed.',readout)
        for slug in ['prior','atlas','tissue','cell-selective']:
            self.field('tasks','bend-'+slug,'counts',definitions,'Complete bundled tables/array dimensions independently checked; model scoring was not rerun.')
        self.row('protocols','bend-tissue-protocol').update(fitted_component='51 ridge heads with shared development-selected penalty; train-only feature/target scaling',selection='Minimum standardized MSE on 1,350 validation genes; no train+validation refit.',split_rule='12,146 training genes, 1,350 validation genes, 5,786 original test genes; four named incomplete-prediction exclusions yield 5,782 common scored genes. Tissue queries are the same 51 represented tissue types.')
        self.row('protocols','bend-atlas-protocol').update(fitted_component='Twelve activity ridge heads with a shared development-selected penalty',selection='Choose ridge penalty on 4,223 train/1,023 validation source constructs; refit all 5,246 sources before predicting 2,411 candidates.')
        self.family('bend','Eight BEND2 task preparations and complete scoring code reviewed. Bundled prior, Atlas, Siraj numeric/direct-outcome and GTEx tables inspected; reference count units retained.',[readout,atlas,tissue,prior,definitions],
            'Large external source archives were not retrieved; canonical source-loader counts are reported and bundled-table counts are measured. Candidate selection tasks do not require novel sequence generation.')

    def bgc(self):
        repo='Nugkta/BGC-Bench';rev='17a7f8e7dd35c0ceb99943189d17c1bc3cdaaf9f'
        fine=self.code('bgc-fine-scorer',repo,rev,'src/bgcbench/tasks/fine.py',
            'Fine classification uses 48 NP Classifier labels, all products unioned within a BGC. The random column holds out fold 4 of the supplied five-fold split, rather than averaging all five folds. Primary AUROC averages classes weighted by positive test examples, excluding classes without both test outcomes. The scorer aligns embeddings and labels before counting train/test.',1,76,'research/sources/Nugkta--BGC-Bench')
        chem=self.code('bgc-chem-scorer',repo,rev,'src/bgcbench/tasks/chem.py',
            'Chemical regression inner-joins split BGCs with 13 first-product RDKit descriptors, drops incomplete descriptor rows and aligns supplied embeddings. Standardized multi-output ridge alpha 1 predicts descriptors; primary mean Spearman across 13 targets. Raw split-file counts therefore exceed the eligible chemical cohort.',1,67,'research/sources/Nugkta--BGC-Bench')
        substrate=self.code('bgc-substrate-scorer',repo,rev,'src/bgcbench/tasks/substrate.py',
            'A-domain scoring retains level_b and nonmissing substrate, giving 2,027 domains in 28 classes, not all 2,315 split rows or 2,504 raw domain instances. All five parent-BGC-grouped folds are scored out of fold; GCF holdout has 292 test domains. Every required domain must have an embedding. Primary top 1 accuracy; label tiers are retained rather than equated to experimental validation.',1,78,'research/sources/Nugkta--BGC-Bench')
        card=self.ev('final-bgc-release','src-bgc-card','Dataset card / Files, split axes and limitations',
            'MIBiG 4.0 active-entry cohort 2,437; random 80/20 seed 42, 20%first-product scaffold groups, 20%BiG-SCAPE c 0.7 GCF groups; each axis holds out its own grouping only. Coarse six-label classification, fine 48-label classification, chemical 13 descriptors, retrieval class-macro Recall@10 with expected credit for ties, and A-domain 28-class specificity are separate tasks. Retrieval scores any associated test product among top 10; four splits include seven class/Hybrid holdouts. Three contrastive-head seeds. Source notes 755 active entries from Streptomyces, not balanced taxa.')
        # Add scorer-filtered counts while preserving the previous complete raw CSV recount.
        for s in BGC_FILTERED:
            tid='bgc-'+s['task'];v=next(v for v in self.d['variants'] if v['task_id']==tid and v['name']==s['file'])
            eid=self.ev('final-bgc-filtered-'+s['file'].split('/')[-1].removesuffix('.csv'),self.row('evidence',v['evidence_id'])['source_id'],
                s['file']+' + exact source eligibility',
                f"{s['raw_rows']:,} raw split rows; {s['eligible_rows']:,} label-eligible rows before model embedding availability. Partition counts {s['partition_counts']}."+(f" {s['target_classes']} substrate classes; evidence tiers {s['evidence_tiers']}." if s['task']=='adomain' else ''),'data')
            if s['task'] in ['chem','adomain']:
                for part,n in s['partition_counts'].items():
                    self.count(tid,n,'label-eligible domains' if s['task']=='adomain' else 'descriptor-eligible BGCs',s['file']+' / '+s['partition_key']+' '+part,eid,v['id'],suffix=s['file'].split('/')[-1]+'-'+part,qualifier='Measured source eligibility before embedding alignment; not necessarily model-specific final scored rows.')
            v['notes']='Complete released split file scanned; label eligibility follows its task-specific scorer. Counts before embedding alignment are distinct from model-specific final scored rows.'
            self.field('tasks',tid,'counts',eid,'Source-specific target eligibility applied; existing raw-file counts retained separately.')
        for t in self.members('bgc'):
            p=self.row('protocols',t['id']+'-probe');slug=t['id'].split('-')[-1]
            p['source_evidence_id']={'fine':fine,'chem':chem,'adomain':substrate}.get(slug,card)
            p['selection']='Fixed standardized linear probes; task-specific contrastive fitting for retrieval. Bootstrap intervals resample the task scoring unit; no joint biological holdout implied by independent split axes.'
            p['notes']='Task-specific eligibility and absent-class handling are specified in the cited scorer. Protein/Pfam and DNA encoders use different source interfaces; final row counts depend on embedding coverage.'
            if slug=='fine':self.metric(p['id'],'auroc','Weighted mean per-label AUROC with weights equal to positive test counts; omit labels without both test classes.',fine)
            if slug=='adomain':p['fitted_component']='Standardized domain-level logistic regression';p['split_rule']='All five supplied parent-BGC-grouped folds; separate GCF c 0.7 holdout. Retain level_b/nonmissing-substrate rows:2,027 total domains, 1,735 train/292 test in GCF split.'
            t['limitations']='Complete pinned split/label tables, full dataset card and task scorer reviewed. Model-specific embedding availability can alter eligible BGC counts. Taxonomy is imbalanced and split axes control scaffold, GCF or class rather than taxonomic distance. Substrate annotation evidence tiers are mixed.'
            self.review('tasks',t['id'],'Full publication/release card and pinned source scorer reviewed; complete split/label artifacts and exact target eligibility inspected.',[card,p['source_evidence_id']]+[v['evidence_id'] for v in self.d['variants'] if v['task_id']==t['id']],t['limitations'])
        self.finding('bgc-adomain-eligibility','bgc-adomain','bgc','Only 2,027 of 2,315 A-domain split rows are eligible level_b targets in 28 classes. Of 2,027 labels, 321 are experimental, 1,281 structure-inferred, 215 sequence-predicted, 8 homology-derived and 202 have no evidence code. GCF test has 292 eligible domains; raw 339 test rows are not the scored target count.',substrate)
        self.family('bgc','All five source tasks reviewed against immutable split/label files and task-specific scorers; target-eligible counts distinguished from raw rows and embedding-aligned model cohorts.',[card,fine,chem,substrate],'Complete taxon-by-model-scored-cohort distributions are not a released common manifest; no species holdout inferred from GCF or scaffold separation.')
        self.bgcs()

    def bgcs(self):
        repo='GenAIBio/BGCs-Bench';rev='2337f657f815aa2f41117b70e79d62b192c7f6fe';base='research/artifacts/final-audit/existing-bgcs'
        dataurl=f'https://github.com/{repo}/blob/{rev}/data.zip'
        self.put('sources',dict(id='final-bgcs-data-file',title='BGCs-Bench complete data.zip',kind='dataset-archive',url=dataurl,version=rev,retrieved=DATE,sha256=BGCS_STATS['archive_sha256'],local_path=base+'/data.zip',availability='available',notes='All metadata, FASTA and 80 CDS label arrays inspected; original MIBiG annotation truth not independently validated.'))
        eid=self.ev('final-bgcs-data','final-bgcs-data-file','Complete data.zip inspection',
            'The 131-kb cohort has 2386 BGCs and the 66-kb cohort has 2044 BGCs, each with five nearly equal folds. The annotation cohort has 80 BGCs, 16 per fold; all 80 FASTA lengths equal their label-array lengths. There are 2,098,355 positions: 1,685,856 CDS and 412,499 intergenic; sequence lengths are 5068–65044 bp. Annotation metadata uses column split, while pinned CDS probing code expects fold. Arabidopsis TaxID 3702 supplies two annotation BGCs; sequence cohorts also contain Arabidopsis, one Methanosarcina BGC and red algae, so Bacteria/Fungi alone is not the full source taxonomy.','data')
        code=self.code('bgcs-cds-interface',repo,rev,'src/probing/cds_annotation.py',
            'Per-base standard scaling uses training BGCs only; class-balanced logistic regression predicts every nucleotide and reports binary F1, balanced accuracy, MCC and AUROC. The default maximum iterations is 100, overridable by CLI. Code reads metadata[fold], but released annotation metadata has split rather than fold; intended five accession folds are available but require field harmonization before this pinned script can execute.',21,85,'research/sources/GenAIBio--BGCs-Bench')
        for tid in ['bgcs-biosynthetic','bgcs-taxonomy','bgcs-cds']:
            t=self.row('tasks',tid);t['status']='artifact-audited'
            t['limitations']='Complete release archive, task labels, fold metadata and source scorers reviewed. Five folds balance labels and do not establish species/family/homology exclusion. The CDS probing script has a fold/split column mismatch with the released metadata; published model training was not rerun.'
            p=self.row('protocols',tid+'-probe')
            if tid=='bgcs-cds':
                p.update(model_interface='Nucleotide-aligned frozen embeddings for every position, not sequence-mean pooling',fitted_component='Class-balanced logistic regression after train-fold StandardScaler; CLI max_iter default 100, publication-specific overrides separate.',split_rule='Five accession/BGC folds of 16 BGCs each in released metadata column split; code expects column fold, requiring explicit schema harmonization. No chromosome, species or homology holdout.',source_evidence_id=code)
                self.count(tid,1685856,'CDS-labeled nucleotide positions','allfivefolds',eid,suffix='CDS-bases')
                self.count(tid,412499,'intergenic-labeled nucleotide positions','allfivefolds',eid,suffix='intergenic-bases')
                self.limit('tasks',tid,'executable_release','conflicting','CDS script reads metadata column fold but pinned annotation metadata provides split. Fold assignment itself is available and fully counted; benchmark execution was not silently assumed.',code)
            self.field('tasks',tid,'counts',eid,'Complete archive independently scanned; total positions and target labels verified.')
            self.review('tasks',tid,'Complete pinned data archive, all split/label metadata and matching task scorer reviewed; scalar sequence targets separated from dense binary CDS annotation.',[eid,code,t['evidence_id']],t['limitations'])
        self.finding('bgcs-release-fold','bgcs-cds','bgcs','Pinned annotation metadata exposes split, but the CDS probing script selects metadata[fold]. The intended five 16-BGC folds are present; the interface mismatch is explicit and no unmodified execution is claimed.',code)
        self.family('bgcs','All three tasks reviewed; full 87-member dataset archive inspected, including three FASTA files, three metadata tables and 80 CDS arrays. Fold counts, base labels and taxonomy exceptions checked.',[eid,code],'CDS fold-column interface conflict retained; whole model inference/probing not reproduced. Source taxonomy is broader than Bacteria/Fungi.')
    def dataset_resource(self, tid, repo, rev, eid, collection=None, file=None, host='huggingface', note='Pinned released evaluation dataset; see task-specific variants and count units.', relation='evaluation-data', kind='dataset'):
        for table in ('data_resources','task_resources','evaluation_resources'):self.d.setdefault(table,[])
        rid='final-data-'+repo.replace('/','-')+('-'+file.replace('/','-') if file else '')
        url=(f'https://huggingface.co/datasets/{repo}/'+('blob/'+rev+'/'+file if file else 'tree/'+rev)) if host=='huggingface' else f'https://github.com/{repo}/blob/{rev}/{file}'
        self.put('data_resources',dict(id=rid,source_id=self.row('evidence',eid)['source_id'],title=repo+(' / '+file if file else ''),kind=kind,host=host,url=url,revision=rev,availability='public',evidence_id=eid,notes=note))
        self.put('task_resources',dict(task_id=tid,resource_id=rid,relation=relation,variant_id=None,evidence_id=eid,note=note),('task_id','resource_id','relation'))
        if collection:self.put('evaluation_resources',dict(evaluation_id=collection,resource_id=rid,relation=relation,evidence_id=eid,note=note),('evaluation_id','resource_id','relation'))

    def population(self, tid, pop, eid, note):
        self.put('task_populations',dict(task_id=tid,population_id=pop,variant_id=None,relation='sequence-origin',coverage=note,evidence_id=eid),('task_id','population_id','relation'))
        templates=[x for x in self.d['coverage_mappings'] if x['population_id']==pop]
        if not templates:return
        template=templates[0];m=dict(template);m.update(id='final-'+tid+'-coverage-'+pop,task_id=tid,evidence_id=eid,supporting_json=json.dumps([eid]));md=json.loads(m['metadata_json']);md.update(url=self.row('evidence',eid)['url'],basis='released sequence-origin membership',note=note);m['metadata_json']=json.dumps(md,ensure_ascii=False);self.put('coverage_mappings',m)

    def sequence_benchmarks(self):
        repo='InstaDeepAI/nucleotide_transformer_downstream_tasks';rev='96d86d567d4cd33536e49b429dc7983121619a08'
        path='research/artifacts/final-audit/existing-hf/'+repo.replace('/','--')+'/README.md'
        self.put('sources',dict(id='final-nt-original-card-source',title='Original NT dataset card',kind='dataset-card',url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/README.md',version=rev,retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][path],local_path=path,availability='available',notes='Publisher explicitly distinguishes the original data through 2023 preprint v3 from the revised peer-reviewed benchmark.'))
        card=self.ev('final-nt-original-card','final-nt-original-card-source','Dataset summary, source attribution and structure table',
            'Original NT data are the 18 configurations used through bioRxiv 10.1101/2023.01.11.523679 v3, superseded during review. Original histones are yeast ChIP-chip; promoter negatives are sampled from source sequences; original enhancers combine strong/weak biological annotations with 6,000 synthetic enhancers and 6,000 synthetic nonenhancers in training. Enhancer types are strong, weak, none. Separate donor/acceptor tasks derive from multi-species Spliceator; splice sites all derives from SpliceFinder. Revised human chromosome holdouts do not establish the original biological split.', 'documentation')
        revised=self.ev('final-nt-revised-partition','project-paper-nt-original-paper','Methods / Nucleotide Transformer downstream tasks, Dataset splits and performance evaluation',
            'Peer-reviewed revised human tasks use chr 20/21 for test and remaining chromosomes for training, remove Ns, balance negatives and cap training 30000 and testing 3000 rows. Within released training, tenfold 90/10 train/validation checkpoint selection repeatedly evaluates the same chromosome-held-out test. Final per-task score is median MCC across ten runs. Histones are K562 human ChIP-seq, unlike original yeast histone tasks; enhancer types are tissue-specific, invariant, none.', 'paper')
        for s in NT_GUE_FILES:
            slug=s['file'].split('/')[0] if s['repo'].startswith('InstaDeep') else s['file'].split('/')[1].removeprefix('emp_')
            tid=('nt-original-' if s['repo'].startswith('InstaDeep') else 'gue-')+slug
            if not any(t['id']==tid for t in self.d['tasks']):continue
            t=self.row('tasks',tid);part=s['file'].split('/')[-1].split('.')[0]
            description=f"Complete file has{s['rows']:,}rows,{s['unique_sequences']:,}distinct sequence strings,observed label counts{s['labels']},and lengths{s['lengths'][0]}–{s['lengths'][1]}nt."
            if 'exact_train_test_sequence_overlap' in s:description+=f" Exact train/test Sequence-string overlap:{s['exact_train_test_sequence_overlap']}; reverse complements and approximate homology were not compared."
            eid=self.data('native-'+tid+'-'+part,s,description)
            vid=tid+'-native-release';self.put('variants',dict(id=vid,task_id=tid,name='Native original release' if tid.startswith('nt-original') else 'GUE upstream release',evidence_id=eid,context='Upstream source configuration; distinct from GENEB repackaged CSVs and revised NT data.',input_length=f"{s['lengths'][0]}–{s['lengths'][1]}nt",dataset_revision=s['revision'],target_count=len(s['labels']),target_unit='scalar observed classes',notes='Source file contains supplied sample identifiers but no validated coordinate/assembly split manifest.'))
            self.count(tid,s['rows'],'sequence rows',part,eid,vid,suffix='native-'+part)
            self.field('tasks',tid,'counts',eid,'Complete native file scan; original and repackaged release counts remain separately attributed.')
            if tid.startswith('nt-original'):
                t['limitations']='Complete native train/test Parquets, source card and original/revised distinction reviewed. Sample-name fields are not a complete assembly/coordinate manifest. No chromosome or homology holdout is established for the original release; exact sequence recurrence is measured separately.'
                t['status']='artifact-audited'
                if slug=='enhancers_types':t.update(name='Strong / weak / non-enhancer (original NT)',target='Strong enhancer versus weak enhancer versus non-enhancer',output_description='One of three source enhancer-strength classes; not revised tissue specificity.',label_basis='Biological enhancer annotations plus source-generated synthetic training controls.')
                if slug=='enhancers':t.update(label_basis='Biological enhancer annotations plus 6,000 synthetic enhancers and 6,000 synthetic nonenhancers in training.',output_description='One binary enhancer/non-enhancer label per 200 nt window.')
                t['input_description']=f"Original release DNA window; measured{s['lengths'][0]}–{s['lengths'][1]}nt in{part}."
                if part=='test' and s.get('exact_train_test_sequence_overlap',0):
                    self.finding('native-overlap-'+tid,tid,'nt-original',f"Complete native train/test files share{s['exact_train_test_sequence_overlap']}distinct exact sequence strings. This is measured nucleotide-string recurrence, not a reverse-complement,approximate-homology or pretraining overlap analysis.",eid)
                self.limit('tasks',tid,'biological_split','not-reported','Original release provides train/test membership and source-specific sample names, but no complete chromosome/coordinate or homology grouping manifest. The revised chr 20/21 split is a different benchmark version.',card)
            else:
                t['limitations']='Complete native GUE train/dev/test CSVs and defining benchmark publication reviewed. GUE and GENEB repackaging remain separate variants; sample-name/coordinate lineage is absent from the released two-column CSVs. No chromosome or homology separation is established by those files.'
                t['status']='artifact-audited'
            self.dataset_resource(tid,s['repo'],s['revision'],eid,'nt-original' if tid.startswith('nt-original') else 'gue')
            self.review('tasks',tid,'Native released row/label/length data and benchmark version/source semantics inspected. Original, revised and GENEB protocols remain linked but distinct.',[card,eid,t['evidence_id']],t['limitations'])
        # The actual original splice inputs contain diverse eukaryotic organisms.
        taxpath=ROOT/'research/artifacts/final-audit/existing-hf/InstaDeepAI--nucleotide_transformer_downstream_tasks/splice-organism-taxonomy.json'
        self.put('sources',dict(id='final-nt-splice-taxonomy-source',title='UniProt taxonomy / original NT organism mnemonics',kind='taxonomy',url='https://rest.uniprot.org/taxonomy/search?query=mnemonic%3APANTR&format=json',version='Live taxonomy retrieved 2026-11-27; snapshot SHA256 recorded',retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][str(taxpath.relative_to(ROOT))],local_path=str(taxpath.relative_to(ROOT)),availability='available',notes='Taxonomy search can include descendants; only exact existing NCBItaxid matches used, with dataset mnemonic presence checked separately.'))
        taxa=self.ev('final-nt-splice-organisms','final-nt-splice-taxonomy-source','Pinned original donor/acceptor name fields and official UniProt taxonomy',
            'Original donor/acceptor sample identifiers contain 126 organism mnemonics across train/test. Exact official mappings confirm named model organisms, including human, mouse, rat, chimpanzee, chicken, zebrafish, fly, worm, Chlamydomonas, cattle, pig, marmoset, silkworm and Tribolium. Presence and per-organism rows are read from each pinned split; this is not human-only or a held-out-species split.','data')
        if not any(x.get('ncbi_taxid')==9598 for x in self.d['populations']):
            self.put('populations',dict(id='chimpanzee',name='Pan troglodytes',rank='species',parent_id='mammals',ncbi_taxid=9598,notes='Original NT Spliceator-derived isolated-site task; organism mnemonic PANTR confirmed by UniProt taxonomy.'))
            # Use the existing selected-species other-mammal row; add an all-species detail row.
            template=dict(self.row('coverage_rows','allSpecies:mammalia-sp-9483'));md=json.loads(template['metadata_json']);md.update(id='mammalia-sp-9598',label='Pan troglodytes',displayLabel='Pan troglodytes',common='chimpanzee',members=['Pan troglodytes'],note='Original NT donor/acceptor isolated-site datasets contain chimpanzee sequences.',lineageHint='Primates')
            template.update(id='allSpecies:mammalia-sp-9598',row_key='mammalia-sp-9598',population_ids_json='["chimpanzee"]',metadata_json=json.dumps(md));self.put('coverage_rows',template)
            m=dict(next(x for x in self.d['coverage_mappings'] if x['population_id']=='marmoset'));m.update(id='final-chimpanzee-template',task_id='nt-original-splice_sites_acceptors',population_id='chimpanzee',evidence_id=taxa,supporting_json=json.dumps([taxa]),all_species_row='allSpecies:mammalia-sp-9598');mm=json.loads(m['metadata_json']);mm.update(name='Pan troglodytes',species='Pan troglodytes',speciesId=9598,taxonomy='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9598',url=self.row('evidence',taxa)['url'],row='mammalia-other',allSpeciesRow='mammalia-sp-9598');m['metadata_json']=json.dumps(mm);self.put('coverage_mappings',m)
        taxbyid={p.get('ncbi_taxid'):p['id'] for p in self.d['populations'] if p.get('ncbi_taxid')}
        for slug,partitions in NT_SPLICE_MNEMONICS.items():
            tid='nt-original-'+slug
            for tx,mnemonic in NT_NAMED_TAXA:
                if tx not in taxbyid or not any(mnemonic in counts for counts in partitions.values()):continue
                pop=taxbyid[tx];note='Released original multi-species splice-site windows; per-split organism membership is measured from sample-name mnemonics. This is isolated-site recognition, not whole-transcript recovery.'
                self.population(tid,pop,taxa,note)
                for part,counts in partitions.items():
                    if mnemonic in counts:self.count(tid,counts[mnemonic],'organism-associated sequence rows',part+' / '+mnemonic,taxa,suffix='species-'+mnemonic+'-'+part,qualifier='Organism-associated names in pinned rows, mapped through official UniProt taxonomy; not independent genes or species-held-out folds.')
            self.field('tasks',tid,'populations',taxa,'Human-only attribution corrected using actual released row identifiers; additional organism mnemonics remain in the public dataset.')
        self.finding('nt-original-multispecies','nt-original-splice_sites_acceptors','nt-original','Original acceptor/donor tasks derive from Spliceator and contain 126 organism mnemonics. Human-only attribution was incorrect; named organisms recur across train/test, so this is not automatically species-held-out evaluation.',taxa)
        for t in self.members('nt-revised'):
            t['limitations']='Complete revised-release train/test files establish rows, scalar labels and input lengths. The paper specifies chr 20/21 test and remaining chromosomes for training; the public sequence-only schema does not independently reconstruct coordinates, reference-assembly consistency or approximate homology.'
            self.review('tasks',t['id'],'Complete released files and peer-reviewed construction/splitting methods reviewed; reported biological partition separated from directly measured rows/labels/lengths.',[t['evidence_id'],revised],t['limitations'])
        for collection in ['nt-original','nt-revised','gue','gb']:
            eids=[card,taxa] if collection=='nt-original' else [revised] if collection=='nt-revised' else [self.row('evaluations',collection)['evidence_id']]
            self.family(collection,'Defining source and dataset variants reviewed; dataset/version, target, split, adaptation and count provenance retained. Native files or prior complete artifact scans support row metadata.',eids,'Exact string equality is narrower than homology; inherited source counts and measured release rows remain separate. No revised chromosome policy is projected onto original or repackaged data.')
    def generator(self):
        v1=self.ev('final-generator-protocol','generator-paper','§4.4–4.7;AppendixC.4,D,E',
            'GENERator evaluates original/revised NT, GenomicBenchmarks and GenerTasks using full fine-tuning and a linear task head. Paper reports ten-fold averages and hyperparameter search over nine learning rates and four batch sizes, with early stopping patience 5. Causal models use terminal EOS embedding; masked models use BOS/CLS; all final-layer backbones are trained. P450/histone generation uses approximately 400000 training CDS per family and samples 100000 sequences per temperature/nucleus pair; after translation/training-deduplication, 10000 unique sequences per family are analyzed. These are protein-family-derived coding sequences, not evidence of genome viability.')
        v2=self.ev('final-generator2-protocol','generator2-paper','§5.1,5.2,5.4;AppendixC',
            'GENERator-v2 recovery samples 6144-bp RefSeq inputs ending in CDS with at least two-thirds noncoding context and compares the next 30 nt with reference. Runtime uses 30000 inputs and 50-nt outputs, a different workload. Revised NT full fine-tuning uses the 1B model only, truncates to a multiple of six, adds separator <s> at both ends and reads the terminal separator hidden state. Search covers learning rates 1e−5, 2e−5, 5e−5 and batch sizes 32, 64, 128, 256; AdamW, 100 warmup steps, plateau schedule, early stopping patience 5; MCC averaged over ten folds.')
        code=self.row('evidence','generator-split-code')['id']
        for p in self.d['protocols']:
            if p['id'].startswith('generator-') and p['id'].endswith('-ft'):
                p['split_rule']='The released GENERator script, when no validation split exists, uses shuffled KFold within the supplied training collection; each fold is validation and the supplied test file stays separate. The paper reports ten-fold results. Exact historical CLI arguments and fold manifests are not released in the inspected code, so native test membership is retained and no newly reconstructed biological split is claimed.'
                p['selection']='Validation-selected early stopping/checkpoints and source hyperparameter search; native test files are not used as training folds by the inspected KFold path.'
                self.limit('protocols',p['id'],'historical_run_arguments','not-released','The paper and executable KFold path are available, but exact historical command arguments and generated fold-index manifests are not included in the inspected release.',code)
            if p['id'].startswith('generator2-') and p['id'].endswith('-ft'):
                p['split_rule']='Paper specifies tenfold cross-validation on revised NT and mean MCC; source revision retains chromosome-held-out native test rows. Exact historical fold-index manifests and nested hyperparameter-selection implementation are not published in the inspected v2 report.'
                p['split_unit']='training example / inherited revised NT chromosome test'
                p['selection']='Source hyperparameter grid and validation-based early stopping; exact fold-index manifests are not reported.'
                p['source_evidence_id']=v2
                self.limit('protocols',p['id'],'historical_fold_manifest','not-released','Appendix C specifies preprocessing, grid, early stopping and tenfold MCC but does not release per-run fold-index manifests or show that native chromosome tests were rebuilt.',v2)
        for tid in ['gener-gene_classification','gener-taxonomic_classification']:
            t=self.row('tasks',tid);t['limitations']='Complete native train/test files and released KFold implementation were inspected. The paper reports ten-fold fine-tuning averages; the script can reserve validation within native training while leaving native test fixed. No historical fold manifest is published, so native file counts and paper-run averages remain separate records.'
            self.review('tasks',tid,'Complete native data, labels and lengths plus paper task definition and released train/validation/test implementation reviewed.',[t['evidence_id'],code,v1],t['limitations'])
        for collection,eid in [('generator-evals',v1),('generator2-evals',v2),('gener-tasks',v1)]:
            self.family(collection,'Full source evaluation/preprocessing and hyperparameter methods reviewed; existing native artifacts and source-specific zero-shot/supervised protocols retained.',[eid,code],
                'Historical per-run fold membership and exact RefSeq sampling/species manifests are not released in the inspected publication/code. Reported averaging and measured native file counts are not equated.')
        for tid in ['generator-recovery','generator2-recovery']:
            self.limit('tasks',tid,'sampled_refseq_manifest','not-released','Publication specifies taxonomic strata, sampling constraints and continuation lengths but does not provide per-example reference accessions/coordinates in the inspected release.',v1 if tid=='generator-recovery' else v2)

    def ceno(self):
        methods=self.ev('final-ceno-structure-design','ceno-paper','§4.14,p.29',
            'Structure-guided insertion design uses CENO proposals and Akita-guided search, then freezes candidates before AlphaGenome evaluation at five positional shifts spanning ±8192 bp. At 4q25: 15312-bp insertions, 160 candidates in five groups of 32; at LMO2: 26629-bp insertions, 136 candidates in four groups of 32 plus eight beam candidates. Beam candidates share search lineages (mean identity 81%/92%), so nominal candidates are not independent trials. At IGF2: 15312-bp insertions, promoter–super-enhancer recovery uses a matched neutral-insertion reference; AlphaGenome averages five shifts but Akita has one evaluation.')
        design=self.ev('final-ceno-enhancer-design','ceno-paper','§4.15,pp.29–32;TableS7',
            'Enhancer generator targets Astro, Oligo, Pvalb and Sst with 500-bp outputs conditioned by one prefix byte. SFT retains oracle MinGap ≥5, up to 8000 training/1000 validation examples per cell type and six epochs. GRPO/DAPO uses 32 completions per prompt, temperature 0.9, KL coefficient 0.03 and 300 optimization steps. Generated DNA is center-padded with N to 2114 bp and scored by the same frozen 19-subclass accessibility oracle used for filtering data and training rewards. Retrospective AAV oracle validation does not prospectively validate newly generated sequences.')
        oracle=self.ev('final-ceno-accessibility-oracle','ceno-paper','§4.15,pp.29–30',
            'Mouse cortex accessibility oracle inputs 2114 bp and predicts 19 subclass values. Unfrozen 600 M CENO backbone plus dilated CNN, pooling and linear output; chromosome 8/10 validation, 9/18 test, remaining train. Two-stage consensus then subclass specific peaks; cosine pattern loss plus log1p MSE; Adam, validation plateau and early stop. Report Pearson, Spearman and related regression metrics on held-out regions. Independent retrospective AAV tested mouse/human-liftover enhancers assess cell classes with rank, precision/recall/F1 and NES, not new design candidate activity.')
        eqtl=self.ev('final-ceno-causal-eqtl','ceno-paper','Fig.3;§4.2,4.9;TableS5',
            'The report lists 8862 binary causal-eQTL examples for human noncoding/coding variants and evaluates likelihood-based variant classification/AUROC. This panel is distinct from GTEx/MPRA eQTL PromoterAI and NTv3 GTEx cohorts. The inspected report does not identify a per-example input manifest, complete causal posterior filter recipe or biological train/test split for this specific fixed zero shot cohort.')
        for tid,eid in [('ceno-enhancer-design',design),('ceno-structure-design',methods),('ceno-mouse-accessibility',oracle),('ceno-causal-eqtl',eqtl)]:
            t=self.row('tasks',tid);p=self.row('protocols',tid+'-protocol');self.field('tasks',tid,'limitations',eid,'Published budgets and remaining source limitations distinguished.')
            if tid=='ceno-enhancer-design':
                t['limitations']='Full SFT/RL proposal recipe and oracle dependency reviewed. The same oracle filters training data, rewards optimization and scores outputs; no independent prospective reporter assay of generated candidates is reported. A fixed final independent per-cell generated evaluation library is not specified by the inspected method.'
                p.update(selection='Final generator from 300-step GRPO/DAPO run; 32 completions per cell prompt. Same oracle used for filtering, reward and final prediction.',notes='Four cell targets; 500-bp output; SFT threshold MinGap ≥5; maximum 8000/1000 training/validation examples per cell. Training completions are not independent final assay examples.')
                self.limit('tasks',tid,'prospective_generated_assay','not-reported','Retrospective AAV experimental data validate the oracle, not a new prospective assay of generated sequences. Final generated library example count is not enumerated in the inspected method.',design)
            elif tid=='ceno-structure-design':
                t['limitations']='Candidate budgets, selection lineage and held-out AlphaGenome protocol reviewed. Readouts are predicted contact-map recovery, not new experimental contact maps. Correlated beam candidates reduce effective sample size; IGF2 uses different numbers of oracle windows across evaluators.'
                p.update(selection='Akita-guided beam/ranked sampling; freeze candidate set before AlphaGenome evaluation.',notes='160 candidates at 4q25,136 at LMO2; held-out AlphaGenome five shifts. IGF2 different neutral reference and Akita one window are separate variants.')
            elif tid=='ceno-mouse-accessibility':
                t.update(input_description='2114-bp mm10 genomic window',output_description='19 mouse cortex subclass scalar accessibility values',limitations='Reference-region chromosome holdouts and oracle fitting reviewed. Retrospective AAV cohort uses mapped cell subclasses and human-to-mouse orthologous liftover; exact retained AAV assay count is not reported in the method. This is a predictive oracle evaluation, not independent experimental validation of new designs.')
                p['split_rule']='Validation chr 8/10; test chr 9/18; remaining chromosomes train. Source AAV tested enhancers form a separate retrospective cohort with cell-taxonomy mapping.'
            else:
                t['description']='Fixed CENO likelihood-scoring panel with 8862 reported human causal-eQTL variant labels; distinct from the separately indexed PromoterAI eQTL panels.'
                t['limitations']='Full report and named panel/table reviewed. The report does not provide the per-example variant manifest or exact posterior/negative-sampling recipe for this specific 8862-example panel; the count remains reported, not artifact measured.'
                self.limit('tasks',tid,'causal_label_recipe','not-reported','Exact posterior cutoff, source variant IDs and negative sampling for the 8862-example panel are not supplied in the inspected report.',eqtl)
            self.review('tasks',tid,'Full cited CENO methods and supplemental tables reviewed; budget, model fitting, oracle reuse, example units and source-unavailable fields recorded.',[eid,t['evidence_id']],t['limitations'])
        self.family('ceno-evals','Full report methods §4.2–4.15 and Tables S5/S7 reviewed; externally shared tasks retain their own source versions and CENO-specific scoring variants.',[methods,design,oracle,eqtl],
            'Per-example manifests for some CENO-specific panels are not released in the inspected material. Predicted design reward is not experimental validation; held-out-model evaluation and oracle-reused evaluation are distinguished.')

    def plantcad(self):
        extra=self.ev('final-plantcad-expression-scope','plantcad2-paper','Results / improved cross-species expression and translation prediction; Methods/gene prediction; Fig.5, S15; Table S9',
            'Journal results include maximum expression across tissues and a separate Arabidopsis-to-maize leaf expression transfer experiment. Maximum expression shares 17-species Andropogoneae training/validation and NAM maize test context; primary leaf expression methods describe log10 TPM and TPM>1 on/off, not a complete maximum expression normalization recipe. Arabidopsis transfer uses separate expression data and 1024 bp upstream/downstream input, with reported AUROC 0.786 within Arabidopsis vs 0.631 in maize. The seven HF fine-tuning configurations do not expose matching named maximum expression or separate Arabidopsis expression-transfer files.')
        for tid in ['plantcad2-ft-maximum-expression','plantcad2-ft-arabidopsis-expression-transfer']:
            t=self.row('tasks',tid);p=self.row('protocols',tid+'-paper')
            t['limitations']='Journal endpoint, figure, methods and released seven-configuration dataset/code resources reviewed. No matching named target configuration or per-example file was located in those releases. Counts and target normalization are not supplied for this extra endpoint; leaf-absolute-expression labels are not substituted.'
            p.update(split_rule='Paper-only endpoint in the stated species-transfer setting; no matching per-example split/target manifest is included in the inspected named release.',notes='Species and input window details reported in the paper are retained; a shared dataset or output normalization is not inferred from adjacent leaf-expression endpoints.',source_evidence_id=extra)
            self.limit('tasks',tid,'matching_target_file','not-released','No matching named configuration exists in the inspected seven-configuration HF release or paper-associated code archive. The paper endpoint remains indexed with source-reported settings and absent field values.',extra)
            self.limit('tasks',tid,'example_count','not-reported','No per-split example count for this extra target is stated in the inspected results/methods or an associated named dataset file.',extra)
            self.review('tasks',tid,'Journal results/methods and released dataset/code configuration inventory reviewed. No adjacent but biologically different expression target was substituted.',[extra,t['evidence_id']],t['limitations'])
        legacy=self.ev('final-genecad-legacy-scope','genecad-paper','Methods / nucleotide, exon, CDS and transcript evaluation',
            'Historical GeneCAD paper reports nucleotide/exon/transcript metrics and a phase-aware CDS evaluator. The current revision uses coding-only GffCompare with distinct default/strict chain settings and does not substitute for historical phase-aware CDS metrics. Per-species reference feature denominators are not enumerated in the historical paper and are not reconstructed from newer revision output tables.')
        for t in self.members('genecad'):
            if t['id'].startswith('genecad-legacy-'):
                t['limitations']='Historical full paper and original evaluation interface reviewed. Per-species reference denominators are not reported for these historical results; newer coding-only GffCompare tables use a different evaluation recipe and are not substituted.'
                self.limit('tasks',t['id'],'historical_reference_denominator','not-reported','Historical paper supplies summary metrics but not the full per-species feature count denominator; current revision counts describe a different protocol.',legacy)
            self.review('tasks',t['id'],'Full historical paper and pinned current training/scoring/structure metric artifacts reviewed. Dense labels, CDS chains, transcripts, exon intervals and BUSCO readouts remain separate.',[legacy,t['evidence_id']],t['limitations'])
        for collection in ['plantcad2-zero','plantcad2-ft','genecad']:
            self.family(collection,'Full source paper, pinned release configuration inventories and existing complete label/count/scorer inspections reviewed; linked species/window/protocol variants retained.',[extra,legacy],
                'Historical and current GeneCAD structure metrics are not interchangeable. Two extra PlantCAD2 expression endpoints have no matching target file in the inspected named release; source absence is recorded explicitly.')
    def existing_measured(self):
        repo='OATML-Markslab/ProteinGym';rev='144fe22b07dfaeec2b366f2346203a9838a55b4c'
        for fname in ['DMS_substitutions.csv','DMS_indels.csv']:
            self.code('proteingym-'+fname.split('.')[0],repo,rev,'reference_files/'+fname,
                'Official assay manifest identifies source_organism, molecule, experimental selection_assay, raw phenotype column, direction and processed mutant count. This is assay metadata, not the nucleotide RNAGym release or an Evo-specific filtered cohort.',1,None,'research/artifacts/final-audit/existing-proteingym-reference')
        for assay in PROTEINGYM_RNAGYM:
            tid='rnagym-'+assay['id'].lower().replace('_','-');t=self.row('tasks',tid)
            source='final-proteingym-'+assay['file'].split('.')[0]+'-source'
            eid=self.ev('final-rnagym-assay-'+assay['id'].lower().replace('_','-'),source,
                assay['id']+' row:selection_assay, selection_type, raw_DMS_phenotype_name, source_organism',
                assay['molecule']+'; selection_assay: '+assay['assay']+'; selection_type: '+(assay['selection'] or 'not specified')+'; raw phenotype: '+assay['phenotype']+'; source_organism: '+assay['organism']+'. RNAGym ASSAY_DESCRIPTION contains a taxonomic label for this coding assay, not its experimental target.','data')
            target=assay['molecule']+' / '+assay['assay']
            t.update(target=target,description='Predict the released numerical mutant score for '+target+'. The assay phenotype is '+assay['phenotype']+'; the RNAGym input remains nucleotide sequence, while the matched ProteinGym entry describes protein-level assay processing.',output_description='One processed RNAGym DMS_score per mutant nucleotide sequence; assay-specific '+assay['phenotype']+' readout.',label_basis='Experimental '+assay['assay']+' assay; ProteinGym raw phenotype '+assay['phenotype']+' is transformed into benchmark DMS_score. This is not a taxonomic class.')
            for field in ['target','description','output_description','label_basis']:self.field('tasks',tid,field,eid,'Experimental readout identified from the exact matching DMS_id in the official assay manifest; nucleotide-input release is preserved.')
            out=next(x for x in self.d['task_outputs'] if x['task_id']==tid)
            out['rationale']='The released assay scores one scalar experimental phenotype per supplied mutant nucleotide sequence. '+target+'. This is an isolated sequence/variant readout, not dense genomic annotation.'
            for x in self.d['task_categories']:
                if x['task_id']==tid and x['category_id'].startswith('output-'):x['rationale']=out['rationale']
            self.dataset_resource(tid,'MarksLab-DasLab/RNAGym','2828cf99316d75daaa8d832a2573cbb25bbd35fe',eid,file='fitness/reference_sheet_final.csv',host='github',note='Assay identity manifest; nucleotide assay libraries are the separately linked RNAGym processed archive.',kind='manifest',relation='identity-manifest')
        # Canonical Evo study rows receive source IDs without replacing their cohorts.
        for tid,dmsid in EVO_PROTEINGYM_IDS.items():
            if not any(t['id']==tid for t in self.d['tasks']):continue
            a=next(x for x in PROTEINGYM_CANONICAL if x['id']==dmsid);source='final-proteingym-'+a['file'].split('.')[0]+'-source'
            eid=self.ev('final-evo-proteingym-'+tid,source,dmsid+' exact assay-reference match',
                'Official ProteinGym assay ID '+dmsid+'; molecule '+a['molecule']+'; raw phenotype '+a['phenotype']+'; selection_assay '+a['assay']+'. This identifies an upstream assay record; published ProteinGym row counts and the original Evo nucleotide-filtered evaluation cohorts are not equated.','data')
            self.field('tasks',tid,'source_assay_identifier',eid,'Exact introducing-study identity match; downstream nucleotide processing and model-specific eligibility stay separate.')
        for t in self.members('rnagym'):
            eid=t['evidence_id'];scope='Existing complete processed assay, all relevant CV partitions and released Evo 2 prediction-member inspections reviewed alongside exact target metadata and signed/direction-invariant scoring semantics.'
            ids=[eid,'rnagym-scorer-audit','rnagym-split-audit']
            if t['target'] not in ['PROK','EUK','HUMAN','VIRUS']:ids += [x['evidence_id'] for x in self.d['field_evidence'] if x['entity_table']=='tasks' and x['entity_id']==t['id'] and x['field']=='target' and x['evidence_id'].startswith('final-')]
            self.review('tasks',t['id'],scope,ids,t['limitations'])
        self.family('rnagym','All 70 processed fitness files, 124 supervised partition files and 70 released Evo 2 prediction members retain their existing full inspections. Coding-assay experimental targets reconciled against 37 exact ProteinGym metadata IDs.',
            ['rnagym-scorer-audit','rnagym-split-audit','rnagym-evo-scorer'],'RNA fitness and coding DMS are distinct target types; assays are not universal fitness scales. Separate RNAGym structure tracks are not implied by the 70 fitness assays.')
        self.family('geneb','All 200 pinned train/test CSVs across 100 configurations retain complete row/label/length and exact-sequence-overlap inspections. Common harness and primary MCC aggregation reviewed; source biological semantics checked separately.',
            ['geneb-spec'],'Two-column repackaged inputs lack a full coordinate/assembly/homology manifest. Source configuration names are not treated as verified class counts; measured duplicates are retained.')
        for t in self.members('geneb'):
            if t['id'].startswith('geneb-'):
                self.review('tasks',t['id'],'Complete pinned train/test CSV and common frozen-probe/few-shot harness reviewed; measured labels, lengths, counts and exact train/test sequence recurrence retained.',
                    [t['evidence_id'],'geneb-spec'],t['limitations'])
        self._additional_artifacts()

    def _additional_artifacts(self):
        # Small source files that resolve task scales without fetching all genomes.
        for s in BACBENCH_FILES:
            if 'repo' not in s:continue
            tid='bacbench-'+('amr-binary' if s['file']=='binary_labels.csv' else 'amr-mic' if s['file']=='mic_regression_labels.csv' else 'phenotype')
            eid=self.data('bacbench-'+s['file'].replace('.','-'),s,
                f"Complete label table has{s['rows']:,}genome rows and{len(s['columns'])}columns. Target-column nonempty counts are recorded per linked variant; these precede embeddings,rare-class filters and particular split seeds.")
            self.dataset_resource(tid,s['repo'],s['revision'],eid,'bacbench')
            self.count(tid,s['rows'],'label-table genome rows','source label table',eid,suffix='label-table-rows')
            for name,n in s['target_counts'].items():
                if name in ['species','genus','family']:continue
                slug=''.join(c.lower() if c.isalnum() else '-' for c in name).strip('-')
                vid=tid+'-target-'+slug
                self.put('variants',dict(id=vid,task_id=tid,name=name,evidence_id=eid,context='Separate drug/phenotype target column; not a genomic output position.',input_length='Whole-genome representation',dataset_revision=s['revision'],target_count=1,target_unit='scalar drug/phenotype readout',notes='Counts are nonempty source label cells before model embedding merge, rare-class filtering, group availability and run-specific split.'))
                self.count(tid,n,'nonempty target-label genome rows',name+' / source label table',eid,vid,suffix='target-'+slug)
        for s in [s for s in BACBENCH_FILES if 'genera' in s]:
            part=s['file'].split('/')[-1].split('-')[0];spec=dict(repo='macwiatrak/bacbench-essential-genes-dna',revision='0210c2445e89c765c0fe5d69618b8a6c262e5d30',file='data/'+s['file'].split('/')[-1],sha256=s['sha256'])
            eid=self.data('bacbench-essential-native-'+part,spec,
                f"Complete nested genome file:{s['rows']}genomes,{s['genes']:,}gene labels,{s['essential']:,}essential labels. Genera:{', '.join(s['genera'])}. All three partition genus sets are disjoint; this doesnotprove gene sequence or protein-homology exclusion.")
            self.row('sources','final-bacbench-essential-native-'+part+'-file')['local_path']=s['file']
            for value,unit,suf in [(s['rows'],'genome rows','genomes'),(s['genes'],'gene labels','genes'),(s['essential'],'essential gene labels','essential')]:self.count('bacbench-essential',value,unit,part,eid,suffix='native-'+part+'-'+suf)
            self.dataset_resource('bacbench-essential',spec['repo'],spec['revision'],eid,'bacbench')
        for s in BEND2_FILES:
            tid='bend-'+('prior' if s['file'].startswith('prior') else 'atlas' if s['file'].startswith('atlas') else 'tissue' if s['file'].startswith('gtex') else 'cell-selective' if s['file'].startswith('siraj_selective') else 'context')
            file='src/bend2/_data/'+s['file'];repo='machinelearninglifescience/BEND2';rev='3ab8ae98109a1f37e1ea5091cff1006eead7ebbf'
            statement='Complete bundled file inspected: '+json.dumps({k:v for k,v in s.items() if k not in ['file','sha256']},ensure_ascii=False)+'.'
            eid=self.code('bend2-file-'+s['file'].replace('.','-'),repo,rev,file,statement,local='research/artifacts/final-audit/existing-bend2',kind='dataset-file')
            self.row('evidence',eid)['basis']='data'
            self.dataset_resource(tid,repo,rev,eid,'bend',file=file,host='github',note='Actual bundled evaluation inputs, labels or fixed preparation references; model weights are not included.')
        self.dataset_resource('bgcs-cds','GenAIBio/BGCs-Bench','2337f657f815aa2f41117b70e79d62b192c7f6fe','final-bgcs-data','bgcs',file='data.zip',host='github',note='Actual 87-member dataset archive with sequence/metadata and dense CDS labels; released code has a separately documented fold-column mismatch.')
        for tid in ['bgcs-biosynthetic','bgcs-taxonomy']:self.dataset_resource(tid,'GenAIBio/BGCs-Bench','2337f657f815aa2f41117b70e79d62b192c7f6fe','final-bgcs-data',file='data.zip',host='github')
        for tid in ['bgc-coarse','bgc-fine','bgc-chem','bgc-retrieval','bgc-adomain']:
            eid=next(v['evidence_id'] for v in self.d['variants'] if v['task_id']==tid)
            self.dataset_resource(tid,'Nugkta/bgc-bench','f64c7f6eb6d3910cc7b4434cdc114dc7501305b1',eid,'bgc')
        for t in self.members('dgeb'):
            for v in [v for v in self.d['variants'] if v['task_id']==t['id'] and '/datasets/' in (v.get('notes') or '')]:
                repo=v['notes'].split('/datasets/')[1].split('/tree/')[0];part='test' if any(s['repo']==repo and '/test-' in s['file'] for s in DGEB_FILES) else 'train';eid='final-dgeb-'+repo.split('/')[-1]+'-'+part
                self.dataset_resource(t['id'],repo,v['dataset_revision'],eid,'dgeb')

    def final_details(self):
        # Source reviews distinguish publication denominators from raw-file measurements.
        plantbase = ROOT / 'research/artifacts/final-audit/existing-plantcad'
        for sid, title, file, url, version, kind in [
            ('final-plantcad-supplement', 'PlantCAD2 supplemental figures S1–S17', 'supplementary/mmc1.pdf', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13576720/#supplementary-material', 'Cell Genomics journal supplement', 'paper-supplement'),
            ('final-plantcad-expression-table', 'PlantCAD2 Table S9: gene expression performance', 'supplementary/mmc10.xlsx', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13576720/#supplementary-material', 'Cell Genomics Table S9', 'dataset-file'),
            ('final-plantcad-code-archive', 'PlantCAD2 paper-associated code archive', 'plantcad2_v1.0.0.zip', 'https://zenodo.org/records/20971052', 'PlantCAD2 v1.0.0 / Zenodo 20971052', 'repository-archive'),
            ('final-plantcad-pretrain-card', 'PlantCAD2 pretraining release revision notice', 'pretraining-README.md', 'https://huggingface.co/datasets/plantcad/Angiosperm_65_genomes_8192bp/blob/4a444fff5520b992aa978d92a5af509a81977098/README.md', '4a444fff5520b992aa978d92a5af509a81977098', 'dataset-card'),
        ]:
            path = plantbase / file
            self.put('sources', dict(id=sid, title=title, kind=kind, url=url, version=version,
                retrieved=DATE, sha256=INSPECTIONS['source_file_sha256'][str(path.relative_to(ROOT))],
                local_path=str(path.relative_to(ROOT)), availability='available',
                notes='Complete supplemental file or archive inventory inspected.'))
        potato = self.ev('final-plantcad-potato-counts', 'final-plantcad-supplement', 'Figure S3, supplemental PDF page 4',
            'Figure S3 reports conserved/neutral counts by potato genomic context: CDS 180507/19001; intron 110925/40745; upstream 27659/23852; downstream 20099/16463; intergenic 22019/63054; transposable element 6290/204384. These are plotted publication denominators, not an independent coordinate-file recount. GERP target thresholds are >1.5 and <0 in the main text.', 'paper')
        tid='plantcad2-potato-gerp'; t=self.row('tasks',tid)
        t.update(input_description='Potato SNP-centered genomic context, scored by reference-allele likelihood; exact released sequence/coordinate manifest is not supplied in the inspected named task release.',
            limitations='Full main text and supplemental Figure S3 reviewed; context-specific class counts are reported in the figure. No matching potato configuration occurs in the 12-configuration HF zero-shot release or paper-associated code archive. Reference coordinates and exact per-model scored windows cannot be reconstructed from the plotted results.')
        for context,positive,negative in [('cds',180507,19001),('intron',110925,40745),('upstream',27659,23852),('downstream',20099,16463),('intergenic',22019,63054),('te',6290,204384)]:
            vid=tid+'-'+context; self.row('variants',vid)['notes']='Figure S3 genomic-context stratum; publication class denominators are explicitly recorded. No raw per-example target manifest is supplied in the inspected named release.'
            for label,n in [('conserved',positive),('neutral',negative)]:
                self.put('counts',dict(id='final-'+tid+'-'+context+'-'+label,task_id=tid,value=n,unit='variant sites',split=context+' / '+label,evidence_id=potato,qualifier='Reported directly in Figure S3; not independently counted from raw variant coordinates.',method='reported',variant_id=vid,protocol_id=None))
        self.limit('tasks',tid,'coordinate_manifest','not-released','No potato-specific coordinate/sequence configuration occurs in the inspected 12-configuration HF zero-shot release or paper-associated code archive.',potato)
        self.field('tasks',tid,'counts',potato,'Previously absent class counts read directly from the primary supplemental figure.')
        self.review('tasks',tid,'Full paper, supplemental figure and released dataset/code inventories reviewed; plotted class denominators and absent per-example files distinguished.',[potato,t['evidence_id']],t['limitations'])
        inventory = self.ev('final-plantcad-extra-release-inventory','final-plantcad-code-archive','All 269 archive members; fine-tuning loader and task configuration inventory',
            'The complete paper-associated v1.0.0 archive has 269 members. The released fine-tuning loader names the seven HF task configurations. No potato GERP, maximum-across-tissue expression or Arabidopsis-to-maize expression-transfer input/label files are included. Table S9 separately reports maximum-expression performance; source absence does not negate the paper endpoint.', 'code')
        for tid in ['plantcad2-ft-maximum-expression','plantcad2-ft-arabidopsis-expression-transfer']:
            self.field('tasks',tid,'limitations',inventory,'Complete archive inventory checked; adjacent expression targets are not substituted.')
        maxexpr=self.ev('final-plantcad-max-expression-table','final-plantcad-expression-table','Table S9 / Max expression across tissues columns',
            'Table S9 explicitly reports maximum expression across tissues as regression, with Spearman, Pearson, R2, MAE and MSE for validation and NAM test; it does not provide row counts or per-gene labels for that target.', 'data')
        self.field('tasks','plantcad2-ft-maximum-expression','task_type',maxexpr,'Independent supplemental confirmation that the extra endpoint is regression.')
        card=self.ev('final-plantcad-pretraining-release','final-plantcad-pretrain-card','Revision Notice and Dataset Structure',
            'The current pretraining dataset card says it replaced revision b5b4eadfd32c6baea27a3e6fb7275ea34f064e87 to correct duplicated sequences. Current revision 4a444fff5520b992aa978d92a5af509a81977098 contains train/validation/test Arrow directories. The inspected card and pretraining methods do not state a chromosome-, species- or homology-disjoint partition construction, nor identify which release revision underlies each published MLM diagnostic.', 'documentation')
        for suffix in ['random','central']:
            p=self.row('protocols','plantcad2-pretraining-mlm-'+suffix)
            p['split_rule']=('Mask 15% of nucleotides in the paper-designated held-out sequences.' if suffix=='random' else 'Mask one central token and compare 512/1024/2048/4096/8192-bp contexts on the paper-designated evaluation sequences.')+' The current public pretraining release provides named train/validation/test partitions; their biological grouping and identity with historical model-run partitions are not specified.'
            self.limit('protocols',p['id'],'historical_partition_identity','not-reported','The public pretraining dataset was replaced after duplicate correction. Neither card nor paper binds the MLM diagnostic to an exact release revision or supplies a biological grouping rule.',card)
        self.dataset_resource('plantcad2-pretraining-mlm','plantcad/Angiosperm_65_genomes_8192bp','4a444fff5520b992aa978d92a5af509a81977098',card,'plantcad2-zero',note='Current corrected pretraining dataset; not asserted to be the exact historical MLM evaluation cohort.')
        self.review('tasks','plantcad2-pretraining-mlm','Full MLM diagnostic methods, code loader and current release revision notice reviewed; masking protocols, context lengths and unspecified historical cohort identity distinguished.',[card,self.row('tasks','plantcad2-pretraining-mlm')['evidence_id']],self.row('tasks','plantcad2-pretraining-mlm')['limitations'])
        # GENEB's actual files contain sequence and scalar label, not a biological grouping key.
        for p in self.d['protocols']:
            if p['id'].startswith('geneb-') and p.get('split_unit')=='sequence; upstream grouping pending':
                p['split_unit']='released sequence row; source-specific biological grouping is not encoded in the repackaged CSV'
                self.limit('protocols',p['id'],'repackaged_grouping_manifest','not-released','Complete pinned GENEB train/test CSVs contain sequence and label only. Upstream chromosome, accession and homology membership is not included; original/revised source semantics are retained separately.', 'geneb-spec')
        # Unambiguous assay-source metadata; the complete protein and nucleotide libraries remain separate.
        for a in PROTEINGYM_RNAGYM:
            tid='rnagym-'+a['id'].lower().replace('_','-'); eid='final-rnagym-assay-'+a['id'].lower().replace('_','-')
            self.dataset_resource(tid,'OATML-Markslab/ProteinGym','144fe22b07dfaeec2b366f2346203a9838a55b4c',eid,file='reference_files/'+a['file'],host='github',note='Exact upstream protein assay identity and phenotype metadata, not the RNAGym nucleotide fitness library.',kind='manifest',relation='identity-manifest')
        for slug in ['dnase_propensity','ccre_propensity','cons30','cons100','gpra_c','gpra_d','cadd_snv','clinvar_snv']:
            spec=next(s for s in GUANINE_FILES if s['repo']=='guanine/'+slug)
            eid='final-guanine-'+slug+'-'+spec['file'].split('/')[-2]+'-'+spec['file'].split('/')[-1].split('.')[0]
            self.dataset_resource('guanine-'+slug,spec['repo'],spec['revision'],eid,'guanine',note='Native GUANinE release; few-shot/development/test schemas were scanned. Most test targets are withheld.')
        self.final_taxonomy()
        # CENO repository explicitly distributes code, not full task cohorts.
        cpath=ROOT/'research/artifacts/final-audit/existing-ceno/README.md'
        rev='eec2158eaed3c4d116072da73f99d7be030b3ffb'
        self.put('sources',dict(id='final-ceno-code-release-source',title='CENO released code and data availability',kind='repository-file',url=f'https://github.com/CladeTeam/CENO/blob/{rev}/README.md',version=rev,retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][str(cpath.relative_to(ROOT))],local_path=str(cpath.relative_to(ROOT)),availability='available',notes='README and full repository tree inspected.'))
        ce=self.ev('final-ceno-code-release','final-ceno-code-release-source','README / code-only scope; generation, finetune and vep directories',
            'The repository identifies its scope as code only. The VEP example is a small TraitGym input example, not a complete CENO-specific benchmark cohort. Source evaluator/generation recipes do not constitute release of complete eQTL, structural-design or generated-enhancer manifests.', 'code')
        self.put('data_resources',dict(id='final-ceno-evaluation-code',source_id='final-ceno-code-release-source',title='CENO evaluation and generation code',kind='evaluation-code',host='github',url=f'https://github.com/CladeTeam/CENO/tree/{rev}',revision=rev,availability='public',evidence_id=ce,notes='Code-only release. Small illustrative TraitGym input is not the full CENO benchmark data.'))
        self.put('evaluation_resources',dict(evaluation_id='ceno-evals',resource_id='final-ceno-evaluation-code',relation='evaluation-code',evidence_id=ce,note='Released source code; dataset availability is assessed separately.'),('evaluation_id','resource_id','relation'))

    def final_taxonomy(self):
        import copy
        for tax in [345632,483547,200940,945030,860625,269797,2763]:
            path=ROOT/f'research/artifacts/final-audit/existing-taxonomy/{tax}.json'
            self.put('sources',dict(id=f'final-taxonomy-{tax}-source',title=f'Official UniProt taxonomy record {tax}',kind='taxonomy',url=f'https://rest.uniprot.org/taxonomy/{tax}',version='Live primary taxonomy snapshot 2026-11-27',retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][str(path.relative_to(ROOT))],local_path=str(path.relative_to(ROOT)),availability='available',notes='Exact taxon and full lineage inspected; scientific task membership is supplied separately by released label metadata.'))
        taxev=self.ev('final-geneb-geobacter-taxonomy','final-taxonomy-345632-source','Exact species and lineage; companion Geoalkalibacter record 483547',
            'Geobacter pickeringii (345632) and Geoalkalibacter subterraneus (483547) are bacterial species in current Thermodesulfobacteriota (200940). The upstream Deep4mC/DeepTorrent task source names these species explicitly; G. abbreviations are not interpreted as Archaea. Pseudomonadati is a kingdom in the primary lineage; it is distinct from the phylum Pseudomonadota.', 'data')
        def branch(node,name,tax,parent,group,label):
            self.put('populations',dict(id=node,name=name,rank='phylum',parent_id='bacteria' if parent=='bacteria' else 'archaeplastida',ncbi_taxid=tax,notes='Primary taxonomy lineage of released evaluation inputs.'))
            n=copy.deepcopy(self.row('coverage_nodes','pseudomonadota'));n.update(id=node,parent_id=parent,population_id=node,label=name,scientific='',rank='Phylum',note='',jump=None,sources_json=json.dumps([f'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={tax}']))
            self.put('coverage_nodes',n)
            path=['bacteria',node] if group=='bacteria' else ['eukaryota','archaeplastida',node]
            for view in ['clade','species']:
                r=copy.deepcopy(self.row('coverage_rows','clade:pseudomonadota' if view=='clade' else 'species:bacillota'))
                md=json.loads(r['metadata_json']);md.update(id=node,label=name,displayLabel=name,common='',note='Named evaluation species; no claim of complete phylum coverage.',group=group,groupLabel=label,node=node,clade=node,cladeLabel=name,kind='clade',path=[node],displayParent=node,displayPath=path,displayLineage=' → '.join(path[:-1]+[name]),lineageLabel=name,members=[])
                r.update(id=view+':'+node,row_key=node,node_id=node,population_ids_json='[]',metadata_json=json.dumps(md));self.put('coverage_rows',r)
        def named(tid,pid,name,tax,node,eid,note):
            self.put('populations',dict(id=pid,name=name,rank='species',parent_id=node,ncbi_taxid=tax,notes=note))
            rid='allSpecies:'+node+'-sp-'+str(tax);row=copy.deepcopy(self.row('coverage_rows','allSpecies:pseudomonadota-sp-562'));md=json.loads(row['metadata_json']);parent=json.loads(self.row('coverage_rows','clade:'+node)['metadata_json'])
            md.update(id=node+'-sp-'+str(tax),label=name,displayLabel=name,common='',note=note,node=node,clade=node,cladeLabel=parent['label'],members=[name],path=parent['path'],displayParent=node,displayPath=parent['displayPath'],displayLineage=parent['displayLineage'],lineageLabel=parent['label'],group=parent['group'],groupLabel=parent['groupLabel'])
            row.update(id=rid,row_key=node+'-sp-'+str(tax),node_id=node,population_ids_json=json.dumps([pid]),metadata_json=json.dumps(md));self.put('coverage_rows',row)
            self.d['coverage_mappings']=[m for m in self.d['coverage_mappings'] if not(m['task_id']==tid and m['population_id'] is None)]
            m=copy.deepcopy(next(x for x in self.d['coverage_mappings'] if x['population_id']=='ecoli'));m.update(id='final-'+tid+'-mapping-'+pid,task_id=tid,population_id=pid,basis='released sequence-origin metadata',evidence_id=eid,supporting_json=json.dumps([eid]),clade_row='clade:'+node,species_row='species:'+node,all_species_row=rid,metadata_json=json.dumps(dict(row=node,name=name,species=name,speciesId=tax,clade=node,allSpeciesRow=rid.removeprefix('allSpecies:'),url=self.row('evidence',eid)['url'],taxonomy=f'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={tax}',note=note)));self.put('coverage_mappings',m)
            self.put('task_populations',dict(task_id=tid,population_id=pid,variant_id=None,relation='sequence-origin',coverage=note,evidence_id=eid),('task_id','population_id','relation'))
        branch('thermodesulfobacteriota','Thermodesulfobacteriota',200940,'bacteria','bacteria','Bacteria')
        for tid,pid,name,tax in [('geneb-deep4mc-g.pickeringii-4mc','taxon-345632','Geobacter pickeringii',345632),('geneb-deep4mc-g.subterraneus-4mc','taxon-483547','Geoalkalibacter subterraneus',483547)]:
            named(tid,pid,name,tax,'thermodesulfobacteriota',taxev,'Upstream Deep4mC/DeepTorrent explicitly names this 4mC-site sequence source; current primary taxonomy resolves its bacterial lineage.')
            self.field('tasks',tid,'populations',taxev,'Exact introducing-source species name and official taxon lineage resolve the abbreviated configuration name.')
        # MIBiG includes plant, archaeal and red-algal entries, not only bacteria/fungi.
        bgcev=self.ev('final-bgc-source-taxonomy','src-bgc-card','Complete provenance/mibig_metadata.csv joined to task split/descriptor IDs',
            'The coarse source cohort includes eight Arabidopsis entries (TaxID 3702), one Methanosarcina barkeri Fusaro (269797) and red algae Digenea simplex (945030) / Chondria armata (860625). Descriptor eligibility retains five Arabidopsis entries and each archaeal/red-algal entry; retrieval random split retains those same five Arabidopsis and three other entries. These are source-cohort memberships, not species-held-out tests or every model’s final aligned cohort.', 'data')
        branch('rhodophyta','Red algae',2763,'archaeplastida','archaeplastida','Archaeplastida')
        self.row('populations','rhodophyta')['name']='Rhodophyta';self.row('coverage_nodes','rhodophyta')['scientific']='Rhodophyta'
        for tid in ['bgc-coarse','bgc-chem','bgc-retrieval']:
            self.population(tid,'arabidopsis',bgcev,'Arabidopsis BGC IDs occur in the released target-eligible source cohort; not inferred from model pretraining.')
            self.population(tid,'archaea',bgcev,'Released eligible source includes Methanosarcina barkeri Fusaro, TaxID 269797; domain-level display retains explicitly named origin in source evidence.')
            for pid,name,tax in [('taxon-945030','Digenea simplex',945030),('taxon-860625','Chondria armata',860625)]:named(tid,pid,name,tax,'rhodophyta',bgcev,'Released target-eligible MIBiG BGC source; exact taxon ID from metadata, red-algal lineage verified in official taxonomy.')
        for pid,name,tax in [('taxon-945030','Digenea simplex',945030),('taxon-860625','Chondria armata',860625)]:
            named('bgc-fine',pid,name,tax,'rhodophyta',bgcev,'Both red-algal IDs occur in the released fine-label five-fold table; Arabidopsis and the Methanosarcina entry are absent from that target subset.')
        for tid in ['bgcs-biosynthetic','bgcs-taxonomy','bgcs-cds']:
            self.population(tid,'arabidopsis','final-bgcs-data','Complete archive metadata identifies Arabidopsis BGCs; the dense annotation subset includes BGC0002397 and BGC0002398.')
            if tid!='bgcs-cds':
                self.population(tid,'archaea','final-bgcs-data','Complete sequence-cohort metadata includes a Methanosarcinaceae BGC, TaxID 269797.')
                for pid,name,tax in [('taxon-945030','Digenea simplex',945030),('taxon-860625','Chondria armata',860625)]:named(tid,pid,name,tax,'rhodophyta','final-bgcs-data','Sequence-cohort metadata identifies red-algal BGC inputs; not transferred into the distinct dense annotation subset.')
