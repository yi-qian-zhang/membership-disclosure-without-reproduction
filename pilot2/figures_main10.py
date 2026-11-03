"""Readable main-text figures for the ten-page revision (31 October 2026).

python -m pilot2.figures_main10 --out paper/figures

Reuse the published figure_data.csv, interpolation, seed aggregation and saturation
reader from figures_privacy. Only layout and labeling change. Single-copy
controls are tabulated separately, not reused as sixteen-copy donor-tier
controls. No experiment results are rewritten. Use --figure ident to redraw
Figure 2 alone.
"""
import argparse
from pathlib import Path
from . import figures_privacy as f
import matplotlib.pyplot as plt


def save(fig, out, name):
    # Exact 6.5-inch media box: 10.2 pt fonts stay >=10 pt at manuscript width.
    # Explicitly disable figures_privacy's global tight crop: bbox_inches=None
    # alone inherits savefig.bbox and can silently change the printed font size.
    with plt.rc_context({'savefig.bbox': None}):
        fig.savefig(out / (name + '.pdf'), bbox_inches=None, pad_inches=0)
        fig.savefig(out / (name + '.png'), bbox_inches=None, pad_inches=0, dpi=220)
    plt.close(fig)


def fig_ident(rows, out):
    """Separate endpoints; show controls as exact seed ranges, not stacked zeros."""
    runs = {f'dnabert2bpe_human_s{s}' for s in (0, 1, 2)}
    # Use the existing reader's epoch labels rather than assuming a CSV spelling.
    reference = f._band(rows, 'bpe_human', runs, '1', 'train', 'rank1_rate')
    epochs = sorted(reference, key=lambda e: f.EPOCH_X[e])
    xs = [f.EPOCH_X[e] for e in epochs]
    fig = plt.figure(figsize=(6.5, 3.35))
    grid = fig.add_gridspec(2, 2, left=.115, right=.985, top=.855,
                           bottom=.335, height_ratios=(1.65, 1),
                           hspace=.16, wspace=.18)
    axes = [[fig.add_subplot(grid[r, c]) for c in range(2)] for r in range(2)]

    def curve(ax, tier, host, field, color, label, marker, ls, open_marker=False):
        d = f._band(rows, 'bpe_human', runs, tier, host, field)
        if set(d) != set(epochs):
            raise ValueError('Figure 2 trajectories must share all six checkpoints')
        means = [d[e][0] for e in epochs]
        errors = [[d[e][0] - d[e][1] for e in epochs],
                  [d[e][2] - d[e][0] for e in epochs]]
        return ax.errorbar(xs, means, yerr=errors, color=color, label=label,
                           marker=marker, ms=4.0, mfc='white' if open_marker else color,
                           mew=.8, ls=ls, lw=1.2, elinewidth=.85,
                           capsize=2.2, capthick=.85, zorder=3)

    handles = []
    for c, (tier, title) in enumerate((('1', 'Single copy'), ('16', 'Sixteen copies'))):
        top, bottom = axes[0][c], axes[1][c]
        own = curve(top, tier, 'train', 'rank1_rate', f.C_ID,
                    'Membership: own', 'o', '-')
        fresh = curve(top, tier, 'fresh', 'rank1_rate', f.C_UTIL,
                      'Membership: fresh', 'D', '--', True)
        recovery = curve(bottom, tier, 'train', 'exact_rate', f.C_VERB,
                         'Prefix: own', 's', '-')
        if c == 0:
            handles = [own, fresh, recovery]
        top.axhline(1 / 101, color=f.C_REF, lw=.8, ls=':', zorder=1)
        top.set_title(title, pad=5, fontweight='bold')
        top.tick_params(axis='x', labelbottom=False)
        for ax in (top, bottom):
            ax.set_xlim(5, 160)
            ax.set_ylim(-.065, 1.065)
            ax.set_xticks([15, 50, 100, 150], ['15', '50', '100', 'final'])
            ax.set_yticks([0, .5, 1], ['0', '0.5', '1'])
            ax.tick_params(length=3, pad=3)
            f._style(ax)
            if c:
                ax.tick_params(axis='y', labelleft=False)
        if tier == '1':
            bottom.text(.52, .42, '0/50 in every seed', transform=bottom.transAxes,
                        ha='center', va='center', color=f.C_VERB)
    axes[0][0].set_ylabel('Rank-1 rate', labelpad=5)
    axes[1][0].set_ylabel('Recovery', labelpad=5)
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.55, .995),
               ncol=3, frameon=False, handlelength=1.6, columnspacing=1.2,
               handletextpad=.5)
    fig.text(.54, .245, 'Fine-tuning round', ha='center', va='center')
    fig.text(.54, .185, 'Single-copy controls: rank-1 range over seeds (%)',
             ha='center', va='center')
    table_ax = fig.add_axes([.115, .015, .87, .145])
    table_ax.axis('off')
    cells = [['Window / round'] + [str(f.EPOCH_X[e]) if e != 'final' else 'final'
                                 for e in epochs]]
    for host, label in (('train', 'Borrowed training'), ('fresh', 'Fresh')):
        d = f._band(rows, 'bpe_human', runs, '0', host, 'rank1_rate')
        vals = []
        for e in epochs:
            lo, hi = (round(100 * v) for v in d[e][1:])
            vals.append(str(lo) if lo == hi else f'{lo}\N{EN DASH}{hi}')
        cells.append([label] + vals)
    table = table_ax.table(cellText=cells, cellLoc='center',
                           colWidths=[.29] + [.71 / len(epochs)] * len(epochs),
                           bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10.2)
    for (r, c), cell in table.get_celld().items():
        cell.set_linewidth(0)
        cell.PAD = .035
        if r == 0:
            cell.set_facecolor('#EEF0F3')
        if c == 0:
            cell.get_text().set_ha('left')
    save(fig, out, 'F6_ident')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=Path('paper/figures'))
    ap.add_argument('--figure', choices=('all', 'ident', 'slots'), default='all')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = f.load(Path('results/figure_data.csv'))
    plt.rcParams.update({'font.size': 10.2, 'axes.titlesize': 10.2,
                         'axes.labelsize': 10.2, 'legend.fontsize': 10.2,
                         'xtick.labelsize': 10.2, 'ytick.labelsize': 10.2})

    if args.figure in ('all', 'ident'):
        fig_ident(rows, args.out)
    if args.figure == 'ident':
        return

    main_data, repl = f.matched(rows, 'kcurve300'), f.matched(rows, 'kcurve')
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9))
    fig.subplots_adjust(left=.09, right=.985, top=.91, bottom=.38, wspace=.40)
    ax, bx = axes
    toks = [t for t in f.TOKS if t in main_data]
    x = list(range(len(toks)))
    colors = ['#9CAAB9', '#768EAB', '#4F6B90', '#1E4F8A']
    for ti, target in enumerate(f.TARGETS):
        valid = [(i, main_data[t][0][ti]) for i,t in enumerate(toks)
                 if main_data[t][0][ti] is not None]
        ax.plot([i for i,y in valid], [y for i,y in valid], '-o',
                ms=3.5, lw=1.1, color=colors[ti], label=f'{target:.2f} bits/nt')
    valid = [(i,repl[t][0][-1]) for i,t in enumerate(toks)
             if t in repl and repl[t][0][-1] is not None]
    ax.plot([i for i,y in valid], [y for i,y in valid], 'o', mfc='none',
            mec=f.INK, ms=6, mew=.8, label='288 nt, at 2.40')
    ax.set_title('Matched-loss recovery')
    ax.set_ylabel('Exact recovery')
    ax.set_xticks(x, [f'{i+1}\n{f.SLOTS[t]:g}' for i,t in enumerate(toks)])
    ax.set_xlabel('Token width k / nominal slots', labelpad=2)
    ax.set_ylim(-.04, 1.04); ax.set_yticks([0, .5, 1], ['0', '50%', '100%'])
    ax.annotate('Unreached\nlosses', (0,.1), color=f.C_REF, fontsize=10.2)
    f._style(ax)
    for table, marker, color, fill, label in (
        (main_data, 's', f.C_ID, f.C_ID, '300 nt'),
        (repl, 'o', f.INK, 'none', '288 nt')):
        valid = [(i, table[t][1]) for i,t in enumerate(toks)
                 if t in table and table[t][1] is not None]
        bx.plot([i for i,y in valid], [y for i,y in valid], '-'+marker,
                color=color, mfc=fill, ms=4, lw=1, label=label)
    bx.set_title('Full-recovery loss')
    bx.set_ylabel('Held-out bits/nt')
    bx.set_xticks(x, [str(i+1) for i in x]); bx.set_xlabel('Token width k', labelpad=2)
    bx.set_xlim(-.2,5.3); bx.set_ylim(2.3,4.5)
    bx.set_yticks([2.5,3.5,4.5]); bx.text(0,2.45,'Not reached',color=f.C_REF,fontsize=10.2)
    bx.legend(frameon=False,loc='upper right',handlelength=1.3)
    f._style(bx)
    h,lab=ax.get_legend_handles_labels()
    fig.legend(h,lab,loc='lower center',bbox_to_anchor=(.5,.005),ncol=3,
               frameon=False,handlelength=1.4,columnspacing=1.2,labelspacing=.3)
    save(fig,args.out,'F5_slots')


if __name__ == '__main__':
    main()
