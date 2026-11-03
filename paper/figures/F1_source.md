# Current Figure 1: editable source and export

The current source is `F1_overview.pptx`. This is the revised original diagram, with
native model cards, cohort icons, DNA curves, mask cells, ranked candidates and token
rectangles. It is not the compact flowchart. The author-designated working copy is
`GLM Collaboration Extensions/Ppaper_Figure/F1_OVERVIEW.pptx`.

From the repository root on Windows, export through Microsoft PowerPoint:

```powershell
& ./paper/export_f1.ps1
```

The command exports `F1_overview.pdf` and `F1_overview.png` from the existing slide;
it does not rebuild or simplify the slide. `main.tex` includes the PDF at 6.5 inches.
The 960-by-996-point source therefore prints at 6.5 by 6.744 inches. Its smallest
21.6-point slide font prints at approximately 10.53 points.

`F1_overview_compact.pptx` and `../build_f1_compact.ps1` are historical artifacts of
the earlier simplification. Do not use that script to regenerate the current figure:
it reconstructs the rejected compact layout and overwrites the PDF.

The current style uses shallow gray panel headers, thin black arrows and blue/orange
accents inspired by the author-supplied DIME figure. Scientific drawings remain native
PowerPoint objects. Panel (c) separates matched-loss recovery from the end-of-training
target-surprise comparison; it does not identify these checkpoints. The endpoint table
shows both absolute planted surprise and the control-minus-planted gap. The common
target before the tokenizer fork is neutral gray.

Both manuscripts now use the same corrected editable figure. The pre-revision
full figure remains in the `methods-before-target48-20261102` and
`paper-full-before-v4-20261031` archive tags. The exact source copy used for this edit
is now archived inside this project at `archive/F1_author_source_before_20261031.pptx`;
its provenance and SHA-256 are recorded in `archive/README.md`. The author working
path is mutable; this archive is the preserved original. See notes 25 and 26 for
object preservation, scientific scope, page count and synchronization checks.

The 2 November endpoint revision distinguishes nominal prefix input from the
hidden48 evaluation crop, shows decoder flank visibility, separates paired own
controls from independently drawn fresh contexts, and labels covering-token bits
including trailing host letters. All native objects and minimum fonts are retained.
