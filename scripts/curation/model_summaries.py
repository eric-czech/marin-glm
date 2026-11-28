"""Short, field-cited model descriptions for the Models comparison table."""
from common import Catalogue


def populate(d):
    c = Catalogue(d)
    d['model_summaries'] = []
    d['field_evidence'] = [r for r in d['field_evidence'] if r['entity_table'] != 'model_summaries']
    # These complete-text sources are already in the catalogue. New evidence
    # locators record the passages inspected for the table, not model-name inference.
    additions = [
        ('summary-ceno-methods', 'ceno-paper', 'Methods 4.1–4.2, pp.23–24; Supplementary Table S1',
         'Hybrid causal Mamba-2/attention/MoE models at 300M,600M,1B total parameters (100M,200M,400M active); byte-level 512-entry DNA tokenizer. OpenGenome2 stage-specific mixtures. Context training at 8192,131072,1048576 tokens; 500B additional tokens for each long-context stage.'),
        ('summary-generator-methods', 'generator-paper', 'Abstract; model architecture and pretraining methods; Figure 1',
         'Decoder-only Transformer in approximately 1B/3B model sizes; nonoverlapping DNA 6-mer tokens. Pretraining uses 386 billion eukaryotic RefSeq nucleotides in annotation-derived gene-centric functional regions. Supported DNA context is approximately 98k nucleotides.'),
        ('summary-generator2-methods', 'generator2-paper', 'Sections 4.2–4.4; Table 1',
         'Approximately 1B/3B eukaryotic and prokaryotic variants share the original Transformer decoder, nonoverlapping 6-mer tokenization and 98k-bp context. Eukaryotic data use RefSeq with genome compression pretraining; prokaryotic data combine RefSeq and GTDB. All use factorized nucleotide supervision.'),
        ('summary-deepd-methods', 'deepd-paper', 'Abstract; Results: model design and training; Figure 1',
         'Phylogeny-conditioned sparse mixture-of-experts models operate at single-nucleotide resolution, using mixed sliding-window and full attention. Model sizes 1.8B and63B; large corpus approximately5.90T nucleotide sequence across eukaryotes,archaea,bacteria and viruses. Context curriculum 8K,32K,128K,512K,1M tokens.'),
        ('summary-gpnstar-methods', 'gpn-paper', 'Model architecture; Supplementary Methods: Training data, Inference; Supplementary Table 10',
         'Encoder-only masked model with sequence self-attention and phylogeny-informed cross-attention over whole-genome alignments and species trees. Sizes25M,85M,200M. Nucleotides are represented at aligned positions. Human vertebrate and four nonhuman models use128-bp windows; human mammal/primate and Arabidopsis use256-bp windows. Training oversamples conserved alignment windows.'),
    ]
    for eid, source, locator, statement in additions:
        c.evidence(eid, source, locator, statement)
        c.get('evidence', eid)['inspected'] = '2026-11-28'
    c.source('summary-ag1-encoding', 'AlphaGenome official nucleotide encoder',
        'https://github.com/google-deepmind/alphagenome_research/blob/3eecf48e58d7babbbc53525a8a0cf29a179e20a6/src/alphagenome_research/model/one_hot_encoder.py#L21-L54',
        'code', version='3eecf48e58d7babbbc53525a8a0cf29a179e20a6')
    c.get('sources', 'summary-ag1-encoding')['retrieved'] = '2026-11-28'
    c.evidence('summary-ag1-encoding', 'summary-ag1-encoding', 'DNAOneHotEncoder; dna_model.py lines 668 and 810–814',
        'Official AlphaGenome inference converts each A/C/G/T nucleotide to four-channel one-hot input; other characters map to zeros. DNAOneHotEncoder is invoked before the model prediction call.', 'code')
    c.get('evidence', 'summary-ag1-encoding')['inspected'] = '2026-11-28'
    evidence = {r['id'] for r in d['evidence']}

    def row(id, architecture, tokenization, training_data, context, refs):
        c.put('model_summaries', dict(id=id, architecture=architecture, tokenization=tokenization,
                                    training_data=training_data, context=context))
        if isinstance(refs, str):refs = [refs] * 4
        for field, sources in zip(['architecture', 'tokenization', 'training_data', 'context'], refs):
            for eid in sources.split():
                assert eid in evidence, eid
                c.field('model_summaries', id, field, eid)

    row('evo1', '7B StripedHyena: Hyena + attention', 'Single-base bytes',
        'OpenGenome: 300B nt; bacteria, archaea, phages and plasmids.',
        'Training: 8,192 → 131,072 bp.',
        ['evo1-architecture', 'evo1-architecture', 'evo1-training', 'evo1-training evo1-essentiality'])
    row('evo2', '1B / 7B / 40B StripedHyena 2', 'Single-base bytes',
        'OpenGenome2: 8.84T nt across domains of life.',
        '7B/40B training extended to 1,048,576 bp.',
        ['evo2-review-architecture', 'evo2-review-tokenization', 'evo2-review-corpus', 'evo2-review-training'])
    row('ceno', '0.3–1B hybrid Mamba-2 / attention / MoE', 'Byte-level DNA',
        'OpenGenome2; mixtures change by training stage.',
        'Training: 8,192 → 131,072 → 1,048,576 tokens.', 'summary-ceno-methods')
    row('carbon', '3B / 8B causal Transformer', 'DNA 6-mers; text BPE vocabulary',
        'Eukaryotic DNA, mRNA/splice sequences and prokaryotes.',
        'Training: 196,608 bp. Inference: 393,216–786,432 bp; see variant limits.', 'carbon-final-model-details')
    row('carbonx', '14.8B Qwen3-derived causal Transformer', 'DNA 6-mers + text BPE',
        'Qwen3 initialization; DNA, biology/general text and instruction mid-training.',
        'Mid-training: 8,192 tokens. Advertised limit: 40,960 tokens.', 'carbonx-final-model-details')
    row('generator', '~1B / 3B causal Transformer', 'Nonoverlapping DNA 6-mers',
        '386B nt of gene-centered eukaryotic RefSeq DNA.',
        'Supported context: ~98k bp.', 'summary-generator-methods')
    row('generator2', '~1B / 3B causal Transformer', 'Nonoverlapping DNA 6-mers',
        'Eukaryotes: RefSeq with genome compression. Prokaryotes: RefSeq + GTDB.',
        'Supported context: ~98k bp.', 'summary-generator2-methods')
    row('botanic1', '0.318–3.2B bidirectional Mamba-2', 'Single-nucleotide tokens',
        'Annotated land plants; 320 species supply filtered training windows.',
        'Base: 8,192 tokens. Separate curriculum: 131,072. Extrapolation tested to 1M bp.', 'botanic-final-model-details')
    row('ntv3', '703M U-Net backbone + Transformer', 'Single bases; learned 128× pooling',
        '~8T nt OpenGenome2; functional post-training on 15 species.',
        'Training: up to 1,048,576 bp. Standard benchmark adaptation: 32,768 bp.',
        ['ntv3-final-architecture', 'ntv3-final-architecture', 'ntv3-final-training', 'ntv3-final-training'])
    row('deepd', '1.8B / 63B phylogeny-conditioned MoE', 'Single-nucleotide resolution',
        '~5.90T nt of whole genomes across domains of life and viruses.',
        'Training: 8K → 32K → 128K → 512K → 1M tokens.', 'summary-deepd-methods')
    row('gpnstar', '25–200M phylogeny-aware Transformer encoder', 'Aligned nucleotide positions',
        'Conserved whole-genome alignment windows; species-tree conditioning.',
        '128 or 256 aligned positions, depending on species/alignment.', 'summary-gpnstar-methods')
    row('loam', '25–624M causal Transformer', 'Single-base A/C/G/T',
        '67.5 Gbp; 15,640 soil species-representative long-read MAGs.',
        'Training: 8,192 nt.', 'final-loam-model-card')
    row('alphagenome', 'Convolutional U-Net + attention', 'One-hot nucleotide input',
        'Supervised human/mouse functional-genomics measurements.',
        'Input: 1,048,576 bp.',
        ['alphagenome-final-journal', 'summary-ag1-encoding', 'alphagenome-final-journal', 'alphagenome-final-journal'])
    row('alphagenome2', 'Convolutional U-Net + attention; cell conditioning', 'One-hot nucleotide input',
        'Human/mouse functional assays; 107M single-cell profiles for encoder/post-training.',
        'Input: 1,048,576 bp. Interval scoring: central 196,608 bp.',
        ['s2f-ag2-model', 's2f-ag2-model', 's2f-ag2-corpus', 's2f-ag2-context'])
    row('genosm', '4.7B causal MoE; ~330M active', 'Single-character tokenizer; vocabulary differs across report/config',
        '~1.2T nt; reference/gut microbial genomes and phages.',
        'Training curriculum and reported inference: up to 1M bp.',
        ['genosm-architecture', 'genosm-hf-tokenizer-evidence', 'genosm-corpus', 'genosm-architecture genosm-inference'])
    row('cerberus', '138M convolution + bidirectional Mamba-2', 'One-hot nucleotide input',
        'Supervised human/mouse functional assays: 8,361 / 3,102 tracks.',
        'Input/output span: 786,432 bp; 32-bp output bins.', 's2f-cerberus-model')
    row('aido2', '235M / 470M / 1B bidirectional Transformer MoE', 'Segmentation/vocabulary not disclosed in official report',
        'OpenGenome2: 8.84T nt.',
        'Report: medium/large 64K, small 256K (units unspecified). Coverage adaptation: 524 kb.',
        ['aido2-architecture', 'aido2-architecture', 'aido2-corpus', 'aido2-architecture aido2-coverage'])
    row('plantcad2', '88–676M Caduceus / bidirectional Mamba-2', 'Single-nucleotide tokens',
        '65 angiosperm genomes; gene-centered windows.',
        'Pretraining: 8,192 bp.',
        ['plantcad2-architecture plantcad2-sizes', 'plantcad2-model-config-ev', 'plantcad2-corpus', 'plantcad2-context'])
    row('spliceai', 'Dilated residual CNN; five-model ensemble', 'One-hot nucleotide input',
        'Supervised human gene annotations; GTEx junctions for the variant model.',
        '10k-flank model: 15,000-bp input, central 5,000-bp output.',
        ['spliceai-architecture', 'spliceai-architecture', 'spliceai-partitions', 'spliceai-architecture'])
    row('spliceai2', '~13M convolution/pooling + junction attention', 'One-hot bases + species channels',
        'Supervised RNA-seq: 314,745 short-read and 330 long-read samples.',
        'Input: 196,608 bp. Central site output: 65,536 bp.',
        ['spliceai2-architecture', 'spliceai2-architecture', 'spliceai2-training-data', 'spliceai2-architecture'])
    next(r for r in d['metadata'] if r['key'] == 'updated')['value'] = '2026-11-28'
