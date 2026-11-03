"""Print-size-consistent main figures, using the published measurements unchanged.

python -m pilot2.figures_main10 --out paper/figures

Figure 2: separate endpoints, seed min--max segments, single-copy controls.
Figure 3: matched-loss means, grouped full-recovery points, replication table.
"""
import argparse
import json
from pathlib import Path
from . import figures_privacy as f
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

FONT = 10.2
MARKER = 4.6
EDGE = 1.0
LINE = 1.25
GRAY = '#7C8CA3'
BLUE = '#1E4F8A'
TEAL = '#3B8686'
ORANGE = '#C2410C'
AUDIT = {}


def style(ax):
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color('#526071')
        ax.spines[side].set_linewidth(.65)
    ax.tick_params(length=3, width=.65, pad=3, colors='#263340')
    ax.grid(axis='y', color='#DCE2E8', lw=.45)
    ax.set_axisbelow(True)


def trajectory(ax, x, y, color, label, key, ls='-', ranges=None):
    """Fixed-size circles cover lines; capless ranges remain visible inside them."""
    x, y = list(x), list(y)
    if ranges is not None:
        lo, hi = map(list, ranges)
    ax.plot(x, y, color=color, ls=ls, lw=LINE, zorder=3)
    ax.plot(x, y, ls='none', marker='o', ms=MARKER, mfc='white',
            mec=color, mew=EDGE, zorder=5)
    if ranges is not None:
        ax.vlines(x, lo, hi, color=color, linewidth=.65, zorder=6)
    AUDIT[key] = dict(x=x, y=y, color=color, linestyle=ls,
                      marker='o', marker_size_pt=MARKER, marker_edge_pt=EDGE,
                      marker_face='white')
    if ranges is not None:
        AUDIT[key].update(seed_min=lo, seed_max=hi)
    return Line2D([], [], color=color, ls=ls, lw=LINE, marker='o',
                  ms=MARKER, mfc='white', mec=color, mew=EDGE, label=label)


def table_panel(fig, bounds, cells, widths):
    ax = fig.add_axes(bounds)
    ax.axis('off')
    tab = ax.table(cellText=cells, cellLoc='center', colWidths=widths, bbox=[0,0,1,1])
    tab.auto_set_font_size(False)
    tab.set_fontsize(FONT)
    for (row, col), cell in tab.get_celld().items():
        cell.set_linewidth(0)
        cell.PAD=.04
        if row==0:
            cell.set_facecolor('#EEF0F3')
        if col==0:
            cell.get_text().set_ha('left')
    return tab


def save(fig, out, name):
    # Preserve the exact 6.5-inch media box and embedded vector text.
    with plt.rc_context({'savefig.bbox': None}):
        fig.savefig(out/(name+'.pdf'), bbox_inches=None, pad_inches=0)
        fig.savefig(out/(name+'.png'), bbox_inches=None, pad_inches=0, dpi=300)
    plt.close(fig)


def fig_ident(rows, out):
    runs={f'dnabert2bpe_human_s{s}' for s in (0,1,2)}
    reference=f._band(rows,'bpe_human',runs,'1','train','rank1_rate')
    epochs=sorted(reference,key=lambda e:f.EPOCH_X[e]);xs=[f.EPOCH_X[e] for e in epochs]
    labels=[str(f.EPOCH_X[e]) if e!='final' else 'final' for e in epochs]
    fig=plt.figure(figsize=(6.5,3.5))
    grid=fig.add_gridspec(2,2,left=.11,right=.985,top=.84,bottom=.34,
                         height_ratios=(1.65,1),hspace=.20,wspace=.18)
    axes=[[fig.add_subplot(grid[r,c]) for c in range(2)] for r in range(2)]
    handles=[]
    for col,(tier,title) in enumerate([('1','(a) Single copy'),('16','(b) Sixteen copies')]):
        top,bottom=axes[0][col],axes[1][col]
        for ax,host,field,color,label,ls in [
            (top,'train','rank1_rate',ORANGE,'Membership: own','-'),
            (top,'fresh','rank1_rate',BLUE,'Membership: fresh','--'),
            (bottom,'train','exact_rate',TEAL,'Prefix: own','-')]:
            band=f._band(rows,'bpe_human',runs,tier,host,field)
            if set(band)!=set(epochs):raise ValueError('Six checkpoints required in each trajectory')
            handle=trajectory(ax,xs,[band[e][0] for e in epochs],color,label,
                f'F2/{tier}/{host}/{field}',ls,
                ([band[e][1] for e in epochs],[band[e][2] for e in epochs]))
            if col==0:handles.append(handle)
        top.set_title(title,fontweight='bold',pad=6)
        top.axhline(1/101,color=GRAY,lw=.8,ls=':',zorder=1)
        for ax in (top,bottom):
            style(ax);ax.set_xlim(5,160);ax.set_ylim(-.065,1.065)
            ax.set_xticks(xs,labels);ax.set_yticks([0,.5,1],['0','0.5','1'])
            if col:ax.tick_params(axis='y',labelleft=False)
        top.tick_params(axis='x',labelbottom=False)
        if tier=='1':bottom.text(.52,.46,'0/50 in every seed',transform=bottom.transAxes,
                                ha='center',va='center',color=TEAL)
    axes[0][0].set_ylabel('Rank-1 rate',labelpad=5)
    axes[1][0].set_ylabel('Recovery',labelpad=5)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,1.0),ncol=3,
               frameon=False,handlelength=1.45,handletextpad=.4,columnspacing=1.05)
    fig.text(.55,.25,'Fine-tuning round',ha='center',va='center')
    fig.text(.55,.185,'Single-copy controls: seed range (%)',ha='center',va='center')
    cells=[['Window / round']+labels]
    for host,label in [('train','Borrowed training'),('fresh','Fresh')]:
        band=f._band(rows,'bpe_human',runs,'0',host,'rank1_rate');vals=[]
        for e in epochs:
            lo,hi=[round(100*v) for v in band[e][1:]]
            vals.append(str(lo) if lo==hi else f'{lo}–{hi}')
        cells.append([label]+vals)
    table_panel(fig,[.11,.015,.875,.14],cells,[.29]+[.71/len(epochs)]*len(epochs))
    AUDIT['F2/control_table']=cells
    save(fig,out,'F6_ident')


def fig_slots(rows,out):
    main,repl=f.matched(rows,'kcurve300'),f.matched(rows,'kcurve')
    toks=[t for t in f.TOKS if t in main];x=list(range(len(toks)))
    fig,(ax,bx)=plt.subplots(1,2,figsize=(6.5,3.6))
    fig.subplots_adjust(left=.12,right=.985,top=.77,bottom=.36,wspace=.34)
    handles=[]
    for ti,(target,color,ls) in enumerate(zip(f.TARGETS,[GRAY,BLUE,TEAL,ORANGE],[':', '--','-.','-'])):
        valid=[(i,main[t][0][ti]) for i,t in enumerate(toks) if main[t][0][ti] is not None]
        handles.append(trajectory(ax,[i for i,y in valid],[y for i,y in valid],color,
                                  f'{target:.2f}',f'F3/matched/{target:.2f}',ls))
    ax.set_title('(a) Matched-loss recovery',fontweight='bold',pad=6)
    ax.set_ylabel('Exact recovery',labelpad=5)
    ax.set_xticks(x,[f'{i+1}\n{f.SLOTS[t]:g}' for i,t in enumerate(toks)])
    ax.set_xlabel('k / nominal slots',labelpad=3)
    ax.set_ylim(-.065,1.065);ax.set_yticks([0,.5,1],['0%','50%','100%']);ax.set_xlim(-.3,5.3)
    ax.text(0,.22,'Not\nreached',ha='left',color=GRAY)
    cost_handles=[]
    for table,color,label,offset,ls in [(main,ORANGE,'300 nt',-.12,'-'),(repl,BLUE,'288 nt',.12,'--')]:
        valid=[(i,table[t][1]) for i,t in enumerate(toks) if t in table and table[t][1] is not None]
        cost_handles.append(trajectory(bx,[i+offset for i,y in valid],[y for i,y in valid],
                            color,label,f'F3/full/{label}',ls))
        AUDIT[f'F3/full/{label}']['display_offset']=offset
        AUDIT[f'F3/full/{label}']['token_widths']=[i+1 for i,y in valid]
    bx.set_title('(b) Full-recovery loss',fontweight='bold',pad=6)
    bx.set_ylabel('Held-out bits/nt',labelpad=5);bx.set_xticks(x,[str(i+1) for i in x])
    bx.set_xlabel('Token width k',labelpad=3);bx.set_xlim(-.3,5.3);bx.set_ylim(2.3,4.5)
    bx.set_yticks([2.5,3.5,4.5]);bx.text(0,2.58,'Not reached',ha='left',color=GRAY)
    for a in (ax,bx):style(a)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.295,1.005),ncol=4,
               title='Held-out loss (bits/nt)',frameon=False,handlelength=1.1,
               handletextpad=.35,columnspacing=.65,title_fontsize=FONT)
    fig.legend(handles=cost_handles,loc='upper center',bbox_to_anchor=(.79,.97),ncol=2,
               frameon=False,handlelength=1.25,handletextpad=.4,columnspacing=.8)
    # Separating this replication avoids near-coincident hollow/filled markers.
    shared=[t for t in toks if t in repl and main[t][0][-1] is not None and repl[t][0][-1] is not None]
    cells=[['Host window / k']+[str(f.TOKS.index(t)+1) for t in shared]]
    for data,label in [(main,'300 nt'),(repl,'288 nt')]:
        cells.append([label]+[f'{100*data[t][0][-1]:.0f}%' for t in shared])
    fig.text(.55,.18,'Replication at 2.40 bits/nt: exact recovery',ha='center',va='center')
    table_panel(fig,[.11,.015,.875,.13],cells,[.32]+[.68/len(shared)]*len(shared))
    AUDIT['F3/replication_table']=cells
    AUDIT['F3/replication_exact']={label:{t:data[t][0][-1] for t in shared}
                                  for data,label in [(main,'300 nt'),(repl,'288 nt')]}
    save(fig,out,'F5_slots')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path('paper/figures'))
    ap.add_argument('--figure',choices=('all','ident','slots'),default='all')
    ap.add_argument('--audit',type=Path)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
        'font.size':FONT,'axes.titlesize':FONT,'axes.labelsize':FONT,'legend.fontsize':FONT,
        'xtick.labelsize':FONT,'ytick.labelsize':FONT,'pdf.fonttype':42,'svg.fonttype':'none'})
    rows=f.load(Path('results/figure_data.csv'))
    if args.figure in ('all','ident'):fig_ident(rows,args.out)
    if args.figure in ('all','slots'):fig_slots(rows,args.out)
    if args.audit:
        args.audit.parent.mkdir(parents=True,exist_ok=True)
        args.audit.write_text(json.dumps(AUDIT,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
