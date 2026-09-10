"""Real projection/record regressions for the recruitment human-output contract."""
from __future__ import annotations

import json
import os
import time
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_ckb import invoke as _invoke, make_repo, review_all, git
from ckb_core.pipeline import _relation_phrase
from ckb_core.human_page_authoring import package_page_author
from test_human_page_authoring import _change_payload


def invoke(*args, **kwargs):
    result = _invoke(*args, **kwargs)
    evidence_dir = os.environ.get("CKB_RECRUITMENT_EVIDENCE_DIR")
    if evidence_dir:
        root = Path(evidence_dir)
        root.mkdir(parents=True, exist_ok=True)
        record = {"command": result.args, "cwd": os.getcwd(), "exit_status": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr,
                  "environment": {"CKB_TEST_PROVIDER": "deterministic-fixture"}, "inputs": {}}
        if result.returncode and "--out" in args:
            out = Path(args[args.index("--out") + 1])
            for relative in ("audit/global.json", "markdown/readability-audit.json"):
                audit = out / relative
                if audit.is_file():
                    record["inputs"][str(audit)] = audit.read_text(encoding="utf-8")
        for index, arg in enumerate(args[:-1]):
            if arg == "--body":
                body = Path(args[index + 1])
                if body.is_file():
                    record["inputs"][str(body)] = body.read_text(encoding="utf-8")
                    manifest = body.parent / "manifest.json"
                    if manifest.is_file():
                        record["inputs"][str(manifest)] = manifest.read_text(encoding="utf-8")
        (root / f"{time.time_ns()}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


class RecruitmentOutputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='ckb-human-contract-')
        cls.root = Path(cls.temp.name)
        cls.repo = make_repo(cls.root)
        cls.output = cls.root / 'output'
        for args in [('init', '--repo', str(cls.repo), '--out', str(cls.output), '--format', 'markdown')]:
            result = invoke(*args)
            if result.returncode:
                raise AssertionError(result.stderr)
        review_all(cls.output)
        for command in ('merge', 'finalize'):
            result = invoke(command, '--out', str(cls.output))
            if result.returncode:
                raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_old_passed_report_does_not_hide_changed_output(self):
        page = next((self.output / 'human/pages').glob('*.md'))
        original = page.read_bytes()
        cached = (self.output / 'human/readability-audit.json').read_bytes()
        try:
            page.write_bytes(original + '\n## 验证摘要\n\nRan 237 tests\n'.encode())
            result = invoke('maintain', '--out', str(self.output))
            report = json.loads(result.stdout)
            self.assertIn('human_readability', report['failed_checks'], result.stdout)
            self.assertTrue(any('l4-evidence-leak' in str(e) for e in report['human_readability']['errors']))
            self.assertEqual((self.output / 'human/readability-audit.json').read_bytes(), cached)
        finally:
            page.write_bytes(original)

    def test_snapshot_failure_is_reported_not_hidden(self):
        path = self.output / 'state.json'
        original = path.read_bytes()
        state = json.loads(original)
        state['source_snapshot']['root'] = str(self.root / 'missing-snapshot')
        try:
            path.write_text(json.dumps(state), encoding='utf-8')
            result = invoke('maintain', '--out', str(self.output))
            report = json.loads(result.stdout)
            self.assertIn('fixed_source_snapshot', report['failed_checks'])
            self.assertEqual(report['checks']['fixed_source_snapshot']['status'], 'failed')
        finally:
            path.write_bytes(original)

    def test_newer_head_is_stale_but_query_remains_available(self):
        git(self.repo, 'commit', '--allow-empty', '-m', 'advance live HEAD')
        result = invoke('maintain', '--out', str(self.output))
        report = json.loads(result.stdout)
        self.assertEqual(report['fact_freshness']['stable_state'], 'stale-committed')
        self.assertEqual(report['status'], 'passed', result.stdout)
        self.assertNotIn('fact_freshness', report['failed_checks'])
        query = invoke('brief', '--out', str(self.output), 'OrderService', '--budget', '1000')
        self.assertEqual(query.returncode, 0, query.stderr)

    def test_record_rejects_l4_and_vague_copy_before_page_write(self):
        title = json.loads((self.output / 'markdown/projection.json').read_text())['pages'][0]['title']
        examples = ['通过 237 项测试。', 'python -m unittest discover -s tests',
                    '& PYTHON scripts\\ckb.py query --out OUTPUT "职责关键词" --budget 1500',
                    '负责处理当前模块的结构化输入或状态。', '[详情](https://example.com)']
        for i, bad in enumerate(examples):
            with self.subTest(bad=bad):
                body = self.root / 'body.md'
                body.write_text('## 当前结论\n\n订单保存写入文件。\n\n' + bad, encoding='utf-8')
                result = invoke('record', '--out', str(self.output), '--kind', 'analysis', '--title', f'反例{i}', '--body', str(body), '--link', title)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse((self.output / f'human/analysis/反例{i}.md').exists())

    def test_record_allows_useful_technical_summary_and_replace_rechecks(self):
        title = json.loads((self.output / 'markdown/projection.json').read_text())['pages'][0]['title']
        body = self.root / 'positive.md'
        body.write_text('## 当前结论\n\nSQLite 保存订单检索索引；测试覆盖订单写入和正数判断。延迟摘要为 12 ms，仅适用于本地小样本。\n', encoding='utf-8')
        result = invoke('record', '--out', str(self.output), '--kind', 'analysis', '--title', '订单检索边界', '--body', str(body), '--link', title)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.output / 'human/analysis/订单检索边界.md'
        original = page.read_bytes()
        body.write_text('## 当前结论\n\n订单保存功能通过 237 项测试。\n', encoding='utf-8')
        replaced = invoke('record', '--out', str(self.output), '--kind', 'analysis', '--title', '订单检索边界', '--body', str(body), '--replace')
        self.assertNotEqual(replaced.returncode, 0)
        self.assertEqual(page.read_bytes(), original)

    def test_actual_navigation_does_not_expose_commands_or_configuration(self):
        wiki = (self.output / 'human/WIKI.md').read_text(encoding='utf-8')
        index = (self.output / 'human/INDEX.md').read_text(encoding='utf-8')
        self.assertNotIn('```powershell', wiki)
        self.assertNotIn('page-config.json', wiki)
        self.assertNotIn('brief --profile', index)
        self.assertIn('## 各类页面负责什么', wiki)

    def test_candidate_is_not_confirmed_dependency(self):
        phrase = _relation_phrase({'type':'references', 'provider':'tree-sitter-lexical-candidate'}, '候选函数')
        self.assertIn('待核验', phrase)
        self.assertNotIn('会用到', phrase)
        self.assertIn('会调用', _relation_phrase({'type':'calls', 'provider':'language-server'}, '真实函数'))

    def test_new_projection_rejects_vague_prose_without_rewriting_source_reviews(self):
        from ckb_core.pipeline import _logical_projection, project_markdown, _readability_report, _human_page_filenames
        candidate = self.root / 'projection-candidate'
        shutil.copytree(self.output, candidate)
        try:
            graph = json.loads((candidate / 'graph.json').read_text())
            entity = next(e for e in graph['entities'] if e['classification'] == 'appendix')
            entity['description_zh'] = '负责处理当前模块的结构化输入或状态。'
            logical = _logical_projection(graph)
            projected = project_markdown(candidate, graph, logical)
            self.assertEqual(projected['readability_status'], 'failed')
            audit = json.loads((candidate / 'markdown/readability-audit.json').read_text())
            self.assertTrue(any(e['reason'] == 'uninformative-narrative-review-required' for e in audit['errors']))
            historical = _readability_report(candidate / 'markdown', graph, logical, _human_page_filenames(logical), historical=True)
            self.assertTrue(any(e['reason'] == 'uninformative-narrative-review-required' for e in historical['errors']))
            projection_path = candidate / 'markdown/projection.json'
            old_projection = json.loads(projection_path.read_text())
            old_projection.pop('content_contract')
            projection_path.write_text(json.dumps(old_projection), encoding='utf-8')
            historical = _readability_report(candidate / 'markdown', graph, logical, _human_page_filenames(logical), historical=True)
            self.assertTrue(any(e['reason'] == 'uninformative-narrative-review-required' for e in historical['warnings']))
            self.assertFalse(any(e['reason'] == 'uninformative-narrative-review-required' for e in historical['errors']))
            self.assertNotIn('处理当前模块', (self.output / 'graph.json').read_text())
        finally:
            shutil.rmtree(candidate)

    def test_graphify_advisory_is_exact_and_never_exempts_new_outputs(self):
        report = json.loads(invoke('maintain', '--out', str(self.output)).stdout)
        self.assertEqual(report['human_readability']['status'], 'passed', report)
        warnings = report['human_readability']['warnings']
        self.assertTrue(any(w.get('advisory_scope') == 'legacy-graphify-query-examples' for w in warnings))
        self.assertFalse(report['human_readability']['full_v3_coverage'])
        self.assertEqual(invoke('brief', '--out', str(self.output), 'OrderService', '--budget', '1000').returncode, 0)
        graph_report = self.output / 'graphify-out/GRAPH_REPORT.md'
        original = graph_report.read_bytes()
        try:
            graph_report.write_bytes(original + b'\nRan 237 tests\n')
            rejected = json.loads(invoke('maintain', '--out', str(self.output)).stdout)
            self.assertTrue(any(e.get('evidence_shape') == 'test-total' for e in rejected['human_readability']['errors']))
        finally:
            graph_report.write_bytes(original)
        command = '& PYTHON scripts\\ckb.py query --out OUTPUT "职责关键词" --budget 1500'
        for relative in ('INDEX.md', 'WIKI.md', 'RECORDS.md', next((self.output / 'human/pages').glob('*.md')).relative_to(self.output / 'human').as_posix()):
            path = self.output / 'human' / relative
            before = path.read_bytes()
            try:
                path.write_bytes(before + ('\n' + command + '\n').encode())
                rejected = json.loads(invoke('maintain', '--out', str(self.output)).stdout)
                self.assertTrue(any(e.get('evidence_shape') == 'complete-command' and e.get('path') == str(path) for e in rejected['human_readability']['errors']), relative)
            finally:
                path.write_bytes(before)

    def test_v3_package_record_and_replace_keep_machine_evidence_and_recheck(self):
        payload = _change_payload()
        payload['title'] = 'V3 订单记录'
        deep = payload['sections']['deep-reading']
        deep['human_summary'] = '[让 Agent 定位订单实现](../INDEX.md#让-Agent-精确定位)。'
        deep['links'][0]['target'] = '../INDEX.md#让-Agent-精确定位'
        evidence = self.root / 'result.txt'
        evidence.write_text('Ran 237 tests\n', encoding='utf-8')
        payload['sections']['result']['machine_evidence_refs'] = [{
            'kind': 'test-total', 'target': 'result.txt', 'purpose': '保留回归测试原始结果',
            'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest(),
        }]
        package = self.root / 'package'
        packed = package_page_author(payload, package, workspace_root=self.root)
        self.assertEqual(packed['status'], 'ready', packed)
        selector = json.loads((self.output / 'markdown/projection.json').read_text())['pages'][0]['title']
        created = invoke('record', '--out', str(self.output), '--kind', 'change', '--title', payload['title'], '--body', str(package / 'body.md'), '--link', selector)
        self.assertEqual(created.returncode, 0, created.stderr)
        meta = json.loads(created.stdout)
        self.assertEqual(meta['human_output_contract']['status'], 'v3-validated')
        self.assertTrue(meta['section_evidence']['sections'])
        page = Path(meta['file'])
        original = page.read_bytes()
        self.assertNotIn(b'237', original)
        self.assertNotIn('## 相关知识页', original.decode())
        self.assertEqual(original.decode().count('# V3 订单记录'), 1)
        raw = self.root / 'legacy-replacement.md'
        raw.write_text('## 结论\n\n订单写入由服务入口发起。', encoding='utf-8')
        failed = invoke('record', '--out', str(self.output), '--kind', 'change', '--title', payload['title'], '--body', str(raw), '--replace')
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(page.read_bytes(), original)
        payload['sections']['result']['human_summary'] = '订单保存和正数判断的覆盖边界保持独立。'
        next_package = self.root / 'replacement-package'
        self.assertEqual(package_page_author(payload, next_package, workspace_root=self.root)['status'], 'ready')
        replaced = invoke('record', '--out', str(self.output), '--kind', 'change', '--title', payload['title'], '--body', str(next_package / 'body.md'), '--replace')
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        self.assertIn('订单保存和正数判断', page.read_text(encoding='utf-8'))
        # A current body defect is found even when both mirrors and the cached
        # readability report look consistent to the old maintenance gate.
        mirror = Path(meta['compatibility_file'])
        saved = page.read_bytes()
        try:
            for target in (page, mirror):
                target.write_bytes(saved.replace('## 修改原因'.encode(), '## 未登记原因'.encode()))
            report = json.loads(invoke('maintain', '--out', str(self.output)).stdout)
            self.assertTrue(any(e.get('reason') == 'required-section-missing' for e in report['human_readability']['errors']))
        finally:
            page.write_bytes(saved)
            mirror.write_bytes(saved)

    def test_actual_projection_keeps_lexical_candidates_uncertain(self):
        from ckb_core.pipeline import _logical_projection, _render_markdown_page
        from ckb_core.source_links import ensure_local_openers
        graph = json.loads((self.output / 'graph.json').read_text())
        # Keep two actual page entities from different files, replacing only
        # this isolated fixture's relation set, not parser-owned production facts.
        entities = [e for e in graph['entities'] if e['classification'] == 'page' and e['kind'] != 'file']
        left = entities[0]
        right = next(e for e in entities if e['path'] != left['path'])
        graph['links'] = [{'id':'candidate-probe', 'source':left['id'], 'target':right['id'],
                           'type':'references', 'provider':'tree-sitter-lexical-candidate'}]
        logical = _logical_projection(graph)
        page = next(p for p in logical['pages'] if p['id'] == left['id'])
        titles = {p['id']:p['title'] for p in logical['pages']}
        text = _render_markdown_page(page, titles, logical['page_config'], ensure_local_openers(self.output, self.repo))
        self.assertIn('待核验的词法关联', text)
        self.assertNotIn(f'实现时会用到 [[{titles[right["id"]]}]]', text)


if __name__ == '__main__':
    unittest.main()
