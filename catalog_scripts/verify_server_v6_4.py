# -*- coding: utf-8 -*-
"""
v6.4 検証用の静的サーバ + 画像保存エンドポイント。

  GET  /<path>          … aritomo-memo 配下を配信 (room.html?debug=1 を開くため)
  POST /__save?name=x   … body (data:image/jpeg;base64,...) を Box の確認用切り出しへ保存

room.html は ES module + importmap なので file:// では動かない。http で配信する。
"""
import base64
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(
    os.path.expanduser('~'), 'Box', 'DIK & Company', '06_Other',
    '野沢用', 'claude', 'nozaROOM', '確認用切り出し')


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        SimpleHTTPRequestHandler.__init__(self, *a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != '/__save':
            self.send_error(404)
            return
        name = (parse_qs(u.query).get('name') or ['shot'])[0]
        name = ''.join(ch for ch in name if ch.isalnum() or ch in '_-.')
        if not name.lower().endswith('.jpg'):
            name += '.jpg'
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n).decode('ascii', 'ignore')
        if ',' in body:
            body = body.split(',', 1)[1]
        raw = base64.b64decode(body)
        if not os.path.isdir(OUT):
            os.makedirs(OUT)
        p = os.path.join(OUT, name)
        with open(p, 'wb') as f:
            f.write(raw)
        msg = ('%s %d bytes' % (p, len(raw))).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)
        sys.stderr.write('saved %s (%d bytes)\n' % (p, len(raw)))
        sys.stderr.flush()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    print('serving %s on 127.0.0.1:%d  (save -> %s)' % (ROOT, port, OUT))
    sys.stdout.flush()
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
