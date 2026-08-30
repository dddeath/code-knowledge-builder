from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "package_release",
    ROOT / "scripts" / "package_release.py",
)
assert SPEC and SPEC.loader
PACKAGE_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE_RELEASE)


class PackageReleaseTests(unittest.TestCase):
    def test_core_packages_exclude_plugins_and_full_only_adds_runtime(self) -> None:
        lite = {path.relative_to(ROOT).as_posix() for path in PACKAGE_RELEASE.source_files(False)}
        full = {path.relative_to(ROOT).as_posix() for path in PACKAGE_RELEASE.source_files(True)}
        self.assertTrue(set(PACKAGE_RELEASE.CORE_REQUIRED_FILES) <= lite)
        self.assertFalse(any(path == "plugins" or path.startswith("plugins/") for path in lite | full))
        self.assertLess(lite, full)
        self.assertTrue(all(path.startswith("assets/runtime/win-x64/") for path in full - lite))

    def test_lite_manifest_retains_core_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = PACKAGE_RELEASE.build("lite", Path(temporary))
            manifest_path = Path(temporary) / f"code-knowledge-builder-lite-{PACKAGE_RELEASE.VERSION}.manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["content"]
            self.assertEqual("passed", result["status"])
            self.assertEqual("core", manifest["category"])
            self.assertTrue(manifest["capabilities"]["source_scanning"])
            self.assertTrue(manifest["capabilities"]["machine_sqlite_knowledge"])
            self.assertFalse(manifest["capabilities"]["bundled_offline_runtime"])
            self.assertFalse(manifest["capabilities"]["obsidian_companion_plugin"])
            with zipfile.ZipFile(result["archive"]) as archive:
                self.assertFalse(any("/plugins/" in name for name in archive.namelist()))

    def test_obsidian_plugin_is_independently_versioned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = PACKAGE_RELEASE.build("obsidian-plugin", Path(temporary))
            archive = Path(result["archive"])
            self.assertIn("code-knowledge-builder-obsidian-", archive.name)
            with zipfile.ZipFile(archive) as plugin_zip:
                self.assertEqual(list(PACKAGE_RELEASE.PLUGIN_FILES), plugin_zip.namelist())
                manifest = json.loads(plugin_zip.read("manifest.json"))
                self.assertEqual("0.8.0", manifest["version"])
                self.assertIn("deploy.py", plugin_zip.namelist())
                self.assertNotIn("SKILL.md", plugin_zip.namelist())


if __name__ == "__main__":
    unittest.main()
