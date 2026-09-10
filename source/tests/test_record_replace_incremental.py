import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_record_replace as base
from test_record_replace import _owned_snapshot
from test_ckb import invoke
from ckb_core import record_replace as rr
from ckb_core.workspace_notes import audit_notes
from ckb_core.output_contract import project_output_contract


class IncrementalRecordReplaceTests(unittest.TestCase):
    title = base.RecordReplaceTests.title
    setUpClass = classmethod(base.RecordReplaceTests.setUpClass.__func__)
    tearDownClass = classmethod(base.RecordReplaceTests.tearDownClass.__func__)
    setUp = base.RecordReplaceTests.setUp
    tearDown = base.RecordReplaceTests.tearDown
    _replace = base.RecordReplaceTests._replace
    other = '另一篇历史记录'

    def prepare_dangling(self, target=True):
        # The completed fixture is copied per test; bind its protocol and any
        # installed plugin contract to this copy before injecting historical links.
        project_output_contract(self.output, self.output / 'human')
        policy = invoke('agent-policy', 'install', '--out', str(self.output))
        self.assertEqual(policy.returncode, 0, policy.stderr)
        created = invoke('record', '--out', str(self.output), '--kind', 'change', '--title', self.other,
                         '--body', str(self.old_body), '--from-pack', str(self.pack))
        self.assertEqual(created.returncode, 0, created.stderr)
        for title in ([self.title, self.other] if target else [self.other]):
            for vault in ('human', 'markdown'):
                path = self.output / vault / 'changes' / (title + '.md')
                path.write_text(path.read_text(encoding='utf8') + '\n历史链接 [[已移除职责]]。\n', encoding='utf8')
        self.before = _owned_snapshot(self.output, self.title)

    def assert_target_unchanged(self):
        self.assertEqual(_owned_snapshot(self.output, self.title), self.before)

    def test_two_dangling_notes_can_be_repaired_one_at_a_time_without_claiming_maintenance(self):
        self.prepare_dangling()
        self.assertEqual(len(audit_notes(self.output)), 2)
        first = self._replace()
        self.assertEqual(first.returncode, 0, first.stderr)
        result = json.loads(first.stdout)
        self.assertEqual(result['status'], 'replaced')
        self.assertFalse(result['maintenance_verified'])
        pending = result['unresolved_baseline_diagnostics']
        self.assertEqual(pending, [{'reason':'note-link-dangling', 'path':'markdown/changes/' + self.other + '.md', 'target':'已移除职责'}])
        manifest = json.loads(Path(result['manifest']).read_text(encoding='utf8'))
        self.assertEqual(manifest['candidate_audit']['unresolved_baseline_diagnostics'], pending)
        self.assertEqual(manifest['verification']['unresolved_baseline_diagnostics'], pending)
        remaining = audit_notes(self.output)
        self.assertEqual(len(remaining), 1)
        self.assertTrue(remaining[0]['path'].endswith(self.other + '.md'))
        maintained = invoke('maintain', '--out', str(self.output))
        self.assertNotEqual(maintained.returncode, 0)
        self.assertIn('note-link-dangling', maintained.stdout)
        second = invoke('record', '--out', str(self.output), '--kind', 'change', '--title', self.other,
                        '--body', str(self.new_body), '--replace')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)['unresolved_baseline_diagnostics'], [])
        self.assertEqual(audit_notes(self.output), [])
        maintained = invoke('maintain', '--out', str(self.output))
        self.assertNotIn('note-link-dangling', maintained.stdout)
        self.assertEqual(maintained.returncode, 0, maintained.stdout + maintained.stderr)

    def test_target_retained_or_new_dangling_link_is_rejected_before_writes(self):
        self.prepare_dangling()
        for target in ['已移除职责', '新坏链']:
            with self.subTest(target=target):
                self.new_body.write_text('修订正文仍然引用 [[' + target + ']]。\n', encoding='utf8')
                failed = self._replace()
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('note-link-dangling', failed.stderr)
                self.assert_target_unchanged()

    def test_other_error_type_and_other_mirror_damage_remain_blocking(self):
        self.prepare_dangling()
        path = self.output / 'markdown/changes' / (self.other + '.md')
        original = path.read_bytes()
        for data in [original.replace('标签：#类型/变更'.encode(), '标签：#类型/分析'.encode()), original + '非镜像内容。\n'.encode()]:
            with self.subTest(data=data):
                path.write_bytes(data)
                failed = self._replace()
                self.assertNotEqual(failed.returncode, 0)
                self.assert_target_unchanged()
        path.write_bytes(original)

    def test_changed_other_candidate_is_not_waived_even_with_same_diagnostic(self):
        self.prepare_dangling()
        original = rr._copy_candidate_note_roots
        for extra in ['新增文字。', '[[新坏链]]', '[[已移除职责]]']:
            def changed(output, candidate):
                original(output, candidate)
                for vault in ('human', 'markdown'):
                    path = candidate / vault / 'changes' / (self.other + '.md')
                    path.write_text(path.read_text(encoding='utf8') + extra, encoding='utf8')
            with self.subTest(extra=extra), patch.object(rr, '_copy_candidate_note_roots', changed):
                with self.assertRaisesRegex(rr.CkbError, 'candidate audit failed'):
                    rr.replace_note(self.output, 'change', self.title, self.new_body)
                self.assert_target_unchanged()

    def test_target_mirror_and_promotion_failures_remain_strict_with_pending_diagnostics(self):
        self.prepare_dangling()
        for fault in ['candidate-mirror-diff', 'after-agent-index-note', 'after-machine-knowledge-note']:
            with self.subTest(fault=fault):
                with self.assertRaises(rr.CkbError):
                    rr.replace_note(self.output, 'change', self.title, self.new_body, fault=fault)
                self.assert_target_unchanged()

    def test_rollback_does_not_restore_a_dangling_target_and_compensates_exactly(self):
        self.prepare_dangling()
        first = self._replace()
        self.assertEqual(first.returncode, 0, first.stderr)
        result = json.loads(first.stdout)
        repaired = _owned_snapshot(self.output, self.title)
        rollback = invoke('record-rollback', '--out', str(self.output), '--manifest', result['manifest'])
        self.assertNotEqual(rollback.returncode, 0)
        self.assertIn('note-link-dangling', rollback.stderr)
        self.assertEqual(_owned_snapshot(self.output, self.title), repaired)


if __name__ == '__main__': unittest.main()
