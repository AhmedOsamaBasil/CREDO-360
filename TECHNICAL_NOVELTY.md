# Technical novelty: opportunity-aware calibrated QoE debt

## State

For user \(i\) at epoch \(t\), let \(q_{i,t}\) be realized QoE and \(q^\star\)
the declared service floor. A decayed deprivation queue is

\[
d_{i,t+1} =
\left[\rho d_{i,t} + q^\star - q_{i,t}\right]_+ .
\]

Unlike snapshot Jain fairness, this state records which individual has
experienced repeated shortfall.

Virtual queues in video allocation are not themselves novel. Zhu et al.
(*IEEE Network*, 2015, DOI `10.1109/MNET.2015.7340418`) use a per-user queue to
stabilize long-term playback fluency, and other Lyapunov streaming methods
track buffer, delay, or compute constraints. The claimed distinction here is
the coupling of **realized QoE shortfall**, a **coverage-calibrated QoE
counterfactual**, and **opportunity gating** in multi-user immersive allocation.

## Calibrated counterfactual opportunity

The QoE model predicts \(\hat q_{i,t}(a)\) for feasible joint bitrate action
\(a\). Online residual calibration yields a lower bound

\[
L_{i,t}(a) =
\operatorname{clip}\!\left(
\hat q_{i,t}(a) - r_{g(i),t}^{1-\alpha}, 1, 5
\right).
\]

Let \(a^{\min}\) be the minimum-service allocation. The recoverable,
uncertainty-adjusted opportunity is

\[
\Delta^+_{i,t}(a) =
\left[L_{i,t}(a)-L_{i,t}(a^{\min})\right]_+ .
\]

Debt is therefore spent only when the candidate action has calibrated evidence
of improving that user. This prevents raw queue weighting from wasting scarce
capacity on non-actionable impairment.

## Allocation

\[
a_t^\star = \arg\max_{a\in\mathcal A(C_t)}
\left[
\sum_i \log L_{i,t}(a)
+\lambda\sum_i
\frac{d_{i,t}}{1+\bar d_t}\Delta^+_{i,t}(a)
-\eta\,S(a,a_{t-1})
\right].
\]

The three terms are:

1. risk-aware Nash welfare;
2. normalized temporal-deprivation recovery; and
3. representation-switching cost.

The implementation scores a deterministic cover of the feasible joint action
space in a single CUDA batch.

## Falsifiable claims

The method is useful only if it demonstrates a declared trade-off:

- increased worst-user mean QoE and/or reduced cumulative service violation;
- no uncontrolled rebuffering increase;
- empirical lower-bound coverage near \(1-\alpha\);
- robustness across service floor, debt gain, decay, and distribution shift.

Mean QoE and CVaR may decrease. Those outcomes must be reported and cannot be
hidden behind a generic “fairness improvement” statement.
