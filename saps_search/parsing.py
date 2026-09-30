from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from bs4 import BeautifulSoup


class SAPSParseError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedTable:
    rows: list[dict[str, str]]
    has_next_page: bool


def _token(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", folded.casefold())


def _document_header(token: str) -> bool:
    return token in {"cnpjcpf", "cpfcnpj", "cnpj", "cpf", "numerocnpj", "numerocpfcnpj"}


def parse_results(html: str) -> ParsedTable:
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        header_row = table.find("thead")
        header_cells = header_row.find_all("th") if header_row else []
        if not header_cells:
            first_row = table.find("tr")
            header_cells = first_row.find_all("th") if first_row else []
        if not header_cells:
            continue

        headers = [cell.get_text(" ", strip=True) for cell in header_cells]
        tokens = {_token(header) for header in headers}
        has_name = bool(tokens & {"nomefantasia", "nome", "razaosocial", "estabelecimento"})
        has_document = any(_document_header(token) for token in tokens)
        if not (has_name and has_document):
            continue

        body = table.find("tbody") or table
        rows: list[dict[str, str]] = []
        for row in body.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if len(values) != len(headers):
                continue
            rows.append(dict(zip(headers, values, strict=True)))

        return ParsedTable(rows=rows, has_next_page=_has_next_page(soup))

    raise SAPSParseError("A resposta não contém a tabela de resultados esperada.")


def _has_next_page(soup: BeautifulSoup) -> bool:
    for anchor in soup.select('a[rel~="next"], .pagination .next a, li.next a'):
        parent = anchor.parent
        parent_classes = set(parent.get("class", [])) if parent else set()
        anchor_classes = set(anchor.get("class", []))
        if "disabled" not in parent_classes | anchor_classes and anchor.get("href"):
            return True
    return False


def normalized_document(value: str) -> str:
    return re.sub(r"\D", "", value)


def row_document(row: dict[str, str]) -> str:
    for header, value in row.items():
        if _document_header(_token(header)):
            return normalized_document(value)
    return ""
