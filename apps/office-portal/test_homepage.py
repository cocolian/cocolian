"""HTTP regression checks for the public README and private trial login."""
import os
import secrets
import tempfile
import threading
import unittest
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer

_tmp = tempfile.TemporaryDirectory()
os.environ['OFFICE_DATA_DIR'] = _tmp.name
os.environ.setdefault('LAB_KEY', secrets.token_urlsafe(24))
import server

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None

class HomepageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.worker = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.worker.start()
        cls.base = 'http://127.0.0.1:' + str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.worker.join(); _tmp.cleanup()
    def request(self, path, data=None, headers=None):
        req = urllib.request.Request(self.base+path, data=data, headers=headers or {})
        try: return urllib.request.build_opener(NoRedirect()).open(req)
        except urllib.error.HTTPError as response: return response
    def test_public_readme_and_qr(self):
        with self.request('/') as response:
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            for text in ('国产化文档渲染与云文档中台', '老熊看架构', '关注', '/login', '/community-qrcode.jpg'):
                self.assertIn(text, body)
            self.assertTrue(server.KEY not in body, 'Credential must not be rendered')
        with self.request('/community-qrcode.jpg') as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), Path(server.__file__).with_name('community-qrcode.jpg').read_bytes())
        with self.request('/project-homepage.css') as response: self.assertEqual(response.status, 200)
    def test_login_new_key_and_workspace(self):
        with self.request('/login', urllib.parse.urlencode({'key':server.KEY}).encode()) as response:
            self.assertEqual(response.status, 303)
            self.assertEqual(response.headers['Location'], '/workspace')
            cookie = response.headers['Set-Cookie'].split(';')[0]
        with self.request('/workspace', headers={'Cookie':cookie}) as response:
            self.assertEqual(response.status, 200)
            self.assertIn('文档工作台', response.read().decode())
        with self.request('/auth', headers={'Cookie':cookie}) as response: self.assertEqual(response.status, 204)
    def test_reject_old_credentials_even_with_valid_session(self):
        invalid = secrets.token_urlsafe(24)
        with self.request('/auth', headers={'Cookie':'office_session='+invalid}) as response: self.assertEqual(response.status, 401)
        with self.request('/login', urllib.parse.urlencode({'key':invalid}).encode(), {'Cookie':'office_session='+server.KEY}) as response:
            self.assertEqual(response.status, 401)
        with self.request('/workspace') as response: self.assertEqual(response.status, 303)
    def test_login_form_has_no_credential(self):
        with self.request('/login') as response:
            body = response.read().decode()
            self.assertIn('type="password"', body)
            self.assertTrue(server.KEY not in body, 'Credential must not be rendered')

if __name__ == '__main__': unittest.main()
