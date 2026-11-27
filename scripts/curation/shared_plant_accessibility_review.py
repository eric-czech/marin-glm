"""One maize accessibility target, with distinct PlantCAD2/BOTANIC protocols."""
import json
from common import Catalogue
from task_identity_review import IdentityReview


def populate(d):
    c=Catalogue(d)
    old='botanic1-long-atac'
    target='plantcad2-ft-cell_type_specific_acr'
    source=c.get('evidence','botanic-final-long-atac')['source_id']
    ev=c.evidence('plant-accessibility-shared-target',source,'BOTANIC-1 §4.7.1, Table S11; linked PlantCAD2 maize cell-type accessibility source',
        'BOTANIC-1 explicitly reuses the PlantCAD2 maize 92-cell-type accessibility dataset. The dataset and target are shared, while BOTANIC reports chromosome 9/10 testing and variable-context adaptation/pooling recipes. The inspected PlantCAD2 release instead holds chromosome 10 for test and uses 600-bp windows. Shared identity does not establish equal historical partitions, context extraction or scored rows.')
    if any(t['id']==old for t in d['tasks']):
        vid=old+'-paper-cohort'
        c.put('variants',dict(id=vid,task_id=old,name='BOTANIC-1 variable-context maize accessibility cohort',
            dataset_revision=None,context='PlantCAD2 source labels; BOTANIC reports chr9/10 test. Original per-example context and scored-cohort manifest not released.',
            input_length='150–128,000 bp source contexts',target_count=92,target_unit='cell-type labels',
            notes='Four adaptation/pooling recipes and context-dependent effective learning rate. Do not substitute the pinned PlantCAD2 HF partition for the BOTANIC paper partition.',evidence_id=ev))
        for p in d['protocols']:
            if p['task_id']==old and p.get('variant_id') is None:p['variant_id']=vid
        for r in d['evaluation_tasks']:
            if r['task_id']==old and r.get('variant_id') is None:r['variant_id']=vid
    IdentityReview(d).merge(old,target,ev,'botanic1-evals',
        'BOTANIC-1 explicitly reuses the PlantCAD2 maize 92-cell-type accessibility dataset and target. Its chromosome partition, contexts and adaptation recipes remain a distinct source protocol/cohort variant.')
    t=c.get('tasks',target)
    t.update(description='Predict the 92-cell-type accessibility vector for supplied maize windows. PlantCAD2 and BOTANIC-1 use the same source dataset and target, with distinct partition, context and adaptation protocols.',
        label_basis='Experimental cell-type-specific maize ATAC-seq accessibility labels',
        input_description='Maize DNA; 600 bp in the pinned PlantCAD2 release, variable contexts in the BOTANIC-1 protocol',
        limitations='Pinned PlantCAD2 coordinate IDs are distinct across partitions, but some exact DNA strings recur. This does not establish interval, homology or pretraining separation. BOTANIC-1 reports a different chromosome partition; exact original scored rows/context extraction are not released. Its context-length comparison also changes the effective learning rate in some LoRA recipes.')
    for field in ['description','label_basis','input_description','limitations']:c.field('tasks',target,field,ev)
    review=next(r for r in d['source_reviews'] if r['entity_table']=='tasks' and r['entity_id']==target)
    c.review('tasks',target,'Shared original dataset × target identity; complete pinned PlantCAD2 Parquet sequence/label/identifier scan; BOTANIC-1 context, chromosome, adaptation and scoring methods separately reviewed.',
        json.loads(review['evidence_ids_json'])+[ev],t['limitations'])
    c.limit('protocols','botanic1-long-atac-protocol','original-context-and-scored-cohort-manifest','not-released',
        'The inspected BOTANIC release does not supply the original per-example context extraction and scored train/test manifest. Its paper uses chr9/10 test, whereas the pinned PlantCAD2 Parquets use chr10 test. Neither exact cohort nor partition equality is assumed.',ev)
    return d
