"use strict";
(() => {
  const db = JSON.parse(document.getElementById("catalogue").textContent);
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const index = rows => Object.fromEntries(rows.map(r => [r.id,r]));
  const group = (rows,key) => {const out={};for(const r of rows)(out[r[key]]??=[]).push(r);return out;};
  const sources=index(db.sources), evidence=index(db.evidence), suites=index(db.evaluations), categories=index(db.categories), populations=index(db.populations), models=index(db.models), papers=index(db.papers), metrics=index(db.metrics), projects=index(db.projects), reviews=index(db.project_reviews);
  const projectsByReview=Object.fromEntries(db.projects.map(p=>[p.review_id,p]));
  const projectMemberships=group(db.project_review_evaluations.filter(r=>projectsByReview[r.review_id]&&["defines","successor-release"].includes(r.relation)),"evaluation_id");
  const taskProjectIds=ids=>[...new Set(ids.flatMap(id=>(projectMemberships[id]??[]).map(r=>projectsByReview[r.review_id].id)))];
  const taskCategories=group(db.task_categories,"task_id"), taskPops=group(db.task_populations,"task_id"), memberships=group(db.evaluation_tasks,"task_id"), protocols=group(db.protocols,"task_id"), variants=group(db.variants,"task_id"), counts=group(db.counts,"task_id"), uses=group(db.model_evaluations,"task_id"), metricLinks=group(db.protocol_metrics,"protocol_id"), fields=group(db.field_evidence,"entity_id");
  const coverageByTask=index(db.coverage.tasks);
  const outputByTask=Object.fromEntries(db.task_outputs.map(r=>[r.task_id,r]));
  const featureScopes=group(db.task_feature_scopes,'task_id');
  const trackCounts=Object.fromEntries(db.task_track_counts.map(r=>[r.task_id,r.tracks]));
  const statusNames={"artifact-audited":"Paper and selected artifacts","paper-audited":"Paper and methods","source-limited":"Source-limited definition","audited":"Sources reviewed"};
  const resources=index(db.data_resources),taskResources=group(db.task_resources,'task_id'),collectionResources=group(db.evaluation_resources,'evaluation_id');
  const sourceLimits=group(db.source_limits,'entity_id'),sourceReviews=group(db.source_reviews,'entity_id');
  db.evidence.forEach((e,i)=>e.number=i+1);
  const cite = id => {const e=evidence[id];return e?`<a class="citation" href="${esc(e.url)}" target="_blank" rel="noopener" title="${esc(e.locator+': '+e.statement)}" aria-label="Source ${e.number}: ${esc(e.locator)}">[${e.number}]</a>`:"";};
  const citations = ids => [...new Set(ids.filter(Boolean))].map(cite).join("");
  const tags = (values,cls="") => values.map(v=>`<span class="tag ${cls}">${esc(v)}</span>`).join("");
  const fieldEvidence = (id,field,fallback) => {const rows=(fields[id]??[]).filter(r=>r.field===field);return citations(rows.length?rows.map(r=>r.evidence_id):[fallback]);};
  const ancestors = id => coveragePopulationIds(id,populations,db.coverage.populationGroups);
  const categoryNames=(t,dimension)=>(taskCategories[t.id]??[]).filter(r=>categories[r.category_id].dimension===dimension).map(r=>categories[r.category_id].name);
  const taskList=db.tasks.map(t=>{
    t._cats=(taskCategories[t.id]??[]).map(r=>r.category_id);
    t._output=outputByTask[t.id];t._outputLabel=categories[t._output.category_id].name;
    const mapped=coverageByTask[t.id].mappings.filter(m=>m.population).map(m=>m.population);
    t._pops=[...new Set(mapped.flatMap(ancestors))];
    t._uses=uses[t.id]??[];
    t._original=t._uses.some(r=>r.model_id==="evo2"&&r.provenance==="original-paper");
    t._external=t._uses.some(r=>r.model_id==="evo2"&&r.provenance==="external-evaluation");
    t._suites=(memberships[t.id]??[]).map(r=>r.evaluation_id);
    t._collectionNames=t._suites.map(id=>suites[id].name);
    t._modelNames=[...new Set(t._uses.map(u=>models[u.model_id].name))];
    const paperIds=[...new Set(t._uses.map(u=>u.paper_id).concat(t._suites.map(id=>suites[id].paper_id)).filter(Boolean))];
    t._paperNames=paperIds.map(id=>{const p=papers[id];const model=db.models.find(m=>m.paper_id===id);return (model?.name??p.title)+` (${p.year})`;});
    t._projects=taskProjectIds(t._suites);
    t._search=[t.id,t.name,t.dataset_name,t.target,t.description,t.task_type,t.label_basis,t.input_description,t.limitations,...t._cats.map(k=>categories[k].name),...t._pops.map(k=>populations[k].name),...t._suites.map(k=>suites[k].name),...t._projects.map(k=>projects[k].name),...(protocols[t.id]??[]).map(p=>[p.name,p.adaptation,p.model_interface,p.split_rule,p.notes].join(" ")),...t._uses.map(u=>models[u.model_id].name)].join(" ").toLowerCase();
    return t;
  }).sort((a,b)=>a.name.localeCompare(b.name));
  const tasks=index(taskList);
  let state={}, matching=[];
  const coverageMatrix=createCoverageMatrix($("coverage-view"),db.coverage,tasks,populations,changes=>setState({...state,...changes}));
  const filterKeys=["q","application","population","capability","region","output","suite","project","evo"];
  const controls={q:"search",application:"application",population:"population",capability:"capability",region:"region",output:"output",suite:"suite",project:"project",evo:"evo"};
  const option=(value,label)=>{const el=document.createElement("option");el.value=value;el.textContent=label;return el;};
  for(const dim of ["application","capability","output"]){for(const r of db.categories.filter(r=>r.dimension===dim).sort((a,b)=>a.name.localeCompare(b.name))){const total=taskList.filter(t=>t._cats.includes(r.id)).length;$(dim).append(option(r.id,r.name+` (${total})`));}}
  for(const g of db.coverage.featureGroups){const optgroup=document.createElement('optgroup');optgroup.label=g.label;for(const id of g.ids){const r=categories[id];if(r)optgroup.append(option(id,r.name+` (${taskList.filter(t=>t._cats.includes(id)).length})`));}$('region').append(optgroup);}
  const popChildren=group(db.populations,"parent_id");
  const popOptions=(parent,prefix="")=>{
    const children=[...(popChildren[parent]??[])].sort((a,b)=>a.name.localeCompare(b.name));
    children.forEach((p,i)=>{
      const root=parent===null,last=i===children.length-1;
      $("population").append(option(p.id,prefix+(root?"":last?"└─ ":"├─ ")+p.name));
      // Nonbreaking spaces preserve indentation in native select menus.
      popOptions(p.id,root?"":prefix+(last?"\u00a0\u00a0\u00a0":"│\u00a0\u00a0"));
    });
  };
  popOptions(null);
  for(const s of [...db.evaluations].sort((a,b)=>a.name.localeCompare(b.name)))$("suite").append(option(s.id,s.name));
  for(const p of [...db.projects].sort((a,b)=>a.name.localeCompare(b.name)))$("project").append(option(p.id,p.name));
  $("updated").textContent=db.metadata.find(r=>r.key==="updated")?.value??"";

  function readState(){state=Object.fromEntries(new URLSearchParams(location.hash.slice(1)));if(state.task==="deepd-annotation-human")state={view:"evaluations",mode:"tasks",suite:"deepd-evals",q:"human routing probe"};if(!state.featureDetail&&state.cellFeature&&db.coverage.features.some(f=>f.id===state.cellFeature))state.featureDetail="individual";delete state.status;if(state.view==="data")state.view="models";const redirect=db.task_redirects.find(r=>r.id===state.task);if(redirect){state.suite=redirect.evaluation_id;if(redirect.replacement_task_id){state.task=redirect.replacement_task_id;state.mode="tasks";}else{delete state.task;state.mode="collections";}}state.view??="evaluations";if(!["evaluations","projects","models","papers","audit"].includes(state.view))state.view="evaluations";if(!["coverage","tasks","collections"].includes(state.mode))state.mode=state.task?"tasks":"coverage";if(!["species","allSpecies","clade"].includes(state.taxonDetail))state.taxonDetail="species";for(const key of filterKeys)$(controls[key]).value=state[key]??"";render();}
  function setState(next){const params=new URLSearchParams(Object.entries(next).filter(([,v])=>v));const hash=params.toString();if(location.hash.slice(1)!==hash)history.pushState(null,"","#"+hash);readState();}
  function fromControls(){const next={view:"evaluations",mode:state.mode,taxonDetail:state.taxonDetail,featureDetail:state.featureDetail,sort:state.sort,dir:state.dir,perPage:state.perPage};for(const key of filterKeys)next[key]=$(controls[key]).value;setState(next);}
  $("filters").addEventListener("submit",e=>e.preventDefault());
  $("filters").addEventListener("change",fromControls);
  $("search").addEventListener("input",()=>{const next={...state,q:$("search").value,task:"",cellRow:"",cellFeature:"",open:"",page:""};history.replaceState(null,"","#"+new URLSearchParams(Object.entries(next).filter(([,v])=>v)));state=next;renderEvaluations();});
  $("filters").addEventListener("reset",e=>{e.preventDefault();setState({view:"evaluations",mode:state.mode});});
  $("coverage-mode").addEventListener("click",()=>setState({...state,mode:"coverage",page:""}));
  $("task-mode").addEventListener("click",()=>setState({...state,mode:"tasks",page:""}));
  $("suite-mode").addEventListener("click",()=>setState({...state,mode:"collections",page:""}));
  $("page-size").addEventListener("change",()=>setState({...state,perPage:$("page-size").value,page:""}));
  function changePage(page){setState({...state,page:String(Math.max(1,page))});$('table-tools').scrollIntoView({block:'start'});}
  $("previous-page").addEventListener("click",()=>changePage(Number(state.page||1)-1));
  $("next-page").addEventListener("click",()=>changePage(Number(state.page||1)+1));
  window.addEventListener("hashchange",readState);
  document.addEventListener("click",e=>{const button=e.target.closest("button[data-task],button[data-suite]");if(button?.dataset.task)setState({view:"evaluations",task:button.dataset.task,mode:"tasks"});if(button?.dataset.suite)setState({...state,view:"evaluations",suite:button.dataset.suite,mode:"tasks",task:"",page:"",open:""});});
  document.addEventListener("click",e=>{const button=e.target.closest("button[data-clear-filter]");if(button){const next={...state,page:"",cellRow:"",cellFeature:"",open:""};delete next[button.dataset.clearFilter];setState(next);}});
  $("results").addEventListener("click",e=>{
    const sort=e.target.closest('[data-sort]');if(sort){setState({...state,sort:sort.dataset.sort,dir:(state.sort||'name')===sort.dataset.sort&&state.dir!=="desc"?"desc":"asc",page:""});return;}
    const pager=e.target.closest('[data-page-change]');if(pager){changePage(Number(state.page||1)+Number(pager.dataset.pageChange));return;}
    const button=e.target.closest('[data-expand-task],[data-expand-suite]');if(!button)return;
    const id=button.dataset.expandTask||button.dataset.expandSuite;
    state={...state,open:state.open===id?'':id};
    history.replaceState(null,'','#'+new URLSearchParams(Object.entries(state).filter(([,v])=>v)));
    if(state.mode==='collections')renderCollectionTable();else renderTaskTable();
    const restored=document.querySelector(`[${button.dataset.expandTask?'data-expand-task':'data-expand-suite'}="${CSS.escape(id)}"]`);
    restored?.focus({preventScroll:true});
  });

  function match(t){
    if(state.task&&t.id!==state.task)return false;
    if(state.q&&!state.q.toLowerCase().trim().split(/\s+/).every(word=>t._search.includes(word)))return false;
    for(const dim of ["application","capability","region","output"])if(state[dim]&&!t._cats.includes(state[dim]))return false;
    if(state.population&&!t._pops.includes(state.population))return false;
    if(state.suite&&!t._suites.includes(state.suite))return false;
    if(state.project&&!t._projects.includes(state.project))return false;
    if(state.evo==="original"&&!t._original||state.evo==="external"&&!t._external||state.evo==="both"&&!(t._original&&t._external))return false;
    return true;
  }
  function render(){
    for(const a of document.querySelectorAll("nav a")){if(a.dataset.view===state.view)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");}
    const titles={evaluations:"Evaluations",projects:"Benchmark projects",models:"Models",papers:"Papers and reports",audit:"Audit notes and evidence"};
    const descriptions={evaluations:"Explore task associations by organism and genomic feature, or browse tasks and collections. Filters apply across all three views.",projects:"Dedicated, reusable benchmarking efforts with documented independent adoption. Papers, benchmark releases and tasks remain separate records.",models:"Primary model scope and additional models included as evaluation sources. Model usage is attributed to the paper or release that documents it.",papers:"Primary papers, reports and benchmark sources. Versions, full-text inspection and released artifacts are separate records.",audit:"Evidence levels, unresolved differences and the scope of the current audit. An inspected field does not establish that an entire task has been verified."};
    $("page-title").textContent=titles[state.view];$("page-description").textContent=descriptions[state.view];
    $("coverage").textContent=`${db.models.filter(m=>m.scope==="primary").length} primary models · ${db.projects.length} benchmark projects · ${db.papers.length} paper/report sources · ${db.evaluations.length} collections · ${taskList.length} task/panel records · ${db.evidence.length} evidence records. Updated ${$("updated").textContent}.`;
    $("eval-view").hidden=state.view!=="evaluations";$("other-view").hidden=state.view==="evaluations";
    if(state.view==="evaluations")renderEvaluations();else{coverageMatrix.close();renderOther();}
  }
  function renderEvaluations(){
    const active=[...filterKeys,"task","cellRow"].filter(k=>state[k]);
    const cellLabel=()=>{const r=db.coverage.presentation.views[state.taxonDetail||'species'].rows.find(r=>r.id===state.cellRow),f=[...db.coverage.features,...db.coverage.groupedFeatures].find(f=>f.id===state.cellFeature);return (r?.displayLabel||state.cellRow)+(f?' × '+f.label:' — all features');};
    $("active-filters").innerHTML=active.length?'Active filters (combined): '+active.map(k=>{const control=controls[k]&&$(controls[k]);const value=k==='cellRow'?cellLabel():k==="task"?tasks[state[k]]?.name??state[k]:control?.tagName==="SELECT"?control.selectedOptions[0]?.textContent??state[k]:state[k];return `<button type="button" class="secondary" data-clear-filter="${esc(k)}" aria-label="Remove ${esc(k==='cellRow'?'selected cell':k)} filter">${esc(k==='cellRow'?'Selected cell':k)}: ${esc(value)} ×</button>`;}).join(" "):'No active filters. Numbers in category menus count all catalogue records, before other filters.';
    const capability=categories[state.capability];$("capability-definition").hidden=!capability;
    $("capability-definition").textContent=capability?capability.name+': '+capability.definition+' '+capability.accommodation:'';
    const output=categories[state.output];$("output-definition").hidden=!output;$("output-definition").textContent=output?output.name+": "+output.definition:"";
    const base=taskList.filter(match);
    const coverage=coverageMatrix.render(state,base,!filterKeys.some(k=>state[k])&&!state.task);
    matching=coverage.tasks;
    const coverageMode=state.mode==='coverage';
    $("coverage-view").hidden=!coverageMode;
    for(const mode of ['coverage','tasks','collections'])$(mode==='collections'?'suite-mode':mode==='tasks'?'task-mode':'coverage-mode').setAttribute('aria-pressed',String(state.mode===mode));
    if(!coverageMode)coverageMatrix.close();
    $("result-count").textContent=`${matching.length} matching records · ${matching.filter(t=>t._original).length} with original Evo 2 usage`+(coverageMode?` · ${coverage.rows} rows · ${coverage.associations.toLocaleString()} markers`:'');
    if(state.mode==='collections')renderCollectionTable();else renderTaskTable();
  }
  function pageSlice(items){
    const size=[25,50,100,250].includes(Number(state.perPage))?Number(state.perPage):100;
    const opened=items.findIndex(t=>t.id===(state.open||state.task));
    const requested=state.page?Number(state.page):opened>=0?Math.floor(opened/size)+1:1;
    const pages=Math.max(1,Math.ceil(items.length/size)),page=Math.min(pages,Math.max(1,requested||1));
    state.page=String(page);$('page-size').value=String(size);
    $('previous-page').disabled=page===1;$('next-page').disabled=page===pages;
    $('page-number').textContent=`${page} / ${pages}`;
    $('table-count').textContent=items.length?`${(page-1)*size+1}–${Math.min(page*size,items.length)} of ${items.length} ${state.mode==='collections'?'collections':'tasks'}`:'No matching records';
    return items.slice((page-1)*size,page*size);
  }
  const brief=(values,max=2)=>{const unique=[...new Set(values)];return unique.length?`<span title="${esc(unique.join('; '))}">${esc(unique.slice(0,max).join('; '))}${unique.length>max?' +'+(unique.length-max):''}</span>`:'';};
  const resourceLabel=r=>(r.host==='huggingface'?'HF':r.host==='github'?'GH':r.host==='zenodo'?'Zenodo':'Source')+' '+({dataset:'data',manifest:'manifest','evaluation-code':'code',results:'results'}[r.kind]);
  function resourceLinks(links){
    const rows=[...new Map(links.map(l=>[l.resource_id,resources[l.resource_id]])).values()].filter(Boolean);
    const ordered=rows.sort((a,b)=>['dataset','manifest','evaluation-code','results'].indexOf(a.kind)-['dataset','manifest','evaluation-code','results'].indexOf(b.kind));
    return ordered.length?'<span class="data-links">'+ordered.slice(0,3).map(r=>`<a href="${esc(r.url)}" target="_blank" rel="noopener" title="${esc(r.title+'; '+r.availability+'; '+r.notes)}">${esc(resourceLabel(r))}</a>`).join(' ')+(ordered.length>3?`<small>+${ordered.length-3} in details</small>`:'')+'</span>':'<span class="muted">Source citations</span>';
  }
  function resourceDetails(links){
    if(!links.length)return '';
    return '<h4>Data and evaluation resources</h4><div class="table-wrap"><table class="resource-table"><thead><tr><th>Resource</th><th>Use / availability</th><th>Scope</th></tr></thead><tbody>'+links.map(l=>{const r=resources[l.resource_id];return `<tr><td><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>${cite(l.evidence_id)}<br><span class="muted">${esc(resourceLabel(r))}${r.revision?' · '+esc(r.revision):''}</span></td><td>${esc(l.relation.replaceAll('-',' '))}<br>${esc(r.availability)}</td><td>${esc(l.note)} ${esc(r.notes)}</td></tr>`;}).join('')+'</tbody></table></div>';
  }
  function reviewDetails(table,id){
    const review=(sourceReviews[id]??[]).find(r=>r.entity_table===table),limits=(sourceLimits[id]??[]).filter(r=>r.entity_table===table);
    return (limits.length?'<h4>Source limits</h4><ul class="source-limits">'+limits.map(l=>`<li><strong>${esc(l.field.replaceAll('_',' '))} — ${esc(l.reason.replaceAll('-',' '))}.</strong> ${esc(l.detail)}${cite(l.evidence_id)}</li>`).join('')+'</ul>':'')+(review?`<details class="source-review"><summary>Source review completed ${esc(review.reviewed)}</summary><p>${esc(review.scope)}${citations(JSON.parse(review.evidence_ids_json))}</p>${review.limitations?'<p>'+esc(review.limitations)+'</p>':''}</details>`:'');
  }
  const originNames=t=>[...new Set(coverageByTask[t.id].mappings.filter(m=>m.population&&m.population!=='synthetic').map(m=>populations[m.population].name))];
  const evoLabel=t=>t._original&&t._external?'Original; external':t._original?'Original paper':t._external?'External':'Not established';
  function sorted(items,value){const key=state.sort||'name',direction=state.dir==='desc'?-1:1;return [...items].sort((a,b)=>direction*String(value(a,key)).localeCompare(String(value(b,key)),undefined,{numeric:true})||a.id.localeCompare(b.id));}
  function column(label,key){return `<th scope="col" aria-sort="${(state.sort||'name')===key?(state.dir==='desc'?'descending':'ascending'):'none'}"><button type="button" class="sort-button" data-sort="${key}">${esc(label)}${(state.sort||'name')===key?(state.dir==='desc'?' (desc)':' (asc)'):''}</button></th>`;}
  function renderTaskTable(){
    const value=(t,key)=>key==='suite'?t._suites.map(k=>suites[k].name).sort().join('; '):key==='organism'?originNames(t).join('; '):key==='type'?t._outputLabel:key==='evo'?evoLabel(t):key==='status'?statusNames[t.status]:t.name;
    const visible=pageSlice(sorted(matching,value));
    const open=state.open||state.task;
    const shortStatus={'artifact-audited':'Artifacts','paper-audited':'Paper / methods','source-limited':'Source limits'};
    const body=visible.map(t=>{
      const expanded=open===t.id;
      return `<tr class="compact-task-row" data-id="${esc(t.id)}"><td><button type="button" class="task-toggle" data-expand-task="${esc(t.id)}" aria-expanded="${expanded}" aria-controls="detail-${esc(t.id)}" title="${esc(t.dataset_name)}">${esc(t.name)}</button></td><td>${brief(t._suites.map(k=>suites[k].name))}</td><td>${brief(originNames(t))||'Unresolved'}${coverageByTask[t.id].protein?'<small>Protein-only reference</small>':''}</td><td title="${esc(t._output.scoring_unit)}">${esc(t._outputLabel)}${t._output.status!=='supported'?'<small>'+esc(t._output.status==='unresolved'?'Unresolved scoring':'Qualified; see details')+'</small>':''}<small>${esc(t.task_type)}</small></td><td class="provenance">${esc(evoLabel(t))}</td><td>${resourceLinks(taskResources[t.id]??[])}</td><td class="evidence-status" title="${esc(statusNames[t.status])}">${esc(shortStatus[t.status])}</td></tr><tr id="detail-${esc(t.id)}" class="task-detail-row" ${expanded?'':'hidden'}><td colspan="7" class="task-detail-cell"><div class="detail-body">${expanded?renderTaskDetail(t):''}</div></td></tr>`;
    }).join('');
    $('results').innerHTML=visible.length?'<div class="table-wrap"><table class="compact-table tasks-table"><thead><tr>'+column('Task','name')+column('Collection','suite')+column('Organisms / targets','organism')+column('Scored output','type')+column('Evo 2 use','evo')+'<th scope="col">Data / code</th>'+column('Evidence','status')+'</tr></thead><tbody>'+body+'</tbody></table></div>'+bottomPager():'<p class="empty">No matching tasks. Missing source metadata can exclude a task.</p>';
  }
  function bottomPager(){return `<div class="result-pager"><button type="button" class="secondary" data-page-change="-1" ${$('previous-page').disabled?'disabled':''}>Previous</button><span>${esc($('page-number').textContent)}</span><button type="button" class="secondary" data-page-change="1" ${$('next-page').disabled?'disabled':''}>Next</button></div>`;}
  function renderCollectionTable(){
    const matchedIds=new Set(matching.map(t=>t.id)),filtered=filterKeys.some(k=>state[k])||state.task||state.cellRow;
    const items=db.evaluations.filter(s=>((!filtered&&!state.suite)||state.suite===s.id||db.evaluation_tasks.some(r=>r.evaluation_id===s.id&&matchedIds.has(r.task_id))||(state.project&&!state.suite&&!filterKeys.some(k=>k!=='project'&&state[k])&&taskProjectIds([s.id]).includes(state.project)))&&(!state.project||taskProjectIds([s.id]).includes(state.project)));
    const taskIds=s=>db.evaluation_tasks.filter(r=>r.evaluation_id===s.id).map(r=>r.task_id),count=s=>taskIds(s).filter(id=>matchedIds.has(id)).length;
    const value=(s,key)=>key==='count'?String(count(s)):key==='evo'?String(taskIds(s).filter(id=>tasks[id]._original).length):key==='status'?s.status:s.name;
    const visible=pageSlice(sorted(items,value));
    $('result-count').textContent=`${items.length} collections · ${matching.length} matching task/panel records`;
    $('results').innerHTML=visible.length?'<div class="table-wrap"><table class="compact-table collections-table"><thead><tr>'+column('Collection','name')+column('Matching / catalogued tasks','count')+column('Original Evo 2 tasks','evo')+'<th scope="col">Data / code</th>'+column('Evidence','status')+'</tr></thead><tbody>'+visible.map(s=>`<tr><td><button type="button" class="collection-toggle" data-expand-suite="${esc(s.id)}" aria-expanded="${state.open===s.id}" aria-controls="collection-detail-${esc(s.id)}">${esc(s.name)}</button></td><td>${count(s)} / ${taskIds(s).length}</td><td>${taskIds(s).filter(id=>tasks[id]._original).length}</td><td>${resourceLinks(collectionResources[s.id]??[])}</td><td>${esc(statusNames[s.status]??s.status)}</td></tr><tr id="collection-detail-${esc(s.id)}" ${state.open===s.id?'':'hidden'}><td colspan="5" class="task-detail-cell">${state.open===s.id?renderSuite(s,matching):''}</td></tr>`).join('')+'</tbody></table></div>':'<p class="empty">No matching collections.</p>';
  }
  function fact(label,value,citation=""){return `<dt>${esc(label)}</dt><dd>${esc(value||"Not established in inspected sources")}${citation}</dd>`;}
  function renderTaskDetail(t){
    const ps=protocols[t.id]??[],vs=variants[t.id]??[],ns=counts[t.id]??[],us=uses[t.id]??[];
    const o=t._output;
    let html=`<p>${esc(t.description)}${cite(t.evidence_id)}</p><dl class="facts">${fact("Dataset",t.dataset_name,fieldEvidence(t.id,"dataset_name",t.evidence_id))}${fact("Target",t.target,fieldEvidence(t.id,"target",t.evidence_id))}${fact("Input",t.input_description,fieldEvidence(t.id,"input_description",t.evidence_id))}${fact("Output",t.output_description==='Target prediction'?o.prediction_form:t.output_description,cite(o.evidence_id))}${fact("Label basis",t.label_basis,fieldEvidence(t.id,"label_basis",t.evidence_id))}</dl>`;
    html+=resourceDetails(taskResources[t.id]??[])+reviewDetails('tasks',t.id);
    if(trackCounts[t.id])html+=`<p class="track-summary"><strong>${Number(trackCounts[t.id]).toLocaleString()} source track identities.</strong> Assay, species and sample context are retained individually in the downloadable SQLite database; protocol-specific evaluated subsets and counts are stated below.</p>`;
    html+=`<h4>Output and scoring scope</h4><dl class="facts">${fact('Scored output',t._outputLabel,cite(o.evidence_id))}${fact('Prediction form',o.prediction_form)}${fact('Scoring unit',o.scoring_unit,fieldEvidence(o.id,'scoring_unit',o.evidence_id))}${fact('Structure scope',o.structure_scope.replaceAll('-',' '))}${fact('Output review',o.status)}</dl><p>${esc(o.rationale)}${cite(o.evidence_id)}</p><p class="muted">${esc(o.limitations)}</p>`;
    for(const f of featureScopes[t.id]||[])html+=`<p class="feature-scope"><strong>${esc(categories[f.feature_id].name)} scope: ${esc(f.scope.replaceAll('-',' '))}.</strong> ${esc(f.rationale)}${cite(f.evidence_id)}</p>`;
    html+='<p>Collections: '+(memberships[t.id]||[]).map(m=>`<a href="#view=evaluations&amp;mode=collections&amp;suite=${encodeURIComponent(m.evaluation_id)}">${esc(suites[m.evaluation_id].name)}</a>${cite(m.evidence_id)}`).join('; ')+'</p>';
    if(t._projects.length)html+='<p>Benchmark project: '+t._projects.map(id=>`<a href="#view=projects&amp;project=${encodeURIComponent(id)}">${esc(projects[id].name)}</a>`).join('; ')+'</p>';
    if(t.limitations)html+=`<p class="note">${esc(t.limitations)}${cite(t.evidence_id)}</p>`;
    html+='<h4>Classification</h4><dl class="facts">';
    for(const dim of ["application","capability","region"]){const rs=(taskCategories[t.id]??[]).filter(r=>categories[r.category_id].dimension===dim);html+=`<dt>${{application:"Application",capability:"Model capability",region:"Genomic feature",output:"Scored output"}[dim]}</dt><dd>${rs.length?rs.map(r=>`${esc(categories[r.category_id].name)} <span class="muted">(${esc(r.relation)}; editorial mapping)</span>${cite(r.evidence_id)}`).join("<br>"):"Not assigned"}</dd>`;}
    html+='<dt>Organism / context</dt><dd>'+((taskPops[t.id]??[]).map(p=>`${esc(populations[p.population_id].name)} — ${esc(p.relation)}. ${esc(p.coverage)}${cite(p.evidence_id)}`).join("<br>")||"Not established; not inferred from a gene-name abbreviation.")+'</dd></dl>';
    if(ps.length)html+='<h4>Evaluation protocols</h4>'+ps.map(p=>renderProtocol(p)).join("");else html+='<p class="note">The cited source does not define an executable evaluation protocol. See the source limits for the reported claim.</p>';
    if(ns.length){html+='<h4>Scale and released-file counts</h4><p class="muted">Reported totals, artifact rows and final scored examples may differ. Counts below are not additive; variants and filtering qualifiers matter.</p><div class="table-wrap"><table><thead><tr><th>Partition / variant</th><th>Count</th><th>Unit</th><th>Basis and qualification</th></tr></thead><tbody>'+ns.map(n=>`<tr><td>${esc(n.split)}${n.variant_id?'<br><span class="muted">'+esc(vs.find(v=>v.id===n.variant_id)?.name??n.variant_id)+'</span>':""}${n.protocol_id?'<br><span class="muted">'+esc(ps.find(p=>p.id===n.protocol_id)?.name??n.protocol_id)+'</span>':""}</td><td class="count-number">${Number(n.value).toLocaleString()}</td><td>${esc(n.unit)}</td><td>${esc(n.method)}. ${esc(n.qualifier)}${fieldEvidence(n.id,"value",n.evidence_id)}</td></tr>`).join("")+'</tbody></table></div>';}
    if(vs.length)html+='<details><summary>'+vs.length+' linked dataset / target / condition variants</summary><div class="table-wrap"><table><thead><tr><th>Variant</th><th>Context / input</th><th>Revision / notes</th></tr></thead><tbody>'+vs.map(v=>`<tr><td>${esc(v.name)}${cite(v.evidence_id)}</td><td>${esc(v.context)}${v.input_length?'<br>'+esc(v.input_length):""}${v.target_count?'<br>'+v.target_count+' '+esc(v.target_unit):""}</td><td>${v.dataset_revision?'<code>'+esc(v.dataset_revision)+'</code><br>':""}${esc(v.notes)}</td></tr>`).join("")+'</tbody></table></div></details>';
    html+='<h4>Documented model usage</h4>'+(us.length?'<div class="table-wrap"><table><thead><tr><th>Model</th><th>Attribution</th><th>Source / protocol</th></tr></thead><tbody>'+us.map(u=>`<tr><td>${esc(models[u.model_id].name)}</td><td>${esc(u.provenance.replaceAll("-"," "))}</td><td>${esc(papers[u.paper_id]?.title)}${cite(u.evidence_id)}${u.protocol_id?'<br>'+esc(ps.find(p=>p.id===u.protocol_id)?.name??u.protocol_id):""}${u.note?'<br><span class="muted">'+esc(u.note)+'</span>':""}</td></tr>`).join("")+'</tbody></table></div>':'<p class="muted">The inspected sources do not establish a model–task association. This does not assert that the task was unused.</p>');
    if(!t._original)html+='<p class="muted">Original Evo 2 use is not documented for this record in the current audit. This is not a verified absence claim.</p>';
    const fs=db.findings.filter(f=>f.task_id===t.id);if(fs.length)html+='<h4>Audit findings</h4>'+fs.map(f=>`<p class="finding note">${esc(f.description)}${cite(f.evidence_id)}</p>`).join("");
    const mapping=coverageByTask[t.id].mappings;
    html+='<details class="coverage-mapping-evidence"><summary>Coverage placement and evidence</summary><p>Assignments identify sequence origin or protein-target provenance; assay/sample host alone does not establish either. Taxon and genomic-feature co-annotation does not establish a released joint subset.</p><ul>'+mapping.map(m=>`<li><strong>${esc(m.name)}</strong> · ${esc(m.basis)}. ${esc(m.note||'')}${cite(m.evidence)}${citations(m.supporting)}</li>`).join('')+'</ul></details>';
    const ids=new Set([t.evidence_id,o.evidence_id,...(fields[o.id]??[]).map(f=>f.evidence_id),...ps.map(p=>p.source_evidence_id),...ns.map(n=>n.evidence_id),...vs.map(v=>v.evidence_id),...us.map(u=>u.evidence_id),...fs.map(f=>f.evidence_id),...(fields[t.id]??[]).map(f=>f.evidence_id),...mapping.flatMap(m=>[m.evidence,...m.supporting])]);
    html+=renderReferences([...ids]);
    html+=`<p class="muted">Record: <code>${esc(t.id)}</code> · <a href="#view=evaluations&amp;task=${encodeURIComponent(t.id)}">Permanent task link</a></p>`;
    return html;
  }
  function renderProtocol(p){
    const ms=(metricLinks[p.id]??[]).map(m=>metrics[m.metric_id].name+(m.is_primary?" (primary)":"")+" — "+m.aggregation).join("; ");
    const embeds=p.requires_embeddings===null?"Not established / protocol-dependent":p.requires_embeddings?"Required":"Not required by this protocol";
    return `<article class="protocol"><h4>${esc(p.name)}${cite(p.source_evidence_id)}</h4><dl class="facts">${fact("Adaptation",p.adaptation)}${fact("Model interface",p.model_interface,fieldEvidence(p.id,"model_interface",p.source_evidence_id))}${fact("Embeddings",embeds)}${fact("Fitted component",p.fitted_component??(p.adaptation.includes("zero-shot")?"None in this protocol":"Not established"))}${fact("Partition rule",p.split_rule,fieldEvidence(p.id,"split_rule",p.source_evidence_id))}${fact("Split unit",p.split_unit)}${fact("Selection",p.selection)}${fact("Metrics",ms||"Metric not specified in the cited source",fieldEvidence(p.id,"metrics",p.source_evidence_id))}</dl>${p.notes?'<p>'+esc(p.notes)+'</p>':""}</article>`;
  }
  function renderReferences(ids){return `<details class="references"><summary>Evidence and source locators (${ids.length})</summary><ol>${ids.map(id=>{const e=evidence[id];if(!e)return"";const s=sources[e.source_id];return `<li value="${e.number}"><a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(s.title)}</a> · ${esc(e.basis)}<br>${esc(e.locator)}. ${esc(e.statement)}<br><span class="muted">${esc(s.version??"")} · inspected ${esc(e.inspected)}${s.sha256?' · SHA-256 <code>'+esc(s.sha256)+'</code>':""}</span></li>`;}).join("")}</ol></details>`;}
  function renderSuite(s,matched){
    const links=db.evaluation_tasks.filter(r=>r.evaluation_id===s.id),all=links.map(r=>tasks[r.task_id]),subset=all.filter(t=>matched.some(m=>m.id===t.id));
    const classes=dim=>[...new Set(all.flatMap(t=>categoryNames(t,dim)))].sort();
    const pops=[...new Set(all.flatMap(t=>(taskPops[t.id]??[]).map(p=>populations[p.population_id].name)))].sort();
    const ps=taskProjectIds([s.id]);
    const projectLinks=ps.length?'<p>Project: '+ps.map(id=>`<a href="#view=projects&amp;project=${encodeURIComponent(id)}">${esc(projects[id].name)}</a>`).join('; ')+'</p>':'';
    return `<article class="collection"><h3>${esc(s.name)} ${tags([statusNames[s.status]??s.status])}</h3><p>${esc(s.description)}${cite(s.evidence_id)}</p>${projectLinks}${resourceDetails(collectionResources[s.id]??[])}${reviewDetails('evaluations',s.id)}<p class="muted">${links.length} linked task/panel records · ${all.filter(t=>t._original).length} with documented original Evo 2 use · ${subset.length} match current filters.</p><dl class="facts">${fact("Applications",classes("application").join("; "))}${fact("Capabilities",classes("capability").join("; "))}${fact("Scored outputs",classes("output").join("; "))}${fact("Genomic features",classes("region").join("; "))}${fact("Organisms / contexts",pops.join("; "))}</dl><p>${esc(s.scope_note)}</p>${s.notes?'<p class="note">'+esc(s.notes)+fieldEvidence(s.id,'output_audit',s.evidence_id)+'</p>':""}<p><button data-suite="${esc(s.id)}" type="button" class="secondary">View tasks</button></p><details><summary>Constituent tasks and source-specific notes</summary><ul>${links.map(r=>`<li><a href="#view=evaluations&amp;task=${encodeURIComponent(r.task_id)}">${esc(tasks[r.task_id].name)}</a>${r.note?' — '+esc(r.note):""}${cite(r.evidence_id)}</li>`).join("")}</ul></details><p class="muted">Collection classifications above are unions of constituent task assignments; they do not apply to every task.</p></article>`;
  }
  function paperLink(id){const p=papers[id];return `<a href="${esc(sources[p.source_id].url)}">${esc(p.title)}</a>`;}
  function renderProjectReviews(){
    const names={"adoption-not-established":"Adoption not established","outside-definition":"Outside project definition"};
    return '<details class="project-reviews"><summary>Other sources reviewed for project inclusion</summary><p class="muted">These are source-review decisions, not additional projects. Failure to establish adoption in this review is not proof that a resource has no users. Papers and useful tasks remain in scope.</p><div class="table-wrap"><table><thead><tr><th>Source</th><th>Decision</th><th>Reason and evidence</th></tr></thead><tbody>'+db.project_reviews.filter(r=>r.decision!=="qualified").sort((a,b)=>a.name.localeCompare(b.name)).map(r=>`<tr><td>${esc(r.name)}</td><td>${esc(names[r.decision])}</td><td>${esc(r.rationale)}${cite(r.evidence_id)}</td></tr>`).join('')+'</tbody></table></div></details>';
  }
  function renderProjects(){
    const policy=db.metadata.find(r=>r.key==="project_policy")?.value;
    const selected=state.project?db.project_summary.filter(p=>p.id===state.project):db.project_summary;
    $("other-view").innerHTML=`<p class="section-note">${esc(policy)}${cite('project-policy')}</p>`+(state.project?'<p><a href="#view=projects">All benchmark projects</a></p>':'')+[...selected].sort((a,b)=>a.name.localeCompare(b.name)).map(p=>{
      const r=reviews[p.review_id],uses=db.project_adoptions.filter(a=>a.review_id===p.review_id),links=db.project_review_evaluations.filter(l=>l.review_id===p.review_id),papersForProject=db.project_review_papers.filter(l=>l.review_id===p.review_id&&l.relation!=="adoption-evidence");
      const taskIds=[...new Set(links.flatMap(l=>db.evaluation_tasks.filter(et=>et.evaluation_id===l.evaluation_id).map(et=>et.task_id)))];
      const evo=taskIds.filter(id=>tasks[id]._original).length;
      const sourceIds=[p.evidence_id,...uses.map(a=>a.evidence_id),...papersForProject.map(l=>l.evidence_id),...(fields[p.id]??[]).map(f=>f.evidence_id)];
      return `<article class="record project" id="project-${esc(p.id)}"><h2><a href="#view=projects&amp;project=${encodeURIComponent(p.id)}">${esc(p.name)}</a></h2><p>${esc(p.description)}${cite(p.evidence_id)}</p><p class="muted">${p.independent_groups} documented external adopter groups · ${p.collection_count} linked collections · ${p.task_count} catalogued task/panel records · ${evo} with original Evo 2 use</p><p>${papersForProject.map(l=>paperLink(l.paper_id)+' '+esc(l.relation)+cite(l.evidence_id)).join('<br>')||'The pinned project documentation is the introducing source.'}</p><ul>${links.map(l=>`<li><a href="#view=evaluations&amp;mode=collections&amp;suite=${encodeURIComponent(l.evaluation_id)}">${esc(suites[l.evaluation_id].name)}</a> — ${esc(l.note)}${cite(l.evidence_id)}</li>`).join('')}</ul><p class="muted">Task counts refer to dataset–target records; linked variants preserve the release inventory.</p><details class="project-adoption" ${state.project?'open':''}><summary>Independent use and qualification evidence</summary><p>${esc(r.rationale)}${cite(r.evidence_id)}</p><div class="table-wrap"><table><thead><tr><th>Adopter / source</th><th>Use and independence</th><th>Release, subset and limitations</th></tr></thead><tbody>${uses.map(a=>`<tr><td>${esc(a.adopter_group)}${a.paper_id?'<br>'+paperLink(a.paper_id):''}</td><td>${esc(a.kind)} · ${esc(a.independence)}<br><span class="muted">${esc(a.independence_note)}</span></td><td>${esc(a.scope)}${cite(a.evidence_id)}</td></tr>`).join('')}</tbody></table></div><p>${esc(p.scope_note)}</p><p class="muted">Reviewed ${esc(r.reviewed)}. ${esc(r.search_scope)}</p>${renderReferences([...new Set(sourceIds)])}</details><p><a href="#view=evaluations&amp;mode=collections&amp;project=${encodeURIComponent(p.id)}">Browse project collections</a></p></article>`;
    }).join('')+(!selected.length?'<p class="empty">Project not found.</p>':'')+(!state.project?renderProjectReviews():'');
  }
  function renderOther(){
    if(state.view==="projects"){renderProjects();return;}
    if(state.view==="models"){
      $("other-view").innerHTML=["primary","evaluation-source"].map(scope=>'<h2>'+(scope==="primary"?"Primary model scope":"Additional evaluation sources")+'</h2>'+db.models.filter(m=>m.scope===scope).map(m=>{
        const assoc=db.model_evaluations.filter(u=>u.model_id===m.id),original=[...new Set(assoc.filter(u=>["original-paper","original-release"].includes(u.provenance)).map(u=>u.task_id))],external=[...new Set(assoc.filter(u=>u.provenance==="external-evaluation").map(u=>u.task_id))];
        const properties=db.model_properties.filter(p=>p.model_id===m.id);
        const propertyTable=properties.length?'<details class="model-properties" open><summary>Corpus, architecture and evaluation procedures</summary><div class="table-wrap"><table><thead><tr><th>Property</th><th>Evidence and limitations</th></tr></thead><tbody>'+properties.map(p=>`<tr><td>${esc(p.name)}<br><span class="muted">${esc(p.category)} · ${esc(p.status)}${p.variant?' · '+esc(p.variant):''}</span></td><td>${esc(p.value)}${citations([p.evidence_id,...(fields[p.id]??[]).map(f=>f.evidence_id)])}${p.notes?'<p class="muted">'+esc(p.notes)+'</p>':''}</td></tr>`).join('')+'</tbody></table></div></details>':'';
        return `<article class="record" id="model-${esc(m.id)}"><h2>${esc(m.name)}</h2><p>${esc(m.description)}${cite(m.evidence_id)}</p>${m.notes?'<p class="note">'+esc(m.notes)+citations((fields[m.id]??[]).map(f=>f.evidence_id))+'</p>':""}<p><a href="${esc(sources[papers[m.paper_id].source_id].url)}">${esc(papers[m.paper_id].title)}</a></p>${propertyTable}${reviewDetails('models',m.id)}<p class="muted">${original.length} documented original-source task/panel associations · ${external.length} external-evaluation associations. Associations refer to the cited releases.</p><details><summary>Task associations by provenance</summary><ul>${[...new Set(assoc.map(u=>u.task_id))].map(id=>`<li><a href="#view=evaluations&amp;task=${encodeURIComponent(id)}">${esc(tasks[id].name)}</a> — ${esc([...new Set(assoc.filter(u=>u.task_id===id).map(u=>u.provenance))].join("; "))}</li>`).join("")||'<li>No task association is established by the cited source.</li>'}</ul></details></article>`;
      }).join("")).join("");return;
    }
    if(state.view==="papers"){
      $("other-view").innerHTML='<p class="section-note">Carbon-X has official release documentation; AIDO.DNA2 has an official technical web report. Full-text availability and the representations inspected are recorded per source. Adoption-evidence papers document external benchmark use and do not expand the primary model scope.</p>'+[...db.papers].sort((a,b)=>(b.year-a.year)||a.title.localeCompare(b.title)).map(p=>{const s=sources[p.source_id],ps=db.project_review_papers.filter(l=>l.paper_id===p.id&&l.relation!=="adoption-evidence"&&projectsByReview[l.review_id]);return `<article class="record"><h2><a href="${esc(s.url)}">${esc(p.title)}</a></h2><p>${esc(p.year)} · ${esc(p.status)} · ${esc(p.scope.replaceAll("-"," "))}</p>${ps.length?'<p>Project: '+ps.map(l=>`<a href="#view=projects&amp;project=${encodeURIComponent(projectsByReview[l.review_id].id)}">${esc(projectsByReview[l.review_id].name)}</a>`).join('; ')+'</p>':''}<p class="muted">${esc(s.version??"")} · ${s.local_path?"Cached full-text/documentation representation; review scope follows the cited evidence":"The cited representation and retrieval limits are stated below"}</p>${p.notes?'<p>'+esc(p.notes)+'</p>':""}${reviewDetails("papers",p.id)}<details><summary>Source metadata</summary><p><code>${esc(p.id)}</code> · ${esc(s.kind)} · retrieved ${esc(s.retrieved)}</p>${s.sha256?'<p>Cached representation SHA-256: <code>'+esc(s.sha256)+'</code></p>':""}<p>${esc(s.notes??"")}</p></details></article>`;}).join("");return;
    }
    const n=status=>taskList.filter(t=>t.status===status).length;
    $("other-view").innerHTML=`<h2>Source review</h2><p>All indexed task definitions and collections have a completed review of the identified primary sources. A completed review does not make unavailable data available. Missing fields, unretrieved supplements and discrepancies are recorded explicitly.</p><dl class="legend"><dt>Paper and selected artifacts (${n("artifact-audited")})</dt><dd>Pinned dataset files, manifests or evaluation code support specific fields. The evidence identifies the files inspected and counts measured.</dd><dt>Paper and methods (${n("paper-audited")})</dt><dd>The primary text supports the task and protocol. Any unavailable examples, partitions or implementation details are stated in the record.</dd><dt>Source-limited definition (${n("source-limited")})</dt><dd>The source reports an evaluation but does not resolve every assay, target or protocol field. The claim remains visible with its precise limits; it is not treated as a fully specified independent assay.</dd></dl><h2>Interpretation</h2><p class="section-note">Evidence is attached to fields, classifications, protocols, counts and model usage. Application mappings are editorial. Long input, a species label, a chromosome split and a zero-shot score answer different questions; none alone establishes pretraining exclusion or biological transfer. Missing model usage is unknown rather than a verified negative.</p><p class="section-note">Measured counts come from pinned public files. A genome row can contain thousands of gene labels; a split file can precede eligibility filters. Repeated targets, variants and suite membership must not be summed as independent examples.</p><h2>Output and feature audit</h2><p>Every task/panel has a cited output review. Prediction form and the unit actually scored are separate: a dense native model can be evaluated only at a supplied site. Complete chains, component intervals, base labels and quantitative signal profiles remain distinct. Qualified or unresolved source definitions do not establish held-out dense scoring.</p><p><a href="https://github.com/eric-czech/marin-glm/blob/main/docs/output-audit.md">Source audit and grouping decisions</a></p><dl class="legend">${db.categories.filter(r=>r.dimension==="output").map(r=>`<dt>${esc(r.name)}</dt><dd>${esc(r.definition)}</dd>`).join("")}</dl><h2>Capability definitions</h2><dl class="legend">${db.categories.filter(r=>r.dimension==="capability").map(r=>`<dt>${esc(r.name)}</dt><dd>${esc(r.definition)} ${esc(r.accommodation)}</dd>`).join("")}</dl><h2>Source findings</h2>${db.findings.map(f=>`<article class="record"><p><span class="badge ${f.severity==="discrepancy"?"pending":""}">${esc(f.severity)}</span> ${esc(f.description)}${cite(f.evidence_id)}</p>${f.task_id?'<p><a href="#view=evaluations&amp;task='+encodeURIComponent(f.task_id)+'">'+esc(tasks[f.task_id].name)+'</a></p>':f.evaluation_id?'<p><a href="#view=evaluations&amp;mode=collections&amp;suite='+encodeURIComponent(f.evaluation_id)+'">'+esc(suites[f.evaluation_id].name)+'</a></p>':""}</article>`).join("")}<h2>Evidence registry</h2>${renderReferences(db.evidence.map(e=>e.id))}`;
  }
  $("export").addEventListener("click",()=>{
    const quote=s=>'"'+String(s??"").replaceAll('"','""')+'"';
    const rows=[["id","task","dataset","target","type","evidence_level","collections","projects","applications","organisms","assay_or_sample_hosts","capabilities","genomic_features","scored_output","prediction_form","scoring_unit","output_review_status","structure_scope","evo2_original","evo2_external","data_resources","source_limits","source_review_date","source"]];
    for(const t of matching)rows.push([t.id,t.name,t.dataset_name,t.target,t.task_type,t.status,t._suites.map(k=>suites[k].name).join("; "),t._projects.map(k=>projects[k].name).join("; "),categoryNames(t,"application").join("; "),originNames(t).join('; '),(taskPops[t.id]??[]).filter(p=>['assay-host','sample-host'].includes(p.relation)).map(p=>populations[p.population_id].name+' ('+p.relation+')').join('; '),categoryNames(t,"capability").join("; "),categoryNames(t,"region").join("; "),t._outputLabel,t._output.prediction_form,t._output.scoring_unit,t._output.status,t._output.structure_scope,t._original?"documented":"not established",t._external?"documented":"not established",(taskResources[t.id]??[]).map(l=>resources[l.resource_id].url).join("; "),(sourceLimits[t.id]??[]).filter(l=>l.entity_table==='tasks').map(l=>l.field+": "+l.reason+" — "+l.detail).join("; "),(sourceReviews[t.id]??[]).find(r=>r.entity_table==='tasks')?.reviewed??"",evidence[t.evidence_id].url]);
    const url=URL.createObjectURL(new Blob([rows.map(r=>r.map(quote).join(",")).join("\r\n")],{type:"text/csv;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download="marin-glm-tasks.csv";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  readState();
})();
