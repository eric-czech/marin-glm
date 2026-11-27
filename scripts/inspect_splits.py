"""Bounded split checks of already cached public releases.

Run in the research environment, never during the offline site build. No network
or dataset download occurs. The separate verify_split_rows.py checks bounded APIs.
Full many-million-row sequence scans are not repeated.
The PlantCAD2 full exact counts are reused from the completed earlier inspection;
this script checks lightweight coordinates and retrieves a bounded set of rows.
"""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import itertools
import numpy as np
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/artifacts/final-audit'
OUT=ROOT/'data/split-inspections.json'
DATE='2026-11-27'
MAX_NEW_SEQUENCE_ROWS=1_500_000
COMPLEMENT=str.maketrans('ACGTRYMKBDHVNacgtrymkbdhvn','TGCAYRKMVHDBNtgcayrkmvhdbn')

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def load():
    return json.loads(OUT.read_text()) if OUT.exists() else dict(inspected=DATE,network_bytes_downloaded=0,cases={},examples=[])
def save(d):
    # Preserve disjoint completed cases if an interactive run resumes from an
    # older in-memory snapshot. Normal authoring runs remain sequential.
    if OUT.exists():
        current=json.loads(OUT.read_text())
        current['cases'].update(d['cases'])
        examples={json.dumps(e,sort_keys=True):e for e in current['examples']+d['examples']}
        d=current;d['examples']=list(examples.values())
    temporary=OUT.with_suffix('.json.tmp');temporary.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');temporary.replace(OUT)
def record_file(path,url):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return dict(path=str(path.relative_to(ROOT)),url=url,sha256=h.hexdigest(),bytes=path.stat().st_size)
def pairs(names):return list(itertools.combinations(names,2))
def hf_row(repo,config,split,index):return f'https://huggingface.co/datasets/{repo}/viewer/{config}/{split}?row={index}'

def plantcad(d):
    repo='plantcad/PlantCAD2_fine_tuning_tasks';rev='de8bd9b67bb413b1502c4bf9e369ddc46180cb10';config='cell_type_specific_acr'
    root=CACHE/'plantcad-ft'/config
    prior=json.loads((ROOT/'data/plantcad-cell-artifact-inspections.json').read_text())
    files=sorted(root.glob('*.parquet'));assert len(files)==6
    coords=collections.defaultdict(lambda:collections.defaultdict(list));example_coords={}
    # Only the compact genomic coordinate columns are read for all 3.39M rows.
    for f in files:
        split=f.name.split('-')[0]
        q=pq.ParquetFile(f)
        for b in q.iter_batches(columns=['chr','start','end'],batch_size=65536):
            names=b.column(0).to_numpy(zero_copy_only=False);starts=b.column(1).to_numpy();ends=b.column(2).to_numpy()
            assert np.all(ends-starts==600)
            for chrom in sorted(set(names)):
                coords[split][chrom].append(starts[names==chrom])
    for split,cs in coords.items():
        for chrom,arr in cs.items():cs[chrom]=np.sort(np.concatenate(arr))
    intersections={}
    for left,right in [('train','validation'),('train','test'),('validation','test')]:
        lp=rp=npairs=0
        for chrom in sorted(set(coords[left])&set(coords[right])):
            a=coords[left][chrom];b=coords[right][chrom]
            c=np.searchsorted(b,a+600,side='left')-np.searchsorted(b+600,a,side='right')
            z=np.searchsorted(a,b+600,side='left')-np.searchsorted(a+600,b,side='right')
            npairs+=int(c.sum());lp+=int(np.count_nonzero(c));rp+=int(np.count_nonzero(z))
            if c.any() and (left,right) not in example_coords:
                i=int(np.flatnonzero(c)[0]);j=int(np.searchsorted(b+600,a[i],side='right'))
                example_coords[left,right]=(chrom,int(a[i]),int(b[j]))
        intersections[left+'-'+right]=dict(interval_pairs=npairs,left_rows_with_any_overlap=lp,right_rows_with_any_overlap=rp,interval_convention='[start,end), positive-length overlap; no padding/context extension')
    # Hold only SHA-256 keys/row metadata; recover ≤3 examples per pair, not a
    # fresh exhaustive comparison. Validation+test have 873,160 rows combined.
    lookup={};newrows=0;examples=[];global_offset=collections.Counter();per_pair=collections.Counter()
    for split in ['test','validation','train']:
        for f in [p for p in files if p.name.startswith(split+'-')]:
            offset=0
            for batch in pq.ParquetFile(f).iter_batches(batch_size=8192):
                for r in batch.to_pylist():
                    if newrows>=MAX_NEW_SEQUENCE_ROWS:break
                    key=digest(r['sequence']);row=dict(split=split,file=f'{config}/{f.name}',file_row=offset,
                        split_row=global_offset[split],chr=r['chr'],start=r['start'],end=r['end'],label=r['label'])
                    row['file_url']=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{row["file"]}'
                    row['viewer_url']=hf_row(repo,config,split,row['split_row'])
                    for other in ['test','validation']:
                        pair=tuple(sorted([split,other]))
                        if other!=split and (other,key) in lookup and per_pair[pair]<3:
                            previous=lookup[other,key]
                            examples.append(dict(case='plantcad-cell',kind='exact-sequence',sequence_sha256=key,sequence_length=600,
                                sequence=r['sequence'],left=previous,right=row,labels_equal=previous['label']==row['label']))
                            per_pair[pair]+=1
                    if split in ['test','validation']:lookup.setdefault((split,key),row)
                    offset+=1;global_offset[split]+=1;newrows+=1
                if newrows>=MAX_NEW_SEQUENCE_ROWS:break
                if split=='train' and per_pair[tuple(sorted(['train','test']))]>=3 and per_pair[tuple(sorted(['train','validation']))]>=3:break
            if newrows>=MAX_NEW_SEQUENCE_ROWS:break
            if split=='train' and per_pair[tuple(sorted(['train','test']))]>=3 and per_pair[tuple(sorted(['train','validation']))]>=3:break
    # Recover the coordinate-only example row positions by scanning just numeric
    # columns; its sequence need not be read or stored.
    for (left,right),(chrom,a,b) in example_coords.items():
        found={}
        for split,start in [(left,a),(right,b)]:
            total=0
            for f in [p for p in files if p.name.startswith(split+'-')]:
                offset=0
                for batch in pq.ParquetFile(f).iter_batches(columns=['chr','start'],batch_size=65536):
                    for ch,st in zip(batch.column(0).to_pylist(),batch.column(1).to_pylist()):
                        if ch==chrom and st==start:
                            found[split]=dict(split=split,file=f'{config}/{f.name}',file_row=offset,split_row=total,
                                chr=chrom,start=start,end=start+600,
                                file_url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{config}/{f.name}',viewer_url=hf_row(repo,config,split,total))
                            break
                        offset+=1;total+=1
                    if split in found:break
                if split in found:break
        examples.append(dict(case='plantcad-cell',kind='interval',left=found[left],right=found[right],overlap_bp=min(a+600,b+600)-max(a,b)))
    d['cases']['plantcad-cell']=dict(repo=repo,revision=rev,full_exact_inspection='data/plantcad-cell-artifact-inspections.json',
        exact_sequence_intersections=prior['exact_sequence_intersections'],coordinate_id_intersections=prior['coordinate_intersections'],
        partition_rows=prior['distinct_coordinates'],interval_intersections=intersections,
        new_sequence_rows_read=newrows,new_sequence_row_cap=MAX_NEW_SEQUENCE_ROWS,
        method='Reuse prior full exact-sequence counts. Read all coordinate columns only for interval checks. Bounded sequence-row pass recovers illustrative matches; it does not estimate or replace full counts.',
        files=[{k:r[k] for k in ['path','rows','sha256','bytes']} for r in prior['files']])
    d['examples']=[e for e in d['examples'] if e['case']!='plantcad-cell']+examples
    print(json.dumps(d['cases']['plantcad-cell'],indent=2));save(d)


def csv_rows(path,column):
    with path.open(newline='') as f:
        for i,r in enumerate(csv.DictReader(f)):
            yield r[column],dict(file_row=i,line=i+2,label=r.get('label',r.get('DMS_score')),id=r.get('mutant',r.get('name')))

def parquet_rows(path,column):
    i=0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=8192):
        for r in batch.to_pylist():
            yield r[column],dict(file_row=i,label=r.get('label'),id=r.get('entry',r.get('Entry',r.get('id',r.get('gene')))))
            i+=1

def sequence_case(d,id,specs,alphabet='DNA',extra=None):
    total=0;seqs={};files=[];parts={}
    for spec in specs:
        path=ROOT/spec['path'];split=spec['split'];rows={};canon={};n=0
        iterator=parquet_rows(path,spec.get('column','sequence')) if path.suffix=='.parquet' else csv_rows(path,spec.get('column','sequence'))
        for seq,meta in iterator:
            if total>=MAX_NEW_SEQUENCE_ROWS:raise ValueError('Case exceeds practical sequence limit: '+id)
            if not isinstance(seq,str) or not seq:continue
            meta.update(split=split,file=spec['path'],file_url=spec['url'])
            if 'viewer_config' in spec:meta['viewer_url']=hf_row(spec['repo'],spec['viewer_config'],split,meta['file_row'])
            rows.setdefault(seq,meta)
            s=seq.upper()
            if alphabet=='DNA':canonical=min(s,s.translate(COMPLEMENT)[::-1]);canon.setdefault(canonical,meta)
            n+=1;total+=1
        seqs[split]=(rows,canon);parts[split]=dict(rows=n,unique_sequences=len(rows),unique_reverse_complement_classes=len(canon) if alphabet=='DNA' else None)
        files.append(record_file(path,spec['url'])|dict(split=split))
    comparisons=[];examples=[]
    for a,b in pairs(list(parts)):
        left,lc=seqs[a];right,rc=seqs[b];shared=sorted(left.keys()&right.keys())
        comparisons.append(dict(left=a,right=b,kind='exact-sequence',shared=len(shared),unit='distinct exact sequence strings'))
        if alphabet=='DNA':
            exact_classes={min(s.upper(),s.upper().translate(COMPLEMENT)[::-1]) for s in shared}
            comparisons.append(dict(left=a,right=b,kind='reverse-complement',shared=len(lc.keys()&rc.keys()),unit='distinct uppercase sequence / reverse-complement equivalence classes'))
            comparisons.append(dict(left=a,right=b,kind='reverse-complement-only',shared=len((lc.keys()&rc.keys())-exact_classes),unit='additional shared equivalence classes without an exact-string match'))
        for s in shared[:2]:examples.append(dict(case=id,kind='exact-sequence',sequence_sha256=digest(s),sequence_length=len(s),sequence=s,
            left=left[s],right=right[s],labels_equal=left[s].get('label')==right[s].get('label')))
        if alphabet=='DNA':
            left_strings={min(s.upper(),s.upper().translate(COMPLEMENT)[::-1]):s for s in left}
            right_strings={min(s.upper(),s.upper().translate(COMPLEMENT)[::-1]):s for s in right}
            for key in sorted((lc.keys()&rc.keys())-exact_classes)[:2]:
                ls=left_strings[key];rs=right_strings[key]
                examples.append(dict(case=id,kind='reverse-complement-only',sequence_sha256=digest(key),sequence_length=len(key),
                    sequence_left=ls,sequence_right=rs,left=left[ls],right=right[rs],
                    hash_definition='SHA-256 of lexicographically smaller uppercase sequence/reverse-complement string'))

    d['cases'][id]=dict(partitions=parts,comparisons=comparisons,files=files,sequence_rows_read=total,
        method='Complete selected files; exact case-sensitive strings, plus uppercase reverse-complement equivalence for DNA only. No similarity search or pretraining comparison.',**(extra or {}))
    d['examples']=[e for e in d['examples'] if e['case']!=id]+examples;save(d)
    print(id,total,[(c['left'],c['right'],c['kind'],c['shared']) for c in comparisons],flush=True)


def selected(d):
    # Pinned native NT/GUE (and their GENEB repackaging) distinguish whole-string
    # equality from reverse-complement leakage without scanning large datasets.
    rev='4edd705be573e48c585c2cf79dc320f9f43c7b04';repo='darlednik/geneb-tasks'
    for config in ['InstaDeepAI_nucleotide_transformer_downstream_tasks_enhancers',
            'InstaDeepAI_nucleotide_transformer_downstream_tasks_revised_enhancers_types',
            'leannmlindsey_GUE_prom_core_all','katarinagresova_Genomic_Benchmarks_human_enhancers_ensembl']:
        specs=[]
        for split in ['train','test']:
            rel='tasks/'+config+'/'+split+'.csv';path=ROOT/'research/artifacts/audit-followup/geneb'/rel
            if path.exists():specs.append(dict(path=str(path.relative_to(ROOT)),split=split,column='text',url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{rel}'))
        if len(specs)==2:sequence_case(d,'selected-'+config,specs,extra=dict(repo=repo,revision=rev,config=config))
    # MIBiG contains DNA examples and protein examples; RC is meaningful only DNA.
    manifest=json.loads((ROOT/'data/existing-benchmark-inspections.json').read_text())['facts']['DGEB_FILES']
    for suffix,alphabet in [('dna','DNA'),('prot','protein')]:
        repo='tattabio/mibig_classification_'+suffix;specs=[]
        for r in manifest:
            if r['repo']!=repo:continue
            split='train' if 'train' in r['file'] else 'test'
            path=CACHE/'existing-hf'/repo.replace('/','--')/r['file']
            if path.suffix=='.parquet':specs.append(dict(path=str(path.relative_to(ROOT)),split=split,column='Sequence',url=f'https://huggingface.co/datasets/{repo}/blob/{r["revision"]}/{r["file"]}'))
        if specs:
            names=pq.ParquetFile(ROOT/specs[0]['path']).schema.names
            for s in specs:s['column']='sequence' if 'sequence' in names else 'Sequence'
            sequence_case(d,'dgeb-mibig-'+suffix,specs,alphabet=alphabet,extra=dict(repo=repo))


def rna_and_mrna(d):
    root=ROOT/'research/artifacts/audit-followup/rnagym'
    for mode in ['random','min_similarity']:
        for assay in ['Ke_2017_mRNA','Pitt_2010_ribozyme']:
            specs=[]
            for split,folder in [('train','train'),('validation','val')]:
                rel=f'CV_splits/{mode}/{folder}/{assay}_{folder}.csv'
                specs.append(dict(path=str((root/rel).relative_to(ROOT)),split=split,column='sequence',
                    url='https://marks.hms.harvard.edu/rnagym/fitness_prediction/fitness_CV_splits.zip'))
            sequence_case(d,'rnagym-'+mode+'-'+assay,specs,alphabet='RNA',extra=dict(archive_member_pattern=f'CV_splits/{mode}/{{train,val}}/{assay}_{{train,val}}.csv'))
    import ast,zipfile,types
    code=CACHE/'existing-mrnabench/mrna_bench/data_splitter/homology_split.py'
    function=next(n for n in ast.parse(code.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='train_test_split_homologous')
    ns={'np':np,'pd':types.SimpleNamespace(DataFrame=object)}
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(code),'exec'),ns)
    zpath=CACHE/'existing-residual/homology_maps_homologene.zip'
    with zipfile.ZipFile(zpath) as z:
        lines=z.read('homology_maps_homologene/human_homology_map.csv').decode().splitlines()
    hmap={r['gene_name']:int(r['gene_group']) for r in csv.DictReader(lines)}
    # The source function uses exactly one DataFrame operation: convert the
    # selected gene-name/group columns to a dict. This adapter supplies that
    # operation without installing pandas or changing the source algorithm.
    class Series:
        def to_dict(self):return hmap
    class HomologyTable:
        def set_index(self,name):return {'gene_group':Series()}
    homology=HomologyTable()
    for repo,file,rev in [('morrislab/mrl-sugimoto','mrl-sugimoto.parquet','4d7404895e8ca1143d769e7f445972bf7ef4b51d'),
        ('morrislab/rna-lifecycle-ietswaart','ietswaart_processed.parquet','1c1e15f85b05cb1e8b2d044f33f8467eaa3c1e8a')]:
        path=CACHE/'existing-residual'/repo.replace('/','--')/file
        records=pq.ParquetFile(path).read(columns=['gene','sequence','target']).to_pylist()
        valid=[(i,r) for i,r in enumerate(records) if r['target'] is not None and (not isinstance(r['target'],float) or np.isfinite(r['target']))]
        fn=ns['train_test_split_homologous'];genes=[r['gene'] for i,r in valid]
        a,bc=fn(genes,homology,.3,2541);b,c=fn([genes[i] for i in bc],homology,.5,2541)
        parts={'train':a,'validation':[bc[i] for i in b],'test':[bc[i] for i in c]}
        maps={};stats={};examples=[];comparisons=[]
        url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{file}'
        for split,indices in parts.items():
            seqmap={}
            for j in indices:
                i,r=valid[j]
                seqmap.setdefault(r['sequence'],dict(split=split,file=file,file_row=i,split_row=None,gene=r['gene'],
                    homology_group=hmap.get(r['gene']),label=r['target'],file_url=url,viewer_url=hf_row(repo,'default','train',i)))
            maps[split]=seqmap
            stats[split]=dict(rows=len(indices),unique_sequences=len(seqmap),mapped_gene_rows=sum(genes[i] in hmap for i in indices))
        for a,b in pairs(list(parts)):
            shared=sorted(maps[a].keys()&maps[b].keys());comparisons.append(dict(left=a,right=b,kind='exact-sequence',shared=len(shared),unit='distinct exact sequence strings'))
            ga={genes[i] for i in parts[a]};gb={genes[i] for i in parts[b]}
            comparisons.append(dict(left=a,right=b,kind='gene-id',shared=len(ga&gb),unit='distinct gene-name strings',mapped_shared_genes=sum(g in hmap for g in ga&gb)))
            groupsa={hmap[g] for g in ga if g in hmap};groupsb={hmap[g] for g in gb if g in hmap}
            comparisons.append(dict(left=a,right=b,kind='homology-group',shared=len(groupsa&groupsb),unit='distinct released HomoloGene mapping-group IDs'))
            for seq in shared[:2]:examples.append(dict(case='mrna-'+repo.split('/')[-1],kind='exact-sequence',sequence_sha256=digest(seq),sequence_length=len(seq),
                sequence=seq if len(seq)<=1000 else None,left=maps[a][seq],right=maps[b][seq]))
        case='mrna-'+repo.split('/')[-1]
        d['cases'][case]=dict(repo=repo,revision=rev,partitions=stats,comparisons=comparisons,
            files=[record_file(path,url),record_file(zpath,'https://zenodo.org/records/13910050/files/homology_maps_homologene.zip'),
                record_file(code,'https://github.com/morrislab/mRNABench/blob/778d691ab91c51c03addeb9219229f2ec81d195c/mrna_bench/data_splitter/homology_split.py')],
            method='Execute exact pinned train_test_split_homologous function twice, seed 2541, after target null/NaN exclusion; human HomoloGene map. Reconstructed library-default split, not asserted historical paper/embedding cohort.',
            eligible_rows=len(valid),mapped_gene_rows=sum(g in hmap for g in genes))
        d['examples']=[e for e in d['examples'] if e['case']!=case]+examples;save(d);print(case,stats,comparisons,flush=True)


def interval_case(d,id,path,url,header=True):
    with path.open() as f:
        reader=csv.DictReader(f,delimiter='\t') if header else (dict(zip(['chromosome','start','end','split'],line.rstrip().split('\t'))) for line in f)
        records=[]
        for i,r in enumerate(reader):
            records.append(dict(chr=r.get('chromosome',r.get('chr')),start=int(float(r['start'])),end=int(float(r['end'])),split=r['split'],
                id=r.get('transcript_id'),line=i+(2 if header else 1),file_row=i,file_url=url,file=str(path.relative_to(ROOT))))
    labels={r['split'] for r in records}
    order=[k for k in ['train','validation','test','valid','val'] if k in labels]+sorted(labels-{'train','validation','test','valid','val'})
    parts={k:[r for r in records if r['split']==k] for k in order}
    comparisons=[];examples=[]
    for a,b in pairs(list(parts)):
        counts=collections.Counter();example=None
        ca={(r['chr'],r['start'],r['end']) for r in parts[a]};cb={(r['chr'],r['start'],r['end']) for r in parts[b]}
        comparisons.append(dict(left=a,right=b,kind='coordinate-id',shared=len(ca&cb),unit='distinct chromosome,start,end tuples'))
        for chrom in sorted({r['chr'] for r in parts[a]}&{r['chr'] for r in parts[b]}):
            left=[r for r in parts[a] if r['chr']==chrom];right=[r for r in parts[b] if r['chr']==chrom]
            la=np.array([r['start'] for r in left]);le=np.array([r['end'] for r in left]);ra=np.array([r['start'] for r in right]);re=np.array([r['end'] for r in right])
            c=np.searchsorted(np.sort(ra),le,side='left')-np.searchsorted(np.sort(re),la,side='right')
            z=np.searchsorted(np.sort(la),re,side='left')-np.searchsorted(np.sort(le),ra,side='right')
            counts['pairs']+=int(c.sum());counts['left']+=int((c>0).sum());counts['right']+=int((z>0).sum())
            if c.any() and example is None:
                x=left[int(np.flatnonzero(c)[0])];y=next(y for y in right if y['start']<x['end'] and y['end']>x['start'])
                example=dict(case=id,kind='interval',left=x,right=y,overlap_bp=min(x['end'],y['end'])-max(x['start'],y['start']))
        comparisons.append(dict(left=a,right=b,kind='interval',shared=counts['pairs'],left_affected=counts['left'],right_affected=counts['right'],unit='positive-length interval pairs'))
        if example:examples.append(example)
    d['cases'][id]=dict(partitions={k:dict(rows=len(v),chromosomes=dict(collections.Counter(r['chr'] for r in v))) for k,v in parts.items()},comparisons=comparisons,
        files=[record_file(path,url)],method='Complete released BED. Compare exact coordinate IDs and positive-length half-open interval overlaps on the same chromosome; no genome-sequence download, flank expansion or homology comparison.')
    d['examples']=[e for e in d['examples'] if e['case']!=id]+examples;save(d)
    print(id,len(records),'comparisons',len(comparisons),'nonzero',[(c['kind'],c['left'],c['right'],c['shared']) for c in comparisons if c['shared']],flush=True)


def intervals(d):
    interval_case(d,'bend-gene-finding',CACHE/'structure-bend-gene_finding.bed','https://sid.erda.dk/share_redirect/aNQa0Oz2lY/data/gene_finding/gene_finding.bed')
    interval_case(d,'bend-enhancer',CACHE/'structure-bend-enhancer_annotation.bed','https://sid.erda.dk/share_redirect/aNQa0Oz2lY/data/enhancer_annotation/enhancer_annotation.bed')
    # The pinned revision is recorded by the existing source registry; do not
    # assign a guessed release to the local BEDs.
    registry=json.loads((ROOT/'data/catalogue.json').read_text())
    for path in sorted((CACHE/'root-residual/ntv3-benchmark').glob('*/splits.bed')):
        source=next(s for s in registry['sources'] if s['id']=='ntv3-benchmark-split-'+path.parent.name+'-source')
        interval_case(d,'ntv3-intervals-'+path.parent.name,path,source['url'],header=False)


def microbial(d):
    import ast
    repo='macwiatrak/bacbench-essential-genes-dna';rev='0210c2445e89c765c0fe5d69618b8a6c262e5d30'
    code=CACHE/'existing-bacbench/bacbench/modeling/embed_dna.py'
    fn=next(n for n in ast.parse(code.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='get_dna_seq')
    ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(code),'exec'),ns)
    maps={};rclasses={};stats={};files=[];comparisons=[];examples=[]
    for split in ['train','validation','test']:
        file='data/'+split+'-00000-of-00001.parquet';path=ROOT/'research/artifacts'/repo.replace('/','--')/file
        url=f'https://huggingface.co/datasets/{repo}/blob/{rev}/{file}'
        seqs={};canonical={};genera=set();genomes=set();n=0
        for row_index,row in enumerate(pq.ParquetFile(path).read().to_pylist()):
            genera.add(row['genus']);genomes.add(row['genome_name'])
            for contig_index,dna in enumerate(row['dna_sequence']):
                starts=row['start'][contig_index];ends=row['end'][contig_index];strands=row['strand'][contig_index];labels=row['essential'][contig_index]
                assert len(starts)==len(ends)==len(strands)==len(labels)
                for j,(start,end,strand,label) in enumerate(zip(starts,ends,strands,labels)):
                    seq=ns['get_dna_seq'](dna,int(start),int(end),strand,promoter_len=0)
                    if not seq:raise ValueError('Empty extracted CDS')
                    n+=1;meta=dict(split=split,file=file,file_row=row_index,contig_index=contig_index,gene_index=j,
                        contig=row['contig_id'][contig_index],start=start,end=end,strand=strand,genus=row['genus'],genome=row['genome_name'],
                        label=label,file_url=url,viewer_url=hf_row(repo,'default',split,row_index))
                    seqs.setdefault(seq,meta);canonical.setdefault(min(seq,seq.translate(COMPLEMENT)[::-1]),meta)
        maps[split]=seqs;rclasses[split]=canonical
        stats[split]=dict(rows=n,unique_sequences=len(seqs),genome_rows=len(genomes),genera=sorted(genera))
        files.append(record_file(path,url)|dict(split=split))
    for a,b in pairs(list(stats)):
        exact=sorted(maps[a].keys()&maps[b].keys());shared=rclasses[a].keys()&rclasses[b].keys()
        comparisons += [dict(left=a,right=b,kind='exact-sequence',shared=len(exact),unit='distinct extracted CDS DNA strings'),
            dict(left=a,right=b,kind='reverse-complement',shared=len(shared),unit='distinct CDS DNA / reverse-complement classes'),
            dict(left=a,right=b,kind='genus',shared=len(set(stats[a]['genera'])&set(stats[b]['genera'])),unit='distinct genus names')]
        for seq in exact[:2]:examples.append(dict(case='bacbench-essential',kind='exact-sequence',sequence_sha256=digest(seq),sequence_length=len(seq),sequence=seq if len(seq)<1000 else None,left=maps[a][seq],right=maps[b][seq]))
    d['cases']['bacbench-essential']=dict(repo=repo,revision=rev,partitions=stats,comparisons=comparisons,files=files,
        method='Complete 55-genome Parquets. Extract all 193,213 CDS intervals with the pinned get_dna_seq implementation and promoter_len=0; compare exact genomic-orientation strings, RC classes and genus names. These CDS-only checks do not reproduce model-specific flanking contexts, chunking or protein-identity thresholds.',
        extraction_code=record_file(code,'https://github.com/macwiatrak/BacBench/blob/64b7d45823b2ff2ef88458e3aa235caa461a12aa/bacbench/modeling/embed_dna.py#L19-L59'))
    d['examples']=[e for e in d['examples'] if e['case']!='bacbench-essential']+examples;save(d);print('bacbench-essential',comparisons,flush=True)
    # This is the released H3 demonstration, not an inferred original-paper run.
    repo='biomap-research/DeepD';rev='2896082aa1b7483d3c4062e125050ebc815aea25'
    specs=[]
    for split,stem in [('train','train'),('validation','valid'),('test','test')]:
        file=f'fine_tune/H3/H3_{stem}.csv';path=ROOT/'research/artifacts/biomap-research--DeepD'/file
        if path.exists():specs.append(dict(path=str(path.relative_to(ROOT)),split=split,column='nt_seq',url=f'https://github.com/{repo}/blob/{rev}/{file}'))
    sequence_case(d,'deepd-h3-demonstration',specs,extra=dict(repo=repo,revision=rev,scope='Released example, not proof of the paper-specific H3/H4 scored partitions.'))
    # BGC family- and BGC-group split manifests are compact independent artifacts.
    repo='Nugkta/bgc-bench';rev='f64c7f6eb6d3910cc7b4434cdc114dc7501305b1'
    for filename,column in [('t5_bgc_grouped_5fold.csv','fold'),('t5_gcf_holdout_c07.csv','split')]:
        path=ROOT/'research/artifacts/Nugkta--bgc-bench/splits'/filename
        rows=list(csv.DictReader(path.open()));labels=sorted({r[column] for r in rows});parts={s:[r for r in rows if r[column]==s] for s in labels}
        comps=[]
        for a,b in pairs(labels):
            for key,kind in [('domain_id','domain-id'),('bgc_id','bgc-id'),('gcf_id','cluster-id')]:
                comps.append(dict(left=a,right=b,kind=kind,shared=len({r[key] for r in parts[a]}&{r[key] for r in parts[b]}),unit='distinct '+key+' values'))
        id='bgc-'+filename.removesuffix('.csv')
        d['cases'][id]=dict(repo=repo,revision=rev,partitions={s:dict(rows=len(rs),unique_bgc_ids=len({r['bgc_id'] for r in rs})) for s,rs in parts.items()},
            comparisons=comps,files=[record_file(path,f'https://huggingface.co/datasets/{repo}/blob/{rev}/splits/{filename}')],
            method='Complete split manifest only. Compare domain, BGC and published gene-cluster-family IDs across partitions. No DNA/protein similarity search or independent BiG-SCAPE rerun.')
        save(d);print(id,[(x['left'],x['right'],x['kind'],x['shared']) for x in comps if x['shared']],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('case',choices=['plantcad','selected','rna','intervals','microbial']);args=parser.parse_args();d=load()
    {'plantcad':plantcad,'selected':selected,'rna':rna_and_mrna,'intervals':intervals,'microbial':microbial}[args.case](d)
