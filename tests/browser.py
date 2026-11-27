"""Exercise the single-page interface locally, with no external requests."""
from pathlib import Path
import csv
import io
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
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
    visit()
    assert page.locator('#page-title').inner_text()=='Evaluations'
    assert page.locator('#coverage-mode').get_attribute('aria-pressed')=='true'
    assert page.locator('.coverage-dot').count()==879
    assert page.locator('[data-taxon]').count()==48
    assert page.locator('.coverage-division').count()==30
    assert '513 matching records' in page.locator('#result-count').inner_text()
    assert len(rows())==100
    assert page.locator('#next-page').is_enabled()
    assert page.evaluate('new Set([...document.querySelectorAll(".coverage-dot")].map(e=>e.dataset.coverageTask)).size')==513
    assert page.locator('.coverage-scroll').evaluate('(e)=>e.clientHeight')>=900
    page.screenshot(path='/tmp/marin-glm-coverage.png')
    # Compact browsing, pagination, sorting and lazy detail expansion.
    click_mode('tasks');first=rows()
    page.locator('#next-page').click();second=rows()
    assert len(second)==100 and not set(first)&set(second)
    assert page.locator('#page-number').inner_text()=='2 / 6'
    page.locator('#previous-page').click();assert rows()==first
    page.locator('#page-size').select_option('250');assert len(rows())==250
    page.locator('[data-sort="name"]').click();assert rows()[0]!=first[0]
    assert page.locator('th[aria-sort="descending"]').count()==1
    page.locator('#page-size').select_option('100')
    page.locator('.task-toggle').first.click()
    assert page.locator('.task-detail-row:not([hidden]) .citation').count()>0
    assert 'Coverage placement and evidence' in page.locator('.task-detail-row:not([hidden])').inner_text()
    page.locator('.task-toggle[aria-expanded=true]').click()
    assert page.locator('.task-detail-row:not([hidden])').count()==0
    page.screenshot(path='/tmp/marin-glm-tasks.png')
    # Existing filters compose and survive all display modes.
    page.select_option('#suite','gpn-evals')
    assert '21 matching records' in page.locator('#result-count').inner_text()
    page.select_option('#population','plants')
    assert '1 matching records' in page.locator('#result-count').inner_text()
    click_mode('coverage')
    assert page.locator('#population').input_value()=='plants'
    assert '1 matching records' in page.locator('#result-count').inner_text()
    click_mode('collections')
    assert page.locator('#population').input_value()=='plants'
    assert page.locator('.collection-toggle').count()>=1
    page.locator('button[type=reset]').click();click_mode('coverage')
    # Species filters restrict associations, not merely multi-species task IDs.
    page.select_option('#population','human')
    assert page.locator('[data-taxon]').count()==1
    assert page.locator('[data-taxon]').get_attribute('data-taxon')=='mammalia-sp-9606'
    assert '181 matching records' in page.locator('#result-count').inner_text()
    page.select_option('#region','cds')
    assert page.locator('.coverage-feature').count()==1
    assert page.locator('.coverage-feature').inner_text()=='CDS'
    assert '37 matching records' in page.locator('#result-count').inner_text()
    page.locator('button[type=reset]').click()
    page.select_option('#population','phages')
    assert page.locator('.coverage-dot[data-coverage-task="evo-phage-essential"]').count()>0
    page.locator('button[type=reset]').click()
    page.select_option('#population','bryophytes')
    assert set(page.locator('[data-taxon]').evaluate_all('(els)=>els.map(e=>e.dataset.taxon)'))=={'bryophytes-sp-3218','bryophytes-sp-3197'}
    page.locator('button[type=reset]').click()
    # Cell selection narrows the table and persists through mode changes/reload.
    dots=page.locator('.coverage-dot[data-row="pseudomonadota-sp-562"][data-feature="cds"]')
    expected=set(dots.evaluate_all('(els)=>els.map(e=>e.dataset.coverageTask)'))
    dots.first.click()
    assert set(rows())==expected
    assert page.locator('[data-clear-filter="cellRow"]').count()==1
    click_mode('tasks');assert set(rows())==expected
    page.reload();page.wait_for_selector('.compact-task-row')
    assert set(rows())==expected and page.locator('.task-detail-row:not([hidden])').count()==1
    page.locator('[data-clear-filter="cellRow"]').click()
    assert '513 matching records' in page.locator('#result-count').inner_text()
    # CSV exports every matching task, including tasks outside the visible page.
    with page.expect_download() as info:page.locator('#export').click()
    exported=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text())))
    assert len(exported)==513 and len({r['id'] for r in exported})==513
    for task in ['bacbench-essential','nt-revised-enhancers_types','gue-H3','gpn-rvat','gpn-annotation','traitgym-mendelian','bend-opensplice','deepstarr-dev','aido2-clinvar-snv','genosm-bgc-types','genosm-crc','plantcad2-tis_recovery','plantcad2-potato-gerp','plantcad2-ft-cell_type_specific_acr','genecad-cds-transcript','genecad-legacy-transcript']:
        visit('#view=evaluations&task='+task)
        assert len(rows())==1 and page.locator('.task-detail-row:not([hidden])').count()==1
        assert page.locator('.task-detail-row:not([hidden]) .citation').count()>0
        assert 'Documented model usage' in page.locator('.task-detail-row:not([hidden])').inner_text()
    visit('#view=evaluations&mode=tasks&q=ceno&capability=generation')
    assert '3 matching records' in page.locator('#result-count').inner_text()
    page.locator('[data-clear-filter="q"]').click()
    assert '20 matching records' in page.locator('#result-count').inner_text()
    visit('#view=evaluations&mode=tasks&suite=genecad&capability=dense-annotation')
    assert '15 matching records' in page.locator('#result-count').inner_text()
    visit('#view=evaluations&task=deepd-annotation-human')
    assert '6 matching records' in page.locator('#result-count').inner_text()
    visit('#view=evaluations&mode=tasks&capability=unconditional-generation')
    assert '2 matching records' in page.locator('#result-count').inner_text()
    visit('#view=evaluations&mode=tasks&project=dart&evo=original')
    assert len(rows())==4
    assert all('Original' in s for s in page.locator('.provenance').all_text_contents())
    visit('#view=evaluations&mode=collections&project=lrb')
    assert page.locator('.collection-toggle').count()==1
    page.locator('.collection-toggle').click()
    assert 'decomposition' in page.locator('.collection').inner_text()
    # Detail levels retain task unions and the simplified hierarchy.
    visit();page.locator('.coverage-detail').select_option('allSpecies')
    assert page.locator('.coverage-dot').count()==1102 and page.locator('[data-taxon]').count()==87
    page.locator('.coverage-detail').select_option('clade')
    assert page.locator('.coverage-dot').count()==820 and page.locator('[data-taxon]').count()==32
    page.locator('.coverage-detail').select_option('species')
    assert page.locator('[data-node="vertebrates"]').get_attribute('data-display-parent')=='animals'
    assert page.locator('[data-taxon="teleostei-sp-7955"]').get_attribute('data-display-parent')=='vertebrates'
    assert page.locator('[data-node="obazoa"]').count()==0
    bad=page.evaluate('''(()=>{const bad=[];for(const c of document.querySelectorAll('.coverage-cell')){const r=c.getBoundingClientRect();for(const m of c.querySelectorAll('.coverage-dot')){const b=m.getBoundingClientRect();if(b.left<r.left||b.right>r.right+.1||b.top<r.top||b.bottom>r.bottom+.1)bad.push(m.dataset.coverageTask);}}return bad;})()''')
    assert not bad,bad
    page.locator('.coverage-expand').click()
    assert page.locator('.coverage-scroll').evaluate('(e)=>e.getBoundingClientRect().height/innerHeight')>.8
    page.locator('[data-jump="plants"]').click()
    page.screenshot(path='/tmp/marin-glm-coverage-expanded.png')
    page.keyboard.press('Escape')
    assert not page.locator('.coverage-pane').evaluate('(e)=>e.classList.contains("expanded")')
    assert page.locator('.coverage-scroll').evaluate('(e)=>getComputedStyle(e).overscrollBehaviorY')=='auto'
    page.evaluate('''(()=>{const w=document.querySelector('.coverage-scroll');w.scrollTop=w.scrollHeight;window.scrollTo(0,500);})()''')
    page.mouse.move(750,800);page.mouse.wheel(0,350);page.wait_for_function('window.scrollY>550')
    page.evaluate('''(()=>{document.querySelector('.coverage-scroll').scrollTop=0;window.scrollTo(0,700);})()''')
    page.mouse.move(750,800);page.mouse.wheel(0,-350);page.wait_for_function('window.scrollY<650')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('.coverage-expand').click()
    assert page.locator('.coverage-scroll').evaluate('(e)=>e.clientHeight')>400
    page.screenshot(path='/tmp/marin-glm-coverage-mobile.png')
    page.keyboard.press('Escape');click_mode('tasks')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='/tmp/marin-glm-task-mobile.png')
    # Secondary sections and model-specific evidence remain available.
    page.set_viewport_size({'width':1440,'height':1100})
    for view in ['projects','models','papers','data','audit']:
        visit('#view='+view)
        assert page.locator('#other-view').inner_text().strip()
        if view=='projects':
            assert page.locator('.project').count()==10
            assert not page.locator('.project-reviews').evaluate('(e)=>e.open')
        if view=='models':
            assert '128' in page.locator('#model-genosm').inner_text()
            assert '256' in page.locator('#model-genosm').inner_text()
            assert '524' in page.locator('#model-aido2').inner_text()
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),view
        page.set_viewport_size({'width':1440,'height':1100})
    assert not errors,errors
    assert not requests,requests
    print(json.dumps({'result':'passed','task_records':513,'marker_associations':[879,1102,820],
        'javascript_errors':errors,'external_runtime_requests':requests,'checks':['default coverage','shared filters','association filtering','compact tables','pagination','sorting','cell links','citations','CSV','Evo 2 provenance','scroll chaining','mobile','secondary sections']}))
    browser.close()
