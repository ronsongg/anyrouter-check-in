#!/usr/bin/env python3
"""Configuration loading for providers and accounts."""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Literal


@dataclass
class ProviderConfig:
    """Provider configuration."""

    name: str
    domain: str
    login_path: str = '/login'
    sign_in_path: str | None = '/api/user/sign_in'
    user_info_path: str = '/api/user/self'
    api_user_key: str = 'new-api-user'
    bypass_method: Literal['waf_cookies'] | None = None
    waf_cookie_names: List[str] | None = None
    request_method: Literal['httpx', 'browser'] = 'httpx'

    def __post_init__(self):
        required_waf_cookies = set()
        if self.waf_cookie_names and isinstance(self.waf_cookie_names, List):
            for item in self.waf_cookie_names:
                name = '' if not item or not isinstance(item, str) else item.strip()
                if not name:
                    print(f'[WARNING] Found invalid WAF cookie name: {item}')
                    continue

                required_waf_cookies.add(name)

        if not required_waf_cookies:
            self.bypass_method = None

        self.waf_cookie_names = list(required_waf_cookies)

        if self.request_method not in ('httpx', 'browser'):
            print(f'[WARNING] Invalid request_method: {self.request_method}, fallback to httpx')
            self.request_method = 'httpx'

    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'ProviderConfig':
        """Create ProviderConfig from a dictionary."""
        return cls(
            name=name,
            domain=data['domain'],
            login_path=data.get('login_path', '/login'),
            sign_in_path=data.get('sign_in_path', '/api/user/sign_in'),
            user_info_path=data.get('user_info_path', '/api/user/self'),
            api_user_key=data.get('api_user_key', 'new-api-user'),
            bypass_method=data.get('bypass_method'),
            waf_cookie_names=data.get('waf_cookie_names'),
            request_method=data.get('request_method', 'httpx'),
        )

    def needs_waf_cookies(self) -> bool:
        """Return whether this provider needs WAF cookie acquisition."""
        return self.bypass_method == 'waf_cookies'

    def needs_manual_check_in(self) -> bool:
        """Return whether this provider needs an explicit sign-in request."""
        return self.sign_in_path is not None

    def uses_browser_requests(self) -> bool:
        """Return whether API requests should run in browser context."""
        return self.request_method == 'browser'


@dataclass
class AppConfig:
    """Application configuration."""

    providers: Dict[str, ProviderConfig]

    @classmethod
    def load_from_env(cls) -> 'AppConfig':
        """Load provider configuration from environment variables."""
        providers = _load_default_providers()
        for name, provider_data in _iter_provider_sources():
            try:
                providers[name] = ProviderConfig.from_dict(name, provider_data)
            except Exception as e:
                print(f'[WARNING] Failed to parse provider "{name}": {e}, skipping')
                continue

        return cls(providers=providers)

    def get_provider(self, name: str) -> ProviderConfig | None:
        """Get provider configuration by name."""
        return self.providers.get(name)


@dataclass
class AccountConfig:
    """Account configuration."""

    cookies: dict | str
    api_user: str
    provider: str = 'anyrouter'
    name: str | None = None

    @classmethod
    def from_dict(cls, data: dict, index: int) -> 'AccountConfig':
        """Create AccountConfig from a dictionary."""
        provider = data.get('provider', 'anyrouter')
        name = data.get('name', f'Account {index + 1}')

        return cls(cookies=data['cookies'], api_user=data['api_user'], provider=provider, name=name if name else None)

    def get_display_name(self, index: int) -> str:
        """Return display name for logs and notifications."""
        return self.name if self.name else f'Account {index + 1}'


def _load_default_providers() -> Dict[str, ProviderConfig]:
    return {
        'anyrouter': ProviderConfig(
            name='anyrouter',
            domain='https://anyrouter.top',
            login_path='/login',
            sign_in_path='/api/user/sign_in',
            user_info_path='/api/user/self',
            api_user_key='new-api-user',
            bypass_method='waf_cookies',
            waf_cookie_names=['acw_tc', 'cdn_sec_tc', 'acw_sc__v2'],
        ),
        'agentrouter': ProviderConfig(
            name='agentrouter',
            domain='https://agentrouter.org',
            login_path='/login',
            sign_in_path=None,
            user_info_path='/api/user/self',
            api_user_key='new-api-user',
            bypass_method='waf_cookies',
            waf_cookie_names=['acw_tc'],
        ),
    }


def _parse_json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def _load_json_env_object(name: str) -> dict:
    raw = os.getenv(name)
    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f'[WARNING] Failed to parse {name} environment variable: {e}')
        return {}

    if not isinstance(data, dict):
        print(f'[WARNING] {name} must be a JSON object, ignoring value')
        return {}

    return data


def _normalize_provider_key(value: str) -> str:
    return value.lower().strip()


def _upsert_account_by_provider(accounts: list[AccountConfig], account: AccountConfig):
    for index, existing in enumerate(accounts):
        if existing.provider == account.provider:
            accounts[index] = account
            return
    accounts.append(account)


def _parse_account_dict(account_dict: dict, index: int, label: str) -> AccountConfig | None:
    if 'cookies' not in account_dict or 'api_user' not in account_dict:
        print(f'ERROR: {label} missing required fields (cookies, api_user)')
        return None

    if 'name' in account_dict and not account_dict['name']:
        print(f'ERROR: {label} name field cannot be empty')
        return None

    return AccountConfig.from_dict(account_dict, index)


def _load_accounts_from_anyrouter_accounts(accounts: list[AccountConfig]) -> bool:
    accounts_str = os.getenv('ANYROUTER_ACCOUNTS')
    if not accounts_str:
        return True

    try:
        accounts_data = json.loads(accounts_str)
    except Exception as e:
        print(f'ERROR: Account configuration format is incorrect: {e}')
        return False

    if not isinstance(accounts_data, list):
        print('ERROR: Account configuration must use array format [{}]')
        return False

    for i, account_dict in enumerate(accounts_data):
        if not isinstance(account_dict, dict):
            print(f'ERROR: Account {i + 1} configuration format is incorrect')
            return False

        account = _parse_account_dict(account_dict, i, f'Account {i + 1}')
        if account is None:
            return False
        accounts.append(account)

    return True


def _load_accounts_from_all_secrets(accounts: list[AccountConfig]) -> bool:
    all_secrets = _load_json_env_object('ALL_SECRETS_JSON')
    for secret_name, secret_value in all_secrets.items():
        if not secret_name.startswith('ANYROUTER_ACCOUNT_'):
            continue

        try:
            account_dict = _parse_json_value(secret_value)
            if not isinstance(account_dict, dict):
                raise ValueError('account secret must be a JSON object')
        except Exception as e:
            print(f'ERROR: Failed to parse {secret_name}: {e}')
            return False

        account = _parse_account_dict(account_dict, len(accounts), secret_name)
        if account is None:
            return False
        _upsert_account_by_provider(accounts, account)

    return True


def _iter_provider_sources():
    providers_data = _load_json_env_object('PROVIDERS')
    for name, provider_data in providers_data.items():
        if isinstance(provider_data, dict):
            yield name, provider_data
        else:
            print(f'[WARNING] Failed to parse provider "{name}": provider config must be a JSON object, skipping')

    all_secrets = _load_json_env_object('ALL_SECRETS_JSON')
    for secret_name, secret_value in all_secrets.items():
        if not secret_name.startswith('PROVIDER_'):
            continue

        try:
            parsed = _parse_json_value(secret_value)
        except Exception as e:
            print(f'[WARNING] Failed to parse {secret_name}: {e}, skipping')
            continue

        if not isinstance(parsed, dict):
            print(f'[WARNING] Failed to parse {secret_name}: provider config must be a JSON object, skipping')
            continue

        if 'domain' in parsed:
            provider_name = _normalize_provider_key(secret_name.removeprefix('PROVIDER_'))
            yield provider_name, parsed
            continue

        for provider_name, provider_data in parsed.items():
            if not isinstance(provider_data, dict):
                print(f'[WARNING] Failed to parse {secret_name}[{provider_name}]: provider config must be a JSON object, skipping')
                continue
            yield provider_name, provider_data


def load_accounts_config() -> list[AccountConfig] | None:
    """Load accounts from ANYROUTER_ACCOUNTS and ALL_SECRETS_JSON."""
    accounts: list[AccountConfig] = []
    if not _load_accounts_from_anyrouter_accounts(accounts):
        return None
    if not _load_accounts_from_all_secrets(accounts):
        return None

    if not accounts:
        print('ERROR: ANYROUTER_ACCOUNTS environment variable not found')
        return None

    return accounts
