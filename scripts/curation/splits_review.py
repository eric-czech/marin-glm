"""Cited split-method survey and bounded release-level overlap inspections."""
from pathlib import Path
import collections
import hashlib
import itertools
import json
import re
from common import Catalogue, ROOT, DATE

REPORT_REV='6ff5201fc1734a76f14d647784de90a4692e849c'
OWN='https://github.com/eric-czech/marin-glm/blob/'+REPORT_REV+'/'
TABLES=['split_strategies','split_protocol_strategies','split_audits','split_audit_tasks','split_partitions','split_comparisons','split_audit_files','split_examples']

def slug(s):return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def short(s):return hashlib.sha256(s.encode()).hexdigest()[:16]


class Splits:
    def __init__(self,d):
        self.d=d;self.c=Catalogue(d);self.case_ids={};self.evidence={};self.resources={r['id']:r for r in d['data_resources']}
        self.protocols={r['id']:r for r in d['protocols']};self.tasks={r['id']:r for r in d['tasks']}
        for table in TABLES:d[table]=[]
        for name in ['split-inspections','geneb-artifact-inspections','dnafoundation-artifact-inspections','rnagym-artifact-inspections','existing-benchmark-inspections','plantcad-cell-artifact-inspections','plantcad-translation-artifact-inspections']:
            path='data/'+name+'.json';self.c.source('splits-'+name,name.replace('-',' '),OWN+path,'inspection-report',REPORT_REV,path=path,
                notes='Inspection evidence, not a new input dataset. Methods, source revisions and per-file hashes are retained in this committed report.')
        self.report=json.loads((ROOT/'data/split-inspections.json').read_text())

    def evidence_for(self,report,key,text):
        eid='split-evidence-'+short(report+'|'+key)
        self.c.evidence(eid,'splits-'+report,key,text,'data',OWN+'data/'+report+'.json')
        return eid

    def audit(self,id,title,release,ev,scope,method,conclusion,limits,evaluation=None,status='measured',order=100):
        self.c.put('split_audits',dict(id=id,title=title,release_name=release,evaluation_id=evaluation,status=status,finding='limited',
            scope=scope,method=method,conclusion=conclusion,limitations=limits,checked=DATE,evidence_id=ev,sort_order=order))
        self.evidence[id]=ev
        return id

    def link(self,id,task,protocol=None,variant=None,note='The audit applies to the named release/cohort only; shared target identity does not establish the exact original scored rows of every model.'):
        assert task in self.tasks,task
        if protocol:assert self.protocols[protocol]['task_id']==task,(id,protocol,task)
        self.c.put('split_audit_tasks',dict(id=id+'-link-'+short(task+'|'+str(protocol)+'|'+str(variant)),audit_id=id,task_id=task,
            protocol_id=protocol,variant_id=variant,note=note,evidence_id=self.evidence[id]))

    def partition(self,id,name,rows=None,unique=None,unit='released rows',detail=''):
        pid=id+'-partition-'+slug(name)
        self.c.put('split_partitions',dict(id=pid,audit_id=id,name=name,row_count=rows,unique_sequences=unique,row_unit=unit,detail=detail,evidence_id=self.evidence[id]))
        return pid

    def comparison(self,id,left,right,kind,n,unit='distinct exact sequence strings',la=None,ra=None,note=''):
        cid=id+'-'+slug(left)+'-'+slug(right)+'-'+kind
        self.c.put('split_comparisons',dict(id=cid,audit_id=id,left_partition_id=id+'-partition-'+slug(left),right_partition_id=id+'-partition-'+slug(right),
            overlap_type=kind,shared_count=n,unit=unit,left_affected=la,right_affected=ra,note=note,evidence_id=self.evidence[id]))
        return cid

    def file(self,id,url,sha=None,bytes=None,rows=None,split=None,revision=None,scope='Complete file inspection unless the audit scope says otherwise.'):
        self.c.put('split_audit_files',dict(id=id+'-file-'+short(url+'|'+str(split)+'|'+str(sha)+'|'+scope),audit_id=id,partition_id=id+'-partition-'+slug(split) if split else None,
            url=url,revision=revision,sha256=sha,bytes=bytes,row_count=rows,scope=scope,evidence_id=self.evidence[id]))

    def resource_tasks(self,fragment):
        return {r['task_id'] for r in self.d['task_resources'] if fragment in self.resources[r['resource_id']]['url']}

    def ingest_new(self):
        descriptions={
            'plantcad-cell':('PlantCAD2: maize cell-type accessibility','PlantCAD2 fine-tuning release','plantcad2-ft',['plantcad2-ft-cell_type_specific_acr']),
            'bend-gene-finding':('BEND: gene finding','Original BEND','bend-original',['bend1-gene-finding']),
            'bend-enhancer':('BEND: enhancer annotation','Original BEND','bend-original',['bend1-enhancer-annotation']),
            'bacbench-essential':('BacBench: essential genes','BacBench native 55-genome release','bacbench',['bacbench-essential']),
            'deepd-h3-demonstration':('DeepD: released H3 demonstration','DeepD released example','deepd-evals',['gue-H3']),
            'dgeb-mibig-dna':('DGEB: MIBiG DNA classification','DGEB','dgeb',['dgeb-MIBIG_dna_classification']),
            'dgeb-mibig-prot':('DGEB: MIBiG protein classification','DGEB','dgeb',['dgeb-MIBIG_protein_classification']),
            'mrna-mrl-sugimoto':('mRNABench: Sugimoto ribosome load, seed 2541','mRNABench reconstructed source default','mrnabench',['mrna-mrl-sugimoto']),
            'mrna-rna-lifecycle-ietswaart':('mRNABench: Ietswaart RNA lifecycle, seed 2541','mRNABench reconstructed source default','mrnabench',['mrna-rna-lifecycle-ietswaart']),
            'bgc-t5_bgc_grouped_5fold':('BGC-Bench: parent-BGC-grouped A-domain folds','BGC-Bench','bgc',['bgc-adomain']),
            'bgc-t5_gcf_holdout_c07':('BGC-Bench: GCF-held-out A domains','BGC-Bench','bgc',['bgc-adomain']),
        }
        # Exact task IDs come from existing explicit dataset resources, not title
        # similarity. New checks enrich the existing release case, avoiding a
        # second apparent independent benchmark for the same input files.
        for case,r in self.report['cases'].items():
            if case.startswith('selected-'):
                cfg=case.removeprefix('selected-');id='split-geneb-'+slug(cfg);self.case_ids[case]=id
                continue
            if case.startswith('rnagym-') and ('-random-' in case or '-min_similarity-' in case):
                mode='min_similarity' if '-min_similarity-' in case else 'random'
                assay=case.split(mode+'-')[1];id='split-rnagym-'+slug(mode+'-'+assay);self.case_ids[case]=id
                continue
            id='split-'+case;self.case_ids[case]=id
            if case.startswith('ntv3-intervals-'):
                species=case.removeprefix('ntv3-intervals-')
                info=('NTv3 benchmark: '+species.replace('_',' ')+' blocks','NTv3 standardized benchmark','ntv3-evals',
                    sorted({r['task_id'] for r in self.d['task_resources'] if r['resource_id']=='ntv3-benchmark-split-'+species}))
            else:info=descriptions[case]
            title,release,evaluation,tasks=info
            if evaluation not in {e['id'] for e in self.d['evaluations']}:evaluation=None
            ev=self.evidence_for('split-inspections','cases/'+case,r['method'])
            limits='No local/global alignment, k-mer similarity threshold, biological score reproduction or model-pretraining comparison. Zero observed overlap applies only to the named keys, files and partitions.'
            method=r['method'];status='metadata-only' if case.startswith(('bend-','ntv3-','bgc-')) else 'measured'
            conclusion='The comparison quantifies the named released separation axis; broader independence is not established.'
            if case=='plantcad-cell':
                conclusion='Chromosome-10 test separation is supported for the released coordinates. Exact DNA uniqueness across partitions is not met. Training/validation core windows also have positive-length interval overlaps; distinct coordinate IDs did not establish disjoint intervals.'
                scope='All 3,390,419 released 600-bp core windows: prior complete exact-string counts; complete lightweight coordinate checks; bounded recovery of illustrative rows. This is not a rescan of all long-context model inputs.'
                limits+=' The prior full sequence scan predates this bounded survey. Only 1,258,184 sequence rows were read to retrieve examples. Examples of equal labels do not establish the labels of every recurring string. Counts of shared strings are not counts of affected rows.'
                order=0
            else:
                scope='Complete named released files and their source-defined comparison units.';order=20 if case in ['bend-gene-finding','bacbench-essential','mrna-mrl-sugimoto'] else 80
            if case=='bend-gene-finding':conclusion='Protein-identity grouping does not make the released genomic spans disjoint. There are 126 train/test overlapping interval pairs, 127 train/valid and one test/valid. These are pairs of spans, not counts of duplicate full sequences or homologous proteins.'
            if case=='bend-enhancer':conclusion='All 45 pairs of the ten chromosome parts have disjoint released spans. The 285 BED rows are input windows; 782 labels per window are not independent split records.'
            if case.startswith('ntv3-intervals-'):conclusion='Released train/validation/test block spans are disjoint. This is a metadata check of blocks, not a sequence or extended-input-window comparison; full signal matrices and reference genomes were not downloaded for this check.'
            if case=='bacbench-essential':
                conclusion='Released genera are pairwise disjoint. Four exact CDS strings recur between training and validation; none recur in test. Genus holdout and exact-sequence uniqueness are separate conditions.'
                limits+=' This is the native 55-genome release, not Genos-m’s reported 51-genome cohort. CDS-only extraction is not an exact reproduction of model-specific flanking contexts.'
            if case=='deepd-h3-demonstration':conclusion='No exact or additional reverse-complement matches across the three released demonstration splits. This does not reconstruct the original DeepD H3/H4 paper cohorts.'
            if case.startswith('mrna-'):
                conclusion='The mapped HomoloGene groups are disjoint, while exact sequences and unmapped gene names recur. The source function splits unmapped rows independently, so the grouping rule does not guarantee sequence or gene-name uniqueness.'
                limits+=' Reconstructed seed 2541 after target-eligibility filtering, without historical embeddings. Other seeds, model-dependent feature filtering and the original paper’s actual run identities are not reconstructed.'
            if case.endswith('bgc_grouped_5fold'):conclusion='Parent BGC IDs and domain IDs are disjoint across folds; some published GCF IDs recur. Parent-BGC holdout is intentionally less restrictive than the separate GCF holdout.'
            if case.endswith('gcf_holdout_c07'):conclusion='Published domain, parent-BGC and GCF IDs are disjoint across the released train/test split. This verifies supplied group IDs, not the underlying sequence-similarity threshold.'
            self.audit(id,title,release,ev,scope,method,conclusion,limits,evaluation,status,order)
            assert tasks,case
            if case.startswith('ntv3-intervals-'):
                for link in self.d['task_resources']:
                    if link['resource_id']=='ntv3-benchmark-split-'+species:self.link(id,link['task_id'],variant=link['variant_id'])
            else:
                for t in tasks:
                    assert t in self.tasks,(case,t)
                    pid={'deepd-h3-demonstration':'deepd-h3-example','plantcad-cell':'plantcad2-ft-cell_type_specific_acr-lora','bend-gene-finding':'bend1-gene-finding-protocol','bend-enhancer':'bend1-enhancer-annotation-protocol','bacbench-essential':'bacbench-essential-protocol'}.get(case)
                    if case.startswith(('mrna-','dgeb-')):pid=t+'-protocol'
                    if case.startswith('bgc-'):pid='bgc-adomain-probe'
                    self.link(id,t,protocol=pid)
            if case=='plantcad-cell':
                for split,n in r['partition_rows'].items():self.partition(id,split,n,unique=r.get('distinct_sequences',{}).get(split),unit='600-bp core windows')
                for pair,n in r['exact_sequence_intersections'].items():self.comparison(id,*pair.split('-'),'exact-sequence',n)
                for pair,n in r['coordinate_id_intersections'].items():self.comparison(id,*pair.split('-'),'coordinate-id',n,'distinct chromosome,start,end tuples')
                for pair,v in r['interval_intersections'].items():self.comparison(id,*pair.split('-'),'interval',v['interval_pairs'],'positive-length interval pairs',v['left_rows_with_any_overlap'],v['right_rows_with_any_overlap'],v['interval_convention'])
                for f in r['files']:self.file(id,f'https://huggingface.co/datasets/{r["repo"]}/blob/{r["revision"]}/{f["path"]}',f['sha256'],f['bytes'],f['rows'],f['path'].split('/')[1].split('-')[0],r['revision'])
            else:self.import_case_rows(id,r)

    def import_case_rows(self,id,r):
        for name,p in r['partitions'].items():
            detail={k:v for k,v in p.items() if k not in ['rows','unique_sequences']}
            self.partition(id,name,p['rows'],p.get('unique_sequences'),'CDS intervals' if id=='split-bacbench-essential' else 'released rows',json.dumps(detail,ensure_ascii=False) if detail else '')
        for v in r['comparisons']:
            note=''
            if v['kind']=='reverse-complement':note='Equivalence-class count; it can be smaller than the exact-string count because both orientations collapse to one class. It is not an affected-row count.'
            if v['kind']=='reverse-complement-only':note='Shared uppercase/RC classes after removing every class represented by an exact-string intersection; this is an additional match count.'
            if v['kind']=='gene-id':note='All shared gene names in these reconstructed source splits lack a mapping in the supplied human HomoloGene map.'
            la=v.get('left_affected');ra=v.get('right_affected')
            if v['kind']=='exact-sequence' and r.get('sequence_length_audit'):
                m=r['sequence_length_audit'];la=m[v['left']+'_rows_with_shared_string'];ra=m[v['right']+'_rows_with_shared_string']
            self.comparison(id,v['left'],v['right'],v['kind'],v['shared'],v['unit'],la,ra,note)
        for f in r['files']:
            self.file(id,f['url'],f['sha256'],f['bytes'],split=f.get('split'),revision=r.get('revision'),scope='Read scope: '+r['method']+' Inspected path/member: '+f['path']+(' Archive member pattern: '+r['archive_member_pattern'] if r.get('archive_member_pattern') else ''))

    def geneb(self):
        rows=json.loads((ROOT/'data/geneb-artifact-inspections.json').read_text());groups=collections.defaultdict(dict)
        for r in rows:groups[r['task']][r['split']]=r
        for cfg,fs in groups.items():
            id='split-geneb-'+slug(cfg);extra=self.report['cases'].get('selected-'+cfg)
            ev=self.evidence_for('geneb-artifact-inspections',cfg,'Complete released train/test CSVs compared by exact case-sensitive sequence. Unique train/test intersection: '+str(fs['test']['train_test_exact_sequence_overlap'])+'.')
            scope='Complete GENEB configuration '+cfg+' at '+fs['test']['revision']+'.'
            method='Reuse the completed whole-file exact-string inspection; no new bulk download or all-suite sequence scan.'
            if extra:method+=' Additional complete exact/RC scan of these selected cached files is recorded in split-inspections.'
            self.audit(id,'GENEB: '+cfg,'GENEB',''+ev,scope,method,
                'Exact released input recurrence is measured; shared upstream datasets are not independent evidence of a second failure. The file schema does not establish chromosome, locus or homology grouping.',
                'No source coordinates in these CSVs. Release-specific train caps, revised labels and benchmark protocols remain distinct. No inference about every historical model’s scored rows or pretraining.', 'geneb',order=120)
            tids=self.resource_tasks('/tasks/'+cfg+'/');assert tids,cfg
            for tid in sorted(tids):
                pids=[p['id'] for p in self.d['protocols'] if p['task_id']==tid and p['id'].startswith('geneb-'+slug(cfg)+'-')]
                if pids:
                    for pid in pids:self.link(id,tid,protocol=pid)
                else:self.link(id,tid)
            if extra:
                # The new exact check must agree with the earlier full scan.
                assert next(v['shared'] for v in extra['comparisons'] if v['kind']=='exact-sequence')==fs['test']['train_test_exact_sequence_overlap']
                self.import_case_rows(id,extra)
                if extra.get('sequence_length_audit'):
                    m=extra['sequence_length_audit'];self.c.get('split_audits',id)['limitations']+=' Shared exact strings span 2–573 nt: 37 below 10 nt, 310 at 10–49 nt, 2,512 at 50–199 nt and 6,643 at ≥200 nt. Five strings have different cross-partition label sets; two have single conflicting labels. The full length strata and denominators are retained in the measurement report. Recurrence does not necessarily provide a consistent label to memorize.'
            else:
                for split,f in fs.items():
                    self.partition(id,split,f['rows'],f['distinct_sequences'],'sequence rows')
                    self.file(id,f'https://huggingface.co/datasets/{f["repo"]}/blob/{f["revision"]}/{f["path"]}',f['sha256'],f['bytes'],f['rows'],split,f['revision'])
                self.comparison(id,'train','test','exact-sequence',fs['test']['train_test_exact_sequence_overlap'])

    def dnafoundation(self):
        m=json.loads((ROOT/'data/dnafoundation-artifact-inspections.json').read_text());files={f['path']:f for f in m['files']}
        for directory,n in m['exact_sequence_overlap'].items():
            name=directory.removeprefix('data/');id='split-dnafoundation-'+slug(name)
            variants=[v for v in self.d['variants'] if v['name']=='DNA Foundation / '+name];assert variants,name
            ev=self.evidence_for('dnafoundation-artifact-inspections','exact_sequence_overlap/'+directory,'Complete deposited train/test sequence strings intersect in '+str(n)+' distinct values. Counts, source files and hashes are retained independently of the source paper’s original benchmark split.')
            self.audit(id,'DNA Foundation: '+name,'DNA Foundation processed release',ev,
                'Complete deposited classification train/test files for '+name+'.',
                'Reuse the completed full archive scan, retaining its member hashes and source revision.',
                'Measured separation applies to this study’s processed split, including reshuffled source datasets; it must not be substituted for a native NT/GUE/GB split.',
                'Coordinates/species/group IDs are absent from the short-sequence CSVs; homology, flanking-context and pretraining separation are untested. The source paper and released code differ on classifier-tuning fold count.','dna-foundation',order=140)
            for v in variants:self.link(id,v['task_id'],variant=v['id'])
            for split in ['train','test']:
                f=files[directory+'/'+split+'.csv'];self.partition(id,split,f['rows'],f.get('unique_sequences'),'sequence rows')
                self.file(id,self.resources['dnafoundation-data']['url'],f['sha256'],f['bytes'],f['rows'],split,
                    self.resources['dnafoundation-data']['revision'],scope='Archive member '+f['path']+'; SHA-256 and size describe the member, not the whole archive.')
            self.comparison(id,'train','test','exact-sequence',n)

    def rnagym(self):
        rows=json.loads((ROOT/'data/rnagym-artifact-inspections.json').read_text());groups=collections.defaultdict(dict)
        for f in rows:
            if f['archive']!='fitness_CV_splits':continue
            _,mode,split,filename=f['member'].split('/');assay=filename.removesuffix('_'+split+'.csv')
            groups[(mode,assay)][split]=f
        for (mode,assay),fs in groups.items():
            id='split-rnagym-'+slug(mode+'-'+assay);tid='rnagym-'+slug(assay)
            variant=None
            if tid not in self.tasks:
                variants=[v for v in self.d['variants'] if v['name']==assay];assert len(variants)==1,assay
                tid=variants[0]['task_id'];variant=variants[0]['id']
            ev=self.evidence_for('rnagym-artifact-inspections',mode+'/'+assay,'Complete archived train/val CSVs inspected; '+str(fs['val']['train_validation_exact_sequence_overlap'])+' distinct exact strings recur across this split.')
            self.audit(id,'RNAGym: '+assay+' / '+mode,'RNAGym supervised CV release',ev,
                'One archived 80/20 train/validation partition for this assay and mode; not the whole-assay zero-shot cohort.',
                'Complete archived strings compared exactly; selected recurring cases additionally rechecked from cached files.',
                'Random or similarity-minimizing partitioning is not a guarantee of unique sequence strings or a strict homology threshold.',
                'The min_similarity routine uses swaps to reduce similarity; it does not impose a maximum allowed identity. These archived fitting splits are not the original Evo 1/2 zero-shot protocols. No all-pairs alignment or pretraining audit.','rnagym',order=160)
            pid=tid+'-cv-'+mode+'-protocol'
            self.link(id,tid,protocol=pid if pid in self.protocols else None,variant=variant,note='RNAGym archived '+mode+' partition for '+assay+' only. Shared assay identity with NABench does not identify NABench’s own training rows.')
            extra=self.report['cases'].get('rnagym-'+mode+'-'+assay)
            if extra:self.import_case_rows(id,extra)
            else:
                for split,f in fs.items():
                    self.partition(id,split,f['rows'],f['distinct_sequences'],'sequence rows')
                    self.file(id,f['archive_url'],f['sha256'],f['bytes'],f['rows'],split,scope='Archive member '+f['member']+'; hash/size identify the member. Archive SHA-256: '+f['archive_sha256'])
                self.comparison(id,'train','val','exact-sequence',fs['val']['train_validation_exact_sequence_overlap'])

    def prior_releases(self):
        m=json.loads((ROOT/'data/existing-benchmark-inspections.json').read_text())
        # PGB: whole held-out FASTAs are available even when oversized training
        # is excluded. Never impute an unmeasured train/test intersection.
        pg=m['residual']['pgb']
        for config,pairs in pg['exact_sequence_intersections'].items():
            id='split-pgb-'+slug(config);fs=[f for f in pg['files'] if f['file'].rsplit('_',1)[0]==config]
            vs=[v for v in self.d['variants'] if v['name']==config];assert vs,config
            ev=self.evidence_for('existing-benchmark-inspections','residual/pgb/'+config,'Complete inspected FASTA partitions, exact DNA counts and chromosome headers; larger training files were excluded from this bounded scan.')
            self.audit(id,'PGB: '+config,'PGB native FASTA release',ev,
                pg['scope']+' This case compares only '+(', '.join(pairs) or 'no pair: only one complete partition was available within the size bound')+'.',
                'Reuse completed whole-file exact-sequence intersections and supplied chromosome headers.',
                'A supplied chromosome holdout does not imply uniqueness of sequence strings. Unmeasured training comparisons are absent, not zero.',
                'No approximate homology, RC-equivalence, full genomic-span or extended-context check. Some training FASTAs have millions of oversampled rows and were not scanned in full.','pgb',status='measured' if pairs else 'metadata-only',order=180)
            for v in vs:self.link(id,v['task_id'],variant=v['id'])
            for f in fs:
                sp=f['file'].rsplit('_',1)[1].removesuffix('.fa');self.partition(id,sp,f['rows'],f['unique_sequences'],'FASTA records',json.dumps(f.get('header_chromosomes',{})))
                self.file(id,'https://huggingface.co/datasets/InstaDeepAI/plant-genomic-benchmark/blob/'+f['revision']+'/'+f['file'],f['sha256'],rows=f['rows'],split=sp,revision=f['revision'])
            for pair,n in pairs.items():self.comparison(id,*pair.split('_'),'exact-sequence',n)
        # Processed mRNA source-library defaults, target eligibility first.
        # Preserve dataset × target boundaries instead of aggregating targets.
        for f in m['residual']['mrna']:
            for target,split in f.get('default_splits',{}).items():
                if f['dataset_names'][0] in ['mrl-sugimoto','rna-lifecycle-ietswaart']:continue
                candidates=[v for v in self.d['variants'] if v['name']==target and any(v['task_id']=='mrna-'+n or v['task_id'].startswith('mrna-'+n+'-') for n in f['dataset_names'])]
                assert candidates,(f['file'],target)
                id='split-mrna-'+slug(f['dataset_names'][0]+'-'+target)
                ev=self.evidence_for('existing-benchmark-inspections','residual/mrna/'+f['file']+'/'+target,'Reconstructed source-library default split after nonmissing-target filtering: '+json.dumps(split))
                self.audit(id,'mRNABench: '+f['dataset_names'][0]+' / '+target,'mRNABench reconstructed source default',ev,
                    'Complete public processed target-eligible rows; seed '+str(split['seed'])+'.',
                    'Reuse the completed reconstruction from the pinned source function and supplied homology map. No historical model embeddings used.',
                    'Exact-string separation is measured for this seed and eligibility filter. Homology groups apply only to mapped genes; unmapped rows can be assigned independently.',
                    'Not the historical ten-seed/model-dependent scored cohort. No claim about every gene family, raw-only dataset, approximate sequence identity or pretraining.','mrnabench',order=200)
                for v in candidates:self.link(id,v['task_id'],variant=v['id'])
                for sp,n in split['rows'].items():self.partition(id,sp,n,unit='target-eligible rows')
                for pair,n in split['exact_sequence_intersections'].items():self.comparison(id,*pair.split('_'),'exact-sequence',n)
                self.file(id,'https://huggingface.co/datasets/'+f['repo']+'/blob/'+f['revision']+'/'+f['file'],f['sha256'],rows=f['rows'],revision=f['revision'],scope='Unsplit processed input; partitions reconstructed by target and seed, not read from three deposited split files.')
        ds=m['residual']['deepstarr'];id='split-deepstarr'
        ev=self.evidence_for('existing-benchmark-inspections','residual/deepstarr',ds['scope'])
        self.audit(id,'DeepSTARR: enhancer activity','DeepSTARR original Zenodo release',ev,
            'All three complete original FASTAs, validated rowwise against the pinned GenerTeam mirror.',
            'Exact case-sensitive full 249-nt strings; supplied chromosome coordinates summarized separately.',
            'No exact string recurs across train/validation/test. Test and validation occupy separate chr2R regions; training uses other chromosomes.',
            'No approximate identity or RC-equivalence check; both strands occur within each partition. A native/mirror match is not an independent benchmark.','deepstarr',order=70)
        for t in ['deepstarr-dev','deepstarr-hk']:self.link(id,t)
        for f in ds['files']:
            self.partition(id,f['split'],f['rows'],f['unique_sequences'],'249-nt sequences',json.dumps(f['chromosome_starts']))
            self.file(id,'https://zenodo.org/records/5502060/files/'+f['fasta_file'],f['fasta_sha256'],rows=f['rows'],split=f['split'])
        for pair,n in ds['exact_sequence_intersections'].items():self.comparison(id,*pair.split('_'),'exact-sequence',n)
        # GUANinE BED/TSV keys are not automatically DNA strings.
        for name,r in m['facts']['GUANINE_OVERLAPS'].items():
            config=name.removeprefix('guanine--');id='split-guanine-'+slug(config);dna=config.startswith('gpra_')
            tid='guanine-'+config;assert tid in self.tasks
            ev=self.evidence_for('existing-benchmark-inspections','facts/GUANINE_OVERLAPS/'+name,'Complete inspected 1% training/development/test keys have pairwise intersections '+json.dumps(r['exact_intersection']))
            self.audit(id,'GUANinE: '+config,'GUANinE v1.1 inspected few-shot/development/test',ev,
                'Complete deposited 1% training, development and test where supplied; ClinVar has development/test only.',
                'Exact synthetic 110-nt seq strings.' if dna else 'Exact supplied coordinate/variant keys; no reference DNA extraction.',
                'No shared exact '+('DNA strings' if dna else 'input keys')+' among these inspected partitions.',
                'Full main training archives excluded from this bounded survey. '+('No approximate homology or RC check.' if dna else 'Disjoint coordinate or variant IDs do not imply disjoint spans, full input sequences or alleles at the same locus.')+' Public test labels are often withheld.','guanine',status='measured' if dna else 'metadata-only',order=220)
            self.link(id,tid,tid+'-protocol')
            for sp,n in r['unique'].items():
                f=next(f for f in m['facts']['GUANINE_FILES'] if f['repo']=='guanine/'+config and ('/'+sp+'/' in '/'+f['file'] or f['file'].startswith(sp+'/')))
                self.partition(id,sp,f['rows'],n if dna else None,'input rows',str(n)+' distinct '+('sequences' if dna else 'coordinate/variant keys'))
                self.file(id,'https://huggingface.co/datasets/'+f['repo']+'/blob/'+f['revision']+'/'+f['file'],f['sha256'],rows=f['rows'],split=sp,revision=f['revision'])
            for pair,n in r['exact_intersection'].items():self.comparison(id,*pair.split(' / '),'exact-sequence' if dna else 'input-key',n,'distinct exact DNA strings' if dna else 'distinct supplied coordinate/variant keys')

    def translation(self):
        m=json.loads((ROOT/'data/plantcad-translation-artifact-inspections.json').read_text())
        for cfg,pairs in m['intersections'].items():
            id='split-plantcad-'+slug(cfg);ev=self.evidence_for('plantcad-translation-artifact-inspections',cfg,'Complete train/validation/test gene identifiers and 500-bp sequences have no pairwise intersections.')
            self.audit(id,'PlantCAD2: '+cfg.replace('cross_species_leaf_','').replace('_',' '),'PlantCAD2 fine-tuning release',ev,
                'Complete three 500-bp translation-proxy files, with target and gene identifiers.',
                'Exact sequence strings and gene IDs; species/chromosome metadata inspected.',
                'Arabidopsis training/validation and maize test have no exact sequence or gene-ID recurrence. Training and validation share chromosomes, while test is a species holdout.',
                'Exact identity does not establish lack of plant homologs or pretraining overlap. Target is the deposited leaf abundance proxy, not an independently measured translation rate.','plantcad2-ft',order=65)
            self.link(id,'plantcad2-ft-'+cfg)
            for f in m['files']:
                if not f['path'].startswith(cfg+'/'):continue
                sp=f['path'].split('/')[1].split('-')[0];self.partition(id,sp,f['rows'],unit='500-bp gene-associated windows',detail=json.dumps(f['chromosomes']))
                self.file(id,'https://huggingface.co/datasets/plantcad/PlantCAD2_fine_tuning_tasks/blob/'+m['revision']+'/'+f['path'],f['sha256'],f['bytes'],f['rows'],sp,m['revision'])
            for pair,values in pairs.items():
                for kind,n in values.items():self.comparison(id,*pair.split('-'),'exact-sequence' if kind=='exact_sequences' else 'gene-id',n,'distinct exact DNA strings' if kind=='exact_sequences' else 'distinct supplied gene IDs')

    def strategies(self):
        unmapped='split-mrna-unmapped-code'
        self.c.evidence(unmapped,'src-mrna-homology','homology_split.py lines 13–70','Only genes mapped to a supplied HomoloGene group are kept together. An unmapped gene uses a one-row fallback during the seeded shuffled traversal, so repeated unmapped gene names can cross partitions.','code','https://github.com/morrislab/mRNABench/blob/778d691ab91c51c03addeb9219229f2ec81d195c/mrna_bench/data_splitter/homology_split.py#L13-L70')
        for p in self.d['protocols']:
            if p['id'].startswith('mrna-') and p['id'].endswith('-protocol') and 'homolog' in p['split_rule'].lower():
                p['split_rule']=p['split_rule'].split(' Grouping applies only')[0]+' Grouping applies only to genes present in the supplied homology map; unmapped rows are assigned independently and can repeat gene names across partitions.'
                self.c.field('protocols',p['id'],'split_rule',unmapped)
        specs=[
          ('random','Random rows or variants','row / variant','Assign examples randomly, possibly stratifying labels.','Separates recorded examples and estimates performance on similar sampled examples.','Identical strings, nearby loci, repeated donors, mutation positions and gene families can cross partitions.'),
          ('chromosome','Chromosome holdout','chromosome','Reserve whole named chromosomes for validation or test.','Separates loci on the reference assembly when assignment is applied to the actual input span.','Repeats, paralogs and homologous chromosomes/species can retain related DNA. Label holdout is distinct from sequence-model training exclusion.'),
          ('blocks','Genomic blocks','genomic interval','Assign larger genomic intervals, with any source-defined padding or buffers.','Can separate nearby windows and long-range labels when windows and buffers respect the boundary.','Disjoint block IDs or scored cores do not establish that full extended input windows are disjoint.'),
          ('gene-family','Genes or homology groups','gene / family','Group related transcripts, genes or proteins before partitioning.','Can reduce leakage through isoforms or homologs at the supplied grouping threshold.','Unmapped genes, grouping thresholds and overlapping genomic spans require separate checks.'),
          ('similarity','Sequence similarity','sequence / similarity objective','Separate examples using sequence similarity, clustering or a similarity-reduction objective.','Reduces related inputs across partitions according to the stated algorithm.','A swap heuristic that lowers average similarity is not a strict identity threshold and can leave exact duplicates.'),
          ('position','Mutation positions','mutated position / block','Keep mutations at a position or contiguous position block together.','Reduces reuse of the same mutated position across training and test.','Background sequences, nearby positions and multi-mutant combinations can still be shared.'),
          ('taxon','Species, genera or clades','taxon','Hold out entire source taxa at an explicitly named rank.','Tests transfer across the held-out taxa rather than random rows from the same taxon.','Conserved sequences and horizontal transfer cross taxon boundaries. Pretraining taxon exclusion is a separate condition.'),
          ('donor','Individuals or donors','individual','Group all measurements from an individual or donor.','Separates participants across the fitted predictor’s train/test data.','Genes and reference sequences may intentionally be shared. Population structure and related donors can remain.'),
          ('condition','Assay tracks or conditions','track / condition','Mask labels for selected cell types, conditions or assays.','Tests an unobserved measurement context or assay.','The same reference DNA may have been seen with other labels; track exclusion is not genome exclusion.'),
          ('time','Time or source version','date / cohort release','Evaluate observations or datasets released after a named cutoff.','Separates new measurements from earlier training and selection sources.','The same loci, individuals or similar assays may occur in both periods; validation data can still guide selection.'),
          ('bgc','BGCs, gene-cluster families or chemical scaffolds','BGC / GCF / scaffold','Group biosynthetic clusters or first-product scaffolds before splitting.','Targets transfer across clusters or chemistry at the chosen grouping level.','Parent-cluster grouping is weaker than GCF grouping. Shared domain sequences may still occur in different clusters.'),
          ('fixed','Fixed zero-shot or observational cohort','assay / variant cohort','Score a fixed assay or external cohort without fitting a new task-specific predictor.','Defines a common score cohort; there is no downstream fitting split to compare.','Pretraining, benchmark-driven model selection, scorer tuning and cohort ascertainment still matter. No downstream split is not evidence of no contamination.'),
        ]
        for order,(id,name,unit,desc,protection,limits) in enumerate(specs):
            self.c.put('split_strategies',dict(id='split-strategy-'+id,name=name,split_unit=unit,description=desc,protection=protection,limitations=limits,sort_order=order))
        def add(pid,strategy,note):
            p=self.protocols[pid]
            eids=[f['evidence_id'] for f in self.d['field_evidence'] if f['entity_table']=='protocols' and f['entity_id']==pid and f['field']=='split_rule']
            eid=eids[-1] if eids else p['source_evidence_id']
            if pid=='bacbench-essential-protocol':eid='final-bacbench-essential-native-test'
            self.c.put('split_protocol_strategies',dict(protocol_id=pid,strategy_id='split-strategy-'+strategy,note=note,evidence_id=eid),('protocol_id','strategy_id'))
        for pid,s,n in [
            ('evo-brca1-probe','position','1,060 train versus 266 test genomic positions; grouped inner CV is training-only.'),
            ('evo-exon-intron-probe','taxon','Random initial species split; human, mouse and zebrafish manually assigned to test; eight eligible test species.'),
            ('spliceai-spliceai-sites-coding-protocol','chromosome','Test chr1/3/5/7/9; random 10% training genes for early stopping.'),
            ('spliceai-spliceai-sites-coding-protocol','gene-family','Test genes exclude those with any annotated paralog.'),
            ('spliceai2-spliceai2-top-transcript-protocol','chromosome','Human-only full-transcript model: 352 eligible chr21/22 genes; same chromosomes serve validation. This is not the main multispecies model’s unrestricted variant cohort.'),
            ('spliceai2-spliceai2-tissue-variant-protocol','chromosome','Ridge CV grouped by chromosome; a different fitting layer from the base sequence model.'),
            ('dnafoundation-expression-regression','donor','75:25 subject partition; shared genes across subjects.'),
            ('dnafoundation-eqtl-rf','chromosome','Three outer chromosome groups and fourfold grouped inner CV.'),
            ('genecad-cds-base-default','taxon','Training eight plant species; additional angiosperm and distant-species test panels.'),
            ('genecad-cds-base-default','random','Within-training-species/chromosome random windows for validation; not a held-out-species validation set.'),
            ('bacbench-essential-protocol','taxon','Native 37/9/9 genome partitions have disjoint genera; this is not Genos-m’s 51-genome scoring cohort.'),
            ('bgc-adomain-probe','bgc','Parent-BGC fivefold partition and separate BiG-SCAPE c=0.7 GCF holdout.'),
            ('bgc-retrieval-probe','bgc','Random, first-product Bemis–Murcko scaffold and GCF holdouts; separate biosynthetic-class retrieval holdout.'),
            ('ag2-cellxgene-expression-lfc-alphagenome2-protocol','time','Cutoff 1 October 2025; 16 new datasets excluded from post-training. Dedicated paragraph evaluates fold-1 validation intervals.'),
            ('ag2-gtex11-eqtl-causality-alphagenome2-protocol','chromosome','Variant-effect labels held out for reporting; all-folds sequence model has already seen reference DNA at the loci.'),
            ('plantcad2-ft-cell_type_specific_acr-lora','chromosome','Released test chr10; training and validation both chr1–9. Core-window overlap checks are linked separately.'),
        ]:add(pid,s,n)
        # These are explicit protocol families with source-specific rules,
        # not a text classifier guessing a split from a task title.
        for p in self.d['protocols']:
            pid=p['id']
            if pid in ['ntv3-annotation-gene-protocol','ntv3-annotation-gene-any-isoform-protocol']:add(pid,'taxon',p['split_rule'])
            if pid in ['dart-ccre-supervised','dart-celltype-supervised','dart-accessibility-supervised','dart-ccre-lora','dart-celltype-lora','dart-accessibility-lora']:add(pid,'chromosome',p['split_rule'])
            if pid in ['dart-ccre-evo-zero','dart-motif-evo-zero','dart-caqtl-evo-zero','dart-dsqtl-evo-zero']:add(pid,'fixed',p['split_rule'])
            if pid in ['botanic1-atac-counts-protocol','botanic1-atac-profile-protocol','botanic1-tf-family-protocol','botanic1-long-atac-protocol']:add(pid,'chromosome',p['split_rule'])
            if pid in ['botanic1-cross-donor-protocol','botanic1-cross-acceptor-protocol']:add(pid,'taxon',p['split_rule'])
            if pid.startswith('ntv3-benchmark-'):add(pid,'blocks',p['split_rule'])
            if pid.startswith('rnagym-') and '-cv-' in pid:add(pid,'random' if '-cv-random-' in pid else 'similarity',p['split_rule']+(' Similarity-minimizing swaps are not strict identity-threshold clustering.' if '-cv-min_similarity-' in pid else ''))
            if pid.startswith('mrna-') and pid.endswith('-protocol'):
                if 'homolog' in p['split_rule'].lower():add(pid,'gene-family',p['split_rule'])
            if pid.startswith('traitgym-'):
                if p['adaptation']=='zero-shot':add(pid,'fixed',p['split_rule'])
                elif 'chromosome' in p['split_rule'].lower():add(pid,'chromosome',p['split_rule'])
            if pid.startswith('ag2-impute-') and pid.endswith('-alphagenome2-protocol'):add(pid,'condition',p['split_rule'])
            if pid.startswith('guanine-'):
                s='chromosome' if p['task_id'] in ['guanine-ccre_propensity','guanine-dnase_propensity','guanine-cadd_snv'] else 'time' if p['task_id']=='guanine-clinvar_snv' else 'random'
                add(pid,s,p['split_rule'])
            if pid in ['evo-brca1-zero'] or pid.startswith('rnagym-') and pid.endswith('-rnagym'):add(pid,'fixed',p['split_rule'])
            if pid.startswith('nabench-') or '-nabench-' in pid:
                if pid.endswith('-position'):add(pid,'position',p['split_rule'])
        # Original BEND's protein grouping and chr-part protocol remain cited.
        for t,s in [('bend1-gene-finding','gene-family'),('bend1-enhancer-annotation','blocks')]:
            for p in self.d['protocols']:
                if p['task_id']==t and not p['id'].startswith(('deepd-','genosm-')):add(p['id'],s,p['split_rule'])

    def boundaries(self):
        def add(key,title,collection,tids,status,scope,conclusion,limits):
            id='split-'+key
            p=next((p for p in self.d['protocols'] if p['task_id']==tids[0]),None)
            ev=p['source_evidence_id'] if p else self.tasks[tids[0]]['evidence_id']
            self.audit(id,title,collection,ev,scope,'Source and released artifact review; no unreported sequence comparison is imputed.',conclusion,limits,collection if collection in {e['id'] for e in self.d['evaluations']} else None,status,250)
            for t in tids:
                ps=[p for p in self.d['protocols'] if p['task_id']==t and p['adaptation'].startswith('zero-shot')] if status=='not-applicable' else []
                if ps:
                    for p in ps:self.link(id,t,protocol=p['id'],note='Fixed zero-shot cohort only. Other fitting protocols on the same task retain their own partition rules.')
                else:self.link(id,t)
            return id
        meta=self.report['large_release_metadata']['generator-recovery']
        tids=[t for t in self.tasks if 'recovery' in t and t.startswith('generator')]
        if tids:
            id=add('generator-recovery-size','GENERator sequence recovery: bulk files excluded','generator2-evals',tids,'skipped-size',
                'Full recovery release: '+str(meta['total_parquet_bytes'])+' compressed Parquet bytes from pinned repository metadata.',
                'The 5.75-GB release was not downloaded for an exhaustive sequence/homology comparison. Source-defined recovery conditions and lengths are catalogued; no clean-split conclusion is made.',
                'File sizes do not establish exact row counts or overlap. Sequence continuation/recovery is not necessarily a downstream fitted classification split.')
            ev=self.evidence_for('split-inspections','large_release_metadata/generator-recovery','Pinned repository file metadata list '+str(meta['total_parquet_bytes'])+' total compressed Parquet bytes; no dataset download.')
            self.c.get('split_audits',id)['evidence_id']=ev;self.evidence[id]=ev
            self.file(id,meta['metadata_url'],revision=meta['revision'],bytes=meta['total_parquet_bytes'],scope='Repository-tree metadata only; total size of listed Parquet objects, not a downloaded dataset hash.')
        add('pgb-large-training','PGB: oversized training partitions excluded','pgb',['pgb-chromatin','pgb-gene-expression','pgb-splice-donor','pgb-splice-acceptor'],'skipped-size',
            'Main chromatin/expression training FASTAs include source-reported 5.12M/6.4M oversampled rows; full large training files excluded. Complete held-out checks appear separately.',
            'Only the fully scanned partitions have measured intersections. No zero is assigned to unscanned training comparisons.',
            'Oversampling and held-out sequence recurrence make raw record counts different from distinct sequences; no full training/homology scan.')
        add('guanine-full-training','GUANinE: full training archives excluded','guanine',[t for t in self.tasks if t.startswith('guanine-') and t!='guanine-clinvar_snv'],'skipped-size',
            'Complete 1% training/development/test checks are separate; full main training archives were not downloaded.',
            'Measured few-shot split keys cannot establish full-training separation.',
            'No full-training sequence, interval or homology comparison. The excluded scope is recorded as a size decision, not a positive or negative result.')
        add('ntv3-expanded-input','NTv3: full long-context inputs excluded','ntv3-evals',[t for t in self.tasks if t.startswith('ntv3-benchmark-')],'skipped-size',
            'Complete compact train/validation/test BEDs inspected separately for 11 species; expanded genomic input windows and signal matrices excluded.',
            'Disjoint metadata block spans do not establish absence of overlap in every 1-Mb model input or its flanks.',
            'No bulk signal matrices, reference sequence extraction or all-pairs long-input comparison; no pretraining contamination estimate.')
        add('spliceai2-cohort','SpliceAI2: split cohort access','spliceai2-evals',['spliceai2-top-transcript'],'unavailable',
            'Primary full-transcript methods specify 352 human chr21/22 genes and human-only training. The released dataset requires access; a complete public split manifest was not available for this inspection.',
            'Chromosome and ortholog-exclusion claims can be cited; exact input and family overlap cannot be recounted from public scored rows here.',
            'Main multispecies variant benchmarks must not inherit the human-only full-transcript split. No claimed clean sequence/homology result.')
        add('dart-cohort','DART-Eval: source split rules, no input recount','dart',[t for t in self.tasks if t.startswith('dart-')],'unavailable',
            'Public evaluation code and Synapse input identifiers reviewed; underlying complete scored sequence cohorts were not retrieved for this bounded survey.',
            'Supervised task protocols name held-out chromosomes. Original Evo 2 zero-shot use does not inherit a fitted supervised task’s partition automatically.',
            'This is an unretrieved cohort, not a finding that Synapse data are gated or missing. No interval, exact-sequence or homology result is reported.')
        for key,title,col,prefix in [('carbonx-prompts','Carbon-X: source-specific evaluation inputs','carbonx-evals','carbonx-'),('deepd-panels','DeepD: paper-only panels','deepd-evals','deepd-')]:
            tids=[t for t in self.tasks if t.startswith(prefix)]
            if tids:add(key,title,col,tids,'unavailable','Source methods and accessible releases reviewed; only identifiable public cohorts have measured comparisons elsewhere.',
                'Several original scored assay IDs, per-example cohorts or split manifests are not publicly resolved by these sources.',
                'The released DeepD H3 demonstration is a separate bounded check. Generic benchmark identity does not prove identity with the original scored rows; inaccessible prompt assets are not a measured negative.')
        # Fixed zero-shot assays have no train/test boundary at the task-head
        # layer. Keep source selection/pretraining risks explicit.
        for key,title,col,tids in [
            ('evo-dms-fixed','Evo 1 / Evo 2: fixed DMS cohorts','evo-original',[t for t in self.tasks if t.startswith('evo-dms-')]),
            ('traitgym-fixed','TraitGym: fixed zero-shot cohorts','traitgym',[t for t in self.tasks if t.startswith('traitgym-')]),
            ('plantcad-zero-fixed','PlantCAD2: fixed zero-shot cohorts','plantcad2-zero',[r['task_id'] for r in self.d['evaluation_tasks'] if r['evaluation_id']=='plantcad2-zero']),
            ('gpn-fixed','GPN-Star: fixed variant cohorts','gpn-evals',[t for t in self.tasks if t.startswith('gpn-')]),
        ]:
            if tids:
                add(key,title,col,tids,'not-applicable','Fixed external variants/assays scored without fitting a new task head.',
                    'No downstream fitting split exists for this zero-shot protocol. This is not evidence that pretraining, model selection or homologous reference sequence are excluded.',
                    'Other probes on the same targets have their own fitting rules. Full pretraining corpora and all model-selection histories were not compared.')

    def examples_and_findings(self):
        comparisons=self.d['split_comparisons']
        for i,x in enumerate(self.report['examples'],1):
            aid=self.case_ids[x['case']];left=x['left'];right=x['right'];kind=x['kind']
            matches=[r for r in comparisons if r['audit_id']==aid and r['overlap_type']==kind and {r['left_partition_id'],r['right_partition_id']}=={aid+'-partition-'+slug(left['split']),aid+'-partition-'+slug(right['split'])}]
            assert len(matches)==1,(x['example_id'],aid,kind)
            r=matches[0]
            note='Illustrative observed pair; it is not a random sample and does not estimate label disagreement or score impact.'
            if kind=='interval':note+=' Positive-length intersection: '+str(x['overlap_bp'])+' bp under half-open coordinates.'
            if kind=='reverse-complement-only':note+=' DNA strings differ but are reverse complements; SHA-256 refers to the uppercase canonical orientation.'
            if 'labels_equal' in x:note+=' This pair’s supplied labels are '+('equal.' if x['labels_equal'] else 'different.')
            self.c.put('split_examples',dict(id=x['example_id'],comparison_id=r['id'],sequence_sha256=x.get('sequence_sha256'),sequence_length=x.get('sequence_length'),
                left_json=json.dumps(left,ensure_ascii=False),right_json=json.dumps(right,ensure_ascii=False),example_url=OWN+'data/split-examples.jsonl#L'+str(i),note=note,evidence_id=self.evidence[aid]))
        grouped=collections.defaultdict(list)
        for r in comparisons:grouped[r['audit_id']].append(r)
        for a in self.d['split_audits']:
            rs=grouped[a['id']]
            a['finding']='not-applicable' if a['status']=='not-applicable' else 'overlap' if any(r['shared_count']>0 for r in rs) else 'no-overlap' if rs else 'limited'
        # A source-supported correction, not a rewrite of the source claim.
        p=self.protocols['plantcad2-ft-cell_type_specific_acr-lora']
        p['notes']=(p.get('notes') or '').split(' Complete 600-bp core-coordinate inspection additionally found')[0]+' Complete 600-bp core-coordinate inspection additionally found 4,531 train/validation positive-length interval pairs (4,477 train and 4,347 validation windows), and zero test interval overlaps. Coordinate-ID equality and span overlap are different checks; see Splits.'
        self.c.field('protocols',p['id'],'notes',self.evidence['split-plantcad-cell'])
        self.c.put('findings',dict(id='plantcad-cell-coordinate-spans',task_id=p['task_id'],evaluation_id='plantcad2-ft',severity='qualification',
            description='PlantCAD2 maize 600-bp core coordinate IDs are disjoint across partitions, but training/validation have 4,531 overlapping interval pairs. Test chr10 spans are disjoint from training/validation; 18 distinct test DNA strings nevertheless occur in training. The source’s chromosome test holdout and exact sequence uniqueness are distinct conditions.',evidence_id=self.evidence['split-plantcad-cell']))


def populate(data):
    s=Splits(data)
    s.ingest_new();s.geneb();s.dnafoundation();s.rnagym();s.prior_releases();s.translation();s.strategies();s.boundaries();s.examples_and_findings()
    return data
