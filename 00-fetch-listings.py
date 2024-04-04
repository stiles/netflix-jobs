#!/usr/bin/env python
# coding: utf-8

"""
Jobs
This script fetches, processes, and analyzes job postings by Netflix.
"""

import re
import json
import logging
import sqlite3
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm

# Load configuration settings
config = {}
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"Failed to load configurations: {e}")
    exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    filename=config.get("log_file_path", "netflix_jobs_log.txt"),
                    filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

headers = config["headers"]
db_path = config["database_path"]
params = config.get('params', {})

# Today's date for file naming
today = datetime.now().strftime("%Y%m%d")

# Keywords list for extraction
keywords = {
    "data science": [
        "database",
        "data science",
        "machine learning",
        "deep learning",
        "statistics",
        "predictive modeling",
        "data analysis",
        "natural language processing",
        "NLP",
        "computer vision",
        "AI",
        "artificial intelligence",
        "python",
    ],
    "data engineering": [
        "data engineering",
        "ETL",
        "data pipeline",
        "data storage",
        "big data",
        "Hadoop",
        "Spark",
        "Apache Airflow",
        "streaming data",
        "data architecture",
        "database design",
        "SQL",
    ],
    "data visualization": [
        "visualization",
        "Tableau",
        "Power BI",
        "D3.js",
        "matplotlib",
        "plotly",
        "ggplot",
        "dashboards",
        "visual analytics",
        "data presentation",
    ],
}

# Helper functions
def extract_first_item(list_like):
    return list_like[0] if list_like and isinstance(list_like, list) else None

def strip_html_tags(content):
    return BeautifulSoup(content, "html.parser").get_text(separator=" ", strip=True) if content else content

def extract_salary(text):
    pattern = r"the\s+range\s+for\s+this\s+role\s+is\s+(\$\d{1,3}(?:,\d{3})+)(?:\s*-\s*(\$\d{1,3}(?:,\d{3})+))?"
    match = re.search(pattern, text, re.IGNORECASE)
    return (match.group(1), match.group(2) if match.group(2) else np.nan) if match else (np.nan, np.nan)

def clean_salary(salary):
    return float(salary.replace("$", "").replace(",", "")) if pd.notna(salary) else np.nan

def extract_keywords(description, keywords):
    found_keywords = []
    description_lower = description.lower()
    for category, keys in keywords.items():
        for key in keys:
            if key.lower() in description_lower:
                found_keywords.append(key.lower())
    return found_keywords

# Initialize database
def initialize_db(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS jobs_archive (
        external_id TEXT UNIQUE,
        slug TEXT,
        description TEXT,
        created_at TEXT,
        updated_at TEXT,
        location TEXT,
        department TEXT,
        team TEXT,
        organization TEXT,
        subteam TEXT,
        lever_team TEXT,
        search_text TEXT,
        keywords TEXT,
        salary_lower REAL,
        salary_upper REAL
    );
    """
    try:
        conn.execute(create_table_query)
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

# Fetch the job postings
def fetch_postings():
    try:
        response = requests.get("https://jobs.netflix.com/api/search", params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        total_pages = data["info"]["postings"]["num_pages"]
        
        all_postings = []
        for page in tqdm(range(1, total_pages + 1)):
            params["page"] = page
            page_response = requests.get("https://jobs.netflix.com/api/search", params=params, headers=headers)
            page_response.raise_for_status()
            postings = page_response.json()["records"]["postings"]
            all_postings.extend(postings)
        return all_postings
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return []


def process_and_store_postings(postings, conn):
    df = pd.DataFrame(postings)
    df['team'] = df['team'].apply(extract_first_item)
    df['description'] = df['description'].apply(strip_html_tags)
    df[['salary_lower', 'salary_upper']] = pd.DataFrame(df['description'].apply(extract_salary).tolist(), index=df.index)
    df['salary_lower'] = df['salary_lower'].apply(clean_salary)
    df['salary_upper'] = df['salary_upper'].apply(clean_salary)
    df['keywords'] = df['description'].apply(lambda x: extract_keywords(x, keywords))
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['salary_lower'] = df['salary_lower'].astype(float)
    df['salary_upper'] = df['salary_upper'].astype(float)
    df['keywords'] = df['keywords'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    df['location'] = df['location'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)
    df['team'] = df['team'].fillna('')
    df['organization'] = df['organization'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    df['organization'] = df['organization'].apply(lambda x: '' if pd.isnull(x) else str(x))
    df['subteam'] = df['subteam'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    df['subteam'] = df['subteam'].apply(lambda x: '' if pd.isnull(x) else str(x))
    
    # Select columns that match the database schema
    df_selected = df[['external_id', 'slug', 'description', 'created_at', 'updated_at', 'location', 'department', 'team','organization', 'subteam', 'lever_team', 'search_text', 'keywords', 'salary_lower', 'salary_upper']].copy()

    # Export to CSV and JSON
    df_selected.to_csv(f"data/processed/netflix_listings.csv", index=False)
    df_selected.to_json(f"data/processed/netflix_listings.json", orient='records', lines=True, indent=4)

    existing_ids = pd.read_sql_query('SELECT external_id FROM jobs_archive', conn)['external_id'].tolist()
    df_filtered = df_selected[~df_selected['external_id'].isin(existing_ids)]

    # Insert processed dataframe into the database
    try:
        # Insert into a temporary table
        df_filtered.to_sql("temp_jobs_archive", conn, if_exists="replace", index=False)

        # Insert from temporary table to main table where external_id does not exist in the main table
        conn.execute("""
            INSERT INTO jobs_archive (external_id, slug, description, created_at, updated_at, location, department, team, organization, subteam, lever_team, search_text, keywords, salary_lower, salary_upper)
            SELECT external_id, slug, description, created_at, updated_at, location, department, team, organization, subteam, lever_team, search_text, keywords, salary_lower, salary_upper
            FROM temp_jobs_archive
            WHERE external_id NOT IN (SELECT external_id FROM jobs_archive)
        """)
        conn.commit()

        full_archive_df = pd.read_sql_query("SELECT * FROM jobs_archive", conn)
        
        # Export the full archive to CSV and JSON
        full_archive_df.to_csv(f"data/processed/netflix_full_archive_{today}.csv", index=False)
        full_archive_df.to_json(f"data/processed/netflix_full_archive_{today}.json", orient='records', lines=True, indent=4)

        # Drop the temporary table after use
        conn.execute("DROP TABLE IF EXISTS temp_jobs_archive")
        conn.commit()

    except Exception as e:
        logging.error(f"Failed to archive postings: {e}")

if __name__ == "__main__":
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        initialize_db(conn)
        postings = fetch_postings()
        if postings:
            process_and_store_postings(postings, conn)
        else:
            logging.info("No new postings found.")
    except Exception as e:
        logging.error(f"Script execution failed: {e}")
    finally:
        if conn:
            conn.close()
