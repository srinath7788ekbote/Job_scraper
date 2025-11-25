.PHONY: setup run clean help debug

PYTHON := python
UV := python -m uv
SHELL := pwsh.exe
.SHELLFLAGS := -NoProfile -Command

help:
	Write-Host "Available commands:"
	Write-Host "  make setup    - Create virtual env and install dependencies"
	Write-Host "  make run      - Run the scraper (LinkedIn, Glassdoor, Naukri)"
	Write-Host "  make debug    - Run a single platform in debug mode"
	Write-Host "  make clean    - Remove temporary files"

setup:
	$(UV) venv --clear
	$(UV) pip install -e . --python .venv\Scripts\python.exe
	$(UV) run --python .venv\Scripts\python.exe playwright install
	.venv\Scripts\Activate.ps1

run:
	.venv\Scripts\python.exe main.py --platform linkedin glassdoor naukri --location "Bengaluru" "Dubai" "London" --keyword "SRE" --days 1 --limit 100 --output jobs.csv

debug:
	.venv\Scripts\python.exe main.py --platform naukri --location Dubai --keyword "SRE" --days 7 --limit 100 --output debug_jobs.csv

clean:
	if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }
	if (Test-Path scrapers/__pycache__) { Remove-Item -Recurse -Force scrapers/__pycache__ }
	if (Test-Path utils/__pycache__) { Remove-Item -Recurse -Force utils/__pycache__ }
	if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }
	if (Test-Path *.csv) { Remove-Item -Force *.csv }
	if (Test-Path *.json) { Remove-Item -Force *.json }
	if (Test-Path uv.lock) { Remove-Item -Force uv.lock }
