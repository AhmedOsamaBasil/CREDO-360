# Causal adaptation under unrestricted future viewports

## Information order

At a request decision the policy knows sender-side maps/bytes/durations, the
fixed past debt, its resource/playback state and feedback from already played
samples. It commits the two whole-segment rungs before playing any sample of
that segment. Let F contain all 216 masks of the existing 100 by 100 degree
angular-window/tile-centre metric. Each future sampled mask may be any element
of F independently of earlier masks. This is a set-valued temporal assumption,
not a claim of statistical independence in observed human motion.

Giving the policy instantaneous, complete earlier feedback cannot remove any
future element of F. This statement would be false for a justified motion
constraint or a temporally coupled scenario model. Samples of the currently
playing EARLIER segment can be known at the next request; they are not samples
of the still unplayed segment being requested.

## Constructive adaptive upper bound

For each future segment t and committed recipient rung a, fix a ten-mask
sequence w(t,a) that minimizes the raw reference-minus-selected MSE at each
sample (the previously published extremal witnesses). Score reference and
selected maps using the SAME masks, round each segment MSE separately to
native micro-MSE units, and call their signed difference d(t,a).

The following response rule is admissible in the unrestricted class: when
the policy commits a, use w(t,a) during that segment. Previously chosen masks
are never revised. A donor sequence can be chosen independently (e.g. fixed
mask 0); donor feedback cannot constrain future recipient masks. For any
fixed deterministic causal policy, simulate this rule recursively. The
result is one complete geometric sequence for which that policy obtains the
computed credit. Once constructed it can be regarded as an exogenous fixed
sequence; a physical action-reacting human model is NOT asserted. This proves
an existence statement separately for each policy, not one shared sequence
that defeats every policy.

Let x=(t,spent,next-request,recipient-end,donor-end). File bytes and the specified
timing realization determine x'=T(x,a,b) independently of viewport quality.
Let g(x,a,b)=max(0,d(t,a))*duration(t) when the selected recipient segment
completes by 40s, and zero otherwise. Ignore both quality floors, allowing
strictly more policies than the original contract. Against this particular
response rule the best achievable total credit satisfies

    V(x) = max_(a,b resource-valid) [g(x,a,b) + V(T(x,a,b))],   V(terminal)=0.

No past quality variable is needed: the same continuation opportunities are
available after every past mask history reaching x. A history-dependent rule
chooses one of the same actions, and induction bounds its continuation by V.
The optimizing response-game strategy can therefore be precomputed, although
the original policy class includes adaptive controllers. Enumerating complete
resource-valid paths is an independent evaluation of the same recursion.

Writing C(pi,w) for delivered credit, for every deterministic policy pi the
constructed w_pi gives

    min_w C(pi,w) <= C(pi,w_pi) <= V(initial),
    hence sup_pi min_w C(pi,w) <= V(initial).

This is an UPPER bound, not necessarily the exact minimax value: the chosen
raw-MSE extremizers need not minimize separately rounded native credit.
Moreover the optimization deliberately ignores floors. Failure of this
generous bound to reach D/2 is sufficient to rule out the original universal
promise. A bound above D/2 would not establish feasibility.

The earlier L+5 micro-MSE envelope bounds d(t,a) from above (reference rung
exactly zero), giving a second, slightly looser upper bound. Its Bellman value
must equal the previously published fixed-plan diagnostic. That numerical
equality alone did not establish the adaptive result; the nonanticipation
and recursive counterexample argument above is the additional step.

## Timing, waiting and randomness boundaries

Use the admissible service-envelope realization with 0.5s additional execution
per segment, placed before playback. Actual durations and all elapsed waiting
are charged. For any realized action path, additional nonnegative waits can
only increase later request and completion times by induction through max/add
clock transitions. They cannot increase completed credit by the deadline.
The earliest-request DP consequently upper-bounds wait-for-feedback policies
too: unrestricted future masks cannot be ruled out by waiting. Smaller actual
execution delay can help particular paths; a universal conditional promise
must also survive this allowed 0.5s realization. This is NOT proof that the
execution/service envelope holds in an arbitrary deployment.

Deterministic rolling Nash, max-min, greedy, MPC or learned rules are covered
if they obey these action/information restrictions; there is no need to pick
one implementation to establish the upper bound. No new empirical baseline
ranking is claimed. Fixing a randomized policy's seed gives the same pathwise
argument when a guarantee is required for every seed, but private-randomized
expected performance against an oblivious environment is a different problem
and is not evaluated here. Do not swap the max/min information order.

## Checks against overgeneralization

Small exact games include a hidden mode revealed in past feedback that fixes
which future action is good. Adaptation can help when this temporal coupling
is retained. Removing that informative signal removes the advantage. A
one-stage crossed-reward example also separates observing a current outcome
before commitment from observing it after. These are synthetic logical
counterexamples, not empirical gains or proposed changes to the fixed contract.

## Prior-art boundary

Robust dynamic programming and rectangular uncertainty are established;
see G. Iyengar, "Robust Dynamic Programming," Mathematics of Operations
Research 30(2), 257-280, 2005,
[doi:10.1287/moor.1040.0129](https://doi.org/10.1287/moor.1040.0129), and
A. Nilim and L. El Ghaoui, "Robust Control of Markov Decision Processes with
Uncertain Transition Matrices," Operations Research 53(5), 780-798, 2005,
[author-hosted paper](https://people.eecs.berkeley.edu/~elghaoui/Pubs/RobMDP_OR2005.pdf).
Those works provide context, not a substitute for the model-specific proof
above. The contribution here is an auditable scope/feasibility diagnosis for
this fixed artifact, not a new general Bellman theorem or a successful new
streaming scheduler. No probability, perceptual or physical HMD inference is
licensed by this analysis.
