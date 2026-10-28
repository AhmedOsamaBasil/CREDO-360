"""Past-only entry API, spatial envelopes and finite admission witnesses."""
from decimal import Decimal, localcontext, ROUND_HALF_UP
from itertools import product
import numpy as np
from metric_contract.core import CAP, TICKS, SLOT, offsets
from duration_contract.core import DEADLINE

ETA = TICKS // 2


def spatial_bounds(maps):
    maps = np.asarray(maps, dtype=float)
    if maps.shape != (6,60,72) or not np.isfinite(maps).all() or (maps < 0).any() or (maps > 65025).any():
        raise ValueError("Finite nonnegative sender maps required")
    delta = maps[2:3] - maps
    lower = np.floor(delta.min(axis=2).reshape(6,6,10).mean(axis=2).T * 1e6).astype(np.int64) - 2
    upper = np.ceil(delta.max(axis=2).reshape(6,6,10).mean(axis=2).T * 1e6).astype(np.int64) + 2
    lower[:,2] = upper[:,2] = 0
    return lower, upper


def forecast(maps, past_reference_mse):
    past = np.asarray(past_reference_mse, dtype=float)
    if past.shape != (2,2) or not np.isfinite(past).all() or (past <= 0).any():
        raise ValueError("Two completed reference observations for each user required")
    area = np.repeat(np.cos(np.deg2rad(np.linspace(75,-75,6))),12)
    area /= area.sum()
    sphere = np.sum(np.asarray(maps,dtype=float) * area,axis=2).reshape(6,6,10).mean(axis=2).T
    if (sphere <= 0).any(): raise ValueError("Positive sender distortion required")
    scale = past.mean(axis=0) / (sphere[:2,2].mean()*1e6)
    return -np.floor(sphere[:,None,:]*scale[None,:,None]*1e6+.5).astype(np.int64)


def entry_inputs(record, durations):
    """Only past quality is projected out; never pass record to a planner."""
    q = record["quality"]
    loss = sum(max(0,int(q[3,t,0,2]-q[3,t,0,0]))*durations[t] for t in (0,1))
    return {"loss":loss, "past_reference_mse":(-q[3,:2,:,2]).tolist(),
            "past_psnr":[[int(q[2,t,0,0]),int(q[2,t,1,2])] for t in (0,1)]}


def clocks(costs, paths, durations, eta):
    if eta < 0: raise ValueError("Nonnegative execution allowance")
    n = len(paths); start=np.zeros(n,dtype=np.int64); finish=np.zeros((n,2),dtype=np.int64)
    ends=np.zeros((n,4,2),dtype=np.int64)
    for j,t in enumerate(range(2,6)):
        a,b=costs[t,paths[:,j,0]],costs[t,paths[:,j,1]]
        arrival=start[:,None]+19500+np.stack((np.minimum(2*a,a+b),np.minimum(2*b,a+b)),axis=1)
        finish=np.maximum(finish,arrival)+durations[t]+eta
        ends[:,j]=finish; start=np.maximum(start+SLOT,arrival.max(axis=1))
    return ends


def path_stats(delta, paths, ends, durations):
    if delta.shape == (6,6): delta=np.repeat(delta[:,None,:],2,axis=1)
    safe=np.ones(len(paths),dtype=bool); gain=np.zeros(len(paths),dtype=np.int64)
    for j,t in enumerate(range(2,6)):
        a,b=delta[t,0,paths[:,j,0]],delta[t,1,paths[:,j,1]]
        safe &= (a>=0)&(b>=0)
        gain += np.maximum(0,a)*durations[t]*(ends[:,j,0]<=DEADLINE)
    return safe,gain


def pick(gain, safe, costs, loss):
    ids=np.flatnonzero(safe & (2*gain>=loss)) if loss>0 else np.array([],dtype=int)
    if not len(ids): return None
    return int(min(ids,key=lambda i:(int(costs[i]),-int(gain[i]),int(i))))


def certificate(lower, upper, costs, arrays, durations, loss, eta=ETA):
    paths=arrays["choices"]
    # Optimistic upper allows every segment, ignores all floors and timing.
    _,optimistic=path_stats(upper,paths,np.zeros((len(paths),4,2),dtype=np.int64),durations)
    maximum=int(optimistic.max())
    index=None; maxlower=None; safe_count=None
    if eta is not None:
        ends=clocks(costs,paths,durations,eta)
        safe,gain=path_stats(lower,paths,ends,durations)
        safe_count=int(safe.sum()); maxlower=int(gain[safe].max())
        index=pick(gain,safe,arrays["cost"],loss)
    status="not_applicable" if loss<=0 else "admit" if index is not None else "impossible" if 2*maximum<loss else "abstain"
    return {"status":status,"eta_ticks":eta,"upper_credit":maximum,"lower_max_credit":maxlower,
            "lower_safe_paths":safe_count,"path":paths[index].tolist() if index is not None else None,
            "certified_credit":int(gain[index]) if index is not None else None,
            "extra_bytes":int(arrays["cost"][index]) if index is not None else None}


def psnr_units(negative_mse):
    with localcontext() as context:
        context.prec=40
        return int((10*(Decimal(65025*1000000)/Decimal(max(1,-int(negative_mse)))).log10()*1000000)
                   .to_integral_value(rounding=ROUND_HALF_UP))


def control_path(name, predicted, costs, durations, reserve, past, loss, eta):
    """Precommit a causal point-forecast path; no realized future observations."""
    if name not in ("cost_greedy","rolling_nash","maxmin"):raise ValueError("Unknown control")
    history=[sum(int(past[t][u])*durations[t] for t in (0,1)) for u in (0,1)]
    path=[]; start=0; finish=[0,0]; spent=credit=0
    for t in range(2,6):
        options=[]
        for a,b in product(range(2,6),repeat=2):
            sizes=[int(costs[t,r]) for r in (a,b)]; extra=max(0,sum(sizes)-2*int(costs[t,2]))
            if sum(sizes)>CAP or spent+extra>reserve:continue
            if predicted[t,0,a]<predicted[t,0,2] or predicted[t,1,b]<predicted[t,1,2]:continue
            arrival=[start+x for x in offsets(sizes)]
            end=[max(finish[u],arrival[u])+durations[t]+eta for u in (0,1)]
            gain=max(0,int(predicted[t,0,a]-predicted[t,0,2]))*durations[t] if end[0]<=DEADLINE else 0
            gain=min(max(0,loss-credit),gain)
            hist=[history[u]+max(1,psnr_units(predicted[t,u,r]))*durations[t] for u,r in enumerate((a,b))]
            score=(gain,-extra) if name=="cost_greedy" else (hist[0]*hist[1],sum(hist),-extra) if name=="rolling_nash" else (min(hist),sum(hist),-extra)
            options.append((score+(-a,-b),(a,b),arrival,end,hist,extra,gain))
        _,chosen,arrival,finish,history,extra,gain=max(options,key=lambda x:x[0])
        path.append(chosen);spent+=extra;credit+=gain;start=max(start+SLOT,max(arrival))
    return np.array(path,dtype=np.int64)


def independent(lower,upper,costs,durations,reserve,loss,eta):
    """Scalar DFS check, independent of vector paths and clocks."""
    best_lower=best_upper=0; safe_count=paths=0; mincost=None
    def walk(t,spent,start,finish,safe,gain,optimistic):
        nonlocal best_lower,best_upper,safe_count,paths,mincost
        if t==6:
            paths+=1;best_upper=max(best_upper,optimistic)
            if safe:
                safe_count+=1;best_lower=max(best_lower,gain)
                if loss>0 and 2*gain>=loss:mincost=spent if mincost is None else min(mincost,spent)
            return
        for a,b in product(range(2,6),repeat=2):
            sa,sb=int(costs[t,a]),int(costs[t,b]);extra=max(0,sa+sb-2*int(costs[t,2]))
            if sa+sb>CAP or spent+extra>reserve:continue
            arr=[start+19500+min(2*n,sa+sb) for n in (sa,sb)]
            end=[max(finish[u],arr[u])+durations[t]+eta for u in (0,1)]
            g=max(0,int(lower[t,a]))*durations[t] if end[0]<=DEADLINE else 0
            walk(t+1,spent+extra,max(start+SLOT,*arr),end,safe and lower[t,a]>=0 and lower[t,b]>=0,
                 gain+g,optimistic+max(0,int(upper[t,a]))*durations[t])
    walk(2,0,0,[0,0],True,0,0)
    return {"paths":paths,"lower_max":best_lower,"upper_max":best_upper,"safe_paths":safe_count,"minimum_cost":mincost}
