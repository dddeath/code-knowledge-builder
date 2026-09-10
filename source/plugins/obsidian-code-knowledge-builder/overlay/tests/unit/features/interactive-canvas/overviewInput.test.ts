import { readFile, realpath } from 'node:fs/promises';

import { readOverviewInput } from '@/features/interactive-canvas/overviewInput';
import { parseCkbOutputContract } from '@/features/selection-learning/CkbStdioClient';

jest.mock('node:fs/promises', () => ({ readFile: jest.fn(), realpath: jest.fn() }));
jest.mock('@/features/selection-learning/CkbStdioClient', () => ({ parseCkbOutputContract: jest.fn() }));
const graph = { schema_version: 4, entities: [], links: [] };
describe('全库读取与绑定', () => {
  beforeEach(() => {
    jest.clearAllMocks();jest.mocked(realpath).mockResolvedValue('/out');
    jest.mocked(parseCkbOutputContract).mockReturnValue({ outputRoot: '/out', python: '/python', ckbScript: '/ckb.py' });
    jest.mocked(readFile).mockImplementation(async path => {
      if (String(path).endsWith('output-contract.json')) return '{}';
      if (String(path).endsWith('graph.json')) return JSON.stringify(graph);
      throw new Error('missing');
    });
  });
  it('完整图不走brief截断；缺少新鲜度和导航时仍返回已知事实', async () => {
    const r = await readOverviewInput('/vault', new AbortController().signal);
    expect(r.graph).toEqual(graph);expect(r.freshness).toContain('未核验');expect(r.navigation).toEqual([]);
    expect(jest.mocked(readFile).mock.calls.some(c => String(c[0]).includes('brief'))).toBe(false);
  });
  it('缺失绑定在读取图前失败', async () => {
    jest.mocked(readFile).mockRejectedValue(new Error('missing contract'));
    await expect(readOverviewInput('/vault', new AbortController().signal)).rejects.toThrow('missing contract');
    expect(readFile).toHaveBeenCalledTimes(1);
  });
  it('损坏绑定在读取图前失败', async () => {
    jest.mocked(parseCkbOutputContract).mockReturnValue(null);
    await expect(readOverviewInput('/vault', new AbortController().signal)).rejects.toThrow('绑定');
    expect(readFile).toHaveBeenCalledTimes(1);
  });
  it('取消不会被可选文件的缺失降级吞掉', async () => {
    const abort = new AbortController();abort.abort();
    await expect(readOverviewInput('/vault', abort.signal)).rejects.toThrow();
  });
});
