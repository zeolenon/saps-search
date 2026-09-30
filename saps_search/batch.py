from __future__ import annotations

from typing import Any


_CLIENT_TARGETS = {"client", "cliente", "clientes"}
_BUILDING_TARGETS = {"building", "edificacao", "edificacoes"}


def search_rows(client: Any, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    cache: dict[tuple[str, str, str], dict[str, Any]] = {}
    output: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        target_raw = (row.get("target") or "").strip().casefold()
        if target_raw in _CLIENT_TARGETS:
            target = "client"
        elif target_raw in _BUILDING_TARGETS:
            target = "building"
        else:
            output.append({
                "row": index,
                "target": target_raw,
                "outcome": "invalid_target",
                "returned_rows": 0,
                "matches": [],
            })
            continue

        document = row.get("cnpj_cpf") or row.get("cpf_cnpj") or ""
        document_digits = "".join(char for char in document if char.isdigit())
        name = (row.get("name") or row.get("nome") or "").strip()

        if document_digits:
            query_type, query_value = "cnpj", document_digits
        elif name:
            query_type, query_value = "name", name.upper()
        else:
            output.append({
                "row": index,
                "target": target,
                "outcome": "missing_query",
                "returned_rows": 0,
                "matches": [],
            })
            continue

        key = (target, query_type, query_value)
        if key not in cache:
            if target == "client":
                result = (
                    client.search_client(cnpj=query_value)
                    if query_type == "cnpj"
                    else client.search_client(name=query_value)
                )
            else:
                result = (
                    client.search_building(cnpj=query_value)
                    if query_type == "cnpj"
                    else client.search_building(name=query_value)
                )
            cache[key] = result

        output.append({"row": index, **cache[key]})

    return output
