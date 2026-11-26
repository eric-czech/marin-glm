"""PlantCAD2 journal paper, released tasks/leaderboard, and GeneCAD adaptation."""
from pathlib import Path
from collections import defaultdict
import csv,json,yaml
from .new_models import property
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'research/sources/plantcad'
PC='plantcad/plantcad';GC='plantcad/genecad'
ZERO='PlantCAD2_zero_shot_tasks';FT='PlantCAD2_fine_tuning_tasks'
REV='plantcad/genecad_revision_models'

def hf(c,id,repo,file,api,local,statement,basis='documentation',kind='datasets'):
    revision=json.loads((BASE/api).read_text())['sha']
    url=f'https://huggingface.co/{kind+"/" if kind else ""}{repo}/blob/{revision}/{file}'
    c.source(id,' / '.join((repo,file)),url,'dataset-file' if kind=='datasets' else 'repository-file',revision,
             str((BASE/local).relative_to(ROOT)))
    return c.ev(id+'-ev',id,file,statement,basis)

def revision(c,slug,file,statement,basis='documentation'):
    return hf(c,'genecad-release-'+slug,REV,file,'genecad-revision-api.json',
              'genecad-revision-'+file.replace('/','--'),statement,basis,kind='')

def populate(c):
    populations(c)
    url='https://pmc.ncbi.nlm.nih.gov/articles/PMC13576720/'
    c.source('plantcad2-paper','PlantCAD2 journal article',url,'paper','Cell Genomics 6(9),101329;2026-08-07',
             'research/papers/plantcad2.txt',notes='Published version corresponding to DOI10.1016/j.xgen.2026.101329 and PII S2666-979X(26)00191-6. Full-text JATS retrieved from Europe PMC; publisher page unavailable through web retrieval.')
    c.paper('plantcad2','PlantCAD2: A DNA foundation model for interpreting genomes across flowering plants','plantcad2-paper',2026,
            status='journal',scope='primary-model',doi='10.1016/j.xgen.2026.101329',date='2026-08-07')
    def pe(slug,section,statement):return c.ev('plantcad2-'+slug,'plantcad2-paper',section,statement,url=url+'#'+section)
    arch=pe('architecture','sec9.3.2','Caduceus with Mamba2 blocks, bidirectional shared projections, reverse-complement equivariance; single-base tokens; 8,192 bp masked-LM training, 15% masking; 240k steps, global batch 2048, AdamW with cosine schedule 2e-4→4e-6, 6% warmup, weight decay 1e-5.')
    corpus=pe('corpus','sec9.3.1','65 Phytozome angiosperm genomes; one assembly/haplotype selection, one genus representative; gene-centered±5 kb regions,8,192 bp windows,4,096 bp stride. Methods do not establish chromosome/homology-separated pretraining splits.')
    c.add('models',id='plantcad2',name='PlantCAD2',scope='primary',paper_id='plantcad2',
          description='Angiosperm-specific, bidirectional, reverse-complement-equivariant Mamba2/Caduceus masked language model. GeneCAD is recorded as a downstream annotation adaptation, with paper and release protocols distinguished.',evidence_id=arch,
          notes='Paper summary/methods and released large checkpoint are labeled 676M; Results/Figure 1 also say 694M. GeneCAD 2025 freezes the encoder; the 2026 revision explicitly updates it and uses a different 200M PlantCAD2-family backbone.')
    config=hf(c,'plantcad2-model-config','kuleshov-group/PlantCAD2-Large-l48-d1536','config.json','plantcad2-model-api.json','plantcad2-model-config.json',
              'Pinned large checkpoint:48 layers, d_model 1536, bidirectional/add, weighttie, rcps=true, vocab_size 8; model type caduceus; context not encoded as max_position_embeddings.',basis='code',kind='')
    property(c,'plantcad2','architecture','architecture','Architecture','Caduceus with Mamba2 blocks; bidirectional processing with shared projections and reverse-complement equivariance. Single-nucleotide masked-token objective.',arch)
    property(c,'plantcad2','config','architecture','Released large configuration','48 layers; d_model=1,536; bidirectional_strategy=add; bidirectional_weight_tie=true; rcps=true; vocab_size=8.',config,status='artifact-inspected')
    property(c,'plantcad2','sizes','architecture','Model sizes','Small 88M (24 layers, width 768); medium 311M (48 layers, width 1024); large 676M (48 layers, width 1536) in summary/checkpoint labeling. Results/Figure 1 also describe 694M for large.',pe('sizes','sec2.1','Three model sizes; large reported both 676M and 694M in the published article.'),notes='Keep the published discrepancy explicit; no independent tensor parameter count performed.')
    property(c,'plantcad2','corpus','pretraining','Corpus and sampling','65 angiosperm genomes from Phytozome; one representative per genus. Gene-centered ±5 kb intervals tiled into 8,192 bp windows with 4,096 bp step; repeats downweighted to 0.1 in MLM loss.',corpus)
    c.field('model_properties','plantcad2-corpus','value',pe('repeat-loss','sec9.3.3','Repetitive nucleotide MLM loss weights 0.1; non-repetitive 1.0. This differs from downstream task sampling.'))
    property(c,'plantcad2','tokenization','tokenization','Tokenizer','Single-nucleotide tokenization; released config vocabulary size 8 and explicit complementary base mapping. No k-mer segmentation.',config,status='artifact-inspected')
    property(c,'plantcad2','training','training','Pretraining procedure','240,000 steps; global batch 2,048; length 8,192 bp; 15% BERT-style masking (80% MASK /10% random /10% unchanged); AdamW, cosine decay 2e-4→4e-6, 6% warmup, weight decay 1e-5.',arch)
    context=pe('context','sec2.6','Actual context experiments: conservation 512–8192 bp; accessibility 600–4600 bp with fixed 600 bp labels; expression 1–4 kb upstream/downstream. Distinguish these controlled input comparisons from a genome-size claim.')
    property(c,'plantcad2','context','context','Context protocols','Pretrained at 8,192 bp. Conservation comparisons vary centered inputs 512–8,192 bp. Accessibility context experiment keeps 600 bp target labels while extending flanks to 4,600 bp; expression varies 1–4 kb upstream and downstream.',context)
    zero_card=hf(c,'plantcad2-zero-card','plantcad/'+ZERO,'README.md',ZERO+'-api.json',ZERO+'-README.md',
        'Pinned dataset manifest has 12 configs and 20 species/configsplit combinations; card provides sizes for 10 configs and prose for Andropogoneae/SV. Recovery files omit labels; classification files provide binary labels.')
    ft_card=hf(c,'plantcad2-ft-card','plantcad/'+FT,'README.md','plantcad2-finetune-api.json','finetune-README.md',
        'Pinned supervised release has 7 configs; counts are manifest-reported unless separately inspected. Cell-type labels serialized as strings; gene-expression files carry genome and orthogroup metadata.')
    c.suite('plantcad2-zero','PlantCAD2 zero-shot tasks','Conservation proxies, junction reconstruction, core-gene membership and simulated deletion effects; species variants share task records.',zero_card,'plantcad2','plantcad2-zero-card',notes='12 released configurations become 12 dataset×target records with species variants. Additional potato conservation and pretraining diagnostics are paper-only additions, not silently counted as released configs.')
    c.suite('plantcad2-ft','PlantCAD2 supervised tasks','LoRA accessibility, gene-expression and Ribo-seq-derived translation tasks; paper-only extra targets remain distinct from 7 released configs.',ft_card,'plantcad2','plantcad2-ft-card')
    zero(c,pe,zero_card)
    supervised(c,pe,ft_card)
    genecad(c)
    artifacts(c)


def populations(c):
    for id,name,rank,parent in [
      ('andropogoneae','Andropogoneae','tribe','poaceae'),('potato','Solanum tuberosum','species','solanaceae'),
      ('eutrema','Eutrema salsugineum','species','brassicaceae'),('setaria-viridis','Setaria viridis','species','poaceae'),
      ('poplar','Populus trichocarpa','species','angiosperms'),('common-bean','Phaseolus vulgaris','species','fabaceae'),
      ('walnut','Juglans regia','species','angiosperms'),('coffee','Coffea arabica','species','angiosperms'),
      ('nicotiana-sylvestris','Nicotiana sylvestris','species','solanaceae'),('nicotiana-tabacum','Nicotiana tabacum','species','solanaceae'),
      ('oil-palm','Elaeis guineensis','species','angiosperms'),('tripterygium','Tripterygium wilfordii','species','angiosperms'),
      ('artichoke','Cynara cardunculus','species','angiosperms'),('aquilegia','Aquilegia coerulea','species','angiosperms'),
      ('nymphaea','Nymphaea colorata','species','angiosperms'),
      ('bryophytes','Bryophytes','group','plants'),('physcomitrium','Physcomitrium patens','species','bryophytes'),
      ('marchantia','Marchantia polymorpha','species','bryophytes'),('chlorophyta','Chlorophyta','phylum','plants'),
      ('bathycoccus','Bathycoccus prasinos','species','chlorophyta'),('ostreococcus','Ostreococcus tauri','species','chlorophyta'),
      ('klebsormidium','Klebsormidium nitens','species','plants'),('marmoset','Callithrix jacchus','species','mammals')]:
        c.add('populations',id=id,name=name,rank=rank,parent_id=parent,ncbi_taxid=None,notes='Task coverage comes from the cited paper/released manifest. Broader ancestral placement is a curatorial taxonomic mapping; grouping does not imply complete clade coverage.')
    # Use the existing algal species under its more informative clade.
    for p in c.rows['populations']:
        if p['id']=='chlamydomonas':p['parent_id']='chlorophyta'
    # The offline builder inserts parents before children.
    chlamydomonas=next(p for p in c.rows['populations'] if p['id']=='chlamydomonas')
    c.rows['populations'].remove(chlamydomonas)
    c.rows['populations'].append(chlamydomonas)
    for id,name,definition in [('translation-start','Translation initiation site','Translation start codon and its genomic context.'),('translation-stop','Translation termination site','Translation stop codon and its genomic context.')]:
        c.add('categories',id=id,dimension='region',name=name,definition=definition,accommodation=None)
    for id,name,definition in [('precision','Precision','Fraction of predicted positive features matching the reference.'),('recall','Recall / sensitivity','Fraction of reference positive features recovered.'),('mae','Mean absolute error','Mean absolute deviation of predicted continuous targets.'),('busco-complete','BUSCO completeness','Percentage of expected lineage orthologs recovered as complete; not annotation coordinate accuracy.')]:
        if id not in c.ids['metrics']:c.add('metrics',id=id,name=name,definition=definition,direction='lower' if id=='mae' else 'higher')


def zero(c,pe,card):
    cons=pe('conservation','sec9.3.4','Sorghum reference aligned with 34 other Andropogoneae; >=34/35 coverage; identity>=34 conserved,<15 neutral. Poaceae codingMSA325 genomes; phyloP>5 conserved,<1.5 neutral; intermediates excluded. Each target at 1-based 4096 of 8192 bp.')
    masked=c.code('plantcad2-refprob',PC,'src/zero-shot-eval.py','def _compute_auroc','Score is predicted probability of the actual reference nucleotide; AUROC, not token accuracy.',end_needle='def _refprob_scores')
    specs=[('conservation_within_andropogoneae','Andropogoneae genome-wide conservation','Sorghum-centered genomic sites','Genome-wide cross-species conservation',('sorghum',),('genome',),38060),
           ('conservation_within_poaceae_non_tis','Poaceae coding conservation excluding TIS','Poaceae aligned coding sites excluding translation initiation','Coding-site cross-species conservation',('poaceae',),('cds',),183685),
           ('conservation_within_poaceae_tis','Poaceae TIS conservation','Poaceae aligned translation initiation sites','TIS cross-species conservation',('poaceae',),('cds','translation-start'),36662)]
    for config,name,ds,target,pops,regions,n in specs:
        t='plantcad2-'+config
        c.task(t,'plantcad2-zero',name,ds,target,'Discriminate conserved from less-conserved positions using alignment-derived labels and a language-model reference-base score. This is an evolutionary proxy, not measured organismal fitness.','binary classification','Coverage/identity or phyloP thresholds from MSAs',cons,
               applications=('plant-breeding','comparative-genomics'),capabilities=('evolutionary-inference','sequence-modeling'),regions=regions,populations=pops,input='8,192 bp target-centered sequence; target index 4095',output='Reference-base probability / conservation score',limitations='Released test-only cohorts have no fitted train/validation split. Conservation is defined by alignment taxa, which need not be the input sequence species; Poaceae input species per row are not established by the two-field schema.')
        p=c.protocol(t,t+'-mlm','Masked reference-base score',masked,'zero-shot','Mask central base; probability assigned to its reference nucleotide','Test-only released cohort; thresholds filter labels, not chromosome/homology split. Overlap with pretraining coordinates requires separate audit.','target site',metrics=('auroc',('ap','Additional released-scorer average precision')),embeddings=False)
        c.variant(t,t+'-test','Released test split',card,revision=ZERO,length='8,192bp');c.count(t,n,'sites',card,qualifier='Card/prose reported; final file counts are separate')
        for length in [512,1024,2048,4096,8192]:c.variant(t,t+'-context-'+str(length),f'Centered{length}bp context',pe('context-conservation-'+str(length)+'-'+config,'sec2.2','Published conservation context comparison; fixed pretrained checkpoint and centered input crop.'),length=str(length)+'bp')
        c.use('plantcad2',t,cons,'plantcad2',protocol=p)
        c.use('evo2',t,pe('evo-'+config,'sec9.3.14','Evo 2-7B uses unmasked full 8192 bp sequence and causal target-base probability; distinct from bidirectional masking.'),'plantcad2','external-evaluation',note='Original PlantCAD2 comparison; not original Evo 2-paper usage. Evo 2 does not see downstream context when scoring the center.')
        c.field('tasks',t,'dataset_name',card)
    c.finding('plantcad2-conservation_within_poaceae_tis','Methods state 36,668TIS sites(26,653/10,015), whereasTable 1/H Fcard state 36,662(26,650/10,012). Non-TIS methods 183,687 versus card 183,685 also differ. Preserve reported counts and inspected artifact counts separately.',cons,severity='discrepancy',suite='plantcad2-zero')
    membership=pe('core-gene','sec9.3.5','Maize 26NA Mgenomes:core presentall 26, dispensable 2–23/private 1; tomato 586 accessions:coreall 586, dispensable 6–580/private<5. Uncovered frequency bins not resolved. Canonical maize transcript, longest tomato transcript.')
    recovery=pe('recovery','sec2.3','Mask full annotated motif, retain canonical and noncanonical junctions; exact top 1 motifmatch. Maize in pretraining, tomato absent.8,192 bp centered inputs; causal comparators evaluated forward and RC.')
    rec_code=c.code('plantcad2-motif-metric',PC,'src/zero-shot-eval.py','def _metric_motif_accuracy','Motif accuracy requires every canonical A/C/G/T position correct; groups containing ambiguous symbols excluded. Token accuracy separate.',end_needle='def _compute_auroc')
    core_code=c.code('plantcad2-core-score',PC,'src/zero-shot-eval.py','def _avg_trueprob_scores','Core/non-core score is arithmetic mean of true-base probabilities across simultaneously masked motif positions; not an allelicLLR.',end_needle='class ZeroShotEval')
    for motif,target,region,length,maize_recovery,maize_core in [('tis','Translation initiation','translation-start',3,39035,36409),('tts','Translation termination','translation-stop',3,39035,36409),('donor','Splice donor','splice',2,153869,144550),('acceptor','Splice acceptor','splice',2,153869,144550)]:
        for kind,ev in [('recovery',recovery),('core_noncore_classification',membership)]:
            config=motif+'_'+kind;t='plantcad2-'+config
            isrec=kind=='recovery'
            c.task(t,'plantcad2-zero',target+(' motif recovery' if isrec else ' core-gene classification'),ZERO+'/'+config,
                   'Annotated junction motif sequence' if isrec else 'Pan-gene core versus non-core membership',
                   'Reconstruct the annotated motif from surrounding DNA, including noncanonical motifs.' if isrec else 'Predict pan-gene membership from the reference junction motif score. This is not junction-versus-background detection.',
                   'sequence reconstruction' if isrec else 'binary classification','Annotated genomic motif' if isrec else 'Pan-genome gene presence/absence',ev,
                   applications=('genome-annotation','plant-breeding'),capabilities=('sequence-modeling',) if isrec else ('evolutionary-inference','sequence-modeling'),regions=((region,'target','Prediction is restricted to this annotated junction; fullwindows include surrounding sequence.'),),populations=('maize','tomato'),input='8,192 bp junction-centered DNA; entire 2/3 nt motif masked',output='Exact reconstructed motif' if isrec else 'Mean probability of true motif bases',limitations='Recovery is evaluated at known annotated sites; it does not test finding sites genome-wide. Species are independent released test variants, not supervised training and test partitions.')
            ecode=rec_code if isrec else core_code
            p=c.protocol(t,t+'-mlm','Masked motif reconstruction' if isrec else 'Masked motif core-membership score',ecode,'zero-shot','Simultaneous motif masks; A/C/G/T probabilities renormalized by released scorer','Test_maize andtest_tomato; no task fitting. Gene/transcript filters differ by species; pretraining overlap not inferred from split name.','annotated junction',metrics=(('exact-match','Complete motif reconstruction; ambiguous groups excluded'),('accuracy','Additional per-token accuracy')) if isrec else ('auroc','ap'),embeddings=False)
            c.field('protocols',p,'split_rule',ev)
            for species in ['maize','tomato']:c.variant(t,t+'-'+species,species+' test cohort',card,context=species,length='8,192bp',revision=ZERO,notes='Exact counts taken from pinned card and selected Parquet inspections; not assumed identical across junctions.')
            c.count(t,maize_recovery if isrec else maize_core,'junctions',card,split='test_maize',qualifier='Reported in paper/card',variant=t+'-maize')
            c.use('plantcad2',t,ev,'plantcad2',protocol=p)
            c.use('evo2',t,recovery,'plantcad2','external-evaluation',note='Evo 2-7B forward/reverse-complement causal reconstruction compared; selected orientation varies by junction type. Not original Evo 2 usage.')
    sv=pe('deletions','sec2.4','Simulated Arabidopsis deletions; negative Delta logP boundary scores versus MSA63 genomephyloP/phastCons constraint proxies; not measured deleteriousness. Mainlabels 7662 conserved/10413 less conserved; flank scoring ablation saturates near 20 nt.')
    sv_code=c.code('plantcad2-sv-score',PC,'src/zero-shot-eval.py','def _sv_llr_boundary','Unmasked ref/mut nucleotide probabilities; negative mean log(mut/ref) at flanks around deletion boundaries. The CLI defaults to five flanking positions per side. This controls output-score averaging rather than truncating the encoder input; the paper flank-width experiment is separate.',end_needle='return scores')
    t='plantcad2-structural_variant_effect_prediction'
    c.task(t,'plantcad2-zero','Simulated deletion constraint','Arabidopsis simulated deletions / 63-genome MSA','High versus low conservation of deletion region','Predict alignment-derived constraint of a deleted region from its effect on flanking-base language-model scores.','binary classification','phyloP/phastCons conservation proxies',sv,applications=('plant-breeding','comparative-genomics'),capabilities=('variant-effects','sequence-modeling'),regions=('genome',),populations=('arabidopsis',),input='RefSeq, MutSeq, left/right deletion boundaries, label',output='Negative boundary log-likelihood ratio',limitations='Conservation proxy labels are not experimental deletion fitness. Exact thresholds and length sampling are not specified in main methods; retain FigureS5/S6 and released file distinctions.')
    p=c.protocol(t,t+'-boundary','Deletion-boundary score',sv_code,'zero-shot','Unmaskedreference/mutant per-base outputprobabilities','Test-only simulated deletion cohort; no genome/chromosome holdout specified. Alternative phyloP/phastCons label definitions are linked variants.','deletion',metrics=('ap','auroc'),embeddings=False,notes='Released sv_effect computes sklearn average_precision_score. Mainpaper describes AUPRC. Flanking default 5 nt; paper explores longer flanks.')
    c.variant(t,t+'-phyloP','Main phyloP labels',sv,notes='PaperTable 1:7662 conserved,10413 less conserved; do not assume all possible deletions included.')
    c.variant(t,t+'-phastCons','Alternative phastCons labels',sv,notes='FigureS6; exact matching released label/cohort not established.')
    for label,n in [('conserved',7662),('less-conserved',10413)]:c.count(t,n,'deletions',sv,split=label)
    c.use('plantcad2',t,sv,'plantcad2',protocol=p);c.use('evo2',t,sv,'plantcad2','external-evaluation',note='Evo 2-7B comparator in PlantCAD2 paper; no attribution to original Evo 2 paper.')
    potato=pe('potato','sec2.2','Potato SNP constraint labels from 95 Solanaceae-genome GERP:>1.5 conserved,<0 neutral. Solanaceae absent from PlantCAD2 pretraining. FigS3 stratifies CDS, upstream, downstream, intron, intergenic, TE.')
    t='plantcad2-potato-gerp'
    c.task(t,'plantcad2-zero','Potato Solanaceae conservation','Potato SNPs /95-genome Solanaceae GERP','GERP conserved versus neutral site','Paper-only lineage evaluation not found in the 12-config HF release. Labels use GERP rather than the Poaceae phyloP recipe.','binary classification','GERP>1.5 versusGERP<0; excludeintermediate',potato,applications=('plant-breeding','comparative-genomics'),capabilities=('evolutionary-inference','sequence-modeling'),regions=('genome',),populations=('potato',),input='PotatoSNP-centered sequence; exact artifact/context manifest pending',output='Reference-base conservation score',limitations='Sample counts, coordinate files and exact window procedure unverified. Family absence is a model-specific paper statement, not anID/OD policy assignment.')
    p=c.protocol(t,t+'-paper','Paper GERP site classification',potato,'zero-shot','Reference-base language-model score','Conservation label threshold filter; no supervised fitting. Source states Solanaceae excluded from pretraining; no automatic gene/chromosome exclusion inferred.','SNP site',metrics=('auroc',),embeddings=False)
    for slug,region in [('cds','cds'),('upstream','promoter'),('downstream','regulatory'),('intron','intron'),('intergenic','intergenic'),('te','repeat')]:
        v=c.variant(t,t+'-'+slug,'GERP '+slug+' subset',potato,notes='FigureS3 source-defined genomic-context stratum; count pending.')
        c.add('task_categories',task_id=t,category_id=region,relation='subset',rationale='Source Figure S3 stratifies this genomic context; task not restricted to this class.',evidence_id=potato,attribution='curatorial')
    c.use('plantcad2',t,potato,'plantcad2',protocol=p);c.use('evo2',t,potato,'plantcad2','external-evaluation',note='PaperFig 2E/FigS3 comparator; no HF task release established.')
    diagnostic=pe('mlm-diagnostic','sec2.1','Held-out pretraining test sequences:15%random-mask accuracy; central-mask context ablation 512→8192; repeated regions inflate MLM accuracy. Exact coordinate/split generation not established.')
    t='plantcad2-pretraining-mlm'
    c.task(t,'plantcad2-zero','Held-out masked-nucleotide prediction','PlantCAD2 pretraining test set','Masked nucleotide','Reconstruct held-out masked tokens; track random mask and central-token context protocols separately.','sequence reconstruction','Original nucleotide',diagnostic,applications=('model-development',),capabilities=('sequence-modeling',('long-context','measured','Source varies input context at fixed central-token target.')),regions=('gene','genome'),populations=('angiosperms',),input='Gene-centered genomic windows',output='Nucleotide identity',limitations='Source calls this held-out test; coordinate overlap across windows and chromosome/homolog separation not established. MLM accuracy is sensitive to repeat content.')
    for mode,split in [('random','15%random nucleotides masked in held-outsequences'),('central','Single central token;context512,1024,2048,4096,8192bp')]:
        p=c.protocol(t,t+'-'+mode,mode+' masking',diagnostic,'zero-shot','Masked-LM output probabilities',split+'; original pretraining train/validation/test assignment unresolved.','token / window',metrics=('accuracy',),embeddings=False);c.use('plantcad2',t,diagnostic,'plantcad2',protocol=p)
    leaderboard(c)


def leaderboard(c):
    api='plantcad2-zeroshot-leaderboard-api.json';repo='plantcad/plantcad2-zeroshot-leaderboard'
    c.source('plantcad2-leaderboard','PlantCAD2 zero-shot leaderboard',
             'https://huggingface.co/spaces/plantcad/plantcad2-zeroshot-leaderboard','leaderboard',
             json.loads((BASE/api).read_text())['sha'],
             'research/sources/plantcad/plantcad2-zeroshot-leaderboard-README.md',
             notes='Live Space; code and CSV evidence are pinned separately.')
    e=hf(c,'plantcad2-leaderboard-results',repo,'data/results.csv',api,'leaderboard-results.csv',
         'Pinned leaderboard stores 220 score rows across 20 species-specific entries and 11 model labels. Context length and selected Evo 2 orientation are per-result fields; this release includes comparators beyond the original journal tables.',basis='data',kind='spaces')
    tasks=hf(c,'plantcad2-leaderboard-tasks',repo,'data/tasks.csv',api,'leaderboard-tasks.csv',
         'Twenty leaderboard entries map to 12 released dataset/target configurations: eight maize/tomato reconstruction entries, eight core-membership entries, three conservation cohorts and one deletion cohort.',basis='data',kind='spaces')
    app=hf(c,'plantcad2-leaderboard-app',repo,'app.py',api,'plantcad2-zeroshot-leaderboard-app.py',
           'Overall ranking averages within-task percentile ranks. It is not a raw-score average; model contexts differ. Evo 2 rows retain a selected strand per task.',basis='code',kind='spaces')
    c.paper('plantcad2-leaderboard','PlantCAD2 zero-shot leaderboard: released results and task definitions','plantcad2-leaderboard',2026,
            status='official leaderboard data',scope='additional-evaluation-source',notes='Release source, distinct from the journal paper and its original comparator set. The catalogue links this leaderboard and records provenance; it does not reproduce an overall ranking.')
    rows=list(csv.DictReader(open(BASE/'leaderboard-results.csv')))
    ids={'cons_andropogoneae':'conservation_within_andropogoneae','cons_poaceae_nontis':'conservation_within_poaceae_non_tis','cons_poaceae_tis':'conservation_within_poaceae_tis','sv_impact_auprc':'structural_variant_effect_prediction'}
    for species in ['maize','tomato']:
        for key,motif in [('start_sites','tis'),('stop_sites','tts'),('donor','donor'),('acceptor','acceptor')]:ids[f'motif_{species}_{key}']=motif+'_recovery'
        for motif in ['tis','tts','donor','acceptor']:ids[f'coreclass_{species}_{motif}']=motif+'_core_noncore_classification'
    grouped=defaultdict(list)
    for row in rows:grouped[(row['model'],ids[row['task_id']])].append(row)
    for (label,config),values in grouped.items():
        model='evo2' if label.startswith('evo2') else 'carbon' if label=='Carbon-3B' else 'ntv3' if label.startswith('NTv3') else 'plantcad2' if label in ('PlantCAD2-S','PlantCAD2-M','PlantCAD2-L') else None
        if model:
            note='Leaderboard model '+label+'; '+ '; '.join(v['task_id']+': context '+v.get('context_bp','unknown')+' bp'+(', '+v['note'] if v.get('note') else '') for v in values)
            if model=='ntv3':note+='; historical 100M/650M checkpoints, not the later 703M N Tv 3 release.'
            c.use(model,'plantcad2-'+config,e,'plantcad2-leaderboard','external-evaluation' if model!='plantcad2' else 'original-release',note=note)
    c.finding(None,'The linked leaderboard has 20 species-specific entries corresponding to 12 dataset/target configurations. Its mean percentile ranking combines different contexts and selected Evo 2 orientations. PlantCAD2.5-L is labeled under development; that label does not establish a public model release.',app,suite='plantcad2-zero')


def supervised(c,pe,card):
    lora=pe('lora','sec9.3.9','LoRA rank 8, alpha 32, dropout 0.1; target x_proj/in_proj/out_proj; over 98% parameters frozen. One epoch, LR1e-4, global batch 128, BF16, linear schedule with 50 warmup steps; no hyperparameter tuning reported.')
    lora_code=c.code('plantcad2-lora-code',PC,'src/lora_fine_tune.py','def create_peft_model','Released PEFT configuration: rank 8, alpha 32, dropout 0.1, x_proj/in_proj/out_proj. Do not interpret the paper’s generic transformer-attention wording as the actual Mamba2 adapter placement.',end_needle='return get_peft_model')
    scoring=c.code('plantcad2-ft-metrics',PC,'src/lora_fine_tune.py','def compute_metrics_classification','Binary classification uses positive softmax scores; PR metric is sklearn average precision. Multilabel PR/AUROC use micro averaging; regression includes Spearman, Pearson, R2, MAE, MSE.',end_needle='def load_base_model')
    property(c,'plantcad2','lora','adaptation','Supervised adaptation','LoRA rank 8, alpha 32, dropout 0.1 in x_proj/in_proj/out_proj, plus task readout. One epoch, LR 1e-4, global batch 128; more than 98% of parameters frozen.',lora)
    c.field('model_properties','plantcad2-lora','value',lora_code)
    acr=pe('acr','sec2.6','600 bp ATAC peak-centered positives versus remaining genomic background; Arabidopsis chromosome validation and 10 test species; nine-species training holds out maize/barley. Cell-type task:92 maize outputs, held-outchr 10; context variants preserve corelabels.')
    expression=pe('expression','sec9.3.7','15 Andropogoneae species panel; validation Tripsacum zopilotense and Zea diploperennis; test 26 maize NAM genomes. TPM >1 expressed,≤1 not expressed; regression log 10 TPM. Inputs concatenate promoter/terminator windows.')
    translation=pe('translation','sec9.3.8','Arabidopsis and maize Ribo-seq filtered for rRNA and mapped to genomes; StringTie gene-level ribosome profiling abundance. log 10 abundance regression andTPM>1 binary labels, not direct protein quantitation.')
    crosspops=('arabidopsis','brachypodium','eutrema','soybean','barley','rice','common-bean','poplar','setaria-viridis','sorghum','maize')
    specs=[
      ('cross_species_acr_train_on_arabidopsis','Cross-species accessible chromatin: Arabidopsis training','ATAC peak versus genomic background','binary classification',acr,('regulatory',),crosspops,'600 bp',
       'Train on Arabidopsis; chromosome-held-out Arabidopsis validation, with ten other species as test cohorts. Exact validation chromosome names require artifact verification.','species; Arabidopsis chromosome','ap'),
      ('cross_species_acr_train_on_nine_species','Cross-species accessible chromatin: nine-species training','ATAC peak versus genomic background','binary classification',acr,('regulatory',),crosspops,'600 bp',
       'Train/validation on nine species; maize and barley reserved for testing. Species holdout applies to adaptation, not necessarily pretraining.','species','ap'),
      ('cell_type_specific_acr','Maize cell-type accessibility','Accessibility in 92 cell types','multilabel classification',acr,('regulatory',),('maize',),'600 bp',
       'Maize chromosome 10 test; remaining training/validation window allocation requires coordinate audit. All cell types are used during adaptation.','chromosome / genomic window','ap'),
      ('cross_species_leaf_on_off_expression','Leaf expression on/off','Leaf TPM >1 versus ≤1','binary classification',expression,('promoter','terminator'),('andropogoneae','maize'),'1,024 bp promoter +1,024 bp terminator',
       'Panel of 15 Andropogoneae species; Tripsacum zopilotense and Zea diploperennis held for validation, 26 maize NAM genomes for test. Homolog/orthogroup separation beyond species is not established.','species / NAM accession','auroc'),
      ('cross_species_leaf_absolute_expression','Leaf expression level','Leaf log10 TPM','regression',expression,('promoter','terminator'),('andropogoneae','maize'),'1,024 bp promoter +1,024 bp terminator',
       'Same 15-species panel, two validation species and 26 NAM test accessions as binary expression. Per-orthogroup correlations form a separate aggregation.','species / NAM accession','spearman'),
      ('cross_species_leaf_on_off_translation','Leaf translation on/off','Ribo-seq TPM >1 versus ≤1','binary classification',translation,('gene',),('arabidopsis','maize'),'500 bp upstream sequence; precise anchor not established',
       'Arabidopsis train/validation; maize cross-species test. The within-Arabidopsis partition is released but its biological split unit remains under audit.','species / gene','auroc'),
      ('cross_species_leaf_absolute_translation','Leaf translation abundance','Log10 Ribo-seq-derived abundance','regression',translation,('gene',),('arabidopsis','maize'),'500 bp upstream sequence; precise anchor not established',
       'Arabidopsis train/validation; maize test, with no homology separation established.','species / gene','spearman')]
    carddata=yaml.safe_load((BASE/'finetune-README.md').read_text().split('---',2)[1]);infos={x['config_name']:x for x in carddata['dataset_info']}
    by_split={'test_brachypodium_distachyon':'brachypodium','test_eutrema_salsugineum':'eutrema','test_glycine_max':'soybean','test_hordeum_vulgare':'barley','test_oryza_sativa':'rice','test_phaseolus_vulgaris':'common-bean','test_populus_trichocarpa':'poplar','test_setaria_viridis':'setaria-viridis','test_sorghum_bicolor':'sorghum','test_zea_mays':'maize'}
    for config,name,target,typ,ev,regions,pops,length,split,unit,metric in specs:
        t='plantcad2-ft-'+config
        c.task(t,'plantcad2-ft',name,FT+'/'+config,target,'Predict the stated functional target using task-specific LoRA adaptation; model size, context and species are linked variants.','multilabel classification' if config=='cell_type_specific_acr' else typ,
               'Experimental ATAC-seq, RNA-seq or ribosome profiling as defined by the target',ev,applications=('plant-breeding','regulatory-engineering') if 'translation' not in config else ('plant-breeding','rna-engineering'),
               capabilities=('functional-prediction','context-specific'),regions=regions,populations=pops,input=length+' DNA',output=target,limitations='Manifest counts do not imply all windows are unique or independent. Species and chromosome separation in adaptation does not establish pretraining exclusion; Ribo-seq is a translation proxy, not measured protein abundance.')
        aggregation='Micro-averaged across region×cell labels in released scorer; Table 2 also reports a mean across 92 cell types.' if config=='cell_type_specific_acr' else 'Per species; published cross-species summaries average species scores.'
        metrics=[(metric,aggregation)]
        if typ=='regression':metrics+=['pearson','r2','mae','mse']
        p=c.protocol(t,t+'-lora','PlantCAD2 LoRA prediction',lora_code,'parameter-efficient fine-tune','DNA → pooled sequence readout; task-specific LoRA/head',split,unit,metrics=metrics,embeddings=False,fitted='LoRA adapters and classification/regression readout',selection='One epoch without hyperparameter tuning reported; precise checkpoint selection requires run metadata.',notes='Frozen embedding extraction is not required as a separate interface; most backbone parameters remain frozen during LoRA. Classifiers and regressors have distinct losses.')
        c.field('protocols',p,'split_rule',ev);c.field('protocols',p,'metrics',scoring);c.use('plantcad2',t,ev,'plantcad2',protocol=p)
        for s in infos[config]['splits']:
            sid=s['name'];v=c.variant(t,t+'-'+sid,sid,card,revision=json.loads((BASE/'plantcad2-finetune-api.json').read_text())['sha'],context=by_split.get(sid),length=length,targets=92 if config=='cell_type_specific_acr' else None,target_unit='cell types' if config=='cell_type_specific_acr' else None)
            c.count(t,s['num_examples'],'rows',card,split=sid,qualifier='Pinned dataset-card count; not independently recounted unless a measured row is linked.',variant=v,protocol=p)
        if 'acr' in config:
            for context in [600,1600,2600,3600,4600]:c.variant(t,t+'-context-'+str(context),str(context)+' bp context',acr,length=str(context)+'bp',notes='600-bp target label retained; flanks extend model input. Exact experiment/config correspondence remains to be checked for Arabidopsis-only versus multispecies runs.')
        if config=='cross_species_leaf_absolute_expression':
            c.variant(t,t+'-orthogroup','Within-orthogroup NAM aggregation',pe('orthogroup','sec2.7','PaperFigureS14 computes within-orthogroup NAM expression correlations; these are lower than across-gene correlations.'),notes='Distinct aggregation of the same target, not a new assay or evidence of strong allelic prediction.')
        if config=='cross_species_acr_train_on_arabidopsis':
            for readout in ['linear','XGBoost']:
                ep=c.protocol(t,'plantcad2-evo-acr-'+readout,'Evo2 frozen '+readout+' probe',acr,'frozen probe','Last hidden-state embeddings; forward, reverse-complement or averaged orientation',split,unit,metrics=('ap',),embeddings=True,fitted=readout,notes='This is the PlantCAD2 paper comparator protocol; it does not imply Evo 2 LoRA or full fine-tuning.')
                c.use('evo2',t,acr,'plantcad2','external-evaluation',protocol=ep)
    c.finding('plantcad2-ft-cell_type_specific_acr','PaperTable 2 summarizes mean AUPRC across 92 cell types, while results prose and released scorer use micro-averaged precision-recall/average precision. These aggregations must remain distinct.',scoring,severity='discrepancy',suite='plantcad2-ft')
    # Journal results extend beyond the seven named HF configurations.
    extra=pe('extra-expression','sec2.7','Additional maximum-across-tissues expression target and Arabidopsis→maize expression-transfer experiment; neither has a matching named configuration in the seven-config HF release.')
    for slug,name,target,pops,regions,metric,split in [
      ('maximum-expression','Maximum expression across tissues','Maximum gene expression across tissues',('andropogoneae','maize'),('promoter','terminator'),'spearman','Same Andropogoneae/NAM transfer setting; exact labels, normalization and matching public file unresolved.'),
      ('arabidopsis-expression-transfer','Arabidopsis-to-maize leaf expression','Binary leaf expression status',('arabidopsis','maize'),('promoter','terminator'),'auroc','Separate Arabidopsis expression dataset trained within species and transferred to maize; chromosome/homology partition unresolved.')]:
        t='plantcad2-ft-'+slug
        c.task(t,'plantcad2-ft',name,'PlantCAD2 paper-only '+slug,target,'Additional supervised endpoint documented in journal results; not represented by a matching HF configuration.','regression' if metric=='spearman' else 'binary classification','Gene-expression assays',extra,applications=('plant-breeding','regulatory-engineering'),capabilities=('functional-prediction','context-specific'),regions=regions,populations=pops,input='Promoter/terminator DNA',output=target,limitations='Counts and released target files unresolved. Do not substitute the leaf-absolute-expression label column for a maximum-expression target.')
        p=c.protocol(t,t+'-paper','Paper LoRA endpoint',extra,'parameter-efficient fine-tune','DNA → LoRA-adapted sequence readout',split,'species / gene',metrics=(metric,),embeddings=False,fitted='LoRA and task readout');c.use('plantcad2',t,extra,'plantcad2',protocol=p)


def genecad(c):
    paper_url='https://pmc.ncbi.nlm.nih.gov/articles/PMC12637538/'
    c.source('genecad-paper','GeneCAD preprint v2',paper_url,'paper','2025-11-12; bioRxiv v2',
             'research/papers/genecad.txt',notes='Full text retrieved through NCBI BioC. This version describes five-species training and a frozen encoder; the 2026 release is independently documented.')
    c.paper('genecad','GeneCAD: Plant Genome Annotation with a DNA Foundation Model','genecad-paper',2025,
            status='preprint v2',scope='additional-evaluation-source',doi='10.1101/2025.10.31.685877',date='2025-11-12',notes='GeneCAD is treated as a downstream PlantCAD2 annotation adaptation, not a separate primary foundation model.')
    older=c.ev('genecad-paper-methods','genecad-paper','Materials and Methods: Independent Test Set; Model Architecture; Training; Performance Evaluation Metrics',
               'Five training references: Arabidopsis, soybean, barley, rice, poplar. Five primary test species: walnut, coffee, common bean, N. sylvestris, N. tabacum; maize separate. Frozen PlantCAD2 + projected states/token embeddings +8-layer ModernBERT +BILOU head +chromosome CRF; ReelProtein filter. Full annotation and custom CDS exact matching.')
    released=revision(c,'overview','README.md','2026 revision: eight training species; U/B/M/R conditions, seeds 11/22/33; defaultMseed 11. Backbone emarro/pcad2-200M-cnet-baseline at 5574ff5d; 1,753 steps, effective batch 384, LR2e-4. Distinct from the 2025 frozen-backbone paper.')
    training=revision(c,'training-inputs','training_inputs/README.md','Release explicitly says backbone not frozen; 671,523 training and 14,317 validation windows. Athaliana, Osativa, Taestivum contribute validation. Genome/annotation checksums and gene-selection lists available.')
    species=revision(c,'species','training_inputs/eight_species.yaml','All eight species used in training. Arabidopsis, rice, wheat also provide validation windows; soybean, barley, poplar, Aquilegia, Nymphaea training only.',basis='data')
    split_code=c.code('genecad-split',GC,'scripts/sample.py','def generate_training_splits','Release splits window indices randomly within each species/chromosome using a seeded permutation. It does not hold out whole chromosomes for validation.',end_needle='splits = []')
    files=revision(c,'predictions','benchmark_predictions/README.md','Eight held-out angiosperms plus maize; six distant genomes(two bryophytes, four green algae); one vertebrate model case. CDS-only default/strict gffcompare metrics, predictions and model versions released. References are not redistributed.')
    manifest=revision(c,'prediction-manifest','benchmark_predictions/files.tsv','Prediction-file manifest: per-file species, model, uncompressed SHA256 and genes_scored. These are prediction counts, not reference-gene counts.',basis='data')
    evaluator=revision(c,'evaluator','analysis/evaluation/evaluate.py','Pinned gffcompare 0.12.10; default and strict(--strict-match -e 0) modes; no-R/-Q denominator restrictions. Levels Base, Exon, Intron, Intronchain, Transcript, Locus. F1 derived from sensitivity andprecision.',basis='code')
    convert=revision(c,'cds-conversion','analysis/evaluation/cds_to_gtf.py','Both reference and prediction converted to CDS-onlyGTF: CDS segments become exons; stop codon extension when present; organelles removed; identical CDS chains within gene collapsed. UTRs ignored; phase is not evaluated by the gffcompare input conversion.',basis='code')
    metrics=revision(c,'metrics','analysis/source_data/06_metrics/revision_cds_metrics.tsv','Released table has species×model×mode×level sensitivity, precision, F1 for revised coding-only benchmark.',basis='data')
    distant=revision(c,'distant-metrics','analysis/source_data/06_metrics/distant_cds_metrics.tsv','Six distant-genome coding-only annotation evaluations: Physcomitrium, Marchantia, Klebsormidium, Chlamydomonas, Bathycoccus, Ostreococcus.',basis='data')
    animal=revision(c,'animal-metrics','benchmark_predictions/vertebrate/Cjacchus/GeneCAD_animal.gffcompare_metrics.tsv','Experimental vertebrate backbone/model evaluated on marmoset; 48,403 reference coding transcripts and 76,515 query transcripts; default and strict scores. This is not the plant-trained checkpoint.',basis='data')
    c.suite('genecad','GeneCAD genome annotation','PlantCAD2 downstream annotation adaptation: historical full-annotation evaluation and revised CDS-only, boundary and completeness evaluations.',released,'genecad','genecad-release-overview',notes='GeneCAD is not counted as a separate primary foundation model. Keep frozen 2025 versus unfrozen 2026 backbones, species cohorts, decoding, optional protein filtering and scoring definitions separate.')
    property(c,'plantcad2','genecad-legacy','adaptation','GeneCAD: 2025 paper','Frozen PlantCAD2 Small/Large encoder; projected contextual states plus token embeddings; trained eight-layer ModernBERT head and 17-class BILOU output; chromosome-wide CRF and protein plausibility filtering.',older,variant='GeneCAD preprint v2')
    property(c,'plantcad2','genecad-release','adaptation','GeneCAD: 2026 release','Full adaptation of emarro/pcad2-200M-cnet-baseline at pinned revision 5574ff5d: backbone not frozen, eight-layer head, 256-dimensional token embedding, 8,192-bp windows. 1,753 updates, effective batch 384, LR 2e-4 cosine schedule.',training,variant='GeneCAD revised M / seed11')
    property(c,'plantcad2','genecad-splits','adaptation','GeneCAD training and validation','Eight training species; random window split within configured chromosomes. Arabidopsis, rice and wheat provide validation windows. 671,523 training and 14,317 validation windows reported; held-out species evaluated separately.',training,variant='GeneCAD 2026 revision',notes='Overlapping neighboring windows need not be independent. Source code does not establish chromosome-held-out validation.')
    c.field('model_properties','plantcad2-genecad-splits','value',split_code)
    trainpops=('arabidopsis','rice','soybean','barley','poplar','aquilegia','nymphaea','wheat')
    mainpops=('walnut','coffee','common-bean','nicotiana-sylvestris','nicotiana-tabacum','oil-palm','tripterygium','artichoke','maize')
    distantpops=('physcomitrium','marchantia','klebsormidium','chlamydomonas','bathycoccus','ostreococcus')
    # The current coding-only scorer has six distinct reference targets.
    for slug,level,typ,target in [
      ('base','Base','token-level binary annotation','Coding nucleotide versus background'),
      ('exon','Exon','interval prediction','Coding segment boundaries'),
      ('intron','Intron','interval prediction','Introns between coding segments'),
      ('chain','Intron chain','structured prediction','Coding intron chain'),
      ('transcript','Transcript','structured prediction','Coding transcript chain and endpoints'),
      ('locus','Locus','structured prediction','Coding locus recovery')]:
        t='genecad-cds-'+slug
        regions=('cds','intron') if slug in ('intron','chain') else ('cds',)
        c.task(t,'genecad','Coding-only annotation: '+level,'GeneCAD revision / CDS-normalized reference annotations',target,
               'Evaluate the named gffcompare level after converting both prediction and reference to CDS-only GTF. Coding segments are treated as exons; UTR sequence is excluded from this scorer.',typ,'Reference coding annotations after shared normalization',convert,
               applications=('genome-annotation','comparative-genomics','plant-breeding'),capabilities=('dense-annotation',('long-context','input-demand','Windowed encoder with chromosome-scale structured decoding; does not give the encoder whole-chromosome attention.')),regions=regions,
               populations=mainpops+distantpops+(('marmoset','sequence-origin','One experimental vertebrate-model case; uses its own vertebrate backbone and does not establish plant-checkpoint transfer.'),),
               input='Genome assembly; PlantCAD2 windows → annotation head → structured decoding',output=target,status='artifact-audited',limitations='Released predictions, manifests, scoring code and metric tables inspected; reference genomes and annotations not downloaded/re-scored. Default gffcompare matching and strict matching differ. CDS-only matching does not validate UTRs or coding phase.')
        for mode in ['default','strict']:
            p=c.protocol(t,t+'-'+mode,'GeneCAD revision / '+mode+' gffcompare',evaluator,'full fine-tune','PlantCAD2-family backbone + ModernBERT/structured annotation pipeline; GFF3 → CDS-only GTF',
                         'Eight training species; random windows within species/chromosome for validation; eight held-out angiosperms plus separately reported maize. Six distant plant genomes and one vertebrate-model case are additional test variants.','species / chromosome-wide annotation',
                         metrics=(('f1','Per species/model '+level+' level; source table reports percentage values'),('precision','Per species'),('recall','Per species')),embeddings=False,
                         fitted='Backbone, token embedding and annotation head; structured decoding and gene-selection variants documented separately',
                         selection='M/B/U/R models have matched windows, initialization and 1,753 steps; seeds 11/22/33. Independent test species. No generic test-score checkpoint selection inferred.',notes='Strict uses --strict-match -e 0; default uses gffcompare defaults. No -R/-Q means unmatched references/predictions remain in denominators. Vertebrate-model training corpus is not established by this plant training recipe.')
            for e in (training,split_code,convert):c.field('protocols',p,'split_rule' if e==split_code else 'model_interface',e)
            c.use('plantcad2',t,released,'genecad','original-release',protocol=p,note='GeneCAD downstream adaptation in the PlantCAD family. Current release uses an unfrozen 200M backbone, distinct from legacy 88M/676M PlantCAD2 encoders.')
        for condition in ['U','B','M','R']:
            c.variant(t,t+'-'+condition,'Training condition '+condition,released,context='Unfiltered/basicQC/MMLR/random-retention conditions',length='8,192bp',notes='Seeds 11,22,33; matched windows and initial weights. Conditions modify annotation supervision, not the evaluation target.')
        for slugv,label,pops,ev in [('angiosperms','Eight held-out angiosperms and maize',mainpops,files),('distant','Two bryophytes and four green algae',distantpops,distant),('vertebrate','Experimental marmoset model',('marmoset',),animal)]:
            v=c.variant(t,t+'-'+slugv,label,ev,context=', '.join(pops),revision=json.loads((BASE/'genecad-revision-api.json').read_text())['sha'],notes='Separate model/cohort context; not a single shared training distribution.')
            if slugv=='vertebrate':
                c.count(t,48403,'reference coding transcripts',animal,split='reference',variant=v)
                c.count(t,76515,'predicted coding transcripts',animal,split='prediction',variant=v)
        for split,n in [('train',671523),('validation',14317)]:c.count(t,n,'overlapping windows',training,split=split,qualifier='Release-reported shared training windows; repeated across endpoint records, not additive.')
        c.field('tasks',t,'target',metrics)
    # Historical whole-annotation endpoints must not be overwritten with CDS-only metrics.
    legacy_pops=('walnut','coffee','common-bean','nicotiana-sylvestris','nicotiana-tabacum','maize')
    for slug,target,regions,typ in [('nucleotide','Per-base gene-feature class',('cds','intron','utr5','utr3','intergenic'),'token-level multiclass annotation'),('exon','Full exon boundaries',('exon','utr5','utr3'),'interval prediction'),('cds','Complete coding structure including phase',('cds','splice'),'structured prediction'),('transcript','Full transcript structure',('gene','exon','utr5','utr3'),'structured prediction')]:
        t='genecad-legacy-'+slug
        c.task(t,'genecad','2025 paper annotation: '+target,'GeneCAD preprint v2 / full reference annotations',target,
               'Historical paper endpoint based on complete reference annotations, evaluated separately from the revised coding-only benchmark.',typ,'Public reference GFF3 annotations',older,
               applications=('genome-annotation','comparative-genomics','plant-breeding'),capabilities=('dense-annotation',),regions=regions,populations=legacy_pops,input='8,192 bp windows,4,096 bp inference stride, frozen PlantCAD2 representations',output=target,
               limitations='Paper-audited historical protocol. Paper says exact transcript/exon matching and a phase-aware custom CDS evaluator; current coding-only gffcompare results are not substituted. Per-species reference counts unresolved.')
        p=c.protocol(t,t+'-frozen','GeneCAD 2025 frozen-backbone annotation',older,'frozen backbone; trained annotation head','Frozen PlantCAD2 → projection/token embeddings → ModernBERT/BILOU → chromosome CRF',
                     'Five training references: Arabidopsis, soybean, barley, rice, poplar. Five primary held-out species; maize separately because comparator training exposures differ. Validation windows/coordinates not fully specified in paper.','species / genome',metrics=('f1','precision','recall'),embeddings=True,
                     fitted='Projection, token embedding and ModernBERT/MLP annotation head; fixed CRF transitions estimated from Arabidopsis/rice',notes='17BILOU/O classes; optional protein plausibility filter uses per-species validation-selected threshold. Do not treat that threshold as a prespecified zero-shot setting.')
        c.use('plantcad2',t,older,'genecad',protocol=p,note='GeneCAD is represented as an annotation adaptation, not a new foundation model; legacy backbone frozen.')
    structure=revision(c,'structure-code','analysis/evaluation/structure_eval.py','Boundary sets are extracted from CDS-only chains; exact coordinate/strand set intersections yield precision, recall, F1 forstart, stop, donor, acceptor. Not full transcript start/end prediction.',basis='code')
    for slug,region,name in [('start','translation-start','Translation initiation'),('stop','translation-stop','Translation termination'),('donor','splice','Splice donor'),('acceptor','splice','Splice acceptor')]:
        t='genecad-boundary-'+slug
        c.task(t,'genecad',name+' boundary detection','GeneCAD revision / coding-chain boundaries',name+' coordinate and strand','Find the named coding-boundary positions from a genome annotation and compare exact position/strand sets. This tests site localization, unlike the known-site motif-recovery tasks.','boundary detection','Boundaries derived from reference coding chains',structure,applications=('genome-annotation','plant-breeding'),capabilities=('dense-annotation',),regions=(region,),populations=mainpops,input='Whole-genome GeneCAD coding predictions',output='Boundary coordinate/strand set',status='artifact-audited',limitations='Evaluator and released summary table inspected; not independently re-scored from reference genomes. Target excludes transcription start/stop and UTR boundaries.')
        p=c.protocol(t,t+'-sets','Exact coding-boundary set comparison',structure,'full fine-tune','GeneCAD annotation pipeline → coding boundary sets','Eight adaptation training species; held-out angiosperm genomes and separately reported maize; random-window validation as in released training recipe.','species / genomic position',metrics=('f1','precision','recall'),embeddings=False,fitted='Released GeneCAD adaptation');c.use('plantcad2',t,released,'genecad','original-release',protocol=p)
    busco=revision(c,'structure-metrics','analysis/source_data/06_metrics/revision_structure_busco_metrics.tsv','Source table reports BUSCO complete, single-copy, duplicated, fragmented, missing percentages and lineage size alongside boundary and ORF statistics.',basis='data')
    t='genecad-busco'
    c.task(t,'genecad','Predicted proteome BUSCO completeness','GeneCAD revision predicted coding products / embryophyta_odb 10','Recovery of expected lineage orthologs','Assess ortholog completeness in predicted proteins; distinguish completeness from exact gene-coordinate accuracy.','ortholog completeness','BUSCO lineage ortholog set',busco,applications=('genome-annotation','comparative-genomics'),capabilities=('dense-annotation',),regions=('cds',),populations=mainpops,input='Proteins translated from predicted CDS',output='Complete/single/duplicated/fragmented/missing fractions',status='artifact-audited',limitations='Released statistics and lineage documentation inspected; BUSCO was not rerun. Completeness can remain high despite duplicate or incorrect gene models.')
    p=c.protocol(t,t+'-lineage','BUSCO predicted-proteome assessment',busco,'full fine-tune','GeneCAD output proteins → BUSCO embryophyta_odb10','Same held-out genome variants as revision; no additional fitted readout.','species / lineage ortholog',metrics=('busco-complete',),embeddings=False,fitted='Released GeneCAD adaptation; BUSCO uses existing lineage models');c.use('plantcad2',t,released,'genecad','original-release',protocol=p)
    c.finding(None,'GeneCAD 2025 preprint uses five species and frozen 88M/large PlantCAD2 encoders. The 2026 release uses eight species and explicitly updates a 200M PlantCAD2-family backbone. Its core benchmark is CDS-only with both default and strict gffcompare scoring; those scores must not be presented as full UTR/transcript annotation accuracy.',training,severity='version-difference',suite='genecad')
    # Preserve a compact manifest audit without copying genomes, model weights or predictions.
    rows=list(csv.DictReader(open(BASE/'genecad-revision-benchmark_predictions--files.tsv'),delimiter='\t'))
    c.finding(None,f'The inspected release manifest lists {len(rows)} prediction files with declared hashes and prediction counts. Reference annotations are linked to their original sources and are not redistributed. Declared hashes were not independently verified against every GFF file.',manifest,suite='genecad')


def artifacts(c):
    """Attach exact card counts and any successful, explicitly scoped Parquet inspections."""
    card=yaml.safe_load((BASE/(ZERO+'-README.md')).read_text().split('---',2)[1])
    for info in card['dataset_info']:
        t='plantcad2-'+info['config_name']
        for split in info['splits']:
            variant=t+'-'+split['name'].replace('test_','')
            if variant not in c.ids['variants']:variant=None
            c.count(t,split['num_examples'],'rows','plantcad2-zero-card-ev',split=split['name'],qualifier='Pinned card count; not a new independent cohort.',variant=variant)
    p=ROOT/'data/plantcad-artifact-inspections.json'
    if not p.exists():return
    inspections=json.loads(p.read_text())
    for i,row in enumerate(inspections):
        config,filename=row['path'].split('/',1);split=filename.split('-000')[0]
        t=('plantcad2-' if row['repo'].endswith(ZERO) else 'plantcad2-ft-')+config
        assert t in c.ids['tasks'],t
        sid='plantcad2-artifact-'+str(i);c.source(sid,row['repo']+'/'+row['path'],row['url'],'dataset-file',row['revision'],notes='HTTP-range inspection. Parquet footer SHA256='+row['footer_sha256']+'. This is not a whole-file hash. Label columns scanned fully; sequence lengths sampled only.')
        e=c.ev(sid+'-ev',sid,'Parquet footer, selected columns and four sequence samples',json.dumps({k:row[k] for k in ['rows','columns','label_counts','chr_counts','sequence_samples','continuous_label_summary','label_vector_lengths','label_transform_checks'] if k in row}),basis='data')
        variant=t+'-'+split.replace('test_','') if row['repo'].endswith(ZERO) else t+'-'+split
        if variant not in c.ids['variants']:
            variant=t+'-file-'+str(i);c.variant(t,variant,'Pinned '+split+' file inspection',e,revision=row['revision'],notes=row['path'])
        c.count(t,row['rows'],'file rows',e,split=split,qualifier='This individual file, not the summed split. Row count read from Parquet footer; no unique-locus claim.',method='measured',variant=variant)
        for label,n in (row.get('label_counts',{}).items() if len(row.get('label_counts',{}))<=10 else []):c.count(t,n,'file rows',e,split=split+'/label='+label,qualifier='Full scalar/serialized label column scan of this file.',method='measured',variant=variant)
        c.field('tasks',t,'input_description',e)
        if row.get('chr_counts') or row.get('label_vector_lengths'):
            for protocol in c.rows['protocols']:
                if protocol['task_id']==t:
                    c.field('protocols',protocol['id'],'split_rule',e)
        if row.get('label_vector_lengths'):
            c.field('tasks',t,'label_basis',e)
        if 'label_transform_checks' in row:
            for task in c.rows['tasks']:
                if task['id']!=t:continue
                if 'absolute_translation/' in row['path']:
                    task['target']='log10(1 + Ribo-seq TPM)'
                    task['output_description']='Released regression label: log10(1 + TPM)'
                    task['label_basis']='Ribosome profiling TPM; released label checked against log10(1 + TPM) over all rows.'
                    c.field('tasks',t,'target',e)
                else:
                    task['label_basis']='Ribosome profiling TPM >1; all inspected labels match the threshold.'
                c.field('tasks',t,'label_basis',e)
        for task in c.rows['tasks']:
            if task['id']==t:task['status']='artifact-audited'
    # Compare only fully inspected splits to card metadata; never treat partial files as complete cohorts.
    api=json.load(open(BASE/(ZERO+'-api.json')))
    files=[s['rfilename'] for s in api['siblings'] if s['rfilename'].endswith('.parquet')]
    groups=defaultdict(list)
    for path in files:groups[(path.split('/')[0],path.split('/')[1].split('-000')[0])].append(path)
    for (config,split),paths in groups.items():
        found=[r for r in inspections if r['repo'].endswith(ZERO) and r['path'] in paths]
        if len(found)!=len(paths):continue
        t='plantcad2-'+config;e='plantcad2-artifact-'+str(inspections.index(found[0]))+'-ev'
        count=c.count(t,sum(r['rows'] for r in found),'rows',e,split=split,qualifier='Summed Parquet footer counts across every pinned file in this split; file-level evidence in inspection manifest.',method='measured')
        for row in found:
            c.field('counts',count,'value','plantcad2-artifact-'+str(inspections.index(row))+'-ev')

    for config in ['cross_species_leaf_absolute_translation','cross_species_leaf_on_off_translation']:
        matching=[r for r in inspections if r['repo'].endswith(FT) and r['path'].startswith(config+'/')]
        if matching:
            e='plantcad2-artifact-'+str(inspections.index(matching[0]))+'-ev'
            c.finding('plantcad2-ft-'+config,'Inspected translation train and validation files both contain Arabidopsis chromosomes 1–5. This is not chromosome-held-out validation. The exact gene-selection rule remains unresolved; test contains maize chromosomes 1–10.',e,suite='plantcad2-ft')
            if 'absolute_translation' in config:
                c.finding('plantcad2-ft-'+config,'The paper describes log10-transformed translation abundance. Every released regression label in train, validation and test instead matches log10(1 + TPM), with maximum absolute error below 7e-15. The catalogue uses the released transformation and retains the paper statement separately.',e,severity='discrepancy',suite='plantcad2-ft')
