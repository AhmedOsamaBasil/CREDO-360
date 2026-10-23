# CREDO-360: research and engineering instructions

## Purpose and working agreement

This repository is the public, reproducible testbed for multi-user immersive
streaming resource allocation and objective viewport-quality fairness.
The author wants technically substantive, honestly validated research, code
available for review, and software changes committed/pushed to GitHub before
manuscript changes. Do not submit manuscripts or contact editors without an
explicit request. Update this file and linked research notes as work proceeds.

The current paper is a standalone journal manuscript, not a "journal extension"
of a conference paper. Objective PSNR/SSIM and operational model indices are
not new human QoE validation, MOS, or perceptual superiority. No new human
participants have been recruited; public HMD traces are secondary human data.
Do not invent consent, ethics exemptions, citations, measurements, or guarantees.

## Repository map and provenance

- `testbed/`: earlier CUDA/packet-trace replay, recovered 13-feature subjective
  schema, legacy learned ensemble, tests and frozen results.
- `live_testbed/`: portable ensemble, candidate search, Mininet/curl DASH runs,
  frozen gate experiments and controller-latency scaling.
- `multimedia_testbed/`: QoEVAVE preparation, objective viewport measurements,
  six-content trace simulation, component ablations and frozen results.
- `literature/`: discovery scripts, evidence table and an INCOMPLETE review.
- `.external/`: ignored third-party source assets. Never redistribute media
  merely because derived measurements are public. Preserve source licensing.
- `README.md`, `REPRODUCIBILITY.md`, `CITATION.cff`: user-facing entry points.

GitHub is `AhmedOsamaBasil/CREDO-360`. The old `agent/powered-live-experiment`
branch has already been merged (PRs #1 and #2). Published evaluation commit
`f5c53e9` is included in main merge `efffc5f`. New work starts from fetched main
on a `research/` branch, as requested by the author. Never rewrite public
history or overwrite frozen results.
The pre-existing untracked `live_testbed/results/journal_gate_orchestration.json`
is not part of new work; do not delete or accidentally commit it.

## Research history to preserve

1. An initial anonymous-feature replay was rejected internally. The recovered
   13-feature replay uses the author's previously published subjective stimuli;
   its positive and adverse outcomes must both remain documented.
2. Earlier 30-seed Mininet studies use Big Buck Bunny DASH, five clients and
   a model-based operational quality index, not measured viewport perception.
3. The non-actionable experiment imposed a client service ceiling and compared
   against **resource/bitrate debt**, not a pure quality-gate ablation.
4. Experiment C uses six QoEVAVE source scenes, six representations, six 10 s
   segments and 30 paired seeds. The source is 8K; encodes are 1920x960 and
   quality analysis is 960x480 at 1 fps. Do not call it 8K delivery validation.
5. The submitted manuscript was assessed as ready too early. The October 2026
   technical audit found the validity problems below. Address them rather than
   treating formatting, more seeds, or a journal change as the remedy.

## Established audit findings (23 October 2026)

- Legacy subjective-model residuals were reused for normalized objective PSNR.
  Equal numeric ranges do not equate targets. Calibration-split HMD rows were
  excluded by `run_generalization.py`, despite contrary supplement wording.
  CREDO objective lower-bound coverage in the frozen v2 data is 530/900=58.9%,
  nominal 90%; these rows are dependent, not 900 independent trials.
- With fixed reference and L(a)>=L(reference), including flat plateaus,
  sum w*[L(a)-L(reference)]+ equals sum w*L(a) minus a constant. The old gate
  therefore cannot be a distinct allocation mechanism in that setting.
  All 900 CREDO vs calibrated-ungated allocations match in the v2 campaign.
- Debt addition improves worst-user VW-PSNR by 1.1789 dB in the existing
  ablation; gate addition is zero; calibration added to mean-debt is -0.0688 dB
  and not significant. Do not claim a demonstrated three-way interaction.
- A difference of two lower bounds is NOT a lower bound on improvement.
  An identical additive radius cancels from the difference when unclipped.
- The 73.9% waste/70.8% stall result versus bitrate debt does not isolate the
  gate; the reward's quantity and scale change as well.
- Round-synchronized live/simulated transfers debit each client's own download
  duration but omit waiting until the next shared round. Correct all elapsed
  playback time, including decision/launch/wait time, before new comparisons.
  All eight v2 controllers' saved stalls occur at epoch zero and totals tie.
- The FairEdge360 comparator is an explicitly labelled objective proxy, not a
  faithful reproduction of its MARL/GNN method. Do not call it SOTA dominance.
- The 5--30-user benchmark measures latency/feasibility, not optimization gap.
  Evaluate candidate quality and label permutation sensitivity against an exact
  small-system optimizer before making stronger scalability claims.
- Viewport weighting uses tile-center inclusion and latitude area, not exact
  fractional viewport overlap. Segment PSNR is log of mean weighted MSE, not
  mean per-frame PSNR. Supplement Jain formula must match the normalized index
  actually used by code. Available traces are not necessarily exercised traces.

## Scientific requirements for the recovery pilot

- Train/calibrate on the **same objective target** as the evaluation. Record
  disjoint subject splits, input hashes, all settings, and calibrated units.
- Never let test labels or future realized head movements enter decision-time
  features. Precomputed sender-side representation properties must be declared.
- Account for correlated frames/segments/actions using an explicit calibration
  unit. Marginal bounds do not imply conditional or adaptively selected-action
  guarantees. State exchangeability/shift assumptions and audit violations.
- A new recovery mechanism must differ meaningfully from quality-debt weighting,
  with identical information, action sets, tuning budget and base objective in
  its matched comparators. Include exact optimization for the pilot.
- Exercise congestion, non-actionable impairment, service restoration and model
  shift. Measure cumulative shortfall, consecutive deprivation, recovery delay,
  waste, stall and quality trade-offs. Use longer-than-six-decision sessions.
- Pilot/replayed/synthetic impairment results are not confirmatory evidence or
  live human validation. Do not silently retune after observing test outcomes.
  Record negative results and conservative/vacuous bounds; simplify the method
  if calibration/gating provides no added value.
- Do not overwrite existing CSVs/reports. Use versioned new result directories,
  fail on output reuse, and give each report a precise source/protocol identity.
- Keep old studies reproducible but visibly mark limitations; never silently
  regenerate manuscript tables from a changed algorithm.

## Literature and publishing guardrails

The prior discovery returned 470 records and a 25-study core table. These are
working counts, not a completed PRISMA review. Full-text verification and
snowballing remain incomplete, especially Risk as a Resource and DK-MARC.
Foundations include virtual queues/Lyapunov control, adaptive conformal inference,
and multi-user uncertainty-aware streaming (including FairEdge360). Evaluate
actual mechanisms, not keyword absence. Do not claim absolute or first-ever
novelty without a carefully supported, appropriately narrow comparison.

The original TMM limit was 10 double-column initial-submission pages; budget
was not a user constraint. The supplement budget was up to four pages. Verify
the target venue's current rules before reusing those limits. All figures,
tables and algorithms must be referenced/discussed using their LaTeX labels;
use genuine algorithm/pseudocode environments and concise informative captions.
Preserve substantive unique information. Update code/results before manuscript.

MIT licenses code; it does not legally require paper citation. `CITATION.cff`
requests scholarly attribution. Never change licensing silently or claim MIT
enforces citation. Public Git history remains public after normal merges.
Do not misstate contribution/ethics disclosures. Author preference: no assistant
names or generation-bot branding in new repository content, branch names,
commit messages, code comments, or manuscript prose. Leave the existing
manuscript acknowledgment unchanged. Preserve required disclosures/provenance
and existing Git history; this preference does not authorize rewriting either.

## Current handoff

- 2026-10-23: author approved technical corrections, development/testing of a
  recovery mechanism, a pilot, and GitHub commits before manuscript changes.
- Working branch: `research/recovery-pilot`, based on fetched `origin/main`.
- Locked protocol and history commit: `4169be8`. The pre-run mathematical review
  corrected the vacuous joint quality/gain error bound from 4 to 6; this is
  documented in `recovery_pilot/PROTOCOL.md`, before outcome inspection.
- Software implementation commit: `26b744b`, pushed to the research branch.
  Objective-panel calibration, direct shortfall-gain recovery, exact allocation,
  corrected playback clock, output/resume safeguards and matched ablations.
- Full Windows regression: 52 tests plus 12 subtests pass. Linux portable:
  48 tests plus 12 subtests pass. Use `.external/venv/bin/python` in WSL Ubuntu;
  bare system Python lacks pytest, and the Linux environment lacks PyTorch.
  The four legacy PyTorch tests passed in Windows, not Linux.
- Pilot v1 COMPLETE: 12 seeds, 4 scenarios, 8 policies, 60 rounds, 5 clients;
  115,200 rows. Integrity audit passes with maximum clock residual ~1.4e-14 s.
  Joint envelope radius 0.474135, 9/9 held-out panels covered; prediction-shift
  selected quality coverage falls to ~74%. No arbitrary-shift guarantee.
- Scientific progression criterion FAILED. Known-ceiling candidate minus
  bounded-quality debt: cumulative shortfall +0.19636 index-rounds/user;
  post-restoration shortfall -0.00847; stall +0.09215 s/user; worst-user mean
  quality -0.00161. Do not present the new controller as superior or retune it
  against the same held-out IDs. See `recovery_pilot/INTERPRETATION.md`.
- Linux first-seed replication: 9,600 scientific rows identical to Windows,
  excluding runtime. That single seed passes the screen; the full campaign
  fails. Never select the single seed to reverse the conclusion.
- Live-clock smoke: two clients, three rounds, six records using existing DASH
  media and the legacy bounded-Nash controller. Exact stored time conservation;
  max observed post-completion wait 0.10854 s. This is NOT live evaluation of
  the new recovery controller or an immersive-player campaign.
- Overleaf and its acknowledgment remain unchanged. Next research decision:
  simpler debt trade-off study versus a separately evaluated feasibility-aware
  recovery mechanism. Wider content/live/scalability/novelty checks remain open.
- Detailed protocol, code, immutable outputs and reproducibility instructions:
  `recovery_pilot/`. Preserve the failure as evidence, not something to hide.
- Reproducibility packaging: new result bytes are preserved with `.gitattributes`.
  Historical input CSVs can differ by Git's LF/CRLF checkout conversion; the
  bound raw/canonical hashes in `input_text_hashes.json` permit only that change.
  Hashed pilot source files use LF. CI verifies the saved artifact, not just tests.
- Results/audits commit: `42b9559`. A fresh Git-archive extraction of that commit
  also passed all 115,200-row integrity checks, including permitted LF/CRLF
  transport differences. The manuscript remains outside this software change.
