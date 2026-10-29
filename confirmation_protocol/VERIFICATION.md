# Design verification

The design registration has canonical SHA-256
`c40d455824ee689d8b2adc356526026ba6a18aed763bb42de3f1b5cfc69d9487`.
Windows and WSL independently reproduce this value from the same frozen design,
claim sources, public catalogue facts, historical manifests and four exposed
result artifacts. This is verification of a research design, not an external
experiment or a second independent replication of the earlier measurements.

All48 new tests pass. They include588 exact integer threshold cases,
positive-admission witnesses, incompatible bound rejection, missing-result
handling, equal-clip versus pooled aggregation, nonfinite metadata rejection,
source-exposure declarations, duplicate source windows and catalogue accounting.
The initially skipped registration test ran and passed after the record was
created. No empirical source was loaded by these synthetic tests.

Full regressions pass538 tests plus24 subtests on Windows and534 plus24 on
WSL/Linux. Four legacy Torch-dependent tests run on Windows only. Portable
model checks pass five on each operating system; Windows JavaScript checks
pass11 existing feedback assertions and the shared-payload-service suite.
The Windows run used a new explicit workspace-local temporary directory.
Git reported routine LF/CRLF warnings for root documentation/configuration;
the new package has explicit LF attributes and canonical text-source hashing.

The existing timing-study workflow40936126587 atf309960 was independently
checked as completed successfully before this design was published. That does
not assert that CI for a later commit has finished; check its exact workflow.

The current registration deliberately reports `blocked_before_outcomes`:
source collection, paired assets, source-to-media timing/projection mapping,
reuse review and adapter freeze remain outstanding. Syntactically complete
JSON metadata does not prove these facts or authorize an experiment. Source
selection must not be chosen after inspecting recovery results.

Earlier frozen code/results and the manuscript are unchanged. No fresh video,
pose values, recruited participants or measured sessions were accessed here.
