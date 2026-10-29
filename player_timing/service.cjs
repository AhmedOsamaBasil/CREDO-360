/* Equal-share finite-quantum application payload shaper, not a network link. */
class FairService {
  constructor(rate=150000, quantum=.02) {
    if (!(rate>0 && quantum>0)) throw Error('Invalid service');
    this.rate=rate; this.quantum=quantum; this.active=[]; this.batches=[];
    this.last=null; this.fraction=0;
  }
  add(id, payload, eligible, write, end) {
    if (!payload.length || this.active.some(x=>x.id===id)) throw Error('Invalid transfer');
    this.active.push({id,payload,eligible,write,end,offset:0});
  }
  step(now) {
    if(this.last===null) {this.last=now;return;}
    if(now<this.last) throw Error('Clock regression');
    const dt=Math.min(now-this.last,this.quantum); this.last=now;
    // Credit only time after eligibility, never idle capacity accumulated earlier.
    let ready=this.active.filter(x=>x.eligible<=now);
    if(!ready.length) {this.fraction=0;return;}
    const start=Math.max(now-dt,Math.min(...ready.map(x=>x.eligible)));
    const credit=this.rate*(now-start)+this.fraction;
    let budget=Math.floor(credit);this.fraction=credit-budget;
    const sent={};
    while(budget>0 && ready.length) {
      const share=Math.max(1,Math.floor(budget/ready.length));
      for(const x of ready) {
        if(budget===0) break;
        const n=Math.min(share,budget,x.payload.length-x.offset);
        x.write(x.payload.subarray(x.offset,x.offset+n)); x.offset+=n; budget-=n;
        sent[x.id]=(sent[x.id]||0)+n;
        if(x.offset===x.payload.length) x.end();
      }
      ready=ready.filter(x=>x.offset<x.payload.length);
    }
    this.active=this.active.filter(x=>x.offset<x.payload.length);
    if(Object.keys(sent).length) this.batches.push({at:now,interval_start:start,budget:Math.floor(credit),sent});
  }
}
module.exports={FairService};
