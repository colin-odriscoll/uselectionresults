export const names = { house: 'House', senate: 'Senate', governor: 'Governor' };
export const partyClass = party => ['D','DEM','DFL'].includes(party) ? 'dem' : ['R','REP'].includes(party) ? 'rep' : 'other';
export function activeCalls(race) { return race.calls.filter(c => c.status === 'called'); }
export function matches(race, { office, state, query = '', status = 'all' }, states) {
  if (race.office !== office || (state && race.state !== state)) return false;
  const haystack = [race.id, race.label, states[race.state], ...(race.official?.candidates.map(c => c.name) || [])].join(' ').toLowerCase();
  if (!haystack.includes(query.toLowerCase().trim())) return false;
  return status === 'all' || (status === 'reporting' && !!race.official) || (status === 'waiting' && !race.official) || (status === 'called' && activeCalls(race).length > 0) || (status === 'certified' && !!race.certification);
}
export function summarize(races, office) {
  const subset = races.filter(r => r.office === office);
  return { total: subset.length, reporting: subset.filter(r => r.official).length, called: subset.filter(r => activeCalls(r).length).length, certified: subset.filter(r => r.certification).length };
}
export function freshness(official, clock = Date.now()) {
  if (!official) return 'No official data';
  const timestamp = official.sourceUpdatedAt || official.retrievedAt;
  return clock - Date.parse(timestamp) > 30 * 60 * 1000 ? 'Stale · more than 30 minutes old' : 'Updated within 30 minutes';
}
export function share(votes, total) { return total > 0 ? `${(votes / total * 100).toFixed(1)}%` : '—'; }
