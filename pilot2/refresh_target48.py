"""Refresh only BPE endpoint columns of the published CSV, preserving run selection.

python -m pilot2.refresh_target48 --root outputs --csv results/figure_data.csv
Historical score files are read-only. Ranking and held-out columns never change.
"""
import argparse,csv,json,math,re
from pathlib import Path
from statistics import mean,variance
from . import export_figure_data as exporter
from .target48 import target48

def wilson(k,n):
    z=1.959963984540054; p=k/n; den=1+z*z/n
    c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [c-h,c+h]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('outputs'))
    ap.add_argument('--csv',type=Path,default=Path('results/figure_data.csv'))
    ap.add_argument('--audit',type=Path,default=Path('results/target48_audit.json'))
    a=ap.parse_args()
    with a.csv.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
    if 'evaluation_endpoint' not in fields:fields.append('evaluation_endpoint')
    for r in rows:r.setdefault('evaluation_endpoint','hidden48')
    changes=[]; legacy_rows=[]; runs=sorted({(r['group'],r['run']) for r in rows if r['run'].startswith('dnabert2bpe')})
    for group,run in runs:
        d=a.root/group/run; meta=exporter._meta(d)
        normal=list(exporter._rows(d,meta,group))
        exporter.target48=lambda x:x
        raw=list(exporter._rows(d,meta,group));exporter.target48=target48
        key=lambda r:(str(r['epoch']),str(r['tier']),r['host'])
        lookup={key(r):r for r in normal}; old={key(r):r for r in raw}
        for r in rows:
            if (r['group'],r['run'])!=(group,run):continue
            k=key(r)
            if k not in lookup:raise ValueError(f'Missing original source: {group}/{run}/{k}')
            r['evaluation_endpoint']=lookup[k]['evaluation_endpoint']
            if r['evaluation_endpoint']=='legacy_variable':legacy_rows.append(dict(group=group,run=run,epoch=k[0],tier=k[1],host=k[2]))
            for col in ('exact_rate','mean_hamming_nt'):
                original=float(r[col]); legacy=float(old[k][col]); new=float(lookup[k][col])
                if abs(original-legacy)>1e-6 and abs(original-new)>1e-6:
                    raise ValueError(f'Published/source mismatch {group}/{run}/{k}/{col}: {original}/{legacy}')
                if abs(original-new)>1e-9:
                    changes.append(dict(group=group,run=run,epoch=k[0],tier=k[1],host=k[2],column=col,old=original,new=new))
                    r[col]=str(lookup[k][col])
    # Detailed chromosome22 statistics follow the same _rb > original source policy.
    cells=[]; gaps=[]
    for seed in range(3):
        d=a.root/'bpe_human'/f'dnabert2bpe_human_s{seed}'
        for tag in ('ep15','ep30','ep50','ep80','ep120','final'):
            f=d/f'scores_{tag}_rb.json'
            if not f.exists():f=d/f'scores_{tag}.json'
            doc=json.loads(f.read_text()); samples={}
            for tier in (0,1,4,16):
                for host in ('train','fresh'):
                    ps=[p for p in doc['probes'] if p['repetitions']==tier and host in p['extract']]
                    if not ps:continue
                    es=[target48(p['extract'][host]) for p in ps]; hs=[e['hamming_nt'] for e in es]
                    n=len(es); k=sum(e['exact'] for e in es); samples[tier,host]=hs
                    cells.append(dict(seed=seed,checkpoint=tag,tier=tier,host=host,source=str(f),n=n,
                        exact_count=k,exact_rate=k/n,wilson95=wilson(k,n),
                        hamming_mean=mean(hs),hamming_sd=math.sqrt(variance(hs)),
                        hamming_se=math.sqrt(variance(hs)/n)))
            x,y=samples[1,'fresh'],samples[0,'fresh']
            se=math.sqrt(variance(x)/len(x)+variance(y)/len(y));gap=mean(y)-mean(x)
            gaps.append(dict(seed=seed,checkpoint=tag,control_minus_member=gap,
                unpaired_descriptive_se=se,gap_over_se=gap/se))
    a.csv.write_text('',encoding='utf-8',newline='\n')
    with a.csv.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    a.audit.write_text(json.dumps(dict(endpoint='hidden48',generation_protocol='unchanged boundary-aligned prefix',
        note='Within-cell SE and Wilson intervals are descriptive; no pooling across repeated checkpoints/seeds.',
        changed_columns=changes,legacy_rows_without_strings=legacy_rows,chromosome22_cells=cells,fresh_single_copy_gaps=gaps),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(runs=len(runs),changes=len(changes),exact_changes=[c for c in changes if c['column']=='exact_rate'],
        gap_over_se_range=[min(g['gap_over_se'] for g in gaps),max(g['gap_over_se'] for g in gaps)]),indent=2))
if __name__=='__main__':main()
