"""Make independent NetLogo validation experiments from BehaviorSearch results."""
from pathlib import Path
import csv, json
import xml.etree.ElementTree as E

base=Path(__file__).resolve().parent
candidates=[]
params=['initial-population','birth-rate','planting-rate','power-plants','polluting-rate']
for method in ['ga','rs']:
    with (base/f'data/{method}.finalBests.csv').open() as f:
        for row in csv.DictReader(f):
            c={'name':method+row['search-number'],'method':method,'search':int(row['search-number']),
               'search_fitness':float(row['best-fitness-so-far']),
               'search_replicates':int(row['num-replicates'])}
            c.update({p:float(row[p+'*']) for p in params})
            candidates.append(c)
candidates.append({'name':'control','method':'control','search':0,'search_fitness':None,
                   'initial-population':100,'birth-rate':.1,'planting-rate':.05,'power-plants':10,'polluting-rate':3})
(base/'data/candidates.json').write_text(json.dumps(candidates,indent=2))
root=E.Element('experiments')
for c in candidates:
    e=E.SubElement(root,'experiment',name=c['name'],repetitions='1',runMetricsEveryStep='true')
    E.SubElement(e,'setup').text='let saved-seed validation-seed random-seed saved-seed setup set validation-seed saved-seed'
    E.SubElement(e,'go').text='search-step'
    E.SubElement(e,'final').text=f'if validation-seed = 30001 [ export-view "images/model-{c["name"]}.png" ]'
    E.SubElement(e,'timeLimit',steps='100')
    for m in ['ticks','count people','count trees','sum [pollution] of patches','policy-loss']:
        E.SubElement(e,'metric').text=m
    for p in params:
        vs=E.SubElement(e,'enumeratedValueSet',variable=p)
        E.SubElement(vs,'value',value=str(c[p]))
    vs=E.SubElement(e,'enumeratedValueSet',variable='validation-seed')
    for seed in range(30001,30031): E.SubElement(vs,'value',value=str(seed))
E.indent(root)
(base/'validation.xml').write_bytes(E.tostring(root,encoding='utf-8'))
print('Created 7 validation scenarios, 30 runs each.')
