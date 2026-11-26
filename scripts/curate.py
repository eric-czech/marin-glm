"""Authoring helpers. Emit the committed catalogue JSON from inspected source notes.

The offline database/site build uses data/catalogue.json, not these research snapshots.
"""
from pathlib import Path
import hashlib
import importlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-11-25'
TABLES = ['metadata', 'sources', 'papers', 'models', 'model_properties', 'evidence', 'evaluations', 'tasks',
          'evaluation_tasks', 'variants', 'populations', 'task_populations', 'categories',
          'task_categories', 'protocols', 'metrics', 'protocol_metrics', 'counts',
          'model_evaluations', 'findings', 'field_evidence', 'project_reviews', 'projects',
          'project_review_papers', 'project_review_evaluations', 'project_adoptions']

class Catalogue:
    def __init__(self):
        self.date = DATE
        self.rows = {name: [] for name in TABLES}
        self.ids = {name: set() for name in TABLES}
        self.snapshots = json.loads((ROOT / 'data/source-snapshots.json').read_text())

    def add(self, table, **row):
        if 'id' in row:
            if row['id'] in self.ids[table]:
                raise ValueError(f'Duplicate {table} id: {row["id"]}')
            self.ids[table].add(row['id'])
        self.rows[table].append(row)
        return row.get('id')

    def source(self, id, title, url, kind='paper', version=None, local_path=None, notes=None):
        digest = None
        if local_path and (ROOT / local_path).exists():
            digest = hashlib.sha256((ROOT / local_path).read_bytes()).hexdigest()
        self.add('sources', id=id, title=title, kind=kind, url=url, version=version,
                 retrieved=self.date, sha256=digest, local_path=local_path,
                 availability='available', notes=notes)
        return id

    def paper(self, id, title, source_id, year, status='preprint', scope='benchmark', doi=None, date=None, notes=None):
        return self.add('papers', id=id, title=title, source_id=source_id, year=year,
                        status=status, scope=scope, doi=doi, publication_date=date, notes=notes)

    def ev(self, id, source_id, locator, statement, basis='paper', url=None):
        source = next(s for s in self.rows['sources'] if s['id'] == source_id)
        return self.add('evidence', id=id, source_id=source_id, locator=locator,
                        statement=statement, basis=basis, url=url or source['url'], inspected=self.date)

    def code(self, id, repo, path, needle, statement, end_needle=None, basis='code', ref=None):
        snapshot = next((s for s in self.snapshots if s['repo'] == repo and s['path'] == path and (not ref or s['ref'] == ref)), None)
        if not snapshot:
            raise ValueError(f'Missing snapshot {repo}:{path}')
        sid = 'src-' + id
        self.source(sid, f'{repo}: {path}', snapshot['url'], 'repository-file',
                    snapshot['ref'], snapshot['local'])
        lines = (ROOT / snapshot['local']).read_text().splitlines()
        starts = [i+1 for i, line in enumerate(lines) if needle in line]
        if not starts:
            raise ValueError(f'No evidence literal {needle!r} in {path}')
        start = starts[0]
        end = next((i+1 for i, line in enumerate(lines) if i+1 >= start and end_needle and end_needle in line), start)
        url = snapshot['url'] + f'#L{start}' + (f'-L{end}' if end != start else '')
        return self.ev(id, sid, f'Lines {start}–{end}', statement, basis, url)

    def suite(self, id, name, description, evidence_id, paper_id=None, source_id=None,
              status='partial', note='Task records describe the inspected version; protocol variants are linked separately.', notes=None):
        return self.add('evaluations', id=id, name=name, description=description,
                        paper_id=paper_id, source_id=source_id, status=status, scope_note=note,
                        evidence_id=evidence_id, notes=notes)

    def task(self, id, suite, name, dataset, target, description, task_type, labels,
             evidence, applications=(), capabilities=(), regions=(), populations=(),
             input='Sequence', output='Target prediction', status='paper-audited', limitations=None):
        self.add('tasks', id=id, name=name, dataset_name=dataset, target=target,
                 description=description, task_type=task_type, label_basis=labels,
                 evidence_id=evidence, status=status, limitations=limitations,
                 input_description=input, output_description=output)
        self.member(suite, id, evidence)
        for dimension, values in [('application', applications), ('capability', capabilities), ('region', regions)]:
            for value in values:
                if isinstance(value, tuple):
                    category, relation, rationale = value
                else:
                    category, relation = value, 'relevance' if dimension == 'application' else ('measured' if dimension == 'capability' else 'input')
                    rationale = {'application': 'Proposed application of the measured target; this is a curatorial mapping, not an industrial validation claim.',
                                 'capability': 'Assigned from the task input, output and evaluation procedure in the cited source.',
                                 'region': 'The cited task definition restricts its input or labels to this functional sequence class.'}[dimension]
                self.add('task_categories', task_id=id, category_id=category, relation=relation,
                         rationale=rationale, evidence_id=evidence, attribution='curatorial')
        for p in populations:
            pop, relation, coverage = p if isinstance(p, tuple) else (p, 'sequence-origin', 'Reported for this task; not a claim of complete clade coverage.')
            self.add('task_populations', task_id=id, population_id=pop, variant_id=None,
                     relation=relation, coverage=coverage, evidence_id=evidence)
        return id

    def member(self, suite, task, evidence, note=None):
        if not any(r['evaluation_id'] == suite and r['task_id'] == task for r in self.rows['evaluation_tasks']):
            self.add('evaluation_tasks', evaluation_id=suite, task_id=task, variant_id=None, note=note, evidence_id=evidence)

    def variant(self, task, id, name, evidence, context=None, length=None, revision=None, targets=None, target_unit=None, notes=None):
        return self.add('variants', id=id, task_id=task, name=name, evidence_id=evidence,
                        context=context, input_length=length, dataset_revision=revision,
                        target_count=targets, target_unit=target_unit, notes=notes)

    def protocol(self, task, id, name, evidence, adaptation, interface, split, unit,
                 metrics=(), embeddings=None, fitted=None, selection=None, variant=None, notes=None):
        self.add('protocols', id=id, task_id=task, variant_id=variant, name=name,
                 adaptation=adaptation, requires_embeddings=embeddings, model_interface=interface,
                 fitted_component=fitted, selection=selection, split_rule=split, split_unit=unit,
                 source_evidence_id=evidence, notes=notes)
        for i, metric in enumerate(metrics):
            if isinstance(metric, tuple):
                metric, aggregation = metric
            else:
                aggregation = 'As reported; see protocol notes.'
            self.add('protocol_metrics', protocol_id=id, metric_id=metric,
                     aggregation=aggregation, is_primary=int(i == 0), evidence_id=evidence)
        return id

    def count(self, task, value, unit, evidence, split='total', qualifier='', method='reported', variant=None, protocol=None):
        return self.add('counts', id=f'count-{len(self.rows["counts"])+1:04d}', task_id=task,
                        value=value, unit=unit, evidence_id=evidence, split=split,
                        qualifier=qualifier, method=method, variant_id=variant, protocol_id=protocol)

    def use(self, model, task, evidence, paper, provenance='original-paper', protocol=None, note=''):
        return self.add('model_evaluations', id=f'use-{len(self.rows["model_evaluations"])+1:04d}',
                        model_id=model, task_id=task, protocol_id=protocol, paper_id=paper,
                        provenance=provenance, evidence_id=evidence, note=note)

    def finding(self, task, text, evidence, severity='limitation', suite=None):
        return self.add('findings', id=f'finding-{len(self.rows["findings"])+1:03d}', task_id=task,
                        evaluation_id=suite, severity=severity, description=text, evidence_id=evidence)

    def field(self, table, id, field, evidence, note=None):
        existing=next((r for r in self.rows['field_evidence'] if r['entity_table']==table and r['entity_id']==id and r['field']==field and r['evidence_id']==evidence),None)
        if existing:
            if note and note!=existing['note']:
                existing['note']='; '.join(x for x in (existing['note'],note) if x)
            return
        self.add('field_evidence', entity_table=table, entity_id=id, field=field, evidence_id=evidence, note=note)

def vocabulary(c):
    applications = [
        ('plant-breeding','Plant breeding','Prioritize trait-associated genes and alleles for plant breeding and validation.'),
        ('variant-interpretation','Variant interpretation','Prioritize human disease-associated variants and assess molecular consequences.'),
        ('target-discovery','Genetic target discovery','Connect trait-associated variants to genes and molecular mechanisms.'),
        ('regulatory-engineering','Regulatory-sequence engineering','Predict or select regulatory sequences for desired activity in a specified host or cell context.'),
        ('gene-therapy','Gene-therapy research','Evaluate sequence components and edits relevant to controlled expression in target cells.'),
        ('rna-engineering','RNA engineering','Predict or select RNA translation, stability, binding, localization and molecular function.'),
        ('strain-engineering','Strain engineering','Predict gene function and cellular phenotypes relevant to microbial strain modification.'),
        ('natural-products','Natural-product discovery','Connect biosynthetic sequences to products, chemical properties and substrates.'),
        ('protein-engineering','Protein engineering','Predict experimental consequences of coding variants and enzyme function.'),
        ('microbial-genomics','Microbial genomics','Interpret microbial genes, genomes and mobile elements.'),
        ('genome-annotation','Genome annotation','Locate and classify functional genomic elements.'),
        ('comparative-genomics','Comparative genomics','Characterize homology, evolutionary relationships and sequence constraint.'),
        ('model-development','Model development','Measure sequence modeling, representation or computational properties.'),
    ]
    capabilities = [
        ('functional-prediction','Functional prediction','Predict an experimentally measured or annotated property from sequence.','A task-specific output/readout and appropriate label supervision or score are needed.'),
        ('variant-effects','Variant-effect prediction','Score the consequence of a specified sequence change.','Allele comparison, mutation localization and a declared scoring function are required.'),
        ('sequence-modeling','Sequence modeling','Predict sequence probabilities, held-out bases or natural continuations.','A nucleotide/token probability interface with an explicit token-to-base scoring rule is required.'),
        ('dense-annotation','Dense annotation','Predict labels at individual bases, boundaries or intervals.','Position-preserving representations and a localized output head are required.'),
        ('sequence-retrieval','Sequence retrieval','Rank related sequences or cross-modal matches.','Comparable embeddings or a retrieval score and query/gallery protocol are required.'),
        ('generation','Generation','Produce new sequence; measured generation is distinct from selecting existing candidates.','A generative decoder, sampling or completion procedure is required.'),
        ('conditional-generation','Conditional generation','Generate sequence with a specified prefix, activity or organism condition.','A mechanism for prefix or attribute conditioning and a declared sampling procedure is required.'),
        ('sequence-selection','Sequence selection','Choose candidates for a specified measured response.','An effect predictor and a selection objective/budget are required; a generative model is not necessary.'),
        ('long-context','Long-context evaluation','Explicitly evaluate context length, distal dependencies or retrieval over extended inputs.','Record input span and intervention; long input alone does not establish a long-range biological dependency.'),
        ('context-specific','Context-specific prediction','Predict dependence on tissue, cell state, genetic background or assay host.','A context input or context-specific heads/readouts and matched labels are required.'),
        ('genetic-interactions','Genetic interactions','Predict non-additive effects or dependence on another allele.','Joint mutation/background modeling and an interaction-specific endpoint are required.'),
        ('evolutionary-inference','Evolutionary inference','Predict constraint, evolutionary relationships or functional enrichment.','Record alignments, trees and population information available to the model.'),
        ('structure-prediction','Structure prediction','Predict secondary or tertiary molecular structure.','A structure/contact output and an explicit structure metric are required.'),
    ]
    regions = [
        ('gene','Genes','Gene bodies or gene-level sequence units.'),('cds','Coding sequence','Protein-coding sequence, including synonymous and nonsynonymous variants.'),
        ('exon','Exons','Exonic sequence; not necessarily protein coding.'),('intron','Introns','Intronic sequence.'),
        ('splice','Splice sites','Donor/acceptor sites or splice-region labels.'),('utr5','5′ UTR','Untranslated sequence upstream of the translated CDS.'),
        ('utr3','3′ UTR','Untranslated sequence downstream of the translated CDS.'),('ncrna','Noncoding RNA','Non-protein-coding RNA sequence.'),
        ('lncrna','lncRNA','Long noncoding RNA.'),('rrna','rRNA','Ribosomal RNA.'),('trna','tRNA','Transfer RNA.'),
        ('ribozyme','Ribozymes','Catalytic RNA.'),('aptamer','Aptamers','Nucleic-acid binding constructs.'),
        ('mrna','mRNA','Mature or reporter mRNA.'),('promoter','Promoters','Promoter sequence or promoter annotation.'),
        ('enhancer','Enhancers','Enhancer sequence or enhancer annotation.'),('regulatory','Regulatory DNA','Regulatory intervals without a narrower universal element assignment.'),
        ('tfbs','TF binding sites','Transcription-factor binding motifs or intervals.'),('polya','Polyadenylation sites','Polyadenylation sites or associated signal regions.'),
        ('terminator','Terminators','Transcription termination regions or experimental terminator constructs.'),
        ('bgc','Biosynthetic gene clusters','Multi-gene biosynthetic clusters.'),('operon','Operons','Co-transcribed bacterial gene groups or boundaries.'),
        ('repeat','Repeats / transposable elements','Repeated sequence or transposable-element annotations.'),
        ('genome','Genome-wide sequence','Whole-genome or broadly sampled sequence; does not imply every functional class is evaluated.'),
        ('intergenic','Intergenic DNA','Sequence between annotated genes.'),('chromatin-boundary','Chromatin boundaries','TAD/insulation boundaries and associated genomic intervals.'),
    ]
    for id, name, definition in applications:
        c.add('categories', id=id, dimension='application', name=name, definition=definition, accommodation=None)
    for id, name, definition, accommodation in capabilities:
        c.add('categories', id=id, dimension='capability', name=name, definition=definition, accommodation=accommodation)
    for id, name, definition in regions:
        c.add('categories', id=id, dimension='region', name=name, definition=definition, accommodation=None)
    taxa = [
        ('euk','Eukaryota','domain',None,2759),('bacteria','Bacteria','domain',None,2),('archaea','Archaea','domain',None,2157),('viruses','Viruses','group',None,10239),
        ('animals','Animalia','kingdom','euk',33208),('plants','Viridiplantae','kingdom','euk',33090),('fungi','Fungi','kingdom','euk',4751),
        ('mammals','Mammalia','class','animals',40674),('insects','Insecta','class','animals',50557),('nematodes','Nematoda','phylum','animals',6231),('birds','Aves','class','animals',8782),('teleosts','Teleostei','clade','animals',32443),
        ('human','Homo sapiens','species','mammals',9606),('mouse','Mus musculus','species','mammals',10090),('pig','Sus scrofa','species','mammals',9823),('chicken','Gallus gallus','species','birds',9031),('zebrafish','Danio rerio','species','teleosts',7955),('fly','Drosophila melanogaster','species','insects',7227),('worm','Caenorhabditis elegans','species','nematodes',6239),
        ('angiosperms','Angiosperms','clade','plants',3398),('poaceae','Poaceae','family','angiosperms',4479),('brassicaceae','Brassicaceae','family','angiosperms',3700),('solanaceae','Solanaceae','family','angiosperms',4070),('fabaceae','Fabaceae','family','angiosperms',3803),
        ('arabidopsis','Arabidopsis thaliana','species','brassicaceae',3702),('rice','Oryza sativa','species','poaceae',4530),('maize','Zea mays','species','poaceae',4577),('sorghum','Sorghum bicolor','species','poaceae',4558),('wheat','Triticum aestivum','species','poaceae',4565),('barley','Hordeum vulgare','species','poaceae',4513),('setaria','Setaria italica','species','poaceae',4555),('brachypodium','Brachypodium distachyon','species','poaceae',15368),
        ('tomato','Solanum lycopersicum','species','solanaceae',4081),('soybean','Glycine max','species','fabaceae',3847),('medicago','Medicago truncatula','species','fabaceae',3880),('clover','Trifolium pratense','species','fabaceae',57577),('cassava','Manihot esculenta','species','angiosperms',3983),('chlamydomonas','Chlamydomonas reinhardtii','species','plants',3055),
        ('yeast','Saccharomyces cerevisiae','species','fungi',4932),('ecoli','Escherichia coli','species','bacteria',562),('phages','Bacteriophages','host-defined group','viruses',None),('synthetic','Synthetic constructs','experimental category',None,None),
    ]
    for id, name, rank, parent, taxid in taxa:
        c.add('populations', id=id, name=name, rank=rank, parent_id=parent, ncbi_taxid=taxid,
              notes='Catalogue grouping; task coverage is specified on individual records. Host-defined and synthetic groups are not taxonomic ranks.' if taxid is None else None)
    metrics = [
        ('auroc','AUROC','Area under the receiver operating characteristic curve.','higher'),
        ('ap','Average precision','Average precision as implemented by the cited scorer; distinguish from trapezoidal PR area.','higher'),
        ('auprc','AUPRC','Area under the precision–recall curve; integration convention follows the source.','higher'),
        ('accuracy','Accuracy','Fraction of correctly classified or recovered targets.','higher'),
        ('balanced-accuracy','Balanced accuracy','Mean recall across classes.','higher'),
        ('mcc','MCC','Matthews correlation coefficient.','higher'),('f1','F1','Harmonic mean of precision and recall; aggregation follows the protocol.','higher'),
        ('pearson','Pearson correlation','Linear association with measured targets.','higher'),('spearman','Spearman correlation','Rank association with measured targets.','higher'),
        ('abs-spearman','Absolute Spearman correlation','Absolute rank correlation; sign is discarded.','higher'),
        ('mse','MSE','Mean squared prediction error.','lower'),('r2','R²','Coefficient of determination.','higher'),
        ('recall10','Recall@10','Fraction of queries with a relevant item among ten retrieved candidates.','higher'),
        ('recall5','Recall@5','Recall among five retrieved candidates.','higher'),('map5','MAP@5','Mean average precision at rank five.','higher'),
        ('v-measure','V-measure','Homogeneity/completeness score for clustering.','higher'),('bits','Bits per base','Base-normalized negative log probability.','lower'),
        ('percentile','Rank percentile','Rank of a selected candidate among experimentally measured alternatives.','lower'),
        ('utility','Selection utility','Task-specific utility of selected measured sequences.','higher'),('enrichment','Enrichment','Ratio/enrichment defined by the cited population-genetic analysis.','higher'),
        ('discoveries','Association discoveries','Significant gene–phenotype associations under the declared multiplicity correction.','higher'),
        ('exact-match','Exact match','Fraction of targets recovered exactly.','higher'),('ndcg','NDCG','Normalized discounted cumulative gain.','higher'),
        ('recall50','Recall@50','Recall among fifty retrieved candidates.','higher'),
        ('recall-auc','Recall AUC','Area under the causal-SNP recall curve; source defines rank/threshold axis.','higher'),
        ('js-distance','Jensen–Shannon distance','Distance between predicted and observed profile distributions.','lower'),
        ('js-improvement','Normalized profile improvement','Clipped improvement of profile Jensen–Shannon distance over a uniform profile.','higher'),
        ('runtime','Runtime','Elapsed inference or evaluation time under a fixed workload.','lower'),
    ]
    for id, name, definition, direction in metrics:
        c.add('metrics', id=id, name=name, definition=definition, direction=direction)

def main():
    c = Catalogue()
    c.add('metadata', key='updated', value='2026-11-26')
    c.add('metadata', key='repository', value='eric-czech/marin-glm')
    c.add('metadata', key='task_unit', value='Dataset × prediction target; species, tracks, conditions and protocols are linked variants.')
    vocabulary(c)
    for module in ('sources', 'evo', 'benchmarks', 'model_evals', 'gpnstar', 'paper_extensions', 'new_models', 'artifacts', 'plantcad', 'projects', 'audit_followup'):
        c.date = '2026-11-26' if module in ('plantcad','projects','audit_followup') else DATE
        importlib.import_module('curation.' + module).populate(c)
    (ROOT / 'data/catalogue.json').write_text(json.dumps(c.rows, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({name: len(rows) for name, rows in c.rows.items()}, indent=2))

if __name__ == '__main__':
    main()
