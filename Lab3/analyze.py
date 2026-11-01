from pathlib import Path
import csv,io,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base=Path(__file__).resolve().parent
candidates=json.loads((base/'data/candidates.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})

def csv_rows(path,behavior_space=False):
    lines=path.read_text().splitlines()
    if behavior_space:
        lines=lines[next(i for i,l in enumerate(lines) if l.startswith('"[run number]"')):]
    return list(csv.DictReader(io.StringIO('\n'.join(lines))))

def write_csv(name,rows):
    with (base/'data'/name).open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

search_summary=[]
fig,axes=plt.subplots(1,2,figsize=(11,4.6),layout='constrained',sharey=True)
for ax,method,label in zip(axes,['ga','rs'],['StandardGA','RandomSearch']):
    raw=csv_rows(base/f'data/{method}.modelRunHistory.csv')
    history=csv_rows(base/f'data/{method}.objectiveFunctionHistory.csv')
    assert len(raw)==1500 and len(history)==300
    for i in range(1,4):
        r=[r for r in history if int(r['search-number'])==i]
        assert len(r)==100 and int(r[-1]['evaluation'])==500
        values=[float(x['best-fitness-so-far']) for x in r]
        assert all(b<=a+1e-12 for a,b in zip(values,values[1:]))
        ax.step([float(x['evaluation']) for x in r],values,where='post',lw=1.8,label=f'Пошук {i}')
        c=next(c for c in candidates if c['name']==method+str(i))
        assert abs(values[-1]-c['search_fitness'])<1e-12
        unique=len({(x['initial-population*'],x['birth-rate*'],x['planting-rate*']) for x in r})
        search_summary.append({'method':label,'search':i,'seed':20261021+i,
            'initial_population':c['initial-population'],'birth_rate':c['birth-rate'],'planting_rate':c['planting-rate'],
            'search_fitness':c['search_fitness'],'replicates_in_record':c['search_replicates'],
            'unique_candidates':unique,'model_runs':500})
    ax.set(title=label,xlabel='Витрачені модельні прогони',xlim=(0,500))
    ax.grid(alpha=.2);ax.legend();ax.spines[['top','right']].set_visible(False)
axes[0].set_ylabel('Найменший знайдений fitness')
fig.suptitle('Порівняння пошуку за однакового бюджету',fontsize=14)
fig.savefig(base/'images/search-progress.png',dpi=170);plt.close(fig)
write_csv('search-summary.csv',search_summary)

validation=[]
per_run=[]
for c in candidates:
    rows=csv_rows(base/f'data/validation-{c["name"]}.csv',True)
    assert len(rows)==3030,(c['name'],len(rows))
    seeds=sorted({int(r['validation-seed']) for r in rows})
    assert seeds==list(range(30001,30031))
    sample=[]
    for seed in seeds:
        run=[r for r in rows if int(r['validation-seed'])==seed]
        assert sorted(int(r['ticks']) for r in run)==list(range(101))
        measured=[r for r in run if int(r['ticks'])>=51]
        assert len(measured)==50
        for r in measured:
            n=float(r['count people']);p=float(r['sum [pollution] of patches'])
            assert p>=0
            expected=10 if n==0 else abs(n-100)/100+p/4473+2*c['planting-rate']
            assert abs(float(r['policy-loss'])-expected)<1e-9
        final=next(r for r in run if int(r['ticks'])==100)
        item={'candidate':c['name'],'seed':seed,'loss':float(np.mean([float(r['policy-loss']) for r in measured])),
              'N100':float(final['count people']),
              'mean_pollution':float(np.mean([float(r['sum [pollution] of patches'])/4473 for r in measured])),
              'extinct':int(float(final['count people'])==0)}
        sample.append(item);per_run.append(item)
    scores=np.array([r['loss'] for r in sample])
    validation.append({'candidate':c['name'],'loss_mean':float(scores.mean()),'loss_sd':float(scores.std(ddof=1)),
        'N100_mean':float(np.mean([r['N100'] for r in sample])),
        'mean_pollution':float(np.mean([r['mean_pollution'] for r in sample])),
        'extinctions':sum(r['extinct'] for r in sample),'runs':30})
write_csv('validation-summary.csv',validation);write_csv('validation-per-run.csv',per_run)

selected={method:min((c for c in candidates if c['method']==method),key=lambda c:c['search_fitness']) for method in ['ga','rs']}
(base/'data/selected.json').write_text(json.dumps(selected,indent=2))
fig,axes=plt.subplots(1,2,figsize=(10,5.2),layout='constrained',gridspec_kw={'width_ratios':[3,1]})
for i,r in enumerate(validation):
    ax=axes[0] if i<6 else axes[1]
    x=i if i<6 else 0
    color='#b3b8bf' if r['candidate']=='control' else ('#3770b2' if r['candidate'].startswith('ga') else '#d47b31')
    ax.errorbar(x,r['loss_mean'],yerr=r['loss_sd'],fmt='o',capsize=6,color=color,markersize=8,lw=2)
axes[0].set(xticks=range(6),xticklabels=['ГА 1','ГА 2','ГА 3','ВП 1','ВП 2','ВП 3'],ylabel='Fitness на нових прогонах',title='Фінальні кандидати')
axes[1].set(xticks=[0],xticklabels=['Контроль'],ylabel='Fitness на нових прогонах',title='Контроль')
for ax in axes:
    ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('30 прогонів для кожного рішення; середнє ± стандартне відхилення\nВертикальні шкали панелей різні',fontsize=12)
fig.savefig(base/'images/validation.png',dpi=170);plt.close(fig)

def fmt(x,n=4):return f'{x:.{n}f}'.replace('.',',')
table='| Метод | Пошук | Початкове населення | birth-rate | planting-rate | Найкращий fitness | Повторень в оцінці | Різних кандидатів |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for r in search_summary:
    table+=f"| {r['method']} | {r['search']} | {r['initial_population']:.0f} | {fmt(r['birth_rate'],3)} | {fmt(r['planting_rate'],3)} | {fmt(r['search_fitness'])} | {r['replicates_in_record']} | {r['unique_candidates']} |\n"
vtable='| Рішення | Fitness, середнє ± s | Середнє N(100) | Середнє забруднення клітини, такти 51–100 | Вимирання до 100-го такту |\n|---|---:|---:|---:|---:|\n'
for r in validation:
    label=r['candidate'].upper() if r['candidate']!='control' else 'Контроль'
    vtable+=f"| {label} | {fmt(r['loss_mean'])} ± {fmt(r['loss_sd'])} | {fmt(r['N100_mean'],2)} | {fmt(r['mean_pollution'])} | {r['extinctions']}/30 |\n"
(base/'data/tables.md').write_text(table + '\n\n' + vtable)
print('Search and validation summaries, tables and figures updated.')
