# Figure 1: editable source and export

[Repository home](../../README.md)

The current editable source is [F1_overview.pptx](F1_overview.pptx); the
[exported PDF](F1_overview.pdf) is supplied for systems without PowerPoint.
The slide uses native shapes and text.

On Windows with Microsoft PowerPoint installed, run from the repository root:

```powershell
& ./paper/export_f1.ps1 -OutputDir ./reproduced/figures
```

This exports PDF and PNG from the existing one-slide source without rebuilding
the layout. A complete TeX manuscript is not included in this public checkout.

Panel (c) distinguishes matched-loss recovery from the end-of-training
covering-token surprise comparison; they are different checkpoints. The source
also distinguishes the nominal prefix from the hidden 48-nt evaluation crop,
decoder flank visibility, and the two control-context protocols.

The original pre-revision source is preserved under [archive/](archive/README.md).
Use the current PPTX above when exporting the submitted overview.
