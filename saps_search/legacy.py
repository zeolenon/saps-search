"""Search adapter for an already authenticated OpenClaw SAPS client.

Never loads credentials, logs in, or persists session state.
"""
from .client import SAPSClient, SAPSAuthError


class ExistingSessionSearch(SAPSClient):
    def __init__(self, legacy_client):
        self._legacy = legacy_client
        self._http = legacy_client._client
        self._authenticated = True

    def login(self):
        raise SAPSAuthError("Sessão SAPS expirada; autentique separadamente com sua conta autorizada.")

    def close(self):
        # The caller owns the existing client and its session.
        pass

    def _search(self, url, data, **kwargs):
        if not self._legacy._cookies:
            raise SAPSAuthError("Nenhuma sessão SAPS aberta; autentique separadamente.")
        self._authenticated = True
        return super()._search(url, data, **kwargs)

    def _post_search(self, url, **kwargs):
        import httpx
        return self._http.post(
            url, cookies=self._legacy._cookies,
            timeout=httpx.Timeout(90.0, connect=10.0, write=15.0, pool=10.0),
            **kwargs,
        )
