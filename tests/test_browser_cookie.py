import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from checkin import build_browser_cookie_items


def test_build_browser_cookie_items_uses_domain_path_format():
    items = build_browser_cookie_items('https://muyuan.do', {'session': 'abc'})

    assert items == [
        {
            'name': 'session',
            'value': 'abc',
            'domain': 'muyuan.do',
            'path': '/',
        }
    ]
    assert 'url' not in items[0]
