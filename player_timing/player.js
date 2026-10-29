/* Browser measurement events share one performance clock, not server time. */
window.runStudy = async function(config) {
  const epoch=performance.now(); const now=()=>performance.now()-epoch;
  const sleep=ms=>new Promise(r=>setTimeout(r,Math.max(0,ms)));
  const videos=[document.querySelector('#a'),document.querySelector('#b')];
  const events=[];const frames=[[],[]];const segments=[[],[]];const receipts=[];
  window.snapshotStudy=()=>({status:'censored',epoch,events,frames,segments,receipts,finished:now()});
  const log=(type,extra={})=>{const e={type,at:now(),...extra};events.push(e);return e.at;};
  const slots=config.units.map(()=>[{},{}]);
  for(const pair of slots) for(const slot of pair) slot.promise=new Promise((r,j)=>{slot.resolve=r;slot.reject=j;});
  let error=null;
  const fetchOne=async(j,u)=>{
    const request=log('request',{j,u});
    const response=await fetch(`/media/${j}/${u}`,{cache:'no-store'});
    if(!response.ok) throw Error(`HTTP ${response.status}`);
    const headers=log('response_headers',{j,u});
    const data=await response.arrayBuffer(); const receipt=log('receipt',{j,u,bytes:data.byteLength});
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),b=>b.toString(16).padStart(2,'0')).join('');
    if(digest!==config.units[j].files[u].sha256 || data.byteLength!==config.units[j].files[u].bytes) throw Error('Receipt identity');
    const ready=log('verified_receipt',{j,u});
    receipts.push({j,u,request,headers,receipt,ready,bytes:data.byteLength,sha256:digest});
    slots[j][u].resolve(new Blob([data],{type:'video/mp4'}));
  };
  const downloader=(async()=>{
    for(let j=0;j<config.units.length;j++) {
      const start=performance.now();await Promise.all([fetchOne(j,0),fetchOne(j,1)]);
      if(j+1<config.units.length) await sleep(config.unit_seconds*1000-(performance.now()-start));
    }
  })();
  // No quality labels or future viewport samples are sent to this player.
  const background=config.control==='background' ? (async()=>{
    log('background_request');const response=await fetch('/background');
    const bytes=(await response.arrayBuffer()).byteLength;log('background_receipt',{bytes});
  })() : Promise.resolve();
  let gate=Promise.resolve();
  if(config.buffered) {
    let duration=0,n=0;
    while(duration<4-1e-9) {duration+=config.units[n].duration;n++;}
    gate=Promise.all(slots.slice(0,n).flat().map(s=>s.promise));
  }
  const play=async(u)=>{
    await gate;const gateTime=log('buffer_gate',{u});
    const video=videos[u];video.muted=true;video.playbackRate=1;
    for(let j=0;j<slots.length;j++) {
      const blob=await slots[j][u].promise;const url=URL.createObjectURL(blob);
      let handle=null;const localFrames=[];const state={j,u,gateTime};
      const mediaEvents=[];
      const listeners=['loadedmetadata','loadeddata','canplay','playing','waiting','stalled','suspend','error'].map(type=>{
        const fn=()=>mediaEvents.push({type,at:now(),currentTime:video.currentTime,
          readyState:video.readyState,code:video.error?.code??null});
        video.addEventListener(type,fn);return [type,fn];
      });
      const callback=(at,meta)=>{
        const frame={j,u,at:at-epoch,mediaTime:meta.mediaTime,
          presentationTime:meta.presentationTime-epoch,expectedDisplayTime:meta.expectedDisplayTime-epoch,
          presentedFrames:meta.presentedFrames,processingDuration:meta.processingDuration??null,
          width:meta.width,height:meta.height};
        frames[u].push(frame);localFrames.push(frame);handle=video.requestVideoFrameCallback(callback);
      };
      const ended=new Promise((resolve,reject)=>{
        video.addEventListener('ended',()=>resolve(log('ended',{j,u,currentTime:video.currentTime})),{once:true});
        video.addEventListener('error',()=>reject(Error(`Video error ${video.error?.code}`)),{once:true});
      });
      state.load=log('load',{j,u});video.src=url;video.load();
      handle=video.requestVideoFrameCallback(callback);
      state.playRequest=log('play_request',{j,u});await video.play();
      state.playResolved=log('play_resolved',{j,u});state.ended=await ended;
      if(handle!==null) video.cancelVideoFrameCallback(handle);
      state.duration=video.duration;state.currentTime=video.currentTime;
      state.playbackQuality=video.getVideoPlaybackQuality?.()??null;
      if(state.playbackQuality) state.playbackQuality={totalVideoFrames:state.playbackQuality.totalVideoFrames,
        droppedVideoFrames:state.playbackQuality.droppedVideoFrames,corruptedVideoFrames:state.playbackQuality.corruptedVideoFrames};
      state.frameCount=localFrames.length;state.mediaEvents=mediaEvents;
      await sleep(0);state.reportReady=log('report_ready',{j,u});
      const response=await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({j,u,ended:state.ended,reportReady:state.reportReady})});
      if(!response.ok) throw Error('Report acknowledgement');
      state.reportAck=log('report_ack',{j,u});segments[u].push(state);
      for(const [type,fn] of listeners) video.removeEventListener(type,fn);
      URL.revokeObjectURL(url);
    }
  };
  try {await Promise.all([downloader,play(0),play(1),background]);}
  catch(e) {error=String(e);}
  return {status:error?'failed':'completed',error,epoch,clock:'browser performance milliseconds',
    userAgent:navigator.userAgent,events,frames,segments,receipts,finished:now()};
};
