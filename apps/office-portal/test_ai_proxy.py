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

    def test_minimax_separates_reasoning(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,size): return json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'最终正文','reasoning_content':'内部思考'}}]}).encode()
        class Opener:
            def open(self, request, timeout):
                body=json.loads(request.data)
                assert body['reasoning_split'] is True
                assert body['max_completion_tokens']==8192
                assert 'max_tokens' not in body
                return Response()
        with patch.dict(os.environ, {'AI_BASE_URL':'https://api.minimax.io/v1','AI_API_KEY':'test-secret','AI_MODEL':'MiniMax-M3'}), patch('urllib.request.build_opener',return_value=Opener()):
            result=ai_proxy.suggest({'text':'原文','instruction':'润色'})
            self.assertEqual(result['suggestion'],'最终正文')
            self.assertNotIn('内部思考',json.dumps(result,ensure_ascii=False))

    def test_chat_history_and_no_selection(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,size): return json.dumps({'choices':[{'message':{'content':'回答'}}]}).encode()
        class Opener:
            def open(self,request,timeout):
                messages=json.loads(request.data)['messages']
                assert messages[1]=={'role':'user','content':'之前的问题'}
                assert messages[-1]['content']=='继续说明'
                return Response()
        with patch.dict(os.environ,{'AI_BASE_URL':'https://example.invalid/v1','AI_API_KEY':'test','AI_MODEL':'test'}),patch('urllib.request.build_opener',return_value=Opener()):
            self.assertEqual(ai_proxy.suggest({'instruction':'继续说明','history':[{'role':'user','content':'之前的问题'}]},chat=True)['suggestion'],'回答')
        with self.assertRaises(ValueError): ai_proxy.suggest({'instruction':'x','history':[{'role':'system','content':'x'}]},chat=True)

    def test_errors_redacted(self):
        with patch.dict(os.environ, {'AI_BASE_URL':'https://example.invalid/v1','AI_API_KEY':'test-secret','AI_MODEL':'test'}), patch('urllib.request.build_opener',side_effect=RuntimeError('test-secret')):
            with self.assertRaises(ai_proxy.AIError) as error: ai_proxy.suggest({'text':'原文','instruction':'润色'})
            self.assertNotIn('test-secret',str(error.exception))

if __name__=='__main__': unittest.main()
