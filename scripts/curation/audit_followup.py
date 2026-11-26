"""Task-level follow-up: measured releases, scorer semantics and explicit gaps."""
from pathlib import Path
import collections
import csv
import json

ROOT=Path(__file__).resolve().parents[2]

def row(c,table,id):return next(x for x in c.rows[table] if x.get('id')==id)

def category(c,t,cat,e,relation='measured',rationale=None):
    if not any(x['task_id']==t and x['category_id']==cat for x in c.rows['task_categories']):
        c.add('task_categories',task_id=t,category_id=cat,relation=relation,
              rationale=rationale or 'Assigned from the cited task output and procedure.',evidence_id=e,attribution='curatorial')
    c.field('tasks',t,'classification:'+cat,e,rationale)

def population(c,t,p,e,relation='sequence-origin',note='Source reports this organism; coverage is limited to the cited dataset.'):
    if not any(x['task_id']==t and x['population_id']==p and x['relation']==relation for x in c.rows['task_populations']):
        c.add('task_populations',task_id=t,population_id=p,variant_id=None,relation=relation,coverage=note,evidence_id=e)

def populate(c):
    c.add('metrics',id='symmetric-auroc',name='max(AUROC, 1 − AUROC)',definition='Direction-invariant AUROC with experimental scores binarized at the assay median; not raw AUROC.',direction='higher')
    c.add('metrics',id='abs-mcc',name='Absolute MCC',definition='Absolute Matthews correlation after experimental and model scores are independently median-thresholded.',direction='higher')
    geneb(c);rnagym(c);carbonx(c);deepd(c);unresolved_panels(c);capabilities(c)
    assignments={(x['task_id'],x['category_id']) for x in c.rows['task_categories']}
    c.rows['field_evidence']=[x for x in c.rows['field_evidence'] if not(x['entity_table']=='tasks' and x['field'].startswith('classification:') and (x['entity_id'],x['field'].split(':',1)[1]) not in assignments)]

def geneb(c):
    stats=json.loads((ROOT/'data/geneb-artifact-inspections.json').read_text())
    spec=json.loads((ROOT/'research/sources/darlednik--GENEB/benchmark/benchmark_spec.json').read_text())
    rev=spec['dataset']['revision'];repo=spec['dataset']['repo_id']
    c.source('geneb-release-card','GENEB pinned dataset card',f'https://huggingface.co/datasets/{repo}/blob/{rev}/README.md','dataset-card',rev,'research/artifacts/audit-followup/geneb/README.md')
    card=c.ev('geneb-release-protocol','geneb-release-card','Record schema; evaluation protocol; task index','Release supplies only text/label train/test CSVs. Upstream dev/validation splits are excluded. MCC is primary; frozen logistic regression uses five seeds and full/10-shot/1-shot regimes.','documentation')
    source=c.ev('geneb-gue-lineage','project-paper-dnabert2','Appendix, Dataset Details: TF-H, TF-M, EMP and species classification','GUE human and mouse datasets are TF binding, not mouse enhancers. Human negatives match GC; mouse negatives are dinucleotide shuffles. Yeast histone labels, human promoters/splice, and virus/fungi origin classifiers are separate tasks.')
    biology=c.ev('geneb-biological-targets','geneb-paper','Appendix, Task Composition and Table 3; Epigenomic and Regulatory Element Tasks','GENEB identifies human, Arabidopsis and bacterial iPro promoter datasets, six named-species 4mC targets, 5mC/6mA targets, six plant lncRNA datasets and cassava transcriptional activity. These descriptions do not supply per-row coordinates or a biochemical label-validation audit.')
    harness=c.code('geneb-probe-metrics','darlednik/GENEB','harness/run_GENEB.py','def metrics(',
                   'GENEB reports MCC, accuracy and macro-F1; fits logistic regression on frozen embeddings; each seed samples up to k examples per observed class without replacement for 1/10-shot.',end_needle='def evaluate_task(')
    for item in spec['tasks']:
        rid=item['id'];slug='geneb-'+rid.lower().replace('_','-')
        v=row(c,'variants',slug+'-release');t=v['task_id'];task=row(c,'tasks',t)
        p=row(c,'protocols',slug+'-probe')
        observed=[s for s in stats if s['task']==rid]
        evs=[]
        for s in observed:
            sid=slug+'-'+s['split']+'-file';url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{s["path"]}'
            c.source(sid,'GENEB '+item['label']+' '+s['split'],url,'dataset-file',rev,notes='Whole-file SHA-256 and derived measurements: data/geneb-artifact-inspections.json. CSV has text/label, without source coordinates or species metadata.')
            row(c,'sources',sid)['sha256']=s['sha256']
            e=c.ev(sid+'-audit',sid,'Complete CSV scan',f'{s["rows"]:,} rows; labels {s["label_counts"]}; lengths {s["length_min"]}–{s["length_max"]} nt; {s["distinct_sequences"]:,} distinct exact sequences. {s["train_test_exact_sequence_overlap"]:,} distinct exact sequences occur in both released train and test.','data');evs.append(e)
            c.count(t,s['rows'],'sequence rows',e,split=s['split'],variant=v['id'],protocol=p['id'],method='measured',qualifier='GENEB repackaged release, not the upstream dataset total.')
            for label,n in s['label_counts'].items():c.count(t,n,'sequence rows',e,split=s['split']+' / label '+label,variant=v['id'],protocol=p['id'],method='measured',qualifier='Observed integer label; biological class names require the upstream label mapping.')
            c.field('tasks',t,'input_description',e,f'GENEB {s["split"]}: measured {s["length_min"]}–{s["length_max"]} nt.')
            c.field('tasks',t,'label_basis',e,'Actual scalar label values and frequencies; not independent validation of the assay labels.')
        labels=set(k for s in observed for k in s['label_counts'])
        if task['status']=='registered':
            task.update(status='artifact-audited',task_type='binary classification' if len(labels)==2 else 'multiclass classification',
                        target=item['category']+' classification / '+item['label'],
                        description='Classify the released sequence windows with the GENEB frozen-embedding logistic-regression protocol. Observed label vocabulary: '+', '.join(sorted(labels))+'.',
                        label_basis='Released scalar integer labels. Class frequencies measured; detailed upstream biological label mapping is not present in these CSVs.',
                        limitations='Complete released train/test files and common readout were inspected. Files lack coordinates and per-row taxonomic metadata: chromosome, locus and homology separation cannot be reconstructed from this release alone. Species and label meanings are assigned only where separately documented.',
                        input_description='DNA sequence → frozen mean embedding; measured lengths recorded with the released variant.',evidence_id=evs[0])
            c.field('tasks',t,'status',evs[0],'Selected artifact audit; no claim of coordinate or homology audit.')
        p['split_rule']='Fixed released train/test CSVs; no development partition. Upstream validation/dev rows are excluded. Few-shot subsets come from train. Chromosome/homology grouping is not recoverable from the two released columns.'
        p['notes']=(p.get('notes') or '')+' Primary metric MCC. Exact train/test sequence overlap is measured separately; no reverse-complement or approximate-homology test was performed.'
        c.field('protocols',p['id'],'split_rule',card)
        c.field('protocols',p['id'],'requires_embeddings',card)
        c.field('protocols',p['id'],'selection',harness,'Full protocol averages five seed runs; few-shot k is per class, capped by available class rows.')
        for metric in c.rows['protocol_metrics']:
            if metric['protocol_id']==p['id']:
                metric['evidence_id']=harness
                metric['aggregation']='Mean over five seeds; macro-F1 across observed classes.' if metric['metric_id']=='f1' else 'Mean over five seeds; MCC is the primary metric.'
        v['input_length']=f'{min(s["length_min"] for s in observed)}–{max(s["length_max"] for s in observed)} nt (complete scan)'
        v['target_count']=len(labels);v['target_unit']='observed scalar classes'
        v['notes']=(v.get('notes') or '')+' Class counts and lengths are measured for this release; upstream biological split provenance remains separate.'
        overlap=observed[0]['train_test_exact_sequence_overlap']
        if overlap:c.finding(t,f'GENEB configuration {rid}: {overlap:,} distinct exact nucleotide strings appear in both released train and test. This comparison is case-sensitive and does not include reverse complements or homologous sequences. It does not establish pretraining exposure.',evs[0],severity='discrepancy',suite='geneb')
        if rid.startswith('leannmlindsey_GUE_'):
            suffix=rid.removeprefix('leannmlindsey_GUE_')
            if suffix.startswith('mouse_'):
                task['name']='GUE mouse TF binding / '+suffix.split('_')[-1]
                task['target']='TF binding versus dinucleotide-shuffled control'
                c.rows['task_categories']=[x for x in c.rows['task_categories'] if not(x['task_id']==t and x['category_id']=='enhancer')]
                category(c,t,'tfbs',source,'input','The introducing GUE paper identifies TF-M as mouse TF binding, with shuffled negatives; the GENEB category Mouse Enh. is misleading.')
                population(c,t,'mouse',source)
                c.finding(t,'GENEB categorizes this configuration as Mouse Enh.; GUE defines the mouse task as transcription-factor binding prediction, with dinucleotide-shuffled negatives. This catalogue follows the target definition, not the misleading category name.',source,severity='discrepancy',suite='geneb')
            elif suffix.startswith(('human_tf_','prom_','splice_')):population(c,t,'human',source)
            elif suffix.startswith('emp_'):population(c,t,'yeast',source)
            elif suffix.startswith('fungi_species'):population(c,t,'fungi',source)
            elif suffix.startswith(('virus_','phage_')):population(c,t,'viruses',source)
            c.field('tasks',t,'target',source)
            if suffix=='virus_species_40':c.finding(t,'The configuration name says virus_species_40, but the complete released train/test files contain 25 distinct integer classes. The name is retained as a source identifier, not a verified class count.',evs[0],severity='discrepancy',suite='geneb')
        if rid.startswith('katarinagresova_Genomic_Benchmarks_'):
            original='gb-'+rid.removeprefix('katarinagresova_Genomic_Benchmarks_')
            if original in c.ids['tasks']:
                upstream=row(c,'tasks',original)
                task['target']=upstream['target'];task['name']=upstream['name']+' / GENEB release'
                for link in list(c.rows['task_populations']):
                    if link['task_id']==original:population(c,t,link['population_id'],link['evidence_id'],link['relation'],link['coverage'])
                c.field('tasks',t,'target',upstream['evidence_id'],'Repackaged source; exact sequence and split equivalence are not assumed.')
        if rid.startswith('iPro-WAEL_Promoter_'):
            task['target']='Promoter versus control classification / '+item['label'];c.field('tasks',t,'target',biology)
            suffix=rid.removeprefix('iPro-WAEL_Promoter_')
            population(c,t,'arabidopsis' if suffix.startswith('Arabidopsis') else 'bacteria' if suffix in ('B_amyloliquefaciens','R_capsulatus') else 'human',biology)
        if rid.startswith('deep4mc_'):
            species=rid.removeprefix('deep4mc_').removesuffix('_4mC')
            task['target']='N4-methylcytosine (4mC) site presence';c.field('tasks',t,'target',biology)
            pop={'A.thaliana':'arabidopsis','C.elegans':'worm','D.melanogaster':'fly','E.coli':'ecoli'}.get(species)
            if pop:population(c,t,pop,biology)
            task['limitations']+=' The 41-nt windows and scalar labels do not encode reference coordinates or independently validate modification status.'
        if rid.startswith('iDNA_ABF_'):
            task['target']='5-methylcytosine (5mC) site presence' if rid.endswith('5mC') else 'N6-methyladenine (6mA) site presence';c.field('tasks',t,'target',biology)
        if rid.startswith('InstaDeepAI_plant-genomic-benchmark_lncrna.'):
            species=rid.split('lncrna.')[-1]
            task['target']='lncRNA versus coding RNA';c.field('tasks',t,'target',biology)
            pop={'g_max':'soybean','m_esculenta':'cassava','s_bicolor':'sorghum','s_lycopersicum':'tomato','t_aestivum':'wheat','z_mays':'maize'}[species]
            population(c,t,pop,biology)
        if rid=='InstaDeepAI_plant-genomic-benchmark_pro_seq.m_esculenta':
            task['target']='Cassava transcriptional activity class';population(c,t,'cassava',biology);c.field('tasks',t,'target',biology,'GENEB groups this under promoters; exact continuous-to-class conversion is not established by the two-column release.')
        if rid=='iDHS-EL_DNase_I':task['target']='DNase-I hypersensitive-site class';c.field('tasks',t,'target',biology)
    suite=row(c,'evaluations','geneb');suite['status']='artifact-audited';suite['notes']='All 200 pinned train/test CSVs scanned (3,393,004 rows in 100 configurations). Counts, labels, length ranges and exact train/test sequence overlap are measured. Twenty-five configurations share exact sequence strings across train/test. Coordinates and detailed biological source metadata are absent; these checks do not establish chromosome or homology separation.'

def rnagym(c):
    inspections=json.loads((ROOT/'data/rnagym-artifact-inspections.json').read_text())
    predictions=json.loads((ROOT/'data/rnagym-evo2-prediction-inspections.json').read_text())
    c.source('rnagym-predictions-archive','RNAGym model-prediction archive',predictions[0]['archive_url'],'dataset-archive','Selected Evo 2 members inspected 2026-11-26',notes='All 70 Evo 2 members were decompressed and checked against ZIP CRCs; member SHA-256 and finite scored-row counts recorded in data/rnagym-evo2-prediction-inspections.json. The full archive was not downloaded or hashed. The public host has an incomplete TLS issuer chain.')
    manifest=list(csv.DictReader((ROOT/'research/sources/MarksLab-DasLab--RNAGym/fitness/reference_sheet_final.csv').open(encoding='utf-8-sig')))
    score=c.code('rnagym-scorer-audit','MarksLab-DasLab/RNAGym','fitness/performance_fitness.py','def calculate_metrics(',
                 'Scorer removes WT rows lacking mutant, drops missing assay/model scores pairwise, and reports absolute Spearman, max(AUROC,1−AUROC) after assay-median binarization, and absolute MCC after both assay/model median thresholds.',end_needle='return {"Spearman"')
    splits=c.code('rnagym-split-audit','MarksLab-DasLab/RNAGym','fitness/utils/cv_split.py','def random_split_assay(',
                  'Released helper makes an 80/20 random split (seed 42); the similarity heuristic starts from it and swaps individual examples for up to 10,000 iterations when a train/validation pair exceeds 0.8 alignment similarity. It is not a guarantee of globally homology-disjoint folds.',end_needle='def save_splits(')
    evo=c.code('rnagym-evo-scorer','MarksLab-DasLab/RNAGym','fitness/baselines/Evo/score_evo_single_dms.py','import ',
               'RNAGym includes an Evo/Evo 2 likelihood-scoring baseline. These are evaluations by the RNAGym authors, not original Evo 2 paper experiments.')
    for archive in sorted(set(x['archive'] for x in inspections)):
        r=next(x for x in inspections if x['archive']==archive)
        c.source('rnagym-'+archive,archive+' public archive',r['archive_url'],'dataset-archive','Bytes retrieved 2026-11-26; SHA-256 recorded',notes='Archive and member hashes recorded in data/rnagym-artifact-inspections.json. Publisher URL is mutable. Public host has an incomplete TLS issuer chain; retrieval did not authenticate that chain. No credentials were sent.')
        row(c,'sources','rnagym-'+archive)['sha256']=r['archive_sha256']
    for m in manifest:
        rid=m['DMS_ID'];slug=rid.lower().replace('_','-');t='rnagym-'+slug;task=row(c,'tasks',t)
        r=next(x for x in inspections if x['archive']=='fitness_processed_assays' and Path(x['member']).stem==rid)
        e=c.ev('rnagym-file-'+slug,'rnagym-fitness_processed_assays',r['member'],f'Complete assay CSV: {r["rows"]:,} rows, {r["distinct_sequences"]:,} distinct sequences, lengths {r["length_min"]}–{r["length_max"]} nt, score range {r["numeric_score_range"]}. {r["scored_mutant_rows_before_model_missingness"]:,} mutant rows have a finite assay score before model-specific missingness. Member SHA-256 {r["sha256"]}.','data')
        v=c.variant(t,t+'-archive','RNAGym processed assay archive',e,length=f'{r["length_min"]}–{r["length_max"]} nt',revision=r['archive_sha256'],notes='Archive/member hash identifies measured bytes. No chromosome or species metadata in sequence/mutant/DMS_score columns.')
        task['status']='artifact-audited';task['evidence_id']=e
        task['target']=m['ASSAY_DESCRIPTION'] or m['TITLE']
        task['label_basis']='Released numerical DMS_score from the cited experimental assay; target directions and transformations differ across assays.'
        task['input_description']=f'Mutant nucleotide sequence; {r["length_min"]}–{r["length_max"]} nt in inspected file.'
        task['limitations']='Whole processed assay file and benchmark scorer inspected. Assay score is not a universal fitness scale. Taxonomic origin and experimental host are separate; no organism is inferred from protein-name abbreviations. Exact WT/reference mapping, original experimental processing and pretraining homology are not independently reconstructed.'
        c.count(t,r['rows'],'assay rows',e,variant=v,method='measured',qualifier='Includes any WT/missing-mutant row; not necessarily the number scored by a model.')
        c.count(t,r['scored_mutant_rows_before_model_missingness'],'eligible mutant rows',e,split='zero-shot cohort before model missingness',variant=v,method='measured',qualifier='Finite DMS_score and nonmissing mutant. Final scored rows are pairwise complete with a particular model score.')
        p=c.protocol(t,t+'-rnagym','RNAGym zero-shot fitness scoring',score,'zero-shot','Sequence likelihood / model-specific fitness score','Complete experimental variant library; no downstream fitting. WT rows with missing mutant are removed; assay/model missing scores removed pairwise. Different models can be scored on different retained subsets.','mutant sequence within one assay',metrics=(('abs-spearman','Absolute Spearman per assay; RNA-type and overall aggregation follow the released scorer.'),'symmetric-auroc','abs-mcc'),embeddings=False,variant=v,notes='Direction-invariant AUROC/MCC are distinct from raw AUROC/MCC. Mutation libraries within the same construct do not constitute a held-out-species test.')
        prediction=next(x for x in predictions if Path(x['member']).stem==rid)
        pe=c.ev('rnagym-evo2-file-'+slug,'rnagym-predictions-archive',prediction['member'],f'Complete released prediction member: {prediction["rows"]:,} rows; {prediction["scored_rows"]} finite assay/model score pairs after removing missing-mutant WT rows. Member SHA-256 {prediction["sha256"]}.','data')
        c.use('evo2',t,pe,'rna','external-evaluation',protocol=p,note='Actual released evo2_7b_score column verified. External RNAGym evaluation, not original Evo 2 paper usage.')
        for col,n in prediction['scored_rows'].items():c.count(t,n,'scored mutant rows',pe,split=col+' / finite paired scores',variant=v,protocol=p,method='measured',qualifier='Released prediction file after the scorer’s missing-mutant and paired finite-score filters; source/model execution not repeated.')
        if prediction['rows']!=r['rows']:c.finding(t,f'The Evo 2 prediction member contains {prediction["rows"]:,} rows versus {r["rows"]:,} in the processed assay member. Counts and finite scored pairs are recorded separately; archive members must not be assumed row-identical.',pe,severity='discrepancy',suite='rnagym')
        for x in inspections:
            if x['archive']!='fitness_CV_splits':continue
            stem=Path(x['member']).stem
            if stem not in (rid+'_train',rid+'_val'):continue
            kind=x['member'].split('/')[1];part='train' if stem.endswith('_train') else 'validation'
            ev=c.ev('rnagym-cv-'+slug+'-'+kind+'-'+part,'rnagym-fitness_CV_splits',x['member'],f'{x["rows"]:,} rows; {x["train_validation_exact_sequence_overlap"]} distinct exact sequences shared with its paired partition; member SHA-256 {x["sha256"]}.','data')
            vid=t+'-cv-'+kind
            if vid not in c.ids['variants']:
                c.variant(t,vid,'Supervised '+kind+' split',splits,revision=x['archive_sha256'],notes='Separate supervised train/validation release; no independent final test partition. Exact overlap is measured, not approximate homology.')
                c.protocol(t,vid+'-protocol','Released supervised '+kind+' partition',splits,'supervised training; model-dependent','Supervised sequence-to-score model; embedding requirement unspecified','Random 80/20 seed 42' if kind=='random' else '80/20 initialized from random seed 42, then alignment-similarity swap heuristic; separation is not guaranteed.','mutant within one assay',metrics=(),embeddings=None,variant=vid,notes='Inspected split files establish row assignment, not a complete supervised fitting/selection recipe or a separate final test set.')
            c.count(t,x['rows'],'assay rows',ev,split=part,variant=vid,protocol=vid+'-protocol',method='measured',qualifier='Measured released supervised partition; not used by the zero-shot protocol.')
            if part=='train' and x['train_validation_exact_sequence_overlap']:
                c.finding(t,f'Released supervised {kind} partitions share {x["train_validation_exact_sequence_overlap"]} distinct exact sequence strings between train and validation. This is separate from the zero-shot fitness protocol and is not a reverse-complement or approximate-homology comparison.',ev,severity='discrepancy',suite='rnagym')
        # Two splicing assays were incorrectly grouped into generic ncRNA.
        if m['RNA_TYPE']=='mRNA-splicing':
            c.rows['task_categories']=[x for x in c.rows['task_categories'] if not(x['task_id']==t and x['category_id']=='ncrna')]
            for cat in ('mrna','exon','splice'):category(c,t,cat,'rnagym-assay-'+slug,'assayed construct','The manifest explicitly describes exon splicing efficiency; this is a splicing assay, not a generic ncRNA-fitness assay.')
        if 'in yeast' in m['ASSAY_DESCRIPTION'] or 'yeast cells' in m['ASSAY_DESCRIPTION']:population(c,t,'yeast','rnagym-assay-'+slug,'assay-host','Manifest explicitly names yeast as the assay host; sequence origin is not inferred.')
        c.field('tasks',t,'target','rnagym-assay-'+slug)
        c.field('tasks',t,'status',e,'Whole processed CSV and metric procedure audited; source-organism gaps remain explicit.')
    s=row(c,'evaluations','rnagym');s['status']='artifact-audited';s['notes']='All 70 processed fitness assay files inspected: 1,117,406 rows. All 124 released supervised partition files inspected: 31 assays × random/similarity heuristic × train/validation. Fitness artifacts do not establish coverage or audit of the separate RNA structure tracks.'
    c.finding(None,'RNAGym fitness metrics discard score orientation per assay: absolute Spearman, max(AUROC,1−AUROC), and absolute MCC. AUROC/MCC use assay/model median thresholds; these are not interchangeable with a fixed pathogenicity threshold or signed correlation.',score,suite='rnagym')
    for f in c.rows['findings']:
        if f['evaluation_id']=='rnagym' and 'manifest count' in f['description']:f['description']='All 70 fitness assay files are now inspected; RNA secondary/tertiary structure tasks remain separate and have not been expanded. Fitness count must not be used as a structure benchmark count.'

def carbonx(c):
    repo='huggingface/carbon';base='carbon-x/evaluation/'
    e=c.code('carbonx-released-evaluator',repo,base+'README.md','# Carbon-X evaluation','Post-training evaluator maps five benchmark subsets to a single pinned DNAIntelligenceIndex dataset; HF split train is used as the evaluation cohort, not downstream fitting.',basis='documentation')
    c.source('carbonx-data-access','DNAIntelligenceIndex dataset access check','https://huggingface.co/datasets/HuggingFaceBio/DNAIntelligenceIndex','dataset','Evaluator pins 2e156b12ef70c0d2295394f90c885ec450c5c79f',notes='Public dataset API and pinned revision returned HTTP 401 on 2026-11-26. This does not distinguish private, renamed or unavailable resources. Raw prompts/rows could not be counted.')
    gap=c.ev('carbonx-data-access-result','carbonx-data-access','Unauthenticated public dataset API and pinned revision checked 2026-11-26','The evaluator and exact expected dataset revision are public, but the dataset endpoint returned HTTP 401. Reported counts remain model-card counts; raw row, taxon and biological-partition verification is unavailable.','documentation')
    details={
        'coding':('bioreason.py','bioreason_coding_sequence_only','Source BioReason coding test split; one fixed prompt per unique original/mutated sequence pair. Gene names are removed because original wording leaked the pathogenic label.','balanced-accuracy'),
        'non-snv':('bioreason.py','bioreason_non_snv','Every row of BioReason non-SNV test split is retained; original source is wanglab/variant_effect_non_snv.','balanced-accuracy'),
        'frontier':('vepqa.py','vepqa_single_1k','Generated answer is parsed and classified as benign/pathogenic; invalid answers remain misses. Coordinates/biological grouping cannot be checked without dataset access.','accuracy'),
        'nextbase':('seqrecqa.py','seqrecqa_varlen','Extract the final DNA answer; count position-wise matches divided by reference length. Missing/short answers lose unmatched positions; extra suffix bases do not lower the per-base score. Length-match accuracy is separate.','accuracy'),
    }
    for t in [x for x in c.rows['tasks'] if x['id'].startswith('carbonx-')]:
        slug=t['id'].removeprefix('carbonx-')
        file,needle,desc,metric=details.get(slug,('genomeqa.py','genomeqa_mcq_carbon','Four-choice question with answer_index mapped to A–D; choice scorer and per-subtask accuracy. Aggregate gives the six subtasks equal weight rather than weighting by question count.','accuracy'))
        ev=c.code('carbonx-scorer-'+slug,repo,base+'tasks/'+file,needle,desc)
        t['status']='paper-audited';t['evidence_id']=ev;t['description']+=' '+desc
        t['limitations']='Released loader, prompt adapter, scorer and aggregation inspected. Exact raw prompts, category counts, taxonomic membership, source-coordinate splits and decontamination cannot be verified: pinned dataset public API returned HTTP 401 on 2026-11-26. Published example counts remain reported, not measured.'
        p=row(c,'protocols',t['id']+'-chat');p['source_evidence_id']=ev
        p['split_rule']='Load the benchmark subset from DNAIntelligenceIndex at revision 2e156b12ef70c0d2295394f90c885ec450c5c79f, HF split train. This is a fixed evaluation collection; it does not imply model fitting or identify a chromosome/species split.'
        p['notes']=(p.get('notes') or '')+' '+desc
        c.field('protocols',p['id'],'split_rule',ev);c.field('tasks',t['id'],'status',ev,'Released procedure audited; dataset access is unresolved.')
        c.finding(t['id'],'Raw dataset verification is blocked by the cited dataset access result. The audit supports the released procedure, not complete artifact-level verification.',gap,suite='carbonx-evals')
        if slug=='nextbase':
            category(c,t['id'],'conditional-generation',ev,rationale='The model generates a continuation from the released DNA prefix prompt; scoring requires actual generated DNA.')
    row(c,'evaluations','carbonx-evals')['notes']='All ten task records now have released loader/scorer evidence. Five underlying subsets use one pinned dataset revision. HF train is an evaluation collection here. Raw data access returned HTTP 401; no fabricated category counts, species assignment or biological split are inferred.'

def deepd(c):
    repo='biomap-research/DeepD';path='notebook/interpretability/data/best_layers.csv'
    data=list(csv.DictReader((ROOT/'research/sources/biomap-research--DeepD'/path).open()))
    e=c.code('deepd-human-routing-release',repo,path,'species,','Human release contains six one-versus-rest targets and two checkpoints, with 72,000/9,000/9,000 train/validation/test rows per target/checkpoint; best-layer and full-test metrics are released.',basis='data')
    models=c.code('deepd-routing-model-release',repo,'notebook/interpretability/models/manifest.csv','species,','Twelve human routing classifiers are XGBoost 3.2.0 models, 576 input features and 5,000 trees each; the released demonstration differs from the linear-classifier description in the paper.',basis='data')
    demo=c.code('deepd-routing-interval',repo,'notebook/interpretability/data/manifest.json','"region"','Released interval is chr11:5,220,000–5,240,000 (0-based, end-exclusive), 20,000 bases. It is a local HBB diagnostic, not the full test set.',basis='data')
    old='deepd-annotation-human'
    # Replace the generic panel with dataset × binary annotation targets.
    for ann in sorted(set(x['annotation'] for x in data)):
        slug=ann.lower().replace('_','-');t='deepd-human-routing-'+slug
        reg=('cds',) if ann=='CDS' else ('regulatory',) if ann=='cCRE' else ('repeat',)
        c.task(t,'deepd-evals','Human routing probe / '+ann,'DeepD human routing annotation release',ann+' membership at each position','Binary one-versus-rest annotation from expert routing vectors. Human 8K and 1M checkpoints use the same reported sample counts; checkpoint/layer choice remains protocol-specific.','dense binary classification','Reference annotation membership',e,applications=('genome-annotation',),capabilities=('dense-annotation',),regions=reg,populations=('human',),input='576-dimensional expert-gating vector per position',output='Position-indexed annotation probability',status='artifact-audited',limitations='Released target manifest, metrics, HBB annotations and model metadata inspected. Full training coordinates and split reconstruction are not released with this example. Counts are metric-table reports, not recounted full-cohort arrays. XGBoost release is distinct from the paper linear probe; local interval is not the complete test set.')
        for x in (x for x in data if x['annotation']==ann):
            v=c.variant(t,t+'-'+x['model_tag'],x['model_label']+' checkpoint / '+x['layer'],e,targets=1,target_unit='binary membership target',context='Routing layer '+x['layer']+'; input context is a checkpoint property, not a controlled input-length ablation.')
            p=c.protocol(t,v+'-probe','Released XGBoost routing classifier',models,'frozen routing-weight probe','Expert gating weights → XGBoost classifier','Reported 72,000 train / 9,000 validation / 9,000 test rows. Coordinate grouping and sampling construction are not available in this example.','genomic position; grouping unresolved',metrics=('auprc','auroc'),embeddings=True,fitted='XGBoost 3.2.0; 576 features; 5,000 trees',selection='A best-layer table is released; selection criterion/cohort is not recoverable from the table alone.',variant=v,notes='Do not substitute these tree models for the paper’s reported linear probes.')
            for part,key in [('train','n_train'),('validation','n_validation'),('test','n_test')]:c.count(t,int(x[key]),'positions',e,split=part,variant=v,protocol=p,qualifier='Reported in released metrics table; full split arrays not independently recounted.')
            c.use('deepd',t,e,'deepd','released-example',protocol=p)
        c.field('tasks',t,'input_description',models)
        c.field('tasks',t,'dataset_name',demo,'The committed 20,000-base local interval is separate from the full split counts.')
    # A removed composite record does not survive as a second task for the same targets.
    for table in ('tasks','evaluation_tasks','task_categories','task_populations','protocols','counts','model_evaluations','variants','findings'):
        removed={x.get('id') for x in c.rows[table] if x.get('task_id')==old or table=='tasks' and x.get('id')==old}
        c.rows[table]=[x for x in c.rows[table] if not(x.get('task_id')==old or table=='tasks' and x.get('id')==old)]
        c.ids[table]-=removed
    valid_protocols=c.ids['protocols']
    c.rows['protocol_metrics']=[x for x in c.rows['protocol_metrics'] if x['protocol_id'] in valid_protocols]
    c.rows['field_evidence']=[x for x in c.rows['field_evidence'] if not(x['entity_table']=='tasks' and x['entity_id']==old)]
    c.finding(None,'The human routing release defines six binary annotation targets and XGBoost models; the paper describes linear probes. The released HBB interval is 20,000 bases and must not replace full-test statistics. Full coordinate/split provenance remains unavailable.',models,severity='discrepancy',suite='deepd-evals')

def unresolved_panels(c):
    # Complete source review can reveal an external information gap; do not fill it by
    # borrowing similarly named assays from another paper or by changing the badge.
    c.source('deepd-supplement-followup','DeepD supplementary figures and captions','https://www.biorxiv.org/content/biorxiv/early/2026/10/18/2026.10.13.758170/DC1/embed/media-1.docx?download=1','supplement','2026-10-18 v1','research/papers/deepd-supp.txt',notes='DOCX inspected, including figure captions. These do not enumerate the primary fitness assay IDs or TF accessions.')
    e=c.ev('deepd-panel-gap-review','deepd-supplement-followup','Figures S3–S5; public repository tree and released demonstration','Supplement confirms five human TF-binding datasets but does not identify the accessions. Public release contains H3 and human HBB examples, not the complete bacterial/eukaryotic/ncRNA/TF assay manifests. Composite task identities cannot be completed by assuming another model’s panel.','documentation')
    for t in c.rows['tasks']:
        if t['status']=='panel-pending' and t['id'].startswith('deepd-'):
            reason='Exact assay IDs / primary split manifests not established in the inspected main paper, supplemental figure captions or public example release.'
            if t['id']=='deepd-annotation-bacteria':reason='Paper identifies E. coli CRISPR repeat/spacer and lac-region annotation examples; complete target manifest, training rows and split coordinates are not available in the inspected release.'
            if t['id']=='deepd-annotation-maize':reason='Paper lists CDS, intron, UTR, CRE and TE-family outputs; the complete TE-family target list and coordinate/split manifest are not available in the inspected release.'
            t['limitations']=reason+' This is an unresolved source-information gap after review, not an audited dataset × target task.'
            if t['id']=='deepd-annotation-bacteria':
                c.rows['task_populations']=[x for x in c.rows['task_populations'] if x['task_id']!=t['id']]
                population(c,t['id'],'ecoli',t['evidence_id'])
            c.finding(t['id'],reason,e,suite='deepd-evals')
            c.field('tasks',t['id'],'limitations',e)
    c.source('gpn-panel-release-check','GPN-Star published Hugging Face collection','https://huggingface.co/collections/songlab/gpn-star-68c0c055acc2ee51d5c4f129','dataset-registry','Collection inspected 2026-11-26','research/artifacts/audit-followup/gpn-collection.json',notes='Public collection enumerates trained alignments, scores and named benchmark datasets but no ProteinGym assay manifest. Archived GPN-MSA workflow lists 31 candidate assays; equivalence to the GPN-Star scored panel is not established.')
    e=c.ev('gpn-panel-gap-review','gpn-panel-release-check','Published collection; supplement Evaluation Benchmarks; archived upstream analysis','GPN-Star reports 31 human ProteinGym v0.1 assays and CADD-based nucleotide conversion, but an exact assay-ID/retained-score manifest was not established from the released collection. Earlier GPN-MSA CADD-derived files are candidate upstream sources, not proof of the final GPN-Star common-score intersection.','documentation')
    t=row(c,'tasks','gpn-proteingym');t['limitations']='Source review complete for the stated panel protocol, but exact GPN-Star assay-ID and retained-variant manifest is not established. Do not replace this with the 31 similarly named upstream GPN-MSA assays without a verifiable mapping.'
    c.finding(t['id'],t['limitations'],e,suite='gpn-evals');c.field('tasks',t['id'],'limitations',e)

def capabilities(c):
    c.add('categories',id='unconditional-generation',dimension='capability',name='Unconditional generation',definition='Sample sequence without a biological prefix, target activity or other example-specific inference condition. Task-specific training can still define the model distribution.',accommodation='A generative sampling procedure is required; a start-of-sequence token alone is not a biological condition.')
    # Conditional generation is a subset of generation, not a competing label.
    for link in list(c.rows['task_categories']):
        if link['category_id']=='conditional-generation':category(c,link['task_id'],'generation',link['evidence_id'],rationale='Parent capability: this protocol emits nucleotide sequence under a specified condition.')
    for slug in ('p450','histone'):
        t='generator-family-'+slug;task=row(c,'tasks',t)
        c.rows['task_categories']=[x for x in c.rows['task_categories'] if not(x['task_id']==t and x['category_id']=='conditional-generation')]
        category(c,t,'unconditional-generation',task['evidence_id'],rationale='Paper §4.4 and Appendix D describe sampling from separately family-fine-tuned models without a sequence/activity inference prompt. Family-specific training is not an example-specific inference condition. Exact start-token initialization is not reported.')
        task['limitations']=(task.get('limitations') or '')+' The paper describes family-specific adaptation and sampling without a biological inference prompt; generation initialization code was not established. Unconditional classification is based on the reported protocol, not a verified sampler implementation.'
    # One count value for a whole peak does not preserve an output coordinate axis.
    c.rows['task_categories']=[x for x in c.rows['task_categories'] if not(x['task_id']=='botanic1-atac-counts' and x['category_id']=='dense-annotation')]
    for x in c.rows['task_categories']:
        if x['task_id']=='genecad-busco' and x['category_id']=='dense-annotation':
            x['relation']='downstream validation';x['rationale']='BUSCO measures completeness of the proteome produced by the annotation pipeline; it does not directly score per-base labels.'
    row(c,'categories','dense-annotation')['definition']='Predict an output indexed by genomic position: labels, signal profiles, boundaries or structured coordinates across an input sequence. A single label or count for an entire window is not dense annotation.'
    row(c,'categories','generation')['definition']='Produce nucleotide sequence by sampling, completion or sequence optimization. This parent category includes conditional and unconditional generation; candidate selection and probability-only scoring are separate.'
