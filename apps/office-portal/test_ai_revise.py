import json
import unittest
from unittest.mock import patch
import ai_proxy

class RevisionPlanTests(unittest.TestCase):
    def payload(self):
        return {'blocks':[{'id':'b0','text':'The budget is 100 yuan.'}], 'comments':[{'id':'1','text':'改成200元','block_ids':['b0']}], 'instruction':'保留单位', 'context':'文档预算说明'}

    def result(self, **changes):
        edit={'block_id':'b0','before':'100','after':'200','comment_ids':['1']};edit.update(changes)
        return json.dumps({'summary':'修改预算','edits':[edit],'warnings':[]})

    def test_prompt_combines_source_anchors_comments_and_instruction(self):
        def complete(messages):
            payload=json.loads(messages[1]['content'])
            self.assertEqual(payload['source_blocks'],self.payload()['blocks'])
            self.assertEqual(payload['comments'],self.payload()['comments'])
            self.assertEqual(payload['instruction'],'保留单位')
            self.assertEqual(payload['context_excerpt'],'文档预算说明')
            return self.result()
        with patch.object(ai_proxy,'_complete',side_effect=complete):
            self.assertEqual(ai_proxy.revise(self.payload())['edits'][0]['after'],'200')

    def test_reject_hallucinated_or_unsafe_ranges(self):
        for change in ({'before':'999'},{'block_id':'missing'},{'after':'200\n300'},{'comment_ids':['unknown']},{'after':'100'}):
            with self.subTest(change=change),patch.object(ai_proxy,'_complete',return_value=self.result(**change)):
                with self.assertRaises(ai_proxy.AIError): ai_proxy.revise(self.payload())

    def test_reject_ambiguous_and_overlapping_ranges(self):
        payload=self.payload();payload['blocks'][0]['text']='100 and 100'
        with patch.object(ai_proxy,'_complete',return_value=self.result()):
            with self.assertRaises(ai_proxy.AIError): ai_proxy.revise(payload)
        result=json.loads(self.result());result['edits']*=2
        with patch.object(ai_proxy,'_complete',return_value=json.dumps(result)):
            with self.assertRaises(ai_proxy.AIError): ai_proxy.revise(self.payload())

    def test_bound_context_and_source_without_silent_truncation(self):
        for field,value in [('context','x'*6001),('blocks',[{'id':'b0','text':'x'*12001}]),('comments',[{'id':'1','text':'x'*4001,'block_ids':[]}])]:
            payload=self.payload();payload[field]=value
            with self.assertRaises(ValueError): ai_proxy.revise(payload)

    def test_completion_requires_explicit_model_report(self):
        with patch.object(ai_proxy,'_complete',return_value=self.result()):
            result=ai_proxy.revise(self.payload())
            self.assertEqual(result['comment_results'][0]['status'],'partial')
        result=json.loads(self.result());result['comment_results']=[{'id':'1','status':'complete','reason':'全部完成'}]
        with patch.object(ai_proxy,'_complete',return_value=json.dumps(result)):
            self.assertEqual(ai_proxy.revise(self.payload())['comment_results'][0]['status'],'complete')

    def test_no_changes_and_unresolved_feedback(self):
        with patch.object(ai_proxy,'_complete',return_value=json.dumps({'summary':'','edits':[],'warnings':['批注无法定位']})):
            self.assertEqual(ai_proxy.revise(self.payload())['warnings'],['批注无法定位'])

if __name__=='__main__': unittest.main()
