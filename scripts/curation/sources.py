def populate(c):
    sources = [
        ('evo-paper','Genome modelling and design across all domains of life with Evo 2','https://pmc.ncbi.nlm.nih.gov/articles/PMC13128491/','Nature 2026','evo2.txt'),
        ('evo-supp','Evo 2 supplementary methods','https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-026-10176-5/MediaObjects/41586_2026_10176_MOESM1_ESM.pdf','Nature 2026','evo2-supp.txt'),
        ('ceno-paper','CENO: A Genome-Scale World Model for Evolutionary Sequence Interpretation and Programmable Regulatory Design','https://cladeteam.github.io/ceno.github.io/assets/paper/CENO_Technical_Report_Version.pdf','Retrieved 2026-11-23','ceno.txt'),
        ('carbon-paper','Carbon: Decoding the Language of Life','https://huggingface.co/HuggingFaceBio/Carbon-3B/resolve/main/tech-report.pdf','Retrieved 2026-11-23','carbon.txt'),
        ('carbonx-card','Carbon-X official model card','https://huggingface.co/HuggingFaceBio/Carbon-X/blob/17de89165e25c49e7de4f845d0e5d464469de359/README.md','17de89165e25c49e7de4f845d0e5d464469de359','carbon-x-card.md'),
        ('generator-paper','GENERator: A Long-Context Generative Genomic Foundation Model','https://arxiv.org/html/2502.07272v5','arXiv v5','generator-v5.txt'),
        ('generator2-paper','GENERator-v2: Reconciling Coarse Tokenization with Single-Nucleotide Resolution in Genomic Language Modeling','https://www.biorxiv.org/content/10.64898/2026.01.27.702015v2.full','bioRxiv v2','generator2.txt'),
        ('botanic-paper','BOTANIC-1: a series of long-context plant genomic foundation models in the agentic era','https://huggingface.co/spaces/living-models/botanic1-report/resolve/main/botanic1-report-v3.pdf','Report v3','botanic1-v3.txt'),
        ('ntv3-paper','A multispecies foundation model for genome function prediction, gene annotation and sequence design','https://pmc.ncbi.nlm.nih.gov/articles/PMC13733737/','bioRxiv v2','ntv3-v2.txt'),
        ('deepd-paper','DeepD enables efficient genome modeling and controllable long-context sequence generation across domains of life','https://www.biorxiv.org/content/10.64898/2026.10.13.758170v1.full','bioRxiv v1','deepd.txt'),
        ('gpn-paper','Predicting genome-wide functional constraints with GPN-Star','https://www.nature.com/articles/s41586-026-11005-5','Nature 2026','gpnstar.txt'),
        ('gpn-supp','GPN-Star supplementary information','https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-026-11005-5/MediaObjects/41586_2026_11005_MOESM1_ESM.pdf','Nature 2026','gpnstar-supp.txt'),
        ('loam-paper','LOAM: A family of genomic language models trained on long-read soil metagenomes','https://doi.org/10.64898/2026.09.28.755120','bioRxiv 2026',None),
        ('dart-paper','DART-Eval: A Comprehensive DNA Language Model Evaluation Benchmark on Regulatory DNA','https://arxiv.org/html/2412.05430v1','arXiv v1','dart.txt'),
        ('traitgym-paper','Benchmarking DNA Sequence Models for Causal Regulatory Variant Prediction in Human Genetics','https://www.biorxiv.org/content/10.1101/2025.02.11.637758v2','bioRxiv v2',None),
        ('bend-paper','BEND 2.0: Benchmarking the Capabilities Needed to Design DNA','https://arxiv.org/html/2611.03806v1','arXiv v1','bend2.txt'),
        ('bgc-paper','Data-Scarce, Multi-Granular, Multimodal: Benchmark Design for Biosynthetic Gene Clusters','https://arxiv.org/html/2611.02275v2','arXiv v2','bgcbench.txt'),
        ('bgcs-paper','Benchmarking long-context genome language models on biosynthetic gene clusters','https://www.biorxiv.org/content/10.64898/2026.05.12.724296v1.full','bioRxiv v1','bgcsbench.txt'),
        ('mrna-paper','mRNABench: A curated benchmark for mature mRNA property and function prediction','https://pmc.ncbi.nlm.nih.gov/articles/PMC12265608/','bioRxiv 2025; current code separately pinned','mrnabench.txt'),
        ('rna-paper','RNAGym: Large-scale Benchmarks for RNA Fitness and Structure Prediction','https://www.biorxiv.org/content/10.1101/2025.06.16.660049v1','bioRxiv v1',None),
        ('na-paper','NABench: Large-Scale Benchmarks of Nucleotide Foundation Models for Fitness Prediction','https://arxiv.org/html/2511.02888v1','arXiv v1','nabench.txt'),
        ('guanine-paper','GUANinE v1.1 reveals complementarity of supervised and genomic language models','https://academic.oup.com/bioinformatics/article/42/Supplement_2/btag427/8767277','Bioinformatics 2026',None),
        ('geneb-paper','GENEB: Why Genomic Models Are Hard to Compare','https://arxiv.org/html/2606.04525v1','arXiv v1','geneb.txt'),
        ('lambda-paper','LAMBDA: a prophage detection benchmark for genomic language models','https://academic.oup.com/nargab/article/8/3/lqag103/8787816','NAR Genomics and Bioinformatics 2026',None),
        ('dgeb-paper','Diverse Genomic Embedding Benchmark for functional evaluation across the tree of life','https://www.biorxiv.org/content/10.1101/2024.07.10.602933v1','bioRxiv v1',None),
        ('gb-paper','Genomic benchmarks: a collection of datasets for genomic sequence classification','https://doi.org/10.1186/s12863-023-01123-8','BMC Genomic Data 2023',None),
        ('pgb-paper','A foundational large language model for edible plant genomes','https://doi.org/10.1038/s42003-024-06465-2','Communications Biology 2024','pgb.txt'),
        ('alphagenome-paper','AlphaGenome paper','https://storage.googleapis.com/deepmind-media/papers/alphagenome.pdf','Author-hosted paper',None),
        ('alphagenome2-paper','AlphaGenome 2 paper','https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphagenome-2-deciphering-how-cells-read-dna-to-better-understand-disease/alphagenome-2.pdf','November 2026 preprint',None),
        ('genosm-paper','Genos-m: a foundation model for human-associated microbial genomes','https://www.biorxiv.org/content/10.64898/2026.05.21.726868v1.full','bioRxiv v1','genosm.txt'),
        ('cerberus-paper','Cerberus: bidirectional state space blocks improve accuracy and efficiency of regulatory sequence models','https://www.biorxiv.org/content/10.64898/2026.10.02.756377v1','bioRxiv v1',None),
    ]
    primary = {'evo-paper','ceno-paper','carbon-paper','carbonx-card','generator-paper','generator2-paper','botanic-paper','ntv3-paper','deepd-paper','gpn-paper','genosm-paper'}
    supplemental = {'alphagenome-paper','alphagenome2-paper','cerberus-paper','loam-paper'}
    for id, title, url, version, local in sources:
        c.source(id, title, url, 'documentation' if id=='carbonx-card' else 'paper', version,
                 'research/papers/'+local if local else None)
        if id.endswith('supp'):
            continue
        year = 2026
        if id in ('dart-paper','dgeb-paper','pgb-paper'): year=2024
        if id in ('mrna-paper','rna-paper','na-paper','traitgym-paper'): year=2025
        if id=='gb-paper': year=2023
        c.paper(id.replace('-paper','').replace('-card',''), title, id, year,
                'documentation' if id=='carbonx-card' else ('journal' if id in ('evo-paper','gpn-paper','guanine-paper','lambda-paper','gb-paper','pgb-paper') else 'preprint/report'),
                'primary-model' if id in primary else ('additional-evaluation-source' if id in supplemental else 'benchmark'),
                notes='Paper/report version and code/data versions are separate catalogue records.')
    models = [
        ('evo2','Evo 2','evo','Genome-wide autoregressive sequence model; paper and external evaluations are tracked separately.'),
        ('ceno','CENO','ceno','Sequence likelihoods, representations, alignment-conditioned prediction and regulatory design.'),
        ('carbon','Carbon','carbon','Autoregressive genomic model with development diagnostics and variant evaluations.'),
        ('carbonx','Carbon-X','carbonx','DNA/text model with question-answering and variant benchmarks; evidence currently comes from official documentation.'),
        ('generator','GENERator','generator','Original GENERator model family; do not merge its paper with GENERator-v2.'),
        ('generator2','GENERator-v2','generator2','Separate model family using factorized nucleotide supervision and genome-compression pretraining.'),
        ('botanic1','BOTANIC-1','botanic','Plant sequence model evaluated by frozen probes, variants and regulatory tasks.'),
        ('ntv3','NTv3','ntv3','Pretrained and functionally post-trained checkpoints; annotation models and adaptation protocols are distinct.'),
        ('deepd','DeepD','deepd','Phylogeny-conditioned mixture-of-experts sequence model with likelihood, representation and generation evaluations.'),
        ('gpnstar','GPN-Star','gpn','Alignment- and species-tree-conditioned model; evolutionary timescale is a model/input variant.'),
        ('loam','LOAM','loam','Microbial sequence model; evaluation source for BacBench, DGEB EC and RNAGym subsets.'),
        ('alphagenome','AlphaGenome','alphagenome','Supervised sequence-to-function model included as an additional evaluation source.'),
        ('alphagenome2','AlphaGenome 2','alphagenome2','Cell-state-conditioned sequence-to-function model included as an additional evaluation source.'),
        ('genosm','Genos-m','genosm','Autoregressive microbial MoE model; frozen representations, RNAfitness scoring, strain phenotypes and microbiome applications.'),
        ('cerberus','Cerberus','cerberus','Supervised regulatory sequence model included as an additional evaluation source.'),
    ]
    for id, name, paper, description in models:
        source = next(p['source_id'] for p in c.rows['papers'] if p['id']==paper)
        ev = c.ev('model-'+id, source, 'Model description / methods', description,
                  'documentation' if id=='carbonx' else 'paper')
        c.add('models', id=id, name=name, scope='primary' if id not in ('loam','alphagenome','alphagenome2','cerberus') else 'evaluation-source',
              paper_id=paper, description=description, evidence_id=ev, notes=None)
