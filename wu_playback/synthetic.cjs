/* Reuse the published generated-pattern media only; never open Wu sources. */
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {session,runtime,hash}=require('./measure.cjs');
const root=path.resolve(__dirname,'..');
async function main() {
  const args=process.argv.slice(2);const arg=n=>args[args.indexOf(n)+1];
  if(!args.includes('--private')||!args.includes('--output')) throw Error('Explicit generated media and new output required');
  const privateRoot=arg('--private'), output=arg('--output');if(fs.existsSync(output)) throw Error('Preserve earlier smoke');
  const report=JSON.parse(fs.readFileSync(path.join(root,'wu_pipeline/results/synthetic_v1/report.json')));
  if(!report.synthetic_only||report.wu_media_accessed) throw Error('Generated-only source required');
  const cases=[];
  for(const seconds of [10,2]) for(const buffered of [false,true]) {
    const entries=seconds===10?[report.parent]:report.children;
    // Repetition here constructs a generated 40s recovery fixture, not source-video data.
    const units=[];
    for(let parent=0;parent<4;parent++) for(let child=0;child<entries.length;child++) {
      const f=entries[child];const file={relative_path:f.relative_path,sha256:f.sha256,bytes:f.bytes,frames:f.frames,duration:seconds};
      units.push({parent,child,duration:seconds,files:[file,file]});
    }
    cases.push({index:cases.length,case_id:`synthetic:${seconds}:${buffered}`,repetition:0,control:'none',
      clip:'generated_only',key:'generated_only:a:b',policy:'cost_greedy',unit_seconds:seconds,buffered,units});
  }
  const current=runtime(process.env.PLAYER_BROWSER,process.env.PLAYWRIGHT_MODULE);
  fs.mkdirSync(output);fs.writeFileSync(path.join(output,'metadata.json'),JSON.stringify({synthetic_only:true,wu_media_accessed:false,runtime:current,
    source_report_sha256:hash(fs.readFileSync(path.join(root,'wu_pipeline/results/synthetic_v1/report.json'))),cases}),{flag:'wx'});
  const browser=await require(process.env.PLAYWRIGHT_MODULE).chromium.launch({executablePath:process.env.PLAYER_BROWSER,headless:true,args:current.args});
  try {
    for(const c of cases) {
      const row=await session(browser,c,privateRoot);
      fs.writeFileSync(path.join(output,`session_${c.index}.json.gz`),zlib.gzipSync(JSON.stringify(row)),{flag:'wx'});
      console.log(JSON.stringify({index:c.index,status:row.status,error:row.error}));
      if(row.status!=='completed') throw Error('Synthetic compatibility failure retained; no retry');
    }
  } finally {await browser.close();}
}
if(require.main===module) main().catch(e=>{console.error(String(e));process.exitCode=1;});
