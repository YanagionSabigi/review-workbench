import json
import tempfile
import unittest
from tests.helpers import write_package
from review_workbench.model import ReviewError
from review_workbench.storage import Store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        write_package(self.tmp.name)
        self.store = Store(self.tmp.name)

    def tearDown(self): self.tmp.cleanup()

    def test_revision_and_restart(self):
        draft = self.store.state()['drafts']
        draft['items']['one'] = {'mode':'comment','comment':'复查','quotes':[]}
        saved = self.store.save(draft, 0)
        self.assertEqual(saved['revision'], 1)
        self.assertEqual(Store(self.tmp.name).state()['drafts']['items']['one']['comment'], '复查')
        with self.assertRaises(ReviewError) as ctx: self.store.save(draft, 0)
        self.assertEqual(ctx.exception.status, 409)

    def test_partial_submission_and_immutable_history(self):
        draft = self.store.state()['drafts']
        draft['items']['one'] = {'mode':'keep','comment':'inactive comment'}
        self.store.save(draft, 0)
        first = self.store.submit(['one'], 1)
        self.assertEqual(len(first['decisions']), 1)
        self.assertNotIn('instruction', first['decisions'][0])
        draft = self.store.state()['drafts']
        draft['items']['one']['mode'] = 'accept'
        self.store.save(draft, 2)
        second = self.store.submit(['one'], 3)
        self.assertNotEqual(first['submission_id'], second['submission_id'])
        original = json.loads((self.store.root/'submissions'/f"{first['submission_id']}.json").read_text(encoding='utf-8'))
        self.assertEqual(original['decisions'][0]['action'], 'keep')

    def test_bulk_excludes_required_and_human_draft(self):
        draft = self.store.state()['drafts']
        draft['items']['one'] = {'mode':None,'comment':'未提交的意见'}
        self.store.save(draft, 0)
        self.assertEqual(self.store.bulk_candidates(['one','two']), [])

    def test_frozen_material_change_rejected(self):
        write_package(self.tmp.name, {**self.store.package, 'title':'changed'})
        with self.assertRaises(ReviewError) as ctx: self.store.submit(['one'], 0)
        self.assertEqual(ctx.exception.status, 409)


if __name__ == '__main__': unittest.main()
