"""Regression coverage for cycle 51 URL and path hardening."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_learning_option_research import _url_error  # noqa: E402


class Cycle51SecurityTests(unittest.TestCase):
    def test_live_learning_urls_reject_internal_and_numeric_hosts(self) -> None:
        for url in ("https://intranet/role", "https://0x7f000001/secret", "https://192.168.1.1/role"):
            with self.subTest(url=url):
                self.assertIsNotNone(_url_error(url, "active", "live"))


if __name__ == "__main__":
    unittest.main()
