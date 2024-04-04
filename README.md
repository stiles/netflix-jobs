# Netflix job postings
A demonstration project that scrapes data-related job postings at Netflix. 

## About
This Python script, with the help of Github Actions, automates fetching, processing, storing and exporting Netflix job postings data. It's structured to work efficiently with the Netflix jobs API, process the data for uniformity, store it in a SQLite database and export it to CSV and JSON formats for easy access and analysis. This process runs each day at 8 a.m. Pacific Time. 

### Fetching
- Makes HTTP GET requests to Netflix's job postings API.
- Handles pagination to ensure all job postings are retrieved.
- Uses `tqdm` for progress tracking through pages.

### Processing
- Utilizes `BeautifulSoup` to parse HTML content, extracting and cleaning relevant fields such as job descriptions and titles.
- Formats list-like fields and dates for consistency.
- Extracts and cleans salary information.
- Searches for predefined keywords within job descriptions to tag postings with relevant categories (data science, engineering, visualization).

### Storing
- Stores processed data in a local SQLite database.
- Checks for and inserts only new job postings based on their unique identifiers to avoid duplicates.

### Exporting
- Fetches the complete dataset, including newly added and previously stored postings, from the SQLite database.
- Exports the dataset to CSV and JSON formats.
- Sends email confirming that new listings were fetched and processed. 

### Outputs

- [CSV](https://github.com/stiles/netflix-jobs/blob/main/data/processed/netflix_listings.csv)
- [JSON](https://github.com/stiles/netflix-jobs/blob/main/data/processed/netflix_listings.json)
- [SQLite db](https://github.com/stiles/netflix-jobs/blob/main/data/db/netflix_jobs.db)

### Configuration and Logging
- External `config.json` file for API endpoints, database paths, and log file paths, allowing easy adjustments without code changes.
- Detailed logging for execution process monitoring, including errors and informational messages.

### Implementation Details
- **Languages and libraries:** Python, using libraries such as `requests`, `pandas`, `BeautifulSoup`, and `sqlite3`.
- **Database:** SQLite for local data persistence.
- **Formats:** Data exported in both CSV and JSON for analysis and sharing.

---

## Use this code

### Prerequisites

Before you begin, ensure you have the following installed on your system:
- Python 3.10

Using a virtual environment for Python projects is recommended. For this repo, [`pipenv`](https://pipenv.pypa.io/en/latest/) is the chosen manager.

### Getting Started

Follow these steps to prepare your environment:

### 1. **Clone the repo**

First, clone this repository to your local machine and navigate into it using your terminal:

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. **Create a virtual environment**
Inside the repository directory, initiate a virtual environment using pipenv:

```
pipenv shell
```

This command creates a virtual environment and activates it.

### 3. Install dependencies

Install the required dependencies, including [Pandas](https://pandas.pydata.org/) and [BeautifulSoup](https://pypi.org/project/beautifulsoup4/), with the following command:

```
pipenv install
```

### Usage
- Ensure all required libraries are installed and the config.json file is configured with the correct paths and settings.
- Run the script to fetch, process, and store the latest job postings data.
- Access the exported CSV and JSON files for the complete dataset.

### About automating with GitHub Actions
This project includes a GitHub Actions workflow to automatically run the script and update the job postings data on a daily basis. If you'd like to receive email notifications about the workflow results, you'll need to set up email secrets in your GitHub repository.

### Setting Uup the action
The provided .github/workflows/main.yml file outlines the workflow to fetch, process, and store the Netflix job postings data. The action is scheduled to run at midnight UTC every day but can be adjusted to your preference.

To use this GitHub Action:

1. **Review the workflow file:** Open `.github/workflows/main.yml` and ensure it matches your project structure and requirements. Adjust the Python version and dependency installation steps if necessary.

2. Configure secrets for email notifications: If you wish to receive email notifications, you'll need to configure the following secrets in your GitHub repository: 
    - `EMAIL_USERNAME`: Your email address or username for the email service.
    - `EMAIL_PASSWORD`: An app-specific password or your email account password. For Gmail, it's recommended to generate an [app password](https://support.google.com/accounts/answer/185833).

To set up these secrets:

- Navigate to your GitHub repository.
- Click on "Settings" > "Secrets" > "Actions".
 Click on "New repository secret" and add each of the above secrets.

### GitHub action for email notifications
The workflow includes a step to send an email notification using the `dawidd6/action-send-mail@v2` GitHub Action. This step uses the configured email secrets to authenticate with your email service and send an email summarizing the workflow results.

Ensure the workflow's email sending step is correctly configured with your email address and preferences. You might need to adjust the SMTP server settings according to your email provider's requirements.

### Testing the action
After setting up the GitHub Action and configuring the email secrets, commit a change to your repository or manually trigger the workflow from the GitHub Actions tab to test it. Verify that the script runs as expected and that you receive an email notification with the workflow results.

This GitHub Action automation ensures that your Netflix job postings data is regularly updated and that you're promptly informed about the operation's success or any issues encountered.

---

## Etc.

### To do: 
- Formatted email output
- Better keyword extraction
- Automated process for summarizing posts 

### Questions/thoughts? 
- [Email me](mailto:mattstiles@gmail.com)