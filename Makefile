test:
	python -m pytest --cov=opensource_watchman --cov-report=xml -p no:warnings --disable-network

types:
	mypy opensource_watchman

check:
	mdl README.md
	flake8 opensource_watchman
	safety check -r requirements.txt
	make test types
