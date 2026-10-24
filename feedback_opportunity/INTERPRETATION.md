# Opportunity audit and feedback implementation: findings

## Main conclusion

**The hidden-label feedback dependency has been replaced by a working compact
telemetry/reconstruction prototype. The recovery controller itself has not
improved, and another holdout is not justified for the unchanged candidate.**

All work uses the six already exposed scenes and existing participant traces.
No new media, participants, manuscript claims or journal submission were added.
The data preparation, packet definition, oracle contract and controller
parameters were fixed before the complete batch; adverse outcomes remain.

## How much recovery opportunity remains?

We exhaustively enumerated **473,088 complete paths** across 168 episodes,
using the actual-file cap of 1.5MB per round, rungs2..5, and the existing finite
extra-byte reserve. A separate gain/cost dynamic program matches the optimal
gain, cost and witness for every structural and strict-floor case.

| Method / bound | Half-repayment episodes | Mean unpaid fraction |
|---|---:|---:|
| Existing causal cost-greedy | 90/168 | 0.369140 |
| Exact-current greedy, immediate credit | 90/168 | 0.369137 |
| Future-known optimum, structural actions | 96/168 | 0.344994 |
| Future-known optimum, actual recipient/donor floors | 96/168 | 0.344994 |
| Future-known optimum plus quality guard | 95/168 | 0.355346 |

The quality guard requires **each episode's** mean worst-user quality to be
at least its saved rolling-Nash value minus0.02. This is a newly declared
diagnostic restriction, not the old cohort-mean screen. All168 guarded cases
have a feasible path. Counts refer to attained half-repayment, not feasibility
of choosing any action.

The full future-known advantage over causal cost-greedy is only **0.024146 in
mean unpaid fraction**; with the quality guard it is **0.013794**. Perfect
current quality barely changes greedy at all. Thus better current-quality
accuracy alone is unlikely to address the principal remaining limitation in
this fixed catalogue. These statements concern this contract and exposed
data, not a universal bound for immersive streaming.

The six additional half-repayment cases are in v2: its strict future-known
count is68/84 versus62/84 for greedy. In v3, even strict future knowledge stays
at28/84, the same as greedy; it can improve partial repayment but not this
binary count. The quality guard reduces the v3 count to27/84.

A separately labeled conditional continuation audit decomposes lost reachable
repayment against the structural future-known bound after each chosen action
(not against the quality-guarded bound). Cost-greedy leaves avoidable loss in65/168
episodes; candidate KNN does so in69/168. For cost-greedy the normalized losses
by recovery decision are0.003008,0.021135,0 and0.000002. Most loss occurs at
the **second recovery decision**, before the first ten-second segment has
finished playing in this cold-start schedule. This identifies where useful
lookahead or a different commitment schedule would have to help. It is not a
proof that the necessary future information is causally predictable.

## Feedback path: what is now implemented?

The sender builds content-only distortion maps from the existing source and
encoded representations. A JavaScript client converts completed viewport
samples into compact tile masks. A Python receiver reconstructs selected-rung
quality and the reference-rung counterfactual from those masks and maps.
The controller's initial event loss and completed recovery credit now come
from that reconstructed feedback, not hidden per-user quality-label tables.

All **1,008 JavaScript-produced reports** traversed a real loopback HTTP
connection. Duplicate, truncated and wrong-content probes were rejected.
Cross-language verification reproduces every packet and response. The first
restricted Windows attempt was denied on its first socket connection; it
produced no valid measurements and is documented separately.

- Payload: **140 bytes per completed ten-second segment**, or112bit/s per
  user before transport/header overhead. Total request payload141,120bytes;
  response bodies429,340bytes. This is not the total TCP/HTTP/TLS wire cost.
- Sender maps: **409,700 compressed bytes**, or622,080 raw float32 bytes,
  across all six 60-second scenes and six representations per scene.
- Local measured median/max reconstruction: **0.572/1.814ms**.
- Local measured median/max complete HTTP roundtrip: **14.977/28.583ms**.
  These are machine/loopback measurements, not WAN or HMD latency guarantees.

With the old pose-sampling rule, map reconstruction matches all6,048 saved
quality values **exactly**. With causal latest-observed-pose sampling, the
same-metric mean absolute difference is **0.000608dB**, maximum **0.202213dB**.
Of6,048 rounded objective-index values,5,968 match exactly; the maximum index
difference is0.017. Mean agreement does not erase that worst case.

These numbers establish fidelity to the existing coarse metric, not accuracy
against human experience or an independently validated viewport metric. The
sender still needs reference analysis. The maps do not capture decoder errors,
dropped frames, rendering/reprojection artifacts or personalized perception.

## Controller substitution result

All seven frozen causal policies were rerun for all168 episodes with the new
feedback-derived loss/reference ledgers. Actual quality and original event D
remain the scoring target. The initial loss estimate differs by at most0.002
index units; candidate final credit differs by at most0.011. **All4,704
selected actions are unchanged** relative to the previous ideal-feedback run,
so all actual quality, stall and repayment outcomes are unchanged.

The candidate still repays half in90/168 episodes, with mean unpaid0.371245,
compared with greedy0.370941 and cost-greedy0.369140. Its previous actual-floor
violations and quality tradeoffs remain. The unchanged practical screen
**fails**. Replacing an unavailable feedback assumption is an engineering
advance, not a new performance advantage.

The original `audit_v1` action-disagreement summary had a tuple-versus-JSON-list
comparison error. Its raw actions, ledgers and outcomes are intact. The
separate `diagnostics_v1` explicitly corrects and verifies those counts; no
measurements or controller decisions were overwritten to obtain agreement.

## What remains before deployment or another scientific claim?

The adapter and receiver are tested components, **not a production-ready HMD
player**. The client was exercised with recorded events under Node.js, not
physical rendering. A real player must align actual rendered orientation and
media presentation, handle partial final segments, verify tracking continuity,
and use authenticated/TLS-protected sessions with appropriate pose-data consent
and retention. The current loopback receiver trusts the reported pose and
completion position; it offers no playback attestation. Raw pose/mask packets
remain private and ignored by Git.

The controller substitution uses the existing fluid playback model and50ms
control allowance. Measured HTTP timings were not injected into a new live
media-player run; publication must not imply end-to-end deployment validation.
The one-frame-short final River01 segment retains the earlier nominal-clock
limitation. No new holdout was used.

Both operating systems reproduce the full audit hash
`510e3b7faa5f08e0d2077911b5e57655badeef3709b8599dab18416e3d2c1fe7`.
The final regression passes 273 tests plus 24 subtests on Windows and 269 tests
plus 24 subtests on Linux; four Torch tests run only on Windows. Both systems
also pass the five portable tests. The new package contributes 26 Python
tests, and the JavaScript client passes 11 assertions under Node.js.
The next defensible research question is whether content-aware causal
lookahead can improve the early commitments where avoidable loss remains,
against the simple cost-greedy control and the explicit quality guard. More
seeds or better retrospective feedback alone cannot establish that result.
