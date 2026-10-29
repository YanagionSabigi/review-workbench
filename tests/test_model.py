import copy
import unittest
from tests.helpers import package
from review_workbench.model import ReviewError, validate_package, resolve_decision


class ModelTests(unittest.TestCase):
    def test_package_and_modes(self):
        p = package()
        validate_package(p)
        self.assertEqual(resolve_decision(p['items'][0], {'mode': 'accept'})['blocks'][0]['text'], '建议')
        self.assertEqual(resolve_decision(p['items'][0], {'mode': 'keep'})['blocks'][0]['text'], '原版')

    def test_duplicate_identity_and_mismatched_blocks_rejected(self):
        p = package()
        p['items'][1]['id'] = 'one'
        with self.assertRaises(ReviewError): validate_package(p)
        p = package()
        p['items'][0]['proposal'][0]['id'] = 'wrong'
        with self.assertRaises(ReviewError): validate_package(p)

    def test_only_current_mode_and_effective_content(self):
        item = package()['items'][0]
        with self.assertRaises(ReviewError): resolve_decision(item, {'mode': 'comment', 'comment': ' '})
        with self.assertRaises(ReviewError): resolve_decision(item, {'mode': 'edit', 'edits': {'body': '改'}, 'touched': False})
        result = resolve_decision(item, {'mode': 'comment', 'comment': '核对', 'edits': {'body': '不应用'}, 'quotes': []})
        self.assertNotIn('blocks', result)
        self.assertEqual(result['instruction'], '核对')

    def test_missing_proposal_and_image_edit_rejected(self):
        item = package()['items'][0]
        item['proposal'] = None
        with self.assertRaises(ReviewError): resolve_decision(item, {'mode': 'accept'})
        item['before'] = item['baseline'] = [{'id':'scan','type':'image','asset_id':'scan'}]
        with self.assertRaises(ReviewError): resolve_decision(item, {'mode':'edit','edits':{},'touched':True})

    def test_invalid_foreign_quote_rejected(self):
        item = package()['items'][0]
        with self.assertRaises(ReviewError):
            resolve_decision(item, {'mode':'comment','comment':'核对','quotes':[{'item_id':'other','block_id':'body','version':'before','text':'原版','start':0,'end':2}]})

    def test_broken_tex_rejected_for_keep_accept_and_edit(self):
        item=package()['items'][0]
        item['before']=item['baseline']=item['proposal']=[{'id':'body','type':'tex','text':r'\definitelyUndefinedMacro{'}]
        for draft in [{'mode':'keep'},{'mode':'accept'},{'mode':'edit','touched':True,'edits':{'body':r'\definitelyUndefinedMacro{'}}]:
            with self.subTest(mode=draft['mode']),self.assertRaises(ReviewError):resolve_decision(item,draft)
        self.assertEqual(resolve_decision(item,{'mode':'comment','comment':'请重做识别','quotes':[]})['processing'],'needs_agent')

    def test_valid_tex_passes(self):
        item=package()['items'][0];item['proposal']=[{'id':'body','type':'tex','text':r'\sqrt{\pi}'}]
        self.assertEqual(resolve_decision(item,{'mode':'accept'})['blocks'][0]['text'],r'\sqrt{\pi}')


if __name__ == '__main__': unittest.main()
