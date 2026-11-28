"""Exercise the compiled single-page interface locally without external requests."""
from pathlib import Path
import csv
import io
import json
import math
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/site-data.json').read_text())
TASKS={t['id']:t for t in DATA['tasks']}
TOTAL=len(TASKS)
OUTPUTS={t['task_id']:t['category_id'] for t in DATA['task_outputs']}
ALIASES={r['id']:r for r in DATA['task_redirects']}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1920,'height':1280})
    errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
    url=(ROOT/'index.html').as_uri()
    def visit(fragment=''):
        page.goto(url+fragment)
        page.wait_for_function('document.querySelector("nav a[aria-current=page]") !== null')
    def rows():return page.locator('.compact-task-row').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
    def click_mode(mode):page.locator('#'+{'coverage':'coverage-mode','tasks':'task-mode','collections':'suite-mode'}[mode]).click()
    def reset():
        if page.locator('#clear-filters').is_enabled():page.locator('#clear-filters').click()
    def all_rows():
        page.locator('#page-size').select_option('250')
        result=[]
        while True:
            result+=rows()
            if page.locator('#next-page').is_disabled():break
            page.locator('#next-page').click()
        return result
    visit()
    assert page.locator('#page-title').inner_text()=='Evaluations'
    assert page.locator('#coverage-mode').get_attribute('aria-pressed')=='true'
    assert page.locator('#status').count()==0
    assert page.locator('#evo').count()==0
    assert page.locator('.primary-filters input,.primary-filters select').evaluate_all('(els)=>els.map(e=>e.id)')==['search','suite','population','region']
    assert not page.locator('#more-filters').evaluate('e=>e.open')
    assert page.locator('#active-filters').is_hidden()
    assert page.locator('#clear-filters').is_disabled()
    assert page.locator('#filters #export').count()==0 and page.locator('#table-tools #export').count()==1
    positions=page.locator('.primary-filters input,.primary-filters select').evaluate_all('(els)=>els.map(e=>e.getBoundingClientRect().top)')
    assert max(positions)-min(positions)<1
    assert page.locator('#filters').bounding_box()['height']<125
    # Retired shared links no longer retain an invisible provenance constraint.
    visit('#view=evaluations&evo=original')
    assert 'evo=' not in page.url and f'{TOTAL} matching records' in page.locator('#result-count').inner_text()
    assert page.locator('.coverage-feature').count()==len(DATA['coverage']['groupedFeatures'])
    # Density must come from layout, without dropping task markers.
    assert page.locator('.coverage-matrix thead').bounding_box()['height']<100
    assert page.locator('.coverage-marks').first.evaluate('(e)=>getComputedStyle(e).gridTemplateColumns.split(" ").length')>5
    assert page.locator('.tasks-table thead th').count()==6
    assert 'Evo 2 use' not in page.locator('.tasks-table thead').inner_text()
    assert page.locator('#output option[value="output-unresolved"]').count()==0
    assert page.evaluate('new Set([...document.querySelectorAll(".coverage-dot")].map(e=>e.dataset.coverageTask)).size')==TOTAL
    assert f'{TOTAL} matching records' in page.locator('#result-count').inner_text()
    assert len(rows())==100 and page.locator('#next-page').is_enabled()
    assert page.locator('.coverage-scroll').evaluate('(e)=>e.clientHeight')>=900
    shape_text=page.locator('.coverage-legends').inner_text()
    labels=['Evo 1 / Evo 2','RNAGym / ProteinGym / TraitGym','PlantCAD2 / GeneCAD / Botanic-1']
    assert all(label in shape_text for label in labels)
    assert [shape_text.index(label) for label in labels]==sorted(shape_text.index(label) for label in labels)
    assert 'Reported; task not yet mapped' not in page.locator('body').inner_text()
    assert page.locator('.coverage-dot[data-coverage-task="evo-dms-blat-firnberg"][data-feature="coding-sequence"]').count()>0
    assert page.locator('.coverage-dot[data-coverage-task="genosm-gene-class"][data-feature="coding-sequence"]').count()==0
    assert page.locator('.coverage-dot[data-coverage-task="carbon-triplet"][data-feature="coding-sequence"]').count()==0
    structure=page.locator('.coverage-dot[data-coverage-task="spliceai2-top-transcript"]')
    assert structure.count()==1 and structure.get_attribute('data-feature')=='transcript-structures'
    assert page.locator('.coverage-dot[data-coverage-task="evo-exon-intron"][data-feature="gene-structures"]').count()==0
    page.screenshot(path='/tmp/marin-glm-coverage.png')
    # Pointer and keyboard tooltips identify the actual source, not just shape.
    dot=page.locator('[data-coverage-task="ntv3-annotation-gene"]').first
    dot.hover();page.wait_for_timeout(150)
    box=dot.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
    page.wait_for_function('!document.querySelector(".coverage-tooltip").hidden')
    tooltip=page.locator('.coverage-tooltip').inner_text()
    assert all(word in tooltip for word in ['Evaluation','Paper','Models','NTv3'])
    page.screenshot(path='/tmp/marin-glm-tooltip.png')
    dot.focus();page.wait_for_function('!document.querySelector(".coverage-tooltip").hidden')
    assert dot.get_attribute('aria-describedby')=='coverage-task-tooltip'
    # Output filtering stays composed through every view.
    page.locator('#more-filters>summary').click()
    page.select_option('#output','output-dense-labels')
    assert page.locator('#more-filter-count').inner_text()=='(1 active)'
    assert 'Scored output:' in page.locator('#active-filters').inner_text()
    page.locator('#more-filters>summary').click()
    assert not page.locator('#more-filters').evaluate('e=>e.open')
    click_mode('tasks')
    assert set(all_rows())=={tid for tid,form in OUTPUTS.items() if form=='output-dense-labels'}
    click_mode('collections');assert page.locator('#output').input_value()=='output-dense-labels'
    click_mode('coverage');assert page.locator('#output').input_value()=='output-dense-labels'
    page.locator('.coverage-feature-detail').select_option('individual')
    assert page.locator('.coverage-dot[data-coverage-task="genecad-busco"]').count()==0
    reset();click_mode('tasks')
    assert not page.locator('#more-filters').evaluate('e=>e.open')
    assert page.locator('#more-filter-count').is_hidden() and page.locator('#active-filters').is_hidden()
    # Shared links reveal secondary filters and preserve them in every view.
    visit('#view=evaluations&mode=tasks&output=output-dense-labels')
    assert page.locator('#more-filters').evaluate('e=>e.open')
    assert page.locator('#output').input_value()=='output-dense-labels'
    page.locator('#more-filters>summary').click()
    page.locator('[data-clear-filter="output"]').click()
    assert page.locator('#output').input_value()=='' and page.locator('#more-filter-count').is_hidden()
    reset()
    # Clearing filters retains display preferences; choose 100 for pagination.
    page.locator('#page-size').select_option('100')
    # Sorting/pagination/detail expansion and resource labels.
    first=rows();page.locator('#next-page').click();second=rows()
    assert len(second)==100 and not set(first)&set(second)
    assert page.locator('#page-number').inner_text()==f'2 / {math.ceil(TOTAL/100)}'
    page.locator('#previous-page').click();assert rows()==first
    page.locator('#page-size').select_option('250');assert len(rows())==250
    page.locator('[data-sort="name"]').click();assert rows()[0]!=first[0]
    assert page.locator('th[aria-sort="descending"]').count()==1
    page.locator('.task-toggle').first.click()
    assert page.locator('.task-detail-row:not([hidden]) .citation').count()>0
    assert 'Source review completed' in page.locator('.task-detail-row:not([hidden])').inner_text()
    page.locator('.task-toggle[aria-expanded=true]').click()
    assert page.locator('.task-detail-row:not([hidden])').count()==0
    page.screenshot(path='/tmp/marin-glm-tasks.png')
    reset();page.select_option('#suite','gpn-evals');page.select_option('#population','plants')
    expected=set(rows());assert expected
    for mode in ['coverage','collections','tasks']:
        click_mode(mode);assert page.locator('#population').input_value()=='plants'
    assert set(rows())==expected
    reset();click_mode('coverage');page.select_option('#population','human')
    assert page.locator('[data-taxon]').count()==1
    assert page.locator('[data-taxon]').get_attribute('data-taxon').endswith('sp-9606')
    page.locator('.coverage-feature-detail').select_option('individual');page.select_option('#region','cds')
    assert page.locator('.coverage-feature').count()==1 and page.locator('.coverage-feature').inner_text()=='CDS'
    reset();page.select_option('#population','phages')
    assert page.locator('.coverage-dot[data-coverage-task="evo-phage-essential"]').count()>0
    reset();page.locator('.coverage-feature-detail').select_option('individual')
    dots=page.locator('.coverage-dot[data-row="pseudomonadota-sp-562"][data-feature="cds"]')
    expected=set(dots.evaluate_all('(els)=>els.map(e=>e.dataset.coverageTask)'))
    dots.first.click();assert set(rows())==expected
    assert page.locator('[data-clear-filter="cellRow"]').count()==1
    click_mode('tasks');assert set(rows())==expected
    page.reload();page.wait_for_selector('.compact-task-row')
    assert set(rows())==expected and page.locator('.task-detail-row:not([hidden])').count()==1
    page.locator('[data-clear-filter="cellRow"]').click();reset()
    with page.expect_download() as info:page.locator('#export').click()
    exported=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text())))
    assert len(exported)==TOTAL and {r['id'] for r in exported}==set(TASKS)
    assert all(r['scored_output'] and r['scoring_unit'] and r['source_review_date'] for r in exported)
    assert {'data_resources','source_limits','evidence_level'}<=set(exported[0])
    assert all('not established' not in r['evo2_original'] and 'not established' not in r['evo2_external'] for r in exported)
    assert sum(r['evo2_original']=='listed in original-paper inventory' for r in exported)==83
    assert next(r for r in exported if r['id']=='nabench-fuente-selection')['evo2_external']=='collection participant; assay execution not specified'
    # Direct links, datasets, source limits and retired IDs remain usable.
    for task in ['bacbench-essential','nt-revised-enhancers_types','nt-original-H3','gpn-rvat','traitgym-mendelian','bend-opensplice','deepstarr-dev','aido2-clinvar-snv','genosm-bgc-types','plantcad2-tis_recovery','plantcad2-ft-cell_type_specific_acr','genecad-cds-transcript','spliceai2-top-transcript','deepd-human-routing-cds','carbon-triplet','evo-sae-prophage']:
        visit('#view=evaluations&task='+task)
        assert rows()==[task]
        text=page.locator('.task-detail-row:not([hidden])').inner_text()
        assert 'Output and scoring scope' in text and 'Documented model usage' in text
        assert 'Source review completed' in text and 'pending' not in text.lower()
        if task=='spliceai2-top-transcript':assert all(v in text for v in ['352','TSS/TES','human-only'])
    visit('#view=evaluations&task=traitgym-mendelian')
    assert page.locator('.resource-table a[href*="huggingface.co/datasets/songlab/TraitGym"]').count()>0
    visit('#view=evaluations&task=deepd-bacterial-fitness')
    assert 'Source limits' in page.locator('.task-detail-row:not([hidden])').inner_text()
    for old in ['geneb-katarinagresova-genomic-benchmarks-human-nontata-promoters','generator2-recovery','gue-H3','geneb-leannmlindsey-gue-emp-h4']:
        if old not in ALIASES:continue
        visit('#view=evaluations&task='+old)
        assert rows()==[ALIASES[old]['replacement_task_id']]
    visit('#view=evaluations&status=panel-pending')
    assert f'{TOTAL} matching records' in page.locator('#result-count').inner_text()
    assert page.locator('#active-filters').is_hidden()
    # Native taxonomy remains separate from the compact display hierarchy.
    visit()
    for detail in ['allSpecies','clade','species']:
        page.locator('.coverage-detail').select_option(detail)
        assert page.evaluate('new Set([...document.querySelectorAll(".coverage-dot")].map(e=>e.dataset.coverageTask)).size')==TOTAL
    nodes=page.locator('.coverage-division').evaluate_all('(els)=>els.map(e=>({id:e.dataset.node,parent:e.dataset.displayParent}))')
    lookup={r['id']:r for r in nodes}
    assert lookup['bacillota']['parent']=='bacteria'
    assert lookup['poaceae']['parent']=='monocots'
    assert lookup['animals']['parent']=='eukaryota'
    assert not {'obazoa','opisthokonta','bilateria','deuterostomia'}&set(lookup)
    # Broad groups remain identifiable after their parent headings scroll away.
    assert 'Cellular life' not in page.locator('.coverage-matrix tbody').inner_text()
    assert page.locator('[data-node="eukaryota"].coverage-domain').count()==1
    assert page.locator('[data-node="plants"].coverage-major').count()==1
    assert page.locator('[data-node="plants"] .coverage-branch').count()==0
    page.locator('[data-jump="plants"]').click()
    page.wait_for_function('document.querySelector(".coverage-lineage").textContent==="Eukaryota › Green plants"')
    page.locator('.coverage-scroll').evaluate('(e)=>e.scrollTop+=180')
    page.wait_for_timeout(100)
    assert page.locator('.coverage-lineage').inner_text()=='Eukaryota › Green plants'
    assert page.locator('[data-node="plants"]').bounding_box()['y']<page.locator('.coverage-scroll').bounding_box()['y']
    page.locator('[data-jump="bacteria"]').click()
    page.wait_for_function('document.querySelector(".coverage-lineage").textContent.includes("Bacteria")')
    assert 'Eukaryota' not in page.locator('.coverage-lineage').inner_text()
    # The matrix permits native scroll chaining to the page at either boundary.
    assert page.locator('.coverage-scroll').evaluate('(e)=>getComputedStyle(e).overscrollBehaviorY')=='auto'
    page.locator('.coverage-expand').click();assert page.locator('body').evaluate('(e)=>e.classList.contains("matrix-expanded")')
    page.keyboard.press('Escape');assert not page.locator('body').evaluate('(e)=>e.classList.contains("matrix-expanded")')
    for view in ['projects','models','papers','audit']:
        visit('#view='+view);assert page.locator('#other-view').inner_text().strip()
    # Compact table is intentionally horizontally scrollable on narrow screens;
    # it must not force the whole document wider than the viewport.
    page.set_viewport_size({'width':390,'height':844});visit();click_mode('tasks')
    assert page.evaluate('document.documentElement.scrollWidth')<=390
    assert page.locator('.compact-task-row').count()==100
    assert page.locator('.compact-task-row').evaluate_all('(els)=>Math.max(...els.map(e=>e.getBoundingClientRect().height))')<150
    page.screenshot(path='/tmp/marin-glm-mobile.png')
    assert not errors,errors
    assert not requests,requests
    browser.close()
print('Browser checks passed: coverage, filters, sources, aliases, CSV, keyboard, taxonomy and mobile layout.')
