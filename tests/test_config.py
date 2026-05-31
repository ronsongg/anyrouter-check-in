import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import ProviderConfig, AppConfig, load_accounts_config


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



def test_all_secrets_json_loads_per_account_secret(monkeypatch):
    monkeypatch.delenv('ANYROUTER_ACCOUNTS', raising=False)
    monkeypatch.setenv('ALL_SECRETS_JSON', json.dumps({
        'ANYROUTER_ACCOUNT_MUYUAN_DO': json.dumps({
            'name': 'muyuan.do',
            'provider': 'muyuan_do',
            'cookies': {'session': 'sess'},
            'api_user': '5210',
        })
    }))

    accounts = load_accounts_config()

    assert accounts is not None
    assert len(accounts) == 1
    assert accounts[0].name == 'muyuan.do'
    assert accounts[0].provider == 'muyuan_do'
    assert accounts[0].cookies == {'session': 'sess'}
    assert accounts[0].api_user == '5210'


def test_all_secrets_json_account_secret_overrides_same_provider_from_list(monkeypatch):
    monkeypatch.setenv('ANYROUTER_ACCOUNTS', '''[
        {"name":"old","provider":"muyuan_do","cookies":{"session":"old"},"api_user":"old-user"},
        {"name":"other","provider":"other","cookies":{"session":"other"},"api_user":"other-user"}
    ]''')
    monkeypatch.setenv('ALL_SECRETS_JSON', json.dumps({
        'ANYROUTER_ACCOUNT_MUYUAN_DO': json.dumps({
            'name': 'new',
            'provider': 'muyuan_do',
            'cookies': {'session': 'new'},
            'api_user': 'new-user',
        })
    }))

    accounts = load_accounts_config()

    assert accounts is not None
    assert [(account.provider, account.name, account.api_user) for account in accounts] == [
        ('muyuan_do', 'new', 'new-user'),
        ('other', 'other', 'other-user'),
    ]


def test_all_secrets_json_loads_single_provider_secret(monkeypatch):
    monkeypatch.delenv('PROVIDERS', raising=False)
    monkeypatch.setenv('ALL_SECRETS_JSON', json.dumps({
        'PROVIDER_MUYUAN_DO': json.dumps({
            'domain': 'https://muyuan.do',
            'sign_in_path': '/api/user/checkin',
            'request_method': 'browser',
        })
    }))

    config = AppConfig.load_from_env()

    provider = config.get_provider('muyuan_do')
    assert provider is not None
    assert provider.domain == 'https://muyuan.do'
    assert provider.sign_in_path == '/api/user/checkin'
    assert provider.request_method == 'browser'


def test_all_secrets_json_provider_secret_can_be_wrapped_object(monkeypatch):
    monkeypatch.delenv('PROVIDERS', raising=False)
    monkeypatch.setenv('ALL_SECRETS_JSON', json.dumps({
        'PROVIDER_CUSTOM_GROUP': json.dumps({
            'foo_router': {'domain': 'https://foo.example.com'},
            'bar_router': {'domain': 'https://bar.example.com', 'api_user_key': 'X-User'},
        })
    }))

    config = AppConfig.load_from_env()

    assert config.get_provider('foo_router').domain == 'https://foo.example.com'
    assert config.get_provider('bar_router').api_user_key == 'X-User'


def test_all_secrets_json_provider_secret_overrides_providers_env(monkeypatch):
    monkeypatch.setenv('PROVIDERS', '''{
        "muyuan_do": {"domain":"https://old.example.com", "request_method":"httpx"},
        "other": {"domain":"https://other.example.com"}
    }''')
    monkeypatch.setenv('ALL_SECRETS_JSON', json.dumps({
        'PROVIDER_MUYUAN_DO': json.dumps({
            'domain': 'https://new.example.com',
            'request_method': 'browser',
        })
    }))

    config = AppConfig.load_from_env()

    assert config.get_provider('other').domain == 'https://other.example.com'
    assert config.get_provider('muyuan_do').domain == 'https://new.example.com'
    assert config.get_provider('muyuan_do').request_method == 'browser'
