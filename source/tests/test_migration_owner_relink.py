import copy
import json
from pathlib import Path
import tempfile
import unittest
from ckb_core.common import json_write
from ckb_core.pipeline import _logical_projection
from ckb_core.migration import relink_preserved_notes


def entity(identifier, name, path, classification='page', kind='function', owner=None):
    value = {'id':identifier,'name':name,'qualified_name':path if kind=='file' else name,
             'path':path,'kind':kind,'classification':classification,'owner_page_id':owner or identifier,
             'language':'python','parent_id':None,'commit':'fixed','blob':'blob',
             'range':{'start_line':1,'end_line':3,'start_byte':0,'end_byte':12}}
    if kind=='boundary': value['kind_original']='function'
    return value


def projection(graph):
    logical = _logical_projection(graph)
    return {'pages':[{k:p[k] for k in ('id','title','page_type')} for p in logical['pages']],
            'links':logical['links'],'entity_owner_pages':logical['entity_owner_pages']}


class MigrationOwnerRelinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ckb-owner-relink-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.old=self.root/'old'; self.new=self.root/'new'
        repository={'root':str(self.root/'repo'),'commit':'fixed'}
        self.old_graph={'repository':repository,'entities':[
            entity('old-file','a.py','src/a.py',kind='file'),
            entity('old-f','audit_migration','src/a.py'),
            entity('old-b','build','lib/builder.py','boundary','boundary'),
        ],'links':[]}
        self.new_graph={'repository':repository,'entities':[
            entity('new-file','a.py','src/a.py',kind='file'),
            entity('new-f','audit_migration','src/a.py','appendix',owner='new-file'),
            entity('new-b','build','lib/builder.py','boundary','boundary'),
        ],'links':[]}
        self.old_projection=projection(self.old_graph)
        for page in self.old_projection['pages']:
            if page['page_type']=='boundary': page['title']='build 的协作边界'
            if page['page_type']=='module': page['title']='旧模块导览'
            if page['page_type']=='repository': page['title']='旧仓库导览'
        self.new_projection=projection(self.new_graph)
        self.old_titles={p['id']:p['title'] for p in self.old_projection['pages']}
        json_write(self.old/'graph.json', self.old_graph)
        json_write(self.old/'markdown/projection.json', self.old_projection)
        self.original=('学习原文仍说 audit_migration，不改其含义。\r\n'
                       '[[audit_migration|原函数]]、[[build 的协作边界]]、[[旧模块导览]]、[[旧仓库导览]]\r\n'
                       '`[[audit_migration]]` 是语法示例。\r\n```text\r\n[[audit_migration]]\r\n```\r\n').encode()
        self.roles=[]
        for root in ('human','markdown'):
            path=f'{root}/user/学习笔记.md';p=self.new/path;p.parent.mkdir(parents=True);p.write_bytes(self.original)
            self.roles.append({'kind':'user-note','relative_target':path})
        for kind, path in [('referenced-machine-evidence','machine/evidence/original.md'),
                           ('authoring-package-file','workspace-meta/authoring/body.md'),
                           ('transaction-archive-file','workspace-meta/record-replace/archive.md')]:
            p=self.new/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(self.original)
            self.roles.append({'kind':kind,'relative_target':path})
        json_write(self.new/'migration/plan.json',{'origin':{'output':str(self.old)},'mutable_files':self.roles})

    def test_page_to_appendix_and_unique_aggregate_links_follow_actual_owner_projection(self):
        result=relink_preserved_notes(self.new,self.new_graph,self.new_projection)
        new_titles={p['id']:p['title'] for p in self.new_projection['pages']}
        self.assertEqual(result['title_map']['audit_migration'],new_titles['new-file'])
        self.assertIn('build 的协作边界',result['title_map'])
        self.assertIn('旧模块导览',result['title_map'])
        self.assertIn('旧仓库导览',result['title_map'])
        expected=self.original
        for old,new in result['title_map'].items():
            # Only the actual second-line links change, never examples/prose.
            lines=expected.splitlines(keepends=True)
            lines[1]=lines[1].replace(('[[%s]]'%old).encode(),('[[%s]]'%new).encode()).replace(('[[%s|'%old).encode(),('[[%s|'%new).encode())
            expected=b''.join(lines)
        for root in ('human','markdown'):
            self.assertEqual((self.new/root/'user/学习笔记.md').read_bytes(),expected)
        for role in self.roles[2:]: self.assertEqual((self.new/role['relative_target']).read_bytes(),self.original)
        self.assertFalse(result['unresolved_titles'])
        self.assertTrue(all(title in new_titles.values() for title in result['title_map'].values()))
        relink_preserved_notes(self.new,self.new_graph,self.new_projection)
        self.assertEqual((self.new/'human/user/学习笔记.md').read_bytes(),expected)

    def test_duplicate_semantic_entities_and_split_boundary_are_not_guessed(self):
        self.new_graph['entities'].append(entity('duplicate-f','audit_migration','src/a.py'))
        old_second=entity('old-b2','deploy','lib/builder.py','boundary','boundary')
        self.old_graph['entities'].append(old_second)
        old_boundary=next(p['id'] for p in self.old_projection['pages'] if p['page_type']=='boundary')
        self.old_projection['entity_owner_pages']['old-b2']=old_boundary
        self.new_graph['entities'].append(entity('new-b2','deploy','lib/builder.py'))
        json_write(self.old/'graph.json',self.old_graph);json_write(self.old/'markdown/projection.json',self.old_projection)
        result=relink_preserved_notes(self.new,self.new_graph,projection(self.new_graph))
        self.assertNotIn('audit_migration',result['title_map'])
        self.assertNotIn('build 的协作边界',result['title_map'])
        unresolved={v['old_title'] for v in result['unresolved_titles']}
        self.assertTrue({'audit_migration','build 的协作边界'}<=unresolved)
        text=(self.new/'human/user/学习笔记.md').read_text(encoding='utf8')
        self.assertIn('[[audit_migration|原函数]]',text)
        self.assertIn('[[build 的协作边界]]',text)

if __name__=='__main__': unittest.main()
