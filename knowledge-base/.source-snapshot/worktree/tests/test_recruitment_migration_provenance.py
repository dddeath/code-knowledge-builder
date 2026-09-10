"""真实小仓库中的快照登记、引用证据与目录切换回归。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ckb_core.common import CkbError, json_load, json_write
from ckb_core.gitrepo import create_source_snapshot, preflight
from ckb_core.migration import _preserve_mutable_layers, migrate_output
from ckb_core.pipeline import _relocate_completed_output, _replace_output_prefix, initialize, finalize
from ckb_core.reference_documents import ingest_reference, project_references, submit_reference_review, audit_references
from test_migration import review_all


def git(repo, *args, check=True):
    p = subprocess.run(["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
                        "-C", str(repo), *args], capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr)
    return p


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ckb-provenance-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init")
        (self.repo / "app.py").write_text("def double(value):\n    return value * 2\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "-m", "fixed fixture")
        self.old = self.root / "old"
        self.new = self.root / "new"

    def test_snapshot_registration_survives_two_renames_cleanup_and_rollback(self):
        repository = preflight(self.repo)
        snapshot = create_source_snapshot(repository, self.old)
        state = {"repository": repository, "source_snapshot": snapshot}
        admin = Path(git(Path(snapshot["root"]), "rev-parse", "--absolute-git-dir").stdout.strip())
        self.assertTrue((admin / "locked").is_file(), "active snapshot must be locked")
        original_gitfile = (Path(snapshot["root"]) / ".git").read_bytes()
        current = self.old
        for destination in (self.new, self.root / "second", self.old):
            current.rename(destination)
            state = _relocate_completed_output(destination, state)
            root = destination / ".source-snapshot/worktree"
            self.assertEqual(Path((admin / "gitdir").read_text().strip()).resolve(), (root / ".git").resolve())
            self.assertEqual(git(root, "rev-parse", "HEAD").stdout.strip(), repository["commit"])
            self.assertTrue((admin / "locked").is_file())
            # A targeted cleanup of a different worktree must not touch the fixed snapshot.
            other = self.root / "disposable"
            git(self.repo, "worktree", "add", "--detach", str(other), "HEAD")
            git(self.repo, "worktree", "remove", str(other))
            self.assertTrue((admin / "HEAD").is_file())
            current = destination
        self.assertEqual((self.old / ".source-snapshot/worktree/.git").read_bytes(), original_gitfile)

    def test_relocation_repairs_relative_gitdir_after_depth_change(self):
        repository = preflight(self.repo)
        snapshot = create_source_snapshot(repository, self.old)
        root = Path(snapshot["root"])
        admin = Path(git(root, "rev-parse", "--absolute-git-dir").stdout.strip())
        with (root / ".git").open("r+", encoding="utf-8", newline="") as stream:
            stream.seek(0)
            stream.write("gitdir: " + os.path.relpath(admin, root).replace("\\", "/") + "\n")
            stream.truncate()
        moved = self.root / "nested" / "moved"
        moved.parent.mkdir()
        self.old.rename(moved)
        state = _relocate_completed_output(moved, {"repository": repository, "source_snapshot": snapshot})
        self.assertEqual(git(Path(state["source_snapshot"]["root"]), "rev-parse", "HEAD").stdout.strip(), repository["commit"])
        self.assertEqual(Path((admin / "gitdir").read_text().strip()).resolve(), moved / ".source-snapshot/worktree/.git")

    def test_dirty_or_foreign_registration_fails_before_backlink_write(self):
        repository = preflight(self.repo)
        snapshot = create_source_snapshot(repository, self.old)
        root = Path(snapshot["root"])
        admin = Path(git(root, "rev-parse", "--absolute-git-dir").stdout.strip())
        original = (admin / "gitdir").read_bytes()
        self.old.rename(self.new)
        (self.new / ".source-snapshot/worktree/app.py").write_text("changed")
        with self.assertRaises(CkbError):
            _relocate_completed_output(self.new, {"repository": repository, "source_snapshot": snapshot})
        self.assertEqual((admin / "gitdir").read_bytes(), original)
        (self.new / ".source-snapshot/worktree/app.py").write_text("def double(value):\n    return value * 2\n")
        (admin / "gitdir").write_text(str(self.root / "foreign/.git") + "\n")
        foreign = (admin / "gitdir").read_bytes()
        with self.assertRaises(CkbError):
            _relocate_completed_output(self.new, {"repository": repository, "source_snapshot": snapshot})
        self.assertEqual((admin / "gitdir").read_bytes(), foreign)

    def evidence_fixture(self):
        json_write(self.old / "workspace-meta/gaps/records/gap.json",
                   {"evidence_paths": ["machine/agent-packs/gap.json"],
                    "resolution_evidence_paths": ["machine/evidence/resolved.txt"]})
        json_write(self.old / "workspace-meta/notes/note.json",
                   {"query_record": str(self.old / "machine/agent-packs/note.json")})
        json_write(self.old / "references/manifests/reference.json",
                   {"evidence_paths": ["machine/evidence/reference.json"]})
        payloads = {
            "machine/agent-packs/gap.json": b'{"evidence_paths":["machine/evidence/nested.txt"]}\n',
            "machine/agent-packs/note.json": b'{"selected_entities":[]}\n',
            "machine/evidence/nested.txt": "原始嵌套证据\r\n".encode(),
            "machine/evidence/resolved.txt": b"closure evidence\n",
            "machine/evidence/reference.json": b'{"confirmed": true}\n',
            "machine/evidence/markdown.txt": b"linked original\n",
        }
        for relative, data in payloads.items():
            target = self.old / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (self.old / "machine/agent-packs/unreferenced.json").write_text("{}")
        json_write(self.old / "workspace-meta/maintenance/latest.json",
                   {"index": {"path": str(self.old / "machine/knowledge.sqlite")}})
        (self.old / "machine/knowledge.sqlite").write_bytes(b"historical status target, not cited evidence")
        for vault in ("human", "markdown"):
            path = self.old / vault / "learning/原文.md"
            path.parent.mkdir(parents=True)
            path.write_bytes("原学习笔记，不改变正文。\r\n[来源证据](../../machine/evidence/markdown.txt)\r\n".encode())
        return payloads

    def test_preserves_only_referenced_machine_evidence_and_original_notes(self):
        payloads = self.evidence_fixture()
        records = _preserve_mutable_layers(self.old, self.new)
        for relative, data in payloads.items():
            self.assertTrue((self.new / relative).is_file(), relative)
            self.assertEqual((self.new / relative).read_bytes(), data)
            record = next(r for r in records if r["relative_target"] == relative)
            self.assertEqual((self.new / record["baseline_relative_target"]).read_bytes(), data)
        self.assertFalse((self.new / "machine/agent-packs/unreferenced.json").exists())
        self.assertFalse((self.new / "machine/knowledge.sqlite").exists())
        for vault in ("human", "markdown"):
            self.assertEqual((self.old / vault / "learning/原文.md").read_bytes(),
                             (self.new / vault / "learning/原文.md").read_bytes())
        self.assertEqual(json_load(self.new / "workspace-meta/notes/note.json")["query_record"],
                         str(self.new / "machine/agent-packs/note.json"))

    def test_missing_required_evidence_fails_without_empty_substitute(self):
        self.evidence_fixture()
        (self.old / "machine/agent-packs/gap.json").unlink()
        with self.assertRaisesRegex(CkbError, "evidence.*missing|missing.*evidence"):
            _preserve_mutable_layers(self.old, self.new)
        self.assertFalse((self.new / "machine/agent-packs/gap.json").exists())

    def test_prefix_relocation_does_not_rewrite_sibling_or_original_prose(self):
        old, new = str(self.old), str(self.new)
        original = {"path": old + "/machine/a.json", "sibling": old + "-backup/a.json",
                    "summary_zh": "原文提及 " + old + "/source.md"}
        actual = _replace_output_prefix(original, old, new)
        self.assertEqual(actual["path"], new + "/machine/a.json")
        self.assertEqual(actual["sibling"], original["sibling"])
        self.assertEqual(actual["summary_zh"], original["summary_zh"])

    def test_pdf_and_static_web_relocation_preserves_extraction_provenance(self):
        from ckb_core.reference_documents import ingest_web_reference
        from ckb_core.reference_pdf import validate_pdf_extraction
        from ckb_core.reference_inputs import validate_web_extraction
        from pdf_fixture_factory import ascii_pdf
        # This test is intentionally static: no server or network acquisition.
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        pdf = ascii_pdf(self.root / "native.pdf",
                        [[(72, 740, "A fixed native PDF paragraph preserves source provenance and text.")]])
        pdf_result = ingest_reference(self.old, pdf, "原生资料", "fixture", "CC0-1.0")
        html = self.root / "snapshot.html"
        html.write_text("<html>\n<body>\n<p>原始静态网页保留来源证据。</p>\n</body>\n</html>", encoding="utf-8")
        web_result = ingest_web_reference(self.old, "静态网页", "fixture", "CC0-1.0", snapshot=html,
                                         requested_url="https://example.test/article",
                                         final_url="https://example.test/article",
                                         retrieved_at_utc="2026-09-05T01:02:03Z", status_code=200,
                                         content_type="text/html; charset=utf-8",
                                         response_headers={"content-type": "text/html; charset=utf-8"})
        originals = {}
        for result in (pdf_result, web_result):
            manifest = json_load(Path(result["manifest"]))
            originals[manifest["reference_id"]] = Path(manifest["source_file"]).read_bytes()
        _preserve_mutable_layers(self.old, self.new)
        for manifest_path in (self.new / "references/manifests").glob("*.json"):
            manifest = json_load(manifest_path)
            validate = validate_pdf_extraction if manifest["source_type"] == "pdf" else validate_web_extraction
            _, errors = validate(self.new, manifest, require_ready=True)
            self.assertEqual(errors, [])
            self.assertEqual(Path(manifest["source_file"]).read_bytes(), originals[manifest["reference_id"]])
        from ckb_core.reference_documents import relocate_reference_paths
        moved = self.root / "renamed-extractions"
        self.new.rename(moved)
        relocate_reference_paths(moved, str(self.new), str(moved))
        for manifest_path in (moved / "references/manifests").glob("*.json"):
            manifest = json_load(manifest_path)
            validate = validate_pdf_extraction if manifest["source_type"] == "pdf" else validate_web_extraction
            self.assertEqual(validate(moved, manifest, require_ready=True)[1], [])
        moved.rename(self.new)
        relocate_reference_paths(self.new, str(moved), str(self.new))
        # A corrupt extraction is an error, not a new trusted digest.
        manifest = json_load(Path(pdf_result["manifest"]))
        with Path(manifest["extraction_file"]).open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(CkbError, "extraction.*drift"):
            _preserve_mutable_layers(self.old, self.root / "corrupt-target")

    def test_two_migrations_reproject_reference_and_navigation_at_target(self):
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        raw = self.root / "reference.md"
        raw.write_text("固定快照用于绑定来源。\n", encoding="utf-8")
        result = ingest_reference(self.old, raw, title="固定来源", origin="fixture",
                                  license_name="CC0-1.0")
        manifest = json_load(self.old / "references/manifests" / (result["reference_id"] + ".json"))
        review = json_load(Path(manifest["review_template"]))
        review.update(status="agent-reviewed", summary_zh="资料说明快照的来源绑定。",
                      claims=[{"claim_zh":"固定快照绑定来源。", "start_line":1, "end_line":1,
                               "source_text":"固定快照用于绑定来源。", "evidence_note":"已核对归档原文第一行。"}],
                      evidence_note="已打开归档原文，核对第一行来源。")
        review_path = self.root / "review.json"
        json_write(review_path, review)
        submit_reference_review(self.old, review_path)
        archived = Path(manifest["source_file"]).read_bytes()
        from ckb_core.research_gaps import create_gap, audit_gap_register
        from ckb_core.workspace_notes import record_note
        evidence = self.old / "machine/agent-packs/retained.json"
        json_write(evidence, {"selected_entities": [], "historical_path": str(self.old / "source.md")})
        evidence_bytes = evidence.read_bytes()
        summary = self.root / "gap.md"
        summary.write_text("固定来源仍需真实样本核验，保留检索原始证据。", encoding="utf-8")
        create_gap(self.old, "insufficient-evidence", summary, ["machine/agent-packs/retained.json"])
        title = json_load(self.old / "markdown/projection.json")["pages"][0]["title"]
        record_note(self.old, "analysis", "来源保留分析", summary, selectors=[title], query_record=evidence)
        for vault in ("human", "markdown"):
            learning = self.old / vault / "user/学习原文.md"
            learning.parent.mkdir(exist_ok=True)
            learning.write_text("学习原文逐字保留。\n", encoding="utf-8")
        # Mirrored malformed Markdown must fail, then the generator repairs it.
        for vault in ("human", "markdown"):
            page = self.old / vault / "references/固定来源.md"
            page.write_text(page.read_text().replace(")）", "）"))
        self.assertEqual(audit_references(self.old)["status"], "failed")
        project_references(self.old)
        self.assertEqual(audit_references(self.old)["status"], "passed")
        # Real legacy failure: local raw bytes exist but manifest links point
        # at a removed staging root rather than the current origin root.
        manifest_path = self.old / "references/manifests" / (result["reference_id"] + ".json")
        stale = json_load(manifest_path)
        for field in ("source_file", "review_file", "review_template"):
            stale[field] = stale[field].replace(str(self.old), str(self.root / "removed-staging"))
        json_write(manifest_path, stale)
        def assert_reference_sources(output, old_outputs):
            from urllib.parse import urlsplit

            page = (output / "human/references/固定来源.md").read_text(encoding="utf-8")
            links = re.findall(r"\]\((vscode://[^)]+)\)", page)
            self.assertEqual(len(links), 2)
            expected = (output / manifest["source_relative"]).resolve()
            for link in links:
                uri = urlsplit(link)
                self.assertEqual((uri.scheme, uri.netloc), ("vscode", "file"))
                local = unquote(re.sub(r":\d+:\d+$", "", uri.path))
                if re.match(r"^/[A-Za-z]:/", local):
                    local = local[1:]  # URI /C:/... becomes the native Windows drive path.
                target = Path(local).resolve()
                self.assertTrue(target.is_relative_to(output.resolve()))
                self.assertEqual(target, expected)
                self.assertTrue(target.is_file())
                self.assertEqual(target.read_bytes(), archived)
            normalized_page = unquote(page).replace("\\", "/")
            for old_output in old_outputs:
                self.assertNotIn(old_output.resolve().as_posix(), normalized_page)

        current = self.old
        for n in (1, 2):
            staging = self.root / f"staging-{n}"
            migrate_output(current, self.repo, staging)
            review_all(staging)
            finalize(staging)
            self.assertEqual(audit_gap_register(staging)["status"], "passed")
            self.assertEqual(audit_references(staging)["status"], "passed")
            assert_reference_sources(staging, [current, self.root / "removed-staging"])
            destination = self.root / f"promoted-{n}"
            staging.rename(destination)
            from ckb_core.pipeline import status
            status(destination)
            from ckb_core.migration import audit_migration
            self.assertEqual((destination / "machine/agent-packs/retained.json").read_bytes(), evidence_bytes)
            self.assertEqual(audit_gap_register(destination)["status"], "passed")
            self.assertEqual(audit_references(destination)["status"], "passed")
            self.assertEqual(audit_migration(destination)["status"], "passed")
            kept = destination / "machine/agent-packs/retained.json"
            kept.write_text("{}")
            self.assertEqual(audit_migration(destination)["status"], "failed")
            kept.write_bytes(evidence_bytes)
            for vault in ("human", "markdown"):
                self.assertEqual((destination / vault / "user/学习原文.md").read_text(), "学习原文逐字保留。\n")
            # No manual JSON or page patching; loading a renamed output refreshes its own links.
            assert_reference_sources(destination, [staging, current, self.root / "removed-staging"])
            for name in ("INDEX.md", "WIKI.md"):
                text = (destination / "human" / name).read_text(encoding="utf-8")
                normalized_text = unquote(text).replace("\\", "/")
                self.assertNotIn(staging.resolve().as_posix(), normalized_text)
            current = destination




def create_v3_record(test, output, package):
    import hashlib
    from ckb_core.human_page_authoring import package_page_author
    from ckb_core.workspace_notes import record_note
    from test_human_page_authoring import _change_payload

    payload = _change_payload()
    payload["title"] = "作者包迁移记录"
    payload["sections"]["deep-reading"]["human_summary"] = "[让 Agent 定位迁移实现](../INDEX.md#让-Agent-精确定位)。"
    payload["sections"]["deep-reading"]["links"][0]["target"] = "../INDEX.md#让-Agent-精确定位"
    source = test.root / "local-evidence.json"
    json_write(source, {"path": str(output / "original-path"), "result": "原证据字节保持不变"})
    payload["sections"]["result"]["machine_evidence_refs"] = [{
        "kind": "log", "target": str(source), "purpose": "复核作者包本地证据",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }]
    # A historical URI inside the signed evidence must not be rewritten.
    payload["sections"]["result"]["source_refs"] = [{
        "kind": "source", "target": (output / "historical-source.txt").as_uri(),
        "purpose": "保留历史来源标识，不将 URI 当作本地文件归档",
    }]
    packed = package_page_author(payload, package, workspace_root=test.root)
    test.assertEqual(packed["status"], "ready", packed)
    selector = json_load(output / "markdown/projection.json")["pages"][0]["title"]
    record = record_note(output, "change", payload["title"], package / "body.md", selectors=[selector])
    test.assertTrue(record["human_output_contract"]["v3_validated"])
    return record


class V3AuthoringMigrationTests(unittest.TestCase):
    def setUp(self):
        ProvenanceTests.setUp(self)
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        self.package = self.root / "external-authoring/package"
        self.record = create_v3_record(self, self.old, self.package)
        self.package_bytes = {p.relative_to(self.package).as_posix(): p.read_bytes()
                              for p in self.package.rglob("*") if p.is_file()}
        (self.package / "unreferenced.json").write_text('{"must_not_copy":true}')
        (self.package.parent / "unrelated.txt").write_text("not part of authoring package")

    def assert_package(self, output):
        from ckb_core.workspace_notes import note_contract_metadata, read_note_body

        meta = json_load(output / "workspace-meta/notes/作者包迁移记录.json")
        manifest = Path(meta["authoring_package"])
        self.assertTrue(manifest.is_relative_to(output), meta)
        self.assertTrue(manifest.is_file(), meta)
        actual = {p.relative_to(manifest.parent).as_posix(): p.read_bytes()
                  for p in manifest.parent.rglob("*") if p.is_file()}
        self.assertEqual(actual, self.package_bytes)
        verified = note_contract_metadata(manifest.parent / "body.md", meta["kind"],
                                          read_note_body(manifest.parent / "body.md"))
        for field in ("validation_context", "section_evidence", "section_evidence_sha256"):
            self.assertEqual(meta[field], self.record[field])
            self.assertEqual(meta[field], verified[field])
        return manifest

    def test_real_v3_record_survives_two_migrations_rename_maintain_and_rollback(self):
        from ckb_core.llm_wiki_capabilities import maintenance_check
        from ckb_core.pipeline import status
        from ckb_core.migration import audit_migration

        original_note = (self.old / "human/changes/作者包迁移记录.md").read_bytes()
        current = self.old
        for n in (1, 2):
            staging = self.root / f"v3-staging-{n}"
            migrate_output(current, self.repo, staging)
            self.assert_package(staging)
            if n == 1:
                shutil.rmtree(self.package.parent)
                (self.root / "local-evidence.json").unlink()
            else:
                # The second migration must not depend on the first archive either.
                shutil.rmtree(self.assert_package(current).parent)
            review_all(staging)
            finalize(staging)
            self.assertEqual(maintenance_check(staging)["status"], "passed")
            promoted = self.root / f"v3-promoted-{n}"
            staging.rename(promoted)
            status(promoted)
            self.assert_package(promoted)
            self.assertEqual((promoted / "human/changes/作者包迁移记录.md").read_bytes(), original_note)
            self.assertEqual(maintenance_check(promoted)["status"], "passed")
            self.assertEqual(audit_migration(promoted)["status"], "passed")
            # Roll directory promotion back, then promote again; keep frozen bytes.
            promoted.rename(staging)
            status(staging)
            self.assert_package(staging)
            self.assertEqual(maintenance_check(staging)["status"], "passed")
            staging.rename(promoted)
            status(promoted)
            current = promoted
        # Verification is rerun, not inferred from retained record counts.
        manifest = self.assert_package(current)
        (manifest.parent / "body.md").write_text("已漂移正文", encoding="utf-8")
        self.assertEqual(audit_migration(current)["status"], "failed")
        self.assertEqual(maintenance_check(current)["status"], "failed")

    def test_missing_drifted_or_detached_metadata_fails_before_staging_write(self):
        body = self.package / "body.md"
        evidence = next(path for path in self.package.rglob("*.json") if path.name not in {"manifest.json", "unreferenced.json"})
        for label, operation in (
            ("missing-body", lambda: body.unlink()),
            ("drifted-body", lambda: body.write_bytes(b"changed")),
            ("missing-manifest", lambda: (self.package / "manifest.json").unlink()),
            ("missing-local-evidence", lambda: evidence.unlink()),
            ("drifted-local-evidence", lambda: evidence.write_bytes(b"changed")),
        ):
            with self.subTest(label=label):
                for relative, data in self.package_bytes.items():
                    target = self.package / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                operation()
                target = self.root / label
                with self.assertRaises(CkbError):
                    migrate_output(self.old, self.repo, target)
                self.assertFalse(target.exists())
                from ckb_core.knowledge_batch_migration import _cold_build
                cold = self.root / (label + "-cold")
                with self.assertRaises(CkbError):
                    _cold_build({"output": str(self.old), "repository": str(self.repo),
                                 "staging": str(cold), "scope_selectors": {}})
                self.assertFalse(cold.exists())
        for relative, data in self.package_bytes.items():
            (self.package / relative).write_bytes(data)
        meta_path = self.old / "workspace-meta/notes/作者包迁移记录.json"
        meta = json_load(meta_path)
        meta["validation_context"] = {"sections": {}, "current_facts": ["not the signed context"]}
        json_write(meta_path, meta)
        with self.assertRaises(CkbError):
            migrate_output(self.old, self.repo, self.root / "metadata-drift")
        self.assertFalse((self.root / "metadata-drift").exists())
        # Ordinary history reading remains available even when authoring evidence is broken.
        from ckb_core.machine_knowledge import retrieve_machine
        self.assertIn(retrieve_machine(self.old, "double", 1000)["status"], {"passed", "needs-source-read"})

    def test_workspace_package_is_preserved_without_mutating_signed_context(self):
        internal = self.old / "workspace-meta/authoring/package"
        shutil.copytree(self.package, internal)
        meta_path = self.old / "workspace-meta/notes/作者包迁移记录.json"
        meta = json_load(meta_path)
        meta["authoring_package"] = str(internal / "manifest.json")
        json_write(meta_path, meta)
        migrate_output(self.old, self.repo, self.new)
        self.assert_package(self.new)


class WindowsHiddenSnapshotTests(unittest.TestCase):
    setUp = ProvenanceTests.setUp

    def test_existing_gitfile_update_uses_nontruncating_open(self):
        from unittest.mock import patch
        repository = preflight(self.repo)
        snapshot = create_source_snapshot(repository, self.old)
        root = Path(snapshot["root"])
        admin = Path(git(root, "rev-parse", "--absolute-git-dir").stdout.strip())
        with (root / ".git").open("r+", encoding="utf-8") as stream:
            stream.seek(0)
            stream.write("gitdir: " + os.path.relpath(admin, root).replace("\\", "/") + "\n")
            stream.truncate()
        moved = self.root / "deeper" / "promoted"
        moved.parent.mkdir()
        self.old.rename(moved)
        gitfile = moved / ".source-snapshot/worktree/.git"
        original_open = Path.open
        modes = []

        def open_existing(path, mode="r", *args, **kwargs):
            if path == gitfile:
                modes.append(mode)
                if "w" in mode:
                    raise PermissionError("fixture models hidden-file truncating-open denial")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", open_existing):
            state = _relocate_completed_output(moved, {"repository": repository, "source_snapshot": snapshot})
        self.assertIn("r+", modes)
        self.assertEqual(git(Path(state["source_snapshot"]["root"]), "rev-parse", "HEAD").stdout.strip(), repository["commit"])

    @unittest.skipUnless(os.name == "nt", "requires native Windows hidden file attribute")
    def test_hidden_relative_gitfile_survives_depth_change_and_keeps_attribute(self):
        import ctypes
        repository = preflight(self.repo)
        snapshot = create_source_snapshot(repository, self.old)
        root = Path(snapshot["root"])
        admin = Path(git(root, "rev-parse", "--absolute-git-dir").stdout.strip())
        gitfile = root / ".git"
        with gitfile.open("r+", encoding="utf-8") as stream:
            stream.seek(0)
            stream.write("gitdir: " + os.path.relpath(admin, root).replace("\\", "/") + "\n")
            stream.truncate()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
        kernel.GetFileAttributesW.restype = ctypes.c_uint32
        kernel.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32]
        kernel.SetFileAttributesW.restype = ctypes.c_int
        attributes = kernel.GetFileAttributesW(str(gitfile))
        self.assertNotEqual(attributes, 0xFFFFFFFF)
        self.assertTrue(kernel.SetFileAttributesW(str(gitfile), attributes | 2))
        moved = self.root / "deeper" / "promoted"
        moved.parent.mkdir()
        self.old.rename(moved)
        state = _relocate_completed_output(moved, {"repository": repository, "source_snapshot": snapshot})
        new_root = Path(state["source_snapshot"]["root"])
        self.assertTrue(kernel.GetFileAttributesW(str(new_root / ".git")) & 2)
        self.assertEqual(git(new_root, "rev-parse", "HEAD").stdout.strip(), repository["commit"])
        self.assertEqual(Path((admin / "gitdir").read_text().strip()).resolve(), (new_root / ".git").resolve())


class SQLiteGapAuditLifecycleTests(unittest.TestCase):
    def setUp(self):
        ProvenanceTests.setUp(self)
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        self.summary = self.root / "summary.md"
        self.summary.write_text("跨平台索引替换仍需真实读取句柄释放证据。", encoding="utf-8")
        self.evidence = self.old / "machine/agent-packs/read-proof.json"
        json_write(self.evidence, {"selected_entities": []})

    def track_gap_connections(self, *, fail_query=False):
        import sqlite3
        from unittest.mock import patch
        original_connect = sqlite3.connect
        connections = []

        class TrackedConnection(sqlite3.Connection):
            closed_by_owner = False

            def close(self):
                self.closed_by_owner = True
                return super().close()

            def execute(self, sql, *args, **kwargs):
                if fail_query and "sqlite_master" in sql:
                    raise sqlite3.OperationalError("injected gap audit read failure")
                return super().execute(sql, *args, **kwargs)

        def connect(*args, **kwargs):
            # Observe only the precise audit reader, not unrelated managed caches.
            if sys._getframe(1).f_code.co_name == "audit_gap_register":
                kwargs["factory"] = TrackedConnection
                connection = original_connect(*args, **kwargs)
                connections.append(connection)  # Keep it live so GC cannot mask a missing close.
                return connection
            return original_connect(*args, **kwargs)

        return patch.object(sqlite3, "connect", connect), connections

    def test_create_gap_releases_reader_before_record_and_same_process_replace(self):
        import sqlite3
        from ckb_core.research_gaps import create_gap
        from ckb_core.workspace_notes import record_note
        from ckb_core.machine_knowledge import build_machine_knowledge

        tracked, connections = self.track_gap_connections()
        try:
            with tracked:
                created = create_gap(self.old, "insufficient-evidence", self.summary,
                                     ["machine/agent-packs/read-proof.json"])
            self.assertEqual(created["audit"]["status"], "passed")
            self.assertEqual(len(connections), 1)
            self.assertTrue(all(c.closed_by_owner for c in connections), "gap audit returned an open SQLite reader")
            with self.assertRaises(sqlite3.ProgrammingError):
                connections[0].execute("SELECT 1")
            title = json_load(self.old / "markdown/projection.json")["pages"][0]["title"]
            record_note(self.old, "analysis", "读取结束后重建", self.summary, selectors=[title], query_record=self.evidence)
            self.assertEqual(build_machine_knowledge(self.old)["status"], "passed")
            database = self.old / "machine/knowledge.sqlite"
            moved = database.with_name("same-process-replace.sqlite")
            database.replace(moved)
            moved.replace(database)
            self.assertEqual(build_machine_knowledge(self.old)["status"], "passed")
        finally:
            for connection in connections:
                connection.close()

    def test_gap_audit_query_exception_also_closes_reader(self):
        import sqlite3
        from ckb_core.research_gaps import create_gap, audit_gap_register
        from ckb_core.machine_knowledge import build_machine_knowledge

        setup, setup_connections = self.track_gap_connections()
        with setup:
            create_gap(self.old, "insufficient-evidence", self.summary, ["machine/agent-packs/read-proof.json"])
        for connection in setup_connections:
            connection.close()  # Isolate the exceptional read from fixture setup.
        tracked, connections = self.track_gap_connections(fail_query=True)
        try:
            with tracked, self.assertRaisesRegex(sqlite3.OperationalError, "injected"):
                audit_gap_register(self.old)
            self.assertEqual(len(connections), 1)
            self.assertTrue(connections[0].closed_by_owner, "exception left the audit reader open")
            self.assertEqual(build_machine_knowledge(self.old)["status"], "passed")
        finally:
            for connection in connections:
                connection.close()


class ReferenceWindowsPrefixTests(unittest.TestCase):
    setUp = ProvenanceTests.setUp

    def test_windows_history_prefix_matches_backslash_and_mixed_paths(self):
        old = "C:/archive/removed-staging"
        new = "D:/current/output"
        value = {
            "review_file": "C:\\archive\\removed-staging\\references\\reviews\\review.json",
            "review_template": "C:/archive\\removed-staging/references\\review-templates/review.json",
            "source_text": "C:\\archive\\removed-staging\\original.md",
            "sibling": "C:\\archive\\removed-staging-backup\\references\\review.json",
            "validation_context": {"target": "C:\\archive\\removed-staging\\original.md"},
        }
        result = _replace_output_prefix(value, old, new)
        self.assertEqual(result["review_file"], new + "/references/reviews/review.json")
        self.assertEqual(result["review_template"], new + "/references/review-templates/review.json")
        for field in ("source_text", "sibling", "validation_context"):
            self.assertEqual(result[field], value[field])

    def test_windows_history_reference_reprojects_existing_raw_and_review_bytes(self):
        from ckb_core.reference_documents import relocate_reference_paths

        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        source = self.root / "history-source.md"
        source.write_text("归档原文保持来源约束。\n", encoding="utf-8")
        result = ingest_reference(self.old, source, "历史路径资料", "fixture", "CC0-1.0")
        manifest_path = Path(result["manifest"])
        manifest = json_load(manifest_path)
        review = json_load(Path(manifest["review_template"]))
        review.update(status="agent-reviewed", summary_zh="资料说明归档原文的来源约束。",
                      claims=[{"claim_zh": "归档原文保留来源约束。", "start_line": 1, "end_line": 1,
                               "source_text": "归档原文保持来源约束。", "evidence_note": "已重新打开归档原文第一行核对。"}])
        review_path = self.root / "review.json"
        json_write(review_path, review)
        submit_reference_review(self.old, review_path)
        manifest = json_load(manifest_path)
        raw = Path(manifest["source_file"])
        raw_bytes = raw.read_bytes()
        archived_review = Path(manifest["review_file"])
        archived_review_bytes = archived_review.read_bytes()
        old_prefix = "C:/archive/removed-staging"
        for field in ("source_file", "review_file", "review_template"):
            relative = Path(manifest[field]).relative_to(self.old).as_posix()
            manifest[field] = (old_prefix + "/" + relative).replace("/", "\\")
        json_write(manifest_path, manifest)
        relocated = relocate_reference_paths(self.old, str(self.root / "prior-output"), str(self.old))
        self.assertIn(manifest_path.relative_to(self.old).as_posix(), relocated)
        manifest = json_load(manifest_path)
        self.assertEqual(Path(manifest["review_file"]).resolve(), archived_review.resolve())
        self.assertEqual(raw.read_bytes(), raw_bytes)
        self.assertEqual(archived_review.read_bytes(), archived_review_bytes)
        project_references(self.old)
        self.assertEqual(audit_references(self.old)["status"], "passed")
        # No digest is replaced to accept a changed archived original.
        raw.write_bytes(raw_bytes + b"changed")
        with self.assertRaisesRegex(CkbError, "source drift"):
            relocate_reference_paths(self.old, old_prefix, str(self.old))


class MigrationDirectoryDescriptionTests(unittest.TestCase):
    def setUp(self):
        ProvenanceTests.setUp(self)
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        from ckb_core.workspace_notes import record_note

        json_write(self.old / "machine/agent-packs/unreferenced.json", {"cache": "unreferenced"})
        json_write(self.old / "machine/agent-packs/old/nested-cache.json", {"cache": "also unreferenced"})
        self.body = self.root / "directory-description.md"
        self.body.write_text(
            "## 当前结论\n\n检索阅读包目录与实际引用的证据文件用途不同。\n\n"
            "| 路径 | 用途 |\n| --- | --- |\n"
            "| " + chr(96) + "machine/agent-packs" + chr(96) + " | 存放按需生成的检索阅读包。 |\n",
            encoding="utf-8",
        )
        title = json_load(self.old / "markdown/projection.json")["pages"][0]["title"]
        record_note(self.old, "experiment", "历史阅读包目录说明", self.body, selectors=[title])
        tick = chr(96)
        self.description = (
            "# 运行期路径说明\n\n"
            + "| 路径 | 用途 |\n| --- | --- |\n"
            + "| " + tick + "machine/agent-packs" + tick + " | 阅读包目录。 |\n"
            + "| " + tick + "machine/knowledge.sqlite.tmp" + tick + " | 构建中的临时数据库。 |\n"
            + "| " + tick + "machine/knowledge.sqlite" + tick + " | 当前检索索引。 |\n"
            + "| " + tick + "machine/agent-packs/unreferenced.json" + tick + " | 仅举例说明归档格式。 |\n"
            + "| " + tick + "machine/runtime/not-created.marker" + tick + " | 尚未生成的运行期路径示例。 |\n"
            + "\n语法示例：" + tick + "[示例](../../machine/agent-packs/missing-example.json)" + tick + "。\n"
        ).encode("utf-8")
        for vault in ("human", "markdown"):
            path = self.old / vault / "user/runtime-paths.md"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(self.description)
        self.assertTrue((self.old / "machine/knowledge.sqlite").is_file())
        self.assertFalse((self.old / "machine/knowledge.sqlite.tmp").exists())

    def test_existing_directory_description_migrates_without_copying_cache_tree(self):
        originals = {vault: (self.old / vault / "experiments/历史阅读包目录说明.md").read_bytes()
                     for vault in ("human", "markdown")}
        migrated = migrate_output(self.old, self.repo, self.new)
        self.assertIn(migrated["status"], {"ready-to-finalize", "pending-agent-review"})
        review_all(self.new)
        self.assertEqual(finalize(self.new)["status"], "complete")
        for vault, original in originals.items():
            self.assertEqual((self.new / vault / "experiments/历史阅读包目录说明.md").read_bytes(), original)
            self.assertEqual((self.old / vault / "experiments/历史阅读包目录说明.md").read_bytes(), original)
        for relative in ("machine/agent-packs/unreferenced.json", "machine/agent-packs/old/nested-cache.json"):
            self.assertFalse((self.new / relative).exists())
        for vault in ("human", "markdown"):
            self.assertEqual((self.old / vault / "user/runtime-paths.md").read_bytes(), self.description)
            self.assertEqual((self.new / vault / "user/runtime-paths.md").read_bytes(), self.description)
        plan = json_load(self.new / "migration/plan.json")
        preserved = {item["relative_target"] for item in plan["mutable_files"]}
        self.assertFalse(any(path.startswith("machine/agent-packs/") for path in preserved))
        self.assertNotIn("machine/knowledge.sqlite", preserved)
        self.assertNotIn("machine/knowledge.sqlite.tmp", preserved)

    def test_explicit_archives_from_links_and_machine_fields_are_preserved(self):
        from ckb_core.research_gaps import create_gap, audit_gap_register

        linked = self.old / "machine/agent-packs/linked-archive.json"
        field = self.old / "machine/agent-packs/field-archive.json"
        json_write(linked, {"evidence": "明确来源链接的归档原文"})
        json_write(field, {"evidence": "正式缺口的归档原文"})
        for vault in ("human", "markdown"):
            path = self.old / vault / "user/runtime-paths.md"
            path.write_bytes(self.description + "\n[读取明确来源](../../machine/agent-packs/linked-archive.json)\n".encode("utf-8"))
        summary = self.root / "explicit-gap.md"
        summary.write_text("实际来源需要正式证据文件核验，不能由说明性路径代替。", encoding="utf-8")
        create_gap(self.old, "insufficient-evidence", summary, ["machine/agent-packs/field-archive.json"])
        migrate_output(self.old, self.repo, self.new)
        review_all(self.new)
        self.assertEqual(finalize(self.new)["status"], "complete")
        self.assertEqual(audit_gap_register(self.new)["status"], "passed")
        for source in (linked, field):
            self.assertEqual((self.new / source.relative_to(self.old)).read_bytes(), source.read_bytes())
        self.assertFalse((self.new / "machine/agent-packs/unreferenced.json").exists())

    def test_missing_explicit_markdown_source_link_fails_before_staging(self):
        for vault in ("human", "markdown"):
            path = self.old / vault / "user/z-source-link.md"
            path.write_text("[读取缺失来源](../../machine/agent-packs/missing-linked.json)\n", encoding="utf-8")
        with self.assertRaisesRegex(CkbError, r"required migration evidence is missing: machine/agent-packs/missing-linked\.json"):
            migrate_output(self.old, self.repo, self.new)
        self.assertFalse(self.new.exists())

    def test_explicit_missing_evidence_file_still_fails_before_staging(self):
        from ckb_core.research_gaps import create_gap

        required = self.old / "machine/agent-packs/required.json"
        json_write(required, {"source": "required evidence"})
        summary = self.root / "gap-summary.md"
        summary.write_text("这一缺口需要保存被明确引用的检索证据文件。", encoding="utf-8")
        create_gap(self.old, "insufficient-evidence", summary, ["machine/agent-packs/required.json"])
        required.unlink()
        with self.assertRaisesRegex(CkbError, r"required migration evidence is missing: machine/agent-packs/required\.json"):
            migrate_output(self.old, self.repo, self.new)
        self.assertFalse(self.new.exists())

    def test_explicit_file_field_referencing_a_directory_still_fails(self):
        json_write(self.old / "workspace-meta/notes/directory-as-file.json",
                   {"query_record": "machine/agent-packs"})
        with self.assertRaisesRegex(CkbError, "required migration evidence is missing: machine/agent-packs"):
            migrate_output(self.old, self.repo, self.new)
        self.assertFalse(self.new.exists())


class MigrationTransactionArchiveTests(unittest.TestCase):
    def setUp(self):
        ProvenanceTests.setUp(self)
        previous = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        self.addCleanup(lambda: os.environ.pop("CKB_TEST_PROVIDER", None) if previous is None
                        else os.environ.__setitem__("CKB_TEST_PROVIDER", previous))
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        from ckb_core.workspace_notes import record_note
        from ckb_core.record_replace import replace_note

        self.pack = self.old / "machine/agent-packs/historical-query.json"
        json_write(self.pack, {"selected_entities": []})
        self.pack_bytes = self.pack.read_bytes()
        self.body = self.root / "record-body.md"
        self.body.write_text("## 当前结论\n\n第一版记录保存原检索依据。\n", encoding="utf-8")
        self.title = "替换后的当前记录"
        self.selector = json_load(self.old / "markdown/projection.json")["pages"][0]["title"]
        record_note(self.old, "analysis", self.title, self.body, selectors=[self.selector], query_record=self.pack)
        self.operations = []
        for version in (2, 3):
            self.body.write_text(f"## 当前结论\n\n第{version}版记录使用当前知识页作为依据。\n", encoding="utf-8")
            result = replace_note(self.old, "analysis", self.title, self.body, selectors=[self.selector])
            self.assertEqual(result["status"], "replaced")
            self.operations.append(Path(result["manifest"]).relative_to(self.old))
        self.meta_relative = "workspace-meta/notes/替换后的当前记录.json"
        self.assertIsNone(json_load(self.old / self.meta_relative)["query_record"])
        self.history = {path.relative_to(self.old).as_posix(): path.read_bytes()
                        for path in (self.old / "workspace-meta/record-replace").rglob("*") if path.is_file()}
        self.assertTrue(any(json.loads(content).get("query_record") == str(self.pack)
                            for relative, content in self.history.items() if relative.endswith(self.meta_relative)))
        self.pack.unlink()

    def test_two_replacements_migrate_current_record_and_freeze_transaction_history(self):
        import hashlib
        from ckb_core.migration import audit_migration
        from ckb_core.pipeline import status
        from ckb_core.record_replace import rollback_replacement

        page = self.old / "human/analysis/替换后的当前记录.md"
        original_page = page.read_bytes()
        # Also protect transaction bytes on a rename before any migration plan exists.
        renamed_origin = self.root / "renamed-origin"
        self.old.rename(renamed_origin)
        status(renamed_origin)
        self.old = renamed_origin
        for relative, original in self.history.items():
            self.assertEqual((self.old / relative).read_bytes(), original)
        migrate_output(self.old, self.repo, self.new)
        review_all(self.new)
        self.assertEqual(finalize(self.new)["status"], "complete")
        for relative, original in self.history.items():
            self.assertEqual((self.old / relative).read_bytes(), original)
            self.assertEqual((self.new / relative).read_bytes(), original)
            self.assertEqual(hashlib.sha256((self.new / relative).read_bytes()).hexdigest(),
                             hashlib.sha256(original).hexdigest())
        self.assertIsNone(json_load(self.new / self.meta_relative)["query_record"])
        self.assertEqual((self.new / "human/analysis/替换后的当前记录.md").read_bytes(), original_page)
        self.assertFalse((self.new / "machine/agent-packs/historical-query.json").exists())
        promoted = self.root / "promoted-history"
        self.new.rename(promoted)
        status(promoted)
        for relative, original in self.history.items():
            self.assertEqual((promoted / relative).read_bytes(), original)
        self.assertIsNone(json_load(promoted / self.meta_relative)["query_record"])
        self.assertEqual(audit_migration(promoted)["status"], "passed")
        # An archived transaction is not silently rebound for cross-OUTPUT replay.
        with self.assertRaisesRegex(CkbError, "OUTPUT differs"):
            rollback_replacement(promoted, promoted / self.operations[-1])
        self.assertIsNone(json_load(promoted / self.meta_relative)["query_record"])
        victim = promoted / self.operations[0]
        original = victim.read_bytes()
        victim.write_bytes(original + b" ")
        self.assertEqual(audit_migration(promoted)["status"], "failed")
        victim.write_bytes(original)
        self.assertEqual(audit_migration(promoted)["status"], "passed")
        promoted.rename(self.new)
        status(self.new)
        for relative, original in self.history.items():
            self.assertEqual((self.new / relative).read_bytes(), original)

    def test_pending_record_is_a_root_until_materialization_finishes(self):
        from ckb_core.migration import _referenced_machine_evidence
        from ckb_core.workspace_notes import queue_pending_note, materialize_pending_notes

        pending = queue_pending_note(
            self.old, "analysis", "已投影的排队记录", "## 当前结论\n\n排队记录使用当前源码页核验。",
            query_record=self.pack, changed_paths=["app.py"],
        )
        with self.assertRaisesRegex(CkbError, "historical-query"):
            _referenced_machine_evidence(self.old)
        # The normal materialization entry binds the current source page when
        # the old optional query pack is absent; its consumed queue is historical.
        results = materialize_pending_notes(self.old)
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["query_record"])
        self.assertEqual(json_load(Path(pending["record"]))["status"], "materialized")
        self.assertEqual(_referenced_machine_evidence(self.old), [])

    def test_same_missing_pack_is_required_when_current_record_or_formal_gap_references_it(self):
        from ckb_core.research_gaps import create_gap

        metadata_path = self.old / self.meta_relative
        original = metadata_path.read_bytes()
        metadata = json_load(metadata_path)
        metadata["query_record"] = str(self.pack)
        json_write(metadata_path, metadata)
        with self.assertRaisesRegex(CkbError, "historical-query"):
            migrate_output(self.old, self.repo, self.new)
        self.assertFalse(self.new.exists())
        metadata_path.write_bytes(original)
        self.pack.write_bytes(self.pack_bytes)
        summary = self.root / "active-gap.md"
        summary.write_text("正式缺口仍要求原检索文件作为证据。", encoding="utf-8")
        create_gap(self.old, "insufficient-evidence", summary, ["machine/agent-packs/historical-query.json"])
        self.pack.unlink()
        with self.assertRaisesRegex(CkbError, "historical-query"):
            migrate_output(self.old, self.repo, self.new)
        self.assertFalse(self.new.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
