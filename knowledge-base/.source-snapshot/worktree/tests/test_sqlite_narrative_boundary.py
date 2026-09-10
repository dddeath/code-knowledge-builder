import unittest
from ckb_core.human_page_templates import human_output_errors

class SQLiteNarrativeBoundaryTests(unittest.TestCase):
    def test_implementation_descriptions_using_through_are_not_machine_results(self):
        examples = [
            '它维护两个 SQLite 索引，通过各文件替换和各索引事务顺序提交并在失败时补偿。',
            'SQLite 保存订单检索索引，调用方通过读取章节与来源链接定位实现。',
        ]
        for text in examples:
            with self.subTest(text=text): self.assertEqual([], human_output_errors(text))

    def test_explicit_database_check_results_remain_machine_evidence(self):
        examples = ['SQLite 完整性检查通过。', 'SQLite passed', 'SQLite: ok',
                    '完整性检查通过。', 'PRAGMA integrity_check', 'PRAGMA quick_check',
                    'agent-index.sqlite 完整性校验：已通过', 'knowledge.sqlite 检查结果: passed']
        for text in examples:
            with self.subTest(text=text):
                self.assertTrue(any(e.get('evidence_shape') == 'sqlite-state' for e in human_output_errors(text)))
