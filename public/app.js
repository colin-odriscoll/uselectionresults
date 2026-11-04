import { names, partyClass, activeCalls, matches, summarize, freshness, share } from './model.js';
const $ = selector => document.querySelector(selector);
const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const safeLink = value => { try { const u = new URL(value); return u.protocol === 'https:' ? escape(u.href) : '#'; } catch { return '#'; } };
const date = value => value ? new Date(value).toLocaleString(undefined, { dateStyle:'medium', timeStyle:'short' }) : 'Not supplied';
let data, health, sources=[], stateNames={}, limit=25;
let filter={ office:'house', state:'', query:'', status:'all' };
function readHash() {
  if (['#main','#methodology'].includes(location.hash)) return;
  const params=new URLSearchParams(location.hash.slice(1));
  filter.office=Object.hasOwn(names,params.get('office')) ? params.get('office') : 'house';
  filter.state=Object.hasOwn(stateNames,params.get('state')) ? params.get('state') : '';
}
function navigate() {
  const params=new URLSearchParams({office:filter.office});
  if(filter.state) params.set('state',filter.state);
  history.replaceState(null,'','#'+params); limit=25; render();
}
function evidence(item) {
  const source=sources.find(s=>s.id===item.sourceId);
  return `<a href="${safeLink(item.url)}" target="_blank" rel="noopener noreferrer">${escape(source?.name || item.sourceId)} ↗</a>`;
}
function raceCard(race) {
  const o=race.official, calls=activeCalls(race);
  const candidate=id=>o?.candidates.find(c=>c.id===id)?.name || 'Unknown candidate';
  const rows=o ? [...o.candidates].sort((a,b)=>b.votes-a.votes).map(c=>`<tr><th scope="row"><span class="party ${partyClass(c.party)}"></span>${escape(c.name)} <small>${escape(c.party)}</small></th><td>${c.votes.toLocaleString()}</td><td>${share(c.votes,o.totalVotes)}</td></tr>`).join('') : '';
  const conflicting = new Set(calls.map(c=>c.candidateId)).size>1;
  return `<article class="race-card"><div class="race-heading"><div><span class="state-code">${race.state}</span><h3>${escape(stateNames[race.state])} <span>/ ${escape(race.label)}</span></h3></div><span class="badge ${race.certification?'certified':o?'official':'waiting'}">${race.certification?'Certified':o?'Official · uncertified':'Awaiting data'}</span></div>${o?`<table><caption class="sr-only">${escape(race.id)} official vote totals</caption><thead><tr><th scope="col">Candidate / party</th><th scope="col">Votes</th><th scope="col">Share</th></tr></thead><tbody>${rows}</tbody></table><div class="race-meta"><span>${o.reporting?`${o.reporting.counted.toLocaleString()} / ${o.reporting.total.toLocaleString()} precincts reporting`:'Reporting completeness unavailable'}</span><span>${escape(freshness(o))}</span></div><details><summary>Official source & timestamps</summary><p>${evidence(o)}</p><p>Source file updated: ${date(o.sourceUpdatedAt)}<br>Retrieved: ${date(o.retrievedAt)}<br>Total votes in this contest: ${o.totalVotes.toLocaleString()}</p><p class="small">Vote share is calculated from reported candidate totals, not all ballots expected. Precinct reporting does not measure ballots remaining.</p></details>`:`<div class="no-data"><span>—</span><div><strong>No official results imported</strong><p>${sources.some(s=>s.state===race.state&&s.enabled)?'The connected official feed has not passed its latest collection checks. See the Source desk for details.':'An official results feed has not been connected for this state.'} Candidate lists and vote totals are not assumed.</p></div></div>`}<div class="calls"><span class="small">NEWS CALLS</span>${race.calls.length?race.calls.map(c=>`<p><span class="badge news">${c.status==='retracted'?'Retracted':'News call'}</span> ${evidence(c)} ${c.status==='called'?'calls this race for':'retracted its call for'} <strong>${escape(candidate(c.candidateId))}</strong> · ${date(c.calledAt)}</p>`).join(''):'<span class="muted small">No verified news call imported</span>'}${conflicting?'<p class="conflict">Outlets disagree. No consensus winner is assigned.</p>':''}</div>${race.certification?`<p class="certification">Certified winner: <strong>${escape(candidate(race.certification.candidateId))}</strong> · ${evidence(race.certification)} · ${date(race.certification.certifiedAt)}</p>`:''}</article>`;
}
function render() {
  if(!data) return;
  $('#summary').innerHTML=Object.entries(names).map(([office,name])=>{const s=summarize(data.races,office);return `<button class="summary-card ${office===filter.office?'selected':''}" data-office="${office}"><span class="eyebrow">${name.toUpperCase()}</span><div><strong>${s.total}</strong><span>races on the ballot</span><span class="arrow">↗</span></div><div class="summary-track"></div><p><b>${s.reporting}</b> with official data <span>· ${s.called} news-called · ${s.certified} certified</span></p></button>`;}).join('');
  $('#view-title').textContent=filter.state?`${stateNames[filter.state]} results`:'National overview';
  $('#state-select').value=filter.state;
  document.querySelectorAll('#offices button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.office===filter.office)));
  $('#states').innerHTML=data.states.map(s=>`<button data-state="${s.code}" aria-pressed="${filter.state===s.code}" title="${escape(s.name)}" aria-label="${escape(s.name)}">${s.code}</button>`).join('');
  const races=data.races.filter(r=>matches(r,filter,stateNames));
  $('#result-count').textContent=`${races.length} ${names[filter.office].toLowerCase()} races${filter.state?' in '+stateNames[filter.state]:''} · showing ${Math.min(limit,races.length)}`;
  $('#races').innerHTML=races.length?races.slice(0,limit).map(raceCard).join(''):'<div class="empty"><h3>No matching races</h3><p>Try another office, state, search or status. Some states have no Senate or governor election this year.</p></div>';
  $('#more').hidden=limit>=races.length;
}
async function getJson(path) { const r=await fetch(path,{cache:'no-store'}); if(!r.ok) throw Error(`Could not load ${path}`); return r.json(); }
async function load() {
  $('#refresh').disabled=true;
  try {
    const [snapshot,registry]=await Promise.all([getJson('/data/results.json'),getJson('/data/sources.json')]);
    if(snapshot.schemaVersion!==1 || snapshot.electionDate!=='2026-11-03' || !Array.isArray(snapshot.races)) throw Error('Unsupported election data');
    data=snapshot; sources=registry; stateNames=Object.fromEntries(data.states.map(s=>[s.code,s.name]));
    $('#state-select').innerHTML='<option value="">All states</option>'+data.states.map(s=>`<option value="${s.code}">${escape(s.name)}</option>`).join('');
    const imported=data.races.filter(r=>r.official).length;
    $('#coverage-label').textContent=imported?'Partial official coverage':'Awaiting official data';
    $('#coverage-description').textContent=imported?`${imported} of ${data.races.length} races have imported counts. Check each source’s freshness.`:'No vote totals or winners have been imported. This is a coverage status, not a claim that voting has not begun.';
    $('#snapshot-time').textContent='Snapshot: '+date(data.generatedAt);
    const connected=new Set(sources.filter(s=>s.kind==='official'&&s.enabled).map(s=>s.state)).size;
    $('#notice').textContent=`Coverage note: ${connected} state adapter${connected===1?'':'s'} enabled. ${50-connected} states and national news feeds are not connected. Missing counts are never shown as zero.`;
    try { health=await getJson('/data/health.json'); } catch { health=null; }
    const staleHealth=!health || Date.now()-Date.parse(health.checkedAt)>30*60*1000;
    $('#health-time').textContent=health?'Last collection check: '+date(health.checkedAt)+(staleHealth?' · UPDATE JOB OVERDUE':''):'Collection health unavailable';
    if(staleHealth) $('#notice').textContent+=' Automatic collection has not reported in over 30 minutes. Results may be outdated.';
    const failed=health?.sources.filter(s=>s.status==='error') || [];
    if(failed.length) $('#notice').textContent+=` ${failed.length} official source(s) failed the latest check; see Source desk.`;
    $('#source-coverage').textContent=`Coverage is partial. ${connected} state adapters are enabled. No national news feed is connected. Unconnected states remain visible without fabricated counts.`;
    $('#sources').innerHTML=sources.map(s=>{const h=health?.sources.find(h=>h.sourceId===s.id);return `<article class="source-row"><div><a href="${safeLink(s.url)}">${escape(s.name)} ↗</a><span class="small">${s.kind==='official'?'Official election authority':'News organization'}</span></div><span class="badge ${h?.status==='error'?'error':'waiting'}">${escape(h?.status || 'unknown')}</span><p>${escape(h?.message||s.note)}</p></article>`;}).join('');
    readHash(); render();
  } catch(error) { $('#notice').textContent=data?'Refresh failed. Showing the last loaded snapshot; check timestamps.':'Election data could not be loaded. Please try Refresh data. No results are being displayed.'; }
  finally { $('#refresh').disabled=false; }
}
document.addEventListener('click',e=>{const b=e.target.closest('button'); if(!b)return; if(b.dataset.office){filter.office=b.dataset.office;navigate();} if(b.dataset.state){filter.state=b.dataset.state;navigate();}});
$('#state-select').addEventListener('change',e=>{filter.state=e.target.value;navigate();});
$('#national').addEventListener('click',()=>{filter.state='';navigate();});
$('#search').addEventListener('input',e=>{filter.query=e.target.value;limit=25;render();});
$('#status').addEventListener('change',e=>{filter.status=e.target.value;limit=25;render();});
$('#more').addEventListener('click',()=>{limit+=25;render();});
$('#refresh').addEventListener('click',load);
window.addEventListener('hashchange',()=>{readHash();limit=25;render();});
setInterval(()=>{if(!document.hidden)load();},60000);
load();
