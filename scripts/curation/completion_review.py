"""Remove superseded catalogue-progress prose after its source work is complete."""
from common import Catalogue


def populate(d):
    c=Catalogue(d)
    # These are superseded editorial progress notes, not unresolved source facts.
    d['findings']=[r for r in d['findings'] if r['id']!='finding-002']
    c.get('sources','project-paper-dna-foundation')['notes']='Earlier source registration. Complete journal text, supplement, released classification tables and variant/attention artifacts are reviewed under dnafoundation-fulltext and the linked task evidence.'
    c.get('evaluations','evo-original')['notes']='Original Evo 2 source collection with task-specific methods and separate scored cohorts. Likelihood perturbations, viral assay claims, generation diagnostics and quantitative SAE analyses are decomposed; exact unpublished manifests remain source limits.'
    count=c.get('counts','count-0114')
    count['qualifier']='Carbon reports 6,840 BRCA2 variants; CENO/Evo 2 report 6,837 in their source protocols. Exact original scored identities are not jointly available, so cohort/filter equivalence is not established.'
    f=c.get('findings','finding-031')
    f['description']='AIDO.DNA2 uses 524-kb coverage inputs and reports 7,379 tracks. The available report does not provide a complete scored track manifest, specify all output bins, or explicitly name the reported correlation as Pearson/Spearman. Long input and local attention do not establish dependence on every distal base.'
    for row in d['field_evidence']:
        if row['entity_table']!='evaluations' or row['field']!='output_audit':continue
        if row['entity_id']=='lambda':
            row['note']='Decomposed segment classification, bacterial/phage controls, shuffled backgrounds and genome-wide detection have separate scored outputs and context variants. See their task-level output reviews.'
        elif row['entity_id']=='lrb':
            row['note']='Decomposed reference-function, QTL and expression readouts retain their own output/scoring units. The inspected workshop release does not provide a dense gene-annotation benchmark.'
        elif row['entity_id']=='dnalongbench':
            row['note']='Decomposed contact-map, functional-track and regulatory relationship targets retain distinct output/scoring units. Contact matrices are not equivalent to isolated enhancer–gene pairs.'
    for row in d['project_review_evaluations']:
        note=row.get('note') or ''
        if any(term in note.lower() for term in ['pending','remain to be','awaiting']):
            n=len([r for r in d['evaluation_tasks'] if r['evaluation_id']==row['evaluation_id']])
            row['note']=f'{n} linked dataset × target records; source-specific cohorts, readouts and splits are retained as variants/protocols.'
    c.get('project_adoptions','adoption-lrb-factory')['scope']='LRB aggregate reported in Table 8. The aggregate alone does not identify each retained task-level cohort/metric; it is adoption evidence, not a reconstructed per-task score table.'
    # Coarse collection labels summarize completed reviews, not iteration state.
    reviewed={r['entity_id'] for r in d['source_reviews'] if r['entity_table']=='evaluations'}
    for collection in d['evaluations']:
        if collection['id'] in reviewed:collection['status']='audited'
    # New standard biological features are retained in the individual view.
    for r in d['task_outputs']:
        if r['limitations'].startswith('This decision concerns the scored output only. It does not upgrade'):
            r['limitations']='Output form is independent of adaptation, source availability and split validity; those are recorded separately.'
    return d
