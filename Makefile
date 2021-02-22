deal_test:
	python -m deal test  *.py */*.py */*/*.py

test:
	python -m pytest --cov=opensource_watchman --cov-report=xml -p no:warnings --disable-network

types:
	mypy opensource_watchman

style:
	flake8 opensource_watchman

safety:
	safety check -r requirements.txt

md_style:
	mdl README.md

check:
	make -j6 test types deal_test style safety md_style
