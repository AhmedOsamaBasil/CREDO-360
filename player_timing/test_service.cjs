const assert=require('node:assert/strict');const {FairService}=require('./service.cjs');
function transfer(s,id,n,t) {let got=0,done=false;s.add(id,Buffer.alloc(n),t,b=>got+=b.length,()=>done=true);return ()=>({got,done});}
const s=new FairService(1000);const a=transfer(s,'a',100,0),b=transfer(s,'b',200,0);
for(let i=0;i<=40;i++) s.step(i/100);
assert.deepEqual(a(),{got:100,done:true});assert.deepEqual(b(),{got:200,done:true});
assert.equal(s.batches.reduce((n,b)=>n+Object.values(b.sent).reduce((a,c)=>a+c,0),0),300);
for(const batch of s.batches) assert.ok(Object.values(batch.sent).reduce((a,b)=>a+b,0)<=batch.budget);
const delayed=new FairService(1000);const c=transfer(delayed,'c',10,10);delayed.step(0);delayed.step(9);assert.equal(c().got,0);delayed.step(10);assert.equal(c().got,0);delayed.step(10.01);assert.ok(c().got<=10);
const slow=new FairService(1000);const d=transfer(slow,'d',1000,0);slow.step(0);slow.step(5);assert.ok(d().got<=20);
assert.throws(()=>slow.step(4));assert.throws(()=>new FairService(0));
console.log('Service tests PASS: shared bytes, fairness completion, no idle credit, capped catch-up, invalid clocks');
