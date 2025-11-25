.PHONY: setup run clean help

PYTHON := python
UV := uv

help:
	@echo "Available commands:"
	@echo "  make setup    - Create virtual env and install dependencies"
	@echo "  make run      - Run the scraper (Bengaluru, SRE, 7 days, 1000 limit)"
	@echo "  make clean    - Remove temporary files"

setup:
	$(UV) venv
	$(UV) pip install .
	$(UV) run playwright install

run:
	$(UV) run $(PYTHON) main.py --platform linkedin indeed glassdoor naukri --location Bengaluru --keyword "SRE" --days 7 --limit 1000 --output jobs.csv

clean:
	rm -rf __pycache__
	rm -rf scrapers/__pycache__
	rm -rf utils/__pycache__
	rm -rf .venv
	rm -f *.csv *.json
