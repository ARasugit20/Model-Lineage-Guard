# Model Lineage Guard Performance Improvements

This pass focused on the lineage scan hot path first, then check execution and report rendering. Local verification used the existing mocked DataHub tests plus the deterministic offline demo fixture because Docker/DataHub was not available locally for live end-to-end timing.

## Summary

| Step | Area | Before | After | Benchmark note |
| --- | --- | --- | --- | --- |
| 1 | Entity metadata fetches | Up to 8 aspect calls per entity when describing scan context entities. | 1 semityped entity request per unique URN, plus a scan-local describe cache. | Regression tests assert one graph call fetches all aspects and duplicate lineage URNs are described once. |
| 2 | Lineage traversal | Direct lineage used an unbounded related-entity fetch and sliced locally. | Uses DataHub `scroll_lineage` pagination when available; BFS reuses a `(URN, direction)` cache. | Mocked repeated walks dropped from 2 direct-edge calls to 1; paginated fetch requested only remaining page sizes (`3`, then `1`). |
| 3 | `scan-all` breadth | Every discovered model was scanned with no early cap warning. | `--max-downstream` defaults to 50 and warns before per-model scan context loads. | Mocked 3-model run with cap 2 made 2 context-load calls instead of 3. |
| 4 | Check entity scans | Each check independently iterated the full entity dictionary. | A scan-local entity type index routes checks to only relevant entity types. | 1000 demo runs: sequential checks `0.1560s`; ThreadPoolExecutor `0.3956s`, so parallel execution was not kept. |
| 5 | Report graph rendering | `_build_graph()` rebuilt graph payloads on repeated render access. | `RiskReport` memoizes the graph payload and returns mutation-safe deep copies. | Regression test shows the second `_build_graph()` call performs zero extra node payload builds. |
| 6 | Property extraction | `entity_properties()` re-merged custom properties per check call. | Entity dicts cache merged properties under a private key. | Regression test proves the second call reuses the same cached object. |
| 7 | HTML filtering | Filter loop wrote `style.display` directly for every finding. | Filter changes are batched with `requestAnimationFrame` and CSS class toggles. | Render test locks out `style.display` and confirms `classList.toggle("is-hidden")`. |

## Blocking Bottlenecks

### 1. Entity Metadata N+1

The biggest server-side cost was describing every entity by issuing repeated aspect-level requests. `describe_entity()` now fetches all required aspects through `get_entity_semityped()` in one request, and `scan_context()` keeps a per-call cache so duplicate URNs in upstream/downstream edges cannot trigger repeat describes.

Measured with tests:

- Per entity aspect fetches: up to 8 calls before, 1 call after.
- Duplicate entity descriptions in one scan: duplicate edge URNs now resolve to one describe call per unique URN.

### 2. Lineage Walk Calls

The direct lineage fetch now prefers DataHub's `scroll_lineage` endpoint. That gives real pagination instead of pulling all related entities and slicing in Python. Multi-hop traversal remains a manual BFS because the installed SDK exposes a lineage scroll endpoint, not a deep multi-hop traversal API.

Measured with tests:

- Repeated cached direct-edge lookup: 2 calls before cache, 1 call after cache.
- Breadth-limited direct lineage fetch: requested the exact remaining page counts (`3`, then `1`) rather than an unbounded fetch.

## Verification

Final local gate:

```text
ruff check .     # clean
mypy app/        # clean
pytest -q        # 43 passed
```

Offline demo baseline remained valid during the pass:

```text
make demo-offline
Findings: 9
Example artifacts validated.
```
