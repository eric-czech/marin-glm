"""Dedicated benchmark projects, related literature, and evidence of external use.

Project qualification is separate from scientific quality and task audit status.
No task/model association is inferred from a wrapper, citation or suite membership.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'research/sources/projects'
DATE = '2026-11-26'
POLICY = (
    'A project must primarily develop a substantial, reusable, standardized evaluation '
    'framework or benchmark suite for nucleotide/genomic models. Require documented '
    'evaluation or software use by at least two distinct external research groups. '
    'Citations, surveys, stars, downloads, model adapters, and author-run leaderboards '
    'alone do not establish adoption. Shared benchmark authorship does not count as '
    'independent adoption. Qualification is not a quality endorsement; adoption is '
    'specific to the release and subset actually used.'
)


def populate(c):
    c.add('metadata', key='project_policy', value=POLICY)
    downloads = {r['id']: r for r in json.loads((BASE / 'downloads.json').read_text())}

    def literature(key, title, year, url, version, *, doi=None, status='preprint',
                   scope='benchmark', notes=None):
        row = downloads.get(key, {})
        local = row.get('text_path') if 'error' not in row else None
        # Failed retrievals never acquire a cached-full-text label.
        sid = 'project-paper-' + key
        c.source(sid, title, url, 'paper', version, local,
                 notes=notes or 'Full text retrieved where cached; only cited sections were reviewed. No numerical results reproduced.')
        c.paper(key, title, sid, year, status=status, scope=scope, doi=doi, notes=notes)
        return sid

    specs = [
        ('omnigenbench', 'OmniGenBench: A Modular Platform for Reproducible Genomic Foundation Models Benchmarking', 2025,
         'https://arxiv.org/html/2505.14402v1', 'arXiv:2505.14402v1', '10.48550/arXiv.2505.14402'),
        ('genbench', 'GenBench: A Benchmarking Suite for Systematic Evaluation of Genomic Foundation Models', 2024,
         'https://arxiv.org/html/2406.01627v2', 'arXiv:2406.01627v2', '10.48550/arXiv.2406.01627'),
        ('gfmbench', 'GFMBench-API: A Standardized Interface for Benchmarking Genomic Foundation Models', 2026,
         'https://www.biorxiv.org/content/10.64898/2026.02.19.706811v2', 'bioRxiv v2, 2026-08-11', '10.64898/2026.02.19.706811'),
        ('bend-original', 'BEND: Benchmarking DNA Language Models on biologically meaningful tasks', 2024,
         'https://arxiv.org/html/2311.12570v4', 'ICLR 2024; arXiv v4', '10.48550/arXiv.2311.12570'),
        ('guanine-original', 'GUANinE v1.0: Benchmark Datasets for Genomic AI Sequence-to-Function Models', 2024,
         'https://proceedings.mlr.press/v240/robson24a/robson24a.pdf', 'PMLR 240, 2024; earlier preprint 2023', None),
        ('dna-foundation', 'Benchmarking DNA foundation models for genomic and genetic tasks', 2025,
         'https://pmc.ncbi.nlm.nih.gov/articles/PMC12663285/', 'Nature Communications 16,10780; 2025-11-28', '10.1038/s41467-025-65823-8'),
        ('nt-original-paper', 'Nucleotide Transformer: building and evaluating robust foundation models for human genomics', 2025,
         'https://www.nature.com/articles/s41592-024-02523-z', 'Nature Methods 22,287–297; published 2024, volume 2025', '10.1038/s41592-024-02523-z'),
        ('dnabert2', 'DNABERT-2: Efficient Foundation Model and Benchmark For Multi-Species Genome', 2024,
         'https://arxiv.org/html/2306.15006v2', 'arXiv v2, 2024-03-18; original 2023', '10.48550/arXiv.2306.15006'),
        ('lrb', 'Advancing DNA Language Models: The Genomics Long-Range Benchmark', 2024,
         'https://llms4science-community.github.io/aaai2024/papers/LLMs4Bio24_paper_12.pdf', 'AAAI 2024 LLMs4Bio workshop version; subsequent submissions tracked separately', None),
        ('dnalongbench', 'DNALongBench: A Benchmark Suite for Long-Range DNA Prediction Tasks', 2025,
         'https://pmc.ncbi.nlm.nih.gov/articles/PMC11741265/', 'bioRxiv v1, 2025-01-08', '10.1101/2025.01.06.631595'),
        ('metagene1', 'METAGENE-1: Metagenomic Foundation Model for Pandemic Monitoring', 2025,
         'https://arxiv.org/html/2501.02045v1', 'arXiv:2501.02045v1; Gene-MTEB section 5.3', '10.48550/arXiv.2501.02045'),
        ('dnachunker', 'DNACHUNKER: Learnable Tokenization for DNA Language Models', 2026,
         'https://proceedings.mlr.press/v306/kim26bn.html', 'ICML 2026, PMLR 306:58951–58968; publisher PDF inspected', '10.48550/arXiv.2601.03019'),
        ('patchdna', 'PatchDNA: A Flexible and Biologically-Informed Alternative to Tokenization for DNA', 2026,
         'https://abdullah-athar.github.io/assets/pdfs/PatchDNA.pdf', 'Author-hosted ICLR 2026 submission PDF; inspected version says under review', '10.1101/2025.11.28.691095'),
        ('genezip', 'GeneZip: Region-Aware Compression for Long Context DNA Modeling', 2026,
         'https://arxiv.org/html/2602.17739v4', 'arXiv:2602.17739v4, 2026-11-09', '10.48550/arXiv.2602.17739'),
        ('ribospan', 'RIBOSPAN: A Long-Context RNA Foundation Model for Versatile RNA Modeling', 2026,
         'https://arxiv.org/html/2608.22849v3', 'arXiv:2608.22849v3, 2026-11-24', '10.48550/arXiv.2608.22849'),
        ('mimic', 'MIMIC: A Generative Multimodal Foundation Model for Biomolecules', 2026,
         'https://arxiv.org/html/2604.24506v1', 'arXiv:2604.24506v1', '10.48550/arXiv.2604.24506'),
        ('genome-factory', 'Genome-Factory: A Library for Tuning, Deploying, and Interpreting Genomic Foundation Models', 2026,
         'https://arxiv.org/html/2509.12266v3', 'arXiv v3, 2026-11-05; first posted 2025', '10.48550/arXiv.2509.12266'),
        ('protberta', 'Optimizing protein tokenization: reduced amino acid alphabets for efficient and accurate protein language models', 2026,
         'https://pmc.ncbi.nlm.nih.gov/articles/PMC13340227/', 'Bioinformatics 42,Supplement_1,btag226', '10.1093/bioinformatics/btag226'),
    ]
    adoption_papers = {'dnachunker','patchdna','genezip','ribospan','mimic','genome-factory','protberta'}
    paper_sources = {}
    for key,title,year,url,version,doi in specs:
        notes = None
        if key == 'gfmbench':
            notes = 'Paper abstract/metadata and pinned repository documentation inspected. Full-text PDF retrieval was rate-limited; no full-paper audit claimed. Distinct from the earlier GFMBench name used by the OmniGenBench authors.'
        if key == 'dna-foundation':
            notes = 'Published full text is available at PMC. Selected paper sections were inspected through web retrieval and the pinned analysis README was inspected; a local full-text cache was not obtained. Individual dataset/target and protocol decomposition remains pending.'
        if key == 'metagene1':
            notes = 'Included as the introducing source for Gene-MTEB (section 5.3), not an expansion of the primary model list.'
        if key == 'patchdna':
            notes = 'Adoption evidence from the author-hosted submission PDF, Tables 1–3 and section 4.2–4.4. Later ICLR publication metadata does not change which PDF was inspected. Comparator numbers can be quoted from original benchmarks rather than rerun.'
        paper_sources[key] = literature(key,title,year,url,version,doi=doi,
            scope='adoption-evidence' if key in adoption_papers else ('associated-model' if key in ('metagene1','dnabert2','nt-original-paper') else 'benchmark'),
            status='journal' if key in ('dna-foundation','nt-original-paper','protberta') else ('conference' if key in ('dnachunker','bend-original','guanine-original','lrb') else 'preprint'),notes=notes)

    def pe(key, slug, locator, statement, anchor=None, needle=None):
        row = downloads.get(key,{})
        if needle and 'text_path' in row and 'error' not in row:
            assert needle.casefold() in (ROOT / row['text_path']).read_text().casefold(), (key,needle)
        return c.ev('project-'+slug,paper_sources[key],locator,statement,
                    url=next(s['url'] for s in c.rows['sources'] if s['id']==paper_sources[key])+(anchor or ''))

    # Register publisher versions without overwriting evidence from earlier releases.
    c.source('project-geneb-published','GENEB published conference paper',
             'https://proceedings.mlr.press/v306/ledneva26b.html','paper','ICML 2026, PMLR306:63325–63391',
             downloads.get('geneb-published',{}).get('text_path'))
    geneb_pub=c.ev('project-geneb-publication','project-geneb-published','Publisher metadata and benchmark definition',
                  'GENEB is a dedicated benchmarking paper published at ICML 2026. Publication and an author-run leaderboard do not establish independent adoption.')
    for p in c.rows['papers']:
        if p['id']=='geneb':p['status']='conference';p['notes']='ICML 2026 conference version registered separately; existing task evidence remains tied to its inspected arXiv/code versions.'
    c.field('papers','geneb','status',geneb_pub)
    c.source('project-guanine-update','GUANinE v1.1 published full text',
             'https://pmc.ncbi.nlm.nih.gov/articles/PMC13501288/','paper','Bioinformatics 2026,btag427',
             downloads['guanine-update']['text_path'])
    guanine_update=c.ev('project-guanine-update','project-guanine-update','Introduction; Methods and datasets',
                        'GUANinE v1.1 extends v1.0 with variant interpretation tasks and model comparisons; versions remain distinct.')
    c.field('papers','guanine','notes',guanine_update)

    # README evidence is pinned at an immutable commit, with line-level locators.
    readmes={r['repo']:r for r in json.loads((BASE/'readmes.json').read_text())}
    for r in json.loads((BASE/'extra-readmes.json').read_text()):
        repo=r['repo'];path=BASE/(repo.replace('/','--')+'--README.md');path.write_text(r['content'])
        readmes[repo]={'repo':repo,'ref':r['sha'],'path':'README.md','text':r['content']}
    def re(repo,slug,needle,statement,end=None):
        r=readmes[repo];path=BASE/(repo.replace('/','--')+'--'+r['path'])
        sid='project-readme-'+slug
        c.source(sid,repo+': '+r['path'],f"https://github.com/{repo}/blob/{r['ref']}/{r['path']}",
                 'repository-file',r['ref'],str(path.relative_to(ROOT)))
        lines=r['text'].splitlines();start=next(i+1 for i,s in enumerate(lines) if needle in s)
        stop=next((i+1 for i,s in enumerate(lines) if i+1>=start and end and end in s),start)
        return c.ev('project-'+slug,sid,f'Lines {start}–{stop}',statement,'documentation',
                    url=f"https://github.com/{repo}/blob/{r['ref']}/{r['path']}#L{start}-L{stop}")

    intent={
        'gb':'gb-definition','dart':'dart-definition','traitgym':'traitgym-definition',
        'rna':'rnagym-definition','mrna':'mrna-catalog','dgeb':'dgeb-definition',
        'bend':pe('bend-original','bend-intent','Introduction; Tasks and datasets','Seven human-genome tasks and an adaptable embedding/readout framework are the main benchmark contribution.',anchor='#S1',needle='adaptable benchmarking framework'),
        'lrb':pe('lrb','lrb-intent','PDF pp.1–3; benchmark definition','Dedicated long-range evaluation resource with task definitions, baselines and context-length experiments.',needle='Genomics Long-Range Benchmark'),
        'dnalongbench':pe('dnalongbench','dnalong-intent','Abstract; Tasks and Datasets','Dedicated benchmark spanning enhancer–gene links, eQTLs, contact maps, regulatory tracks and initiation profiles.',needle='five important genomics tasks'),
        'omnigenbench':pe('omnigenbench','omni-intent','Abstract; Section 2, framework and benchmark modules','Dedicated benchmarking software integrating existing DNA/RNA suites; integrations do not create independent datasets.',anchor='#S2',needle='five benchmark suites'),
        'genbench':pe('genbench','genbench-intent','Introduction; datasets; Codebase Structure','Dedicated benchmarking paper and modular framework. Downstream reuse must be verified separately.',needle='modular'),
        'gfmbench':re('NVIDIA/GFMBench-api','gfm-intent','# GFMBench-API','Dedicated model/task middleware and benchmark implementations; not evidence of external users.',end='## Quick Start'),
        'gene-mteb':pe('metagene1','gene-mteb-intent','Section 5.3; Table 3','Gene-MTEB is introduced within METAGENE-1 evaluation: eight classification and eight clustering task entries in this paper.',anchor='#S5.SS3',needle='Genomic Embedding Benchmark'),
        'dna-foundation':re('ChongWuLab/dna_foundation_benchmark','dna-foundation-intent','## Introduction','Dedicated comparative evaluation of DNA model embeddings; paper, processed datasets and analysis scripts are provided.',end='## References'),
        'qc':re('genomic-benchmarks/genomic-benchmarks-audit','qc-intent','93','A separate dataset-QC/audit effort. It is not the Grešová et al. 2023 Genomic Benchmarks dataset collection.',end='## What the run found'),
        'bacbench':re('macwiatrak/BacBench','bacbench-intent','# BacBench','Standalone reusable multi-scale bacterial benchmark; five active tasks and deprecated strain clustering are distinguished.',end='## Setup'),
    }
    loam=re('Soilytix/gLMBench','loam-use','## What it measures','LOAM independently evaluates BacBench essentiality, DGEB DNA EC and prokaryotic RNAGym assays; subset use does not validate full parent suites.',end='**What you can do')

    # Source-only collections are explicit registrations, not artificial task panels.
    registrations=[
        ('bend-original','BEND (original)','Original seven-task human-genome benchmark; separate from BEND 2.0.','bend', 'bend-original'),
        ('lrb','Genomics Long-Range Benchmark (LRB)','Configurable-context human regulatory and variant benchmarks.','lrb','lrb'),
        ('dnalongbench','DNALongBench','Long-input prediction of gene regulation, eQTLs and chromatin contacts.','dnalongbench','dnalongbench'),
        ('genbench','GenBench','Short- and long-input genomic prediction collection.','genbench','genbench'),
        ('dna-foundation','DNA Foundation Benchmark','Sequence classification, personal expression, variant effects and TAD analysis.','dna-foundation','dna-foundation'),
        ('gene-mteb','Gene-MTEB','Metagenomic sequence embedding classification and clustering.','gene-mteb','metagene1'),
    ]
    for id,name,description,key,paper in registrations:
        c.suite(id,name,description,intent[key],paper,paper_sources[paper],status='registered',
                note='Paper/source registered in the project review. Individual dataset × target decomposition, released-data mapping and protocol verification remain pending. Published task counts are not imported as audited task records.')
    # Repair missing source-paper attribution without changing any task or protocol.
    for suite in c.rows['evaluations']:
        if suite['id']=='gue':
            suite['paper_id']='dnabert2'
            c.field('evaluations','gue','paper_id',pe('dnabert2','gue-paper','Introduction; GUE benchmark','GUE is introduced with DNABERT-2; manuscript versions and repository task inventories differ.',needle='Genome Understanding Evaluation'))
        if suite['id'] in ('nt-original','nt-revised'):
            suite['paper_id']='nt-original-paper'
            c.field('evaluations',suite['id'],'paper_id',pe('nt-original-paper','nt-paper-'+suite['id'],'Downstream tasks and evaluation','The NT model paper is the associated source; this link does not equate original and revised datasets.',needle='downstream'))
    c.finding(None,'GUE is version-dependent: the supplied list describes an original 28-dataset/7-category suite, whereas DNABERT-2 arXiv v2 describes 36 datasets across 9 tasks. Existing selective GUE records are retained; neither headline count is treated as complete artifact-audited coverage.',
              'project-gue-paper',suite='gue',severity='version-difference')
    c.finding(None,'Gene-MTEB README says four clustering tasks in its overview but lists four human-virus and four HMP clustering entries; METAGENE-1 section 5.3 describes eight. Reconcile implementation and actual datasets before task expansion.',
              re('metagene-ai/gene-mteb','gene-mteb-count','We add in total','README overview and listed task modules have inconsistent clustering counts.',end='## Installation'),suite='gene-mteb',severity='discrepancy')

    def review(id,name,decision,dedicated,rationale,evidence,collections=(),papers=(),description=None,scope_note=None):
        c.add('project_reviews',id=id,name=name,decision=decision,dedicated=int(dedicated),reviewed=DATE,
              search_scope='Supplied candidate list and all previously registered collections; primary papers, pinned repositories and targeted searches for external evaluation/software use. This is a dated, non-exhaustive adoption review, not a citation-count survey.',
              rationale=rationale,evidence_id=evidence)
        if decision=='qualified':
            c.add('projects',id=id,name=name,review_id=id,description=description or rationale,
                  scope_note=scope_note or 'Project membership does not establish dataset equivalence, full-suite coverage, task validity, or original Evo 2 use. See cited release/subset-specific adoption records.',evidence_id=evidence)
        for eid,relation,note in collections:
            collection=next(s for s in c.rows['evaluations'] if s['id']==eid)
            c.add('project_review_evaluations',review_id=id,evaluation_id=eid,relation=relation,note=note,evidence_id=collection['evidence_id'])
        for pid,relation in papers:
            paper=next(p for p in c.rows['papers'] if p['id']==pid)
            link=c.ev('project-paper-link-'+id+'-'+pid,paper['source_id'],'Paper identity and catalogue relationship',
                      f'This source is linked to {name} as {relation.replace("-"," ")}. The relationship is curatorial; it does not equate paper, code or dataset versions.','curatorial')
            c.add('project_review_papers',review_id=id,paper_id=pid,relation=relation,evidence_id=link)

    yes=[
        ('gb','Genomic Benchmarks (2023)', [('gb','defines','The Grešová et al. dataset collection. Shared naming with the later QC/audit ecosystem does not establish release or project identity.')], [('gb','introducing')], 'Dedicated sequence-classification dataset package and reusable evaluation resource.'),
        ('dart','DART-Eval',[('dart','defines','Task numbers contain distinct targets and adaptation procedures.')],[('dart','introducing')],'Dedicated regulatory DNA benchmark with zero-shot, probed and fine-tuned comparisons.'),
        ('traitgym','TraitGym',[('traitgym','defines','Control matching and human variant cohorts remain task/protocol specific.')],[('traitgym','introducing')],'Dedicated benchmark of causal regulatory variant prioritization.'),
        ('bend','BEND',[('bend-original','defines','Independent adoption evidence below concerns original BEND.'),('bend','successor-release','BEND 2.0 is a successor. Original BEND adoption is not evidence of independent BEND 2.0 adoption.')],[('bend-original','introducing'),('bend','update')],'Dedicated human genomic benchmark with original BEND and separately versioned BEND 2.0.'),
        ('lrb','Genomics Long-Range Benchmark',[('lrb','defines','2024 paper version and current dataset release require task-level reconciliation.')],[('lrb','introducing')],'Dedicated benchmark with configurable sequence context and human regulatory/variant targets.'),
        ('dnalongbench','DNALongBench',[('dnalongbench','defines','Published five task families; individual task records are pending.')],[('dnalongbench','introducing')],'Dedicated long-range genomic prediction benchmark.'),
        ('rna','RNAGym',[('rnagym','defines','DNA-model fitness scoring uses subsets of an RNA resource; structure evaluation is distinct.')],[('rna','introducing')],'Dedicated RNA fitness and structure benchmark used by nucleotide models.'),
        ('mrna','mRNABench',[('mrnabench','defines','Released catalogue and original paper have different inventories; linked targets retain versions.')],[('mrna','introducing')],'Dedicated mature-mRNA representation benchmark with common probing procedures.'),
        ('dgeb','DGEB',[('dgeb','defines','DNA/RNA and protein task interfaces are distinct. Protein-only adoption is marked below.')],[('dgeb','introducing')],'Dedicated functional/evolutionary embedding evaluation across nucleic-acid and protein modalities.'),
        ('bacbench','BacBench',[('bacbench','defines','Five active task families; deprecated clustering is not made active by historical use.')],[],'Dedicated multi-scale bacterial benchmark, released separately from the later BacLM addition.'),
    ]
    for id,name,collections,papers,description in yes:
        review(id,name,'qualified',True,'Dedicated benchmark effort with at least two documented independent adopter groups; evidence and used subsets are listed separately.',intent[id],collections,papers,description)

    def adoption(review_id,slug,group,paper,evidence,scope,independence='independent',kind='evaluation-use',note=None):
        c.add('project_adoptions',id='adoption-'+slug,review_id=review_id,paper_id=paper,adopter_group=group,
              kind=kind,independence=independence,scope=scope,
              independence_note=note or 'External adopter group identified from the cited publication/release, distinct from the benchmark maintainer group. Independence is a curatorial assessment, not institutional or funding independence.',evidence_id=evidence)
        if paper and not any(r['review_id']==review_id and r['paper_id']==paper for r in c.rows['project_review_papers']):
            c.add('project_review_papers',review_id=review_id,paper_id=paper,relation='adoption-evidence',evidence_id=evidence)

    # Actual new-model evaluations, not every copied comparator row, establish use.
    gb_use=pe('dnachunker','chunker-gb','Section 4.1; Table 3','DNAChunker evaluates Genomic Benchmarks; this is external benchmark use, not a claim all comparator models were rerun.',needle='Genomic Benchmarks')
    adoption('gb','gb-chunker','KAIST / INOCRAS DNAChunker','dnachunker',gb_use,'Genomic Benchmarks sequence-classification evaluation.')
    adoption('gb','gb-generator','GENERator author group','generator','generator-eval-methods','Original GENERator evaluation on the Genomic Benchmarks dataset collection.')
    patch_dart=pe('patchdna','patch-dart','Section 4.2; Table 1; PDF pp.6–7','PatchDNA runs DART tasks, using zero-shot scoring where available and trained probes for other tasks; comparator scores can be inherited.',needle='DART-Eval')
    adoption('dart','dart-patch','Relation Therapeutics PatchDNA','patchdna',patch_dart,'DART tasks 1–5 with protocol-specific zero-shot and frozen-probe settings.')
    adoption('dart','dart-evo','Arc Institute / Evo 2','evo','evo-a3','Original Evo 2 DART tasks 1,2,5 only; caQTL/dsQTL endpoints, not full-suite use.')
    carbon_trait=c.ev('project-carbon-traitgym','carbon-paper','Evaluation benchmarks; TraitGym Mendelian; Appendix E',
                      'Carbon reports TraitGym Mendelian evaluations, separately from its ClinVar and BRCA2 tests. The Carbon author group is external to the TraitGym benchmark authors.')
    ceno_trait=c.ev('project-ceno-traitgym','ceno-paper','Title-page author list; variant-effect evaluation; TraitGym context comparison',
                    'Shanghai AI Laboratory and collaborators report CENO TraitGym Mendelian/complex-trait evaluations; this is external to the Song lab TraitGym author group.')
    adoption('traitgym','trait-carbon','Hugging Face Carbon','carbon',carbon_trait,'TraitGym Mendelian variant evaluation; protocol and cohort documented separately.')
    adoption('traitgym','trait-ceno','Shanghai AI Laboratory / CENO','ceno',ceno_trait,'TraitGym Mendelian and complex-trait evaluation with context/protocol variants.')
    adoption('traitgym','trait-gpn','Song lab GPN-Star','gpn','gpn-benchmarks','TraitGym cohorts used in GPN-Star; retained as related-author follow-up, not independent adoption.',independence='shared-authorship',note='TraitGym and GPN-Star are Song lab/Benegas-lineage work; this follow-up does not contribute to the external-group threshold.')
    adoption('bend','bend-chunker','KAIST / INOCRAS DNAChunker','dnachunker',pe('dnachunker','chunker-bend','Section 4.1; Table 4; PDF p.8','DNAChunker reports original BEND results across seven tasks.',needle='BEND benchmark'),'Original BEND, seven downstream tasks. No BEND 2.0 use asserted.')
    adoption('bend','bend-patch','Relation Therapeutics PatchDNA','patchdna',pe('patchdna','patch-bend','Section 4.3; Table 2; Appendix A.3.3','PatchDNA evaluates original BEND using frozen embeddings and fitted probes; copied comparator rows are not new experiments.',needle='original BEND evaluation protocol'),'Original BEND gene finding, chromatin annotation and additional long-range/VEP endpoints; not BEND 2.0.')
    adoption('lrb','lrb-patch','Relation Therapeutics PatchDNA','patchdna',pe('patchdna','patch-lrb','Section 4.4; Table 3; Appendix A.3.6','PatchDNA uses LRB CAGE with 50 tracks and 114,688-bp input; fine-tunes models and reports correlations.',needle='50 CAGE tracks'),'LRB CAGE subset; context/readout differs from short classification tasks.')
    adoption('lrb','lrb-factory','Northwestern Genome-Factory','genome-factory',pe('genome-factory','factory-lrb','Appendix; Table 8','Genome-Factory reports LoRA evaluations on LRB and GUANinE. Its aggregate MCC is source-specific and not interchangeable with original regression metrics.',needle='Evaluation on GUANinE'),'LRB aggregate as reported in Table 8; task-level metric/cohort reconciliation pending.')
    adoption('dnalongbench','dnalong-chunker','KAIST / INOCRAS DNAChunker','dnachunker',pe('dnachunker','chunker-dnalong','Section 4.1; Figure 2; Appendix C.4','DNAChunker evaluates five DNALongBench task families using frozen-backbone linear probes; published fine-tuning baselines are distinct.',needle='five long-range genomic prediction tasks'),'Five DNALongBench task families under linear probing, not a reproduction of every full-fine-tuning baseline.')
    adoption('dnalongbench','dnalong-genezip','GeneZip Zhao / Tang group','genezip',pe('genezip','genezip-dnalong','DNALongBench downstream evaluation; Table 3','GeneZip adapts its model to four DNALongBench tasks: contact map, eQTL, enhancer–target gene and initiation signal.',anchor='#S4.SS3',needle='adapting the same pretrained GeneZip checkpoint'),'Four task families; regulatory sequence activity is not included in this adoption record.')
    ribo_rna=pe('ribospan','ribospan-rna','Section 3.4.1; Appendix D','RiboSpan evaluates RNAGym mutation fitness with assay-specific scoring and aggregation.',anchor='#S3.SS4.SSS1',needle='Zero-Shot Mutation Fitness Prediction on RNAGym')
    adoption('rna','rna-ribospan','Shanghai AI Laboratory / RiboSpan','ribospan',ribo_rna,'RNAfitness evaluation; does not establish adoption of every RNAGym structure task.')
    adoption('rna','rna-genosm','Genos-m author group','genosm','genosm-doc-rna','Thirteen prokaryote-related RNAGym assays; subset and scoring differ from the entire suite.')
    adoption('mrna','mrna-ribospan','Shanghai AI Laboratory / RiboSpan','ribospan',pe('ribospan','ribospan-mrna','Section 3.4.2; Appendix E','RiboSpan evaluates six mRNABench task families using frozen transcript representations and linear probes.',anchor='#S3.SS4.SSS2',needle='six mRNABench task families'),'Six mature-transcript task families; not every released mRNABench configuration.')
    adoption('mrna','mrna-mimic','Polymathic AI / MIMIC','mimic',pe('mimic','mimic-mrna','Section 4.2; Appendix D.3; Table S11','MIMIC trains probes on its own representations for mRNABench. Comparator results are copied from prior work; modality conditioning is selected on validation.',anchor='#A4.SS3',needle='we trained a supervised probe on MIMIC representations'),'MIMIC probe experiments count as external use; inherited comparator rows do not. Some inputs include protein/codon modalities.')
    adoption('dgeb','dgeb-loam','Soilytix / LOAM','loam',loam,'DGEB DNA enzyme-classification subset; one task, not the entire DNA/protein suite.',kind='software-use',note='Soilytix/LOAM is an external adopter to TattaBio/DGEB; this is a distinct release/author group, not the DGEB authors’ own gLM2 evaluation.')
    c.source('project-protberta-section','ProtBERTa published DGEB evaluation','https://pmc.ncbi.nlm.nih.gov/articles/PMC13340227/','paper','Bioinformatics 2026,btag226',downloads.get('protberta',{}).get('text_path'))
    protberta=c.ev('project-protberta-dgeb','project-protberta-section','Section 3.2.1; Table 2; Figure 2','Rannon and Burstein evaluate their ProtBERTa models on amino-acid DGEB tasks. This establishes external project adoption only, not nucleotide-task performance.')
    adoption('dgeb','dgeb-protberta','Burstein lab / ProtBERTa','protberta',protberta,'Protein-only DGEB evaluation. No protein-task equivalence or nucleotide-model evaluation is inferred.')
    adoption('bacbench','bacbench-loam','Soilytix / LOAM','loam',loam,'BacBench essentiality reimplementation with frozen probes; parent-suite coverage is partial.',kind='software-use')
    adoption('bacbench','bacbench-genosm','Genos-m author group','genosm','genosm-doc-essential','BacBench essentiality plus phenotype cohorts; source cohorts and splits differ from LOAM.')

    # Dedicated intent without established adoption is retained in the review ledger.
    pending=[
        ('qc','Genomic Benchmarks QC / audit',[],[], 'Dedicated QC/audit ecosystem, distinct from the 2023 dataset collection. No qualifying pair of independent evaluation/software users established; manuscript is in preparation, not a published paper.'),
        ('omnigenbench','OmniGenBench',[],[('omnigenbench','introducing')], 'Substantial dedicated software/paper; two independently verified external adopter groups were not established in this review. Model integrations and author-run demonstrations do not meet the threshold.'),
        ('gfmbench','GFMBench-API',[],[('gfmbench','introducing')], 'Dedicated middleware and released tasks. Two external adopter groups were not established. NVIDIA JEPA-DNA use is same-organization evidence, not automatically independent.'),
        ('genbench','GenBench',[('genbench','defines','Task decomposition pending.')],[('genbench','introducing')], 'Dedicated benchmark paper; citations in reviews and reuse of comparator numbers do not establish two independent users of its released task/protocol collection.'),
        ('dna-foundation','DNA Foundation Benchmark',[('dna-foundation','defines','Task decomposition and overlap reconciliation pending.')],[('dna-foundation','introducing')], 'Dedicated comparative study with released data/code. Two independent external users of this particular processed release/protocol were not established.'),
        ('geneb','GENEB',[('geneb','defines','Existing manifest/protocol records retained.')],[('geneb','introducing')], 'Dedicated published benchmark and public submission harness. No two independently verified external adopter groups established; benchmarking other groups’ models is not their adoption of GENEB.'),
        ('guanine','GUANinE',[('guanine','successor-release','Existing v1.1 task records retained.')],[('guanine-original','introducing'),('guanine','update')], 'Dedicated benchmark, but only one external evaluation group established here (Genome-Factory). v1.0 use does not establish v1.1 adoption.'),
    ]
    for id,name,collections,papers,rationale in pending:
        review(id,name,'adoption-not-established',True,rationale,intent.get(id,'geneb-spec') if id!='guanine' else guanine_update,collections,papers)
    adoption('guanine','guanine-factory','Northwestern Genome-Factory','genome-factory','project-factory-lrb','GUANinE v1.0 only; Table 8 aggregate MCC requires reconciliation with original regression targets.')

    # The remaining existing collections are reviewed against the same definition.
    reviewed={r['evaluation_id'] for r in c.rows['project_review_evaluations']}
    reasons={
        'gue':('GUE',False,'Model-associated benchmark introduced with DNABERT-2. Widely reused, but not a primarily dedicated benchmark project under this catalogue’s definition.'),
        'nt-original':('Nucleotide Transformer benchmark',False,'Model-associated benchmark introduced with NT. Independent reuse does not change the model-centered origin; retained as versioned collections.'),
        'nt-revised':('Nucleotide Transformer revised benchmark',False,'Revised release of a model-associated benchmark; retained separately from original NT without creating a dedicated project.'),
        'pgb':('Plant Genomic Benchmark',False,'Introduced in the AgroNT model paper. Useful multi-species collection, but a model-associated benchmark rather than a dedicated project.'),
        'nabench':('NABench',True,'Dedicated benchmark with paper and released manifest, but two independent adopter groups were not established. Existing registered assays remain in scope.'),
        'bgc':('BGC-Bench',True,'Dedicated benchmark paper; very recent release. Two independent adopter groups were not established. Keep its multimodal task records without a project entry.'),
        'bgcs':('BGCs-Bench',True,'Dedicated benchmarking effort; two independent adopter groups were not established. Distinct from BGC-Bench.'),
        'lambda':('LAMBDA',True,'Dedicated prophage-detection benchmark; two independent adopter groups were not established. Task/source registration remains in scope.'),
        'proteingym':('ProteinGym',False,'Dedicated and adopted protein benchmark, but its project is outside the nucleotide/genomic framework scope. Selected gLM-compatible assays remain linked.'),
    }
    for suite in c.rows['evaluations']:
        if suite['id'] in reviewed:continue
        id=suite['id'];name,dedicated,rationale=reasons.get(id,(suite['name'],False,
            'A model-associated evaluation collection, experimental assay resource, or task-specific method; not a primarily dedicated standardized gLM evaluation framework. Retained as an evaluation source.'))
        decision='adoption-not-established' if dedicated else 'outside-definition'
        review('collection-'+id,name,decision,dedicated,rationale,suite['evidence_id'],
               [(id,'associated-collection','Retained in the task catalogue; no qualified project membership.')],
               [(suite['paper_id'],'introducing' if dedicated else 'associated-model')] if suite['paper_id'] else [])
    # Refine the model-associated origin after the complete collection review.
    for r in c.rows['project_reviews']:
        if r['id']=='collection-gene-mteb':
            r['rationale']='Gene-MTEB is introduced within METAGENE-1 section 5.3. Its software and tasks remain sources; it does not meet the primarily dedicated project requirement.'
    c.source('project-policy','marin-glm project inclusion policy',
             'https://github.com/eric-czech/marin-glm#benchmark-projects','curatorial','2026-11-26')
    policy=c.ev('project-policy','project-policy','Benchmark projects: inclusion and adoption criteria',POLICY,'curatorial')
    for project in c.rows['projects']:
        c.field('projects',project['id'],'review_id',policy,'Project qualification is an explicit curatorial decision supported by purpose and independent-use evidence.')
    # This anonymous submission is a related paper, not a verified version of the
    # current repository. The README still requests a repository citation.
    c.source('project-bacbench-submission','BacBench ICLR 2026 submission',
             'https://openreview.net/pdf?id=2wu96xvRIG','paper','Anonymous ICLR 2026 submission',
             notes='Indexed abstract and task description inspected; direct full-text retrieval blocked by OpenReview. Current repository-to-submission version correspondence remains unresolved.')
    c.paper('bacbench-submission','BacBench: Evaluating Genomic Language Models for Bacteria',
            'project-bacbench-submission',2026,status='conference-submission',scope='benchmark',
            notes='Related anonymous submission describes 11 datasets and 6 tasks. Pinned repository has five active task families plus deprecated strain clustering and says citation details are forthcoming. No acceptance status or current-release equivalence inferred.')
    bac_paper=c.ev('project-bacbench-paper','project-bacbench-submission','Indexed abstract; benchmark definition',
                   'Related BacBench submission describes a dedicated bacterial benchmark; correspondence to the current release and later publication is not established.')
    c.add('project_review_papers',review_id='bacbench',paper_id='bacbench-submission',relation='related-report',evidence_id=bac_paper)
