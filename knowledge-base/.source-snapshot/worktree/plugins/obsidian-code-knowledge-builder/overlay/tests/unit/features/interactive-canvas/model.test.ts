import { copyDocument, editUnit, importUnits, newUnitPayload } from '@/features/interactive-canvas/model';

const original = () => ({
  nodes: [{ id: 'ordinary', type: 'text', text: '用户原有文字', x: 73, y: 91, width: 240, height: 170, thirdParty: { keep: true } }],
  edges: [{ id: 'user-edge', fromNode: 'ordinary', toNode: 'ordinary', label: '用户连线', thirdParty: 1 }],
  extension: { untouched: true },
});
function payload() {
  return { status: 'experimental-interchange-only', version: '0.1-draft', units: [
    { unit_id: 'root', parent_id: null, title: '功能', summary: '目录', implementation_summary: '设计', state: 'proposed', source_refs: [], session_refs: [] },
    { unit_id: 'child', parent_id: 'root', title: '子功能', summary: '正文', implementation_summary: '未实现', state: 'verified', source_refs: [{ path: 'sample.py', commit: 'opaque', sha256: 'opaque' }], session_refs: [] },
  ], relations: [] };
}
describe('原生白板功能节点数据', () => {
  it('保留普通节点、布局、边与第三方字段且不修改输入', () => {
    const before = original(), snapshot = JSON.stringify(before);
    const result = importUnits(before, payload());
    expect(JSON.stringify(before)).toBe(snapshot);
    expect(result.document.nodes[0]).toEqual(before.nodes[0]);
    expect(result.document.edges[0]).toEqual(before.edges[0]);
    expect(result.document.extension).toEqual(before.extension);
    expect(result.added).toHaveLength(2);
  });
  it('仅移除插件拥有的父子边，保留用户同端点连线', () => {
    const { document, added } = importUnits(original(), payload());
    document.edges.push({ id: 'same-endpoints', fromNode: added[0], toNode: added[1], label: '用户关系' });
    const changed = editUnit(document, added[1], { parent_id: null });
    expect(changed.edges.some(e => e.ckbFunctionParent === true)).toBe(false);
    expect(changed.edges.find(e => e.id === 'same-endpoints')).toEqual(document.edges.find(e => e.id === 'same-endpoints'));
  });
  it('重复导入保留已有编辑且不新增节点和边', () => {
    const result = importUnits(original(), payload());
    const edited = editUnit(result.document, result.added[0], { summary: '人工编辑' });
    const twice = importUnits(edited, payload());
    expect(twice.skipped).toBe(2);expect(twice.added).toEqual([]);expect(twice.document).toEqual(edited);
  });
  it('保存需求与人工确认，不把输入状态改成已验证', () => {
    const result = importUnits(original(), payload());
    const changed = editUnit(result.document, result.added[0], { requirement: '必须离线', human_confirmed: true, state: 'verified' });
    expect(changed.nodes[1].ckbFunction).toMatchObject({ requirement: '必须离线', human_confirmed: true, state: 'proposed' });
  });
  it('机器引用只进入扩展数据，不进入原生可见卡片文字', () => {
    const { document } = importUnits(original(), payload());
    expect(document.nodes[2].ckbFunction?.source_refs).toEqual(payload().units[1].source_refs);
    expect(document.nodes[2].text).not.toContain('opaque');expect(document.nodes[2].text).not.toContain('sha256');
    expect(copyDocument(JSON.parse(JSON.stringify(document)))).toEqual(document);
  });
  it('循环和悬空父级阻止写入', () => {
    const result = importUnits(original(), payload());
    expect(() => editUnit(result.document, result.added[0], { parent_id: 'child' })).toThrow('循环');
    expect(() => editUnit(result.document, result.added[0], { parent_id: 'missing' })).toThrow('不存在');
  });
  it('损坏白板和损坏功能元数据保持失败', () => {
    expect(() => copyDocument({ nodes: [], edges: null })).toThrow('格式');
    expect(() => copyDocument({ nodes: [{ id: 'x', ckbFunction: {} }], edges: [] })).toThrow('版本');
  });
  it('缺来源的设计节点可创建和保存', () => {
    const result = importUnits(original(), newUnitPayload('新设计', '尚无源码'));
    expect(result.document.nodes[1].ckbFunction?.source_refs).toEqual([]);
    expect(result.document.nodes[1].ckbFunction?.state).toBe('proposed');
  });
  it('损坏导入、重复标识与坏引用报错', () => {
    expect(() => importUnits(original(), {})).toThrow('格式');
    const duplicate = payload();duplicate.units.push(duplicate.units[0]);
    expect(() => importUnits(original(), duplicate)).toThrow('重复');
    const bad = payload() as unknown as { units: { source_refs: unknown }[] };bad.units[0].source_refs = 'broken';
    expect(() => importUnits(original(), bad)).toThrow('引用格式');
  });
});
