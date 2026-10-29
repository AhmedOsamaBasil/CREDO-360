/* Isolated headless-browser sessions with controlled loopback delivery. */
const fs=require('node:fs');const path=require('node:path');const http=require('node:http');
const crypto=require('node:crypto');const zlib=require('node:zlib');const {performance}=require('node:perf_hooks');
const {FairService}=require('./service.cjs');
const root=path.resolve(__dirname,'..');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const delay=ms=>new Promise(r=>setTimeout(r,ms));

async function session(browser,entry) {
  const files=entry.units.map(unit=>unit.files.map(f=>{
    const base=f.cache==='split'?'.external/player_timing_v1':'.external/causal_playback_v1';
    const p=path.resolve(root,base,f.relative_path);const buffer=fs.readFileSync(p);
    if(hash(buffer)!==f.sha256 || buffer.length!==f.bytes) throw Error('Media preflight mismatch');
    return buffer;
  }));
  const epoch=performance.now();const stamp=()=> (performance.now()-epoch)/1000;
  const transfers=[];const reports=[];const service=new FairService();
  const server=http.createServer((req,res)=>{
    const match=/^\/media\/(\d+)\/(0|1)$/.exec(req.url);
    if(req.url==='/') {res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><title>Video timing study</title><video id="a" width="480" height="240" playsinline muted></video><video id="b" width="480" height="240" playsinline muted></video><script src="/player.js"></script>');return;}
    if(req.url==='/player.js') {res.setHeader('Content-Type','application/javascript');res.end(fs.readFileSync(path.join(__dirname,'player.js')));return;}
    if(req.url==='/report' && req.method==='POST') {
      let body='';req.on('data',c=>body+=c);req.on('end',()=>{reports.push({serverAt:stamp(),...JSON.parse(body)});res.end('ok');});return;
    }
    let data,id,extra=0;
    if(match) {const j=Number(match[1]),u=Number(match[2]);data=files[j]?.[u];id=`${j}:${u}`;
      if(entry.control==='late_recipient' && u===0 && j===0) extra=40;}
    else if(req.url==='/background' && entry.control==='background') {data=Buffer.alloc(6000000);id='background';}
    if(!data) {res.statusCode=404;res.end();return;}
    const row={id,request:stamp(),bytes:data.length,completed:null,connectionClosed:false};transfers.push(row);
    row.eligible=row.request+.13+extra;
    res.setHeader('Content-Type',id==='background'?'application/octet-stream':'video/mp4');
    res.setHeader('Content-Length',data.length);res.setHeader('Cache-Control','no-store');
    res.flushHeaders();res.on('close',()=>{row.connectionClosed=true;row.closeAt=stamp();});
    service.add(id,data,row.eligible,b=>res.write(b),()=>{row.completed=stamp();res.end();});
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const timer=setInterval(()=>service.step(stamp()),10);
  const context=await browser.newContext({viewport:{width:1024,height:600}});const page=await context.newPage();
  const mediaProperties=[];const cdp=await context.newCDPSession(page);
  cdp.on('Media.playerPropertiesChanged',e=>mediaProperties.push(e));await cdp.send('Media.enable');
  let result=null,error=null;const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  let watchdog;
  try {
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    const config={units:entry.units,unit_seconds:entry.unit_seconds,buffered:entry.buffered,control:entry.control};
    result=await Promise.race([page.evaluate(c=>window.runStudy(c),config),
      new Promise((r,j)=>{watchdog=setTimeout(()=>j(Error('150-second session watchdog')),150000);})]);
  } catch(e) {error=String(e);try {result=await page.evaluate(()=>window.snapshotStudy?.()??null);}catch(_) {}}
  finally {clearTimeout(watchdog);await context.close();clearInterval(timer);server.closeAllConnections();await new Promise(r=>server.close(r));}
  return {index:entry.index,key:entry.key,policy:entry.policy,unit_seconds:entry.unit_seconds,
    buffered:entry.buffered,control:entry.control,status:error?'failed':result.status,error,
    browser:result,pageErrors:errors,mediaProperties,server:{clock:'server performance seconds, separate epoch',
      transfers,reports,batches:service.batches,finished:stamp()},browserVersion:browser.version()};
}

async function main() {
  const playwright=require(process.env.PLAYWRIGHT_MODULE||'playwright');
  const schedulePath=path.join(root,'player_timing/results/replay_v1/schedule.json');
  let entries=JSON.parse(fs.readFileSync(schedulePath));
  const smoke=process.argv.includes('--smoke');
  if(smoke) entries=[{...entries[0],index:0,units:entries[0].units.slice(0,2),buffered:false}];
  const out=path.join(root,smoke?'work/player_smoke_v1':'player_timing/results/browser_v1');
  fs.mkdirSync(out,{recursive:false});
  const meta={schedule_sha256:hash(fs.readFileSync(schedulePath)),smoke,headless:true,
    method:JSON.parse(fs.readFileSync(path.join(root,'player_timing/results/replay_v1/metadata.json'))),
    node:process.version,playwrightVersion:require(path.join(process.env.PLAYWRIGHT_MODULE||'playwright','package.json')).version,
    browserExecutableSha256:hash(fs.readFileSync(process.env.PLAYER_BROWSER)),
    measuredSessionIndices:entries.map(e=>e.index)};
  fs.writeFileSync(path.join(out,'metadata.json'),JSON.stringify(meta,null,2));
  const browser=await playwright.chromium.launch({executablePath:process.env.PLAYER_BROWSER,headless:true,
    args:['--autoplay-policy=no-user-gesture-required','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
  const completion=[];
  try {
    for(const entry of entries) {
      let row;try {row=await session(browser,entry);}catch(e) {row={index:entry.index,status:'failed',error:String(e)};}
      fs.writeFileSync(path.join(out,`session_${String(entry.index).padStart(2,'0')}.json.gz`),zlib.gzipSync(JSON.stringify(row)));
      completion.push({index:entry.index,status:row.status,error:row.error});
      fs.writeFileSync(path.join(out,'completion.json'),JSON.stringify(completion,null,2));
      console.log(JSON.stringify({index:entry.index,key:entry.key,policy:entry.policy,unit:entry.unit_seconds,
        buffered:entry.buffered,control:entry.control,status:row.status,error:row.error}));
      await delay(250);
    }
  } finally {await browser.close();}
}
if(require.main===module) main().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={session};
