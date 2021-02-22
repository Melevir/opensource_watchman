deal_test:
	python -m deal test  *.py */*.py */*/*.py

test:
	python -m pytest --cov=opensource_watchman --cov-report=xml -p no:warnings --disable-network

types:
	mypy opensource_watchman

check:
	mdl README.md
	flake8 opensource_watchman
	safety check -r requirements.txt
	make -j3 test types deal_test
