#!/usr/bin/env python3
"""Check the Instagram logins still work, keep the Instagram Login token alive, warn before expiry.

- Instagram Login (IG_LOGIN_TOKEN): checks the account, then refreshes the token
  (graph.instagram.com/refresh_access_token, resets it to 60 days; the token must be
  at least 24 hours old). When the refresh hands back a different token and
  GH_SECRETS_TOKEN (a fine-grained GitHub token with "Secrets: read and write" on this
  repository) is set, the IG_LOGIN_TOKEN secret is replaced automatically.
- Facebook Login (IG_ACCESS_TOKEN + IG_USER_ID): checks the account and the expiry date.

Fails (exit 1) when a configured login is unusable or expires within WARN_DAYS, so the
GitHub Actions run turns red and GitHub sends a failure email.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ig_api  # noqa: E402

WARN_DAYS = int(os.environ.get("WARN_DAYS", "10"))
problems = []


def account_ok(api):
    acc = api.get(api.user, {"fields": "username,followers_count,media_count"})
    print(f"[{api.name}] account OK: @{acc.get('username')} "
          f"({acc.get('followers_count')} followers, {acc.get('media_count')} posts)")


def check_instagram(api):
    account_ok(api)
    try:
        res = ig_api.Backend("instagram", api.token)
        res.api = "https://graph.instagram.com"
        new = res.get("refresh_access_token", {"grant_type": "ig_refresh_token"})
    except ig_api.ApiError as exc:
        print(f"[instagram] refresh skipped: {exc}", file=sys.stderr)
        return
    token, days = new.get("access_token", ""), new.get("expires_in", 0) / 86400
    if token:
        print(f"::add-mask::{token}")
    print(f"[instagram] refreshed: valid for {days:.0f} more days")
    if not token or token == api.token:
        return
    gh_token = os.environ.get("GH_SECRETS_TOKEN")
    if not gh_token:
        print(f"[instagram] the refresh returned a new token, but GH_SECRETS_TOKEN is not set, so the "
              f"{api.secret_name} secret was not updated. Generate a new token in the app dashboard before "
              "the old one runs out (60 days after it was made).", file=sys.stderr)
        return
    done = subprocess.run(["gh", "secret", "set", api.secret_name, "--body", token,
                           "--repo", os.environ.get("GITHUB_REPOSITORY", "")],
                          env=dict(os.environ, GH_TOKEN=gh_token), capture_output=True, text=True)
    if done.returncode:
        problems.append(f"could not update the {api.secret_name} secret: {done.stderr.strip()[:200]}")
    else:
        print(f"[instagram] {api.secret_name} secret updated")


def check_system(api):
    """Unified-login business token: issued as non-expiring and cannot inspect itself with debug_token."""
    account_ok(api)
    print("[system] non-expiring business token: no refresh needed")


def check_facebook(api):
    account_ok(api)
    info = api.get("debug_token", {"input_token": api.token}).get("data", {})
    if not info.get("is_valid"):
        problems.append("Facebook Login token is not valid")
        return
    expires = info.get("expires_at") or 0
    if expires == 0:
        print("[facebook] token does not expire")
        return
    days = (datetime.fromtimestamp(expires, timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 86400
    print(f"[facebook] token expires in {days:.1f} days")
    if days < WARN_DAYS:
        problems.append(f"Facebook Login token expires in under {WARN_DAYS} days: "
                        f"create a new one and update the IG_ACCESS_TOKEN secret")


for api in ig_api.backends():
    try:
        {"instagram": check_instagram, "system": check_system}.get(api.name, check_facebook)(api)
    except ig_api.ApiError as exc:
        problems.append(str(exc))

for p in problems:
    print(p, file=sys.stderr)
sys.exit(1 if problems else 0)
