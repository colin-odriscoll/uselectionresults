# Data contract

The canonical machine-readable contract is [`schema/results.schema.json`](../schema/results.schema.json). All objects reject unknown properties. Run `python scripts/validate.py` before publishing; it enforces constraints that JSON Schema alone cannot express.

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Integer `1`; incompatible consumers must reject another version. |
| `electionDate` | Exactly `2026-11-03`. This dataset is not a primary or historical results feed. |
| `generatedAt` | ISO 8601 UTC snapshot assembly time; not a source result timestamp. Unchanged snapshots keep this timestamp. |
| `states` | Unique 50-state code/name catalog. |
| `races[].id` | Stable ID: `MN-house-01`, `AK-house-AL`, `MN-senate-2`, `FL-senate-3-special`, `MN-governor-general`. Senate seat identifies class, not candidate. |
| `state`, `office`, `label`, `special` | Inventory metadata; office is `house`, `senate` or `governor`. |
| `official` | `null` when not imported; otherwise a single official authority's complete candidate snapshot. No aggregation across rival feeds. |
| `calls` | Latest state per named outlet. Empty means no call imported, not proof no outlet has called the race. |
| `certification` | `null` unless an independent official certification record has been reviewed. |

An `official` record requires `sourceId`, HTTPS `url`, `retrievedAt`, nullable `sourceUpdatedAt`, a raw-body `sha256`, `candidates`, `totalVotes` and nullable `reporting`. Candidate fields: `id`, `name`, source `party` abbreviation and nonnegative integer `votes`. A real zero is allowed only in an imported record. Candidate IDs must be unique, votes must sum exactly to `totalVotes`, and the source must be an official authority for that state.

`reporting` is either null or `{ "kind": "precincts", "counted": N, "total": N }`. Counted cannot exceed total; total must be positive. It does not estimate ballots counted. The browser computes candidate vote share from the imported contest total; a zero denominator displays a dash.

## News calls and certification

Add reviewed records to `config/editorial.json` and run the pipeline. Every editorial record has a `raceId` that is removed during normalization. Calls also require `sourceId` from the **news** registry, HTTPS evidence `url`, `retrievedAt`, `candidateId`, `calledAt`, and `status` (`called` or `retracted`). The candidate must exist in the official snapshot; this intentionally prevents unsupported candidate identity matching. To support news-only races in the future, introduce a separately sourced candidate registry and version the contract.

A certification has `sourceId` from the **official** registry for that state, HTTPS evidence `url`, `retrievedAt`, `candidateId` and `certifiedAt`. Link the actual certification document, not a homepage. The evidence URL must use an allowlisted host. Schema validation checks structure and provenance identity; it cannot prove that an editor's evidence actually supports a claim. Review each record before committing.

Different outlets may call different candidates. The UI displays disagreement and never chooses a consensus winner. Retracted calls remain visible but are excluded from called-race counts. Removing an editorial record removes it from the next snapshot. Git history retains prior versions. A certification does not silently delete conflicting news calls.

`public/data/health.json` is operational metadata: collection check time plus per-source `waiting`, `disabled`, `ok`, or `error`. Failure does not advance the official record's retrieval time. It is published separately so an outage is visible even when the result snapshot is unchanged. The build copies the source registry to `dist/data/sources.json` for human-readable attribution.
