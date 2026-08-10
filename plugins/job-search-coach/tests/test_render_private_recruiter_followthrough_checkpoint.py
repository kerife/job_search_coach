import copy
import datetime as dt
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_private_recruiter_followthrough_checkpoint.py"
FIXTURE = ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json"

spec = importlib.util.spec_from_file_location("checkpoint_renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)


class FollowthroughCheckpointRendererTests(unittest.TestCase):
    def test_cli_normalizes_invalid_as_of_to_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out.html"
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"), "--receipt", str(FIXTURE), "--output", str(output), "--as-of", "bad"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_normalizes_missing_required_receipt_to_input_error(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"), "--output", "/tmp/unwritten-checkpoint.html", "--as-of", "2026-08-08"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertNotIn("Traceback", result.stderr)
    def setUp(self):
        self.receipt = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.item = {
            "schema_version": "private-recruiter-followthrough-checkpoint-v1",
            "artifact_kind": "private_recruiter_followthrough_checkpoint",
            "locale": "en",
            "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"},
            "action_state": "completed", "observed_date": "2026-08-08",
            "next_measurement_event": "screen_prepared",
            "next_safe_action": "route_to_prepare-role-interviews",
            "delivery": {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "local_save_mode": "disabled"},
        }

    def test_all_states_and_locales_use_fixed_labels_and_omit_private_values(self):
        mapping = [("accepted", "unknown", "manual_reenter_private_prep"), ("deferred", "unknown", "clarify_context_before_reply"), ("declined", "unknown", "record_stop_decision"), ("completed", "screen_prepared", "route_to_prepare-role-interviews")]
        for locale in ("en", "es"):
            for state, event, action in mapping:
                item = copy.deepcopy(self.item); item.update(locale=locale, action_state=state, next_measurement_event=event, next_safe_action=action)
                html = renderer.render_checkpoint_html(item, self.receipt, as_of=dt.date(2026, 8, 8))
                self.assertIn(f'<html lang="{locale}">', html)
                self.assertNotIn("D-104", html); self.assertNotIn("F-105", html); self.assertNotIn("screen_requested", html)
                self.assertNotIn("<form", html.lower()); self.assertNotIn("<button", html.lower()); self.assertNotIn("javascript:", html.lower())

    def test_css_accessibility_hooks_and_deterministic_render(self):
        first = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        second = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertEqual(first, second)
        self.assertIn('<main id="main-content" class="checkpoint-shell" tabindex="-1">', first)
        for hook in ("@media print", "prefers-reduced-motion", "forced-colors", "@media (min-width"):
            self.assertIn(hook, first)

    def test_atomic_private_write_mode_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "checkpoint.html"
            renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8))
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError): renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8))
            renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8), force=True)
            self.assertFalse(any(path.name.startswith(".checkpoint.html.tmp-") for path in Path(directory).iterdir()))

    def test_invalid_receipt_is_rejected_before_render(self):
        bad = copy.deepcopy(self.receipt); bad["source_artifact_id"] = "D-999"
        with self.assertRaises(renderer.CheckpointRenderValidationError): renderer.render_checkpoint_html(self.item, bad, as_of=dt.date(2026, 8, 8))


if __name__ == "__main__": unittest.main()
