"""Exercise the actual generated page without an HTTP server or external requests."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'index.html').as_uri())
    page.wait_for_selector('details.task')
    assert page.locator('details.task').count()==40
    page.select_option('#suite','gpn-evals')
    page.wait_for_function("location.hash.includes('suite=gpn-evals')")
    assert '21 matching records' in page.locator('#result-count').inner_text()
    page.locator('details.task').first.locator('summary').first.click()
    page.wait_for_selector('details.task[open] .detail-body h4')
    assert page.locator('.detail-body').first.inner_text().strip()
    page.screenshot(path='/tmp/marin-glm-desktop.png',full_page=True)
    # Taxon ancestry includes the Arabidopsis GPN-Star task.
    page.select_option('#population','plants')
    page.wait_for_function("location.hash.includes('population=plants')")
    assert '1 matching records' in page.locator('#result-count').inner_text()
    page.locator('button[type=reset]').click()
    page.select_option('#evo','original')
    page.wait_for_function("location.hash.includes('evo=original')")
    assert page.locator('details.task').count()>0
    assert page.locator('details.task .tag.evo').filter(has_text='original paper').count()>0
    page.locator('#suite-mode').click()
    page.wait_for_selector('.collection')
    assert 'DART' in page.locator('#results').inner_text()
    # A direct link restores one task, its facts, counts and provenance.
    for task in ['bacbench-essential','nt-revised-enhancers_types','gue-H3','gpn-rvat','gpn-annotation','traitgym-mendelian','bend-opensplice','deepstarr-dev','aido2-clinvar-snv','genosm-bgc-types','genosm-crc']:
        page.goto((ROOT/'index.html').as_uri()+'#view=evaluations&task='+task)
        page.wait_for_selector('details.task[open] .detail-body h4')
        assert page.locator('details.task').count()==1
        assert page.locator('.detail-body .citation').count()>0
        assert 'Documented model usage' in page.locator('.detail-body').inner_text()
    # CSV download exports the filter result, not just the visible page.
    page.goto((ROOT/'index.html').as_uri()+'#view=evaluations&suite=gpn-evals')
    page.wait_for_selector('details.task')
    with page.expect_download() as download_info:page.locator('#export').click()
    download=download_info.value
    content=Path(download.path()).read_text()
    assert 'gpn-clinvar' in content and 'gpn-rare-arabidopsis' in content
    for view in ['models','papers','data','audit']:
        page.goto((ROOT/'index.html').as_uri()+'#view='+view)
        page.wait_for_function(f"document.getElementById('other-view').hidden === false && document.querySelector('nav a[aria-current=page]').dataset.view === '{view}'")
        assert page.locator('#other-view').inner_text().strip()
        if view=='models':
            assert '128' in page.locator('#model-genosm .model-properties').inner_text()
            assert '256' in page.locator('#model-genosm .model-properties').inner_text()
            assert '524-kb' in page.locator('#model-aido2 .model-properties').inner_text()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.set_viewport_size({'width':1440,'height':1100})
    page.goto((ROOT/'index.html').as_uri()+'#view=evaluations&suite=gpn-evals')
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_selector('details.task')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/marin-glm-mobile.png',full_page=True)
    assert not errors,errors
    print(json.dumps({'javascript_errors':errors,'desktop_screenshot':'/tmp/marin-glm-desktop.png','mobile_screenshot':'/tmp/marin-glm-mobile.png','result':'passed'}))
    browser.close()
