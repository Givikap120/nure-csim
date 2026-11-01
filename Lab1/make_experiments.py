from pathlib import Path
import xml.etree.ElementTree as E

root = E.Element('experiments')
cases = [('power-plants', [0,4,8,12,16,20]), ('polluting-rate', [0,1,2,3,4,5]), ('planting-rate', [0,.02,.04,.06,.08,.1])]
for index, (parameter, values) in enumerate(cases, 1):
    exp = E.SubElement(root, 'experiment', name=f'experiment-{index}', repetitions='1', runMetricsEveryStep='false')
    E.SubElement(exp, 'setup').text = 'random-seed experiment-seed setup'
    E.SubElement(exp, 'go').text = 'go'
    E.SubElement(exp, 'timeLimit', steps='100')
    E.SubElement(exp, 'exitCondition').text = 'not any? people'
    for metric in ['ticks','count people','count trees','sum [pollution] of patches']:
        E.SubElement(exp, 'metric').text = metric
    fixed = {'initial-population':100,'birth-rate':0.1,'power-plants':10,'polluting-rate':3,'planting-rate':0.05}
    for key, value in fixed.items():
        vs = E.SubElement(exp, 'enumeratedValueSet', variable=key)
        for v in (values if key == parameter else [value]):
            E.SubElement(vs, 'value', value=str(v))
    vs = E.SubElement(exp, 'enumeratedValueSet', variable='experiment-seed')
    for seed in range(1001,1021): E.SubElement(vs, 'value', value=str(seed))
E.indent(root)
Path(__file__).with_name('experiments.xml').write_bytes(E.tostring(root, encoding='utf-8', xml_declaration=False))
original = Path(__file__).with_name('Urban Suite - Pollution.nlogo').read_text()
Path(__file__).with_name('Pollution-experiments.nlogo').write_text('globals [ experiment-seed ]\n' + original)
