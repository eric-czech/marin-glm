"""BOTANIC-1 v3: distinguish probe targets, assay profiles and diagnostics."""
import json
from common import Catalogue, ROOT
from taxonomy_layout import TaxonomyLayout

REV='1a1826804938e6320e20f037956b3818b9c40700'
SPACE='https://huggingface.co/spaces/living-models/botanic1-report'


def populate(d):
    c=Catalogue(d);layout=TaxonomyLayout(d)
    inventory=json.loads((ROOT/'data/botanic-artifact-inspections.json').read_text())
    def paper(slug,locator,page,statement):
        return c.evidence('botanic-final-'+slug,'botanic-paper',locator,statement,
            url=SPACE+'/resolve/'+REV+'/botanic1-report-v3.pdf#page='+str(page))
    suite=paper('suite','§4.3.2–4.3.6; Tables S4–S6',44,
        'Nine families/22 metrics enter Sbal; twelve cross-species splice/TIS/TTS metrics are reported separately. Seven families use frozen XGBoost probes; two use allele likelihood. '+
        'Training-suite scores guided data/architecture decisions; they were not independent untouched benchmarks. Test protocols and decoder/encoder pooling differ explicitly.')
    pooled=paper('pooling','Table S5; §4.3.6.1',99,
        'Center-token: conservation, TIS/TTS and final splice probes. Genomic region: mean central 100 bp of 512 bp, encoder RC average versus decoder two-strand center concatenation. '+
        'PRO-seq/accessibility: whole-window mean. Region labels are CDS, intron, 5′ UTR, 3′ UTR, ncRNA, repeat and intergenic. These are supplied single-class windows, not dense gene recovery.')
    sizes=paper('sizes','Table S6 and §4.3.4–4.3.5',100,
        'Probe caps are 20,000 train/5,000 test for most tasks; PRO-seq is complete. Final Arabidopsis splice probes train on 200,000 rows and use prevalence-matched 100,000-row tests. '+
        'Each cross-species site test samples 500 positives/4,500 negatives with prevalence correction. The report finds those cross-species estimates positively biased and excludes them from Sbal.')
    site_sid=c.source('botanic-final-site-data','PlantCaduceus single-nucleotide annotation release',
        'https://huggingface.co/datasets/kuleshov-group/cross-species-single-nucleotide-annotation/blob/ce38574d8a2aa8737167c6d5416a37a82d15eba4/README.md',
        'dataset','ce38574d8a2aa8737167c6d5416a37a82d15eba4')
    sites=c.evidence('botanic-final-site-data',site_sid,'Dataset overview; size tables; explicit TSV paths',
        'TIS/TTS/donor/acceptor train on Arabidopsis chr1–4, upstream validation chr5; rice/sorghum/maize are external species test files. '+
        'Conservation trains on sorghum chr1–9, upstream validation chr10 and external maize. BOTANIC-1 uses the upstream validation cohorts as its within-species evaluation cohorts.', 'documentation')
    site_res=c.resource('botanic-final-site-data',site_sid,'PlantCaduceus site/conservation TSVs','dataset','huggingface',
        'https://huggingface.co/datasets/kuleshov-group/cross-species-single-nucleotide-annotation/tree/ce38574d8a2aa8737167c6d5416a37a82d15eba4',
        sites,revision='ce38574d8a2aa8737167c6d5416a37a82d15eba4',notes='Card and named partition sizes inspected; full multi-gigabyte sequence TSVs were not scanned.')
    def space_resource(name,kind,relation,statement):
        sid=c.source('botanic-final-'+name,'BOTANIC-1 public report: '+name+'.json',SPACE+'/blob/'+REV+'/data/'+name+'.json',
            'dataset' if kind in ['dataset','manifest'] else 'documentation',REV)
        ev=c.evidence('botanic-final-'+name,sid,'Complete JSON release',statement,'data')
        rid=c.resource('botanic-final-'+name,sid,name+'.json',kind,'huggingface',SPACE+'/blob/'+REV+'/data/'+name+'.json',ev,revision=REV)
        c.collection_resource('botanic1-evals',rid,ev,relation)
        return ev,rid
    causal,causalres=space_resource('causal','manifest','identity-manifest',
        'All 545 study IDs include species, gene, causal coordinate/ref/alt and publication identifier; 14 species. Classes: 482 missense, 30 nonsense, 11 splice, 7 regulatory, 1 TFBS, 11 promoter SNP, 1 coding, 2 unspecified. '+
        'Per-model ranks are public. Complete all-candidate scored tables for every locus and the detailed manual curation audit are not supplied by this JSON.')
    abi,abires=space_resource('abi5-locus','dataset','evaluation-data',
        'Complete ABI5 locus contains 5,948 candidate coordinates/alleles, absolute scores, ranks/ties and causal flag; 38 gene annotations and explicit score provenance. This one locus is not the full 545-locus input release.')
    leader,leaderres=space_resource('leaderboard','results','results',
        'Nine families and per-model 22 metric result cells with uncertainty; these are aggregate results, not per-example labels or split manifests.')
    atacres_ev,atacres=space_resource('atac','results','results','Ten model/head result rows and the two held-out peak-cohort definitions, not the raw insertion tracks.')
    tfres_ev,tfres=space_resource('tf','results','results','Public validation/test/contrast TF-family summaries, not the 46-label per-window matrix.')
    ft_ev,ftres=space_resource('finetune','results','results','36 adaptation result cells with anonymized s0–s5 species labels plus baselines. These labels do not establish a reliable species-name correspondence.')
    c.collection_resource('botanic1-evals',site_res,sites)
    def reset_population(tid):
        d['task_populations']=[r for r in d['task_populations'] if r['task_id']!=tid]
        d['coverage_mappings']=[r for r in d['coverage_mappings'] if r['task_id']!=tid]
    def resolve(tid,names,ev,variant=None):
        reset_population(tid)
        for name in names:layout.link(tid,name,ev,variant=variant)
    def variant(tid,slug,name,ev,n=None,length=None,notes='',revision=None):
        vid=tid+'-'+slug
        c.put('variants',dict(id=vid,task_id=tid,name=name,evidence_id=ev,context=name,input_length=length,
            dataset_revision=revision,target_count=n,target_unit='targets' if n else None,notes=notes))
        return vid
    def new(tid,name,dataset,target,typ,ev,description,regions,caps,apps,names,output='diagnostic',axis='none',structure='none'):
        c.put('tasks',dict(id=tid,name=name,dataset_name=dataset,target=target,description=description,task_type=typ,
            label_basis='Source-defined annotation/experimental or constructed labels; see protocol',evidence_id=ev,
            status='paper-audited',limitations='',input_description='Source-defined DNA windows or positions',output_description=target))
        c.member(tid,'botanic1-evals',ev)
        for cat in regions+caps+apps:c.category(tid,cat,ev,description)
        resolve(tid,names,ev)
        c.output(tid,output,ev,target,'source-defined example',axis=axis,structure=structure)
        c.use(tid,'botanic1','botanic',ev)
    def finish(tid,evs,scope,lim=''):
        t=c.get('tasks',tid);t['limitations']=lim
        c.review('tasks',tid,scope,evs,lim)
        for p in [r for r in d['protocols'] if r['task_id']==tid]:
            c.review('protocols',p['id'],'Adaptation, pooling, split/selection, scoring unit and metric reviewed against the cited methods.',[p['source_evidence_id']])
    # Existing task identities remain stable; release and training protocol are linked variants.
    for tid in ['botanic1-regions','botanic1-conservation','botanic1-tis','botanic1-tts']:
        c.get('tasks',tid)['status']='paper-audited'
        c.task_resource(tid,leaderres,leader,'results')
        c.get('protocols',tid+'-protocol').update(source_evidence_id=pooled,
            notes='BOTANIC-1 test protocol: frozen XGBoost. Upstream validation is reused as a reported evaluation cohort; the base model is not species-excluded by this probe split.')
    resolve('botanic1-regions',['Arabidopsis thaliana','Oryza sativa','Zea mays','Solanum lycopersicum'],suite)
    for feature in ['cds','intron','utr5','utr3','ncrna','repeat','intergenic']:
        c.category('botanic1-regions',feature,pooled,'Actual seven-class window target, not a dense annotation output.','target')
    c.get('tasks','botanic1-regions').update(description='Seven-class annotation of supplied 512-bp single-class windows using central 100-bp pooled embeddings. Four plant species, chromosome holdouts.',
        label_basis='Ensembl/GPN-derived CDS, intron, 5′ UTR, 3′ UTR, ncRNA, repeat and intergenic annotations')
    c.protocol('botanic1-regions-protocol','botanic1-regions','BOTANIC-1 frozen region-window classification','frozen probe',
        'Mean central 100-bp embeddings from 512-bp windows, averaged across reverse complements for encoders; XGBoost seven-class classifier',
        'Four separate annotated plant genomes tiled into nonoverlapping, single-class 512-bp windows; chromosome-held-out train/test partitions within each genome. Probe cap: 20,000 training and 5,000 test rows per species. Exact held-out chromosome IDs are not reported.',
        'chromosome / supplied window',pooled,embeddings=True,fitted='XGBoost seven-class classifier',
        selection='Fixed depth 6, learning rate 0.3, at most 100 boosting rounds, early stopping after three rounds without improvement; exact early-stopping row membership is not enumerated.',
        metrics=[('balanced-accuracy','Per species; seven annotation classes')],
        notes='This is a study-constructed GPN-derived window cohort, not the Arabidopsis-trained PlantCaduceus site transfer panel.')
    c.count('botanic1-regions',20000,'probe training rows per species',sizes,split='probe train')
    c.count('botanic1-regions',5000,'probe test rows per species',sizes,split='probe test')
    c.limit('tasks','botanic1-regions','full-window-inventory','not-released','The report defines window tiling, class purity and chromosome holdouts but does not expose a complete per-window input/label and exact chromosome manifest in its public Space.',suite)
    finish('botanic1-regions',[suite,pooled,sizes,leader],'Full v3 methods/appendix and public aggregate result JSON.',
        'Exact per-window source counts/held-out chromosome IDs are not specified in the report; 20,000/5,000 are probe caps, not reconstructed original dataset sizes.')
    resolve('botanic1-conservation',['Sorghum bicolor','Zea mays'],suite)
    c.task_resource('botanic1-conservation',site_res,sites)
    c.protocol('botanic1-conservation-protocol','botanic1-conservation','BOTANIC-1 frozen conservation probe','frozen probe',
        'Center-token embeddings; XGBoost',
        'Sorghum chr1–9 train, chr10 within-species evaluation; maize external species evaluation. Each split uniformly capped at 20,000 train/5,000 test.',
        'chromosome / species',pooled,embeddings=True,fitted='XGBoost',metrics=[('auprc','per species')])
    for slug,n,notes in [('train',858086,'Sorghum chr1–9'),('sorghum',38060,'Sorghum chr10, upstream validation'),('maize',1923999,'External maize')]:
        vid=variant('botanic1-conservation',slug,notes,sizes)
        c.count('botanic1-conservation',n,'source positions',sizes,split=slug,variant=vid)
    finish('botanic1-conservation',[suite,pooled,sizes,sites,leader],'Full protocol/size table and upstream source card; public result cells checked.',
        'Counts are source-reported; complete source TSV payloads were not reprocessed. Conservation is an evolutionary proxy, not an experimental phenotype.')
    site_counts={
        'tis':[(198591,24711),(57825,7311),(1403089,2974),(3940933,3214),(11268672,3098)],
        'tts':[(245564,25112),(71826,7461),(3721003,2974),(10448744,3214),(29539071,3098)]}
    for target,counts in site_counts.items():
        tid='botanic1-'+target
        c.task_resource(tid,site_res,sites)
        c.protocol(tid+'-protocol',tid,'BOTANIC-1 frozen '+target.upper()+' candidate recognition','frozen probe',
            'Center-token embeddings with XGBoost; 512-bp source context',
            'Arabidopsis chr1–4 probe train; chr5 reported within-species test (upstream validation). Same probe evaluated on rice/sorghum/maize. '+
            'Train cap 20,000. Arabidopsis test cap 5,000 uniform; cross-species 500 positives + 4,500 negatives with prevalence correction.',
            'chromosome / species',sizes,metrics=[('auprc','Arabidopsis; prevalence-corrected cross-species AUPRC separately')],embeddings=True,fitted='XGBoost')
        resolve(tid,['Arabidopsis thaliana','Oryza sativa','Sorghum bicolor','Zea mays'],suite)
        for slug,(n,pos) in zip(['training','arabidopsis','rice','sorghum','maize'],counts):
            vid=variant(tid,slug,slug+' full source candidate pool',sizes,length='512 bp')
            c.count(tid,n,'source candidate positions',sizes,split=slug,variant=vid,qualifier=str(pos)+' positive positions; protocol subsamples this pool.')
        finish(tid,[suite,pooled,sizes,sites,leader],'Every reported species/probe-size cell and the original source partition definitions.',
            'Isolated supplied-position recognition, not sequence-wide localization. Cross-species stratified estimates are positively biased/noisy and excluded from Sbal (§4.3.5).')
    # Original PGB donor/acceptor and the PlantCaduceus transfer panel are distinct datasets.
    for kind,counts in [('donor',[3786512,10846742,34540437]),('acceptor',[4173737,12665374,40050298])]:
        tid='botanic1-cross-'+kind
        new(tid,'Cross-species splice '+kind+' recognition','PlantCaduceus single-nucleotide annotation',
            'Supplied candidate is a splice '+kind,'binary classification',sizes,
            'Arabidopsis-trained center-token XGBoost evaluated on supplied rice/sorghum/maize candidate positions.',
            ['splice'],['functional-prediction'],['genome-annotation','plant-breeding'],
            ['Oryza sativa','Sorghum bicolor','Zea mays'],output='isolated',axis='sampled')
        c.protocol(tid+'-protocol',tid,'BOTANIC-1 cross-species '+kind+' probe','frozen probe',
            'Center-token frozen embeddings; XGBoost; native 512-bp candidates',
            'Arabidopsis source training; external rice/sorghum/maize test files, each sampled to 500 positives/4,500 negatives.',
            'species',sizes,metrics=[('auprc','prevalence-corrected; excluded from Sbal')],embeddings=True,fitted='XGBoost')
        for name,n in zip(['rice','sorghum','maize'],counts):
            vid=variant(tid,name,name+' full candidate pool',sites,length='512 bp')
            c.count(tid,n,'source candidate positions',sites,split=name,variant=vid)
        c.task_resource(tid,site_res,sites)
        finish(tid,[suite,sizes,sites],'Explicit cross-species transfer methods and actual named source files.',
            'Report finds the 500-positive stratified estimator noisy and optimistic. No dense joint splice graph or isoform output is scored.')
    # Distinguish the small signed consequence proxy from population-genetic diagnostics.
    c.get('tasks','botanic1-llr').update(description='Ensembl consequence-derived deleterious/neutral labels; three allele-frequency-matched neutral SNPs per deleterious SNP in Arabidopsis, maize and tomato.',
        label_basis='VEP consequence classes; 1:3 matched proxy labels',limitations='Exact consequence whitelist and per-species retained variant IDs/counts are not supplied in Table S6 or the public result JSON.')
    resolve('botanic1-llr',['Arabidopsis thaliana','Zea mays','Solanum lycopersicum'],suite)
    c.protocol('botanic1-llr-protocol','botanic1-llr','BOTANIC-1 consequence-based SNP scoring','zero-shot',
        'Masked marginal LLR for encoders; full-window likelihood difference for decoders; W=min(4096, trained context)',
        'External proxy-labeled SNP cohorts; three allele-frequency-matched neutral variants per deleterious SNP; no fitted classifier.',
        'variant',pooled,metrics=[('auroc','per source species')])
    c.task_resource('botanic1-llr',leaderres,leader,'results')
    c.limit('tasks','botanic1-llr','retained-input-cohorts','not-released',c.get('tasks','botanic1-llr')['limitations'],sizes)
    finish('botanic1-llr',[suite,pooled,sizes,leader],'Full consequence-proxy definition and public result rows.',c.get('tasks','botanic1-llr')['limitations'])
    pop=paper('population','§4.9; Fig. 10; Figs S34/S37',60,
        'Population panels: Arabidopsis 6,491,238 biallelic SNPs (88.37% call rate), rice 6,494,573 (99%), chickpea 880,345 (95%). '+
        'Uses 6,001-bp likelihood/embedding scores, consequence/frequency enrichment and phyloP comparisons, not a trained pathogenicity classifier. Arabidopsis 1-Mb paired block jackknife controls linkage dependence.')
    tid='botanic1-population-constraint'
    new(tid,'Population-variant constraint diagnostics','1001 Genomes / RiceVarMap2 / CicerSeq panels',
        'Model-score association with allele frequency, consequence and phyloP','population-genetic diagnostic',pop,
        'Assess likelihood/embedding scores against population frequency and annotation/conservation proxies; distinguish call-rate filtering from causal validation.',
        ['genome'],['variant-effects','evolutionary-inference','embedding-analysis'],['plant-breeding','comparative-genomics'],
        ['Arabidopsis thaliana','Oryza sativa','Cicer arietinum'])
    c.protocol(tid+'-protocol',tid,'Population SNP score/enrichment diagnostics','zero-shot',
        '6,001-bp centered likelihood scores; optional reference/alternate embedding dot products at four relative depths',
        'All passing source SNPs, no supervised train/test partition. Model-specific scored coverage differs; 1-Mb paired blocks for uncertainty.',
        'variant / genomic block',pop,metrics=[('enrichment','frequency/consequence bins; source-defined phyloP summaries')],embeddings=None,
        notes='Earlier XL checkpoint is excluded from comparable model-size results. Final S/M/L and selected comparator coverage are explicit in figures.')
    for slug,n in [('arabidopsis',6491238),('rice',6494573),('chickpea',880345)]:
        vid=variant(tid,slug,slug+' population SNP panel',pop,length='6001 bp')
        c.count(tid,n,'passing biallelic SNPs',pop,split=slug,variant=vid)
    c.limit('tasks',tid,'complete-scored-panel','not-released','The methods identify source population panels and filters, but a complete original per-SNP multi-model score matrix is not in the inspected report Space.',pop)
    finish(tid,[pop],'Full population panel filtering/scoring/uncertainty methods and distinction from Sbal labels.',
        'Frequency/consequence/conservation are proxies. The Arabidopsis filter differs from AgroNT because the authors could not reproduce its stated count; this is documented rather than silently inherited.')
    causal_method=paper('causal-methods','§4.10–4.11; Tables S12–S14',61,
        '545 validated causal SNPs in 14 species are ranked by |LLR| among all documented SNPs of a 100-kb locus; positives have publication-backed functional evidence. '+
        'Background is positive-unlabeled, not proven neutral. Ties use expected recall within the tied block. The development subset uses signed LLR and 100 selected backgrounds, so its score is not interchangeable.')
    tid='botanic1-causal';resolve(tid,list(inventory['causal_species']),causal)
    c.get('tasks',tid).update(status='artifact-audited',limitations='Public positive study identities and per-model ranks are available, contrary to an abstract-only reading. Complete candidate tables for all loci and the full curation audit are not released; the ABI5 locus is a complete public example.')
    for feature in ['cds','splice','promoter','tfbs','regulatory']:
        c.category(tid,feature,causal,'The released study manifest contains this causal-variant class; species-specific classes are recorded in the mapping.','target')
    class_features={'missense':['cds'],'nonsense':['cds'],'coding':['cds'],'splice':['splice'],'promoter_SNP':['promoter'],'TFBS':['tfbs'],'regulatory':['regulatory'],None:['genome']}
    for m in [r for r in d['coverage_mappings'] if r['task_id']==tid]:
        name=c.get('populations',m['population_id'])['name'];classes={r['variant_class'] for r in inventory['causal_studies'] if r['species']==name}
        md=json.loads(m['metadata_json']);md['featureIds']=sorted({f for cl in classes for f in class_features[cl]});md['featureEvidence']=causal
        m['metadata_json']=json.dumps(md,ensure_ascii=False)
    c.protocol(tid+'-protocol',tid,'Full BOTANIC-1 causal-SNP ranking','zero-shot',
        'Absolute masked LLR or full-window decoder Δ log likelihood; W=min(4096, trained context)',
        '545 literature-supported loci; all documented biallelic SNPs within 100 kb. No fitted classifier or train/test split; related-locus overlap is not excluded by a released manifest.',
        'study/locus',causal_method,metrics=[('recall-auc','tie-aware study recall versus searched fraction')])
    c.protocol(tid+'-development-protocol',tid,'29-study signed-LLR development ranking','zero-shot',
        'Signed LLR; reference-genome allele as reference',
        '13 Arabidopsis, 11 rice, 4 wheat, 1 sorghum studies; each causal SNP plus 100 backgrounds: 50 nearest by allele frequency and 50 by position when frequency is available, otherwise 100 nearest by position.',
        'study/locus',causal_method,metrics=[('recall-auc','29-study development subset')],variant=tid+'-development',
        notes='This protocol guided model development and is not an untouched held-out test. Its signed ranking differs from full absolute ranking.')
    c.output(tid,'retrieval',causal_method,'Rank documented candidate SNPs to recover a known causal SNP','study / candidate shortlist',rationale='The final assessed output is a candidate ranking within a locus, summarized by tie-aware recall versus shortlist fraction; this is not a binary classifier scored over proven negatives.')
    c.count(tid,545,'study/locus identities',causal,method='measured')
    c.task_resource(tid,causalres,causal,'identity-manifest');c.task_resource(tid,abires,abi)
    c.limit('tasks',tid,'all-candidate-tables','not-released','545 positive study identities and aggregate ranks are public; complete background candidate tables and the detailed curation audit for all loci are not in the inspected public Space.',causal)
    finish(tid,[causal_method,causal,abi],'Every public study identity, variant-class/species breakdown, rank output and full/development scorer definition.',c.get('tasks',tid)['limitations'])
    atac=paper('atac-methods','§4.5.1–4.5.6',50,
        '2114-bp peak inputs predict central 1000-bp ATAC. Arabidopsis SRX8571616: train chr1/3/5, validation chr2, test chr4 (4646 peaks). '+
        'Maize SRX21046141: train chr2/3/5/6/7/8/10, validation chr4, test chr1/9 (23220 peaks). Test is peaks only; background is resampled in training. '+
        'Count totals and basewise profile shape are separate heads/metrics; one fine-tuning seed per model, not an independent replicate distribution.')
    for tid in ['botanic1-atac-counts','botanic1-atac-profile']:
        resolve(tid,['Arabidopsis thaliana','Zea mays'],atac)
        p=c.get('protocols',tid+'-protocol')
        p.update(source_evidence_id=atac,split_rule='Arabidopsis train chr1/3/5, validation chr2, test chr4; maize train chr2/3/5/6/7/8/10, validation chr4, test chr1/9. Peaks-only test; 10% resampled background in training.',
            name='BOTANIC-1 ATAC '+('count' if tid.endswith('counts') else 'profile')+' prediction',adaptation='full fine-tune',
            fitted_component='Full backbone plus single per-base head, or separate count/profile heads; trained and random initialization are distinct comparisons',
            model_interface='2114-bp DNA input; central 1000-bp per-base signal and log1p total count',
            selection='Best validation loss; up to 15 Arabidopsis or 20 maize epochs, stop after five epochs without improvement; one training seed per configuration.',
            notes='Full backbone/head adaptation, single/dual heads and random-initialization comparators are separate model conditions. Source libraries are SRX8571616 and SRX21046141.')
        for slug,n in [('arabidopsis',4646),('maize',23220)]:
            vid=variant(tid,slug,slug+' held-out ATAC peaks',atac,length='2114 bp input / 1000 bp target')
            c.count(tid,n,'test peaks',atac,split='test',variant=vid)
        c.task_resource(tid,atacres,atacres_ev,'results')
        c.limit('tasks',tid,'processed-insertion-targets','not-released','The methods identify source sequencing libraries and processing; the public Space supplies results rather than the exact peak-window insertion matrices.',atac)
        finish(tid,[atac,atacres_ev],'Full source library, processing, window geometry, partitions, adaptation and head-specific metric audit.',
            'Reported peak counts; original matrices were not reconstructed from raw sequencing. Count correlation and profile shape are distinct endpoints.')
    tf=paper('tf-methods','§4.6.1–4.6.4',55,
        '568 DAP/ampDAP libraries,529 TFs,46 families. Nonoverlapping 250-bp targets require at least 141 bp overlap with 201 bp peaks and 90% canonical DNA. '+
        'Train chr1–3 293591 windows, validation chr4 74327, test chr5 107851. Full fine-tune 2048-bp input and central 250-bp pooling,46 sigmoids. Three rates × three seeds; selection on mean validation macro AP among settings with all seeds finite.')
    tid='botanic1-tf-family';resolve(tid,['Arabidopsis thaliana'],tf)
    c.get('protocols',tid+'-protocol').update(source_evidence_id=tf,split_rule='Chromosome-disjoint train 1–3, validation 4, test 5.',selection='Three learning rates × three seeds; validation macro AP selects only fully finite seed triplets; Reduce rate by 0.3 after 2 evaluations without improvement; early stop after 9 without ≥0.0005 improvement, cap 18 epochs. Settings within 0.002 mean AP use lower seed standard deviation then fewer median optimizer steps.',notes='One 46-output vector per supplied window, not basewise binding occupancy. Main Botanic1-S arm uses context-extended 131k/800B checkpoint; M comparison uses released 8k/314.6B checkpoint. Evaluation averages reverse-complement logits.')
    c.get('protocols',tid+'-protocol').update(name='BOTANIC-1 TF-family window prediction',adaptation='full fine-tune',
        fitted_component='Full backbone and 46-output head; asymmetric multilabel loss',
        model_interface='2048-bp DNA input; mean central 250-bp hidden states through 46 sigmoid outputs')
    for split,n in [('train',293591),('validation',74327),('test',107851)]:c.count(tid,n,'windows',tf,split=split)
    c.task_resource(tid,tfres,tfres_ev,'results')
    c.limit('tasks',tid,'processed-label-matrix','not-released','The public Space supplies family result summaries, not the full 46-label window matrix or exact processed peak assignments.',tf)
    finish(tid,[tf,tfres_ev],'Full window labeling, source assay coverage, chromosome partition and seed/learning-rate selection.',
        'In-vitro DAP/ampDAP binding; not in-vivo occupancy. Family labels are window-level, not dense sequence labels.')
    long=paper('long-atac','§4.7; Table S11',57,
        'Maize PlantCAD accessibility: 92cell types,150–128,000 bp context, test chr9/10. Compares full/central-window LoRA and fixed/learned frozen positional pooling. '+
        'LoRA rank 8 alpha 8, one epoch; effective learning rate was multiplied by gradient accumulation factor, varying with context (Table S11). Context trends are therefore not a pure isolated context-length intervention.')
    c.get('protocols','botanic1-long-atac-protocol').update(source_evidence_id=long,split_rule='Maize chr9/10 test, remaining source chromosomes train; matched labels across context lengths.',notes='Four adaptation/pooling recipes; 92 per-cell-type AUPRCs; paired Wilcoxon with Holm correction. Effective learning-rate confound is documented in Table S11.')
    pid='botanic1-long-atac-protocol'
    c.get('protocols',pid).update(name='BOTANIC-1 full-window LoRA accessibility',adaptation='LoRA fine-tune',
        model_interface='Last hidden states mean-pooled over the entire input through a two-layer ESM-style 92-output classifier',
        fitted_component='Rank-8 LoRA (alpha 8, no dropout) and task head; backbone otherwise frozen',
        requires_embeddings=False,
        selection='One epoch, effective batch 128, nominal learning rate 1e-4, linear schedule with 50 warm-up steps. Actual optimizer rate is multiplied by the cell-specific gradient-accumulation factor.',
        notes='All backbones: 150–8,000 bp; context-extended BOTANIC-S also 16,000/32,000 bp. Source Table S11 gives actual learning rates. This branch does not test 128,000-bp LoRA inputs.')
    long_recipes=[
        ('central-lora','Central-window LoRA accessibility','LoRA fine-tune',False,
         'Same LoRA recipe as full-window adaptation; mean-pool the fixed central 101 bp through the classifier',
         'Rank-8 LoRA and task head',
         'One epoch; BOTANIC-S-128k inputs 150–32,000 bp. Same nominal/actual learning-rate discrepancy as full-window LoRA.'),
        ('frozen-fixed','Frozen fixed-pooling accessibility','frozen probe',True,
         'Frozen hidden states mean-pooled over peak-centered widths 1/11/25/51/101/151/201/251/301/351/401 bp; linear or ESM-style 92-output head',
         'Task head only',
         'Input context sweep 150–128,000 bp; one epoch, effective batch 128. Pool width and head architecture are separate reported conditions.'),
        ('frozen-learned','Frozen learned-pooling accessibility','frozen probe',True,
         'Frozen per-position states pooled by a learned softmax position vector through an ESM-style 92-output head',
         'Position-weight logits and task head',
         'One epoch; three seeds; uniform/random pool initialization, pooling-rate multipliers 1/10/100 and reverse-complement input controls are separate conditions. Input contexts extend to 128,000 bp.')]
    for slug,name,adaptation,embeddings,interface,fitted,selection in long_recipes:
        c.protocol('botanic1-long-atac-'+slug,'botanic1-long-atac',name,adaptation,interface,
            'Same maize source peaks/92 labels and held-out chr9/10; all remaining source chromosomes train. Symmetric context extension retains peak/label identity; boundary contexts are N-padded.',
            'source chromosome / peak',long,metrics=[('auprc','Per each of 92 cell types; paired context comparisons use Wilcoxon with Holm correction')],
            embeddings=embeddings,fitted=fitted,selection=selection,
            notes='Study-specific adaptation/context condition on the PlantCAD2 maize cell-type accessibility dataset; no new biological target is introduced.')
    for use in d['model_evaluations']:
        if use['task_id']=='botanic1-long-atac' and use['model_id']=='botanic1' and use['paper_id']=='botanic' and use.get('protocol_id') is None:use['protocol_id']=pid
    for slug,*_ in long_recipes:c.use('botanic1-long-atac','botanic1','botanic',long,protocol='botanic1-long-atac-'+slug,note='Distinct adaptation/pooling protocol on the same source peak dataset.')
    c.get('tasks','botanic1-long-atac')['description']='92-label maize accessibility classification across 150–128,000-bp contexts; evaluate per-cell-type AUPRC, not a base-resolution profile.'
    finish('botanic1-long-atac',[long],'All four adaptation recipes, held-out chromosomes, target count and effective learning-rate discrepancy.',
        'Changing context also changes effective learning rate in reported LoRA runs. Frozen pooling recipes are distinct and avoid treating all points as the same intervention.')
    pp=paper('pppl','§4.4.1',49,
        '1,251 sequences × 30 masked positions; repeat-weighted corpus pseudo-perplexity. Paired fixed positions, 10,000 sequence bootstrap draws. '+
        'Nested held-out 131,072-bp contexts score central 8,192 bp positions and symmetrically extend up to 1,048,576 bp; fixed-length training/held-out panels are separate.')
    tid='botanic1-pseudo-perplexity'
    c.get('tasks',tid).update(description='Repeat-weighted masked-base likelihood at paired positions across checkpoint/context conditions.',
        output_description='Exponentiated weighted mean negative log likelihood; not functional prediction')
    c.protocol(tid+'-protocol',tid,'Paired masked-position pseudo-perplexity','zero-shot',
        '30 single-position masks per sequence; repeat weight 0.1; corpus-level exponentiated weighted mean NLL',
        'Separate training and held-out source windows. Nested held-out 131,072-bp contexts with fixed central 8,192-bp scored positions; symmetric doublings to 1,048,576 bp.',
        'sequence / paired position',pp,metrics=[('bits','Weighted masked-base NLL is exponentiated as PPPL; not autoregressive bits-per-base')],
        notes='PPPL is not an autoregressive likelihood; 10,000 paired bootstrap sequence resamples, simultaneous checkpoint comparisons.')
    # Do not assign an autoregressive bits metric to a masked PPPL endpoint.
    c.put('metrics',dict(id='pseudo-perplexity',name='Pseudo-perplexity',definition='Exponentiated weighted mean single-position masked negative log likelihood; not autoregressive sequence perplexity.',direction='lower'))
    d['protocol_metrics']=[r for r in d['protocol_metrics'] if r['protocol_id']!=tid+'-protocol']
    c.put('protocol_metrics',dict(protocol_id=tid+'-protocol',metric_id='pseudo-perplexity',evidence_id=pp,aggregation='Repeat-weighted corpus PPPL; paired sequence bootstrap',is_primary=True),('protocol_id','metric_id'))
    c.count(tid,1251,'source sequences',pp);c.count(tid,30,'scored positions per sequence',pp)
    finish(tid,[pp],'Complete masked-position/repeat-weight/context/uncertainty protocol.',
        'Exact held-out window IDs are not supplied in the public report Space. This measures masked nucleotide modeling, not experimental genomic function.')
    nr=paper('niah','§4.4.2',50,
        'Uniform random DNA haystacks; 100-bp keys, 16-bp masked values, 10 depths 0–90%, lengths 1,024–131,072 bp, 8 repeats/cell. '+
        'One parallel MLM forward pass recovers all value bases; mean base accuracy rescaled from 0.25 chance, clipped below 0. Key/value length ablations are separate linked conditions.')
    tid='botanic1-niah';reset_population(tid);c.population(tid,'synthetic',nr,'Uniform random DNA; no source species or plant host.')
    c.get('tasks',tid).update(description='Recover a 16-bp masked value from a repeated 100-bp key in uniformly random DNA; vary context and insertion depth.',
        input_description='Synthetic uniformly random DNA with planted key/value and a repeated key followed by masked value',output_description='Parallel masked-span reconstruction; chance-corrected base accuracy')
    c.protocol(tid+'-protocol',tid,'BOTANIC-1 parallel masked-value retrieval','zero-shot reconstruction',
        'Single MLM forward pass; 16 masked positions decoded in parallel',
        'Synthetic grid: 8 context lengths × 10 depths × 8 repeats per model condition. Deterministic seed from key length, value length and repeat.',
        'synthetic key/value example',nr,metrics=[('accuracy','Mean fraction of 16 bases recovered; chance-corrected/clipped grid average')])
    c.output(tid,'sequence',nr,'16-base masked value reconstruction','synthetic key/value example',axis='contiguous',rationale='One parallel MLM pass emits the 16 nucleotide identities of a synthetic masked value; no biological dense annotation is scored.')
    for cat in ['generation','conditional-generation']:c.category(tid,cat,nr,'Conditional masked-span sequence reconstruction, not free-running autoregressive design.','measured')
    finish(tid,[nr],'Exact synthetic generator, decoding, depth/length grid and chance-normalized metric.',
        'Uniform random DNA is not plant genomic background. Parallel masked reconstruction differs from Carbon autoregressive retrieval and Evo 2 categorical-Jacobian diagnostics.')
    # Quantified ISM and SAE assessments have explicit targets; they are not future work.
    ism=paper('ism','§4.5.6',54,
        'HY5/TCP22/HHO3 motif perturbations: 50 selected peak windows per motif; 3,001 forward passes per locus (3 alternatives × 1,000 positions + reference). '+
        'Motif-versus-flank standardized attribution, cross-locus consistency and paired Wilcoxon assess model motif behavior, not experimentally measured mutation effects.')
    tid='botanic1-atac-motif-ism'
    new(tid,'ATAC motif perturbation diagnostic','BOTANIC-1 selected Arabidopsis accessible windows','Motif versus flank predicted ATAC response',
        'in-silico perturbation diagnostic',ism,'Inspect attribution at HY5/TCP22 versus HHO3 negative-control motifs in selected peak windows.',
        ['tfbs','regulatory'],['interpretability','variant-effects'],['model-development','regulatory-engineering'],['Arabidopsis thaliana'])
    c.protocol(tid+'-protocol',tid,'ATAC predictor saturation mutagenesis','post-hoc diagnostic',
        'Fine-tuned ATAC predictor; mutate each central 1-kb position to three alternatives',
        '50 selected peaks per motif; selection is not an independent experimental variant test.',
        'peak / motif',ism,metrics=[('effect-size-trend','motif-versus-flank attribution and paired contrasts')])
    c.count(tid,50,'selected peaks per motif',ism)
    finish(tid,[ism],'Full motif selection, saturation-mutation workload and diagnostic scoring.',
        'The response is produced by the trained predictor; there is no external per-mutation assay truth.')
    sae=paper('sae','§4.8.1–4.8.3; Tables S16–S17',58,
        'Eight BatchTopK SAEs, 8,192 features, k=64; reported dictionary is Botanic1-M layer 35/52. Trained on 80,000 windows of 8,191 bp. '+
        'Concept analysis uses 32,000 windows from Arabidopsis/rice/tomato/maize with chromosome-disjoint selection 16,510/validation 8,277/test 7,213. '+
        'Single-feature threshold MCCs are selected on validation and reported on test. PastDB splice tree uses 885 intermediate + 885 constitutive + 885 decoy donors; the report also says balanced accuracy/confusion/thresholds are all computed on these 2,655 sites, so an independent test denominator is not established.')
    for slug,name,regions,structure in [('region-concepts','Region concepts',['cds','intron','exon','utr','intergenic'],'none'),
            ('site-concepts','Boundary and splice concepts',['splice','translation-start','translation-stop','promoter','terminator'],'none'),
            ('codon-phase','Codon position',['cds'],'none')]:
        tid='botanic1-sae-'+slug
        new(tid,'SAE '+name.lower(),'BOTANIC-1 coordinate-anchored concept windows','Single-feature association with '+name.lower(),
            'representation diagnostic',sae,'Threshold per-token SAE activations against base/region annotation masks throughout coordinate-anchored windows; independent binary concept detectors, not jointly decoded genes.',
            regions,['interpretability','embedding-analysis'],['model-development','genome-annotation'],
            ['Arabidopsis thaliana','Oryza sativa','Solanum lycopersicum','Zea mays'],output='dense-labels',axis='contiguous',structure=structure)
        c.protocol(tid+'-protocol',tid,'SAE feature/threshold concept selection','frozen representation diagnostic',
            'Frozen residual stream→fitted unsupervised SAE→one feature threshold per concept',
            'Chromosome-disjoint selection 16,510/validation 8,277/test 7,213 coordinate windows. Feature/threshold chosen on validation, final MCC on test.',
            'chromosome / per-token annotated position',sae,metrics=[('mcc','per selected concept feature, species and direction')],embeddings=True,
            fitted='Unsupervised BatchTopK dictionary; concept-specific feature/threshold selection')
        finish(tid,[sae],'Full representation/concept split and model/threshold-selection method.',
            'Per-token binary concept associations across windows do not establish linked gene or isoform reconstruction. Full activation/label arrays and exact eligibility masks are not released; the eligible-base denominator is not independently measured.')
    tid='botanic1-sae-splice-usage'
    new(tid,'SAE alternative splice-donor usage','PastDB Arabidopsis donor sites',
        'Intermediate versus constitutive versus decoy donor; activation–PSU association','representation diagnostic',sae,
        'A two-feature tree separates supplied donor-usage classes; a broader 3,254 donor + 885 decoy panel tests activation association with usage.',
        ['splice'],['interpretability','embedding-analysis','functional-prediction'],['model-development','rna-engineering'],['Arabidopsis thaliana'],output='isolated',axis='sampled')
    c.protocol(tid+'-protocol',tid,'Two-feature donor-usage tree','frozen probe',
        'Two-level predefined tree on selected SAE features; thresholds maximize balanced accuracy',
        'Source states chromosome validation/test split, but also computes balanced accuracy/confusion/thresholds on all 2,655 selected sites. Additional donors are excluded from feature/threshold selection; Spearman uses 3,254 donors.',
        'donor site / chromosome',sae,metrics=[('balanced-accuracy','2,655 balanced sites; selection/evaluation denominator caveat'),('spearman','3,254 donors spanning usage bins')],embeddings=True,fitted='Two-feature tree')
    c.count(tid,2655,'balanced classification sites',sae);c.count(tid,3254,'donors for usage correlation',sae)
    c.limit('tasks',tid,'independent-test-denominator','conflicting','§4.8.3 states a chromosome validation/test split but also says thresholds and reported confusion/accuracy are all computed on the 2,655 sites. A separate held-out denominator/assignment is not released.',sae)
    finish(tid,[sae],'Exact PastDB donor filters, class balancing, feature selection and wider correlation cohort.',
        'Supplied donor-usage prediction; no splice-junction pairing, transcript chain, or whole-isoform recovery. Independent classification denominator is unresolved in the published methods.')
    d['task_resources']=[r for r in d['task_resources'] if not (r['task_id'] in ['pgb-chromatin','pgb-enhancer','pgb-splice-donor','pgb-splice-acceptor'] and r['resource_id']==ftres)]
    probe=paper('probe-methods','§4.3.6.1–4.3.6.2; Tables S4–S6',47,
        'Frozen XGBoost probes use final/default embeddings, with an explicit Evo 2 intermediate-layer exception. Encoders use center-token states for point tasks, whole-window mean for accessibility/PRO-seq; genomic region uses central 100 bp pooling plus RC average. Splice test uses 200,000 training rows and prevalence-matched 100,000 test positions; training signal uses 20,000 training and a 500 positive / 4,500 negative draw. XGBoost max_depth=6, up to 1,000 rounds, early stop 10; encoder PRO-seq/accessibility/splicing eta=0.05, lambda=0. Exact early-stop fitting/dev membership is not enumerated in these methods.')
    for tid,pid in [('pgb-chromatin','botanic-pgb-chromatin'),('pgb-enhancer','botanic-pgb-enhancer'),('pgb-splice-donor','botanic-pgb-splice-donor'),('pgb-splice-acceptor','botanic-pgb-splice-acceptor')]:
        splice='splice-' in tid
        c.protocol(pid,tid,'BOTANIC-1 final frozen '+('site' if splice else 'window')+' probe','frozen probe',
            'Encoder center-token embedding from 398 bp input' if splice else 'Encoder mean frozen embedding over 1,000 bp input',
            'Native PGB chromosome-defined source train/test. '+('200,000 training rows; 100,000 prevalence-matched test positions (donor 2,400 positive/97,600 negative; acceptor 3,500/96,500). This is not the cross-species PlantCaduceus site cohort.' if splice else 'Uniform 20,000 train/5,000 test cap per accessibility configuration; PRO-seq uses the complete 16,852 train / 812 test source rows.'),
            'source chromosome / supplied site or window',probe,
            metrics=[('auprc','Prevalence-corrected stratified AUPRC, per donor/acceptor task' if splice else 'Per-track AUPRC, macro across tracks per configuration; exact numerical integration is not specified by the report' if tid=='pgb-chromatin' else 'Cassava PRO-seq window AUPRC')],
            embeddings=True,fitted='XGBoost(max_depth=6, eta=0.05, lambda=0, up to 1,000 rounds)',selection='Fixed family hyperparameters; early stopping after 10 rounds without improvement; exact early-stopping data membership is not reported.',
            notes='Sbal is a model/data development signal. Final test protocol is distinguished from the training-frequency pooling/scoring protocol. Seven accessibility configurations represent six species, with two rice assemblies.')
        c.limit('protocols',pid,'probe-early-stop-membership','not-reported','The report specifies early stopping and fixed family hyperparameters, but does not release the exact probe fitting/evaluation row IDs or enumerate a distinct early-stopping development membership.',probe)
        c.review('protocols',pid,'Full model-specific frozen pooling, XGBoost configuration, source train/test definition, sampling and metric methods.',[probe,pooled,sizes])
        if splice:
            vid=tid+'-botanic-test-probe'
            c.put('variants',dict(id=vid,task_id=tid,name='BOTANIC-1 final Arabidopsis site probe',evidence_id=sizes,context='Same PGB binary site target; study-specific frozen probe subsampling.',input_length='398 bp',dataset_revision=None,target_count=1,target_unit='binary site label',notes='200,000 training rows and 100,000 prevalence-matched test rows. Frozen row indices are not released.'))
            c.get('protocols',pid)['variant_id']=vid
            for part,n in [('probe train',200000),('probe test',100000)]:c.count(tid,n,'probe sequence rows',sizes,split=part,variant=vid,protocol=pid,qualifier='Reported BOTANIC study-specific subsample; native PGB cohort counts remain separate.')
            development=pid+'-development'
            c.protocol(development,tid,'BOTANIC-1 training-signal splice probe','frozen probe',
                'Mean frozen states over 398 bp input, one encoder forward pass',
                '20,000 training rows; stratified test 500 positives + 4,500 negatives, corrected to source prevalence. Same source task, different development readout.',
                'supplied site',probe,metrics=[('auroc','Prevalence-corrected stratified AUROC used for training-signal Sbal')],embeddings=True,
                fitted='Family-fixed XGBoost probe',selection='Task aggregate steered data/architecture choices; no untouched-test claim.')
            c.review('protocols',development,'Explicit training-signal pooling, sampling and metric difference from final leaderboard probe.',[probe,pooled,sizes])
            c.limit('protocols',development,'training-signal-test-sampling','conflicting',
                'Table S6 defines the training-signal test draw as 500 positives and 4,500 negatives. Section 4.3.5.4 instead says training-signal AUROC scores the same 100,000-row prevalence-matched draw as final-test AUPRC. No released row-index manifest resolves these descriptions.',sizes)
            c.get('protocols',development)['notes']='The stated 500/4,500 training-signal draw follows Table S6; Section 4.3.5.4 describes the same prevalence-matched draw as final testing instead. The report gives conflicting sampling descriptions.'
        c.task_resource(tid,leaderres,leader,'results',note='Actual frozen-probe aggregate result cells; raw source data are linked separately under PGB.')
    adaptation=paper('pgb-adaptation','§2.3.2.1,4.3.8; Table 1; Supplementary Table S9',48,
        'Four PGB tasks use separate full-backbone, LoRA and IA3 adaptation. Hyperparameters are validation grid-searched per task/backbone/regime, then the selected run is retrained on full training data before fixed-test scoring. LoRA rank 8, alpha 8, no dropout modifies both-direction Mamba2 input/output projections; IA3 scales input-projection output and output-projection input; heads are always trained. Classification reports six-species mean AUROC with global versus per-species top-two validation selection; regression reports Pearson/R2 for tobacco/maize contexts. Terminator trains a joint two-context head; promoter and classification tuning are per subtask.')
    for tid in ['pgb-polya','pgb-lncrna','pgb-promoter-strength','pgb-terminator-strength']:
        regression='strength' in tid
        for regime,label in [('full','full fine-tune'),('lora','LoRA fine-tune'),('ia3','IA3 fine-tune')]:
            vid=tid+'-botanic-'+regime
            c.put('variants',dict(id=vid,task_id=tid,name='BOTANIC-1 '+label,evidence_id=adaptation,context='Same PGB dataset × target; model-specific adaptation and validation selection.',input_length='Native source windows/transcripts; source configuration-specific',dataset_revision=None,target_count=2 if tid=='pgb-terminator-strength' else 1,target_unit='reporter contexts' if tid=='pgb-terminator-strength' else 'target per subtask',notes='Terminator uses a joint two-context head. Other subtasks have source-specific fits. Raw labels and native partition variants remain upstream PGB records.'))
            pid=vid+'-protocol'
            c.protocol(pid,tid,'BOTANIC-1 PGB '+label,label,
                'DNA through adapted encoder and task-specific regression/classification head',
                'Source-defined PGB train/test. Separate validation grid per task × backbone × regime; selected hyperparameters are retrained from scratch on full training before test. No immutable validation-row manifest is released.',
                'source reporter / chromosome / species configuration',adaptation,
                metrics=[('pearson','Per assay context; arithmetic mean across tobacco/maize'),('r2','Per assay context, separate from squared Pearson')] if regression else [('auroc','Mean across six source species; global hyperparameters and per-species top-two-validation runoff are separate result variants')],
                embeddings=False,fitted='Backbone and task head' if regime=='full' else 'Rank-8 LoRA matrices plus trained task head' if regime=='lora' else 'IA3 scaling vectors plus trained task head',
                selection='Validation grid search; per-species classification results additionally compare the top two validation configurations after retraining. Reported cross-model instability/finite-species exclusions retain the Table 1 denominators.',
                notes='These four tasks are outside frozen-probe Sbal. Exact processed cohort and fitted-run memberships are not represented by anonymized s0–s5 labels in the public aggregate JSON.',variant=vid)
            for metric in d['protocol_metrics']:
                if metric['protocol_id']==pid and metric['metric_id']=='r2':metric['is_primary']=False
            c.review('protocols',pid,'Full adaptation mechanism, task/regime-specific validation search, final retraining and reported metric/denominator definitions reviewed.',[adaptation,ft_ev])
            c.limit('protocols',pid,'validation-row-manifest','not-released','The report describes separate validation selection and final full-training refit, but its public aggregate result JSON contains no fitting/validation/test row-index manifest for these fine-tuning runs.',adaptation)
            if regime=='full':
                old_uses=[u for u in d['model_evaluations'] if u['model_id']=='botanic1' and u['paper_id']=='botanic' and u['task_id']==tid and u.get('protocol_id') is None]
                for use in old_uses:use.update(protocol_id=pid,evidence_id=adaptation,note='Full fine-tuning; LoRA and IA3 are separate linked model/protocol uses, outside frozen-probe Sbal.')
                if not old_uses and not any(u['model_id']=='botanic1' and u['paper_id']=='botanic' and u['task_id']==tid and u.get('protocol_id')==pid for u in d['model_evaluations']):c.use(tid,'botanic1','botanic',adaptation,protocol=pid)
            else:c.use(tid,'botanic1','botanic',adaptation,protocol=pid,note='Distinct adaptation regime on the same upstream PGB dataset × target.')
        c.task_resource(tid,ftres,ft_ev,'results',note='Public adaptation result cells; s0–s5 are anonymized, not source-species identity evidence.')
    # The dictionary is applied per token through coordinate windows; these are
    # independently thresholded concept masks, not a linked gene decoder.
    for slug in ['region-concepts','site-concepts','codon-phase']:
        tid='botanic1-sae-'+slug
        c.category(tid,'dense-annotation',sae,'Per-token feature thresholds are evaluated against positional annotation masks across source windows. Independent concept masks do not recover a valid gene/transcript chain.','measured')
        out=c.get('task_outputs',tid+'-output-review')
        out.update(scoring_unit='Annotated token position, aggregated per concept/species/direction',rationale='Methods 4.8.1–4.8.2 compare per-token feature activations with region/site/codon masks throughout coordinate-anchored windows. No central candidate-site sampler is described; this is source-reported positional concept labeling, not linked gene reconstruction.',limitations='Exact released activation arrays, eligibility masks and retained base denominators are absent, so no independent all-position recount is claimed.')
        c.limit('tasks',tid,'eligible-base-denominator','not-reported','The report gives window/split counts and per-token concept scoring but no full per-concept eligible-base denominators or released scoring masks.',sae)
        for name,selection,valid,test,chroms in [
            ('Arabidopsis thaliana',3713,2478,1809,'selection: chr1/3; validation: chr2/4; test: chr5'),
            ('Oryza sativa',4258,1896,1846,'selection: chr1/4–8; validation: chr2/9/11; test: chr3/10/12'),
            ('Zea mays',4429,1932,1639,'selection: chr1/6–10; validation: chr2/5; test: chr3/4'),
            ('Solanum lycopersicum',4110,1971,1919,'selection: chr1/4–6/9/10; validation: chr2/7/11; test: chr3/8/12')]:
            vid=tid+'-'+name.lower().replace(' ','-')
            c.put('variants',dict(id=vid,task_id=tid,name=name+' SAE concept masks',evidence_id=sae,context=chroms,input_length='8191 bp',dataset_revision=None,target_count=None,target_unit='independent binary positional concepts',notes='Table S16 reports 8,000 windows per species. Exact annotation/activation/scoring-mask arrays are not released.'))
            for part,n in [('selection',selection),('validation',valid),('test',test)]:c.count(tid,n,'coordinate-anchored windows',sae,split=part,variant=vid)
    # Main family-binding arm and released base comparison have different budgets.
    for slug,name,budget,ctx in [('s128k','Botanic1-S context-extended',800000000000,'131,072 bp training context'),('m8k','Botanic1-M released base',314600000000,'8,192-token training context')]:
        variant('botanic1-tf-family',slug,name,tf,length='2048 bp evaluation input',notes=format(budget,',')+' training tokens; '+ctx+'. Source 4.6.2 explicitly identifies this checkpoint.')
    for tid in [r['task_id'] for r in d['evaluation_tasks'] if r['evaluation_id']=='botanic1-evals']:
        if tid in ['pgb-polya','pgb-lncrna','pgb-promoter-strength','pgb-terminator-strength']:
            c.task_resource(tid,ftres,ft_ev,'results',note='BOTANIC-1 adaptation results; anonymized species labels do not replace native PGB source taxonomy.')
        if tid.startswith('botanic1-'):
            for p in [r for r in d['protocols'] if r['task_id']==tid]:
                c.review('protocols',p['id'],'Reviewed full source-specific scoring/adaptation/split definition.',[p['source_evidence_id']])
    c.get('evaluations','botanic1-evals').update(status='audited',description='Frozen plant probes, consequence/causal/population variant assessments, accessibility/binding adaptation, masked-context retrieval and quantitative interpretability diagnostics.',
        notes='Full v3 report and all public report JSON files reviewed. Aggregate result tables, positive identity manifests, complete one-locus candidate data and unreleased complete input panels are distinguished.')
    c.review('evaluations','botanic1-evals','Full v3 report including appendix and all public report JSON artifacts; individual source limits retained.',
        [suite,pooled,sizes,sites,causal,abi,atac,tf,long,pp,nr,sae,ism])
    c.review('models','botanic1','Full model/training report and model-specific adaptation/decoding/representation protocols.',[suite,pp,nr,sae])
    c.review('papers','botanic','Complete v3 technical report, full appendix and official public result/identity resources.',[suite,causal,abi,sae])
    for tid,scope,ev,why in [
        ('botanic1-causal','mixed',causal,'Positive manifest includes coding, splice and regulatory causal variants; this is not a coding-only target.'),
        ('botanic1-regions','mixed',pooled,'CDS is one of seven supplied window classes.'),
        ('botanic1-sae-region-concepts','mixed',sae,'CDS is one of several independently assessed annotation concepts.'),
        ('botanic1-sae-codon-phase','restricted-target',sae,'Codon-position labels are defined within coding sequence.')]:
        c.put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope=scope,rationale=why,evidence_id=ev),('task_id','feature_id'))
    return d
