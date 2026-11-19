"""
Kinship QA: runs every check and prints one summary. Safe to run as often as you like.

    python qa/run_all.py            everything (server scenarios + fuzzer + website tests)
    python qa/run_all.py --quick    fewer random rounds
    python qa/run_all.py --seed 123 replay the exact random run another run printed
    python qa/run_all.py --live     also poke the live website with read-only requests

Nothing here touches your real data: the server checks use a throwaway in-memory database, the
website checks are pure code, and the --live checks only read (and expect to be turned away).
"""
import argparse
import os
import random
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS = os.path.join(ROOT, 'qa', 'scenarios')
GREEN, RED, DIM, END = '\033[32m', '\033[31m', '\033[2m', '\033[0m'
if not sys.stdout.isatty():
    GREEN = RED = DIM = END = ''


def label(name):
    return name[:-3].replace('check_', '').replace('_', ' ')


def run(cmd, cwd, env=None, timeout=900):
    full_env = {**os.environ, **(env or {})}
    started = time.time()
    p = subprocess.run(cmd, cwd=cwd, env=full_env, capture_output=True, text=True, timeout=timeout,
                       encoding='utf-8', errors='replace')
    return p.returncode, (p.stdout or '') + (p.stderr or ''), time.time() - started


def server_script(name, seed, rounds):
    env = {
        'DJANGO_SETTINGS_MODULE': 'qa.settings',
        'PYTHONPATH': ROOT,
        'PYTHONIOENCODING': 'utf-8',
        'QA_SEED': str(seed),
        'QA_ROUNDS': str(rounds),
    }
    code, out, secs = run([sys.executable, os.path.join(SCENARIOS, name)], ROOT, env)
    passed = len(re.findall(r'^PASS ', out, re.M))
    failed = re.findall(r'^FAIL (.*)$', out, re.M)
    ok = code == 0 and not failed
    return ok, passed, failed, out, secs


def web_tests(seed, rounds):
    web = os.path.join(ROOT, 'web')
    npx = shutil.which('npx') or shutil.which('npx.cmd')
    if not npx or not os.path.isdir(os.path.join(web, 'node_modules')):
        return None
    code, out, secs = run([npx, 'vitest', 'run'], web, {'QA_SEED': str(seed), 'QA_ROUNDS': str(rounds)}, 600)
    m = re.search(r'Tests\s+(?:(\d+) failed \| )?(\d+) passed', out)
    failed = int(m.group(1) or 0) if m else 1
    passed = int(m.group(2)) if m else 0
    return code == 0, passed, failed, out, secs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, help='replay a previous random run')
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--no-web', action='store_true')
    ap.add_argument('--verbose', action='store_true', help='show the output of every check')
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 10**9)
    rounds = 150 if args.quick else 600
    print(f'Kinship QA  (random seed {seed}; replay with: python qa/run_all.py --seed {seed})\n')

    results, bad_outputs = [], []
    scripts = sorted(f for f in os.listdir(SCENARIOS) if f.endswith('.py') and not f.startswith('_'))
    for name in scripts:
        ok, passed, failed, out, secs = server_script(name, seed, rounds)
        results.append((label(name), ok, passed, len(failed) or (0 if ok else 1), secs))
        if not ok:
            bad_outputs.append((name, out))
        elif args.verbose:
            print(out)
        print(f'  {GREEN + "PASS" if ok else RED + "FAIL"}{END}  {label(name):<24} {passed:>4} checks  {DIM}{secs:4.1f}s{END}')

    if not args.no_web:
        res = web_tests(seed, rounds)
        if res is None:
            print(f'  {DIM}skip  website tests (run "npm install" in web/ first){END}')
        else:
            ok, passed, failed, out, secs = res
            results.append(('website tests', ok, passed, failed, secs))
            if not ok:
                bad_outputs.append(('website tests', out))
            print(f'  {GREEN + "PASS" if ok else RED + "FAIL"}{END}  {"website tests":<24} {passed:>4} checks  {DIM}{secs:4.1f}s{END}')

    if args.live:
        code, out, secs = run([sys.executable, os.path.join(ROOT, 'qa', 'live_smoke.py')], ROOT, {'PYTHONIOENCODING': 'utf-8'}, 120)
        passed = len(re.findall(r'^PASS ', out, re.M))
        failed = re.findall(r'^FAIL (.*)$', out, re.M)
        ok = code == 0 and not failed
        results.append(('live site', ok, passed, len(failed), secs))
        if not ok:
            bad_outputs.append(('live site', out))
        print(f'  {GREEN + "PASS" if ok else RED + "FAIL"}{END}  {"live site (read-only)":<24} {passed:>4} checks  {DIM}{secs:4.1f}s{END}')

    total = sum(r[2] for r in results)
    failures = [r for r in results if not r[1]]
    print()
    if not failures:
        print(f'{GREEN}All clear: {total} checks passed.{END}')
    else:
        print(f'{RED}{len(failures)} group(s) failed.{END} Details:\n')
        for name, out in bad_outputs:
            lines = [l for l in out.splitlines() if l.startswith(('FAIL', 'Traceback', 'AssertionError', '  File')) or 'Error' in l or 'seed' in l.lower()]
            print(f'--- {name}')
            print('\n'.join(lines[-25:]) or out[-1500:])
        print(f'\nReplay: python qa/run_all.py --seed {seed}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
