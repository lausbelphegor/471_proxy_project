import unittest
import requests

PROXY = "http://localhost:8080"

class TestProxyServer(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()
        self.session.proxies = {
            "http": PROXY,
            "https": PROXY
        }

    def tearDown(self):
        self.session.close()


    def test_example_http(self):
        url = "http://example.com"
        response = self.session.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Example Domain", response.text)

    def test_example_https(self):
        url = "https://example.com"
        response = self.session.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Example Domain", response.text)

    def test_neverssl(self):
        url = "http://neverssl.com"
        response = self.session.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("NeverSSL", response.text)
        
    def test_download_200MB_zip(self):
        url = "http://212.183.159.230/200MB.zip"
        response = self.session.get(url, stream=True)
        self.assertEqual(response.status_code, 200)
        total_size = 0
        for chunk in response.iter_content(4096):
            total_size += len(chunk)
        self.assertTrue(total_size > 200 * 1024 * 1024)  # Verify that the file is indeed 200MB

if __name__ == '__main__':
    unittest.main()
