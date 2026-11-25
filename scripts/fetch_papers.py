"""Retrieve public paper text for local source inspection (not the site build)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research' / 'papers'
SOURCES = {
    'bend2': 'https://arxiv.org/html/2611.03806v1',
    'bgcbench': 'https://arxiv.org/html/2611.02275v2',
    'geneb': 'https://arxiv.org/html/2606.04525v1',
    'nabench': 'https://arxiv.org/html/2511.02888v1',
    'dart': 'https://arxiv.org/html/2412.05430v1',
    'gpnstar': 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC13736532/unicode',
    'guanine': 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC13501288/unicode',
    'mrnabench': 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC12265608/unicode',
    'generator2': 'https://www.biorxiv.org/content/10.64898/2026.01.27.702015v2.full',
    'deepd': 'https://www.biorxiv.org/content/10.64898/2026.10.13.758170v1.full',
    'bgcsbench': 'https://www.biorxiv.org/content/10.64898/2026.05.12.724296v1.full',
}

def fetch(item):
    key, url = item
    try:
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        raw = response.content
        if b'<collection' in raw[:2000]:
            doc = ET.fromstring(raw)
            text = '\n\n'.join(''.join(p.itertext()) for p in doc.findall('.//passage/text'))
            ext = 'xml'
        else:
            soup = BeautifulSoup(raw, 'html.parser')
            for node in soup(['script', 'style', 'nav']):
                node.decompose()
            text = soup.get_text('\n', strip=True)
            ext = 'html'
        if len(text) < 10000 or 'Checking your browser' in text[:1000]:
            raise ValueError(f'No full paper content ({len(text)} characters)')
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / f'{key}.{ext}').write_bytes(raw)
        (DEST / f'{key}.txt').write_text(text)
        return {'id': key, 'url': url, 'status': 'retrieved', 'bytes': len(raw), 'characters': len(text), 'sha256': hashlib.sha256(raw).hexdigest()}
    except Exception as exc:
        return {'id': key, 'url': url, 'status': 'unavailable', 'error': str(exc)}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:
        result = list(pool.map(fetch, SOURCES.items()))
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'retrieval.json').write_text(json.dumps(result, indent=2) + '\n')
    for row in result:
        print(json.dumps(row))
