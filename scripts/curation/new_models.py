"""AIDO.DNA2 report and Genos-m v1: model properties and task-level protocols."""
import json
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[2]
GENOS='BGI-HangzhouAI/Genos-m'
DOC='Technical_Notes/Benchmarks_en.md'

def property(c,model,slug,category,name,value,ev,variant=None,status='source-reported',notes=None):
    c.add('model_properties',id=model+'-'+slug,model_id=model,category=category,name=name,
          variant=variant,value=value,status=status,evidence_id=ev,notes=notes)

def populate(c):
    # These are model-level corpus descriptions, not entries in the future data catalogue.
    c.add('categories',id='embedding-analysis',dimension='capability',name='Embedding analysis',
          definition='Analyze sequence representations using projection, clustering or similarity diagnostics.',
          accommodation='Requires access to hidden representations; diagnostic geometry need not measure prediction accuracy.')
    c.add('categories',id='interpretability',dimension='capability',name='Model interpretability',
          definition='Relate learned hidden features to genomic annotations.',
          accommodation='Requires token-level activations and a feature/readout analysis; threshold selection is part of the protocol.')
    c.add('categories',id='microbiome-analysis',dimension='application',name='Microbiome analysis',
          definition='Analyze microbial communities, sample structure and associations with host phenotype.',accommodation=None)
    c.add('metrics',id='cluster-agreement',name='Cluster assignment agreement',
          definition='Fraction of samples whose low-depth cluster assignment agrees with the full-depth reference; cluster-label correspondence must be specified separately.',direction='higher')
    aido(c);genos(c)

def aido(c):
    url='https://genbio.ai/aido-dna2-multi-species-genomic-pretraining-model/'
    c.source('aido2-report','AIDO.DNA2 technical report',url,'technical-web-report','2025-10-06; inspected 2026-11-25',
             'research/papers/aido2-web.txt',notes='Cached web-tool text representation. Direct HTTP retrieval from this VM returned 403; report text was accessible through web retrieval. No separate AIDO.DNA2 paper or public tokenizer artifact established in this audit.')
    c.paper('aido2','AIDO.DNA2: Scalable and Efficient Multi-Species Genomic Pretraining Model with Mixture-of-Experts',
            'aido2-report',2025,status='technical web report',scope='primary-model',date='2025-10-06',
            notes='Official GenBio AI report. A source registration does not imply public weights or evaluation data.')
    def ev(slug,section,text):return c.ev('aido2-'+slug,'aido2-report',section,text,'documentation',url+'#:~:text='+quote(section.split(';')[0]))
    arch=ev('architecture','Architecture; Long-context curriculum learning','Bidirectional masked-token encoder; 235M/470M/1B total sparse parameters, 8 routed + 1 shared expert, top-2 routed experts per token. Medium/large 64K, small 256K final training contexts.')
    c.add('models',id='aido2',name='AIDO.DNA2',scope='primary',paper_id='aido2',
          description='Bidirectional masked-token MoE encoder pretrained on OpenGenome2; embedding diagnostics, ClinVar embedding-distance scores and frozen-backbone coverage adapters.',evidence_id=arch,
          notes='Tokenization and active parameter counts are not specified in the inspected report. The 524-kb adapter experiment uses local attention and is distinct from the reported pretraining contexts.')
    corpus=ev('corpus','Pretraining Data','OpenGenome2 totals 8.84T nucleotides across eukaryotic/prokaryotic genomes, metagenomes and augmented functional elements; report follows official Evo2 preprocessing. Corpus size is not a model-specific consumed-token count.')
    property(c,'aido2','corpus','pretraining','Corpus','OpenGenome2: 8.84T nucleotides; eukaryotic and prokaryotic genomes, metagenomes, mRNA, ncRNA, promoters, organelle DNA and splice sites. Official Evo2 preprocessing reported.',corpus,notes='Source coverage and sampling are reported, not independently reconstructed. This does not establish benchmark decontamination.')
    property(c,'aido2','architecture','architecture','Architecture','Encoder-only bidirectional Transformer; pre-LayerNorm, RoPE, RMSNorm with zero-centered gamma, SwiGLU. MoE replaces FFNs: 8 routed experts + 1 shared expert, sigmoid routing with learned bias, top-2 routed experts, normalized gate combination.',arch)
    property(c,'aido2','capacity','architecture','Parameter variants','Small 235M; medium 470M; large 1B total sparse parameters. Active parameters per token, layer counts and hidden widths are unresolved.',arch)
    property(c,'aido2','objective','training','Objective','Masked-token recovery; no assay labels in pretraining. Load balancing, router z-loss and initial token dropping reported.',arch)
    property(c,'aido2','tokenizer','tokenization','Tokenizer','Not specified in the inspected report; no public model-specific tokenizer/config established.',arch,status='unresolved',notes='Do not substitute AIDO.DNA predecessor tokenization or infer one nucleotide per token from the objective.')
    property(c,'aido2','curriculum','context','Pretraining context','Progressive 2K → 8K → 64K → 256K schedule; final medium/large 64K, small 256K.',arch)
    property(c,'aido2','tokens','pretraining','Consumed tokens','Embedding diagnostic uses large-8K-4T, explicitly described as 4T consumed tokens. Other model-specific totals remain unresolved.',ev('embeddings','AIDO.DNA2 Captures Global Structure of rRNAs and Human Genomic Elements','Large-8K-4T checkpoint; 119,745 SSU rRNAs, 95,279 LSU rRNAs and 21,680 human genomic elements projected with UMAP min_dist=0.5, n_jobs=25. No held-out classification metric reported.'))
    em='aido2-embeddings'
    cv=ev('clinvar','Zero-shot ClinVar Variant Effect Prediction','ClinVar 20240301 selected review/significance groups; 40,899 pathogenic and 151,159 benign SNVs; 8,538 pathogenic and 5,057 benign non-SNVs. Reference/alternate embeddings from ±4,096-nt flanks; local 128-nt L2 distance; AUPRC. Balanced SNV figure arm does not specify sampling manifest.')
    cov=ev('coverage','Supervised Coverage Prediction','Original Borzoi folds retained: train 0–2, 5–7, validation 4, test 3. Frozen AIDO.DNA2 with Flashzoi adapter on 524-kb sequences; sliding attention ±8,192 tokens, linear projection to 512 channels. Five assay families; four-run medium/large ensembles. Report states correlations without identifying the correlation statistic in text.')
    c.suite('aido2-evals','AIDO.DNA2 evaluations','Embedding diagnostics, report-specific ClinVar cohorts and five Borzoi-derived coverage targets.',arch,'aido2','aido2-report',notes='All entries are documentation-audited; task artifacts and exact track/cohort manifests remain unverified. No new benchmark name is assigned to reused datasets.')
    for slug,name,n,pops,regions in [('ssu','SSU rRNA taxonomy',119745,('euk','bacteria','archaea'),('rrna',)),('lsu','LSU rRNA taxonomy',95279,('euk','bacteria','archaea'),('rrna',)),('human-elements','Human genomic-element classes',21680,('human',),('cds','utr5','utr3','ncrna','lncrna','rrna'))]:
        t='aido2-'+slug
        c.task(t,'aido2-evals',name,'AIDO.DNA2 '+name,'Embedding structure by annotated class','UMAP projection colored by taxonomy or element type; a representation diagnostic with no reported held-out classifier. Human classes additionally include miRNA, snRNA and snoRNA.','embedding diagnostic','Sequence taxonomy or genomic-element annotation',em,
               applications=('comparative-genomics','model-development') if slug!='human-elements' else ('genome-annotation','model-development'),capabilities=('embedding-analysis',),regions=regions,populations=pops,
               input='rRNA or genomic-element sequences; exact length distribution unresolved',output='Two-dimensional UMAP and annotation colors',limitations='Sequence source, filtering, duplicates, class balance and train/test exclusions are not established; visual separation is not classification accuracy.')
        p=c.protocol(t,t+'-umap','Large-8K-4T UMAP',em,'frozen embedding analysis','Sequence hidden representations → UMAP','No supervised train/test split described; cohorts are projected for visualization.','sequence',embeddings=True,fitted='UMAP; min_dist=0.5; n_jobs=25',notes='Embedding pooling/layer details not specified in report.')
        c.count(t,n,'sequences',em);c.use('aido2',t,em,'aido2','original-release',p)
    for kind,pos,neg in [('snv',40899,151159),('non-snv',8538,5057)]:
        t='aido2-clinvar-'+kind
        c.task(t,'aido2-evals','ClinVar '+kind.upper()+' pathogenicity','ClinVar 20240301 / AIDO.DNA2 cohort','Pathogenic versus benign variant','Discriminate selected ClinVar labels using reference/alternate embedding distance. SNVs and non-SNVs remain separate cohorts.','binary classification','Pathogenic, Likely_pathogenic or combined versus Benign, Likely_benign or combined; multiple submitters, practice guidelines or expert review',cv,
               applications=('variant-interpretation',),capabilities=('variant-effects',),populations=('human',),input='Reference/alternate sequences centered on mutation with 4,096 nt flanks each side',output='Embedding L2-distance score',limitations='No coordinate release, length normalization, local embedding reduction/alignment, gene/chromosome separation or pretraining-overlap audit established.')
        p=c.protocol(t,t+'-l2','Local reference/alternate embedding distance',cv,'zero-shot','Embeddings within 128 nt adjacent to mutation; reference/alternate L2 distance','Selected ClinVar cohort evaluated without fitting; no gene/species/chromosome holdout described.','variant',metrics=('auprc',),embeddings=True,notes='Window/context variants differ in checkpoint training context and token consumption; not a controlled same-checkpoint distal-context ablation.')
        c.count(t,pos,'variants',cv,split='pathogenic');c.count(t,neg,'variants',cv,split='benign')
        c.variant(t,t+'-unbalanced','Reported complete cohort',cv,revision='ClinVar20240301',length='4,096 nt flanks + allele')
        if kind=='snv':c.variant(t,t+'-balanced','Balanced SNV figure arm',cv,notes='Balancing algorithm, retained variant IDs and sample count unresolved; not assumed to be twice the pathogenic count.')
        c.use('aido2',t,cv,'aido2','original-release',p)
        c.use('evo2',t,cv,'aido2','external-evaluation',note='Report compares Evo2-1B here. This is not usage in the original Evo2 paper; comparator scoring details remain unresolved.')
    property(c,'aido2','coverage-context','context','Coverage adaptation context','524-kb input with frozen backbone and Flashzoi adapter; local sliding-window attention ±8,192 tokens. This is an adaptation/inference procedure, separate from 64K/256K pretraining contexts.',cov)
    for slug,target,region in [('tf-chip','TF ChIP-seq','tfbs'),('histone-chip','Histone ChIP-seq','genome'),('dnase','DNase-seq','chromatin-boundary'),('cage','CAGE','promoter'),('rna','RNA-seq coverage','gene')]:
        t='aido2-coverage-'+slug
        # Accessibility is not a chromatin-boundary target.
        regions=(('regulatory','target'),) if slug=='dnase' else ((region,'target'),)
        regions=tuple((r,rel,'Functional target of the assay; inputs span full genomic windows, not isolated elements.') for r,rel in regions)
        c.task(t,'aido2-evals',target+' coverage','Original Borzoi training data / AIDO.DNA2 adapter',target+' signal by track','Predict dense assay signal from long genomic inputs with frozen encoder representations and a trained Flashzoi adapter.','dense regression','Experimental coverage tracks',cov,
               applications=('genome-annotation','regulatory-engineering'),capabilities=('dense-annotation','context-specific',('long-context','input-demand','524-kb sequence input with local attention; no separate distal-dependency ablation established.')),regions=regions,
               input='524-kb genomic windows; exact species×track manifest pending',output='Assay-specific coverage tracks',limitations='Example counts, track IDs, output binning, species allocation and exact correlation statistic unresolved. Do not infer all five readouts use identical head details from RNA-specific method text.')
        p=c.protocol(t,t+'-adapter','Frozen AIDO.DNA2 + Flashzoi adapter',cov,'frozen backbone; trained adapter','Hidden representations → 512-channel linear projection → Flashzoi adapter','Original 8-fold Borzoi partition: train 0–2, 5–7;validation 4;test 3. Coordinate and homology relationships require manifest audit.','Borzoi fold / genomic window',embeddings=True,fitted='Projection and Flashzoi adapter; encoder frozen',selection='Validation fold 4; precise early stopping not specified',notes='BF16; sliding attention ±8192 tokens;32 H100,global batch 32,LR warmup 2e-5,weight decay 1e-8,gradient clip 0.15. Report states reverse complement and 0–3 nt input shifts with labels unchanged. Correlations reported, type unresolved.')
        c.variant(t,t+'-ensemble','Medium/large four-run ensembles',cov,notes='Average predictions from four independently trained runs; separate from single-run scores.')
        c.use('aido2',t,cov,'aido2','original-release',p)
    c.finding(None,'AIDO.DNA2 coverage uses 524-kb inputs and local attention. Reported pretraining context and inference input size do not establish that performance depends on all distal bases; species/track manifests and correlation definition remain pending.',cov,suite='aido2-evals')

def genos(c):
    def pe(slug,locator,text):
        sections={'corpus':'sec-13','architecture':'sec-14','inference':'sec-15','supervised':'sec-16','fitness':'sec-18','sae':'sec-22','crc':'sec-23','lowdepth':'sec-24'}
        url='https://www.biorxiv.org/content/10.64898/2026.05.21.726868v1.full'
        return c.ev('genosm-'+slug,'genosm-paper',locator,text,url=url+'#'+sections.get(slug,'sec-12'))
    corpus=pe('corpus','Methods: Pretraining data curation and corpus design; Supplementary Figure1','Approximately 1.2T nucleotide tokens; GTDB R220 representatives, public human-associated prokaryotic genomes, UHGV phages and in-house gut MAGs; >90% completeness, <1% prokaryote contamination; independent dynamic sampling for 8K, 32K, 128K, 1M.')
    arch=pe('architecture','Methods: Model architecture and training','Causal MoE Transformer: 4.7B total, ~330M active, 12 layers, width 1024, 16 attention heads, 8 KV groups, 32 experts, top-2, expert FFN width 4096, RMSNorm, RoPE 50M, SwiGLU. Single-nucleotide tokenizer, reported vocabulary 128. 8K→32K→128K→1M curriculum.')
    for row in c.rows['papers']:
        if row['id']=='genosm':row.update(publication_date='2026-05-24',doi='10.64898/2026.05.21.726868',status='bioRxiv preprint v1')
    property(c,'genosm','corpus','pretraining','Corpus sources','GTDB R220: 67,525 representative genomes; public human-associated prokaryotes: 102,986; in-house gut MAGs: 89,320; UHGV phages: 57,514. Approximately 1.2T nucleotide tokens; 186 phyla, 3,448 families, 69,056 species. Human-associated prokaryote subset: 45 phyla, 585 families, 12,273 species.',corpus,notes='Corpus/sampling size reported, not independently reconstructed. In-house genomes are not established as public artifacts; downstream holdouts do not establish exclusion from pretraining.')
    comp=c.code('genosm-corpus-table',GENOS,'README_en.md','| GTDB R220 (a)',
        'Corpus table: 379B GTDB tokens/31.30%; 446B human-associated prokaryote tokens/36.85%; 382B in-house MAG tokens/31.53%; 3.8B UHGV tokens/0.32%.',end_needle='| UHGV (i)',basis='documentation')
    property(c,'genosm','sampling','pretraining','Sampling','GTDB: 379B tokens (31.30% dataloader weight); public prokaryotes: 446B (36.85%); in-house gut MAGs: 382B (31.53%); UHGV: 3.8B (0.32%).',comp)
    property(c,'genosm','quality','pretraining','Quality and preprocessing','Per-context dynamic stratified sampling; prokaryote completeness >90%, contamination <1%; phage CheckV complete or high-quality >90%. Contigs separated with #; runs of >3 N replaced with @; reverse-complement probability 0.5.',corpus)
    property(c,'genosm','architecture','architecture','Architecture','Causal MoE Transformer: 12 layers, width 1024, 16 attention heads, 8 KV groups; 32 experts, top-2/token, expert FFN width 4096; RMSNorm, RoPE base 50M, SwiGLU. 4.7B total parameters, ~330M active.',arch)
    property(c,'genosm','objective','training','Objective','Next-token prediction; N and unknown tokens excluded from the language-model loss.',arch)
    property(c,'genosm','curriculum','context','Training context','8K→32K→128K→1M bp curriculum; separate sampling schemes at each stage. Exact per-stage token budgets unresolved.',arch)
    property(c,'genosm','optimizer','training','Optimization','AdamW, cosine decay, 5% warmup, peak LR 1e-4, gradient clip 1, weight decay 0.1, global batch 1,024, microbatch 1; load-balancing and z-loss coefficients 1e-3; BF16 with FP32 sensitive operations; Megatron parallelism.',arch,notes='The released 8K launch script specifies microbatch 4 and no validation iterations; it is a separate artifact from the paper recipe.')
    inf=pe('inference','Methods: Inference hardware and performance; Discussion','Report claims 1-Mbp inference on an 80-GB GPU and ~200 kb on a 24-GB GPU. Genome readouts average 1-Mbp chunks; this loses cross-chunk dependencies. Hardware feasibility is not a distal-dependency evaluation.')
    property(c,'genosm','inference','context','Inference and genome pooling','Reported 1-Mbp input on one 80-GB GPU; approximately 200 kb on a 24-GB GPU. Whole bacterial genomes are split into 1-Mbp chunks; token embeddings are averaged within chunks and chunk embeddings averaged per genome.',inf,notes='No direct same-checkpoint context ablation or retrieval benchmark established. Genome size can exceed a single model context.')
    sha=json.loads((ROOT/'research/sources/new-models/Genos-m-api.json').read_text())['sha']
    def hf(file,slug,statement,basis='code'):
        source='genosm-hf-'+slug
        url=f'https://huggingface.co/{GENOS}/blob/{sha}/{file}'
        c.source(source,'Genos-m '+file,url,'model-artifact',sha,'research/sources/new-models/genosm-'+file)
        return c.ev('genosm-hf-'+slug+'-evidence',source,file,statement,basis)
    config=hf('config.json','config','Pinned HF config: MixtralForCausalLM; max_position_embeddings=1048576, sliding_window=null, vocab_size=256, router_aux_loss_coef=0.01, num_local_experts=32, num_experts_per_tok=2.')
    tok=hf('tokenizer.json','tokenizer','Pinned tokenizer is Unigram with 17 entries: single-character nucleotide symbols C,G,T,A,N,U and #,@ plus special symbols. No multi-base k-mer/BPE pieces occur in this vocabulary. Paper/card 128 vocabulary differs from config 256 and tokenizer 17.')
    property(c,'genosm','tokenizer','tokenization','Released tokenizer','Unigram JSON with 17 listed entries, including single-character C, G, T, A, N, U, #, @ and special symbols. Paper/card report a vocabulary size of 128; released config vocab_size is 256.',tok,status='artifact-inspected',notes='Keep biological tokenization, listed tokenizer entries and model vocabulary padding distinct; the reason for 128 versus 256 is unresolved.')
    c.field('model_properties','genosm-tokenizer','value',arch)
    c.field('model_properties','genosm-tokenizer','value',config)
    property(c,'genosm','config','architecture','Released checkpoint configuration','MixtralForCausalLM; max_position_embeddings=1,048,576; sliding_window=null; vocab_size=256; router_aux_loss_coef=0.01. Architecture widths and 32/top-2 experts match the paper.',config,status='artifact-inspected',notes='The paper/training script auxiliary-loss coefficient 0.001 differs from released inference config 0.01; the inference config alone does not establish the training recipe.')
    launch=c.code('genosm-launch',GENOS,'Scripts/Genos-m-4.7B-pretrain.sh','SEQ_LENGTH=8192','Released launcher specifies 8K sequences with max positions=1048576; SentencePieceTokenizer, microbatch 4, no held-out data or evaluation iterations. It is not a release of the entire long-context curriculum.',end_needle='ROTARY_BASE=50000000')
    property(c,'genosm','launcher','context','Released training script','Script seq_length=8,192, max positions=1,048,576, SentencePieceTokenizer, microbatch 4. This launcher alone does not reproduce 32K/128K/1M training stages.',launch,status='artifact-inspected')
    for key,e in [('description',arch),('notes',tok)]:c.field('models','genosm',key,e)
    for m in c.rows['models']:
        if m['id']=='genosm':m['notes']='Paper/card vocabulary 128 differs from released config 256 and tokenizer 17 entries. Benchmark checkpoint is labeled cpt32k in project Table 9; relation to final 1M-context weights is not established.'
    unified=pe('supervised','Methods: Unified supervised evaluation; Local sequence tasks; Gene-fitness regression','Frozen backbone, final-layer mean-pooled embeddings; lightweight MLP classification/regression, AUROC with ACC/F1 for classification, Pearson for regression. Strain phenotypes use linear classifiers.')
    doc=c.code('genosm-inventory',GENOS,DOC,'**Table 1. Dataset inventory','Task sources, reported sizes and split descriptions; paper/released-data differences require explicit variants.',end_needle='### Unified Supervised Evaluation Protocol',basis='documentation')
    c.suite('genosm-evals','Genos-m evaluations','Microbial local/regional tasks, BacBench subsets, 13 RNAGym assays, SAE features and microbiome sample applications.',unified,'genosm','genosm-paper',notes='Paper and pinned protocol documentation audited; no task dataset/split artifact audit for the new cohorts. Comparator architecture/checkpoint labels must not be conflated with current model families.')
    def de(slug,needle,text):
        lines=(ROOT/'research/sources/new-models/genosm'/DOC).read_text().splitlines()
        start=next(i for i,line in enumerate(lines) if needle in line)
        end=next((line for line in lines[start+1:] if line.startswith('##')),lines[start])
        return c.code('genosm-doc-'+slug,GENOS,DOC,needle,text,end_needle=end,basis='documentation')
    def use(t,e,p=None,comparators=False):
        c.use('genosm',t,e,'genosm',protocol=p)
        if comparators:c.use('evo2',t,e,'genosm','external-evaluation',p,note='Genos-m comparison uses Evo2-40B-base (8,192 context), not original Evo2-paper usage. Comparator inputs may be truncated/windowed; exact per-model policy needs code audit.')
    # Reused essentiality target: preserve the source-specific cohort and split as a variant.
    e=de('essential','### 1.1 Essential gene identification','Project describes 51 genomes, 37 species, 22,486 essential + 146,922 nonessential genes; 30/10/11 genome genus-disjoint split, three seeds. Differs from pinned 55-genome artifact already audited for LOAM.')
    t='bacbench-essential';c.member('genosm-evals',t,e)
    v=c.variant(t,'genosm-essential-cohort','Genos-m documented 51-genome cohort',e,targets=51,target_unit='genomes',notes='Do not overwrite the independently measured LOAM/HF 55-genome variant.')
    p=c.protocol(t,'genosm-essential-probe','Genos-m BacBench essentiality MLP',e,'frozen probe','Final-layer mean-pooled gene sequence embeddings','Genus-disjoint 60/20/20: 30 train, 10 validation, 11 test genomes; three seed repeats according to documentation.','genus / genome',metrics=('auroc','accuracy','f1'),embeddings=True,fitted='MLP',variant=v)
    for n,split,unit in [(169408,'total','genes'),(22486,'essential','genes'),(146922,'non-essential','genes'),(30,'train','genomes'),(10,'validation','genomes'),(11,'test','genomes')]:c.count(t,n,unit,e,split=split,variant=v,protocol=p)
    use(t,e,p,True)
    c.finding(t,'Genos-m documentation reports 51 genomes and 169,408 genes with 30/10/11 genomes, while the pinned HF artifact inspected for LOAM has 55 genomes and 37/9/9. Release/cohort equivalence has not been established.',e,severity='discrepancy',suite='genosm-evals')
    local=[
      ('promoter','iPro-MP promoter benchmark','Prokaryotic promoter versus negative fragment','binary classification',321858,'81 bp','23 prokaryotic species; 81-bp [-60,+20] TSS windows; 107,286 deduplicated positives, CDS/convergent-intergenic negatives sampled 2:1. Species-specific heads; released 8:2 random split.','Random sequences within each species; no held-out species implied.',('promoter',),(),'### 1.2 Promoter recognition'),
      ('gene-class','GenerAnno bacterial gene classification','Six genomic-region classes','multiclass classification',30000,'Average 837 bp','RefSeq CDS, pseudogene, tRNA, rRNA, ncRNA and intergenic fragments; approximately balanced 30k. Documentation says 10-fold cross-validation; inventory gives 9:1.','Ten-fold cross-validation per task prose; exact train/validation subdivision unresolved.',('cds','gene','trna','rrna','ncrna','intergenic'),('bacteria',),'### 1.3 Six-class bacterial gene classification'),
      ('amr','GenerAnno drug_resistence_prediction','Antibiotic-resistance gene versus control','binary classification',16100,'120 bp–4.5 kb','CARD positive genes versus length-distribution-matched RefSeq non-AMR genes; single-gene annotation, not strain AST.','Project states 8:2 train/test but also ~14.5k train + 1.6k test of 16.1k (approximately 9:1); unresolved.',('cds',),('bacteria',),'### 1.4 Antibiotic Resistance Gene Prediction'),
      ('virulence','Genos-m VFDB core / DEG controls','Virulence-factor gene versus control','binary classification',9559,'<8 kb','4,570 VFDB core positive genes; 4,989 DEG essential negative genes after filtering virulence-associated annotations; negatives species-stratified.','8:2 label-stratified random train/test; genus/homology separation not established.',('cds','gene'),('bacteria',),'### 1.5 Virulence Factor Gene Identification')]
    for slug,ds,target,typ,n,length,desc,split,regions,pops,needle in local:
        e=de(slug,needle,desc+' '+split);t='genosm-'+slug
        c.task(t,'genosm-evals',target,ds,target,desc,typ,'Source annotations; see task description',e,
               applications=('genome-annotation','microbial-genomics'),capabilities=('functional-prediction',),regions=regions,populations=pops,
               input=length+' DNA fragments',output='Class probabilities',limitations='Dataset version, sample IDs, label-specific counts and validation strategy require artifact audit. Reported taxon coverage is not a species holdout.')
        p=c.protocol(t,t+'-mlp','Frozen representation MLP',e,'frozen probe','Final-layer mean-pooled embeddings',split,'sequence',metrics=('auroc','accuracy','f1'),embeddings=True,fitted='Task-specific MLP; 23 species-specific heads for promoters' if slug=='promoter' else 'Task-specific MLP')
        c.count(t,n,'sequences',e,qualifier='Approximate' if slug in ('gene-class','amr') else 'Reported');c.variant(t,t+'-input','Reported input configuration',e,length=length)
        use(t,e,p,True)
        if slug=='virulence':
            for split,count in [('positive',4570),('negative',4989)]:c.count(t,count,'genes',e,split=split)
        if slug=='amr':c.finding(t,'Documented 8:2 split conflicts with ~14.5k/1.6k counts (~9:1). Neither is silently converted to exact split counts.',e,severity='discrepancy',suite='genosm-evals')
    fitness=pe('fitness','Methods: Gene-fitness regression','Eight GenerAnno/FitnessBrowser conditions; MSE training loss, Pearson metric. Gene fitness under the specified nutrient/stress condition; not unconditional organism-wide fitness.')
    for slug,name,n,length in [('glucose','Min-media-glucose',35600,1002),('arabinose','L-Arabinose_C',60000,1030),('pyruvate','Pyruvate_C',60000,1013),('alanine','D-Alanine_N',28100,1015),('ammonium','Ammonium-chloride_N',37600,1004),('histidine','L-Histidine_nutrient',35600,1002),('cisplatin','Cisplatin_stress',20900,1028),('perchlorate','perchlorate_stress',14200,959)]:
        t='genosm-fitness-'+slug
        c.task(t,'genosm-evals',name+' gene fitness','GenerAnno / FitnessBrowser '+name,'Condition-specific gene fitness','Predict contribution of a bacterial gene to measured fitness in the named condition.','regression','FitnessBrowser experimental fitness scores',fitness,
               applications=('strain-engineering','microbial-genomics'),capabilities=('functional-prediction','context-specific'),regions=('gene','cds'),populations=('bacteria',),input='Gene DNA sequence; condition fixed by dataset',output='Continuous fitness score',limitations='Individual species, assay IDs, label processing and split files are not verified; random sequence folds need not separate homologs.')
        p=c.protocol(t,t+'-mlp','Frozen gene-embedding regression',fitness,'frozen probe','Final-layer mean-pooled gene embeddings','Inventory reports 9:1; released GenerAnno fold/split implementation and validation subdivision not established.','gene sequence',metrics=('pearson',),embeddings=True,fitted='MLP regressor; MSE loss')
        c.count(t,n,'genes',doc,qualifier='Approximate inventory count; not recounted');c.variant(t,t+'-input','Inventory sequence length',doc,length=f'Average {length} bp')
        c.field('protocols',p,'split_rule',doc);use(t,fitness,p,True)
    genos_bgc(c,de,use)
    genos_rna(c,de,use,pe)
    genos_phenotypes(c,de,use,pe)
    genos_applications(c,pe,use)

def genos_bgc(c,de,use):
    for slug,target,n,needle in [('binary','BGC versus non-BGC region',4214,'### 2.1 BGC Binary Classification'),('types','Six BGC biosynthetic classes',2636,'### 2.2 BGC Multilabel Classification')]:
        desc=('MIBiG4 positives excluding fungal, unknown and abnormal-length entries; antiSMASH-screened BGC-free negatives matched on length and CDS count. Given candidate regions, not genome-wide boundary detection.' if slug=='binary' else 'MIBiG4 known BGC regions with six potentially simultaneous labels: PKS, NRPS, ribosomal/RiPP, saccharide, terpene and other. This cohort is distinct from other MIBiG-derived benchmark releases.')
        e=de('bgc-'+slug,needle,desc);t='genosm-bgc-'+slug
        c.task(t,'genosm-evals',target,'Genos-m MIBiG4 / GTDB226-derived cohort' if slug=='binary' else 'Genos-m MIBiG4 type cohort',target,desc,'binary classification' if slug=='binary' else 'multilabel classification','Curated MIBiG annotations; antiSMASH-screened negatives for binary task',e,
               applications=('natural-products','microbial-genomics'),capabilities=('functional-prediction',('long-context','input-demand','Regional sequences may exceed a model context; truncation/windowing differs by comparator. No controlled distal-dependency test established.')),regions=('bgc',),
               input='BGC/candidate-region DNA; inventory gives 8 kb–1 Mb+',output='One BGC probability' if slug=='binary' else 'Six class probabilities',limitations='Released dataset and exact train/test IDs unverified. Fungal removal is specified for binary positives only; species coverage of the multilabel cohort is not asserted. Multi-gene input length alone does not prove long-range dependency use.')
        p=c.protocol(t,t+'-mlp','Frozen regional embedding MLP',e,'frozen probe','Final-layer mean-pooled regional representations','8:1:1 train/validation/test; balance preserved for binary; label distributions approximately preserved for multilabel. No genus/homology separation established.','candidate region',metrics=('auroc','accuracy','f1'),embeddings=True,fitted='MLP classifier' if slug=='binary' else 'MLP with focal loss',selection='Per-label thresholds selected on validation for multilabel task.' if slug=='types' else 'Validation selection details unresolved.',notes='Project allows truncation or sliding-window aggregation beyond each model context. Exact per-checkpoint transformation remains unresolved; Genos-m comparison checkpoint labeled cpt32k in Table 9.')
        c.count(t,n,'regions','genosm-inventory',qualifier='Inventory reported; not recounted')
        if slug=='binary':
            for label in ('positive','negative'):c.count(t,2107,'regions',e,split=label)
        c.variant(t,t+'-context','Reported candidate region length',e,length='8 kb–1 Mb+; comparator-specific truncation/windowing unresolved')
        use(t,e,p,True)
    c.finding(None,'Genos-m Table 9 labels its benchmark checkpoint cpt32k while listing 1M maximum context. The connection between this checkpoint, the final released weights and each BGC input protocol remains unresolved. This is separate from evidence of 1M inference feasibility.',de('checkpoint','| Genos-m | Genos-m(cpt32k)','Comparison table identifies Genos-m(cpt32k); other entries include Evo2-40B-base (8K) and older NTv3_650M_pre.'),suite='genosm-evals')

def genos_rna(c,de,use,pe):
    e=de('rna','### 1.7 RNAfitness Prediction, Zero-Shot','Thirteen named prokaryote-related RNAGym assays total 54,384 mutants; U→T; mean next-token log-likelihood; absolute Spearman per assay then mean. Comparator results imported from RNAGym release, not rerun here.')
    assays=['Andreasson_2020_ribozyme','BCHB_CHLTE_Tsuboyama_2023_2KRU','BLAT_ECOLX_Firnberg_2014','BLAT_ECOLX_Jacquier_2013','CCDB_ECOLI_Adkar_2012','ESTA_BACSU_Nutschel_2020','F7YBW8_MESOW_Ding_2023','IF1_ECOLI_Kelsic_2016','MLAC_ECOLI_MacRae_2023','PSAE_PICP2_Tsuboyama_2023_1PSE','Peri_2022_ribozyme','Q837P4_ENTFA_Meier_2023','RNC_ECOLI_Weeks_2023']
    for assay in assays:
        t='rnagym-'+assay.lower().replace('_','-');assert t in c.ids['tasks'],t
        c.member('genosm-evals',t,e,'Reuse the existing individual assay; Genos-m scoring is a separate protocol. Keyword-based selection is not verified taxonomic provenance.')
        p=c.protocol(t,'genosm-'+t,'Genos-m causal RNAfitness score',e,'zero-shot','RNA U→T; whole-mutant mean next-token log-likelihood','All eligible mutants in the selected external assay; no task-specific training. No held-out mutation-order or sequence-family split described.','mutant sequence',metrics=(('abs-spearman','Absolute within-assay Spearman; equal-weight mean across 13 assays'),('auroc','Reported alongside correlation; binary threshold definition not established'),('mcc','Reported alongside correlation; threshold definition not established')),embeddings=False,notes='54,384 is a panel total, not an individual assay count. Assay identities are explicit; benchmark filter is based on identifiers/descriptions and includes synthetic ribozymes.')
        use(t,e,p)
        c.use('evo2',t,e,'genosm','external-evaluation',note='Evo2-7B comparator values imported from RNAGym release for this 13-assay subset; not newly executed or original Evo2-paper usage.')
    property(c,'genosm','rna-panel','evaluation','RNAfitness cohort','Thirteen explicit RNAGym assays; 54,384 mutants total. Includes 11 protein-coding assays and 2 ribozymes; no per-assay count inferred from this aggregate.',e)

def genos_phenotypes(c,de,use,pe):
    e=de('phenotype','### Genomic Phenotype Prediction','GIDEON/BacBench 1,175 genomes; independent phenotype classifiers; genus-disjoint 70/10/20, seeds 1,2,3; genome embeddings average 1-Mb chunks. Trait-specific label availability differs.')
    for slug,name,pos,neg in [('gram','Gram-positive status',550,602),('anaerobe','Anaerobe status',322,789),('motile','Motility',292,746),('spores','Spore formation',95,1074),('hemolysis','Beta hemolysis',52,631)]:
        t='genosm-phenotype-'+slug
        c.task(t,'genosm-evals',name,'BacBench / GIDEON strain phenotype collection',name,'Predict the named binary strain phenotype from whole-genome representations. Each trait has its own observed-label subset.','binary classification','GIDEON phenotype labels',e,
               applications=('strain-engineering','microbial-genomics'),capabilities=('functional-prediction',('long-context','input-demand','Genome represented through averaged 1-Mb chunks; no attention or dependencies across chunks.')),regions=('genome',),populations=('bacteria',),input='Bacterial genome, average 3.7 Mb; split into 1-Mb chunks',output='Binary phenotype probability',limitations='Genome identifiers, per-split label counts, genus memberships and pretraining overlaps unverified; 1,175 is the shared collection size, not the observed label count for every trait.')
        c.member('bacbench',t,e,'GIDEON target-specific expansion from Genos-m; not assumed identical to the existing combined Madin/Traitar/Brbic phenotype task.')
        p=c.protocol(t,t+'-linear','Genome embedding linear classifier',e,'frozen probe','1-Mb chunk hidden states → mean chunk embedding → mean genome embedding','Genus-disjoint 70/10/20 train/validation/test; seeds 1,2,3.','genus / genome',metrics=(('auroc','Mean and SD across seeds 1,2,3'),),embeddings=True,fitted='Independent linear classifier per phenotype')
        for label,n in [('positive',pos),('negative',neg)]:c.count(t,n,'genomes with observed label',e,split=label)
        use(t,e,p)


def genos_applications(c,pe,use):
    sae=pe('sae','Methods: Sparse autoencoder interpretability; Figure4','SAE trained on approximately 305k 32K chunks from pretraining corpus, downsampled and shuffled to ~1B token activations; 4096 latents, Batch-TopK 128. E. coli NC000913.3 one-v-rest annotation alignment; Domain F1 threshold sweep.')
    for slug,name,region in [('orf','ORF','cds'),('intergenic','Intergenic','intergenic'),('trna','tRNA','trna'),('rrna','rRNA','rrna')]:
        t='genosm-sae-'+slug
        c.task(t,'genosm-evals','SAE feature alignment: '+name,'E. coli NC000913.3 / Genos-m SAE annotations',name+' annotation alignment','Search sparse autoencoder features for agreement with the named genomic annotation. This is a feature-interpretation analysis.','token-level binary annotation / interpretability','Annotated E. coli regions',sae,
               applications=('genome-annotation','model-development'),capabilities=('interpretability',),regions=((region,'target','Named annotation target; feature analysis is performed over genomic positions.'),),populations=('ecoli',),input='Last-layer token activations from E. coli genome',output='Sparse features aligned to annotation',limitations='No independent feature-search/threshold-selection test split established. Reported Domain F1 is descriptive after threshold sweeping, not a prespecified held-out annotation accuracy.')
        p=c.protocol(t,t+'-sae','Batch-TopK SAE annotation alignment',sae,'frozen backbone; trained sparse autoencoder','Token activations → 4096 latent features','SAE activation training samples drawn from pretraining corpus; feature search on E. coli NC000913.3. No separate annotation validation/test cohort described.','token / genomic position',metrics=(('f1','One-versus-rest Domain F1 after activation threshold sweep'),),embeddings=True,fitted='SAE: Batch-TopK 128, batch 4096, LR 5e-5, one epoch',selection='Feature search and activation-threshold sweep on annotation cohort')
        use(t,sae,p)
    crc=pe('crc','Methods: Community-level microbiome self-supervised learning with genome-level representations; Figure5','Genos-m genome embeddings augment species tokens in a separate microbiome Transformer pretrained on ~400k unlabeled gut profiles; frozen microbiome backbone + MLP; 14 CRC cohorts, within-cohort 10-fold and pairwise cross-cohort validation; AUROC.')
    t='genosm-crc'
    c.task(t,'genosm-evals','Colorectal cancer versus control','14 CRC gut-metagenomic cohorts from Piccinno et al.','CRC case/control status','Evaluate a microbiome abundance model augmented with Genos-m genome-informed species representations. This is a composite pipeline rather than a direct nucleotide-only diagnosis.','binary classification','Cohort case/control labels',crc,
           applications=('microbiome-analysis',),capabilities=('functional-prediction','context-specific'),populations=(('human','sample-host','Human gut metagenomes; human is the host, not the microbial sequence origin.'),),
           input='Species relative-abundance profiles + projected Genos-m representative-genome embeddings',output='Case/control probability',limitations='Individual cohort/sample IDs and counts not yet imported. Overlap between 400k microbiome pretraining profiles and CRC cohorts is not established. Cohort transfer is separate from species holdout.')
    for slug,split,unit in [('within','Within each cohort, 10-fold cross-validation; subject grouping and model-selection nesting unresolved.','sample'),('cross','Pairwise train-one-cohort/test-another among 14 cohorts; exact validation and participant overlap require audit.','cohort')]:
        p=c.protocol(t,t+'-'+slug,'CRC '+slug+'-cohort evaluation',crc,'frozen genome encoder and microbiome backbone; trained classifier','Genos-m genome embeddings augment species-token abundance Transformer',split,unit,metrics=('auroc',),embeddings=True,fitted='Separate microbiome Transformer pretrained on ~400k profiles; frozen for downstream MLP')
        use(t,crc,p)
    c.count(t,14,'cohorts',crc)
    low=pe('lowdepth','Methods: Low-depth metagenomic embedding evaluation; Figure6','Read 2 reverse-complemented then concatenated with read 1; read embeddings mean-pooled by sample. 15 samples × 4 depths × 5 replicates; 10K-read mixtures; geography 4,137 samples; enterotype 2,033 samples with full-depth Kraken2/PAM-JSD reference.')
    specs=[
      ('stability','Embedding consistency across read depths','15 samples at 10K, 100K, 1M, 10M reads; five independent downsampling replicates per depth. Compare sample embedding geometry with UMAP and embedding consistency analyses.','embedding diagnostic',15,'biological samples','Matched sample comparisons across sequencing depths; no fitted prediction train/test split.','Sample identity / depth','UMAP and embedding consistency; exact numerical statistic unresolved'),
      ('mixture','Embedding response to community mixture','A representative sample pair mixed at 0–100% in 10% increments, 10 repeats, 10K reads per mixture. Test continuity of embedding trajectories.','embedding diagnostic',2,'source biological samples','Controlled synthetic mixtures of one sample pair; no held-out mixture test described.','Mixture proportion','Embedding trajectory; no scalar predictive metric established'),
      ('geography','Sample geographic origin','4,137 human gut metagenomes; 2,033 Northeast China, 500 East China, 500 South China, 500 Europe, 500 Africa, 104 North America. Linear classifier on 10K-read sample embeddings.','multiclass classification',4137,'samples','Train/test proportions, participant separation and cohort/site handling not stated in inspected methods.','Geographic collection group','AUROC; class averaging unresolved'),
      ('enterotype','Enterotype assignment agreement','2,033 in-house gut samples; full-depth average 73.6M paired reads. Reference PAM/Jensen-Shannon genus profiles from Kraken2/UHGG; 10K-read embeddings clustered with K-means/cosine distance.','clustering agreement',2033,'samples','Same samples at 10K reads and full depth; reference cluster assignments derived from full-depth profiles, not independent clinical labels.','Prevotella- versus Bacteroides-dominated enterotype','Agreement with full-depth reference; cluster-label alignment unresolved')]
    for slug,name,desc,typ,n,unit,split,target,metric in specs:
        t='genosm-lowdepth-'+slug
        c.task(t,'genosm-evals',name,'Genos-m low-depth gut-metagenomic study / '+slug,target,desc,typ,'Sample metadata, controlled mixtures or full-depth clustering',low,
               applications=('microbiome-analysis',),capabilities=('embedding-analysis',) if slug!='geography' else ('functional-prediction',),populations=(('human','sample-host','Human gut metagenomes; host metadata is not microbial taxonomic coverage.'),),input='Read 1 concatenated with reverse-complement read 2; 10K read-level embeddings mean-pooled per sample',output=metric,
               limitations='Primary datasets include in-house samples; availability and participant/cohort overlaps require verification. These are sample-level microbial community analyses, not host-genome tasks.')
        p=c.protocol(t,t+'-pool','Low-depth pooled-read representation',low,'frozen embedding analysis' if slug!='geography' else 'frozen probe','Mean token/read representations → mean sample representation',split,'sample',metrics=('auroc',) if slug=='geography' else (('cluster-agreement',) if slug=='enterotype' else ()),embeddings=True,fitted='Linear classifier' if slug=='geography' else ('K-means with cosine distance' if slug=='enterotype' else 'Projection / similarity analysis'),notes=metric)
        c.count(t,n,unit,low);use(t,low,p)
    c.finding(None,'Genos-m microbiome applications use sample-level host metadata and additional pooling or abundance-model training. They do not establish microbial species holdouts, direct host-DNA prediction or cross-chunk genomic dependency learning.',low,suite='genosm-evals')
