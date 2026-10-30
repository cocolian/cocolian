import json
import os
import unittest
from unittest.mock import patch
import ai_proxy

class ProxyTests(unittest.TestCase):
    def test_invalid_payload(self):
        for payload in (None, [], {}, {'text':'a','instruction':2}, {'text':'a'*20001,'instruction':'x'}):
            with self.assertRaises(ValueError): ai_proxy.suggest(payload)

    def test_missing_config(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ai_proxy.AIError): ai_proxy.suggest({'text':'a','instruction':'x'})

    def test_success_and_key_stays_in_header(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,size): return json.dumps({'choices':[{'message':{'content':'修改后'}}]}).encode()
        class Opener:
            def open(self, request, timeout):
                assert request.headers['Authorization']=='Bearer test-secret'
                assert b'test-secret' not in request.data
                return Response()
        with patch.dict(os.environ, {'AI_BASE_URL':'https://example.invalid/v1','AI_API_KEY':'test-secret','AI_MODEL':'test'}), patch('urllib.request.build_opener',return_value=Opener()):
            self.assertEqual(ai_proxy.suggest({'text':'原文','instruction':'润色'})['suggestion'],'修改后')

    def test_errors_redacted(self):
        with patch.dict(os.environ, {'AI_BASE_URL':'https://example.invalid/v1','AI_API_KEY':'test-secret','AI_MODEL':'test'}), patch('urllib.request.build_opener',side_effect=RuntimeError('test-secret')):
            with self.assertRaises(ai_proxy.AIError) as error: ai_proxy.suggest({'text':'原文','instruction':'润色'})
            self.assertNotIn('test-secret',str(error.exception))

if __name__=='__main__': unittest.main()
