# Remaining opportunities and implementable feedback

Use only the six exposed v2/v3 scenes, existing local encoded media and public
trace archives. Preserve all older sources/results. No new holdout, downloads,
manuscript changes or new controller tuning. Commit the protocol/software
before the full audit and publish all outcomes before any further holdout.

## Remaining recovery opportunity

Keep the original 168 event losses, rung2 reference, structural rungs2..5,
1,500,000 actual-file bytes per round and non-refilling extra reserve equal
to four baseline rounds. Enumerate all four-step joint paths subject to these
constraints. Report three future-known benchmarks: unrestricted actual-quality
floors (optimistic structural upper bound), actual recipient/donor floors,
and actual floors plus a per-episode worst-quality floor of the saved rolling
Nash result minus0.02. The last guard is a NEW diagnostic restriction, not the
previous cohort-mean progression screen. Include exact-current greedy with
immediate credit as an idealized diagnostic, not a deployable comparator.

Report attainable half-repayment, remaining versus avoidable unpaid loss,
minimum extra bytes for half-repayment, and strict-oracle differences from all
seven frozen causal policies by episode/cohort/scene. Independently cross-check
the unguarded integer gain/cost dynamic program against exhaustive enumeration.
Oracle gaps are not evidence that an online method can realize them. No claim
of new optimization theory or a successful recovery controller is intended.

## Feedback without hidden per-user quality labels

Sender: decode existing source/renditions with the old analysis settings and
build content-only per-rung/per-second 12x6 tile-MSE maps. Bind them to source
hashes. No participant/viewport labels enter map preparation. Client: report
ten 72-bit viewed-tile masks for the completed segment plus a descriptor hash,
segment, selected rung, sequence and media-completion position. Server: combine
masks with latitude weights and sender MSE maps, average MSE before taking the
log, and reconstruct selected and counterfactual reference quality. Neither
reference video nor an all-rung quality table is on the client.

Implement the client encoder in portable JavaScript and the receiver/reconstructor
in Python. Reject malformed, wrong-content, duplicate/out-of-order, incomplete
and premature messages. Missing samples fail closed; they are not filled with
unobserved poses. A player must call the adapter with its rendered orientation
and presentation clock. This work tests recorded pose events, not a physical
HMD. No subjective, no-reference metric or authenticated playback-attestation
claim is made. Production authentication/TLS and pose-consent controls remain
integration requirements; the prototype listener binds to loopback only.

For all28 existing trace IDs in all6 scenes, sample the latest pose at or before
each half-second sample point (causal zero-order hold). Old labels used the
first pose at or after that point. Keep that difference explicit; independently
check old-sampling reconstruction parity, then measure the new causal feedback
error. Do not silently redefine original evaluation labels or event losses.
The 1fps tile-center metric retains its old geometric/temporal approximation.

Run real JavaScript-produced binary packets through a local HTTP receiver for
all1,008 subject-segments, recording payload/response bytes, processing/roundtrip
times, hashes and reconstructed qualities. Do not publish participant-specific
pose/mask packets or third-party raw traces. Publish derived scalar outcomes,
sender distortion maps and hashes; keep raw telemetry local and ignored.

Substitute reconstructed completed-segment feedback into all7 frozen causal
policies, preserving their parameters, action/cost constraints and fluid timing.
The controller's event loss and completed reference credits must now come from
the feedback path, not target-label tables. Evaluation keeps original D and
actual quality. Release feedback only after modeled playback completion.
Report differences from the previous ideal-feedback run, all actual floor
losses, repayment estimation error and the unchanged practical screen. This
is wire-tested feedback plus controller replay, not a new end-to-end HMD trial.

Freeze before batch outcomes. Do not tune maps, sample rates, thresholds or
controllers to rescue a failed result. Include cross-language vectors, future
mutation tests, resource/clock audits, independent oracle checks and both-OS
verification. A technically working feedback channel alone does not authorize
another holdout or a positive paper claim.
