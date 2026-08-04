# Recommendation Diagnostics

This slice distinguishes three no-result states: no candidates returned by the baseline strategy pipeline, candidates evaluated but all rejected by user constraints, and scan errors.

It adds elapsed time, per-symbol diagnostics, rejection analysis, constraint impact, and bounded what-if guidance. Raw option-contract and pre-strategy spread-generation counts are not exposed by the current pipeline and are therefore not inferred.
