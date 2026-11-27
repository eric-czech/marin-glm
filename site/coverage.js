"use strict";
window.coveragePopulationIds=function(id,populations,groups){
  const out=[],seen=new Set();
  for(let p=populations[id];p&&!seen.has(p.id);p=populations[p.parent_id]){out.push(p.id);seen.add(p.id);}
  for(const [group,members] of Object.entries(groups||{}))if(members.some(id=>seen.has(id))&&!seen.has(group))out.push(group);
  return out;
};
// Coverage is a presentation of canonical task IDs, not a second catalogue.
window.createCoverageMatrix=function(element,db,taskLookup,populations,onSelect){
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link=(url,label)=>`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
  const tree=db.presentation,nodes=Object.fromEntries(tree.nodes.map(n=>[n.id,n]));
  const shapes={circle:'<circle cx="6" cy="6" r="4.5"/>',square:'<rect x="1.5" y="1.5" width="9" height="9"/>',triangle:'<path d="M6 1 11 11H1Z"/>',diamond:'<path d="m6 0 6 6-6 6-6-6Z"/>',hexagon:'<path d="M3 1h6l3 5-3 5H3L0 6Z"/>',cross:'<path d="M4 0h4v4h4v4H8v4H4V8H0V4h4Z"/>'};
  const shape=(name,cls='')=>`<svg viewBox="0 0 12 12" aria-hidden="true" class="${cls}">${shapes[name]}</svg>`;
  let state={},matching=[],rowTasks={},cells={},rows=[],features=[],currentCell=null;
  const parentIncludes=(id,ancestor)=>coveragePopulationIds(id,populations,db.populationGroups).includes(ancestor);
  element.innerHTML=`<div class="coverage-pane"><div class="coverage-tools"><div class="coverage-nav" aria-label="Jump to a biological division"></div><div class="coverage-controls"><label>Taxon detail<select class="coverage-detail"><option value="species">Selected organisms</option><option value="allSpecies">Every named species</option><option value="clade">Clades only</option></select></label><button type="button" class="secondary coverage-expand" aria-pressed="false">Expand matrix</button></div></div><div class="coverage-legends"></div><p class="coverage-key">Hollow: protein-only reference. Faint: unresolved panel. Row totals count unique task records; totals are not additive.</p><div class="coverage-scroll" role="region" aria-label="Scrollable organism by genomic feature matrix"><table class="coverage-matrix" aria-label="Task associations by biological division and genomic feature"></table></div><div class="coverage-selection" role="status" aria-live="polite"></div></div><div class="coverage-notes"></div><div class="coverage-tooltip" role="tooltip" hidden></div>`;
  const $=selector=>element.querySelector(selector),wrap=$('.coverage-scroll'),table=$('.coverage-matrix');
  function resizeColumns(){
    if(!features.length)return;
    const first=matchMedia('(max-width:850px)').matches?270:320;
    const width=Math.max(first+features.length*49,wrap.clientWidth);
    table.style.width=width+'px';table.style.minWidth=(first+features.length*49)+'px';
    table.querySelectorAll('col').forEach((col,i)=>col.style.width=(i?(width-first)/features.length:first)+'px');
  }
  if(window.ResizeObserver)new ResizeObserver(resizeColumns).observe(wrap);
  else window.addEventListener('resize',resizeColumns);
  $('.coverage-legends').innerHTML=`<div><strong>Color</strong> ${db.modes.map((m,i)=>`<span class="coverage-legend mode-${i}"><span class="coverage-swatch"></span>${esc(m)}</span>`).join('')}</div><div><strong>Shape</strong> ${db.sources.map(s=>`<span class="coverage-legend">${shape(s.shape,'neutral')}${esc(s.label)}</span>`).join('')}</div>`;
  $('.coverage-nav').innerHTML=[['bacteria','Bacteria'],['archaea','Archaea'],['eukaryota','Eukaryota'],['animals','Animals'],['fungi','Fungi'],['plants','Green plants'],['viruses','Viruses'],['context','Unplaced']].map(([id,label])=>`<button type="button" data-jump="${id}">${esc(label)}</button>`).join('');
  function expand(on){$('.coverage-pane').classList.toggle('expanded',on);document.body.classList.toggle('matrix-expanded',on);$('.coverage-expand').setAttribute('aria-pressed',String(on));$('.coverage-expand').textContent=on?'Restore view':'Expand matrix';$('.coverage-tooltip').hidden=true;}
  $('.coverage-expand').addEventListener('click',()=>expand(!$('.coverage-pane').classList.contains('expanded')));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')expand(false);});
  $('.coverage-detail').addEventListener('change',()=>onSelect({taxonDetail:$('.coverage-detail').value,cellRow:'',cellFeature:'',page:''}));
  $('.coverage-nav').addEventListener('click',e=>{const b=e.target.closest('[data-jump]');if(!b)return;const target=table.querySelector(`[data-group="${b.dataset.jump}"]`);if(target)wrap.scrollTop+=target.getBoundingClientRect().top-wrap.getBoundingClientRect().top-table.tHead.getBoundingClientRect().height;});
  function choose(row,feature,task){onSelect({cellRow:row,cellFeature:feature||'*',open:task||'',page:''});}
  table.addEventListener('click',e=>{
    const dot=e.target.closest('[data-coverage-task]');if(dot){choose(dot.dataset.row,dot.dataset.feature,dot.dataset.coverageTask);return;}
    const row=e.target.closest('[data-select-row]');if(row){choose(row.dataset.selectRow,null);return;}
    const cell=e.target.closest('[data-cell-row]');if(cell)choose(cell.dataset.cellRow,cell.dataset.cellFeature);
  });
  $('.coverage-selection').addEventListener('click',e=>{if(e.target.closest('[data-clear-cell]'))onSelect({cellRow:'',cellFeature:'',open:'',page:''});if(e.target.closest('[data-inspect-cell]')){expand(false);document.getElementById('results').scrollIntoView({block:'start'});}});
  const tooltip=$('.coverage-tooltip');
  table.addEventListener('pointermove',e=>{const dot=e.target.closest('[data-coverage-task]');if(!dot){tooltip.hidden=true;return;}const t=taskLookup[dot.dataset.coverageTask],meta=db.tasks.find(t=>t.id===dot.dataset.coverageTask);tooltip.innerHTML=`<strong>${esc(t.name)}</strong><br>${esc(db.modes[meta.mode])} · ${esc(db.sources[meta.source].label)}<br>${esc(rows.find(r=>r.id===dot.dataset.row)?.label)} × ${esc(db.features.find(f=>f.id===dot.dataset.feature)?.label)}`;tooltip.hidden=false;const r=tooltip.getBoundingClientRect();tooltip.style.left=Math.max(8,Math.min(e.clientX+14,innerWidth-r.width-8))+'px';tooltip.style.top=Math.max(8,Math.min(e.clientY+16,innerHeight-r.height-8))+'px';});
  table.addEventListener('pointerleave',()=>tooltip.hidden=true);wrap.addEventListener('scroll',()=>tooltip.hidden=true);

  function render(next,matched,unfiltered){
    const oldScroll={top:wrap.scrollTop,left:wrap.scrollLeft};state=next;matching=matched;
    const view=state.taxonDetail||'species',field={clade:'clade',species:'row',allSpecies:'allSpeciesRow'}[view];
    const sourceView=tree.views[view]||tree.views.species;
    $('.coverage-detail').value=view;
    const ids=new Set(matching.map(t=>t.id));rowTasks={};cells={};
    for(const [i,meta] of db.tasks.entries()){
      if(!ids.has(meta.id))continue;
      const maps=meta.mappings.filter(m=>!state.population||state.population==='synthetic'||(m.population&&parentIncludes(m.population,state.population)));
      const assigned=new Set(maps.map(m=>m[field]));
      if(assigned.has('synthetic')&&[...assigned].some(r=>!['synthetic','unknown'].includes(r)))assigned.delete('synthetic');
      for(const rid of assigned){
        (rowTasks[rid]??=[]).push(i);
        for(const f of meta.features)if(!state.region||state.region===f)(cells[rid+'|'+f]??=[]).push(i);
      }
    }
    rows=sourceView.rows.filter(r=>rowTasks[r.id]?.length);
    features=state.region?db.features.filter(f=>f.id===state.region):db.features;
    const active=new Set(rows.flatMap(r=>r.displayPath));
    const known=unfiltered?tree.known:[];
    for(const k of known){let n=nodes[k.parent];while(n){active.add(n.id);n=nodes[n.parent];}}
    const divisions=['vertebrates','mammalia','aves','insecta','nematoda','cnidaria','land','angiosperms','monocots','eudicots','poaceae','arecales','ascomycota','basidiomycota','pseudomonadota','bacillota','cyanobacteriota','chlorobiota','duplodnaviria','riboviria','floreoviria','alveolata','stramenopiles'];
    const retained=new Set([...divisions,...rows.filter(r=>r.placementStatus).map(r=>r.displayParent),...tree.nodes.filter(n=>n.jump||n.rank==='Domain').map(n=>n.id)]);
    for(const n of tree.nodes)if(rows.filter(r=>r.displayParent===n.id&&!r.placementStatus).length>1)retained.add(n.id);
    function detailsFor(node){
      const lineage=[];let n=node;while(n){if(!tree.sections.some(s=>s.root===n.id))lineage.unshift(n);n=nodes[n.parent];}
      const omitted=parent=>tree.nodes.filter(n=>n.parent===parent&&active.has(n.id)&&!retained.has(n.id)).flatMap(n=>[n,...omitted(n.id)]);
      const items=[...lineage,...omitted(node.id)];
      return `<details class="coverage-taxonomy"><summary>Taxonomy details</summary><ul>${items.map(n=>`<li><strong>${esc(n.label)}</strong>${n.scientific?' ('+esc(n.scientific)+')':''}${n.parent?' · within '+esc(nodes[n.parent].label):''}${n.note?': '+esc(n.note):''} ${n.sources.map(u=>link(u,'source')).join(' · ')}</li>`).join('')}${tree.context.filter(x=>items.some(n=>n.id===x.parent)).map(x=>`<li><strong>${esc(nodes[x.parent].label+' — '+x.label)}:</strong> ${esc(x.why)} ${link(x.source,'source')}</li>`).join('')}</ul></details>`;
    }
    function marks(indices,row,f){return indices.map(i=>{const m=db.tasks[i],t=taskLookup[m.id];return `<button type="button" class="coverage-dot mode-${m.mode}${m.protein?' protein':''}${t.status==='panel-pending'?' panel':''}${state.open===t.id?' selected':''}" data-coverage-task="${esc(t.id)}" data-row="${row}" data-feature="${f}" aria-label="${esc(t.name+'; '+db.modes[m.mode]+'; '+db.sources[m.source].label+'; '+rows.find(r=>r.id===row).label+'; '+db.features.find(x=>x.id===f).label)}">${shape(db.sources[m.source].shape)}</button>`;}).join('');}
    function dataRow(r,depth,node,displayParent){
      const max=Math.max(0,...features.map(f=>(cells[r.id+'|'+f.id]||[]).length)),height=Math.max(44,Math.ceil(max/5)*9+14);
      const label=r.placementStatus?r.displayLabel:node&&(!r.kind||r.kind==='clade')?'All mapped tasks':r.kind==='clade'?nodes[r.displayParent].label:r.label;
      const sub=[r.common,r.lineageHint,nodes[r.displayParent].label].filter((s,i,a)=>s&&s!==label&&a.indexOf(s)===i).join(' · ');
      return `<tr data-taxon="${r.id}" data-parent-node="${r.displayParent}" data-display-parent="${displayParent||''}" style="--depth:${depth}"><th class="coverage-taxon ${r.kind==='species'?'species':''}" scope="row"><button type="button" data-select-row="${r.id}" aria-label="${esc(r.displayLineage+'; '+label+'; '+rowTasks[r.id].length+' tasks')}"><span>${esc(label)}${sub?`<small>${esc(sub)}</small>`:''}</span><small>${rowTasks[r.id].length}</small></button></th>${features.map(f=>{const ii=cells[r.id+'|'+f.id]||[],shade=ii.length?Math.min(.17,.025+Math.log2(ii.length+1)*.022):0;return `<td class="coverage-cell" data-cell-row="${r.id}" data-cell-feature="${f.id}" style="height:${height}px;background:rgba(45,72,58,${shade.toFixed(3)})" aria-label="${esc(label+' × '+f.label+': '+ii.length+' task records')}"><div class="coverage-marks">${marks(ii,r.id,f.id)}</div></td>`;}).join('')}</tr>`;
    }
    function branch(parent,depth,section,displayParent=parent){
      let out='';
      for(const node of tree.nodes.filter(n=>n.parent===parent&&n.section===section&&active.has(n.id))){
        const direct=rows.filter(r=>r.displayParent===node.id&&!r.placementStatus);
        if(!retained.has(node.id)){for(const r of direct)out+=dataRow(r,depth,null,displayParent);out+=branch(node.id,depth,section,displayParent);continue;}
        const n=new Set(rows.filter(r=>r.displayPath.includes(node.id)).flatMap(r=>rowTasks[r.id]||[])).size;
        out+=`<tr class="coverage-division" data-node="${node.id}" data-display-parent="${displayParent||''}" ${node.jump?`data-group="${node.jump}"`:''} style="--depth:${depth}"><th scope="row">↳ ${esc(node.label)}${node.scientific||node.rank?` <small>${esc([node.scientific,node.rank].filter(Boolean).join(' · '))}</small>`:''}</th><td colspan="${features.length}"><span class="coverage-node-count">${n?n+' unique mapped tasks':'Paper evidence below'}</span>${esc(node.note)} ${node.sources.map(u=>link(u,'source')).join(' · ')} ${detailsFor(node)}</td></tr>`;
        for(const r of direct)out+=dataRow(r,depth+1,node,node.id);
        out+=branch(node.id,depth+1,section,node.id);
      }
      for(const r of rows.filter(r=>r.displayParent===parent&&r.placementStatus))out+=dataRow(r,depth,null,displayParent);
      const k=known.filter(x=>x.parent===parent);
      if(k.length)out+=`<tr class="coverage-paper"><th scope="row">Reported; task not yet mapped</th><td colspan="${features.length}">${k.map(x=>`<strong>${esc(x.label)}.</strong> ${esc(x.why)} ${link(x.source,'Evaluation evidence')}`).join('<br>')}</td></tr>`;
      return out;
    }
    const featureGroups=db.featureGroups.map(g=>({...g,ids:g.ids.filter(id=>features.some(f=>f.id===id))})).filter(g=>g.ids.length);
    let html='<colgroup><col style="width:320px">'+features.map(()=>'<col style="width:49px">').join('')+'</colgroup><thead><tr><th class="coverage-corner" rowspan="2" scope="col">Biological division / species<br><small>Unique task records</small></th>'+featureGroups.map(g=>`<th class="coverage-feature-group" colspan="${g.ids.length}">${esc(g.label)}</th>`).join('')+'</tr><tr>'+features.map(f=>`<th class="coverage-feature" scope="col"><span>${esc(f.label)}</span></th>`).join('')+'</tr></thead><tbody>';
    for(const section of tree.sections){if(!rows.some(r=>nodes[r.displayParent].section===section.id)&&!known.some(k=>nodes[k.parent].section===section.id))continue;html+=`<tr class="coverage-section" ${section.root?`data-group="${nodes[section.root].jump}"`:''}><th scope="rowgroup" colspan="${features.length+1}">${esc(section.label)}</th></tr>`+branch(section.root,0,section.id);}
    table.innerHTML=html+'</tbody>';resizeColumns();
    wrap.hidden=!rows.length&&!known.length;
    for(const b of element.querySelectorAll('[data-jump]'))b.hidden=!table.querySelector(`[data-group="${b.dataset.jump}"]`);
    wrap.scrollTop=oldScroll.top;wrap.scrollLeft=oldScroll.left;
    const selected=rows.find(r=>r.id===state.cellRow);
    let indices=null;currentCell=null;
    if(selected){const f=features.find(f=>f.id===state.cellFeature);indices=state.cellFeature==='*'?rowTasks[selected.id]:f?(cells[selected.id+'|'+f.id]||[]):[];currentCell={row:selected.id,feature:state.cellFeature};$('.coverage-selection').innerHTML=`<span><strong>${esc(selected.displayLabel)}${f?' × '+esc(f.label):' — all features'}</strong> · ${indices.length} matching tasks. Task-level associations; a released species × feature subset is not implied.</span><span><button type="button" class="secondary" data-inspect-cell>Inspect tasks</button> <button type="button" class="secondary" data-clear-cell>Clear cell</button></span>`;}
    else{$('.coverage-selection').innerHTML='<span>Select a marker or cell to inspect matching tasks below. An empty cell means no mapped catalogue evidence.</span>'+(state.cellRow?'<button type="button" class="secondary" data-clear-cell>Clear cell</button>':'');if(state.cellRow)indices=[];}
    $('.coverage-notes').innerHTML=unfiltered?`<details><summary>Priority coverage questions (${tree.gaps.length})</summary><p>Selected research, production and ecological priorities; no mapped task does not establish absence from every released panel.</p><ul>${tree.gaps.map(g=>`<li><strong>${esc(g.label)} (${esc(g.species)}).</strong> ${esc(g.why)} <strong>${esc(g.status)}.</strong> ${esc(g.coverage||'')} ${link(g.source,'Importance source')}<details><summary>Coverage evidence and limits</summary><p>${esc(g.scope)} ${esc(g.caveat||'')} ${g.coverageSources.map(s=>link('#view=evaluations&task='+s.task,s.name)).join(' · ')} ${(g.contextSources||[]).map(u=>link(u,'Context evidence')).join(' · ')}</p></details></li>`).join('')}</ul></details>`:'';
    const filtered=indices===null?matching:indices.map(i=>taskLookup[db.tasks[i].id]);
    return {tasks:filtered,rows:rows.length,associations:Object.values(cells).reduce((n,a)=>n+a.length,0),cell:currentCell};
  }
  return {render,close:()=>expand(false),getCell:()=>currentCell};
};
