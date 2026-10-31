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

Only a new nonexistent output directory can be evaluated. A failed attempt must
be retained; verification is read-only. Conditional analytical completion does
not replace the separately planned measured-playback stage. Preparation labels
were already exposed before this integration; no new untouched-holdout claim.
