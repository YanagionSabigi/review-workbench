import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
from tests.helpers import package, write_package, init_git
from review_workbench.gitops import snapshot, verify_baseline
from review_workbench.model import ReviewError
from review_workbench.storage import Store, atomic_json, read_json
from review_workbench.transfer import export_package, import_results, history_conflicts


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);init_git(self.root)
        self.review=self.root/'review';p=write_package(self.review)
        p['base_commit']=snapshot(self.root,['review/package.json'],'test')
        atomic_json(self.review/'package.json',p);self.store=Store(self.review)
    def tearDown(self):self.tmp.cleanup()

    def submit(self,mode):
        d=self.store.state()['drafts'];rev=d['revision'];d['items']['one']={'mode':mode};self.store.save(d,rev);return self.store.submit(['one'],rev+1)

    def test_portable_export_relocation_and_result_return(self):
        archive=export_package(self.review,self.root/'portable.zip')
        moved=self.root/'moved';moved.mkdir()
        with zipfile.ZipFile(archive) as z:z.extractall(moved)
        p=Store(moved).package;verify_baseline(moved,p)
        self.assertTrue((moved/'start_review.py').is_file());self.assertTrue((moved/'web/vendor/katex/katex.min.js').is_file())
        self.assertNotIn(str(self.root), (moved/'package.json').read_text(encoding='utf-8'))
        other=Store(moved);d=other.state()['drafts'];d['items']['one']={'mode':'keep'};other.save(d,0);other.submit(['one'],1)
        reply=export_package(moved,self.root/'reply.zip',results_only=True)
        first=import_results(self.review,reply);self.assertEqual(first['imported'],1)
        second=import_results(self.review,reply);self.assertEqual(second['duplicates'],1)

    def test_different_decisions_preserved_as_conflict(self):
        first=self.submit('keep');second=copy.deepcopy(first);second['submission_id']='different'
        second['decisions'][0]['action']='accept';second['decisions'][0]['blocks']=self.store.package['items'][0]['proposal']
        result=import_results(self.review,{'schema_version':'1','package_id':'test-package','base_commit':self.store.package['base_commit'],'submissions':[second]})
        self.assertTrue(result['conflicts']);self.assertEqual(len(self.store.submissions()),2)

    def test_forged_accept_and_wrong_baseline_rejected(self):
        s=self.submit('accept');s['submission_id']='forged';s['decisions'][0]['blocks'][0]['text']='未展示的内容'
        result={'schema_version':'1','package_id':'test-package','base_commit':self.store.package['base_commit'],'submissions':[s]}
        with self.assertRaises(ReviewError):import_results(self.review,result)
        result['base_commit']='0'*40
        with self.assertRaises(ReviewError):import_results(self.review,result)

    def test_zip_traversal_rejected_without_extraction(self):
        path=self.root/'evil.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr('../escape.json','{}')
        with self.assertRaises(ReviewError):import_results(self.review,path)
        self.assertFalse((self.root.parent/'escape.json').exists())

    def test_explicit_resolution_keeps_history_and_clears_conflict(self):
        first=self.submit('keep');self.submit('accept')
        self.assertTrue(history_conflicts(self.store)['conflicts'])
        revision=self.store.state()['drafts']['revision']
        self.store.resolve_conflict('p1',first['submission_id'],'one',revision)
        self.assertEqual(len(self.store.submissions()),3)
        self.assertEqual(history_conflicts(self.store)['conflicts'],[])

    def test_different_comment_instructions_need_resolution(self):
        d=self.store.state()['drafts'];d['items']['one']={'mode':'comment','comment':'请改用术语A','quotes':[]};self.store.save(d,0);self.store.submit(['one'],1)
        d=self.store.state()['drafts'];d['items']['one']['comment']='请改用术语B';self.store.save(d,2);self.store.submit(['one'],3)
        self.assertTrue(history_conflicts(self.store)['conflicts'])


if __name__=='__main__':unittest.main()
