from pathlib import Path
import csv, io, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
labels = ['Кількість електростанцій', 'Рівень забруднення електростанції', 'Ймовірність посадки дерева за такт']
parameters = ['power-plants', 'polluting-rate', 'planting-rate']
summary = []
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11})
for i, parameter in enumerate(parameters, 1):
    text = (base / f'data/experiment-{i}.csv').read_text()
    lines = text.splitlines()
    start = next(j for j,line in enumerate(lines) if line.startswith('"[run number]"'))
    rows = list(csv.DictReader(io.StringIO('\n'.join(lines[start:]))))
    assert len(rows) == 120, (i, len(rows))
    assert all(float(r['ticks']) == 100 for r in rows), 'Early extinction: revise analysis'
    records = []
    for value in sorted({float(r[parameter]) for r in rows}):
        group = [r for r in rows if float(r[parameter]) == value]
        assert len(group) == 20
        record = {'experiment':i, 'parameter':parameter, 'value':value, 'runs':len(group)}
        for key,col in [('people','count people'), ('trees','count trees'), ('pollution','sum [pollution] of patches')]:
            a = np.array([float(r[col]) for r in group])
            record[key+'_mean'] = float(a.mean())
            record[key+'_sd'] = float(a.std(ddof=1))
        records.append(record)
    summary.extend(records)
    fig, axes = plt.subplots(1,2,figsize=(11.5,4.3), layout='constrained')
    for ax,key,title,color in zip(axes,['pollution','people'],['Сумарне забруднення, умовні одиниці','Чисельність людей, осіб'],['#c54c37','#276a97']):
        ax.errorbar([r['value'] for r in records], [r[key+'_mean'] for r in records], yerr=[r[key+'_sd'] for r in records], fmt='o-', color=color, capsize=5, lw=2)
        ax.set(xlabel=labels[i-1], ylabel=title)
        ax.set_xticks([r['value'] for r in records])
        ax.grid(alpha=.2)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle(f'Експеримент {i} • стан на 100-му такті\nСереднє за 20 прогонами; відрізки — ±1 стандартне відхилення', fontsize=12)
    fig.savefig(base / f'images/experiment-{i}.png', dpi=160)
    plt.close(fig)
with (base/'data/summary.csv').open('w') as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
(base/'data/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
for i in range(1,4):
    print('\nEXPERIMENT',i)
    for r in summary:
        if r['experiment']==i: print(f"{r['value']:g}: pollution {r['pollution_mean']:.2f} ± {r['pollution_sd']:.2f}; people {r['people_mean']:.2f} ± {r['people_sd']:.2f}; trees {r['trees_mean']:.2f}")
