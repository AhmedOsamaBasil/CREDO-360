# Execution notes

- The fixed primary batch and both-OS full replays completed without a failed
  scientific check. All original scores/bounds matched and all independent
  enumeration checks passed. No frozen method or outcome was changed.
- The separate post-hoc diagnostic initially wrote its scalar JSON and two
  figures, then failed while writing metadata because `Path` was not imported.
  The missing import was fixed. Metadata completion requires the existing
  scalar results to match a full recomputation and both figures to exist;
  it does not overwrite any result or figure. This was a reporting defect,
  not a change to the sensitivity analysis or its conclusions.
- That first figure build also warned that the default user-level Matplotlib
  font cache was not writable. Figure files were created. Future figure builds
  use the repository's ignored `.matplotlib` cache; no global setting changes.
- Common-admissibility analysis and floor-loss magnitudes are post-hoc
  diagnostics. They are kept separate from the frozen sensitivity results,
  not presented as predeclared additional success conditions.
- The first WSL diagnostic verification exposed Windows backslashes in the
  diagnostic metadata's relative-path keys. Scientific digest and script digest
  already agreed. Portable POSIX keys are now used, with a separately created
  `metadata_portable.json` successor. The original metadata is retained and
  hash-bound, as are identical input hashes, results and figures. No scientific
  computation or value was changed by this metadata repair.
- The first Windows full regression completed 335 tests and 24 subtests but one
  fixture could not create a directory in the sandbox's default temporary area.
  The rerun uses a new explicit workspace-local base directory. No historical
  test or controller was altered to bypass the environment error.
