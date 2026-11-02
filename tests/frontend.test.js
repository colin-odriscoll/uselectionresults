import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { matches, summarize, share, freshness, activeCalls } from '../public/model.js';
const data=JSON.parse(readFileSync(new URL('../public/data/results.json',import.meta.url)));
const states=Object.fromEntries(data.states.map(s=>[s.code,s.name]));
test('national totals and Minnesota drilldown',()=>{
 assert.equal(summarize(data.races,'house').total,435);
 assert.equal(data.races.filter(r=>matches(r,{office:'house',state:'MN'},states)).length,8);
 assert.equal(data.races.filter(r=>matches(r,{office:'senate',state:'CA'},states)).length,0);
});
test('search resolves state names and district labels',()=>{
 assert.equal(data.races.filter(r=>matches(r,{office:'house',query:'North Carolina'},states)).length,14);
 assert.equal(data.races.filter(r=>matches(r,{office:'house',state:'AK',query:'At-large'},states)).length,1);
});
test('zero denominator is not 0 percent',()=>{assert.equal(share(0,0),'—');assert.equal(share(25,100),'25.0%');});
test('unknown is not fresh; old source time is stale even after a recent fetch',()=>{
 assert.equal(freshness(null),'No official data');
 assert.match(freshness({sourceUpdatedAt:'2026-11-03T00:00:00Z',retrievedAt:'2026-11-04T00:00:00Z'},Date.parse('2026-11-04T00:01:00Z')),/Stale/);
});
test('retractions excluded; conflicting outlet calls retained independently',()=>{
 const race={calls:[{status:'retracted',candidateId:'a'},{status:'called',candidateId:'b'},{status:'called',candidateId:'a'}]};
 assert.equal(activeCalls(race).length,2);
 assert.equal(new Set(activeCalls(race).map(c=>c.candidateId)).size,2);
});
