# Recommendation Constraints v0.4.0

The Recommendations workspace now separates:

- hard constraints, enforced before a candidate is returned;
- display filters, applied only to already-included candidates.

All fields are optional in this release. Blank means no user-imposed override.

Pricing transparency includes short and long bid/ask, natural credit, midpoint
credit, conservative credit, scoring credit, selected pricing method, and
credit per contract.

The normalized option model does not currently preserve the Schwab quote
timestamp. The UI therefore displays the timestamp as unavailable rather than
inventing one.
