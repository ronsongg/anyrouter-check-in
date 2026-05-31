# Any Router Multi-account Check-in

Multi-provider and multi-account automatic check-in for NewAPI/OneAPI-like sites. The project has built-in support for Any Router and Agent Router, and can be configured for other compatible providers.

## Features

- Multi-provider support.
- Single-account and multi-account check-in.
- Optional notification integrations.
- WAF cookie acquisition through Playwright.
- Optional browser-context API requests for strict Cloudflare/WAF sites.
- Backward-compatible support for the old single JSON secrets and the new per-account/per-provider secrets.

## Recommended GitHub Secrets

The recommended style is to store each account and each custom provider in its own GitHub Environment Secret:

- `ANYROUTER_ACCOUNT_<PROVIDER_ID_UPPER>`: one account object.
- `PROVIDER_<PROVIDER_ID_UPPER>`: one provider object.

The workflow injects `ALL_SECRETS_JSON` with `${{ toJson(secrets) }}` and the script discovers these secrets automatically.

### Example: single account secret

Secret Name:

```text
ANYROUTER_ACCOUNT_MUYUAN_DO
```

Secret Value:

```json
{"name":"muyuan.do","provider":"muyuan_do","cookies":{"session":"xxx"},"api_user":"5210"}
```

Fields:

- `cookies` (required): authentication cookies.
- `api_user` (required): API user header value.
- `provider` (optional): provider id, defaults to `anyrouter`.
- `name` (optional): display name used in logs and notifications.

### Example: single provider secret

Secret Name:

```text
PROVIDER_MUYUAN_DO
```

Secret Value:

```json
{"domain":"https://muyuan.do","login_path":"/login","sign_in_path":"/api/user/checkin","user_info_path":"/api/user/self","api_user_key":"New-API-User","bypass_method":"waf_cookies","waf_cookie_names":["cf_clearance"],"request_method":"browser"}
```

Fields:

- `domain` (required): provider base URL.
- `login_path` (optional): login page path, default `/login`.
- `sign_in_path` (optional): check-in endpoint, default `/api/user/sign_in`.
- `user_info_path` (optional): user info endpoint, default `/api/user/self`.
- `api_user_key` (optional): API user header name, default `new-api-user`.
- `bypass_method` (optional): set to `waf_cookies` to collect WAF cookies with Playwright.
- `waf_cookie_names` (optional): WAF cookie names, for example `["cf_clearance"]`.
- `request_method` (optional): default `httpx`; set to `browser` when strict Cloudflare/WAF blocks `httpx` even after WAF cookies are collected.

## Backward-compatible secrets

The old single JSON secrets continue to work:

- `ANYROUTER_ACCOUNTS`
- `PROVIDERS`

`ANYROUTER_ACCOUNTS` value is an array:

```json
[
  {"name":"main","provider":"anyrouter","cookies":{"session":"xxx"},"api_user":"12345"}
]
```

`PROVIDERS` value is an object keyed by provider id:

```json
{
  "customrouter": {
    "domain": "https://custom.example.com"
  }
}
```

## Merge order

Accounts are loaded in this order:

1. `ANYROUTER_ACCOUNTS`
2. `ANYROUTER_ACCOUNT_*` values inside `ALL_SECRETS_JSON`

A per-account secret overrides an existing account with the same `provider`; otherwise it is appended.

Providers are loaded in this order:

1. built-in providers (`anyrouter`, `agentrouter`)
2. `PROVIDERS`
3. `PROVIDER_*` values inside `ALL_SECRETS_JSON`

A per-provider secret overrides an existing provider with the same provider id; otherwise it is added.

`PROVIDER_*` values may be either:

1. A single provider config object, where the provider id is inferred from the secret suffix, for example `PROVIDER_MUYUAN_DO` -> `muyuan_do`.
2. A wrapped providers object, for example `{"foo_router":{"domain":"https://foo.example.com"}}`.

## GitHub Actions setup

Use the `production` environment in your repository settings and add either the recommended per-secret values or the old single JSON values.

You do not need to manually create a secret named `ALL_SECRETS_JSON`. The workflow sets it automatically:

```yaml
ALL_SECRETS_JSON: ${{ toJson(secrets) }}
ANYROUTER_ACCOUNTS: ${{ secrets.ANYROUTER_ACCOUNTS }}
PROVIDERS: ${{ secrets.PROVIDERS }}
```

Keeping `ANYROUTER_ACCOUNTS` and `PROVIDERS` in the workflow preserves backward compatibility.

## Cloudflare / strict WAF

For Cloudflare-protected sites such as `muyuan.do`, use WAF cookies and browser-context requests:

```json
{
  "bypass_method": "waf_cookies",
  "waf_cookie_names": ["cf_clearance"],
  "request_method": "browser"
}
```

- `bypass_method: "waf_cookies"` opens a browser to collect WAF cookies.
- `request_method: "browser"` executes `/api/user/self` and check-in requests inside the Playwright browser context.

## Built-in providers

`anyrouter` and `agentrouter` are built in. You only need custom provider secrets for other sites or when overriding a built-in provider.

## Local development

```bash
uv sync --dev
uv run playwright install chromium
uv run pytest tests/
uv run checkin.py
```

## License

MIT
