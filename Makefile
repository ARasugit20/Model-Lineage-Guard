.PHONY: test demo demo-offline

test:
	ruff check .
	mypy app/
	pytest -q

demo:
	datahub docker quickstart
	python3 scripts/seed_demo_lineage.py
	mlguard scan-all --out out/demo --write-back dry-run
	mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/demo/credit_risk_v3 --write-back dry-run

demo-offline:
	mlguard demo-report --out examples --write-back dry-run
