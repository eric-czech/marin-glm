"""Complete the two previously unresolved PlantCAD2 partition definitions."""
import json
from common import Catalogue, ROOT

REV='de8bd9b67bb413b1502c4bf9e369ddc46180cb10'
BASE='https://huggingface.co/datasets/plantcad/PlantCAD2_fine_tuning_tasks/'


def populate(d):
    c=Catalogue(d)
    for name,config,taskids in [
        ('cell','cell_type_specific_acr',['plantcad2-ft-cell_type_specific_acr']),
        ('translation','cross_species_leaf_absolute_translation',['plantcad2-ft-cross_species_leaf_absolute_translation','plantcad2-ft-cross_species_leaf_on_off_translation'])]:
        path='data/plantcad-'+name+'-artifact-inspections.json'
        manifest=json.loads((ROOT/path).read_text())
        sid=c.source('plantcad-final-'+name+'-inspection','PlantCAD2 complete '+name+' release inspection',
            'https://github.com/eric-czech/marin-glm/blob/main/'+path,'dataset',REV,path=path)
        if name=='cell':
            statement=('All six Parquets fully scanned: 2,517,259 train, 629,315 validation, 243,845 test windows. '+
                'Every DNA sequence is 600 bp and every label is a 92-character binary vector. Train/validation both span maize chr1–9; test is chr10. '+
                'Exact coordinate IDs are disjoint; exact DNA strings overlap by 69 train/validation, 18 train/test and 6 validation/test unique strings.')
        else:
            statement=('All six absolute/on-off translation Parquets fully scanned: 21,894 Arabidopsis train, 5,492 Arabidopsis validation, 39,035 maize test rows per target. '+
                'Training and validation both contain Arabidopsis chr1–5; no shared gene IDs or exact sequences across any partition pair. '+
                'All sequences are 500 bp. Absolute labels equal log10(1+TPM), binary labels equal TPM>1 in every row.')
        ev=c.evidence('plantcad-final-'+name+'-inspection',sid,'Whole-file SHA256; full sequences, labels and partition identifiers',statement,'data')
        for tid in taskids:
            t=c.get('tasks',tid);t['status']='artifact-audited'
            related=[r for r in manifest['files'] if (name=='cell' or r['path'].startswith(tid.removeprefix('plantcad2-ft-')+'/'))]
            for row in related:
                fileid='plantcad-final-file-'+row['path'].replace('/','-').removesuffix('.parquet')
                fs=c.source(fileid,'PlantCAD2: '+row['path'],BASE+'blob/'+REV+'/'+row['path'],'dataset-file',REV,
                    notes='Whole-file SHA256: '+row['sha256']+'. Complete sequence/label/partition scan in the linked inspection manifest.')
                rid=c.resource(fileid,fs,row['path'],'dataset','huggingface',BASE+'blob/'+REV+'/'+row['path'],ev,revision=REV)
                c.task_resource(tid,rid,ev)
                c.collection_resource('plantcad2-ft',rid,ev)
            if name=='cell':
                split='Training and validation both use maize chr1–9; held-out test is chr10. Exact coordinate IDs are disjoint. Exact DNA strings recur across splits (69 train/validation, 18 train/test, 6 validation/test unique strings); chromosome holdout does not guarantee sequence uniqueness.'
                notes='Full 600-bp DNA and 92-label vectors were checked for every released row. Coordinate-ID uniqueness does not establish that intervals on shared chromosomes do not overlap. All cell-type labels participate in adaptation; this is not a held-out-cell-type protocol.'
                for partition,n in [('train',2517259),('validation',629315),('test',243845)]:
                    c.count(tid,n,'released windows',ev,split=partition,method='measured')
                t['limitations']='The exact coordinate IDs are disjoint, but repeated DNA strings occur across partitions. Homology separation and pretraining exclusion are not established by this scan.'
            else:
                split='Arabidopsis gene rows are split into training/validation, with all chr1–5 represented in both; maize genes on chr1–10 form the species-transfer test. No shared gene IDs or exact 500-bp sequences occur between partitions. Validation is not a chromosome holdout.'
                notes='Released labels are TPM>1 for on/off and log10(1+TPM) for regression. The latter differs from the paper’s stated log10(TPM). These labels derive from Ribo-seq abundance, not direct protein quantitation.'
                t['limitations']='Complete gene-ID and exact-sequence separation was verified for the released splits; homologous genes across species may remain. The source does not report a homology exclusion procedure.'
            for p in [r for r in d['protocols'] if r['task_id']==tid and r['id'].startswith('plantcad2-')]:
                p.update(split_rule=split,notes=notes)
                c.field('protocols',p['id'],'split_rule',ev)
                c.review('protocols',p['id'],'Full released partition/label/sequence inspection plus the cited original adaptation method.',[ev,p['source_evidence_id']],t['limitations'])
            c.field('tasks',tid,'limitations',ev)
            c.review('tasks',tid,'Complete pinned Parquet DNA/label/identifier scan across all released splits; original-paper adaptation kept separate.',[ev,t['evidence_id']],t['limitations'])
    return d
