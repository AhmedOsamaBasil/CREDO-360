"""Playback-clock replay; prefix predictions are separate from actual scoring."""
from causal_playback.replay import reserve
from feedback_opportunity.controller import FeedbackState
from early_commitment.core import decision,visible_index,wait_time,transfer_offsets


def simulate(record,policy,feedback,forecasts,delay=.08):
    state=FeedbackState(record,feedback); rounds=[]
    keys=tuple(f'{record.cohort}:{record.scene}:{sid}' for sid in (record.recipient,record.donor))
    for t in range(2,6):
        prior=state.time; remaining=reserve(record)-state.spent
        start=wait_time(policy,state.items,prior,record.costs[t],remaining,delay)
        idle=state.idle(start); _,released=state.view(start-delay)
        partial=policy.startswith('prefix_')
        indices=tuple(visible_index(state.items,u,start,delay,partial) for u in (0,1))
        quality=tuple(tuple(tuple(forecasts[keys[u]][indices[u]][s]) for u in (0,1)) for s in range(6))
        history=list(state.initial_history); pending=[]
        for item in state.items:
            q=tuple(quality[item['segment']][u][item['rungs'][u]] for u in (0,1))
            history.append(q)
            if not item['reported'][0]:
                pending.append(max(0,q[0]-quality[item['segment']][0][2]))
        action=decision(policy,quality,record.costs,t,state.loss,state.credit,pending,history,remaining)
        sizes=tuple(record.costs[t][j] for j in action['rungs'])
        arrivals=tuple(start+x for x in transfer_offsets(sizes)); end=max(start+10,max(arrivals))
        metrics=state.deliver(record,t,action,arrivals,end)
        rounds.append({'segment':t,'prior_boundary':prior,'start':start,'wait_seconds':start-prior,
                       'idle_stall':idle,'visible_indices':indices,'released':released,'predicted_menus':quality[t:],
                       'history':history,'pending_gains':pending,'decision':action,'file_bytes':sizes,
                       'arrivals':arrivals,'end':end,**metrics})
    score=state.final_score(record)
    score['current_mae']=sum(abs(r['actual_quality'][u]-r['decision']['predicted_quality'][u]) for r in rounds for u in (0,1))/8000
    score['wait_seconds']=sum(r['wait_seconds'] for r in rounds)
    score['startup_seconds']=sum(rounds[0]['arrivals'])/2
    return {'key':record.key,'cohort':record.cohort,'scene':record.scene,'policy':policy,'delay':delay,
            'original_loss_units':record.loss,'reserve_bytes':reserve(record),'rounds':rounds,**score}
