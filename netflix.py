#!/usr/bin/env python
# coding: utf-8

# Jobs
# > This script fetches, processes and analyzes [job postings by Netflix](https://jobs.netflix.com/search?page=`1`). 

#### Load Python tools and Jupyter config

import re
import json
import logging
import sqlite3
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

today = pd.Timestamp("today").strftime("%Y%m%d")

logging.basicConfig(level=logging.INFO, filename="netflix_jobs_log.txt", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    logging.getLogger().handlers[0].baseFilename = config.get("log_file_path", "netflix_jobs_log.txt")
except Exception as e:
    logging.error(f"Failed to load configurations: {e}")
    exit(1)


## Helper functions

#### Function to deal with lists in some columns

def extract_first_item(list_like):
    """Extract the first item from a list-like object or return None if empty."""
    if list_like and isinstance(list_like, list):
        return list_like[0]
    return None


#### Strip markup from description columns

def strip_html_tags(content):
    """Remove HTML tags from the provided content."""
    if content:
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    return content

#### Function to extract salary ranges

def extract_salary(text):
    pattern = r"the\s+range\s+for\s+this\s+role\s+is\s+(\$\d{1,3}(?:,\d{3})+)(?:\s*-\s*(\$\d{1,3}(?:,\d{3})+))?"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1), match.group(2) if match.group(2) else np.nan
    return np.nan, np.nan


#### Function to clean and convert salary values

def clean_salary(salary):
    if pd.isna(salary):
        return np.nan
    return float(salary.replace("$", "").replace(",", ""))


#### Function to extract our keywords

def extract_keywords(description, keywords):
    found_keywords = []
    description_lower = description.lower()
    for category, keys in keywords.items():
        for key in keys:
            if key.lower() in description_lower and key.lower() not in found_keywords:
                found_keywords.append(key.lower())
    return found_keywords



## Fetch

#### Headers and parameters for initial request

try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    headers = config["headers"]
    db_path = config["database_path"]
    params = config['params']

    logging.getLogger().handlers[0].baseFilename = config.get("log_file_path", "netflix_jobs_log.txt")
except Exception as e:
    logging.error(f"Failed to load configurations: {e}")

#### Initial request to get the total number of pages

try:
    response = requests.get("https://jobs.netflix.com/api/search", params=params, headers=headers)
    response.raise_for_status()  # This will raise an error for bad responses
    data = response.json()
    total_pages = data["info"]["postings"]["num_pages"]
except requests.exceptions.RequestException as e:
    logging.error(f"Request failed: {e}")
    exit(1)

#### Loop through each page to fetch postings

all_postings = []

for page in range(1, total_pages + 1):
    params["page"] = page
    response = requests.get(
        "https://jobs.netflix.com/api/search", params=params, headers=headers
    )
    postings = response.json()["records"]["postings"]

    all_postings.extend(postings)


## Process

#### Convert the list of postings into a pandas DataFrame

cols = [
    "external_id",
    "slug",
    "text",
    "department",
    "team",
    "state",
    "updated_at",
    "created_at",
    "location",
    "organization",
    "subteam",
    "lever_team",
    "description",
    "search_text",
]

src = pd.DataFrame(all_postings)[cols]

#### Apply the function to each list column

src["team"] = src["team"].apply(extract_first_item)
src["subteam"] = src["subteam"].apply(extract_first_item)
src["organization"] = src["organization"].apply(extract_first_item)

#### Apply the function to strip HTML from the 'description' and 'search_text' columns

src["description"] = src["description"].apply(strip_html_tags)
src["search_text"] = src["search_text"].apply(strip_html_tags)

#### Deal with all dates

src["created_at"] = pd.to_datetime(src["created_at"])
src["updated_at"] = pd.to_datetime(src["updated_at"])


## Extract

#### Apply the function and directly split the results into two new columns

src["salary_lower"], src["salary_upper"] = zip(
    *src["description"].apply(extract_salary)
)

#### Clean and convert salary columns

src["salary_lower"] = src["salary_lower"].apply(clean_salary)
src["salary_upper"] = src["salary_upper"].apply(clean_salary)


#### On the hunt for data science-y roles

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

#### Place the keywords in a column

src["keywords"] = src["description"].apply(lambda x: extract_keywords(x, keywords))


## Store

#### A clean dataframe

df = src.copy()

#### Connect to a SQLite database

try:
    conn = sqlite3.connect(db_path)  # Use db_path from config
except sqlite3.Error as e:
    logging.error(f"Database connection failed: {e}")
    exit(1)

#### Prepare data types for the database

df = df.astype(str)
df["created_at"] = pd.to_datetime(df["created_at"]).astype(str)
df["updated_at"] = pd.to_datetime(df["updated_at"]).astype(str)

#### Store the dataframe as a table in the database

try:
    df.to_sql("jobs", conn, if_exists="replace", index=False)
except Exception as e:
    logging.error(f"Failed to insert data into the database: {e}")

#### Use Pandas to execute a query for 'data' jobs that are remote or in LA

query = """
SELECT * FROM jobs 
WHERE 
    (location LIKE '%Los Angeles%' OR location LIKE '%Remote%') 
    AND 
    team LIKE '%Data%';
"""
df_query_results = pd.read_sql_query(query, conn)


## Exports

#### CSV format

df.to_csv("data/processed/netflix_listings.csv", index=False)
df.to_csv(f"data/processed/archive/netflix_listings_{today}.csv", index=False)

#### JSON format

df.to_json("data/processed/netflix_listings.json", indent=4, orient="records")
df.to_json(f"data/processed/archive/netflix_listings_{today}.json", indent=4, orient="records")

