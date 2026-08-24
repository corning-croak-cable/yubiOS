#!/usr/bin/env python3
"""F4 caustic classification (Zernike program, Slot 2). Recon stage.

Stage 1 (--mode recon): locate the recorded dimension-ladder data
(results/ladder_VD.json) inside papers/is-this-x-2026-08-12-Final.zip and dump
enough of the bundle's own generator/pipeline code to reconstruct the
rank-2 degenerate design configurations faithfully.
"""
import argparse
import json
import os
import zipfile

BUNDLE = os.path.join('papers', 'is-this-x-2026-08-12-Final.zip')


def recon():
    out = {'stage': 'recon', 'bundle': BUNDLE, 'bundle_exists': os.path.exists(BUNDLE)}
    if not out['bundle_exists']:
        print('RESULT_JSON ' + json.dumps(out))
        return
    zf = zipfile.ZipFile(BUNDLE)
    names = zf.namelist()
    out['n_entries'] = len(names)
    print('=== NAMELIST ===')
    for n in names:
        print('ENTRY ' + n)
    ladder = [n for n in names if n.endswith('ladder_VD.json') or n.endswith('ladder-VD.json')]
    out['ladder_candidates'] = ladder
    for n in ladder:
        raw = zf.read(n).decode('utf-8', 'replace')
        print('=== LADDER FILE ' + n + ' (' + str(len(raw)) + ' bytes) ===')
        print(raw)
    wanted = ('common.py', 'create_corpus.py', 'ladder_correlations.py')
    for n in names:
        base = n.split('/')[-1]
        if base in wanted:
            raw = zf.read(n).decode('utf-8', 'replace')
            print('=== SCRIPT ' + n + ' (' + str(len(raw)) + ' bytes) ===')
            print(raw)
    print('RESULT_JSON ' + json.dumps(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='classify')
    args = ap.parse_args()
    if args.mode == 'recon':
        recon()
    else:
        print('RESULT_JSON ' + json.dumps({'stage': 'classify', 'status': 'not_implemented_yet'}))


if __name__ == '__main__':
    main()
