# Instagram Account Manager

A desktop application built with **Python, PySide6, SQLite, and Playwright** for managing Instagram usernames through a graphical interface.

## Features

* Import usernames from TXT, CSV, and JSON files
* Automatically clean usernames and remove duplicates
* Local SQLite database for persistent data
* Search usernames
* Individual account processing
* Process all pending users sequentially
* Background processing using `QThread`
* Pause / Resume processing
* Stop batch processing
* Progress bar and completion tracking
* Status management:

  * Pending
  * Blocked
  * Skipped
  * Failed
* Export account data to CSV
* Separate processing status for different Instagram accounts
* Persistent Chrome session through Playwright

## Technology Stack

* Python
* PySide6
* SQLite
* Playwright
* Chromium / Google Chrome

## Project Structure

```text
InstagramAccountManager/
│
├── app.py
├── database.py
├── instagram.py
├── importer.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│
└── chrome_profile/
```

## Installation

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd InstagramAccountManager
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browser support:

```bash
playwright install
```

Run the application:

```bash
python app.py
```

## Processing Workflow

1. Import usernames from TXT, CSV, or JSON.
2. Select the Instagram account currently being used.
3. Pending users are loaded for that account.
4. Use **Process** for an individual username or **Process All** for sequential processing.
5. Processing runs in a background thread so the GUI remains responsive.
6. Results are stored in the SQLite database.
7. Progress is displayed in the application.

## Multi-Account Processing

Processing status is maintained separately for each Instagram account.

For example:

```text
Account A
    user123 → Blocked

Account B
    user123 → Pending
```

This allows the same username to have an independent processing status for different Instagram accounts.

## Process Controls

### Process All

Processes Pending users sequentially.

### Pause

Temporarily pauses the batch before continuing with the next user.

### Resume

Continues a paused batch.

### Stop

Stops the batch after the current operation completes.

## Database

The application stores its local database under:

```text
data/instagram.db
```

The local database should not be committed to Git.

## Development

This project is currently being developed as a self-learning project using Python desktop GUI development, SQLite database design, Playwright browser automation, multithreading, and Git version control.

## License

Add your preferred license here.
