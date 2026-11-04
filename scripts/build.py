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
# Version the module graph too, including changes to collection-health messaging.
model=(ROOT/'dist/model.js').read_bytes()
model_name='model.'+hashlib.sha256(model).hexdigest()[:12]+'.js'
(ROOT/'dist'/model_name).write_bytes(model)
app=(ROOT/'dist/app.js').read_text().replace("'./model.js'",f"'./{model_name}'")
app_name='app.'+hashlib.sha256(app.encode()).hexdigest()[:12]+'.js'
(ROOT/'dist'/app_name).write_text(app)
index.write_text(index.read_text().replace('src="/app.js"',f'src="/{app_name}"'))
print('Built dist/ (static assets only)')
