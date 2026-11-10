#!/usr/bin/env python3
"""Shared Instagram API access for publish.py, collect.py and check_token.py.

Two ways in (2026-11-09: a Facebook account checkpoint blocked every post, so
publishing no longer depends on Facebook when an Instagram Login token is set):

  "instagram"  Instagram API with Instagram Login (graph.instagram.com).
               No Facebook Page or Facebook login needed at run time.
               Secrets: IG_LOGIN_TOKEN (60-day token from the app dashboard,
               Instagram > API setup with Instagram business login > Generate token),
               optional IG_LOGIN_USER_ID (looked up from /me when empty).
               Publishing, our own insights, followers/media counts.
  "facebook"   Instagram API with Facebook Login (graph.facebook.com), the old setup.
               Secrets: IG_ACCESS_TOKEN, IG_USER_ID.
               Still the only way to read other accounts (business_discovery
               benchmark), which Instagram Login does not offer.

backends() lists the configured ones, Instagram Login first. Only the
Python standard library is used.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

HOSTS = {
    "instagram": "https://graph.instagram.com/v26.0",
    "facebook": "https://graph.facebook.com/v27.0",
    "system": "https://graph.facebook.com/v27.0",
}
# @junglejuggle's Instagram professional account ID (shown in the app dashboard), used when no ID secret is set
DEFAULT_IG_USER_ID = "17841410918177759"

# Errors that mean "this login/token is unusable right now", where trying the other backend is safe
AUTH_SIGNS = ("OAuthException", "(190)", "(102)", "access token", "Access token", "log in to www.facebook.com",
              "Session has expired", "checkpoint", "(401)", "(403)")


class ApiError(RuntimeError):
    pass


class Backend:
    def __init__(self, name, token, user_id=""):
        self.name = name
        self.api = HOSTS[name]
        self.token = token
        self._user = user_id
        self.secret_name = "IG_LOGIN_TOKEN"  # GitHub secret holding this token (check_token.py refreshes it)

    def __repr__(self):
        return f"<{self.name} API>"

    def call(self, method, path, params=None, timeout=60):
        params = dict(params or {})
        params["access_token"] = self.token
        data = urllib.parse.urlencode(params)
        url = f"{self.api}/{path}"
        if method == "GET":
            req = urllib.request.Request(f"{url}?{data}")
        else:
            req = urllib.request.Request(url, data=data.encode(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            body = err.read().decode(errors="replace")
            try:
                e = json.loads(body).get("error", {})
                msg = f"{e.get('message', body)} [{e.get('type', '')} ({e.get('code', '')})]"
            except ValueError:
                msg = body[:300]
            raise ApiError(f"{method} {path} failed via {self.name} ({err.code}): {msg}") from None

    def get(self, path, params=None, timeout=60):
        return self.call("GET", path, params, timeout)

    @property
    def user(self):
        """Instagram professional account ID for this backend."""
        if not self._user:
            me = self.get("me", {"fields": "user_id,username"})
            self._user = str(me.get("user_id") or me["id"])
        return self._user


def is_auth_error(exc):
    return any(s in str(exc) for s in AUTH_SIGNS)


def backends():
    out = []
    login = os.environ.get("IG_LOGIN_TOKEN", "").strip()
    if login.startswith("EAA"):
        # 2026-11-09: new Meta apps only offer "API setup with Unified login", which issues a non-expiring
        # business system-user token (EAA...). It works on graph.facebook.com with the IG user ID, not on
        # graph.instagram.com, and does not depend on anyone's personal Facebook session.
        uid = os.environ.get("IG_LOGIN_USER_ID") or os.environ.get("IG_USER_ID") or DEFAULT_IG_USER_ID
        out.append(Backend("system", login, uid))
    elif login:
        out.append(Backend("instagram", login, os.environ.get("IG_LOGIN_USER_ID", "")))
    if os.environ.get("IG_ACCESS_TOKEN") and os.environ.get("IG_USER_ID"):
        out.append(Backend("facebook", os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]))
    reels_login = os.environ.get("IG_IGLOGIN_TOKEN", "").strip()
    if reels_login.startswith("EAA"):  # a Facebook-type token does not work on graph.instagram.com: ignore it
        reels_login = ""
    if reels_login and not any(b.name == "instagram" for b in out):
        # 2026-11-10: reels fail at media_publish ("Fatal [OAuthException (-1)]") through graph.facebook.com
        # with both the system and Facebook tokens, while carousels still go through. Reels went out fine
        # through graph.instagram.com before the switch, so an Instagram Login token (IGAA...) is kept for them.
        b = Backend("instagram", reels_login, os.environ.get("IG_IGLOGIN_USER_ID", ""))
        b.secret_name = "IG_IGLOGIN_TOKEN"
        out.append(b)
    if not out:
        raise SystemExit("No Instagram credentials: set IG_LOGIN_TOKEN (Instagram Login) "
                         "or IG_ACCESS_TOKEN + IG_USER_ID (Facebook Login)")
    return out


def facebook_backend():
    """The Facebook Login backend (needed for business_discovery), or None."""
    found = backends()
    return next((b for b in found if b.name == "facebook"), None) or next((b for b in found if b.name == "system"), None)
