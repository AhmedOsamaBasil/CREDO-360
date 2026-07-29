# Systematic literature review protocol

## Review question

Does prior work jointly provide:

1. multi-user immersive or adaptive-media resource allocation;
2. QoE fairness across users;
3. calibrated, coverage-controlled uncertainty for learned QoE/viewport models;
4. adaptation under non-stationary distribution shift; and
5. explicit memory of persistent per-user QoE deprivation?

The review tests the intersection. A paper covering only one component may
invalidate a broad component claim even when it does not cover the intersection.

## Scope and date

- Search date: 28 July 2026.
- Years: 2010–2026, with backward snowballing for earlier foundations.
- Types: peer-reviewed journal/conference papers; recent preprints retained
  only when clearly labelled.
- Language: English.

## Sources

- OpenAlex for broad discovery, deduplication, and citation-count metadata.
- IEEE Xplore, ACM Digital Library, official proceedings, journal sites, and
  institutional repositories for primary-source verification.
- The author’s publication site for identifying the prior-work lineage.

## Search families

1. `quality of experience fairness adaptive video streaming DASH resource allocation`
2. `360 video immersive VR QoE fairness multi-user viewport bitrate allocation`
3. `conformal prediction uncertainty quantification streaming network resource allocation`
4. `temporal fairness long-term fairness persistent deprivation network scheduling`
5. `QoE prediction distribution shift uncertainty adaptive streaming`
6. Synonym audit: `deficit`, `virtual queue`, `starvation`, `minimum service`,
   `long-term fairness`, and `risk-sensitive utility`.

The reproducible OpenAlex query script and raw discovery output are stored next
to this protocol.

## Eligibility

Include work that models, measures, predicts, or controls multimedia QoE, or
supplies a directly reusable uncertainty/fairness mechanism. The contribution
must be verifiable from an academic primary source and sufficiently specified
for algorithmic comparison.

Exclude marketing material, unsourced summaries, duplicated theses, pure
image-quality work without streaming relevance, and generic AI-fairness work
without a transferable sequential resource-allocation mechanism.

## Extraction fields

For each retained study, record:

- media type and single-/multi-user setting;
- QoE model and fairness objective;
- heuristic, Bayesian/ensemble, or calibrated uncertainty;
- coverage claim and assumptions;
- handling of distribution shift;
- persistent per-user fairness memory;
- dataset/testbed, baselines, and limitations;
- DOI/URL, venue, year, publication status, and dated OpenAlex citation count.

Citation counts identify established foundations; they are not evidence of
quality or novelty. Recent overlap papers remain essential despite low counts.

## Current flow

- Records returned across five OpenAlex search families: 470 deduplicated.
- Studies retained in the current core evidence table: 25.
- Full-text PDFs directly inspected so far: FairEdge360 and Adaptive Conformal
  Inference.
- Abstract/bibliographic verification only: Risk as a Resource and DK-MARC,
  because openly accessible full text was not found.

These are working counts, not a final PRISMA flow. Title/abstract screening,
exclusion reasons, duplicate handling across snowballing, and independent
checking must be completed before publication.

## Claim standard

Do not use an absolute “first” claim based on keyword absence. The strongest
permitted form is:

> To the best of our knowledge, among the studies retrieved by the documented
> search, verification, and snowballing protocol, none jointly …

Every component claim must name the closest contrary work and state the exact
remaining difference.
