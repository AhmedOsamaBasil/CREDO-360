"""Playback queue with delayed selected-rung feedback and finite media endpoint."""
import numpy as np
from live_testbed.playback_clock import advance_round,advance_idle


class State:
    def __init__(self,record):
        self.loss=record.loss
        self.observations=[(t,u,0 if u==0 else 2,record.quality[t][u][0 if u==0 else 2])
                           for t in (0,1) for u in (0,1)]
        self.initial_history=tuple(tuple(record.quality[t][u][0 if u==0 else 2] for u in (0,1)) for t in (0,1))
        self.buffer=np.zeros(2); self.stall=np.zeros(2); self.finish=np.zeros(2)
        self.time=0.; self.spent=0; self.items=[]; self.credit=0

    def release(self,now):
        released=[]
        for item in self.items:
            for u in (0,1):
                if not item['reported'][u] and item['play_end'][u]<=now:
                    item['reported'][u]=True
                    q=item['actual_quality'][u]
                    self.observations.append((item['segment'],u,item['rungs'][u],q))
                    if u==0: self.credit+=min(self.loss-self.credit,max(q-item['reference'][u],0))
                    released.append({'segment':item['segment'],'user':u,'quality':q,
                                     'play_end':item['play_end'][u],'released_at':now})
        return released

    def idle(self,now):
        if now<self.time-1e-9: raise ValueError('clock moved backwards')
        r=advance_idle(self.buffer,max(0,now-self.time))
        self.buffer=r.buffer_s; self.stall+=r.stall_s; self.time=now
        return r.stall_s.tolist()

    def view(self,now):
        released=self.release(now)
        history=list(self.initial_history); pending=[]
        for item in self.items:
            history.append(tuple(item['actual_quality'][u] if item['reported'][u] else item['predicted_quality'][u] for u in (0,1)))
            if not item['reported'][0]: pending.append(item['predicted_gain'])
        return {'observations':tuple(sorted(self.observations)),'observed_credit':self.credit,
                'pending_gains':tuple(pending),'history':tuple(history)},released

    def deliver(self,record,segment,decision,arrivals,end):
        if any(x<self.time or x>end for x in arrivals): raise ValueError('invalid delivery timestamps')
        q=tuple(record.quality[segment][u][decision['rungs'][u]] for u in (0,1))
        ref=tuple(record.quality[segment][u][2] for u in (0,1))
        finishes=np.maximum(self.finish,np.asarray(arrivals))+10
        before=self.buffer.copy(); prior_stall=self.stall.copy(); begin=self.time
        used_ends=[]
        for u in (0,1):
            # No stall after the final media item has finished playing.
            stop=min(end,float(finishes[u])) if segment==5 else end
            step=advance_round(self.buffer[u:u+1],np.array([arrivals[u]-begin]),stop-begin)
            self.buffer[u]=step.buffer_s[0]; self.stall[u]+=step.stall_s[0]; used_ends.append(stop)
            assert abs(before[u]+10+step.stall_s[0]-(stop-begin)-self.buffer[u])<1e-8
        item={'segment':segment,'rungs':decision['rungs'],'predicted_quality':decision['predicted_quality'],
              'predicted_gain':decision['predicted_gain'],'actual_quality':q,'reference':ref,
              'arrivals':tuple(arrivals),'play_end':tuple(float(x) for x in finishes),'reported':[False,False]}
        self.items.append(item); self.finish=finishes; self.time=end; self.spent+=decision['extra_bytes']
        return {'buffer_before':before.tolist(),'buffer_after':self.buffer.tolist(),
                'stall_increment':(self.stall-prior_stall).tolist(),'stall_total':self.stall.tolist(),
                'play_end':item['play_end'],'actual_quality':q,'reference':ref,'accounted_end':used_ends}

    def final(self):
        if len(self.items)!=4: raise ValueError('four recovery segments required')
        self.release(float(max(self.finish)))
        for u in (0,1): assert abs(40+self.stall[u]-self.finish[u])<1e-7
        means=[sum(x['actual_quality'][u] for x in self.items)/4000 for u in (0,1)]
        return {'remaining_units':self.loss-self.credit,'unpaid_fraction':(self.loss-self.credit)/self.loss,
            'half_repaid':2*(self.loss-self.credit)<=self.loss,'extra_bytes':self.spent,
            'worst_quality':min(means),'mean_quality':sum(means)/2,
            'stall_seconds':self.stall.tolist(),'mean_stall_seconds':float(self.stall.mean()),
            'media_finish_seconds':self.finish.tolist(),'final_tail_mode':'analytic drain; no display/decoder',
            'donor_floor_violations':sum(x['actual_quality'][1]<x['reference'][1] for x in self.items),
            'recipient_floor_violations':sum(x['actual_quality'][0]<x['reference'][0] for x in self.items),
            'donor_loss_units':sum(max(0,x['reference'][1]-x['actual_quality'][1]) for x in self.items),
            'current_mae':sum(abs(x['actual_quality'][u]-x['predicted_quality'][u]) for x in self.items for u in (0,1))/8000}
