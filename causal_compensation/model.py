"""A fixed causal forecast using other exposed scenes and disjoint source IDs."""


def training_pool(episodes, scene, recipient, donor):
    ids = {recipient, donor}
    pool = tuple(e for e in episodes if e.scene != scene and not ids.intersection((e.recipient,e.donor)))
    if any(e.scene == scene or ids.intersection((e.recipient,e.donor)) for e in pool):
        raise AssertionError('training contamination')
    return pool


def forecast(prefix_gains, loss, training, neighbors=8, padding=50):
    """No target episode or target future can be passed to this interface."""
    if len(prefix_gains) != 3 or loss < 0 or len(training) < neighbors or padding < 0:
        raise ValueError('three observed gains and a sufficient training pool required')
    ranked = []
    for e in training:
        distance = 2*sum(abs(a-o.gain) for a,o in zip(prefix_gains,e.offers[:3]))+abs(loss-e.loss)
        ranked.append((distance,e.key,e))
    nearest = sorted(ranked, key=lambda r:r[:2])[:neighbors]
    bounds = tuple((max(0,min(e.offers[t].gain for _,_,e in nearest)-padding),
                    min(4000,max(e.offers[t].gain for _,_,e in nearest)+padding)) for t in range(3,6))
    return {'bounds': bounds, 'neighbors': tuple({'key':key,'distance':d} for d,key,_ in nearest),
            'training_count':len(training), 'prefix':tuple(prefix_gains), 'loss':loss}
