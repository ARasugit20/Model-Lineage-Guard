.PHONY: test demo demo-offline examples env-check

test:
	ruff check .
	mypy app/
	pytest -q

env-check:
	python3 scripts/check_environment.py

examples:
	python3 scripts/generate_examples.py
	python3 scripts/validate_examples.py

demo:
	datahub docker quickstart
	python3 scripts/seed_demo_lineage.py
	mlguard scan-all --out out/demo --write-back dry-run
	mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/demo/credit_risk_v3 --write-back dry-run

demo-offline:
	mlguard demo-report --out examples --write-back dry-run
	python3 scripts/validate_examples.py
