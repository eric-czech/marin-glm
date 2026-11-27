"""Validate the canonical catalogue or apply an explicit research authoring helper.

No source imports or historical migrations run implicitly. Helpers may require
ignored research caches; normal validation/builds do not.
"""
from pathlib import Path
import argparse
import importlib
import json
import re
import sqlite3
import sys
from build import load_catalogue

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='append',default=[],metavar='MODULE',
        help='Apply scripts/curation/MODULE.py to the existing catalogue. Repeat to specify an explicit order.')
    args=parser.parse_args()
    path=ROOT/'data/catalogue.json'
    data=json.loads(path.read_text())
    sys.path.insert(0,str(ROOT))
    sys.path.insert(0,str(ROOT/'scripts/curation'))
    for name in args.apply:
        if not re.fullmatch('[a-z][a-z0-9_]*',name):parser.error('Invalid helper module name')
        module=importlib.import_module(name)
        module.populate(data)
    with sqlite3.connect(':memory:') as db:load_catalogue(data,db)
    if args.apply:
        temporary=path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(path)
        print('Updated validated authoring document. Run scripts/build.py to regenerate SQLite and the site.')
    else:print('Catalogue structure, references and completed source reviews are valid.')
    print(f'{len(data["tasks"])} tasks; {len(data["evaluations"])} collections; {len(data["papers"])} paper/report records.')


if __name__=='__main__':main()
