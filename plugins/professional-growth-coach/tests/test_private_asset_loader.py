import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER_PATH = ROOT / "scripts" / "private_asset_loader.py"
SPEC = importlib.util.spec_from_file_location("private_asset_loader_contract", LOADER_PATH)
assert SPEC is not None and SPEC.loader is not None
loader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loader)


class PrivateAssetLoaderContractTests(unittest.TestCase):
    def test_regular_copy_is_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "plugin"
            assets = root / "assets"
            assets.mkdir(parents=True)
            asset = assets / "asset.css"
            asset.write_text("body { color: green; }\n", encoding="utf-8")

            self.assertEqual(
                "body { color: green; }\n",
                loader.read_private_asset(root, asset),
            )

    def test_external_hardlink_is_rejected_without_reading_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "plugin"
            assets = root / "assets"
            assets.mkdir(parents=True)
            outside = Path(directory) / "outside-private.txt"
            outside.write_text("PRIVATE-CANDIDATE-CONTENT\n", encoding="utf-8")
            asset = assets / "asset.css"
            os.link(outside, asset)

            with self.assertRaises(loader.PrivateAssetError) as raised:
                loader.read_private_asset(root, asset)

            self.assertNotIn("PRIVATE-CANDIDATE-CONTENT", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
