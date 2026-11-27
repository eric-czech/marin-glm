"""NABench: reconcile the paper, manifest, actual files and shared RNA tasks."""
from pathlib import Path
import collections
import csv
import json
from common import Catalogue, ROOT

REV='99c8681ec1eab706e10ff90a5c329dcf184cc1d1'
REPO='https://github.com/mrzzmrzz/NABench'
PDF='https://arxiv.org/pdf/2511.02888v1'


def populate(d):
    c=Catalogue(d)
    # Earlier imports confused this identity inventory with an actual split.
    for table in ['task_resources','evaluation_resources']:
        d[table]=[r for r in d.get(table,[]) if not (r['resource_id']=='nabench-metadata' and r['relation']=='split-manifest')]
    root=ROOT/'research/artifacts/final-audit/registered-nabench'
    metadata=list(csv.DictReader((root/'metadata.csv').open()))
    scans=json.loads((ROOT/'data/nabench-artifact-inspections.json').read_text())
    files={r['id']:r for r in scans['files']}
    byid={r['DMS_ID']:r for r in metadata}
    c.source('nabench-complete-paper','NABench complete paper and appendices',PDF,
        version='arXiv 2511.02888v1; 42 pages',path='research/artifacts/final-audit/nabench.pdf')
    methods=c.evidence('nabench-complete-methods','nabench-complete-paper','§3.4–3.6; AppendicesB–D; PDFpp.6–7,25–29',
        'Paper reports mean representation scores without fitting, ridge probes with fivefold random or mutation-position-block CV, ten-label ridge probes and cross-assay transfer. DMS supervised metric is Spearman; SELEX supervised metric is AUROC. Zero-shot reports Spearman, NDCG, AUROC and MCC, defining the top 10% of fitness scores as positives. Splits are over mutant rows, positions or assays, not species or chromosomes. Exact fold indices and downstream ridge implementation are not in the inspected release.',url=PDF+'#page=6')
    biology=c.evidence('nabench-complete-biology','nabench-complete-paper','AppendixA, Tables3–4 and study descriptions; PDFpp.18–25',
        'Named phenotypes include catalytic RNA activity, aminoacylation, suppressor function, splicing, promoter/enhancer activity and binding selection. Table 3 and Appendix A.4 contain biological misdescriptions. Classifications use the released files and original assay studies where available; the benchmark appendix alone is not reliable evidence of molecule identity or organism.',url=PDF+'#page=18')
    c.source('nabench-release-readme','NABench released-data availability',REPO+f'/blob/{REV}/README.md','repository-file',REV,
        'research/artifacts/final-audit/registered-nabench/README.md')
    release=c.evidence('nabench-release-availability','nabench-release-readme','Resources, lines68–70; complete repository data tree',
        'README says DMS assay data are released in data/, while processed SELEX data are not released. At this pinned revision there are 47 CSV files. The 170-row metadata manifest is not a 170-file release or the same inventory as the 162 paper assays.','documentation',REPO+f'/blob/{REV}/README.md#L68-L70')
    c.source('nabench-release-metadata','NABench assay metadata',REPO+f'/blob/{REV}/metadata.csv','dataset-manifest',REV,
        'research/artifacts/final-audit/registered-nabench/metadata.csv')
    manifest=c.evidence('nabench-manifest-complete-review','nabench-release-metadata','All 170 manifest rows, compared with 47 CSV filenames',
        f'Manifest has 170 rows. {len(scans["manifest_ids_without_files"])} manifest IDs have no corresponding CSV. Two Rachapun f1u files are present but absent from the manifest; both appear in paper Table 4. The union is 172 named entries, not 172 independent tasks. Many entries are selection rounds, linker lengths, environments or trajectory libraries.','data')
    c.source('nabench-evo-extractor','NABench Evo readout implementation',REPO+f'/blob/{REV}/scripts/evo/seq_emb.py','repository-file',REV,
        'research/artifacts/final-audit/registered-nabench/scripts/evo/seq_emb.py')
    interface=c.evidence('nabench-evo-readout-review','nabench-evo-extractor','extract_features and main; lines 139–248',
        'Despite the embedding docstring, the Evo script stores per-position logits_to_logprobs of observed tokens. It does not extract a hidden-layer embedding or trim individual padded positions after batching. It removes nonfinite rows and saves scores with DMS_score. Generic paper embedding terminology is not proof that all models use hidden embeddings; exact downstream ridge/fold code is not released.','code',REPO+f'/blob/{REV}/scripts/evo/seq_emb.py#L139-L248')
    c.resource('nabench-data','nabench-release-readme','NABench released assay CSVs','dataset','github',REPO+f'/tree/{REV}/data',release,REV,
        notes='47 released CSV files. Processed SELEX libraries are not included.')
    c.resource('nabench-metadata','nabench-release-metadata','NABench assay manifest','manifest','github',REPO+f'/blob/{REV}/metadata.csv',manifest,REV,
        notes='170 named entries; not a release of 170 assay tables.')
    c.resource('nabench-code','nabench-evo-extractor','NABench model feature extraction','evaluation-code','github',REPO+f'/tree/{REV}/scripts',interface,REV,
        notes='Feature extraction scripts; downstream ridge-fitting and fold manifests are not supplied.')
    c.collection_resource('nabench','nabench-data',release)
    c.collection_resource('nabench','nabench-metadata',manifest,'identity-manifest',note='Assay identity manifest only; contains no fold assignments.')
    c.collection_resource('nabench','nabench-code',interface,'evaluation-code')
    c.get('evaluations','nabench').update(status='artifact-audited',source_id='nabench-release-readme',
        description='Nucleotide fitness and regulatory assays with zero-shot representation scores, ridge probes and source-defined transfer settings.',
        scope_note='Dataset–target records reuse matching RNAGym targets. Selection rounds, library trajectory steps, linker lengths and environments are linked variants. Released files, manifest-only claims and paper counts remain distinct.',
        evidence_id=methods,notes='Paper: 162 assays / 2.6 million mutants. Inspected release: 47 CSV files; 170 manifest entries and two additional files named by the paper. Processed SELEX data and exact evaluation-fold manifests are not released. Several appendix descriptions conflict with the original assay studies; those conflicts are recorded explicitly.')
    # Exact released assay IDs identify shared RNAGym targets. A new release
    # becomes a variant; it does not become a second canonical biological task.
    existing={t['dataset_name']:t['id'] for t in d['tasks'] if t['id'].startswith('rnagym-')}
    groups=collections.defaultdict(list)
    for aid in sorted(set(byid)|set(files)):
        if aid in existing:groups[existing[aid]].append(aid)
        elif aid.startswith('Rachapun_'):groups['nabench-rachapun-ribozyme'].append(aid)
        elif aid.startswith('Townshend_'):groups['nabench-townshend-device'].append(aid)
        elif aid.startswith('Eilon_'):groups['nabench-sharon-promoter'].append(aid)
        elif aid.startswith('Adriana_2020_aptamer_cycle'):groups['nabench-fuente-selection'].append(aid)
        elif aid.startswith('Dimitri_2022_aptamer_Cycle'):groups['nabench-simaeys-selection'].append(aid)
        elif aid.startswith('Li_2018_fitness'):groups['nabench-li-environments'].append(aid)
        elif aid.startswith('Baeza-Centurion_'):groups['nabench-baeza-splicing'].append(aid)
        elif aid.startswith('Martin_2019_'):groups['nabench-martin-regulatory-panel'].append(aid)
        elif aid=='Yu_2024_glmS_ribozyme':groups['nabench-yu-glms'].append(aid)
        elif aid=='Shai_2015_promoter':groups['nabench-lubliner-promoter'].append(aid)
        elif aid=='Gregory_2018_mRNA':groups['nabench-findlay-readout'].append(aid)
        elif aid=='Martin_2018_myc_enhancer':groups['nabench-myc-enhancer'].append(aid)
        elif aid=='Patwardhan_2012_fitness_ECR11enhancer':groups['nabench-ecr11-enhancer'].append(aid)
        elif aid=='Starita_2021_splicing_assay_SRSF1_binding_site':groups['nabench-srsf1-binding'].append(aid)
        elif aid=='Starita_2021_splicing_assay_Wilms_tumor_gene_exon':groups['nabench-wt1-splicing'].append(aid)
        else:groups['nabench-selection-panel'].append(aid)
    specs={
        'nabench-rachapun-ribozyme':('Rotrattanadumrong 2022: RNA ligase activity','Relative RNA ligation activity',['ribozyme'],['synthetic']),
        'nabench-townshend-device':('Townshend 2015: RNA device activity','Regulatory activity of an aptamer–ribozyme device',['aptamer','ribozyme'],['synthetic']),
        'nabench-sharon-promoter':('Sharon 2012: promoter activity','Reporter expression associated with promoter variants',['promoter'],['yeast']),
        'nabench-fuente-selection':('DeLaFuente2020: selection enrichment','Selection-derived sequence fitness',['aptamer'],['synthetic']),
        'nabench-simaeys-selection':('VanSimaeys2022: selection enrichment','Selection-derived sequence fitness',['aptamer'],['synthetic']),
        'nabench-li-environments':('Li2018: tRNA fitness across environments','Cellular fitness of tRNA variants',['trna'],[]),
        'nabench-baeza-splicing':('Baeza-Centurion2020: exon splicing','Exon-inclusion phenotype',['exon','splice'],['human']),
        'nabench-martin-regulatory-panel':('NABench: named regulatory activity panel','Regulatory-element fitness; exact phenotype/element mapping not released',['regulatory'],[]),
        'nabench-yu-glms':('Yu2024: glmS ribozyme activity','Catalytic cleavage rate',['ribozyme'],['taxon-1423']),
        'nabench-lubliner-promoter':('Lubliner2015: core-promoter activity','Reporter expression associated with core-promoter variants',['promoter'],['yeast']),
        'nabench-findlay-readout':('NABench Findlay2018: released DMS score','Released DMS_score; cell-viability versus RNA-abundance mapping not specified',['exon','splice'],['human']),
        'nabench-myc-enhancer':('NABench: MYC enhancer activity','Released enhancer-activity DMS score',['enhancer'],[]),
        'nabench-ecr11-enhancer':('NABench: ECR11 enhancer activity','Reported enhancer-activity fitness',['enhancer'],[]),
        'nabench-srsf1-binding':('NABench: SRSF1 binding-site fitness','Reported RNA-binding-site fitness',['ncrna'],[]),
        'nabench-wt1-splicing':('NABench: WT1 exon splicing','Reported exon-splicing fitness',['exon','splice'],[]),
        'nabench-selection-panel':('NABench: unreleased selection experiments','Selection-enrichment fitness across named experimental libraries',['aptamer'],['synthetic'])}
    for tid,aids in groups.items():
        released=[a for a in aids if a in files]
        new=tid not in {t['id'] for t in d['tasks']}
        if not new and tid in specs:
            c.get('tasks',tid).update(name=specs[tid][0],target=specs[tid][1],output_description=specs[tid][1])
        if new:
            name,target,features,pops=specs[tid]
            limits='Exact released evaluation-fold membership and downstream fitting implementation are not supplied.'
            if not released:limits+=' Processed sequence/fitness tables are not released for these named entries.'
            if tid in ['nabench-selection-panel','nabench-martin-regulatory-panel']:
                limits+=' Per-entry target identities or primary-study mappings are incomplete in the manifest. This is an explicitly retained source panel, not a fully resolved collection of independent assays.'
            if tid=='nabench-findlay-readout':limits+=' Paper Table3 lists both viability and mRNA abundance; the released scalar column does not identify which phenotype it represents. Sequences contain an X separator; this is not a pure CDS fitness task.'
            c.put('tasks',dict(id=tid,name=name,dataset_name='NABench / '+', '.join(aids) if len(aids)<=2 else 'NABench / '+name,
                target=target,description='Predict one scalar functional score per supplied sequence. Named release entries and conditions are preserved as linked variants.',
                task_type='regression / ranking',label_basis='Released DMS_score values' if released else 'Paper/manifest claim; processed labels not released',
                status='artifact-audited' if released else 'source-limited',evidence_id=biology,limitations=limits,
                input_description='Supplied nucleotide variant or synthetic selection-library sequence; raw lengths and alphabet recorded for each released file.',output_description=target))
            for feature in features:c.category(tid,feature,biology,'Study-specific functional target; no inference of dense labeling from element name.')
            for category in ['functional-prediction','rna-engineering' if set(features)&{'ribozyme','aptamer','trna','ncrna','splice'} else 'regulatory-engineering']:
                c.category(tid,category,biology,'The target measures sequence function in the reported assay.')
            if pops:
                for pop in pops:c.population(tid,pop,biology,'Source-defined molecule/construct origin. Selection targets and assay hosts are not treated as genomic origin.')
            else:c.unknown_origin(tid,manifest,'Sequence origin is not established by the supplied metadata; no taxon inferred from an assay target name.')
            partial=not released or tid=='nabench-findlay-readout'
            c.output(tid,'isolated',methods,'One scalar score per supplied sequence','sequence variant / experimental library',status='partial' if partial else 'supported',
                limitations=limits,rationale='The source evaluates sequence-level fitness, not base-wise annotation or complete biological structures.')
        c.member(tid,'nabench',manifest,note='The linked entries are release/condition variants; counts are not independent biological tasks.')
        c.task_resource(tid,'nabench-metadata',manifest,'identity-manifest',note='Identity metadata only; does not supply labels or splits.')
        c.task_resource(tid,'nabench-code',interface,'evaluation-code')
        for aid in aids:
            s=files.get(aid);vid='nabench-'+aid.lower().replace('_','-')+'-release'
            c.put('variants',dict(id=vid,task_id=tid,name=aid,dataset_revision=REV,context='Named assay/library/selection round or condition, as released.',
                input_length=(str(s['length_min'])+'–'+str(s['length_max'])+'nt (complete scan)') if s else None,
                target_count=1,target_unit='scalar fitness score',notes='Actual file inspected.' if s else 'Manifest-only named entry; processed labels and per-entry split files are not released.',evidence_id=manifest))
            if not s:continue
            sid='nabench-file-'+aid.lower().replace('_','-')
            url=REPO+f'/blob/{REV}/'+s['path']
            c.source(sid,'NABench '+aid,url,'dataset-file',REV,'research/artifacts/final-audit/registered-nabench/'+s['path'])
            eid=c.evidence(sid+'-inspection',sid,'Complete CSV scan; data/nabench-artifact-inspections.json',
                f'{s["rows"]} rows; {s["unique_sequences"]} unique exact sequences; lengths {s["length_min"]}–{s["length_max"]}; columns {s["columns"]}; {s["nonfinite_score_rows"]} nonfinite scores. Whole-file hash retained. No fold column.','data')
            rid='nabench-data-'+aid.lower().replace('_','-')
            c.resource(rid,sid,aid,'dataset','github',url,eid,REV,notes='Exact released CSV. Scope and counts refer to this NABench file, not upstream cohort totals.')
            c.task_resource(tid,rid,eid,variant=vid)
            c.count(tid,s['rows'],'sequence rows',eid,variant=vid,method='measured',qualifier='Complete NABench release scan, before model-specific missingness.')
            c.field('tasks',tid,'input_description',eid,'Measured lengths and nucleotide alphabet; no independent validation of biological phenotype.')
        # A positional mutant split requires a wild-type coordinate system.
        # A named SELEX round without a released WT mapping cannot inherit it.
        arms=['zero','random','few-shot','transfer']
        if tid.startswith('rnagym-') or tid in ['nabench-rachapun-ribozyme','nabench-li-environments','nabench-baeza-splicing','nabench-yu-glms']:
            arms.insert(2,'position')
        for arm in arms:
            pid=tid+'-nabench-'+arm
            split={'zero':'No downstream fitting; all eligible assay sequences scored.',
                'random':'Fivefold random variant-level CV; exact row assignments are not released.',
                'position':'Five contiguous blocks along wild-type sequence; mutation-position block held out. Exact assignments and handling of variants spanning blocks are not released.',
                'few-shot':'Ten labeled examples for ridge training; exact sampled rows and seed manifests are not released.',
                'transfer':'Fit on complete source assays and evaluate another assay; exact donor/recipient and row manifests are not released for every named entry.'}[arm]
            c.protocol(pid,tid,'NABench '+arm+' protocol','zero-shot representation score' if arm=='zero' else 'frozen representation ridge probe',
                'Paper: mean representation for zero-shot scores; ridge for fitted settings. Evo release instead stores position-wise observed-token log probabilities; a hidden-embedding interface cannot be inferred from the generic paper description.',
                split,'mutant sequence / mutation-position block / source assay',methods,
                [('spearman','DMS assay correlation; source-specific scoring cohort.'),('auroc','SELEX supervised or top 10%-fitness zero-shot classification, as specified by the source.')],
                embeddings=None,fitted=None if arm=='zero' else 'Ridge regression',notes='Paper-defined protocol family. The release does not provide a complete task × arm execution manifest; association with this task records the defined evaluation procedure rather than a verified result for every linked condition.')
            if arm=='zero':
                for metric in ['ndcg','mcc']:c.put('protocol_metrics',dict(protocol_id=pid,metric_id=metric,aggregation='Source-defined assay metric; the top 10% of fitness scores defines binary labels where applicable.',is_primary=False,evidence_id=methods),('protocol_id','metric_id'))
        c.limit('tasks',tid,'split_manifest','not-released','Paper defines random/position/assay protocols but release provides no fold assignment or ten-label subset manifest.',methods)
        if not released:c.limit('tasks',tid,'processed_labels','not-released','Named source entries are retained; corresponding processed sequence/fitness CSVs are absent from the pinned release.',release)
        if tid in ['nabench-selection-panel','nabench-martin-regulatory-panel','nabench-findlay-readout']:
            c.limit('tasks',tid,'target','not-reported','Exact per-entry phenotype/target mapping is not established by the paper/manifest/CSV combination. The task target and linked variants state the available scope.',biology)
        c.review('tasks',tid,'NABench paper and complete release inventory; exact assay-ID matching; all available sequence/score rows for the linked variants; released model feature interfaces and missing fold manifests.',
            [methods,manifest,release,interface]+[r['evidence_id'] for r in d.get('task_resources',[]) if r['task_id']==tid],
            limitations='This review establishes the NABench release-specific association. Original-source targets and protocols remain separately attributed. Unreleased entries retain explicit source limits.')
    primaries=[
        ('rachapun','10.1038/s41467-022-32538-z','Experimental exploration of a ribozyme neutral network using evolutionary algorithm and deep learning',
         'nabench-rachapun-ribozyme','Results, Fig. 2 and Methods',
         'The original study measures relative ligation activity in the 35 nt catalytic core of the F1*U RNA ligase, including evolutionary trajectory libraries and the 2^16 intermediates between two active sequences. It is not a hammerhead self-cleavage assay. The study-wide total over 120,000 sequences is not substituted for the counts of individual NABench files.'),
        ('townshend','10.1038/nmeth.3486','High-Throughput, Data-Rich Cellular RNA Device Engineering',
         'nabench-townshend-device','Abstract; RNA device architecture; FACS-Seq and yeast transformation methods',
         'The devices use ligand-responsive aptamer–ribozyme tertiary interactions, measured by FACS-Seq in budding yeast W303α. They are not mammalian toehold switches. The synthetic device sequences are distinguished from the assay host; linker lengths remain variants of the same device-activity task.'),
        ('sharon','10.1038/nbt.2205','Inferring gene regulatory logic from high-throughput measurements of thousands of systematically designed promoters',
         'nabench-sharon-promoter','Results and Fig. 1; Methods',
         'A library of 6,500 designed promoters tests yeast transcription-factor sites and nucleosome-disfavoring sequences through YFP expression and cell sorting. E. coli is used for plasmid amplification before transformation into yeast. The study is not an HEK293 promoter assay. The two NABench files are release-specific variants, not independent human assays.'),
        ('lubliner','10.1101/gr.188193.114','Core promoter sequence in yeast is a major determinant of expression level',
         'nabench-lubliner-promoter','Library design; reporter measurements; Methods',
         'The study synthesizes 13,000 oligos encoding 7,536 unique 118 bp core-promoter sequences, with extra barcoded replicates, and measures reporter activity in S. cerevisiae. It includes native, designed and orthologous promoters. NABench does not release this processed file; neither the study total nor a generic ADH1 library description establishes its retained NABench cohort.')]
    for name,doi,title,tid,locator,statement in primaries:
        sid='nabench-primary-'+name;url='https://doi.org/'+doi
        c.source(sid,title,url,version='Full-text primary study; Europe PMC XML',path='research/artifacts/final-audit/nabench-'+name+'.xml')
        eid=c.evidence(sid+'-review',sid,locator,statement,url=url)
        for field in ['target','label_basis','input_description']:c.field('tasks',tid,field,eid)
        for r in d['task_categories']:
            if r['task_id']==tid:r['evidence_id']=eid
        c.limit('tasks',tid,'benchmark_appendix_description','conflicting',statement,biology)
        c.get('source_reviews','tasks-'+tid+'-review')['evidence_ids_json']=json.dumps([methods,manifest,release,interface,eid])
    # Remove old positional-protocol rows from entries without a released WT
    # coordinate system; a source-defined protocol family is not universal use.
    keep_position={tid+'-nabench-position' for tid in groups if tid.startswith('rnagym-') or tid in ['nabench-rachapun-ribozyme','nabench-li-environments','nabench-baeza-splicing','nabench-yu-glms']}
    removed={p['id'] for p in d['protocols'] if p['id'].endswith('-nabench-position') and p['id'] not in keep_position}
    d['protocols']=[p for p in d['protocols'] if p['id'] not in removed]
    d['protocol_metrics']=[r for r in d['protocol_metrics'] if r['protocol_id'] not in removed]
    c.limit('evaluations','nabench','assay_inventory','conflicting','Paper: 162 assays; manifest: 170 rows; release: 47 CSV files with two files absent from the manifest. These are different inventories.',manifest)
    c.limit('evaluations','nabench','downstream_code','not-released','Release contains model feature extractors, not the complete ridge/CV/transfer execution harness.',interface)
    c.review('evaluations','nabench','Complete 42-page paper and appendices; all 170 metadata rows and all 47 released CSVs; feature extractors; exact-ID overlap with RNAGym; grouped condition/round variants.',
        [methods,biology,release,manifest,interface],limitations='Processed SELEX tables, exact folds and some target mappings are source-limited. No model inference or label-validity experiment is claimed.')
    return d


if __name__=='__main__':
    p=ROOT/'data/catalogue.json';p.write_text(json.dumps(populate(json.loads(p.read_text())),ensure_ascii=False,indent=2)+'\n')
