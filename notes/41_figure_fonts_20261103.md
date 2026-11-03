# Figure font-family unification — 2026-11-03

User requested matching Fig1's font throughout all figures, then explicitly clarified:
retain font sizes; change font family only. Any initially contemplated appendix
font-size/layout enlargement was reverted before figure generation or publication.

Fig1 uses embedded Arial/Arial Bold. It is unchanged. F2/F3 formerly used DejaVu Sans;
appendix FigureA1 used DejaVu Serif and FigureA2 Times New Roman. All five included
figures now use only Arial (and Arial Bold where already bold).

## Scope and preservation

- All original PDF media-box sizes and nominal font sizes are preserved. Main
  quantitative figures remain10.2pt; appendix source sizes remain6.5/7/8pt.
  The unchanged LaTeX inclusion widths also preserve the printed size scale.
- Curve data, seed ranges, markers, colors, line widths and existing figure text
  are unchanged. FigureA2's old ticks are explicitly pinned because changing font
  metrics otherwise changed Matplotlib AutoLocator's tick density. FigureA1's
  output crop is pinned to its original media box to prevent tight-bbox changes
  from changing the print scaling. Neither adjustment changes the measurements.
- All TeX, abstracts, bibliography, tables and results/ files remain byte-identical
  to baseline568ba25. F1 PDF/PNG and native PPTX sources are unchanged.
- `pilot2.figure_fonts.use_arial` requires genuine Arial; missing font installation
  gives an explicit error. The README documents GLMEXT_FONT_DIR. Font binaries
  are held in a private rendering cache, not committed or distributed publicly.
- Main plots regenerate with `figures_main10`; appendix plots use
  `figures_privacy --only blind` and `figures_paper --only variance`, avoiding the
  legacy entrypoints overwriting current main figures. All run on TJU_6004_sync.

## Checks

All four regenerated PDFs are vector text/graphics with embedded Arial; all five
included figures have the same text-token multiset as baseline. Every nominal
font-size set and PDF page rectangle matches its original. Fig2/3's complete
plotted-value audit JSON is byte-identical to note40's audit. All paired full/
submission figure assets match. Font inventory and before/after hashes are in
the adjacent validation JSON and local work/figure_fonts_20261103 directory.

Submission:37pages/main10/references3/appendix23; Figures1/2/3/A1/A2 at physical
pages3/7/9/24/31, unchanged. Errors0, undefined0, Overfull0, float-too-large0,
known Underfull2; literal xrefs4/4. Full version:48pages, xrefs5/5, same page
map and existing F1 long-caption float warning as the prior build. No new warnings.
Visual inspection at paper size found no new overlap or visibly clipped glyphs.
The Arial font line boxes in FigureA2 extend slightly beyond the tight crop for
three labels; this is not treated as proof of clipped ink. Rendered labels were
checked separately from these font-metric bounding boxes.
Independent verification expanded FigureA2's PDF MediaBox/CropBox by10pt and
rendered at4x: actual ink remains at least0.50pt from the original page boundary
(left0.50, top0.75, right1.94, bottom0.64pt). No glyph ink is cropped, so no font
size or position adjustment is warranted.

中文：按用户纠正，本轮只统一为Fig1的Arial，未改字号、图尺寸、数据、正文或图注。
正文及附录全部5张图已核对。投稿版仍正文10页、附录23页，所有图所在页未变。
字体文件只用于私有渲染，不进入GitHub或Overleaf；生成脚本新增明确的字体依赖说明。

Remote synchronization receipts follow after verification.
