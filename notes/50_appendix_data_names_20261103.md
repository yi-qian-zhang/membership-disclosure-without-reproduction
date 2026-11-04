# 50. Appendix data names rather than filenames (3 November 2026)

The user requested that the scientific supplement contain no codebase filenames
or code. Alex clarified that the two A2 filenames were upstream data identifiers,
not repository scripts, and could legitimately remain. We explicitly acknowledged
that this is a presentation choice, not a correction of the data source. Following
the user's stricter preference, moved the exact file-level identifiers to the
English and Chinese READMEs while preserving scientific provenance in A2.

A2 now names the phased IGSR GRCh38 release announced 12 March 2019 and the GRCh38
reference assembly with decoy/HLA sequences, with its original citations.
The filenames ALL.chr22.GRCh38.phased.vcf.gz and
GRCh38_full_analysis_set_plus_decoy_hla.fa, and the VCF date 27 February 2019,
are retained in both README data-setup paragraphs. Those distinguish upstream
reference filenames from the builder's local chr22.fa input. No new data facts
or scientific measurements were introduced.

Replaced two visible appendix README mentions with repository documentation /
reproduction guide; the opening pinned guide hyperlink remains. Updated the main
Availability pointer from release dates/reference filename to data release/reference
assembly. The concrete VCF name already in main Availability was outside this
appendix-only request and remains unchanged. Scientific model names, dataset names,
AC/AN and mathematical notation remain; invisible TeX input paths are not prose.

Public README commit 0baf010; collaboration manuscript cd8ec74; submission
Overleaf 8896baa. The appendix guide and local protocol pointer pin the updated README.
Rendered appendix scan and independent read-only inspection found no remaining
visible filenames, code paths or script names in its text, 12 tables or utility plot.
Compiled 22 total pages, main10/appendix8; zero errors/undefined/Overfull, one existing
bibliography Underfull. All28 active references resolve; all46 label numbers/pages
unchanged. Inspected A2 and downstream pages visually. 53/53 Overleaf/local files
match; all42 full-version files unchanged. Bilingual nine bash command blocks are
unchanged. No tables, figures, results, bibliography or full manuscript were edited.
