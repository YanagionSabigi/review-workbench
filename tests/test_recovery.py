"""Kill real writers between durable writes, then reopen through Store."""
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from review_workbench.gitops import compare, git_diff, snapshot
from review_workbench.model import ReviewError
from review_workbench.storage import Store, atomic_json
from review_workbench.transfer import import_results
from tests.helpers import block, init_git, write_package


CRASH_WRITER = r'''
import os, sys
from pathlib import Path
import review_workbench.storage as storage
import review_workbench.transfer as transfer
root=Path(sys.argv[1]); operation=sys.argv[2]; point=sys.argv[3]
store=storage.Store(root)
real_write=storage.atomic_json
submission_writes=0
def crash_after_write(path,data):
    global submission_writes
    real_write(path,data)
    path=Path(path)
    if path.parent.name=='submissions':
        submission_writes+=1
        target='submission-'+str(submission_writes)
    else: target=path.name
    if target==point: os._exit(73)
storage.atomic_json=transfer.atomic_json=crash_after_write
revision=store.state()['drafts']['revision']
if operation=='submit': store.submit(['one'],revision)
elif operation=='resolve':
    first=next(s for s in store.submissions() if s['decisions'][0]['action']=='keep')
    store.resolve_conflict('p1',first['submission_id'],'one',revision)
else: transfer.import_results(root,root/'incoming.json')
'''


def submit(store, mode):
    draft=store.state()['drafts']; revision=draft['revision']
    draft['items']['one']={'mode':mode}
    store.save(draft,revision)
    return store.submit(['one'],revision+1)


class RecoveryTests(unittest.TestCase):
    def prepare_operation(self, root, operation):
        write_package(root); store=Store(root)
        first=submit(store,'keep')
        if operation=='submit':
            draft=store.state()['drafts'];draft['items']['one']={'mode':'accept'}
            store.save(draft,2)
        elif operation=='resolve': submit(store,'accept')
        else:
            other=copy.deepcopy(first);other['submission_id']='incoming-one'
            other['decisions'][0].update(action='accept',blocks=[block('建议')])
            second=copy.deepcopy(first);second['submission_id']='incoming-two'
            second['decisions'][0].update(item_id='two',target_id='p2',blocks=[block('第二段')])
            atomic_json(root/'incoming.json',{'schema_version':'1','package_id':'test-package',
                'base_commit':None,'submissions':[other,second]})
        return store

    def test_interrupted_operations_recover_history_revision_drafts_and_conflicts(self):
        # Removing recovery must leave either stale revision, missing history,
        # stale conflicts, or a resolution whose draft still selects accept.
        for operation in ('submit','resolve','import'):
            points=['submission-1','drafts.json','comparison.json']
            if operation=='import': points.insert(1,'submission-2')
            for point in points:
                with self.subTest(operation=operation,point=point), tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp);self.prepare_operation(root,operation)
                    result=subprocess.run([sys.executable,'-c',CRASH_WRITER,str(root),operation,point],capture_output=True)
                    self.assertEqual(result.returncode,73,result.stderr.decode(errors='replace'))
                    state=Store(root).state()
                    self.assertEqual(state['drafts']['revision'],{'submit':4,'resolve':5,'import':3}[operation])
                    self.assertEqual(len(state['submissions']),2 if operation=='submit' else 3)
                    self.assertEqual(state['drafts']['items']['one']['mode'],'keep' if operation=='resolve' else ('accept' if operation=='submit' else 'keep'))
                    self.assertEqual(bool(state['comparison']['conflicts']),operation!='resolve')
                    if operation=='import':
                        self.assertEqual(state['drafts']['items']['two']['mode'],'keep')
                        retry=import_results(root,root/'incoming.json')
                        self.assertEqual((retry['imported'],retry['duplicates']),(0,2))
                    # Recovery is idempotent, including after importing again.
                    self.assertEqual(Store(root).state()['drafts']['revision'],state['drafts']['revision'])

    def test_existing_store_recovers_before_accepting_stale_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=self.prepare_operation(root,'submit')
            real_write=atomic_json
            def fail_after_submission(path,data):
                real_write(path,data)
                if Path(path).parent.name=='submissions': raise OSError('injected disk failure')
            with patch('review_workbench.storage.atomic_json',side_effect=fail_after_submission):
                with self.assertRaises(OSError): store.submit(['one'],3)
            with self.assertRaises(ReviewError) as ctx: store.submit(['one'],3)
            self.assertEqual(ctx.exception.status,409)
            state=store.state()
            self.assertEqual(state['drafts']['revision'],4)
            self.assertEqual(len(state['submissions']),2)
            self.assertTrue(state['comparison']['conflicts'])

    def test_failed_intent_write_leaves_operation_uncommitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=self.prepare_operation(root,'submit')
            before=store.state()
            real_write=atomic_json
            def fail_intent(path,data):
                if Path(path).name=='.pending-operation.json': raise OSError('cannot record intent')
                real_write(path,data)
            with patch('review_workbench.storage.atomic_json',side_effect=fail_intent):
                with self.assertRaises(OSError): store.submit(['one'],3)
            self.assertEqual(store.state(),before)

    def test_recovery_can_itself_be_interrupted_without_duplicate_commits(self):
        recover_script=r'''
import os,sys
from pathlib import Path
import review_workbench.storage as storage
real_write=storage.atomic_json
def crash(path,data):
    real_write(path,data)
    if Path(path).name=='drafts.json': os._exit(73)
storage.atomic_json=crash
storage.Store(sys.argv[1])
'''
        for operation in ('submit','resolve','import'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);self.prepare_operation(root,operation)
                # Interrupt immediately after the durable intent, before data files.
                result=subprocess.run([sys.executable,'-c',CRASH_WRITER,str(root),operation,'.pending-operation.json'],capture_output=True)
                self.assertEqual(result.returncode,73,result.stderr.decode(errors='replace'))
                for _ in range(2):
                    result=subprocess.run([sys.executable,'-c',recover_script,str(root)],capture_output=True)
                    self.assertEqual(result.returncode,73,result.stderr.decode(errors='replace'))
                state=Store(root).state()
                self.assertEqual(state['drafts']['revision'],{'submit':4,'resolve':5,'import':3}[operation])
                self.assertEqual(len(state['submissions']),2 if operation=='submit' else 3)
                self.assertEqual(bool(state['comparison']['conflicts']),operation!='resolve')
                self.assertEqual(Store(root).state(),state)


class ComparisonRaceTests(unittest.TestCase):
    def prepare_comparison(self, root):
        init_git(root);review=root/'review';data=write_package(review)
        data['base_commit']=snapshot(root,['review/package.json'],'test')
        atomic_json(review/'package.json',data)
        store=Store(review);submit(store,'keep')
        current={'package_id':'test-package','base_commit':data['base_commit'],
                 'targets':[{'target_id':'p1','blocks':[block('原版')]}]}
        return store,current

    def test_new_submission_during_comparison_preserves_new_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store,current=self.prepare_comparison(Path(tmp));review=store.root
            def concurrent_submission(before,after):
                submit(store,'accept')
                return git_diff(before,after)
            with patch('review_workbench.gitops.git_diff',side_effect=concurrent_submission):
                with self.assertRaises(ReviewError) as ctx: compare(review,current)
            self.assertEqual(ctx.exception.status,409)
            state=store.state()
            self.assertTrue(state['comparison']['conflicts'])
            self.assertEqual(len(state['comparison']['items']),2)
            self.assertTrue(compare(review,current)['conflicts'])

    def test_import_resolution_or_draft_change_invalidates_comparison(self):
        for change in ('import','resolve','draft'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                store,current=self.prepare_comparison(Path(tmp))
                first=store.submissions()[0]
                if change=='resolve': submit(store,'accept')
                latest=[]
                changed=False
                def change_during_diff(before,after):
                    nonlocal changed
                    if not changed:
                        changed=True
                        revision=store.state()['drafts']['revision']
                        if change=='import':
                            incoming=copy.deepcopy(first);incoming['submission_id']='imported'
                            incoming['decisions'][0].update(action='accept',blocks=[block('建议')])
                            import_results(store.root,{'schema_version':'1','package_id':'test-package',
                                'base_commit':current['base_commit'],'submissions':[incoming]})
                        elif change=='resolve': store.resolve_conflict('p1',first['submission_id'],'one',revision)
                        else:
                            draft=store.state()['drafts'];draft['items']['two']={'mode':'comment','comment':'请复查'}
                            store.save(draft,revision)
                        latest.append(store.state()['comparison'])
                    return git_diff(before,after)
                with patch('review_workbench.gitops.git_diff',side_effect=change_during_diff):
                    with self.assertRaises(ReviewError) as ctx: compare(store.root,current)
                self.assertEqual(ctx.exception.status,409)
                self.assertEqual(store.state()['comparison'],latest[0])
                result=compare(store.root,current)
                self.assertEqual(bool(result['conflicts']),change=='import')
