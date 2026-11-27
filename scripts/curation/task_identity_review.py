"""Canonical dataset×target identities and scoped model/publication source reviews.

Release-specific example selection, fitted heads and score transformations remain in
linked variants/protocols. Identity here never implies equal historical model runs.
"""
import json
from scripts.curation.existing_audit import Audit, ROOT, DATE, INSPECTIONS

GB_DATASETS = (
    'human_nontata_promoters', 'drosophila_enhancers_stark',
    'dummy_mouse_enhancers_ensembl', 'human_enhancers_cohn',
    'human_enhancers_ensembl', 'demo_human_or_worm',
    'human_ensembl_regulatory', 'human_ocr_ensembl',
    'demo_coding_vs_intergenomic_seqs',
)


def populate(d):
    a = IdentityReview(d)
    a.genomic_benchmarks()
    a.gue()
    a.recovery()
    a.model_publications()
    return d


def unique_text(*values):
    return ' '.join(dict.fromkeys(v.strip() for v in values if v and v.strip()))


class IdentityReview(Audit):
    def merge(self, old_id, new_id, evidence_id, evaluation_id, reason):
        """Redirect every task foreign key, retaining independent release records.

        Composite-key rows are coalesced with their source evidence retained in
        field_evidence. Surviving output rows keep their classification; identical
        source target units cannot create two task_output rows for one task.
        """
        self.d.setdefault('task_redirects', [])
        old = next((r for r in self.d['tasks'] if r['id'] == old_id), None)
        new = self.row('tasks', new_id)
        self.put('task_redirects', dict(id=old_id, evaluation_id=evaluation_id,
            replacement_task_id=new_id, reason=reason))
        if old is None:
            return
        old_variants = [r for r in self.d['variants'] if r['task_id'] == old_id]
        default_variant = next((v['id'] for v in old_variants if v['id'] == old_id+'-release'), None)
        if default_variant:
            for r in self.d['protocols']:
                if r['task_id'] == old_id and r.get('variant_id') is None:
                    r['variant_id'] = default_variant
            for r in self.d['evaluation_tasks']:
                if r['task_id'] == old_id and r.get('variant_id') is None:
                    r['variant_id'] = default_variant
        # Every direct task reference, including newly introduced linked tables.
        for table, rows in self.d.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if row.get('task_id') == old_id:
                    row['task_id'] = new_id
                if row.get('entity_table') == 'tasks' and row.get('entity_id') == old_id:
                    row['entity_id'] = new_id
        self.d['tasks'] = [r for r in self.d['tasks'] if r['id'] != old_id]
        # IDs in these tables are polymorphic evidence targets. Remap references
        # when an equivalent one-per-task or one-per-feature row is coalesced.
        removed_ids = {}
        compound = {
            'evaluation_tasks': ('evaluation_id','task_id'),
            'task_populations': ('task_id','population_id','relation'),
            'task_categories': ('task_id','category_id','relation'),
            'task_resources': ('task_id','resource_id','relation'),
            'task_tracks': ('task_id','track_id'),
            'task_outputs': ('task_id',),
            'task_feature_scopes': ('task_id','feature_id'),
            'source_reviews': ('entity_table','entity_id'),
            'field_evidence': ('entity_table','entity_id','field','evidence_id'),
        }
        for table, keys in compound.items():
            if table not in self.d:
                continue
            kept = []
            index = {}
            # Native canonical metadata appears first in authoring data; stable
            # sorting makes that preference explicit for outputs and scopes.
            rows = self.d[table]
            if table in ['task_outputs','task_feature_scopes']:
                rows = sorted(rows, key=lambda r: old_id in r.get('id',''))
            for row in rows:
                key = tuple(row.get(k) for k in keys)
                first = index.get(key)
                if first is None:
                    index[key] = row
                    kept.append(row)
                    continue
                if row.get('id') and first.get('id'):
                    removed_ids[(table,row['id'])] = first['id']
                if table == 'source_reviews':
                    first['scope'] = unique_text(first['scope'],row['scope'])
                    first['limitations'] = unique_text(first['limitations'],row['limitations'])
                    first['evidence_ids_json'] = json.dumps(list(dict.fromkeys(
                        json.loads(first['evidence_ids_json'])+json.loads(row['evidence_ids_json'])
                    )))
                elif table == 'field_evidence':
                    first['note'] = unique_text(first.get('note'),row.get('note'))
                else:
                    for col in ['note','rationale','coverage','limitations']:
                        if col in row:
                            first[col] = unique_text(first.get(col),row.get(col))
                    # Composite schemas store a single evidence pointer. Retain
                    # every additional source as explicit field-level evidence.
                    if row.get('evidence_id') and row['evidence_id'] != first.get('evidence_id'):
                        self.field('tasks',new_id,table,row['evidence_id'],
                            'Merged source record '+old_id+': '+json.dumps(row,sort_keys=True))
                    if row.get('variant_id') != first.get('variant_id') and row.get('variant_id'):
                        if 'note' in first:
                            first['note'] = unique_text(first['note'],'Additional linked release variant: '+row['variant_id']+'.')
            self.d[table] = kept
        for rows in self.d.values():
            if not isinstance(rows,list):
                continue
            for row in rows:
                key = (row.get('entity_table'),row.get('entity_id'))
                if key in removed_ids:
                    row['entity_id'] = removed_ids[key]
        # A remapped polymorphic reference can now share an existing key.
        self.coalesce_field_evidence()
        self.field('tasks',new_id,'dataset_identity',evidence_id,reason)
        review = next((r for r in self.d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==new_id),None)
        if review:
            review['scope'] = unique_text(review['scope'],'Native source and repackaged dataset×target identity reviewed; release-specific rows and protocols remain linked variants.')
            review['evidence_ids_json'] = json.dumps(list(dict.fromkeys(json.loads(review['evidence_ids_json'])+[evidence_id])))
        new['status'] = 'artifact-audited' if old['status']=='artifact-audited' else new['status']

    def coalesce_field_evidence(self):
        out = {};keys = ('entity_table','entity_id','field','evidence_id')
        for row in self.d['field_evidence']:
            key = tuple(row[k] for k in keys)
            if key in out:
                out[key]['note'] = unique_text(out[key].get('note'),row.get('note'))
            else:
                out[key] = row
        self.d['field_evidence'] = list(out.values())

    def genomic_benchmarks(self):
        for name in GB_DATASETS:
            tid = 'gb-'+name
            old = 'geneb-katarinagresova-genomic-benchmarks-'+name.replace('_','-')
            facts = [r for r in INSPECTIONS['identity_comparisons']['GB_GENEB'] if r['dataset']==name]
            assert len(facts)==2 and all(r['geneb_rows_all_present_with_same_label'] for r in facts)
            eids = []
            for fact in facts:
                spec = dict(repo=fact['repo'],revision=fact['revision'],file=fact['file'],sha256=fact['sha256'])
                statement = f"Complete native {fact['part']} file contains {fact['rows']:,} sequence/label rows; GENEB contains {fact['geneb_rows']:,}. "
                statement += ('All sequence/label pairs match rowwise.' if fact['rowwise_sequence_label_equal'] else 'All GENEB sequence/label pairs are an exact multiplicity-preserving subset of this native file; GENEB applies its documented 100,000-row cap.')
                eid = self.data('identity-gb-'+name+'-'+fact['part'],spec,statement)
                eids.append(eid)
                source = self.row('sources',self.row('evidence',eid)['source_id'])
                source['local_path'] = 'research/artifacts/final-audit/existing-identity/'+name+'/'+fact['file']
                self.field('tasks',tid,'dataset_identity',eid,'Compared every native sequence/label row with the complete pinned GENEB file; column name changes seq→text do not change the target.')
            eid = self.ev('identity-gb-'+name,'geneb-release-card','Pinned task index and train/test distribution; complete native/repackaged comparisons',
                'GENEB config katarinagresova_Genomic_Benchmarks_'+name+' reuses this native Genomic Benchmarks dataset and prediction target. Both released tests match rowwise; training is identical or a documented-size exact label-preserving subset. Independent readout fitting, evaluation membership and release counts are preserved as linked variants.','data')
            self.merge(old,tid,eid,'gb','Same named upstream dataset and prediction target; full native/GENEB sequence-label comparison confirms shared identity. Release-specific subsampling and protocols remain separate.')
            t = self.row('tasks',tid)
            t['description'] = 'Predict '+t['target'].lower()+' from the source-defined sequence windows. Native Genomic Benchmarks and GENEB releases share this dataset×target; source partitions and GENEB subsampling/readout remain separate linked variants.'
            t['task_type'] = 'multiclass classification' if name=='human_ensembl_regulatory' else 'binary classification'
            t['limitations'] = 'Complete native and GENEB releases compared for sequence/label identity. GENEB preserves the native test and uses either the same training rows or a 100,000-row subset. These sequence-only tables do not independently reconstruct genomic coordinates, homology separation or historical model-training overlap. Dataset-specific source construction remains distinct across this suite.'
            self.review('tasks',tid,'Complete native Parquet and GENEB train/test CSV comparison, documented source identity and label-preserving subsampling reviewed. All release-specific counts, fitting protocols and memberships retained.',eids+[eid,t['evidence_id'],'geneb-spec'],t['limitations'])
            nativevid = tid+'-native-hf'
            self.put('variants',dict(id=nativevid,task_id=tid,name='Native Genomic Benchmarks HF release',dataset_revision=facts[0]['revision'],context='Source dataset before GENEB training subsampling.',input_length='Dataset-specific windows; complete files compared.',target_count=3 if name=='human_ensembl_regulatory' else 2,target_unit='classes',notes='Native Parquet sequence/label rows retained. This release is not inferred to have a common chromosome or homology split with other Genomic Benchmarks configurations.',evidence_id=eids[0]))
            for fact,e in zip(facts,eids):
                self.count(tid,fact['rows'],'sequence rows','native HF / '+fact['part'],e,nativevid,suffix='native-hf-'+fact['part'],qualifier='Complete native file count; GENEB counts remain attached to its own release variant.')
            self.dataset_resource(tid,facts[0]['repo'],facts[0]['revision'],eids[0],'gb',note='Native HF dataset, compared completely with GENEB. Counts and release identity are distinct from the source paper’s original construction metadata.')
            for p in self.d['protocols']:
                if p['task_id']==tid and p['id'].startswith(old) and not p.get('variant_id'):
                    p['variant_id']=old+'-release'

    def gue(self):
        for mark in ['H3','H4']:
            tid='gue-'+mark;old='geneb-leannmlindsey-gue-emp-'+mark.lower()
            facts=INSPECTIONS['identity_comparisons']['GUE_GENEB'][mark]
            assert all(v['rowwise_sequence_label_equal'] for v in facts.values())
            eid=self.ev('identity-gue-'+mark,'geneb-release-card','Pinned GUE-emp task index; complete native GUE/GENEB train/test sequence-label comparisons',
                f"Native GUE emp_{mark} and GENEB leannmlindsey_GUE_emp_{mark} have identical ordered sequence/label rows: train {facts['train']['native_rows']:,}, test {facts['test']['native_rows']:,}. GENEB excludes the native dev split. Whole-file hashes differ only with representation changes, so identity is established from parsed pairs, not filenames. This does not equate GUE with original NT yeast histone cohorts.",'data')
            self.merge(old,tid,eid,'gue','Same GUE empirical yeast histone dataset×target; every native train/test sequence and label matches GENEB in the same order. Native dev and release-specific protocols remain distinct.')
            t=self.row('tasks',tid)
            t['description']='Binary '+mark+' histone annotation in yeast sequence windows. Native GUE, GENEB, GenBench and DNA Foundation reuse share this target; released partitions, model heads and selection protocols remain linked separately.'
            t['limitations']='Native GUE and GENEB train/test sequence-label rows match exactly; GENEB excludes the native dev partition. Source files do not supply sample coordinates or a homology-group manifest. Original NT yeast histone tasks remain separate because that cohort identity was not established.'
            review=next(r for r in self.d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==tid)
            review['limitations']=t['limitations']

    def recovery(self):
        repo='GenerTeam/GENERator';rev='5132e2c35da5d5e9a7dcec7484901be4de864bf6'
        local='research/artifacts/final-audit/existing-identity/sequence_recovery.py'
        path=ROOT/local;sid='identity-generator-recovery-code-source'
        self.put('sources',dict(id=sid,title='Shared GENERator v1/v2 sequence recovery adapter',kind='repository-file',url=f'https://github.com/{repo}/blob/{rev}/src/tasks/downstream/sequence_recovery.py',version=rev,retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][local],local_path=local,availability='available',notes='One official adapter exposes the shared benchmark; historical publication cohorts are not identified by a per-example manifest.'))
        eid=self.ev('identity-generator-recovery',sid,'parse_args; calculate_accuracy; parquet load and output',
            'The official GENERator repository documents both v1 and v2 and uses the same sequence_recovery.py. The adapter defaults to a v2 checkpoint and GenerTeam/sequence-recovery; it keeps the rightmost 6144 bp and scores the first 30 decoded nucleotides. Both full reports define this RefSeq continuation target. Shared dataset×target identity does not establish byte-identical historical sampled cohorts.','code')
        for tid,paper,e in [('generator-recovery','generator','final-generator-protocol'),('generator2-recovery','generator2','final-generator2-protocol')]:
            # Existing protocols have no cohort variant, so create explicit paper
            # variants before redirecting to the shared biological target.
            if not any(t['id']==tid for t in self.d['tasks']):continue
            vid=tid+'-paper-cohort'
            self.put('variants',dict(id=vid,task_id=tid,name=('GENERator v1' if paper=='generator' else 'GENERator v2')+' reported recovery protocol',dataset_revision=None,context='RefSeq natural continuation; historical per-example cohort identity not supplied.',input_length='6144 bp prompt; next 30 bp scored',target_count=30,target_unit='reference nucleotide positions',notes='Shared source and target; paper-specific sample/context protocols retained without asserting equal historical sampled rows.',evidence_id=e))
            for p in self.d['protocols']:
                if p['task_id']==tid and p['id']==tid+'-protocol':p['variant_id']=vid
        self.merge('generator2-recovery','generator-recovery',eid,'generator-evals','Same official RefSeq recovery dataset×target and scorer for GENERator v1/v2. Publication-specific cohorts/protocols are linked variants; historical row equality is not claimed.')
        t=self.row('tasks','generator-recovery')
        t['description']='Recover reference nucleotides after a supplied genomic prompt. Main GENERator comparisons use a 6144-bp prompt ending in CDS with at least two-thirds noncoding context and score the next 30 bases. V1, v2 and Carbon scoring protocols are linked separately.'
        t['limitations']='Shared official recovery dataset and target established from the released adapter and both full reports. Historical paper-specific sampled reference accessions/coordinates are not released, so cohort equality across papers and model-pretraining disjointness are not established. Nucleotide recovery is not experimental validation of generated sequence function.'
        self.field('tasks','generator-recovery','dataset_identity',eid,'Paper-specific variants preserve scientific uncertainty about exact sampled cohorts.')
        review=next(r for r in self.d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']=='generator-recovery')
        review['limitations']=t['limitations']
        rid='identity-generator-recovery-code'
        self.put('data_resources',dict(id=rid,source_id=sid,title='Official GENERator sequence recovery adapter',kind='evaluation-code',host='github',url=self.row('sources',sid)['url'],revision=rev,availability='public',evidence_id=eid,notes='Shared v1/v2 source adapter; not a separate biological dataset.'))
        self.put('task_resources',dict(task_id='generator-recovery',resource_id=rid,relation='evaluation-code',variant_id=None,evidence_id=eid,note='6144 bp input default and 30 nt recovery scorer.'),('task_id','resource_id','relation'))
        dataset_rev='3ac1de1be0e4c55dd180c719c1f3805a2cdb9be9';card_path='research/artifacts/final-audit/existing-identity/recovery-README.md'
        card_sid='identity-generator-recovery-card-source';card_url=f'https://huggingface.co/datasets/GenerTeam/sequence-recovery/blob/{dataset_rev}/README.md'
        self.put('sources',dict(id=card_sid,title='Official GENERator recovery dataset card',kind='dataset-card',url=card_url,version=dataset_rev,retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][card_path],local_path=card_path,availability='available',notes='Pinned card and repository file inventory inspected; multi-gigabyte full Parquet data were not downloaded.'))
        card=self.ev('identity-generator-recovery-card',card_sid,'YAML configs; Sequence and Label definition',
            'The official recovery release declares bacteria/eukaryote/others test Parquets, up to 96k-bp source context and the next 128 bp as labels, allowing shorter prompt/output protocols. The card still shows the former next-kmer-prediction loader name. Official current scoring code uses GenerTeam/sequence-recovery and takes a 6144 bp suffix/30 bp target; the publication workload need not equal all public rows.','documentation')
        rid='identity-generator-recovery-data'
        self.put('data_resources',dict(id=rid,source_id=card_sid,title='Official GENERator RefSeq sequence-recovery data',kind='dataset',host='huggingface',url=f'https://huggingface.co/datasets/GenerTeam/sequence-recovery/tree/{dataset_rev}',revision=dataset_rev,availability='public',evidence_id=card,notes='Actual public test Parquet files. Card-level source identity inspected; full large files and historical sampled cohorts were not recounted.'))
        self.put('task_resources',dict(task_id='generator-recovery',resource_id=rid,relation='evaluation-data',variant_id=None,evidence_id=card,note='Native recovery source; model-specific context and output lengths remain protocol variants.'),('task_id','resource_id','relation'))
        for collection in ['generator-evals','generator2-evals','carbon-evals']:
            self.put('evaluation_resources',dict(evaluation_id=collection,resource_id=rid,relation='evaluation-data',evidence_id=eid,note='Shared sequence-recovery source, with separate paper/model-specific protocols.'),('evaluation_id','resource_id','relation'))
        self.limit('tasks','generator-recovery','full_public_recovery_scan','not-retrieved','Complete official card, file inventory and scoring adapters reviewed. The multi-gigabyte Parquet release was not fully downloaded; this source review does not assert an independent full-row recount or a historical paper-cohort reconstruction.',card)

    def model_publications(self):
        architecture=self.ev('final-ceno-model-scope','ceno-paper','Methods 4.1–4.2; Supplementary Tables S1–S2',
            'CENO uses causal Mamba-2/attention/MoE, 512-entry byte vocabulary and 300M/600M/1B total parameters with approximately 100M/200M/400M active per token. OpenGenome2 training progresses from 8192 through 131072 to 1048576 tokens; RegMix uses selected VEP benchmarks for mixture selection. Source corpus splits and stage budgets are reported; trained artifacts and all historical training logs were not independently reconstructed.')
        scopes={
            'ceno':('Architecture, tokenizer, OpenGenome2 source composition and staged context schedules reviewed in full report; all indexed evaluation families reviewed against paper/code where released.',[architecture,'final-ceno-structure-design','final-ceno-enhancer-design','final-ceno-accessibility-oracle','final-ceno-causal-eqtl'],'Released CENO repository is code-only. Paper-reported training stages are not independently reproduced; mixture selection uses a subset of variant benchmarks, so those scores are not untouched pretraining-selection holdouts.'),
            'generator':('Full v5 model/data/tokenization methods, supervised and zero-shot evaluation protocols and wet-lab CRE generation reviewed; pinned downstream implementation and native target releases inspected.',['model-generator','final-generator-protocol','identity-generator-recovery','final-generator-cre-library'],'Historical training corpus membership, per-run command arguments and per-paper sampled RefSeq accession manifests are not released in the inspected material. Parameter labels and published budgets are source-reported, not independently reconstructed training runs.'),
            'generator2':('Full v2 report architecture, six-mer tokenization, factorized nucleotide supervision, genome-compression pretraining and evaluation context/selection methods reviewed; shared recovery adapter inspected.',['model-generator2','final-generator2-protocol','identity-generator-recovery'],'Model-specific paper protocols remain separate from v1. Historical fold IDs, training corpus membership and sampled RefSeq accession lists are not published in the inspected report; no training run was reproduced.'),
            'plantcad2':('Full journal article, supplementary tables, native zero-shot/fine-tuning datasets, model config and GeneCAD legacy/current adaptation evidence reviewed. Architecture, training/tokenization and context properties retain their field-level evidence.',['plantcad2-architecture','plantcad2-corpus','plantcad2-sizes','plantcad2-model-config-ev','plantcad2-context','genecad-release-training-inputs-ev'],'Paper has 676M/694M large-model labels; no tensor parameter recount is claimed. Historical pretraining release predates corrected current dataset. GeneCAD 2025 and 2026 protocols use different encoders/fitting, and are not interchangeable.'),
        }
        for mid,(scope,eids,lim) in scopes.items():
            self.review('models',mid,scope,eids,lim)
        # LOAM's public card is readable while gated config/weights require terms.
        local='research/artifacts/final-audit/existing-identity/loam-README.md'
        sid='final-loam-model-card-source';rev='5e45323881ec1cb4c28c6936bd33a81cd3f3fcf2'
        self.put('sources',dict(id=sid,title='LOAM-624M official model card',kind='model-card',url=f'https://huggingface.co/Soilytix/LOAM-624M/blob/{rev}/README.md',version=rev,retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][local],local_path=local,availability='available',notes='Complete public model card read. Configuration request returned 401; model weights are gated behind terms acceptance.'))
        loam=self.ev('final-loam-model-card',sid,'Model variants; Tokenizer and input preparation; Training and limitations; Benchmark results',
            'Official card reports decoder-only Peri-LN transformers 25.5M–624.2M; single-nucleotide 58-ID vocabulary with only uppercase A/C/G/T trained, 8192-nt context, no learned sequence-boundary special tokens. Training uses 67.5 Gbp from 15640 Microflora Danica species-representative long-read MAGs for approximately one epoch, reverse-complement augmentation and whole-genome partitions without established species-level separation. Probes report best tested layer; variant scoring is zero-shot.','documentation')
        abstract_sid='final-loam-primary-metadata-source'
        abstract_path='research/artifacts/final-audit/existing-identity/loam-api.json'
        self.put('sources',dict(id=abstract_sid,title='LOAM primary bioRxiv metadata and abstract',kind='paper-metadata',url='https://api.biorxiv.org/details/biorxiv/10.64898/2026.09.28.755120',version='v1 / 2026-10-02',retrieved=DATE,sha256=INSPECTIONS['source_file_sha256'][abstract_path],local_path=abstract_path,availability='available',notes='Official bioRxiv API metadata and full abstract retrieved; linked full JATS XML returns429.'))
        abstract=self.ev('final-loam-primary-metadata',abstract_sid,'collection[0] title, authors, date, version, abstract and jatsxml', 'Primary bioRxiv metadata confirms title, authors, DOI, version1 and publication date2026-10-02. Abstract describes25–624M decoder-only models trained on long-read environmental metagenomes, context interventions, hidden-layer probes and homolog-associated variant performance. Full model-methods text is not part of this metadata response.','documentation')
        self.row('papers','loam').update(doi='10.64898/2026.09.28.755120',publication_date='2026-10-02')
        self.review('models','loam','Complete pinned official model card, primary bibliographic identity and indexed BacBench/DGEB/RNAGym evaluation definitions reviewed; source scope distinguishes accessible card/evaluation code from gated configuration/weights.',[loam,abstract,'model-loam','final-bacbench-essential-scorer'],
            'Model config and weights are gated; no terms were accepted or weights inspected. Direct bioRxiv full-text retrieval is inaccessible in this audit environment, so the full model training methods are represented from the official card rather than claimed as independently paper-verified.')
        self.row('sources','loam-paper').update(availability='not-retrieved',notes='Primary report identity and abstract indexed; full HTML/PDF could not be retrieved. Official author model card and evaluation releases are separately inspected sources.')
        self.limit('models','loam','released_config_weights','access-restricted','Public model card is readable; pinned config request returns 401 and release requires acceptance of its Hugging Face access terms. No user identity/terms submission was made.',loam)
        self.limit('papers','loam','full_text_retrieval','not-retrieved','Direct primary bioRxiv HTML and PDF requests return 429 and the browsing service cannot access the DOI target. Indexed evaluation claims and official author model card remain available; this record does not claim a full-paper model-methods inspection.',loam)
        # Paper review is a source audit, not a claim every unindexed result or
        # training artifact has been independently reimplemented.
        paper_sources={
            'ceno':[architecture,'ceno-eval-methods','final-ceno-structure-design','final-ceno-enhancer-design'],
            'generator':['final-generator-protocol','identity-generator-recovery','final-generator-cre-library'],
            'generator2':['final-generator2-protocol','identity-generator-recovery'],
            'loam':[loam,abstract,'model-loam'],
            'plantcad2':['plantcad2-architecture','plantcad2-corpus','plantcad2-sizes','plantcad2-context'],
            'genecad':['genecad-paper-methods','genecad-release-training-inputs-ev'],
            'dart':['dart-eval-methods'],
            'mrna':['final-mrna-paper-targets','final-mrna-split-semantics','final-mrna-probe-semantics'],
            'guanine':['final-guanine-scoring'],
            'geneb':['geneb-spec','geneb-spec'],
            'dgeb':['final-dgeb-scorers','final-dgeb-pairing','final-dgeb-retrieval-contract'],
            'pgb':['final-pgb-primary-methods','final-pgb-native-loader'],
            'bend':['bend-paper-extras','final-bend2-fixed-ridge'],
            'bgc':['final-bgc-substrate-scorer'],
            'bgcs':['final-bgcs-data'],
        }
        # Use explicit extant evidence records; full family reviews supply source
        # links where historical evidence IDs differ across catalogue revisions.
        known={e['id'] for e in self.d['evidence']}
        for pid,preferred in paper_sources.items():
            if not any(p['id']==pid for p in self.d['papers']):continue
            paper=self.row('papers',pid)
            eids=[e for e in preferred if e in known]
            eids+= [r['id'] for r in self.d['evidence'] if r['source_id']==paper['source_id'] and r['basis']=='paper'][:3]
            if not eids:
                raise ValueError('No inspected source evidence for paper '+pid)
            scope='Publication identity, indexed dataset×target definitions, fitting/scoring and reported split/count methods reviewed. Released artifacts and implementation are evaluated separately with field-level source evidence; publication claims are not substituted for measured release rows.'
            limitations='Review covers the indexed catalogue claims; it does not assert reproduction of all model training, all original raw assays or every historical benchmark score.'
            if pid=='loam':
                scope='Primary publication identity, indexed benchmark claims and author model card reviewed; full-paper model-methods inspection is explicitly outside the retrieved source scope.'
                limitations='Primary full-text HTML/PDF requests were blocked; model details derive from the pinned official author card, with release access limitations recorded separately.'
            self.review('papers',pid,scope,list(dict.fromkeys(eids)),limitations)
