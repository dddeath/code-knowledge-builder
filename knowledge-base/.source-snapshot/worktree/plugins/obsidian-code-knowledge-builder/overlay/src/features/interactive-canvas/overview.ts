import { createHash } from 'node:crypto';

import type { CanvasDocument, CanvasEdge, CanvasNode, FunctionUnit } from './model';
import { copyDocument } from './model';

type Row = Record<string, unknown>;
export interface OverviewDetail { id: string; name: string; summary: string; path: string; line: number; category: string; source: string; owner: string }
export interface OverviewInput { graph: Row; output: string; freshness: string; navigation: string[] }
interface Stamp { version: 1; owner: string; base: Row }
interface Manifest { version: 1; owner: string; nodes: string[]; edges: string[]; deletedNodes: string[]; deletedEdges: string[] }
export const row = (v: unknown): Row => v && typeof v === 'object' && !Array.isArray(v) ? v as Row : {};
const str = (v: unknown): string => typeof v === 'string' ? v : '';
const hash = (v: string): string => createHash('sha256').update(v).digest('hex').slice(0, 24);
const same = (a: unknown, b: unknown): boolean => JSON.stringify(a) === JSON.stringify(b);
const narrative = (e: Row): string => e.review_status === 'agent-reviewed'
  ? [e.role_zh, e.meaning_zh, e.description_zh].map(str).find(s => /[\u3400-\u9fff]/u.test(s)) || '职责待核验；仅依据源码位置收纳。'
  : '职责待核验；仅依据源码位置收纳。';

export function buildOverview(input: OverviewInput): CanvasDocument {
  const g = input.graph;
  if (g.schema_version !== 4 || !Array.isArray(g.entities) || !Array.isArray(g.links)) throw new Error('知识库图版本或结构不兼容，原白板保持不变。');
  const entities = g.entities.map(row), ids = new Set<string>();
  for (const e of entities) {
    if (!str(e.id) || ids.has(str(e.id))) throw new Error('知识库实体标识缺失或重复，原白板保持不变。');
    ids.add(str(e.id));
  }
  const owner = hash(input.output), nodes: CanvasNode[] = [], edges: CanvasEdge[] = [];
  const repo = row(g.repository), commit = str(repo.commit), scope = row(g.scope);
  const paths = row(scope.selectors).scope_paths;
  const scopeText = Array.isArray(paths) && paths.length ? paths.join('、') : '以本次建库实体集合为限';
  const add = (key: string, title: string, summary: string, parent: string | null, x: number, y: number, details: OverviewDetail[], extra: Row = {}) => {
    const id = hash(owner + ':' + key);
    const unit: FunctionUnit = { version: 1, unit_id: id, parent_id: parent, title, summary, implementation_summary: '固定知识库事实；包含线表示导航层级，不表示执行顺序或确定依赖。', requirement: '', state: 'implemented', human_confirmed: false, source_refs: [], session_refs: [] };
    const base = { type: 'text', x, y, width: 360, height: 230, text: `# ${title}\n\n${summary.slice(0, 360)}`, ckbFunction: unit, ckbOverviewDetails: details, ...extra };
    nodes.push({ id, ...base, ckbGenerated: { version: 1, owner, base: JSON.parse(JSON.stringify(base)) as Row } });
    if (parent) {
      const edgeBase = { fromNode: parent, toNode: id, fromSide: 'right', toSide: 'left', label: '包含' };
      edges.push({ id: hash(owner + ':edge:' + key), ...edgeBase, ckbGenerated: { version: 1, owner, base: edgeBase } });
    }
    return id;
  };
  // 功能身份不包含提交、实体id、行号或展示排名。缺少签名的同名重载归为功能族。
  const identity = (e: Row): string => JSON.stringify([str(e.path).replace(/\\/g, '/'), str(e.language), str(e.kind), str(e.qualified_name || e.name), str(e.signature).replace(/\s+/gu, ' ').trim()]);
  const byId = new Map(entities.map(e => [str(e.id), e]));
  const pageRows = entities.filter(e => e.classification === 'page');
  const pageKeys = new Map(pageRows.map(e => [str(e.id), identity(e)]));
  const pageNodeIds = new Map(pageRows.map(e => [str(e.id), hash(owner + ':function:' + identity(e))]));
  const files = new Map(entities.filter(e => e.kind === 'file' && pageNodeIds.has(str(e.id))).map(e => [str(e.path), e]));
  const parentPage = (e: Row): string | null => {
    let parent = str(e.parent_id);const seen = new Set<string>([str(e.id)]);
    while (parent && !seen.has(parent)) {
      seen.add(parent);if (pageNodeIds.has(parent)) return pageNodeIds.get(parent)!;
      parent = str(byId.get(parent)?.parent_id);
    }
    const file = files.get(str(e.path));
    return file && file.id !== e.id ? pageNodeIds.get(str(file.id))! : null;
  };
  const rootId = hash(owner + ':root'), boundaryId = hash(owner + ':boundary');
  const detailOwner = (e: Row): string => {
    if (pageNodeIds.has(str(e.id))) return pageNodeIds.get(str(e.id))!;
    // 明确遵循投影owner_page_id，不用词法目录或抽样排名替代职责归属。
    const declared = pageNodeIds.get(str(e.owner_page_id));
    return declared || parentPage(e) || boundaryId;
  };
  const detailGroups = new Map<string, OverviewDetail[]>();
  for (const e of entities) {
    const p = str(e.path).replace(/\\/g, '/'), line = Number(row(e.range).start_line) || 1;
    const absolute = str(repo.root).replace(/\\/g, '/').replace(/\/$/u, '') + '/' + p;
    const target = detailOwner(e), items = detailGroups.get(target) || [];
    items.push({ id: str(e.id), name: str(e.qualified_name) || str(e.name) || '未命名实体', summary: narrative(e), path: p, line,
      category: e.classification === 'boundary' || !p ? '明确边界' : e.classification === 'page' ? '主功能' : '辅助详情',
      source: p ? `vscode://file/${encodeURI(absolute).replace(/[?#]/gu, encodeURIComponent)}:${line}:1` : '', owner: target });
    detailGroups.set(target, items);
  }
  const title = (e: Row): string => {
    if (e.review_status !== 'agent-reviewed') return `${str(e.name)} · 职责待核验`;
    const meaning = str(e.meaning_zh);
    // 只截取已审阅原句，不推断或硬编码业务分类。
    const reviewed = meaning.match(/(?:负责|用于|用来)([^。；\n]+)/u)?.[1];
    if (reviewed && /[\u3400-\u9fff]/u.test(reviewed)) return reviewed.length > 44 ? reviewed.slice(0, 44) + '…' : reviewed;
    return `${str(e.name)} · ${narrative(e).replace(/`/gu, '').slice(0, 38)}`;
  };
  add('root', '知识库功能总览', `版本：${commit.slice(0, 12) || '未标记'}\n${new Set(pageKeys.values()).size} 个已有功能页，${entities.length} 个实体。\n在侧栏按职责查找并逐层展开；所有主要功能均可到达。`, null, 0, 0, [], {
    ckbOverviewInfo: { commit, scope: scopeText, freshness: input.freshness, entityCount: entities.length, primaryCount: pageRows.length, relationCount: g.links.length, navigation: input.navigation,
      warning: '依据已审阅页面与归属关系导航，辅助实体归其所属功能。仅覆盖已建库范围；包含线不是依赖或执行顺序。缺少稳定签名的同名声明按功能族收纳。' },
  });
  const corePaths = new Set(Array.isArray(row(g.navigation_plan).core_paths) ? row(g.navigation_plan).core_paths as string[] : []);
  pageRows.sort((a, b) => Number(corePaths.has(str(b.path))) - Number(corePaths.has(str(a.path))) || title(a).localeCompare(title(b), 'zh-CN') || identity(a).localeCompare(identity(b)));
  const emitted = new Set<string>();let y = 0;
  for (const e of pageRows) {
    const key = identity(e);if (emitted.has(key)) continue;emitted.add(key);
    const id = pageNodeIds.get(str(e.id))!, parent = parentPage(e) || rootId;
    const summary = [e.review_status === 'agent-reviewed' ? str(e.meaning_zh) : '', narrative(e)].filter(s => /[\u3400-\u9fff]/u.test(s)).join('\n');
    add('function:' + key, title(e), summary || '职责待核验。', parent, parent === rootId ? 480 : 960, y, detailGroups.get(id) || [], {
      ckbOverviewIdentity: key, ckbOverviewSource: { path: str(e.path), qualified: str(e.qualified_name || e.name), kind: str(e.kind), signature: str(e.signature) },
    });y += 270;
  }
  if (detailGroups.has(boundaryId)) add('boundary', '边界与待核验归属', '尚未映射到已有功能页的实体；保留来源供核验，不编造职责。', rootId, 480, y, detailGroups.get(boundaryId)!);
  // 所有功能保留在可检索目录中；原生卡片按访问逐步展开，不因分页丢失功能。
  const all = nodes.slice(1);
  const catalog = { version: 2, nodes: all, edges };
  nodes[0].ckbOverviewCatalog = catalog;
  const initial = all.filter(n => n.ckbFunction?.parent_id === rootId).slice(0, 6);
  initial.forEach((n, i) => { n.x = 480;n.y = i * 270;const s = row(n.ckbGenerated);s.base = { ...row(s.base), x: n.x, y: n.y }; });
  const visible = new Set([rootId, ...initial.map(n => n.id)]);
  return { nodes: [nodes[0], ...initial], edges: edges.filter(e => visible.has(e.fromNode) && visible.has(e.toNode)) };
}

export function overviewCatalog(document: CanvasDocument): CanvasDocument {
  const root = document.nodes.find(n => n.ckbOverviewInfo), c = row(root?.ckbOverviewCatalog);
  return Array.isArray(c.nodes) && Array.isArray(c.edges) ? { nodes: c.nodes as CanvasNode[], edges: c.edges as CanvasEdge[] } : { nodes: [], edges: [] };
}
export function expandOverview(document: CanvasDocument, id: string): CanvasDocument {
  const result = copyDocument(document), catalog = overviewCatalog(result);
  const byId = new Map(catalog.nodes.map(n => [n.id, n]));
  const present = new Set(result.nodes.map(n => n.id)), seen = new Set<string>();
  let node = byId.get(id);
  const pending: CanvasNode[] = [];
  while (node && !present.has(node.id)) {
    if (seen.has(node.id)) throw new Error('功能页归属出现循环，未展开。');
    seen.add(node.id);pending.unshift(node);node = byId.get(node.ckbFunction?.parent_id || '');
  }
  let y = Math.max(0, ...result.nodes.map(n => n.y + n.height)) + 80;
  for (const entry of pending) {
    const n = JSON.parse(JSON.stringify(entry)) as CanvasNode;
    const parent = result.nodes.find(p => p.id === n.ckbFunction?.parent_id);
    n.x = (parent?.x || 0) + 480;n.y = y;y += 270;
    const s = row(n.ckbGenerated);s.base = { ...row(s.base), x: n.x, y: n.y };
    result.nodes.push(n);present.add(n.id);
  }
  const added = new Set(pending.map(n => n.id));
  for (const e of catalog.edges) if ((added.has(e.fromNode) || added.has(e.toNode)) && present.has(e.fromNode) && present.has(e.toNode) && !result.edges.some(x => x.id === e.id)) result.edges.push(JSON.parse(JSON.stringify(e)) as CanvasEdge);
  const root = result.nodes.find(n => n.ckbOverviewState);
  if (root) {
    const state = row(root.ckbOverviewState);
    // 显式选择已删除功能表示请求重新展开，仅恢复该次请求的节点及其父链。
    state.deletedNodes = (Array.isArray(state.deletedNodes) ? state.deletedNodes : []).filter(x => !present.has(String(x)));
    state.nodes = result.nodes.filter(n => n.ckbGenerated).map(n => n.id);state.edges = result.edges.filter(e => e.ckbGenerated).map(e => e.id);
  }
  return result;
}

function stamp(item: Row): Stamp | null {
  const s = row(item.ckbGenerated);
  return s.version === 1 && typeof s.owner === 'string' && s.base && typeof s.base === 'object' ? s as unknown as Stamp : null;
}
function mergeFields(current: Row, previous: Row, desired: Row, conflicts: string[], prefix: string): Row {
  const result = { ...current };
  for (const key of Object.keys(desired)) {
    if (key === 'ckbFunction') {
      result[key] = mergeFields(row(current[key]), row(previous[key]), row(desired[key]), conflicts, prefix + '.功能');
    } else if (same(current[key], previous[key])) result[key] = desired[key];
    else if (!same(current[key], desired[key])) conflicts.push(prefix + '.' + key);
  }
  return result;
}

export function mergeOverview(value: unknown, desired: CanvasDocument): { document: CanvasDocument; conflicts: string[] } {
  const document = value === null ? { nodes: [], edges: [] } as CanvasDocument : copyDocument(value);
  desired = copyDocument(desired);
  const catalog = overviewCatalog(desired);
  const migration = new Map<string, string>();
  for (const n of document.nodes) {
    if (!stamp(n) || n.ckbOverviewIdentity || !n.ckbFunction?.title.endsWith(' · 主要功能')) continue;
    const d = (Array.isArray(n.ckbOverviewDetails) ? n.ckbOverviewDetails as OverviewDetail[] : []).find(d => d.category === '主功能');
    if (!d) continue;
    const matches = catalog.nodes.filter(c => row(c.ckbOverviewSource).path === d.path && row(c.ckbOverviewSource).qualified === d.name);
    if (matches.length > 1) throw new Error('旧版功能对应多个稳定签名，需要明确迁移映射；未写入。');
    if (matches.length === 1) migration.set(n.id, matches[0].id);
  }
  if (migration.size) {
    for (const n of document.nodes) {
      const oldId = n.id;n.id = migration.get(n.id) || n.id;
      if (n.ckbFunction) {
        n.ckbFunction.unit_id = n.id;n.ckbFunction.parent_id = migration.get(n.ckbFunction.parent_id || '') || n.ckbFunction.parent_id;
        const s = stamp(n);
        if (s && oldId !== n.id) s.base.ckbFunction = { ...row(s.base.ckbFunction), unit_id: n.id };
      }
    }
    for (const e of document.edges) { e.fromNode = migration.get(e.fromNode) || e.fromNode;e.toNode = migration.get(e.toNode) || e.toNode; }
    const r = document.nodes.find(n => n.ckbOverviewState), state = row(r?.ckbOverviewState);
    for (const field of ['nodes', 'deletedNodes']) if (Array.isArray(state[field])) state[field] = (state[field] as string[]).map(id => migration.get(id) || id);
  }
  // 保持已展开功能；展示顺序变化不改变实体身份，也不抹掉人工修改。
  for (const node of document.nodes) if (catalog.nodes.some(n => n.id === node.id)) desired = expandOverview(desired, node.id);
  const root = desired.nodes[0], owner = stamp(root)!.owner;
  const existingRoot = document.nodes.find(n => n.id === root.id);
  const old = row(existingRoot?.ckbOverviewState) as unknown as Manifest;
  if (value !== null && (old.version !== 1 || old.owner !== owner || !Array.isArray(old.nodes) || !Array.isArray(old.edges)
    || !Array.isArray(old.deletedNodes) || !Array.isArray(old.deletedEdges))) throw new Error('目标文件不是此知识库的生成白板，或所属信息已被修改；未覆盖。请重命名现有文件后重试。');
  const conflicts: string[] = [];
  const deletedNodes = new Set(old.deletedNodes || []), deletedEdges = new Set(old.deletedEdges || []);
  for (const id of old.nodes || []) if (!document.nodes.some(n => n.id === id)) deletedNodes.add(id);
  for (const id of old.edges || []) if (!document.edges.some(e => e.id === id)) deletedEdges.add(id);
  function reconcile<T extends CanvasNode | CanvasEdge>(current: T[], next: T[], deleted: Set<string>): T[] {
    const wanted = new Map(next.map(n => [n.id, n]));
    const result: T[] = [];
    for (const item of current) {
      const s = stamp(item), target = wanted.get(item.id);
      if (target && (!s || s.owner !== owner)) throw new Error('生成标识与用户内容冲突，未覆盖。');
      if (!s || s.owner !== owner) { result.push(item);continue; }
      if (!target) {
        // 暂时退出主功能展示仍保留身份与比较基线；重新进入时继续三方合并。
        result.push({ ...item, ckbOverviewRetired: true });continue;
      }
      const base = stamp(target)!.base;
      result.push({ ...mergeFields(item, s.base, base, conflicts, item.id), id: item.id, ...(item.ckbOverviewRetired ? { ckbOverviewRetired: false } : {}), ckbGenerated: { version: 1, owner, base } } as unknown as T);
      wanted.delete(item.id);
    }
    for (const item of wanted.values()) if (!deleted.has(item.id)) result.push(item);
    return result;
  }
  document.nodes = reconcile(document.nodes, desired.nodes, deletedNodes);
  document.edges = reconcile(document.edges, desired.edges, deletedEdges);
  const live = new Set(document.nodes.map(n => n.id));
  document.edges = document.edges.filter(e => {
    if (!stamp(e) || (live.has(e.fromNode) && live.has(e.toNode))) return true;
    deletedEdges.add(e.id);return false;
  });
  const finalRoot = document.nodes.find(n => n.id === root.id)!;
  finalRoot.ckbOverviewCatalog = desired.nodes[0].ckbOverviewCatalog;
  finalRoot.ckbOverviewState = { version: 1, owner, nodes: document.nodes.filter(n => stamp(n)?.owner === owner).map(n => n.id), edges: document.edges.filter(e => stamp(e)?.owner === owner).map(e => e.id), deletedNodes: [...deletedNodes], deletedEdges: [...deletedEdges] };
  return { document, conflicts };
}
