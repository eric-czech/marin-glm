'Source audit of LRB, DNALongBench, Gene-MTEB, LAMBDA and GenBench.\n\nAuthoring only: populate(d) returns normalized records; it never writes the catalogue.\nPinned releases and measured artifact scans are kept distinct from paper protocols.\n'
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'research/artifacts/final-audit'
# Compact, committed artifact measurements allow repeatable curation without raw GB files.
INSPECTIONS = json.loads((ROOT / 'data/registered-benchmark-inspections.json').read_text())
DATE = '2026-11-27'
REVISIONS = {
    'lrb': ('InstaDeepAI/genomics-long-range-benchmark', 'b56f68ee30c01daf8f80a8d0b8a47f84199de08e'),
    'dnalongbench': ('ma-compbio/DNALONGBENCH', '6c43266c6dc85b5529b5a784b880ee88cc1a54b3'),
    'genemteb': ('metagene-ai/gene-mteb', 'cdfacab370d8ec49370a78d3ab283f6a27d98cf0'),
    'lambda': ('leannmlindsey/LAMBDA', '21c4441f714ade5efa91157229f0595ef15e166c'),
    'genbench': ('jimmylihui/OpenGenome', '3a1f870b346c5b9b464b664f562d2b4d03618c7c'),
}


def populate(d):
    def put(table, row, keys=('id',)):
        d.setdefault(table, [])
        old = next((r for r in d[table] if all(r.get(k) == row.get(k) for k in keys)), None)
        if old is None:
            d[table].append(row)
        else:
            old.update(row)
        return row

    def evidence(eid, source, locator, statement, url=None, basis='paper'):
        src = next(s for s in d['sources'] if s['id'] == source)
        put('evidence', dict(id=eid, source_id=source, locator=locator, statement=statement,
                            url=url or src['url'], basis=basis, inspected=DATE))
        return eid

    def code(group, file, slug, statement, lines=None):
        repo, rev = REVISIONS[group]
        if rev is None:
            import subprocess
            rev = subprocess.check_output(['git', '-C', str(ART / ('registered-' + group)), 'rev-parse', 'HEAD'], text=True).strip()
        host = 'https://huggingface.co/datasets/' if group == 'lrb' else 'https://github.com/'
        url = f'{host}{repo}/blob/{rev}/{file}'
        path = ART / ('registered-' + group) / file
        sid = f'final-{group}-{slug}'
        put('sources', dict(id=sid, title=f'{repo}: {file}', kind='repository-file', url=url,
            version=rev, retrieved=DATE, sha256=INSPECTIONS['source_files'][group + '/' + file],
            local_path=str(path.relative_to(ROOT)), availability='available',
            notes='Pinned released interface inspected; source audit does not imply independent biological label validation.'))
        return evidence(sid + '-evidence', sid, file + (f' lines {lines}' if lines else ''), statement,
                        url + (f'#L{lines}' if lines else ''), 'code')

    def paper(group, slug, locator, statement):
        return evidence(f'final-{group}-{slug}', 'project-paper-' + group, locator, statement)

    def mapped(tid, pop, eid, note):
        template = next((m for m in d['coverage_mappings'] if m['population_id'] == pop), None)
        if template is None and pop == 'phages':
            template = copy.deepcopy(next(m for m in d['coverage_mappings'] if m['population_id'] == 'viruses'))
            md = json.loads(template['metadata_json'])
            md.update(name='Bacteriophages; lineage not resolved by released source labels', taxonomy=None)
            template['metadata_json'] = json.dumps(md)
        if template is None and pop == 'mammals':
            template = copy.deepcopy(next(m for m in d['coverage_mappings'] if m['population_id'] == 'human'))
            template.update(species_row='species:mammalia-unresolved', all_species_row='allSpecies:mammalia-unresolved')
            md = json.loads(template['metadata_json'])
            md.update(row='mammalia-unresolved', name='Mammals; scientific species unresolved', species=None, speciesId=None, allSpeciesRow='mammalia-unresolved')
            template['metadata_json'] = json.dumps(md)
            for view in ['species','allSpecies']:
                rid = view + ':mammalia-unresolved'
                existing = next(r for r in d['coverage_rows'] if r['id'] == view + ':mammalia-sp-9606')
                row = copy.deepcopy(existing)
                md = json.loads(row['metadata_json'])
                md.update(id='mammalia-unresolved', label='Scientific species unresolved', common='hippo / lemur config names', kind='unresolved', members=[], note='GenBench config names hippo and lemur, without scientific names or assembly accessions.')
                row.update(id=rid, row_key='mammalia-unresolved', population_ids_json='["mammals"]', metadata_json=json.dumps(md))
                put('coverage_rows', row)
        if template is None:
            raise ValueError('No coverage placement for audited origin: ' + str(pop))
        row = copy.deepcopy(template)
        row.update(id=tid + '-mapping-' + (pop or 'unknown'), task_id=tid, population_id=pop,
                   evidence_id=eid, supporting_json='[]', basis='audited sequence origin' if pop else 'source does not resolve sequence origin')
        md = json.loads(row['metadata_json'])
        md.update(url=next(e['url'] for e in d['evidence'] if e['id'] == eid), note=note, basis=row['basis'])
        row['metadata_json'] = json.dumps(md, ensure_ascii=False)
        put('coverage_mappings', row)
        if pop is not None:
            put('task_populations', dict(task_id=tid, population_id=pop, variant_id=None,
                relation='sequence-origin', coverage=note, evidence_id=eid), ('task_id', 'population_id', 'relation'))

    def category(tid, cid, eid, why, relation='target'):
        put('task_categories', dict(task_id=tid, category_id=cid, relation=relation,
            rationale=why, evidence_id=eid, attribution='curatorial'), ('task_id','category_id','relation'))

    def output(tid, oid, form, unit, axis, eid, why, limitations=''):
        put('task_outputs', dict(id=tid+'-output-review', task_id=tid, category_id=oid,
            prediction_form=form, scoring_unit=unit, position_axis=axis, structure_scope='none',
            status='supported', rationale=why, limitations=limitations, evidence_id=eid))
        category(tid, oid, eid, why)

    def task(tid, collection, name, dataset, target, typ, desc, eid, features, apps, caps,
             pops, oid='output-isolated', form='One sequence-level label or value',
             unit='Supplied sequence', axis='none', limits='', status='paper-audited'):
        put('tasks', dict(id=tid, name=name, dataset_name=dataset, target=target,
            description=desc, task_type=typ, label_basis='Cited experimental measurements or source annotations; details in target and protocol.',
            status=status, evidence_id=eid, limitations=limits,
            input_description='DNA sequence; exact context and preprocessing specified in linked protocols.',
            output_description=form))
        put('evaluation_tasks', dict(evaluation_id=collection, task_id=tid, variant_id=None,
            note='Dataset × prediction target; assay tracks and protocol settings are linked variants.', evidence_id=eid), ('evaluation_id','task_id'))
        for c in features + apps + caps:
            category(tid,c,eid,'Assignment follows the inspected target and scored output, not model pretraining taxa or input length alone.')
        for p in pops:
            mapped(tid,p,eid,'Sequence origin is explicitly identified in the cited source. ' + limits if p else limits)
        output(tid,oid,form,unit,axis,eid,desc,limits)
        if 'cds' in features:
            put('task_feature_scopes', dict(id=tid+'-cds-scope', task_id=tid, feature_id='cds',scope='restricted-target',
                rationale='The target is explicitly coding sequence or coding-region variants; not merely a mixed annotation background.', evidence_id=eid))
        return tid

    def variant(tid, vid, name, eid, length, targets=None, unit='outputs', notes='', revision=None):
        put('variants', dict(id=vid, task_id=tid, name=name, dataset_revision=revision,
            context='Linked release/assay/protocol variation; not a new dataset × target.', input_length=length,
            target_count=targets, target_unit=unit, notes=notes, evidence_id=eid))

    def protocol(tid,pid,eid,adapt,interface,fit,split,split_unit,metrics,variant_id=None,selection='Source-specific validation/checkpoint selection.',notes='',emb=True):
        put('protocols', dict(id=pid,task_id=tid,variant_id=variant_id,name=pid.replace('-',' '),adaptation=adapt,
            requires_embeddings=emb,model_interface=interface,fitted_component=fit,selection=selection,
            split_rule=split,split_unit=split_unit,source_evidence_id=eid,notes=notes))
        for metric,aggregation in metrics:
            put('protocol_metrics',dict(protocol_id=pid,metric_id=metric,aggregation=aggregation,is_primary=1,evidence_id=eid),('protocol_id','metric_id'))

    def count(tid,pid,value,split,eid,unit='released rows',vid=None,method='reported',qualifier='Reported by cited source; not an independent recount.'):
        put('counts', dict(id=f'{pid}-{vid or "all"}-{split.replace(' ',"-")}-{method}-count',task_id=tid,variant_id=vid,protocol_id=pid,
            split=split,value=value,unit=unit,qualifier=qualifier,method=method,evidence_id=eid))

    def suite(cid,eid,scope,notes):
        obj=next(e for e in d['evaluations'] if e['id']==cid)
        obj.update(status='paper-audited',scope_note=scope,notes=notes,evidence_id=eid)

    # A complete 2-D contact matrix is not an isolated supplied-edge prediction.
    put('categories',dict(id='output-contact-map',name='Contact map',dimension='output',accommodation=None,
        definition='A two-dimensional array of genomic contact values over locus pairs; distinct from a scalar label for a supplied pair.'))
    put('metrics',dict(id='scc',name='Stratum-adjusted correlation',definition='Contact-map correlation stratified by genomic separation; implementation and aggregation must be specified.',direction='higher'))

    # LRB: the paper benchmarks three tasks; the pinned release now defines nine.
    lrbe=code('lrb','README.md','card',
        'Pinned card defines nine task configurations. The workshop paper benchmarks only causal eQTL, CAGE and bulk expression. Later ClinVar/OMIM, chromatin and SCREEN tasks are released interfaces, not workshop-paper results.')
    lrbl=code('lrb','genomics-long-range-benchmark.py','loader',
        'CAGE returns position × track labels (896 × 50 at the default 114,688 bp), with context-dependent central label cropping; bulk expression returns 218 tissue values for one TSS. SNP tasks return reference/alternate sequences and a scalar label. Histone/DNase return 20 track labels at one central 200 bp bin; SCREEN returns one binary element label. Long context does not make the latter outputs dense.', '125-L878')
    lrbp=paper('lrb','workshop-protocol','Tasks; Evaluation Methodology; Table 1',
        'Workshop protocols: frozen backbone embeddings, two-hidden-layer MLP for SNPs/CAGE and one-hidden-layer MLP for bulk RNA. SNP ref/alt embeddings are pooled over 1,500 bp and concatenated with one-hot tissue labels. Bulk RNA pools 384 bp upstream and 256 bp downstream of the TSS. Five-fold model selection uses validation chromosomes for SNP/bulk and random 10% portions for CAGE. Test chromosomes: eQTL 9/10, bulk 8; CAGE uses original region splits with train/validation combined. log1p/scaling are protocol preprocessing, not a universal property of raw release labels.')
    lrb_specs=[
        ('eqtl','Causal eQTL classification','GTEx / Enformer fine-mapped variants','Causal versus matched noncausal SNP','binary classification',['regulatory'],['variant-interpretation'],['variant-effects','long-context'],'Test chr 9/10; remaining chromosomes training. Workshop validation selects five training chromosomes as folds.','chromosome','auroc',None,1),
        ('clinvar','Coding variant pathogenicity','GPN-MSA ClinVar / gnomAD','ClinVar pathogenic versus common coding variant','binary classification',['cds'],['variant-interpretation'],['variant-effects'],'Test chr 8; remaining chromosomes training. ClinVar submission eligibility differs from Evo 2 expert-reviewed ClinVar.','chromosome','auroc',None,1),
        ('omim','Regulatory pathogenicity','GPN-MSA OMIM / gnomAD','Curated pathogenic regulatory versus common variant','binary classification',['regulatory'],['variant-interpretation'],['variant-effects'],'Test-only all chromosomes. Full and smaller subset options.','variant','auroc',None,1),
        ('cage','CAGE profiles','Basenji / FANTOM5 fifty-track release','Binned CAGE transcription-initiation signals','profile regression',['promoter'],['regulatory-engineering'],['signal-profile-prediction','long-context'],'Release train 33,891/validation 2,195/test 1,922 retained from Basenji. The workshop combines train/validation and samples 10% for validation folds; this is not chromosome holdout.','genomic region','pearson','output-signal-profile',50),
        ('bulk','Bulk expression','ExPecto / GTEx / FANTOM5','Gene expression across 218 tissues','multivariate regression',['gene','promoter'],['target-discovery','regulatory-engineering'],['functional-prediction','long-context'],'Test chr 8; other chromosomes train; the workshop selects five training chromosomes as validation folds.','chromosome','spearman',None,218),
        ('histone','Window histone marks','DeepSEA / ENCODE / Roadmap','Twenty selected histone-mark peak labels','multilabel classification',['genome'],['regulatory-engineering'],['functional-prediction'],'Train chr 1–7/10–22; test chr 8/9. Track subsampling gives 20 outputs.','chromosome','auroc',None,20),
        ('accessibility','Window DNA accessibility','DeepSEA / ENCODE / Roadmap','Twenty selected DNase peak labels','multilabel classification',['regulatory'],['regulatory-engineering'],['functional-prediction'],'Train chr 1–7/10–22; test chr 8/9. Track subsampling gives 20 outputs.','chromosome','auroc',None,20),
        ('promoter','SCREEN promoter membership','ENCODE SCREEN','Promoter overlap of the central 200 bp bin','binary classification',['promoter'],['genome-annotation','regulatory-engineering'],['functional-prediction'],'Train chr 1–7/10–22; test chr 8/9; positive labels require at least 50% overlap; negatives are randomly subsampled from the genome.','chromosome','auroc',None,1),
        ('enhancer','SCREEN enhancer membership','ENCODE SCREEN','Enhancer overlap of the central 200 bp bin','binary classification',['enhancer'],['genome-annotation','regulatory-engineering'],['functional-prediction'],'Train chr 1–7/10–22; test chr 8/9; positive labels require at least 50% overlap; negatives are randomly subsampled from the genome.','chromosome','auroc',None,1)]
    lrb_files={'eqtl':'variant_effect_causal_eqtl/All_Tissues.csv','clinvar':'variant_effect_pathogenic/vep_pathogenic_coding.csv','omim':'variant_effect_pathogenic/vep_pathogenic_non_coding.csv','cage':'cage_prediction/sequences_coordinates.csv','bulk':'bulk_rna_expression/gene_coordinates.csv','histone':'chromatin_features/histones_and_dnase.csv','accessibility':'chromatin_features/histones_and_dnase.csv','promoter':'regulatory_elements/promoter_dataset.csv','enhancer':'regulatory_elements/enhancer_dataset.csv'}
    scans=INSPECTIONS['lrb_csv']
    scans={r['file']:r for r in scans}
    for slug,name,dataset,target,typ,features,apps,caps,split,splitunit,metric,oid,n in lrb_specs:
        tid='lrb-'+slug; ispaper=slug in ('eqtl','cage','bulk')
        limits=('The workshop model results concern this task.' if ispaper else 'Released extension absent from workshop experiments; model results and fitting recipes are not specified by this dataset interface.')
        desc=target+'. '+split+' The release permits configurable flanking context; samples extending outside chromosomes may be dropped.'
        task(tid,'lrb','LRB: '+name,dataset,target,typ,desc,lrbl,features,apps,caps,['human'],oid=oid or 'output-isolated',
            form='Position × 50-track CAGE profile at 128 bp resolution' if slug=='cage' else target,unit='Central 128 bp bin × track' if slug=='cage' else 'Supplied variant or sequence window',axis='contiguous' if slug=='cage' else 'none',limits=limits,status='artifact-audited')
        variant(tid,tid+'-release','Pinned configurable-context release',lrbe,'Configurable; CAGE length must be a multiple of 256 bp',n,notes=limits,revision=REVISIONS['lrb'][1])
        pid=tid+'-workshop' if ispaper else tid+'-release-interface'
        protocol(tid,pid,lrbp if ispaper else lrbl,'Frozen embeddings + trained MLP' if ispaper else 'Dataset interface; adaptation not prescribed',
            'Paired ref/alt mean embeddings + tissue metadata' if slug=='eqtl' else 'Position-aligned embeddings → MLP' if slug=='cage' else 'TSS-centered pooled embeddings → MLP' if slug=='bulk' else 'Sequence →target vector; exact fitting not prescribed by release',
            'Two-hidden-layer MLP' if slug in ('eqtl','cage') else 'One-hidden-layer MLP' if slug=='bulk' else 'Not prescribed',split,splitunit,
            [(metric,'Across genes/tissues as Table 1; exact aggregation specified in the paper') ] if ispaper else [],notes=limits,emb=ispaper)
        if slug in ('cage','bulk'):
            put('protocol_metrics',dict(protocol_id=pid,metric_id='r2',aggregation='Table1 multi-output coefficient of determination',is_primary=0,evidence_id=lrbp),('protocol_id','metric_id'))
        elif slug=='eqtl':
            put('protocol_metrics',dict(protocol_id=pid,metric_id='accuracy',aggregation='All eligible test variants',is_primary=0,evidence_id=lrbp),('protocol_id','metric_id'))
        st=scans[lrb_files[slug]]
        if not st.get('error') and 'split_counts' in st:
            se=evidence('final-'+tid+'-scan', next(s['id'] for s in d['sources'] if s['id']=='final-lrb-loader'),
                'Complete pinned '+lrb_files[slug]+' row/partition scan',f"Measured {st['rows']} rows; partitions {st['split_counts']}; coordinate/label columns {st['columns']}. Counts describe stored rows before context-boundary exclusion, not necessarily generated examples.",
                f'https://huggingface.co/datasets/{REVISIONS["lrb"][0]}/blob/{REVISIONS["lrb"][1]}/{lrb_files[slug]}','data')
            for part,val in st['split_counts'].items():count(tid,pid,val,part,se,method='measured',qualifier='Complete pinned coordinate/label CSV scan; generator counts can fall after sequence-boundary checks.')
        for field in ['target','output_description','input_description']:
            put('field_evidence',dict(entity_table='tasks',entity_id=tid,field=field,evidence_id=lrbl,note='Pinned loader target and configurable context.'),('entity_table','entity_id','field','evidence_id'))
    suite('lrb',lrbe,'Nine released dataset × target tasks; three were actually benchmarked in the workshop paper.',
          'CAGE is a positional profile; bulk RNA and 20-track chromatin vectors are sequence-level outputs. The released eQTL CSV has 89,060 train/8,862 test rows, differing from card counts 88,717/8,846. Stored rows and generated sequence examples are different units.')

    # DNALongBench: five biological task families, with species/assay linked variants.
    dle=paper('dnalongbench','tasks','Proposed Dataset; all five task sections; Table 2',
        'Five task families: enhancer–gene interaction, eQTL classification, contact-map regression, regulatory signal profiles and nucleotide-resolution initiation profiles. Contacts use 1,048,576 bp inputs and 2,048 bp bins; cropping 32 bins per side gives a 448 × 448 map, with 99,681 upper-triangle values at diagonal offset 2. Regulatory profiles have 5,313 human or 1,643 mouse tracks, each across 896 bins of 128 bp. Initiation profiles have 10 stranded assay channels at 1 bp. Regulatory-profile Pearson pools positions and tracks within each sample, then averages samples.')
    dll=code('dnalongbench','dnalongbench/utils.py','loaders',
        'Loaders return five contact cell variants (HFF, H1hESC, GM12878, IMR90, HCT116), human/mouse regulatory profiles, nine GTEx eQTL tissues and ten stranded initiation tracks. Initiation training is capped at 100,000 random windows; validation chr 10, test chr 8/9. The paper scores the central 50,000 bp of each 100,000 bp initiation input. The repository adds Evo 2 and GENERator experiment scripts after the original paper; script presence is not a reproduced model result.')
    dl_specs=[
        ('enhancer-gene','Enhancer–target gene links','CRISPRi-FlowFISH K562 enhancer–promoter pairs','True enhancer–gene interaction','binary classification',['enhancer','promoter'],['regulatory-engineering','target-discovery'],['functional-prediction','long-context'],['human'],'output-isolated','One probability per supplied enhancer–gene pair','Candidate enhancer–gene pair','none','450,000bp',1,'2,602 total pairs; exact split files are provided, but the Table 2 total is not a training count. The ABC expert uses DNase, H3K27ac and Hi-C in addition to sequence, unlike sequence-only gLM baselines.','Provided train/validation/test pair files; exact split construction is not reported in the main text.','pair','auroc'),
        ('eqtl','eQTL–gene links','GTEx / Enformer nine-tissue subset','Causal variant–gene association','binary classification',['regulatory'],['variant-interpretation','target-discovery'],['variant-effects','long-context'],['human'],'output-isolated','One probability per supplied variant–gene pair','Variant–gene–tissue pair','none','450,000bp',1,'31,282 reported pairs across nine tissues; genes require at least 2 positive, 2 negative and 5 total pairs. Candidate variant intervals are masked to reduce confounding by other variants.','Stratified random 8:1:1 pair partition; at least one positive and negative pair in training and validation per eligible gene. This is not chromosome or gene holdout.','pair','auroc'),
        ('contact','Chromatin contact maps','Akita / Micro-C / Hi-C','Binned pairwise contact frequency','matrix regression',['genome'],['regulatory-engineering'],['structure-prediction','long-context'],['human'],'output-contact-map','99,681 upper-triangle contact values for a 448 × 448 cropped map','Genomic bin pair within the contact map','contiguous','1,048,576bp',99681,'7,008 train/419 validation/413 test sequences. The main method mentions four additional cell lines, but the general loader exposes five original Akita outputs; all nine are not verified as released matrices.','Randomly assigned nonoverlapping virtual contigs, stated 8:1:1; not whole-chromosome holdout.','virtualcontig','pearson'),
        ('regulatory','Regulatory activity profiles','Enformer human / mouse target tracks','Quantitative epigenomic and transcriptional signals','profile regression',['regulatory'],['regulatory-engineering'],['signal-profile-prediction','long-context'],['human','mouse'],'output-signal-profile','896 bins × species-specific assay-track vector','128 bp bin × assay track','contiguous','196,608 bp; central 114,688 bp labeled',None,'38,171 human and 33,521 mouse reported windows. There are 5,313 human/1,643 mouse tracks; individual assay tracks are linked target variants.','Original Enformer train/validation/test region assignments retained by the loader: human 34,021/2,213/1,937; mouse 29,295/2,209/2,017.','genomicregion','pearson'),
        ('initiation','Transcription-initiation profiles','Puffin FANTOM/ENCODE CAGE,RAMPAGE,GRO-cap,PRO-cap','Stranded nucleotide-resolution transcription initiation','profile regression',['promoter'],['regulatory-engineering'],['signal-profile-prediction','long-context'],['human'],'output-signal-profile','Ten stranded quantitative tracks at each base','Nucleotide × assay strand','contiguous','100,000 bp; central 50,000 bp evaluated',10,'100,000 is a sampled training-window budget, not total dataset cardinality. Test chr 8/9 are scored with 50 kb steps; exclude regions within 1 kb of unknown bases and 25 kb of chromosome ends.','Train other chromosomes; validation chr 10; test chr 8/9 using sliding 100 kb windows with a 50 kb step.','chromosome','pearson')]
    for slug,name,dataset,target,typ,features,apps,caps,pops,oid,form,unit,axis,length,n,limits,split,sunit,metric in dl_specs:
        tid='dnalong-'+slug
        task(tid,'dnalongbench','DNALongBench: '+name,dataset,target,typ,limits,dle,features,apps,caps,pops,oid,form,unit,axis,limits)
        variant(tid,tid+'-release','Original paper / released loader',dll,length,n,notes=limits,revision=REVISIONS['dnalongbench'][1])
        protocol(tid,tid+'-finetune',dll,'Full backbone fine-tuning + task head','Position-aligned states for tensor targets; pooled/paired states for classification','Task head and foundation model parameters',split,sunit,[(metric,'Test sample correlation averaged across samples' if slug=='regulatory' else 'Task-specific whole-test aggregation')],notes=limits)
        if slug=='contact':
            put('protocol_metrics',dict(protocol_id=tid+'-finetune',metric_id='scc',aggregation='Stratified by genomic separation, aggregated across the test set',is_primary=1,evidence_id=dle),('protocol_id','metric_id'))
            for part,val in [('train',7008),('validation',419),('test',413)]:count(tid,tid+'-finetune',val,part,dle,unit='genomic windows')
        elif slug=='regulatory':
            for species,ntracks,cts in [('human',5313,[34021,2213,1937]),('mouse',1643,[29295,2209,2017])]:
                vid=tid+'-'+species;variant(tid,vid,species+' track release',dll,length,ntracks,notes='896 position bins per window.',revision=REVISIONS['dnalongbench'][1])
                for part,val in zip(['train','validation','test'],cts):count(tid,tid+'-finetune',val,part,dle,vid=vid,unit='genomic windows')
        elif slug in ('enhancer-gene','eqtl','initiation'):
            count(tid,tid+'-finetune',{'enhancer-gene':2602,'eqtl':31282,'initiation':100000}[slug],'sampled training budget' if slug=='initiation' else 'reported total',dle,unit='sampled windows' if slug=='initiation' else 'candidate pairs')
    suite('dnalongbench',dle,'Five decomposed target families, with species, cell type and assay variants.',
          'Contact matrices are distinct from isolated regulatory links and 1D profiles. For initiation, 100,000 is a training sampling budget. Profile assignments follow the target axis, not input length. The original paper and later repository interfaces are separate versions.')
    # Gene-MTEB: sixteen benchmark entries reduce to ten dataset × target tasks.
    gmp=paper('metagene1','gene-mteb','§5.3; Table 5',
        'Gene-MTEB has eight classification entries and eight clustering entries. Classification fits logistic regression to frozen sequence embeddings; clustering uses mini-batch K-means with V-measure. The datasets are distinct from pretraining wastewater and must not inherit its organism coverage.')
    gmclass=code('genemteb','mteb/tasks/Classification/metagene/HumanVirusClassification.py','virus-classification',
        'Four Human Virus Infecting configurations predict the released binary source column. Loader computes test fraction 1−8/M where M is the smallest class count, then uses random unstratified row splitting at seed 42. It does not split subjects, collection sites or viral species. Actual released source labels 0/1 have no accompanying label-to-species map.', '7-L342')
    gmhmp=code('genemteb','mteb/tasks/Classification/metagene/HumanMicrobiomeProjectDemonstrationClassification.py','hmp-classification',
        'Separate disease, host_sex and isolation_source targets. As in virus classification, random row splitting uses 1−8/min_class_count, without stratification or subject grouping. Source host labels are not the taxonomy of sequenced organisms.')
    gmmulti=code('genemteb','mteb/tasks/MultiLabelClassification/metagene/HumanMicrobiomeProjectDemonstrationMultiLabelClassification.py','hmp-multilabel',
        'The released multilabel transformation sorts and integer-encodes each categorical column, then adds the attribute NAME (disease,host_sex,isolation_source) when its code>0. It therefore creates three binary attribute indicators, not one-hot indicators for all original category values. Raw row split is 90% test with seed 42. This release behavior differs from an intuitive joint multicategorical metadata task.', '38-L97')
    gmeval=code('genemteb','mteb/abstasks/AbsTaskClassification.py','classification-evaluator',
        'Main score accuracy. Frozen-embedding logistic regression; evaluator additionally undersamples to eight examples per label over ten experiments by default. Loader pool cardinality is not final fitted-example cardinality.', '136-L216')
    gmveval=code('genemteb','mteb/abstasks/AbsTaskClusteringFast.py','clustering-evaluator',
        'Clustering uses selected frozen embeddings and hierarchical taxonomy-label lists, with bootstrapped mini-batch K-means/V-measure; per-task caps limit embedded rows. Cluster assignment is not a trained genome annotation head.', '27-L225')
    scans=INSPECTIONS['gene_data']
    dataset_revs=INSPECTIONS['gene_dataset_revisions']

    def gmdata(dataset,file):
        st=next(r for r in scans if r['file']=='registered-gene-'+dataset+'-'+file.replace('/','--'))
        rev=dataset_revs[dataset]
        url=f'https://huggingface.co/datasets/metagene-ai/{dataset}/blob/{rev}/{file}'
        sid='final-gene-data-'+dataset+'-'+file.replace('/','-').replace('.parquet','')
        put('sources',dict(id=sid,title='Gene-MTEB released '+dataset+'/'+file,kind='dataset-file',url=url,
            version=rev,retrieved=DATE,sha256=st['sha256'],local_path='research/artifacts/final-audit/'+st['file'],
            availability='available',notes='Complete Parquet read: row counts, sequence lengths and label columns scanned. No biological-label or donor identity certification.'))
        summary={k:v for k,v in st.items() if k not in ['sha256','file','virus_name','organism']}
        eid=evidence(sid+'-inspection',sid,'Complete released Parquet scan',json.dumps(summary,ensure_ascii=False),basis='data')
        return st,eid,rev

    for i in range(1,5):
        tid='gene-mteb-virus-'+str(i);st,ge,rev=gmdata('HumanVirusInfecting',f'hv/{i}/data.parquet')
        limits='Released binary source labels are 0/1; no source-to-virus taxonomy map is supplied. Human refers to sample host, not sequence origin. No donor/collection identifiers are available to verify grouped splits.'
        task(tid,'gene-mteb',f'Gene-MTEB: Human-Virus-{i} source classification','Human Virus Infecting / class-'+str(i),
             'Released source 0/1 label','binary classification','Predict the binary source label from one metagenomic read; the source label is not a dense or taxonomic annotation.',gmclass,
             ['genome'],['microbiome-analysis'],['embedding-analysis'],[None],limits=limits,status='artifact-audited')
        variant(tid,tid+'-release','Pinned twenty-thousand-read cohort',ge,'Measured '+str(st['length_min'])+'–'+str(st['length_max'])+'bp',2,'classes',revision=rev)
        protocol(tid,tid+'-probe',gmeval,'Frozen embeddings; logistic regression','Mean/encoder-specific pooled sequence embedding','Logistic regression',
            'Random row split at seed 42; test fraction 1−8/10000=0.9992 for balanced source classes. Sixteen-row candidate train pool; evaluator attempts 8 per label over 10 experiments. No independent subject/species holdout.',
            'read', [('accuracy','Mean over ten probe repetitions')],notes=limits)
        count(tid,tid+'-probe',st['rows'],'released',ge,method='measured',qualifier='Complete Parquet scan; source 0=10000 and source 1=10000. This is before loader/evaluator subsampling.')
        for field in ['target','label_basis']:
            put('field_evidence',dict(entity_table='tasks',entity_id=tid,field=field,evidence_id=ge,note='Released label values and columns.'),('entity_table','entity_id','field','evidence_id'))
    for slug,column in [('disease','disease'),('sex','host_sex'),('source','isolation_source'),('multi-label',None)]:
        tid='gene-mteb-hmp-'+slug;st,ge,rev=gmdata('HumanMicrobiomeProjectDemonstration',f'hmpd/{slug}/data.parquet')
        multi=column is None
        target='Three indicators of non-first encoded metadata category' if multi else column.replace('_',' ')+' category'
        desc='Current code creates a binary indicator for each attribute name when its alphabetically sorted category code exceeds zero.' if multi else 'Predict sample metadata from a supplied metagenomic sequence; host sex and disease are sample attributes, not labels of a human genomic locus.'
        limits='No source organism taxonomy, subject identifier or independent sample grouping is supplied in the released table. Random row partitions do not establish donor-level generalization.'
        if multi:limits+=' The release encodes three binary indicators rather than jointly reconstructing all nine disease, three sex and fourteen source categories.'
        task(tid,'gene-mteb','Gene-MTEB: HMP '+slug+' prediction','Human Microbiome Project Demonstration / '+slug,target,
            'multilabel classification' if multi else 'multiclass classification',desc,gmmulti if multi else gmhmp,
            ['genome'],['microbiome-analysis'],['embedding-analysis'],[None],limits=limits,status='artifact-audited')
        n=3 if multi else len(st[column]);variant(tid,tid+'-release','Pinned HMP read/metadata cohort',ge,f"Measured {st['length_min']}–{st['length_max']} bp",n,'binary labels' if multi else 'classes',revision=rev,notes=limits)
        split='Random 90% test row split at seed 42; remaining 10% is candidate probe-training pool.' if multi else 'Random row split at seed 42 with test fraction 1−8/minimum label count; not stratified. Downstream evaluator additionally caps eight examples per class.'
        protocol(tid,tid+'-probe',gmmulti if multi else gmeval,'Frozen embeddings; one-vs-rest/logistic regression','Sequence embedding → sample metadata prediction','Logistic-regression readout',split,'read',
                 [('accuracy','Exact-label-set accuracy for multilabel release' if multi else 'Mean across ten probe repetitions')],notes=limits)
        count(tid,tid+'-probe',st['rows'],'released',ge,method='measured',qualifier='Complete Parquet scan; released configs differ by one row, so the four cohorts are not silently equated.')

    for slug,dataset,pop in [('virus-reference','HumanVirusReference','viruses'),('hmp-reference','HumanMicrobiomeProjectReference','bacteria')]:
        tid='gene-mteb-'+slug;filename='hvr/data.parquet' if slug=='virus-reference' else 'hmpr/data.parquet'
        st,ge,rev=gmdata(dataset,filename)
        file='mteb/tasks/Clustering/metagene/'+('HumanVirusReferenceClustering.py' if slug=='virus-reference' else 'HumanMicrobiomeProjectReferenceClustering.py')
        gce=code('genemteb',file,slug+'-clustering',
            'P2P uses whole supplied genome strings and a random 90% test split. S2S makes Gaussian chunks around 200 bp with overlap around 50 bp before random 99.5% test splitting. Both remove the first taxonomy level. Align/small/tiny differ in embedded-document caps, not biological targets: 40/147/40/3 for virus and 27/2,198/27/3 for HMP. The comment comparing three documents to a 3-mer does not make the inputs 3 bp or change tokenization.')
        limits='The released taxonomy lists vary in depth. S2S sibling fragments can appear on both sides of the row split; it is not a held-out-genome test. P2P embeds whole genome strings subject to the model wrapper truncation, which README example caps at 512 tokens. Clustering has no independently fitted supervised task head.'
        task(tid,'gene-mteb','Gene-MTEB: '+('Human-virus' if slug=='virus-reference' else 'HMP bacterial')+' reference taxonomy clustering',dataset,
            'Hierarchical taxonomy agreement of embedding clusters','clustering','Group reference genomes or derived chunks by sequence embedding; score hierarchical taxonomy agreement.',gce,
            ['genome'],['microbiome-analysis','comparative-genomics'],['embedding-analysis','evolutionary-inference'],[pop],
            oid='output-isolated',form='Cluster assignment per genome or derived fragment',unit='Genome/fragment within taxonomy-level clustering trial',limits=limits,status='artifact-audited')
        caps=[40,147,40,3] if slug=='virus-reference' else [27,2198,27,3]
        for kind,cap in zip(['p2p','s2s-align','s2s-small','s2s-tiny'],caps):
            vid=tid+'-'+kind;iswhole=kind=='p2p'
            variant(tid,vid,kind,gce,f"Full genomes {st['length_min']}–{st['length_max']} bp; wrapper may truncate" if iswhole else 'Gaussian chunks around 200 bp with overlap around 50 bp',None,
                    notes=f'Embed at most {cap} test documents; cap counts sequences, not bp. Remove first taxonomy level; evaluate up to five remaining depths.',revision=rev)
            protocol(tid,vid+'-clustering',gmveval,'Frozen embeddings; unsupervised mini-batch K-means','One embedding per selected genome/fragment','Mini-batch K-means on assessed embeddings',
                'Random 90% test genome-row split seed 42.' if iswhole else 'Chunk complete references first, then random 99.5% test fragment split seed 42; sibling chunks not grouped.',
                'genome' if iswhole else 'fragment',[('v-measure','Mean over bootstrapped taxonomy-depth trials')],variant_id=vid,notes=limits)
        count(tid,tid+'-p2p-clustering',st['rows'],'released reference genomes',ge,method='measured',qualifier='Complete reference Parquet scan. Derived fragment counts depend on seeded Gaussian chunk generation; this is not the number of embedded test documents.')
    suite('gene-mteb',gmp,'Ten dataset × target records represent sixteen released benchmark entries: eight classification targets and two reference-clustering targets with four variants each.',
          'All ten source Parquet files inspected. Human sample metadata does not establish human sequence origin. HMP reference contains 29 bacterial genomes; virus reference 370 viral genomes. Released multilabel encoding and ungrouped fragment splits are documented explicitly.')
    # GenBench reuses established datasets; retain collection-specific protocols.
    gbr=code('genbench','README.md','resources',
        'The repository links Genomic Benchmarks, GUE, GENA-LM promoter data, SpliceAI-derived site data, DeepSTARR and Orca contact resources. Linked upstream releases are dataset resources; a model checkpoint or experiment command is not a released dataset.')
    gbp=paper('genbench','tasks','§3.1–3.4; Table 2; §4',
        'The paper defines 38 short-range dataset entries and five long-range task families. DeepSTARR has two scalar outputs per construct. Long tasks comprise dense splice-site labels, mammal species classification, promoter classification, contact-map regression and bulk expression. Table 2 gives source-scale lengths including 80 Mb/256 Mb for species/contact; actual reported experiments use much shorter sampled contexts, including 6000 bp for contact regression.')
    gbseq=code('genbench','src/dataloaders/datasets/genomic_bench_dataset.py','gb-loader',
        'Genomic Benchmarks loader reads upstream train/test folders and aliases requested validation to test. Input sequences are padded/truncated for the selected tokenizer. The code supplies no third independent split.', '122-L183')
    gbgue=code('genbench','experiment/GUE/GUE_hyena.sh','gue-entries',
        'Experiment loops list 10 yeast histone,5 human TF,6 promoter,1 splice,5 mouse TF and 1 SARS-CoV-2 targets. These are 28 GUE dataset targets, reused as existing catalogue tasks, not new targets invented for GenBench.')
    gbgue_loader=code('genbench','src/dataloaders/datasets/nucleotide_transformer_dataset.py','gue-loader',
        'FASTA classification loader aliases validation to test and parses the final character of each record identifier as the class label. These single sequence labels are not positional tracks.', '26-L86')
    gblong=code('genbench','src/dataloaders/datasets/genomic_long_range_benchmark.py','lrb-loader',
        'GenBench imports LRB CAGE and bulk RNA datasets. CAGE reads both validation and test but uses the test data for every non-training split; bulk similarly distinguishes train from all other modes. Dataset reuse does not inherit the LRB workshop frozen-probe protocol.')
    gbsplice=code('genbench','src/dataloaders/datasets/splicing_prediction_dataset.py','splice-loader',
        'Loads train_seq.npy/train_target.npy and test_seq.npy/test_target.npy; validation aliases test. A three-class positional target is retained over 5000 central bases. The source is linked as SpliceAI-derived data; the converted array cohort is not byte-identical to the original-paper cohort by demonstration.', '122-L206')
    gbspecies=code('genbench','src/dataloaders/datasets/species_dataset.py','species-loader',
        'The loader samples a species, chromosome and sequence window dynamically. Species-specific chromosome maps hold out chromosomes 1/3/12/13 for validation and 5/7/9/10/11 for test. Additional species names in this utility do not prove use in benchmark experiments.', '28-L79')
    gbspecies_cfg=code('genbench','configs/dataset/species.yaml','species-config',
        'Active config species list: human,mouse,hippo,pig,lemur. Dataset total_size 1000 is a sampling/epoch size; it is not a fixed disjoint set of 1000 genomic loci. Other mammals listed in the loader are not included by this config.')
    gbcontact=code('genbench','src/dataloaders/genomics.py','contact-loader',
        'Contact targets use 1000 bp bins from H1-ESC and HFF Micro-C matrices. The sampler declares validation chr 8 and test chr 9/10. Actual test_dataloader returns the validation dataset. Dataset size is dynamic; sequence length is configured separately from chromosome lengths in Table 2.', '2926-L3031')
    gbcontact_metric=code('genbench','src/tasks/metrics.py','contact-scorer',
        'Contact scorer normalizes observed contact counts by expected contact frequency at each genomic separation, applies a log transform, masks NaNs, computes Pearson correlation over flattened matrix entries per example and averages examples. It does not assess full gene/transcript structures.', '264-L294')
    gbresources={
        'gb-dummy_mouse_enhancers_ensembl':'Mouse enhancer classification',
        'gb-demo_coding_vs_intergenomic_seqs':'Transcript/intergenic classification',
        'gb-demo_human_or_worm':'Human/worm classification',
        'gb-human_enhancers_cohn':'Cohn enhancer classification',
        'gb-human_enhancers_ensembl':'Ensembl enhancer classification',
        'gb-human_ensembl_regulatory':'Regulatory class',
        'gb-human_nontata_promoters':'Non-TATA promoter classification',
        'gb-human_ocr_ensembl':'Open-chromatin classification',
    }
    for mark in ['h3','h3k4me1','h3k4me2','h3k4me3','h3k9ac','h3k14ac','h3k36me3','h3k79me3','h4','h4ac']:
        gbresources['geneb-leannmlindsey-gue-emp-'+mark]='GUE yeast '+mark
    for tag in ['300-all','300-notata','300-tata','core-all','core-notata','core-tata']:
        gbresources['geneb-leannmlindsey-gue-prom-'+tag]='GUE promoter '+tag
    for species in ['mouse','human-tf']:
        for i in range(5):gbresources[f'geneb-leannmlindsey-gue-{species}-{i}']='GUE '+species+' TF '+str(i)
    gbresources['geneb-leannmlindsey-gue-splice-reconstructed']='GUE isolated splice-site classification'
    gbresources['geneb-leannmlindsey-gue-virus-covid']='GUE SARS-CoV-2 variant classification'
    for tid,title in gbresources.items():
        isgb=tid.startswith('gb-');eid=gbseq if isgb else gbgue_loader
        put('evaluation_tasks',dict(evaluation_id='genbench',task_id=tid,variant_id=None,
            note='Reuses established dataset × target. GenBench fitting and validation are a linked protocol; existing source-release protocols remain distinct.',evidence_id=gbr),('evaluation_id','task_id'))
        vid='genbench-'+tid+'-release'
        variant(tid,vid,'GenBench '+title,eid,'Tokenizer/context-specific; source windows retained before truncation',notes='Upstream dataset reuse, not a new biological target.',revision=REVISIONS['genbench'][1])
        protocol(tid,vid+'-finetune',eid,'Full backbone fine-tuning with classification head','Sequence pooled representation → class logits','Backbone and classification head',
            'Released loader uses upstream train/test; validation aliases test. Early stopping on validation therefore does not establish a separate untouched test set.',
            'sequence',[('mcc','Task-specific sequence classification MCC')],variant_id=vid,notes='Fine-tuning experiments differ from the source collection’s probes or other fitting variants.')
    # DeepSTARR targets are already distinct dataset × target tasks.
    gbdeep=code('genbench','src/dataloaders/datasets/drosophila_enhancer_activity_dataset.py','deepstarr-loader',
        'DeepSTARR construct inputs produce two activity scalars, developmental and housekeeping; no genomic position axis is predicted. Each scalar reuses an existing dataset × target task.')
    for tid in ['deepstarr-dev','deepstarr-hk']:
        put('evaluation_tasks',dict(evaluation_id='genbench',task_id=tid,variant_id=None,note='DeepSTARR target reused; two scalar outputs are not a dense annotation track.',evidence_id=gbdeep),('evaluation_id','task_id'))
        protocol(tid,'genbench-'+tid+'-finetune',gbdeep,'Backbone fine-tuning and regression head','Pooled sequence representation → two activity values','Backbone and two-output regression head',
            'Provided DeepSTARR train/test files, with tokenizer-specific truncation/padding. Released GenBench loader aliases validation to test; no untouched third set is established.',
            'construct',[('pearson','Per developmental/housekeeping target; code averages two correlations')],notes='No assumption of dense enhancer localization.')
    for tid in ['lrb-cage','lrb-bulk']:
        put('evaluation_tasks',dict(evaluation_id='genbench',task_id=tid,variant_id=None,note='Reuses LRB data with GenBench fitting; CAGE is a repository extension beyond Table 2 task list.',evidence_id=gblong),('evaluation_id','task_id'))
        protocol(tid,'genbench-'+tid+'-finetune',gblong,'Backbone fine-tuning and regression head','Sequence states → CAGE profile or gene-level expression vector','Backbone and regression head',
            'Source LRB partitions; released GenBench loader uses source test for non-training splits, so validation/test independence is absent in that interface.',
            'genomic region',[('pearson','Target-specific correlation')],notes='Do not attribute LRB workshop five-fold frozen-probe methodology to these experiments.')
    tid='spliceai-sites-coding'
    put('evaluation_tasks',dict(evaluation_id='genbench',task_id=tid,variant_id=None,note='SpliceAI-derived dense coding-gene splice-site target; converted NPY release is a linked cohort/protocol variant, not proof of original-paper cohort identity.',evidence_id=gbsplice),('evaluation_id','task_id'))
    variant(tid,'genbench-splice-arrays','GenBench converted SpliceAI-derived arrays',gbsplice,'15,000 bp context; 5,000 bp central target',3,'site classes',
        notes='Paper reports roughly 146 ktraining/16 ktest windows. Original-model gene counts are not these window counts. Validation uses test arrays.')
    protocol(tid,'genbench-splice-finetune',gbsplice,'Backbone fine-tuning with positional head','Position-aligned states → donor/acceptor/neither probabilities','Backbone and dense classification head',
        'Provided train/test NPY arrays; validation aliases test. Exact chromosome/gene manifest of converted arrays is not released in the inspected repository.',
        'sequence window',[('auprc','Mean donor/acceptor PR-AUC across assessed positions')],variant_id='genbench-splice-arrays',notes='Dense site labeling, not all-isoform reconstruction.')
    task('genbench-species','genbench','GenBench: mammal species classification','Configured five-mammal reference genomes','Species of origin','multiclass classification',
        'Predict one species label for a dynamically sampled genomic window from the five configured mammals.',gbspecies_cfg,
        ['genome'],['comparative-genomics'],['sequence-modeling','long-context'],['human','mouse','pig','mammals'],
        limits='Active config includes hippo and lemur without scientific-name/assembly accessions. Loader also lists chimp, gorilla, orangutan, goat and sheep, but active benchmark config does not establish their evaluation. Epoch sampling counts are not independent example counts.')
    variant('genbench-species','genbench-species-contexts','Configured context-length sweep',gbspecies_cfg,'512/1000/2000/3000 bp; Hyena additionally 30000 bp',5,'classes',
        notes='Config total_size 1000; sampled coordinates change dynamically. Table 2’s 80 Mb is not the actual model context.')
    protocol('genbench-species','genbench-species-finetune',gbspecies,'Backbone fine-tuning and classification head','Sequence representation → five species logits','Backbone and classifier',
        'Per-species chromosome lists: validation 1/3/12/13; test 5/7/9/10/11; remaining listed chromosomes train. Known species occur in all partitions.',
        'chromosome',[('accuracy','Sequence species-classification accuracy')],notes='Not held-out-species recognition; larger contexts can still sample only a portion of a chromosome.')
    task('genbench-promoter-long','genbench','GenBench: long-context promoter classification','GENA-LM promoter-derived dataset','Promoter versus non-promoter','binary classification',
        'Classify an entire supplied window for promoter presence. Multiple context lengths test access to flanking sequence; output remains one label.',gbp,
        ['promoter'],['regulatory-engineering','genome-annotation'],['functional-prediction','long-context'],['human'],
        limits='Paper Table 2 reports about 41 k train/12 k test examples and 8 kb source context, while experiment scripts sweep 512–30,000 bp. The config train_len value 7,288 is a scheduler value. No exact converted-file cohort or coordinate manifest is committed; scheduler lengths are not measured dataset counts.')
    variant('genbench-promoter-long','genbench-promoter-lengths','GENA-LM-derived promoter context sweep',gbr,'512/1000/2000/3000/30000 bp configured; source context availability is separate',2,'classes',
        notes='Configured token limit can exceed source sequence; padding does not supply additional genomic context.')
    protocol('genbench-promoter-long','genbench-promoter-finetune',gbgue_loader,'Backbone fine-tuning and classification head','Sequence representation → binary class','Backbone and classifier',
        'Local converted FASTA files; validation aliases test. Original source chromosome split is not verified by the converted artifact interface.',
        'sequence',[('mcc','Window-level promoter classification')],notes='No dense promoter annotation target.')
    task('genbench-contact','genbench','GenBench: chromatin contact maps','Orca H1-ESC / HFF Micro-C','Normalized contact frequency between genomic bins','matrix regression',
        'Predict a two-dimensional contact matrix at 1000 bp bin resolution from a sampled genomic input, with H1-ESC and HFF as linked assay variants.',gbcontact,
        ['genome'],['regulatory-engineering'],['structure-prediction','long-context'],['human'],
        oid='output-contact-map',form='Two-dimensional contact-frequency matrix',unit='Genomic bin pair',axis='contiguous',
        limits='Paper Table 2’s 21/3 entries and 256 Mb describe source chromosome resources, not 21 training windows of 256 Mb. Actual scripts use 6000 bp contexts and dynamic 10000-sample training budgets. Test loader returns validation, so its declared chr 9/10 holdout is not an independently evaluated test path.')
    for cell in ['H1-ESC','HFF']:
        vid='genbench-contact-'+cell.lower();variant('genbench-contact',vid,cell,gbcontact,'6000 bp in reported experiment scripts',None,'1000 bp bin-pair values',
            notes='Target uses distance-normalized log contact counts; not a gene-structure matrix.')
        protocol('genbench-contact',vid+'-finetune',gbcontact_metric,'Backbone fine-tuning and matrix head','Sequence states → 2D contact matrix','Backbone and contact head',
            'Sampler declares validation chr 8, test chr 9/10. Released test_dataloader returns validation; no independent third-set result is established by this code.',
            'chromosome',[('pearson','Mean per-example Pearson over flattened finite matrix entries'),('mse','Contact-count regression error')],variant_id=vid,
            notes='The short configured matrix extent does not certify long-range modelling over the full source chromosomes.')
    suite('genbench',gbp,'All paper target families mapped:38 reused short-range targets plus five long-range families; CAGE is also implemented as a released extension.',
          'Existing GB/GUE/DeepSTARR/LRB/SpliceAI targets are reused with GenBench protocols; three distinct targets are newly indexed. Source chromosome sizes, sampled contexts, dynamic epoch lengths and stored example counts remain separate. Validation/test aliasing is recorded explicitly.')
    # LAMBDA: released bacterial CDS controls must remain CDS-specific tasks.
    laread=code('lambda','README.md','resources',
        'The benchmark separates segment classification, GC-preserving shuffled controls, bacterial CDS false-positive controls, phage false-negative controls and genome-wide detection. Current README paths and checkpoint claims describe a newer layout than fixed data record 19236553; the downloaded record is inspected independently.')
    laselect=code('lambda','dataset_creation/METHODS_DATA_SELECTION.md','selection',
        'GTDB r220 bacterial representatives: completeness ≥95%, contamination ≤5%, one genome per genus. INPHARED 2025-04-14 phages: representatives of approximately 95% ANI clusters. Train/development/test 80/10/10 assigned by bacterial genus and phage cluster before segment sampling. The method document reports approximate, pre-filter segment totals; these are not final released row counts.')
    lacontrol=code('lambda','dataset_creation/create_gc_control_csvs.sh','shuffled',
        'Shuffled phage/bacterial test segments retain original source labels 1/0, but source strings identify inphared_shuffled/gtdb_shuffled. This tests compositional dependence; MCC near zero is the intended diagnostic reference, not failed phage localization.')
    laprobe=code('lambda','inference/evo2_sae/README.md','evo-interfaces',
        'Evo 2 interfaces include a trained linear probe, trained three-layer neural network and a selected Goodfire SAE feature 19746 on layer 26 activations. Frozen Evo 2 with a supervised probe is not zero-shot with respect to benchmark labels. The SAE feature is a separate no-task-head readout with manually chosen feature/threshold settings.')
    lagrid=code('lambda','replication/grid_search_clustering.py','intervals',
        'Genome scanning collapses overlapping windows to nonoverlapping stride bins, averages probabilities and votes labels; normalization, bidirectional smoothing, thresholding, gap merging and minimum-size filtering produce intervals. Script grid search chooses the best macro MCC on supplied reference genomes, so that selection is not independent held-out testing. Its stride-bin metrics differ from the separate exact base-overlap scorer.')
    labase=code('lambda','dataset_creation/calculate_prophage_metrics.py','base-scorer',
        'Dedicated interval scorer converts inclusive start/end intervals to nucleotide-position sets, computes TP/TN/FP/FN for each genome and reports nucleotide accuracy, precision, recall, F1 and MCC. This does not require exact prophage boundary matching and is not full gene structure recovery.')
    for mid,label,definition in [
        ('false-positive-rate','False-positive rate','FP / (FP + TN) on an all-negative or mixed cohort.'),
        ('false-negative-rate','False-negative rate','FN / (FN + TP) on an all-positive or mixed cohort.')]:
        put('metrics',dict(id=mid,name=label,definition=definition,direction='lower'))
    lstats=INSPECTIONS['lambda_files']
    lfile=INSPECTIONS['lambda_archive']
    lsid='final-lambda-data-record'
    lurl='https://zenodo.org/records/19236553'
    put('sources',dict(id=lsid,title='LAMBDA fixed Zenodo dataset record 19236553',kind='dataset-file',url=lurl,
        version='10.5281/zenodo.19236553; '+lfile['checksum'],retrieved=DATE,sha256=lfile['sha256'],
        local_path='research/artifacts/final-audit/registered-lambda-data.tar.gz',availability='available',
        notes='Complete 1,006,852,286-byte archive downloaded. All 266 CSV files scanned; sequence lengths, row counts and labels measured. Archive paths differ from current README examples.'))
    lae=evidence('final-lambda-archive-scan',lsid,'All 266 CSV members of LAMBDA.tar.gz',
        'Main segment rows: 2 kb train 54,659/dev 7,100/test 6,827; 4 kb 54,658/7,100/6,827; 8 kb 51,624/6,689/6,453. Bacterial CDS controls 5,000/3,000/2,000 rows for 2/4/8 kb settings, with measured lengths 501–1,998, 1,002–3,993, 2,001–7,767 bp. Phage window controls 36,176/17,891/8,774 rows. PHROG-annotated 2 kb fragments: 64,237 rows, lengths 1–2,000 bp. Genome-wide folders have 82/81/81 CSV files but 80 distinct assembly/accession filename identifiers at each setting; duplicate variants must not become extra genomes.',basis='data')
    laspecs=[
        ('segments','Phage/bacterial segment classification','GTDB / INPHARED split genomes','Phage versus bacterial segment','binary classification',['genome'],['microbial-genomics','microbiome-analysis'],['embedding-analysis','sequence-modeling'],['bacteria','phages'],'output-isolated','One phage probability per supplied segment','Sequence fragment','none',
         'Genus-/cluster-assigned train/development/test partitions; three input-length settings. Final filtering produces slightly imbalanced classes despite intended 50:50 design.'),
        ('bacterial-cds','Bacterial CDS false-positive control','GTDB held-out bacterial coding sequences','False phage calls on bacterial CDS','binary diagnostic',['cds'],['microbial-genomics'],['sequence-modeling'],['bacteria'],'output-isolated','One phage probability on a supplied bacterial CDS','Bacterial coding sequence','none',
         'All released labels are 0. CDS controls are shorter than the nominal context limit; they must not be described as fixed-length whole-genome windows.'),
        ('phage-windows','Phage-window false-negative control','Held-out INPHARED whole-phage windows','Missed phage segments','binary diagnostic',['genome'],['microbial-genomics'],['sequence-modeling'],['phages'],'output-isolated','One phage probability per window','Phage window','none',
         'All labels are 1. Overlapping windows from the same phage are correlated; row count is not independent-phage count.'),
        ('phrog-cds','Phage CDS recognition by function','PHROG-annotated held-out phage CDS fragments','Phage sensitivity stratified by PHROG function','binary diagnostic',['cds'],['microbial-genomics'],['sequence-modeling'],['phages'],'output-isolated','Phage probability; PHROG category is a reporting stratum','Annotated CDS fragment','none',
         'The prediction target remains phage identity; PHROG function is not a functional class predicted by the model. Released fragments range 1–2,000 bp and include uncharacterized/no-PHROG categories.'),
        ('shuffled','GC-preserving shuffled-sequence control','Shuffled GTDB / INPHARED test segments','Residual source discrimination after shuffling','binary diagnostic',['genome'],['model-development'],['sequence-modeling','interpretability'],['bacteria','phages'],'output-diagnostic','Source-class probability on shuffled control','Shuffled sequence fragment','none',
         'Original source labels are retained after sequence shuffling; this diagnostic tests composition-based discrimination rather than preserved biological function.'),
        ('genome-wide','Genome-wide prophage localization','Eighty reference bacterial genomes with prophage intervals','Prophage coverage and interval localization','interval detection',['genome'],['genome-annotation','microbial-genomics'],['element-detection','dense-annotation'],['bacteria','phages'],'output-element-set','Prophage intervals from tiled sequence scores','Nucleotide overlap or collapsed stride bin, depending on protocol','interval-set',
         'Whole genomes are scanned; exact boundary/interval identity is not the headline metric. Raw and filtered results are separate protocol variants. Archive filenames include alternate multi-contig and prediction exports for the same 80 genome identifiers.')]
    for slug,name,dataset,target,typ,features,apps,caps,pops,oid,form,unit,axis,limits in laspecs:
        tid='lambda-'+slug
        task(tid,'lambda','LAMBDA: '+name,dataset,target,typ,limits,lae,features,apps,caps,pops,oid,form,unit,axis,limits,status='artifact-audited')
        sizes=['2k'] if slug=='phrog-cds' else ['2k','4k','8k']
        for size in sizes:
            vid=tid+'-'+size
            variant(tid,vid,size+' context setting',lae,'Up to '+{'2k':'2000','4k':'4000','8k':'8000'}[size]+'bp',
                notes='Actual CDS/terminal-window lengths vary; measured lengths are recorded by archive member.',revision='10.5281/zenodo.19236553')
            if slug=='segments':
                adapt='Frozen backbone with trained linear/nonlinear probe; selected models also fine-tuned'
                fit='Linear probe or three-layer neural network; full backbone for eligible fine-tuned baselines'
                split='Bacterial genus / phage 95% ANI cluster split 80/10/10 before sampling; held-out test fragments.'
                metrics=[('mcc','All eligible test fragments')]
            else:
                adapt='Reuse segment-trained predictor or selected SAE readout; no extra label fitting on control'
                fit='Inherited predictor; interval postprocessing may select additional parameters' if slug=='genome-wide' else 'Inherited predictor'
                split='Separate diagnostic or whole-genome evaluation cohort; no new train/validation partition.'
                metrics=[('mcc','Raw versus filtered; per-genome macro-average or pooled base overlap must be distinguished')] if slug in ['genome-wide','shuffled'] else [('false-positive-rate','All supplied bacterial CDS controls')] if slug=='bacterial-cds' else [('false-negative-rate','All supplied phage windows')] if slug=='phage-windows' else [('recall','Per PHROG functional-category stratum')]
            protocol(tid,vid+'-protocol',lagrid if slug=='genome-wide' else laprobe,adapt,
                'Tiled fragment probabilities → normalized/smoothed intervals' if slug=='genome-wide' else 'Sequence embedding or selected SAE feature → phage score',fit,split,
                'genome' if slug=='genome-wide' else 'genus / phage cluster',metrics,variant_id=vid,
                selection='Source-specific predictor validation; interval grid-search explicitly uses supplied reference genomes and must not be treated as a third untouched set.' if slug=='genome-wide' else 'Train on segment train split, select on development split; no control-label adaptation.',notes=limits)
            if slug=='genome-wide':
                protocol(tid,vid+'-raw',lagrid,'Inherited segment predictor; no interval filtering','Overlapping-window probabilities collapsed to stride-bin calls','Inherited predictor',
                    'Eighty independent whole-genome evaluation accession IDs; no new model fitting.','genome',
                    [('mcc','Per-genome macro-average on collapsed stride bins'),('recall','Per-genome sensitivity')],variant_id=vid,
                    selection='No postprocessing grid selection in raw condition.',notes='Stride-bin scores and exact nucleotide-overlap scores are different protocols.')
                protocol(tid,vid+'-base-overlap',labase,'Inherited interval predictions','Intervals converted to exact nucleotide-position sets','Inherited predictor and interval caller',
                    'Provided reference prophage intervals on supplied genomes.','genome',
                    [('mcc','Mean per-genome nucleotide confusion matrix score'),('precision','Nucleotide precision'),('recall','Nucleotide recall'),('f1','Nucleotide F1')],variant_id=vid,
                    selection='Depends on inherited interval-generation settings; scorer alone does not define independent tuning.',
                    notes='Inclusive start/end coordinate convention. Does not require exact interval boundary recovery.')
            if slug=='segments':selected=[r for r in lstats if f'/binary_segments_{size}/' in r['name'] and r['name'].endswith('.csv')]
            elif slug=='bacterial-cds':selected=[r for r in lstats if r['name'].endswith(f'/bacterial_cds_{size}.csv')]
            elif slug=='phage-windows':selected=[r for r in lstats if f'/error_and_bias_{size}/phage_segments_' in r['name']]
            elif slug=='phrog-cds':selected=[r for r in lstats if '/phrog_annotation_analysis/' in r['name']]
            elif slug=='shuffled':selected=[r for r in lstats if r['name'].endswith(f'/gc_control_{size}_test.csv')]
            else:selected=[]
            for row in selected:
                part=row['name'].rsplit('/',1)[-1].removesuffix('.csv')
                count(tid,vid+'-protocol',row['rows'],part,lae,vid=vid,method='measured',qualifier='Complete archive-member scan; rows are fragments, not independent organisms. '+str(row['label_counts']))
        if slug=='genome-wide':
            count(tid,tid+'-2k-protocol',80,'distinct filename assembly IDs',lae,unit='assembly/accession identifiers',method='measured',qualifier='Each context setting has 80 distinct filename accession identifiers; duplicate alternate exports are not extra genomes. This is not a sequence-based assembly deduplication.')
        # This is an independent evaluation, not an Evo2-original-paper task.
        put('model_evaluations',dict(id='final-evo2-'+tid,model_id='evo2',task_id=tid,protocol_id=None,paper_id='lambda',
            provenance='external-evaluation',evidence_id=laprobe,note='LAMBDA independent evaluation. Evo 2 frozen probes and selected SAE readout have different fitting/selection; no generic baseline protocol is inherited.'))
    suite('lambda',lae,'Six dataset × target records, including distinct bacterial/phage CDS controls and three context variants where released.',
        'Fixed data record 19236553 is fully scanned. Current repository README describes a newer archive layout; the fixed record does not contain those renamed metadata/checkpoint files. Genome-wide interval/coverage scores and isolated fragment scores remain separate; no exact boundary-recovery claim is inferred.')
    lp=next(p for p in d['papers'] if p['id']=='lambda')
    lp.update(doi='10.1093/nargab/lqag103',publication_date='2026-09-08',notes='Published journal version; fixed data and current code are separately pinned. Methods interfaces and complete deposited CSV contents audited; numerical performance not reproduced.')
    # The linked GenBench splice release is available as text shards, not NPY arrays.
    gbsurl='https://drive.google.com/file/d/1oB0DUrVfz-l0-wAe5_1kDVY5xZ1W4zMF/view'
    gbssha=INSPECTIONS['genbench_splice']['sha256']
    put('sources',dict(id='final-genbench-splice-data',title='GenBench linked splicing_prediction.zip',kind='dataset-file',url=gbsurl,
        version='Google Drive file ID; retrieved 2026-11-27; byte SHA-256 recorded',retrieved=DATE,sha256=gbssha,
        local_path='research/artifacts/final-audit/registered-genbench-splicing.zip',availability='available',
        notes='Complete 299,209,797-byte ZIP inspected; all 149 sequence/target shard pairs scanned. No genomic coordinates are included in the text shards.'))
    gbse=evidence('final-genbench-splice-scan','final-genbench-splice-data','Complete train/test text shard scan and bundled split scripts',
        '133 training shards contain 162,706 sequence/target pairs; 16 test shards contain 16,505 pairs. Every sequence is 15,000 bp; every target line is 5,000 space-separated labels from 0/1/2. Bundled splitter removes floor(10% of training rows)=16,270 validation rows at seed 42, leaving 146,436 training rows. Current repository loader still aliases validation to test. ZIP contains text shards and conversion/split scripts, not final NPY arrays.',basis='data')
    variant('spliceai-sites-coding','genbench-splice-arrays','GenBench converted SpliceAI-derived arrays',gbse,'15,000 bp sequence; 5,000 central labels',3,'site classes',
        notes='Released 162,706 train-source/16,505 test rows. Bundled 10% validation split leaves 146,436 train and 16,270 validation rows; these stages reconcile the paper’s rounded counts. Current loader aliases validation to test.')
    for part,val in [('released-train-source',162706),('released-test',16505)]:
        count('spliceai-sites-coding','genbench-splice-finetune',val,part,gbse,vid='genbench-splice-arrays',method='measured',unit='sequence/target pairs',
            qualifier='Complete text shard scan, before optional validation splitting or NPY conversion. Original SpliceAI gene counts are a different cohort unit.')

    # Resolve the deposited genome identifiers through primary NCBI records.
    # This is evaluated input coverage, not the taxonomy of the pretraining corpus.
    taxtable=INSPECTIONS['lambda_taxonomy']
    taxpath=ART/'registered-lambda-taxonomy.xml'
    taxurl='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id='+','.join(str(t['requested_id']) for t in taxtable)
    put('sources',dict(id='final-lambda-ncbi-taxonomy',title='NCBI taxonomy for LAMBDA deposited genome identifiers',kind='taxonomy-record',url=taxurl,
        version='NCBI taxonomy retrieved 2026-11-27; request IDs and byte hash recorded',retrieved=DATE,sha256=INSPECTIONS['lambda_taxonomy_xml_sha256'],
        local_path=str(taxpath.relative_to(ROOT)),availability='available',notes='76 assembly records plus 4 nucleotide-accession records resolve 80 deposited filename identifiers. Taxonomy resolves 73 distinct strain/species IDs to 49 species in 4 phyla.'))
    taxev=evidence('final-lambda-taxonomic-panel','final-lambda-ncbi-taxonomy','NCBI assembly/nucleotide reports + taxonomy LineageEx',
        'The 80 deposited genome identifiers resolve to 49 bacterial species in Pseudomonadota, Bacillota, Actinomycetota and Spirochaetota. Species ancestors are used instead of strain-level labels. Nucleotide-only IDs NC_000913/NC_002695 are E. coli, NC_000964 is B. subtilis and NC_003197 is S. enterica.',basis='data')
    # Add two observed phyla to the existing bacterial decomposition.
    phyla={t['phylum']['id']:t['phylum'] for t in taxtable if t['phylum']}
    for tx in phyla.values():
        phid=tx['name'].lower()
        if any(n['id']==phid for n in d['coverage_nodes']):continue
        template=copy.deepcopy(next(n for n in d['coverage_nodes'] if n['id']=='pseudomonadota'))
        label={'actinomycetota':'Actinobacteria','spirochaetota':'Spirochetes'}.get(phid,tx['name'])
        template.update(id=phid,parent_id='bacteria',population_id=phid,label=label,scientific=tx['name'],rank='phylum',
            note='Observed in the deposited LAMBDA genome-wide panel.',sources_json=json.dumps(['https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(tx['id'])]))
        put('coverage_nodes',template)
        put('populations',dict(id=phid,name=tx['name'],rank='phylum',parent_id='bacteria',ncbi_taxid=tx['id'],notes='NCBI lineage of evaluated LAMBDA genome sequences.'))
        for view in ['clade','species']:
            row=copy.deepcopy(next(r for r in d['coverage_rows'] if r['id']==('clade:pseudomonadota' if view=='clade' else 'species:bacillota')))
            md=json.loads(row['metadata_json']);md.update(id=phid,label=tx['name'],common=label,note='Observed LAMBDA genome-wide input sequences; no claim of complete phylum coverage.',
                node=phid,displayParent=phid,clade=phid,cladeLabel=tx['name'],path=[phid],members=[],lineageLabel=label,displayPath=['bacteria',phid],displayLineage='Bacteria → '+label,displayLabel=tx['name'])
            row.update(id=view+':'+phid,row_key=phid,node_id=phid,population_ids_json='[]',metadata_json=json.dumps(md));put('coverage_rows',row)
    tid='lambda-genome-wide'
    d['task_populations']=[r for r in d['task_populations'] if not(r['task_id']==tid and r['population_id']=='bacteria')]
    d['coverage_mappings']=[r for r in d['coverage_mappings'] if not(r['task_id']==tid and r['population_id']=='bacteria')]
    species={t['species']['id']:(t['species'],t['phylum']) for t in taxtable}
    for taxid,(sp,ph) in sorted(species.items()):
        phid=ph['name'].lower()
        existing=next((p for p in d['populations'] if p['ncbi_taxid']==taxid and p['rank']=='species'),None)
        pid=existing['id'] if existing else 'taxon-'+str(taxid)
        if existing is None:put('populations',dict(id=pid,name=sp['name'],rank='species',parent_id=phid,ncbi_taxid=taxid,notes='Species ancestor of a deposited LAMBDA evaluation assembly, resolved through NCBI.'))
        existingmap=next((m for m in d['coverage_mappings'] if m['population_id']==pid),None)
        if existingmap:
            mapped(tid,pid,taxev,'NCBI-resolved origin of deposited LAMBDA genome-wide input sequences; no transfer from pretraining taxa.')
            continue
        selected='species:pseudomonadota-other' if phid=='pseudomonadota' else 'species:'+phid
        allid='allSpecies:'+phid+'-sp-'+str(taxid)
        row=copy.deepcopy(next(r for r in d['coverage_rows'] if r['id']=='allSpecies:pseudomonadota-sp-562'))
        md=json.loads(row['metadata_json']);md.update(id=phid+'-sp-'+str(taxid),label=sp['name'],displayLabel=sp['name'],common='',note='NCBI-resolved LAMBDA genome-wide evaluation origin.',
            clade=phid,cladeLabel=ph['name'],node=phid,displayParent=phid,members=[sp['name']],path=[phid],lineageLabel=ph['name'],displayPath=['bacteria',phid],displayLineage='Bacteria → '+ph['name'])
        row.update(id=allid,row_key=phid+'-sp-'+str(taxid),node_id=phid,population_ids_json=json.dumps([pid]),metadata_json=json.dumps(md));put('coverage_rows',row)
        m=copy.deepcopy(next(m for m in d['coverage_mappings'] if m['population_id']=='ecoli'))
        m.update(id=tid+'-mapping-'+pid,task_id=tid,population_id=pid,basis='deposited accession resolved by NCBI',evidence_id=taxev,supporting_json='[]',
            clade_row='clade:'+phid,species_row=selected,all_species_row=allid,
            metadata_json=json.dumps(dict(row=selected.removeprefix('species:'),name=sp['name'],species=sp['name'],speciesId=taxid,clade=phid,
                allSpeciesRow=allid.removeprefix('allSpecies:'),url=taxurl,taxonomy='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+str(taxid),
                note='Genome identifier is present in the deposited evaluation archive; species ancestor resolved from primary NCBI taxonomy.')))
        put('coverage_mappings',m)
        put('task_populations',dict(task_id=tid,population_id=pid,variant_id=None,relation='sequence-origin',coverage='NCBI-resolved species of a deposited evaluation genome.',evidence_id=taxev),('task_id','population_id','relation'))

    # All released CAGE target tensors were scanned, not inferred from a loader schema.
    cagestats=INSPECTIONS['lrb_cage']
    cagemeta='https://huggingface.co/datasets/'+REVISIONS['lrb'][0]+'/tree/'+REVISIONS['lrb'][1]+'/cage_prediction/targets_subset'
    put('sources',dict(id='final-lrb-cage-tensors',title='LRB complete fifty-track CAGE target tensors',kind='dataset-file',url=cagemeta,
        version=REVISIONS['lrb'][1],retrieved=DATE,sha256=None,local_path='research/artifacts/final-audit/registered-lrb/cage_prediction/targets_subset',
        availability='available',notes='All 39 NPZ files downloaded and every 38,008 target array scanned; individual byte hashes retained in the source audit manifest.'))
    cagetensor_e=evidence('final-lrb-cage-tensor-scan','final-lrb-cage-tensors','All 39 NPZ files/38,008 array scan and coordinate-key reconciliation',
        'Every target array has shape (1, 896, 50) and dtype float32. All values are finite and nonnegative, observed range 0–456.5. There are 33,891 training/2,195 validation/1,922 test arrays, and all coordinate-row target keys match exactly with no missing/extra arrays. Stored labels are quantitative profiles, not binary promoter labels or pre-log1p targets.',basis='data')
    put('field_evidence',dict(entity_table='tasks',entity_id='lrb-cage',field='output_description',evidence_id=cagetensor_e,note='Full released target tensor scan; no extrapolation from schema.'),('entity_table','entity_id','field','evidence_id'))

    # Explicit resources distinguish actual datasets from code and results.
    def resource(rid,sid,title,kind,host,url,revision,eid,availability='public',notes=''):
        put('data_resources',dict(id=rid,source_id=sid,title=title,kind=kind,host=host,url=url,
            revision=revision,availability=availability,evidence_id=eid,notes=notes))
        return rid

    def link_resource(cid,tid,rid,eid,relation='evaluation-data',note='',vid=None):
        if cid:
            put('evaluation_resources',dict(evaluation_id=cid,resource_id=rid,relation=relation,evidence_id=eid,note=note),('evaluation_id','resource_id','relation'))
        if tid:
            put('task_resources',dict(task_id=tid,resource_id=rid,relation=relation,variant_id=vid,evidence_id=eid,note=note),('task_id','resource_id','relation'))

    # LRB CSVs contain targets and coordinates. Sequences are generated from references.
    for slug,file in lrb_files.items():
        tid='lrb-'+slug;sid='final-lrb-data-'+slug;path=ART/'registered-lrb'/file
        url=f'https://huggingface.co/datasets/{REVISIONS["lrb"][0]}/blob/{REVISIONS["lrb"][1]}/{file}'
        sha=next(r['sha256'] for r in INSPECTIONS['lrb_csv'] if r['file']==file)
        put('sources',dict(id=sid,title='LRB released '+file,kind='dataset-file',url=url,version=REVISIONS['lrb'][1],retrieved=DATE,
            sha256=sha,local_path=str(path.relative_to(ROOT)),availability='available',notes='Complete CSV scanned. Target vectors/coordinates are not necessarily generated sequence examples.'))
        eid='final-'+tid+'-scan'
        ev=next(e for e in d['evidence'] if e['id']==eid);ev['source_id']=sid
        rid=resource(sid,sid,'LRB '+slug+' target/coordinate table','dataset','huggingface',url,REVISIONS['lrb'][1],eid)
        link_resource('lrb',tid,rid,eid,note='Exact released target/coordinate artifact; loader fetches genome sequence separately.')
    rid=resource('final-lrb-cage-target-resource','final-lrb-cage-tensors','LRB complete CAGE target NPZ files','dataset','huggingface',cagemeta,REVISIONS['lrb'][1],cagetensor_e,
        notes='All 39 NPZ files and 38,008 arrays read. Coordinate/target keys reconcile exactly.')
    link_resource('lrb','lrb-cage',rid,cagetensor_e)
    link_resource('genbench','lrb-cage',rid,cagetensor_e,'upstream-data')
    rid=resource('final-lrb-loader-resource','final-lrb-loader','LRB dataset loader','evaluation-code','huggingface',
        f'https://huggingface.co/datasets/{REVISIONS["lrb"][0]}/blob/{REVISIONS["lrb"][1]}/genomics-long-range-benchmark.py',REVISIONS['lrb'][1],lrbl)
    link_resource('lrb',None,rid,lrbl,'evaluation-code')
    for tid in ['lrb-cage','lrb-bulk']:
        rid='final-lrb-data-'+tid.removeprefix('lrb-');link_resource('genbench',tid,rid,lrbl,'upstream-data',note='GenBench imports the LRB dataset; fitting protocol differs.')

    for ds in ['HumanVirusInfecting','HumanMicrobiomeProjectDemonstration','HumanVirusReference','HumanMicrobiomeProjectReference']:
        rev=dataset_revs[ds]
        for source in [s for s in d['sources'] if s['id'].startswith('final-gene-data-'+ds+'-')]:
            eid=source['id']+'-inspection';rid=resource(source['id'],source['id'],'Gene-MTEB '+source['title'].removeprefix('Gene-MTEB released '),
                'dataset','huggingface',source['url'],rev,eid)
            for tid in [t['id'] for t in d['tasks'] if t['id'].startswith('gene-mteb-')]:
                matching=(ds=='HumanVirusInfecting' and tid=='gene-mteb-virus-'+source['url'].split('/hv/')[1][0] if '/hv/' in source['url'] else False)
                if ds=='HumanMicrobiomeProjectDemonstration':matching=tid=='gene-mteb-hmp-'+source['url'].split('/hmpd/')[1].split('/')[0]
                if ds=='HumanVirusReference':matching=tid=='gene-mteb-virus-reference'
                if ds=='HumanMicrobiomeProjectReference':matching=tid=='gene-mteb-hmp-reference'
                if matching:link_resource('gene-mteb',tid,rid,eid)
    rid=resource('final-lambda-data-resource',lsid,'LAMBDA complete fixed data archive','dataset','zenodo',lurl,'10.5281/zenodo.19236553',lae,
        notes='Six target cohorts; exact archive member paths and counts retained. Current README paths differ.')
    for slug,*_ in laspecs:link_resource('lambda','lambda-'+slug,rid,lae)
    for group,cid,eid in [('dnalongbench','dnalongbench',dll),('genemteb','gene-mteb',gmveval),('lambda','lambda',lagrid),('genbench','genbench',gbr)]:
        repo,rev=REVISIONS[group];rid='final-'+group+'-code-resource'
        sid=next(e['source_id'] for e in d['evidence'] if e['id']==eid)
        resource(rid,sid,repo+' pinned evaluation code','evaluation-code','github',f'https://github.com/{repo}/tree/{rev}',rev,eid)
        link_resource(cid,None,rid,eid,'evaluation-code')
    for slug,did in [('enhancer-gene','CTEQXX'),('eqtl','YUP2G5'),('contact','AZM25S'),('regulatory','MNUEZR'),('initiation','VXQKWO')]:
        rid='final-dnalong-data-'+slug
        resource(rid,'final-dnalongbench-loaders','DNALongBench '+slug+' deposited data','dataset','other',
            'https://doi.org/10.7910/DVN/'+did,'DOI as linked by pinned repository',dll,availability='not-retrieved',
            notes='Primary repository links the exact data deposit; the Dataverse API returned HTTP 403 responses from this environment. Definition and loader reviewed; tensor files are not certified by a full artifact scan.')
        link_resource('dnalongbench','dnalong-'+slug,rid,dll)
    rid=resource('final-genbench-splice-data-resource','final-genbench-splice-data','GenBench splice-site sequence/target shards','dataset','other',gbsurl,
        'Retrieved 2026-11-27; SHA-256 in source record',gbse,notes='Complete archive scanned. Text shard inputs require conversion to the NPY filenames used by current loader.')
    link_resource('genbench','spliceai-sites-coding',rid,gbse,vid='genbench-splice-arrays')
    # Repository pointers to upstream resources must not be mislabelled released data files.
    rid=resource('final-genbench-upstream-index','final-genbench-resources','GenBench upstream data links','manifest','github',
        f'https://github.com/{REVISIONS["genbench"][0]}/blob/{REVISIONS["genbench"][1]}/README.md',REVISIONS['genbench'][1],gbr,
        notes='Manifest of upstream GB/GUE/DeepSTARR/GENA-LM/Orca resources; this README is not itself the data.')
    link_resource('genbench',None,rid,gbr,'upstream-data')

    def source_limit(table,id,field,reason,detail,eid,slug):
        put('source_limits',dict(id='final-registered-'+id+'-'+slug,entity_table=table,entity_id=id,
            field=field,reason=reason,detail=detail,evidence_id=eid))

    # Completion is source review, not an assertion that unavailable donor IDs or files exist.
    for cid,eid in [('lrb',lrbe),('dnalongbench',dle),('gene-mteb',gmp),('lambda',lae),('genbench',gbp)]:
        tids={r['task_id'] for r in d['evaluation_tasks'] if r['evaluation_id']==cid}
        all_eids={eid}
        for table in ['tasks','variants','protocols','task_outputs']:
            for row in d[table]:
                if row.get('task_id',row.get('id') if table=='tasks' else None) in tids:
                    e=row.get('evidence_id',row.get('source_evidence_id'))
                    if e:all_eids.add(e)
        put('source_reviews',dict(id='final-registered-review-'+cid,entity_table='evaluations',entity_id=cid,reviewed=DATE,
            scope='All indexed dataset × target definitions, linked protocol/release variants, available counts, scored output, fitting, sequence origin, feature assignments and direct data/code resources reviewed against the cited primary sources.',
            evidence_ids_json=json.dumps(sorted(all_eids)),limitations='Source restrictions, unreported fields and observed release discrepancies are recorded individually; numerical model performance and underlying experimental label truth were not independently reproduced.'))
    new_tids={t['id'] for t in d['tasks'] if t['id'].startswith(('lrb-','dnalong-','gene-mteb-','genbench-','lambda-'))}
    for tid in new_tids:
        t=next(t for t in d['tasks'] if t['id']==tid)
        eids={t['evidence_id']}
        eids.update(r['source_evidence_id'] for r in d['protocols'] if r['task_id']==tid)
        eids.update(r['evidence_id'] for r in d['counts'] if r['task_id']==tid)
        eids.update(r['evidence_id'] for r in d['field_evidence'] if r['entity_table']=='tasks' and r['entity_id']==tid)
        put('source_reviews',dict(id='final-registered-review-'+tid,entity_table='tasks',entity_id=tid,reviewed=DATE,
            scope='Dataset × target, release interface, label/output dimensions, fitting and split rule, counts, sequence origin, capability/feature classifications and direct resources reviewed.',
            evidence_ids_json=json.dumps(sorted(eids)),limitations=t['limitations']))
    for tid in ['gene-mteb-virus-'+str(i) for i in range(1,5)]+['gene-mteb-hmp-'+s for s in ['disease','sex','source','multi-label']]:
        source_limit('tasks',tid,'sequence-origin','not-reported',
            'Released read tables contain sequence and sample metadata/source labels, without read-level organism labels. Human sample host is not evidence of human genomic origin.',gmclass if 'virus' in tid else gmhmp,'read-taxonomy')
        source_limit('tasks',tid,'split-grouping','not-reported',
            'No donor/sample identifier is provided in the released table. The exact code uses random read rows; donor-level independence cannot be established from the artifact.',gmclass if 'virus' in tid else gmhmp,'donor-grouping')
    for tid in ['gene-mteb-virus-reference','gene-mteb-hmp-reference']:
        source_limit('tasks',tid,'taxonomy-depth-mask','conflicting',
            'Clustering scorer inserts integer -1 for missing taxonomy depths, then converts mixed string/integer labels to a NumPy array. The sentinel becomes string -1 and the subsequent comparison against integer -1 retains it. Missing depths can therefore form a scored class. This behavior was reproduced with the same NumPy conversion/comparison, without rerunning model inference.',gmveval,'missing-depth-mask')
    source_limit('tasks','gene-mteb-hmp-multi-label','label_basis','conflicting',
        'Raw data have nine disease, three sex and fourteen source categories. Released transformation produces three attribute-name indicators based on code>0, not all categorical labels.',gmmulti,'label-transformation')
    source_limit('tasks','genbench-species','scientific-species-accessions','not-reported',
        'Active config names hippo and lemur without scientific species or assembly accessions. Extra chromosome maps for chimp and other mammals are not evidence that the active experiment used them.',gbspecies_cfg,'species-accessions')
    source_limit('tasks','dnalong-enhancer-gene','split-construction','not-reported',
        'The main paper and loader specify train/validation/test pair files but do not state a definitive pair/gene/chromosome holdout rule for this cohort.',dle,'split-rule')
    for slug in ['enhancer-gene','eqtl','contact','regulatory','initiation']:
        source_limit('tasks','dnalong-'+slug,'artifact-tensor-inspection','not-retrieved',
            'The exact DOI-linked data deposit is identified. Its tensor payload was not retrieved because the Dataverse endpoint returned non-JSON responses; paper targets and pinned loaders were inspected. Reported counts are retained as reported.',dll,'tensor-files')
    source_limit('tasks','dnalong-contact','released-cell-panel','conflicting',
        'Paper methods mention nine cell lines; the pinned general loader exposes the original five Akita cell outputs. The four additional matrices are not established by that loader.',dll,'cell-panel')
    source_limit('evaluations','lambda','archive-layout','conflicting',
        'Fixed data record 19236553 contains binary_segments, error_and_bias and genome_wide_segments folders. Current README names train_val_test/fpr_test/fnr_test and additional checkpoints/metadata that are absent from this exact archive. Counts and access links are pinned by release.',lae,'release-layout')
    source_limit('evaluations','genbench','validation-test-independence','conflicting',
        'Several released loaders alias validation to test; contact test_dataloader returns validation. Declared source partitions and actual evaluated interface are retained separately. These paths do not establish an untouched third test set.',gbseq,'validation-aliasing')
    source_limit('tasks','lrb-eqtl','count','conflicting',
        'Complete pinned CSV scan gives 89,060 train/8,862 test rows, while the card reports 88,717/8,846. Configurable sequence-boundary exclusion can change generated counts, but no single context-specific reconciliation is reported.',lrbe,'card-count')

    return d
