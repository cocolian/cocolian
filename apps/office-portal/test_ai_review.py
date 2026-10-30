import tempfile
import unittest
from pathlib import Path
import ai_review

C='c'*64
A='a'*64
B='b'*64

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)
        self.comments=[{'key':C,'id':'1','resolved':False}]
    def call(self,op,revisions=None,**kw):
        return ai_review.update(self.path,'1',{'op':op,'client':'alice','comments':self.comments,'revisions':revisions or [],**kw})
    def create(self,complete=True):
        token=self.call('begin')['token']
        self.call('prepare',token=token,keys=[C])
        self.call('record',[A,B],token=token,keys=[C],linked=[A,B],certain=True)
        self.call('finish',[A,B],token=token,complete=[C] if complete else [])
    def test_pending_skip_and_persistence(self):
        self.create();self.assertTrue(self.call('sync',[A,B])['statuses'][C]['skip'])
        result=ai_review.update(self.path,'1',{'op':'begin','client':'bob','comments':self.comments,'revisions':[A,B]})
        self.assertEqual(result['eligible'],[])
    def test_only_all_accepted_resolves(self):
        self.create()
        result=self.call('sync',[B],decisions={A:'accepted'})
        self.assertEqual(result['actions'],[])
        result=self.call('sync',[],decisions={B:'accepted'})
        self.assertEqual(result['actions'],[{'key':C,'id':'1','resolved':True}])
    def test_reject_restores_ready_after_remaining_review(self):
        self.create();self.call('sync',[B],decisions={A:'rejected'})
        self.assertTrue(self.call('sync',[B])['statuses'][C]['skip'])
        result=self.call('sync',decisions={B:'accepted'})
        self.assertEqual(result['statuses'][C]['state'],'ready');self.assertFalse(result['statuses'][C]['skip']);self.assertFalse(result['actions'])
    def test_partial_completion_never_resolves(self):
        self.create(complete=False)
        result=self.call('sync',decisions={A:'accepted',B:'accepted'})
        self.assertFalse(result['actions']);self.assertEqual(result['statuses'][C]['state'],'ready')
    def test_disappearance_without_decision_is_not_acceptance(self):
        self.create();result=self.call('sync')
        self.assertEqual(result['statuses'][C]['state'],'needs_review');self.assertEqual(result['actions'],[])
    def test_duplicate_or_unconfirmed_links_need_manual_review(self):
        token=self.call('begin')['token'];self.call('prepare',token=token,keys=[C])
        self.call('record',[A,A],token=token,keys=[C],linked=[A],certain=True)
        result=self.call('finish',[],token=token,complete=[C])
        self.assertEqual(result['statuses'][C]['state'],'needs_review');self.assertFalse(result['actions'])
    def test_actions_are_claimed_by_one_client(self):
        self.create();self.call('sync',decisions={A:'accepted',B:'accepted'})
        result=ai_review.update(self.path,'1',{'op':'sync','client':'bob','comments':self.comments,'revisions':[]})
        self.assertEqual(result['actions'],[])
    def test_undo_reinstates_pending_and_reopens_auto_resolved(self):
        self.create();self.call('sync',decisions={A:'accepted',B:'accepted'});self.comments[0]['resolved']=True
        result=self.call('sync',[A,B],history=True)
        self.assertEqual(result['statuses'][C]['state'],'pending_review');self.assertFalse(result['actions'][0]['resolved'])
    def test_manual_resolve_and_reopen(self):
        self.create();self.comments[0]['resolved']=True;self.call('manual',[A,B],key=C,resolved=True)
        self.comments[0]['resolved']=False
        self.call('manual',key=C,resolved=False)
        self.assertEqual(self.call('begin')['eligible'],[C])
    def test_expired_unconfirmed_write_stays_blocked(self):
        first=ai_review.update(self.path,'1',{'op':'begin','client':'alice','comments':self.comments},now=1)
        ai_review.update(self.path,'1',{'op':'prepare','client':'alice','comments':self.comments,'token':first['token'],'keys':[C]},now=2)
        result=ai_review.update(self.path,'1',{'op':'sync','client':'bob','comments':self.comments},now=700)
        self.assertEqual(result['statuses'][C]['state'],'needs_review')
    def test_document_lease_prevents_parallel_writes(self):
        self.call('begin')
        with self.assertRaises(ai_review.ReviewConflict):self.call('begin')
    def test_long_generation_renews_lease(self):
        payload={'client':'alice','comments':self.comments}
        token=ai_review.update(self.path,'1',dict(payload,op='begin'),now=1)['token']
        ai_review.update(self.path,'1',dict(payload,op='heartbeat',token=token),now=500)
        ai_review.update(self.path,'1',dict(payload,op='prepare',token=token,keys=[C]),now=700)
        with self.assertRaises(ai_review.ReviewConflict):
            ai_review.update(self.path,'1',dict(payload,op='heartbeat',token=token),now=1400)
    def test_unhandled_reply_blocks_resolving_root(self):
        self.comments[0]['thread']=C
        self.comments.append({'key':'d'*64,'id':'2','resolved':False,'thread':C})
        token=self.call('begin')['token'];self.call('prepare',token=token,keys=[C])
        self.call('record',[A],token=token,keys=[C],linked=[A],certain=True)
        self.call('finish',[A],token=token,complete=[C])
        result=self.call('sync',decisions={A:'accepted'})
        self.assertEqual(result['actions'],[])
        self.assertEqual(result['statuses'][C]['state'],'pending_review')

    def test_review_mutex_serializes_different_clients(self):
        result=self.call('review-start')
        with self.assertRaises(ai_review.ReviewConflict):
            ai_review.update(self.path,'1',{'op':'review-start','client':'bob','comments':self.comments})
        self.call('review-end',review_token=result['review_token'])
        result=ai_review.update(self.path,'1',{'op':'review-start','client':'bob','comments':self.comments})
        self.assertIn('review_token',result)

    def test_unprepared_failure_can_retry(self):
        token=self.call('begin')['token'];self.call('finish',token=token,complete=[])
        self.assertEqual(self.call('begin')['eligible'],[C])

if __name__=='__main__':unittest.main()
