#!/usr/bin/env python3
"""Check that IG_ACCESS_TOKEN still works and warn before it expires.

Fails (exit 1) when the token is invalid or expires within WARN_DAYS, so the
GitHub Actions run turns red and GitHub sends a failure email.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://graph.facebook.com/v27.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER = os.environ["IG_USER_ID"]
WARN_DAYS = int(os.environ.get("WARN_DAYS", "10"))


def get(path, params):
    query = urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(f"{API}/{path}?{query}", timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        print(f"Request to {path} failed ({err.code}): {body}", file=sys.stderr)
        sys.exit(1)


account = get(IG_USER, {"fields": "username,followers_count,media_count", "access_token": TOKEN})
print(f"Account OK: @{account.get('username')} "
      f"({account.get('followers_count')} followers, {account.get('media_count')} posts)")

info = get("debug_token", {"input_token": TOKEN, "access_token": TOKEN}).get("data", {})
if not info.get("is_valid"):
    print("Token is not valid", file=sys.stderr)
    sys.exit(1)

expires = info.get("expires_at") or 0
if expires == 0:
    print("Token does not expire")
    sys.exit(0)

left = datetime.fromtimestamp(expires, timezone.utc) - datetime.now(timezone.utc)
days = left.total_seconds() / 86400
print(f"Token expires in {days:.1f} days")
if days < WARN_DAYS:
    print(f"Token expires in under {WARN_DAYS} days: create a new one and update the "
          f"IG_ACCESS_TOKEN secret", file=sys.stderr)
    sys.exit(1)
