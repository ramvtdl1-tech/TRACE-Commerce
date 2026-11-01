"""Hosting origin selection preserves checkout returns and origin protection."""
import unittest
from unittest.mock import patch

from commerce.settings import Settings


class HostingTests(unittest.TestCase):
    def settings(self, variables):
        with patch.dict("os.environ", variables, clear=True), patch("dotenv.load_dotenv"):
            return Settings.from_env()

    def test_render_origin_is_used_when_explicit_origin_is_missing(self):
        settings = self.settings({"RENDER_EXTERNAL_URL": "https://trace-test.onrender.com/", "COOKIE_SECURE": "true"})
        settings.validate()
        self.assertEqual(settings.public_base_url, "https://trace-test.onrender.com")

    def test_custom_origin_overrides_default_render_domain(self):
        settings = self.settings({"RENDER_EXTERNAL_URL": "https://trace-test.onrender.com", "PUBLIC_BASE_URL": "https://shop.example.com", "COOKIE_SECURE": "true"})
        settings.validate()
        self.assertEqual(settings.public_base_url, "https://shop.example.com")

    def test_automatically_selected_origin_still_requires_https(self):
        settings = self.settings({"RENDER_EXTERNAL_URL": "http://trace-test.onrender.com", "COOKIE_SECURE": "true"})
        with self.assertRaises(ValueError):
            settings.validate()
