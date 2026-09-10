import { readFile, realpath } from 'node:fs/promises';
import path from 'node:path';

import { parseCkbOutputContract } from '../selection-learning/CkbStdioClient';
import type { OverviewInput } from './overview';
import { row } from './overview';

export async function readOverviewInput(vault: string, signal: AbortSignal): Promise<OverviewInput> {
  const binding = parseCkbOutputContract(await readFile(path.join(vault, '.ckb/output-contract.json'), { encoding: 'utf8', signal }), vault);
  if (!binding) throw new Error('当前 vault 的知识库绑定缺失或损坏；原白板保持不变。');
  const output = await realpath(binding.outputRoot);
  const graph = row(JSON.parse(await readFile(path.join(output, 'graph.json'), { encoding: 'utf8', signal })));
  let freshness = '源码当前状态未核验；显示固定知识库版本。';
  try {
    const state = row(JSON.parse(await readFile(path.join(output, 'workspace-meta/freshness/state.json'), { encoding: 'utf8', signal })));
    const labels: Record<string, string> = { 'stale-committed': '源码已有新提交，知识库事实陈旧', 'stale-dirty': '源码有未提交修改', current: '上次检查时与源码一致', fresh: '上次检查时与源码一致' };
    freshness = `最近检查：${labels[String(state.state)] || '源码状态待核验'}（${String(state.observed_at_utc || '时间未记录')}）。当前源码未重新核验。`;
  } catch { signal.throwIfAborted(); }
  const navigation: string[] = [];
  for (const entry of ['INDEX.md', 'WIKI.md', 'RECORDS.md', 'REFERENCES.md']) {
    try { await readFile(path.join(vault, entry), { encoding: 'utf8', signal });navigation.push(entry); } catch { signal.throwIfAborted(); }
  }
  signal.throwIfAborted();
  return { graph, output, freshness, navigation };
}
