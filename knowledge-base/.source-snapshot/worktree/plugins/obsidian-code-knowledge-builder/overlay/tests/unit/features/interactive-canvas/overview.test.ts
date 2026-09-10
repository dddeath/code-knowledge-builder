import { editUnit } from '@/features/interactive-canvas/model';
import { buildOverview, expandOverview, mergeOverview, overviewCatalog } from '@/features/interactive-canvas/overview';

const entity = (id: string, extra = {}) => ({ id, name: id, qualified_name: id, kind: 'function', language: 'python', path: 'src/main.py', classification: 'page', review_status: 'agent-reviewed', role_zh: '读取输入并生成结果。', range: { start_line: 1 }, ...extra });
const input = () => ({ output: '/fixture', freshness: '陈旧事实', navigation: ['RECORDS.md'], graph: { schema_version: 4, repository: { root: '/source', commit: 'abc123' }, entities: [entity('a'), entity('b', { classification: 'appendix', owner_page_id: 'a' }), entity('c', { classification: 'boundary', path: '' })], links: [{ type: 'lexical-reference', source: 'a', target: 'b' }] } });
const generated = () => mergeOverview(null, buildOverview(input())).document;
const main = (d: ReturnType<typeof generated>) => d.nodes.find(n => String(n.ckbOverviewIdentity).includes('"a"'))!;

describe('职责页导航与稳定身份', () => {
  it('按页归属完整收纳辅助实体，词法关系不变成依赖线', () => {
    const d = generated(), all = overviewCatalog(d).nodes.flatMap(n => n.ckbOverviewDetails as { id: string; owner: string; category: string; source: string }[]);
    expect(all.map(d => d.id).sort()).toEqual(['a', 'b', 'c']);
    expect(all.find(d => d.id === 'b')?.owner).toBe(main(d).id);
    expect(all.find(d => d.id === 'c')?.category).toBe('明确边界');
    expect(all.find(d => d.id === 'a')?.source).toBe('vscode://file//source/src/main.py:1:1');
    expect(d.edges.every(e => e.label === '包含')).toBe(true);
  });
  it('同一顶级目录内六个不同职责均可导航，所有主要声明可展开且辅助归属正确', () => {
    const i = input();i.graph.entities = [];
    const duties = ['解析输入', '检索知识', '构建页面', '归档资料', '校验结果', '同步状态'];
    duties.forEach((d, n) => {
      const path = `src/feature${n}.py`;
      i.graph.entities.push(entity(`file${n}`, { kind: 'file', path, meaning_zh: `该聚合负责${d}。` }), entity(`main${n}`, { path, parent_id: `file${n}`, meaning_zh: `该功能负责${d}的公开入口。` }), entity(`helper${n}`, { path, classification: 'appendix', owner_page_id: `main${n}` }));
    });
    let d = mergeOverview(null, buildOverview(i)).document;
    const catalog = overviewCatalog(d);expect(catalog.nodes).toHaveLength(12);expect(d.nodes).toHaveLength(7);
    for (const title of duties) expect(catalog.nodes.some(n => n.ckbFunction!.title === title)).toBe(true);
    for (let n = 0; n < 6; n++) {
      const page = catalog.nodes.find(p => String(p.ckbOverviewIdentity).includes(`"main${n}"`))!;
      expect((page.ckbOverviewDetails as { id: string }[]).map(x => x.id)).toEqual([`main${n}`, `helper${n}`]);
      d = expandOverview(d, page.id);expect(d.nodes.some(x => x.id === page.id)).toBe(true);
      expect(d.edges.some(e => e.toNode === page.id && e.fromNode === page.ckbFunction!.parent_id)).toBe(true);
    }
    expect(d.nodes).toHaveLength(13);
  });
  it('空库只有总览；旧schema和重复实体id明确失败', () => {
    const i = input();i.graph.entities = [];expect(buildOverview(i).nodes).toHaveLength(1);
    expect(() => buildOverview({ ...input(), graph: { schema_version: 3, entities: [], links: [] } })).toThrow();
    i.graph.entities = [entity('a'), entity('a')];expect(() => buildOverview(i)).toThrow();
  });
  it('缺少语法范围和职责不编造业务说明', () => {
    const i = input();i.graph.entities[0] = entity('a', { range: null, review_status: 'pending', role_zh: 'invented', meaning_zh: '尚未核验的业务宣称' });
    expect(JSON.stringify(buildOverview(i))).not.toContain('业务宣称');expect(JSON.stringify(buildOverview(i))).toContain('职责待核验');
  });
  it('重复生成和磁盘往返幂等', () => {
    const d = generated();expect(mergeOverview(JSON.parse(JSON.stringify(d)), buildOverview(input())).document).toEqual(d);
  });
  it.each(['line', 'entity-id', 'rank', 'signature-line'] as const)('%s变化不重复卡片，保留布局文字需求和用户边', change => {
    const i = input();if (change === 'signature-line') Object.assign(i.graph.entities[0], { signature: 'a(value: int)' });
    const d = mergeOverview(null, buildOverview(i)).document, n = main(d);n.x = 777;n.text = '原生手改文字';n.ckbFunction!.requirement = '用户需求';
    d.edges.push({ id: 'user', fromNode: d.nodes[0].id, toNode: n.id, label: '用户连线' });
    if (change === 'line' || change === 'signature-line') i.graph.entities[0].range.start_line = 99;
    if (change === 'entity-id') { i.graph.entities[0].id = 'new-commit-a';Object.assign(i.graph.entities[1], { owner_page_id: 'new-commit-a' });i.graph.repository.commit = 'new-commit'; }
    if (change === 'rank') i.graph.entities.reverse();
    const r = mergeOverview(d, buildOverview(i)).document;
    expect(r.nodes.map(x => x.id).sort()).toEqual(d.nodes.map(x => x.id).sort());
    expect(r.nodes.find(x => x.id === n.id)?.text).toBe('原生手改文字');expect(r.nodes.find(x => x.id === n.id)?.x).toBe(777);
    expect(r.nodes.find(x => x.id === n.id)?.ckbFunction?.requirement).toBe('用户需求');expect(r.edges.find(e => e.id === 'user')).toEqual(d.edges.find(e => e.id === 'user'));
  });
  it('临时移出主要页再进入不失去所属身份或撞id', () => {
    const d = generated(), n = main(d);n.text = '人改';n.y = 500;d.edges.push({ id: 'user', fromNode: d.nodes[0].id, toNode: n.id });
    const i = input();i.graph.entities[0].classification = 'appendix';
    const absent = mergeOverview(d, buildOverview(i)).document;expect(absent.nodes.find(x => x.id === n.id)?.ckbGenerated).toBeTruthy();expect(absent.nodes.find(x => x.id === n.id)?.ckbOverviewRetired).toBe(true);
    const restored = mergeOverview(absent, buildOverview(input())).document;
    expect(restored.nodes.filter(x => x.id === n.id)).toHaveLength(1);expect(restored.nodes.find(x => x.id === n.id)?.text).toBe('人改');expect(restored.nodes.find(x => x.id === n.id)?.y).toBe(500);expect(restored.edges.find(e => e.id === 'user')).toBeTruthy();expect(restored.nodes.find(x => x.id === n.id)?.ckbOverviewRetired).toBe(false);
  });
  it('入口优先级实际改变初始排名，原来末位功能仍保持身份和人工布局', () => {
    const i = input();i.graph.entities = Array.from({ length: 7 }, (_, n) => entity(`f${n}`, { path: `src/f${n}.py` }));
    const d = mergeOverview(null, buildOverview(i)).document;
    const selected = d.nodes.find(n => String(n.ckbOverviewIdentity).includes('"f5"'))!;
    selected.x = 606;selected.y = 888;selected.text = '排名变化也保留';
    Object.assign(i.graph, { navigation_plan: { core_paths: ['src/f6.py'] } });
    const next = buildOverview(i);
    expect(next.nodes.some(n => n.id === selected.id)).toBe(false);
    const merged = mergeOverview(d, next).document;
    expect(merged.nodes.filter(n => n.id === selected.id)).toHaveLength(1);
    expect(merged.nodes.find(n => n.id === selected.id)).toMatchObject({ x: 606, y: 888, text: '排名变化也保留' });
    expect(new Set(merged.nodes.map(n => n.id)).size).toBe(merged.nodes.length);
  });
  it('真实移出图再进入仍复用卡片', () => {
    const d = generated(), i = input(), n = main(d);i.graph.entities = [];
    const absent = mergeOverview(d, buildOverview(i)).document;
    expect(mergeOverview(absent, buildOverview(input())).document.nodes.filter(x => x.id === n.id)).toHaveLength(1);
  });
  it('稳定签名区分同名重载；行号和实体id不是区分字段', () => {
    const i = input();i.graph.entities = [entity('a-int', { qualified_name: 'a', signature: 'a(int)' }), entity('a-str', { qualified_name: 'a', signature: 'a(string)' })];
    const before = overviewCatalog(buildOverview(i)).nodes.map(n => n.id).sort();
    i.graph.entities[0].id = 'new-int';i.graph.entities[0].range.start_line = 888;
    expect(overviewCatalog(buildOverview(i)).nodes.map(n => n.id).sort()).toEqual(before);expect(new Set(before).size).toBe(2);
  });
  it('用户删除不自动复活，显式导航可重新展开', () => {
    const d = generated(), n = main(d);d.nodes = d.nodes.filter(x => x.id !== n.id);
    const r = mergeOverview(d, buildOverview(input())).document;expect(r.nodes.some(x => x.id === n.id)).toBe(false);
    expect(expandOverview(r, n.id).nodes.some(x => x.id === n.id)).toBe(true);
  });
  it('旧0.9.0行号标识通过唯一来源映射迁移，用户边继续指向原功能', () => {
    const d = generated(), n = main(d), stable = n.id, originalId = 'legacy-line-key';
    n.id = originalId;n.ckbFunction!.unit_id = originalId;n.ckbFunction!.title = 'a · 主要功能';
    delete n.ckbOverviewIdentity;delete n.ckbOverviewSource;
    const s = n.ckbGenerated as { base: Record<string, unknown> };
    s.base.ckbFunction = { ...n.ckbFunction };n.text = '保留旧版手改';
    for (const e of d.edges) if (e.toNode === stable) e.toNode = originalId;
    d.edges.push({ id: 'human-old', fromNode: d.nodes[0].id, toNode: originalId });
    const r = mergeOverview(d, buildOverview(input())).document;
    expect(r.nodes.filter(x => x.id === stable)).toHaveLength(1);expect(r.nodes.some(x => x.id === originalId)).toBe(false);
    expect(r.nodes.find(x => x.id === stable)?.text).toBe('保留旧版手改');expect(r.edges.find(e => e.id === 'human-old')?.toNode).toBe(stable);
  });
  it('大库全部主要页仍可发现，首批卡片数不随实体平铺增长', () => {
    const i = input();i.graph.entities = [];
    for (let n = 0; n < 100; n++) {
      i.graph.entities.push(entity(`page${n}`, { path: `src/m${n}.py`, meaning_zh: `该页面负责职责${n}。` }));
      for (let a = 0; a < 99; a++) i.graph.entities.push(entity(`helper${n}-${a}`, { path: `src/m${n}.py`, classification: 'appendix', owner_page_id: `page${n}` }));
    }
    const d = buildOverview(i), catalog = overviewCatalog(d);
    expect(catalog.nodes).toHaveLength(100);expect(d.nodes).toHaveLength(7);
    expect(catalog.nodes.flatMap(n => n.ckbOverviewDetails as unknown[])).toHaveLength(10000);
    for (const n of catalog.nodes) expect(expandOverview(mergeOverview(null, d).document, n.id).nodes.some(x => x.id === n.id)).toBe(true);
  });
  it('展开其他功能不复活人工删除的生成边', () => {
    const i = input();i.graph.entities = Array.from({ length: 7 }, (_, n) => entity(`f${n}`));
    const d = mergeOverview(null, buildOverview(i)).document, removed = d.edges.shift()!;
    const hidden = overviewCatalog(d).nodes.find(n => !d.nodes.some(x => x.id === n.id))!;
    expect(expandOverview(d, hidden.id).edges.some(e => e.id === removed.id)).toBe(false);
  });
  it('同名用户画布不覆盖，已有功能编辑保留用户边', () => {
    expect(() => mergeOverview({ nodes: [], edges: [] }, buildOverview(input()))).toThrow('目标文件');
    const d = generated(), n = main(d);d.edges.push({ id: 'user', fromNode: d.nodes[0].id, toNode: n.id });
    const edited = editUnit(d, n.id, { parent_id: null });expect(edited.edges.some(e => e.id === 'user')).toBe(true);
  });
});
