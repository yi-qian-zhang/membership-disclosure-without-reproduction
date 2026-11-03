# Hidden-48-nt endpoint and Methods corrections — 2 November 2026

This release updates saved BPE prefix endpoints by coordinate cropping, without
changing inference or historical raw JSON. See results/README.md and
results/target48_audit.json for the exact changed cells and uncertainty calculations.
Single-copy chromosome-22 exact recovery remains zero; final16-copy own rates are
42%,44%,40%. Membership scores, held-out loss and18–26% single-copy fresh ranking
are unchanged. Fresh Hamming differences are small relative to within-cell errors;
no reliable partial-recovery advantage is inferred. Older rows lacking saved strings
are marked legacy_variable and excluded from the manuscript48-nt evaluations.

Methods now distinguish independently drawn fresh controls from matched own-window
controls, define the admissible-content normalization used by PLL selection, and
identify teacher-forced surprise as covering-token surprise divided by48 target nt.
Trailing host letters remain in that scored event. F1 shows different downstream
host visibility for prefix and search protocols. The native single-slide PowerPoint
and its PowerPoint-exported PDF contain the corrected units and conditioning labels.

The per-seed table adds16-copy fresh membership; Figure2 ticks use measured rounds.
A new table reports per-seed/checkpoint Hamming means and descriptive standard errors.
The earlier E. coli BPE30%-versus0% comparison is3/10 prefix versus0/20 search,
not a common50-record evaluation; manuscript captions now report both budgets.

Regenerate plots and tables using the README commands. Regenerating the CSV itself
requires original private run outputs, and overwrites the change-list receipt on a
second run; preserve the committed initial audit. Do not replace the public redacted
historical records with unredacted outputs. No new training or GPU inference was run.
