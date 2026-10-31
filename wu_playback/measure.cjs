/* Isolated software-playback measurement; no offline quality enters the page. */
const fs=require('node:fs'), path=require('node:path'), http=require('node:http');
const crypto=require('node:crypto'), zlib=require('node:zlib'), os=require('node:os');
const {performance}=require('node:perf_hooks'), {spawnSync}=require('node:child_process');
const {FairService}=require('../player_timing/service.cjs');
const root=path.resolve(__dirname,'..');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const save=(p,value)=>fs.writeFileSync(p,JSON.stringify(value),{flag:'wx'});

function safePath(base,relative) {
  if(typeof relative!=='string'||!relative||relative.includes('\\')||relative.includes(':')||relative.split('/').includes('..')||path.posix.isAbsolute(relative)) throw Error('Unsafe media path');
  const realBase=fs.realpathSync(base), target=fs.realpathSync(path.resolve(realBase,relative));
  if(!target.startsWith(realBase+path.sep)) throw Error('Media path escapes private root');
  return target;
}

function validateEntry(entry) {
  const allowed=['index','case_id','repetition','control','clip','key','policy','unit_seconds','buffered','units'];
  if(Object.keys(entry).some(k=>!allowed.includes(k))||!allowed.every(k=>Object.hasOwn(entry,k))) throw Error('Delivery allowlist differs');
  if(![10,2].includes(entry.unit_seconds)||typeof entry.buffered!=='boolean'||!['none','late_recipient','background'].includes(entry.control)) throw Error('Invalid delivery configuration');
  if(entry.units.length!==40/entry.unit_seconds) throw Error('Four full recovery parents required');
  for(const [j,u] of entry.units.entries()) {
    if(Object.keys(u).sort().join(',')!=='child,duration,files,parent'||u.duration!==entry.unit_seconds||u.files.length!==2) throw Error('Unit schema');
    if(u.parent!==Math.floor(j/(10/entry.unit_seconds))||u.child!==j%(10/entry.unit_seconds)) throw Error('Unit order');
    for(const f of u.files) {
      if(Object.keys(f).sort().join(',')!=='bytes,duration,frames,relative_path,sha256'||f.duration!==u.duration||f.frames!==30*u.duration||!Number.isSafeInteger(f.bytes)||f.bytes<=0||!/^[a-f0-9]{64}$/.test(f.sha256)) throw Error('File schema');
    }
  }
}

function runtime(browserPath,modulePath) {
  const dir=path.dirname(browserPath); const names=['chrome.exe','chrome.dll','resources.pak','icudtl.dat'];
  return {platform:process.platform,release:os.release(),arch:process.arch,node:process.version,
    node_sha256:hash(fs.readFileSync(process.execPath)),playwrightVersion:require(path.join(modulePath,'package.json')).version,
    playwright_package_sha256:hash(fs.readFileSync(path.join(modulePath,'package.json'))),
    browser_files:Object.fromEntries(names.map(n=>[n,hash(fs.readFileSync(path.join(dir,n)))])),
    cpu:os.cpus()[0].model,logical_cpus:os.cpus().length,total_memory_bytes:os.totalmem(),headless:true,
    args:['--autoplay-policy=no-user-gesture-required','--disable-background-timer-throttling','--disable-renderer-backgrounding']};
}

async function session(browser,entry,privateRoot) {
  validateEntry(entry);
  const files=entry.units.map(u=>u.files.map(f=>{
    const buffer=fs.readFileSync(safePath(privateRoot,f.relative_path));
    if(buffer.length!==f.bytes||hash(buffer)!==f.sha256) throw Error('Selected media hash/size mismatch');
    return buffer;
  }));
  const epoch=performance.now(), stamp=()=> (performance.now()-epoch)/1000;
  const transfers=[], reports=[], service=new FairService();
  const server=http.createServer((req,res)=>{
    const match=/^\/media\/(\d+)\/(0|1)$/.exec(req.url);
    if(req.url==='/') {res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><title>Playback timing</title><video id="a" width="480" height="240" playsinline muted></video><video id="b" width="480" height="240" playsinline muted></video><script src="/player.js"></script>');return;}
    if(req.url==='/player.js') {res.setHeader('Content-Type','application/javascript');res.end(fs.readFileSync(path.join(root,'player_timing/player.js')));return;}
    if(req.url==='/report'&&req.method==='POST') {
      let body='';req.on('data',chunk=>{body+=chunk;if(body.length>4096) req.destroy();});
      req.on('end',()=>{try {reports.push({serverAt:stamp(),...JSON.parse(body)});res.end('ok');}catch(_) {res.statusCode=400;res.end();}});return;
    }
    let data,id,extra=0;
    if(match) {const j=Number(match[1]),u=Number(match[2]);data=files[j]?.[u];id=`${j}:${u}`;
      if(entry.control==='late_recipient'&&j===0&&u===0) extra=40;}
    else if(req.url==='/background'&&entry.control==='background') {data=Buffer.alloc(6000000);id='background';}
    if(!data) {res.statusCode=404;res.end();return;}
    if(transfers.some(t=>t.id===id)) {res.statusCode=409;res.end();return;}
    const row={id,request:stamp(),bytes:data.length,completed:null,connectionClosed:false};
    row.eligible=row.request+.13+extra;transfers.push(row);
    res.setHeader('Content-Type',id==='background'?'application/octet-stream':'video/mp4');
    res.setHeader('Content-Length',data.length);res.setHeader('Cache-Control','no-store');res.flushHeaders();
    res.on('close',()=>{row.connectionClosed=true;row.closeAt=stamp();});
    service.add(id,data,row.eligible,b=>res.write(b),()=>{row.completed=stamp();res.end();});
  });
  let context=null,timer=null,watchdog=null,result=null,error=null;const mediaProperties=[],errors=[];
  try {
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    timer=setInterval(()=>service.step(stamp()),10);
    context=await browser.newContext({viewport:{width:1024,height:600}});const page=await context.newPage();
    const cdp=await context.newCDPSession(page);cdp.on('Media.playerPropertiesChanged',e=>mediaProperties.push(e));await cdp.send('Media.enable');
    page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    const config={units:entry.units,unit_seconds:entry.unit_seconds,buffered:entry.buffered,control:entry.control};
    try {
      result=await Promise.race([page.evaluate(c=>window.runStudy(c),config),
        new Promise((resolve,reject)=>{watchdog=setTimeout(()=>reject(Error('150-second session watchdog')),150000);})]);
    } catch(e) {error=String(e);try {result=await page.evaluate(()=>window.snapshotStudy?.()??null);}catch(_) {}}
  } catch(e) {error=String(e);}
  finally {
    clearTimeout(watchdog);if(context) await context.close();clearInterval(timer);
    if(server.listening) {server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
  }
  return {index:entry.index,case_id:entry.case_id,repetition:entry.repetition,key:entry.key,policy:entry.policy,
    unit_seconds:entry.unit_seconds,buffered:entry.buffered,control:entry.control,
    status:error?'failed':result?.status??'failed',error,browser:result,pageErrors:errors,mediaProperties,
    server:{clock:'separate server performance seconds',transfers,reports,batches:service.batches,finished:stamp()},
    browserVersion:browser.version()};
}

function requireNewOutsideRepo(output,privateRoot) {
  const target=path.resolve(output);const roots=[root,path.resolve(privateRoot)];
  if(fs.existsSync(target)||roots.some(r=>target===r||target.startsWith(r+path.sep))) throw Error('New private output outside repository and source root required');
  const parent=fs.realpathSync(path.dirname(target));
  if(roots.some(r=>parent===r||parent.startsWith(r+path.sep))) throw Error('Output ancestor inside repository/source');
  return target;
}

async function main() {
  const args=process.argv.slice(2);const option=n=>{const i=args.indexOf(n);return i<0?null:args[i+1];};
  const modulePath=process.env.PLAYWRIGHT_MODULE,browserPath=process.env.PLAYER_BROWSER;
  if(!modulePath||!browserPath) throw Error('Explicit isolated browser and Playwright module required');
  const current=runtime(browserPath,modulePath);
  if(option('--runtime-output')) {save(option('--runtime-output'),current);console.log(JSON.stringify(current));return;}
  const activate=option('--activate'),privateRoot=option('--private'),outputArg=option('--output');
  if(!activate||!privateRoot||!outputArg||!process.env.WU_PYTHON) throw Error('Explicit activation, media root, new output and Python required');
  const output=requireNewOutsideRepo(outputArg,privateRoot);
  const frozen=JSON.parse(fs.readFileSync(path.join(__dirname,'registration.json')));
  if(JSON.stringify(current)!==JSON.stringify(frozen.runtime)) {
    // Python's canonical serialization sorts keys; compare each semantic object.
    const canonical=x=>JSON.stringify(x, function(k,v){return v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v;});
    if(canonical(current)!==canonical(frozen.runtime)) throw Error('Pinned browser/runtime changed');
  }
  const checked=spawnSync(process.env.WU_PYTHON,['-m','wu_playback.preflight','--private',privateRoot,'--activate',activate],{cwd:root,encoding:'utf8',windowsHide:true});
  if(checked.status!==0) throw Error('Read-only method/media preflight failed');
  const preflight=JSON.parse(checked.stdout.trim());
  const deliveryPath=path.join(__dirname,'results/plan_v1/delivery.json'),delivery=JSON.parse(fs.readFileSync(deliveryPath));
  for(const e of delivery) validateEntry(e);
  fs.mkdirSync(output);save(path.join(output,'metadata.json'),{registration_sha256:activate,delivery_sha256:hash(fs.readFileSync(deliveryPath)),runtime:current,preflight,
    planned_indices:delivery.map(e=>e.index),automatic_retries:0,clock:'first recovery request on browser clock',no_personal_profile:true});
  const completion=[];let browser;
  try {
    browser=await require(modulePath).chromium.launch({executablePath:browserPath,headless:true,args:current.args});
    for(const entry of delivery) {
      let row;try {row=await session(browser,entry,privateRoot);}catch(e) {row={index:entry.index,case_id:entry.case_id,repetition:entry.repetition,control:entry.control,status:'failed',error:String(e)};}
      fs.writeFileSync(path.join(output,`session_${String(entry.index).padStart(3,'0')}.json.gz`),zlib.gzipSync(JSON.stringify(row)),{flag:'wx'});
      completion.push({index:entry.index,status:row.status,error:row.error});
      save(path.join(output,`checkpoint_${String(entry.index).padStart(3,'0')}.json`),completion);
      console.log(JSON.stringify({index:entry.index,clip:entry.clip,policy:entry.policy,unit:entry.unit_seconds,buffered:entry.buffered,control:entry.control,status:row.status}),null,0);
      await delay(250);
    }
    save(path.join(output,'completion.json'),completion);
  } catch(e) {save(path.join(output,'failure.json'),{status:'failed_incomplete',completed_indices:completion.map(e=>e.index),error:String(e),automatic_retry:false});throw e;}
  finally {if(browser) await browser.close();}
}
if(require.main===module) main().catch(e=>{console.error(String(e));process.exitCode=1;});
module.exports={session,safePath,validateEntry,requireNewOutsideRepo,runtime,hash};
