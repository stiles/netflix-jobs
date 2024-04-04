# Netflix job postings
A demonstration project that scrapes data-related job postings at Netflix. 

## About
This Python script, with the help of Github Actions, automates fetching, processing, storing and exporting Netflix job postings data. It's structured to work efficiently with the Netflix jobs API, process the data for uniformity, store it in a SQLite database and export it to CSV and JSON formats for easy access and analysis. This process runs each day at 8 a.m. Pacific Time. 

## Fetching
- Makes HTTP GET requests to Netflix's job postings API.
- Handles pagination to ensure all job postings are retrieved.
- Uses `tqdm` for progress tracking through pages.

## Processing
- Utilizes `BeautifulSoup    to parse HTML content, extracting and cleaning relevant fields such as job descriptions and titles.
- Formats list-like fields and dates for consistency.
- Extracts and cleans salary information.
- Searches for predefined keywords within job descriptions to tag postings with relevant categories (data science, engineering, visualization).

## Storing
- Stores processed data in a local SQLite database.
- Checks for and inserts only new job postings based on their unique identifiers to avoid duplicates.

## Exporting
- Fetches the complete dataset, including newly added and previously stored postings, from the SQLite database.
- Exports the dataset to CSV and JSON formats.
- Sends me email confirming that new listings were fetched and processed. 

## Configuration and Logging
- External `config.json` file for API endpoints, database paths, and log file paths, allowing easy adjustments without code changes.
- Detailed logging for execution process monitoring, including errors and informational messages.

## Implementation Details
- **Languages and libraries:** Python, using libraries such as `requests`, `pandas`, `BeautifulSoup`, and `sqlite3`.
- **Database:** SQLite for local data persistence.
- **Formats:** Data exported in both CSV and JSON for analysis and sharing.

## Usage
- Ensure all required libraries are installed and the config.json file is configured with the correct paths and settings.
- Run the script to fetch, process, and store the latest job postings data.
- Access the exported CSV and JSON files for the complete dataset.