"""公开小样本：真实 Tree-sitter 实体与 lexical_links，不代替编码成功率。"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ckb_core.parsers import parse_file, lexical_links


def graph(sources):
    entities = []
    data = {path: text.encode() if isinstance(text, str) else text for path, text in sources.items()}
    for path, source in data.items():
        parsed = parse_file({'commit': 'scope-fixture'}, {'id': 'file-' + path, 'path': path,
            'blob': hashlib.sha1(source).hexdigest(), 'language': 'python'}, source)
        assert parsed['parse']['status'] == 'passed', parsed['parse']
        entities.extend(parsed['entities'])
    by_id = {e['id']: (e['path'], e['qualified_name']) for e in entities}
    return {(by_id[e['source']], by_id[e['target']]) for e in lexical_links(entities, data)
            if e['type'] == 'references'}


# 每项只标注指定调用者的 references；目标列表为空表示没有可证明的项目实体目标。
CASES = [
    ('list-member', {'app.py': 'def check():\n    failed = []\n    failed.append("x")\n',
                     'test_noise.py': 'def test_case():\n    def append(): pass\n'}, ('app.py', 'check'), []),
    ('unknown-member', {'app.py': 'def append(): pass\ndef check(obj):\n    obj.append()\n'}, ('app.py', 'check'), []),
    ('local-call', {'app.py': 'def check():\n    def helper(): pass\n    helper()\n'}, ('app.py', 'check'), [('app.py', 'check.helper')]),
    ('sibling-scope', {'app.py': 'def owner():\n    def hidden(): pass\ndef check():\n    hidden()\n'}, ('app.py', 'check'), []),
    ('alias-import', {'app.py': 'from lib import work as alias\ndef check():\n    alias()\n', 'lib.py': 'def work(): pass\n'}, ('app.py', 'check'), [('lib.py', 'work')]),
    ('same-name-modules', {'app.py': 'from lib import work\ndef check():\n    work()\n', 'lib.py': 'def work(): pass\n', 'noise.py': 'def work(): pass\n'}, ('app.py', 'check'), [('lib.py', 'work')]),
    ('module-alias', {'app.py': 'import lib as service\ndef check():\n    service.work()\n', 'lib.py': 'def work(): pass\n', 'noise.py': 'def work(): pass\n'}, ('app.py', 'check'), [('lib.py', 'work')]),
    ('same-file', {'app.py': 'def work(): pass\ndef check():\n    work()\n', 'noise.py': 'def work(): pass\n'}, ('app.py', 'check'), [('app.py', 'work')]),
    ('argument-shadow', {'app.py': 'def work(): pass\ndef check(work):\n    work()\n'}, ('app.py', 'check'), []),
    ('assignment-shadow', {'app.py': 'def work(): pass\ndef check():\n    work = factory()\n    work()\n'}, ('app.py', 'check'), []),
    ('strings-comments', {'app.py': 'def work(): pass\ndef check():\n    "work"\n    # work()\n    pass\n'}, ('app.py', 'check'), []),
    ('nested-owner', {'app.py': 'def work(): pass\ndef check():\n    def inner():\n        work()\n'}, ('app.py', 'check'), []),
    ('relative-import', {'pkg/app.py': 'from .lib import work as alias\ndef check():\n    alias()\n', 'pkg/lib.py': 'def work(): pass\n'}, ('pkg/app.py', 'check'), [('pkg/lib.py', 'work')]),
    ('class-receiver', {'app.py': 'class Worker:\n    def work(self): pass\n    def check(self):\n        self.work()\n'}, ('app.py', 'Worker.check'), [('app.py', 'Worker.work')]),
    ('class-is-not-closure', {'app.py': 'class Worker:\n    def work(self): pass\n    def check(self):\n        work()\n'}, ('app.py', 'Worker.check'), []),
    ('comprehension-shadow', {'app.py': 'def work(): pass\ndef check(items):\n    return [work() for work in items]\n'}, ('app.py', 'check'), []),
    ('closure', {'app.py': 'def check():\n    def work(): pass\n    def inner():\n        work()\n'}, ('app.py', 'check.inner'), [('app.py', 'check.work')]),
]


def measurements():
    rows = []
    for name, sources, caller, expected in CASES:
        actual = {target for source, target in graph(sources) if source == caller}
        wanted = set(expected)
        rows.append({'case': name, 'caller': caller, 'expected': sorted(wanted), 'actual': sorted(actual),
                     'tp': len(actual & wanted), 'fp': len(actual - wanted), 'fn': len(wanted - actual)})
    totals = {key: sum(row[key] for row in rows) for key in ('tp', 'fp', 'fn')}
    return {'labels': rows, **totals, 'precision': totals['tp'] / (totals['tp'] + totals['fp']) if totals['tp'] + totals['fp'] else None,
            'recall': totals['tp'] / (totals['tp'] + totals['fn']), 'scope': '公开开发样本；非留出评测，非编码成功率'}


class RecruitmentRelationScopeTests(unittest.TestCase):
    def test_labeled_parser_cases(self):
        for name, sources, caller, expected in CASES:
            with self.subTest(case=name):
                self.assertEqual({t for s, t in graph(sources) if s == caller}, set(expected))

    def test_unrelated_tests_do_not_change_local_call(self):
        sources = {'app.py': 'def check():\n    def helper(): pass\n    helper()\n'}
        before = graph(sources)
        after = graph({**sources, 'tests/noise.py': 'def test_noise():\n    def helper(): pass\n'})
        self.assertEqual({e for e in after if e[0][0] == 'app.py'}, before)

    def test_additional_binding_boundaries(self):
        cases = [
            ('annotation', 'class Model: pass\ndef check(value: Model) -> Model: return value\n', [('app.py', 'Model')]),
            ('lambda', 'def work(): pass\ndef check():\n    callback = lambda work: work()\n', []),
            ('walrus', 'def work(): pass\ndef check(items):\n    [(work := item) for item in items]\n    work()\n', []),
            ('except', 'def work(): pass\ndef check():\n    try: pass\n    except Exception as work: work()\n', []),
            ('pattern', 'def work(): pass\ndef check(obj):\n    match obj:\n        case {"key": work}: work()\n', []),
            ('global', 'def work(): pass\ndef check():\n    global work\n    work()\n', [('app.py', 'work')]),
            ('global-write', 'def work(): pass\ndef mutate():\n    global work\n    work = factory()\ndef check(): work()\n', []),
            ('static', 'class Worker:\n    def work(self): pass\n    @staticmethod\n    def check(self): self.work()\n', []),
            ('receiver-write', 'class Worker:\n    def work(self): pass\n    def check(self):\n        self = factory()\n        self.work()\n', []),
        ]
        for label, source, expected in cases:
            with self.subTest(case=label):
                caller = ('app.py', 'Worker.check' if label in {'static', 'receiver-write'} else 'check')
                self.assertEqual({t for s, t in graph({'app.py': source}) if s == caller}, set(expected))

    def test_import_path_is_not_an_arbitrary_module_suffix(self):
        sources = {'app.py': 'import lib\ndef check(): lib.work()\n',
                   'unrelated/lib.py': 'def work(): pass\n'}
        self.assertEqual({t for s, t in graph(sources) if s == ('app.py', 'check')}, set())

    def test_attribute_store_and_delete_invalidate_only_matching_member(self):
        for operation in ('= lambda: 2', 'DELETE', '+= 1'):
            with self.subTest(receiver='module', operation=operation):
                mutation = 'del lib.work' if operation == 'DELETE' else 'lib.work ' + operation
                sources = {
                    'lib.py': 'def work(): return 1\ndef keep(): return 3\n',
                    'other.py': 'def work(): return 4\n',
                    'app.py': ('import lib\nimport lib as alias\nimport other\n'
                               'def caller():\n    ' + mutation + '\n'
                               '    alias.work()\n    lib.keep()\n    other.work()\n'
                               'def untouched():\n    lib.work()\n'),
                }
                edges = graph(sources)
                self.assertEqual({t for s, t in edges if s == ('app.py', 'caller')},
                                 {('lib.py', 'keep'), ('other.py', 'work')})
                self.assertIn((('app.py', 'untouched'), ('lib.py', 'work')), edges)
            for receiver, decorator in [('self', ''), ('cls', '    @classmethod\n')]:
                with self.subTest(receiver=receiver, operation=operation):
                    mutation = ('del ' + receiver + '.work' if operation == 'DELETE'
                                else receiver + '.work ' + operation)
                    source = ('class Worker:\n    def work(self): return 1\n'
                              '    def keep(self): return 3\n' + decorator +
                              '    def caller(' + receiver + '):\n        ' + mutation + '\n'
                              '        ' + receiver + '.work()\n        ' + receiver + '.keep()\n'
                              '    def untouched(self):\n        self.work()\n')
                    edges = graph({'app.py': source})
                    self.assertEqual({t for s, t in edges if s == ('app.py', 'Worker.caller')},
                                     {('app.py', 'Worker.keep')})
                    self.assertIn((('app.py', 'Worker.untouched'), ('app.py', 'Worker.work')), edges)

    def test_attribute_invalidation_reaches_nested_scope_not_unrelated_receiver(self):
        sources = {
            'lib.py': 'def work(): return 1\n',
            'app.py': ('import lib\n'
                       'def caller():\n    lib.work = lambda: 2\n'
                       '    def inner():\n        lib.work()\n'
                       'def untouched():\n    return lib.work()\n'),
        }
        edges = graph(sources)
        self.assertEqual({t for s, t in edges if s == ('app.py', 'caller.inner')}, set())
        self.assertIn((('app.py', 'untouched'), ('lib.py', 'work')), edges)

    def test_real_maintenance_append(self):
        paths = ['scripts/ckb_core/llm_wiki_capabilities.py', 'tests/test_management_agent.py']
        edges = graph({path: (ROOT / path).read_bytes() for path in paths})
        wrong = ((paths[0], 'maintenance_check'), (paths[1],
            'ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append'))
        self.assertNotIn(wrong, edges)


if __name__ == '__main__':
    if '--measure' in sys.argv:
        print(json.dumps(measurements(), ensure_ascii=False, indent=2))
    else:
        unittest.main()
