const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
const {chromium}=require(process.argv[4]);
const E=process.argv[2],packageDir=process.argv[3],exe=process.argv[5];
const ID='code-knowledge-builder-companion',vault=E+'/host-vault',profile=E+'/host-profile';
const input={status:'experimental-interchange-only',version:'0.1-draft',units:[
 {unit_id:'root',parent_id:null,title:'资料目录',summary:'逐层查找资料',implementation_summary:'尚未实现',state:'proposed',source_refs:[],session_refs:[]},
 {unit_id:'child',parent_id:'root',title:'正文阅读',summary:'展示正文',implementation_summary:'导入的设计摘要',state:'verified',source_refs:[{path:'sample.py',commit:'opaque-commit-1234567890',sha256:'opaque-sha256-1234567890'},{}],session_refs:[]}
],relations:[]};
(async()=>{
 fs.mkdirSync(vault+'/.obsidian/plugins/'+ID,{recursive:true});fs.mkdirSync(profile,{recursive:true});
 for(const f of ['main.js','manifest.json','styles.css'])fs.copyFileSync(packageDir+'/'+f,vault+'/.obsidian/plugins/'+ID+'/'+f);
 fs.writeFileSync(vault+'/.obsidian/community-plugins.json',JSON.stringify([ID]));
 fs.writeFileSync(profile+'/obsidian.json',JSON.stringify({vaults:{ckbfunctional:{path:vault,ts:Date.now(),open:true}}}));
 const seed={nodes:[{id:'ordinary',type:'text',text:'用户原有节点',x:15,y:40,width:260,height:180,thirdParty:{keep:'untouched'}},{id:'ordinary2',type:'text',text:'另一个用户节点',x:15,y:300,width:260,height:180}],edges:[{id:'ordinary-edge',fromNode:'ordinary',toNode:'ordinary2',fromSide:'bottom',toSide:'top',label:'用户原有连线',thirdParty:{keep:true}}]};
 fs.writeFileSync(vault+'/功能验证.canvas',JSON.stringify(seed));
 const env={...process.env};delete env.CKB_OUTPUT;delete env.CKB_PYTHON;delete env.CKB_SCRIPT;
 const child=spawn(exe,['--user-data-dir='+profile,'--remote-debugging-port=19348'],{cwd:E,env,stdio:['ignore','pipe','pipe']});
 child.stdout.on('data',d=>fs.appendFileSync(E+'/host-test.stdout',d));child.stderr.on('data',d=>fs.appendFileSync(E+'/host-test.stderr',d));
 let browser,page;const checks=[],errors=[];
 try{
  for(let i=0;i<30;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:19348');break}catch{await new Promise(r=>setTimeout(r,1000))}}
  if(!browser)throw Error('Obsidian CDP未就绪');page=browser.contexts()[0].pages()[0];page.on('pageerror',e=>errors.push(e.message));
  await page.waitForFunction(id=>!!window.app?.plugins?.plugins[id]||document.body.innerText.includes('信任仓库作者并启用插件'),ID,{timeout:60000});
  const trust=page.getByRole('button',{name:'信任仓库作者并启用插件',exact:true});if(await trust.isVisible())await trust.click();
  await page.waitForFunction(id=>!!window.app?.plugins?.plugins[id],ID,{timeout:30000});
  await page.evaluate(()=>new Promise(resolve=>app.workspace.onLayoutReady(resolve)));
  assert.equal(await page.evaluate(()=>app.vault.getName()),'host-vault');
  await page.evaluate(async()=>{await app.workspace.getLeaf().openFile(app.vault.getAbstractFileByPath('功能验证.canvas'));});
  await page.waitForTimeout(600);
  const data=()=>page.evaluate(()=>app.workspace.getLeavesOfType('canvas')[0].view.canvas.getData());
  const initial=await data();
  await page.evaluate(id=>app.commands.executeCommandById(id+':open-function-nodes'),ID);
  await page.locator('.ckb-function-panel').waitFor();
  await page.waitForTimeout(800);
  async function importInput(value){await page.getByRole('button',{name:'导入功能',exact:true}).click();await page.getByRole('textbox',{name:'粘贴功能节点 JSON'}).fill(JSON.stringify(value));await page.getByRole('button',{name:'确定',exact:true}).click();}
  await importInput(input);await page.waitForFunction(()=>app.workspace.getLeavesOfType('canvas')[0].view.canvas.getData().nodes.length===4);
  await page.waitForTimeout(600);let current=await data();
  assert.deepEqual(current.nodes.find(n=>n.id==='ordinary'),initial.nodes.find(n=>n.id==='ordinary'));assert.deepEqual(current.edges.find(n=>n.id==='ordinary-edge'),initial.edges.find(n=>n.id==='ordinary-edge'));checks.push('native-import-preserves-user-nodes-edges-layout-extensions');
  const root=current.nodes.find(n=>n.ckbFunction?.unit_id==='root').id,childId=current.nodes.find(n=>n.ckbFunction?.unit_id==='child').id;
  async function clickNode(id){await page.evaluate(()=>app.workspace.getLeavesOfType('canvas')[0].view.canvas.zoomToFit());await page.waitForTimeout(400);const box=await page.evaluate(id=>{const r=app.workspace.getLeavesOfType('canvas')[0].view.canvas.nodes.get(id).nodeEl.getBoundingClientRect();return {x:r.x+20,y:r.y+15}},id);await page.mouse.click(box.x,box.y);await page.waitForTimeout(650);}
  await clickNode(childId);await page.locator('.ckb-function-panel h4').filter({hasText:'正文阅读'}).waitFor();checks.push('native-pointer-selection-updates-panel');
  assert.ok(!(await page.locator('body').innerText()).includes('opaque-commit-1234567890'));
  await page.locator('.ckb-function-panel summary').filter({hasText:/^来源 1$/}).click();assert.ok(!(await page.locator('body').innerText()).includes('opaque-commit-1234567890'));
  await page.locator('.ckb-function-panel summary').filter({hasText:'查看技术详情'}).first().click();assert.ok((await page.locator('body').innerText()).includes('opaque-commit-1234567890'));checks.push('native-progressive-reference-disclosure');
  await page.locator('.ckb-function-panel summary').filter({hasText:/^来源 1$/}).click();
  await page.evaluate(async({root,childId})=>{const v=app.workspace.getLeavesOfType('canvas')[0].view,c=v.canvas,d=c.getData();d.edges.push({id:'user-same-endpoints',fromNode:root,toNode:childId,fromSide:'bottom',toSide:'top',label:'用户同端点连线'});c.setData(d);c.requestSave();await v.save();},{root,childId});
  await page.getByRole('textbox',{name:'功能说明',exact:true}).fill('人类编辑后的说明');await page.getByRole('textbox',{name:'需求',exact:true}).fill('保持离线阅读');await page.getByRole('combobox',{name:'父功能'}).selectOption('');
  await page.getByRole('button',{name:'保存功能',exact:true}).click();await page.waitForTimeout(900);
  current=await data();assert.equal(current.nodes.find(n=>n.id===childId).ckbFunction.summary,'人类编辑后的说明');assert.equal(current.nodes.find(n=>n.id===childId).ckbFunction.parent_id,null);assert.ok(current.edges.some(e=>e.id==='user-same-endpoints'));assert.ok(!current.edges.some(e=>e.ckbFunctionParent===true));checks.push('edit-save-parent-change-retains-user-same-endpoint-edge');
  await page.getByRole('button',{name:'人工确认',exact:true}).click();await page.waitForTimeout(700);current=await data();assert.equal(current.nodes.find(n=>n.id===childId).ckbFunction.human_confirmed,true);assert.equal(current.nodes.find(n=>n.id===childId).ckbFunction.state,'verified');checks.push('human-confirmation-separate-from-input-state');
  const beforeDuplicate=await data();await importInput(input);await page.waitForTimeout(900);assert.deepEqual(await data(),beforeDuplicate);checks.push('duplicate-import-no-overwrite');
  const beforeBad=await data();await importInput({broken:true});await page.locator('.modal').filter({hasText:'导入文件不是共同功能节点格式'}).waitFor();assert.deepEqual(await data(),beforeBad);await page.keyboard.press('Escape');checks.push('corrupt-import-no-write');
  await page.getByRole('button',{name:'创建功能',exact:true}).click();await page.getByRole('textbox',{name:'输入功能标题'}).fill('无源码的新设计');await page.getByRole('button',{name:'确定',exact:true}).click();await page.waitForTimeout(800);
  current=await data();assert.equal(current.nodes.filter(n=>n.ckbFunction).length,3);const created=current.nodes.find(n=>n.ckbFunction?.title==='无源码的新设计');assert.deepEqual(created.ckbFunction.source_refs,[]);checks.push('create-design-without-source');
  await clickNode(created.id);await page.getByRole('combobox',{name:'父功能'}).selectOption('root');await page.getByRole('button',{name:'保存功能',exact:true}).click();await page.waitForTimeout(700);
  await clickNode(root);await page.getByRole('combobox',{name:'父功能'}).selectOption(created.ckbFunction.unit_id);await page.getByRole('button',{name:'保存功能',exact:true}).click();await page.getByRole('status').filter({hasText:'循环'}).waitFor();checks.push('cycle-edit-no-write');
  await clickNode(childId);await page.screenshot({path:E+'/01-native-canvas-edited.png',fullPage:true});
  // 直接读取磁盘，不把内存对象当作持久化证明。
  const disk=JSON.parse(fs.readFileSync(vault+'/功能验证.canvas','utf8'));assert.deepEqual(disk.nodes.find(n=>n.id===childId).ckbFunction,(await data()).nodes.find(n=>n.id===childId).ckbFunction);
  await page.evaluate(()=>app.workspace.detachLeavesOfType('canvas'));await page.waitForTimeout(350);
  await page.evaluate(async()=>{await app.workspace.getLeaf('tab').openFile(app.vault.getAbstractFileByPath('功能验证.canvas'));});
  await page.waitForFunction(()=>app.workspace.getLeavesOfType('canvas').length>0);await page.waitForTimeout(700);
  assert.deepEqual((await data()).nodes.find(n=>n.id===childId).ckbFunction,disk.nodes.find(n=>n.id===childId).ckbFunction);checks.push('disk-save-close-reopen-keeps-extension');
  await clickNode(childId);
  await page.getByRole('button',{name:'取消讨论',exact:true}).click();assert.match(await page.getByRole('status').innerText(),/已取消讨论/);
  await page.evaluate(id=>{window.__oldController=app.plugins.plugins[id].interactiveCanvas;app.workspace.detachLeavesOfType('ckb-interactive-canvas');},ID);await page.waitForTimeout(500);
  assert.equal(await page.evaluate(()=>window.__oldController.service),null);checks.push('panel-close-releases-discussion');
  await page.evaluate(async id=>{await app.plugins.disablePlugin(id);},ID);await page.waitForTimeout(800);
  assert.deepEqual(await page.evaluate(()=>({disposed:window.__oldController.disposed,timer:window.__oldController.timer,service:window.__oldController.service,views:app.workspace.getLeavesOfType('ckb-interactive-canvas').length})),{disposed:true,timer:null,service:null,views:0});
  assert.deepEqual(JSON.parse(fs.readFileSync(vault+'/功能验证.canvas','utf8')).nodes.find(n=>n.id===childId).ckbFunction,disk.nodes.find(n=>n.id===childId).ckbFunction);checks.push('plugin-unload-keeps-canvas-data-and-cleans-controller');
  await page.screenshot({path:E+'/02-native-canvas-plugin-unloaded.png',fullPage:true});
  await page.evaluate(async id=>{await app.plugins.enablePlugin(id);app.commands.executeCommandById(id+':open-function-nodes');},ID);await page.locator('.ckb-function-panel').waitFor();await clickNode(childId);assert.equal(await page.getByRole('textbox',{name:'需求',exact:true}).inputValue(),'保持离线阅读');checks.push('plugin-reload-retains-fields');
  // 不配置真实模型时也保留可编辑能力；实际Provider测试单独记录。
  await page.screenshot({path:E+'/03-native-canvas-reloaded.png',fullPage:true});
  fs.writeFileSync(E+'/host-result.json',JSON.stringify({status:'passed',checks,errors,vault,input,version:await page.evaluate(()=>app.appId||'obsidian'),browser:browser.version(),native_canvas:true,provider:'separate-test-required'},null,2));console.log(JSON.stringify({status:'passed',checks,errors}));
 }catch(e){if(page)await page.screenshot({path:E+'/host-failure.png',fullPage:true});fs.writeFileSync(E+'/host-failure.json',JSON.stringify({checks,error:String(e),errors},null,2));throw e;}
 finally{if(browser)await browser.close();if(child.exitCode===null)child.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
