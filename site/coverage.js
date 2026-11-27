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
  const taxonLink=(url,label)=>url?`<a class="coverage-taxon-link" href="${esc(url)}" target="_blank" rel="noopener" title="${esc(label+' — taxonomy source')}">${esc(label)}</a>`:esc(label);
  const tree=db.presentation,nodes=Object.fromEntries(tree.nodes.map(n=>[n.id,n]));
  const shapes={circle:'<circle cx="6" cy="6" r="4.5"/>',square:'<rect x="1.5" y="1.5" width="9" height="9"/>',triangle:'<path d="M6 1 11 11H1Z"/>',diamond:'<path d="m6 0 6 6-6 6-6-6Z"/>',hexagon:'<path d="M3 1h6l3 5-3 5H3L0 6Z"/>',cross:'<path d="M4 0h4v4h4v4H8v4H4V8H0V4h4Z"/>'};
  const shape=(name,cls='')=>`<svg viewBox="0 0 12 12" aria-hidden="true" class="${cls}">${shapes[name]}</svg>`;
  let state={},matching=[],rowTasks={},cells={},rows=[],features=[],currentCell=null;
  const parentIncludes=(id,ancestor)=>coveragePopulationIds(id,populations,db.populationGroups).includes(ancestor);
  element.innerHTML=`<div class="coverage-pane"><div class="coverage-tools"><div class="coverage-nav" aria-label="Jump to a biological division"></div><div class="coverage-controls"><label>Features<select class="coverage-feature-detail"><option value="grouped">Grouped</option><option value="individual">Individual</option></select></label><label>Taxon detail<select class="coverage-detail"><option value="species">Selected organisms</option><option value="allSpecies">Every named species</option><option value="clade">Clades only</option></select></label><button type="button" class="secondary coverage-expand" aria-pressed="false">Expand matrix</button></div></div><div class="coverage-legends"></div><p class="coverage-key">Structure columns require a jointly scored gene or transcript; element columns include partial targets. Use Scored output to separate isolated values, dense labels, signal profiles and complete structures. Hollow: protein-only reference. Faint: source-limited definition. Totals are not additive.</p><div class="coverage-scroll" role="region" aria-label="Scrollable organism by genomic feature matrix"><table class="coverage-matrix" aria-label="Task associations by biological division and genomic feature"></table></div><div class="coverage-selection" role="status" aria-live="polite"></div></div><div class="coverage-notes"></div><div class="coverage-tooltip" role="tooltip" hidden></div>`;
  const $=selector=>element.querySelector(selector),wrap=$('.coverage-scroll'),table=$('.coverage-matrix');
  function resizeColumns(){
    if(!features.length)return;
    const first=matchMedia('(max-width:850px)').matches?250:300;
    const featureWidth=state.featureDetail==='individual'?58:76;
    const width=Math.max(first+features.length*featureWidth,wrap.clientWidth);
    table.style.width=width+'px';table.style.minWidth=(first+features.length*featureWidth)+'px';
    table.querySelectorAll('col').forEach((col,i)=>col.style.width=(i?(width-first)/features.length:first)+'px');
  }
  if(window.ResizeObserver)new ResizeObserver(resizeColumns).observe(wrap);
  else window.addEventListener('resize',resizeColumns);
  $('.coverage-legends').innerHTML=`<div><strong>Color</strong> ${db.modes.map((m,i)=>`<span class="coverage-legend mode-${i}"><span class="coverage-swatch"></span>${esc(m)}</span>`).join('')}</div><div><strong>Shape</strong> ${db.sources.map(s=>`<span class="coverage-legend">${shape(s.shape,'neutral')}${esc(s.label)}</span>`).join('')}</div>`;
  $('.coverage-nav').innerHTML=[['eukaryota','Eukaryota'],['animals','Animals'],['plants','Green plants'],['fungi','Fungi'],['bacteria','Bacteria'],['archaea','Archaea'],['viruses','Viruses'],['context','Unplaced']].map(([id,label])=>`<button type="button" data-jump="${id}">${esc(label)}</button>`).join('');
  function expand(on){$('.coverage-pane').classList.toggle('expanded',on);document.body.classList.toggle('matrix-expanded',on);$('.coverage-expand').setAttribute('aria-pressed',String(on));$('.coverage-expand').textContent=on?'Restore view':'Expand matrix';$('.coverage-tooltip').hidden=true;}
  $('.coverage-expand').addEventListener('click',()=>expand(!$('.coverage-pane').classList.contains('expanded')));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')expand(false);});
  $('.coverage-detail').addEventListener('change',()=>onSelect({taxonDetail:$('.coverage-detail').value,cellRow:'',cellFeature:'',page:''}));
  $('.coverage-feature-detail').addEventListener('change',()=>onSelect({featureDetail:$('.coverage-feature-detail').value,cellRow:'',cellFeature:'',open:'',page:''}));
  $('.coverage-nav').addEventListener('click',e=>{const b=e.target.closest('[data-jump]');if(!b)return;const target=table.querySelector(`[data-group="${b.dataset.jump}"]`);if(target)wrap.scrollTop+=target.getBoundingClientRect().top-wrap.getBoundingClientRect().top-table.tHead.getBoundingClientRect().height;});
  function choose(row,feature,task){onSelect({cellRow:row,cellFeature:feature||'*',open:task||'',page:''});}
  table.addEventListener('click',e=>{
    const dot=e.target.closest('[data-coverage-task]');if(dot){choose(dot.dataset.row,dot.dataset.feature,dot.dataset.coverageTask);return;}
    const row=e.target.closest('[data-select-row]');if(row){choose(row.dataset.selectRow,null);return;}
    const cell=e.target.closest('[data-cell-row]');if(cell)choose(cell.dataset.cellRow,cell.dataset.cellFeature);
  });
  $('.coverage-selection').addEventListener('click',e=>{if(e.target.closest('[data-clear-cell]'))onSelect({cellRow:'',cellFeature:'',open:'',page:''});if(e.target.closest('[data-inspect-cell]')){expand(false);document.getElementById('results').scrollIntoView({block:'start'});}});
  const tooltip=$('.coverage-tooltip');
  function showTooltip(dot,x,y){
    const t=taskLookup[dot.dataset.coverageTask],meta=db.tasks.find(t=>t.id===dot.dataset.coverageTask);
    const concise=values=>esc(values.slice(0,2).join('; ')+(values.length>2?' +'+(values.length-2):''));
    tooltip.innerHTML=`<strong>${esc(t.name)}</strong><br>${esc(db.modes[meta.mode])} · ${esc(t._outputLabel)}<dl><dt>Evaluation</dt><dd>${concise(t._collectionNames)}</dd><dt>Paper</dt><dd>${concise(t._paperNames)||'Source in task details'}</dd><dt>Models</dt><dd>${concise(t._modelNames)|| (t._collectionModelNames.length?concise(t._collectionModelNames)+' (collection participants; assay runs not specified)':'Dataset source; no task-specific model run cited')}</dd></dl><span>${esc(rows.find(r=>r.id===dot.dataset.row)?.label)} × ${esc(features.find(f=>f.id===dot.dataset.feature)?.label)}</span>`;
    tooltip.hidden=false;const r=tooltip.getBoundingClientRect();
    tooltip.style.left=Math.max(8,Math.min(x+14,innerWidth-r.width-8))+'px';tooltip.style.top=Math.max(8,Math.min(y+16,innerHeight-r.height-8))+'px';
    dot.setAttribute('aria-describedby','coverage-task-tooltip');
  }
  tooltip.id='coverage-task-tooltip';
  table.addEventListener('pointermove',e=>{const dot=e.target.closest('[data-coverage-task]');if(!dot){tooltip.hidden=true;return;}showTooltip(dot,e.clientX,e.clientY);});
  table.addEventListener('focusin',e=>{const dot=e.target.closest('[data-coverage-task]');if(dot)requestAnimationFrame(()=>requestAnimationFrame(()=>{if(document.activeElement===dot){const r=dot.getBoundingClientRect();showTooltip(dot,r.right,r.bottom);}}));});
  table.addEventListener('focusout',()=>tooltip.hidden=true);
  table.addEventListener('pointerleave',()=>tooltip.hidden=true);wrap.addEventListener('scroll',()=>tooltip.hidden=true);

  function render(next,matched,unfiltered){
    const oldScroll={top:wrap.scrollTop,left:wrap.scrollLeft};state=next;matching=matched;
    const view=state.taxonDetail||'species',field={clade:'clade',species:'row',allSpecies:'allSpeciesRow'}[view];
    const sourceView=tree.views[view]||tree.views.species;
    $('.coverage-detail').value=view;
    const grouped=state.featureDetail!=='individual',featureSpecs=grouped?db.groupedFeatures:db.features;
    $('.coverage-feature-detail').value=grouped?'grouped':'individual';
    const ids=new Set(matching.map(t=>t.id));rowTasks={};cells={};
    for(const [i,meta] of db.tasks.entries()){
      if(!ids.has(meta.id))continue;
      const maps=meta.mappings.filter(m=>(!state.population||state.population==='synthetic'||(m.population&&parentIncludes(m.population,state.population)))&&(!state.region||m.features.includes(state.region)));
      const assigned=new Set(maps.map(m=>m[field]));
      if(assigned.has('synthetic')&&[...assigned].some(r=>!['synthetic','unknown'].includes(r)))assigned.delete('synthetic');
      for(const rid of assigned){
        (rowTasks[rid]??=[]).push(i);
        const mappedFeatures=new Set(maps.filter(m=>m[field]===rid).flatMap(m=>grouped?m.groupedFeatures:m.features));
        for(const f of mappedFeatures)if(grouped||!state.region||state.region===f)(cells[rid+'|'+f]??=[]).push(i);
      }
    }
    rows=sourceView.rows.filter(r=>rowTasks[r.id]?.length);
    features=state.region?featureSpecs.filter(f=>grouped?Object.keys(cells).some(k=>k.endsWith('|'+f.id)):f.id===state.region):featureSpecs;
    const active=new Set(rows.flatMap(r=>r.displayPath));
    const divisions=['vertebrates','mammalia','aves','insecta','nematoda','cnidaria','land','angiosperms','monocots','eudicots','poaceae','arecales','ascomycota','basidiomycota','pseudomonadota','bacillota','cyanobacteriota','chlorobiota','duplodnaviria','riboviria','floreoviria','alveolata','stramenopiles','lycophytes','amoebozoa','apicomplexa','schizosaccharomycetes','rhodophyta','thermodesulfobacteriota'];
    const retained=new Set([...divisions,...rows.filter(r=>r.placementStatus).map(r=>r.displayParent),...tree.nodes.filter(n=>n.jump||n.rank==='Domain').map(n=>n.id)]);
    for(const n of tree.nodes)if(rows.filter(r=>r.displayParent===n.id&&!r.placementStatus).length>1)retained.add(n.id);
    function detailsFor(node){
      const lineage=[];let n=node;while(n){if(!tree.sections.some(s=>s.root===n.id))lineage.unshift(n);n=nodes[n.parent];}
      const omitted=parent=>tree.nodes.filter(n=>n.parent===parent&&active.has(n.id)&&!retained.has(n.id)).flatMap(n=>[n,...omitted(n.id)]);
      const items=[...lineage,...omitted(node.id)];
      return `<details class="coverage-taxonomy"><summary>Taxonomy details</summary><ul>${items.map(n=>`<li><strong>${taxonLink(n.sources[0],n.label)}</strong>${n.scientific?' ('+esc(n.scientific)+')':''}${n.parent?' · within '+esc(nodes[n.parent].label):''}${n.note?': '+esc(n.note):''}${n.sources.slice(1).map((u,i)=>' '+link(u,'Reference '+(i+2))).join('')}</li>`).join('')}${tree.context.filter(x=>items.some(n=>n.id===x.parent)).map(x=>`<li><strong>${taxonLink(x.source,nodes[x.parent].label+' — '+x.label)}:</strong> ${esc(x.why)}</li>`).join('')}</ul></details>`;
    }
    function marks(indices,row,f){return indices.map(i=>{const m=db.tasks[i],t=taskLookup[m.id];return `<button type="button" class="coverage-dot mode-${m.mode}${m.protein?' protein':''}${t.status==='source-limited'?' panel':''}${state.open===t.id?' selected':''}" data-coverage-task="${esc(t.id)}" data-row="${row}" data-feature="${f}" data-output="${esc(m.output)}" aria-label="${esc(t.name+'; '+db.modes[m.mode]+'; '+t._outputLabel+'; '+db.sources[m.source].label+'; '+rows.find(r=>r.id===row).label+'; '+features.find(x=>x.id===f).label)}">${shape(db.sources[m.source].shape)}</button>`;}).join('');}
    function dataRow(r,depth,node,displayParent){
      const label=r.placementStatus?r.displayLabel:node&&(!r.kind||r.kind==='clade')?(view==='clade'?'All mapped tasks':'Species not specified'):r.kind==='clade'?nodes[r.displayParent].label:r.label;
      const context=[r.common,r.lineageHint,nodes[r.displayParent].label].filter((s,i,a)=>s&&s.toLowerCase()!==label.toLowerCase()&&a.findIndex(v=>v?.toLowerCase()===s.toLowerCase())===i).join(' · ');
      const sub=[...(r.kind==='species'?[r.common,r.lineageHint]:[]),...(r.displayParent!==displayParent?[nodes[r.displayParent].label]:[])].filter((s,i,a)=>s&&s!==label&&a.indexOf(s)===i).join(' · ');
      const population=r.kind==='species'&&r.populations.length===1?populations[r.populations[0]]:null;
      const source=population?.ncbi_taxid?'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id='+population.ncbi_taxid:label===nodes[r.displayParent].label?nodes[r.displayParent].sources[0]:null;
      const name=source?taxonLink(source,label):`<button type="button" class="coverage-row-select" data-select-row="${r.id}">${esc(label)}</button>`;
      return `<tr data-taxon="${r.id}" data-parent-node="${r.displayParent}" data-display-parent="${displayParent||''}" style="--depth:${depth}"><th class="coverage-taxon ${r.kind==='species'?'species':''}" scope="row"><div class="coverage-row-label" title="${esc(context)}"><span><span class="coverage-row-name">${name}</span>${sub?` <small>· ${esc(sub)}</small>`:''}</span><button type="button" class="coverage-row-count" data-select-row="${r.id}" title="Show matching tasks" aria-label="${esc('Show '+rowTasks[r.id].length+' matching tasks: '+r.displayLineage+'; '+label)}">${rowTasks[r.id].length}</button></div></th>${features.map(f=>{const ii=cells[r.id+'|'+f.id]||[],shade=ii.length?Math.min(.17,.025+Math.log2(ii.length+1)*.022):0;return `<td class="coverage-cell" data-cell-row="${r.id}" data-cell-feature="${f.id}" style="background:rgba(45,72,58,${shade.toFixed(3)})" aria-label="${esc(label+' × '+f.label+': '+ii.length+' task records')}"><div class="coverage-marks">${marks(ii,r.id,f.id)}</div></td>`;}).join('')}</tr>`;
    }
    function visibleBranches(parent,section){
      return tree.nodes.filter(n=>n.parent===parent&&n.section===section&&active.has(n.id)).flatMap(node=>retained.has(node.id)?[{node}]:[
        ...rows.filter(r=>r.displayParent===node.id&&!r.placementStatus).map(row=>({row})),
        ...visibleBranches(node.id,section),
        ...rows.filter(r=>r.displayParent===node.id&&r.placementStatus).map(row=>({row}))]);
    }
    function branch(parent,depth,section,displayParent=parent){
      let out='';
      const order=parent===null?['eukaryota','bacteria','archaea']:parent==='eukaryota'?['animals','plants','fungi']:[];
      const priority=entry=>{const i=order.indexOf(entry.node?.id);return i<0?order.length:i;};
      for(const entry of visibleBranches(parent,section).sort((a,b)=>priority(a)-priority(b))){
        if(entry.row){out+=dataRow(entry.row,depth,null,displayParent);continue;}
        const node=entry.node;
        const direct=rows.filter(r=>r.displayParent===node.id&&!r.placementStatus);
        const n=new Set(rows.filter(r=>r.displayPath.includes(node.id)).flatMap(r=>rowTasks[r.id]||[])).size;
        out+=`<tr class="coverage-division" data-node="${node.id}" data-display-parent="${displayParent||''}" ${node.jump?`data-group="${node.jump}"`:''} style="--depth:${depth}"><th scope="row">↳ ${taxonLink(node.sources[0],node.label)}${node.scientific||node.rank?` <small>${esc([node.scientific?.toLowerCase()!==node.label.toLowerCase()?node.scientific:'',node.rank].filter(Boolean).join(' · '))}</small>`:''}</th><td colspan="${features.length}"><span class="coverage-node-count">${n} tasks</span>${esc(node.note)} ${detailsFor(node)}</td></tr>`;
        for(const r of direct)out+=dataRow(r,depth+1,node,node.id);
        out+=branch(node.id,depth+1,section,node.id);
      }
      for(const r of rows.filter(r=>r.displayParent===parent&&r.placementStatus))out+=dataRow(r,depth,null,displayParent);
      return out;
    }
    const groups=grouped?[...new Set(featureSpecs.map(f=>f.group))].map(label=>({label,ids:featureSpecs.filter(f=>f.group===label).map(f=>f.id)})):db.featureGroups;
    const featureGroups=groups.map(g=>({...g,ids:g.ids.filter(id=>features.some(f=>f.id===id))})).filter(g=>g.ids.length);
    let html='<colgroup><col style="width:300px">'+features.map(()=>'<col style="width:76px">').join('')+'</colgroup><thead><tr><th class="coverage-corner" rowspan="2" scope="col">Biological division / species<br><small>Unique task records</small></th>'+featureGroups.map(g=>`<th class="coverage-feature-group" colspan="${g.ids.length}">${esc(g.label)}</th>`).join('')+'</tr><tr>'+features.map(f=>`<th class="coverage-feature" scope="col" title="${esc(f.definition)}"><span>${esc(f.label)}</span></th>`).join('')+'</tr></thead><tbody>';
    for(const section of tree.sections){if(!rows.some(r=>nodes[r.displayParent].section===section.id))continue;html+=`<tr class="coverage-section" ${section.root?`data-group="${nodes[section.root].jump}"`:''}><th scope="rowgroup" colspan="${features.length+1}">${esc(section.label)}</th></tr>`+branch(section.root,0,section.id);}
    table.innerHTML=html+'</tbody>';resizeColumns();
    wrap.hidden=!rows.length;
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
