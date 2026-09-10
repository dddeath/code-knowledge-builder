import { FileSystemAdapter } from 'obsidian';

import { ProviderRegistry } from '@/core/providers/ProviderRegistry';
import { ProviderWorkspaceRegistry } from '@/core/providers/ProviderWorkspaceRegistry';
import { InteractiveCanvasController } from '@/features/interactive-canvas/InteractiveCanvas';

jest.mock('obsidian', () => ({
  FileSystemAdapter: class { getBasePath() { return '/fixture'; } },
  ItemView: class {}, Modal: class {}, Notice: jest.fn(),
}));
jest.mock('@/core/providers/ProviderRegistry', () => ({ ProviderRegistry: {
  isEnabled: jest.fn(() => true), createSelectionLearningService: jest.fn(),
} }));
jest.mock('@/core/providers/ProviderWorkspaceRegistry', () => ({ ProviderWorkspaceRegistry: { ensureInitialized: jest.fn() } }));
jest.mock('@/features/selection-learning/SelectionLearningProvider', () => ({
  resolveSelectionLearningProviderContext: () => ({ providerId: 'claude' }),
}));
function deferred() {
  let resolve!: () => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<void>((yes, no) => { resolve = yes;reject = no; });
  return { promise, resolve, reject };
}
function setup() {
  const node = (id: string) => ({ id, type: 'text', x: 0, y: 0, width: 100, height: 100, ckbFunction: {
    version: 1, unit_id: id, parent_id: null, title: id, summary: '设计说明', implementation_summary: '未实现',
    requirement: '', state: 'proposed', human_confirmed: false, source_refs: [], session_refs: [],
  } });
  const document = { nodes: [node('a'), node('b')], edges: [] };
  const native = { file: { path: 'test.canvas' }, canvas: { getData: () => document, selection: new Set([{ id: 'a' }]) } };
  const plugin = { app: { vault: { adapter: new FileSystemAdapter() }, workspace: { detachLeavesOfType: jest.fn() } }, settings: {} };
  const controller = new InteractiveCanvasController(plugin as unknown as ConstructorParameters<typeof InteractiveCanvasController>[0]);
  Object.defineProperty(controller, 'getNative', { value: () => native });
  const view = { status: jest.fn(), render: jest.fn(), answer: jest.fn() };
  controller.attach(view as unknown as Parameters<typeof controller.attach>[0]);
  const service = { editText: jest.fn().mockResolvedValue({ success: true, clarification: '仅讨论' }), continueConversation: jest.fn(), cancel: jest.fn(), setModelOverride: jest.fn(), setProgressCallback: jest.fn() };
  jest.mocked(ProviderRegistry.createSelectionLearningService).mockReturnValue(service as unknown as ReturnType<typeof ProviderRegistry.createSelectionLearningService>);
  return { controller, native, view, service, document };
}
describe('讨论懒初始化与取消代次', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(ProviderRegistry.isEnabled).mockReturnValue(true);
    jest.mocked(ProviderWorkspaceRegistry.ensureInitialized).mockResolvedValue(undefined);
  });
  it('等待现有工作区初始化后才创建和调用执行器', async () => {
    const gate = deferred(), { controller, service } = setup();
    jest.mocked(ProviderWorkspaceRegistry.ensureInitialized).mockReturnValue(gate.promise);
    const pending = controller.ask('a', '解释');
    expect(ProviderWorkspaceRegistry.ensureInitialized).toHaveBeenCalledWith(expect.anything(), 'claude', 'interactive-canvas');
    expect(ProviderRegistry.createSelectionLearningService).not.toHaveBeenCalled();
    gate.resolve();await pending;
    expect(service.editText).toHaveBeenCalledTimes(1);
    expect(jest.mocked(ProviderWorkspaceRegistry.ensureInitialized).mock.invocationCallOrder[0]).toBeLessThan(jest.mocked(ProviderRegistry.createSelectionLearningService).mock.invocationCallOrder[0]);
    controller.dispose();
  });
  it.each(['cancel', 'switch', 'switch-before-poll', 'dispose'] as const)('初始化中%s后不创建过期执行器', async action => {
    const gate = deferred(), { controller, native } = setup();
    jest.mocked(ProviderWorkspaceRegistry.ensureInitialized).mockReturnValue(gate.promise);
    const pending = controller.ask('a', '解释');
    if (action === 'switch') { native.canvas.selection = new Set([{ id: 'b' }]);controller.sync(); }
    else if (action === 'switch-before-poll') native.canvas.selection = new Set([{ id: 'b' }]);
    else if (action === 'dispose') controller.dispose();
    else controller.cancel();
    gate.resolve();await pending;
    expect(ProviderRegistry.createSelectionLearningService).not.toHaveBeenCalled();
    expect(Reflect.get(controller, 'asking')).toBe(false);
    controller.dispose();
  });
  it('旧初始化失败不取消新一轮初始化', async () => {
    const old = deferred(), fresh = deferred(), { controller, service } = setup();
    jest.mocked(ProviderWorkspaceRegistry.ensureInitialized).mockReturnValueOnce(old.promise).mockReturnValueOnce(fresh.promise);
    const first = controller.ask('a', '旧问题');controller.cancel();const second = controller.ask('a', '新问题');
    old.reject(new Error('旧初始化失败'));await first;
    expect(Reflect.get(controller, 'asking')).toBe(true);
    fresh.resolve();await second;expect(service.editText).toHaveBeenCalledTimes(1);controller.dispose();
  });
  it('没有启用Provider时不启动初始化且保留节点', async () => {
    const { controller, document, view } = setup(), before = JSON.stringify(document);
    jest.mocked(ProviderRegistry.isEnabled).mockReturnValue(false);
    await controller.ask('a', '解释');expect(ProviderWorkspaceRegistry.ensureInitialized).not.toHaveBeenCalled();
    expect(view.status).toHaveBeenLastCalledWith(expect.stringContaining('尚未启用'));
    expect(JSON.stringify(document)).toBe(before);controller.dispose();
  });
});
