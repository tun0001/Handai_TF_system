# univ-athlete-db

This project is designed to scrape athletic competition results from specified URLs and store the data in a database. It allows users to filter results by university and retrieve athlete names along with their events and records.

## Project Structure

```
univ-athlete-db
├── src
│   ├── cli.py               # Command-line interface for user interaction
│   ├── config.py            # Configuration settings for the application
│   ├── scraper
│   │   ├── fetcher.py       # Fetches HTML content from URLs
│   │   └── parser.py        # Parses HTML to extract athlete data
│   └── database
│       ├── db.py            # Manages database connections and queries
│       └── models.py        # Defines data models for athlete and event records
├── tests
│   ├── test_scraper.py      # Unit tests for scraper functionality
│   └── test_database.py      # Unit tests for database functionality
├── requirements.txt         # Lists project dependencies
├── setup.py                 # Setup script for the project
└── README.md                # Project documentation
```

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To run the application, use the command line to specify the URL of the results page and the university name you want to filter by:

```
python src/cli.py <url> <university_name> [--json]
```

The `--json` flag can be added to output the results in JSON format.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.