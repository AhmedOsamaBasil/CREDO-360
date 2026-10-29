# Interpretation: faster completion is not a recovery guarantee

The exposed matched-path study is complete: all 2,688 analytical cells and
all 74 scheduled browser sessions are retained. The 74 sessions pass the frozen
event audit and independent post-hoc conservation/ledger checks. This is a
successful measurement implementation, **not a successful new recovery
controller**. The detailed [report](results/diagnostics_v2/REPORT.md),
[figure](results/presentation_v2/timing_and_repayment.png) and raw records are
part of the same artifact.

## Main findings

| Fixed path | Replay protected half /168, every configuration | Browser protected half /6, every configuration | Browser cold finish: 10s to 2s files |
|---|---:|---:|---:|
| Cost-greedy | 27 | 1 | 49.823s to 43.203s |
| Rolling Nash | 4 | 0 | 49.835s to 43.207s |
| Max-min | 4 | 0 | 49.833s to 43.194s |

The original parent account and the separately defined chunk account have the
same protected-half counts in this study. They are nevertheless different
metrics: their positive-part operation, floor granularity and credited units
are not interchangeable. The 168 exposed episodes use 28 reused identities over
six scenes. Each browser cell uses the fixed 1:2 identity pair in those scenes,
not six newly recruited pairs or a fresh test cohort. Policy runs and frames
are not independent statistical samples; no p-value or confidence interval is
assigned to this batch.

**Shorter delivery helps completion timing.** Mean final recipient completion
falls by 6.62-6.64s in cold browser runs. Charged four-second buffering then adds
about 1.15-1.18s to the two-second configurations. It does not provide free
advance service or change the 40s deadline. These are matched descriptive
effects for fixed parent rungs, not an optimal two-second adaptive policy.

**Faster completion alone does not change target attainment.** In analytical
replay, shorter units alter the number of on-time completed parents in 28/168
episodes for each nonbaseline path, but change original credited repayment in
none. The changed completed parents carry no additional positive original
credit. Thus completion counts must not be substituted for quality repayment.
All reported reserve and parent-pair byte-cap checks pass, including remux
container bytes. The original R4 entitlement is not replenished per chunk.

**Real timing exposes a deadline cliff hidden by the ideal replay.** All six
ten-second Cheerleading sessions (three paths, two startup modes) finish one
positive-credit parent after 40s, losing 5.873 percentage points of repayment
relative to the ideal queue. Two-second delivery retains that parent's credit.
Neither configuration reaches half repayment for that scene, so the protected
target count stays unchanged. For session 17, the parent finishes at 39.9686s
in the ideal model and 40.0204s in the measured record. This is an observed
near-deadline miss, not a reason to loosen the deadline after the fact:

```sh
python -m player_timing.inspect --index 17
```

**Protection remains a separate condition.** In the measured River pair, all
three paths repay 80.93% of the input debt. Cost-greedy satisfies the native
floors; Nash/max-min do not. Those strict numerical floor failures are retained
without being described as demonstrated perceptual harm. This is not evidence
that a newly developed controller outperforms the baselines: the paths are
the earlier frozen diagnostic controls.

## Controls and measurement uncertainty

- Delaying the first recipient transfer by 40s yields zero original credit and
  a recipient finish of 82.239s. Late receipt is not counted as timely recovery.
- A 6MB background transfer shares the same cap. It increases served payload
  from 3,874,125 to 9,874,125 bytes and moves recipient finish from 42.633s to 57.216s.
  Original repayment remains 34.47% for that Park path; contention does not
  necessarily change the chosen deadline score. This unchanged outcome is
  retained, not forced into a negative recovery result.
- The logs contain 156,655 video-frame callbacks, 19,685 callback sequence gaps
  and 122 summed per-file browser dropped-frame counts. All 1,808 file playbacks
  have a callback within the declared 1.5-frame-period tail tolerance. These
  quantities are different; a tail witness does not prove every frame appeared.
- Ended-event, client-report-ready and tail-witness accounts give the same
  original and chunk credit in all 74 sessions. Their event timestamps are not
  identical. A remote controller's receipt is not inferred by subtracting
  unsynchronized server and client clocks.
- The first request occurs 0.4-1.1ms after the browser run epoch. The frozen
  audit is therefore slightly stricter than the exact first-request deadline.
  Explicit post-hoc realignment changes neither account's credit or half-target
  classification in any session; both calculations remain inspectable.
- Observed load-to-ended overhead beyond media duration ranges from 8.1 to 73.5ms.
  These finite observations do not establish a hard future execution bound.

The system plays full equirectangular H.264 files in headless Chromium under
controlled loopback payload service. It is not an interactive viewport renderer,
physical network, HMD or subjective study. Quality is an offline sampled-trace
label, while playback completion is newly measured. The earlier loss-generating
interval is supplied by the frozen ledger, not replayed to a human here.

## Consequences for the research claim

The timing diagnosis survives this specific shorter-file/charged-buffer
sensitivity: target success remains concentrated on River, while measured
deadline fragility is now directly observable. This does **not** extend the
old unrestricted-future impossibility theorem to a new shorter-action policy
class. The new sessions fix each parent rung across its children; within-parent
adaptation, calibrated future viewport sets and physical presentation remain
untested. A fixed-path negative result is not a proof that all alternative
controllers fail.

The [full-text comparison](PRIOR_ART.md) also rules out treating generic
conformal risk control or uncertainty-weighted CVaR streaming as our novelty.
The candidate contribution remains the explicit feasibility/information/time
audit of a protected repayment commitment. Its value must be established by
correctness, tightness and useful service decisions, not by the number of tests
or by recasting standard optimization ingredients as new theory.

No further feedback-only tuning or fresh holdout is justified merely by these
unchanged target counts. Before independent confirmation, lock the final
feasibility question, exact action/information contract, primary endpoints and
dependence-aware sampling. A broader controller-superiority claim would require
a genuinely distinct method and matched modern streaming baselines, not just
Nash/max-min labels. No manuscript, acknowledgment or submission was changed.
