"""Close bibliographic, collection and review-reference consistency checks."""
import json
from common import Catalogue, DATE


def populate(d):
    c=Catalogue(d)
    # A model's own evaluation collection is not a dedicated benchmark project.
    ev='evo1-training'
    c.put('project_reviews',dict(id='collection-evo1',name='Evo 1 original evaluations',decision='outside-definition',
        dedicated=0,reviewed=DATE,search_scope='Full original Science paper and pinned original code/data release; benchmark purpose reviewed.',
        rationale='Evaluation accompanies a foundation-model paper. It does not primarily establish a dedicated standardized evaluation framework.',evidence_id=ev))
    c.put('project_review_evaluations',dict(review_id='collection-evo1',evaluation_id='evo1-original',relation='associated-collection',
        note='Model-associated evaluation collection; not a qualified dedicated benchmark project.',evidence_id=ev),('review_id','evaluation_id'))
    c.put('project_review_papers',dict(review_id='collection-evo1',paper_id='evo1',relation='associated-model',evidence_id=ev),('review_id','paper_id','relation'))
    # The full journal source superseded the earlier DNA Foundation registration.
    for link in d['project_review_papers']:
        if link['paper_id']=='dna-foundation' and link['relation']!='adoption-evidence':link['evidence_id']='dnafoundation-classification-method'
    alpha_source=c.source('alphagenome-journal','Advancing regulatory variant effect prediction with AlphaGenome',
        'https://www.nature.com/articles/s41586-025-10014-0','paper','Nature 649, 1206–1218 (2026)',
        path='research/artifacts/final-audit/other-models/alphagenome-journal.xml',
        notes='Full journal XML retrieved through Europe PMC. Earlier 103-page author preprint is retained as a separate source representation.')
    alpha=c.evidence('alphagenome-final-journal',alpha_source,'Article metadata; Unifying DNA sequence-to-function model; Methods',
        'Journal publication 28 January 2026, DOI 10.1038/s41586-025-10014-0. Supervised human/mouse sequence-to-function model: 1-Mb DNA input, multiple genomic signal and splicing outputs. '+
        'Original paper includes both genomic track and variant-effect evaluations; catalogued BEND/NTv3 re-evaluations retain their own protocols.')
    c.get('papers','alphagenome').update(title='Advancing regulatory variant effect prediction with AlphaGenome',
        source_id=alpha_source,doi='10.1038/s41586-025-10014-0',publication_date='2026-01-28',year=2026,status='journal')
    c.field('papers','alphagenome','source_id',alpha,'Earlier author-hosted preprint remains in the evidence registry; journal and preprint versions are distinct.')
    c.review('models','alphagenome','Original model/output definition and catalogued BEND/NTv3 comparison interfaces; full journal and earlier author report available.',[alpha,'model-alphagenome'],
        'Additional evaluation-source scope, rather than a claim that every assay in the original model paper has an independent catalogue record.')
    c.review('papers','alphagenome','Full journal metadata/main methods and prior author-report representation; associated re-evaluations reviewed independently.',[alpha])
    # Close bibliographic records only at their actual reviewed scope. An adoption
    # paper does not become a new primary model/evaluation merely by being cited.
    reviewed={(r['entity_table'],r['entity_id']) for r in d['source_reviews']}
    for p in d['papers']:
        if ('papers',p['id']) in reviewed:continue
        direct=[e['id'] for e in d['evidence'] if e['source_id']==p['source_id']]
        if not direct:
            # Some registry entries are official artifact/documentation releases,
            # rather than articles. Record that identity without inventing text.
            source=c.get('sources',p['source_id'])
            direct=[c.evidence('registry-identity-'+p['id'],p['source_id'],'Official source identity and inspected version',
                p['title']+'. Source representation: '+source['kind']+'; '+(source['version'] or 'version not stated')+'.',
                basis='documentation')]
        purpose='Publication identity/version, indexed benchmark definitions and source-specific task citations.'
        if p['scope']=='adoption-evidence':purpose='Publication identity and the particular external benchmark adoption cited by the project review; not an audit of every experiment in this paper.'
        elif p['scope']=='additional-evaluation-source':purpose='Publication identity and the indexed evaluation-source claims; task-specific review scopes remain in the linked task records.'
        c.review('papers',p['id'],purpose,direct,
            'This bibliographic review does not assert that every experiment or raw dataset in the publication is independently reproduced.')
    # Explicitly derived protocol reviews use their own primary source locator and
    # the completed task review; they are not new claims of data verification.
    reviews={(r['entity_table'],r['entity_id']):r for r in d['source_reviews']}
    for p in d['protocols']:
        if ('protocols',p['id']) in reviews:continue
        task=reviews.get(('tasks',p['task_id']))
        if task:
            ids=[p['source_evidence_id']]+json.loads(task['evidence_ids_json'])
            c.review('protocols',p['id'],'Protocol is included in the completed task-source review: adaptation, interface, partition/scoring rule and any stated selection. Primary locator is retained separately.',ids,
                'Reported definitions are distinguished from recounted artifacts; source limits on the task and protocol remain applicable.')
    # Collections that only aggregate already reviewed tasks still need an explicit
    # final source summary, rather than a frozen progress flag.
    for eid in ['traitgym','proteingym','compass']:
        collection=c.get('evaluations',eid)
        members=[r['task_id'] for r in d['evaluation_tasks'] if r['evaluation_id']==eid]
        evidence=[collection['evidence_id']]
        for tid in members:
            review=next((r for r in d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==tid),None)
            if review is None:raise ValueError('Unreviewed collection member: '+tid)
            evidence.extend(json.loads(review['evidence_ids_json']))
        collection['status']='audited'
        c.review('evaluations',eid,'All indexed constituent dataset × target records and their source-specific protocols/resources reviewed. Shared benchmark membership is not a new independent assay.',evidence)
    return d
