check:
	mdl README.md
	flake8 opensource_watchman
	mypy opensource_watchman
	python -m pytest --cov=opensource_watchman --cov-report=xml -p no:warnings --disable-network
	safety check -r requirements.txt
