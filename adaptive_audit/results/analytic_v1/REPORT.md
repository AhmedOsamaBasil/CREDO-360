# Adaptive-policy feasibility audit

deterministic causal whole-segment policies; unrestricted sampled geometric future masks

| Execution allowance | Episodes | Universal half promise ruled out | Largest response upper / debt |
|---|---:|---:|---:|
| ideal | 168 | 168 | 32.163619104% |
| half_second | 168 | 168 | 32.163619104% |

These are conditional upper bounds with quality floors removed, not observed
recovery rates or positive admission certificates. Synthetic response sequences
are geometric model counterexamples, not measured human traces.

## Exact information-order counterexamples

| Constructed game | Fixed plan | Causal policy | Clairvoyant |
|---|---:|---:|---:|
| coupled_informative_past | 0 | 1 | 1 |
| coupled_uninformative_past | 0 | 0 | 1 |
| current_outcome_after_commit | 0 | 0 | 1 |
| current_outcome_before_commit | 0 | 1 | 1 |

Causal column in the before-commit row intentionally has a different
information order. It is not an allowed policy for the streaming audit.

See THEORY.md for quantifiers, nonanticipation, waiting and scope boundaries.
