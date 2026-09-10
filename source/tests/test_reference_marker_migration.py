from pathlib import Path
import unittest

import test_migration as base
from ckb_core.common import CkbError, json_load, json_write
from ckb_core import VERSION
from ckb_core.migration import _add_mutable_baseline, _preserve_mutable_layers, audit_migration
from ckb_core.pipeline import initialize, finalize
from ckb_core.reference_documents import ingest_reference, submit_reference_review, audit_references


class ReferenceMarkerMigrationTests(unittest.TestCase):
    setUp = base.MigrationTest.setUp
    tearDown = base.MigrationTest.tearDown

    def migrate_failed_reference_marker(self):
        initialize(self.repo, self.old, 'markdown', [], [], 1, 'both', [])
        base.review_all(self.old)
        finalize(self.old)
        source = self.root / 'reference.md'
        source.write_text('固定快照用于绑定来源。\n', encoding='utf8')
        result = ingest_reference(self.old, source, title='固定来源', origin='fixture', license_name='CC0-1.0')
        manifest = json_load(Path(result['manifest']))
        review = json_load(Path(manifest['review_template']))
        review.update(status='agent-reviewed', summary_zh='资料说明快照的来源绑定。',
                      claims=[{'claim_zh':'固定快照绑定来源。','start_line':1,'end_line':1,
                               'source_text':'固定快照用于绑定来源。','evidence_note':'已核对归档原文第一行。'}])
        reviewed = self.root / 'review.json';json_write(reviewed, review)
        submit_reference_review(self.old, reviewed)
        raw = Path(manifest['source_file']);original = raw.read_bytes()
        raw.write_bytes(original + '错误变更。'.encode())
        failed = audit_references(self.old)
        self.assertEqual(failed['status'], 'failed')
        self.assertIn('reference-source-drift', {e['reason'] for e in failed['errors']})
        self.failed_bytes = (self.old / 'references/.failed').read_bytes()
        raw.write_bytes(original)  # Correct source, retain the genuine prior failure marker.
        for relative in ['references/raw/.failed', 'references/user-state.txt']:
            p = self.old / relative;p.parent.mkdir(parents=True, exist_ok=True);p.write_bytes(b'preserve-me')
        initialize(self.repo, self.new, 'markdown', [], [], 1, 'both', [])
        base.review_all(self.new)
        finalize(self.new)
        roles = _preserve_mutable_layers(self.old, self.new)
        state = json_load(self.new / 'state.json')
        state['migration'] = {'target_version': VERSION}
        json_write(self.new / 'state.json', state)
        # Existing staging already has its graph; exercise the captured plan
        # against a real completed library, without rebuilding that graph.
        json_write(self.new / 'migration/plan.json', {
            'origin': {'output': str(self.old)}, 'target': {'commit': state['repository']['commit']},
            'files': {'reused': []}, 'entities': {'old_to_new_id_map': {}}, 'mutable_files': roles,
        })
        finalize(self.new)
        self.plan = json_load(self.new / 'migration/plan.json')
        self.marker = next(r for r in self.plan['mutable_files'] if r['relative_target'] == 'references/.failed')

    def test_successful_reference_rebuild_retires_failed_marker_but_keeps_baseline_and_legacy_plan(self):
        self.migrate_failed_reference_marker()
        result = audit_migration(self.new)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(finalize(self.new)['status'], 'complete')
        self.assertFalse((self.new / 'references/.failed').exists())
        self.assertTrue((self.new / 'references/.complete').is_file())
        saved = self.new / self.marker['baseline_relative_target']
        self.assertEqual(saved.read_bytes(), self.failed_bytes)
        self.assertEqual(self.marker['kind'], 'reference-status-marker')
        self.assertEqual(audit_references(self.new)['status'], 'passed')
        self.assertIn('references/.failed', result['retired_reference_status_markers'])
        self.marker['kind'] = 'reviewed-reference-source'
        json_write(self.new / 'migration/plan.json', self.plan)
        self.assertEqual(audit_migration(self.new)['status'], 'passed')
        saved.write_bytes(b'changed baseline')
        failed = audit_migration(self.new)
        self.assertEqual(failed['status'], 'failed')
        self.assertIn('preserved-baseline-missing-or-changed', str(failed))
        saved.write_bytes(self.failed_bytes)
        saved.unlink()
        self.assertEqual(audit_migration(self.new)['status'], 'failed')

    def test_missing_raw_manifest_review_and_non_marker_paths_still_block(self):
        self.migrate_failed_reference_marker()
        paths = ['references/raw/.failed', 'references/user-state.txt']
        paths += [r['relative_target'] for r in self.plan['mutable_files']
                  if r['relative_target'].startswith(('references/raw/', 'references/manifests/', 'references/reviews/'))
                  and r['relative_target'] != 'references/raw/.failed']
        self.assertTrue(any('/manifests/' in p for p in paths))
        self.assertTrue(any('/reviews/' in p for p in paths))
        for relative in paths:
            with self.subTest(path=relative):
                path = self.new / relative;raw = path.read_bytes();path.unlink()
                failed = audit_migration(self.new)
                self.assertEqual(failed['status'], 'failed')
                checks = next(c for c in failed['checks'] if c['name'] == 'mutable-layers-preserved')
                self.assertIn({'path':relative,'reason':'live-mutable-file-missing'}, checks['detail'])
                path.write_bytes(raw)
        self.assertEqual(audit_migration(self.new)['status'], 'passed')

    def test_current_reference_failures_are_not_hidden_by_marker_retirement(self):
        self.migrate_failed_reference_marker()
        raw_role = next(r for r in self.plan['mutable_files'] if r['relative_target'].startswith('references/raw/')
                        and r['relative_target'] != 'references/raw/.failed')
        path = self.new / raw_role['relative_target'];path.write_bytes(path.read_bytes() + b'changed')
        failed = audit_references(self.new)
        self.assertEqual(failed['status'], 'failed')
        with self.assertRaisesRegex(CkbError, 'reference source drifted'):
            finalize(self.new)
        self.assertEqual(json_load(self.new / 'references/audit.json')['status'], 'failed')

    def test_complete_and_pending_markers_follow_real_reference_state_transitions(self):
        self.migrate_failed_reference_marker()

        def capture(name):
            plan = json_load(self.new / 'migration/plan.json')
            plan['mutable_files'].append(_add_mutable_baseline(self.new, {
                'kind': 'reviewed-reference-source', 'relative_target': 'references/' + name,
            }))
            json_write(self.new / 'migration/plan.json', plan)

        capture('.complete')
        source = self.root / 'next.md'
        source.write_text('新资料说明版本边界。\n', encoding='utf8')
        ingested = ingest_reference(self.new, source, title='新资料', origin='fixture', license_name='CC0-1.0')
        self.assertEqual(audit_references(self.new)['status'], 'pending-agent-review')
        self.assertFalse((self.new / 'references/.complete').exists())
        self.assertEqual(audit_migration(self.new)['status'], 'passed')
        capture('.pending-agent-review')
        review = json_load(Path(ingested['review_template']))
        review.update(status='agent-reviewed', summary_zh='资料说明版本边界。', claims=[{
            'claim_zh':'新资料说明版本边界。', 'start_line':1, 'end_line':1,
            'source_text':'新资料说明版本边界。', 'evidence_note':'已核对归档原文第一行。',
        }])
        path = self.root / 'next-review.json';json_write(path, review)
        submit_reference_review(self.new, path)
        self.assertEqual(audit_references(self.new)['status'], 'passed')
        self.assertFalse((self.new / 'references/.pending-agent-review').exists())
        audited = audit_migration(self.new)
        self.assertEqual(audited['status'], 'passed', audited)
        self.assertIn('references/.pending-agent-review', audited['retired_reference_status_markers'])


if __name__ == '__main__': unittest.main()
