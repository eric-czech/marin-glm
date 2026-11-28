"""Source-based output/scoring audit, including explicit ambiguous cases.

This reconciliation is run intentionally, not as part of the offline build.
Known scalar benchmark families share inspected file/scorer evidence. Annotation,
tracks, structures and diagnostic exceptions below have specific source reviews.
The generated task_outputs rows are the durable individual review decisions.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
DATE='2026-11-27'

OUTPUTS=[
 ('isolated','Isolated labels / values','A label, scalar or non-positional vector for a supplied sequence, locus, exon or variant. Multiple tissues/classes do not make a genomic position axis.'),
 ('sampled-positions','Sampled position labels','Labels or feature alignment evaluated at selected genomic/token positions. Dense display tracks alone do not establish contiguous held-out scoring.'),
 ('dense-labels','Dense labeling','Biological labels evaluated at successive positions across each assessed sequence. Independent base accuracy does not establish valid exon chains.'),
 ('signal-profile','Signal profiles','Quantitative experimental signal indexed by multiple genomic positions or bins across an assessed sequence. Distinct from annotation labels and one pooled interval value.'),
 ('element-set','Element / boundary detection','A set of intervals or boundaries scored by coordinate matching. Correct individual elements do not imply a complete valid gene/transcript.'),
 ('linked-structure','Gene / transcript structures','Linked exon, intron or coding structures evaluated jointly. Coding phase, outer boundaries, isoform multiplicity and matching tolerance remain protocol-specific.'),
 ('pairwise','Pairwise relationships','A supplied pair, edge or condition contrast is scored. Junction or enhancer–gene scores do not themselves reconstruct a complete graph or transcript.'),
 ('sequence','Sequence generation / recovery','Nucleotide identities or generated sequence. This output alone is not biological dense annotation; experimental and computational validation differ.'),
 ('retrieval','Retrieval / selection','Ranking, retrieving or selecting among supplied candidates, including edits. Candidate choice is not new sequence generation.'),
 ('diagnostic','Aggregate / diagnostic analysis','Representation, constraint, enrichment, interpretation, runtime or cohort-level analysis. Positional visualizations are not automatically annotation benchmarks.'),
 ('unresolved','Unresolved / mixed outputs','The available source does not resolve the individual outputs or their scoring population sufficiently.')]


def populate(d):
    def put(table,row,keys=('id',)):
        old=next((x for x in d[table] if all(x[k]==row[k] for k in keys)),None)
        if old is None:d[table].append(row)
        else:old.update(row)
        return row.get('id')
    def cat(id,dim,name,definition,accommodation=None):
        put('categories',dict(id=id,dimension=dim,name=name,definition=definition,accommodation=accommodation))
    for slug,name,definition in OUTPUTS:cat('output-'+slug,'output',name,definition)
    cat('transcript','region','Transcript structures','Linked spliced transcript or coding-transcript coordinates. Coverage does not imply alternate-isoform recall, abundance, TSS/TES accuracy or UTR inclusion.')
    cat('splice-junction','region','Splice junctions','Donor–acceptor connections or intron chains; distinct from independent splice-site identity and from complete transcript recovery.')
    cat('structured-annotation','capability','Gene / transcript structure prediction','Predict linked gene/transcript coordinates and evaluate the chain or gene jointly; matching scope and tolerance are stated separately.','Structured decoding, phase/strand constraints or a splice graph may be required; independent site labels are insufficient.')
    cat('signal-profile-prediction','capability','Signal-profile prediction','Predict quantitative signal indexed by genomic positions or bins; a scalar whole-window count is not a signal profile.','Position-preserving features and a quantitative track head; binning and central cropping must be retained.')
    cat('element-detection','capability','Element / boundary detection','Locate a set of genomic elements or boundaries across an assessed sequence, rather than classify only supplied candidates.','Position-preserving features or coordinate outputs; exact/tolerant interval matching is explicit.')
    # Refine definitions without conflating biological features and evaluation form.
    definitions={
      'gene':('Genes / gene bodies','Gene-level sequence or gene-body context. Does not by itself establish full gene-structure recovery.'),
      'exon':('Exons','Exonic sequence, intervals or labels. Correct exon classification/detection does not establish a complete transcript chain.'),
      'intron':('Introns','Intronic sequence, intervals or labels. Supplied intron windows and recovered intron chains are different evaluations.'),
      'splice':('Splice sites','Donor/acceptor boundary identities or local splice-region effects. Junction pairing and complete isoforms are separate features.'),
      'mrna':('Mature / reporter mRNA','Mature transcript or reporter sequence as input/construct; does not imply reconstruction of a transcript from genomic DNA.'),
      'genome':('Broad genomic sequence','Whole-genome or broadly sampled sequence context; does not imply genome-wide validation or coverage of every element.'),
      'ncrna':('Noncoding RNA (broad)','Non-protein-coding RNA without a narrower universal class. Broad ncRNA assignments are not automatically “other than lncRNA/rRNA/tRNA”.')}
    for id,(name,definition) in definitions.items():
        r=next(c for c in d['categories'] if c['id']==id);r.update(name=name,definition=definition)
    dense=next(c for c in d['categories'] if c['id']=='dense-annotation')
    dense['definition']='Annotate biological features across sequence using position-aligned labels, detected elements or decoded structures. The Scored output field distinguishes bases, individual elements and complete chains; a supplied midpoint label or a proteome completeness statistic is insufficient.'
    # Register precise new locators for cases where prior capability assignments
    # overclaimed dense evaluation. Existing cached source hashes remain intact.
    def ev(id,source,locator,statement,url=None,basis='paper'):
        src=next(s for s in d['sources'] if s['id']==source)
        return put('evidence',dict(id=id,source_id=source,locator=locator,statement=statement,
            url=url or src['url'],basis=basis,inspected=DATE))
    botanic=ev('output-botanic-pooling','botanic-paper','Report v3 §4.3.6.1; Table S4',
        'Conservation/TIS/TTS/splicing use the centre-token embedding and scalar labels. Genomic-region classification pools the central 100 bp of a 512-bp window. Neither is a dense sequence-label output. ATAC profile and total counts are different outputs.')
    evo=ev('output-evo-midpoint','evo-supp','Exon/intron probe method; midpoint target',
        'Exon/intron evaluation labels only the midpoint of each sequence and probes forward/reverse representations. Genomic position origin and long input context do not make the assessed output dense.')
    nt=ev('output-ntv3-annotation','ntv3-paper','Gene annotation: Methods4.4, exact CDS-exon/gene scoring and HMM decoding',
        'HMM converts per-base state/phase predictions into complete coding transcripts. Exon-level exact interval scoring and whole-gene exact coding-structure scoring are separate targets. Primary reference uses longest isoform and excludes UTRs; alternative-isoform sensitivity is a separate analysis. No full mature transcript or all-isoform abundance benchmark is implied.')
    sei=ev('output-ntv3-seiplant','ntv3-paper','External evaluations: SeiPlant',
        'Each evaluation window contributes one central 128-bp H3K4me3 signal bin. NTv3 base-resolution output is averaged over that bin; source reports chromosome/experiment correlation. This selected-bin readout differs from scoring an entire output profile per input.')
    deep=ev('output-deepd-routing','src-deepd-human-routing-release','best_layers.csv; released train/validation/test row counts',
        'Human routing probes report 72,000/9,000/9,000 position rows per target. Selected layers produce continuous HBB display tracks, but the release does not establish that the scored test rows form a contiguous chromosome-held-out labeling benchmark.',basis='data')
    deeptrack=ev('output-deepd-demonstration','src-deepd-routing-interval','manifest.json: selection, rows, interval',
        'The released HBB demonstration contains 20,000 consecutive rows from chr11:5,220,000–5,240,000, selected as the original figure interval, with no random sampling. This proves dense demonstration output, not independence or contiguous coverage of the classifier test cohort.',basis='documentation')
    sae=ev('output-genosm-sae','genosm-paper','Methods: sparse autoencoder interpretability',
        'SAE feature search uses E. coli NC000913.3 ORF/intergenic/tRNA/rRNA annotations; one-versus-rest Domain F1 after activation-threshold sweeping. No separate annotation validation/test cohort is described. Token-wise alignment is an interpretation analysis, not a supervised held-out dense annotation benchmark.')
    aido=ev('output-aido-tracks','aido2-report','Supervised coverage prediction / frozen Flashzoi adapter',
        'Frozen AIDO.DNA2 representations feed an adapted Flashzoi coverage head on long sequences. Five assays score quantitative coverage; output binning is not specified in the inspected technical report. Do not assume single-base labels from input length or Borzoi ancestry.')
    gc=ev('output-genecad-components','genecad-release-cds-conversion','cds_to_gtf.py docstring and conversion',
        'Every CDS segment becomes an exon; current Base/Exon/Intron/Intron chain/Transcript/Locus scores all concern coding chains with UTRs omitted. The benchmark distinguishes component coordinates from linked structures, collapses identical coding chains, and normalizes stop codons.',basis='code')
    gceval=ev('output-genecad-matching','genecad-release-evaluator','evaluate.py: MODES, LEVELS and main',
        'Same predictions are scored at six levels with default gffcompare and --strict-match -e 0. Default intron-chain/transcript matching need not require identical outer boundaries; strict mode tightens them. These protocols are not interchangeable.',basis='code')
    # Authoritative scorer documentation resolves locus vs complete transcript.
    sid='gffcompare-scoring-doc'
    put('sources',dict(id=sid,title='GffCompare: accuracy assessment levels',kind='documentation',
        url='https://ccb.jhu.edu/software/stringtie/gffcompare.shtml',version='Inspected 2026-11-27',retrieved=DATE,
        sha256=None,local_path=None,availability='available',notes='Authoritative scorer definitions; release commands are separately pinned.'))
    gff=ev('output-gffcompare-levels',sid,'Accuracy assessment levels: base, exon, intron, chain, transcript, locus',
        'Intron-chain match requires all introns with equal count and exact coordinates, ignoring outer ends. Default transcript matching adds single-exon overlap; strict mode constrains terminal ends. Locus match needs at least one matched transcript, not recovery of every isoform.',basis='documentation')

    def assign(tid,cid,eid,relation='measured',rationale='Cited output/scoring definition.'):
        put('task_categories',dict(task_id=tid,category_id=cid,relation=relation,
            rationale=rationale,evidence_id=eid,attribution='curatorial'),('task_id','category_id','relation'))
    # New biological associations come from actual structural targets, not the
    # model's hypothetical capacity or every sub-feature in its training labels.
    structural={'ntv3-annotation-gene':'coding-chain','genecad-cds-chain':'coding-chain',
        'genecad-cds-transcript':'coding-chain','genecad-cds-locus':'gene-locus',
        'genecad-legacy-cds':'coding-chain','genecad-legacy-transcript':'full-transcript',
        'spliceai2-top-transcript':'splice-pattern'}
    for tid,scope in structural.items():
        eid='spliceai2-top-transcript-method' if tid.startswith('spliceai2') else nt if tid.startswith('ntv3') else 'genecad-paper-methods' if 'legacy' in tid else gc
        for cid in ('transcript','structured-annotation'):assign(tid,cid,eid,rationale='Joint linked-coordinate target; coding/terminal/isoform scope remains explicit in the output review.')
        if scope!='gene-locus':assign(tid,'splice-junction',eid,'target','Linked intron or coding-exon connections are part of the scored structure; not merely independent site labels.')
    for tid in ('genecad-cds-intron',):assign(tid,'splice-junction',gc,'target','Exact intron interval connects a donor and acceptor; no full chain required.')
    assign('ntv3-annotation-gene','cds',nt,'target','The exact gene-structure target is explicitly coding-only and excludes UTRs. Preserve CDS scope even though the compact view places complete chains in the structure column.')
    for tid,feature in [('botanic1-tis','translation-start'),('botanic1-tts','translation-stop')]:assign(tid,feature,botanic,'target','The source evaluates the corresponding central translation boundary, not an entire coding structure.')
    # Preserve references to the old classification in the audit report, while
    # removing it from current filters when the evidence does not support it.
    remove_dense={'evo-exon-intron','botanic1-regions','botanic1-conservation','botanic1-tis','botanic1-tts','genecad-busco'}
    signal={t['id'] for t in d['tasks'] if t['id'].startswith(('ntv3-tracks-','ntv3-ag-','aido2-coverage-'))}|{'botanic1-atac-profile'}
    remove_dense |= signal
    d['task_categories']=[r for r in d['task_categories'] if not(r['category_id']=='dense-annotation' and r['task_id'] in remove_dense)]
    for r in d['task_categories']:
        if r['category_id']=='dense-annotation' and r['task_id'].startswith(('deepd-human-routing-','deepd-annotation-')):
            r.update(relation='demonstrated-output',evidence_id=deeptrack if 'human-routing' in r['task_id'] else 'deepd-eval-methods',
                rationale='Continuous annotation tracks are demonstrated. The output review separately qualifies the sampled or unresolved quantitative test cohort; this assignment does not establish a chromosome-held-out dense benchmark.')
    d['field_evidence']=[r for r in d['field_evidence'] if not(r['entity_table']=='tasks' and r['field']=='classification:dense-annotation' and r['entity_id'] in remove_dense)]
    for tid in signal:assign(tid,'signal-profile-prediction',aido if tid.startswith('aido2') else 'botanic1-eval-methods' if tid.startswith('botanic') else 'ntv3-eval-methods')

    d.setdefault('task_outputs',[])
    decisions={}
    def review(ids, form, prediction, unit, axis='none', scope='none', eid=None, rationale=None, status=None, limitations=None, support=()):
        for tid in ids:
            if tid in decisions:raise ValueError('Duplicate review: '+tid)
            t=next(t for t in d['tasks'] if t['id']==tid)
            e=eid or t['evidence_id']
            decisions[tid]=dict(id=tid+'-output-review',task_id=tid,category_id='output-'+form,
                prediction_form=prediction,scoring_unit=unit,position_axis=axis,
                structure_scope=scope,status=status or ('partial' if t['status'] in ('registered','panel-pending') else 'supported'),
                rationale=rationale or 'The cited task scores '+t['target']+' for supplied examples. '+t['description'],
                limitations=limitations or ('This decision concerns the scored output only. It does not upgrade the task’s artifact, split, or label audit; linked protocols retain their own adaptation and selection rules.'),evidence_id=e)
            for s in support:
                put('field_evidence',dict(entity_table='task_outputs',entity_id=tid+'-output-review',field='scoring_unit',evidence_id=s,note='Supporting output/metric semantics.'),('entity_table','entity_id','field','evidence_id'))
    def ids(prefix):return [t['id'] for t in d['tasks'] if t['id'].startswith(prefix)]
    review(['evo-exon-intron'],'isolated','Label at the input midpoint','One supplied midpoint',axis='sampled',eid=evo,
        rationale='Binary exon/intron readout at the supplied midpoint; not a predicted annotation track, exon set or gene chain.')
    review(['botanic1-regions'],'isolated','One pooled-window class','One central 100-bp window',eid=botanic,
        rationale='Central-window pooling yields one compartment label; a genic annotation source is not a dense output axis.')
    review(['botanic1-conservation','botanic1-tis','botanic1-tts'],'isolated','Central-position class','One supplied centre position',axis='sampled',eid=botanic,
        rationale='Centre-token frozen probe; the source supplies point-feature candidates. This does not locate all sites across a sequence.')
    review(['ntv3-seiplant'],'isolated','Dense native track reduced to one interval value','One central 128-bp interval per window',eid=sei,
        rationale='The readout averages a native positional prediction over the matched central bin; the benchmark does not score the whole NTv3 profile per input.')
    review(sorted(signal),'signal-profile','Quantitative assay profile over genomic positions/bins','Assay track × scored genomic position/bin',axis='contiguous',
        rationale='Assay signals retain a genomic position axis across a scored output region. Track identity, binning, central crop and transform are protocol-specific; this is regression, not element labels or transcript reconstruction.')
    for tid in signal:
        if tid.startswith('aido2'):
            decisions[tid].update(evidence_id=aido,status='partial',prediction_form='Quantitative coverage profile; output binning not specified',limitations='Report describes coverage and Pearson scoring but does not establish exact output bins, target manifest or every split. Do not infer single-base resolution from the architecture.')
    review(['bgcs-cds'],'dense-labels','Coding/intergenic probabilities at every nucleotide','Nucleotide within a held-out BGC',axis='contiguous',eid='bgcs-cds-code',
        rationale='Released scorer concatenates per-accession nucleotide embeddings and labels, holding entire BGC accessions in folds. Biological position labels are dense within each BGC; no exon-chain decoding.',
        support=('bgcs-methods',))
    review(['genecad-cds-base','genecad-legacy-nucleotide'],'dense-labels','Position-aligned genomic feature probabilities','Genomic base',axis='contiguous',eid=gc,
        rationale='Current release scores coding-base overlap; historical paper scores per-base feature labels. These are versioned outputs, not complete structure metrics.',support=(gceval,))
    decisions['genecad-legacy-nucleotide']['evidence_id']='genecad-paper-methods'
    review(['spliceai-sites-coding','spliceai-sites-linc'],'dense-labels','Donor/acceptor/neither probability at every output base','Genomic base / donor-acceptor class',axis='contiguous',
        rationale='Original paper scores all positions in the evaluated transcript sequences, with class-wise top-k and PR-AUC. This is dense site labeling, not paired junction or full-isoform accuracy.')
    if any(t['id']=='bend1-gene-finding' for t in d['tasks']):
        review(['bend1-gene-finding'],'dense-labels','Nine strand-aware biological labels at every input base','Nucleotide; multiclass MCC over the full assessed sequence',axis='contiguous',eid='bend1-gene-method',
            rationale='Original BEND gene finding labels coding/exon, intron, donor/acceptor and background positions. The metric is nucleotide MCC, not exact complete-chain recovery.',support=('bend1-gene-readout','bend1-dimensions','bend1-label-utility'))
        review(['bend1-enhancer-annotation'],'dense-labels','One binary enhancer label per 128-bp bin','128-bp output bin across a 100,096-bp window',axis='contiguous',eid='bend1-enhancer-method',
            rationale='782 adjacent binary bins, not a pooled window label or continuous assay profile. Known TSS and incompletely tested negative bins limit the target interpretation.',support=('bend1-enhancer-readout','bend1-dimensions'))
    for tid,scope in structural.items():
        e='spliceai2-top-transcript-method' if tid.startswith('spliceai2') else nt if tid.startswith('ntv3') else 'genecad-paper-methods' if 'legacy' in tid else gc
        unit='Gene locus with at least one matching coding transcript' if scope=='gene-locus' else 'Dominant transcript internal splice chain' if scope=='splice-pattern' else 'Complete coding exon/phase chain' if tid=='genecad-legacy-cds' else 'Linked coding exon / gene coordinates' if scope=='coding-chain' else 'Complete transcript coordinates'
        review([tid],'linked-structure','Linked exon/intron coordinates decoded from positional outputs',unit,axis='linked',scope=scope,eid=e,
            rationale='The benchmark jointly matches linked structure rather than averaging isolated site labels. '+next(t['description'] for t in d['tasks'] if t['id']==tid),
            limitations='Current GeneCAD coding metrics omit UTRs and differ between default and strict terminal matching; locus match needs only one matched transcript. NTv3 scores coding gene models. SpliceAI2 scores dominant splice patterns without transcript ends or all-isoform recall. These tasks are not interchangeable.',support=(gceval,gff) if tid.startswith('genecad-cds') else ())
    element=['genecad-cds-exon','genecad-cds-intron','genecad-legacy-exon','ntv3-annotation-exon']+ids('genecad-boundary-')
    for tid in element:
        e=nt if tid.startswith('ntv3') else 'genecad-paper-methods' if 'legacy' in tid else 'genecad-release-structure-code-ev' if 'boundary' in tid else gc
        review([tid],'element-set','Genome-indexed intervals / boundary coordinate set','Individual interval or boundary coordinate',axis='interval-set',eid=e,
            rationale='Compare detected coordinates to reference elements across annotated sequence. Individual interval/boundary accuracy is scored separately from complete linked gene recovery.',support=(gceval,gff) if tid.startswith('genecad-cds') else ())
        assign(tid,'element-detection',e)
    review(['genecad-busco'],'diagnostic','Proteins translated from predicted gene structures','Proteome-level BUSCO completeness classes',eid='genecad-release-structure-code-ev',
        rationale='BUSCO evaluates recovery of conserved orthologs from the predicted proteome. It neither scores every genomic base nor directly establishes exact exon chains, and duplicated/missing classes are aggregate outcomes.')
    review(ids('deepd-human-routing-'),'sampled-positions','Position-wise routing classifier; dense HBB demonstration track','Reported test position rows; coordinate grouping unresolved',axis='sampled',eid=deep,status='partial',
        rationale='Released best-layer test metrics concern position rows. The contiguous HBB display is a selected demonstration, not established as an independent dense test span.',support=(deeptrack,'deepd-routing-model-release'))
    review(['deepd-annotation-bacteria','deepd-annotation-maize'],'unresolved','Position-wise routing probability tracks for multiple annotation targets','Composite annotation panel; exact scored position cohort unresolved',axis='unresolved',scope='unresolved',eid='deepd-eval-methods',status='unresolved',
        rationale='Paper shows continuous label tracks and maize category AUPRC, but the registered panel does not resolve all dataset × target units or coordinate sampling. Dense output capability is demonstrated; dense held-out cohort scoring is not established.')
    review(ids('genosm-sae-'),'sampled-positions','Sparse latent activations thresholded against token annotations','Token-to-annotation Domain F1 on one E. coli genome',axis='sampled',eid=sae,status='partial',
        rationale='Token-level annotation alignment and illustrative activation tracks are assessed after feature/threshold selection on the same genome. This is not an independent dense annotation generalization result.')
    # Reviewed reusable dataset families: actual scalar-label/fitness releases,
    # not deductions that a genomic feature name implies a position axis.
    for prefix in ('geneb-','rnagym-','nt-original-','nt-revised-','gb-','gue-','mrna-'):
        ts=[t for t in d['tasks'] if t['id'].startswith(prefix)]
        for t in ts:
            review([t['id']],'isolated','Per-example class / measured value / non-positional target vector','One supplied sequence or variant',
                rationale='Released benchmark records and the cited readout associate labels/fitness with supplied sequences or variants. The feature annotation identifies the input/target biology, not a dense genomic label axis. '+t['target']+'.')
    # Remaining explicit output-type families were inspected in the existing
    # paper/protocol audit. We do not silently call unknown forms isolated.
    scalar_types={'binary classification','multiclass classification','multilabel classification','classification',
        'regression','regression / ranking','ordinal prediction','multioutput regression','multilabel prediction','multitask prediction',
        'question answering','binary classification / ranking','ranking','classification / representation analysis',
        'paired discrimination','paired sequence discrimination'}
    diagnostic_types={'embedding diagnostic','exploratory representation analysis','computational benchmark','sequence diagnostic',
        'enrichment analysis','association analysis','association / enrichment analysis','constraint diagnostic','mechanistic case study',
        'clustering agreement','clustering','eds','controlled context diagnostic'}
    for t in d['tasks']:
        tid=t['id']
        if tid in decisions:continue
        typ=t['task_type']
        if tid in ('ntv3-re2g','bacbench-operondb','bacbench-operon-longread','bacbench-ppi') or typ in ('pair_classification','pairwise regression'):
            review([tid],'pairwise','Score on a supplied pair / junction / condition contrast','Supplied pair or edge',
                rationale='The cited task supplies pair identities (gene pairs, junctions or conditions) and scores their relation/value. It does not reconstruct the full gene/transcript or interaction graph. '+t['target'])
        elif typ in scalar_types:
            review([tid],'isolated','Per-example label / value / non-positional target vector','One supplied sequence, site, gene or variant')
        elif typ in ('generation','generation / design','generation / search','sequence prediction','sequence reconstruction'):
            review([tid],'sequence','Generated, continued or reconstructed nucleotide sequence','Nucleotide / generated sequence and source-specific validation endpoint',
                rationale='The target is sequence identity/design rather than biological labels along the input. '+t['description']+' Sequence recovery at known sites is not genome-wide feature discovery.')
        elif typ in ('retrieval','exact retrieval','bigene_mining','candidate selection'):
            review([tid],'retrieval','Ranked / selected supplied candidate','Query or candidate-choice request',rationale='The benchmark chooses or retrieves supplied items. '+t['description'])
        elif typ in diagnostic_types:
            review([tid],'diagnostic','Source-specific diagnostic / aggregate statistic','Source-defined analysis unit',rationale='This is an analysis of representations, selection, associations or computation. '+t['description'])
        else:raise ValueError('Unreviewed output form: '+tid+' / '+typ)
    # Correct known candidate-selection and diagnostic cases that have a scalar
    # numerical score but should not be advertised as biological labeling.
    for tid in ('carbon-triplet','carbon-synonymous','bend-haplotype-recovery','bend-haplotype-preference'):
        decisions[tid].update(category_id='output-diagnostic',prediction_form='Native nucleotide likelihood / allele preference diagnostic',scoring_unit='Natural / altered sequence or carrier background contrast')
    decisions['ceno-tad']['rationale']='Supplied boundary-centred positive/negative examples are classified; this is not de novo detection of a boundary set or a predicted chromatin contact map.'
    decisions['plantcad2-ft-cell_type_specific_acr']['rationale']='One maize ACR sequence receives 92 cell-type labels. The vector indexes cell types, not genomic positions, and is not a dense annotation track.'
    decisions['pgb-chromatin']['rationale']='A supplied genomic window has chromatin-accessibility/histone target labels. Multiple assay outputs are not a genomic position axis.'
    output_ids={c['id'] for c in d['categories'] if c['dimension']=='output'}
    d['task_categories']=[r for r in d['task_categories'] if r['category_id'] not in output_ids]
    for tid,r in decisions.items():
        put('task_outputs',r)
        assign(tid,r['category_id'],r['evidence_id'],'scored-output',r['rationale'])
    # All records have a decision, including explicitly unresolved panels.
    assert set(decisions)=={t['id'] for t in d['tasks']}
    known={e['id'] for e in d['evidence']}
    assert all(r['evidence_id'] in known for r in decisions.values()),[(r['task_id'],r['evidence_id']) for r in decisions.values() if r['evidence_id'] not in known]

    # CDS-specific targets are not the union of every task carrying a CDS tag.
    # Mixed region classifiers, whole-genome generation and mature-mRNA inputs
    # must not inflate the dedicated coding-sequence column.
    d.setdefault('task_feature_scopes',[])
    mixed={'evo-gen-mitochondria','evo-gen-bacterial-genome','evo-gen-yeast-chr',
        'mrna-go-bp','mrna-go-cc','mrna-go-mf','mrna-prot-loc','gpn-mmrdb','gpn-flybase',
        'aido2-human-elements','genosm-gene-class','plantcad2-potato-gerp',
        'deepd-annotation-bacteria','deepd-annotation-maize','genecad-legacy-nucleotide',
        'bacbench-essential','gpn-rvat','bend1-gene-finding'}
    context={'botanic1-tis','botanic1-tts','plantcad2-conservation_within_poaceae_tis'}
    cds={r['task_id'] for r in d['task_categories'] if r['category_id']=='cds'}
    for t in d['tasks']:
        if t['id'] not in cds:continue
        tid=t['id']
        scope='protein-reference' if t['input_description'].startswith('PROTEIN') else 'mixed' if tid in mixed else 'context' if tid in context else 'derived-readout' if tid=='genecad-busco' else 'restricted-target'
        reason={
            'restricted-target':'The defined target concerns coding sequence, coding variants, a coding gene’s function, or coding-region annotation; flanking input and noncoding negative labels do not change the target. ',
            'mixed':'CDS is one context/class/subset in a broader target or assay; a restriction to CDS is not established for the whole record. ',
            'context':'The scored target is a translation boundary, not general CDS function/identity. ',
            'protein-reference':'The record is a protein-only reference, not an evaluated DNA sequence; hollow markers retain this distinction. ',
            'derived-readout':'The endpoint is completeness of a derived proteome, not a CDS sequence label or coding-variant measurement. '}[scope]
        put('task_feature_scopes',dict(id=tid+'-cds-scope',task_id=tid,feature_id='cds',scope=scope,
            rationale=reason+t['description'],evidence_id=t['evidence_id']))

    # Biological-feature details remain intact. The compact default view groups
    # components and reserves columns for actual jointly scored structures.
    grouped=[
      ('gene-structures','Gene structures','Gene annotation','Joint coding/gene structures; terminal, phase and UTR rules differ by protocol.'),
      ('coding-sequence','Coding sequence','Gene annotation','CDS-specific sequence, coding-variant, coding-function or component-annotation targets. Excludes mixed region classifiers and broad genomic context. Hollow symbols are protein-only references.'),
      ('transcript-structures','Splice isoforms','Splicing','Joint spliced transcript paths; this does not imply all-isoform recall or TSS/TES accuracy.'),
      ('gene-elements','Gene elements','Gene annotation','Supplied or detected gene/CDS/exon/intron components; output filter separates isolated labels from dense labels and interval detection.'),
      ('splice-elements','Splice sites / junctions','Splicing','Component splice-site or junction targets; full transcript paths are shown separately.'),
      ('utrs','UTRs','Gene annotation','5′/3′ untranslated-region tasks. These are distinct from translation start/stop detection.'),
      ('translation-boundaries','Translation start / stop','Gene annotation','Initiation/termination codons or boundary tasks, not transcript starts/ends.'),
      ('regulatory-elements','Regulatory elements','Regulation','Promoter/enhancer/TF-binding/regulatory targets; output form distinguishes isolated values from dense quantitative profiles.'),
      ('chromatin-organization','Chromatin boundaries','Regulation','TAD/insulation boundary classification or sequence design; no complete regulatory-network task is inferred.'),
      ('rna-features','RNA features','RNA','Mature/reporter mRNA and ncRNA feature or sequence tasks; not reconstruction of genomic transcript structure.'),
      ('clusters-operons','Gene clusters / operons','Microbial regions','Biosynthetic cluster and operon targets; supplied-region or supplied-pair tasks remain distinguishable by scored output.'),
      ('repetitive','Repeats / TEs','Sequence context','Repeat/transposable element context or labels.'),
      ('intergenic-context','Intergenic DNA','Sequence context','Intergenic sequence context or labels.'),
      ('broad-context','Broad / unspecified','Sequence context','Broad sequence or no specific feature assignment; does not imply all functional elements are evaluated.')]
    settings={r['key']:r for r in d['coverage_settings']}
    settings['features']['value_json']=json.dumps([
        dict(id=c['id'],label={'cds':'CDS','gene':'Genes / gene bodies','transcript':'Transcript structures','splice-junction':'Splice junctions','ncrna':'ncRNA (broad)'}.get(c['id'],c['name']),
             group='Gene structure' if c['id'] in {'gene','transcript','cds','exon','intron','splice','splice-junction','utr5','utr3','translation-start','translation-stop'} else 'Regulation' if c['id'] in {'promoter','enhancer','regulatory','tfbs','polya','terminator','chromatin-boundary'} else 'RNA' if c['id'] in {'mrna','ncrna','lncrna','rrna','trna','ribozyme','aptamer'} else 'Sequence context / multi-gene regions',definition=c['definition'])
        for c in sorted([c for c in d['categories'] if c['dimension']=='region'],key=lambda c: ['gene','transcript','cds','exon','intron','splice','splice-junction','utr5','utr3','translation-start','translation-stop','promoter','enhancer','tfbs','regulatory','polya','terminator','chromatin-boundary','mrna','lncrna','ncrna','rrna','trna','ribozyme','aptamer','bgc','operon','repeat','intergenic','genome'].index(c['id']))]
        +[dict(id='unspecified',label='Unspecified',group='Sequence context / multi-gene regions',definition='No specific feature assignment.')],ensure_ascii=False)
    features=json.loads(settings['features']['value_json'])
    # Keep features of each group adjacent so table colspans remain meaningful.
    order=['Gene structure','Regulation','RNA','Sequence context / multi-gene regions']
    settings['featureGroups']['value_json']=json.dumps([dict(label=g,ids=[f['id'] for f in features if f['group']==g]) for g in order])
    # Rearrange grouped features by group for the same invariant.
    group_order=['Gene annotation','Splicing','Regulation','RNA','Microbial regions','Sequence context']
    compact=[dict(id=i,label=l,group=g,definition=definition) for g in group_order for i,l,gg,definition in grouped if gg==g]
    put('coverage_settings',dict(key='groupedFeatures',value_json=json.dumps(compact,ensure_ascii=False)),('key',))
    # Registered collections without decomposed tasks remain visible, with the
    # specific limit relevant to this review. No hypothetical task gets a dot.
    pending_notes={
      'nabench':'Output audit: the 170-entry source manifest describes sequence/variant fitness assays. RNA_TYPE alone does not establish element identity or a positional label axis. Individual assay reconciliation remains incomplete.',
      'lambda':'Output audit: prophage detection/localization can assess interval recovery, but this registration does not yet establish its exact output tensors, scoring unit or task variants. No dense or complete-structure task is inferred.',
      'lrb':'Output audit: reference-sequence/variant readouts remain to be decomposed. Genome annotation is described as future work in the inspected workshop paper; do not count a released dense gene-annotation task from that statement.',
      'dnalongbench':'Output audit: the paper includes chromatin-contact-map and functional-track prediction. A scored contact matrix is distinct from a supplied enhancer–gene edge, a TAD-centred classifier and a one-dimensional signal track. Dataset × target/split decomposition is still pending; no matrix task is invented from the registration.',
      'genbench':'Output audit: short/long sequence tasks and site annotation require task-specific output/scorer reconciliation. Site annotation alone does not establish full gene-chain recovery. No broad dense or structure assignment is made to this registered collection.',
      'dna-foundation':'Output audit: sequence classification, individual expression/variant readouts and TAD analysis must retain their actual readout units. Long input or a boundary-related dataset name does not establish contiguous label or contact-map evaluation.',
      'gene-mteb':'Output audit: metagenomic sequence classification/clustering concerns sequence representations, not dense genomic labels. Its sixteen reported entries still require dataset/target and split reconciliation before individual task records are added.'}
    for id,note in pending_notes.items():
        r=next(r for r in d['evaluations'] if r['id']==id)
        previous=r.get('notes') or ''
        if 'Output audit:' in previous:previous=previous.split('Output audit:')[0].strip()
        r['notes']=(previous+' '+note).strip()
        put('field_evidence',dict(entity_table='evaluations',entity_id=id,field='output_audit',evidence_id=r['evidence_id'],note=note),('entity_table','entity_id','field','evidence_id'))
    return d


if __name__=='__main__':
    p=ROOT/'data/catalogue.json'
    p.write_text(json.dumps(populate(json.loads(p.read_text())),ensure_ascii=False,indent=2)+'\n')
