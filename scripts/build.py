"""Build only public assets. CI validates data separately before deployment."""
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'public/data/results.json').read_text())
assert data['schemaVersion']==1 and data['electionDate']=='2026-11-03'
shutil.rmtree(ROOT/'dist',ignore_errors=True)
shutil.copytree(ROOT/'public',ROOT/'dist')
shutil.copyfile(ROOT/'config/sources.json',ROOT/'dist/data/sources.json')
shutil.copytree(ROOT/'schema',ROOT/'dist/schema')
print('Built dist/ (static assets only)')
