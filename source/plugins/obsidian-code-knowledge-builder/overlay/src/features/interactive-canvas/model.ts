export interface FunctionUnit {
  version: 1;
  unit_id: string;
  parent_id: string | null;
  title: string;
  summary: string;
  implementation_summary: string;
  requirement: string;
  state: string;
  human_confirmed: boolean;
  source_refs: (string | Record<string, unknown>)[];
  session_refs: (string | Record<string, unknown>)[];
}
export interface CanvasNode extends Record<string, unknown> {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  ckbFunction?: FunctionUnit;
}
export interface CanvasEdge extends Record<string, unknown> {
  id: string;
  fromNode: string;
  toNode: string;
}
export interface CanvasDocument extends Record<string, unknown> {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}
const states = ['proposed', 'confirmed', 'in_progress', 'implemented', 'verified', 'superseded'];
function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
export function validateUnit(value: unknown): asserts value is FunctionUnit {
  if (!object(value) || value.version !== 1) throw new Error('功能节点数据版本无效。');
  for (const field of ['unit_id', 'title', 'summary', 'implementation_summary', 'requirement', 'state']) {
    if (typeof value[field] !== 'string') throw new Error('功能节点缺少文字字段。');
  }
  if (!(value.unit_id as string).trim() || !(value.title as string).trim()) throw new Error('功能标识与标题不能为空。');
  if (value.parent_id !== null && typeof value.parent_id !== 'string') throw new Error('父级格式无效。');
  if (!states.includes(value.state as string) || typeof value.human_confirmed !== 'boolean') throw new Error('功能节点状态无效。');
  for (const field of ['source_refs', 'session_refs']) {
    if (!Array.isArray(value[field]) || value[field].some((v: unknown) => typeof v !== 'string' && !object(v))) throw new Error('引用格式无效，原白板保持不变。');
  }
}
export function units(document: CanvasDocument): Map<string, CanvasNode> {
  const found = new Map<string, CanvasNode>();
  for (const node of document.nodes) {
    if (node.ckbFunction === undefined) continue;
    validateUnit(node.ckbFunction);
    if (found.has(node.ckbFunction.unit_id)) throw new Error('白板中有重复功能标识。');
    found.set(node.ckbFunction.unit_id, node);
  }
  return found;
}
function validateTree(found: Map<string, CanvasNode>): void {
  for (const node of found.values()) {
    let u = node.ckbFunction!;
    const seen = new Set<string>();
    while (true) {
      if (seen.has(u.unit_id)) throw new Error('父子关系形成循环，请选择其他父级。');
      seen.add(u.unit_id);
      if (seen.size > 32) throw new Error('功能层级超过 32 层。');
      if (u.parent_id === null) break;
      const parent = found.get(u.parent_id);
      if (!parent) throw new Error('父功能不存在，请先修正父级。');
      u = parent.ckbFunction!;
    }
  }
}
export function copyDocument(value: unknown): CanvasDocument {
  if (!object(value) || !Array.isArray(value.nodes) || !Array.isArray(value.edges)) throw new Error('白板格式损坏，未写入。');
  const ids = new Set<string>();
  for (const item of [...(value.nodes as unknown[]), ...(value.edges as unknown[])]) {
    if (!object(item) || typeof item.id !== 'string' || ids.has(item.id)) throw new Error('白板标识损坏或重复，未写入。');
    ids.add(item.id);
  }
  const document = JSON.parse(JSON.stringify(value)) as CanvasDocument;
  units(document);
  return document;
}
function caption(u: FunctionUnit): string {
  return `# ${u.title.replace(/[\r\n]+/g, ' ')}\n\n${u.summary.slice(0, 240)}`;
}
function hierarchy(document: CanvasDocument): void {
  const found = units(document);
  validateTree(found);
  document.edges = document.edges.filter(edge => edge.ckbFunctionParent !== true);
  document.edges = document.edges.filter(edge => {
    if (!edge.ckbGenerated) return true;
    const child = document.nodes.find(n => n.id === edge.toNode)?.ckbFunction;
    return !child || found.get(child.parent_id || '')?.id === edge.fromNode;
  });
  for (const node of found.values()) {
    const parentId = node.ckbFunction!.parent_id;
    if (parentId === null) continue;
    if (document.edges.some(e => e.ckbGenerated && e.fromNode === found.get(parentId)!.id && e.toNode === node.id)) continue;
    document.edges.push({ id: crypto.randomUUID(), fromNode: found.get(parentId)!.id, toNode: node.id,
      fromSide: 'right', toSide: 'left', label: '包含', ckbFunctionParent: true });
  }
}
export function editUnit(value: unknown, nodeId: string, update: Partial<FunctionUnit>): CanvasDocument {
  const document = copyDocument(value);
  const node = document.nodes.find(n => n.id === nodeId);
  if (!node?.ckbFunction) throw new Error('所选功能节点已不存在，请重新选择。');
  // 标识、来源与输入状态不是编辑表单的可写字段。
  node.ckbFunction = { ...node.ckbFunction, title: update.title ?? node.ckbFunction.title,
    summary: update.summary ?? node.ckbFunction.summary, requirement: update.requirement ?? node.ckbFunction.requirement,
    parent_id: update.parent_id === undefined ? node.ckbFunction.parent_id : update.parent_id,
    human_confirmed: update.human_confirmed ?? node.ckbFunction.human_confirmed };
  validateUnit(node.ckbFunction);
  node.text = caption(node.ckbFunction);
  hierarchy(document);
  return document;
}
export function importUnits(value: unknown, payload: unknown): { document: CanvasDocument; skipped: number; added: string[] } {
  const document = copyDocument(value);
  if (!object(payload) || payload.status !== 'experimental-interchange-only' || payload.version !== '0.1-draft'
    || !Array.isArray(payload.units) || !Array.isArray(payload.relations)) throw new Error('导入文件不是共同功能节点格式。');
  if (payload.units.length > 200) throw new Error('单次导入超过 200 个功能。');
  const found = units(document), incoming = new Set<string>(), added: string[] = [];
  let skipped = 0;
  const right = Math.max(0, ...document.nodes.map(n => n.x + n.width)) + 120;
  for (const item of payload.units) {
    if (!object(item)) throw new Error('导入单元格式损坏。');
    const u = { ...item, version: 1, requirement: '', human_confirmed: false } as unknown as FunctionUnit;
    validateUnit(u);
    if (incoming.has(u.unit_id)) throw new Error('导入文件含重复功能标识。');
    incoming.add(u.unit_id);
    if (found.has(u.unit_id)) { skipped++; continue; }
    const id = crypto.randomUUID();
    const node: CanvasNode = { id, type: 'text', x: right, y: added.length * 250, width: 320, height: 200, text: caption(u), ckbFunction: u };
    document.nodes.push(node);found.set(u.unit_id, node);added.push(id);
  }
  if (!added.length) return { document, skipped, added };
  hierarchy(document);
  for (const r of payload.relations) {
    if (!object(r) || typeof r.from !== 'string' || typeof r.to !== 'string' || typeof r.kind !== 'string'
      || !found.has(r.from) || !found.has(r.to)) throw new Error('导入关系引用了不存在的功能。');
    const from = found.get(r.from)!, to = found.get(r.to)!;
    if (!added.includes(from.id) && !added.includes(to.id)) continue;
    document.edges.push({ id: crypto.randomUUID(), fromNode: from.id, toNode: to.id,
      fromSide: 'right', toSide: 'left', label: '关系', ckbFunctionRelation: r });
  }
  return { document, skipped, added };
}
export function newUnitPayload(title: string, summary: string): unknown {
  return { status: 'experimental-interchange-only', version: '0.1-draft', relations: [], units: [{
    unit_id: crypto.randomUUID(), parent_id: null, title, summary, implementation_summary: '尚未提供实现说明',
    state: 'proposed', source_refs: [], session_refs: [],
  }] };
}
