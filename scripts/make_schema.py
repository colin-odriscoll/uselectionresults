"""Maintain a closed JSON Schema; pipeline also validates referential integrity."""
import json
from pathlib import Path

def obj(properties, required=None):
    return dict(type='object', properties=properties, required=list(properties) if required is None else required, additionalProperties=False)
def arr(items): return dict(type='array', items=items)
def nullable(value): return dict(anyOf=[value, {'type':'null'}])
text = {'type':'string','minLength':1}
stamp = {'type':'string','format':'date-time'}
url = {'type':'string','format':'uri','pattern':'^https://'}
count = {'type':'integer','minimum':0,'maximum':9007199254740991}
evidence = dict(sourceId=text, url=url, retrievedAt=stamp)
candidate = obj(dict(id=text, name=text, party=text, votes=count))
official = obj(dict(**evidence, sourceUpdatedAt=nullable(stamp), sha256={'type':'string','pattern':'^[a-f0-9]{64}$'},
    candidates=arr(candidate), totalVotes=count,
    reporting=nullable(obj(dict(kind={'const':'precincts'}, counted=count, total={'type':'integer','minimum':1})))))
call = obj(dict(**evidence, candidateId=text, calledAt=stamp, status={'enum':['called','retracted']}))
certification = obj(dict(**evidence, candidateId=text, certifiedAt=stamp))
race = obj(dict(id=text,state={'type':'string','pattern':'^[A-Z]{2}$'},office={'enum':['house','senate','governor']},
    label=text,special={'type':'boolean'},official=nullable(official),calls=arr(call),certification=nullable(certification)))
schema = dict(obj(dict(schemaVersion={'const':1},electionDate={'const':'2026-11-03'},generatedAt=stamp,
    states=arr(obj(dict(code=text,name=text))),races=arr(race))), **{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:uselectionresults:schema:results:1'})
if __name__ == '__main__':
    Path('schema').mkdir(exist_ok=True)
    Path('schema/results.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
