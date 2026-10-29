# Verification and provenance

The approved split was published as64b6d5d before calibration pose access.
The method and pre-comparison reference-time clarification were committed
as ec3269e before the full calculation; the method commit was pushed after
that calculation. No claim of a new preregistered recovery experiment is made.
All original frozen packages, source assets and service parameters are unchanged.

## Reproduction identities

- Windows calibration report:
  `64d558aedc8af526030d5b0c46580ece3c5bf1e7525c7928ff53490df76b1c67`.
- Independently derived WSL/Linux report:
  `1e50d3389a17c1f2cb01cae05b2a888d7fd335717a1e4e2d68e837631f362f7c`.
- Conservative adapter/scalar validation, identical on both platforms:
  `1b9cd5d12bf9b099c1eb7eebb2e6e9baab21df0f84632e2bf4bf6e38b294d315`.
- Private author-reference SHA-256:
  `f7973e0a6a3dea7b25dd276d98afb5eafabdb9ece13be657b86138a709932afc`,
  with the expected Git blob identity verified before comparison.

The two primary reports are **not bit-identical**. All discrete decisions,
source identities, counts and scope flags agree. Among1868 float values,
276 differ; the largest absolute difference is9.38e-11 degrees. Both full
scalar reports and the executable comparison are published, rather than
rounding one platform's report to claim an identical hash. The comparison
allows1e-5deg angular and1e-10 other numeric error; actual differences are
much smaller. Replaying the published Windows artifact succeeds on both OSes.

## Tests and independent checks

All48 new unit/artifact tests pass on Windows and Linux. Full regression gives
694 tests plus41 subtests on Windows and690 plus41 on Linux; the four legacy
Torch tests are covered on Windows. The five portable-model tests are included
in broad collection and also pass separately on Windows. Windows client checks
pass11 assertions and shared-payload service tests pass. These counts do not
represent independent research participants or experimental replications.

Scalar enumeration independently checks5760 target crossings across96 traces.
Hamilton quaternion multiplication and a separate scalar tile-mask/weight
implementation check2880 accepted samples at1e-10deg and1e-12 weight tolerance.
The two clips repeat48 source identities. Forty-eight basketball traces qualify;
all48 skiing traces are rejected for the duplicated0.5s crossing. No silent
first/last selection, time shift or whole-parent contract change is performed.

The prior source report and original confirmation registration still verify
unchanged. Earlier workflow40966975994 at5d7fc7b is verified completed
successfully; this does not assert completion of a later commit's workflow.

## Failures and limitations retained

- Exact decisecond-key lookup found no rows at the five fixed target keys.
  Reference timestamp inspection showed the author's coarser cadence. The
  separate pre-comparison alignment record reproduces the renderer's held
  bucket and compares at its actual recorded time. Targets and error gates
  were not retuned after coordinate results.
- An adapter regression test caught an ambiguity loophole: filtering crossings
  by age first could hide an out-of-age repeat. Before real adapter evaluation,
  the rule was strengthened to count all crossings before checking age. The
  formerly failing example and additional stale/initial/coverage cases pass.
  The original calibration comparison and its output are preserved unchanged.
- An initial read-only Git query used the workspace instead of nested repository
  and failed safe-ownership checking. Correcting the working directory resolved
  it; no global Git setting was changed. WSL systemd-session warnings were
  nonfatal. No experiment or source was rerun to seek favorable performance.

The author demonstration supplies a projection reference, not an independent
measurement of physical display timing. Private source overlays were visually
checked against the published figures but are not republished. Raw traces,
calendar timestamps, source frames, reference CSV and demographic files are
excluded from the public artifact. Sixteen confirmation clips' pose values
remain unopened. Full source qualification, quality labels, recovery results,
manuscript changes and a new submission are outside this completed stage.
