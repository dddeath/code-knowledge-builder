import type { Plugin, TFile, WorkspaceLeaf } from 'obsidian';
import { FileSystemAdapter, ItemView, Modal, Notice, TFile as NativeFile } from 'obsidian';

import type { ProviderHost } from '../../core/providers/ProviderHost';
import { ProviderRegistry } from '../../core/providers/ProviderRegistry';
import { ProviderWorkspaceRegistry } from '../../core/providers/ProviderWorkspaceRegistry';
import type { InlineEditService } from '../../core/providers/types';
type CanvasHost = Plugin & ProviderHost;
import { resolveSelectionLearningProviderContext } from '../selection-learning/SelectionLearningProvider';
import type { CanvasDocument, FunctionUnit } from './model';
import { copyDocument, editUnit, importUnits, newUnitPayload, units } from './model';
import type { OverviewDetail } from './overview';
import { buildOverview, expandOverview, mergeOverview, overviewCatalog, row } from './overview';
import { readOverviewInput } from './overviewInput';

export const FUNCTION_VIEW = 'ckb-interactive-canvas';
interface NativeNode { id: string }
interface NativeCanvas {
  getData(): unknown;
  setData(data: CanvasDocument): void;
  requestSave(): void;
  selection: Set<NativeNode>;
  nodes: Map<string, NativeNode>;
  selectOnly(node: NativeNode): void;
  zoomToSelection(): void;
}
interface NativeView { file: TFile; canvas: NativeCanvas; save(): Promise<void> }
const stateLabels: Record<string, string> = { proposed: '设计提议', confirmed: '已确认', in_progress: '进行中', implemented: '已实现', verified: '已验证', superseded: '已替代' };

class InputModal extends Modal {
  constructor(private host: CanvasHost, private title: string, private submit: (text: string) => Promise<void>) { super(host.app); }
  onOpen(): void {
    this.titleEl.setText(this.title);
    const input = this.contentEl.createEl('textarea', { attr: { rows: '8', 'aria-label': this.title } });
    input.addClass('ckb-function-input');
    const status = this.contentEl.createEl('p');
    this.contentEl.createEl('button', { text: '确定' }).onclick = async () => {
      try { await this.submit(input.value);this.close(); } catch (e) { status.setText(message(e)); }
    };
  }
}
function message(error: unknown): string { return error instanceof Error ? error.message : '操作未完成，请重试。'; }

export class InteractiveCanvasController {
  private native: NativeView | null = null;
  private view: FunctionView | null = null;
  private signature = '';
  private busy = false;
  private disposed = false;
  private service: InlineEditService | null = null;
  private contextKey = '';
  private conversation = false;
  private generation = 0;
  private asking = false;
  private timeout: number | null = null;
  private timer: number | null = null;
  private overviewAbort: AbortController | null = null;
  constructor(private plugin: CanvasHost) {}
  install(): void {
    this.plugin.registerView(FUNCTION_VIEW, leaf => new FunctionView(leaf, this));
    this.plugin.addCommand({ id: 'open-function-nodes', name: '打开功能节点面板', callback: () => { void this.open(); } });
    this.plugin.addCommand({ id: 'create-function-node', name: '创建功能节点', callback: () => this.create() });
    this.plugin.addCommand({ id: 'import-function-nodes', name: '导入功能节点', callback: () => this.import() });
    this.plugin.addCommand({ id: 'generate-knowledge-overview', name: '生成知识库白板', callback: () => { void this.generateOverview(); } });
    this.plugin.addRibbonIcon('network', '生成知识库白板', () => { void this.generateOverview(); });
    this.plugin.addCommand({ id: 'cancel-knowledge-overview', name: '取消生成知识库白板', callback: () => this.cancelOverview() });
    this.timer = window.setInterval(() => this.sync(), 350);
    this.plugin.registerInterval(this.timer);
  }
  cancelOverview(): void { this.overviewAbort?.abort();this.view?.status('已取消生成，已保存的白板保持原样。'); }
  async generateOverview(): Promise<void> {
    if (this.overviewAbort || this.busy || this.disposed) return;
    const abort = this.overviewAbort = new AbortController();
    const check = () => { abort.signal.throwIfAborted();if (this.disposed) throw new Error('插件已卸载。'); };
    const started = performance.now();
    new Notice('正在读取完整知识库，可用“取消生成知识库白板”命令取消。');
    try {
      const adapter = this.plugin.app.vault.adapter;
      if (!(adapter instanceof FileSystemAdapter)) throw new Error('生成白板需要桌面本地 vault。');
      const input = await readOverviewInput(adapter.getBasePath(), abort.signal);check();
      const desired = buildOverview(input);check();
      const vault = this.plugin.app.vault, target = '知识库总览.canvas';
      let file = vault.getAbstractFileByPath(target);
      let conflicts: string[] = [];
      if (file) {
        if (!(file instanceof NativeFile)) throw new Error('白板目标被同名目录占用，未写入。');
        const existing = this.plugin.app.workspace.getLeavesOfType('canvas').map(l => l.view as unknown as NativeView).find(v => v.file === file);
        if (existing) await existing.save();check();
        const live = existing ? JSON.stringify(existing.canvas.getData()) : null;
        let applied: CanvasDocument | null = null;
        await vault.process(file, text => {
          check();
          if (existing && JSON.stringify(existing.canvas.getData()) !== live) throw new Error('白板正在编辑，本次生成已取消，请重试。');
          const result = mergeOverview(JSON.parse(text), desired);conflicts = result.conflicts;applied = result.document;
          return JSON.stringify(result.document, null, 2);
        });
        // process 完成后若出现新的原生编辑，不用旧结果覆盖内存。
        if (existing && JSON.stringify(existing.canvas.getData()) === live && applied && !this.disposed) {
          existing.canvas.setData(applied);existing.canvas.requestSave();await existing.save();
        }
      } else {
        const result = mergeOverview(null, desired);check();
        file = await vault.create(target, JSON.stringify(result.document, null, 2));
      }
      check();
      if (!(file instanceof NativeFile)) throw new Error('白板保存结果不是文件。');
      const persisted = copyDocument(JSON.parse(await vault.read(file)));check();
      if (!persisted.nodes.some(n => n.id === desired.nodes[0].id && n.ckbOverviewState)) throw new Error('白板持久化核验失败。');
      const leaf = this.plugin.app.workspace.getLeavesOfType('canvas').find(l => (l.view as unknown as NativeView).file === file) ?? this.plugin.app.workspace.getLeaf('tab');
      await leaf.openFile(file);check();
      this.native = leaf.view as unknown as NativeView;
      await this.open();this.select(desired.nodes[0].id);
      const result = `已生成 ${persisted.nodes.length} 张卡片，用时 ${Math.round(performance.now() - started)} 毫秒。${conflicts.length ? `保留 ${conflicts.length} 处人工编辑与生成差异；自动更新只改未编辑字段。` : '再次生成保留人工卡片、连线、布局和文字。'}`;
      this.view?.status(result);new Notice(result);
    } catch (e) {
      if (!this.disposed) { const text = abort.signal.aborted ? '生成已取消；已保存文件保持原样。' : `生成未完成：${message(e)}`;this.view?.status(text);new Notice(text); }
    } finally { if (this.overviewAbort === abort) this.overviewAbort = null; }
  }
  async openOverviewLink(link: string): Promise<void> {
    if (['INDEX.md', 'WIKI.md', 'RECORDS.md', 'REFERENCES.md'].includes(link)) await this.plugin.app.workspace.openLinkText(link, '', true);
  }
  private getNative(): NativeView {
    const active = this.plugin.app.workspace.getMostRecentLeaf()?.view;
    if (active?.getViewType() === 'canvas') this.native = active as unknown as NativeView;
    const v = this.native;
    if (!v?.file || !this.plugin.app.workspace.getLeavesOfType('canvas').some(l => l.view === (v as unknown))) throw new Error('请先打开原生白板文件。');
    if (typeof v.canvas?.getData !== 'function' || typeof v.canvas?.setData !== 'function' || typeof v.canvas?.requestSave !== 'function' || typeof v.save !== 'function') throw new Error('当前白板版本未提供兼容保存入口；原生编辑不受影响。');
    return v;
  }
  async open(): Promise<void> {
    try {
      this.getNative();
      const leaf = this.plugin.app.workspace.getLeavesOfType(FUNCTION_VIEW)[0] ?? this.plugin.app.workspace.getRightLeaf(false);
      if (!leaf) throw new Error('没有可用的侧栏位置。');
      await leaf.setViewState({ type: FUNCTION_VIEW, active: true });
      await this.plugin.app.workspace.revealLeaf(leaf);
      this.signature = '';this.sync();
    } catch (e) { new Notice(message(e)); }
  }
  attach(view: FunctionView): void { this.view = view;this.signature = '';this.sync(); }
  detach(view: FunctionView): void { if (this.view === view) { this.cancel();this.view = null;this.signature = ''; } }
  sync(): void {
    if (this.disposed || !this.view || this.busy) return;
    try {
      const v = this.getNative(), document = copyDocument(v.canvas.getData());
      const selected = [...v.canvas.selection].find(n => document.nodes.some(d => d.id === n.id && d.ckbFunction));
      const signature = `${v.file.path}:${selected?.id ?? ''}:${JSON.stringify(document.nodes.map(n => [n.id,n.ckbFunction]))}`;
      if (signature === this.signature) return;
      this.cancel();this.signature = signature;
      this.view.render(document, selected?.id ?? null);
    } catch (e) { this.view.status(message(e)); }
  }
  select(id: string): void {
    try { const c = this.getNative().canvas, node = c.nodes.get(id);if (node) { c.selectOnly(node);c.zoomToSelection();this.sync(); } } catch (e) { this.view?.status(message(e)); }
  }
  async navigateOverview(id: string): Promise<void> {
    try {
      const data = copyDocument(this.getNative().canvas.getData());
      if (!data.nodes.some(n => n.id === id)) await this.write(value => expandOverview(copyDocument(value), id));
      this.select(id);
    } catch (e) { this.view?.status(message(e)); }
  }
  create(): void {
    try { this.getNative();new InputModal(this.plugin, '输入功能标题', async text => {
      await this.importValue(newUnitPayload(text.trim(), '请在侧栏填写功能说明。'));await this.open();
    }).open(); } catch (e) { new Notice(message(e)); }
  }
  import(): void {
    try { this.getNative();new InputModal(this.plugin, '粘贴功能节点 JSON', async text => {
      await this.importValue(JSON.parse(text));await this.open();
    }).open(); } catch (e) { new Notice(message(e)); }
  }
  private async write(transform: (data: unknown) => CanvasDocument): Promise<void> {
    if (this.busy || this.overviewAbort || this.disposed) throw new Error('正在保存，请稍后再试。');
    const v = this.getNative(), file = v.file, canvas = v.canvas;
    this.busy = true;
    let before: CanvasDocument | null = null;
    let applied: CanvasDocument | null = null;
    try {
      copyDocument(JSON.parse(await this.plugin.app.vault.read(file)));
      if (v.file !== file || v.canvas !== canvas || this.disposed) throw new Error('白板已切换，请重新操作。');
      before = copyDocument(canvas.getData());
      const next = transform(before);
      canvas.setData(next);canvas.requestSave();applied = copyDocument(canvas.getData());await v.save();
      const persisted = JSON.parse(await this.plugin.app.vault.read(file)) as CanvasDocument;
      for (const node of next.nodes.filter(n => n.ckbFunction)) {
        if (JSON.stringify(persisted.nodes.find(n => n.id === node.id)?.ckbFunction) !== JSON.stringify(node.ckbFunction)) throw new Error('保存后的功能字段核验失败。');
      }
    } catch (e) {
      if (before && applied && v.file === file && JSON.stringify(canvas.getData()) === JSON.stringify(applied)) {
        canvas.setData(before);canvas.requestSave();await v.save();
      }
      throw e;
    } finally { this.busy = false;this.signature = '';this.sync(); }
  }
  async importValue(value: unknown): Promise<void> {
    let skipped = 0;
    await this.write(data => { const result = importUnits(data, value);skipped = result.skipped;return result.document; });
    new Notice(skipped ? `已保留 ${skipped} 个重复功能，未覆盖。` : '功能节点已保存到白板。');
  }
  async save(id: string, update: Partial<FunctionUnit>): Promise<void> {
    try { await this.write(data => editUnit(data, id, update));this.view?.status('已保存到白板。'); } catch (e) { this.view?.status(message(e)); }
  }
  async ask(id: string, question: string): Promise<void> {
    if (this.disposed || this.asking || !question.trim()) return;
    let generation = ++this.generation;
    this.asking = true;
    try {
      const v = this.getNative(), u = copyDocument(v.canvas.getData()).nodes.find(n => n.id === id)?.ckbFunction;
      if (!u) throw new Error('请先选择功能节点。');
      const sourcePath = v.file.path;
      const context = resolveSelectionLearningProviderContext(this.plugin.settings);
      if (!ProviderRegistry.isEnabled(context.providerId, this.plugin.settings)) throw new Error('尚未启用可用 Provider；仍可编辑和保存功能节点。');
      const key = `${v.file.path}:${id}:${context.providerId}:${context.modelOverride ?? ''}`;
      if (!this.service || this.contextKey !== key) {
        this.cancel();generation = ++this.generation;this.asking = true;
        this.view?.status('正在初始化现有 Provider，可点击取消。');
        await ProviderWorkspaceRegistry.ensureInitialized(this.plugin, context.providerId, 'interactive-canvas');
        if (generation !== this.generation || this.disposed || this.getNative() !== v
          || v.file.path !== sourcePath || ![...v.canvas.selection].some(node => node.id === id)) return;
        const adapter = this.plugin.app.vault.adapter;
        if (!(adapter instanceof FileSystemAdapter)) throw new Error('讨论需要桌面本地 vault。');
        this.service = ProviderRegistry.createSelectionLearningService(this.plugin, context.providerId, adapter.getBasePath());
        this.service.setModelOverride?.(context.modelOverride);this.contextKey = key;
      }
      const service = this.service;
      this.asking = true;this.view?.status('正在讨论，可点击取消。');
      const timeout = this.timeout = window.setTimeout(() => this.cancel('讨论超时，已取消。'), 300000);
      try {
        const instruction = `只讨论以下设计，不调用任何工具，不执行命令，不修改文件，不宣称通过验证。请用中文回答问题；把回答放在现有解释响应格式中。\n功能：${u.title}\n说明：${u.summary}\n需求：${u.requirement}\n问题：${question}`;
        const result = this.conversation ? await service.continueConversation(instruction) : await service.editText({ mode: 'selection', notePath: v.file.path, selectedText: u.summary || u.title, instruction });
        if (generation !== this.generation || this.disposed) return;
        if (!result.success) throw new Error(result.error || 'Provider 未返回讨论结果。');
        this.conversation = true;
        this.view?.answer(result.clarification ?? result.editedText ?? result.insertedText ?? 'Provider 返回空结果。');
        this.view?.status('讨论结束；节点内容和状态未自动修改。');
      } finally { window.clearTimeout(timeout);if (this.timeout === timeout) this.timeout = null;if (generation === this.generation) this.asking = false; }
    } catch (e) {
      if (generation === this.generation && !this.disposed) { this.cancel();this.view?.status(`讨论未完成：${message(e)}`); }
    } finally { if (generation === this.generation) this.asking = false; }
  }
  cancel(reason?: string): void {
    if (this.timeout !== null) window.clearTimeout(this.timeout);this.timeout = null;
    this.generation++;this.asking = false;this.service?.cancel();this.service?.setProgressCallback?.(undefined);this.service = null;this.conversation = false;this.contextKey = '';
    if (reason) this.view?.status(reason);
  }
  dispose(): void {
    this.disposed = true;this.cancelOverview();this.cancel();if (this.timer !== null) window.clearInterval(this.timer);this.timer = null;
    this.plugin.app.workspace.detachLeavesOfType(FUNCTION_VIEW);this.view = null;this.native = null;
  }
}

export class FunctionView extends ItemView {
  private statusEl: HTMLElement | null = null;
  private answerEl: HTMLElement | null = null;
  constructor(leaf: WorkspaceLeaf, private controller: InteractiveCanvasController) { super(leaf); }
  getViewType(): string { return FUNCTION_VIEW; }
  getDisplayText(): string { return '功能节点'; }
  getIcon(): string { return 'workflow'; }
  async onOpen(): Promise<void> { this.controller.attach(this); }
  async onClose(): Promise<void> { this.controller.detach(this); }
  status(text: string): void { this.statusEl?.setText(text); }
  answer(text: string): void { this.answerEl?.setText(text); }
  render(document: CanvasDocument, selected: string | null): void {
    const root = this.contentEl;root.empty();root.addClass('ckb-function-panel');
    root.createEl('h3', { text: '功能节点' });
    const controls = root.createDiv();
    controls.createEl('button', { text: '生成知识库白板' }).onclick = () => { void this.controller.generateOverview(); };
    controls.createEl('button', { text: '取消生成' }).onclick = () => this.controller.cancelOverview();
    controls.createEl('button', { text: '创建功能' }).onclick = () => this.controller.create();
    controls.createEl('button', { text: '导入功能' }).onclick = () => this.controller.import();
    const selectedNode = document.nodes.find(n => n.id === selected);
    const list = root.createEl('details');list.createEl('summary', { text: selectedNode?.ckbGenerated ? '下一级功能' : '功能目录' });
    list.open = !!selectedNode?.ckbGenerated;
    const catalog = overviewCatalog(document);
    if (selectedNode?.ckbGenerated && catalog.nodes.length) {
      const search = list.createEl('input', { attr: { 'aria-label': '搜索全部功能职责', placeholder: '搜索职责、功能名或源码位置' } });
      const entries = list.createDiv();const paging = list.createDiv();let page = 0;
      const render = () => {
        entries.empty();paging.empty();const query = search.value.trim().toLocaleLowerCase();
        const found = catalog.nodes.filter(n => query ? `${n.ckbFunction!.title} ${n.ckbFunction!.summary} ${JSON.stringify(n.ckbOverviewSource)}`.toLocaleLowerCase().includes(query) : n.ckbFunction!.parent_id === selectedNode.ckbFunction!.unit_id);
        entries.createEl('p', { text: `${query ? '全部功能搜索' : '下一级功能'}：${found.length} 项；第 ${page + 1} / ${Math.max(1, Math.ceil(found.length / 8))} 页。` });
        for (const n of found.slice(page * 8, (page + 1) * 8)) {
          const item = entries.createDiv();item.createEl('button', { text: n.ckbFunction!.title, attr: { 'data-function-node': n.id } }).onclick = () => { void this.controller.navigateOverview(n.id); };
          item.createEl('p', { text: String(row(n.ckbOverviewSource).qualified || '') });
        }
        if (page) paging.createEl('button', { text: '上一页功能' }).onclick = () => { page--;render(); };
        if ((page + 1) * 8 < found.length) paging.createEl('button', { text: '下一页功能' }).onclick = () => { page++;render(); };
      };
      search.oninput = () => { page = 0;render(); };render();
    } else for (const node of units(document).values()) list.createEl('button', { text: node.ckbFunction!.title, attr: { 'data-function-node': node.id } }).onclick = () => this.controller.select(node.id);
    if (selectedNode?.ckbGenerated && !selectedNode.ckbOverviewInfo) {
      const overview = document.nodes.find(n => n.ckbOverviewInfo);
      if (overview) controls.createEl('button', { text: '返回总览' }).onclick = () => this.controller.select(overview.id);
    }
    this.statusEl = root.createEl('p', { attr: { role: 'status' } });
    const node = document.nodes.find(n => n.id === selected);
    if (!node?.ckbFunction) { root.createEl('p', { text: '请在白板上选择功能节点。普通节点保持原样。' });return; }
    const u = node.ckbFunction;
    root.createEl('h4', { text: u.title });
    if (node.ckbOverviewRetired) root.createEl('p', { text: '此功能暂未列为当前主要页面；保留所属身份和人工编辑，后续进入时继续更新。' });
    const info = row(node.ckbOverviewInfo);
    if (info.warning) {
      root.createEl('p', { text: String(info.freshness) });
      root.createEl('p', { text: `建库范围：${String(info.scope)}` });
      root.createEl('p', { text: String(info.warning) });
      const navLabels: Record<string, string> = { 'INDEX.md': '阅读首页', 'WIKI.md': '知识导航', 'RECORDS.md': '分析与工作记录', 'REFERENCES.md': '已审阅参考资料' };
      for (const link of Array.isArray(info.navigation) ? info.navigation : []) {
        if (typeof link === 'string' && navLabels[link]) root.createEl('button', { text: navLabels[link] }).onclick = () => { void this.controller.openOverviewLink(link); };
      }
    }
    if (Array.isArray(node.ckbOverviewDetails) && node.ckbOverviewDetails.length) {
      const details = node.ckbOverviewDetails as OverviewDetail[];
      const panel = root.createEl('details', { cls: 'ckb-overview-details' });
      panel.createEl('summary', { text: `全部职责与来源（${details.length}）` });
      const search = panel.createEl('input', { attr: { placeholder: '搜索功能、路径或职责', 'aria-label': '搜索职责' } });
      const rows = panel.createDiv();let limit = 20;
      const more = panel.createEl('button', { text: '显示更多' });
      const render = () => {
        rows.empty();const query = search.value.toLocaleLowerCase();
        const found = details.filter(d => `${d.name} ${d.path} ${d.summary}`.toLocaleLowerCase().includes(query));
        rows.createEl('p', { text: `匹配 ${found.length} 项；显示前 ${Math.min(limit, found.length)} 项。` });
        for (const d of found.slice(0, limit)) {
          const item = rows.createEl('details');item.createEl('summary', { text: `${d.name} · ${d.category}` });
          item.createEl('p', { text: d.summary });item.createEl('p', { text: `${d.path || '范围外位置待核验'}:${d.line}` });
          if (typeof d.source === 'string' && d.source.startsWith('vscode://file/')) item.createEl('a', { text: '打开源码位置（当前工作树，可能与固定版本不同）', href: d.source });
        }
        more.hidden = found.length <= limit;
      };
      search.oninput = () => { limit = 20;render(); };more.onclick = () => { limit += 20;render(); };panel.ontoggle = () => { if (panel.open) render(); };
    }
    root.createEl('p', { text: node.ckbGenerated ? '知识库导航节点；不代表开发验收状态。' : `输入状态：${stateLabels[u.state]}；人工${u.human_confirmed ? '已确认' : '未确认'}` });
    const field = (label: string, value: string) => { root.createEl('label', { text: label });const input = root.createEl('textarea', { attr: { 'aria-label': label, rows: '2' } });input.value = value;input.addClass('ckb-function-input');return input; };
    const title = field('功能标题', u.title), summary = field('功能说明', u.summary), requirement = field('需求', u.requirement);
    root.createEl('label', { text: '父功能' });
    const parent = root.createEl('select', { attr: { 'aria-label': '父功能' } });parent.createEl('option', { text: '顶层功能', value: '' });
    for (const n of units(document).values()) if (n.id !== node.id) parent.createEl('option', { text: n.ckbFunction!.title, value: n.ckbFunction!.unit_id });
    parent.value = u.parent_id ?? '';
    root.createEl('button', { text: '保存功能' }).onclick = () => { void this.controller.save(node.id, { title: title.value, summary: summary.value, requirement: requirement.value, parent_id: parent.value || null }); };
    root.createEl('button', { text: '人工确认' }).onclick = () => { void this.controller.save(node.id, { human_confirmed: true }); };
    const impl = root.createEl('details');impl.createEl('summary', { text: '关键实现' });impl.createEl('p', { text: u.implementation_summary });
    for (const [label, refs] of [['来源', u.source_refs], ['会话', u.session_refs]] as const) {
      root.createEl('h5', { text: label });
      if (!refs.length) root.createEl('p', { text: `尚未绑定${label}。` });
      refs.forEach((ref, i) => {
        const entry = root.createEl('details');entry.createEl('summary', { text: `${label} ${i + 1}` });entry.createEl('p', { text: '入口未绑定，未核验存在性；不自动打开资源。' });
        const technical = entry.createEl('details');technical.createEl('summary', { text: '查看技术详情' });technical.createEl('pre', { text: typeof ref === 'string' ? ref : JSON.stringify(ref, null, 2) });
      });
    }
    const question = field('向 Agent 提问', '请解释这个功能的设计与尚需确认的问题。');
    root.createEl('button', { text: '讨论此功能' }).onclick = () => { void this.controller.ask(node.id, question.value); };
    root.createEl('button', { text: '取消讨论' }).onclick = () => this.controller.cancel('已取消讨论，节点保持不变。');
    this.answerEl = root.createDiv({ cls: 'ckb-function-answer' });
  }
}
