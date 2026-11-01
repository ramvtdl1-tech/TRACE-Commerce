"""Provider diagnostics expose useful categories without disclosing upstream data."""
import io
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from commerce.providers import ProviderError, request_json


class ProviderErrorTests(unittest.TestCase):
    def test_http_errors_explain_categories_and_never_leak_upstream_details(self):
        cases = {401: "authentication", 402: "credits", 403: "access denied",
                 404: "not found", 422: "configuration", 429: "quota", 503: "temporarily"}
        for status, expected in cases.items():
            with self.subTest(status=status):
                upstream = HTTPError("https://private.example/secret-key", status,
                                     "private-key-in-reason", {"X-Private": "secret"},
                                     io.BytesIO(b'{"error":"private-key-in-body"}'))
                opener = MagicMock()
                opener.open.side_effect = upstream
                with patch("commerce.providers.build_opener", return_value=opener):
                    with self.assertRaises(ProviderError) as caught:
                        request_json("https://provider.example", provider="ai")
                message = str(caught.exception)
                self.assertIn(str(status), message)
                self.assertIn(expected, message)
                self.assertIn("AI provider", message)
                self.assertNotIn("private", message)
                self.assertNotIn("secret", message)

    def test_network_errors_keep_sensitive_exception_details_private(self):
        opener = MagicMock()
        opener.open.side_effect = URLError("private-key-in-network-error")
        with patch("commerce.providers.build_opener", return_value=opener):
            with self.assertRaises(ProviderError) as caught:
                request_json("https://provider.example", provider="ai")
        self.assertIn("connection failed", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))

    def test_timeout_is_identified_without_exception_text(self):
        opener = MagicMock()
        opener.open.side_effect = TimeoutError("private-token")
        with patch("commerce.providers.build_opener", return_value=opener):
            with self.assertRaises(ProviderError) as caught:
                request_json("https://provider.example", provider="paypal")
        self.assertIn("PayPal sandbox request timed out", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))
