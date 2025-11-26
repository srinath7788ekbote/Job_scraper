@echo off
REM Navigate to the Job_scraper directory explicitly
cd /d "C:\Users\sekbote\Job_scraper" || (echo Failed to enter Job_scraper directory & exit /b 1)

REM Run make setup
make setup || (echo make setup failed & exit /b 1)

REM Activate the virtual environment
call .venv\Scripts\activate.bat || (echo Failed to activate virtual environment & exit /b 1)

REM Run make run with arguments if provided
IF "%~1"=="" (
    make run || (echo make run failed & exit /b 1)
) ELSE (
    make run ARGS="%*" || (echo make run failed & exit /b 1)
)

REM List directory contents
dir
