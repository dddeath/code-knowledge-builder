from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/human-maintenance-prompts'
CONTRACT = json.loads((FIXTURES/'readme-current.json').read_text(encoding='utf-8'))


def section(markdown, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', markdown, re.M | re.S)
    return match.group(1) if match else ''


def contract_errors(markdown):
    errors = []
    headings = re.findall(r'^## (.+)$', markdown, re.M)
    if headings != CONTRACT['headings']:
        errors.append('headings')
    first = section(markdown, '先选择你要完成的任务')
    rows = re.findall(r'^\| ([^|]+) \| \[([^]]+)\]\((#[^)]+)\) \| ([^|]*) \|$', first, re.M)
    if [row[1] for row in rows] != CONTRACT['task_links']:
        errors.append('three-task-entries')
    if len(rows) != 3 or any(not row[3].strip() for row in rows):
        errors.append('direct-results')
    all_headings = re.findall(r'^#{1,6} (.+)$', markdown, re.M)
    anchors = {re.sub(r'[^\w\u3400-\u9fff -]', '', text.lower()).replace(' ', '-') for text in all_headings}
    for target in re.findall(r'\]\(#([^)]+)\)', markdown):
        if unquote(target).lower() not in anchors:
            errors.append('broken-anchor')
    for heading in CONTRACT['prompt_sections']:
        body = section(markdown, heading)
        prompts = re.findall(r'```text\n(.*?)\n```', body, re.S)
        if not prompts or any(not text.strip() or len(text) > 700 for text in prompts):
            errors.append('copyable-prompt:' + heading)
    prompts = '\n'.join(re.findall(r'```text\n(.*?)\n```', markdown, re.S))
    if re.search(r'<[^>]+>|(?:repository|question|项目来源|发布版本)\s*=', prompts, re.I):
        errors.append('parameter-slots')
    install = section(markdown, '让 Agent 安装本项目')
    explain = section(markdown, '让 Agent 解释自己的项目')
    if '本次只安装，不为业务仓库建库' not in install or '已有可用版本时不要重复安装' not in install:
        errors.append('install-boundary')
    if '当前 Git 仓库' not in explain or '已有知识库' not in explain or '不要修改业务代码' not in explain:
        errors.append('explain-boundary')
    for body in (install, explain):
        if '**完成后，你应当得到：**' not in body:
            errors.append('completion-result')
    canvas = section(markdown, '想用白板看项目结构')
    if '可选的实验功能，不是使用 CKB 的前提' not in canvas or '保留已有设置和白板' not in canvas:
        errors.append('optional-canvas')
    if '只验收最终结果' in markdown:
        errors.append('obsolete-internal-acceptance')
    return sorted(set(errors))


class ReadmeHumanEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markdown = (ROOT/'README.md').read_text(encoding='utf-8')

    def test_current_readme_has_direct_entries_prompts_boundaries_and_valid_anchors(self):
        self.assertEqual([], contract_errors(self.markdown))

    def test_historical_v5_fixture_remains_unchanged_and_is_not_current_contract(self):
        historical = FIXTURES/CONTRACT['historical_fixture']
        self.assertEqual(CONTRACT['historical_sha256'], hashlib.sha256(historical.read_bytes()).hexdigest())
        old = json.loads(historical.read_text(encoding='utf-8'))
        self.assertNotEqual(old['headings'], CONTRACT['headings'])
        self.assertIn('安装后继续指挥 Agent', old['headings'])

    def test_deleted_entry_is_rejected(self):
        bad = re.sub(r'^\| 让当前 Agent 使用 CKB .*\n', '', self.markdown, flags=re.M)
        self.assertNotEqual(bad, self.markdown)
        self.assertIn('three-task-entries', contract_errors(bad))

    def test_broken_internal_link_is_rejected(self):
        bad = self.markdown.replace('](#让-agent-安装本项目)', '](#不存在的入口)', 1)
        self.assertIn('broken-anchor', contract_errors(bad))

    def test_restored_parameter_slots_are_rejected(self):
        bad = self.markdown.replace('本次只安装', '项目来源=<项目地址>，发布版本=<版本或分支>。本次只安装', 1)
        self.assertIn('parameter-slots', contract_errors(bad))

    def test_missing_prompt_result_or_optional_boundary_is_rejected(self):
        cases = [
            (self.markdown.replace('```text', '```bash', 1), 'copyable-prompt:了解本项目知识库结构'),
            (self.markdown.replace('**完成后，你应当得到：**', '**步骤：**'), 'completion-result'),
            (self.markdown.replace('可选的实验功能，不是使用 CKB 的前提', '使用 CKB 的必需功能'), 'optional-canvas'),
            (self.markdown.replace('本次只安装，不为业务仓库建库', '安装后立即建立业务知识库'), 'install-boundary'),
        ]
        for text, reason in cases:
            with self.subTest(reason=reason): self.assertIn(reason, contract_errors(text))

if __name__ == '__main__': unittest.main()
