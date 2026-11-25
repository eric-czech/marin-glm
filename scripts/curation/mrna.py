from pathlib import Path

def populate(c):
    repo='morrislab/mRNABench';cat='mrna_bench/datasets/dataset_catalog.py'
    e=c.code('mrna-catalog',repo,cat,'DATASET_CATALOG','The pinned catalogue registers 23 dataset names; prediction target types and default split choices are declared separately.')
    c.suite('mrnabench','mRNABench','Mature transcript, reporter and UTR-variant tasks. Dataset version and target determine the prediction problem.',e,'mrna',notes='Current code catalogue and 2025 paper are different snapshots. Do not interpret the current 23 dataset names as 23 source papers or as the original paper’s full evaluation set.')
    split=c.code('mrna-homology',repo,'mrna_bench/data_splitter/homology_split.py','class HomologySplitter','Default homology splitter uses HomoloGene groups, nominal 70/15/15 partitions and gene grouping; actual size depends on groups.')
    probe=c.ev('mrna-paper-probe','mrna-paper','Appendix D, linear probing; Table 2','Mean token embeddings, chunking long transcripts, RidgeCV regression and logistic classification. Original paper reports Pearson R or micro-AUPRC over replicated splits.')
    records=[
      ('eclip-binding-k562','eclip_binding.py','RBP binding in K562','classification',('mrna',),'human','homology'),
      ('eclip-binding-hepg2','eclip_binding.py','RBP binding in HepG2','classification',('mrna',),'human','homology'),
      ('go-bp','go_bio_proc.py','Gene Ontology biological-process labels','multilabel classification',('mrna','cds'),'human','homology'),
      ('go-cc','go_cell_comp.py','Gene Ontology cellular-component labels','multilabel classification',('mrna','cds'),'human','homology'),
      ('go-mf','go_mol_func.py','Gene Ontology molecular-function labels','multilabel classification',('mrna','cds'),'human','homology'),
      ('rnahl-human','rna_hl_human.py','Human mRNA half-life','regression',('mrna',),'human','homology'),
      ('rnahl-mouse','rna_hl_mouse.py','Mouse mRNA half-life','regression',('mrna',),'mouse','homology'),
      ('rna-loc-fazal','rna_loc_fazal.py','Subcellular RNA localization','multilabel classification',('mrna',),'human','homology'),
      ('rna-lifecycle-ietswaart','rna_lifecycle_ietswaart.py','RNA-lifecycle compartment labels','multilabel classification',('mrna',),'human','homology'),
      ('prot-loc','prot_loc.py','Protein subcellular localization','multilabel classification',('mrna','cds'),'human','homology'),
      ('mirna-target','mirna_target.py','miRNA-target membership','classification',('mrna',),'human','homology'),
      ('mrl-sugimoto','mrl_sugimoto.py','Mean ribosome load','regression',('mrna',),'human','homology'),
      ('mrl-hl-lbkwk-hl','mrl_hl_lbkwk.py','Reporter in-cell half-life','regression',('mrna',),'synthetic','default'),
      ('mrl-hl-lbkwk-mrl','mrl_hl_lbkwk.py','Reporter ribosome load','regression',('mrna',),'synthetic','default'),
      ('mrl-sample-egfp','mrl_sample.py','EGFP reporter mean ribosome load','regression',('utr5','mrna'),'synthetic','default'),
      ('mrl-sample-mcherry','mrl_sample.py','mCherry reporter mean ribosome load','regression',('utr5','mrna'),'synthetic','default'),
      ('mrl-sample-designed','mrl_sample.py','Designed-UTR reporter mean ribosome load','regression',('utr5','mrna'),'synthetic','default'),
      ('mrl-sample-varying','mrl_sample.py','Variable-length-UTR mean ribosome load','regression',('utr5','mrna'),'synthetic','default'),
      ('translation-efficiency-human','translation_efficiency_human.py','Human translation efficiency','regression',('mrna',),'human','homology'),
      ('translation-efficiency-mouse','translation_efficiency_mouse.py','Mouse translation efficiency','regression',('mrna',),'mouse','homology'),
      ('utr-variants-bohn-utr5','utr_variants_bohn.py','5′-UTR functional variant class','classification',('utr5',),'human','default'),
      ('utr-variants-bohn-utr3','utr_variants_bohn.py','3′-UTR functional variant class','classification',('utr3',),'human','default'),
      ('vep-traitgym-complex','vep_traitgym.py','UTR complex-trait variant class','classification',('utr5','utr3'),'human','default'),
      ('vep-traitgym-mendelian','vep_traitgym.py','UTR Mendelian variant class','classification',('utr5','utr3'),'human','default'),
    ]
    root=Path(__file__).resolve().parents[2]/'research/sources/morrislab--mRNABench/mrna_bench/datasets'
    for slug,file,target,typ,regions,pop,split_type in records:
        source=(root/file).read_text()
        ev=c.code('mrna-'+slug+'-data',repo,'mrna_bench/datasets/'+file,'class ',target+' sequence construction/source dataset class; combine with the catalogue for task type and default split.')
        t='mrna-'+slug
        labels='Gene/protein functional annotation' if slug.startswith(('go-','prot-loc')) else 'Experimental measurements / processed assay labels'
        c.task(t,'mrnabench',target,'mRNABench / '+slug,target,'Predict '+target.lower()+' from the released mature transcript or reporter construct. Preserve target/condition variants and dataset version.',typ,labels,ev,applications=('rna-engineering','genome-annotation') if slug.startswith('go-') else ('rna-engineering',),capabilities=('variant-effects',) if 'variants' in slug or 'traitgym' in slug else ('functional-prediction',),regions=regions,populations=(pop,),input='Mature transcript or reporter RNA, with CDS/splice tracks where released',limitations='Source processing code is inspected, but processed dataset rows and final split sizes remain unaudited. Some raw-processing methods explicitly raise NotImplementedError.')
        c.field('tasks',t,'task_type',e)
        c.field('protocols',t+'-protocol','split_rule',split if split_type=='homology' else e)
        rule='HomoloGene-based gene groups, nominal 70/15/15 train/validation/test; keep homologous groups on one side. Verify mapping coverage and actual split output.' if split_type=='homology' else 'Use dataset-preserved split column/default source split; do not substitute the homology default used by other datasets.'
        c.protocol(t,t+'-protocol','mRNABench frozen readout',e,'frozen probe','Frozen token embeddings, pooled over sequence; chunking when needed',rule,'homology group / gene' if split_type=='homology' else 'source-defined construct / variant group',metrics=('pearson',) if typ=='regression' else ('auprc',),embeddings=True,fitted='Ridge regression' if typ=='regression' else 'Logistic / multioutput logistic regression',notes='Paper-level readout conventions are separate from the current code dataset registry. Repeated-seed results do not imply independent datasets.')
        c.field('protocols',t+'-protocol','fitted_component',probe)
        if slug=='mrl-sample-egfp':
            for cond in ('unmodified','pseudouridine','N1-methylpseudouridine'):
                c.variant(t,t+'-'+cond.lower(),cond+' EGFP condition',e,context='Nucleoside modification; same ribosome-load target, linked condition variant.')
        if slug.startswith('eclip'):
            c.variant(t,t+'-rbps','RBP-specific binary target columns',e,context='RBP identities are linked target variants; K562 and HepG2 are assay contexts, not different species.')
        if 'NotImplementedError' in source:
            c.finding(t,'The released class links processed data but its raw-processing method is not implemented. Processed availability does not establish reproducibility of source curation.',ev)
        # The old paper establishes Evo 2 use for these families, not every later addition.
        if slug.startswith(('eclip-','go-','rnahl-','rna-loc-','rna-lifecycle-','prot-loc','mrl-sugimoto','mrl-hl','mrl-sample')):
            c.use('evo2',t,probe,'mrna','external-evaluation',note='Original mRNABench paper family; dataset-version reconciliation with current code still required.')
    c.finding(None,'Current source catalogue contains 23 dataset names. This catalogue splits the paired reporter half-life/ribosome-load targets, yielding 24 task records; cell/RBP/condition columns remain variants.',e,suite='mrnabench')
