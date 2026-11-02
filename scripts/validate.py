import json
from pathlib import Path
from datetime import datetime, timezone
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
def timestamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    assert parsed.tzinfo is not None, 'Timestamp needs timezone'
    assert parsed<=datetime.now(timezone.utc), 'Future timestamp'
    return parsed

def validate(data, sources=None):
    schema=json.loads((ROOT/'schema/results.schema.json').read_text())
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(data)
    timestamp(data['generatedAt'])
    sources = sources or json.loads((ROOT/'config/sources.json').read_text())
    sources={s['id']:s for s in sources}
    states={s['code'] for s in data['states']}
    assert len(states)==len(data['states'])==50, 'Invalid state inventory'
    ids=set()
    def evidence(item, kind):
        source=sources.get(item['sourceId'])
        assert source and source['kind']==kind, 'Source type mismatch'
        from urllib.parse import urlparse
        assert urlparse(item['url']).hostname in source['hosts'], 'Unapproved evidence host'
        retrieved=timestamp(item['retrievedAt'])
        for field in ('sourceUpdatedAt','calledAt','certifiedAt'):
            if item.get(field):
                assert timestamp(item[field])<=retrieved, 'Evidence timestamp follows retrieval'
    for race in data['races']:
        assert race['id'] not in ids and race['state'] in states, 'Duplicate race or unknown state'
        ids.add(race['id'])
        candidates=set()
        if race['official'] is not None:
            o=race['official']; evidence(o,'official')
            assert sources[o['sourceId']]['state']==race['state'], 'Source state mismatch'
            candidates={c['id'] for c in o['candidates']}
            assert len(candidates)==len(o['candidates']) and candidates, 'Duplicate or empty candidates'
            assert sum(c['votes'] for c in o['candidates'])==o['totalVotes'], 'Vote totals mismatch'
            if o['reporting']:
                assert o['reporting']['counted']<=o['reporting']['total'], 'Reporting exceeds total'
        call_sources=set()
        for call in race['calls']:
            evidence(call,'news')
            assert call['sourceId'] not in call_sources, 'Duplicate outlet call'
            call_sources.add(call['sourceId'])
            assert call['candidateId'] in candidates, 'Unknown called candidate'
        if race['certification']:
            evidence(race['certification'],'official')
            assert sources[race['certification']['sourceId']]['state']==race['state'], 'Certification state mismatch'
            assert race['certification']['candidateId'] in candidates, 'Unknown certified candidate'
    # This inventory covers regular 2026 seats and FL/OH special Senate contests.
    from catalog import seed
    expected={r['id']:(r['state'],r['office'],r['special']) for r in seed()['races']}
    actual={r['id']:(r['state'],r['office'],r['special']) for r in data['races']}
    assert actual==expected, 'Election inventory changed; review catalog and schema together'
    return data

if __name__=='__main__':
    import sys
    validate(json.loads(Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'public/data/results.json').read_text()))
    print('Snapshot schema and integrity checks passed.')
