"""Compact record tables retain source details, citations and direct navigation."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'data/site-data.json').read_text())
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1600, 'height':1100})
    errors, network = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: network.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
    url = (ROOT/'index.html').as_uri()
    page.goto(url+'#view=projects');page.wait_for_selector('.project-table')
    assert page.locator('.project-table .catalogue-row').count() == len(DATA['projects'])
    assert page.locator('.project-table .catalogue-expanded').count() == 0
    assert page.locator('#other-view article.record').count() == 0
    assert all(label in page.locator('.project-table thead').inner_text() for label in ['Biological coverage', 'Evaluation methods', 'Documented independent use'])
    for project in DATA['projects']:
        row=page.locator(f'[data-project-id="{project["id"]}"]')
        uses=[u for u in DATA['project_adoptions'] if u['review_id']==project['review_id'] and u['independence']=='independent' and u['kind']!='citation-only']
        assert row.locator('.project-use-list li').count() == len(uses)
        assert row.locator('a.citation').count() >= len(uses)+2
        assert row.locator('.project-collection-link').count() > 0
    assert 'protein-only evaluation' in page.locator('[data-project-id="dgeb"]').inner_text()
    assert 'No BEND 2.0 adoption asserted' in page.locator('[data-project-id="bend"]').inner_text()
    page.screenshot(path='/tmp/marin-glm-projects.png')
    page.locator('[data-project-open="traitgym"]').focus();page.keyboard.press('Enter')
    assert page.locator('.project-table .catalogue-row').count() == len(DATA['projects'])
    assert page.locator('#project-detail-traitgym').count() == 1
    assert 'shared authorship' in page.locator('#project-detail-traitgym').inner_text()
    assert 'GPN-Star' in page.locator('#project-detail-traitgym').inner_text()
    page.reload();page.wait_for_selector('#project-detail-traitgym')
    page.locator('[data-project-open="traitgym"]').click()
    assert page.locator('.project-table .catalogue-expanded').count() == 0
    page.locator('[data-project-id="dart"] .project-collection-link').first.click()
    page.wait_for_selector('.collections-table')
    assert page.locator('#suite').input_value() == 'dart'
    page.goto(url+'#view=models');page.wait_for_selector('.model-table')
    assert page.locator('.model-table .catalogue-row').count() == len(DATA['models'])
    assert page.locator('.model-table .catalogue-expanded').count() == 0
    assert page.locator('#other-view article.record').count() == 0
    for row in page.locator('.model-table .catalogue-row').all():
        # Architecture, nucleotide encoding, corpus and context each have evidence.
        assert row.locator('a.citation').count() >= 4
        assert row.locator('td').nth(4).locator('a[href^="https://"]').count() == 1
    carbon = page.locator('[data-model-id="carbon"]')
    assert '196,608 bp' in carbon.inner_text() and 'Inference' in carbon.inner_text()
    assert '15,000-bp input' in page.locator('[data-model-id="spliceai"]').inner_text()
    assert 'units unspecified' in page.locator('[data-model-id="aido2"]').inner_text()
    page.locator('[data-model-open="genosm"]').focus();page.keyboard.press('Enter')
    assert page.locator('#model-detail-genosm').count() == 1
    assert 'vocab_size=256' in page.locator('#model-detail-genosm').inner_text()
    page.reload();page.wait_for_selector('#model-detail-genosm')
    assert page.locator('.catalogue-expanded').count() == 1
    page.locator('[data-model-open="genosm"]').click()
    assert page.locator('.catalogue-expanded').count() == 0
    page.locator('[data-model-open="evo2"]').click()
    repeated='Pinned configuration and data artifacts support specified fields; original training was not independently rerun.'
    assert page.locator('#model-detail-evo2').inner_text().count(repeated) == 1
    # A model-to-paper link selects the matching paper without losing the table.
    page.locator('[data-model-id="aido2"] a[href^="#view=papers"]').click()
    page.wait_for_selector('.paper-table')
    assert page.locator('.paper-table .catalogue-row').count() == len(DATA['papers'])
    assert page.locator('.paper-table .catalogue-expanded').count() == 1
    assert page.locator('.paper-detail h3').inner_text().startswith('AIDO.DNA2')
    page.locator('.paper-metadata summary').click()
    assert 'retrieved' in page.locator('.paper-metadata').inner_text()
    page.goto(url+'#view=papers');page.wait_for_selector('.paper-table')
    assert page.locator('.paper-table .catalogue-expanded').count() == 0
    for paper in ['cerberus', 'opensplice', 'gfmbench']:
        assert 'Abstract / metadata' in page.locator(f'[data-paper-id="{paper}"]').inner_text()
    assert page.locator('.paper-table tbody tr>td:nth-child(2)>a[href^="https://"]').count() == len(DATA['papers'])
    page.locator('[data-paper-open="loam"]').focus();page.keyboard.press('Enter')
    assert 'Abstract / metadata' in page.locator('[data-paper-id="loam"]').inner_text()
    page.locator('.paper-metadata summary').click()
    assert 'not-retrieved' in page.locator('#paper-detail-loam').inner_text()
    page.reload();page.wait_for_selector('#paper-detail-loam')
    page.locator('[data-paper-open="loam"]').click()
    assert page.locator('.catalogue-expanded').count() == 0
    # Summary tables scroll locally on small screens.
    page.set_viewport_size({'width':390, 'height':844})
    for fragment, selector in [('projects', '.project-table'), ('models', '.model-table'), ('papers', '.paper-table'),
                               ('splits&splitSection=strategies', '.split-summary-table')]:
        page.goto(url+'#view='+fragment);page.wait_for_selector(selector)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), fragment
        assert page.locator(selector).evaluate('e=>e.parentElement.scrollWidth>e.parentElement.clientWidth'), fragment
    assert not errors, errors
    assert not network, network
    browser.close()
print('Catalogue table checks passed: rows, field citations, details, keyboard, direct links and mobile.')
