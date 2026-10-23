# Longer-horizon recovery: exposed-data development plan

This plan is written before development outcomes. No new holdout is loaded
during model/parameter development. Previous v1/v2 failures remain immutable.

## Mechanism

A six-segment sender-known quality catalogue defines a time-average service
contract. At each contract renewal, solve a capped max-min linear program over
mixtures of **joint** feasible action vectors per segment. Each support vector
fits a shared stateless bounded-Nash byte cap for that segment. The contract is
feasible in expectation for the forecast, not an integral execution schedule,
not an average of independently unattainable user maxima, and not a guarantee
under bandwidth error or viewport/model shift. The LP uses mean predictions,
not pessimistic instantaneous lower floors that suppressed the v2 queue.

Renew every six rounds and on an observed ceiling or prediction-regime change.
Forecast capacity for contracts is the mean of the last twelve observed round
capacities (initial 3 Mbps). Current admission uses the previous observation
(initial 3 Mbps). The future video catalogue is sender-known VoD information;
future network capacities, impairment transitions and HMD outcomes are not.

Recovery state is the positive part of the sum of **signed** target-minus-quality
residuals over the previous H rounds. Surplus offsets previous shortfall, and
expired residuals are recorded separately, never counted as delivered recovery.
Choose an exact joint action maximizing bounded Nash utility minus

    strength/(2*H) * sum_i [D_i + target_i - predicted_quality_i(action)]_+^2.

This is a terminal-deficit penalty, not a conformal improvement certificate.
The non-queue Nash baseline has the same byte cap and prediction information.
No policy uses a switching penalty in this version; switching is reported.

The main memoryless control uses H times the most recent positive residual,
so its normalized per-round deficit scale matches the window controller. A
second unscaled one-step control and a fixed-target-four window control are
retained. This tests history, not merely larger accumulated weights.

## Development search (exposed data only)

Use the three exposed v2 scenes and their fixed sender predictor/calibration.
Development seeds 202610300--202610305, five users, 120 rounds. Conditions:
capacity_only, known_ceiling, delayed_ceiling, prediction_shift. Capacity follows
the existing Normal(3,0.3), clipped[1,4.5], times0.4 for t mod8>=5 pattern.
One user has a rung-one display ceiling in rounds40--79, restored80; delay is
one round. Shift adds0.6 to predictions in40--79. No new participant claim.

Evaluate H in {12,24}, strength in {0.5,2,8}, all five policies. Select the
configuration with greatest mean worst-user-quality improvement versus Nash
in known_ceiling among configurations satisfying: positive improvement versus
the scale-matched memoryless control; mean-quality loss <=0.03; fixed-target
cumulative-shortfall increase <=5%; stall increase <=5% (0.1s if baseline0),
for BOTH key baselines. Ties prefer smaller H then strength. If none qualifies,
select the best worst-user gain as explicitly failed-development fallback and
report that limitation. Preserve all configurations, not just the selected one.

Fresh content and exact test seeds, progression criteria and the selected
configuration will be frozen in PROTOCOL.md after development and BEFORE new
downloads/outcome inspection. No held-out retuning. Source IDs may recur across
new videos; this will be content/trace-sequence holdout, not independent people.

This is an exploratory implementation of established queueing, fair allocation
and horizon-control ideas; engineering success would not prove literature novelty.
