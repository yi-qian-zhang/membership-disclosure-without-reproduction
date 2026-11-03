# Downstream utility against leakage — utility

MCC on each task's full test split: ft is the fine-tuned head and probe the frozen linear probe. Each task averages its available training configurations/seeds. Loss and canary statistics give equal weight to each unique configuration/seed/checkpoint across the human and yeast arms. Repeated task panels are merged before averaging; old single-task reports are included. Canary extraction evaluates the hidden 48 nucleotides of the 16-copy tier in its training host.

These are available-case descriptive summaries, not a balanced or paired panel: seed coverage and record counts vary across checkpoints and tasks. Repeated record evaluations are not independent trials. utility_downstream.json retains unrounded selection values, source hashes, configuration identities, per-checkpoint record counts and per-task seed coverage.

## DNABERT-2 BPE

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2.688 | 2.73 | 0% | 0.0% | 0.797 (0.740) | 0.591 (0.494) | 0.648 (0.530) | 0.000 (0.232) | 0.715 (0.604) | 0.000 (0.203) |
| 1 | 1.968 | 2.03 | 3% | 0.0% | 0.792 (0.759) | 0.592 (0.550) | 0.656 (0.561) | 0.608 (0.240) | 0.744 (0.642) | 0.086 (0.193) |
| 3 | 1.943 | 1.92 | 80% | 0.0% | 0.792 (0.771) | 0.603 (0.562) | 0.663 (0.543) | 0.697 (0.295) | 0.721 (0.646) | 0.180 (0.194) |
| 8 | 1.944 | 0.73 | 100% | 30.0% | 0.816 (0.785) | 0.600 (0.566) | 0.662 (0.564) | 0.664 (0.285) | 0.714 (0.619) | 0.269 (0.195) |
| 15 | 1.975 | 0.27 | 100% | 100.0% | 0.812 (0.782) | 0.598 (0.548) | 0.649 (0.571) | 0.734 (0.299) | 0.712 (0.607) | 0.281 (0.197) |
| 30 | 2.186 | 0.14 | 100% | 100.0% | 0.817 (0.771) | 0.608 (0.550) | 0.652 (0.553) | 0.751 (0.296) | 0.732 (0.590) | 0.294 (0.194) |
| 50 | 2.589 | 0.04 | 100% | 100.0% | 0.819 (0.760) | 0.596 (0.547) | 0.632 (0.554) | 0.755 (0.280) | 0.740 (0.563) | 0.289 (0.187) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/60; round 1: 6/60; round 3: 6/60; round 8: 6/60; round 15: 6/60; round 30: 6/60; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 1: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 3: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 8: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 15: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 30: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.
Task coverage, round 50: promoter detection (human): gue seed 2, gue seed 1, gue seed 0; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0, yeast seed 1.

## DNABERT 3-mer

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2.840 | 2.88 | 0% | 0.0% | 0.827 (0.773) | 0.628 (0.562) | 0.650 (0.626) | 0.767 (0.258) | 0.721 (0.644) | 0.252 (0.181) |
| 1 | 1.970 | 2.08 | 3% | 0.0% | 0.819 (0.772) | 0.624 (0.588) | 0.653 (0.581) | 0.756 (0.241) | 0.709 (0.648) | 0.238 (0.193) |
| 3 | 1.931 | 2.04 | 0% | 0.0% | 0.826 (0.797) | 0.632 (0.601) | 0.650 (0.576) | 0.756 (0.367) | 0.702 (0.659) | 0.242 (0.222) |
| 8 | 1.922 | 2.04 | 0% | 0.0% | 0.836 (0.810) | 0.642 (0.612) | 0.675 (0.629) | 0.792 (0.421) | 0.694 (0.686) | 0.250 (0.242) |
| 15 | 1.918 | 2.00 | 8% | 0.0% | 0.842 (0.817) | 0.636 (0.613) | 0.647 (0.652) | 0.795 (0.402) | 0.721 (0.706) | 0.259 (0.241) |
| 30 | 1.916 | 1.76 | 52% | 6.0% | 0.845 (0.809) | 0.640 (0.598) | 0.654 (0.635) | 0.794 (0.422) | 0.721 (0.724) | 0.278 (0.260) |
| 50 | 1.948 | 1.14 | 97% | 36.7% | 0.843 (0.806) | 0.636 (0.590) | 0.642 (0.634) | 0.797 (0.398) | 0.714 (0.703) | 0.302 (0.252) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/60; round 1: 6/60; round 3: 5/50; round 8: 5/50; round 15: 5/50; round 30: 5/50; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 1: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 3: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 8: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 15: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 30: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 50: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.

## DNABERT 4-mer

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2.659 | 2.82 | 0% | 0.0% | 0.811 (0.765) | 0.614 (0.568) | 0.663 (0.577) | 0.753 (0.243) | 0.710 (0.660) | 0.239 (0.169) |
| 1 | 2.015 | 2.09 | 0% | 0.0% | 0.808 (0.775) | 0.628 (0.570) | 0.664 (0.605) | 0.736 (0.270) | 0.709 (0.646) | 0.235 (0.207) |
| 3 | 1.936 | 2.05 | 0% | 0.0% | 0.552 (0.794) | 0.621 (0.588) | 0.665 (0.619) | 0.761 (0.361) | 0.722 (0.673) | 0.161 (0.222) |
| 8 | 1.924 | 2.03 | 0% | 0.0% | 0.821 (0.808) | 0.635 (0.608) | 0.658 (0.629) | 0.773 (0.410) | 0.701 (0.707) | 0.248 (0.237) |
| 15 | 1.920 | 1.98 | 4% | 0.0% | 0.821 (0.816) | 0.628 (0.607) | 0.657 (0.639) | 0.779 (0.435) | 0.710 (0.718) | 0.240 (0.250) |
| 30 | 1.926 | 1.61 | 90% | 2.0% | 0.816 (0.814) | 0.639 (0.606) | 0.671 (0.636) | 0.782 (0.430) | 0.719 (0.728) | 0.268 (0.257) |
| 50 | 1.959 | 0.78 | 100% | 50.8% | 0.833 (0.811) | 0.646 (0.610) | 0.680 (0.645) | 0.794 (0.415) | 0.738 (0.731) | 0.290 (0.257) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/60; round 1: 6/60; round 3: 6/60; round 8: 5/50; round 15: 5/50; round 30: 5/50; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1.
Task coverage, round 1: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1.
Task coverage, round 3: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1.
Task coverage, round 8: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 15: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 30: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 50: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2, yeast seed 1.

## DNABERT 5-mer

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3.086 | 3.04 | 0% | 0.0% | 0.845 (0.775) | 0.618 (0.569) | 0.676 (0.630) | 0.763 (0.278) | 0.714 (0.659) | 0.240 (0.198) |
| 1 | 2.078 | 2.24 | 0% | 0.0% | 0.832 (0.769) | 0.627 (0.566) | 0.668 (0.630) | 0.749 (0.286) | 0.695 (0.657) | 0.233 (0.191) |
| 3 | 1.941 | 2.03 | 0% | 0.0% | 0.847 (0.793) | 0.628 (0.596) | 0.670 (0.649) | 0.776 (0.328) | 0.713 (0.669) | 0.231 (0.235) |
| 8 | 1.932 | 2.00 | 0% | 0.0% | 0.838 (0.804) | 0.647 (0.599) | 0.654 (0.632) | 0.765 (0.374) | 0.714 (0.711) | 0.248 (0.254) |
| 15 | 1.928 | 1.93 | 28% | 0.0% | 0.839 (0.814) | 0.637 (0.609) | 0.631 (0.660) | 0.774 (0.410) | 0.724 (0.720) | 0.253 (0.248) |
| 30 | 1.932 | 1.33 | 100% | 10.0% | 0.852 (0.808) | 0.656 (0.609) | 0.638 (0.642) | 0.782 (0.419) | 0.707 (0.728) | 0.259 (0.246) |
| 50 | 1.974 | 0.44 | 100% | 84.2% | 0.853 (0.805) | 0.664 (0.602) | 0.633 (0.639) | 0.775 (0.399) | 0.716 (0.712) | 0.285 (0.248) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/60; round 1: 6/60; round 3: 5/50; round 8: 5/50; round 15: 5/50; round 30: 5/50; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0.
Task coverage, round 1: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0.
Task coverage, round 3: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0.
Task coverage, round 8: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0.
Task coverage, round 15: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0.
Task coverage, round 30: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 0.
Task coverage, round 50: promoter detection (human): gue seed 0, gue seed 2, gue seed 1; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0; histone H3K4me3 (yeast): yeast seed 2, yeast seed 1, yeast seed 0.

## DNABERT 6-mer

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4.581 | 4.73 | 0% | 0.0% | 0.845 (0.751) | 0.643 (0.569) | 0.664 (0.601) | 0.766 (0.257) | 0.711 (0.616) | 0.232 (0.201) |
| 1 | 2.027 | 2.15 | 0% | 0.0% | 0.845 (0.793) | 0.641 (0.588) | 0.627 (0.618) | 0.000 (0.358) | 0.709 (0.675) | 0.241 (0.221) |
| 3 | 1.934 | 1.97 | 8% | 0.0% | 0.860 (0.801) | 0.653 (0.599) | 0.656 (0.639) | 0.782 (0.393) | 0.727 (0.685) | 0.254 (0.232) |
| 8 | 1.922 | 1.94 | 30% | 0.0% | 0.854 (0.813) | 0.654 (0.602) | 0.653 (0.636) | 0.782 (0.409) | 0.717 (0.708) | 0.256 (0.256) |
| 15 | 1.916 | 1.76 | 88% | 0.0% | 0.853 (0.815) | 0.661 (0.609) | 0.660 (0.652) | 0.795 (0.432) | 0.729 (0.704) | 0.246 (0.251) |
| 30 | 1.940 | 0.71 | 100% | 44.0% | 0.857 (0.808) | 0.662 (0.595) | 0.655 (0.637) | 0.803 (0.429) | 0.733 (0.702) | 0.263 (0.242) |
| 50 | 2.027 | 0.25 | 100% | 95.0% | 0.854 (0.796) | 0.658 (0.589) | 0.646 (0.633) | 0.801 (0.410) | 0.728 (0.685) | 0.277 (0.234) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/60; round 1: 6/60; round 3: 6/60; round 8: 5/50; round 15: 5/50; round 30: 5/50; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2.
Task coverage, round 1: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2.
Task coverage, round 3: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2.
Task coverage, round 8: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 15: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 30: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 2.
Task coverage, round 50: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2; histone H3K4me3 (yeast): yeast seed 0, yeast seed 1, yeast seed 2.

## HyenaDNA medium

| round | held-out loss | canary bits/nt | recognised | extracted | promoter detection (human) | core promoter (human) | TF binding (human) | splice sites (human, 3-class) | histone H3 (yeast) | histone H3K4me3 (yeast) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.967 | 2.11 | 2% | 0.0% | 0.804 (0.764) | 0.603 (0.568) | 0.607 (0.626) | 0.668 (0.277) | 0.688 (0.654) | 0.223 (0.223) |
| 1 | 1.918 | 2.03 | 2% | 0.0% | 0.794 (0.779) | 0.605 (0.575) | 0.625 (0.651) | 0.597 (0.282) | 0.697 (0.669) | 0.221 (0.217) |
| 3 | 1.915 | 1.99 | 6% | 0.0% | 0.793 (0.788) | 0.611 (0.587) | 0.607 (0.664) | 0.692 (0.279) | 0.707 (0.679) | 0.225 (0.246) |
| 8 | 1.918 | 0.38 | 100% | 70.0% | 0.799 (0.793) | 0.616 (0.586) | 0.617 (0.635) | 0.724 (0.246) | 0.677 (0.683) | 0.237 (0.231) |
| 15 | 1.949 | 0.24 | 100% | 87.5% | 0.802 (0.792) | 0.618 (0.582) | 0.634 (0.614) | 0.648 (0.227) | 0.701 (0.674) | 0.244 (0.227) |
| 30 | 2.179 | 0.17 | 100% | 83.3% | 0.809 (0.786) | 0.626 (0.582) | 0.640 (0.610) | 0.686 (0.234) | 0.698 (0.656) | 0.246 (0.221) |
| 50 | 2.746 | 0.12 | 100% | 82.5% | 0.808 (0.780) | 0.620 (0.570) | 0.639 (0.638) | 0.720 (0.213) | 0.716 (0.644) | 0.252 (0.228) |

Coverage (unique configurations / 16-copy record evaluations): round 0: 6/120; round 1: 6/120; round 3: 6/120; round 8: 6/120; round 15: 6/120; round 30: 6/120; round 50: 6/120.

Task coverage, round 0: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 1: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 3: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 8: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 15: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 30: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.
Task coverage, round 50: promoter detection (human): gue seed 1, gue seed 0, gue seed 2; core promoter (human): gue seed 0; TF binding (human): gue seed 0; splice sites (human, 3-class): gue seed 0; histone H3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2; histone H3K4me3 (yeast): yeast seed 1, yeast seed 0, yeast seed 2.

## What a practitioner's stopping rule would pick

| model | best held-out loss | canary there | best downstream | canary there | last round | canary there |
|---|---|---|---|---|---|---|
| DNABERT-2 BPE | round 3 (1.943) | 0.0% extracted | round 30 (MCC 0.642) | 100.0% extracted | round 50 | 100.0% extracted |
| DNABERT 3-mer | round 30 (1.916) | 6.0% extracted | round 50 (MCC 0.656) | 36.7% extracted | round 50 | 36.7% extracted |
| DNABERT 4-mer | round 15 (1.920) | 0.0% extracted | round 50 (MCC 0.663) | 50.8% extracted | round 50 | 50.8% extracted |
| DNABERT 5-mer | round 15 (1.928) | 0.0% extracted | round 50 (MCC 0.654) | 84.2% extracted | round 50 | 84.2% extracted |
| DNABERT 6-mer | round 15 (1.916) | 0.0% extracted | round 30 (MCC 0.662) | 44.0% extracted | round 50 | 95.0% extracted |
| HyenaDNA medium | round 3 (1.915) | 0.0% extracted | round 50 (MCC 0.626) | 82.5% extracted | round 50 | 82.5% extracted |
