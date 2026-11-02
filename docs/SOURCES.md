# Source research — verified November 2, 2026

This is an endpoint and inventory audit, not an assertion that production results are available. Research used official publishers. An official-domain test feed must never become election results.

## Minnesota — implemented

- [2026 download index](https://electionresults.sos.mn.gov/Select/MediaFiles/Index?ersElectionId=201): identifies November 3, 2026; observed **Test Results** on November 2. Production ingestion is therefore not yet validated against live election-night results.
- [Official layout](https://electionresults.sos.mn.gov/Results/MediaFileLayout/Index?erselectionId=201): semicolon-separated candidate rows; statewide/district results include candidate votes, contest total, and reporting/total precincts. Layout revision June 3, 2026.
- Exact linked endpoints: [Senate](https://electionresultsfiles.sos.mn.gov/20261103/ussenate.txt), [House districts](https://electionresultsfiles.sos.mn.gov/20261103/ushouse.txt), [Governor](https://electionresultsfiles.sos.mn.gov/20261103/Governor.txt). Paths and capitalization were inspected, not synthesized. Test data from them is not included in public snapshots.
- The publisher describes updates at intervals of 15 minutes or less on election night. That does not guarantee our GitHub schedule, successful ingestion or deployment timing.
- [Minnesota voting hours](https://www.sos.mn.gov/elections-voting/election-day-voting/voting-hours/): the adapter gates ingestion until 8 p.m. Central on election day (`2026-11-04T02:00:00Z`).

## North Carolina — researched, not implemented

- [Official downloads page](https://er.ncsbe.gov/downloads.html) loads its election catalog from [elections.txt](https://er.ncsbe.gov/enr/elections.txt).
- Its published page code constructs ZIP downloads under `https://dl.ncsbe.gov/ENRS/YYYY_MM_DD/results_pct_YYYYMMDD.zip` and checks a filter catalog for unavailable packages. **A URL pattern is not verification that the 2026 artifact exists or contains production results.**
- [Official results layout](https://dl.ncsbe.gov/ENRS/layout_results_pct.txt), inspected directly: tab-delimited precinct/candidate rows, with election date and separate voting-method counts plus a total. An eventual adapter must prevent duplicates and double-counting and verify election identity and production status. No parser or auto-enable is claimed here.
- [Official historical data page](https://www.ncsbe.gov/results-data/election-results/historical-election-results-data) documents the archive. Do not silently substitute historical totals for the upcoming election.

## News organizations

- [AP Elections API](https://developer.ap.org/ap-elections-api/) is a documented integration route; licensed credentials/entitlements must be arranged separately. No credentials or simulated AP response are supplied.
- CNN and Fox remain evidence-linked editorial call sources only. No authorized public machine-readable call endpoint was verified in this research. Do not scrape undocumented private interfaces or label official vote leaders as CNN/Fox winners.

## Race inventory

- House state seat counts: [US Census 2020 apportionment tables](https://www.census.gov/data/tables/2020/dec/2020-apportionment-data.html). All 435 voting seats are included. District labels are identifiers; no district boundary map or geographic claims are made.
- Regular Senate races: [US Senate Class II roster](https://www.senate.gov/senators/Class_II.htm), 33 seats with terms ending January 2027. The roster is used for state/class membership only, not to infer ballot candidates.
- Ohio special Senate race: [Ohio 2026 Candidate Requirement Guide](https://www.ohiosos.gov/globalassets/publications/election/2026_crg.pdf), unexpired term ending January 3, 2029.
- Florida Senate race: [official November 2026 election notice](https://files.floridados.gov/media/710256/2026_nge_des_english.pdf) and [2026 federal qualifying handbook](https://files.floridados.gov/media/710687/2026-federal-qualifying-handbook.pdf). Class III unexpired seat is separately keyed.
- Governor schedule: [National Governors Association election calendar](https://www.nga.org/governors/elections/). Its 39 contests include three territories; this project's 50-state scope includes 36 state races.

Re-check the inventory if special elections are added. This release does not claim coverage of every election on November 3, county contests, House unexpired-term special elections, runoffs or ranked-choice tabulation rounds. Adding such coverage requires explicit race/round identifiers rather than overwriting regular-election records.
