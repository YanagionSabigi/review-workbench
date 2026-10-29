import copy
import json
import subprocess
from pathlib import Path


def block(text, key='body', kind='text'):
    return {'id': key, 'type': kind, 'text': text}


def package():
    return {'schema_version': '1', 'package_id': 'test-package', 'title': '校对',
            'base_commit': None, 'groups': [{'id': 'text', 'title': '文本'}],
            'facets': [], 'assets': [], 'items': [
                {'id': 'one', 'target_id': 'p1', 'group_id': 'text', 'facets': {},
                 'requires_human': False, 'before': [block('原版')],
                 'baseline': [block('原版')], 'proposal': [block('建议')],
                 'evidence': [], 'rationale': '依据', 'location': '第一段'},
                {'id': 'two', 'target_id': 'p2', 'group_id': 'text', 'facets': {},
                 'requires_human': True, 'before': [block('第二段')],
                 'baseline': [block('第二段')], 'proposal': [block('修订第二段')],
                 'evidence': [], 'rationale': '', 'location': '第二段'}]}


def write_package(root, data=None):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    data = copy.deepcopy(data or package())
    (root / 'package.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return data


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True).stdout.decode('utf-8').strip()


def init_git(root):
    git(root, 'init')
    git(root, 'config', 'user.name', 'Test')
    git(root, 'config', 'user.email', 'test@example.invalid')
