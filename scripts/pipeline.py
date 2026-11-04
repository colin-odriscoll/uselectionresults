"""Fetch -> archive -> normalize -> validate -> atomically publish. No inferred winners."""
import copy
import csv
import hashlib
import io
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from validate import ROOT, validate

MN_PAGE='https://electionresults.sos.mn.gov/Select/MediaFiles/Index?ersElectionId=201'
MN_FILES={'senate':'ussenate.txt','house':'ushouse.txt','governor':'Governor.txt'}
NC_BASE='https://er.ncsbe.gov/enr/20261103/data/'

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def integer(value):
    if not re.fullmatch(r'\d+',value): raise ValueError('Expected nonnegative integer')
    return int(value)

def fetch(url):
    error=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'USElectionResults/1.0 (public election data)','Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=30) as response:
                if response.url!=url:
                    if 'perfdrive.com' in response.url:
                        raise ValueError('Official site requires a CAPTCHA; automated collection blocked')
                    raise ValueError('Unexpected redirect; review endpoint')
                body=response.read(10_000_001)
                if len(body)>10_000_000: raise ValueError('Feed size limit exceeded')
                return body, response.headers.get('Last-Modified')
        except Exception as exc:
            error=exc
            if attempt<2: time.sleep(2**attempt)
    raise error

def archive(body, url, timestamp, folder):
    digest=hashlib.sha256(body).hexdigest()
    folder.mkdir(parents=True,exist_ok=True)
    (folder/(digest+'.raw')).write_bytes(body)
    (folder/(digest+'.json')).write_text(json.dumps(dict(url=url,retrievedAt=timestamp,sha256=digest),indent=2))
    return digest

def guard_minnesota(page):
    text=re.sub(r'<[^>]+>',' ',page)
    text=re.sub(r'\s+',' ',text)
    if re.search(r'\b(test|sample|mock)\s+results\b',text,re.I):
        raise ValueError('Official source is publishing TEST RESULTS; rejected')
    if 'November 3, 2026' not in text or not re.search(r'Unofficial Results|Official Results',text,re.I):
        raise ValueError('Unrecognized election identity or production status')

def parse_minnesota(text, office, evidence):
    result={}
    for row in csv.reader(io.StringIO(text.lstrip('\ufeff')),delimiter=';'):
        if not row: continue
        if len(row)!=16 or row[0]!='MN' or row[1] or row[2]:
            raise ValueError('MN layout/geographic level changed')
        label={'house':'U.S. Representative','senate':'U.S. Senator','governor':'Governor'}[office]
        if not row[4].startswith(label): raise ValueError('Wrong office in feed')
        seat=f'{integer(row[5]):02}' if office=='house' else ('2' if office=='senate' else 'general')
        if office!='house' and row[5]: raise ValueError('Unexpected statewide district')
        rid=f'MN-{office}-{seat}'
        reporting=dict(kind='precincts',counted=integer(row[11]),total=integer(row[12]))
        total=integer(row[15])
        item=result.setdefault(rid,dict(**evidence,candidates=[],totalVotes=total,reporting=reporting))
        if item['totalVotes']!=total or item['reporting']!=reporting:
            raise ValueError('Inconsistent totals/reporting across candidates')
        item['candidates'].append(dict(id=f"MN-{row[3]}-{row[6]}",name=row[7],party=row[10] or 'Unknown',votes=integer(row[13])))
    if not result: raise ValueError('Empty results file')
    return result

def collect_minnesota(source, folder, fetcher=fetch):
    page,_=fetcher(MN_PAGE)
    archive(page,MN_PAGE,now(),folder)
    guard_minnesota(page.decode('utf-8-sig'))
    updates={}
    for office,filename in MN_FILES.items():
        url='https://electionresultsfiles.sos.mn.gov/20261103/'+filename
        # Require the exact official link, rather than guessing a date-shaped URL.
        if url not in page.decode('utf-8-sig'): raise ValueError('Expected download link missing')
        body,modified=fetcher(url)
        retrieved=now()
        digest=archive(body,url,retrieved,folder)
        updated=None
        if modified:
            from email.utils import parsedate_to_datetime
            updated=parsedate_to_datetime(modified).astimezone(timezone.utc).isoformat().replace('+00:00','Z')
        evidence=dict(sourceId=source['id'],url=url,retrievedAt=retrieved,sourceUpdatedAt=updated,sha256=digest)
        updates.update(parse_minnesota(body.decode('utf-8-sig'),office,evidence))
    # Re-check the status page after the downloads to catch a mode transition.
    page,_=fetcher(MN_PAGE)
    archive(page,MN_PAGE,now(),folder)
    guard_minnesota(page.decode('utf-8-sig'))
    expected={'MN-senate-2','MN-governor-general'}|{f'MN-house-{n:02}' for n in range(1,9)}
    if set(updates)!=expected: raise ValueError('Incomplete Minnesota race coverage')
    return updates

def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    os.replace(tmp,path)

def guard_north_carolina(body):
    rows=json.loads(body)
    state=[r for r in rows if r.get('cid')=='0']
    if len(state)!=1 or state[0].get('tle')!='11/03/2026 UNOFFICIAL GENERAL ELECTION RESULTS - STATEWIDE':
        raise ValueError('NC election identity or production status not verified')
    return state[0]

def parse_north_carolina(body,evidence):
    rows=json.loads(body)
    result={}; groups={}
    for row in rows:
        if row.get('cid')!='0': raise ValueError('NC feed is not statewide')
        name=row.get('cnm','')
        if name=='US SENATE (VOTE FOR 1)': rid='NC-senate-2'
        else:
            match=re.fullmatch(r'US HOUSE OF REPRESENTATIVES DISTRICT (\d{2}) \(VOTE FOR 1\)',name)
            if not match:
                if row.get('ogl')=='FED': raise ValueError('Unmapped NC federal contest')
                continue
            rid='NC-house-'+match[1]
        if row.get('vfr')!='1': raise ValueError('Unexpected vote-for limit')
        if rid in groups and groups[rid]!=row['gid']: raise ValueError('Conflicting NC contest identities')
        groups[rid]=row['gid']
        reporting=dict(kind='precincts',counted=integer(row['prt']),total=integer(row['ptl']))
        item=result.setdefault(rid,dict(**evidence,candidates=[],totalVotes=0,reporting=reporting))
        if item['reporting']!=reporting: raise ValueError('Inconsistent NC precinct reporting')
        votes=integer(row['vct'])
        if votes!=sum(integer(row[k]) for k in ('evc','ovc','avc','pvc')):
            raise ValueError('NC voting-method totals mismatch')
        # The publisher supplies no candidate ID here; stable identity uses contest + exact ballot name + party.
        identity=hashlib.sha256((row['bnm']+'|'+row['pty']).encode()).hexdigest()[:16]
        item['candidates'].append(dict(id=f"NC-{row['gid']}-{identity}",name=row['bnm'],party=row['pty'] or 'Unknown',votes=votes))
        item['totalVotes']+=votes
    expected={'NC-senate-2'}|{f'NC-house-{i:02}' for i in range(1,15)}
    if set(result)!=expected: raise ValueError('Incomplete NC federal race inventory')
    return result

def collect_north_carolina(source,folder,fetcher=fetch):
    catalog_url='https://er.ncsbe.gov/enr/elections.txt'
    catalog,_=fetcher(catalog_url);archive(catalog,catalog_url,now(),folder)
    if not any(r.get('edt')=='11/03/2026' and r.get('con')=='1' for r in json.loads(catalog)):
        raise ValueError('NC election missing from official catalog')
    status_url=NC_BASE+'county.txt'
    status,_=fetcher(status_url);archive(status,status_url,now(),folder)
    guard_north_carolina(status)
    url=NC_BASE+'results_0.txt'
    body,modified=fetcher(url);retrieved=now();digest=archive(body,url,retrieved,folder)
    updated=None
    if modified:
        from email.utils import parsedate_to_datetime
        updated=parsedate_to_datetime(modified).astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    evidence=dict(sourceId=source['id'],url=url,retrievedAt=retrieved,sourceUpdatedAt=updated,sha256=digest)
    result=parse_north_carolina(body,evidence)
    status,_=fetcher(status_url);archive(status,status_url,now(),folder)
    guard_north_carolina(status)
    return result

def apply_editorial(data, editorial):
    races={r['id']:r for r in data['races']}
    for r in races.values(): r['calls']=[]; r['certification']=None
    for item in editorial['calls']:
        value=dict(item); rid=value.pop('raceId'); races[rid]['calls'].append(value)
    for item in editorial['certifications']:
        value=dict(item); rid=value.pop('raceId')
        if races[rid]['certification']: raise ValueError('Duplicate certification')
        races[rid]['certification']=value

def run():
    path=ROOT/'public/data/results.json'
    previous=validate(json.loads(path.read_text()))
    data=copy.deepcopy(previous)
    sources=json.loads((ROOT/'config/sources.json').read_text())
    health=[]; failures=False
    for source in sources:
        entry=dict(sourceId=source['id'],checkedAt=now(),status='disabled',message=source['note'])
        if source['enabled']:
            if now()<source['notBefore']:
                entry.update(status='waiting',message='Waiting for scheduled poll close; no results imported.')
            else:
                try:
                    collectors={'minnesota':collect_minnesota,'north_carolina':collect_north_carolina}
                    if source['adapter'] not in collectors: raise ValueError('Adapter not implemented; keep disabled')
                    updates=collectors[source['adapter']](source,ROOT/'work/raw')
                    trial=copy.deepcopy(data)
                    for race in trial['races']:
                        if race['id'] in updates:
                            incoming=updates[race['id']]; old=race['official']
                            # Corrections may reduce votes. Accept them, but require non-regressing source time.
                            if old and old['sourceUpdatedAt'] and incoming['sourceUpdatedAt'] and incoming['sourceUpdatedAt']<old['sourceUpdatedAt']:
                                raise ValueError('Source timestamp regressed')
                            race['official']=incoming
                    validate(trial,sources)
                    data=trial
                    entry.update(status='ok',message='Validated official vote totals; not certified.')
                except Exception as exc:
                    failures=True
                    entry.update(status='error',message=str(exc)[:250]+' Previous validated data retained.')
        health.append(entry)
    apply_editorial(data,json.loads((ROOT/'config/editorial.json').read_text()))
    if data!=previous:
        data['generatedAt']=now()
    validate(data,sources)
    atomic_json(path,data)
    atomic_json(ROOT/'public/data/health.json',dict(checkedAt=now(),sources=health))
    print(json.dumps(health,indent=2))
    return 1 if failures else 0

if __name__=='__main__':
    raise SystemExit(run())
