import unittest
from src.scraper.fetcher import fetch_html
from src.scraper.parser import fetch_results
from unittest.mock import patch, Mock

class TestScraper(unittest.TestCase):

    @patch('src.scraper.fetcher.requests.get')
    def test_fetch_html_success(self, mock_get):
        mock_response = Mock()
        mock_response.content = b'<html></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_html('http://example.com')
        self.assertEqual(result, '<html></html>')

    @patch('src.scraper.fetcher.requests.get')
    def test_fetch_html_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.HTTPError

        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_html('http://example.com')

    @patch('src.scraper.fetcher.fetch_html')
    def test_fetch_results(self, mock_fetch_html):
        mock_fetch_html.return_value = '<table><tr><th>氏名</th><th>記録</th></tr><tr><td>選手A</td><td>10.5</td></tr></table>'
        
        results = fetch_results('http://example.com')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['氏名'], '選手A')
        self.assertEqual(results[0]['記録'], '10.5')

if __name__ == '__main__':
    unittest.main()