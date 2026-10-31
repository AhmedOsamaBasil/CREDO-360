const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {safePath,validateEntry,requireNewOutsideRepo}=require('./measure.cjs');
const file={relative_path:'a.mp4',sha256:'a'.repeat(64),bytes:100,duration:10,frames:300};
const entry={index:0,case_id:'synthetic',repetition:0,control:'none',clip:'synthetic',key:'a:b',policy:'cost_greedy',unit_seconds:10,buffered:false,
  units:Array.from({length:4},(_,parent)=>({parent,child:0,duration:10,files:[file,file]}))};
validateEntry(entry);
assert.throws(()=>validateEntry({...entry,loss:123}));
assert.throws(()=>validateEntry({...entry,units:entry.units.slice(1)}));
assert.throws(()=>validateEntry({...entry,control:'unregistered'}));
const changed=structuredClone(entry);changed.units[0].files[0].quality=55;assert.throws(()=>validateEntry(changed));
const wrong=structuredClone(entry);wrong.units[2].parent=0;assert.throws(()=>validateEntry(wrong));
const wrongFile=structuredClone(entry);wrongFile.units[0].files[0].bytes=0;assert.throws(()=>validateEntry(wrongFile));
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'wu-playback-unit-'));
try {
  fs.writeFileSync(path.join(tmp,'a.mp4'),'test');
  assert.equal(safePath(tmp,'a.mp4'),fs.realpathSync(path.join(tmp,'a.mp4')));
  for(const name of ['../a.mp4','/a.mp4','C:/a.mp4','a\\b.mp4','']) assert.throws(()=>safePath(tmp,name));
  assert.throws(()=>requireNewOutsideRepo(tmp,tmp));
  assert.throws(()=>requireNewOutsideRepo(path.join(tmp,'child'),tmp));
  assert.throws(()=>requireNewOutsideRepo(path.resolve(__dirname,'new'),tmp));
} finally {fs.unlinkSync(path.join(tmp,'a.mp4'));fs.rmdirSync(tmp);}
console.log('Runner guards PASS: delivery allowlist, complete units, byte identity, path confinement, no source/repository output');
