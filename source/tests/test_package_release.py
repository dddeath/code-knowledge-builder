from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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
RUNTIME_SPEC = importlib.util.spec_from_file_location(
    "build_runtime_payload",
    ROOT / "scripts" / "build_runtime_payload.py",
)
assert RUNTIME_SPEC and RUNTIME_SPEC.loader
BUILD_RUNTIME = importlib.util.module_from_spec(RUNTIME_SPEC)
RUNTIME_SPEC.loader.exec_module(BUILD_RUNTIME)


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
            self.assertTrue(manifest["capabilities"]["session_scoped_stdio"])
            self.assertFalse(manifest["capabilities"]["bundled_offline_runtime"])
            self.assertFalse(manifest["capabilities"]["obsidian_companion_plugin"])
            with zipfile.ZipFile(result["archive"]) as archive:
                self.assertFalse(any("/plugins/" in name for name in archive.namelist()))
                session_modules = [name for name in archive.namelist() if name.endswith("/scripts/ckb_core/session_stdio.py")]
                self.assertEqual(len(session_modules), 1)
                archive.extractall(Path(temporary) / "installed")
                package_root = Path(temporary) / "installed" / Path(session_modules[0]).parents[2]
                canary = subprocess.run(
                    [sys.executable, str(package_root / "scripts/ckb.py"), "stdio-session", "--help"],
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                )
                self.assertEqual(canary.returncode, 0, canary.stderr)
                self.assertIn("request", canary.stdout)
                self.assertIn("cleanup", canary.stdout)

    def test_full_runtime_locks_pypdf_without_expanding_lite_runtime_boundary(self) -> None:
        lock = json.loads((ROOT / "toolchain.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["lock_id"], BUILD_RUNTIME.RUNTIME_LOCK_ID)
        component = next(item for item in lock["components"] if item["name"] == "pypdf")
        self.assertEqual(component["version"], BUILD_RUNTIME.PYPDF_VERSION)
        self.assertEqual(component["license"], "BSD-3-Clause")
        self.assertEqual(component["distribution"], "full-win-x64")
        self.assertEqual(component["artifact_size"], BUILD_RUNTIME.PYPDF_WHEEL_SIZE)
        self.assertEqual(component["artifact_sha256"], BUILD_RUNTIME.PYPDF_WHEEL_SHA256)
        payload = PACKAGE_RELEASE.validate_full_payload(lock)
        with zipfile.ZipFile(payload) as archive:
            names = set(archive.namelist())
            self.assertTrue(set(BUILD_RUNTIME.PYPDF_REQUIRED) <= names)
            wheel = archive.read(f"sources/{BUILD_RUNTIME.PYPDF_WHEEL}")
            self.assertEqual(len(wheel), BUILD_RUNTIME.PYPDF_WHEEL_SIZE)
            self.assertEqual(PACKAGE_RELEASE.hashlib.sha256(wheel).hexdigest(), BUILD_RUNTIME.PYPDF_WHEEL_SHA256)
            metadata = archive.read(
                f"python/Lib/site-packages/pypdf-{BUILD_RUNTIME.PYPDF_VERSION}.dist-info/METADATA"
            ).decode("utf-8")
            self.assertIn(f"Version: {BUILD_RUNTIME.PYPDF_VERSION}", metadata.splitlines())
            self.assertIn("License-Expression: BSD-3-Clause", metadata.splitlines())
            self.assertEqual(
                archive.read(f"python/Lib/site-packages/pypdf-{BUILD_RUNTIME.PYPDF_VERSION}.dist-info/licenses/LICENSE"),
                archive.read(f"licenses/pypdf-{BUILD_RUNTIME.PYPDF_VERSION}/LICENSE"),
            )
            build_record = json.loads(archive.read("runtime-build-record.json"))
            self.assertFalse(build_record["pdf_runtime"]["ocr_engine_bundled"])
            self.assertEqual(build_record["pdf_runtime"]["version"], BUILD_RUNTIME.PYPDF_VERSION)
            with tempfile.TemporaryDirectory() as temporary:
                staged = Path(temporary)
                for name in BUILD_RUNTIME.PYPDF_REQUIRED:
                    archive.extract(name, staged)
                validated = BUILD_RUNTIME.validate_pdf_runtime(staged)
                self.assertEqual(validated["wheel_sha256"], BUILD_RUNTIME.PYPDF_WHEEL_SHA256)
        lite = {path.relative_to(ROOT).as_posix() for path in PACKAGE_RELEASE.source_files(False)}
        self.assertFalse(any(path.startswith("assets/runtime/win-x64/") for path in lite))

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
