# Wu fixed-contract feasibility evaluation

Applies the predeclared feasibility design to the audited Wu v2 derived artifact.
See [PROTOCOL.md](PROTOCOL.md) for information limits, unchanged contract,
dispositions, numerical alignment and scope. No raw media or poses are needed.

Before evaluation:

```sh
python -m unittest wu_feasibility.test_core -v
python -m wu_feasibility.spec --freeze
python -m wu_feasibility.spec
```

Publish the registration before activating an evaluation using its exact SHA256:

```sh
python -m wu_feasibility.run --evaluate REGISTRATION_SHA256
```

After a complete result exists, reproduce every clip, bound, control and summary:

```sh
python -m wu_feasibility.run --verify
```

The initial strict Linux replay of the Windows result stopped at `e1v05`:
one maximum-mask witness ID differed (132 versus 84). That failure is retained;
the registered evaluator is not edited. The post-freeze `replication.py`
diagnostic can preserve an entire other-platform result and every exact
difference. It does not apply a new tolerance or claim byte-identical replay.
All original scalar extrema, endpoint and accounting checks are still run.

```sh
python -m unittest wu_feasibility.test_replication -v
python -m wu_feasibility.replication --output wu_feasibility/results/replication_linux_v1
python -m wu_feasibility.replication --verify-saved wu_feasibility/results/replication_linux_v1
python -m wu_feasibility.replication --audit
```

`--audit` is a disclosed post-freeze scientific-output comparison, not the
original exact replay. It recomputes all original checks and requires exact
equality of every field except extremal mask witness IDs. Each recomputed
witness still passes the original independent scalar-extremum check; no bound,
integer reward, path, decision or summary may differ. Any ID differences are
printed and `exact_replay_passed` remains false. This avoids treating an
alternative numerical extremum witness as a changed scientific result without
hiding the strict serialization discrepancy.

Only a new nonexistent output directory can be evaluated. A failed attempt must
be retained; verification is read-only. Conditional analytical completion does
not replace the separately planned measured-playback stage. Preparation labels
were already exposed before this integration; no new untouched-holdout claim.
