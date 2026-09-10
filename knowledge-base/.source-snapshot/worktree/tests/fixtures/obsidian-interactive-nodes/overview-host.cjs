const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict'), { spawn, spawnSync } = require('node:child_process');
const E = process.argv[2], packageDir = process.argv[3], { chromium } = require(process.argv[4]), exe = process.argv[5];
const ID = 'code-knowledge-builder-companion', vault = path.join(E, 'host-vault'), profile = path.join(E, 'host-profile');
const destination = path.join(vault, '.obsidian/plugins', ID), target = path.join(vault, '知识库总览.canvas');
const checks = [], errors = [];
const write = (name, value) => fs.writeFileSync(path.join(E, name), JSON.stringify(value, null, 2));
(async () => {
  fs.mkdirSync(destination, { recursive: true });fs.mkdirSync(profile, { recursive: true });
  for (const f of ['main.js', 'manifest.json', 'styles.css']) fs.copyFileSync(path.join(packageDir, f), path.join(destination, f));
  fs.writeFileSync(path.join(vault, '.obsidian/community-plugins.json'), JSON.stringify([ID]));
  fs.writeFileSync(path.join(profile, 'obsidian.json'), JSON.stringify({ vaults: { overview: { path: vault, ts: Date.now(), open: true } } }));
  const env = { ...process.env };for (const k of ['CKB_OUTPUT', 'CKB_SCRIPT', 'CKB_PYTHON']) delete env[k];
  const child = spawn(exe, ['--user-data-dir=' + profile, '--remote-debugging-port=19458'], { cwd: E, env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
  write('host-pid.json', { pid: child.pid, profile });
  child.stdout.on('data', d => fs.appendFileSync(path.join(E, 'host.stdout'), d));child.stderr.on('data', d => fs.appendFileSync(path.join(E, 'host.stderr'), d));
  let browser, page;
  try {
    for (let i = 0; i < 40; i++) { try { browser = await chromium.connectOverCDP('http://127.0.0.1:19458');break; } catch { await new Promise(r => setTimeout(r, 500)); } }
    if (!browser) throw Error('宿主端口未就绪');
    page = browser.contexts()[0].pages()[0];page.on('pageerror', e => errors.push(e.message));
    await page.waitForFunction(() => !!window.app, null, { timeout: 60000 });
    await page.waitForFunction(id => !!app.plugins.plugins[id] || document.body.innerText.includes('信任仓库作者并启用插件'), ID, { timeout: 60000 });
    const trust = page.getByRole('button', { name: '信任仓库作者并启用插件', exact: true });
    if (await trust.isVisible()) await trust.click();
    await page.waitForFunction(id => !!window.app?.plugins?.plugins[id], ID, { timeout: 60000 });
    assert.equal(await page.evaluate(() => app.vault.adapter.getBasePath()), vault);
    // 本隔离配置没有任何模型凭据；生成路径不调用Provider。
    const generation = async () => {
      const start = Date.now();await page.getByLabel('生成知识库白板', { exact: true }).first().click();
      await page.waitForFunction(id => app.plugins.plugins[id].interactiveCanvas.overviewAbort === null, ID, { timeout: 60000 });
      return Date.now() - start;
    };
    const elapsed = await generation();
    assert.ok(fs.existsSync(target));await page.locator('.ckb-function-panel').waitFor();
    const disk = () => JSON.parse(fs.readFileSync(target, 'utf8'));
    const data = () => page.evaluate(() => app.workspace.getLeavesOfType('canvas').find(l => l.view.file?.path === '知识库总览.canvas').view.canvas.getData());
    let d = disk();const graph = JSON.parse(fs.readFileSync(path.join(E, 'host-output/graph.json'), 'utf8'));
    assert.equal(d.nodes[0].ckbOverviewInfo.entityCount, graph.entities.length);
    const catalog = d.nodes[0].ckbOverviewCatalog.nodes;
    assert.equal(new Set(catalog.flatMap(n => n.ckbOverviewDetails.map(x => x.id))).size, graph.entities.length);
    const primaryIds = catalog.flatMap(n => n.ckbOverviewDetails.filter(x => x.category === '主功能').map(x => x.id));
    assert.deepEqual(primaryIds.sort(), graph.entities.filter(e => e.classification === 'page').map(e => e.id).sort());
    const known = new Set([d.nodes[0].id, ...catalog.map(n => n.id)]);
    assert.ok(catalog.every(n => known.has(n.ckbFunction.parent_id)));
    for (const pageNode of catalog) {
      let parent = pageNode;const seen = new Set();
      while (parent.ckbFunction.parent_id !== d.nodes[0].id) {
        assert.ok(!seen.has(parent.id));seen.add(parent.id);
        parent = catalog.find(n => n.id === parent.ckbFunction.parent_id);assert.ok(parent);
      }
    }
    checks.push('all-primary-pages-navigable-and-auxiliary-owner-mapping');
    assert.ok(d.edges.every(e => e.label === '包含'));checks.push('visible-ribbon-full-graph-generation-open-no-provider');
    await page.waitForTimeout(5000);await page.screenshot({ path: path.join(E, '01-overview-first-screen.png'), fullPage: true });
    await page.evaluate(() => { app.workspace.leftSplit.collapse();app.workspace.rightSplit.collapse();app.workspace.getLeavesOfType('canvas')[0].view.canvas.zoomToFit(); });
    await page.waitForTimeout(700);await page.screenshot({ path: path.join(E, '01b-native-full-hierarchy.png'), fullPage: true });
    await page.evaluate(() => { app.workspace.leftSplit.expand();app.workspace.rightSplit.expand(); });
    await page.waitForTimeout(700);
    const selected = catalog.find(n => n.ckbOverviewSource?.path === 'scripts/ckb_core/machine_knowledge.py' && n.ckbOverviewSource?.kind === 'file');
    assert.ok(selected);
    async function searchAndOpen(query, id, screenshot) {
      await page.getByRole('textbox', { name: '搜索全部功能职责' }).fill(query);
      while (!await page.locator(`[data-function-node="${id}"]`).count()) {
        await page.getByRole('button', { name: '下一页功能', exact: true }).click();
      }
      await page.locator(`[data-function-node="${id}"]`).scrollIntoViewIfNeeded();await page.waitForTimeout(400);
      await page.screenshot({ path: path.join(E, screenshot), fullPage: true });
      await page.locator(`[data-function-node="${id}"]`).click();
      await page.waitForFunction(({ id, node }) => app.plugins.plugins[id].interactiveCanvas.native.canvas.getData().nodes.some(n => n.id === node), { id: ID, node: id });
      await page.waitForTimeout(700);
    }
    await searchAndOpen('检索', selected.id, '02a-retrieval-entry.png');
    await page.locator('.ckb-overview-details > summary').click();
    await page.getByRole('textbox', { name: '搜索职责' }).fill('');
    await page.locator('.ckb-overview-details a').first().waitFor({ state: 'attached' });
    const link = await page.locator('.ckb-overview-details a').first().getAttribute('href');assert.ok(link.startsWith('vscode://file/'));
    await page.locator('.ckb-overview-details details > summary').first().click();
    await page.screenshot({ path: path.join(E, '02-module-details.png'), fullPage: true });
    checks.push('native-chinese-hierarchy-search-progressive-source-links');
    const buildPage = catalog.find(n => n.ckbOverviewSource?.path === 'scripts/ckb_core/pipeline.py' && n.ckbOverviewSource?.kind === 'file');
    await page.getByRole('button', { name: '返回总览', exact: true }).click();
    await searchAndOpen('编排固定快照', buildPage.id, '02b-build-entry.png');
    checks.push('native-retrieval-and-build-responsibilities-discoverable');
    const secondElapsed = await generation();
    d = disk();const before = JSON.stringify(d);await generation();assert.equal(JSON.stringify(disk()), before);checks.push('native-repeat-idempotent');
    // 原生实时数据包含手改文字、位置及同端点边；不从初次生成副本覆盖。
    const chosen = catalog.find(n => n.ckbOverviewSource?.path === 'scripts/ckb_core/machine_knowledge.py' && n.ckbOverviewSource?.qualified === 'retrieve_machine');
    assert.ok(chosen);await page.evaluate(async ({ id, node }) => app.plugins.plugins[id].interactiveCanvas.navigateOverview(node), { id: ID, node: chosen.id });
    await page.evaluate(async id => {
      const v = app.workspace.getLeavesOfType('canvas').find(l => l.view.file?.path === '知识库总览.canvas').view, c = v.canvas, d = c.getData();
      const n = d.nodes.find(n => n.id === id);n.text = '用户在原生白板手改的文字';n.x += 71;n.y += 29;
      d.nodes.push({ id: 'human-card', type: 'text', text: '用户手工卡片', x: 90, y: 400, width: 260, height: 180 });
      const edge = d.edges[0];d.edges.push({ id: 'human-same-endpoints', fromNode: edge.fromNode, toNode: edge.toNode, fromSide: 'bottom', toSide: 'top', label: '人类连线' });
      c.setData(d);c.requestSave();await v.save();
    }, chosen.id);
    const edited = disk(), expected = edited.nodes.find(n => n.id === chosen.id);
    await generation();d = disk();assert.equal(d.nodes.find(n => n.id === chosen.id).text, expected.text);assert.equal(d.nodes.find(n => n.id === chosen.id).x, expected.x);
    assert.deepEqual(d.nodes.find(n => n.id === 'human-card'), edited.nodes.find(n => n.id === 'human-card'));
    assert.deepEqual(d.edges.find(n => n.id === 'human-same-endpoints'), edited.edges.find(n => n.id === 'human-same-endpoints'));checks.push('native-user-text-layout-cards-same-endpoint-edge-preserved');
    await page.evaluate(({ id, node }) => app.plugins.plugins[id].interactiveCanvas.select(node), { id: ID, node: chosen.id });
    await page.getByRole('textbox', { name: '需求', exact: true }).fill('无模型时仍可编辑');await page.getByRole('button', { name: '保存功能', exact: true }).click();await page.waitForTimeout(650);
    assert.equal(disk().nodes.find(n => n.id === chosen.id).ckbFunction.requirement, '无模型时仍可编辑');checks.push('existing-function-editor-works-on-generated-node');
    const saved = disk();
    await page.evaluate(async () => { app.workspace.detachLeavesOfType('canvas');await app.workspace.getLeaf().openFile(app.vault.getAbstractFileByPath('知识库总览.canvas')); });await page.waitForTimeout(600);
    assert.deepEqual((await data()).nodes.find(n => n.id === chosen.id).ckbFunction, saved.nodes.find(n => n.id === chosen.id).ckbFunction);checks.push('actual-disk-close-reopen-preserves-fields');
    // 同一原生宿主验证损坏输入失败不破坏原画布。
    const graphPath = path.join(E, 'host-output/graph.json'), originalGraph = fs.readFileSync(graphPath);
    const stableBefore = disk(), originalItem = graph.entities.find(e => e.path === 'scripts/ckb_core/machine_knowledge.py' && e.qualified_name === 'retrieve_machine');
    const changed = structuredClone(graph), item = changed.entities.find(e => e.id === originalItem.id), oldId = item.id;
    item.id = 'new-commit-entity';item.range.start_line += 50;changed.repository.commit = 'new-version-fixture';
    for (const e of changed.entities) { if (e.owner_page_id === oldId) e.owner_page_id = item.id;if (e.parent_id === oldId) e.parent_id = item.id; }
    try {
      fs.writeFileSync(graphPath, JSON.stringify(changed));await generation();
      assert.equal(disk().nodes.filter(n => n.id === chosen.id).length, 1);assert.equal(disk().nodes.find(n => n.id === chosen.id).x, stableBefore.nodes.find(n => n.id === chosen.id).x);
      item.classification = 'appendix';fs.writeFileSync(graphPath, JSON.stringify(changed));await generation();
      assert.equal(disk().nodes.find(n => n.id === chosen.id).ckbOverviewRetired, true);
      fs.writeFileSync(graphPath, originalGraph);await generation();
      const restored = disk();assert.equal(restored.nodes.filter(n => n.id === chosen.id).length, 1);assert.equal(restored.nodes.find(n => n.id === chosen.id).ckbFunction.requirement, '无模型时仍可编辑');
      assert.ok(restored.edges.some(e => e.id === 'human-same-endpoints'));
    } finally { fs.writeFileSync(graphPath, originalGraph); }
    checks.push('native-line-commit-rank-remove-reenter-stable-identity');
    let originalCanvas = fs.readFileSync(target);
    try {
      fs.writeFileSync(graphPath, '{broken');await generation();assert.deepEqual(fs.readFileSync(target), originalCanvas);
      fs.writeFileSync(graphPath, JSON.stringify({ schema_version: 3, entities: [], links: [] }));await generation();assert.deepEqual(fs.readFileSync(target), originalCanvas);
    } finally { fs.writeFileSync(graphPath, originalGraph); }
    const contractPath = path.join(vault, '.ckb/output-contract.json'), contract = fs.readFileSync(contractPath);
    try { fs.writeFileSync(contractPath, '{}');await generation();assert.deepEqual(fs.readFileSync(target), originalCanvas); } finally { fs.writeFileSync(contractPath, contract); }
    checks.push('native-corrupt-graph-old-schema-bad-binding-no-write');
    await page.evaluate(async () => {
      for (const leaf of app.workspace.getLeavesOfType('canvas')) await leaf.view.save();
    });await page.waitForTimeout(2500);
    await page.evaluate(() => app.workspace.detachLeavesOfType('canvas'));await page.waitForTimeout(400);
    await page.evaluate(async () => {
      await app.vault.rename(app.vault.getAbstractFileByPath('知识库总览.canvas'), '已保存总览.canvas');
      await app.vault.create('知识库总览.canvas', JSON.stringify({ nodes: [{ id: 'manual-only', type: 'text', text: '原有用户画布', x: 0, y: 0, width: 200, height: 100 }], edges: [] }));
    });
    const collision = fs.readFileSync(target);await generation();assert.deepEqual(fs.readFileSync(target), collision);
    await page.evaluate(async () => {
      await app.vault.rename(app.vault.getAbstractFileByPath('知识库总览.canvas'), '用户同名画布.canvas');
      await app.vault.rename(app.vault.getAbstractFileByPath('已保存总览.canvas'), '知识库总览.canvas');
      await app.workspace.getLeaf().openFile(app.vault.getAbstractFileByPath('知识库总览.canvas'));
    });
    await page.waitForTimeout(600);checks.push('native-preexisting-target-conflict-no-overwrite');
    await page.evaluate(async () => { for (const leaf of app.workspace.getLeavesOfType('canvas')) await leaf.view.save(); });
    await page.waitForTimeout(2500);originalCanvas = fs.readFileSync(target);
    // 取消与卸载：加载过程中立刻取消，避免写入；已有Provider生命周期由原专项测试复查。
    await page.evaluate(async id => { const c = app.plugins.plugins[id].interactiveCanvas, p = c.generateOverview();c.cancelOverview();await p; }, ID);
    assert.deepEqual(fs.readFileSync(target), originalCanvas);checks.push('native-generation-cancellation-no-write');
    await page.evaluate(async id => { window.oldOverview = app.plugins.plugins[id].interactiveCanvas;const pending = oldOverview.generateOverview();await app.plugins.disablePlugin(id);await pending; }, ID);await page.waitForTimeout(700);
    assert.deepEqual(await page.evaluate(() => ({ disposed: oldOverview.disposed, pending: oldOverview.overviewAbort, service: oldOverview.service, timer: oldOverview.timer })), { disposed: true, pending: null, service: null, timer: null });
    assert.deepEqual(fs.readFileSync(target), originalCanvas);checks.push('native-unload-cleans-controller-preserves-canvas');
    await page.evaluate(async id => { await app.plugins.enablePlugin(id); }, ID);await generation();
    await page.screenshot({ path: path.join(E, '03-overview-reloaded.png'), fullPage: true });
    if (process.argv[6] && process.argv[7]) {
      const preserved = disk();const rollback = [];
      for (const mode of ['old', 'new']) {
        await page.evaluate(async id => app.plugins.disablePlugin(id), ID);
        const args = [process.argv[7], mode, '--vault', vault];
        const p = spawnSync(process.argv[6], args, { cwd: E, encoding: 'utf8', windowsHide: true, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
        rollback.push({ command: [process.argv[6], ...args], cwd: E, stdout: p.stdout, stderr: p.stderr, exit_status: p.status });
        write('native-rollback-commands.json', rollback);
        assert.equal(p.status, 0);await page.evaluate(async id => { await app.plugins.loadManifests();await app.plugins.enablePlugin(id); }, ID);
        assert.equal(await page.evaluate(id => app.plugins.plugins[id].manifest.version, ID), mode === 'old' ? '0.9.0' : '0.9.1');
        assert.equal(await page.evaluate(id => !!app.commands.commands[id + ':generate-knowledge-overview'], ID), true);
        assert.deepEqual(disk(), preserved);
      }
      write('native-rollback.json', { status: 'passed', commands: rollback, preserved_canvas: true });checks.push('native-0.9.0-rollback-0.9.1-restored-without-canvas-loss');
    }
    const result = { status: 'passed', checks, errors, native_canvas: true, version: await page.evaluate(id => app.plugins.plugins[id].manifest.version, ID), entities: graph.entities.length, relations: graph.links.length, cards: disk().nodes.length, first_ms: elapsed, second_ms: secondElapsed, browser: browser.version(), provider: 'not-configured-and-not-called' };
    write('overview-host-result.json', result);console.log(JSON.stringify(result));
    await page.evaluate(async id => app.plugins.disablePlugin(id), ID);
  } catch (e) { if (page) await page.screenshot({ path: path.join(E, 'overview-host-failure.png'), fullPage: true });write('overview-host-failure.json', { error: String(e), checks, errors });throw e; }
  finally { if (browser) await browser.close();if (child.exitCode === null) child.kill(); }
})().catch(e => { console.error(e);process.exitCode = 1; });
