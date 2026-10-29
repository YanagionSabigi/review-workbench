import copy
import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import init_git, git, write_package, package, block
from review_workbench.gitops import snapshot, prepare, compare
from review_workbench.storage import Store, atomic_json
from review_workbench.model import ReviewError


class GitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name);init_git(self.root)
    def tearDown(self): self.tmp.cleanup()

    def test_snapshot_preserves_head_index_and_working_tree(self):
        (self.root/'a.txt').write_text('old',encoding='utf-8');(self.root/'unrelated').write_text('private',encoding='utf-8')
        git(self.root,'add','.');git(self.root,'commit','-m','base')
        head=git(self.root,'rev-parse','HEAD')
        (self.root/'a.txt').write_text('staged',encoding='utf-8');git(self.root,'add','a.txt')
        (self.root/'a.txt').write_text('working',encoding='utf-8');(self.root/'unrelated').write_text('staged-other',encoding='utf-8');git(self.root,'add','unrelated')
        index=(self.root/'.git/index').read_bytes()
        sha=snapshot(self.root,['a.txt'],'round-one')
        self.assertEqual(git(self.root,'show',sha+':a.txt'),'working')
        self.assertEqual((self.root/'.git/index').read_bytes(),index)
        self.assertEqual(git(self.root,'rev-parse','HEAD'),head)
        self.assertEqual((self.root/'a.txt').read_text(encoding='utf-8'),'working')

    def test_initial_snapshot_and_prepare(self):
        write_package(self.root/'input')
        atomic_json(self.root/'scope.json',['input/package.json'])
        result=prepare(self.root,self.root/'input/package.json',self.root/'scope.json',self.root/'review')
        self.assertTrue(result['base_commit'])
        self.assertEqual(Store(self.root/'review').package['package_id'],'test-package')

    def test_worktree_snapshot(self):
        (self.root/'a').write_text('base');git(self.root,'add','a');git(self.root,'commit','-m','base')
        linked=self.root/'linked';git(self.root,'worktree','add','--detach',str(linked))
        (linked/'a').write_text('changed')
        sha=snapshot(linked,['a'],'worktree')
        self.assertEqual(git(linked,'show',sha+':a'),'changed')
        git(self.root,'worktree','remove','--force',str(linked))

    def test_compare_uses_baseline_not_before(self):
        p=package();p['items'][0]['baseline']=[block('建议')]
        write_package(self.root/'review',p)
        sha=snapshot(self.root,['review/package.json'],'round')
        p['base_commit']=sha;atomic_json(self.root/'review/package.json',p)
        store=Store(self.root/'review');d=store.state()['drafts'];d['items']['one']={'mode':'keep'};store.save(d,0);store.submit(['one'],1)
        current={'package_id':p['package_id'],'base_commit':sha,'targets':[{'target_id':'p1','blocks':[block('建议')]}]}
        result=compare(store.root,current)
        self.assertEqual(result['items'][0]['status'],'ready')
        current['targets'][0]['blocks']=[block('原版')]
        self.assertEqual(compare(store.root,current)['items'][0]['status'],'satisfied')
        current['targets'][0]['blocks']=[block('另一版')]
        self.assertEqual(compare(store.root,current)['items'][0]['status'],'conflict')

    def test_same_target_conflicting_submissions(self):
        p=package();write_package(self.root/'review',p);sha=snapshot(self.root,['review/package.json'],'round');p['base_commit']=sha;atomic_json(self.root/'review/package.json',p)
        store=Store(self.root/'review');d=store.state()['drafts'];d['items']['one']={'mode':'keep'};store.save(d,0);store.submit(['one'],1)
        d=store.state()['drafts'];d['items']['one']={'mode':'accept'};store.save(d,2);store.submit(['one'],3)
        current={'package_id':p['package_id'],'base_commit':sha,'targets':[{'target_id':'p1','blocks':[block('原版')]}]}
        self.assertTrue(compare(store.root,current)['conflicts'])


if __name__=='__main__':unittest.main()
