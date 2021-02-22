deal_test:
	python -m deal test  *.py */*.py */*/*.py

test:
	python -m pytest --cov=opensource_watchman --cov-report=xml -p no:warnings --disable-network -n 4

types:
	mypy opensource_watchman

style:
	flake8 opensource_watchman

safety:
	safety check -r requirements.txt

md_style:
	mdl README.md

check:
	make -j5 test types style safety md_style
