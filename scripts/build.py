"""Build only public assets. CI validates data separately before deployment."""
import json
import hashlib
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'public/data/results.json').read_text())
assert data['schemaVersion']==1 and data['electionDate']=='2026-11-03'
shutil.rmtree(ROOT/'dist',ignore_errors=True)
shutil.copytree(ROOT/'public',ROOT/'dist')
shutil.copyfile(ROOT/'config/sources.json',ROOT/'dist/data/sources.json')
shutil.copytree(ROOT/'schema',ROOT/'dist/schema')
# A changed design gets a new URL so browsers cannot reuse the previous CSS.
css=(ROOT/'dist/styles.css').read_bytes()
css_name='styles.'+hashlib.sha256(css).hexdigest()[:12]+'.css'
(ROOT/'dist'/css_name).write_bytes(css)
index=ROOT/'dist/index.html'
index.write_text(index.read_text().replace('href="/styles.css"',f'href="/{css_name}"'))
print('Built dist/ (static assets only)')
