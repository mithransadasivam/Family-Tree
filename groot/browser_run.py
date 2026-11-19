"""
Groot's browser tests: opens the real Kinship website in a real (headless) browser and uses it like a
person would, on a throwaway copy of the server that exists only on this computer.

  * a fresh build of the website is made from the current source
  * a temporary server + database starts on 127.0.0.1 (nothing from the live site is used)
  * dummy accounts and a dummy "Groot Test Family" are created through the screens
  * when it finishes, the server and the whole database are deleted, so nothing is ever visible anywhere

Run alone:  python groot/browser_run.py   (screenshots land in groot/reports/)
"""
import glob
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'web')
BROWSERS = [
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
]


def find_browser():
    return os.environ.get('GROOT_BROWSER') or next((b for b in BROWSERS if os.path.exists(b)), None)


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def main():
    npx = shutil.which('npx') or shutil.which('npx.cmd')
    node = shutil.which('node')
    browser = find_browser()
    if not (npx and node and os.path.isdir(os.path.join(WEB, 'node_modules', 'playwright-core'))):
        print('SKIP browser tests need Node and "npm install" in web/')
        return 0
    if not browser:
        print('SKIP browser tests need Microsoft Edge or Google Chrome installed')
        return 0

    for old in glob.glob(os.path.join(tempfile.gettempdir(), 'groot_*')):  # leftovers from an interrupted run
        shutil.rmtree(old, ignore_errors=True)
    work = tempfile.mkdtemp(prefix='groot_')
    server = None
    log = None
    try:
        site = os.path.join(work, 'site')
        build = subprocess.run([npx, 'vite', 'build', '--outDir', site, '--emptyOutDir'], cwd=WEB, capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
        if build.returncode != 0:
            print('FAIL the website did not build\n' + (build.stdout + build.stderr)[-800:])
            return 1
        port = free_port()
        url = f'http://127.0.0.1:{port}'
        tokens = os.path.join(work, 'tokens.json')
        reports = os.path.join(ROOT, 'groot', 'reports')
        shutil.rmtree(reports, ignore_errors=True)
        os.makedirs(reports, exist_ok=True)
        env = {**os.environ, 'GROOT_DB': os.path.join(work, 'groot.sqlite3'), 'GROOT_WEBAPP': site, 'GROOT_URL': url,
               'PYTHONPATH': ROOT, 'PYTHONIOENCODING': 'utf-8', 'DJANGO_SETTINGS_MODULE': 'groot.browser_settings'}
        log = open(os.path.join(work, 'server.log'), 'w', encoding='utf-8')
        server = subprocess.Popen([sys.executable, os.path.join(ROOT, 'groot', 'browser', 'serve.py'), str(port), tokens],
                                  cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(120):
            time.sleep(0.5)
            if server.poll() is not None:
                print('FAIL the test server stopped\n' + open(os.path.join(work, 'server.log'), encoding='utf-8').read()[-1500:])
                return 1
            try:
                urllib.request.urlopen(url + '/api/relationship-types/', timeout=2)
            except urllib.error.HTTPError:
                break  # 401 = it is up and refusing anonymous visitors, which is right
            except Exception:  # noqa: BLE001
                continue
        else:
            print('FAIL the test server did not start')
            return 1
        flows_env = {**os.environ, 'GROOT_URL': url, 'GROOT_TOKENS': tokens, 'GROOT_REPORTS': reports, 'GROOT_BROWSER': browser}
        code = subprocess.run([node, os.path.join(ROOT, 'groot', 'browser', 'flows.mjs')], cwd=ROOT, env=flows_env).returncode
        return code
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(10)
            except subprocess.TimeoutExpired:
                server.kill()
        if log:
            log.close()
        for _ in range(10):  # Windows can hold a file for a moment after its program exits
            shutil.rmtree(work, ignore_errors=True)
            if not os.path.exists(work):
                break
            time.sleep(0.5)  # the dummy data is gone for good


if __name__ == '__main__':
    sys.exit(main())
