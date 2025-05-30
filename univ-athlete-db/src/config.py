# filepath: /univ-athlete-db/univ-athlete-db/src/config.py

DATABASE_URI = 'sqlite:///univ_athlete.db'  # Database connection string
DEBUG = True  # Enable debug mode for development
TIMEOUT = 10  # Timeout for HTTP requests in seconds

# Constants for scraping
BASE_URL = 'https://example.com/results'  # Base URL for scraping results
RESULTS_TABLE_ID = 'results'  # ID of the results table in the HTML

# Other configuration settings can be added here as needed