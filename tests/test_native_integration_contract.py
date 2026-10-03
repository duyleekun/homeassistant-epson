"""Static contract checks for the native Epson Home Assistant integration."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "epson_l3210"


class NativeIntegrationContractTest(unittest.TestCase):
    def test_hacs_and_manifest_metadata(self) -> None:
        hacs = json.loads((ROOT / "hacs.json").read_text())
        manifest = json.loads((INTEGRATION / "manifest.json").read_text())
        self.assertFalse(hacs["content_in_root"])
        self.assertEqual(manifest["domain"], "epson_l3210")
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["integration_type"], "device")
        self.assertIn("media_source", manifest["dependencies"])

    def test_all_declared_platforms_and_media_source_exist(self) -> None:
        for platform in (
            "binary_sensor",
            "button",
            "event",
            "image",
            "number",
            "select",
            "sensor",
            "text",
        ):
            self.assertTrue((INTEGRATION / f"{platform}.py").is_file())
        self.assertTrue((INTEGRATION / "media_source.py").is_file())

    def test_event_and_scan_contracts_are_declared(self) -> None:
        init_source = (INTEGRATION / "__init__.py").read_text()
        const_source = (INTEGRATION / "const.py").read_text()
        bridge_source = (
            ROOT / "apps" / "sane_l3210" / "rootfs" / "usr" / "local" / "bin" / "epson_ha_bridge.py"
        ).read_text()
        engine_source = (
            ROOT / "apps" / "sane_l3210" / "rootfs" / "usr" / "local" / "bin" / "epson_scan_engine.py"
        ).read_text()
        event_source = (INTEGRATION / "event.py").read_text()

        for event_type in ("button_pressed", "scan_completed", "scan_failed"):
            self.assertIn(event_type, event_source)
        self.assertIn("epson_l3210_scan_request", bridge_source)
        self.assertIn("epson_l3210_activity", engine_source)
        self.assertIn('"fire_event"', engine_source)
        self.assertIn("SUPERVISOR_WS_URL", engine_source)
        self.assertIn("def scan_sane", engine_source)
        self.assertIn("trying SANE fallback", bridge_source)
        self.assertIn("SERVICE_SCAN_SCHEMA", init_source)
        for resolution in ("100", "200", "300"):
            self.assertIn(resolution, const_source)
        self.assertIn('"color"', const_source)
        self.assertIn('"grayscale"', const_source)

    def test_scanner_has_no_web_ingress_and_keeps_sane(self) -> None:
        config = (ROOT / "apps" / "sane_l3210" / "config.yaml").read_text()
        self.assertIn("homeassistant_api: true", config)
        self.assertIn("6566/tcp: 6566", config)
        self.assertNotIn("ingress:", config)
        self.assertNotIn("ingress_port:", config)
        self.assertFalse((ROOT / "apps" / "sane_l3210" / "scanweb").exists())

    def test_python_sources_parse(self) -> None:
        sources = list(INTEGRATION.glob("*.py")) + list(
            (ROOT / "apps" / "sane_l3210" / "rootfs" / "usr" / "local" / "bin").glob("*.py")
        )
        for source in sources:
            with self.subTest(source=source):
                ast.parse(source.read_text(), filename=str(source))


if __name__ == "__main__":
    unittest.main()
