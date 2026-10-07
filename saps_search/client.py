from __future__ import annotations

from typing import Any

import httpx

from .auth import SAPSCredentials
from .parsing import ParsedTable, normalized_document, parse_results, row_document


ORIGIN = "https://sistemascbm.rn.gov.br"
BASE = f"{ORIGIN}/serten"
LOGIN_URL = f"{BASE}/usuarios/login"
CLIENTS_URL = f"{BASE}/clientes"
BUILDINGS_URL = f"{BASE}/edificacoes"

_HEADERS = {
    "User-Agent": "SAPS-Search/0.1 (authorized read-only lookup)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class SAPSError(RuntimeError):
    pass


class SAPSAuthError(SAPSError):
    pass


class SAPSRequestError(SAPSError):
    pass


class SAPSClient:
    def __init__(self, credentials: SAPSCredentials, *, read_timeout: float = 90.0):
        timeout = httpx.Timeout(
            read_timeout,
            connect=10.0,
            write=15.0,
            pool=10.0,
        )
        self._credentials = credentials
        self._http = httpx.Client(
            verify=True,
            follow_redirects=False,
            timeout=timeout,
            headers=_HEADERS,
        )
        self._authenticated = False

    def __enter__(self) -> "SAPSClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self._http.cookies.clear()
        self._http.close()
        self._authenticated = False

    def login(self) -> None:
        try:
            initial = self._http.get(LOGIN_URL)
            if initial.status_code >= 400:
                raise SAPSAuthError(
                    f"Não foi possível abrir a tela de login (HTTP {initial.status_code})."
                )
            response = self._http.post(
                LOGIN_URL,
                data={
                    "_method": "POST",
                    "data[Usuario][matricula]": self._credentials.username,
                    "data[Usuario][senha]": self._credentials.password,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": ORIGIN,
                    "Referer": LOGIN_URL,
                },
            )
        except httpx.TimeoutException as exc:
            raise SAPSAuthError("Tempo esgotado durante o login SAPS.") from exc
        except httpx.HTTPError as exc:
            raise SAPSAuthError("Falha de conexão TLS/HTTP durante o login SAPS.") from exc

        if self._is_login_response(response):
            raise SAPSAuthError(
                "O SAPS retornou à tela de login. Verifique sua conta autorizada."
            )
        if response.status_code >= 400:
            raise SAPSAuthError(f"Falha no login SAPS (HTTP {response.status_code}).")
        self._authenticated = True

    def search_client(
        self,
        *,
        cnpj: str | None = None,
        name: str | None = None,
        redesim: str | None = None,
    ) -> dict[str, Any]:
        supplied = [value is not None for value in (cnpj, name, redesim)]
        if sum(supplied) != 1:
            raise ValueError("Informe exatamente um entre cnpj, name ou redesim.")

        data: dict[str, str] = {
            "_method": "POST",
            "data[Filter][filterFormId]": "Cliente",
        }
        if cnpj is not None:
            query_type = "cnpj"
            query_value = normalized_document(cnpj)
            if not query_value:
                raise ValueError("CPF/CNPJ sem dígitos.")
            data["data[Cliente][num_cnpj]"] = query_value
        elif name is not None:
            query_type = "name"
            query_value = name.strip().upper()
            if not query_value:
                raise ValueError("Nome vazio.")
            data["data[Cliente][dsc_nomefantasia]"] = query_value
        else:
            query_type = "redesim"
            query_value = redesim.strip() if redesim else ""
            if not query_value:
                raise ValueError("Protocolo REDESIM vazio.")
            data["data[Cliente][prot_redesim]"] = query_value

        return self._search(
            CLIENTS_URL,
            data,
            target="client",
            query_type=query_type,
            query_value=query_value,
        )

    def search_building(
        self,
        *,
        cnpj: str | None = None,
        name: str | None = None,
        client_id: str | None = None,
        classification: str | None = None,
        address: str | None = None,
        uf: str | None = None,
        city: str | None = None,
        neighborhood: str | None = None,
    ) -> dict[str, Any]:
        if (cnpj is None) == (name is None):
            raise ValueError("Informe exatamente um entre cnpj ou name.")

        data: dict[str, str] = {"_method": "POST"}
        if cnpj is not None:
            query_type = "cnpj"
            query_value = normalized_document(cnpj)
            if not query_value:
                raise ValueError("CPF/CNPJ sem dígitos.")
            data["data[Edificacao][num_cnpj]"] = query_value
        else:
            query_type = "name"
            query_value = (name or "").strip().upper()
            if not query_value:
                raise ValueError("Nome vazio.")
            data["data[Edificacao][dsc_nomefantasia]"] = query_value

        optional = {
            "client_id": (client_id, "cod_cliente"),
            "classification": (classification, "cod_classificacao"),
            "address": (address, "dsc_endereco"),
            "uf": (uf, "dsc_uf"),
            "city": (city, "dsc_cidade"),
            "neighborhood": (neighborhood, "dsc_bairro"),
        }
        for _arg_name, (value, field_name) in optional.items():
            if value is not None and value.strip():
                data[f"data[Edificacao][{field_name}]"] = value.strip()

        return self._search(
            BUILDINGS_URL,
            data,
            target="building",
            query_type=query_type,
            query_value=query_value,
        )

    def _search(
        self,
        url: str,
        data: dict[str, str],
        *,
        target: str,
        query_type: str,
        query_value: str,
    ) -> dict[str, Any]:
        for attempt in range(2):
            if not self._authenticated:
                self.login()
            try:
                response = self._post_search(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": ORIGIN,
                        "Referer": url,
                    },
                )
            except httpx.TimeoutException as exc:
                raise SAPSRequestError(
                    "A busca excedeu o timeout configurado; não houve repetição automática."
                ) from exc
            except httpx.HTTPError as exc:
                raise SAPSRequestError(
                    "Falha de conexão TLS/HTTP durante a busca SAPS."
                ) from exc

            if self._is_login_response(response):
                self._authenticated = False
                if attempt == 0:
                    continue
                raise SAPSAuthError("A busca continuou redirecionando ao login.")
            if response.status_code != 200:
                raise SAPSRequestError(
                    f"A busca SAPS respondeu HTTP {response.status_code}."
                )
            try:
                parsed = parse_results(response.text)
            except Exception as exc:
                from .parsing import SAPSParseError

                if isinstance(exc, SAPSParseError):
                    raise SAPSRequestError(str(exc)) from exc
                raise SAPSRequestError("Não foi possível interpretar a tabela SAPS.") from exc
            return self._format_result(
                parsed,
                target=target,
                query_type=query_type,
                query_value=query_value,
            )

        raise SAPSAuthError("Não foi possível autenticar para esta busca.")

    def _post_search(self, url: str, **kwargs) -> httpx.Response:
        return self._http.post(url, **kwargs)

    def _is_login_response(self, response: httpx.Response) -> bool:
        location = response.headers.get("location", "").casefold()
        if "usuarios/login" in location:
            return True
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text[:200_000], "html.parser")
        names = {node.get("name", "") for node in soup.select("input[name]")}
        return (
            "data[Usuario][matricula]" in names
            and "data[Usuario][senha]" in names
        )

    @staticmethod
    def _format_result(
        parsed: ParsedTable,
        *,
        target: str,
        query_type: str,
        query_value: str,
    ) -> dict[str, Any]:
        exact_matches: list[dict[str, str]] = []
        if query_type == "cnpj":
            expected = normalized_document(query_value)
            exact_matches = [
                row for row in parsed.rows if row_document(row) == expected
            ]

        if parsed.has_next_page:
            outcome = "exact_match" if exact_matches else "incomplete"
        elif exact_matches:
            outcome = "exact_match"
        elif parsed.rows:
            outcome = "candidate"
        else:
            outcome = "no_exact_hit"

        return {
            "target": target,
            "route": "/serten/clientes" if target == "client" else "/serten/edificacoes",
            "query": {"type": query_type, "value": query_value},
            "outcome": outcome,
            "returned_rows": len(parsed.rows),
            "exact_document_matches": len(exact_matches),
            "has_next_page": parsed.has_next_page,
            "matches": parsed.rows,
        }
