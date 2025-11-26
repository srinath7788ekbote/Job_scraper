# Job Scraper

A modular, scalable Python job scraper that aggregates job listings from multiple platforms with concurrent processing and advanced filtering capabilities.

## Features

- ✅ **Multi-Platform Support**: Scrapes LinkedIn, Glassdoor, and Naukri
- ✅ **Date Filtering**: Search jobs posted within the last N days (e.g., `--days=1` for last 24 hours)
- ✅ **Concurrent Processing**: Multi-threading and multi-processing for faster scraping
- ✅ **Modular Architecture**: Easy to add new job portals via base class interface
- ✅ **Comprehensive Data**: Extracts title, company, location, description, skills, experience, and posted date
- ✅ **Robust Error Handling**: Custom exceptions and retry logic
- ✅ **Flexible Output**: Export to CSV or JSON format

## Installation

### Prerequisites

- Python 3.9 or higher
- Chrome/Chromium browser (for Selenium)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd Job_scraper

# Install dependencies using make
make setup

# Or manually with uv
python -m uv venv
python -m uv pip install -e .
python -m uv run playwright install
```

## Usage

### Basic Usage

```bash
# Scrape all platforms for SRE jobs in Berlin from last 24 hours
python main.py --keyword "SRE" --location "Berlin" --days 1 --limit 10

# Scrape specific platforms for multiple locations
python main.py --platform linkedin glassdoor --keyword "DevOps" --location "US" "UK" --days 7 --limit 50

# Scrape Naukri for jobs in India from last 3 days
python main.py --platform naukri --keyword "Python Developer" --location "India" --days 3 --limit 20
```

### Using Makefile

```bash
# Run default scraping (configured in Makefile)
make run

# Run debug mode (single platform)
make debug

# Clean temporary files
make clean
```

### Command-Line Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--keyword` | Job search keyword (required) | - | `"SRE"`, `"DevOps Engineer"` |
| `--location` | Locations to search (required, multiple allowed) | - | `"Berlin"`, `"US"`, `"India"` |
| `--platform` | Platforms to scrape (optional, multiple allowed) | All platforms | `linkedin`, `glassdoor`, `naukri` |
| `--days` | Filter jobs posted in last N days | 7 | `1` (last 24h), `7` (last week) |
| `--limit` | Max jobs per platform per location | 100 | `50`, `200` |
| `--output` | Output base filename | `jobs` | `results`, `my_jobs` |
| `--workers` | Number of concurrent workers | 3 | `5`, `10` |

### Output Format

The scraper automatically creates **both CSV and JSON** files with your results:

- **CSV file**: `{output}.csv` - Tabular format, easy to open in Excel/Google Sheets
- **JSON file**: `{output}.json` - Structured format, easy to parse programmatically

Example:
```bash
python main.py --keyword "SRE" --location "US" --output my_jobs
# Creates: my_jobs.csv AND my_jobs.json
```

Both files contain the following fields:

- `title`: Job title
- `company`: Company name
- `location`: Job location
- `url`: Link to job posting
- `platform`: Source platform (LinkedIn, Glassdoor, Naukri)
- `description`: Full job description
- `key_responsibilities`: Extracted key responsibilities
- `skills`: Required skills
- `years_of_experience`: Required years of experience
- `posted_date`: Date when job was posted (YYYY-MM-DD format)
- `email`: Contact email address (if provided in job listing)

## Architecture

### Project Structure

```
Job_scraper/
├── main.py                      # Entry point with CLI
├── scrapers/
│   ├── __init__.py
│   ├── base.py                  # Base scraper interface
│   ├── scraper_registry.py      # Factory pattern for scrapers
│   ├── linkedin.py              # LinkedIn scraper
│   ├── glassdoor.py             # Glassdoor scraper
│   └── naukri.py                # Naukri scraper
├── utils/
│   ├── __init__.py
│   ├── exceptions.py            # Custom exception classes
│   ├── date_parser.py           # Date parsing utilities
│   ├── concurrency_config.py    # Concurrency settings
│   ├── parallel.py              # Parallel processing utilities
│   ├── text_parser.py           # Job description parser
│   ├── keyword_matcher.py       # Keyword matching logic
│   ├── exporter.py              # CSV/JSON export
│   └── stealth.py               # Anti-detection utilities
├── pyproject.toml               # Project dependencies
├── Makefile                     # Build and run commands
└── README.md                    # This file
```

### Key Components

1. **Base Scraper Interface** (`scrapers/base.py`):
   - `JobScraper`: Abstract base class all scrapers must implement
   - `JobListing`: Data structure for job information
   - `validate_config()`: Input validation
   - `get_platform_name()`: Platform identifier

2. **Scraper Registry** (`scrapers/scraper_registry.py`):
   - Factory pattern for creating scrapers
   - Auto-discovery of available platforms
   - Easy registration of new scrapers

3. **Concurrency** (`utils/parallel.py`):
   - Threading for I/O-bound web scraping
   - Multiprocessing support for CPU-bound tasks
   - Automatic retry logic with exponential backoff

4. **Date Parsing** (`utils/date_parser.py`):
   - Converts relative dates ("2 days ago") to ISO format
   - Supports various date formats across platforms

## Adding New Job Portals

See [CONTRIBUTING.md](CONTRIBUTING.md) for a detailed guide on adding new scrapers.

### Quick Start

1. Create a new file in `scrapers/` (e.g., `indeed.py`)
2. Inherit from `JobScraper` base class
3. Implement required methods:
   - `get_platform_name()`: Return platform name
   - `scrape()`: Scraping logic
4. The scraper will be auto-registered on import

Example:

```python
from scrapers.base import JobScraper, JobListing
from typing import List

class IndeedScraper(JobScraper):
    @classmethod
    def get_platform_name(cls) -> str:
        return "Indeed"
    
    def scrape(self, keyword: str, location: str, limit: int = 100, days: int = 7) -> List[JobListing]:
        self.validate_config(keyword, location, limit, days)
        # Your scraping logic here
        return jobs
```

## Troubleshooting

### Common Issues

**Issue**: "Playwright not installed"
```bash
# Solution: Install Playwright browsers
python -m playwright install
```

**Issue**: "ChromeDriver not found"
```bash
# Solution: Ensure Chrome is installed and accessible
# The scraper uses undetected-chromedriver which auto-downloads ChromeDriver
```

**Issue**: "Rate limiting detected"
```bash
# Solution: Reduce concurrent workers or add delays
python main.py --workers 2 --limit 20 ...
```

**Issue**: "No jobs found"
```bash
# Solution: Try different keywords, locations, or increase days
python main.py --keyword "Software Engineer" --location "Remote" --days 30
```

## Performance Tips

1. **Optimize Workers**: Start with 3 workers and adjust based on your system
2. **Batch Processing**: Use smaller limits per platform and combine results
3. **Date Filtering**: Use `--days=1` for recent jobs to reduce scraping time
4. **Platform Selection**: Scrape one platform at a time for debugging

## License

This project is for educational purposes. Please respect the terms of service of each job platform.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

### v0.2.0 (Current)
- ✅ Added modular scraper registry with factory pattern
- ✅ Implemented posted_date extraction for all platforms
- ✅ Enhanced concurrency with retry logic
- ✅ Added custom exception classes
- ✅ Improved date parsing utilities
- ✅ Added comprehensive validation
- ✅ Enhanced logging and statistics

### v0.1.0
- Initial release with LinkedIn, Glassdoor, and Naukri support
