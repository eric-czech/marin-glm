"use strict";
(() => {
  const db = JSON.parse(document.getElementById("catalogue").textContent);
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const index = rows => Object.fromEntries(rows.map(r => [r.id,r]));
  const group = (rows,key) => {const out={};for(const r of rows)(out[r[key]]??=[]).push(r);return out;};
  const sources=index(db.sources), evidence=index(db.evidence), suites=index(db.evaluations), categories=index(db.categories), populations=index(db.populations), models=index(db.models), papers=index(db.papers), metrics=index(db.metrics);
  const taskCategories=group(db.task_categories,"task_id"), taskPops=group(db.task_populations,"task_id"), memberships=group(db.evaluation_tasks,"task_id"), protocols=group(db.protocols,"task_id"), variants=group(db.variants,"task_id"), counts=group(db.counts,"task_id"), uses=group(db.model_evaluations,"task_id"), metricLinks=group(db.protocol_metrics,"protocol_id"), fields=group(db.field_evidence,"entity_id");
  const statusNames={"artifact-audited":"Selected artifacts audited","paper-audited":"Paper / protocol audit","registered":"Registered; task audit pending","panel-pending":"Composite panel; expansion pending"};
  db.evidence.forEach((e,i)=>e.number=i+1);
  const cite = id => {const e=evidence[id];return e?`<a class="citation" href="${esc(e.url)}" target="_blank" rel="noopener" title="${esc(e.locator+': '+e.statement)}" aria-label="Source ${e.number}: ${esc(e.locator)}">[${e.number}]</a>`:"";};
  const citations = ids => [...new Set(ids.filter(Boolean))].map(cite).join("");
  const tags = (values,cls="") => values.map(v=>`<span class="tag ${cls}">${esc(v)}</span>`).join("");
  const fieldEvidence = (id,field,fallback) => {const rows=(fields[id]??[]).filter(r=>r.field===field);return citations(rows.length?rows.map(r=>r.evidence_id):[fallback]);};
  const ancestors = id => {const out=[];for(let p=populations[id];p;p=populations[p.parent_id])out.push(p.id);return out;};
  const categoryNames=(t,dimension)=>(taskCategories[t.id]??[]).filter(r=>categories[r.category_id].dimension===dimension).map(r=>categories[r.category_id].name);
  const taskList=db.tasks.map(t=>{
    t._cats=(taskCategories[t.id]??[]).map(r=>r.category_id);
    t._pops=[...new Set((taskPops[t.id]??[]).flatMap(r=>ancestors(r.population_id)))];
    t._uses=uses[t.id]??[];
    t._original=t._uses.some(r=>r.model_id==="evo2"&&r.provenance==="original-paper");
    t._external=t._uses.some(r=>r.model_id==="evo2"&&r.provenance==="external-evaluation");
    t._suites=(memberships[t.id]??[]).map(r=>r.evaluation_id);
    t._search=[t.name,t.dataset_name,t.target,t.description,t.task_type,t.label_basis,t.input_description,t.limitations,...t._cats.map(k=>categories[k].name),...t._pops.map(k=>populations[k].name),...t._suites.map(k=>suites[k].name),...(protocols[t.id]??[]).map(p=>[p.name,p.adaptation,p.model_interface,p.split_rule,p.notes].join(" ")),...t._uses.map(u=>models[u.model_id].name)].join(" ").toLowerCase();
    return t;
  }).sort((a,b)=>a.name.localeCompare(b.name));
  const tasks=index(taskList);
  let state={}, limit=40, matching=[];
  const filterKeys=["q","application","population","capability","region","suite","evo","status"];
  const controls={q:"search",application:"application",population:"population",capability:"capability",region:"region",suite:"suite",evo:"evo",status:"status"};
  const option=(value,label)=>{const el=document.createElement("option");el.value=value;el.textContent=label;return el;};
  for(const dim of ["application","capability","region"]){for(const r of db.categories.filter(r=>r.dimension===dim).sort((a,b)=>a.name.localeCompare(b.name)))$(dim).append(option(r.id,r.name));}
  const popChildren=group(db.populations,"parent_id");
  const popOptions=(parent,depth=0)=>{for(const p of (popChildren[parent]??[]).sort((a,b)=>a.name.localeCompare(b.name))){$("population").append(option(p.id,"· ".repeat(depth)+p.name));popOptions(p.id,depth+1);}};
  popOptions(null);
  for(const s of [...db.evaluations].sort((a,b)=>a.name.localeCompare(b.name)))$("suite").append(option(s.id,s.name));
  $("updated").textContent=db.metadata.find(r=>r.key==="updated")?.value??"";

  function readState(){state=Object.fromEntries(new URLSearchParams(location.hash.slice(1)));state.view??="evaluations";if(!["evaluations","models","papers","data","audit"].includes(state.view))state.view="evaluations";for(const key of filterKeys)$(controls[key]).value=state[key]??"";limit=40;render();}
  function setState(next){const params=new URLSearchParams(Object.entries(next).filter(([,v])=>v));const hash=params.toString();if(location.hash.slice(1)!==hash)history.pushState(null,"","#"+hash);readState();}
  function fromControls(){const next={view:"evaluations",mode:state.mode};for(const key of filterKeys)next[key]=$(controls[key]).value;setState(next);}
  $("filters").addEventListener("submit",e=>e.preventDefault());
  $("filters").addEventListener("change",fromControls);
  $("search").addEventListener("input",()=>{const next={...state,q:$("search").value,task:""};history.replaceState(null,"","#"+new URLSearchParams(Object.entries(next).filter(([,v])=>v)));state=next;limit=40;renderEvaluations();});
  $("filters").addEventListener("reset",e=>{e.preventDefault();setState({view:"evaluations",mode:state.mode});});
  $("task-mode").addEventListener("click",()=>setState({...state,mode:"tasks",task:""}));
  $("suite-mode").addEventListener("click",()=>setState({...state,mode:"collections",task:""}));
  $("more").addEventListener("click",()=>{limit+=40;renderEvaluations();});
  window.addEventListener("hashchange",readState);
  document.addEventListener("click",e=>{const button=e.target.closest("button[data-task],button[data-suite]");if(button?.dataset.task)setState({view:"evaluations",task:button.dataset.task,mode:"tasks"});if(button?.dataset.suite)setState({view:"evaluations",suite:button.dataset.suite,mode:"tasks"});});

  function match(t){
    if(state.task&&t.id!==state.task)return false;
    if(state.q&&!state.q.toLowerCase().trim().split(/\s+/).every(word=>t._search.includes(word)))return false;
    for(const dim of ["application","capability","region"])if(state[dim]&&!t._cats.includes(state[dim]))return false;
    if(state.population&&!t._pops.includes(state.population))return false;
    if(state.suite&&!t._suites.includes(state.suite))return false;
    if(state.status&&state.status!==t.status)return false;
    if(state.evo==="original"&&!t._original||state.evo==="external"&&!t._external||state.evo==="both"&&!(t._original&&t._external))return false;
    return true;
  }
  function render(){
    for(const a of document.querySelectorAll("nav a")){if(a.dataset.view===state.view)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");}
    const titles={evaluations:"Evaluation catalogue",models:"Models",papers:"Papers and reports",data:"Data",audit:"Audit notes and evidence"};
    const descriptions={evaluations:"Tasks are organized by application, organism, model capability and functional region. A task is a dataset × prediction target; assay conditions and protocols are linked variants.",models:"Primary model scope and additional models included as evaluation sources. Model usage is attributed to the paper or release that documents it.",papers:"Primary papers, reports and benchmark sources. Versions, full-text inspection and released artifacts are separate records.",data:"The pretraining-data catalogue is work in progress. No entries have been defined.",audit:"Evidence levels, unresolved differences and the scope of the current audit. An inspected field does not establish that an entire task has been verified."};
    $("page-title").textContent=titles[state.view];$("page-description").textContent=descriptions[state.view];
    const pending=taskList.filter(t=>["registered","panel-pending"].includes(t.status)).length;
    $("coverage").textContent=`${db.models.filter(m=>m.scope==="primary").length} primary models · ${db.papers.length} paper/report sources · ${db.evaluations.length} collections · ${taskList.length} task/panel records (${pending} pending task audit or decomposition) · ${db.evidence.length} evidence records. Updated ${$("updated").textContent}.`;
    $("eval-view").hidden=state.view!=="evaluations";$("other-view").hidden=state.view==="evaluations";
    if(state.view==="evaluations")renderEvaluations();else renderOther();
  }
  function renderEvaluations(){
    matching=taskList.filter(match);
    const collectionMode=state.mode==="collections";
    $("task-mode").setAttribute("aria-pressed",String(!collectionMode));$("suite-mode").setAttribute("aria-pressed",String(collectionMode));
    if(collectionMode){
      const matchedIds=new Set(matching.map(t=>t.id));
      // With no task filters, also show registered sources with no decomposed tasks.
      const filtered=filterKeys.some(k=>state[k])||state.task;
      const visible=db.evaluations.filter(s=>(!filtered&&!state.suite)||state.suite===s.id||db.evaluation_tasks.some(r=>r.evaluation_id===s.id&&matchedIds.has(r.task_id))).sort((a,b)=>a.name.localeCompare(b.name));
      $("results").innerHTML=visible.map(s=>renderSuite(s,matching)).join("")||'<p class="empty">No matching collections.</p>';
      $("result-count").textContent=`${visible.length} collections · ${matching.length} matching task/panel records`;
      $("more").hidden=true;
    }else{
      $("results").innerHTML=matching.slice(0,limit).map(renderTaskSummary).join("")||'<p class="empty">No matching tasks. Missing metadata can exclude a task from a filtered view.</p>';
      $("result-count").textContent=`${matching.length} matching records · ${matching.filter(t=>t._original).length} with original Evo 2 usage`;
      $("more").hidden=matching.length<=limit;
      $("results").querySelectorAll("details.task").forEach(el=>el.addEventListener("toggle",()=>{if(el.open&&!el.dataset.loaded){el.querySelector(".detail-body").innerHTML=renderTaskDetail(tasks[el.dataset.id]);el.dataset.loaded="true";}}));
      if(state.task){const el=$("results").querySelector("details.task");if(el){el.open=true;el.querySelector(".detail-body").innerHTML=renderTaskDetail(tasks[el.dataset.id]);el.dataset.loaded="true";}}
    }
  }
  function renderTaskSummary(t){
    const pending=["registered","panel-pending"].includes(t.status);
    const names=(taskPops[t.id]??[]).map(p=>populations[p.population_id].name);
    return `<details class="task" data-id="${esc(t.id)}"><summary><div class="row-top"><span class="task-name">${esc(t.name)}</span><span class="row-meta">${esc(t.task_type)} · ${esc(statusNames[t.status]??t.status)}</span></div><p class="row-description">${esc(t.dataset_name)} · ${esc(t.target)}</p><div class="tags">${tags(t._suites.map(k=>suites[k].name))}${tags(names)}${t._original?tags(["Evo 2: original paper"],"evo"):""}${t._external?tags(["Evo 2: external evaluation"],"evo"):""}${pending?tags(["Audit incomplete"],"pending"):""}</div></summary><div class="detail-body"></div></details>`;
  }
  function fact(label,value,citation=""){return `<dt>${esc(label)}</dt><dd>${esc(value||"Not established in inspected sources")}${citation}</dd>`;}
  function renderTaskDetail(t){
    const ps=protocols[t.id]??[],vs=variants[t.id]??[],ns=counts[t.id]??[],us=uses[t.id]??[];
    let html=`<p>${esc(t.description)}${cite(t.evidence_id)}</p><dl class="facts">${fact("Dataset",t.dataset_name,fieldEvidence(t.id,"dataset_name",t.evidence_id))}${fact("Target",t.target,cite(t.evidence_id))}${fact("Input",t.input_description,fieldEvidence(t.id,"input_description",t.evidence_id))}${fact("Output",t.output_description)}${fact("Label basis",t.label_basis,cite(t.evidence_id))}</dl>`;
    if(t.limitations)html+=`<p class="note">${esc(t.limitations)}${cite(t.evidence_id)}</p>`;
    html+='<h4>Classification</h4><dl class="facts">';
    for(const dim of ["application","capability","region"]){const rs=(taskCategories[t.id]??[]).filter(r=>categories[r.category_id].dimension===dim);html+=`<dt>${{application:"Application",capability:"Model capability",region:"Functional region"}[dim]}</dt><dd>${rs.length?rs.map(r=>`${esc(categories[r.category_id].name)} <span class="muted">(${esc(r.relation)}; editorial mapping)</span>${cite(r.evidence_id)}`).join("<br>"):"Not assigned"}</dd>`;}
    html+='<dt>Organism / context</dt><dd>'+((taskPops[t.id]??[]).map(p=>`${esc(populations[p.population_id].name)} — ${esc(p.relation)}. ${esc(p.coverage)}${cite(p.evidence_id)}`).join("<br>")||"Not established; not inferred from a gene-name abbreviation.")+'</dd></dl>';
    if(ps.length)html+='<h4>Evaluation protocols</h4>'+ps.map(p=>renderProtocol(p)).join("");else html+='<p class="note">Protocol audit pending. No adaptation method or split is assumed.</p>';
    if(ns.length){html+='<h4>Scale and released-file counts</h4><p class="muted">Reported totals, artifact rows and final scored examples may differ. Counts below are not additive; variants and filtering qualifiers matter.</p><div class="table-wrap"><table><thead><tr><th>Partition / variant</th><th>Count</th><th>Unit</th><th>Basis and qualification</th></tr></thead><tbody>'+ns.map(n=>`<tr><td>${esc(n.split)}${n.variant_id?'<br><span class="muted">'+esc(vs.find(v=>v.id===n.variant_id)?.name??n.variant_id)+'</span>':""}${n.protocol_id?'<br><span class="muted">'+esc(ps.find(p=>p.id===n.protocol_id)?.name??n.protocol_id)+'</span>':""}</td><td class="count-number">${Number(n.value).toLocaleString()}</td><td>${esc(n.unit)}</td><td>${esc(n.method)}. ${esc(n.qualifier)}${cite(n.evidence_id)}</td></tr>`).join("")+'</tbody></table></div>';}
    if(vs.length)html+='<details><summary>'+vs.length+' linked dataset / target / condition variants</summary><div class="table-wrap"><table><thead><tr><th>Variant</th><th>Context / input</th><th>Revision / notes</th></tr></thead><tbody>'+vs.map(v=>`<tr><td>${esc(v.name)}${cite(v.evidence_id)}</td><td>${esc(v.context)}${v.input_length?'<br>'+esc(v.input_length):""}${v.target_count?'<br>'+v.target_count+' '+esc(v.target_unit):""}</td><td>${v.dataset_revision?'<code>'+esc(v.dataset_revision)+'</code><br>':""}${esc(v.notes)}</td></tr>`).join("")+'</tbody></table></div></details>';
    html+='<h4>Documented model usage</h4>'+(us.length?'<div class="table-wrap"><table><thead><tr><th>Model</th><th>Attribution</th><th>Source / protocol</th></tr></thead><tbody>'+us.map(u=>`<tr><td>${esc(models[u.model_id].name)}</td><td>${esc(u.provenance.replaceAll("-"," "))}</td><td>${esc(papers[u.paper_id]?.title)}${cite(u.evidence_id)}${u.protocol_id?'<br>'+esc(ps.find(p=>p.id===u.protocol_id)?.name??u.protocol_id):""}${u.note?'<br><span class="muted">'+esc(u.note)+'</span>':""}</td></tr>`).join("")+'</tbody></table></div>':'<p class="muted">No model–task association has yet been established. This does not assert that the task was unused.</p>');
    if(!t._original)html+='<p class="muted">Original Evo 2 use is not documented for this record in the current audit. This is not a verified absence claim.</p>';
    const fs=db.findings.filter(f=>f.task_id===t.id);if(fs.length)html+='<h4>Audit findings</h4>'+fs.map(f=>`<p class="finding note">${esc(f.description)}${cite(f.evidence_id)}</p>`).join("");
    const ids=new Set([t.evidence_id,...ps.map(p=>p.source_evidence_id),...ns.map(n=>n.evidence_id),...vs.map(v=>v.evidence_id),...us.map(u=>u.evidence_id),...fs.map(f=>f.evidence_id),...(fields[t.id]??[]).map(f=>f.evidence_id)]);
    html+=renderReferences([...ids]);
    html+=`<p class="muted">Record: <code>${esc(t.id)}</code> · <a href="#view=evaluations&amp;task=${encodeURIComponent(t.id)}">Permanent task link</a></p>`;
    return html;
  }
  function renderProtocol(p){
    const ms=(metricLinks[p.id]??[]).map(m=>metrics[m.metric_id].name+(m.is_primary?" (primary)":"")+" — "+m.aggregation).join("; ");
    const embeds=p.requires_embeddings===null?"Not established / protocol-dependent":p.requires_embeddings?"Required":"Not required by this protocol";
    return `<article class="protocol"><h4>${esc(p.name)}${cite(p.source_evidence_id)}</h4><dl class="facts">${fact("Adaptation",p.adaptation)}${fact("Model interface",p.model_interface,fieldEvidence(p.id,"model_interface",p.source_evidence_id))}${fact("Embeddings",embeds)}${fact("Fitted component",p.fitted_component??(p.adaptation.includes("zero-shot")?"None in this protocol":"Not established"))}${fact("Partition rule",p.split_rule,fieldEvidence(p.id,"split_rule",p.source_evidence_id))}${fact("Split unit",p.split_unit)}${fact("Selection",p.selection)}${fact("Metrics",ms||"Metric transcription / scorer audit pending",fieldEvidence(p.id,"metrics",p.source_evidence_id))}</dl>${p.notes?'<p>'+esc(p.notes)+'</p>':""}</article>`;
  }
  function renderReferences(ids){return `<details class="references"><summary>Evidence and source locators (${ids.length})</summary><ol>${ids.map(id=>{const e=evidence[id];if(!e)return"";const s=sources[e.source_id];return `<li value="${e.number}"><a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(s.title)}</a> · ${esc(e.basis)}<br>${esc(e.locator)}. ${esc(e.statement)}<br><span class="muted">${esc(s.version??"")} · inspected ${esc(e.inspected)}${s.sha256?' · SHA-256 <code>'+esc(s.sha256)+'</code>':""}</span></li>`;}).join("")}</ol></details>`;}
  function renderSuite(s,matched){
    const links=db.evaluation_tasks.filter(r=>r.evaluation_id===s.id),all=links.map(r=>tasks[r.task_id]),subset=all.filter(t=>matched.some(m=>m.id===t.id));
    const classes=dim=>[...new Set(all.flatMap(t=>categoryNames(t,dim)))].sort();
    const pops=[...new Set(all.flatMap(t=>(taskPops[t.id]??[]).map(p=>populations[p.population_id].name)))].sort();
    return `<article class="collection"><h3>${esc(s.name)} ${tags([s.status],s.status==="registered"?"pending":"")}</h3><p>${esc(s.description)}${cite(s.evidence_id)}</p><p class="muted">${links.length} linked task/panel records · ${all.filter(t=>t._original).length} with documented original Evo 2 use · ${subset.length} match current filters.</p><dl class="facts">${fact("Applications",classes("application").join("; "))}${fact("Capabilities",classes("capability").join("; "))}${fact("Functional regions",classes("region").join("; "))}${fact("Organisms / contexts",pops.join("; "))}</dl><p>${esc(s.scope_note)}</p>${s.notes?'<p class="note">'+esc(s.notes)+cite(s.evidence_id)+'</p>':""}<p><button data-suite="${esc(s.id)}" type="button" class="secondary">View tasks</button></p><details><summary>Constituent tasks and source-specific notes</summary><ul>${links.map(r=>`<li><a href="#view=evaluations&amp;task=${encodeURIComponent(r.task_id)}">${esc(tasks[r.task_id].name)}</a>${r.note?' — '+esc(r.note):""}${cite(r.evidence_id)}</li>`).join("")||'<li>Task decomposition pending.</li>'}</ul></details><p class="muted">Collection classifications above are unions of constituent task assignments; they do not apply to every task.</p></article>`;
  }
  function renderOther(){
    if(state.view==="data"){$("other-view").innerHTML='<p class="section-note">Work in progress. Evaluation datasets are documented within their task records. A separate pretraining-data catalogue has not yet been specified.</p>';return;}
    if(state.view==="models"){
      $("other-view").innerHTML=["primary","evaluation-source"].map(scope=>'<h2>'+(scope==="primary"?"Primary model scope":"Additional evaluation sources")+'</h2>'+db.models.filter(m=>m.scope===scope).map(m=>{
        const assoc=db.model_evaluations.filter(u=>u.model_id===m.id),original=[...new Set(assoc.filter(u=>["original-paper","original-release"].includes(u.provenance)).map(u=>u.task_id))],external=[...new Set(assoc.filter(u=>u.provenance==="external-evaluation").map(u=>u.task_id))];
        const properties=db.model_properties.filter(p=>p.model_id===m.id);
        const propertyTable=properties.length?'<details class="model-properties" open><summary>Corpus, architecture and evaluation procedures</summary><div class="table-wrap"><table><thead><tr><th>Property</th><th>Evidence and limitations</th></tr></thead><tbody>'+properties.map(p=>`<tr><td>${esc(p.name)}<br><span class="muted">${esc(p.category)} · ${esc(p.status)}${p.variant?' · '+esc(p.variant):''}</span></td><td>${esc(p.value)}${citations([p.evidence_id,...(fields[p.id]??[]).map(f=>f.evidence_id)])}${p.notes?'<p class="muted">'+esc(p.notes)+'</p>':''}</td></tr>`).join('')+'</tbody></table></div></details>':'';
        return `<article class="record" id="model-${esc(m.id)}"><h2>${esc(m.name)}</h2><p>${esc(m.description)}${cite(m.evidence_id)}</p>${m.notes?'<p class="note">'+esc(m.notes)+citations((fields[m.id]??[]).map(f=>f.evidence_id))+'</p>':""}<p><a href="${esc(sources[papers[m.paper_id].source_id].url)}">${esc(papers[m.paper_id].title)}</a></p>${propertyTable}<p class="muted">${original.length} documented original-source task/panel associations · ${external.length} external-evaluation associations. Incomplete audits can undercount usage.</p><details><summary>Task associations by provenance</summary><ul>${[...new Set(assoc.map(u=>u.task_id))].map(id=>`<li><a href="#view=evaluations&amp;task=${encodeURIComponent(id)}">${esc(tasks[id].name)}</a> — ${esc([...new Set(assoc.filter(u=>u.task_id===id).map(u=>u.provenance))].join("; "))}</li>`).join("")||'<li>Associations pending; source remains in scope.</li>'}</ul></details></article>`;
      }).join("")).join("");return;
    }
    if(state.view==="papers"){
      $("other-view").innerHTML='<p class="section-note">Carbon-X has official release documentation; AIDO.DNA2 has an official technical web report. Additional source papers may be registered before their full text is inspected; availability is not inferred from a title or DOI.</p>'+[...db.papers].sort((a,b)=>(b.year-a.year)||a.title.localeCompare(b.title)).map(p=>{const s=sources[p.source_id];return `<article class="record"><h2><a href="${esc(s.url)}">${esc(p.title)}</a></h2><p>${esc(p.year)} · ${esc(p.status)} · ${esc(p.scope.replaceAll("-"," "))}</p><p class="muted">${esc(s.version??"")} · ${s.local_path?"Cached full-text/documentation representation inspected":"Source registered; full-text inspection not recorded here"}</p>${p.notes?'<p>'+esc(p.notes)+'</p>':""}<details><summary>Source metadata</summary><p><code>${esc(p.id)}</code> · ${esc(s.kind)} · retrieved ${esc(s.retrieved)}</p>${s.sha256?'<p>Cached representation SHA-256: <code>'+esc(s.sha256)+'</code></p>':""}<p>${esc(s.notes??"")}</p></details></article>`;}).join("");return;
    }
    const n=status=>taskList.filter(t=>t.status===status).length;
    $("other-view").innerHTML=`<h2>Audit status</h2><dl class="legend"><dt>Selected artifacts audited (${n("artifact-audited")})</dt><dd>Selected pinned files were read and counted. The evidence states which fields were checked. This does not certify label validity, pretraining exclusion or every protocol.</dd><dt>Paper / protocol audit (${n("paper-audited")})</dt><dd>Paper, methods or released procedure supports a task definition; complete raw-data and split verification is pending.</dd><dt>Registered (${n("registered")})</dt><dd>Source/manifest entry retained in scope; individual target and artifact audit incomplete.</dd><dt>Composite panel (${n("panel-pending")})</dt><dd>Paper reports an assay collection. Individual dataset × target decomposition remains pending; do not count it as one fully specified task.</dd></dl><h2>Interpretation</h2><p class="section-note">Evidence is attached to fields, classifications, protocols, counts and model usage. Application mappings are editorial. Long input, a species label, a chromosome split and a zero-shot score answer different questions; none alone establishes pretraining exclusion or biological transfer. Missing model usage is unknown rather than a verified negative.</p><p class="section-note">Measured counts come from pinned public files. A genome row can contain thousands of gene labels; a split file can precede eligibility filters. Repeated targets, variants and suite membership must not be summed as independent examples.</p><h2>Capability definitions</h2><dl class="legend">${db.categories.filter(r=>r.dimension==="capability").map(r=>`<dt>${esc(r.name)}</dt><dd>${esc(r.definition)} ${esc(r.accommodation)}</dd>`).join("")}</dl><h2>Findings and work remaining</h2>${db.findings.map(f=>`<article class="record"><p><span class="badge ${f.severity==="discrepancy"?"pending":""}">${esc(f.severity)}</span> ${esc(f.description)}${cite(f.evidence_id)}</p>${f.task_id?'<p><a href="#view=evaluations&amp;task='+encodeURIComponent(f.task_id)+'">'+esc(tasks[f.task_id].name)+'</a></p>':f.evaluation_id?'<p><a href="#view=evaluations&amp;mode=collections&amp;suite='+encodeURIComponent(f.evaluation_id)+'">'+esc(suites[f.evaluation_id].name)+'</a></p>':""}</article>`).join("")}<h2>Evidence registry</h2>${renderReferences(db.evidence.map(e=>e.id))}`;
  }
  $("export").addEventListener("click",()=>{
    const quote=s=>'"'+String(s??"").replaceAll('"','""')+'"';
    const rows=[["id","task","dataset","target","type","audit_status","collections","applications","organisms","capabilities","regions","evo2_original","evo2_external","source"]];
    for(const t of matching)rows.push([t.id,t.name,t.dataset_name,t.target,t.task_type,t.status,t._suites.map(k=>suites[k].name).join("; "),categoryNames(t,"application").join("; "),(taskPops[t.id]??[]).map(p=>populations[p.population_id].name).join("; "),categoryNames(t,"capability").join("; "),categoryNames(t,"region").join("; "),t._original?"documented":"not established",t._external?"documented":"not established",evidence[t.evidence_id].url]);
    const url=URL.createObjectURL(new Blob([rows.map(r=>r.map(quote).join(",")).join("\r\n")],{type:"text/csv;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download="marin-glm-tasks.csv";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  readState();
})();
