#!/usr/bin/env python3
import json, glob, sys, statistics
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
for f in sorted(glob.glob(sys.argv[1])):
    d = json.load(open(f))
    rows.append({'seed': find(d, 'seed'), 'amp': find(d, 'amplitude_s'), 'identity_J': find(d, 'identity_J'), 'best_J': find(d, 'best_J'), 'delta': find(d, 'delta_J_sd'), 'H1': find(d, 'H1_supported'), 'rej': find(d, 'guard_rejections')})
rows.sort(key=lambda r: (r['amp'] if r['amp'] is not None else 0, r['delta']))
print('TAB_BEGIN')
for r in rows:
    print('ROW amp=%s seed=%s identity_J=%.4f best_J=%.4f delta_J_sd=%+.4f H1=%s rej=%s' % (r['amp'], r['seed'], r['identity_J'], r['best_J'], r['delta'], r['H1'], r['rej']))
amps = sorted(set(r['amp'] for r in rows if r['amp'] is not None))
if len(amps) > 1:
    for a in amps:
        vs = [r['delta'] for r in rows if r['amp'] == a]
        np_ = sum(1 for r in rows if r['amp'] == a and r['H1'])
        print('AMP %-5s n=%d min=%+.3f max=%+.3f median=%+.3f H1=%d/%d' % (a, len(vs), min(vs), max(vs), statistics.median(vs), np_, len(vs)))
vals = [r['delta'] for r in rows]
print('RANGE min=%+.4f max=%+.4f median=%+.4f H1_FRACTION %d/%d' % (min(vals), max(vals), statistics.median(vals), sum(1 for r in rows if r['H1']), len(rows)))
print('TAB_END')
