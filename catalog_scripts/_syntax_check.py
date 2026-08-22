# -*- coding: utf-8 -*-
u"""room.html 内の <script> を全部取り出して node --check にかける (構文検査)"""
import io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = io.open(os.path.join(ROOT, 'room.html'), encoding='utf-8').read()

blocks = re.findall(r'<script([^>]*)>(.*?)</script>', src, re.S)
rc = 0
tmp = tempfile.mkdtemp()
for i, (attrs, body) in enumerate(blocks):
    if 'importmap' in attrs or 'src=' in attrs:
        print('  [skip] block %d (%s)' % (i, attrs.strip() or 'no attrs'))
        continue
    mod = 'type="module"' in attrs or "type='module'" in attrs
    p = os.path.join(tmp, 'b%d.%s' % (i, 'mjs' if mod else 'js'))
    io.open(p, 'w', encoding='utf-8').write(body)
    r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
    print('  [%s] block %d  %s  (%d bytes)' % ('OK ' if r.returncode == 0 else 'NG ', i,
          'module' if mod else 'script', len(body)))
    if r.returncode:
        print(r.stdout); print(r.stderr); rc = 1
sys.exit(rc)
