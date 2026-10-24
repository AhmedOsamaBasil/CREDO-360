"""Frozen policies with feedback-derived ledgers; labels used only for scoring."""
import numpy as np
from causal_playback.clock import State
from causal_playback.core import decide
from causal_playback.replay import reserve


class FeedbackState(State):
    def __init__(self,record,feedback):
        super().__init__(record)
        self.feedback=feedback
        self.ids=(record.recipient,record.donor)
        self.scene=record.scene; self.cohort=record.cohort
        self.loss=sum(max(0,self.values(t,0)[2]-self.values(t,0)[0]) for t in (0,1))
        self.observations=[(t,u,0 if u==0 else 2,self.values(t,u)[0 if u==0 else 2]) for t in (0,1) for u in (0,1)]
        self.initial_history=tuple(tuple(self.values(t,u)[0 if u==0 else 2] for u in (0,1)) for t in (0,1))

    def values(self,t,u): return self.feedback[self.cohort,self.scene,self.ids[u],t]

    def release(self,now):
        released=[]
        for item in self.items:
            for u in (0,1):
                if not item['reported'][u] and item['play_end'][u]<=now:
                    item['reported'][u]=True
                    q=self.values(item['segment'],u); selected=q[item['rungs'][u]]
                    self.observations.append((item['segment'],u,item['rungs'][u],selected))
                    if u==0: self.credit+=min(self.loss-self.credit,max(0,selected-q[2]))
                    released.append({'segment':item['segment'],'user':u,'quality':selected,
                                     'reference_quality':q[2],'play_end':item['play_end'][u],'released_at':now})
        return released

    def view(self,now):
        released=self.release(now); history=list(self.initial_history); pending=[]
        for item in self.items:
            history.append(tuple(self.values(item['segment'],u)[item['rungs'][u]] if item['reported'][u]
                                 else item['predicted_quality'][u] for u in (0,1)))
            if not item['reported'][0]: pending.append(item['predicted_gain'])
        return {'observations':tuple(sorted(self.observations)),'observed_credit':self.credit,
                'pending_gains':tuple(pending),'history':tuple(history)},released

    def final_score(self,record):
        self.release(float(max(self.finish)))
        for u in (0,1): assert abs(40+self.stall[u]-self.finish[u])<1e-7
        credit=min(record.loss,sum(max(0,x['actual_quality'][0]-x['reference'][0]) for x in self.items))
        means=[sum(x['actual_quality'][u] for x in self.items)/4000 for u in (0,1)]
        return {'remaining_units':record.loss-credit,'unpaid_fraction':(record.loss-credit)/record.loss,
            'half_repaid':2*credit>=record.loss,'extra_bytes':self.spent,
            'worst_quality':min(means),'mean_quality':sum(means)/2,
            'stall_seconds':self.stall.tolist(),'mean_stall_seconds':float(self.stall.mean()),
            'media_finish_seconds':self.finish.tolist(),'estimated_loss_units':self.loss,
            'estimated_credit_units':self.credit,'actual_credit_units':credit,
            'donor_floor_violations':sum(x['actual_quality'][1]<x['reference'][1] for x in self.items),
            'recipient_floor_violations':sum(x['actual_quality'][0]<x['reference'][0] for x in self.items)}


def simulate(record,training,policy,feedback):
    state=FeedbackState(record,feedback); rounds=[]
    for t in range(2,6):
        start=state.time; idle=state.idle(start); view,released=state.view(start)
        decision=decide(policy,state.loss,**view,sender=record.sender,costs=record.costs,t=t,
                        training=training,reserve=reserve(record)-state.spent)
        n=tuple(record.costs[t][r] for r in decision['rungs'])
        arrivals=tuple(start+.05+.08+(2*x if x==min(n) else sum(n))*8/1_200_000 for x in n)
        end=max(start+10,max(arrivals)); metrics=state.deliver(record,t,decision,arrivals,end)
        rounds.append({'segment':t,'start':start,'view':view,'feedback_released':released,'idle_stall':idle,
                       'decision':decision,'file_bytes':n,'arrivals':arrivals,'end':end,**metrics})
    return {'key':record.key,'scene':record.scene,'cohort':record.cohort,'policy':policy,
            'reserve_bytes':reserve(record),'original_loss_units':record.loss,'rounds':rounds,**state.final_score(record)}
