import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import ProviderConfig, AppConfig


def test_provider_config_parses_browser_request_method():
    provider = ProviderConfig.from_dict('muyuan_do', {
        'domain': 'https://muyuan.do',
        'sign_in_path': '/api/user/checkin',
        'user_info_path': '/api/user/self',
        'api_user_key': 'New-API-User',
        'bypass_method': 'waf_cookies',
        'waf_cookie_names': ['cf_clearance'],
        'request_method': 'browser',
    })

    assert provider.request_method == 'browser'
    assert provider.uses_browser_requests() is True


def test_provider_config_defaults_to_httpx_request_method():
    provider = ProviderConfig.from_dict('plain', {'domain': 'https://example.com'})

    assert provider.request_method == 'httpx'
    assert provider.uses_browser_requests() is False
