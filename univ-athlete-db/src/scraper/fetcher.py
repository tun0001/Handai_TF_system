import requests

def fetch_html(url):
    """Fetch HTML content from the specified URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        encoding = response.apparent_encoding
        return response.content.decode(encoding, errors='replace')
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching data from {url}: {e}")