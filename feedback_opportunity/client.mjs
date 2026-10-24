// Renderer adapter: only orientation and presentation-clock events enter here.
export function viewportMask(yaw, pitch) {
  if (!Number.isFinite(yaw) || !Number.isFinite(pitch) || pitch < -90 || pitch > 90)
    throw new Error('finite renderer yaw/pitch in degrees required');
  let bits = 0n;
  for (let row = 0; row < 6; row++) for (let col = 0; col < 12; col++) {
    const dy = Math.abs((((-165 + 30 * col - yaw + 180) % 360) + 360) % 360 - 180);
    if (dy <= 50 && Math.abs(75 - 30 * row - pitch) <= 50)
      bits |= 1n << BigInt(row * 12 + col);
  }
  if (bits === 0n) throw new Error('empty viewport');
  const out = new Uint8Array(9);
  for (let i = 8; i >= 0; i--) { out[i] = Number(bits & 255n); bits >>= 8n; }
  return out;
}

export class SegmentFeedback {
  constructor(descriptor, segment, rung, sequence) {
    if (!/^[0-9a-f]{64}$/.test(descriptor) || !Number.isInteger(segment) || segment < 0 || segment > 5 ||
        !Number.isInteger(rung) || rung < 0 || rung > 5 || !Number.isInteger(sequence) || sequence < 0 || sequence > 0xffffffff)
      throw new Error('invalid descriptor/segment/rung/sequence');
    Object.assign(this, { descriptor, segment, rung, sequence }); this.masks = []; this.closed = false;
  }
  sample(mediaTime, poseTime, yaw, pitch) {
    const target = this.segment * 10 + this.masks.length + 0.5;
    if (this.closed || this.masks.length >= 10 || !Number.isFinite(mediaTime) || !Number.isFinite(poseTime) ||
        Math.abs(mediaTime - target) > 1e-6 || poseTime > mediaTime || mediaTime - poseTime > .1)
      throw new Error('missing, future, stale or misordered pose sample');
    this.masks.push(viewportMask(yaw, pitch));
  }
  observe(mediaTime, yaw, pitch) {
    // Called from renderer presentation events. Resample only the stored past
    // pose when an event crosses a half-second target; never use a future pose.
    viewportMask(yaw, pitch);
    if (!Number.isFinite(mediaTime) || this.closed || mediaTime < this.segment*10 ||
        (this.lastPose && mediaTime < this.lastPose.time)) throw new Error('invalid presentation clock');
    while (this.masks.length < 10 && this.segment*10+this.masks.length+.5 <= mediaTime) {
      const target = this.segment*10+this.masks.length+.5;
      const pose = mediaTime === target ? {time:mediaTime,yaw,pitch} : this.lastPose;
      if (!pose) throw new Error('missing pose history');
      this.sample(target,pose.time,pose.yaw,pose.pitch);
    }
    this.lastPose = {time:mediaTime,yaw,pitch};
  }
  finish(mediaTime) {
    if (this.closed || this.masks.length !== 10 || !Number.isFinite(mediaTime) || mediaTime < (this.segment + 1) * 10)
      throw new Error('incomplete or premature feedback');
    const out = new Uint8Array(140), view = new DataView(out.buffer);
    out.set([86,81,70,49], 0);
    out.set(this.descriptor.match(/../g).map(x => parseInt(x, 16)), 4);
    view.setUint8(36, this.segment); view.setUint8(37, this.rung);
    view.setUint32(38, this.sequence); view.setFloat64(42, mediaTime);
    this.masks.forEach((m,i) => out.set(m, 50 + 9*i)); this.closed = true;
    return out;
  }
}

// Offline adapter exerciser. Input pose events and output packets stay local.
if (typeof process !== 'undefined' && process.argv[1] && import.meta.url.endsWith('/client.mjs') &&
    process.argv[1].replaceAll('\\','/').endsWith('/client.mjs')) {
  const fs = await import('node:fs');
  const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const output = input.map(r => {
    const c = new SegmentFeedback(r.descriptor,r.segment,r.rung,r.sequence);
    for (const e of r.events) c.sample(e.mediaTime,e.poseTime,e.yaw,e.pitch);
    return { key:r.key, packet:Buffer.from(c.finish(r.mediaEnd)).toString('base64') };
  });
  fs.writeFileSync(process.argv[3],JSON.stringify(output),{flag:'wx'});
}
