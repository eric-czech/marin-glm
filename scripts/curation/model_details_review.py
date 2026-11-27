"""Keep training context and evaluation context distinct in model descriptions."""
from common import Catalogue


def populate(d):
    c=Catalogue(d)
    def prop(model,slug,name,category,value,ev,notes=''):
        c.put('model_properties',dict(id=model+'-final-'+slug,model_id=model,category=category,name=name,
            variant=None,value=value,status='source-reported',evidence_id=ev,notes=notes))
    carbon=c.evidence('carbon-final-model-details','carbon-paper','§3, Table 2; §4; §5.1–5.3, Table 3; §6.5, Table 5',
        'Standard causal Transformer (RMSNorm, SwiGLU, RoPE, GQA); DNA uses nonoverlapping 6-mers inside a hybrid text vocabulary. '+
        'Base mixture: 70% GENERator-v2 eukaryotic DNA, 16% mRNA, 4% mRNA-splice, 10% prokaryotic OpenGenome2. '+
        'Training uses 8,192 tokens then 32,768. Prose specifies YaRN inference at 65,536/131,072 tokens for 3B/8B, respectively; Table 5 also reports 3B at 131,072 tokens. Context extrapolation is separate from genomic retrieval performance.',
        url=c.get('sources','carbon-paper')['url']+'#page=8')
    prop('carbon','corpus','Pretraining mixture','pretraining',
        'Base sampling: 70% GENERator-v2 eukaryotic DNA, 16% OpenGenome2 mRNA, 4% mRNA-splice, 10% prokaryote. '+
        'Table 2 inventories 423/116/197/358 Gbp in those sources; sampling weights differ from raw corpus sizes. Later decay and context stages change the mixture.',carbon,
        'Corpus content and consumed training tokens are separate. No benchmark decontamination is inferred from these source names.')
    prop('carbon','architecture','Architecture','architecture',
        'Decoder-only Transformer with RMSNorm, SwiGLU, RoPE and GQA. 3B: 30 layers, width 3,072, 32 query heads / 4 KV groups. 8B: 32 layers, width 4,096, 32 query heads / 8 KV groups.',carbon)
    prop('carbon','tokenizer','Tokenization','tokenization',
        'DNA: 4,096 nonoverlapping canonical 6-mers. Hybrid Qwen3 text BPE plus DNA structural tokens; total vocabulary 155,776. DNA tags do not contribute to the training loss.',carbon)
    prop('carbon','objective','Training objective','training',
        'Next-token cross entropy for the first 100B tokens, then factorized nucleotide supervision (FNS). Roughly 1T base-stage tokens followed by 50B tokens of context extension. Loss is restricted to DNA 6-mer positions; structural tags and metadata text are excluded. Pure-DNA training does not train the natural-language BPE component as a language assistant.',carbon)
    prop('carbon','context','Training and inference context','context',
        'Base: 8,192 tokens (49,152 bp). Trained extension: 32,768 tokens (196,608 bp), with RoPE base increasing from 500,000 to 5,000,000. '+
        'Prose specifies inference YaRN extension for 3B at 2× to 65,536 tokens (393,216 bp), and 8B at 4× to 131,072 tokens (786,432 bp). Table 5 also reports 3B at 131,072 tokens under a 4× extension; this differs from the stated 3B limit. Evaluations must identify the checkpoint and extrapolation setting.',carbon)
    c.limit('models','carbon','tied-embeddings-description','conflicting',
        'Section 5.1 prose states tied input/output embeddings; Table 3 marks 3B tied and 8B untied. The catalogue preserves this report-level discrepancy rather than selecting one statement without a checkpoint-specific config.',carbon)
    c.limit('models','carbon','3b-inference-extension','conflicting',
        'Sections 5.1, 5.3 and 6.5 specify a 2× YaRN extension to 65,536 tokens for 3B. Figure 5 and Table 5 instead include 3B at 131,072 tokens under a 4× extension. These report descriptions do not establish a single unambiguous maximum for every released 3B checkpoint.',carbon)
    botanic=c.evidence('botanic-final-model-details','botanic-paper','§4.1–4.2; Figure 1; Tables S19–S20',
        'Bidirectional Mamba2 encoder family with 318M/688M/2.1B/3.2B parameters, a nucleotide tokenizer and a 15% masked-position objective. '+
        'All final base models use 314.6B training tokens in 8,192-token windows (CLS plus 8,191 bases). '+
        'Source corpus contributes windows from 320 plant species; the context-extended S model is separate from base checkpoints.',
        url=c.get('sources','botanic-paper')['url']+'#page=34')
    prop('botanic1','architecture','Architecture and tokenizer','architecture',
        'Bidirectional Mamba2 encoder with 318M/688M/2.1B/3.2B parameters, untied embeddings/head and a nine-token nucleotide vocabulary (A/C/G/T, N, UNK, PAD, MASK, CLS). Base input is one CLS token plus 8,191 DNA bases.',botanic)
    prop('botanic1','corpus','Pretraining corpus','pretraining',
        'Curated annotated land-plant assemblies: 326 genomes in the 8k corpus, 322 assigned to training and four to held-out species; 320 training species contribute windows after filtering. Function-balanced window sampling, redundancy/N-content filters and genome-length reweighting. '+
        'The full 320 species are not uniformly represented as evaluation targets.',botanic)
    prop('botanic1','objective','Training objective and budget','training',
        'Masked language modeling on 15% of eligible positions, with repeat-dependent weighting. Each final base checkpoint consumes 314.6B tokens. S/M/L use 200,000 steps; XL uses 100,000 steps.',botanic)
    prop('botanic1','context','Context protocols','context',
        'Base pretraining uses 8,192 tokens. A separate S context curriculum starts from 500B tokens at 8k and adds 50/50/100/100B tokens at 16k/32k/64k/128k, reaching 800B tokens. The released 314.6B base checkpoints are distinct. Masked pseudo-perplexity evaluates extrapolated windows up to 1,048,576 bp. '+
        'Random-DNA key/value retrieval and maize accessibility context sweeps have separate protocols and do not establish interchangeable biological long-range performance.',botanic)
    card=c.evidence('carbonx-final-model-details','carbonx-card','Model summary; Key features; Training',
        '14.8B decoder initialized from Qwen3-14B: 40 layers, width 5,120, 40 query heads / 8 KV heads. '+
        'One DNA/text token stream; 4,096 DNA 6-mers, 1,364 tail tokens and structural markers. Context limit: 40,960 tokens. A roughly 10B-token embedding warm-up precedes 302B full mid-training tokens, then SFT and RL with verifiable rewards.',basis='documentation')
    prop('carbonx','architecture','Architecture and initialization','architecture',
        'Qwen3-14B-derived 14.8B decoder, 40 layers, width 5,120, 40 query heads / 8 KV heads, SwiGLU, RMSNorm/QK-norm; one shared DNA/text decoder with no separate DNA encoder.',card)
    prop('carbonx','tokenizer','Hybrid DNA/text tokenizer','tokenization',
        'Qwen3 text BPE plus 4,096 DNA 6-mers, 1,364 tail tokens and three DNA markers. Noncanonical 6-mers become OOV; automatic DNA detection/tagging affects prompt tokenization.',card)
    prop('carbonx','training','Training and context','training',
        'Roughly 10B tokens of embedding-only warm-up, then 302B tokens of full mid-training on DNA, biology text, English and instruction data, followed by supervised fine-tuning and RL with verifiable rewards. Full mid-training uses 8,192-token sequences; the model card advertises a 40,960-token context limit. Reported evaluations disable thinking and use one sampled answer per prompt.',card,
        'DNA base span depends on the text/DNA mixture and chat overhead. Context limit is not a demonstrated long-range retrieval result.')
    return d
