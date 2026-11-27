"""Final source review of DeepD, GPN-Star, AIDO.DNA2 and Genos-m.

This is an intentional authoring reconciliation, never a networked build step.
Missing source information is recorded separately from completion of source
review. Released demonstrations are not substituted for paper-wide cohorts.
"""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DATE = '2026-11-27'
DEEPD = '2896082aa1b7483d3c4062e125050ebc815aea25'
DEEPD_HF = 'b1b888e2482a06a51b6bf03fa5091f40b9b57e96'
DEEPD_SITE = '86c4d3d3f0fe9357b2cd64514859464a8848a90d'
GPN_CURRENT = 'dc5fd287599f2955a79d010bca0e0f7f8178c67e'
GPN_ARCHIVE = '30dee6cf45849dfdcfc043ca8baf44fd6ba51d74'
GENOS = 'f0b05fdbd5441fe74bf41bb2e8750f03e2c50a03'
REMOVED_TASKS = ['deepd-annotation-bacteria', 'deepd-annotation-maize']


def populate(d):
    def put(table, value, keys=('id',)):
        rows = d.setdefault(table, [])
        old = next((r for r in rows if all(r.get(k) == value.get(k) for k in keys)), None)
        if old is None:
            rows.append(value)
        else:
            old.update(value)
        return value.get('id')

    def row(table, id):
        return next(r for r in d[table] if r.get('id') == id)

    def source(id, title, url, version, path=None, kind='repository-file', notes=None,
               availability='available'):
        f = ROOT / path if path else None
        put('sources', dict(id=id, title=title, url=url, version=version, kind=kind,
            retrieved=DATE, sha256=hashlib.sha256(f.read_bytes()).hexdigest() if f and f.exists() else None,
            local_path=path, availability=availability, notes=notes))
        return id

    def ev(id, sid, loc, text, basis='documentation', url=None):
        put('evidence', dict(id=id, source_id=sid, locator=loc, statement=text,
            basis=basis, url=url or row('sources', sid)['url'], inspected=DATE))
        return id

    def field(table, id, name, eid, note=None):
        put('field_evidence', dict(entity_table=table, entity_id=id, field=name,
            evidence_id=eid, note=note), ('entity_table', 'entity_id', 'field', 'evidence_id'))

    def limit(table, id, name, reason, text, eid):
        slug = 'model-final-' + id + '-' + name.replace(' ', '-').replace(':', '-')
        put('source_limits', dict(id=slug, entity_table=table, entity_id=id, field=name,
            reason=reason, detail=text, evidence_id=eid))
        field(table, id, name, eid, text)

    def review(table, id, scope, eids, limitations=None):
        put('source_reviews', dict(id='model-final-' + table + '-' + id,
            entity_table=table, entity_id=id, reviewed=DATE, scope=scope,
            evidence_ids_json=json.dumps(list(dict.fromkeys(eids))), limitations=limitations or ''),
            ('entity_table','entity_id'))

    def finding(id, tid, collection, text, eid, severity='limitation'):
        put('findings', dict(id='model-final-' + id, task_id=tid, evaluation_id=collection,
            severity=severity, description=text, evidence_id=eid))

    def count(id, tid, value, unit, eid, split='released cohort', method='measured',
              qualifier=None, variant=None, protocol=None):
        put('counts', dict(id='model-final-' + id, task_id=tid, value=value, unit=unit,
            evidence_id=eid, split=split, method=method, qualifier=qualifier or '',
            variant_id=variant, protocol_id=protocol))

    def output(tid, category, form, unit, eid, axis='none', rationale=None, limitations=None,
               status='supported'):
        o = next((r for r in d['task_outputs'] if r['task_id'] == tid), None)
        if o is None:
            o = dict(id=tid+'-output-review', task_id=tid)
            d['task_outputs'].append(o)
        o.update(category_id='output-' + category, prediction_form=form, scoring_unit=unit,
            position_axis=axis, structure_scope='none', status=status, evidence_id=eid,
            rationale=rationale or row('evidence', eid)['statement'], limitations=limitations)
        d['task_categories'] = [x for x in d['task_categories']
            if not(x['task_id'] == tid and x['category_id'].startswith('output-'))]
        put('task_categories', dict(task_id=tid, category_id='output-' + category,
            relation='scored-output', rationale=o['rationale'], evidence_id=eid,
            attribution='curatorial'), ('task_id', 'category_id', 'relation'))

    def code(id, repo, revision, file, text, path=None, first=1, last=None):
        u = f'https://github.com/{repo}/blob/{revision}/{file}'
        sid = source(id + '-source', repo + ' / ' + file, u, revision, path)
        binary = file.endswith(('.webp', '.png', '.pdf'))
        return ev(id, sid, file, text, 'documentation' if binary else 'code',
            u if binary else u + f'#L{first}' + (f'-L{last}' if last else ''))

    def resource(id, sid, title, kind, host, url, revision, eid, notes=None,
                 availability='public', tasks=(), collection=None, relation=None, variant=None):
        notes=notes or ''
        put('data_resources', dict(id=id, source_id=sid, title=title, kind=kind, host=host,
            url=url, revision=revision, availability=availability, evidence_id=eid, notes=notes))
        relation = relation or ('evaluation-code' if kind == 'evaluation-code' else
            'results' if kind == 'results' else 'identity-manifest' if kind == 'manifest' else 'evaluation-data')
        for tid in tasks:
            put('task_resources', dict(task_id=tid, resource_id=id, relation=relation,
                variant_id=variant, evidence_id=eid, note=notes), ('task_id', 'resource_id', 'relation'))
        if collection:
            put('evaluation_resources', dict(evaluation_id=collection, resource_id=id,
                relation=relation, evidence_id=eid, note=notes), ('evaluation_id', 'resource_id', 'relation'))

    def associated(model):
        return {r['task_id'] for r in d['model_evaluations'] if r['model_id'] == model}

    # Source review includes complete immutable repository trees, not just the
    # demonstration README cached in the earlier catalogue pass.
    cache = 'research/artifacts/final-audit/'
    deep_tree = source('model-final-deepd-tree', 'DeepD complete official code release',
        f'https://github.com/biomap-research/DeepD/tree/{DEEPD}', DEEPD,
        cache + 'model-gaps-releases/DeepD-tree.json', 'repository-tree',
        'Complete recursive Git tree and complete archive downloaded. Runtime HF subtrees separately enumerated.')
    deep_release = ev('model-final-deepd-release', deep_tree, 'Complete Git tree; runtime asset links in README',
        'The release contains zero-shot coding ClinVar, H3 embedding-classifier, human HBB routing, species-conditioned generation and one yeast synteny demonstration. It does not contain bacterial/eukaryotic/ncRNA DMS manifests, mouse/human TF accession manifests, full routing training/test coordinates, or complete maize routing input arrays.')
    hf_sid = source('model-final-deepd-hf', 'DeepD dataset / pinned runtime assets',
        f'https://huggingface.co/datasets/biomap-research/DeepD/tree/{DEEPD_HF}', DEEPD_HF,
        cache + 'model-gaps-deepd/hf-root-tree.json', 'dataset-repository',
        'Root is fine_tune/H3 and interpretability. The complete 27-entry interpretability subtree was enumerated; H3 CSVs are separately audited in the existing catalogue.')
    hf_ev = ev('model-final-deepd-hf-release', hf_sid, 'Root and complete interpretability subtree',
        'Pinned HF root contains fine_tune/H3 and interpretability only. Interpretability releases eight 20,000×576 feature arrays and twelve human XGBoost model files; no complete 90,000-row classifier split arrays or bacterial/maize routing assets are present.')
    resource('deepd-h3-release-data', hf_sid, 'DeepD released H3 sequences, labels and embeddings',
        'dataset', 'huggingface', f'https://huggingface.co/datasets/biomap-research/DeepD/tree/{DEEPD_HF}/fine_tune/H3',
        DEEPD_HF, hf_ev, 'Released H3 example; paper H4/TF cohorts are not present under this subtree.',
        tasks=['gue-H3'], collection='deepd-evals')
    meta = source('model-final-deepd-publication-metadata', 'DeepD bioRxiv publication metadata',
        'https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.13.758170',
        'bioRxiv v 1; retrieved 2026-11-27', cache+'model-gaps-deepd/api.data', 'publication-metadata')
    metae = ev('model-final-deepd-date', meta, 'API collection record for the exact DOI',
        'bioRxiv reports version 1 posted 2026-10-18, DOI 10.64898/2026.10.13.758170; no journal publication is listed.')
    row('papers', 'deepd').update(doi='10.64898/2026.10.13.758170', publication_date='2026-10-18', status='bioRxiv preprint v 1')
    for name in ['doi', 'publication_date', 'status']:
        field('papers', 'deepd', name, metae)
    dc2_source=source('model-final-deepd-method-details', 'DeepD DC2 Method Details',
        'https://www.biorxiv.org/content/biorxiv/early/2026/10/18/2026.10.13.758170/DC2/embed/media-2.docx?download=true',
        'bioRxiv v 1; linked file supplements/758170_file 03.docx', kind='supplement',
        notes='Supplementary-material page explicitly lists a second document labelled Method Details. Normal downloads returned HTTP 429; both web retrieval tools failed on 2026-11-27. Contents were not retrieved or inspected.',
        availability='not-retrieved')
    dc2=ev('model-final-deepd-unretrieved-methods',dc2_source,
        'Linked Method Details document; retrieval state, not document contents',
        'The public supplementary-material page links DC2 Method Details, separately from DC1 Supplementary Figures. DC1 was inspected, including its images. DC2 normal downloads returned HTTP 429 and web tools could not retrieve it on 2026-11-27; no statement about DC2 contents is asserted.',
        'documentation','https://www.biorxiv.org/content/10.64898/2026.10.13.758170v1.supplementary-material')
    for table,id in [('papers','deepd'),('evaluations','deepd-evals')]:
        limit(table,id,'method_details_document','not-retrieved',
            'Identified linked primary supplement DC2 could not be downloaded (HTTP 429; normal DOI/dated-download URLs and both web tools tried 2026-11-27). It was not part of completed content inspection. This is an access failure, not evidence that methods were unpublished.',dc2)
    for family in ['bacterial-fitness', 'euk-fitness', 'ncrna-fitness']:
        t = row('tasks', 'deepd-' + family)
        t['status'] = 'source-limited'
        if family == 'ncrna-fitness':
            t['description'] = 'Seven mutational fitness assays spanning rRNA, tRNA and ribozymes; exact assay identities and source-specific processing are not supplied by the inspected available release.'
        elif family == 'euk-fitness':
            t['description'] = 'Five eukaryotic protein mutational fitness assays; exact assay identities are not supplied by the inspected available release.'
        t['limitations'] = ('The main paper reports this panel and its assay count but does not name its constituent assay IDs. '
            'The inspected DC1 supplement contains figures and captions, and the pinned complete GH and HF releases do not supply the panel manifest. '
            'The separately linked DC2 Method Details is identified explicitly in source availability; its contents must not be inferred from another model’s benchmark panel.')
        limit('tasks', t['id'], 'assay_ids', 'not-released',
            'Exact assay IDs and processed variant manifest are absent from the inspected complete GH/HF releases. Main-paper counts 7/5/7 do not establish equivalence to an Evo panel.', deep_release)
        limit('tasks', t['id'], 'retained_variant_counts', 'not-reported',
            'Main paper and DC1 captions report assay-level correlations and panel sizes, not per-assay scored variant counts.', 'deepd-panel-gap-review')
        p = row('protocols', t['id'] + '-protocol')
        p.update(name='DeepD reported zero-shot fitness panel',
            split_rule='Zero-shot mutant/reference likelihood comparison; no downstream fitted head. Exact per-assay variant eligibility and processing are not reported in the inspected main paper/DC1, and processed manifests are absent from the pinned code/data release.',
            notes='Panel-level source claim: constituent assays are not identified by the inspected release. No Evo assay IDs are borrowed.')
        output(t['id'], 'isolated', 'One likelihood-derived score per supplied mutation',
            'Mutation within each source assay; absolute Spearman summarized over assays', 'deepd-eval-methods',
            limitations='Output form is explicit; exact assay identities and retained mutation cohorts have separate source limits.')

    # Image labels resolve task components that the previous caption-only audit
    # missed. Do not recover numeric bar values by estimating pixels.
    maize = code('model-final-deepd-maize-targets', 'biomap-research/DeepD-website', DEEPD_SITE,
        'assets/fig/f5-maize-auprc.webp',
        'Figure 5D displays exactly seven maize targets: CDS, intron, UTR, CRE, TE_DNA, TE_LTR/Copia and TE_LTR/Gypsy. It reports best-test AUPRC for 8K/1M checkpoints and a selected routing layer for each target.',
        cache + 'model-gaps-deepd/f5-maize-auprc.webp')
    ecoli = code('model-final-deepd-ecoli-targets', 'biomap-research/DeepD-website', DEEPD_SITE,
        'assets/fig/f5-ecoli.webp',
        'Figure 5B displays separate CRISPR-repeat and CRISPR-spacer probabilities at approximately 2,877.25–2,879 kb and a coding track across the lac region at approximately 361–368 kb. These are qualitative local tracks, without a displayed cohort-wide accuracy statistic.',
        cache + 'model-gaps-deepd/f5-ecoli.webp')
    mouse = code('model-final-deepd-mouse-tf-labels', 'biomap-research/DeepD-website', DEEPD_SITE,
        'assets/fig/f3-regulatory.webp',
        'Figure 3B names five source configurations mouse_tf 0, mouse_tf 1, mouse_tf 2, mouse_tf 3 and mouse_tf 4, alongside H3/H4. TF protein identities and experimental accessions are not supplied in these labels.',
        cache + 'model-gaps-deepd/f3-regulatory.webp')
    s3 = ev('model-final-deepd-human-tf-labels', 'deepd-supplement-followup',
        'DC1 Figure S3E; embedded image 3.png visually inspected',
        'The figure explicitly names human_tf 0, human_tf 1, human_tf 2, human_tf 3 and human_tf 4. These source identifiers establish five configurations but do not identify TF proteins or source experiments.')
    for tid, eid, desc in [
        ('deepd-annotation-maize', maize, 'Seven source-defined binary annotation targets: CDS, intron, UTR, CRE, TE_DNA, TE_LTR/Copia and TE_LTR/Gypsy; Fig. 5D best-test AUPRC and local tb 1/gt 1 probability tracks.'),
        ('deepd-annotation-bacteria', ecoli, 'E. coli local routing-track demonstrations: CRISPR repeats, CRISPR spacers and CDS in the lac region. No quantitative full-cohort score is displayed for these loci.'),
        ('deepd-mouse-tf', mouse, 'Five sequence classifiers named mouse_tf 0 through mouse_tf 4 in Fig. 3B. Molecular TF identities and accessions are not established by those source labels.'),
        ('deepd-human-tf', s3, 'Five sequence classifiers named human_tf 0 through human_tf 4 in Fig. S3E. Molecular TF identities and accessions are not established by those source labels.')]:
        if not any(t['id'] == tid for t in d['tasks']):
            continue
        t = row('tasks', tid); t.update(description=desc)
        field('tasks', tid, 'description', eid)
        limit('tasks', tid, 'processed_dataset', 'not-released',
            'The pinned complete GH and HF releases contain H3/human HBB demonstrations, not the source-specific cohort and coordinate manifest for this panel.', hf_ev)
        if 'tf' in tid:
            t['status'] = 'source-limited'
            t['limitations'] = 'Source configuration names and AUROC are reported. Experimental TF identities, accessions, exact sample counts, negative construction and partition membership are not reported in the inspected main paper/DC1 and are not released in the pinned GH/HF trees.'
            limit('tasks', tid, 'tf_identity', 'not-reported',
                'The source labels use numbered TF configurations, without experimental TF names/accessions.', eid)
            output(tid, 'isolated', 'Binary TF-binding label per supplied sequence',
                'Source-defined TF configuration / sequence', eid,
                limitations='Five configurations are identified; experimental TF identities and exact cohorts are separately unavailable.')
        elif tid.endswith('maize'):
            t.update(target='Seven one-versus-rest maize annotation targets',
                output_description='Position-indexed binary membership probabilities; best-test AUPRC per target',
                limitations='All seven Fig. 5D target names are established. Full train/validation/test coordinates, sampling construction, class counts and numeric score files are not released in the inspected official trees. Local tb 1/gt 1 figures do not establish contiguous held-out test scoring.')
            output(tid, 'sampled-positions', 'Position-indexed binary membership probabilities',
                'Source-defined annotation positions, separately per target/checkpoint', maize, axis='sampled',
                limitations='Scored test-row coordinate continuity and partition construction are not established; local continuous tracks are diagnostic examples.', status='partial')
        else:
            t.update(task_type='routing-feature interpretation / local annotation demonstration',
                target='CRISPR-repeat, CRISPR-spacer and lac-region CDS alignment',
                output_description='Local annotation-aligned probability tracks',
                limitations='The source supports three qualitative local readouts. It does not display a corresponding quantitative independent-test cohort or full split manifest; the released human 90,000-row classifier counts do not apply to E. coli.')
            output(tid, 'diagnostic', 'Local annotation-aligned routing probability tracks',
                'Displayed E. coli locus', ecoli,
                limitations='No cohort-wide held-out scoring statistic is shown for the displayed bacterial loci.')

    # Replace the two mixed panels with the individual documented targets.
    # Root reconciliation removes REMOVED_TASKS and all their dependent rows;
    # their original claims persist in these targets and the collection notes.
    from common import Catalogue
    c = Catalogue(d)
    put('categories', dict(id='utr', dimension='region', name='UTRs (unspecified)',
        definition='Source evaluates an undivided UTR label and does not distinguish 5′ from 3′ UTRs.', accommodation=None))
    put('categories', dict(id='crispr-array', dimension='region', name='CRISPR arrays',
        definition='CRISPR repeat–spacer arrays. Repeat identity and spacer identity are distinct component targets; no complete adaptive-immune-system function is implied.', accommodation=None))
    for pop, specs, eid in [
        ('maize', [
            ('cds', 'CDS', 'cds'), ('intron', 'Intron', 'intron'),
            ('utr', 'UTR', 'utr'), ('cre', 'CRE', 'regulatory'),
            ('te-dna', 'TE_DNA', 'repeat'), ('te-ltr-copia', 'TE_LTR/Copia', 'repeat'),
            ('te-ltr-gypsy', 'TE_LTR/Gypsy', 'repeat')], maize),
        ('ecoli', [('crispr-repeat', 'CRISPR repeat', 'crispr-array'),
                   ('crispr-spacer', 'CRISPR spacer', 'crispr-array'),
                   ('cds', 'lac-region CDS', 'cds')], ecoli)]:
        for slug, name, feature in specs:
            tid = 'deepd-' + pop + '-routing-' + slug
            qualitative = pop == 'ecoli'
            limitations = (
                'Qualitative local probability-track example. The source supplies locus coordinates and annotation overlays, but no quantitative held-out test cohort or train/validation/test manifest for this target. '
                'Human routing sample counts and released XGBoost classifiers do not establish the bacterial protocol.' if qualitative else
                'Figure 5D identifies the binary target and reports test AUPRC by checkpoint; local tb 1/gt 1 probability tracks are separate demonstrations. '
                'Target-specific class counts, coordinate partitions, complete score files, layer-selection rule and maize routing arrays are not released in the inspected official trees.')
            put('tasks', dict(id=tid, name='DeepD ' + ('E. coli' if qualitative else 'maize') + ' routing / ' + name,
                dataset_name='DeepD E. coli local annotation demonstration' if qualitative else 'DeepD maize routing annotation panel',
                target=name + ' membership', description=(
                    'Relate expert-routing probabilities to the named annotation at the displayed E. coli locus.' if qualitative else
                    'Predict the named binary annotation from expert-routing vectors; compare separately trained 8K and 1M checkpoints using best-test AUPRC.'),
                task_type='local annotation-alignment diagnostic' if qualitative else 'position-level binary annotation probe',
                label_basis='Reference annotation overlays and source-defined genomic memberships', status='paper-audited',
                evidence_id=eid, limitations=limitations,
                input_description='576-dimensional expert-gating vectors across layers 2–24',
                output_description='Local positional membership-probability track' if qualitative else 'One binary annotation probability per source-defined genomic position'))
            c.member(tid, 'deepd-evals', eid, note='Decomposed source-defined target; no duplicate composite panel dot.')
            c.population(tid, pop, eid, 'E. coli local loci in Figure 5B.' if qualitative else 'Zea mays routing targets in Figure 5D.')
            for cid in ['genome-annotation', 'interpretability', feature]:
                c.category(tid, cid, eid, 'Actual named annotation target in the inspected figure; full structures are not jointly evaluated.')
            if not qualitative:
                c.category(tid, 'functional-prediction', eid, 'Binary annotation probe scored by target-specific AUPRC.')
            c.category(tid, 'dense-annotation', eid,
                'The displayed probability track is position-aligned. This is a demonstrated output, not proof of contiguous held-out evaluation.', 'demonstrated-output')
            if feature == 'cds':
                put('task_feature_scopes', dict(id=tid+'-cds-scope', task_id=tid, feature_id='cds',
                    scope='restricted-target', rationale='This target is specifically CDS membership; it is distinct from intron, UTR, regulatory and repeat targets.', evidence_id=eid),
                    ('task_id', 'feature_id'))
            pid = tid + '-protocol'
            c.protocol(pid, tid, 'DeepD local routing interpretation' if qualitative else 'DeepD reported maize routing probe',
                'frozen routing-feature interpretation' if qualitative else 'frozen routing-weight probe',
                '576-dimensional expert-gating vector at each position',
                'Local E. coli locus overlays; no independently scored partition is identified in the available source.' if qualitative else
                'Figure 5D reports test AUPRC, but exact train/validation/test coordinate assignment and sampling are not reported by the inspected available sources.',
                'displayed locus' if qualitative else 'source-defined genomic position', eid,
                metrics=() if qualitative else [('auprc', 'Separately per target and checkpoint; best layer displayed.')],
                embeddings=True, fitted='Annotation-specific classifier; paper describes linear probes',
                selection='Selected routing layer; complete selection rule and search cohort are not reported.',
                notes='8K and 1M are separately trained checkpoints, not a controlled inference-only context ablation.')
            c.use(tid, 'deepd', 'deepd', eid, pid)
            output(tid, 'diagnostic' if qualitative else 'sampled-positions',
                'Local annotation-aligned probability track' if qualitative else 'Binary membership probability at genomic positions',
                'Displayed E. coli locus' if qualitative else 'Source-defined test positions per target/checkpoint',
                eid, axis='none' if qualitative else 'sampled', limitations=limitations,
                status='supported' if qualitative else 'partial')
            limit('tasks', tid, 'processed_dataset', 'not-released',
                'The complete pinned official GH/HF releases contain H3 and human HBB assets, not this organism’s routing arrays or coordinate splits.', hf_ev)
            if not qualitative:
                limit('tasks', tid, 'split_coordinates', 'not-reported',
                    'Test AUPRC is displayed, but the figure and available code do not state test-coordinate continuity, sampling or chromosome/locus grouping.', eid)
            else:
                limit('tasks', tid, 'quantitative_test', 'not-applicable',
                    'The available evidence is a local annotation-overlay demonstration, not an independently scored held-out test.', eid)
    row('evaluations', 'deepd-evals')['notes'] = (
        'Figure-level source review resolves seven maize routing targets and three E. coli local annotation readouts, now represented individually. '
        'Human HBB release is a separate XGBoost demonstration with full-workflow metrics and a 20,000-base local interval. '
        'Protein/ncRNA fitness panels and numbered TF configurations retain their exact source limitations; no unrelated assay manifest is substituted.')

    # Preserve the phage claim without asserting unreported Lambda/P1 identity.
    # The human DMS result is another explicit paper claim, previously omitted.
    human_fit = code('model-final-deepd-human-fitness-claim', 'biomap-research/DeepD-website', DEEPD_SITE,
        'assets/fig/f4-protein.webp',
        'Figure 4A reports human protein fitness as mean absolute Spearman correlation over assay points using mutation-induced sequence-likelihood changes. DeepD-60B mean is 0.627. Assay IDs and exact retained mutation counts are not listed in the figure.',
        cache+'model-gaps-deepd/f4-protein.webp')
    for tid, name, dataset, target, typ, eid, pop, cap, metric, description in [
        ('deepd-phage-essential', 'DeepD phage gene essentiality', 'DeepD source-defined phage essentiality cohort',
         'Phage gene essential versus nonessential status', 'binary classification', 'deepd-eval-methods', 'viruses',
         'variant-effects', 'auroc', 'Figure 3A reports zero-shot phage essential-gene prediction. The inspected main paper does not identify the phage genomes or establish equivalence to the original Evo Lambda/P1 cohort.'),
        ('deepd-human-fitness', 'DeepD human protein fitness', 'DeepD human protein mutational fitness panel',
         'Experimental human protein mutational fitness', 'regression / ranking', human_fit, 'human',
         'variant-effects', 'abs-spearman', 'Figure 4A reports human protein fitness from mutation-induced likelihood changes, summarized as absolute Spearman across assays. The source figure does not enumerate the assay identities.')]:
        put('tasks', dict(id=tid, name=name, dataset_name=dataset, target=target, task_type=typ,
            label_basis='Experimental fitness / essentiality assays as described by the source paper',
            evidence_id=eid, status='source-limited', description=description,
            input_description='Source-defined DNA sequence / mutation likelihood input',
            output_description='Experimental essentiality ranking' if metric=='auroc' else 'Mutational fitness score ranking',
            limitations='Source claim retained with explicit missing fields: exact assay/genome IDs, processed example counts and score-cohort manifests are not released in the inspected official trees. No another-paper cohort is substituted.'))
        c.member(tid, 'deepd-evals', eid)
        c.population(tid, pop, eid, 'Human protein fitness cohorts in Figure 4A.' if pop=='human' else 'Phage genes in Figure 3A; exact phage taxa are not named in the available source.')
        for cid in [cap, 'cds', 'protein-engineering' if pop=='human' else 'microbial-genomics']:
            c.category(tid, cid, eid, 'Source-defined coding functional-effect target; exact cohort remains source-limited.')
        put('task_feature_scopes', dict(id=tid+'-cds-scope', task_id=tid, feature_id='cds', scope='restricted-target',
            rationale='Protein-coding fitness or gene essentiality is the assessed target; not a mixed gene-element classifier.', evidence_id=eid),
            ('task_id', 'feature_id'))
        pid=tid+'-protocol'
        c.protocol(pid, tid, 'DeepD reported human protein fitness' if pop=='human' else 'DeepD reported phage essentiality',
            'zero-shot', 'Mutation-induced sequence-likelihood changes',
            'No downstream fitted head. Experimental cohort is evaluated directly; exact genomic/assay membership and perturbation processing are not supplied by the inspected available sources.',
            'mutation within assay' if pop=='human' else 'source-defined phage gene', eid,
            metrics=[(metric, 'Absolute correlation within each assay, then source-reported mean.' if pop=='human' else 'Source-reported AUROC.')],
            embeddings=False)
        c.use(tid, 'deepd', 'deepd', eid, pid)
        output(tid, 'isolated', 'One likelihood-derived score per supplied functional perturbation',
            'Mutation within assay' if pop=='human' else 'Source-defined gene perturbation', eid,
            limitations='Output and source metric are explicit; underlying cohort and score manifests have separate source limits.')
        limit('tasks', tid, 'cohort_identity', 'not-reported',
            'The main paper/figure names the evaluation endpoint, but does not list the exact assay IDs or phage genomes.', eid)
        limit('tasks', tid, 'processed_dataset', 'not-released',
            'Complete pinned code and HF releases do not supply this cohort’s examples or score manifest.', deep_release)
    # This targeted correction leaves the original Evo record and all its other
    # model uses unchanged. Source-specific provenance belongs to the new task.
    d['model_evaluations'] = [r for r in d['model_evaluations'] if not(
        r['model_id']=='deepd' and r['task_id']=='evo-phage-essential')]
    d['evaluation_tasks'] = [r for r in d['evaluation_tasks'] if not(
        r['evaluation_id']=='deepd-evals' and r['task_id']=='evo-phage-essential')]
    d['protocols'] = [r for r in d['protocols'] if r['id']!='deepd-evo-phage-essential']
    d['protocol_metrics'] = [r for r in d['protocol_metrics'] if r['protocol_id']!='deepd-evo-phage-essential']

    # Replace copied placeholder text with the actual endpoint in each reused
    # resource; model-specific cohort boundaries remain explicit source fields.
    for pid, split, unit in [
        ('deepd-evo-clinvar', 'Zero-shot ClinVar cohort stratified by SNV/non-SNV and coding annotation. No supervised fitting; exact source release and full cohort processing are not identified in the inspected main text/DC1.', 'human variant'),
        ('deepd-evo-splicevardb', 'Zero-shot splice-altering versus control variants, with exonic/intronic strata. No downstream head; exact source version and retained variant IDs are not released.', 'human variant'),
        ('deepd-evo-brca1', 'Zero-shot experimental BRCA1 variant cohort, also stratified by molecular consequence; no downstream fitted head. Exact score-cohort file is not released.', 'BRCA1 variant'),
        ('deepd-evo-brca2', 'Zero-shot experimental BRCA2 variant cohort, also stratified by molecular consequence; no downstream fitted head. Exact score-cohort file is not released.', 'BRCA2 variant'),
        ('deepd-gue-H3', 'Frozen-embedding yeast H3 binary classification reported by AUROC in the paper. Paper-specific partition and downstream-head settings are not supplied by the inspected main paper; the released H3 MLP example has its own linked protocol.', 'yeast sequence window'),
        ('deepd-gue-H4', 'Frozen-embedding yeast H4 binary classification reported by AUROC in the paper. The inspected release contains H3, not H4 dataset/head artifacts; exact H4 partitions are not supplied.', 'yeast sequence window')]:
        p = row('protocols', pid); p.update(split_rule=split, split_unit=unit,
            notes='Model-specific source protocol; upstream task identity does not certify identical processed cohorts or evaluation partitions.')
        field('protocols', pid, 'split_rule', 'deepd-eval-methods')
        limit('protocols', pid, 'processed_cohort', 'not-released',
            'The complete official release does not include the full paper-specific scored cohort for this endpoint. The released H3/ClinVar demonstrations remain distinct variants/protocols.', deep_release)
    for p in d['protocols']:
        if p['id'] in ['deepd-core-promoter-probe','deepd-promoter-probe','deepd-splice-probe','deepd-human-tf-probe']:
            p.update(fitted_component='Classifier on frozen embeddings; paper-specific architecture not supplied in the inspected main paper/DC1',
                split_rule='Source reports supervised sequence classification; exact train/validation/test construction is not supplied in the inspected main paper/DC1 or released as source-specific partition files.',
                split_unit='source-defined sequence windows')
            field('protocols', p['id'], 'split_rule', deep_release)
    for p in d['protocols']:
        if p['task_id'] in ['deepd-mouse-tf','deepd-human-tf']:
            p['notes']='Five source-named numbered configurations; no TF accession or processed split manifest is supplied by the inspected release.'

    # Generation cohorts are source-reported, not held-out predictor test sets.
    promoter_generation = ev('model-final-deepd-promoter-cohort', 'deepd-paper',
        'Figure 6 and Supplementary Figure S6; maize promoter generation and validation',
        'Condition on 26,572 STARR-seq maize core promoters (−165 to +5 bp around TSS); Low/Med/High use 30/40/30 percentiles with thresholds −3.007/−2.018. After computational filtering, select 100 High and 100 Low candidates; experimental figure reports 83 High and 71 Low with three biological replicates. Those stages have different denominators.')
    count('deepd-promoter-training', 'deepd-maize-promoter', 26572, 'STARR-seq promoter sequences', promoter_generation, split='fine-tuning cohort', method='reported')
    for stage, n in [('selected High',100),('selected Low',100),('experiment High',83),('experiment Low',71)]:
        count('deepd-promoter-'+stage.replace(' ','-'), 'deepd-maize-promoter', n, 'promoter constructs', promoter_generation, split=stage, method='reported')
    row('protocols', 'deepd-maize-promoter-protocol').update(
        split_rule='Activity-conditioned adaptation uses 26,572 STARR-seq promoters. Candidate filtering/selection yields 100 High and 100 Low; experimental results report 83 High and 71 Low. These are design/selection/measurement cohorts, not a train/test predictor split.',
        split_unit='source promoter / selected generated construct',
        selection='Sequential BLAST/composition/predicted-strength/diversity/training-similarity filters; then experimental dual-luciferase assays. Candidate sequence manifest and exclusions are not released.',
        notes='Three biological replicates per experimentally reported construct; computational oracle scores are separate from reporter measurements.')
    row('tasks', 'deepd-maize-promoter')['limitations']='Training, selected candidate and measured construct counts are explicitly distinguished. The pinned official releases do not supply full candidate sequences, reporter measurements or split/selection files. Predicted-strength filtering precedes experimental measurement.'
    for tid, n, notes in [
        ('deepd-yeast-chromosome',29,'Paper reports 29 generated yeast chromosome III sequences 309.86–316.62 kb using held-out S288C ChrIII backbone. The pinned Git tree releases one AIYeast 00 synteny example, not a complete 29-sequence panel; HF root has no generation subtree.'),
        ('deepd-arabidopsis-mb',3,'Paper reports three generated 1 Mb Arabidopsis regions with computational gene/synteny/variation diagnostics. No corresponding complete 3-sequence panel is present in the inspected Git/HF release.')]:
        eid=ev('model-final-'+tid+'-cohort','deepd-paper','Chromosome-scale and megabase generation results; Code and data availability',notes)
        count(tid+'-generated',tid,n,'generated genomic sequences',eid,split='paper-reported generated cohort',method='reported')
        row('tasks',tid)['limitations']=notes+' These computational diagnostics do not establish organismal viability or experimentally validated genome function.'
        row('protocols',tid+'-protocol').update(split_rule=notes,
            split_unit='generated genomic sequence / computational annotation',
            notes='Context–Anchor–Body generation and computational reference comparisons. Availability statements and actual pinned release inventory are distinct evidence.')
        limit('tasks',tid,'complete_generation_cohort','not-released',notes,deep_release)

    # Actual released ClinVar demonstration uses a perplexity difference. It is
    # not silently relabeled as the paper's general sequence-likelihood score.
    clinvar = code('model-final-deepd-clinvar-data', 'biomap-research/DeepD', DEEPD,
        'notebook/zero_shot/clinvar_snv_coding.csv',
        'Complete 184-row CSV: 99 label 1 and 85 label 0; paired WT/mutant sequences have equal lengths 5,244–8,001 nt, 176 pairs are 8,001 nt. Columns are unique_id, mut_seq, wt_seq, label; no explicit chromosome/position fields.',
        cache+'model-gaps-releases/biomap-research-DeepD-2896082/notebook/zero_shot/clinvar_snv_coding.csv')
    row('evidence', clinvar)['basis'] = 'data'
    clinvar_code = code('model-final-deepd-clinvar-scorer', 'biomap-research/DeepD', DEEPD,
        'notebook/zero_shot/coding_auroc.ipynb',
        'The released notebook calls the DeepD logits API with Homo sapiens, reads mean per-token NLL loss, and ranks exp(loss_mutant)−exp(loss_WT), i.e. perplexity difference. It evaluates rank-based AUROC over the 184 supplied coding SNVs, without fitting. Exact API checkpoint is not pinned by the notebook.',
        cache+'model-gaps-releases/biomap-research-DeepD-2896082/notebook/zero_shot/coding_auroc.ipynb')
    vid = 'deepd-clinvar-coding-demonstration'
    put('variants', dict(id=vid, task_id='evo-clinvar', name='Released DeepD coding-SNV demonstration',
        dataset_revision=DEEPD, input_length='5,244–8,001 nt;176 of 184 pairs 8,001 nt',
        target_count=1, target_unit='binary pathogenicity target', context='Supplied WT/mutant sequences; no genomic coordinates in the four-column release.',
        notes='184-row source-specific demonstration, not the full ClinVar paper cohort. API checkpoint is not pinned by the notebook.', evidence_id=clinvar))
    pid = 'deepd-clinvar-coding-demonstration-protocol'
    c.protocol(pid, 'evo-clinvar', 'Released DeepD coding-SNV perplexity difference',
        'zero-shot', 'DeepD mean per-token NLL → mutant/WT perplexity difference',
        'All 184 supplied coding SNVs; no downstream head or supervised partition. Notebook does not supply genomic grouping or an independently scored validation set.',
        'supplied coding SNV', clinvar_code, metrics=[('auroc', 'Rank-based AUROC over the entire supplied binary cohort.')],
        embeddings=False, variant=vid,
        notes='Score is exp (NLL_mutant)−exp (NLL_WT), not mutant/reference LLR. API checkpoint is not pinned.')
    c.use('evo-clinvar', 'deepd', 'deepd', clinvar_code, pid, provenance='released-example',
        note='Source-specific 184-row codingSNV demonstration, separately linked from the paper-wide DeepD ClinVar protocol.')
    count('deepd-clinvar-coding-demo', 'evo-clinvar', 184, 'variant pairs', clinvar,
        qualifier='Complete released DeepD demonstration; not the full Evo 2 or DeepD paper ClinVar cohort.', variant=vid, protocol=pid)
    limit('protocols', pid, 'checkpoint', 'not-reported',
        'Notebook calls the gateway API without an immutable model/checkpoint identifier.', clinvar_code)
    resource('deepd-coding-clinvar-release-data', 'model-final-deepd-clinvar-data-source',
        'DeepD coding-SNV WT/mutant sequence pairs', 'dataset', 'github',
        f'https://github.com/biomap-research/DeepD/blob/{DEEPD}/notebook/zero_shot/clinvar_snv_coding.csv',
        DEEPD, clinvar, '184-row released demonstration, separately linked from full paper cohorts.',
        tasks=['evo-clinvar'], collection='deepd-evals', variant=vid)
    resource('deepd-coding-clinvar-release-code', 'model-final-deepd-clinvar-scorer-source',
        'DeepD coding-SNV perplexity-difference scorer', 'evaluation-code', 'github',
        f'https://github.com/biomap-research/DeepD/blob/{DEEPD}/notebook/zero_shot/coding_auroc.ipynb',
        DEEPD, clinvar_code, tasks=['evo-clinvar'], collection='deepd-evals', variant=vid)

    # Complete small artifacts: every annotation/prediction row was read.
    hbb_path = cache + 'model-gaps-releases/biomap-research-DeepD-2896082/notebook/interpretability/data/human/annotations.csv'
    hbb = code('model-final-deepd-hbb-row-audit', 'biomap-research/DeepD', DEEPD,
        'notebook/interpretability/data/human/annotations.csv',
        'Complete 20,000-row scan: chr 11:5,220,000–5,240,000, consecutive demo_row 0–19,999 and original npy_row 20,000–39,999. Positive memberships: CDS1,054; cCRE10,358; DNA-transposon 0; LTR533; LINE4,966; SINE1,286. The source rows contain overlapping memberships; plot-priority labels and independent binary membership are different readouts.', hbb_path)
    routing = code('model-final-deepd-routing-interface', 'biomap-research/DeepD', DEEPD,
        'notebook/interpretability/hbb_ovr_demo.py',
        'The example validates 12 model hashes and 8 feature arrays, reproduces all 20,000 local probabilities, and computes local AP/AUROC. Its README explicitly instructs using best_layers.csv complete-workflow metrics rather than substituting interval scores. No training or split-construction implementation is included.',
        cache + 'model-gaps-releases/biomap-research-DeepD-2896082/notebook/interpretability/hbb_ovr_demo.py')
    for tid in sorted(t for t in associated('deepd') if t.startswith('deepd-human-routing-')):
        t = row('tasks', tid)
        t['task_type'] = 'sampled-position binary annotation probe'
        t['limitations'] = ('Complete released target/metric tables, 20,000 HBB annotation rows and 20,000 reference-prediction rows inspected. '
            'Full 90,000-row training/validation/test coordinate arrays and sampler are absent from the pinned release. '
            'Reported 72,000/9,000/9,000 counts are full-workflow row counts; HBB is a separate continuous demonstration. '
            'Released XGBoost classifiers differ from the paper’s linear probes.')
        limit('tasks', tid, 'split_coordinates', 'not-released',
            'Only 20,000 HBB rows and their original matrix indices are released; original full-cohort partition membership cannot be reconstructed.', hf_ev)
        limit('tasks', tid, 'layer_selection', 'not-reported',
            'The table reports selected layers and validation/test metrics, but not a reproducible layer-selection rule or complete search results.', 'deepd-human-routing-release')
        output(tid, 'sampled-positions', 'Independent binary annotation probability at a supplied genomic position',
            'Reported full-test position rows; continuous HBB rows separately diagnostic', hbb, axis='sampled',
            limitations='Full-test position sampling and coordinate partition are unavailable. The 20,000 contiguous HBB rows do not establish contiguous held-out scoring.', status='partial')
        for p in d['protocols']:
            if p['task_id'] == tid:
                p.update(split_unit='reported genomic-position rows; coordinate grouping not released',
                    selection='Per-target checkpoint and selected layer are reported in best_layers.csv; layer-selection rule and complete search table are not reported in the inspected release.')
                field('protocols', p['id'], 'split_rule', hf_ev)
        field('tasks', tid, 'limitations', routing)
    human_routing = sorted(t for t in associated('deepd') if t.startswith('deepd-human-routing-'))
    resource('deepd-hbb-local-data', 'model-final-deepd-hbb-row-audit-source',
        'DeepD continuous HBB annotation rows', 'dataset', 'github',
        f'https://github.com/biomap-research/DeepD/blob/{DEEPD}/notebook/interpretability/data/human/annotations.csv',
        DEEPD, hbb, '20,000-base local demonstration; not the full classifier train/validation/test cohort.',
        tasks=human_routing, collection='deepd-evals')
    resource('deepd-hbb-features', hf_sid, 'DeepD HBB routing-feature arrays', 'dataset', 'huggingface',
        f'https://huggingface.co/datasets/biomap-research/DeepD/tree/{DEEPD_HF}/interpretability/data/human/features',
        DEEPD_HF, hf_ev, 'Eight local 20,000×576 arrays; full partition arrays are not released.',
        tasks=human_routing, collection='deepd-evals')
    resource('deepd-hbb-reproduction-code', 'model-final-deepd-routing-interface-source',
        'DeepD HBB model verification and local scoring', 'evaluation-code', 'github',
        f'https://github.com/biomap-research/DeepD/blob/{DEEPD}/notebook/interpretability/hbb_ovr_demo.py',
        DEEPD, routing, tasks=human_routing, collection='deepd-evals')
    resource('deepd-routing-full-workflow-results', 'src-deepd-human-routing-release',
        'DeepD selected-layer full-workflow metrics', 'results', 'github',
        f'https://github.com/biomap-research/DeepD/blob/{DEEPD}/notebook/interpretability/data/best_layers.csv',
        DEEPD, 'deepd-human-routing-release', 'Reported counts and metrics; not a released partition manifest.',
        tasks=human_routing, collection='deepd-evals')

    # AIDO: inspect the figures themselves; a source-wide RNA-specific recipe
    # must not be attached indiscriminately to all five assay-family heads.
    aid_fig = source('model-final-aido-coverage-figure', 'AIDO.DNA2 coverage figure: all tracks',
        'https://genbio.ai/wp-content/uploads/2025/10/image-2.png', 'Official 2025-10 report; inspected 2026-11-27',
        cache + 'model-gaps-aido/image-2.png', 'report-figure')
    aid_e = ev('model-final-aido-track-counts', aid_fig, 'X-axis labels; entire image inspected',
        'Figure explicitly labels TF ChIP 1,885, DNase 674, histone ChIP 2,001, CAGE 1,276 and RNA 1,543 tracks, totaling 7,379. The y-axis says Score, not Pearson/Spearman. The text calls results correlations but does not define the statistic or genomic-bin aggregation.')
    aid_scatter = source('model-final-aido-comparison-figure', 'AIDO.DNA2 ensemble comparison figure',
        'https://genbio.ai/wp-content/uploads/2025/10/image-1.png', 'Official 2025-10 report; inspected 2026-11-27',
        cache + 'model-gaps-aido/image-1.png', 'report-figure')
    aid_s = ev('model-final-aido-aggregation-discrepancy', aid_scatter, 'Five plotted points and axis labels',
        'The image shows five points, one labelled for each assay family with its track count. The surrounding report and figure legend describe each point as a track. This is not a released per-track prediction/score table; aggregation across tracks is not specified.')
    aid_recipe = ev('model-final-aido-recipe-scope', 'aido2-report',
        'Supervised Coverage Prediction, paragraphs 1–4',
        'All five families reuse original Borzoi folds (train 0–2/5–7, validation 4, test 3). The explicit 524 kb input, linear 512 channel projection, ±8,192 token local attention, frozen backbone and optimizer recipe are introduced specifically for RNA-seq. General text says DNA2 adapters/frozen backbones across families, but does not specify identical input geometry or heads for the other four.')
    for slug, n in [('tf-chip', 1885), ('histone-chip', 2001), ('dnase', 674), ('cage', 1276), ('rna', 1543)]:
        tid = 'aido2-coverage-' + slug; t = row('tasks', tid)
        count(tid + '-track-count', tid, n, 'assay tracks', aid_e, split='reported assay family', method='reported',
            qualifier='Figure-axis count; not independent sequence examples, genes or split sizes.')
        t['limitations'] = ('Assay-family track count is explicit in the figure. Exact track IDs, species allocation, output bins, processed windows and correlation statistic are not reported or linked by the inspected report. '
            'The detailed 524 kb/Flashzoi/local-attention recipe is explicit for RNA-seq; identical geometry for other heads is not established. '
            'The ensemble scatter shows five assay-family points despite its per-track wording.')
        t['input_description'] = '524 kb genomic windows for RNA-seq; exact geometry for this non-RNA family is not reported' if slug != 'rna' else '524 kb genomic windows; frozen encoder and Flashzoi adapter'
        for p in d['protocols']:
            if p['task_id'] == tid:
                p['notes'] = ('Original Borzoi fold partition retained. Single-run and four-run medium/large ensembles reported. '
                    'Report calls scores correlations; exact statistic and aggregation are not defined. '
                    + ('RNA-specific recipe: BF16, local attention ±8192 tokens, 32 H100, global batch 32, LR warmup 2e-5, weight decay 1e-8, clip 0.15.' if slug == 'rna' else 'The RNA paragraph’s 524 kb/512 channel/local-attention/optimizer details are not established for this head.'))
                if slug != 'rna':
                    p.update(model_interface='Frozen DNA2 representations → source-described trained coverage adapter; exact family-specific head not reported', fitted_component='Coverage adapter; family-specific architecture not reported')
        for name, text in [
            ('output_binning', 'Report states coverage/profile prediction but supplies no bin width, central output crop or output array schema.'),
            ('metric', 'Text says correlations and figure says Score; Pearson/Spearman and track/genomic aggregation are not defined.'),
            ('species', 'No species×track allocation is supplied; multi-species pretraining and Borzoi ancestry do not establish evaluation species.'),
            ('track_ids', 'Figure supplies family counts, not an accession list or exact target manifest.')]:
            limit('tasks', tid, name, 'not-reported', text, aid_e)
        limit('tasks', tid, 'processed_dataset', 'not-released',
            'Report does not link its converted NPZ windows, targets, split manifests or evaluation code. Upstream Borzoi data alone do not establish the adapter’s processed cohort.', aid_recipe)
        output(tid, 'signal-profile', 'Quantitative assay coverage across genomic positions/bins',
            'Source-defined quantitative track; family counts separately reported', aid_recipe, axis='contiguous',
            limitations='Signal-profile form is explicit; exact binning, metric and taxonomic allocation have field-specific source limits.')
        field('tasks', tid, 'limitations', aid_s)
    finding('aido-scatter', None, 'aido2-evals', row('evidence', aid_s)['statement'], aid_s, 'discrepancy')
    row('evaluations', 'aido2-evals')['notes'] = ('Technical report text and all coverage figures inspected. '
        'All five track counts are explicit; processed datasets, track IDs, species allocation, output bins and the correlation definition are not supplied. '
        'The ensemble figure’s five assay-family points conflict with its per-track wording.')
    limit('models', 'aido2', 'tokenizer', 'not-reported',
        'The complete inspected official report does not define its tokenizer or vocabulary. Official HF search for AIDO.DNA2 returns no named model release; predecessor tokenization is not substituted.', 'aido2-architecture')
    limit('models', 'aido2', 'active_parameter_count', 'not-reported',
        'Total sparse parameter counts and routing topology are reported, but active-parameter totals and full layer/width configuration are not specified.', 'aido2-architecture')

    # Genos-m: source-defined SAE statistics are descriptive feature searches,
    # not independently held-out dense annotation accuracy.
    gs = source('model-final-genosm-complete-release', 'Genos-m complete official repository',
        f'https://github.com/BGI-HangzhouAI/Genos-m/tree/{GENOS}', GENOS,
        cache + 'model-gaps-releases/Genos-m-tree.json', 'repository-tree',
        'Complete archive downloaded, including both benchmark notes and the 24-page author PDF. No SAE implementation, activation thresholds, feature-search labels or evaluation split arrays are included.')
    ge = ev('model-final-genosm-release-scope', gs, 'Complete 23-entry tree; README; benchmark notes; paper PDF',
        'Release contains model descriptions, benchmark documentation, training launcher, figures and full paper, but no new Genos-m cohort CSV/Parquet arrays or supervised evaluation code. Benchmark notes identify upstream BacBench, GenerAnno and RNAGym datasets; equivalence to exact processed Genos-m cohorts is not established merely by their names.')
    sae_source = source('model-final-genosm-pdf', 'Genos-m complete author manuscript',
        f'https://github.com/BGI-HangzhouAI/Genos-m/blob/{GENOS}/paper/Genos-m.pdf', GENOS,
        cache + 'model-gaps-releases/BGI-HangzhouAI-Genos-m-f0b05fd/paper/Genos-m.pdf', 'paper')
    sae = ev('model-final-genosm-sae-definition', sae_source,
        'PDF pp. 7–8 (results),17–18 (methods),19 (availability); Figure 3',
        'SAE trains on approximately 305,000 random 32k pretraining chunks, token activations downsampled 10-fold and globally shuffled to approximately 1 billion. 4,096 latents, Batch-TopK 128, batch 4096, LR 5e-5, one epoch. Feature search on E. coli NC000913.3 ORF/intergenic/tRNA/rRNA annotations; one-versus-rest Domain F1 after activation-threshold sweeping. The source gives no Domain F1 formula, threshold grid, complete feature-selection rule, label arrays, candidate token count or separate feature-search validation/test split.',
        'paper', row('sources', sae_source)['url'] + '#page=17')
    row('evidence', 'genosm-sae')['locator'] = 'Methods: Sparse autoencoder interpretability; Figure 3'
    limit('models', 'genosm', 'vocabulary_size', 'conflicting',
        'Paper/card report 128; pinned model config declares 256; tokenizer JSON lists 17 entries. These represent different source claims and their relationship is not explained.', 'genosm-hf-tokenizer-evidence')
    limit('models', 'genosm', 'benchmark_checkpoint', 'not-reported',
        'Official benchmark Table 9 labels Genos-m (cpt 32k), while model documentation advertises 1M context. Exact benchmark checkpoint hash and its equivalence to final weights are not supplied.', 'genosm-doc-checkpoint')
    for tid in sorted(t for t in associated('genosm') if t.startswith('genosm-sae-')):
        t = row('tasks', tid)
        t.update(task_type='post-hoc feature/annotation alignment diagnostic',
            output_description='Source-defined one-versus-rest Domain F1 after feature search and threshold sweeping',
            limitations='Descriptive analysis on one annotated E. coli reference. Feature identities/thresholds are selected with annotation alignment; no independent validation/test cohort, exact Domain F1 formula, threshold grid, label array or SAE scorer is reported/released. The ≈1 billion SAE training activations are not an evaluation sample count.')
        output(tid, 'diagnostic', 'Post-hoc latent-feature annotation alignment statistic',
            'Source-defined one-versus-rest Domain F1 on the annotated E. coli reference', sae,
            limitations='Feature/threshold search and evaluation reuse the annotated genome. Exact formula, denominator and scorer are not provided; no held-out dense annotation claim.')
        for name, reason, text in [
            ('metric_definition', 'not-reported', 'Domain F1 is named and one-versus-rest threshold sweeping described, but its exact formula, coordinate aggregation and denominator are not defined.'),
            ('selection', 'not-reported', 'The feature-search and threshold-sweep grid/tie rules are not supplied.'),
            ('independent_test', 'not-applicable', 'This source reports a descriptive feature search on one annotated reference, without an independent annotation test. Do not recast it as a predictive benchmark.'),
            ('scorer_and_labels', 'not-released', 'Complete official tree has no SAE scorer, activation/label arrays or target-coordinate manifest.')]:
            limit('tasks', tid, name, reason, text, sae)
        for p in d['protocols']:
            if p['task_id'] == tid:
                p.update(split_unit='annotated reference genome / selected latent feature',
                    selection='Post-hoc feature search and activation-threshold sweep on the same E. coli annotation cohort; grid and tie rules not reported',
                    notes='Domain F1 is source-defined; exact formula not provided. No independent annotation test is asserted. Training activations are not evaluation examples.')

    # Summaries describe what was actually checked and do not imply every
    # biological label, training run, or absent artifact was independently rerun.
    family_sources = {
        'deepd': ('deepd-evals', [deep_release, hf_ev, maize, ecoli, mouse, s3, hbb, routing, 'deepd-eval-methods']),
        'gpnstar': ('gpn-evals', ['gpn-benchmarks', 'gpn-scoring', 'gpn-association', 'gpn-annotation']),
        'aido2': ('aido2-evals', ['aido2-architecture', 'aido2-embeddings', 'aido2-clinvar', aid_e, aid_s, aid_recipe]),
        'genosm': ('genosm-evals', [ge, sae, 'genosm-inventory', 'genosm-supervised'])}
    for model, (collection, eids) in family_sources.items():
        for tid in sorted(associated(model)):
            own = tid.startswith(('deepd-', 'gpn-', 'aido2-', 'genosm-'))
            review('tasks', tid,
                f'{model} task use: full paper/report and indexed supplement, complete pinned official release inventory, available task-specific code/data interfaces. '
                'Shared upstream task records retain their separately audited original protocols.',
                [row('tasks', tid)['evidence_id']] + eids,
                'Source review does not establish omitted cohort/split details, independent biological label validation, or reproduction of model scores.')
            if model == 'genosm' and own and not tid.startswith('genosm-sae-'):
                limit('tasks', tid, 'model_specific_processed_cohort', 'not-released',
                    'Complete official repository has documentation and results but not Genos-m-specific processed cohort IDs, partition files or task evaluator. Linked upstream releases remain distinct sources.', ge)
                t = row('tasks', tid)
                # Remove vague future-work language; retain the exact scientific
                # limitations already authored for each individual target.
                text = t.get('limitations') or ''
                text = text.replace('require artifact audit', 'are not released in the inspected official repository')
                text = text.replace('require verification', 'are not established by the inspected release')
                text = text.replace('not yet imported', 'not provided as a model-specific released manifest')
                text = text.replace('remain to be audited', 'are not supplied by the inspected release')
                t['limitations'] = text
            if model == 'deepd':
                limit('tasks', tid, 'method_details_document', 'not-retrieved',
                    'The separately linked DC2 Method Details document could not be retrieved; findings use the inspected main paper, DC1 figures and captions and complete pinned official releases. No claim about absent DC2 content is made.', dc2)
        uses = [m for m in d['model_evaluations'] if m['model_id']==model]
        for pid in sorted({m['protocol_id'] for m in uses if m.get('protocol_id')}):
            p = row('protocols', pid)
            review('protocols', pid, 'Model-specific adaptation/readout/partition description checked against the cited paper/report and available official release; shared upstream protocols remain separate.',
                [p['source_evidence_id']]+eids,
                'Reported partition names do not establish unavailable coordinate manifests or preprocessing equivalence.')
        review('evaluations', collection, 'Complete review of identified available primary report/paper and pinned official releases; individual task and protocol evidence retained.', eids,
            'Fields absent from available reports/releases are recorded separately. Source availability is not equivalent to raw-data verification.')
        review('models', model, 'Paper/report model descriptions compared with complete current official code/model card release where available.', eids)
        if model != 'deepd':
            paper = {'gpnstar': 'gpn', 'aido2': 'aido2', 'genosm': 'genosm'}[model]
            scope = {
                'gpnstar': 'Full GPN-Star paper and supplementary benchmark/scoring methods; complete current and archived official code; all thirteen released benchmark cohorts and prediction-file inventories.',
                'aido2': 'Complete official technical web report, architecture/pretraining text, coverage protocol and all supplied result figures; public model/dataset-release searches distinguished from the report claims.',
                'genosm': 'Complete 24-page author paper, model card/configuration/tokenizer files, benchmark notes and full official repository; paper-specific methods distinguished from named upstream benchmark releases.'}[model]
            review('papers', paper, scope, eids,
                'Review completion records the identified primary-source scope. Unreported methods and unreleased processed cohorts remain explicit field-level limits; training and model scores were not independently rerun.')
    review('papers','deepd','Cached full main paper and DC1 supplementary figures and captions; actual figure labels; publication metadata; complete official code/data inventories.',
        [deep_release,'deepd-panel-gap-review',maize,ecoli,mouse,s3,metae],
        'DC2 Method Details is identified but not retrieved, with its access failure recorded separately. Its contents are not included in the completed inspection scope.')
    gpn_artifacts(d, put, row, source, ev, field, limit, review, finding, count, resource)
    gpn_evidence = [x['id'] for x in d['evidence'] if x['id'].startswith('model-final-gpn-')
        and x['id'].endswith(('-inspection', '-score-inspection'))]
    review('papers', 'gpn',
        'Full GPN-Star paper and supplementary benchmark/scoring methods; complete current and archived official code; all thirteen released benchmark datasets and every published prediction Parquet fully scanned.',
        ['gpn-benchmarks', 'gpn-scoring', 'gpn-association', 'gpn-annotation', 'model-final-gpn-panel-source-review'] + gpn_evidence,
        'The 31-assay ProteinGym panel lacks a GPN-Star-specific released identity manifest; all-current-score intersections are not silently substituted for the exact comparator/consequence denominator of a paper plot.')

    # Genos-m provides upstream identifiers but not processed cohort files.
    # Label these links upstream-data, rather than presenting a source project
    # homepage or a training launcher as a released evaluation dataset/scorer.
    ga_rev='6c682a709c8bc801e942a8c410dca165d8f4c199'
    ga_source=source('model-final-genosm-generanno-upstream', 'GenerAnno prokaryotic task release / Genos-m upstream',
        f'https://huggingface.co/datasets/GenerTeam/prokaryotic-gener-tasks/tree/{ga_rev}', ga_rev,
        cache+'model-gaps-genosm/generanno-tree.json', 'dataset-repository',
        'Pinned root enumerates the named upstream configurations; exact Genos-m processed cohort equivalence is not asserted.')
    ga_e=ev('model-final-genosm-generanno-identifiers', ga_source, 'Pinned root tree plus official Genos-m benchmark inventory',
        'The upstream release contains gene_classification_bacteria, drug_resistence_prediction and all eight Genos-m named nutrient/stress fitness configurations. The Genos-m-specific cohort counts/splits remain documentation claims where they differ from upstream releases.')
    ga_targets=[('genosm-gene-class','gene_classification_bacteria'),('genosm-amr','drug_resistence_prediction')]
    for slug, folder in [
        ('glucose','Min-media-glucose_nutrient'),('arabinose','L-Arabinose_C'),('pyruvate','Pyruvate_C'),
        ('alanine','D-Alanine_N'),('ammonium','Ammonium-chloride_N'),('histidine','L-Histidine_nutrient'),
        ('cisplatin','Cisplatin_stress'),('perchlorate','perchlorate_stress')]:
        ga_targets.append(('genosm-fitness-'+slug,'fitness_prediction_'+folder))
    for tid, config in ga_targets:
        resource('genosm-upstream-'+config, ga_source, 'GenerAnno / '+config,
            'dataset','huggingface',f'https://huggingface.co/datasets/GenerTeam/prokaryotic-gener-tasks/tree/{ga_rev}/{config}',
            ga_rev,ga_e,'Named upstream release; Genos-m-specific processing/partitions are separately documented.',
            tasks=[tid],collection='genosm-evals',relation='upstream-data')
    resource('genosm-benchmark-results', 'src-genosm-inventory', 'Genos-m official benchmark protocols and result tables',
        'results','github',f'https://github.com/BGI-HangzhouAI/Genos-m/blob/{GENOS}/Technical_Notes/Benchmarks_en.md',
        GENOS,'genosm-inventory','Documentation and result tables; this file is not an evaluation dataset or executable scorer.',
        tasks=sorted(associated('genosm')),collection='genosm-evals')
    d['task_categories'].sort(key=lambda r:(r['task_id'],r['category_id'],r['relation']))


def gpn_artifacts(d, put, row, source, ev, field, limit, review, finding, count, resource):
    """Whole-file measurements of official HF benchmark releases and scores."""
    p = ROOT / 'research/artifacts/final-audit/model-gaps-gpn'
    manifest=ROOT/'data/gpnstar-artifact-inspections.json'
    if manifest.exists():
        measured=json.loads(manifest.read_text())
        scans=measured['files']
        scores=measured['score_intersections']
    else:
        scans=json.loads((p/'inspections.json').read_text())
        scores=json.loads((p/'score-intersections.json').read_text())
    intersections = {s['repo']: s for s in scores}
    mapping = {
        'clinvar_vs_benign': 'gpn-clinvar', 'cosmic': 'gpn-cosmic',
        'ukb_finemapped_coding': 'gpn-gwas-coding', 'gnomad_balanced': 'gpn-rare-human',
        'wmgp_balanced': 'gpn-rare-mouse', 'dest': 'gpn-rare-fly',
        'caendr': 'gpn-rare-worm', 'galbase': 'gpn-rare-chicken',
        '1001gp': 'gpn-rare-arabidopsis', 'mmrdb': 'gpn-mmrdb',
        'flybase_lethal': 'gpn-flybase', 'celegans_lethal': 'gpn-qin',
        'gpn-star-umap-regions': 'gpn-annotation'}
    for repo, tid in mapping.items():
        s = next(r for r in scans if r['repo'] == repo and r['path'] == 'test.parquet')
        revision = s['revision']; sid = 'model-final-gpn-' + repo
        u = f'https://huggingface.co/datasets/songlab/{repo}/blob/{revision}/test.parquet'
        source(sid, 'GPN-Star released benchmark / ' + repo, u, revision,
            f'research/artifacts/final-audit/model-gaps-gpn/{repo}/test.parquet', 'dataset-file',
            'Complete Parquet read; row counts, labels, coordinates and score-table lengths inspected. Dataset test is a storage split, not a pretraining chromosome holdout.')
        labels = s.get('label_counts', {})
        statement = (f'Complete pinned test.parquet scan: {s["rows"]:,} rows; labels {labels}; columns ' + ', '.join(s['columns']) + '. '
            'All rows are a released evaluation-source cohort, before any plot-specific consequence/score-availability restriction. This file does not itself define model pretraining train/test partitions.')
        eid = ev(sid + '-inspection', sid, 'Complete Parquet row/label/schema inspection', statement, 'data')
        resource(sid+'-data', sid, 'GPN-Star / '+repo, 'dataset', 'huggingface', u, revision, eid,
            'Complete released cohort; plot-specific scored subsets are separate.', tasks=[tid], collection='gpn-evals')
        t = row('tasks', tid); t['status'] = 'artifact-audited'
        count(repo + '-rows', tid, s['rows'], 'released rows', eid,
            qualifier='Complete pinned source cohort; not silently equated with a paper plot’s all-model finite-score denominator.')
        for label, n in labels.items():
            count(repo + '-label-' + label, tid, n, 'released rows', eid,
                split='label=' + label, qualifier='Source scalar label, before plot-specific filters.')
        t['limitations'] = ('Complete pinned benchmark file and all published score tables inspected. '
            'The released cohort count differs from each plot’s subset whenever consequence or score-availability filters apply. '
            'A finite intersection of every currently published score file is not automatically the comparator set used by a paper plot. '
            'No supervised chromosome/species holdout is inferred from the HF split name test.')
        field('tasks', tid, 'dataset_name', eid)
        field('tasks', tid, 'label_basis', eid)
        if repo in intersections:
            scores = intersections[repo]
            scoretext = (f'Every published prediction Parquet was fully scanned; each has {s["rows"]:,} rows aligned by release order. '
                f'Finite intersection across every currently published table: {scores["all_published_score_files_finite_intersection"]:,} rows, '
                f'labels {scores["finite_intersection_labels"]}. '
                'This diagnostic includes currently published comparator/configuration files, potentially more than a particular original figure; it is not asserted to reproduce a paper figure denominator.')
            se = ev(sid + '-score-inspection', sid,
                'Complete predictions/*.parquet; finite-value check by release row order', scoretext, 'data',
                f'https://huggingface.co/datasets/songlab/{repo}/tree/{revision}/predictions')
            resource(sid+'-results', sid, 'GPN-Star / '+repo+' released scores', 'results', 'huggingface',
                f'https://huggingface.co/datasets/songlab/{repo}/tree/{revision}/predictions', revision, se,
                'All released prediction tables inspected; not necessarily identical to a particular paper comparator set.',
                tasks=[tid], collection='gpn-evals')
            field('tasks', tid, 'limitations', se)
            review('tasks', tid, 'Complete official pinned benchmark and all released prediction Parquets; paper task/control definitions and archived workflow.',
                [eid, se, 'gpn-benchmarks'], 'Published score inventory can include configurations beyond individual figures; original plot-specific comparator eligibility remains separate.')
            limit('tasks', tid, 'paper_figure_denominator', 'not-reported',
                'Full source cohort and score availability are measurable. A machine-readable specification of the exact comparator/consequence subset for each reported figure is not included with these benchmark files.', se)
        if repo == 'mmrdb':
            finding('gpn-mmrdb-count', tid, 'gpn-evals',
                'Supplement reports 470 positive source SNVs before processing. Pinned released benchmark contains 433 positive and 503,959 control rows. These are distinct filtering stages; the positive source count is not the released cohort size.', eid, 'discrepancy')
        if repo == 'gpn-star-umap-regions':
            t.update(task_type='seven-class window classification',
                target='CDS, 5′ UTR, 3′ UTR, lncRNA exon, promoter-like cCRE, distal enhancer-like cCRE, background',
                output_description='One of seven genomic-region classes per supplied 100 bp window')
            for cid in ['cds', 'utr5', 'utr3', 'lncrna', 'promoter', 'enhancer', 'intergenic']:
                put('task_categories', dict(task_id=tid, category_id=cid, relation='class-target',
                    rationale='Actual released scalar class vocabulary; mixed region classifier, not a CDS-only assay.', evidence_id=eid, attribution='curatorial'),
                    ('task_id', 'category_id', 'relation'))
            put('task_feature_scopes', dict(id='model-final-gpn-annotation-cds', task_id=tid,
                feature_id='cds', scope='mixed', rationale='CDS is one of seven mutually exclusive classes; the task also includes UTRs, lncRNA, cCREs and background.', evidence_id=eid),
                ('task_id', 'feature_id'))
            field('tasks', tid, 'classification:cds', eid, 'Mixed seven-class classifier; not CDS-only coverage.')
            field('tasks', tid, 'target', eid)

    # Check both current supported code and the maintainer-published scientific
    # archive; the 31-item GPN-MSA list is not silently promoted to GPN-Star data.
    sid = source('model-final-gpn-releases', 'GPN current release and scientific archive inventory',
        f'https://github.com/songlab-cal/gpn/blob/{GPN_CURRENT}/release/analysis-archive.md', GPN_CURRENT,
        'research/artifacts/final-audit/model-gaps-releases/songlab-cal-gpn-dc5fd28/release/analysis-archive.md',
        'repository-file', 'Complete current repository and full archived research snapshot 30dee6cf downloaded; official songlab HF dataset registry and GPN-Star collection inspected.')
    eid = ev('model-final-gpn-panel-source-review', sid,
        'Historical archive manifest; GPN-Star Snakefile_hg38 lines 74–88; upstream GPN-MSA dms.smk',
        'Current maintained release explicitly archives paper analyses at 30dee6cf. Archived GPN-Star workflow has a commented local results/dms dependency but no released scored ProteinGym manifest; upstream GPN-MSA code enumerates 31 CADD-derived human assays. Official songlab HF registry and published GPN-Star collection contain no matching ProteinGym release. Same panel size is not proof of exact assay/score-intersection identity.')
    resource('gpn-archived-variant-scoring-code','src-gpn-calibration-code',
        'GPN-Star archived likelihood/entropy calibration workflow','evaluation-code','github',
        f'https://github.com/songlab-cal/gpn/blob/{GPN_ARCHIVE}/analysis/gpn-star/train_and_eval/workflow/rules/vep.smk',
        GPN_ARCHIVE,'gpn-calibration-code',
        'Archived scientific workflow with external/local inputs; this file is code, not a released benchmark cohort.',
        tasks=[t['id'] for t in d['tasks'] if t['id'].startswith('gpn-') and t['id'] not in ['gpn-annotation','gpn-ldsc','gpn-rvat','gpn-ldlr']],
        collection='gpn-evals')
    t = row('tasks', 'gpn-proteingym')
    t['status'] = 'source-limited'
    t['limitations'] = ('Supplement explicitly defines 31 human ProteinGym v0.1 assays, single-nucleotide-accessible amino-acid substitutions and CADD-based nucleotide choice. '
        'Complete current/archived GPN code and official HF registry do not release a GPN-Star-specific assay/retained-variant manifest. '
        'The upstream GPN-MSA 31-item list is identifiable but is not asserted to equal the final GPN-Star scored intersection.')
    limit('tasks', t['id'], 'assay_manifest', 'not-released', t['limitations'], eid)
    review('tasks', t['id'], 'Full supplement benchmark definition; complete current and archived official code; complete official HF dataset registry and GPN-Star collection.',
        [eid, 'gpn-benchmarks'], 'Panel claim retained; no unverifiable per-assay records manufactured.')
    field('tasks', t['id'], 'limitations', eid)
    for o in d['task_outputs']:
        if o['task_id']==t['id']:
            o.update(status='supported',
                rationale='The source explicitly evaluates a likelihood-derived score per supplied mutation and absolute/rank correlation within protein assays. Unknown assay IDs do not make the isolated output form ambiguous.',
                limitations='The 31-assay identity and processed mutation manifest are not released; these are separate source fields, not an output-form ambiguity.')
    hgmd=row('tasks','gpn-hgmd')
    hgmd['limitations']='Supplement defines curated regulatory positives and nine matched common controls per positive. Exact matched cohort, processed score tables and retained all-model intersection are not present in the inspected official registry/release.'
    limit('tasks','gpn-hgmd','processed_dataset','not-released',hgmd['limitations'],eid)
    row('evaluations', 'gpn-evals')['notes'] = ('Paper/supplement and complete pinned current/archived code inspected. '
        'Thirteen official benchmark datasets and all published prediction tables fully scanned. '
        'Raw release counts and finite-score intersections remain distinct from paper plot denominators. '
        'The 31-assay ProteinGym claim lacks a model-specific released manifest.')
