#!/usr/bin/env python3
import json, glob, statistics
def find(d, key):
    if isinstance(d, dict):
        if key in d: return d[key]
        for v in d.values():
            r = find(v, key)
            if r is not None: return r
    elif isinstance(d, list):
        for v in d:
            r = find(v, key)
            if r is not None: return r
    return None
rows = []
for f in sorted(glob.glob('/tmp/g_*.json')):
    d = json.load(open(f))
    rows.append({'seed': find(d, 'seed'), 'identity_J': find(d, 'identity_J'), 'best_J': find(d, 'best_J'), 'delta_J_sd': find(d, 'delta_J_sd'), 'H1': find(d, 'H1_supported'), 'guard_rej': find(d, 'guard_rejections')})
rows.sort(key=lambda r: r['delta_J_sd'])
print('SWEEP_TABLE_BEGIN')
for r in rows:
    bj = ('%.4f' % r['best_J']) if r['best_J'] is not None else 'NA'
    print('SEED %8s identity_J=%.4f best_J=%s delta_J_sd=%+.4f H1=%s guard_rej=%s' % (r['seed'], r['identity_J'], bj, r['delta_J_sd'], r['H1'], r['guard_rej']))
vals = [r['delta_J_sd'] for r in rows]
n_pass = sum(1 for r in rows if r['H1'])
print('RANGE min=%+.4f max=%+.4f median=%+.4f mean=%+.4f sd=%.4f' % (min(vals), max(vals), statistics.median(vals), statistics.mean(vals), statistics.stdev(vals)))
print('H1_FRACTION %d/%d clear the 2-sigma bar' % (n_pass, len(rows)))
print('SWEEP_TABLE_END')
