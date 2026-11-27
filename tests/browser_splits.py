"""Offline figures use the same counts/denominators as SQLite and CSV."""
from pathlib import Path
import csv
import io
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/site-data.json').read_text());C={r['id']:r for r in D['split_comparisons']};P={r['id']:r for r in D['split_partitions']}
with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page(viewport={'width':1600,'height':1200});errors=[];network=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http:','https:')) else None)
    url=(ROOT/'index.html').as_uri()
    page.goto(url+'#view=splits');page.wait_for_selector('.split-chart-row')
    assert page.locator('#page-title').inner_text()=='Splits'
    assert page.locator('.split-chart-row').count()==12
    for el in page.locator('.split-chart-row').all():
        c=C[el.get_attribute('data-comparison')];n=int(el.get_attribute('data-count'));d=int(el.get_attribute('data-denominator'))
        if c['overlap_type']=='exact-sequence':
            assert n==c['shared_count'];assert d in [P[c['left_partition_id']]['unique_sequences'],P[c['right_partition_id']]['unique_sequences']]
        else:
            assert n in [c['left_affected'],c['right_affected']];assert d in [P[c['left_partition_id']]['row_count'],P[c['right_partition_id']]['row_count']]
    text=page.locator('.split-locus-example').inner_text()
    assert all(x in text for x in ['chr10:2,816,452–2,817,052','chr6:111,348,504–111,349,104','600 bp'])
    assert 'undefined' not in page.locator('.splits').inner_text()
    page.screenshot(path='/tmp/marin-splits-desktop.png')
    page.locator('#split-scale').select_option('1')
    assert page.locator('.split-chart-row path.split-marker').count()>=4
    # Keyboard selection exposes source rules, examples and data provenance.
    row=page.locator('.split-chart-row').first;row.focus();page.keyboard.press('Enter')
    page.wait_for_selector('#split-audit-detail')
    assert '4,531' in page.locator('#split-audit-detail').inner_text()
    assert page.locator('#split-audit-detail .split-examples a[href*="split-examples.jsonl#L"]').count()==10
    assert page.locator('#split-audit-detail a[href*="/viewer/"]').count()==20
    page.locator('.split-source-rules summary').click()
    assert 'chr10' in page.locator('.split-source-rules').inner_text()
    page.screenshot(path='/tmp/marin-splits-detail.png')
    # State survives reload; table links select a different audit.
    page.reload();page.wait_for_selector('#split-audit-detail')
    page.locator('#split-search').fill('BEND');page.wait_for_timeout(350)
    assert 'BEND' in page.locator('#split-search').input_value()
    assert page.locator('.split-audit-table tbody tr').count()==2
    page.locator('.split-audit-table a').first.click()
    assert 'BEND' in page.locator('#split-audit-detail h3').inner_text()
    page.locator('#split-filters button[type=reset]').click()
    assert page.locator('.split-audit-table tbody tr').count()==30
    first=page.locator('.split-audit-table a').first.inner_text();page.locator('#split-next').click()
    assert page.locator('.split-audit-table a').first.inner_text()!=first
    page.locator('#split-release').select_option('GENEB');page.locator('#split-finding').select_option('overlap')
    assert page.locator('.split-audit-table tbody tr').count()==25
    with page.expect_download() as dl:page.locator('#split-export').click()
    rows=list(csv.DictReader(io.StringIO(Path(dl.value.path()).read_text())))
    assert len(rows)>=25 and all(r['release']=='GENEB' and r['finding']=='overlap' for r in rows)
    # Size exclusions contain no synthetic comparison rows.
    page.locator('#split-filters button[type=reset]').click();page.locator('#split-status').select_option('skipped-size')
    assert page.locator('.split-audit-table tbody tr').count()>=4
    assert 'No measured comparison' in page.locator('.split-audit-table').inner_text()
    # Task details expose associated checks without introducing model attribution.
    page.goto(url+'#view=evaluations&task=plantcad2-ft-cell_type_specific_acr')
    page.wait_for_selector('.task-split-links');page.locator('.task-split-links summary').click()
    assert page.locator('.task-split-links a[href*="split-plantcad-cell"]').count()==1
    # Mobile uses local scroll containers, not a wider document.
    page.set_viewport_size({'width':390,'height':844});page.goto(url+'#view=splits');page.wait_for_selector('.split-chart')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    assert page.locator('.split-chart-wrap').first.evaluate('e=>e.scrollWidth>e.clientWidth')
    page.screenshot(path='/tmp/marin-splits-mobile.png')
    assert not errors,errors
    assert not network,network
    b.close()
print('Splits browser checks passed: figures, units, examples, keyboard, filters, state, CSV and mobile.')
