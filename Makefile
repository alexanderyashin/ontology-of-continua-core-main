.PHONY: release-check release-build release-test release-package shit-control

release-check:
	python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run

release-build:
	python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish

release-test:
	python simulations/run_all.py --write-report
	python -m unittest discover release_machine/tests

release-package:
	python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish

shit-control:
	python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5
