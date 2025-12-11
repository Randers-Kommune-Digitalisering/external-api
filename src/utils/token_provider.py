import time
import logging
import requests
import threading
from requests.auth import AuthBase

logger = logging.getLogger(__name__)


class OAuth2TokenProvider:
    """
    OAuth2 Token Provider supporting Client Credentials and Refresh Token flows.
    """
    def __init__(self, token_url, client_id, client_secret,
                 refresh_token=None, extra_params=None, timeout=10):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.extra_params = extra_params or {}
        self.timeout = timeout

        self._access_token = None
        self._exp_ts = 0
        self._refresh_exp_ts = 0  # Track refresh token expiration
        self._lock = threading.RLock()

    def _now(self):
        return int(time.time())

    def _is_expired(self, skew=30):
        return self._now() >= (self._exp_ts - skew)

    def _is_refresh_expired(self, skew=30):
        if not self.refresh_token or not self._refresh_exp_ts:
            return True
        return self._now() >= (self._refresh_exp_ts - skew)

    def _request_token(self, data):
        resp = requests.post(self.token_url, data=data, timeout=self.timeout)
        resp.raise_for_status()
        token = resp.json()
        self._access_token = token["access_token"]
        if "expires_in" not in token:
            raise ValueError(f"Token response from {self.token_url} missing 'expires_in' field")
        expires_in = int(token["expires_in"])
        self._exp_ts = self._now() + expires_in
        self.refresh_token = token.get("refresh_token", self.refresh_token)
        refresh_expires_in = token.get("refresh_expires_in")
        if self.refresh_token:
            if refresh_expires_in is None:
                raise ValueError(f"Token response from {self.token_url} missing 'refresh_expires_in' field when refresh_token is present")
            self._refresh_exp_ts = self._now() + int(refresh_expires_in)
        else:
            self._refresh_exp_ts = 0
        return self._access_token

    def acquire(self):
        """
        Acquire a token via client credentials.
        """
        with self._lock:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            data.update(self.extra_params)
            return self._request_token(data)

    def refresh(self):
        """
        Refresh token using the refresh_token if available and not expired,
        otherwise fall back to acquire().
        """
        with self._lock:
            if self.refresh_token and not self._is_refresh_expired():
                data = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                }
                data.update(self.extra_params)
                try:
                    return self._request_token(data)
                except requests.HTTPError:
                    return self.acquire()
            else:
                return self.acquire()

    def get_token(self):
        """
        Returns a valid token, refreshing if expired or missing.
        """
        with self._lock:
            if self._access_token is None or self._is_expired():
                return self.refresh() if self._access_token else self.acquire()
            return self._access_token


class BearerAuth(AuthBase):
    """
    A requests.AuthBase that attaches 'Authorization: Bearer <token>'
    and retries once on 401/403 with a refreshed token.
    """
    def __init__(self, token_provider: OAuth2TokenProvider = None, *,
                 token_url=None, client_id=None, client_secret=None,
                 refresh_token=None, extra_params=None, timeout=10):
        if token_provider is not None:
            self.token_provider = token_provider
        elif token_url and client_id and client_secret:
            self.token_provider = OAuth2TokenProvider(
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                extra_params=extra_params,
                timeout=timeout
            )
        else:
            raise ValueError("Must provide either token_provider or all credentials for OAuth2TokenProvider.")

    def __call__(self, r: requests.PreparedRequest):
        token = self.token_provider.get_token()
        r.headers["Authorization"] = f"Bearer {token}"
        return r

    def handle_response(self, r: requests.Response, **kwargs):
        """
        Handle 401/403 responses by refreshing the token and retrying once
        Can be used as a response hook to session.hooks['response']
        """
        if r.status_code in (401, 403):
            self.token_provider.refresh()
            req = r.request
            req.headers["Authorization"] = f"Bearer {self.token_provider.get_token()}"
            new_resp = r.connection.send(req, **kwargs)
            return new_resp
        return r
