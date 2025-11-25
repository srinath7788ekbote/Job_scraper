import pandas as pd
import json
from typing import List
from scrapers.base import JobListing
from dataclasses import asdict

def export_to_csv(jobs: List[JobListing], filename: str):
    df = pd.DataFrame([asdict(job) for job in jobs])
    df.to_csv(filename, index=False)
    print(f"Exported {len(jobs)} jobs to {filename}")

def export_to_json(jobs: List[JobListing], filename: str):
    data = [asdict(job) for job in jobs]
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Exported {len(jobs)} jobs to {filename}")
