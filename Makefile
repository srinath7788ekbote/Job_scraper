.PHONY: setup run clean help debug test-linkedin test-glassdoor test-naukri test-all

PYTHON := python
UV := python -m uv
SHELL := pwsh.exe
.SHELLFLAGS := -NoProfile -Command

help:
	Write-Host "Available commands:"
	Write-Host "  make setup         - Create virtual env and install dependencies"
	Write-Host "  make run           - Run the scraper (creates both .csv and .json files)"
	Write-Host "  make debug         - Run a single platform in debug mode"
	Write-Host "  make test-linkedin - Test LinkedIn scraper only"
	Write-Host "  make test-glassdoor- Test Glassdoor scraper only"
	Write-Host "  make test-naukri   - Test Naukri scraper only"
	Write-Host "  make test-all      - Test all platforms with small limits"
	Write-Host "  make clean         - Remove temporary files (.csv, .json, cache)"

setup:
	$(UV) venv --clear
	$(UV) pip install -e . --python .venv\Scripts\python.exe
	$(UV) run --python .venv\Scripts\python.exe playwright install

ARGS ?= --platform linkedin glassdoor naukri --location "Berlin" "US" --keyword "python" --days 1 --limit 1 --output jobs

run:
	.venv\Scripts\python.exe main.py $(ARGS)

debug:
	.venv\Scripts\python.exe main.py --platform naukri --location "Dubai" --keyword "SRE" --days 7 --limit 3 --output debug_jobs

test-linkedin:
	.venv\Scripts\python.exe main.py --platform linkedin --location "Australia" --keyword "SRE" --days 1 --limit 3 --output test_linkedin

test-glassdoor:
	.venv\Scripts\python.exe main.py --platform glassdoor --location "US" --keyword "Python" --days 1 --limit 3 --output test_glassdoor

test-naukri:
	.venv\Scripts\python.exe main.py --platform naukri --location "India" --keyword "Python" --days 1 --limit 3 --output test_naukri

test-all:
	.venv\Scripts\python.exe main.py --platform linkedin glassdoor naukri --location "Berlin" --keyword "SRE" --days 1 --limit 2 --workers 3 --output test_all

clean:
	if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }
	if (Test-Path scrapers/__pycache__) { Remove-Item -Recurse -Force scrapers/__pycache__ }
	if (Test-Path utils/__pycache__) { Remove-Item -Recurse -Force utils/__pycache__ }
	if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }
	if (Test-Path *.csv) { Remove-Item -Force *.csv }
	if (Test-Path *.json) { Remove-Item -Force *.json }
	if (Test-Path uv.lock) { Remove-Item -Force uv.lock }
