# Frozen fresh-content pilot: longer-horizon recovery

This protocol is frozen after the exposed-data search, before downloading or
viewing outcomes for the new scenes. It is an exploratory progression screen,
not a claim of validated novelty, human QoE, or population-level significance.
The prior v1 and v2 failed pilots remain part of the public record.

## Development and mechanism

DEVELOPMENT.md defines the six-configuration search. All six pass its relatively
weak development screen. The prespecified largest worst-user gain selects
H=24 and strength=8: development known-ceiling gain +0.01714 quality-index units
versus Nash and +0.03249 versus scale-matched memoryless. These are in-sample
selection outcomes, not independent confirmation. Preserve all 720 episode
summaries, causal plans and reference witnesses in results/development_v1.

The contract is a capped max-min six-period mixture of JOINT action vectors
under a common per-context Nash byte cap. It uses sender-known VoD quality
and segment bytes, past twelve capacity observations, and currently reported
display ceilings. It cannot look ahead at network capacities, transitions or
head movement. Renewal occurs every six rounds and at reported regime changes.
Each support vector fits its period's byte cap. Feasibility is in expectation
under predictions; the mixture is not itself an executable integral schedule.
No performance or convergence theorem is asserted.

The state sums signed target-minus-observed quality over the last24 decisions,
then clips the sum at zero. Surplus provides credit. Expiring residuals are
logged and must not be described as delivered recovery. Exact joint allocation
maximizes sum log(max(1,prediction-radius)) minus 8/(2*24) times predicted squared
terminal positive deficit. The current action is also capped at the bytes of
the stateless Nash solution; this prevents buying a quality gain with additional
bytes. It does not guarantee unchanged per-user stalls or fairness.

## Fresh data and calibration

Use the first60s of BuskingUnderpass05, Cheerleading01 and ConferenceParticipant02,
none of which occurs in either exposed catalogue. Conference scenes may share
a venue with historical material; this is not a new-dataset generalization test.
The same28 public source IDs appear in different trace sequences. Sort IDs by
SHA256("horizon-v3-"+ID), first9 calibration, remaining19 evaluation. No new
people, subjective ratings, consent collection, or human QoE validation.

Full-sphere area-weighted sender PSNR predicts the normalized objective quality
q=1+4*clip((PSNR-18)/24,0,1). There is no fitted subjective model. Calibration is
the maximum of9 participant-panel errors, each maximized over18 contexts and6
rungs. This is the finite-sample90% split-conformal rank only under panel
exchangeability, with a fixed catalogue. Adaptive selected-action and shifted
coverage are diagnostics, not conditional or transfer guarantees. Calibration
is written before loading the held-out outcome file. Raw test PSNR is accessed
only after action selection; controllers receive selected past feedback only.

The compressed25Mbps8K source is a reference, not lossless ground truth. Six
H264 NVENC representations are1920x960; metrics use960x480,1fps,12x6 tile-center
viewport approximation,100-degree fields and cosine-latitude weights. Segment
PSNR is log of average weighted MSE. Six10s segments repeat to120rounds: this
tests longer control history, not120distinct segments or independent samples.
Third-party raw media/traces stay outside the published repository.

## Paired experiment

Twenty seeds202610400--202610419, five users. Draw120 capacities Normal(3,.3),
clip[1,4.5]Mbps, multiply by.4 when epoch mod8>=5. Then sample five distinct
test IDs. Content assignment rotates by seed index/user. Current admission
uses last observed capacity, initial3Mbps. Fluid processor sharing and the
corrected synchronized playback clock charge every elapsed transport second;
each user starts with4s buffer. Computation time is measured but NOT injected.
This is an offline simulated transport experiment, not live headset streaming.

Conditions: capacity_only; known_ceiling (user index seed mod5 limited to rung1
in40--79, restored80); delayed_ceiling (one-round feedback delay); prediction_shift
(+0.6 prediction bias in40--79). No future regime transition is supplied.

Five matched policies: bounded stateless nash; window_recovery; memoryless_scaled
(24 times last positive residual); memoryless_unscaled (last positive residual);
fixed_window (same24-round state but target4). All share action sets, resource
cap, prediction information and base objective. No switching penalty in any
policy; switching is measured. This distinguishes history from a larger weight.
Expected240000user-round rows,400episodes,48000joint decisions.

## Outcomes and progression screen

Primary condition is known_ceiling. Report paired candidate-minus-baseline
differences for worst-user time-average normalized quality, fixed-target-four
cumulative shortfall, post-restoration shortfall (80--119), impaired-user
post-restoration shortfall, stall, mean quality, and switching. Use paired-seed
bootstrap2000 draws with seed481518 for descriptive95% intervals. Seeds share
the fixed content/participant pool; these are NOT independent people or a
population confidence guarantee. No uncorrected p-value or universal superiority
claim. Show every scenario and content-specific heterogeneity regardless of sign.

The pilot progresses only if ALL apply in the primary condition:

1. All20 paired seeds complete.
2. Worst-user-quality paired95% interval is strictly above zero against BOTH
   Nash and scale-matched memoryless.
3. Mean post-restoration fixed shortfall AND impaired-user post-restoration
   shortfall decrease against BOTH baselines (descriptive means).
4. Against BOTH, mean-quality loss <=0.03, cumulative shortfall increase <=5%,
   stall increase <=5% (absolute0.1s allowance only if baseline stall is zero).
5. Recovery state is active for >5% of user-rounds and >1% of individual actions
   differ from EACH primary baseline. Activation alone is not effectiveness.

The unscaled and fixed-window controls are secondary; they cannot replace a
failed primary comparison. Report censored recovery waits separately from
observed two-successive-round recovery events;40-round cap is not an event.
Report expired positive/negative residuals separately from delivered surplus.
No parameter, criterion, content or seed replacement after fresh outcomes.

## Reproducibility and interpretation

Bind source, data, configuration and result hashes. Save all raw rows, plans,
calibration panels, LP witnesses, paired summaries and failed checks. Replay
scientific fields across Windows/Linux, verify clock conservation and per-round
Nash byte limits, and independently inspect joint witnesses and state updates.
Publish the software and complete results before any manuscript edits. A pass
would support a limited objective controller result, not establish originality
over queue-based fairness, virtual queues, MPC, or prior immersive allocation.

Dataset sources: Robotham et al., QoMEX2022,
https://doi.org/10.1109/QoMEX55416.2022.9900893; Singla et al., QoMEX2023,
https://doi.org/10.1109/QoMEX58391.2023.10178588. Exact URLs: manifest.json.
