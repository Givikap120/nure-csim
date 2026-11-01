from pathlib import Path
import csv, io, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base=Path(__file__).resolve().parent

def read_runs(name):
    lines=(base/f'data/{name}.csv').read_text().splitlines()
    start=next(i for i,line in enumerate(lines) if line.startswith('"[run number]"'))
    return list(csv.DictReader(io.StringIO('\n'.join(lines[start:]))))

metrics={'people':'count people','trees':'count trees','pollution':'sum [pollution] of patches'}
names={'baseline':'Вихідна модель','variant':'Зміни за варіантом','full':'Варіант + самоочищення'}
colors={'baseline':'#596475','variant':'#d07821','full':'#147e83'}
summary=[]
all_rows={}
for scenario in names:
    rows=read_runs(scenario)
    all_rows[scenario]=rows
    assert len(rows)==120
    assert all(float(r['ticks'])==100 for r in rows)
    for value in [0,4,8,12,16,20]:
        group=[r for r in rows if float(r['power-plants'])==value]
        assert sorted(int(r['experiment-seed']) for r in group)==list(range(1001,1021))
        record={'scenario':scenario,'power_plants':value,'runs':len(group)}
        for key,col in metrics.items():
            a=np.array([float(r[col]) for r in group])
            record[key+'_mean']=float(a.mean())
            record[key+'_sd']=float(a.std(ddof=1))
        summary.append(record)

with (base/'data/summary.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
(base/'data/summary.json').write_text(json.dumps(summary,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
for key,ylabel in [('people','Кількість людей на 100-му такті'),('pollution','Сумарне забруднення на 100-му такті, ум. од.')]:
    fig,ax=plt.subplots(figsize=(8.3,5),layout='constrained')
    for scenario in names:
        records=[r for r in summary if r['scenario']==scenario]
        ax.errorbar([r['power_plants'] for r in records], [r[key+'_mean'] for r in records],
                    yerr=[r[key+'_sd'] for r in records],fmt='o-',capsize=4,lw=2,
                    color=colors[scenario],label=names[scenario])
    ax.set(xlabel='Кількість електростанцій',ylabel=ylabel,xticks=[0,4,8,12,16,20])
    ax.set_title('Вплив кількості електростанцій\n20 прогонів на точку; середнє ± стандартне відхилення',fontsize=12)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(alpha=.2)
    ax.legend()
    fig.savefig(base/f'images/{key}.png',dpi=170)
    plt.close(fig)

def fmt(x): return f'{x:.2f}'.replace('.',',')
tables=[]
for key,label in [('people','N(100)'),('pollution','P(100)')]:
    table='| Електростанції | Вихідна модель | Зміни за варіантом | Повна модифікація |\n|---:|---:|---:|---:|\n'
    for n in [0,4,8,12,16,20]:
        values=[]
        for scenario in names:
            r=next(r for r in summary if r['scenario']==scenario and r['power_plants']==n)
            values.append(fmt(r[key+'_mean'])+' ± '+fmt(r[key+'_sd']))
        table+='| '+str(n)+' | '+' | '.join(values)+' |\n'
    tables.append(table)
(base/'data/tables.md').write_text('\n\n'.join(tables))
for r in summary:
    print(r['scenario'],r['power_plants'],f"N={r['people_mean']:.2f}±{r['people_sd']:.2f}; P={r['pollution_mean']:.3f}±{r['pollution_sd']:.3f}; T={r['trees_mean']:.2f}")
print('Summary, tables and figures created from 360 research runs.')
