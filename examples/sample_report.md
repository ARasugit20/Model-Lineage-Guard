## Model Lineage Guard

Scanned `urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)` with 7 finding(s): 2 critical, 4 high, 1 medium, 0 low.

Full report: `report.html`
Write-back: dry-run

| Severity | Check | Entity | Finding |
| --- | --- | --- | --- |
| critical | pii_exposure | `urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)` | PII flows into model lineage without an approved exception |
| critical | pii_exposure | `urn:li:mlFeatureTable:(urn:li:dataPlatform:demo,user_risk_features)` | PII flows into model lineage without an approved exception |
| high | schema_drift | `urn:li:mlFeatureTable:(urn:li:dataPlatform:demo,user_risk_features)` | Upstream schema changed after feature computation |
| high | stale_dataset | `urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)` | Upstream dataset is stale for its declared cadence |
| high | feature_leakage_risk | `urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)` | Feature may use post-outcome information |
| high | feature_leakage_risk | `urn:li:mlFeature:(user_risk_features,chargeback_resolved_at)` | Feature may use post-outcome information |
| medium | missing_owner | `urn:li:mlFeatureTable:(urn:li:dataPlatform:demo,user_risk_features)` | Lineage entity has no registered owner |
